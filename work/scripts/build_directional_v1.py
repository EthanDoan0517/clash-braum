"""Directional Q, balanced E edges, connected glowing W and two main R bolt layers."""
import json,re,zipfile,struct
import numpy as np
from PIL import Image,ImageOps,ImageFilter
import build_lightning_trial as p
from build_readability_v1 import emitters,name,guard,color,replace_texture,strip,PREFIX
ROOT=p.ROOT;OUT=ROOT/'build/directional_v1'


def mirrored_scb(source,target):
    old=source.read_bytes();data=bytearray(old)
    assert old[:8]==b'r3d2Mesh' and struct.unpack_from('<HH',old,8)==(3,2)
    nv,nf,flags=struct.unpack_from('<III',old,140);vt=struct.unpack_from('<I',old,176)[0];off=180
    verts=np.array(struct.unpack_from('<'+str(nv*3)+'f',old,off)).reshape(-1,3)
    center=float(verts[:,2].min()+verts[:,2].max());reflected=verts.copy();reflected[:,2]=center-verts[:,2]
    assert np.isfinite(reflected).all()
    assert np.allclose(verts.min(0),reflected.min(0)) and np.allclose(verts.max(0),reflected.max(0))
    for i,v in enumerate(reflected):struct.pack_into('<3f',data,off+i*12,*v)
    off+=nv*12+(nv*4 if vt==1 else 0)
    pivot=list(struct.unpack_from('<3f',old,off));pivot[2]=center-pivot[2];struct.pack_into('<3f',data,off,*pivot);off+=12
    for i in range(nf):
        ids=struct.unpack_from('<3I',old,off);assert max(ids)<nv
        struct.pack_into('<3I',data,off,ids[0],ids[2],ids[1])
        uv=struct.unpack_from('<6f',old,off+76);struct.pack_into('<6f',data,off+76,uv[0],uv[2],uv[1],uv[3],uv[5],uv[4])
        # Reflection + winding reversal keeps outward-facing triangles and area.
        a,b,c=verts[list(ids)];aa,bb,cc=reflected[[ids[0],ids[2],ids[1]]]
        normal=np.cross(b-a,c-a);expected=normal*np.array([1,1,-1]);newnormal=np.cross(bb-aa,cc-aa)
        assert np.allclose(expected,newnormal,atol=.001)
        assert old[off+12:off+76]==data[off+12:off+76]
        off+=100
    assert off==len(old);target.write_bytes(data)
    return dict(vertices=nv,faces=nf,reflection_axis='native Z (horizontal across shield before native Y rotation)',bounds_preserved=True,areas_and_winding_verified=True,source_sha256=p.sha(source),output_sha256=p.sha(target))


def main():
    assert not OUT.exists(),'Preserve candidate.'
    parent=ROOT/'build/sfx_v2_refinement/Braum_Clash_Refinement_SFX_v2.fantome'
    assert p.sha(parent)=='fba996378d8961d525a7abc3ce43c9fa09d3fb7361fb35b37121cc0efb33c622'
    OUT.mkdir(parents=True);package=OUT/'package'
    with zipfile.ZipFile(parent) as z:
        assert z.testzip() is None;z.extractall(package)
        previous={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
    wad=package/'WAD/Braum.wad.client';assets=wad/p.ASSET
    mesh_path=p.ASSET+'e_right_edge.scb'
    mesh_check=mirrored_scb(ROOT/'Braum.wad/54b4111fcf3b367a.scb',wad/mesh_path)
    # Recreate connected original logo, without passive quadrant divider gaps.
    logo=Image.open(ROOT/'work/textures/passive_clash/source_logo.png').convert('RGB')
    bbox=logo.convert('L').point(lambda v:255 if v>5 else 0).getbbox();logo=ImageOps.contain(logo.crop(bbox),(232,232),Image.Resampling.LANCZOS)
    canvas=Image.new('RGB',(256,256));canvas.paste(logo,((256-logo.width)//2,(256-logo.height)//2))
    intensity=np.array(canvas).max(2);coverage=Image.fromarray(np.rint(np.clip(intensity.astype(float)/30,0,1)*255).astype(np.uint8))
    closed=coverage.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    edge=np.maximum(np.array(closed).astype(float)-np.array(closed.filter(ImageFilter.MinFilter(5))).astype(float),0)
    halo=np.array(Image.fromarray(edge.astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2))).astype(float)
    alpha=np.rint(np.clip(edge*.35+halo*.22,0,255)).astype(np.uint8)
    rgba=np.zeros((256,256,4),np.uint8);rgba[:,:,:3]=[80,165,245];rgba[:,:,3]=alpha
    Image.fromarray(rgba).save(OUT/'w_outline.png')
    p.run([p.TEX,'encode',OUT/'w_outline.png','-o',assets/'w_outline.tex','-f','bc3','--generate-mipmaps'])
    for mip in (0,2):
        decoded=OUT/f'w_outline_mip{mip}.png';p.run([p.TEX,'decode',assets/'w_outline.tex','-o',decoded,'--mipmap',mip]);im=Image.open(decoded).convert('RGBA')
        assert im.size==(256>>mip,256>>mip) and im.getpixel((0,0))[3]==0
    # Central split no longer intentionally erased; broad holes stay transparent.
    assert alpha[:,126:130].max()>50 and alpha[126:130,:].max()>50
    assert alpha[90,128]==0  # Center of upper opening, beyond the inward halo.
    preview=Image.new('RGBA',(256,256),'#101827');preview.alpha_composite(Image.fromarray(rgba));preview.convert('RGB').save(OUT/'w_preview.png')
    source=ROOT/'build/refinement_v2/skin0.ritobin';text=source.read_text();before=p.entries(text)
    binpath=wad/'data/characters/braum/skins/skin0.bin';p.run([p.RITO,'-i','text','-o','bin','-k',source,OUT/'parent.bin']);assert p.sha(OUT/'parent.bin')==p.sha(binpath)
    changed={};changes=[]
    key=PREFIX+'Braum_E_Shield_cas';e=before[key];left=next(b for _,_,b in emitters(e) if name(b)=='Inchant_shield')
    right=left.replace('EmitterName: string = "Inchant_shield"','EmitterName: string = "Clash_E_Right_Edge"')
    right=right.replace('ASSETS/Characters/Braum/Skins/Base/Particles/Braum_Base_E_shield_inchant.scb',mesh_path)
    # Alternate start frame already random; same intensity/binding/scale as good edge.
    guard(left,right,['EmitterName','Primitive'])
    marker='        ComplexEmitterDefinitionData: list[pointer] = {';assert e.count(marker)==1
    changed[key]=e.replace(marker,marker+'\n'+right,1);assert all(b in changed[key] for _,_,b in emitters(e))
    changes.append('E: added mirrored right-edge emitter; original left edge and all current E behavior unchanged.')
    # Use the native 3D missile-head carrier/orientation, never a camera-facing quad.
    native=p.entries((ROOT/'build/lightning_v1/core/skin0.ritobin').read_text())
    key=PREFIX+'Braum_Q_mis';e=before[key];native_head=next(b for _,_,b in emitters(native[key]) if name(b)=='Ice_head')
    primitive=next(b for _,_,b in p.blocks(native_head,r'^                Primitive: [^\n]*\{'))
    rotation=next(b for _,_,b in p.blocks(native_head,r'^                BirthRotation0: [^\n]*\{'))
    for a,z,b in reversed(emitters(e)):
        n=name(b)
        if n not in {'Clash_Q_Electric_Core','Clash_Q_Electric_Arc'}:continue
        new=strip(b,['BirthScale0'])
        scale=(1.35,1.35,2.5) if n.endswith('Core') else (1.6,1.6,2.8)
        extra=primitive+'\n'+rotation+'\n                BirthScale0: embed = ValueVector3 {\n                    ConstantValue: vec3 = { '+', '.join(map(str,scale))+' }\n                }\n                DisableBackfaceCull: bool = true\n'
        new=new.rsplit('\n',1)[0]+'\n'+extra+'            }'
        assert 'ParticleIsLocalOrientation: flag = true' in new
        assert 'BirthRotationalVelocity0:' not in new
        guard(b,new,['Primitive','BirthRotation0','BirthScale0','DisableBackfaceCull'])
        e=e[:a]+new+e[z:]
    changed[key]=e;changes.append('Q: core and arc now native 3D missile-head meshes with native local rotation and fixed direction; no free spin or camera-facing geometry.')
    # Keep just the two existing side arcs on the main R; secondary/cast placement
    # effects keep their dark ground without spawning further bolts.
    for short in ['Braum_R_mis','Braum_R_Small_mis','Braum_R_PBAOE_Cas']:
        key=PREFIX+short;e=before[key]
        for a,z,b in reversed(emitters(e)):
            n=name(b)
            remove=n in {'line','Clash_R_Ground_Arc'} or short!='Braum_R_mis' and n in {'cracks_left','cracks_right'}
            if remove:
                assert not re.search(r'(?i)(sound|audio|child|event)',b)
                e=e[:a]+e[z:]
        for _,_,b in emitters(before[key]):
            if name(b) in {'Frozen','GroundBurn'}:assert b in e
        changed[key]=e
    main_r=changed[PREFIX+'Braum_R_mis'];assert {name(b) for _,_,b in emitters(main_r) if 'crackle_atlas.tex' in b}=={'cracks_left','cracks_right'}
    changes.append('R: only two main side-bolt layers retained; dense line/ground arcs and secondary bolts removed; dark floor exact.')
    for key,e in changed.items():text=text.replace(before[key],e)
    after=p.entries(text);assert before.keys()==after.keys() and {k for k in before if before[k]!=after[k]}==changed.keys()
    trial=OUT/'skin0.ritobin';trial.write_text(text);p.run([p.RITO,'-i','text','-o','bin','-k',trial,binpath]);p.run([p.RITO,'-i','bin','-o','text',binpath,OUT/'verified.ritobin']);p.run([p.RITO,'-i','text','-o','bin','-k',OUT/'verified.ritobin',OUT/'verified.bin']);assert p.sha(binpath)==p.sha(OUT/'verified.bin')
    meta=package/'META/info.json';info=json.loads(meta.read_text());info.update(Name='Clash Braum Directional v1 + SFX v2 TRIAL',Version='0.3.5-directional',Description='Balanced E edges, connected softly glowing W, directional 3D Q and two main R bolt layers. Existing SFX v2 retained unchanged.');meta.write_text(json.dumps(info,indent=2))
    actual={f.relative_to(package).as_posix():f.read_bytes() for f in package.rglob('*') if f.is_file()}
    assert actual.keys()-previous.keys()=={'WAD/Braum.wad.client/'+mesh_path}
    assert {n for n in previous if actual[n]!=previous[n]}=={'META/info.json','WAD/Braum.wad.client/data/characters/braum/skins/skin0.bin','WAD/Braum.wad.client/'+p.ASSET+'w_outline.tex'}
    refs=set(re.findall(r'"(assets/characters/braum/skins/base/braum_clash/[^"]+)"',text,re.I));assert all((wad/r.lower()).is_file() for r in refs)
    archive=OUT/'Braum_Clash_Directional_v1_SFX_v2.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for n,data in sorted(actual.items()):z.writestr(n,data)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None and all(z.read(n)==data for n,data in actual.items())
    report=dict(status='PASS affected offline checks; gameplay pending',archive=str(archive.relative_to(ROOT)),sha256=p.sha(archive),parent_sha256=p.sha(parent),changes=changes,mesh=mesh_check,
      W='Source logo without quadrant splits; continuous contour with 2.2px Gaussian halo inward/outward, same blue RGB and restrained alpha. Mip0/2 checked.',
      protected='Accepted character SKN/SKL, model/texture colors, passive, loading art, SFX v2 bank bytes and unchanged events exact. Existing E left-side and R ground unchanged.',
      reused='SFX v2 evidence and all unchanged visual assets; no audio decode or character deformation checks repeated.',
      payloads=[dict(path=f.relative_to(wad).as_posix(),sha256=p.sha(f)) for f in sorted(wad.rglob('*')) if f.is_file()])
    (ROOT/'validation/directional_v1_build.json').write_text(json.dumps(report,indent=2));(ROOT/'validation/directional_v1_build_logs.json').write_text(json.dumps(p.logs,indent=2));print(json.dumps({k:report[k] for k in ['status','archive','sha256','changes']},indent=2))


if __name__=='__main__':main()
