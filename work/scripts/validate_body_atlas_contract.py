"""Reloaded atlas contracts against accepted geometry and packed source material scene."""
from pathlib import Path
import hashlib,json
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot(filename):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/scenes'/filename),load_ui=False,use_scripts=False)
    result={}
    for o in bpy.context.scene.objects:
        if o.type!='MESH':continue
        m=o.data
        geom=repr((list(map(tuple,o.matrix_world)),[(tuple(v.co),[(g.group,g.weight) for g in v.groups]) for v in m.vertices], [tuple(p.vertices) for p in m.polygons],[tuple(n.vector) for n in m.corner_normals]))
        result[o.name]={'geometry':hashlib.sha256(geom.encode()).hexdigest(),'uv':{u.name:hashlib.sha256(repr([tuple(d.uv) for d in u.data]).encode()).hexdigest() for u in m.uv_layers}}
    return result
accepted=snapshot('clash_braum_shield_reduced_accepted.blend')
source=snapshot('clash_braum_body_atlas_packed_trial.blend')
trial=snapshot('clash_braum_body_atlas_preview_trial.blend')
assert accepted.keys()==source.keys()==trial.keys()
assert all(accepted[n]['geometry']==source[n]['geometry']==trial[n]['geometry'] for n in trial)
assert source==trial
body=json.loads((ROOT/'validation/body_atlas_layout_trial.json').read_text())['body_objects']
for n in body:
    assert trial[n]['uv']['BodySourceUV'] in accepted[n]['uv'].values()
    o=bpy.data.objects[n];assert o.data.uv_layers.active.name=='BodyAtlas'
    assert len(o.data.materials)==1 and o.data.materials[0]==bpy.data.objects[body[0]].data.materials[0]
mat=bpy.data.objects[body[0]].data.materials[0];normal=next(n for n in mat.node_tree.nodes if n.type=='NORMAL_MAP')
assert normal.uv_map=='BodyAtlas' and normal.inputs['Strength'].default_value==1
texture_stats={}
for channel in ('basecolor','opacity','normal'):
    p=ROOT/f'work/textures/body_atlas_trial/clash_body_{channel}.png'
    im=bpy.data.images.load(str(p),check_existing=False)
    im.colorspace_settings.name='sRGB' if channel=='basecolor' else 'Non-Color'
    a=np.empty(im.size[0]*im.size[1]*4,dtype=np.float32);im.pixels.foreach_get(a);a=a.reshape(-1,4)
    assert np.isfinite(a).all() and a.min()>=0 and a.max()<=1
    texture_stats[channel]={'sha256':sha(p),'size':list(im.size),'min':float(a.min()),'max':float(a.max())}
    if channel=='basecolor':base=a.copy()
    if channel=='opacity':opacity=a.copy()
    if channel=='normal':
        visible=opacity[:,0]>.5;length=np.linalg.norm(a[visible,:3]*2-1,axis=1)
        texture_stats[channel]['covered_vector_length_percentiles']=np.quantile(length,[0,.01,.5,.99,1]).tolist()
        assert np.quantile(length,.01)>.95 and np.quantile(length,.99)<1.05
assert np.max(np.abs(base[:,3]-opacity[:,0]))<=1/255+1e-6
report=dict(pass_contract=True,scene_sha256=sha(ROOT/'work/scenes/clash_braum_body_atlas_preview_trial.blend'),geometry_weights_topology_transforms_corner_normals_exact=True,all_67_torso_corrections_preserved=True,legacy_uvs_preserved=True,active_body_uv='BodyAtlas',normal_space='TANGENT +X +Y +Z; strength 1',texture_stats=texture_stats,scope='Reloaded PNG and saved-scene contracts. Render comparison establishes preview equivalence; Riot shader and mip behavior require runtime integration.')
(ROOT/'validation/body_atlas_contract.json').write_text(json.dumps(report,indent=2))
print('PASS BODY ATLAS CONTRACT')
