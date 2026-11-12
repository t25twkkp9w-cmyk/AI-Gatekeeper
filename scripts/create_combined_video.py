"""Combined workflow-led product and application film with readable 1440p crops."""
from pathlib import Path
import ast,subprocess,json,re,sys,math
from PIL import Image,ImageDraw,ImageFont,ImageOps
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'docs'; WORK=ROOT.parent/'work/combined-v3';WORK.mkdir(parents=True,exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe();W,H=2560,1440
NAVY='#18354b';INK='#203b50';MUTED='#506d80';BG='#f4f7fa';PURPLE='#eee6f7'
def font(n,b=False):return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if b else '')+'.ttf',n)
def wrap(d,t,x,y,width,size=36,color=INK,bold=False):
 line=''
 for word in t.split():
  test=(line+' '+word).strip()
  if d.textlength(test,font=font(size,bold))>width and line:d.text((x,y),line,font=font(size,bold),fill=color);y+=size*1.3;line=word
  else:line=test
 if line:d.text((x,y),line,font=font(size,bold),fill=color);y+=size*1.3
 return y

def box(d,rect,title,body='',active=False,purple=False):
 x,y,x2,y2=rect;d.rounded_rectangle(rect,18,fill=PURPLE if purple else '#dcecf5' if active else 'white',outline='#477f9f' if active else '#cad8e2',width=4 if active else 2)
 yy=wrap(d,title,x+22,y+18,x2-x-44,33,INK,True)
 if body:wrap(d,body,x+22,yy+10,x2-x-44,28,MUTED)
def arrow(d,a,b,color='#7294ab',dashed=False):
 if dashed:
  dist=math.dist(a,b)
  for k in range(0,int(dist),22):
   f=k/dist;g=min((k+12)/dist,1);d.line((a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f,a[0]+(b[0]-a[0])*g,a[1]+(b[1]-a[1])*g),fill=color,width=4)
 else:d.line((a,b),fill=color,width=4)
 ang=math.atan2(b[1]-a[1],b[0]-a[0]);d.polygon([b,(b[0]-18*math.cos(ang-.5),b[1]-18*math.sin(ang-.5)),(b[0]-18*math.cos(ang+.5),b[1]-18*math.sin(ang+.5))],fill=color)
stages=['1  Intake','2  Evidence','3  Risk and controls','4  Human review','5  Decision']
def ribbon(d,active,y=200):
 for i,t in enumerate(stages):
  x=70+i*490;box(d,(x,y,x+450,y+94),t,active=i in active)
  if i<4:arrow(d,(x+450,y+47),(x+487,y+47))
def base(title,active,part='PRODUCT AND ARCHITECTURE'):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 d.text((70,35),'AI GATEKEEPER  /  '+part,font=font(28,True),fill=MUTED)
 wrap(d,title,70,90,2420,54,NAVY,True);ribbon(d,active)
 return im,d

def graph(d,active):
 # Every explanatory slide returns to the same branch and call map.
 box(d,(70,380,520,530),'Capture scope','Owner, purpose, data and tool',0 in active)
 box(d,(590,380,1040,530),'Inspect evidence','Metadata and version checks',1 in active)
 box(d,(1110,380,1560,530),'Assess risk','Tool status, policy and controls',2 in active)
 arrow(d,(520,455),(590,455));arrow(d,(1040,455),(1110,455))
 box(d,(590,600,1040,735),'Pause for evidence','Attach, recheck and resume',1 in active)
 arrow(d,(815,530),(815,600));arrow(d,(620,600),(620,530))
 box(d,(1110,600,1560,735),'Pause on failure','Two attempts, explicit retry',2 in active)
 arrow(d,(1335,530),(1335,600));arrow(d,(1140,600),(1140,530))
 box(d,(70,810,520,970),'MODEL calls','Intake / Risk / Review specialists',any(x in active for x in [1,2,3]))
 box(d,(590,810,1040,970),'TOOL calls','inspect_evidence • lookup_tool • retrieve_policy',any(x in active for x in [1,2]))
 arrow(d,(520,875),(590,875),dashed=True);arrow(d,(590,935),(520,935),dashed=True)
 box(d,(1110,810,1560,970),'Human decision','Verify, approve, reject or revise',any(x in active for x in [3,4]))
 d.line([(1560,455),(1610,455),(1610,790),(1450,790)],fill='#7294ab',width=4);arrow(d,(1450,790),(1450,810));arrow(d,(1040,890),(1110,890))
 box(d,(70,1050,1560,1185),'LANGSMITH  |  Required observability','Trace workflow, model calls, tool results, failures, latency and usage.',purple=True)
 for x in [295,815,1335]:arrow(d,(x,970),(x,1050),color='#8d71ab',dashed=True)
 wrap(d,'Solid: workflow and local tools. Dashed: live model / tracing integration. Recorded demo: not connected to providers.',70,1230,1490,27,MUTED)

spec=[
('Welcome to AI Gatekeeper',[0,1,2,3,4],[('Business context','Healthcare teams need a consistent path from an AI proposal to an accountable decision.'),('Intent','Prepare a traceable review packet, with policy evidence and human authority.')],
 'Welcome to AI Gatekeeper. Healthcare teams want AI to help staff find policies, draft patient communications and support clinical workflows. Governance teams need to understand the purpose, data, tooling and oversight before deciding whether a proposal can proceed. This application organizes that work into the five stages you see here: intake, evidence, risk and controls, human review, and decision. We will keep returning to this visual, then follow the same path in the application.'),
('Business friction and constraints',[0,1],[('Pain points','Scattered evidence, repeated follow-ups, unclear ownership and difficult decision reconstruction.'),('Constraints','Sensitive data, clinical scope, changing vendor terms and system-specific evidence.')],
 'Start on the left of the workflow. In our fictional healthcare scenario, requests arrive with incomplete context and scattered documents. Reviewers repeat questions, wait for evidence and struggle to reconstruct decisions. Sensitive data and clinical consequences make those gaps important. Structured intake captures the owner, purpose, tool and declared data class. The evidence stage checks required artifacts and versions. Missing inputs lead to a visible pause, rather than an invented answer.'),
('Workflow branches preserve progress',[1,2,3,4],[('Pause and resume','Missing evidence and unavailable tools retain the same case and checkpoint.'),('Human handoff','Verify evidence, record rationale, approve, reject or return for changes.')],
 'Now follow the two branches beneath evidence and risk. Missing artifacts pause the case until evidence arrives. A tools register outage gets two attempts, then waits for an explicit retry. Successful checks prepare findings, controls and review routes. The right side remains a human handoff. A reviewer can approve, reject or request changes, which sends the case back for reassessment. LangGraph preserves state across these transitions. Approval does not trigger deployment.'),
('ReAct connects model and tool calls',[1,2,3],[('MODEL → TOOL → OBSERVATION','Select an allowed tool, read its returned facts, then continue or prepare a response.'),('Bounded authority','Intake, risk and review specialists advise. Code enforces policy and approval gates.')],
 'The lower loop explains the agentic design. In live mode, a specialist model considers the case, selects an allowed tool, observes the returned result and either continues or prepares a response. This is the ReAct pattern, implemented with LangChain create agent loops inside the LangGraph workflow. Three specialists support intake, risk and review preparation. Calls and iterations are bounded. The model cannot waive required controls or approve a case. The recorded application uses deterministic rules and real local tools; live model execution still needs validation.'),
('Models tools and governed data',[1,2],[('Model need','Tool selection and advisory synthesis. Configurable OpenAI model, default gpt-4.1-mini.'),('Internal and external sources','Internal policies and tools register drive checks. Vendor evidence and HHS/NIST guidance inform review.'),('Data quality','Source owner, version, provenance and human content verification.')],
 'The model supports tool selection and advisory synthesis, with GPT four point one mini as the configured default. The three read only tools inspect evidence, look up approved tooling and retrieve exact policy clauses. Internal sources provide the organization’s rules, controls and case records. External vendor terms and assurance reports would support real review, while HHS and NIST guidance provides background. This build uses synthetic catalog data and text evidence, not live external connectors. Source versions and human content verification remain essential.'),
('Technology layers serve the workflow',[0,1,2,3,4],[('Experience and action control','Next.js and React workspace; FastAPI validation, revision checks and decision gates.'),('Orchestration and records','LangGraph state, LangChain tools and agents, SQLite cases and durable checkpoints.'),('Observability','LangSmith is a required architecture component and a deployment validation gate.')],
 'Read the technology stack through this same workflow. Next.js and React provide the shared workspace. FastAPI validates actions and enforces decision gates. LangGraph manages state, branches and human interrupts. LangChain provides tool interfaces and model loops. SQLite stores cases and durable checkpoints. LangSmith is a required architecture component, not an optional add on. Before deployment, its traces must be connected and verified alongside authenticated roles, protected storage and independently attributable approvals.'),
('Observability follows every handoff',[1,2,3,4],[('LANGSMITH • Required','Correlate workflow runs, model and tool spans, failures, latency and token usage.'),('Audit • Separate responsibility','Retain human decisions, evidence verification, source versions and rationale.'),('Recorded build status','Local events work. LangSmith delivery and live model calls are not yet credential-validated.')],
 'The purple layer follows every stage. The target LangSmith trace links the workflow to model calls, tool inputs and outputs, failures, latency and token usage when models run. Human audit records separately capture decisions and rationale. Observability explains execution; it does not replace governance evidence. In the recorded build, local events are working, but LangSmith delivery and live model calls have not been credential validated. We show that status honestly while making tracing mandatory for deployment readiness.'),
('From design to the application',[0,1,2,3,4],[('Follow the same five stages','Staff knowledge: complete review. Patient messages: evidence pause. Discharge drafts: tool recovery.'),('What to watch','Case state, tool observations, policy citations and the human decision boundary.')],
 'Let us move directly from this diagram into the application. We will follow the same stages in three cases. Staff knowledge demonstrates a complete review. Patient message drafting pauses for missing evidence. Discharge instruction drafting recovers from a failed tool. Watch how case state, source citations and tool observations lead to the next step. The following close ups are edited captures of actual app interactions with synthetic data, so the actions and their results are easy to read.')
]
segments=[]
for i,(title,active,items,narration) in enumerate(spec):
 im,d=base(title,active);graph(d,active);y=390
 for head,body in items:
  y=wrap(d,head,1670,y,800,37,INK,True)+15;y=wrap(d,body,1670,y,790,33,MUTED)+55
 p=WORK/f'final-product-{i}.png';im.save(p);segments.append((title,[p],narration,None))
# Read the existing authored narration without running its media-generation side effects.
tree=ast.parse((ROOT/'scripts/create_walkthrough_v2.py').read_text())
walk=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='chapters' for t in n.targets))
active_by=[[],[0],[0,2],[0,1,2],[1,2],[3,4],[0,1],[1,2],[2],[1,2],[2,3],[4]]
for idx,(title,names,narration) in enumerate(walk):
 if idx==0:continue # no second introduction at the transition
 if idx==11:narration='Monitoring shows eighteen workflow events, two failed tool attempts and one human decision. The audit view records actions and rationale. Local traces demonstrate actual execution in this build. LangSmith is required in the architecture, but this recorded session is not yet connected to it. Before deployment, verify end to end trace delivery for workflow, model and tool calls. Across these cases, we have seen saved state, evidence handoffs, bounded retries and human decisions.'
 paths=[]
 for j,name in enumerate(names):
  shot=Image.open(OUT/'walkthrough-v2-captures'/f'{name}.png').convert('RGB')
  # Focus on task content instead of shrinking the whole browser into a video.
  if name=='02-intake-form':crop=(850,60,2400,1936)
  elif name=='16-source-policy':crop=(1000,350,2450,1550)
  elif name in ['09-review-ready','10-approved','21-recovery-events']:crop=(500,0,3236,1750)
  elif name=='01-dashboard':crop=(500,0,3236,1500)
  elif name in ['03-policy-library','04-portfolio','22-monitoring','23-audit']:crop=(500,180,3236,1850)
  else:crop=(500,580,3236,1936)
  shot=shot.crop(crop)
  im,d=base(title,active_by[idx],'APPLICATION WALKTHROUGH')
  shot=ImageOps.contain(shot,(2440,1030),Image.Resampling.LANCZOS)
  im.paste(shot,((W-shot.width)//2,325))
  d.text((70,1380),'Actual app interaction captures • Synthetic data • Rule-based execution • Live tracing validation pending',font=font(27),fill=MUTED)
  p=WORK/f'final-walk-{idx}-{j}.png';im.save(p);paths.append(p)
 cache=None if idx==11 else ROOT.parent/'work/walkthrough-v2'/f'audio-{idx}.mp3'
 segments.append((title,paths,narration,cache))
im,d=base('Thank you',[0,1,2,3,4],'AI GATEKEEPER')
wrap(d,'Evidence first. Human decision, always.',220,490,2120,76,NAVY,True)
wrap(d,'A healthcare governance workflow that makes tool use, handoffs and decisions visible.',220,650,2100,49,MUTED)
wrap(d,'Next milestone: user validation, live model and LangSmith verification, then deployment readiness.',220,900,2100,43,MUTED)
p=WORK/'final-thank-you.png';im.save(p)
segments.append(('Thank you',[p],'Thank you for exploring AI Gatekeeper. We have connected the business problem, agentic architecture and real application behavior through one workflow. Our next milestone is user validation, live model and LangSmith verification, followed by deployment readiness.',None))
if __name__=='__main__':
 clips=[];timings=[];elapsed=0;transcript=[]
 for i,(title,frames,words,cache) in enumerate(segments):
  audio=cache if cache and cache.exists() else WORK/f'audio-{i}.mp3'
  if not audio.exists() or audio.stat().st_size<1000:
   txt=WORK/f'audio-{i}.txt';txt.write_text(words)
   for attempt in range(3):
    try:subprocess.run([sys.executable,'-m','edge_tts','--voice','en-US-JennyNeural','--rate=+12%','--file',str(txt),'--write-media',str(audio)],check=True,timeout=55);break
    except (subprocess.TimeoutExpired,subprocess.CalledProcessError):
     if attempt==2:raise
  probe=subprocess.run([FF,'-i',str(audio)],capture_output=True,text=True).stderr;m=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',probe);duration=int(m[1])*3600+int(m[2])*60+float(m[3])+.5
  listing=WORK/f'frames-{i}.txt';listing.write_text(''.join(f"file '{p}'\nduration {duration/len(frames)}\n" for p in frames)+f"file '{frames[-1]}'\n")
  clip=WORK/f'clip-{i}.mp4'
  subprocess.run([FF,'-y','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-i',str(audio),'-vf','fps=24,format=yuv420p','-c:v','libx264','-preset','ultrafast','-crf','17','-c:a','aac','-b:a','160k','-af','apad','-t',str(duration),str(clip)],check=True)
  clips.append(clip);timings.append({'title':title,'start_seconds':round(elapsed,2),'duration_seconds':round(duration,2)});elapsed+=duration;transcript.append(title+'\n'+words);print(f'{i+1}/{len(segments)} {title}',flush=True)
 listing=WORK/'concat.txt';listing.write_text(''.join(f"file '{p}'\n" for p in clips));target=OUT/'AI-Gatekeeper-Complete-Overview-and-Demo.mp4'
 subprocess.run([FF,'-y','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(target)],check=True)
 assert elapsed<600, f'Video exceeds 10 minutes: {elapsed}'
 (OUT/'AI-Gatekeeper-Complete-Overview-and-Demo-chapters.json').write_text(json.dumps(timings,indent=2))
 (OUT/'AI-Gatekeeper-Complete-Overview-and-Demo-transcript.txt').write_text('\n\n'.join(transcript))
 print(json.dumps({'seconds':elapsed,'bytes':target.stat().st_size,'file':str(target)}),flush=True)
