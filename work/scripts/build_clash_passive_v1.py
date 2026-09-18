"""Four-quarter supplied Clash logo on native passive stack states; integrated kit."""
import json,re,zipfile
import numpy as np
from PIL import Image,ImageOps,ImageDraw
import build_lightning_trial as p
ROOT=p.ROOT
OUT=ROOT/'build/clash_passive_v1'
ASSET=p.ASSET+'passive/'


def neutralize_rgb(block):
    for a,b,c in reversed(list(p.blocks(block,r'^                Color: embed = ValueColor \{'))):
        def change(m):
            v=m.group(1).split(','); peak=max(float(x) for x in v[:3])
            return '{ '+', '.join([format(peak,'.9g')]*3)+', '+v[3].strip()+' }'
        c=re.sub(r'\{\s*([-+\d.eE]+\s*,\s*[-+\d.eE]+\s*,\s*[-+\d.eE]+\s*,\s*[-+\d.eE]+)\s*\}',change,c)
        block=block[:a]+c+block[b:]
    return block


def normalize(block):
    block=re.sub(r'(?m)^                Texture: string = .*','',block)
    for a,b,c in reversed(list(p.blocks(block,r'^                Color: embed = ValueColor \{'))):
        c=re.sub(r'\{\s*([-+\d.eE]+\s*,\s*[-+\d.eE]+\s*,\s*[-+\d.eE]+\s*,\s*[-+\d.eE]+)\s*\}',lambda m:'{ RGB, '+m.group(1).split(',')[3].strip()+' }',c)
        block=block[:a]+c+block[b:]
    return block


def main():
    assert not OUT.exists(),'Preserve candidate.'
    parent=ROOT/'build/darkblue_kit_v1/Braum_Clash_Dark_Blue_Kit_v1.fantome'
    assert p.sha(parent)=='90f25df781d135076f05ae5cb8341298c71a60aa89237145a31a436ec538fca8'
    OUT.mkdir(parents=True);package=OUT/'package'
    with zipfile.ZipFile(parent) as z:
        assert z.testzip() is None;z.extractall(package)
        before_files={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
    wad=package/'WAD/Braum.wad.client';assets=wad/ASSET;assets.mkdir(parents=True)
    source=ROOT/'work/textures/passive_clash/source_logo.png'
    assert p.sha(source)=='8a1ddeb92d0fd5a94f34c3a0378c925552a844320c386a90dc8aaa7c093e6d79'
    logo=Image.open(source).convert('RGB');gray=logo.convert('L');bbox=gray.point(lambda x:255 if x>5 else 0).getbbox()
    cropped=logo.crop(bbox); fitted=ImageOps.contain(cropped,(232,232),Image.Resampling.LANCZOS)
    canvas=Image.new('RGB',(256,256));canvas.paste(fitted,((256-fitted.width)//2,(256-fitted.height)//2))
    intensity=np.array(canvas).max(2).astype(float)/255
    # Grey ring becomes deep electric blue; white outlines/checkers become cyan-blue.
    strength=np.clip((intensity-.40)/.60,0,1)
    rgb=np.rint(np.array([18,65,165])[None,None,:]*(1-strength[:,:,None])+np.array([95,190,255])[None,None,:]*strength[:,:,None]).astype(np.uint8)
    alpha=np.rint(np.clip(intensity/.12,0,1)*255).astype(np.uint8)
    # Crosshair gaps make the four stack segments readable at game zoom.
    alpha[:,126:130]=0;alpha[126:130,:]=0
    yy,xx=np.indices(alpha.shape)
    quadrants=[(xx>=130)&(yy<126),(xx>=130)&(yy>=130),(xx<126)&(yy>=130),(xx<126)&(yy<126)]
    textures={}
    def rgba(a):return Image.fromarray(np.dstack([rgb,a]))
    textures['base']=rgba(np.rint(alpha*.17).astype(np.uint8))
    for i,q in enumerate(quadrants,1):textures[f'quarter_{i}']=rgba(np.where(q,alpha,0).astype(np.uint8))
    textures['full']=rgba(alpha)
    textures['warning']=rgba(np.where(quadrants[0]|quadrants[1]|quadrants[2],alpha,0).astype(np.uint8))
    # Disjoint segments must exactly reconstruct the full icon.
    pieces=[np.array(textures[f'quarter_{i}'])[:,:,3].astype(int) for i in range(1,5)]
    assert np.array_equal(sum(pieces),alpha)
    checks=[]
    for key,img in textures.items():
        png=OUT/(key+'.png');img.save(png);tex=assets/(key+'.tex')
        p.run([p.TEX,'encode',png,'-o',tex,'-f','bc3','--generate-mipmaps'])
        for mip in (0,2):
            decoded=OUT/f'{key}_mip{mip}.png';p.run([p.TEX,'decode',tex,'-o',decoded,'--mipmap',mip])
            im=Image.open(decoded).convert('RGBA');assert im.size==(256>>mip,256>>mip)
            assert im.getpixel((0,0))[3]==0 and im.getextrema()[3][1]>0
        checks.append(dict(texture=key,sha256=p.sha(tex),mip0_2=True))
    preview=Image.new('RGB',(1024,280),'#101827');draw=ImageDraw.Draw(preview)
    for count in range(1,5):
        tile=Image.new('RGBA',(256,256),'#101827');tile.alpha_composite(textures['base'])
        for i in range(1,count+1):tile.alpha_composite(textures[f'quarter_{i}'])
        preview.paste(tile.convert('RGB'),((count-1)*256,24));draw.text(((count-1)*256+10,5),f'{count} stack'+('s' if count>1 else ''),fill='white')
    preview.save(OUT/'passive_preview.png')
    source_bin=ROOT/'build/darkblue_kit_v1/skin0.ritobin';text=source_bin.read_text();before=p.entries(text)
    binpath=wad/'data/characters/braum/skins/skin0.bin'
    p.run([p.RITO,'-i','text','-o','bin','-k',source_bin,OUT/'parent.bin']);assert p.sha(OUT/'parent.bin')==p.sha(binpath)
    rows={r['resource_key']:r for r in json.loads((ROOT/'audit/evidence/base_vfx_dependencies.json').read_text())}
    added=[];rewires=[];changes=[]
    for key in ['Braum_P_stack_1','Braum_P_stack_2','Braum_P_stack_3','Braum_P_stack_4','Braum_P_stack_3_warning']:
        row=rows[key];native=p.entries((ROOT/'build/lightning_v1'/(row['owner_hash']+'.ritobin')).read_text())[row['entry']]
        dest='Characters/Braum/Skins/Skin0/Particles/Clash_Logo_'+key
        entry=native.replace('"'+row['entry']+'"','"'+dest+'"')
        entry=re.sub(r'(ParticleName: string = )"[^"]+"',r'\1"Clash_Logo_'+key+'"',entry)
        count=0
        for a,b,old in reversed(list(p.blocks(entry,r'^            VfxEmitterDefinitionData \{'))):
            n=re.search(r'EmitterName: string = "([^"]+)"',old).group(1)
            texkey={'ground_stack_base':'base','full_stack':'full','stack_warning':'warning'}.get(n)
            if n.startswith('ground_stack_0'):texkey='quarter_'+str(int(n[-1]))
            if not texkey:continue
            assert not re.search(r'\b(?:TexDiv|FrameRate|StartFrame):',old)
            new=neutralize_rgb(old)
            new,num=re.subn(r'(?m)^(                Texture: string = )"[^"]+"',r'\1"'+ASSET+texkey+'.tex"',new);assert num==1
            assert normalize(old)==normalize(new),(key,n)
            entry=entry[:a]+new+entry[b:];count+=1
        assert count>0;added.append(entry);changes.append(dict(system=key,marker_emitters=count))
        old='"'+key+'" = "'+row['entry']+'"';new='"'+key+'" = "'+dest+'"'
        assert text.count(old)==1;text=text.replace(old,new);rewires.append((old,new))
    text=text.rstrip()[:-1]+'\n'+'\n'.join(added)+'\n}\n'
    after=p.entries(text)
    for key,e in before.items():
        if key.endswith('/Resources'):
            for old,new in rewires:e=e.replace(old,new)
        assert after[key]==e,key
    assert len(after)==len(before)+5
    trial=OUT/'skin0.ritobin';trial.write_text(text)
    p.run([p.RITO,'-i','text','-o','bin','-k',trial,binpath])
    p.run([p.RITO,'-i','bin','-o','text',binpath,OUT/'verified.ritobin'])
    p.run([p.RITO,'-i','text','-o','bin','-k',OUT/'verified.ritobin',OUT/'verified.bin']);assert p.sha(binpath)==p.sha(OUT/'verified.bin')
    meta=package/'META/info.json';info=json.loads(meta.read_text());info.update(Name='Clash Braum Dark Blue Kit + Passive Logo TRIAL',Version='0.3.1-passive',Description='Corrected E, dark-blue Q/W/R, Clash loading portrait and four-quarter electric-blue Clash passive marker. Manual gameplay approval pending.');meta.write_text(json.dumps(info,indent=2))
    actual={f.relative_to(package).as_posix():f.read_bytes() for f in package.rglob('*') if f.is_file()}
    assert actual.keys()-before_files.keys()=={'WAD/Braum.wad.client/'+ASSET+k+'.tex' for k in textures}
    assert not before_files.keys()-actual.keys()
    assert {n for n in before_files if actual[n]!=before_files[n]}=={'META/info.json','WAD/Braum.wad.client/data/characters/braum/skins/skin0.bin'}
    archive=OUT/'Braum_Clash_Dark_Blue_Kit_Passive_v1.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for n,data in sorted(actual.items()):z.writestr(n,data)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None and all(z.read(n)==data for n,data in actual.items())
    report=dict(status='PASS targeted build; integrated package check and gameplay pending',archive=str(archive.relative_to(ROOT)),sha256=p.sha(archive),parent_sha256=p.sha(parent),source_logo_sha256=p.sha(source),changes=changes,textures=checks,
        protected='Only passive marker texture/RGB and five resolver targets changed; native stack logic, alpha/timing, transforms, stun, cooldown and other emitters retained.',
        reused='Dark-blue kit affected-field/alpha checks; exact inherited splash and model textures; accepted geometry unchanged.',
        payloads=[dict(path=f.relative_to(wad).as_posix(),sha256=p.sha(f)) for f in sorted(wad.rglob('*')) if f.is_file()])
    (ROOT/'validation/clash_passive_v1_build.json').write_text(json.dumps(report,indent=2));(ROOT/'validation/clash_passive_v1_build_logs.json').write_text(json.dumps(p.logs,indent=2))
    print(json.dumps({k:report[k] for k in ['status','archive','sha256','changes']},indent=2))


if __name__=='__main__':main()
