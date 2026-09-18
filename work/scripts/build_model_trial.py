"""Build an isolated legacy-material runtime trial; preserve original gameplay/VFX/audio."""
from pathlib import Path
import hashlib,json,shutil,subprocess,zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/model_runtime_trial';OUT.mkdir(parents=True,exist_ok=True)
PKG=OUT/'package';MAIN=PKG/'WAD/Braum.wad.client'
BASE='assets/characters/braum/skins/base/braum_clash/'
assets=MAIN/BASE;assets.mkdir(parents=True,exist_ok=True)
rito=Path('C:/Users/etqdo/Downloads/cslol-go/cslol-tools/ritobin_cli.exe')
tex=ROOT/'work/tools/ltk-tex-utils.exe'
logs=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):
    r=subprocess.run([str(a) for a in args],cwd=ROOT,capture_output=True,text=True,encoding='utf8',errors='replace')
    logs.append(dict(argv=list(map(str,args)),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
    assert r.returncode==0,(r.stdout,r.stderr)
report=json.loads((ROOT/'validation/model_shield_material_export.json').read_text())
scene=ROOT/'work/scenes/clash_braum_shield_material_trial.blend'
assert report['input_scene_sha256']==sha(scene) and report['exact_native_joint_records']
for ext in ('skn','skl'):shutil.copyfile(ROOT/f'build/model_shield_material/braum_clash.{ext}',assets/f'braum_clash.{ext}')
textures={}
for name,png in [('body',ROOT/'work/textures/body_atlas_trial/clash_body_basecolor.png'),('shield_frame',ROOT/'work/textures/shield_material_trial/clash_shield_basecolor.png')]:
    target=assets/f'{name}.tex'
    run([tex,'encode',png,'-o',target,'-f','bc3','--generate-mipmaps'])
    run([tex,'info','-i',target])
    for mip in (0,2,4):run([tex,'decode',target,'-o',OUT/f'{name}_mip{mip}.png','--mipmap',str(mip)])
    textures[name]=dict(source_sha256=sha(png),sha256=sha(target),mipmaps=True,format='BC3')
# A constant low-gloss trial avoids projecting the old Braum gloss onto new UVs.
# Legacy implicit shader has no established normal-map input in supplied B0.
gloss=OUT/'neutral_gloss.png';Image.new('RGBA',(4,4),(12,12,12,255)).save(gloss)
run([tex,'encode',gloss,'-o',assets/'neutral_gloss.tex','-f','bc3','--generate-mipmaps'])
original=ROOT/'Braum.wad/eb9d53354a504663.bin';named=OUT/'skin0_source.ritobin'
run([rito,'-i','bin','-o','text','-d',ROOT/'audit/sources',original,named])
run([rito,'-i','text','-o','bin','-k',named,OUT/'skin0_noop.bin'])
assert original.read_bytes()==(OUT/'skin0_noop.bin').read_bytes()
text=named.read_text();start=text.index('        SkinMeshProperties: embed = SkinMeshDataProperties {');end=text.index('        ArmorMaterial:',start)
block=text[start:end];oldblock=block
replacements={
 'Skeleton: string = "ASSETS/Characters/Braum/Skins/Base/Braum_Base.skl"':f'Skeleton: string = "{BASE}braum_clash.skl"',
 'SimpleSkin: string = "ASSETS/Characters/Braum/Skins/Base/Braum_Base.skn"':f'SimpleSkin: string = "{BASE}braum_clash.skn"',
 'Texture: file = 0x55b5d46776387920':f'Texture: file = "{BASE}body.tex"',
 'GlossTexture: file = 0x9b701e6000aefb27':f'GlossTexture: file = "{BASE}neutral_gloss.tex"'}
for a,b in replacements.items():assert block.count(a)==1;block=block.replace(a,b)
anchor='            MaterialOverride: list[embed] = {\n'
assert block.count(anchor)==1
block=block.replace(anchor,anchor+'                SkinMeshDataProperties_MaterialOverride {\n'+f'                    Texture: file = "{BASE}shield_frame.tex"\n'+'                    Submesh: string = "ShieldFrame"\n'+'                }\n')
candidate=OUT/'skin0_trial.ritobin';candidate.write_text(text[:start]+block+text[end:])
binpath=MAIN/'data/characters/braum/skins/skin0.bin';binpath.parent.mkdir(parents=True,exist_ok=True)
run([rito,'-i','text','-o','bin','-k',candidate,binpath])
# Reparse both BINs to hashed text and prove all bytes of text outside mesh settings match.
for name,path in [('original',original),('candidate',binpath)]:run([rito,'-i','bin','-o','text','-d',ROOT/'audit/sources',path,OUT/f'{name}_verified.ritobin'])
a=(OUT/'original_verified.ritobin').read_text();b=(OUT/'candidate_verified.ritobin').read_text()
def strip_mesh(s):
    lo=s.index('        SkinMeshProperties: embed = SkinMeshDataProperties {');hi=s.index('        ArmorMaterial:',lo)
    return s[:lo]+s[hi:]
assert strip_mesh(a)==strip_mesh(b)
assert 'InitialSubmeshToHide: string = "Poro"' in b and 'Submesh: string = "Poro"' in b
meta=PKG/'META';meta.mkdir(exist_ok=True)
(meta/'info.json').write_text(json.dumps(dict(Name='Clash Braum MODEL ONLY - RUNTIME TRIAL',Author='Ethan',Version='0.1.0-trial',Description='Unaccepted runtime trial. Native animations, gameplay, VFX and audio retained. Legacy diffuse/low-gloss shader; baked normal is not bound. Check opacity, culling, Poro and performance.'),indent=2))
archive=OUT/'Braum_Clash_Model_Trial.fantome'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(PKG.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(PKG).as_posix())
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
result=dict(status='BUILT MODEL-ONLY RUNTIME TRIAL; not accepted, not final Braum_Clash.fantome',archive=str(archive.relative_to(ROOT)),sha256=sha(archive),scene_sha256=sha(scene),textures=textures,original_bin_sha256=sha(original),output_bin_sha256=sha(binpath),outside_skin_mesh_settings_identical=True,original_poro_override_preserved=True,tool=dict(url='https://github.com/LeagueToolkit/ltk-tex-utils/releases/tag/v0.3.0',sha256=sha(tex)),
 limits='Legacy implicit diffuse/low-gloss runtime trial. Body normal PNG remains accepted offline but is NOT bound: supplied base shader exposes no established normal input. Alpha/normal fidelity, patch compatibility, culling and performance need actual runtime evidence. No source WAD, manager library or live game changed.',
 files=[dict(path=p.relative_to(PKG).as_posix(),sha256=sha(p)) for p in sorted(PKG.rglob('*')) if p.is_file()])
(ROOT/'validation/model_runtime_trial_build.json').write_text(json.dumps(result,indent=2))
(ROOT/'validation/model_runtime_trial_build.log.json').write_text(json.dumps(logs,indent=2))
print(result['status'])
