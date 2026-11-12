import os
import tempfile
from pathlib import Path
os.environ['GATEKEEPER_DATA_DIR']=tempfile.mkdtemp(prefix='gatekeeper-test-')
os.environ['GATEKEEPER_MODE']='demo'
os.environ['LANGSMITH_TRACING']='false'
from fastapi.testclient import TestClient
from backend.main import app
from backend.workflow import build_graph

client=TestClient(app)

def get(cid): return client.get('/api/cases/'+cid).json()
def post(cid,action,role='Requester',**extra):
    return client.post(f'/api/cases/{cid}/{action}',json={'revision':get(cid)['revision'],**extra},headers={'X-Persona':role})
def ready(cid):
    assert post(cid,'run').status_code==200
    if get(cid)['status']=='waiting_evidence':
        assert post(cid,'sample-evidence').status_code==200
        assert post(cid,'resume').status_code==200
    if get(cid)['status']=='tool_error': assert post(cid,'resume').status_code==200
    return get(cid)

def test_complete_case_and_human_gate():
    v=ready('GK-001'); assert v['status']=='awaiting_review'; assert v['risk']=='Low'
    d={'outcome':'approved','rationale':'Verified scope and all required evidence for the internal pilot.'}
    assert post('GK-001','decision',**d).status_code==403
    assert post('GK-001','decision','Reviewer',**d).status_code==422
    assert post('GK-001','decision','Reviewer',**d,verified=[e['id'] for e in v['case']['evidence']],signoffs=v['reviewers']).status_code==200
    assert get('GK-001')['status']=='approved'
    assert post('GK-001','sample-evidence').status_code==409

def test_missing_evidence_pause_and_resume():
    assert post('GK-002','run').status_code==200
    v=get('GK-002'); assert v['status']=='waiting_evidence'; assert set(v['missing'])=={'baa','evaluation','monitoring'}
    assert post('GK-002','resume').status_code==200
    assert get('GK-002')['status']=='waiting_evidence'
    assert post('GK-002','sample-evidence').status_code==200
    assert post('GK-002','resume').status_code==200
    v=get('GK-002'); assert v['risk']=='High'; assert 'Privacy' in v['reviewers']

def test_conflict_and_changes_loop():
    v=ready('GK-003'); assert any('reconciliation' in x['title'] for x in v['findings'])
    assert post('GK-003','decision','Reviewer',outcome='changes_requested',rationale='Please revise vendor reconciliation with explicit contractual scope.').status_code==200
    assert get('GK-003')['status']=='changes_requested'
    assert post('GK-003','sample-evidence').status_code==200
    assert post('GK-003','resume').status_code==200
    assert get('GK-003')['status']=='awaiting_review'
    assert not get('GK-003').get('decision')

def test_wrong_version_not_accepted():
    assert post('GK-004','run').status_code==200
    ev={'kind':'deidentification','title':'Wrong version report','author':'Test reviewer','date':'2026-01-01','system_version':'0.9','content':'This synthetic report applies only to the previous version.'}
    assert post('GK-004','evidence',evidence=ev).status_code==200
    assert post('GK-004','resume').status_code==200
    assert 'deidentification' in get('GK-004')['missing']
    assert post('GK-004','sample-evidence').status_code==200
    assert post('GK-004','resume').status_code==200
    assert get('GK-004')['risk']=='Moderate'

def test_tool_failure_and_checkpoint_recovery():
    assert post('GK-005','run').status_code==200
    v=get('GK-005'); assert v['status']=='tool_error'
    assert len([e for e in v['events'] if e['kind']=='error'])==2
    graph,conn=build_graph(Path(os.environ['GATEKEEPER_DATA_DIR'])/'checkpoints.sqlite')
    assert graph.get_state({'configurable':{'thread_id':'GK-005'}}).values['status']=='tool_error'
    conn.close()
    assert post('GK-005','resume').status_code==200
    assert get('GK-005')['status']=='awaiting_review'
    assert len([e for e in get('GK-005')['events'] if e['kind']=='error'])==2

def test_blocker_cannot_be_overridden():
    v=ready('GK-006'); assert v['risk']=='Blocked'
    res=post('GK-006','decision','Reviewer',outcome='approved',rationale='Attempting to approve despite mandatory policy blockers.',verified=[e['id'] for e in v['case']['evidence']],signoffs=v['reviewers'])
    assert res.status_code==422
    assert post('GK-006','decision','Reviewer',outcome='rejected',rationale='Autonomous prescribing and unapproved tooling are outside permitted scope.').status_code==200

def test_auditor_read_only():
    assert post('GK-002','decision','Auditor',outcome='rejected',rationale='Auditor must not be allowed to record any decision.').status_code==403
    assert post('GK-002','sample-evidence','Auditor').status_code==403

def test_stale_revision():
    r=client.post('/api/cases/GK-002/decision',headers={'X-Persona':'Reviewer'},json={'revision':-1,'outcome':'rejected','rationale':'This action is based on a stale revision and must fail.'})
    assert r.status_code==409

def test_export_and_citations():
    r=client.get('/api/cases/GK-001/export'); assert r.status_code==200
    v=r.json(); assert v['synthetic_demo']; assert v['audit']; assert v['decision']['outcome']=='approved'
    ids={p['id'] for p in client.get('/api/catalog').json()['policies']}
    assert all(f['policy'] in ids for f in get('GK-006')['findings'])

def test_new_case_validation():
    body={'title':'Internal staff assistant','department':'Operations','owner':'Test Owner','purpose':'A synthetic internal knowledge assistant with human review of outputs.','data_class':'Internal','tool_id':'northstar-assist'}
    r=client.post('/api/cases',json=body); assert r.status_code==200
    cid=r.json()['id']; assert post(cid,'run').json()['status']=='waiting_evidence'
    assert client.post('/api/cases',json=body,headers={'X-Persona':'Auditor'}).status_code==403

def test_live_mode_without_key_falls_back(monkeypatch):
    from backend.workflow import specialist, retrieve_policy
    monkeypatch.setenv('GATEKEEPER_MODE','live')
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    narrative,events=specialist('Review Preparation',{'risk':'Low'},[retrieve_policy])
    assert narrative is None
    assert events[0]['action']=='MODEL: unavailable'


def test_live_provider_failure_falls_back(monkeypatch):
    import langchain_openai
    from backend.workflow import specialist, retrieve_policy
    monkeypatch.setenv('GATEKEEPER_MODE','live')
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-test-key-not-a-real-credential')
    def fail(**kwargs): raise TimeoutError('Simulated provider timeout')
    monkeypatch.setattr(langchain_openai,'ChatOpenAI',fail)
    narrative,events=specialist('Review Preparation',{'risk':'Low'},[retrieve_policy])
    assert narrative is None
    assert 'TimeoutError' in events[0]['detail']
    assert 'synthetic-test-key' not in str(events)
