"""Gameplay-feedback pass: Q core, quiet W logo, directional E, sparse R and portrait."""
import json,re,zipfile
from PIL import Image,ImageOps
import build_lightning_trial as p
ROOT=p.ROOT
OUT=ROOT/'build/readability_v1'
PREFIX='Characters/Braum/Skins/Skin0/Particles/Clash_v1_'


def emitters(e):return list(p.blocks(e,r'^            VfxEmitterDefinitionData \{'))
def name(b):return re.search(r'EmitterName: string = "([^"]+)"',b).group(1)


def strip(b,fields):
    for f in fields:
        for a,z,_ in reversed(list(p.blocks(b,rf'^                {f}: [^\n]*\{{'))):b=b[:a]+b[z:]
        b=re.sub(rf'(?m)^                {f}:[^\n]*\n?','',b)
    return b


def guard(old,new,fields):
    assert re.sub(r'\s+',' ',strip(old,fields)).strip()==re.sub(r'\s+',' ',strip(new,fields)).strip(),name(old)


def color(b,rgb,alpha=1):
    for a,z,c in reversed(list(p.blocks(b,r'^                Color: embed = ValueColor \{'))):
        c=re.sub(r'\{\s*([-+\d.eE]+\s*,\s*[-+\d.eE]+\s*,\s*[-+\d.eE]+\s*,\s*[-+\d.eE]+)\s*\}',
            lambda m:'{ '+', '.join(map(str,rgb))+', '+format(float(m.group(1).split(',')[3])*alpha,'.9g')+' }',c)
        b=b[:a]+c+b[z:]
    return b


def replace_texture(b,path):
    b,n=re.subn(r'(?m)^(                Texture: string = )"[^"]+"',r'\1"'+path+'"',b);assert n==1
    return b


def main():
    assert not OUT.exists(),'Preserve previous output.'
    parent=ROOT/'build/crackle_v1/Braum_Clash_White_Core_Crackle_v1.fantome'
    assert p.sha(parent)=='bc51d5d16093f3d5c46fc75de43a1862fef1480302a3356b229fd081a1a7e44e'
    OUT.mkdir(parents=True);package=OUT/'package'
    with zipfile.ZipFile(parent) as z:
        assert z.testzip() is None;z.extractall(package)
        previous_files={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
    wad=package/'WAD/Braum.wad.client';binpath=wad/'data/characters/braum/skins/skin0.bin'
    source=ROOT/'build/crackle_v1/skin0.ritobin';text=source.read_text();before=p.entries(text)
    p.run([p.RITO,'-i','text','-o','bin','-k',source,OUT/'parent.bin']);assert p.sha(OUT/'parent.bin')==p.sha(binpath)
    native=p.entries((ROOT/'build/lightning_v1/core/skin0.ritobin').read_text())
    changed={};changes=[]
    # New orientation evidence identifies the default camera billboard, not meshes.
    key=PREFIX+'Braum_E_Shield_cas';e=before[key];removed=[]
    for a,z,b in reversed(emitters(e)):
        if name(b)=='Inchant_flash':
            assert 'Primitive:' not in b and '{ 300, 300, 300 }' in b
            e=e[:a]+e[z:];removed.append(name(b))
    assert removed==['Inchant_flash']
    for _,_,b in emitters(before[key]):
        if name(b)!='Inchant_flash':assert b in e
    changed[key]=e;changes.append('E: remove Inchant_flash camera billboard; all directional mesh/other effects exact.')
    # Native missile head supplies binding, life and travel placement. Replace only
    # its rendering with a compact additive core + animated electrical shell.
    key=PREFIX+'Braum_Q_mis';e=before[key]
    head=next(b for _,_,b in emitters(native[key]) if name(b)=='Ice_head')
    fields=['Primitive','BlendMode','Color','AlphaRef','BirthRotation0','BirthRotationalVelocity0','BirthScale0','Scale0','Texture','EmitterName','FrameRate','NumFrames','TexDiv','IsRandomStartFrame']
    added=[]
    for suffix,scale,texture in [('Core',(52,52,52),'ASSETS/Characters/Braum/Skins/Base/Particles/Braum_Base_I_shield_glow.tex'),('Arc',(90,58,58),p.ASSET+'crackle_atlas.tex')]:
        b=strip(head,['Primitive','AlphaRef','BirthRotation0','BirthRotationalVelocity0','Scale0'])
        b=b.replace('EmitterName: string = "Ice_head"','EmitterName: string = "Clash_Q_Electric_'+suffix+'"').replace('BlendMode: u8 = 3','BlendMode: u8 = 4')
        b=color(b,(.94,.98,1));b=replace_texture(b,texture)
        extra='    BirthScale0: embed = ValueVector3 {\n                    ConstantValue: vec3 = { '+', '.join(map(str,scale))+' }\n                }\n'
        if suffix=='Arc':extra+='                FrameRate: f32 = 18\n                NumFrames: u16 = 16\n                TexDiv: vec2 = { 4, 4 }\n                IsRandomStartFrame: flag = true\n'
        b=b[:-1]+extra+'            }';guard(head,b,fields);added.append(b)
    marker='        ComplexEmitterDefinitionData: list[pointer] = {';assert e.count(marker)==1
    e=e.replace(marker,marker+'\n'+'\n'.join(added),1)
    assert all(b in e for _,_,b in emitters(before[key]));changed[key]=e
    changes.append('Q: add bound white core and crackle shell from native missile-head lifetime/placement; existing Q electricity exact.')
    # W: no electrical burst or body particles; a single faint logo decal remains.
    for short,keep in [('Braum_W_Dash_Land',{'Distortion'}),('Braum_W_Shield_buf',{'Decal_shield'})]:
        key=PREFIX+short;e=before[key]
        for a,z,b in reversed(emitters(e)):
            n=name(b)
            if n not in keep:
                assert not re.search(r'(?i)(audio|sound|child|event)',b);new=''
            elif n=='Decal_shield':
                new=color(b,(1,1,1),.55);new=replace_texture(new,p.ASSET+'passive/full.tex')
                guard(b,new,['Color','Texture'])
            else:new=b
            e=e[:a]+new+e[z:]
        assert {name(b) for _,_,b in emitters(e)}==keep
        changed[key]=e
    changes.append('W: landing electrical emitters removed; buff keeps only faint full Clash logo, native decal timing/size/fade retained.')
    # R: substantially fewer bolts and a dark alpha-blended native ground mask.
    for short in ['Braum_R_mis','Braum_R_Small_mis','Braum_R_PBAOE_Cas']:
        key=PREFIX+short;e=before[key]
        for a,z,b in reversed(emitters(e)):
            n=name(b);new=b
            if n in ['cracks_left','cracks_right']:
                assert not re.search(r'(?i)(audio|sound|child|event)',b);new=''
            elif n=='line':
                rate=list(p.blocks(b,r'^                Rate: embed = ValueFloat \{'));assert len(rate)==1
                lo,hi,r=rate[0];assert re.search(r'ConstantValue: f32 = 80\b',r) and 'Dynamics:' not in r
                new=b[:lo]+r.replace('ConstantValue: f32 = 80','ConstantValue: f32 = 20')+b[hi:];guard(b,new,['Rate'])
            elif n=='Frozen':
                original=next(x for _,_,x in emitters(native[key]) if name(x)=='Frozen')
                tex=re.search(r'(?m)^                Texture: string = "([^"]+)"',original).group(1)
                new=strip(b,['FrameRate','NumFrames','TexDiv','IsRandomStartFrame'])
                new=replace_texture(new,tex);new=color(new,(.015,.025,.055),.72)
                assert 'BlendMode: u8 = 1' in new
                guard(b,new,['Texture','Color','FrameRate','NumFrames','TexDiv','IsRandomStartFrame'])
            elif n=='GroundBurn':
                new=color(b,(.015,.025,.055),.8);guard(b,new,['Color'])
            e=e[:a]+new+e[z:]
        changed[key]=e
    changes.append('R: main line rates 80->20, flanking crack bolts removed; Frozen/GroundBurn dark navy ground mask, original ground footprint/life preserved.')
    for key,e in changed.items():text=text.replace(before[key],e)
    after=p.entries(text);assert before.keys()==after.keys()
    assert {k for k in before if before[k]!=after[k]}==changed.keys()
    trial=OUT/'skin0.ritobin';trial.write_text(text)
    p.run([p.RITO,'-i','text','-o','bin','-k',trial,binpath]);p.run([p.RITO,'-i','bin','-o','text',binpath,OUT/'verified.ritobin'])
    p.run([p.RITO,'-i','text','-o','bin','-k',OUT/'verified.ritobin',OUT/'verified.bin']);assert p.sha(binpath)==p.sha(OUT/'verified.bin')
    # Recenter crop on Clash's face/body axis (~x562), not the landscape midpoint.
    reference=ROOT/'clash new.avif'
    portrait=ImageOps.fit(Image.open(reference).convert('RGB'),(308,560),Image.Resampling.LANCZOS,centering=(.455,.5))
    portrait.save(OUT/'loading_portrait.png');splash=wad/'assets/characters/braum/skins/base/braumloadscreen.tex'
    p.run([p.TEX,'encode',OUT/'loading_portrait.png','-o',splash,'-f','bc3','--generate-mipmaps'])
    for mip in (0,2):
        decoded=OUT/f'loading_mip{mip}.png';p.run([p.TEX,'decode',splash,'-o',decoded,'--mipmap',mip])
        img=Image.open(decoded).convert('RGBA');assert img.size==(308>>mip,560>>mip) and img.getextrema()[3]==(255,255)
    meta=package/'META/info.json';info=json.loads(meta.read_text());info.update(Name='Clash Braum Readability v1 TRIAL',Version='0.3.3-readability',Description='Centered loading portrait; Q electric core; W faint Clash logo; E camera billboard removed; sparse R over dark ground. Manual gameplay approval pending.');meta.write_text(json.dumps(info,indent=2))
    actual={f.relative_to(package).as_posix():f.read_bytes() for f in package.rglob('*') if f.is_file()}
    assert actual.keys()==previous_files.keys()
    assert {n for n in actual if actual[n]!=previous_files[n]}=={'META/info.json','WAD/Braum.wad.client/data/characters/braum/skins/skin0.bin','WAD/Braum.wad.client/assets/characters/braum/skins/base/braumloadscreen.tex'}
    refs=set(re.findall(r'"(assets/characters/braum/skins/base/braum_clash/[^"]+)"',text,re.I));assert all((wad/r.lower()).is_file() for r in refs)
    archive=OUT/'Braum_Clash_Readability_v1.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for n,data in sorted(actual.items()):z.writestr(n,data)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None and all(z.read(n)==d for n,d in actual.items())
    report=dict(status='PASS targeted build; gameplay pending',archive=str(archive.relative_to(ROOT)),sha256=p.sha(archive),parent_sha256=p.sha(parent),changes=changes,
        protected='Only seven VFX entries changed; resolver/telegraphs/audio/model/rig/body/shield/passive assets exact. W/R appearance changes and R emission reduction explicitly authorized; lifetime/cleanup fields retained.',
        loading='308x560, crop center .455/.5; opaque mip0/2 checked.',
        reused='Unchanged crackle atlas, passive/logo, model/rig texture evidence; no new art or geometry tests.',
        payloads=[dict(path=f.relative_to(wad).as_posix(),sha256=p.sha(f)) for f in sorted(wad.rglob('*')) if f.is_file()])
    (ROOT/'validation/readability_v1_build.json').write_text(json.dumps(report,indent=2));(ROOT/'validation/readability_v1_build_logs.json').write_text(json.dumps(p.logs,indent=2))
    print(json.dumps({k:report[k] for k in ['status','archive','sha256','changes']},indent=2))


if __name__=='__main__':main()
