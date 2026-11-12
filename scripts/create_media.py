"""Reproducible narrated overview and edited walkthrough from actual app captures."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess, json, re, textwrap
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1]; WORK=ROOT.parent/'work/media'; OUT=ROOT/'docs'; CAP=ROOT/'docs/captures'
WORK.mkdir(parents=True,exist_ok=True);OUT.mkdir(exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe()
FONT='/System/Library/Fonts/Supplemental/Arial.ttf';BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
NAVY='#18354b';INK='#294a61';MUTED='#6c8494';BG='#f4f7fa';BLUE='#e8f0f6';PURPLE='#eee6f7';TEAL='#e8f3ef'
def font(n,bold=False):return ImageFont.truetype(BOLD if bold else FONT,n)
def wrap(draw,text,x,y,width,size=28,color=INK,bold=False,spacing=10):
    words=text.split();line=''
    for w in words:
        if draw.textlength(line+' '+w,font=font(size,bold))>width and line:
            draw.text((x,y),line,font=font(size,bold),fill=color);y+=size+spacing;line=w
        else:line=(line+' '+w).strip()
    if line:draw.text((x,y),line,font=font(size,bold),fill=color);y+=size+spacing
    return y

def base(title,kicker='AI GATEKEEPER  /  HEALTHCARE',num=''):
    im=Image.new('RGB',(1600,900),BG);d=ImageDraw.Draw(im)
    d.rounded_rectangle((55,50,105,106),radius=13,fill=NAVY);d.text((68,61),'G',font=font(30,True),fill='white')
    d.text((125,67),kicker,font=font(19,True),fill=MUTED)
    wrap(d,title,60,145,1470,52,NAVY,True,10)
    d.line((60,838,1540,838),fill='#dce6ed',width=2)
    d.text((60,859),'Synthetic healthcare demo  |  Human decision authority',font=font(18),fill=MUTED)
    d.text((1470,859),num,font=font(18),fill=MUTED)
    return im,d

def card(d,box,title,body='',fill='white',size=25):
    x,y,x2,y2=box;d.rounded_rectangle(box,radius=15,fill=fill,outline='#d9e4ec',width=2)
    yy=wrap(d,title,x+22,y+20,x2-x-44,size,INK,True,8)
    if body:wrap(d,body,x+22,yy+12,x2-x-44,size-4,MUTED,False,7)
def arrow(d,a,b,color='#82a0b2'):
    d.line((a,b),fill=color,width=4)
    import math
    ang=math.atan2(b[1]-a[1],b[0]-a[0]);tip=[]
    for v in [-.5,.5]:tip.append((b[0]-15*math.cos(ang+v),b[1]-15*math.sin(ang+v)))
    d.polygon([b,*tip],fill=color)
def architecture():
    im,d=base('Architecture that keeps decisions accountable','SOLUTION ARCHITECTURE','02')
    card(d,(60,255,465,370),'Next.js workspace','Intake • Evidence • Review • Audit')
    card(d,(550,255,970,370),'FastAPI action gates','Validation • Persona • Revision checks')
    card(d,(1055,255,1540,370),'Cases and audit store','SQLite • JSON decision export',BLUE)
    arrow(d,(465,310),(550,310));arrow(d,(970,310),(1055,310))
    card(d,(550,435,970,540),'LangGraph orchestrator','Routing • Pause • Resume',BLUE)
    arrow(d,(760,370),(760,435))
    card(d,(60,435,465,540),'Persistent checkpoints','SQLite thread state and interrupts',BLUE)
    arrow(d,(550,487),(465,487))
    card(d,(1055,435,1540,540),'Optional LangSmith','Traces only when configured',PURPLE)
    arrow(d,(970,487),(1055,487))
    for x,t,b in [(60,'Intake and Evidence','inspect_evidence'),(565,'Risk and Controls','lookup_tool • retrieve_policy'),(1070,'Review Preparation','Cited packet • Human handoff')]:
        card(d,(x,615,x+470,755),t,b,TEAL)
        arrow(d,(760,540),(x+235,615))
    d.text((60,788),'Optional MODEL calls: bounded read-only specialist agents. Code enforces policy and approvals.',font=font(23),fill=MUTED)
    im.save(OUT/'architecture.png');return im

def workflow():
    im,d=base('A case can pause without losing its place','WORKFLOW AND RECOVERY','03')
    positions={'intake':(60,280,450,390),'evidence':(60,500,450,625),'risk':(605,280,995,390),'retry':(605,500,995,625),'review':(1150,280,1540,390),'decision':(1150,500,1540,625)}
    card(d,positions['intake'],'1. Inspect evidence','Metadata and version checks',BLUE)
    card(d,positions['evidence'],'Pause for evidence','Attach or revise, then resume',fill='#fff5e3')
    card(d,positions['risk'],'2. Assess risk','Look up tools and map controls',BLUE)
    card(d,positions['retry'],'Pause on tool failure','Two attempts, then explicit retry',fill='#fff5e3')
    card(d,positions['review'],'3. Human review','Verify evidence and sign-offs',TEAL)
    card(d,positions['decision'],'Record the decision','Approve • Reject • Request changes',TEAL)
    arrow(d,(450,335),(605,335));arrow(d,(995,335),(1150,335))
    arrow(d,(255,390),(255,500));arrow(d,(800,390),(800,500));arrow(d,(1345,390),(1345,500))
    d.text((285,430),'missing',font=font(22),fill=MUTED);d.text((830,430),'failure',font=font(22),fill=MUTED)
    d.line([(150,500),(150,445),(90,445),(90,390)],fill='#82a0b2',width=4);arrow(d,(90,445),(90,390))
    d.line([(700,500),(700,445),(640,445),(640,390)],fill='#82a0b2',width=4);arrow(d,(640,445),(640,390))
    d.line([(1345,625),(1345,710),(255,710),(255,625)],fill='#82a0b2',width=4);arrow(d,(255,710),(255,625))
    d.text((560,733),'Changes requested return to evidence and full reassessment.',font=font(24),fill=MUTED)
    im.save(OUT/'workflow.png');return im

ARCH=architecture();FLOW=workflow()
overview=[]
def slide(title,items,idx,narration):
    im,d=base(title,num=f'{idx:02}')
    y=270
    for head,body in items:
        d.ellipse((65,y+7,77,y+19),fill='#54849e')
        yy=wrap(d,head,100,y,1420,31,INK,True)
        y=wrap(d,body,100,yy+5,1380,25,MUTED)+35
    p=WORK/f'overview-{idx}.png';im.save(p);overview.append((p,narration))
slide('Healthcare AI governance, from proposal to review',[
 ('The product','AI Gatekeeper helps teams prepare evidence-based decisions about proposed healthcare AI use cases.'),
 ('The outcome','A versioned case, cited findings, required controls, specialist review routes and a recorded human decision.'),
 ('The boundary','A synthetic local demonstration. It does not make clinical decisions or certify legal compliance.')],1,
 'AI Gatekeeper is a standalone healthcare AI governance application. It helps a business requester move from a proposed AI use case to an evidence based human review. The result is a case with supporting evidence, policy grounded findings, mapped controls and a recorded decision. The fictional organization is Northstar Health. Every patient related example, vendor and policy in this demonstration is synthetic. The application does not make clinical decisions or certify legal compliance.')
overview.append((OUT/'architecture.png','The architecture has three layers. Next.js provides the review workspace. FastAPI validates actions, checks the selected demo persona and prevents stale updates. LangGraph orchestrates the assessment and saves checkpoints in SQLite. Three specialist roles handle intake and evidence, risk and controls, and review preparation. LangChain exposes read only tools for evidence inspection, the approved tools register and exact policy lookup. A separate SQLite store holds cases and human action records. Optional LangSmith tracing can be enabled after credentials are configured.'))
overview.append((OUT/'workflow.png','The workflow branches according to the case. Missing evidence causes an interrupt. The case remains saved until evidence is attached and the user resumes. A failed tools register lookup receives two attempts, then pauses for an explicit retry. Once checks complete, the application prepares findings and a decision packet. Human review is another interrupt. A reviewer can approve, reject or request changes. Requested changes return the case to evidence collection and full reassessment. Approval never follows automatically from an AI recommendation.'))
slide('Two execution modes, with the same hard gates',[
 ('Default demo mode','Real LangGraph workflow and LangChain tools. Rule-based risk assessment. No API keys required.'),
 ('Optional live agent mode','Three model-assisted specialists select bounded read-only tools and generate advisory analysis.'),
 ('Application authority','Evidence requirements, risk thresholds, tool restrictions and human approval remain enforced in code.')],4,
 'The application supports two execution modes. The default is a rule based demonstration that runs real LangGraph state transitions and real local tool calls without API keys. In optional live mode, three specialist agents can choose relevant read only tools and produce advisory analysis. Calls are bounded, and provider failures fall back to the deterministic workflow. The model cannot change risk gates or grant approval. OpenAI and LangSmith paths are implemented but have not been verified with live credentials in this build.')
slide('Three core healthcare journeys',[
 ('Staff policy knowledge assistant','Complete oversight evidence. Low-risk internal scope. Demonstrates a full human approval journey.'),
 ('Patient message drafting','PHI and an external processor. Missing BAA, evaluation and monitoring evidence cause a pause.'),
 ('Discharge instruction drafting','Clinical and patient-facing scope. A simulated tools register outage demonstrates recovery.')],5,
 'Three journeys make the demo easy to follow. The staff policy assistant has complete oversight evidence and a bounded internal scope. It demonstrates an end to end approval. Patient message drafting handles protected health information through an external processor. The workflow identifies missing contractual, evaluation and monitoring evidence, then resumes after attachment. Discharge instruction drafting includes clinical and patient facing scope. A deliberate tools register outage demonstrates failed attempts, saved state and recovery. The resulting review route includes clinical safety, privacy and governance. These requirements come from the fictional internal policy catalog.')
slide('Additional scenarios test the boundaries',[
 ('Clinical note summarization','Reported vendor contradictions require reconciliation evidence and specialist review.'),
 ('Research cohort exploration','A de-identification claim needs a documented method with the matching system version.'),
 ('Autonomous prescribing','Unapproved tooling and prohibited autonomous scope cannot receive approval in this demo.')],6,
 'Three additional cases test important boundaries. Clinical note summarization begins with a reported conflict in vendor terms, requiring reconciliation evidence. Research cohort exploration requires a documented de identification method. A report for the wrong system version does not satisfy the check. Autonomous prescribing is deliberately outside the permitted demonstration scope. Even a reviewer cannot approve a case with mandatory blockers. Evidence presence alone is never treated as proof of compliance. A human must evaluate the content and attest the required specialist reviews.')
slide('What the validation demonstrates',[
 ('12 automated tests passed','Approval gates, evidence gaps, stale revisions, wrong versions, tool failures, recovery and exports.'),
 ('Live browser checks completed','Approval, missing evidence and retry journeys were exercised in the running local application.'),
 ('Production work remains','Authenticated roles, independent sign-offs, hardened storage, audit integrity and deployment review.')],7,
 'Twelve automated tests pass. They cover approval boundaries, missing and wrong version evidence, conflict review, change requests, durable checkpoints, tool failure recovery, auditor restrictions, stale revisions and exports. The main journeys were also exercised in the running browser. This is a local portfolio demonstration, not a production healthcare system. Before deployment, replace persona switching with authentication, add independently recorded specialist approvals, harden storage and uploads, and complete security and operational review. The project source and setup instructions are in the private AI Gatekeeper GitHub repository.')

walk=[
 ('01-overview.png','Workspace overview','This walkthrough uses edited captures from the running local application. The dashboard shows six synthetic healthcare cases, current review status and the three stage governance workflow. The selected persona controls which demonstration actions are available. The current mode is rule based; no live model or LangSmith session is claimed.'),
 ('02-intake.png','Journey 1  |  Run an assessment','We open the staff policy knowledge assistant. The submission declares internal data, a named owner and an approved tool. Clicking Run assessment starts the saved LangGraph workflow. The application checks the evidence inventory before moving to tool lookup and risk assessment.'),
 ('04-tools.png','Real tool calls and workflow events','The Activity tab shows the actual execution trace. Evidence inspection found the required oversight document. The lookup tool returned Northstar Assist as approved. The risk role mapped the internal use case to its policy and controls. Review preparation then paused for a human decision. These are observed local workflow events, not invented model reasoning.'),
 ('05-human-review.png','Human verification and approval','We switch to Governance Reviewer. The reviewer verifies the oversight evidence, attests the governance sign off and enters a meaningful rationale. The backend checks these requirements again. A business requester or auditor cannot submit an approval through the API.'),
 ('06-approved.png','Decision recorded','The approval is recorded with its rationale and time. It applies to the proposed scope in this synthetic demo. It does not deploy the system. The decision packet can be exported as JSON with the case, findings, evidence, source version and audit entries.'),
 ('07-missing-evidence.png','Journey 2  |  Pause for missing evidence','The patient message drafting case takes a different path. Protected health information, external processing and patient facing outputs trigger additional requirements. The workflow pauses because BAA, evaluation and monitoring evidence are missing. The case stays saved while the requester gathers the material.'),
 ('08-evidence-workspace.png','Evidence workspace','The evidence workspace separates present and missing evidence kinds. Each record includes an author, document date and applicable system version. We use the explicitly labeled Add demo evidence action to attach synthetic fixtures. In a normal demonstration, the requester can also paste a fictional evidence excerpt into the attachment form.'),
 ('09-resumed.png','Resume the same case','Resuming rechecks completeness and proceeds to the risk assessment. This case is now high risk and routes to AI Governance, Privacy and Security or Vendor Risk. Adding evidence does not approve the case. The human review gate still applies.'),
 ('10-policy-citation.png','Inspect a policy source','Each substantive finding links to a versioned policy clause. Opening the citation shows the exact fictional policy used by the workflow. Public healthcare references are background material. The application does not interpret a submitted document as proof of legal compliance.'),
 ('12-failed-attempts.png','Journey 3  |  Tool failure','Discharge instruction drafting demonstrates recovery. Its evidence is complete, but the tools register is deliberately unavailable. The trace shows two failed attempts. The workflow stops at an interrupt instead of treating the missing register result as an approval.'),
 ('14-recovery-trace.png','Recover without losing prior events','An explicit retry clears the demonstration outage. The same case resumes, successfully looks up the tool and maps the clinical risks. Earlier failures remain visible alongside the recovery. The checkpoint mechanism preserves progress; it does not erase unsuccessful attempts.'),
 ('16-audit.png','Traceable actions and remaining boundaries','The audit view records assessment runs, evidence attachments, resumes and the human decision. These are local application records, not a tamper proof audit service. The optional live mode adds bounded model selected tool calls and can export traces to LangSmith once configured. The tested demonstration shown here uses local rules and tools, with human decision authority throughout.')
]
walk_segments=[]
for i,(name,title,narration) in enumerate(walk,1):
    im=Image.new('RGB',(1600,1000),NAVY);d=ImageDraw.Draw(im)
    d.text((40,24),'AI GATEKEEPER  /  RECORDED APP WALKTHROUGH',font=font(18,True),fill='#c4d6e2')
    d.text((40,61),title,font=font(34,True),fill='white')
    screenshot=Image.open(CAP/name).convert('RGB').resize((1600,900))
    # Keep full app viewport; title and footer are outside the capture.
    im=Image.new('RGB',(1600,1080),NAVY);im.paste(screenshot,(0,130));d=ImageDraw.Draw(im)
    d.text((40,25),'AI GATEKEEPER  /  RECORDED APP WALKTHROUGH',font=font(18,True),fill='#c4d6e2');d.text((40,64),title,font=font(34,True),fill='white')
    d.text((40,1046),'Actual local app states • Edited screen captures • Synthetic data • Rule-based mode',font=font(20),fill='#c4d6e2')
    p=WORK/f'walk-{i}.png';im.save(p);walk_segments.append((p,narration))

def render_video(name,segments):
    paths=[];transcript=[];elapsed=0;chapters=[]
    for i,(img,text) in enumerate(segments):
        txt=WORK/f'{name}-{i}.txt';audio=WORK/f'{name}-{i}.mp3';mp4=WORK/f'{name}-{i}.mp4';txt.write_text(text)
        subprocess.run([__import__('sys').executable,'-m','edge_tts','--voice','en-US-JennyNeural','--rate=+5%','--file',str(txt),'--write-media',str(audio)],check=True)
        probe=subprocess.run([FF,'-i',str(audio)],capture_output=True,text=True).stderr
        m=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',probe);duration=int(m[1])*3600+int(m[2])*60+float(m[3])+0.7
        chapters.append({'start_seconds':round(elapsed,2),'duration_seconds':round(duration,2),'image':img.name})
        elapsed+=duration
        subprocess.run([FF,'-y','-loglevel','error','-loop','1','-i',str(img),'-i',str(audio),'-vf','scale=1600:900:force_original_aspect_ratio=decrease,pad=1600:900:(ow-iw)/2:(oh-ih)/2:color=0x18354b,format=yuv420p','-c:v','libx264','-preset','ultrafast','-tune','stillimage','-crf','20','-r','24','-c:a','aac','-b:a','128k','-af','apad','-t',str(duration),str(mp4)],check=True)
        paths.append(mp4);transcript.append(text)
    listing=WORK/f'{name}-concat.txt';listing.write_text(''.join(f"file '{p}'\n" for p in paths))
    output=OUT/f'{name}.mp4'
    subprocess.run([FF,'-y','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(output)],check=True)
    (OUT/f'{name}-transcript.txt').write_text('\n\n'.join(transcript))
    (OUT/f'{name}-chapters.json').write_text(json.dumps(chapters,indent=2))
    print(json.dumps({'file':str(output),'seconds':round(elapsed,1),'bytes':output.stat().st_size}),flush=True)

if __name__=='__main__':
    render_video('AI-Gatekeeper-Product-Architecture-Overview',overview)
    render_video('AI-Gatekeeper-App-Walkthrough',walk_segments)
