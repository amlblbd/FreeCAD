from pathlib import Path
import json
old=Path('D:/freecad/b柱设计资料');new=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest');rows=[]
for f in old.rglob('*'):
 if not f.is_file():continue
 g=new/f.relative_to(old);a=f.read_bytes();b=g.read_bytes()
 if a!=b:rows.append(dict(path=f.relative_to(old).as_posix(),old_bytes=len(a),new_bytes=len(b),only_line_endings=a.replace(b'\r\n',b'\n')==b.replace(b'\r\n',b'\n')))
print(json.dumps(rows,ensure_ascii=False,indent=2))
