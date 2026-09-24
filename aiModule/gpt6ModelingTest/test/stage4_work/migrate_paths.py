from pathlib import Path
import shutil,json,hashlib,zipfile
old=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest');root=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest');test=root/'test';work=test/'stage4_work';work.mkdir(exist_ok=True)
rows=[]
for f in old.rglob('*'):
 if not f.is_file():continue
 g=root/f.relative_to(old);a=f.read_bytes();b=g.read_bytes()
 rows.append(dict(path=f.relative_to(old).as_posix(),old_bytes=len(a),new_bytes=len(b),binary_equal=a==b,text_equal_after_newline_normalization=a.replace(b'\r\n',b'\n')==b.replace(b'\r\n',b'\n')))
source=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work')
for f in source.iterdir():
 if f.is_file():shutil.copy2(f,work/f.name)
for stage,names in [('stage3',['smooth_fitted.json','compatible_profiles.json','smooth_outer.brep']),('stage2',['faces.json','fitted_sections.json'])]:
 target=work/'inputs'/stage;target.mkdir(parents=True,exist_ok=True)
 for name in names:shutil.copy2(Path('D:/freecad/FreeCAD/build/bpillar_'+stage)/name,target/name)
replacements={
 'D:/freecad/FreeCAD/aiModule/gpt6ModelingTest':root.as_posix(),
 'D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test':test.as_posix(),
 'D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work':work.as_posix(),
 'D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work/inputs/stage3':(work/'inputs'/'stage3').as_posix(),
 'D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work/inputs/stage2':(work/'inputs'/'stage2').as_posix(),
 'D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work':work.as_posix(),
 'D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work/inputs/stage3':(work/'inputs'/'stage3').as_posix(),
 'D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work/inputs/stage2':(work/'inputs'/'stage2').as_posix(),
}
updated=[]
for f in work.iterdir():
 if f.suffix.lower() not in ['.py','.fcmacro']:continue
 s=f.read_text(encoding='utf-8-sig');before=s
 # Retain comparison/audit scripts as historical records.
 if f.name in ['path_compare.py','check_document_paths.py']:continue
 for a,b in replacements.items():s=s.replace(a,b)
 if s!=before:f.write_text(s,encoding='utf-8');updated.append(f.name)
back=work/'migration_backup';back.mkdir(exist_ok=True);docs=[]
for f in test.glob('*.FCStd'):
 with zipfile.ZipFile(f) as z:
  xml=z.read('Document.xml');newxml=xml.replace(str(old).encode('utf-8'),str(root).encode('utf-8'))
  if newxml==xml:continue
  shutil.copy2(f,back/f.name);temp=f.with_suffix('.migration_tmp')
  with zipfile.ZipFile(temp,'w') as dst:
   dst.comment=z.comment
   for item in z.infolist():dst.writestr(item,newxml if item.filename=='Document.xml' else z.read(item.filename))
 temp.replace(f);docs.append(f.name)
report=dict(old_root=str(old),new_root=str(root),old_file_count=len(rows),new_original_file_count=len(rows),comparison_before_migration=rows,updated_scripts=updated,source_metadata_updated_documents=docs,working_directory=str(work),status='Stage 4 in progress; experimental solids are not validated deliverables.')
(test/'路径迁移核对.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(work/'README.md').write_text('''# 阶段4工作目录\n\n当前阶段4尚未完成，目录内 solid_test.brep 等均为试算，不是交付实体。\n\n- 参考件：../../model/B pillar trim lower-0612.step（从本目录实际使用 ../../model 需改为 ../../model 的上一级；脚本使用绝对新路径）。\n- 当前基准文档：../B_pillar_stage3.FCStd。\n- 后续最终文档、宏与报告保存到上一级 test 目录。\n- 壁厚实测：125 个有效法向点均约 2.500 mm。\n- 直接偏置未通过增强检查，正在分别构建内外表面。\n- reference_normals.py 已修正 distToShape 支撑索引为零起始，最新 reference_normals.json 已完成计算；下一步运行 refnormal_solid.py，用最新法向重建并复核。\n- tabs.json：四个耳部平面壁板已通过增强检查，两处矩形开口保留在面模板中。\n- migration_backup 保留迁移前阶段1、2、3文档；新目录文档仅更新 ReferenceSTEP.SourceFile，几何数据未改。\n'''.replace('参考件：../../model/B pillar trim lower-0612.step（从本目录实际使用 ../../model 需改为 ../../model 的上一级；脚本使用绝对新路径）。','参考件：../../model/B pillar trim lower-0612.step。'),encoding='utf-8')
print(json.dumps(dict(copied_work_files=len(list(source.iterdir())),updated_scripts=len(updated),updated_documents=docs),ensure_ascii=True))
