from pathlib import Path
import re
from html.parser import HTMLParser
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
ROOT=Path(__file__).resolve().parents[1]
doc=Document();sec=doc.sections[0]
sec.top_margin=sec.bottom_margin=Inches(.7);sec.left_margin=sec.right_margin=Inches(.7)
sec.page_width=Inches(8.5);sec.page_height=Inches(11)
for name in ('Normal','Title','Subtitle','Heading 1','Heading 2'):
 st=doc.styles[name];st.font.name='Calibri';st.font.color.rgb=RGBColor(0,0,0)
doc.styles['Normal'].font.size=Pt(11)
doc.styles['Normal'].paragraph_format.space_after=Pt(7)
doc.styles['Normal'].paragraph_format.line_spacing=1.08
for name,size in [('Title',28),('Heading 1',21),('Heading 2',14)]:
 doc.styles[name].font.size=Pt(size)
 doc.styles[name].paragraph_format.keep_with_next=True
class Rich(HTMLParser):
 def __init__(self,para):super().__init__();self.para=para;self.bold=False;self.url=None
 def handle_starttag(self,tag,attrs):
  if tag=='b':self.bold=True
  elif tag=='br':self.para.add_run().add_break()
  elif tag=='link':self.url=dict(attrs).get('href')
 def handle_endtag(self,tag):
  if tag=='b':self.bold=False
  elif tag=='link':
   if self.url:self.para.add_run(' ('+self.url+')')
   self.url=None
 def handle_data(self,data):self.para.add_run(data).bold=self.bold

def p(text,sty='Body'):
 style='Title' if sty=='DocTitle' else 'Heading 2' if sty=='Heading2' else 'Normal'
 if sty=='DocTitle':text='AI Gatekeeper Solution Document'
 para=doc.add_paragraph(style=style);Rich(para).feed(text)
 if sty=='SmallBody':
  for run in para.runs:run.font.size=Pt(10)
 return para

def h(text):doc.add_heading(text,2)
def page(title,kicker):
 para=doc.add_heading(re.sub('[^A-Za-z0-9 ]',' ',title),1)
 para.paragraph_format.page_break_before=True

def table(headers,rows,widths):
 t=doc.add_table(rows=1,cols=len(headers));t.autofit=False
 for cell,w in zip(t.rows[0].cells,widths):cell.width=Inches(7.1*w/sum(widths))
 for col,w in zip(t.columns,widths):col.width=Inches(7.1*w/sum(widths))
 for idx,values in enumerate([headers]+rows):
  row=t.rows[0] if idx==0 else t.add_row()
  pr=row._tr.get_or_add_trPr();pr.append(OxmlElement('w:cantSplit'))
  if idx==0:pr.append(OxmlElement('w:tblHeader'))
  for cell,value in zip(row.cells,values):
   cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   para=cell.paragraphs[0];para.paragraph_format.space_after=Pt(3);para.paragraph_format.space_before=Pt(3);para.paragraph_format.line_spacing=1.04
   Rich(para).feed(str(value))
   for run in para.runs:run.font.size=Pt(10);run.bold=idx==0
   props=cell._tc.get_or_add_tcPr();shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E8F0F6' if idx==0 else 'F7F9FB' if idx%2==0 else 'FFFFFF');props.append(shade)
   margins=OxmlElement('w:tcMar')
   for edge in ('top','bottom','left','right'):
    item=OxmlElement('w:'+edge);item.set(qn('w:w'),'90');item.set(qn('w:type'),'dxa');margins.append(item)
   props.append(margins)
 borders=OxmlElement('w:tblBorders')
 for edge in ('top','bottom','left','right','insideH','insideV'):
  el=OxmlElement('w:'+edge);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'D9D9D9');borders.append(el)
 t._tbl.tblPr.append(borders)
 doc.add_paragraph().paragraph_format.space_after=Pt(2)
def diagram(name):doc.add_picture(str(ROOT/'docs'/name),width=Inches(5.6))
source=(ROOT/'scripts/create_solution.py').read_text()
body=source[source.index("p('WEEK 3 PROJECT"):source.index('\ndef footer(')]
exec(body)
foot=sec.footer.paragraphs[0];foot.text='AI Gatekeeper | Healthcare solution document | '
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');foot._p.append(fld)
for run in foot.runs:run.font.size=Pt(9)
for style in doc.styles:
 if style.type==1:
  pp=style.element.find(qn('w:pPr'))
  if pp is not None:
   for border in list(pp.findall(qn('w:pBdr'))):pp.remove(border)
for para in doc.paragraphs:
 pp=para._p.find(qn('w:pPr'))
 if pp is not None:
  for border in list(pp.findall(qn('w:pBdr'))):pp.remove(border)
doc.core_properties.title='AI Gatekeeper Solution Document';doc.core_properties.subject='Healthcare AI governance architecture workflows and local demonstration';doc.core_properties.author='AI Gatekeeper Project'
out=ROOT/'docs/AI-Gatekeeper-Solution-Document.docx';doc.save(out);print(out)
