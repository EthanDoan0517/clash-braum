"""Promote only the reviewed, UV-checked and export-verified shield child."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[2]
def read(name):return json.loads((ROOT/'validation'/name).read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
geometry=read('shield_surface_v2_trial.json');uv=read('shield_atlas_trial.json');check=read('shield_atlas_repaired_uv_validation.json')
full=read('shield_surface_v2_full_validation.json');targeted=read('shield_surface_v2_targeted.json');export=read('model_shield_reduced_export.json')
source=ROOT/'work/scenes'/uv['scene'];target=ROOT/'work/scenes/clash_braum_shield_reduced_accepted.blend'
assert sha(source)==uv['scene_sha256']==check['scene_sha256']==export['input_scene_sha256']
assert uv['parent_sha256']==geometry['scene_sha256']==full['input_scene_sha256']['refined']==targeted['scene_sha256']
assert uv['geometry_weights_topology_corner_normals_material_indices_transforms_exact'] and uv['uv_only_change']
assert full['revisions']['refined']['total_frames']==3963 and full['native_rest_contract_unchanged'] and full['imported_action_channels_unchanged']
assert check['pass'] and not check['interior_overlaps'] and check['broadphase_pairs_checked']>0
assert export['exact_native_joint_records'] and export['preserved_poro_triangles']==1018
assert all(p['protected_posed_body_max_error']==0 for p in targeted['poses'])
if target.exists():assert sha(target)==sha(source)
else:shutil.copyfile(source,target)
report={'status':'ACCEPTED OFFLINE SHIELD REDUCTION / ATLAS-READY UV CHECKPOINT; runtime and textures incomplete',
 'checkpoint':target.name,'scene_sha256':sha(target),'parent_gameplay_sha256':geometry['parent_sha256'],
 'shield_triangles_before':12256,'shield_triangles_after':9062,'export_vertices':export['vertices'],'export_triangles':export['triangles'],
 'body_and_all_67_torso_seam_corrections_preserved':True,
 'visual_review':'Matched shield front/back and directional-E grips: no new gameplay-visible silhouette/aperture/contact issue. Source corner-normal reconstruction fixes broad shading damage from the rejected Data Transfer draft. Fine normal interpolation differences remain on small hardware.',
 'uv_review':'Shared ShieldAtlas, legacy UVs retained. 44 triangles isolated after real 2D overlap test; fresh sweep-line/polygon-clipping check passes. 23.94% area coverage; density/mipmap quality remains a texture-stage concern.',
 'evidence':{'full_animation':'shield_surface_v2_full_validation.json','uv_only_geometry_identity':'shield_atlas_trial.json','targeted':'shield_surface_v2_targeted.json','uv':'shield_atlas_repaired_uv_validation.json','export':'model_shield_reduced_export.json'},
 'limits':'59-action structural validation covers the exact final geometry/weights via the UV-only identity contract. Not an all-frame collision certificate. Shield materials remain temporary. No runtime build is claimed.',
 'next':'Body atlas pipeline, protected-region-aware geometry reduction, final material integration.'}
(ROOT/'validation/shield_checkpoint_acceptance.json').write_text(json.dumps(report,indent=2))
print(report['status'],report['export_vertices'],report['export_triangles'])
