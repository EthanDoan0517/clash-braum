"""Map all-frame local collision regressions to existing source components."""
from pathlib import Path
import json
import bpy

ROOT=Path(__file__).resolve().parents[2]
audit=json.loads((ROOT/'validation/torso_outline_recovery_audit.json').read_text())
regions=json.loads((ROOT/'validation/rig_regions.json').read_text())['objects']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/scenes/clash_braum_torso.blend'),load_ui=False,use_scripts=False)
mapping={}
for name,components in regions.items():
    mapping[name]={i:c['id'] for c in components for i in c['indices']}
targets={('Object002',pair[0]) for row in audit['new_intersection_frame_details'] for pair in row['new_local_intersections']}
targets.update((pair[1],pair[2]) for row in audit['new_intersection_frame_details'] for pair in row['new_local_intersections'])
rows=[]
for name,index in sorted(targets):
    obj=bpy.data.objects[name];face=obj.data.polygons[index]
    vertices=[]
    for i in face.vertices:
        v=obj.data.vertices[i]
        vertices.append({'index':i,'rest':list(v.co),'weights':{obj.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0}})
    rows.append({'object':name,'polygon':index,'component_ids':sorted({mapping[name][i] for i in face.vertices}),'vertices':vertices})
report={'scene_sha256':audit['parent_scene_sha256'],'status':'Read-only mapping; no topology or weights changed','polygons':rows}
(ROOT/'validation/torso_outline_failure_geometry.json').write_text(json.dumps(report,indent=2))
print({name:sorted({c for r in rows if r['object']==name for c in r['component_ids']}) for name in sorted({r['object'] for r in rows})})
