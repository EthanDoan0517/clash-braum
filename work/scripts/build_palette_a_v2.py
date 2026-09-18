"""Palette A v2 on the current integrated candidate; texture-only, no model export."""
import json, zipfile
import numpy as np
from PIL import Image
import build_lightning_trial as p
ROOT=p.ROOT;OUT=ROOT/'build/palette_a_v2'
PARENT=ROOT/'build/strike_vo_v1/Braum_Clash_Travelling_Strikes_English_VO_v1.fantome'


def paint(source,kind):
    a=np.array(source.convert('RGBA'));h,w=a.shape[:2]
    result=a.copy();occupied=np.zeros((h,w),bool);changed=np.zeros((h,w),bool)
    stats={}
    for file in sorted((ROOT/'build/palette_a_inputs').glob('*.npy')):
        shield=file.stem.startswith('CCE_')
        if shield != (kind=='shield_frame'):continue
        count=0
        for tri in np.load(file):
            uv=tri[:,:2]*[w-1,-(h-1)]+[0,h-1]
            x0,y0=np.maximum(np.floor(uv.min(0)).astype(int),0)
            x1,y1=np.minimum(np.ceil(uv.max(0)).astype(int),[w-1,h-1])
            yy,xx=np.mgrid[y0:y1+1,x0:x1+1]
            v0,v1=uv[1]-uv[0],uv[2]-uv[0]
            det=v0[0]*v1[1]-v1[0]*v0[1]
            if abs(det)<1e-8:continue
            dx,dy=xx-uv[0,0],yy-uv[0,1]
            b1=(dx*v1[1]-dy*v1[0])/det;b2=(v0[0]*dy-v0[1]*dx)/det
            inside=(b1>=-.001)&(b2>=-.001)&(b1+b2<=1.001)
            if not inside.any():continue
            y=yy[inside];x=xx[inside]
            weights=np.stack([1-b1[inside]-b2[inside],b1[inside],b2[inside]],1)
            xyz=weights@tri[:,2:5];normal=weights@tri[:,5:8]
            normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-8)
            # A restrained baked top-light adds broad form without moving UVs.
            light=np.clip(.91+.19*normal[:,2]-.055*normal[:,1],.70,1.15)
            old=a[y,x,:3].astype(float);lum=old@[.2126,.7152,.0722]
            detail=np.clip(lum/np.maximum(np.median(lum),25),.62,1.28)
            shade=light*(.72+.28*detail)
            n=file.stem;edit=np.ones(len(x),bool)
            if shield:
                # Frame only: smoked glass and all electrical textures are separate.
                rim=(np.abs(xyz[:,0]+1.791)>.282)|(xyz[:,2]<.115)|(xyz[:,2]>.67)
                rgb=np.where(rim[:,None],np.array([190,211,225]),np.array([42,66,94]))*shade[:,None]
                if file.stem=='CCE_mesh_13.001':rgb=np.array([87,119,145])*shade[:,None]
            elif n=='Object002':
                rgb=np.array([41,77,145])*shade[:,None]
                # Retain pale lettering/checker detail and original collar fabric.
                neutral=(old.max(1)-old.min(1)<24)&(lum>105)
                rgb[neutral]=old[neutral]
            elif n=='Object004':
                sleeves=xyz[:,2]>1.30
                rgb=np.where(sleeves[:,None],np.array([202,217,228]),np.array([27,38,55]))*shade[:,None]
                # Police sleeve badge stays legible.
                badge=(old.max(1)-old.min(1)<25)&(lum>115)
                rgb[badge]=old[badge]
            elif n=='Object001':
                rgb=np.array([29,41,60])*shade[:,None]
            elif n=='Object006':
                rgb=np.array([38,51,73])*shade[:,None]
            elif n=='Object007':
                rgb=np.array([94,124,156])*shade[:,None]
            elif n=='hjhjh_2':
                rgb=np.array([35,51,75])*shade[:,None]
            elif n=='hjhjh_4':
                # Painted close crop: no new hair geometry, rig or silhouette.
                hairline=1.863+.037*np.clip(-xyz[:,1]/.11,0,1)
                edit=xyz[:,2]>hairline
                curl=.5+.5*np.sin(xyz[:,0]*1250)*np.sin(xyz[:,1]*1250)*np.sin(xyz[:,2]*1250)
                rgb=np.array([21,24,29])[None,:]*(.8+.5*curl[:,None])*light[:,None]
            else:
                edit[:]=False;rgb=old
            occupied[y,x]=True
            result[y[edit],x[edit],:3]=np.clip(np.rint(rgb[edit]),0,255).astype(np.uint8)
            changed[y[edit],x[edit]]=True;count+=int(edit.sum())
        stats[file.stem]=count
    # Pad islands for minification, never paint over another mapped island.
    filled=occupied.copy();eligible=changed.copy();pad=np.zeros_like(occupied)
    for _ in range(5):
        oldeligible=eligible.copy();oldresult=result.copy()
        for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
            donor=np.roll(oldeligible,(dy,dx),(0,1));available=~filled&donor
            available[[0,-1],:]=False;available[:,[0,-1]]=False
            result[available,:3]=np.roll(oldresult,(dy,dx),(0,1))[available,:3]
            filled[available]=True;eligible[available]=True;pad|=available
    assert np.array_equal(a[:,:,3],result[:,:,3])
    assert np.array_equal(a[~(changed|pad)],result[~(changed|pad)])
    return Image.fromarray(result),stats


def main():
    assert not (OUT/'Braum_Clash_Palette_A_Cobalt_Ivory_v2.fantome').exists(),'Preserve completed candidate.'
    assert p.sha(PARENT)=='3c48b0ad64981b26a733502b35a10bad7e26a23ad5f8c52e8b7a9d1b5a236655'
    OUT.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(PARENT) as z:
        assert z.testzip() is None
        before={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
    after=before.copy();checks=[]
    for kind in ['body','shield_frame']:
        member='WAD/Braum.wad.client/'+p.ASSET+kind+'.tex'
        original=OUT/(kind+'_parent.tex');original.write_bytes(before[member])
        parentpng=OUT/(kind+'_parent.png');p.run([p.TEX,'decode',original,'-o',parentpng])
        painted,stats=paint(Image.open(parentpng),kind)
        png=OUT/(kind+'.png');painted.save(png)
        target=OUT/(kind+'.tex');p.run([p.TEX,'encode',png,'-o',target,'-f','bc3','--generate-mipmaps'])
        # BC3 alpha blocks are independent of RGB. Retain original compressed
        # alpha at every mip, avoiding decode/re-encode quantization changes.
        prior=original.read_bytes();encoded=bytearray(target.read_bytes())
        assert encoded[:12]==prior[:12] and encoded[:4]==b'TEX\x00'
        assert len(encoded)==len(prior) and (len(encoded)-12)%16==0
        for offset in range(12,len(encoded),16):encoded[offset:offset+8]=prior[offset:offset+8]
        target.write_bytes(encoded)
        mips=[]
        for mip in [0,2,4]:
            oldpath=OUT/f'{kind}_parent_mip{mip}.png';newpath=OUT/f'{kind}_mip{mip}.png'
            p.run([p.TEX,'decode',original,'-o',oldpath,'--mipmap',mip])
            p.run([p.TEX,'decode',target,'-o',newpath,'--mipmap',mip])
            old=np.array(Image.open(oldpath).convert('RGBA'));new=np.array(Image.open(newpath).convert('RGBA'))
            assert old.shape==new.shape
            assert np.array_equal(old[:,:,3],new[:,:,3]),(kind,mip,'alpha mismatch')
            mips.append(dict(mip=mip,dimensions=list(new.shape[:2]),alpha_exact=True))
        after[member]=target.read_bytes()
        checks.append(dict(texture=kind,source_sha256=p.sha(original),output_sha256=p.sha(target),mips=mips,painted_samples=stats))
    info=json.loads(before['META/info.json'])
    info.update(Name='Clash Braum Palette A Cobalt Ivory v2 TRIAL',Version='0.4.1-palette-a',Description='Cobalt armor, ivory sleeves, navy kit, silver shield edges over dark lower panel and painted close-cropped hair. Current travelling-strikes VFX and English VO/audio preserved. Manual gameplay acceptance pending.')
    after['META/info.json']=json.dumps(info,indent=2).encode()
    changed={n for n in before if before[n]!=after[n]}
    assert changed=={'META/info.json'}|{'WAD/Braum.wad.client/'+p.ASSET+k+'.tex' for k in ['body','shield_frame']}
    archive=OUT/'Braum_Clash_Palette_A_Cobalt_Ivory_v2.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for n,data in sorted(after.items()):z.writestr(n,data)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(before)
        assert all(z.read(n)==data for n,data in after.items())
    report=dict(status='PASS affected texture encoding/alpha/mips and package; visual review and gameplay pending',archive=str(archive.relative_to(ROOT)),sha256=p.sha(archive),parent_sha256=p.sha(PARENT),textures=checks,changed_members=sorted(changed),protected='All other archive members byte-identical: accepted geometry/rig/exports, E, other VFX, glass, English VO and louder Q/R.',reused='strike_vo_v1 package/backend, geometry/rig and audio evidence: byte-identical members and identical path set. No repeated geometry, BIN or backend conversion.',limitations='Palette concept adapted to existing geometry. Hair is painted close crop, not raised curls. Texture shading is broad normal-based form/detail, not a new sculpt or full texture rebake.',inputs={f.name:p.sha(f) for f in (ROOT/'build/palette_a_inputs').glob('*.npy')})
    (ROOT/'validation/palette_a_v2_build.json').write_text(json.dumps(report,indent=2))
    (ROOT/'validation/palette_a_v2_build_logs.json').write_text(json.dumps(p.logs,indent=2))
    print(json.dumps({k:report[k] for k in ['status','archive','sha256']},indent=2))

if __name__=='__main__':main()
