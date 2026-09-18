"""Validate changed English WPK and Q/R gain; reuse byte-identical media evidence."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys,zipfile,xml.etree.ElementTree as ET
from diagnose_sfx_silence import wem_info,fnv
from build_sfx_v3_volume import objects,props,EVENTPATH
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/clash_vo_v1/validation'
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
    r=json.loads((ROOT/'validation/clash_vo_v1_build.json').read_text()); OUT.mkdir(exist_ok=True)
    archive=ROOT/r['archive'];assert sha(archive.read_bytes())==r['sha256']
    parent=ROOT/r['parent'];assert sha(parent.read_bytes())==r['parent_sha256']
    event='WAD/Braum.wad.client/'+EVENTPATH;vo='WAD/Braum.en_US.wad.client/'+r['vo_path']
    with zipfile.ZipFile(archive) as z,zipfile.ZipFile(parent) as p:
        assert z.testzip() is None
        assert set(z.namelist())==set(p.namelist())|{vo}
        for n in p.namelist():
            if n not in [event,'META/info.json']:assert z.read(n)==p.read(n)
        bank=z.read(event);wpk=z.read(vo);restored=bytearray(bank)
        for c in r['sfx_volume_changes']:
            assert struct.unpack_from('<f',bank,c['offset'])[0]==16
            struct.pack_into('<f',restored,c['offset'],10)
        assert bytes(restored)==p.read(event)
    assert sha(wpk)==r['wpk_sha256'] and sha(bank)==r['sfx_event_bank_sha256']
    mapping=json.loads((ROOT/'work/audio/clash_vo_mapping_v1.json').read_text())['media']
    native=(ROOT/'audit/scratch/voice_original/4826a53ff12ced20.wpk').read_bytes()
    assert wpk[:12]==native[:12] and struct.unpack_from('<I',wpk,8)[0]==115
    end=0;seen=set()
    for i in range(115):
        pos=struct.unpack_from('<I',wpk,12+4*i)[0];oldpos=struct.unpack_from('<I',native,12+4*i)[0];assert pos==oldpos
        start,size,n=struct.unpack_from('<III',wpk,pos)
        assert wpk[pos+8:pos+12+n*2]==native[pos+8:pos+12+n*2]
        name=wpk[pos+12:pos+12+n*2].decode('utf-16-le').rstrip('\0');mid=Path(name).stem
        assert start%8==0 and start>=end and start+size<=len(wpk);end=start+size
        b=wpk[start:end];a=mapping[mid];assert sha(b)==a['wem_sha256']
        assert b==(ROOT/f"build/clash_vo_clips_v1/wem/{a['clip']}.wem").read_bytes()
        info=wem_info(b);assert info['uid']==fnv(info['setup']);seen.add(mid)
    assert seen==set(mapping)
    logs=[]
    def run(args):
        args=list(map(str,args));p=subprocess.run(args,capture_output=True,text=True,encoding='utf8',errors='replace')
        logs.append(dict(argv=args,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
        (ROOT/'validation/clash_vo_v1_validation_logs.json').write_text(json.dumps(logs,indent=2));assert p.returncode==0,(p.stdout,p.stderr)
    bankfile=OUT/'events.bnk';bankfile.write_bytes(bank)
    run([sys.executable,ROOT/'audit/scratch/wwiser-master/wwiser.py','-d','xml','-dn',OUT/'events',bankfile])
    parsed=objects(ET.parse(OUT/'events.xml').getroot());louder={c['sound_id'] for c in r['sfx_volume_changes']}
    prior=json.loads((ROOT/'validation/sfx_v3_volume_build.json').read_text())
    for c in prior['changes']:
        values=[p for p in props(parsed[c['sound_id']]).findall('./list/object') if p.find('./field[@name="pID"]').get('value')=='0']
        assert len(values)==1 and float(values[0].find('./field[@name="pValue"]').get('value'))==(16 if c['sound_id'] in louder else 10)
    run(['C:/Users/etqdo/Downloads/cslol-go/cslol-tools/mod-tools.exe','import',archive,OUT/'imported'])
    sys.path.insert(0,str(ROOT/'audit/scratch/python_lib'));from xxhash import xxh64_hexdigest
    for wad,path,expected in [('Braum.wad.client',EVENTPATH,bank),('Braum.en_US.wad.client',r['vo_path'],wpk)]:
        key=xxh64_hexdigest(path.encode());dest=OUT/wad
        run(['C:/Users/etqdo/Downloads/wadtools-0.5.7-windows-x64/wadtools.exe','--config',ROOT/'work/config/wadtools.toml','--hashtable-dir',ROOT/'work/cache/hashes','--progress=false','extract','-i',OUT/'imported/WAD'/wad,'-o',dest,'--no-bin-paths','--hash',key])
        matches=[p for p in dest.rglob('*') if p.is_file() and p.stem==key];assert len(matches)==1 and matches[0].read_bytes()==expected
    result=dict(status='PASS',archive=r['archive'],sha256=r['sha256'],wpk_slots_verified=115,independent_parser_volume_verified=True,approved_e_unchanged=True,isolated_backend_both_changed_payloads_exact=True,reused='All 66 used clips match independently decoded media evidence. All prior payloads except seven Q/R gain floats are byte-identical; no repeated visual or geometry checks.',runtime='User English-VO playback/context/stop/volume and Q/R loudness test pending.')
    (ROOT/'validation/clash_vo_v1_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
