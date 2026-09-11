from pathlib import Path
import json,hashlib,re,struct,zipfile,collections,sys,types,importlib.util,csv
ROOT=Path(__file__).resolve().parents[2]; AUDIT=ROOT/'audit'; OUT=AUDIT/'evidence'; SRC=AUDIT/'sources'
sys.path.insert(0,str(AUDIT/'scratch/python_lib'))
import xxhash,zstandard
def write(n,d): (OUT/n).write_text(json.dumps(d,indent=2),encoding='utf8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
files=[p for p in ROOT.rglob('*') if p.is_file() and AUDIT not in p.parents]
wanted={p.stem for p in (ROOT/'Braum.wad').iterdir() if p.is_file()}
def wad_entries(p):
    b=p.read_bytes();maj,minr=b[2:4];assert b[:2]==b'RW' and maj==3
    n=struct.unpack_from('<I',b,268)[0];a=[]
    for i in range(n):
        h,o,sz,uz,typ,dup,sub,ck=struct.unpack_from('<QIIIBBHQ',b,272+i*32)
        a.append({'hash':f'{h:016x}','offset':o,'compressed_size':sz,'size':uz,'compression':typ,'checksum':f'{ck:016x}'})
    return b,{'path':str(p),'version':f'{maj}.{minr}','sha256':sha(p),'count':n,'entries':a}
archives=[]
for p in [ROOT/'Braum.en_US.wad.client',Path(r'C:\Users\etqdo\Downloads\wadtools-0.5.7-windows-x64\Braum.wad.client')]:
    b,meta=wad_entries(p);archives.append((b,meta));wanted.update(e['hash'] for e in meta['entries'])
paths={}
def candidate(s):
    s=s.lower().replace('\\','/');h=xxhash.xxh64_hexdigest(s.encode())
    if h in wanted:paths[h]=s
for p in SRC.glob('hashes.game.txt.*'):
    for line in p.open(encoding='utf8'):
        h,s=line.rstrip('\n').split(' ',1)
        if h in wanted:paths[h]=s
        if s.endswith('.dds'):candidate(s[:-4]+'.tex')
if (OUT/'bin_index.json').exists():
    for b in json.loads((OUT/'bin_index.json').read_text()):
        for s in b.get('references',[])+b.get('links',[]):candidate(s)
for i in range(100):
    candidate(f'data/characters/braum/skins/skin{i}.bin')
    candidate(f'data/characters/braum/animations/skin{i}.bin')
write('path_map.json',paths)
(SRC/'project.hashes.txt').write_text(''.join(f'{h} {s}\n' for h,s in sorted(paths.items())),encoding='utf8')
pkg=types.ModuleType('audit_cdtb');pkg.__path__=[];sys.modules['audit_cdtb']=pkg
hm=types.ModuleType('audit_cdtb.hashes')
class HashFile:
    def __init__(self,filename,hash_size=16):self.filename=filename;self.cache=None
    def load(self):
        if self.cache is None:
            if self.filename.name=='hashes.game.txt':self.cache={int(h,16):s for h,s in paths.items()}
            else:self.cache={int(h,16):s for h,s in (l.rstrip('\n').split(' ',1) for l in self.filename.open(encoding='utf8'))}
        return self.cache
hm.HashFile=HashFile;hm.default_hash_dir=SRC;hm.hashfile_game=HashFile(SRC/'hashes.game.txt');sys.modules[hm.__name__]=hm
spec=importlib.util.spec_from_file_location('audit_cdtb.binfile',SRC/'binfile.py');bm=importlib.util.module_from_spec(spec);sys.modules[spec.name]=bm;spec.loader.exec_module(bm)
bindir=OUT/'bins';bindir.mkdir(exist_ok=True)
bins=[];refs=collections.defaultdict(set)
def strings(x):
    if isinstance(x,dict):
        for k,v in x.items():yield from strings(v)
    elif isinstance(x,list):
        for v in x:yield from strings(v)
    elif isinstance(x,str):yield x
for p in (ROOT/'Braum.wad').glob('*.bin'):
    try:
        f=bm.BinFile(str(p));d=f.to_serializable();(bindir/(p.stem+'.json')).write_text(json.dumps(d,indent=2),encoding='utf8')
        brefs=sorted({s for s in strings(d) if re.search(r'\.(bin|tex|dds|skn|skl|anm|scb|sco|bnk|wpk|troy|lua|inibin)$',s,re.I)})
        for s in brefs:refs[s.lower()].add(p.name)
        bins.append({'file':p.name,'path':paths.get(p.stem),'version':f.version,'entries':{str(e.path):str(e.type) for e in f.entries},'links':f.linked_files,'references':brefs})
    except Exception as e:bins.append({'file':p.name,'error':repr(e)})
write('bin_index.json',bins)
rows=[]
purposes={'.skn':'Skinned mesh with submeshes and vertex weights','.skl':'Skeleton, bind transforms and influence palette','.anm':'Animation tracks','.bin':'Property configuration and asset links','.bnk':'Wwise event graph or embedded audio bank','.wpk':'Packaged Wwise media','.tex':'League texture','.dds':'DirectDraw texture','.scb':'Static mesh, commonly VFX geometry','.obj':'Wavefront static source mesh','.blend':'Blender source scene','.rar':'Clash source archive','.zip':'Addon distribution','.avif':'Visual reference','.jpg':'Visual reference'}
for p in files:
    rel=p.relative_to(ROOT).as_posix();h=p.stem if p.parent.name=='Braum.wad' else '';gp=paths.get(h,'');b=p.read_bytes();suf=p.suffix
    rows.append({'file':p.name,'extension':suf or '[none]','original_path':str(p),'relative_path':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'magic_hex':b[:16].hex(),'wad_hash':h,'resolved_game_path':gp,'purpose':purposes.get(suf,'WAD archive' if p.name.endswith('.wad.client') else 'Unknown; inspect magic'),'relevance':'base or shared candidate' if ('/base/' in gp or '/skin0.' in gp or '/braum.bin' in gp) else ('other skin/shared; see reference graph' if h else 'source/tool/reference'),'referenced_by':';'.join(sorted(refs.get(gp.lower(),[])))})
write('project_inventory.json',rows)
with (OUT/'project_inventory.tsv').open('w',encoding='utf8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0],delimiter='\t');w.writeheader();w.writerows(rows)
for b,meta in archives:
    for e in meta['entries']:e['path']=paths.get(e['hash'])
    write(meta['path'].split('\\')[-1]+'.index.json',meta)
    if meta['path'].endswith('Braum.en_US.wad.client'):
        target=AUDIT/'scratch/voice_original';target.mkdir(exist_ok=True)
        for e in meta['entries']:
            raw=b[e['offset']:e['offset']+e['compressed_size']]
            if e['compression']==0:data=raw
            elif e['compression']==3:data=zstandard.ZstdDecompressor().decompress(raw,max_output_size=e['size'])
            else:raise Exception(('unsupported compression',e))
            assert len(data)==e['size'];ext=Path(e.get('path') or '').suffix
            (target/(e['hash']+ext)).write_bytes(data)
write('summary.json',{'files':len(files),'bytes':sum(r['bytes'] for r in rows),'extensions':dict(collections.Counter(r['extension'] for r in rows)),'resolved':len(paths),'unresolved':sorted(wanted-paths.keys()),'bins_parsed':sum('error' not in b for b in bins),'bin_errors':[b for b in bins if 'error'in b]})
print('SUMMARY',len(files),'resolved',len(paths),'unresolved',len(wanted-paths.keys()),'bin errors',[b for b in bins if 'error'in b])
