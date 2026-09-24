from pathlib import Path
import zipfile,xml.etree.ElementTree as E,json
root=Path('aiModule/gpt6ModelingTest/test');out=[]
for f in root.glob('*.FCStd'):
 with zipfile.ZipFile(f) as z:
  tree=E.fromstring(z.read('Document.xml'))
  for obj in tree.findall('.//ObjectData/Object'):
   for prop in obj.findall('./Properties/Property'):
    if any('b柱设计资料' in str(v) or 'bpillar_stage' in str(v) for e in prop.iter() for v in e.attrib.values()):out.append(dict(file=f.name,object=obj.get('name'),property=prop.get('name'),values=[e.attrib for e in prop if e.attrib]))
print(json.dumps(out,ensure_ascii=True,indent=2))
