"""Compare native/current-game bank and Vorbis setup identity contracts."""
from pathlib import Path
import hashlib,json,struct,zlib,sys,collections
from inspect_sfx_source import chunks
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'audit/scratch/python_lib'))
import xxhash
sha=lambda b:hashlib.sha256(b).hexdigest()

def wem_info(b):
    at=12;c={}
    while at+8<=len(b):
        tag=b[at:at+4];size=struct.unpack_from('<I',b,at+4)[0];assert at+8+size<=len(b)
        c[tag]=b[at+8:at+8+size];at+=8+size
    f=c[b'fmt '];d=c[b'data'];seek,ao=struct.unpack_from('<II',f,40)
    size=struct.unpack_from('<H',d,seek)[0]
    assert ao==seek+size+2
    setup=d[seek+2:ao]
    return {'uid':struct.unpack_from('<I',f,60)[0],'setup_sha256':sha(setup),'setup':setup,'setup_packet':d[seek:ao],'fmt':f,'chunks':[k.decode() for k in c]}

def fnv(b,xor_first=False):
    h=2166136261
    for c in b:h=((h^c)*16777619)&0xffffffff if xor_first else ((h*16777619)^c)&0xffffffff
    return h

def main():
    out=ROOT/'build/sfx_silence_diagnosis';out.mkdir(exist_ok=True)
    nativebank=(ROOT/'Braum.wad/668ac17b89a8d8ea.bnk').read_bytes();c=dict(chunks(nativebank))
    profiles=[]
    for mid,offset,size in struct.iter_unpack('<III',c[b'DIDX']):
        p=wem_info(c[b'DATA'][offset:offset+size]);p['id']=mid;profiles.append(p)
    algorithms={'crc32':zlib.crc32,'fnv1':fnv,'fnv1a':lambda b:fnv(b,True),'xxh32':lambda b:xxhash.xxh32(b).intdigest()}
    matches={f'{key}/{algo}':sum(func(p[key])==p['uid'] for p in profiles) for key in ['setup','setup_packet'] for algo,func in algorithms.items()}
    new=[]
    for path in sorted((ROOT/'build/sfx_v1/wem').glob('*.wem')):
        p=wem_info(path.read_bytes());p['id']=int(path.stem);new.append(p)
    def groups(rows):
        d=collections.defaultdict(set)
        for p in rows:d[p['uid']].add(p['setup_sha256'])
        return {str(k):len(v) for k,v in d.items()}
    live=list((out/'live_audio').glob('*.bnk'))
    result={'runtime_feedback':'All abilities and attacks silent; voice still plays. v1 rejected.','installed_banks_match_supplied':{p.name:sha(p.read_bytes())==sha((ROOT/'Braum.wad'/p.name).read_bytes()) for p in live},'native_hash_algorithm_matches':matches,'native_uid_distinct_setups':groups(profiles),'v1_uid_distinct_setups':groups(new),'v1_profiles':[{k:v for k,v in p.items() if k not in ['setup','setup_packet','fmt']} for p in new]}
    (ROOT/'validation/sfx_silence_diagnosis.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ['native_uid_distinct_setups','v1_profiles']},indent=2))
    print('native UID collision count',sum(n>1 for n in groups(profiles).values()))

if __name__=='__main__':main()
