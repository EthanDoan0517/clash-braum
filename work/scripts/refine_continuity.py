"""Continue the refined rig with anatomical cloth fields and cuff continuity.

The imported skeleton, actions, topology, UVs, authored digits and original
checkpoint remain unchanged. No pose-specific corrections are baked into ANMs.
"""
from pathlib import Path
import sys, json, hashlib
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'work/tools'), str(ROOT/'work/scripts')]
from native_export import assert_native_rig

SOURCE = ROOT/'work/scenes/clash_braum_rig_refined.blend'
TARGET = ROOT/'work/scenes/clash_braum_continuity.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False, use_scripts=False)
rig = bpy.data.objects['Braum_Native']
regions = json.loads((ROOT/'validation/rig_regions.json').read_text())
report = json.loads((ROOT/'validation/rig_refinement.json').read_text())
report.update(input=str(SOURCE.relative_to(ROOT)), input_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              output=str(TARGET.relative_to(ROOT)), continuity_edits=[],
              status='Stage 3 anatomical continuity revision; contact and visual review tracked separately')

def smooth(a, b, value):
    t = max(0., min(1., (value-a)/(b-a)))
    return t*t*(3.-2.*t)

def weights_of(obj, vertex):
    return {obj.vertex_groups[g.group].name: g.weight for g in vertex.groups if g.weight > 0}

def set_weights(obj, index, weights):
    weights = {n: w for n, w in weights.items() if w > 1e-6}
    assert 0 < len(weights) <= 4, weights
    total = sum(weights.values())
    for g in list(obj.data.vertices[index].groups):
        obj.vertex_groups[g.group].remove([index])
    for name, w in weights.items():
        obj.vertex_groups[name].add([index], w/total, 'REPLACE')

def mix(a, b, factor):
    result = {n: a.get(n, 0)*(1-factor)+b.get(n, 0)*factor for n in a.keys() | b.keys()}
    return dict(sorted(result.items(), key=lambda row: -row[1])[:4])

def shell_ids(name, cid):
    return next(c['indices'] for c in regions['objects'][name] if c['id'] == cid)

def torso(p):
    # Body-height field excludes stock armor/shoulder helpers from the vest.
    anchors = [(1.08, 'Root'), (1.20, 'Spine1'), (1.35, 'Spine2'), (1.48, 'Spine3')]
    if p.z <= anchors[0][0]:
        return {'Root': 1.}
    for (a, na), (b, nb) in zip(anchors, anchors[1:]):
        if p.z <= b:
            t = smooth(a, b, p.z)
            return {na: 1-t, nb: t}
    return {'Spine3': 1.}

def arm(p, side):
    shoulder, elbow, wrist = [rig.data.bones[side+'_'+n].head_local for n in ['Shoulder', 'Elbow', 'Hand']]
    upper = (p-shoulder).dot(elbow-shoulder)/(elbow-shoulder).length_squared
    lower = (p-elbow).dot(wrist-elbow)/(wrist-elbow).length_squared
    elbow_weight = smooth(.45, 1.40, upper)
    hand = smooth(.58, 1.02, lower)
    twist = .35*smooth(.08, .48, lower)*(1-hand)
    weights = {side+'_Shoulder': 1-elbow_weight,
               side+'_Elbow': elbow_weight*(1-hand-twist),
               side+'_Hand_Twist': elbow_weight*twist,
               side+'_Hand': elbow_weight*hand}
    # Shared torso-to-sleeve field across upper arm and armpit surfaces.
    attachment = smooth(.14, .34, abs(p.x))*smooth(1.20, 1.42, p.z)
    # Distal arm vertices must stay fully attached even below the chest gate.
    attachment = max(attachment, smooth(.30, .43, abs(p.x)))
    clavicle = .55*smooth(.10, .24, abs(p.x))*smooth(1.42, 1.60, p.z)
    chest = mix(torso(p), {side+'_Clavicle': 1.}, clavicle)
    return mix(chest, weights, attachment)

def pants(p, old):
    hip = 1-smooth(.81, 1.04, p.z)
    left = smooth(-.045, .045, p.x)
    waist = smooth(.98, 1.10, p.z)
    desired = {'L_Hip': hip*left, 'R_Hip': hip*(1-left),
               'Pelvis': (1-hip)*(1-waist), 'Root': (1-hip)*waist}
    return mix(old, desired, smooth(.72, .80, p.z))

def edit_shell(name, cid, field, description):
    obj = bpy.data.objects[name]
    ids = shell_ids(name, cid)
    changed = 0
    for index in ids:
        v = obj.data.vertices[index]
        old = weights_of(obj, v)
        new = field(v.co, old)
        if max(abs(old.get(n, 0)-new.get(n, 0)) for n in old.keys() | new.keys()) > 1e-6:
            set_weights(obj, index, new)
            changed += 1
    obj.data.update()
    report['continuity_edits'].append({'object': name, 'component': cid, 'vertices_changed': changed, 'method': description})

edit_shell('Object001', 0, pants, 'Anatomical pelvis/hip/waist field above knee; remove transferred upper-spine seat weights')
edit_shell('Object002', 0, lambda p, w: arm(p, 'L' if p.x >= 0 else 'R'), 'Continuous spine/clavicle/armhole field shared with sleeves; exclude animated shoulder armor helpers')
# Small center collar insert follows the same upper vest attachment.
edit_shell('Object002', 1661, lambda p, w: {'Spine3': 1.}, 'Keep collar insert attached to the existing Spine3 collar')
for name, shells in {'Object004': [(0, 'R'), (12, 'R'), (217, 'L'), (253, 'L')],
                     'Object009': [(652, 'R'), (810, 'L')]}.items():
    for cid, side in shells:
        edit_shell(name, cid, lambda p, w, side=side: arm(p, side), 'Shared anatomical shoulder/elbow/twist/wrist field across cloth and exposed forearm')

for cid, side in [(865, 'R'), (2539, 'L')]:
    def cuff(p, old, side=side):
        # Preserve the existing glove digit/palm fit. Only replace proximal cuff
        # vertices; all exposed digit shells are outside this component.
        elbow, wrist = [rig.data.bones[side+'_'+n].head_local for n in ['Elbow', 'Hand']]
        t = (p-elbow).dot(wrist-elbow)/(wrist-elbow).length_squared
        return mix(arm(p, side), old, smooth(.98, 1.12, t))
    edit_shell('Object004', cid, cuff, 'Blend proximal glove cuff into the same forearm field; retain palm/digit weights')

for name, cid, bone in [('Object006', 1366, 'Root'), ('Object006', 1400, 'Root'),
                        ('Object007', 2611, 'Spine3'), ('Object007', 2583, 'Spine3')]:
    edit_shell(name, cid, lambda p, w, bone=bone: {bone: 1.}, 'Attach belt/center vest hardware consistently with adjacent authored equipment')
    report['rigid_components'].append({'object': name, 'component': cid, 'bone': bone, 'vertices': len(shell_ids(name, cid))})

assert_native_rig(rig)
rig.animation_data.action = bpy.data.actions['braum_idle_01_loop']
rig.animation_data.action_slot = rig.animation_data.action.slots[0]
bpy.context.scene.frame_set(17)
bpy.context.scene['stage'] = report['status']
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
report['output_sha256'] = hashlib.sha256(TARGET.read_bytes()).hexdigest()
(ROOT/'validation/rig_continuity.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report['continuity_edits'], indent=2))
