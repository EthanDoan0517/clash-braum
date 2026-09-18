"""W glow, connected travelling R strikes/craters, and isolated Q/R ice cast removal."""
import json,re,zipfile,struct
import numpy as np
import build_lightning_trial as p
from build_readability_v1 import emitters,name,strip,guard,color,PREFIX
ROOT=p.ROOT;OUT=ROOT/'build/strike_v1'
GLOW='ASSETS/Characters/Braum/Skins/Base/Particles/Braum_Base_I_shield_glow.tex'

def field(n,t,value):return f'                {n}: {t} = {value}\n'
def val(n,t,value):return field(n,'embed',f'Value{t} {{\n                    ConstantValue: '+({'Float':'f32','Vector3':'vec3'}[t])+f' = {value}\n                }}')
def add(b,extra):return b.rsplit('\n',1)[0]+'\n'+extra+'            }'
def mesh(path,points,width):
    # Crossed ribbons share every polyline endpoint, so the silhouette is connected
    # from above and at shallow game-camera angles. Constant central glow UVs.
    vertices=[];faces=[]
    for a,b in zip(points,points[1:]):
        a=np.array(a,float);b=np.array(b,float);d=b-a;d/=np.linalg.norm(d)
        ref=np.array([0.,1.,0.]) if abs(d[1])<.9 else np.array([1.,0.,0.])
        u=np.cross(d,ref);u/=np.linalg.norm(u);v=np.cross(d,u)
        for axis in [u,v]:
            j=len(vertices);vertices.extend([a-axis*width,b-axis*width,b+axis*width,a+axis*width]);faces.extend([(j,j+1,j+2),(j,j+2,j+3)])
    vs=np.array(vertices);lo=vs.min(0);extent=vs.max(0)-lo
    header=b'r3d2Mesh'+struct.pack('<HH',3,2)+b'Clash lightning'.ljust(128,b'\0')+struct.pack('<III',len(vs),len(faces),0)+struct.pack('<6f',*lo,*extent)+struct.pack('<I',0)
    data=header+vs.astype('<f4').tobytes()+struct.pack('<3f',0,0,0)
    for ids in faces:
        a,b,c=vs[list(ids)];assert np.linalg.norm(np.cross(b-a,c-a))>.001
        data+=struct.pack('<3I',*ids)+b'lightning'.ljust(64,b'\0')+struct.pack('<6f',.5,.5,.5,.5,.5,.5)
    assert len(data)==180+len(vs)*12+12+len(faces)*100 and np.isfinite(vs).all()
    path.write_bytes(data)
    return dict(path=path.name,vertices=len(vs),faces=len(faces),bounds=[lo.tolist(),vs.max(0).tolist()],connected_centerline=True,nondegenerate=True,sha256=p.sha(path))

def mesh_primitive(path):return field('Primitive','pointer','VfxPrimitiveMesh {\n                    mMesh: embed = VfxMeshDefinitionData {\n                        mSimpleMeshName: string = "'+path+'"\n                    }\n                }')
def offset(x,y=0,z=0):return field('SpawnShape','pointer','VfxShapeLegacy {\n                    EmitOffset: embed = ValueVector3 {\n                        ConstantValue: vec3 = { '+f'{x}, {y}, {z}'+' }\n                    }\n                }')
def pulse(rgb,short=False):
    times=[0,.035,.045,.10,.13,.19,.22,.80,1] if not short else [0,.06,.1,.24,.28,.48,.55,1]
    alphas=[0,1,.45,1,.5,1,.68,.8,0] if not short else [0,1,.35,1,.1,.85,.3,0]
    return field('Color','embed','ValueColor {\n                    Dynamics: pointer = VfxAnimatedColorVariableData {\n                        Times: list[f32] = {\n'+''.join('                            '+str(t)+'\n' for t in times)+'                        }\n                        Values: list[vec4] = {\n'+''.join('                            { '+', '.join(map(str,(*rgb,a)))+' }\n' for a in alphas)+'                        }\n                    }\n                }')

def main():
    assert not OUT.exists(),'Preserve previous candidate.'
    parent=ROOT/'build/directional_sfx_v3/Braum_Clash_Directional_v1_SFX_v3.fantome'
    assert p.sha(parent)=='485a6aa1577c2731299ef28d1c7b2125032e3cce5290f6043478f0ce8396c018'
    OUT.mkdir();package=OUT/'package'
    with zipfile.ZipFile(parent) as z:
        assert z.testzip() is None;z.extractall(package);previous={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
    wad=package/'WAD/Braum.wad.client';assets=wad/p.ASSET;binpath=wad/'data/characters/braum/skins/skin0.bin'
    text=(ROOT/'build/directional_v1/skin0.ritobin').read_text();before=p.entries(text)
    p.run([p.RITO,'-i','text','-o','bin','-k',ROOT/'build/directional_v1/skin0.ritobin',OUT/'parent.bin']);assert p.sha(OUT/'parent.bin')==p.sha(binpath)
    rails=[(0,9,-80),(8,11,-63),(-9,8,-44),(6,10,-28),(-12,9,-9),(9,11,7),(-7,8,24),(11,10,43),(-5,9,62),(0,9,80)]
    strike=[(0,0,0),(15,55,-5),(-10,92,4),(18,140,-8),(-12,191,5),(20,235,0),(0,300,-8),(14,380,0),(0,470,0)]
    meshes=[mesh(assets/'r_connected_rail.scb',rails,2),mesh(assets/'r_downstrike.scb',strike,3.5)]
    changed={};removed=[]
    # Boost the existing line-and-halo texture at exactly the same footprint.
    key=PREFIX+'Braum_W_Shield_buf';e=before[key]
    for a,z,b in reversed(emitters(e)):
        if name(b)=='Decal_shield':
            new=color(b,(1,1,1),2);guard(b,new,['Color']);e=e[:a]+new+e[z:]
            glow=color(b,(.38,.7,1),3).replace('EmitterName: string = "Decal_shield"','EmitterName: string = "Clash_W_Line_Glow"')
            glow=re.sub(r'BlendMode: u8 = \d+','BlendMode: u8 = 4',glow)
            guard(b,glow,['Color','EmitterName','BlendMode'])
            marker='        ComplexEmitterDefinitionData: list[pointer] = {';e=e.replace(marker,marker+'\n'+glow,1)
    changed[key]=e
    # Animation-bound native cast systems are separate from E and Q's missile.
    for key in ['Characters/Braum/Skins/Skin0/Particles/Braum_Base_Q_Shield_base_cas','Characters/Braum/Skins/Skin0/Particles/Braum_base_R_shield_Base_cas']:
        e=before[key]
        for a,z,b in reversed(emitters(e)):
            if name(b) in {'Ice_shield','Ice_override','shield_break','shield_break1','shield_break2','ice_shard'}:
                assert not re.search(r'(?i)(sound|audio|child|event)',b);removed.append([key,name(b)]);e=e[:a]+e[z:]
        changed[key]=e
    source=next(b for _,_,b in emitters(before[PREFIX+'Braum_R_mis']) if name(b)=='cracks_left')
    fields=['EmitterName','Velocity','SpawnShape','Primitive','BlendMode','Color','BirthRotation0','Rotation0','BirthScale0','Texture','FrameRate','NumFrames','TexDiv','IsRandomStartFrame','ParticleIsLocalOrientation','ParticleLinger']
    base=strip(source,fields)
    ground=next(b for _,_,b in emitters(before[PREFIX+'Braum_R_Small_mis']) if name(b)=='GroundBurn')
    groundfields=['EmitterName','EmitterPosition','SpawnShape','Color','BirthRotation0','BirthScale0','Scale0','ParticleLifetime','ParticleLinger','ParticleIsLocalOrientation']
    for short in ['Braum_R_mis','Braum_R_Small_mis','Braum_R_PBAOE_Cas']:
        key=PREFIX+short;e=before[key]
        for a,z,b in reversed(emitters(e)):
            if name(b) in {'cracks_left','cracks_right','Frozen','GroundBurn'}:e=e[:a]+e[z:]
        additions=[]
        for side,x in [('Left',-65),('Right',65)]:
            if short!='Braum_R_PBAOE_Cas':
                common=offset(x)+val('BirthRotation0','Vector3','{ 0, 0, 0 }')+val('BirthScale0','Vector3','{ 1, 1, 1 }')+field('ParticleIsLocalOrientation','flag','true')+field('BlendMode','u8','4')+field('Texture','string','"'+GLOW+'"')
                bolt=add(base,common+field('EmitterName','string','"Clash_R_Connected_'+side+'"')+mesh_primitive(p.ASSET+'r_connected_rail.scb')+pulse((.22,.55,1)))
                guard(source,bolt,fields);additions.append(bolt)
                falling=strip(bolt,['ParticleLifetime','Color','Primitive','EmitterName'])
                falling=add(falling,val('ParticleLifetime','Float','.22')+field('EmitterName','string','"Clash_R_Strike_'+side+'"')+mesh_primitive(p.ASSET+'r_downstrike.scb')+pulse((.8,.94,1),True))
                guard(bolt,falling,['ParticleLifetime','Color','Primitive','EmitterName']);additions.append(falling)
            crater=add(strip(ground,groundfields),offset(x,3)+field('EmitterName','string','"Clash_R_Crater_'+side+'"')+val('ParticleLifetime','Float','4')+val('BirthRotation0','Vector3','{ 90, 0, 0 }')+val('BirthScale0','Vector3','{ 38, 38, 38 }')+field('ParticleIsLocalOrientation','flag','true')+pulse((.008,.012,.02)))
            guard(ground,crater,groundfields);additions.append(crater)
        marker='        ComplexEmitterDefinitionData: list[pointer] = {';e=e.replace(marker,marker+'\n'+'\n'.join(additions),1);changed[key]=e
    for key,e in changed.items():text=text.replace(before[key],e)
    after=p.entries(text);assert {k for k in before if before[k]!=after[k]}==set(changed)
    assert all(before[k]==after[k] for k in before if re.search(r'(?i)(braum_e_|braum_q_mis)',k))
    assert 'braum_base_q_shield_base.scb' not in ''.join(changed[k] for k in changed if 'shield_Base_cas' in k or 'Shield_base_cas' in k)
    trial=OUT/'skin0.ritobin';trial.write_text(text)
    compiled=OUT/'compiled.bin';p.run([p.RITO,'-i','text','-o','bin','-k',trial,compiled]);assert compiled.is_file()
    assert compiled.read_bytes()!=binpath.read_bytes();binpath.write_bytes(compiled.read_bytes())
    p.run([p.RITO,'-i','bin','-o','text',binpath,OUT/'verified.ritobin']);assert 'Clash_R_Strike_Left' in (OUT/'verified.ritobin').read_text()
    p.run([p.RITO,'-i','text','-o','bin','-k',OUT/'verified.ritobin',OUT/'verified.bin']);assert p.sha(binpath)==p.sha(OUT/'verified.bin')
    meta=package/'META/info.json';info=json.loads(meta.read_text());info.update(Name='Clash Braum Travelling Strikes v1 + SFX v3',Version='0.3.6-strikes',Description='Stronger W line glow, two connected R tracks with successive strikes and discrete scorch marks; removes Q/R ice cast shield. Accepted E and SFX v3 preserved.');meta.write_text(json.dumps(info,indent=2))
    actual={f.relative_to(package).as_posix():f.read_bytes() for f in package.rglob('*') if f.is_file()}
    assert {n for n in previous if actual[n]!=previous[n]}=={'META/info.json','WAD/Braum.wad.client/data/characters/braum/skins/skin0.bin'}
    assert actual.keys()-previous.keys()=={'WAD/Braum.wad.client/'+p.ASSET+n for n in ['r_connected_rail.scb','r_downstrike.scb']}
    refs=set(re.findall(r'"(assets/characters/braum/skins/base/braum_clash/[^"]+)"',text,re.I));assert all((wad/r.lower()).is_file() for r in refs)
    archive=OUT/'Braum_Clash_Travelling_Strikes_v1_SFX_v3.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(actual.items()):z.writestr(n,b)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None and all(z.read(n)==b for n,b in actual.items())
    report=dict(status='PASS affected offline checks; manual gameplay pending',archive=archive.relative_to(ROOT).as_posix(),sha256=p.sha(archive),parent_sha256=p.sha(parent),meshes=meshes,removed_cast_emitters=removed,changed_entries=list(changed),protected='All E entries, Q missile, accepted character geometry/textures, passive/loading and audio exact.',reused='All textures are unchanged, including W alpha/mip evidence. Prior audio/character evidence reused by byte identity.',runtime='Verify continuous tracks, successive strikes at native R segment spawn positions, distinct electrified craters, W glow and absence of Q/R ice shield; E accepted and closed.',payloads=[dict(path=f.relative_to(wad).as_posix(),sha256=p.sha(f)) for f in sorted(wad.rglob('*')) if f.is_file()])
    (ROOT/'validation/strike_v1_build.json').write_text(json.dumps(report,indent=2));(ROOT/'validation/strike_v1_build_logs.json').write_text(json.dumps(p.logs,indent=2));print(json.dumps({k:report[k] for k in ['status','archive','sha256']},indent=2))

if __name__=='__main__':main()
