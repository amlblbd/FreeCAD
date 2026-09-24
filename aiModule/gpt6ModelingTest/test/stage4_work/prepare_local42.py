from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work')
s=(p/'extract_dense.py').read_text(encoding='utf-8-sig').replace('reference_inner_skin.brep','reference_inner_complete.brep').replace('heights=[5,10,12,14,18,22,28,36,42,44,44.8,44.9,46,47.3,47.5,49,51,53,57,60,65,70,600,602,604]','heights=[42.2,42.35,42.39,42.6,43,43.5]').replace('dense_raw.json','local42_raw.json').replace('dense_error.txt','local42_error.txt')
(p/'extract_local42.py').write_text(s,encoding='utf-8')
s=(p/'fit_dense.py').read_text(encoding='utf-8-sig').replace('dense_raw.json','local42_raw.json').replace('_profiles_before_dense.json','_profiles_before_local42.json').replace('dense_fit_audit.json','local42_fit_audit.json')
(p/'fit_local42.py').write_text(s,encoding='utf-8')
