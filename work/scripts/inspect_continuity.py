"""Read the current checkpoint's anatomical shells and native motion deltas."""
from pathlib import Path
import json
import bpy
ROOT = Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/scenes/clash_braum_rig_refined.blend'), load_ui=False, use_scripts=False)
rig = bpy.data.objects['Braum_Native']
regions = json.loads((ROOT/'validation/rig_regions.json').read_text())
names = ['Root', 'Pelvis', 'Spine1', 'Spine2', 'Spine3', 'L_Clavicle', 'L_Shoulder', 'L_Elbow', 'L_Hand_Twist', 'L_Hand', 'L_Hip', 'L_KneeUpper', 'L_KneeLower']
report = {'bones': {n: {'head': list(rig.data.bones[n].head_local), 'tail': list(rig.data.bones[n].tail_local), 'parent': rig.data.bones[n].parent.name if rig.data.bones[n].parent else None} for n in names}, 'shells': {}, 'poses': {}}
for name in ['Object001', 'Object002', 'Object004', 'Object006', 'Object007', 'Object009']:
    obj = bpy.data.objects[name]
    rows = []
    for shell in regions['objects'][name]:
        if shell['vertices'] < 70 and shell['id'] != 2611:
            continue
        weights = {}
        for i in shell['indices']:
            for g in obj.data.vertices[i].groups:
                key = obj.vertex_groups[g.group].name
                weights[key] = weights.get(key, 0) + g.weight / len(shell['indices'])
        rows.append({'id': shell['id'], 'vertices': shell['vertices'], 'bounds': shell['bounds'], 'weights': {k: round(v, 3) for k, v in weights.items() if v > .005}})
    report['shells'][name] = rows
for clip, frame in [('braum_recall', 65), ('braum_dance_loop', 50)]:
    action = bpy.data.actions[clip]
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    bpy.context.scene.frame_set(frame)
    report['poses'][clip] = {n: {'head': list(rig.pose.bones[n].head), 'scale': list(rig.pose.bones[n].scale)} for n in names}
(ROOT/'validation/continuity_inspection.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
