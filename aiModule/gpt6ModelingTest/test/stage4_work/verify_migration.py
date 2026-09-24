from pathlib import Path
import zipfile,json
root=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test');back=root/'stage4_work/migration_backup';out=[]
for b in back.glob('*.FCStd'):
 with zipfile.ZipFile(b) as old,zipfile.ZipFile(root/b.name) as new:
  changed=[name for name in old.namelist() if old.read(name)!=new.read(name)]
  assert changed==['Document.xml'],changed
  out.append(dict(file=b.name,changed_entries=changed,all_geometry_and_view_data_identical=True))
(root/'stage4_work/migration_integrity.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
