"""White-core flipbook electricity; no speculative E layer removals."""
import json,re,zipfile
import numpy as np
from PIL import Image
import build_lightning_trial as p
ROOT=p.ROOT
OUT=ROOT/'build/crackle_v1'
NEW=p.ASSET+'crackle_atlas.tex'


def appearance_guard(b):
    b=re.sub(r'(?m)^                (?:Texture|FrameRate|NumFrames|TexDiv|IsRandomStartFrame):[^\n]*','',b)
    for a,z,_ in reversed(list(p.blocks(b,r'^                BirthUvScrollRate: [^\n]*\{'))):b=b[:a]+b[z:]
    for a,z,c in reversed(list(p.blocks(b,r'^                Color: embed = ValueColor \{'))):
        c=re.sub(r'\{\s*([-+\d.eE]+\s*,\s*[-+\d.eE]+\s*,\s*[-+\d.eE]+\s*,\s*[-+\d.eE]+)\s*\}',lambda m:'{ RGB, '+m.group(1).split(',')[3].strip()+' }',c)
        b=b[:a]+c+b[z:]
    return re.sub(r'\s+',' ',b).strip()


def main():
    assert not OUT.exists(),'Preserve candidate.'
    parent=ROOT/'build/clash_passive_v1/Braum_Clash_Dark_Blue_Kit_Passive_v1.fantome'
    assert p.sha(parent)=='04123b8cdd518d310f97c58a851cda1af45ed9f0227e4b124c40409a3298f867'
    OUT.mkdir(parents=True);package=OUT/'package'
    with zipfile.ZipFile(parent) as z:
        assert z.testzip() is None;z.extractall(package)
        before_files={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
    wad=package/'WAD/Braum.wad.client'
    generated=ROOT/'work/textures/crackle_v1/generated_atlas.png';im=Image.open(generated).convert('RGBA')
    assert im.getextrema()[3][0]==0
    atlas=Image.new('RGBA',(1024,1024));frames=[]
    for j in range(4):
        for i in range(4):
            crop=im.crop((round(i*im.width/4),round(j*im.height/4),round((i+1)*im.width/4),round((j+1)*im.height/4))).resize((224,224),Image.Resampling.LANCZOS)
            tile=Image.new('RGBA',(256,256));tile.paste(crop,(16,16));frames.append(tile)
            atlas.paste(tile,(i*256,j*256))
    atlas.save(OUT/'crackle_atlas.png')
    p.run([p.TEX,'encode',OUT/'crackle_atlas.png','-o',wad/NEW,'-f','bc3','--generate-mipmaps'])
    for mip in (0,2,4):
        decoded=OUT/f'crackle_mip{mip}.png';p.run([p.TEX,'decode',wad/NEW,'-o',decoded,'--mipmap',mip])
        a=np.array(Image.open(decoded).convert('RGBA'));size=256>>mip
        assert a.shape==(1024>>mip,1024>>mip,4)
        for j in range(4):
            for i in range(4):
                tile=a[j*size:(j+1)*size,i*size:(i+1)*size]
                assert tile[:,:,3].max()>0
                assert not tile[0,:,3].any() and not tile[-1,:,3].any() and not tile[:,0,3].any() and not tile[:,-1,3].any()
    preview=[]
    for f in frames:
        bg=Image.new('RGBA',f.size,'#080d1c');bg.alpha_composite(f);preview.append(bg.convert('RGB'))
    preview[0].save(OUT/'crackle_preview.gif',save_all=True,append_images=preview[1:],duration=55,loop=0)
    # Preserve logo shapes, transparency and stack segmentation; whiten cyan edges.
    passive=[]
    for key in ['base','quarter_1','quarter_2','quarter_3','quarter_4','full','warning']:
        a=np.array(Image.open(ROOT/f'build/clash_passive_v1/{key}.png').convert('RGBA'))
        b=a.copy();rgb=a[:,:,:3].astype(float);weight=np.clip((rgb[:,:,1]-100)/90,0,1)[:,:,None]
        b[:,:,:3]=np.rint(rgb*(1-weight)+np.array([238,248,255])*weight).astype(np.uint8)
        assert np.array_equal(a[:,:,3],b[:,:,3])
        png=OUT/f'passive_{key}.png';Image.fromarray(b).save(png)
        tex=wad/(p.ASSET+'passive/'+key+'.tex');p.run([p.TEX,'encode',png,'-o',tex,'-f','bc3','--generate-mipmaps'])
        for mip in (0,2):
            decoded=OUT/f'passive_{key}_mip{mip}.png';p.run([p.TEX,'decode',tex,'-o',decoded,'--mipmap',mip])
            old=np.array(Image.open(ROOT/f'build/clash_passive_v1/{key}_mip{mip}.png').convert('RGBA'))
            new=np.array(Image.open(decoded).convert('RGBA'));assert np.array_equal(old[:,:,3],new[:,:,3])
        passive.append(key)
    source=ROOT/'build/clash_passive_v1/skin0.ritobin';text=source.read_text();before=p.entries(text);changes=[]
    binpath=wad/'data/characters/braum/skins/skin0.bin'
    p.run([p.RITO,'-i','text','-o','bin','-k',source,OUT/'parent.bin']);assert p.sha(OUT/'parent.bin')==p.sha(binpath)
    for key,entry in before.items():
        if '/Clash_v1_Braum_' not in key:continue
        original=entry;edited=[]
        for lo,hi,old in reversed(list(p.blocks(entry,r'^            VfxEmitterDefinitionData \{'))):
            bolt=p.ASSET+'lightning_trail.tex' in old
            b=old
            for a,z,c in reversed(list(p.blocks(b,r'^                Color: embed = ValueColor \{'))):
                def white(m):
                    vals=m.group(1).split(',');v=[float(x) for x in vals];peak=max(v[:3])
                    if bolt or peak>0 and v[2]>=max(v[:2]) and min(v[:3])/peak>=.25:
                        return '{ '+', '.join(format(peak*x,'.9g') for x in [.94,.98,1])+', '+vals[3].strip()+' }'
                    return m.group(0)
                c=re.sub(r'\{\s*([-+\d.eE]+\s*,\s*[-+\d.eE]+\s*,\s*[-+\d.eE]+\s*,\s*[-+\d.eE]+)\s*\}',white,c)
                b=b[:a]+c+b[z:]
            if bolt:
                assert not re.search(r'\b(?:TexDiv|FrameRate|NumFrames|StartFrame):',b)
                b=b.replace(p.ASSET+'lightning_trail.tex',NEW)
                for a,z,_ in reversed(list(p.blocks(b,r'^                BirthUvScrollRate: [^\n]*\{'))):b=b[:a]+b[z:]
                b=b[:-1]+'    FrameRate: f32 = 18\n                NumFrames: u16 = 16\n                TexDiv: vec2 = { 4, 4 }\n                IsRandomStartFrame: flag = true\n            }'
            assert appearance_guard(old)==appearance_guard(b),(key,'protected fields')
            if b!=old:
                edited.append(dict(emitter=re.search(r'EmitterName: string = "([^"]+)"',b).group(1),flipbook=bolt))
                entry=entry[:lo]+b+entry[hi:]
        if entry!=original:text=text.replace(original,entry);changes.append(dict(system=key,emitters=edited))
    after=p.entries(text);assert after.keys()==before.keys()
    for key in before:
        if '/Clash_v1_Braum_' not in key:assert before[key]==after[key]
    trial=OUT/'skin0.ritobin';trial.write_text(text)
    p.run([p.RITO,'-i','text','-o','bin','-k',trial,binpath]);p.run([p.RITO,'-i','bin','-o','text',binpath,OUT/'verified.ritobin'])
    p.run([p.RITO,'-i','text','-o','bin','-k',OUT/'verified.ritobin',OUT/'verified.bin']);assert p.sha(binpath)==p.sha(OUT/'verified.bin')
    meta=package/'META/info.json';info=json.loads(meta.read_text());info.update(Name='Clash Braum White Core Crackle v1 TRIAL',Version='0.3.2-crackle',Description='White-core branching electric flipbook replaces smooth scrolling; whiter passive accents. E size/layer correction pending annotated gameplay evidence.');meta.write_text(json.dumps(info,indent=2))
    actual={f.relative_to(package).as_posix():f.read_bytes() for f in package.rglob('*') if f.is_file()}
    assert actual.keys()-before_files.keys()=={'WAD/Braum.wad.client/'+NEW}
    allowed={'META/info.json','WAD/Braum.wad.client/data/characters/braum/skins/skin0.bin'}|{'WAD/Braum.wad.client/'+p.ASSET+'passive/'+k+'.tex' for k in passive}
    assert {n for n in before_files if actual[n]!=before_files[n]}<=allowed
    refs=set(re.findall(r'"(assets/characters/braum/skins/base/braum_clash/[^"]+)"',text,re.I));assert all((wad/r.lower()).is_file() for r in refs)
    archive=OUT/'Braum_Clash_White_Core_Crackle_v1.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for n,data in sorted(actual.items()):z.writestr(n,data)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None and all(z.read(n)==d for n,d in actual.items())
    report=dict(status='PASS affected offline checks; E layer/size correction pending screenshot',archive=str(archive.relative_to(ROOT)),sha256=p.sha(archive),parent_sha256=p.sha(parent),generated_source_sha256=p.sha(generated),changes=changes,
        motion='16 padded frames, 18 fps, random starting frame; no continuous UV scrolling on converted bolts.',
        protected='Alpha envelopes, lifetimes, rates, scale, transforms, gameplay and non-appearance fields exact. No E emitters removed/resized. Model, loading and stack logic retained.',
        textures='Atlas mip0/2/4 transparent frame borders/nonempty cells; passive source/decoded mip0/2 alpha exact.',
        reused='Accepted model/rig/loading evidence, exact unchanged bytes.',
        payloads=[dict(path=f.relative_to(wad).as_posix(),sha256=p.sha(f)) for f in sorted(wad.rglob('*')) if f.is_file()])
    (ROOT/'validation/crackle_v1_build.json').write_text(json.dumps(report,indent=2));(ROOT/'validation/crackle_v1_build_logs.json').write_text(json.dumps(p.logs,indent=2))
    print(json.dumps({k:report[k] for k in ['status','archive','sha256','motion']},indent=2))


if __name__=='__main__':main()
