"""Replace only HUD icons on the user-accepted complete skin."""
import json,zipfile,sys,hashlib
import numpy as np
from PIL import Image,ImageOps,ImageDraw
import build_lightning_trial as p
ROOT=p.ROOT;OUT=ROOT/'build/ui_icons_v1';HUD='assets/characters/braum/hud/'
def main():
    assert not (OUT/'Braum_Clash_New_UI_Icons_v1.fantome').exists(),'Preserve candidate.'
    parent=ROOT/'build/audio_3x_v1/Braum_Clash_Custom_Hex_3x_Voice_SFX_v1.fantome'
    assert p.sha(parent)=='48c6f7ae0ae2c1900ca51cfde33f2dcc62083673653a77ec32a34b57e3c558b7'
    OUT.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(parent) as z:
        assert z.testzip() is None;before={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
    after=before.copy();added={};checks=[];preview=Image.new('RGB',(640,230),'#20242c');draw=ImageDraw.Draw(preview)
    sources={'passive':ROOT/'Ability icons/passive icon.jpg','q':ROOT/'Ability icons/Q icon.webp','w':ROOT/'Ability icons/W icon.jpg','e':ROOT/'Ability icons/E icon.jpg','r':ROOT/'work/textures/ui_icons_v1/r_source.png'}
    mapping=json.loads((ROOT/'audit/evidence/path_map.json').read_text())
    for col,(name,src) in enumerate(sources.items()):
        image=Image.open(src).convert('RGB')
        if name=='w':image=image.crop((0,0,720,720))
        image=ImageOps.fit(image,(64,64),Image.Resampling.LANCZOS)
        target=OUT/(name+'.dds');image.save(target,pixel_format='DXT1')
        path=HUD+'icons2d/braum_'+name+'.dds';key=next(h for h,n in mapping.items() if n==path)
        native=(ROOT/'Braum.wad'/f'{key}.dds').read_bytes();data=target.read_bytes()
        assert data[:4]==b'DDS ' and data[84:88]==native[84:88]==b'DXT1' and len(data)==len(native)
        decoded=Image.open(target);decoded.load();assert decoded.size==(64,64)
        added[path]=data;checks.append(dict(path=path,dimensions=[64,64],format='DXT1',source=str(src.relative_to(ROOT)),source_sha256=p.sha(src)))
        preview.paste(decoded.resize((112,112)),(col*128+8,24));draw.text((col*128+10,6),name.upper(),fill='white')
        preview.paste(decoded,(col*128+32,155))
    face=Image.open(ROOT/'clash new.avif').convert('RGB').crop((460,90,690,320)).resize((128,128),Image.Resampling.LANCZOS)
    for name,key,fmt in [('circle','b7a7a4ab8b7380c5','bc3'),('square','42f25b703b2122c8','bc1')]:
        original=ROOT/'Braum.wad'/f'{key}.tex';nativepng=OUT/(name+'_native.png')
        p.run([p.TEX,'decode',original,'-o',nativepng]);native=Image.open(nativepng).convert('RGBA');assert native.size==(128,128)
        image=face.convert('RGBA');image.putalpha(native.getchannel('A'))
        png=OUT/(name+'.png');image.save(png);target=OUT/(name+'.tex');p.run([p.TEX,'encode',png,'-o',target,'-f',fmt])
        # Encoder emits a mip chain; native HUD TEX has just mip0. TEX stores
        # smallest levels first, so keep the last native-sized level/header.
        nativebytes=original.read_bytes();encoded=target.read_bytes()
        assert nativebytes[:11]==encoded[:11]
        target.write_bytes(nativebytes[:12]+encoded[-(len(nativebytes)-12):])
        if name=='circle':
            a=original.read_bytes();b=bytearray(target.read_bytes());assert a[:12]==b[:12] and len(a)==len(b)
            for off in range(12,len(b),16):b[off:off+8]=a[off:off+8]
            target.write_bytes(b)
        decoded=OUT/(name+'_decoded.png');p.run([p.TEX,'decode',target,'-o',decoded]);new=Image.open(decoded).convert('RGBA')
        assert new.size==native.size and np.array_equal(np.array(new)[:,:,3],np.array(native)[:,:,3])
        path=HUD+'braum_'+name+'.tex';added[path]=target.read_bytes();checks.append(dict(path=path,dimensions=[128,128],format=fmt,native_alpha_exact=True,portrait_crop=[460,90,690,320]))
    preview.save(OUT/'ability_preview.png')
    for path,data in added.items():
        member='WAD/Braum.wad.client/'+path;assert member not in before;after[member]=data
    info=json.loads(after['META/info.json']);info.update(Name='Clash Braum Accepted Skin + New UI Icons',Version='0.4.6-ui',Description='Accepted custom colors, complete electrical VFX and 3x voice/SFX unchanged. Supplied passive/Q/W/E icons, generated electrical fissure R icon and Clash HUD portraits only.')
    after['META/info.json']=json.dumps(info,indent=2).encode()
    assert {n for n in before if before[n]!=after[n]}=={'META/info.json'}
    archive=OUT/'Braum_Clash_New_UI_Icons_v1.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(after.items()):z.writestr(n,b)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None and set(z.namelist())==set(after) and all(z.read(n)==b for n,b in after.items())
    sys.path.insert(0,str(ROOT/'audit/scratch/python_lib'));from xxhash import xxh64_hexdigest
    validation=OUT/'validation';p.run(['C:/Users/etqdo/Downloads/cslol-go/cslol-tools/mod-tools.exe','import',archive,validation/'imported'])
    for path,data in added.items():
        key=xxh64_hexdigest(path.encode());dest=validation/key
        p.run(['C:/Users/etqdo/Downloads/wadtools-0.5.7-windows-x64/wadtools.exe','--config',ROOT/'work/config/wadtools.toml','--hashtable-dir',ROOT/'work/cache/hashes','--progress=false','extract','-i',validation/'imported/WAD/Braum.wad.client','-o',dest,'--no-bin-paths','--hash',key])
        matches=[f for f in dest.rglob('*') if f.is_file() and f.stem==key];assert len(matches)==1 and matches[0].read_bytes()==data
    report=dict(status='PASS icon format/dimensions/portrait alpha/package/isolated paths; UI gameplay pending',archive=archive.relative_to(ROOT).as_posix(),sha256=p.sha(archive),parent_sha256=p.sha(parent),checks=checks,added_paths=list(added),protected='Every accepted parent payload byte-exact. No BIN, gameplay texture/model, VFX, audio, VO, or loading portrait changes.',reused='User explicitly accepts everything in audio_3x_v1; all previous gameplay/media/geometry evidence retained. Only seven HUD images added.',runtime='Confirm HUD/minimap/scoreboard portrait and passive/Q/W/E/R icons render correctly.')
    (ROOT/'validation/ui_icons_v1_build.json').write_text(json.dumps(report,indent=2));(ROOT/'validation/ui_icons_v1_logs.json').write_text(json.dumps(p.logs,indent=2))
    print(json.dumps({k:report[k] for k in ['status','archive','sha256']},indent=2))
if __name__=='__main__':main()
