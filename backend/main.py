import json
import os
import sqlite3
import threading
import uuid
from pathlib import Path
from typing import Literal
from datetime import date
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1]/'.env')
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import Response
from pydantic import BaseModel, Field
from langgraph.types import Command
from backend.workflow import build_graph, CATALOG, now, required_evidence
from backend.seed import seeds, evidence as demo_evidence

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=Path(os.getenv('GATEKEEPER_DATA_DIR',ROOT/'runtime'))
RUNTIME.mkdir(parents=True,exist_ok=True)
graph,checkpoint_connection=build_graph(RUNTIME/'checkpoints.sqlite')
lock=threading.RLock()
db=sqlite3.connect(RUNTIME/'cases.sqlite',check_same_thread=False)
db.execute('CREATE TABLE IF NOT EXISTS cases (id TEXT PRIMARY KEY, payload TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 0)')
db.execute('CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT, at TEXT, actor TEXT, action TEXT, details TEXT)')
for c in seeds(): db.execute('INSERT OR IGNORE INTO cases(id,payload) VALUES(?,?)',(c['id'],json.dumps(c)))
db.commit()
app=FastAPI(title='AI Gatekeeper Healthcare Demo',version='0.1.0')

class Action(BaseModel):
    revision:int

class Evidence(BaseModel):
    kind:Literal['oversight','data_flow','baa','clinical_validation','evaluation','monitoring','deidentification','vendor_reconciliation']
    title:str=Field(min_length=3,max_length=160)
    author:str=Field(min_length=2,max_length=100)
    date:date
    system_version:str=Field(min_length=1,max_length=30)
    content:str=Field(min_length=30,max_length=12000)

class EvidenceAction(Action):
    evidence:Evidence

class Decision(Action):
    outcome:Literal['approved','rejected','changes_requested']
    rationale:str=Field(min_length=15,max_length=3000)
    verified:list[str]=[]
    signoffs:list[str]=[]

class NewCase(BaseModel):
    title:str=Field(min_length=5,max_length=120)
    department:str=Field(min_length=2,max_length=80)
    owner:str=Field(min_length=2,max_length=80)
    purpose:str=Field(min_length=30,max_length=4000)
    data_class:Literal['Public','Internal','De-identified','PHI']
    tool_id:str
    patient_facing:bool=False
    clinical:bool=False
    external:bool=False
    vendor_conflict:bool=False
    autonomous_prescribing:bool=False
    system_version:str=Field(default='1.0',min_length=1,max_length=30)


def allowed(role,roles):
    if role not in roles: raise HTTPException(403,'This demo persona cannot perform this action.')

def row(cid):
    r=db.execute('SELECT payload,revision FROM cases WHERE id=?',(cid,)).fetchone()
    if not r: raise HTTPException(404,'Case not found.')
    return json.loads(r[0]),r[1]

def view(cid):
    c,revision=row(cid)
    snap=graph.get_state({'configurable':{'thread_id':cid}})
    values=dict(snap.values) if snap.values else {'case':c,'status':'draft','events':[],'risk':'Not assessed','required':required_evidence(c),'missing':[]}
    # Submitted evidence is stored before graph resumes.
    values['case']=c
    values['revision']=revision
    values['id']=cid
    values['pending']=bool(snap.next)
    return values

def check_revision(cid,rev):
    if row(cid)[1]!=rev: raise HTTPException(409,'Case changed. Refresh before trying again.')

def audit(cid,role,action,details=''):
    db.execute('INSERT INTO audit(case_id,at,actor,action,details) VALUES(?,?,?,?,?)',(cid,now(),role,action,details))

def save(cid,c,role,action,details=''):
    db.execute('UPDATE cases SET payload=?, revision=revision+1 WHERE id=?',(json.dumps(c),cid))
    audit(cid,role,action,details); db.commit()

def invoke(cid,input):
    try: return graph.invoke(input,{'configurable':{'thread_id':cid},'recursion_limit':40})
    except Exception as exc:
        # Do not leak provider responses or credentials.
        raise HTTPException(503,f'Workflow interrupted ({type(exc).__name__}). Saved checkpoints are retained.') from exc

@app.get('/api/health')
def health():
    return {'ok':True,'mode':os.getenv('GATEKEEPER_MODE','demo'),'model_configured':bool(os.getenv('OPENAI_API_KEY')),'tracing_enabled':os.getenv('LANGSMITH_TRACING','false').lower()=='true' and bool(os.getenv('LANGSMITH_API_KEY')),'storage':'SQLite checkpoints and audit records','authentication':'Local demo persona selection; not production authentication'}

@app.get('/api/catalog')
def catalog(): return CATALOG

@app.get('/api/cases')
def cases():
    with lock: return [view(r[0]) for r in db.execute('SELECT id FROM cases ORDER BY id').fetchall()]

@app.get('/api/cases/{cid}')
def case(cid:str):
    with lock: return view(cid)

@app.post('/api/cases')
def create(body:NewCase,x_persona:str=Header(default='Requester')):
    allowed(x_persona,['Requester'])
    if body.tool_id not in {t['id'] for t in CATALOG['tools']}: raise HTTPException(422,'Select a registered tool.')
    with lock:
        cid='GK-'+uuid.uuid4().hex[:6].upper()
        c=body.model_dump()|{'id':cid,'evidence':[],'simulate_failure':False}
        db.execute('INSERT INTO cases(id,payload) VALUES(?,?)',(cid,json.dumps(c)))
        audit(cid,x_persona,'Create synthetic case',body.title); db.commit()
        return view(cid)

@app.post('/api/cases/{cid}/run')
def run(cid:str,body:Action,x_persona:str=Header(default='Requester')):
    allowed(x_persona,['Requester','Reviewer'])
    with lock:
        check_revision(cid,body.revision); v=view(cid)
        if v['status']!='draft': raise HTTPException(409,'This case has already started. Use its pending action.')
        invoke(cid,{'case':v['case'],'events':[]})
        save(cid,v['case'],x_persona,'Run assessment')
        return view(cid)

@app.post('/api/cases/{cid}/evidence')
def add_evidence(cid:str,body:EvidenceAction,x_persona:str=Header(default='Requester')):
    allowed(x_persona,['Requester','Reviewer'])
    with lock:
        check_revision(cid,body.revision); v=view(cid)
        if v['status'] not in ['draft','waiting_evidence','changes_requested']: raise HTTPException(409,'Evidence is locked during or after final review. Request changes first.')
        e=body.evidence.model_dump(mode='json')
        if e['date']>date.today().isoformat(): raise HTTPException(422,'Evidence date cannot be in the future.')
        e.update({'id':'EV-'+uuid.uuid4().hex[:8],'synthetic':True})
        c=v['case']; c['evidence']=[x for x in c['evidence'] if x['kind']!=e['kind']]+[e]
        save(cid,c,x_persona,'Attach evidence',e['title'])
        return view(cid)

@app.post('/api/cases/{cid}/sample-evidence')
def sample_evidence(cid:str,body:Action,x_persona:str=Header(default='Requester')):
    allowed(x_persona,['Requester','Reviewer'])
    with lock:
        check_revision(cid,body.revision); v=view(cid)
        if v['status'] not in ['draft','waiting_evidence','changes_requested']: raise HTTPException(409,'Evidence cannot be modified at this stage.')
        c=v['case']; needed=required_evidence(c)
        if v['status']=='changes_requested': needed=list(set(needed)|{e['kind'] for e in c['evidence']})
        for kind in needed:
            if not any(e['kind']==kind and e['system_version']==c['system_version'] for e in c['evidence']) or v['status']=='changes_requested':
                ev=demo_evidence(kind,cid,f"SYNTHETIC DEMO EVIDENCE: {kind.replace('_',' ')}. Applies to {c['title']} version {c['system_version']}. Named reviewer must validate this artifact. Human oversight, purpose-limited processing and documented escalation are required. This fixture demonstrates workflow behavior only.")
                ev['system_version']=c['system_version']
                c['evidence']=[e for e in c['evidence'] if e['kind']!=kind]+[ev]
        save(cid,c,x_persona,'Attach synthetic sample evidence','Demo fixture only; reviewer verification still required.')
        return view(cid)

@app.post('/api/cases/{cid}/resume')
def resume(cid:str,body:Action,x_persona:str=Header(default='Requester')):
    allowed(x_persona,['Requester','Reviewer'])
    with lock:
        check_revision(cid,body.revision); v=view(cid)
        if v['status'] not in ['waiting_evidence','changes_requested','tool_error']: raise HTTPException(409,'No resumable interruption.')
        payload={'retry':True} if v['status']=='tool_error' else {'evidence':v['case']['evidence']}
        invoke(cid,Command(resume=payload))
        save(cid,v['case'],x_persona,'Resume assessment',v['status'])
        return view(cid)

@app.post('/api/cases/{cid}/decision')
def decide(cid:str,body:Decision,x_persona:str=Header(default='Requester')):
    allowed(x_persona,['Reviewer'])
    with lock:
        check_revision(cid,body.revision); v=view(cid)
        if v['status']!='awaiting_review': raise HTTPException(409,'Case is not awaiting review.')
        if not body.rationale.strip() or len(body.rationale.strip())<15: raise HTTPException(422,'Record a meaningful decision rationale.')
        if body.outcome=='approved':
            if v['risk']=='Blocked': raise HTTPException(422,'Unresolved blockers prevent approval.')
            ids={e['id'] for e in v['case']['evidence'] if e['kind'] in v['required'] and e['system_version']==v['case']['system_version']}
            if not ids.issubset(set(body.verified)): raise HTTPException(422,'Verify all required evidence before approval.')
            if not set(v['reviewers']).issubset(set(body.signoffs)): raise HTTPException(422,'Record all required specialist sign-offs before approval.')
        invoke(cid,Command(resume=body.model_dump()|{'actor':x_persona,'at':now()}))
        save(cid,v['case'],x_persona,'Human decision: '+body.outcome,body.rationale)
        return view(cid)

@app.get('/api/audit')
def all_audit():
    with lock:
        return [dict(zip(['seq','case_id','at','actor','action','details'],r)) for r in db.execute('SELECT * FROM audit ORDER BY seq DESC LIMIT 300').fetchall()]

@app.get('/api/cases/{cid}/export')
def export(cid:str):
    with lock:
        v=view(cid)
        v['catalog_version']=CATALOG['version']
        v['synthetic_demo']=True
        v['audit']=[a for a in all_audit() if a['case_id']==cid]
        return Response(json.dumps(v,indent=2),media_type='application/json',headers={'Content-Disposition':f'attachment; filename="{cid}-decision-packet.json"'})
