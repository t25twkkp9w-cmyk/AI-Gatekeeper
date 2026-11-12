from pathlib import Path
import runpy,subprocess,re,json,sys
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs';WORK=ROOT.parent/'work/walkthrough-v2';WORK.mkdir(parents=True,exist_ok=True)
v=runpy.run_path(str(Path(__file__).with_name('create_media.py')));font=v['font'];ff=v['FF']
RAW=ROOT.parent/'work/tour-v2-raw';CAP=OUT/'walkthrough-v2-captures';CAP.mkdir(exist_ok=True)
for p in RAW.glob('*.png'):
 im=Image.open(p).convert('RGB');im.crop((112,162,3348,2098)).save(CAP/p.name)
chapters=[
('Welcome and business context',['01-dashboard'],'Welcome to the AI Gatekeeper application walkthrough. Imagine a healthcare team proposing an AI assistant. Governance reviewers need evidence, approved tooling and accountable decisions, but manual handoffs create gaps and delays. We will tour the workspace, then follow three real local workflows. This is an edited capture of an interactive session using synthetic data and rule based execution, not a live language model demonstration.'),
('Feature tour  |  Dashboard and intake',['01-dashboard','02-intake-form'],'The dashboard brings the portfolio and review status together. New assessment opens the intake form. The requester declares an owner, purpose, data classification, tool and system version. Clinical use, patient facing output and external processing are explicit flags. These declarations determine later evidence requirements. We close the form and use seeded cases for this demonstration.'),
('Feature tour  |  Sources and portfolio',['03-policy-library','04-portfolio'],'The policy library exposes versioned internal rules and the approved tools register. This makes the assessment basis visible to reviewers. The assessment portfolio supports searching and status filtering. Inside each case, Assessment, Evidence, Decision and Activity organize the work. Monitoring and Audit provide cross case visibility, which we will inspect after running the scenarios.'),
('Use case 1  |  Run the staff assistant assessment',['05-staff-before','06-staff-result'],'Our first proposal is a staff policy knowledge assistant. It uses internal data and an approved tool, with oversight evidence already present. We select Run assessment. The saved workflow inspects evidence, checks the register and maps policy requirements. The result is low risk and ready for AI Governance review. The business value is a prepared review packet, not automatic approval.'),
('Observe the actual tool results',['07-staff-trace'],'Open Activity to see what actually executed. Evidence inspection found one matching evidence kind and no gaps. Lookup tool returned Northstar Assist as approved. The risk step produced a finding grounded in versioned policy. Review preparation then paused for a human decision. These are recorded tool results and state transitions, not generated explanations of hidden model reasoning.'),
('Human handoff  |  Verify and decide',['08-requester-gate','09-review-ready','10-approved'],'The Business Requester cannot approve. Switching to Governance Reviewer enables evidence verification and sign off. We check the oversight record, attest AI Governance review and enter a scope specific rationale. Approve scope records the outcome and preserves the verified checks. Export packet is available for the case record. The approval concerns this synthetic proposal and does not deploy any system.'),
('Use case 2  |  Patient messages need evidence',['11-patient-before','12-missing-evidence'],'Patient message drafting introduces protected health information, patient facing output and an external processor. Running the assessment now produces a different route. The workflow pauses for BAA, evaluation and monitoring evidence. It retains the case rather than filling gaps with assumptions. This is a practical agentic behavior: stop, explain the missing inputs and wait for the next authorized action.'),
('Supply evidence and resume',['13-evidence-gaps','14-evidence-added','15-patient-result'],'The Evidence workspace identifies missing artifacts. We select Add demo evidence to attach explicitly synthetic fixtures. Their metadata includes author, date and system version. Resume assessment rechecks completeness and continues the same case. It now reaches high risk review with AI Governance, Privacy and Security or Vendor Risk. Evidence presence does not remove the human decision gate.'),
('Inspect the source behind a finding',['16-source-policy'],'Opening the policy citation reveals the exact fictional clause behind the finding. The reviewer can compare the requirement with the submitted evidence. This connects the result to a source instead of asking the reviewer to trust a fluent summary. The current evidence tool checks metadata and version, so people still need to verify content and scope.'),
('Use case 3  |  A tool becomes unavailable',['17-discharge-before','18-tool-error','19-failed-trace'],'Discharge instruction drafting has complete evidence, but its tools register deliberately fails. We run the assessment and open Activity. Two lookup attempts fail, then the workflow pauses with the case saved. It does not interpret an unavailable register as approval. This scenario tests bounded retries and a visible recovery path for the person operating the system.'),
('Retry and inspect preserved history',['20-recovered','21-recovery-events'],'Select Retry lookup. The synthetic outage clears, and the same checkpoint resumes. The trace keeps both failed attempts, then adds the resume event, successful lookup, high risk assessment and review preparation. We can explain what changed and why the workflow continued. A human decision is still required after recovery.'),
('Monitoring audit and the model boundary',['22-monitoring','23-audit'],'Monitoring shows eighteen workflow events, two failed tool attempts and one human decision. Audit records the actions and rationale. In this tested mode, rules select the workflow path and real local tools execute. Optional live mode adds bounded model selected tool loops and advisory summaries. Live model and LangSmith integration still need credentialed validation. This demonstration proves local state, tool use, interruption, recovery and human handoff, while preserving decision accountability.')
]
frames=[]
for idx,(title,names,words) in enumerate(chapters):
 seq=[]
 for j,name in enumerate(names):
  canvas=Image.new('RGB',(1920,1280),'#18354b');d=ImageDraw.Draw(canvas)
  d.text((35,20),'AI GATEKEEPER  /  INTERACTIVE SESSION WALKTHROUGH',font=font(23,True),fill='#c4d6e2')
  d.text((35,61),title,font=font(36,True),fill='white')
  shot=ImageOps.contain(Image.open(CAP/(name+'.png')),(1920,1100))
  canvas.paste(shot,((1920-shot.width)//2,115))
  d.text((35,1246),'Actual app actions and results • Edited session captures • Synthetic data • Rule-based mode',font=font(22),fill='#c4d6e2')
  path=WORK/f'frame-{idx}-{j}.png';canvas.save(path);seq.append(path)
 frames.append(seq)
if __name__=='__main__':
 paths=[];timings=[];elapsed=0
 for i,((title,names,words),seq) in enumerate(zip(chapters,frames)):
  txt=WORK/f'audio-{i}.txt';txt.write_text(words);audio=WORK/f'audio-{i}.mp3'
  if not audio.exists() or audio.stat().st_size<1000:
   for attempt in range(3):
    try:subprocess.run([sys.executable,'-m','edge_tts','--voice','en-US-JennyNeural','--rate=+12%','--file',str(txt),'--write-media',str(audio)],check=True,timeout=55);break
    except (subprocess.TimeoutExpired,subprocess.CalledProcessError):
     if attempt==2:raise
  probe=subprocess.run([ff,'-i',str(audio)],capture_output=True,text=True).stderr;m=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',probe);dur=int(m[1])*3600+int(m[2])*60+float(m[3])+.5
  listing=WORK/f'frames-{i}.txt';listing.write_text(''.join(f"file '{p}'\nduration {dur/len(seq)}\n" for p in seq)+f"file '{seq[-1]}'\n")
  target=WORK/f'clip-{i}.mp4'
  subprocess.run([ff,'-y','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-i',str(audio),'-vf','fps=24,format=yuv420p','-c:v','libx264','-preset','ultrafast','-crf','20','-c:a','aac','-b:a','128k','-af','apad','-t',str(dur),str(target)],check=True)
  paths.append(target);timings.append({'title':title,'start_seconds':round(elapsed,2),'duration_seconds':round(dur,2)});elapsed+=dur;print(f'Completed {i+1}/{len(chapters)}: {title}',flush=True)
 listing=WORK/'concat.txt';listing.write_text(''.join(f"file '{p}'\n" for p in paths));target=OUT/'AI-Gatekeeper-App-Walkthrough.mp4'
 subprocess.run([ff,'-y','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(target)],check=True)
 (OUT/'AI-Gatekeeper-App-Walkthrough-transcript.txt').write_text('\n\n'.join(title+'\n'+words for title,_,words in chapters))
 (OUT/'AI-Gatekeeper-App-Walkthrough-chapters.json').write_text(json.dumps(timings,indent=2))
 print(json.dumps({'duration_seconds':elapsed,'file':str(target)}),flush=True)
