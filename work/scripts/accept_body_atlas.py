"""Preserve the visually reviewed body atlas after independent structural/export gates."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
def read(n):return json.loads((ROOT/'validation'/n).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=ROOT/'work/scenes/clash_braum_body_atlas_preview_trial.blend'
target=ROOT/'work/scenes/clash_braum_body_atlas_accepted.blend'
bake=read('body_atlas_bake_trial.json');contract=read('body_atlas_contract.json');full=read('body_atlas_full_validation.json');export=read('model_body_atlas_export.json');uv=read('body_atlas_packed_uv_validation.json')
assert sha(source)==bake['scene_sha256']==contract['scene_sha256']==full['input_scene_sha256']['refined']==export['input_scene_sha256']
assert bake['source_sha256']==uv['scene_sha256'] and uv['pass'] and contract['pass_contract']
assert full['revisions']['refined']['total_frames']==3963 and full['native_rest_contract_unchanged'] and full['imported_action_channels_unchanged']
assert export['exact_native_joint_records'] and export['preserved_poro_triangles']==1018
for ch,t in bake['textures'].items():assert sha(ROOT/t['path'])==t['sha256']==contract['texture_stats'][ch]['sha256']
for view in ('front','reverse'):
    m=read(f'atlas_baked_{view}_render_manifest.json');assert m['scene_sha256']==sha(source) and len(m['renders'])==4
if target.exists():assert sha(target)==sha(source)
else:shutil.copyfile(source,target)
report=dict(status='ACCEPTED OFFLINE BODY ATLAS equivalence to reconstructed source preview; not runtime acceptance',checkpoint=target.name,scene_sha256=sha(target),export_vertices=export['vertices'],export_triangles=export['triangles'],textures=bake['textures'],
 visual_review='Reviewed eight matched gameplay-size views: idle, running E, R17, recall65 from opposing elevated cameras. No material gameplay-visible seam, texture alignment, silhouette/opacity, color/value or hard-surface shading regression. Minor fine-detail filtering differences accepted.',
 technical_review='Zero UV overlaps; source UVs and exact geometry/weights/normals retained; +Y tangent normal strength1; saved alpha matches opacity bake; full3963-frame structural and matched native export pass. Body joined only in export memory into Braum submesh.',
 limitations='13.17% atlas coverage, 2048 square, 4px dilation. Very small UV triangles and filtered normal vectors retain close-up imperfections. Native-size previews show no disruptive bleeding; actual Riot shader, DDS/TEX mipmap/alpha and normal convention remain runtime gates. Existing source material reconstruction excludes custom detail shader. Scene material name Braum.001 is normalized to Braum in export; source reference material retained.',
 evidence=['body_atlas_contract.json','body_atlas_full_validation.json','body_atlas_packed_uv_validation.json','model_body_atlas_export.json','body_atlas_gameplay_comparison.json'],next='Finish shield textures/materials, then model-only BIN/texture packaging and runtime gate; preserve accepted body/cuff/shield.')
(ROOT/'validation/body_atlas_acceptance.json').write_text(json.dumps(report,indent=2))
print(report['status'])
