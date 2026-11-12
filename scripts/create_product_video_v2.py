"""Business-led product film; reusable illustrated slides and narrated chapters."""
from pathlib import Path
import runpy,json,subprocess,re,sys
v=runpy.run_path(str(Path(__file__).with_name('create_media.py')))
base,card,arrow,wrap,font=[v[k] for k in ('base','card','arrow','wrap','font')]
ROOT=v['ROOT'];OUT=ROOT/'docs';WORK=ROOT.parent/'work/product-v2';WORK.mkdir(parents=True,exist_ok=True)
segments=[]
def slide(title,items,narration,kind='cards'):
 n=len(segments)+1;im,d=base(title,'AI GATEKEEPER  /  PRODUCT OVERVIEW',f'{n:02}')
 if kind=='react':
  for box,head,body,fill in [((80,280,690,440),'MODEL • Decide the next step','Use the case and available evidence to select a tool.','#e8f0f6'),((910,280,1520,440),'ACT • Call an allowed tool','Inspect evidence, look up tooling or retrieve policy.','white'),((910,550,1520,710),'OBSERVE • Read the result','Use returned facts and source versions.','white'),((80,550,690,710),'RESPOND • Prepare a handoff','Continue if needed or provide an advisory summary.','#e8f3ef')]:card(d,box,head,body,fill,size=30)
  arrow(d,(690,355),(910,355));arrow(d,(1210,440),(1210,550));arrow(d,(910,625),(690,625));arrow(d,(380,550),(380,440))
  wrap(d,'Bounded ReAct-style loop inside a durable workflow. Human approval stays outside model authority.',80,760,1440,25)
 elif kind=='layers':
  for i,(head,body) in enumerate(items):
   y=255+i*106;card(d,(65,y,1535,y+92),head,body,'#eee6f7' if i==4 else 'white',size=25)
 else:
  y=260
  for head,body in items:
   yy=wrap(d,head,75,y,1450,34,v['INK'],True,8)
   y=wrap(d,body,75,yy+12,1430,28,v['MUTED'],False,8)+35
 p=WORK/f'slide-{n:02}.png';im.save(p);segments.append((p,narration,title))
slide('Welcome to AI Gatekeeper',[
 ('Healthcare AI governance, from proposal to decision','A standalone workspace for business requesters and governance reviewers.'),
 ('Our intent','Prepare a traceable, evidence-based review packet while keeping decisions with people.'),
 ('Today’s story','Business need → workflow → agents and data → architecture → validation')],
 'Welcome to AI Gatekeeper. Healthcare teams want to use AI for staff knowledge, patient communication and clinical support. Before a proposal moves forward, governance teams need to understand its purpose, data, tools, evidence and required oversight. This application brings that review into one traceable workspace. Our intent is to prepare an evidence based decision packet while keeping final authority with people.')
slide('The business problem behind the product',[
 ('Fragmented work','Requests, vendor terms, policies and evidence arrive in separate places.'),
 ('Repeated review and handoff delays','Missing documents and unclear ownership send the same case back and forth.'),
 ('Limited decision visibility','Reviewers need to know which policy version, evidence and rationale supported a decision.')],
 'Consider the operating problem this project addresses. A requester describes an AI idea, but evidence and policies are scattered. Privacy, security and clinical reviewers ask overlapping questions. Missing documents trigger repeated follow ups, and a vendor outage can interrupt progress. Without a shared case history, it is difficult to reconstruct why a decision was made. These are design assumptions for our fictional healthcare organization, not measured customer research.')
slide('Constraints shape the solution',[
 ('Sensitive data and clinical consequences','Scope and declared data classes determine evidence and specialist reviews.'),
 ('Changing and incomplete evidence','System versions, vendor conflicts and missing artifacts must remain visible.'),
 ('Human accountability','A model recommendation cannot waive controls or grant approval.')],
 'The constraints are as important as the opportunity. Patient related information needs careful handling. Clinical and patient facing uses require additional oversight in our synthetic policy. Evidence must match the proposed system version, and contradictory vendor terms need reconciliation. The application therefore checks structured declarations and preserves human gates. It is a local demonstration using fictional data, not a clinical decision system or a compliance certification.')
slide('A workflow that preserves the case',[
 ('1  Intake and evidence','Capture scope → inspect required artifacts → pause and collect what is missing.'),
 ('2  Risk and controls','Check approved tooling → retrieve policy → map findings and reviewer routes.'),
 ('3  Human review and decision','Verify evidence → approve, reject or request changes → retain the audit record.')],
 'The workflow starts with a proposal and its evidence. Missing artifacts pause the case until the requester adds them and resumes. Tooling and policy checks then produce findings, controls and reviewer routes. Failed register lookups get two attempts before an explicit retry. Finally, a reviewer verifies evidence and records a decision. Requested changes return to assessment. Durable state prevents each handoff from becoming a fresh start.')
slide('Where agentic behavior adds value',[
 ('Coordinate a multi-step task','Carry context across tools, interruptions, recovery and human review.'),
 ('Three specialist roles','Intake and Evidence • Risk and Controls • Review Preparation'),
 ('Separate assistance from authority','Models can assist analysis; application rules enforce required evidence and decision gates.')],
 'An agentic design addresses the coordination problem by carrying context through multiple actions and adapting to returned results. Three specialist roles organize evidence, risk and review preparation. LangGraph preserves the overall workflow. Optional model assisted specialists can choose relevant read only tools and summarize what they find. The intended benefit is less manual assembly and more consistent handoffs. Time savings have not yet been measured.')
slide('ReAct framework inside the workflow',[],
 'ReAct connects reasoning and action. A specialist considers the case, selects an allowed tool, observes the returned facts, and decides whether to continue or prepare a response. Our optional live mode uses LangChain create agent loops for this pattern. Iteration and provider calls are bounded. The trace records tool activity and outcomes, not private model reasoning. Human review and mandatory policy gates remain enforced outside the model loop.',kind='react')
slide('Model tools and data requirements',[
 ('MODEL • Optional OpenAI model via LangChain','Configurable gpt-4.1-mini default for tool selection and advisory synthesis; live path unverified.'),
 ('TOOLS • Three read-only functions','inspect_evidence • lookup_tool • retrieve_policy'),
 ('DATA • Authoritative records before generated prose','Internal policies, approved tools, case scope, evidence metadata and decision history.')],
 'The model is useful for selecting tools and synthesizing an advisory narrative across evidence. The configured default is GPT four point one mini; model quality, latency and cost still need evaluation. Three tools inspect evidence metadata, look up approved tooling and retrieve exact policy clauses. These tools supply current catalog facts that the model should not invent. The tested default mode runs real tools and workflow transitions with deterministic rules, without model credentials.')
slide('Internal and external sources have different roles',[
 ('Internal • Used by the local application','Five synthetic policies, four tools, twelve controls, six cases and attached text evidence.'),
 ('External • Background and future evidence inputs','HHS and NIST guidance; vendor terms, BAA records and assurance reports reviewed by people.'),
 ('Data quality • Required for useful decisions','Source owner, effective version, system version, provenance and reviewer verification.')],
 'Internal sources define what the organization permits and what evidence is required. External guidance from HHS and NIST informs the design, while vendor contracts and assurance reports would support real reviews. This build does not fetch external sources during assessment or ingest binary documents. It uses synthetic catalog records and text evidence. Production needs governed ingestion, access controls, source versioning and content verification. Metadata completeness alone does not prove compliance.')
slide('Technology layers and their business purpose',[
 ('Experience • Next.js and React','One workspace for requesters, reviewers and auditors.'),
 ('Action control • FastAPI','Validate submissions, enforce decision gates and reject stale updates.'),
 ('Orchestration • LangGraph and LangChain','Preserve workflow state and expose bounded specialist tool loops.'),
 ('Records • SQLite and versioned catalog','Retain cases, evidence, checkpoints, policy references and decision exports.'),
 ('Observability • Local traces and optional LangSmith','Explain failures and handoffs; enable external tracing when configured.')],
 'Each technology layer serves a business need. Next.js and React provide a shared review experience. FastAPI validates actions and protects decision gates. LangGraph manages state and interruptions; LangChain supplies tools and optional agent loops. SQLite retains cases and checkpoints, with a versioned policy catalog for traceability. Local events make execution inspectable, and optional LangSmith supports configured tracing. Live model and LangSmith delivery remain unverified. Authenticated roles and hardened storage are deployment prerequisites.',kind='layers')
slide('Use cases validate experience and design',[
 ('Staff knowledge • Can a complete case reach review?','Validates intake, policy grounding and human approval.'),
 ('Patient messages • Can missing evidence be resolved?','Validates evidence requests, saved state, resume and specialist routing.'),
 ('Discharge drafts • Can the workflow recover?','Validates failed tool attempts, explicit retry and preserved history.')],
 'Three journeys validate the experience and architecture together. Staff knowledge tests the complete review and approval path. Patient message drafting tests missing evidence, resume and specialist routing. Discharge instruction drafting tests tool failure and recovery. Additional cases cover vendor conflicts, de identification evidence and blocked autonomous prescribing. Twelve automated tests and browser exercises support local workflow behavior. They do not establish clinical safety, regulatory compliance or live model performance.')
slide('Next explore the live application walkthrough',[
 ('Detailed feature tour','Dashboard • intake • evidence • policy citations • decision gates • monitoring • audit'),
 ('Tool calls and agentic workflow behavior','Follow actual local execution, evidence handoffs, interruptions and recovery.'),
 ('Validate locally before deployment','The companion walkthrough uses narrated captures of the running app in rule-based mode.')],
 'The separate live application walkthrough addresses the app features at length: intake, evidence, citations, reviewer actions, tool traces, monitoring and audit export. It uses edited captures from the running local app in rule based mode. This product overview explains why the solution exists and how its design supports the business workflow. The next milestone is user validation, followed by live integration testing and deployment readiness. Thank you.')

if __name__=='__main__':
 (OUT/'AI-Gatekeeper-Product-Architecture-Overview-transcript.txt').write_text('\n\n'.join(title+'\n'+text for _,text,title in segments))
 (OUT/'AI-Gatekeeper-Product-Video-Sources.txt').write_text('Technical reference: https://reference.langchain.com/python/langchain/agents/factory/create_agent\nImplementation: backend/workflow.py and backend/main.py\nBusiness pain points are scenario assumptions. External guidance is background, not a live integration.\n')
 paths=[];chapters=[];elapsed=0;ff=v['FF']
 for i,(img,text,title) in enumerate(segments):
  audio=WORK/f'audio-{i}.mp3';txt=WORK/f'audio-{i}.txt';txt.write_text(text)
  if not audio.exists() or audio.stat().st_size<1000:
   for attempt in range(3):
    try:
     subprocess.run([sys.executable,'-m','edge_tts','--voice','en-US-JennyNeural','--rate=+12%','--file',str(txt),'--write-media',str(audio)],check=True,timeout=55);break
    except (subprocess.TimeoutExpired,subprocess.CalledProcessError):
     if attempt==2:raise
  probe=subprocess.run([ff,'-i',str(audio)],capture_output=True,text=True).stderr
  m=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',probe);dur=int(m[1])*3600+int(m[2])*60+float(m[3])+.5
  clip=WORK/f'clip-{i}.mp4'
  subprocess.run([ff,'-y','-loglevel','error','-loop','1','-i',str(img),'-i',str(audio),'-vf','format=yuv420p','-c:v','libx264','-preset','ultrafast','-tune','stillimage','-crf','20','-r','24','-c:a','aac','-b:a','128k','-af','apad','-t',str(dur),str(clip)],check=True)
  paths.append(clip);chapters.append({'title':title,'start_seconds':round(elapsed,2),'duration_seconds':round(dur,2)});elapsed+=dur;print(f'Completed {i+1}/{len(segments)}: {title}',flush=True)
 listing=WORK/'concat.txt';listing.write_text(''.join(f"file '{p}'\n" for p in paths))
 target=OUT/'AI-Gatekeeper-Product-Architecture-Overview.mp4'
 subprocess.run([ff,'-y','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(target)],check=True)
 (OUT/'AI-Gatekeeper-Product-Architecture-Overview-chapters.json').write_text(json.dumps(chapters,indent=2))
 print(json.dumps({'duration_seconds':elapsed,'file':str(target)}),flush=True)
