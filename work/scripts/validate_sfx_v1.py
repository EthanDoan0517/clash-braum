"""Changed-bank integrity/shared-event checks and isolated offline packaging only."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys,xml.etree.ElementTree as ET,zipfile
from inspect_sfx_source import chunks
from diagnose_sfx_silence import wem_info,fnv

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'audit/scratch/python_lib'))
from xxhash import xxh64_hexdigest
sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
    label=sys.argv[1] if len(sys.argv)>1 else 'sfx_v1'
    assert label in ['sfx_v1','sfx_v2','sfx_v2_refinement']
    report=json.loads((ROOT/f'validation/{label}_build.json').read_text())
    archive=ROOT/report['archive'];assert sha(archive.read_bytes())==report['sha256']
    out=archive.parent/'validation';assert not out.exists();out.mkdir()
    source=(ROOT/'Braum.wad/668ac17b89a8d8ea.bnk').read_bytes()
    with zipfile.ZipFile(archive) as z:
        new=z.read('WAD/Braum.wad.client/'+report['bank_path'])
        with zipfile.ZipFile(ROOT/report['parent']) as parent:
            assert set(z.namelist())==set(parent.namelist())|{'WAD/Braum.wad.client/'+report['bank_path']}
            for name in parent.namelist():
                if name!='META/info.json':assert z.read(name)==parent.read(name)
    oldchunks=dict(chunks(source));newchunks=dict(chunks(new));assert oldchunks[b'DIDX']==newchunks[b'DIDX']
    records={i:(o,n) for i,o,n in struct.iter_unpack('<III',oldchunks[b'DIDX'])}
    changed={x['id'] for x in report['changed_media']}
    roots=ET.fromstring('<banks>'+(ROOT/'audit/evidence/base_audio_wwiser.xml').read_text()+'</banks>')
    eventbank=(ROOT/'Braum.wad/6a0cd1a55c7df583.bnk').read_bytes()
    assert sha(eventbank)==report['event_bank_sha256_unchanged']
    verified=[]
    for obj in roots[0].findall('.//list[@name="listLoadedItem"]/object'):
        media=obj.find('.//field[@name="sourceID"]')
        if media is None or int(media.get('value')) not in changed:continue
        mid=int(media.get('value'));size=obj.find('.//field[@name="uInMemoryMediaSize"]');plugin=obj.find('.//field[@name="ulPluginID"]')
        assert size is not None and plugin is not None
        for f in [media,size,plugin]:assert struct.unpack_from('<I',eventbank,int(f.get('offset')))[0]==int(f.get('value'))
        assert int(size.get('value'))==records[mid][1] and int(plugin.get('value'))==0x40001
        verified.append(mid)
    assert set(verified)==changed
    setup_ids={}
    for mid,(off,size) in records.items():
        old=oldchunks[b'DATA'][off:off+size]; replacement=newchunks[b'DATA'][off:off+size]
        if label.startswith('sfx_v2'):
            p=wem_info(replacement)
            assert p['uid']==fnv(p['setup']),(mid,'Invalid engine setup cache hash')
            assert p['uid'] not in setup_ids or setup_ids[p['uid']]==p['setup_sha256']
            setup_ids[p['uid']]=p['setup_sha256']
        if mid not in changed:assert old==replacement;continue
        assert len(replacement)==size and replacement[:4]==b'RIFF'
        assert struct.unpack_from('<I',replacement,4)[0]+8==size
        assert replacement[12:16]==b'fmt '
        assert struct.unpack_from('<HHI',replacement,20)==(65535,1,44100)
        assert struct.unpack_from('<I',replacement,16)[0]==66
    logs=[]
    def run(args):
        r=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8',errors='replace')
        logs.append(dict(argv=list(map(str,args)),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
        (ROOT/f'validation/{label}_package_logs.json').write_text(json.dumps(logs,indent=2))
        assert r.returncode==0,(r.stdout,r.stderr)
    run(['C:/Users/etqdo/Downloads/cslol-go/cslol-tools/mod-tools.exe','import',archive,out/'imported'])
    key=xxh64_hexdigest(report['bank_path'].encode())
    run(['C:/Users/etqdo/Downloads/wadtools-0.5.7-windows-x64/wadtools.exe','--config',ROOT/'work/config/wadtools.toml','--hashtable-dir',ROOT/'work/cache/hashes','--progress=false','extract','-i',out/'imported/WAD/Braum.wad.client','-o',out/'extracted','--no-bin-paths','--hash',key])
    matches=[p for p in (out/'extracted').rglob('*') if p.is_file() and p.stem==key]
    assert len(matches)==1 and matches[0].read_bytes()==new
    result={'status':'PASS','archive_sha256':report['sha256'],'changed_bank_sha256':sha(new),'changed_bank_path_hash':key,'changed_media':len(changed),'unchanged_media':len(records)-len(changed),'native_event_plugin_and_memory_sizes_verified':len(verified),'all_parent_payloads_exact':True,'isolated_backend_bank_path_and_bytes_exact':True,'reused':'readability_v1 geometry/rig/VFX/texture/package evidence: original payload bytes unchanged. Build checks independently decode all 20 new padded WEMs, exact sample counts, correlations >0.9, no clipped samples.','runtime':'User must test playback, volume, residual source beep, E expiry/death cleanup. Offline decoding is not runtime acceptance.'}
    if label.startswith('sfx_v2'):
        result.update(native_setup_hash_contract_verified=114,distinct_setup_hashes=len(setup_ids),reused='v1 decoding/sample count/peak/correlation evidence reused: only setup cache hash changed, compressed data byte-exact. Parent visual evidence reused; changed bank checked once in isolated backend.',runtime='User must retest bank playback: W/basic attacks as controls, then Q/E/R, E expiry/death stops and beep/volume. v1 was silent in game despite decoder success.')
    (ROOT/f'validation/{label}_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':main()
