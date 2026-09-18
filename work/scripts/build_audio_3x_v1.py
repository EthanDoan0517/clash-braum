"""Triple Braum sound and English voice playback gain without re-encoding media."""
import json,math,struct,sys,zipfile,hashlib,xml.etree.ElementTree as ET
import build_lightning_trial as p
from build_sfx_v3_volume import objects,props,EVENTPATH
from inspect_sfx_source import chunks
ROOT=p.ROOT;OUT=ROOT/'build/audio_3x_v1';GAIN=20*math.log10(3)
VO='assets/sounds/wwise2016/vo/en_us/characters/braum/skins/base/braum_base_vo_events.bnk'
def boost(original,label):
    rawpath=OUT/(label+'_original.bnk');rawpath.write_bytes(original)
    p.run([sys.executable,ROOT/'audit/scratch/wwiser-master/wwiser.py','-d','xml','-dn',OUT/(label+'_original'),rawpath])
    xml=ET.parse(OUT/(label+'_original.xml')).getroot();edits={};details=[]
    for oid,obj in objects(xml).items():
        if obj.get('name')!='CAkSound':continue
        start=int(obj.find('./field[@name="eHircType"]').get('offset'));length=int(obj.find('./field[@name="dwSectionSize"]').get('value'))
        raw=original[start:start+5+length];assert raw[0]==2 and struct.unpack_from('<I',raw,5)[0]==oid
        count=props(obj).find('./field[@name="cProps"]');n=int(count.get('value'));at=int(count.get('offset'))-start
        ids=raw[at+1:at+1+n];values=raw[at+1+n:at+1+n+4*n]
        assert raw[at]==n
        if 0 in ids:
            idx=ids.index(0);off=at+1+n+4*idx;old=struct.unpack_from('<f',raw,off)[0]
            updated=bytearray(raw);struct.pack_into('<f',updated,off,old+GAIN)
            restored=bytearray(updated);struct.pack_into('<f',restored,off,old);assert restored==raw
            updated=bytes(updated)
        else:
            old=0.0
            updated=raw[:at]+bytes([n+1,0])+ids+struct.pack('<f',GAIN)+values+raw[at+1+5*n:]
            updated=updated[:1]+struct.pack('<I',len(updated)-5)+updated[5:]
            restored=updated[:at]+bytes([n])+updated[at+2:at+2+n]+updated[at+2+n+4:]
            restored=restored[:1]+struct.pack('<I',length)+restored[5:];assert restored==raw
        edits[oid]=updated;details.append(dict(sound_id=oid,old_db=old,new_db=old+GAIN))
    assert edits
    rebuilt=[];unchanged=0
    for tag,body in chunks(original):
        if tag==b'HIRC':
            count=struct.unpack_from('<I',body)[0];at=4;parts=[]
            for _ in range(count):
                size=struct.unpack_from('<I',body,at+1)[0];raw=body[at:at+5+size];oid=struct.unpack_from('<I',raw,5)[0]
                parts.append(edits.get(oid,raw));unchanged+=oid not in edits;at+=5+size
            assert at==len(body);body=struct.pack('<I',count)+b''.join(parts)
        rebuilt.append(tag+struct.pack('<I',len(body))+body)
    bank=b''.join(rebuilt);target=OUT/(label+'.bnk');target.write_bytes(bank)
    p.run([sys.executable,ROOT/'audit/scratch/wwiser-master/wwiser.py','-d','xml','-dn',OUT/label,target])
    parsed=objects(ET.parse(OUT/(label+'.xml')).getroot());assert parsed.keys()==objects(xml).keys()
    for d in details:
        volumes=[v for v in props(parsed[d['sound_id']]).findall('./list/object') if v.find('./field[@name="pID"]').get('value')=='0']
        assert len(volumes)==1
        actual=float(volumes[0].find('./field[@name="pValue"]').get('value'))
        assert abs(actual-d['new_db'])<.00002
        assert abs(10**((actual-d['old_db'])/20)-3)<.00001
    return bank,dict(sound_count=len(edits),unchanged_objects=unchanged,changes=details)

def main():
    assert not OUT.exists(),'Preserve prior outputs.'
    parent=ROOT/'build/user_hex_v1/Braum_Clash_Custom_Hex_Full_Lightning_R_v1.fantome'
    assert p.sha(parent)=='f81b7c04644c856997004b2bc9e1a97e231b16a2fa20a92383deb65f650b6601'
    OUT.mkdir(parents=True)
    with zipfile.ZipFile(parent) as z:
        assert z.testzip() is None;before={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
    after=before.copy();details={}
    prefix='WAD/Braum.wad.client/'
    assert prefix+VO not in before
    for label,path,original in [('sfx',EVENTPATH,before[prefix+EVENTPATH]),('voice',VO,(ROOT/'audit/scratch/voice_original/17802985c2cae524.bnk').read_bytes())]:
        bank,details[label]=boost(original,label);after[prefix+path]=bank
    assert details['voice']['sound_count']==115
    info=json.loads(after['META/info.json']);info.update(Name='Clash Braum Custom Colors + 3x Voice and SFX',Version='0.4.5-audio-3x',Description='Custom hex colors and full-lightning R retained. All Braum SFX and English voice sound nodes gain +9.542425dB (3x linear amplitude) relative to prior candidate. Playback balance/distortion check pending.')
    after['META/info.json']=json.dumps(info,indent=2).encode()
    assert {n for n in before if before[n]!=after[n]}=={'META/info.json',prefix+EVENTPATH}
    assert after.keys()-before.keys()=={prefix+VO}
    archive=OUT/'Braum_Clash_Custom_Hex_3x_Voice_SFX_v1.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(after.items()):z.writestr(n,b)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None and set(z.namelist())==set(after) and all(z.read(n)==b for n,b in after.items())
    # Only the two affected banks require an isolated backend path/byte check.
    sys.path.insert(0,str(ROOT/'audit/scratch/python_lib'));from xxhash import xxh64_hexdigest
    validation=OUT/'validation'
    p.run(['C:/Users/etqdo/Downloads/cslol-go/cslol-tools/mod-tools.exe','import',archive,validation/'imported'])
    for path in [EVENTPATH,VO]:
        key=xxh64_hexdigest(path.encode())
        p.run(['C:/Users/etqdo/Downloads/wadtools-0.5.7-windows-x64/wadtools.exe','--config',ROOT/'work/config/wadtools.toml','--hashtable-dir',ROOT/'work/cache/hashes','--progress=false','extract','-i',validation/'imported/WAD/Braum.wad.client','-o',validation/key,'--no-bin-paths','--hash',key])
        matches=[f for f in (validation/key).rglob('*') if f.is_file() and f.stem==key]
        assert len(matches)==1 and matches[0].read_bytes()==after[prefix+path]
    report=dict(status='PASS sound property/independent parser/package/isolated bank checks; gameplay pending',archive=archive.relative_to(ROOT).as_posix(),sha256=p.sha(archive),parent_sha256=p.sha(parent),linear_amplitude_multiplier=3,gain_db=GAIN,banks=details,protected='All media/WPK bytes, timings, containers, play/stop actions, visual assets, full R and geometry exact. Only sound-level Volume properties and required bank lengths changed.',reused='All unchanged media decode/cache/timing evidence and visual validation. No audio reencoding or visual checks.',runtime='Check actual voice/SFX loudness, distortion, mix balance and E stop behavior; game mixer may limit peaks. User explicitly reopens E volume with all-SFX request.')
    (ROOT/'validation/audio_3x_v1_build.json').write_text(json.dumps(report,indent=2));(ROOT/'validation/audio_3x_v1_logs.json').write_text(json.dumps(p.logs,indent=2))
    print(json.dumps({k:report[k] for k in ['status','archive','sha256','gain_db']},indent=2));print({k:v['sound_count'] for k,v in details.items()})
if __name__=='__main__':main()
