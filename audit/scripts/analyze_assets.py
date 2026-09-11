from pathlib import Path
import json,struct,collections,math,re,zipfile,hashlib,sys
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'audit/evidence';P=json.loads((O/'path_map.json').read_text());F={p.stem:p for p in (R/'Braum.wad').iterdir()}
def write(n,d):(O/n).write_text(json.dumps(d,indent=2),encoding='utf8')
def readskl(p):
    b=p.read_bytes();magic,ver=struct.unpack_from('<II',b,4);assert magic==0x22fd4fc3
    nj,ni,jo,_,io=struct.unpack_from('<H I i i i',b,14);j=[]
    for i in range(nj):
        o=jo+i*100;flags,idx,par,fl,h,r=struct.unpack_from('<H H h H I f',b,o);nameoff=struct.unpack_from('<i',b,o+96)[0]+o+96;name=b[nameoff:b.index(b'\0',nameoff)].decode()
        tr,sc,qt=struct.unpack_from('<3f',b,o+16),struct.unpack_from('<3f',b,o+28),struct.unpack_from('<4f',b,o+40)
        x,y,z,w=qt;rot=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
        mat=np.eye(4);mat[:3,:3]=rot@np.diag(sc);mat[:3,3]=tr
        if par>=0:mat=np.array(j[par]['global_matrix'])@mat
        j.append({'index':i,'id':idx,'name':name,'parent_index':par,'parent':j[par]['name'] if par>=0 else None,'hash':f'{h:08x}','translation':tr,'scale':sc,'quaternion_xyzw':qt,'global_position':mat[:3,3].tolist(),'global_matrix':mat.tolist()})
    inf=list(struct.unpack_from('<'+'H'*ni,b,io));return {'path':str(p),'version':ver,'bone_count':nj,'influence_count':ni,'influence_palette':inf,'joints':j}
def readskn(p,skl):
    b=p.read_bytes();magic,ma,mi,n=struct.unpack_from('<IHHI',b);assert magic==0x112233
    o=12;sm=[]
    for i in range(n):
        name=b[o:o+64].split(b'\0')[0].decode();vs,vc,ist,ic=struct.unpack_from('<4I',b,o+64);o+=80;sm.append({'name':name,'vertex_start':vs,'vertices':vc,'index_start':ist,'indices':ic})
    if ma>=4:o+=4
    idx,vc=struct.unpack_from('<II',b,o);o+=8;stride=52;vt=0
    if ma>=4:stride,vt=struct.unpack_from('<II',b,o);o+=48
    ii=struct.unpack_from('<'+'H'*idx,b,o);o+=idx*2;verts=[];allweights=collections.Counter()
    for i in range(vc):
        v=struct.unpack_from('<3f4B4f3f2f',b,o+i*stride);verts.append(v)
    for s in sm:
        vv=verts[s['vertex_start']:s['vertex_start']+s['vertices']];ws=collections.Counter();rig=collections.Counter()
        for v in vv:
            active=[]
            for bi,w in zip(v[3:7],v[7:11]):
                if w>0:
                    name=skl['joints'][skl['influence_palette'][bi]]['name'];ws[name]+=w;active.append(name)
            if len(active)==1:rig[active[0]]+=1
        s['weight_totals']=dict(ws.most_common());s['rigid_vertices_by_bone']=dict(rig);s['bounds']=[[min(v[a] for v in vv),max(v[a] for v in vv)] for a in range(3)]
    return {'path':str(p),'version':f'{ma}.{mi}','vertices':vc,'triangles':idx//3,'stride':stride,'vertex_type':vt,'submeshes':sm,'bounds':[[min(v[a] for v in verts),max(v[a] for v in verts)] for a in range(3)],'max_index':max(ii),'max_weight_error':max(abs(sum(v[7:11])-1) for v in verts)}
sk=readskl(F['9b8248658ce51711']);write('braum_skeleton.json',sk);mesh=readskn(F['fbf88fcfc8ec8dc4'],sk);write('braum_mesh.json',mesh)
bins={p.stem:json.loads(p.read_text()) for p in (O/'bins').glob('*.json')};owners=collections.defaultdict(list)
for h,d in bins.items():
    for k,v in d.items():
        if not k.startswith('__'):owners[k].append(h)
skin=bins['eb9d53354a504663'];resolver=skin['Characters/Braum/Skins/Skin0/Resources']['ResourceMap'];vfx=[]
def vals(x,trail=''):
    if isinstance(x,dict):
        for k,v in x.items():yield from vals(v,trail+'/'+k)
    elif isinstance(x,list):
        for i,v in enumerate(x):yield from vals(v,trail+'/'+str(i))
    elif isinstance(x,str):yield trail,x
sys.path.insert(0,str(R/'audit/scratch/python_lib'));import xxhash
for key,entry in resolver.items():
    own=owners.get(entry,[])
    for h in own:
        d=bins[h][entry];deps=[]
        for field,v in vals(d):
            if re.search(r'\.(tex|dds|scb|skn|skl|anm|bin)$',v,re.I):
                hh=xxhash.xxh64_hexdigest(v.lower().encode());deps.append({'field':field,'path':v,'hash':hh,'supplied':hh in F,'local':F[hh].name if hh in F else None})
        vfx.append({'resource_key':key,'entry':entry,'owner_hash':h,'owner_path':P.get(h),'emitters':[{k:v for k,v in e.items() if k in ['EmitterName','BirthColor','Color','BlendMode','ParticleLifetime','Lifetime','IsSingleParticle','Linger','Texture','SoundOnCreate','SoundPersistent','Disabled','MeshRenderFlags','RenderPhaseOverride','IsGroundLayer','IsLocalOrientation']} for e in d.get('ComplexEmitterDefinitionData',[])], 'dependencies':deps,'sound_fields':[(k,v) for k,v in vals(d) if 'sound' in k.lower()]})
write('base_vfx_dependencies.json',vfx)
ani=bins['0b01eaec2c944f55']['Characters/Braum/Animations/Skin0'];write('base_animation_clips.json',ani)
rows=[]
for p in list((R/'Braum.wad').glob('*.bnk'))+list((R/'audit/scratch/voice_original').glob('*.bnk')):
    b=p.read_bytes();o=0;chunks=[];did=[];hirc=[]
    while o+8<=len(b):
        tag=b[o:o+4].decode();n=struct.unpack_from('<I',b,o+4)[0];raw=b[o+8:o+8+n];c={'tag':tag,'size':n}
        if tag=='BKHD':c['version'],c['bank_id']=struct.unpack_from('<II',raw)
        if tag=='DIDX':did=[dict(zip(['media_id','offset','size'],struct.unpack_from('<III',raw,i))) for i in range(0,n,12)]
        if tag=='HIRC':
            c['count']=struct.unpack_from('<I',raw)[0];at=4
            for i in range(c['count']):
                typ,sz=struct.unpack_from('<BI',raw,at);hid=struct.unpack_from('<I',raw,at+5)[0];data=raw[at+9:at+5+sz];hirc.append({'type':typ,'id':hid,'payload_hex':data.hex()});at+=5+sz
            assert at==len(raw)
        chunks.append(c);o+=8+n
    rows.append({'file':str(p),'path':P.get(p.stem),'chunks':chunks,'media':did,'hirc':hirc})
write('audio_banks.json',rows)
tex=[]
for p in (R/'audit/scratch/CHR_Clash').rglob('*'):
    if p.is_file():
        d={'archive':'CHR_Clash.rar','member':p.relative_to(R/'audit/scratch').as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'extension':p.suffix}
        if p.suffix.lower() in ['.dds','.tga','.jpg']:
            try:
                im=Image.open(p);d.update(size=im.size,mode=im.mode,format=im.format)
                if p.suffix=='.dds':d['fourcc']=p.read_bytes()[84:88].decode('ascii',errors='replace');d['mip_count']=struct.unpack_from('<I',p.read_bytes(),28)[0]
                d['channel_extrema']=im.getextrema()
            except Exception as e:d['error']=str(e)
        tex.append(d)
write('clash_archive_inventory.json',tex)
z=zipfile.ZipFile(R/'Aventurine-3.1.5.zip');write('addon_archive_inventory.json',[{'archive':'Aventurine-3.1.5.zip','member':i.filename,'bytes':i.file_size,'crc32':f'{i.CRC:08x}'} for i in z.infolist()])
print('MESH',json.dumps(mesh,indent=2));print('SKELETON',sk['bone_count'],sk['influence_count'],[(j['name'],j['parent']) for j in sk['joints']]);print('VFX',len(vfx),'missing',len({r['path'] for x in vfx for r in x['dependencies'] if not r['supplied']}));print('AUDIO',[(Path(x['file']).name,len(x['media']),collections.Counter(y['type'] for y in x['hirc'])) for x in rows])
