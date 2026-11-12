from pathlib import Path
import subprocess,json,re
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs';ff=imageio_ffmpeg.get_ffmpeg_exe()
for name in ('AI-Gatekeeper-Product-Architecture-Overview','AI-Gatekeeper-App-Walkthrough'):
 p=OUT/(name+'.mp4');meta=OUT/(name+'-chapters.json');chap=json.loads(meta.read_text());seconds=sum(c['duration_seconds'] for c in chap)
 if seconds>295:
  speed=seconds/295;tmp=OUT/(name+'-paced.mp4')
  subprocess.run([ff,'-y','-loglevel','error','-i',str(p),'-vf',f'setpts=PTS/{speed}','-af',f'atempo={speed}','-c:v','libx264','-preset','ultrafast','-crf','20','-r','24','-c:a','aac','-b:a','128k','-movflags','+faststart',str(tmp)],check=True)
  tmp.replace(p)
  for c in chap:c['start_seconds']=round(c['start_seconds']/speed,2);c['duration_seconds']=round(c['duration_seconds']/speed,2)
  meta.write_text(json.dumps(chap,indent=2))
 subprocess.run([ff,'-v','error','-i',str(p),'-f','null','-'],check=True)
 probe=subprocess.run([ff,'-i',str(p)],capture_output=True,text=True).stderr
 print(name,re.search(r'Duration: ([^,]+)',probe)[1],p.stat().st_size,flush=True)
readme=ROOT/'README.md';s=readme.read_text().replace('(4:24)','(revised business overview)').replace('(3:54)','(revised feature tour and three use case demonstrations)')
s=s.replace('- [Solution document](docs/AI-Gatekeeper-Solution-Document.pdf)','- [Solution document in Word](docs/AI-Gatekeeper-Solution-Document.docx)\n- [Solution document in PDF](docs/AI-Gatekeeper-Solution-Document.pdf)')
s+='\nThe revised product video begins with business context and constraints, explains the ReAct-style live-agent design, maps models/tools/internal and external data, and connects technology layers to validation use cases. The revised walkthrough shows a fresh interactive session with the larger-font UI, edited into action/result sequences. Both distinguish tested rule-based workflow behavior from unverified live model integrations.\n'
readme.write_text(s)
