"""Refine feedback on logos, equipment contrast, projectile size and R density."""
import json,re,zipfile
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
import build_lightning_trial as p
from build_readability_v1 import emitters,name,guard,color,replace_texture,PREFIX
ROOT=p.ROOT;OUT=ROOT/'build/refinement_v2'


def main():
    assert not OUT.exists(),'Preserve candidate.'
    parent=ROOT/'build/readability_v1/Braum_Clash_Readability_v1.fantome'
    assert p.sha(parent)=='94b1270c8e3dd297b1d5d2f00c2a0cfabb3d19e9c72d39a2c2f7f20cc832b939'
    OUT.mkdir(parents=True);package=OUT/'package'
    with zipfile.ZipFile(parent) as z:
        assert z.testzip() is None;z.extractall(package)
        original_files={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
    wad=package/'WAD/Braum.wad.client';assets=wad/p.ASSET
    texture_checks=[]
    def encode(img,key,path,alpha_reference=None,mips=(0,2)):
        png=OUT/(key+'.png');img.save(png);p.run([p.TEX,'encode',png,'-o',path,'-f','bc3','--generate-mipmaps'])
        for mip in mips:
            dest=OUT/f'{key}_mip{mip}.png';p.run([p.TEX,'decode',path,'-o',dest,'--mipmap',mip])
            decoded=np.array(Image.open(dest).convert('RGBA'))
            assert decoded.shape[:2]==(img.height>>mip,img.width>>mip)
            if alpha_reference:
                old=np.array(Image.open(ROOT/alpha_reference.format(mip=mip)).convert('RGBA'));assert np.array_equal(old[:,:,3],decoded[:,:,3])
        texture_checks.append(dict(key=key,sha256=p.sha(path),mips=list(mips),alpha_exact=bool(alpha_reference)))
    # W is a single-color contour; all original holes remain transparent.
    full=np.array(Image.open(ROOT/'build/clash_passive_v1/full.png').convert('RGBA'))
    a=Image.fromarray(full[:,:,3]);eroded=np.array(a.filter(ImageFilter.MinFilter(5)))
    outline=np.maximum(full[:,:,3].astype(int)-eroded.astype(int),0)
    w=np.zeros_like(full);w[:,:,:3]=[80,165,245];w[:,:,3]=np.rint(outline*.35).astype(np.uint8)
    assert not w[:,:,3][full[:,:,3]==0].any()
    encode(Image.fromarray(w),'w_outline',assets/'w_outline.tex')
    # Passive uses light blue outlines and dark blue interior/checker spaces.
    base_alpha=full[:,:,3];support=np.zeros_like(base_alpha)
    for y,row in enumerate(base_alpha):
        xs=np.flatnonzero(row)
        if len(xs):support[y,xs[0]:xs[-1]+1]=255
    support[:,126:130]=0;support[126:130,:]=0
    rgb=np.zeros_like(full[:,:,:3]);rgb[:]=[15,42,92]
    bright=full[:,:,1]>110;ring=(base_alpha>0)&~bright
    rgb[ring]=[24,79,165];rgb[bright]=[90,178,248]
    yy,xx=np.indices(support.shape);qs=[(xx>=130)&(yy<126),(xx>=130)&(yy>=130),(xx<126)&(yy>=130),(xx<126)&(yy<126)]
    imgs={'full':Image.fromarray(np.dstack([rgb,support])),'base':Image.fromarray(np.dstack([rgb,np.rint(support*.17).astype(np.uint8)]))}
    for i,q in enumerate(qs,1):imgs[f'quarter_{i}']=Image.fromarray(np.dstack([rgb,np.where(q,support,0).astype(np.uint8)]))
    imgs['warning']=Image.fromarray(np.dstack([rgb,np.where(qs[0]|qs[1]|qs[2],support,0).astype(np.uint8)]))
    assert np.array_equal(sum(np.array(imgs[f'quarter_{i}'])[:,:,3].astype(int) for i in range(1,5)),support)
    for key,img in imgs.items():encode(img,'passive_'+key,assets/'passive'/f'{key}.tex')
    sheet=Image.new('RGB',(1280,280),'#101827');draw=ImageDraw.Draw(sheet)
    for i,img in enumerate([imgs['quarter_1'],imgs['quarter_2'],imgs['quarter_3'],imgs['full'],Image.fromarray(w)]):
        tile=Image.new('RGBA',(256,256),'#101827');tile.alpha_composite(img);sheet.paste(tile.convert('RGB'),(i*256,24));draw.text((i*256+8,6),['Quarter 1','Quarter 2','Quarter 3','Full passive','Faint W outline'][i],fill='white')
    sheet.save(OUT/'logos.png')
    # Texture-only outfit accents from existing per-object atlas UVs.
    groups=json.loads((ROOT/'validation/equipment_atlas/groups.json').read_text())
    targets={'Object007':np.array([.34,.47,.59]),'hjhjh_2':np.array([.38,.41,.34]),'Object006':np.array([.30,.35,.41])}
    src=ROOT/'build/color_pop_v3/body.png';body=np.array(Image.open(src).convert('RGBA'));result=body.copy();size=body.shape[0]
    masks={};protected=Image.new('L',(size,size));pd=ImageDraw.Draw(protected)
    for g in groups:
        mask=Image.new('L',(size,size));d=ImageDraw.Draw(mask)
        for poly in g['polygons']:
            points=[(u*(size-1),(1-v)*(size-1)) for u,v in poly['uv']];d.polygon(points,fill=255)
            if g['name'] not in targets:pd.polygon(points,fill=255)
        if g['name'] in targets:masks[g['name']]=mask
    locked=np.array(protected)>0;union=np.zeros((size,size),bool);stats=[]
    for group,target in targets.items():
        mask=np.array(masks[group].filter(ImageFilter.MaxFilter(9)))>0;mask&=~locked;union|=mask
        old=body[:,:,:3].astype(float)/255
        # Lift tools/pouches to separate material families, retaining source detail.
        lifted=np.clip(old*.55+target*.65,0,1)
        result[:,:,:3][mask]=np.rint(lifted[mask]*255).astype(np.uint8)
        masks[group].save(OUT/(group+'_mask.png'));stats.append(dict(group=group,pixels=int(mask.sum()),target=target.tolist()))
    assert np.array_equal(body[:,:,3],result[:,:,3]) and np.array_equal(body[~union],result[~union])
    assert not (union&locked).any()
    encode(Image.fromarray(result),'body',assets/'body.tex','build/color_pop_v3/body_mip{mip}.png',(0,2,4))
    # Apply bounded emitter edits and preserve everything outside their fields.
    source=ROOT/'build/readability_v1/skin0.ritobin';text=source.read_text();before=p.entries(text)
    crackle=p.entries((ROOT/'build/crackle_v1/skin0.ritobin').read_text());changed={}
    binpath=wad/'data/characters/braum/skins/skin0.bin';p.run([p.RITO,'-i','text','-o','bin','-k',source,OUT/'parent.bin']);assert p.sha(OUT/'parent.bin')==p.sha(binpath)
    for short in ['Braum_Q_mis','Braum_W_Shield_buf','Braum_E_Shield_cas','Braum_R_mis','Braum_R_Small_mis','Braum_R_PBAOE_Cas']:
        key=PREFIX+short;e=before[key]
        for lo,hi,b in reversed(emitters(e)):
            n=name(b);new=b
            if short=='Braum_Q_mis' and n.startswith('Clash_Q_Electric_'):
                for a,z,v in reversed(list(p.blocks(new,r'^                BirthScale0: embed = ValueVector3 \{'))):
                    v=re.sub(r'ConstantValue: vec3 = \{ ([^}]+) \}',lambda m:'ConstantValue: vec3 = { '+', '.join(format(float(x)*2.5,'.9g') for x in m.group(1).split(','))+' }',v);new=new[:a]+v+new[z:]
                guard(b,new,['BirthScale0'])
            elif short=='Braum_W_Shield_buf' and n=='Decal_shield':
                new=replace_texture(b,p.ASSET+'w_outline.tex');new=new.replace('{ 125, 125, 0 }','{ 80, 80, 0 }');guard(b,new,['Texture','BirthScale0'])
            elif short=='Braum_E_Shield_cas' and n in ['Inchant_shield','Inchant_shield_2']:
                new=color(b,(1,1,1),1.35) if n=='Inchant_shield' else color(b,(.12,.30,.7),.85);guard(b,new,['Color'])
            elif short.startswith('Braum_R_') and n=='line':
                new=b.replace('ConstantValue: f32 = 20\n','ConstantValue: f32 = 60\n',1);guard(b,new,['Rate'])
            e=e[:lo]+new+e[hi:]
        if short.startswith('Braum_R_'):
            restore=[]
            for _,_,b in emitters(crackle[key]):
                if name(b) in ['cracks_left','cracks_right']:restore.append(b)
                elif name(b)=='Frozen':
                    new=b.replace('EmitterName: string = "Frozen"','EmitterName: string = "Clash_R_Ground_Arc"');new=color(new,(.94,.98,1),.8)
                    new=new.replace('Pass: i16 = -52','Pass: i16 = -51');guard(b,new,['EmitterName','Color','Pass']);restore.append(new)
            marker='        ComplexEmitterDefinitionData: list[pointer] = {';assert e.count(marker)==1;e=e.replace(marker,marker+'\n'+'\n'.join(restore),1)
            for _,_,b in emitters(before[key]):
                if name(b) in ['Frozen','GroundBurn']:assert b in e
        if e!=before[key]:changed[key]=e;text=text.replace(before[key],e)
    after=p.entries(text);assert before.keys()==after.keys();assert {k for k in before if before[k]!=after[k]}==changed.keys()
    trial=OUT/'skin0.ritobin';trial.write_text(text);p.run([p.RITO,'-i','text','-o','bin','-k',trial,binpath]);p.run([p.RITO,'-i','bin','-o','text',binpath,OUT/'verified.ritobin']);p.run([p.RITO,'-i','text','-o','bin','-k',OUT/'verified.ritobin',OUT/'verified.bin']);assert p.sha(binpath)==p.sha(OUT/'verified.bin')
    # Raise the subject by cropping excess top, without adding a blank bottom.
    art=Image.open(ROOT/'clash new.avif').convert('RGB');portrait=art.crop((401,40,724,627)).resize((308,560),Image.Resampling.LANCZOS)
    encode(portrait,'loading',wad/'assets/characters/braum/skins/base/braumloadscreen.tex')
    meta=package/'META/info.json';info=json.loads(meta.read_text());info.update(Name='Clash Braum Refinement v2 TRIAL',Version='0.3.4-refinement',Description='Smaller faint outline W, blue passive, larger Q core, restored R bolts/dark floor, higher portrait and contrasting equipment. Manual gameplay approval pending.');meta.write_text(json.dumps(info,indent=2))
    actual={f.relative_to(package).as_posix():f.read_bytes() for f in package.rglob('*') if f.is_file()}
    assert actual.keys()-original_files.keys()=={'WAD/Braum.wad.client/'+p.ASSET+'w_outline.tex'}
    allowed={'META/info.json','WAD/Braum.wad.client/data/characters/braum/skins/skin0.bin','WAD/Braum.wad.client/assets/characters/braum/skins/base/braumloadscreen.tex','WAD/Braum.wad.client/'+p.ASSET+'body.tex'}|{'WAD/Braum.wad.client/'+p.ASSET+'passive/'+k+'.tex' for k in imgs}
    assert {n for n in original_files if actual[n]!=original_files[n]}<=allowed
    archive=OUT/'Braum_Clash_Refinement_v2.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for n,data in sorted(actual.items()):z.writestr(n,data)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None and all(z.read(n)==data for n,data in actual.items())
    report=dict(status='PASS targeted build; gameplay pending',archive=str(archive.relative_to(ROOT)),sha256=p.sha(archive),parent_sha256=p.sha(parent),textures=texture_checks,equipment_masks=stats,
      changes=['W 125->80 scale, alpha-texture outline .35 with holes transparent','Passive light blue/dark blue, outside and quadrant gaps transparent','Q core/shell 2.5x scale','E white core vs deeper blue second surface','R line 60 vs original 80, ground/side bolts restored over exact dark floor','Clash portrait cropped 40px higher','Tools/pouches/straps recolored through object UV masks; trousers protected'],
      protected='Other entries, model/rig, spell timings/attachments, dark R floor and source body alpha unchanged.',reused='Unchanged geometry/rig and crackle atlas evidence.',
      payloads=[dict(path=f.relative_to(wad).as_posix(),sha256=p.sha(f)) for f in sorted(wad.rglob('*')) if f.is_file()])
    (ROOT/'validation/refinement_v2_build.json').write_text(json.dumps(report,indent=2));(ROOT/'validation/refinement_v2_build_logs.json').write_text(json.dumps(p.logs,indent=2));print(json.dumps({k:report[k] for k in ['status','archive','sha256','changes']},indent=2))


if __name__=='__main__':main()
