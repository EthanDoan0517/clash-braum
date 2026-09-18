"""Raise only the 20 working custom SFX by 10dB in their sound properties."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys,zipfile,xml.etree.ElementTree as ET
from inspect_sfx_source import chunks
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/sfx_v3_volume'
GAIN=10.0
sha=lambda b:hashlib.sha256(b).hexdigest()
EVENTPATH='assets/sounds/wwise2016/sfx/characters/braum/skins/base/braum_base_sfx_events.bnk'

def objects(xml):
    return {int(o.find('./field[@name="ulID"]').get('value')):o for o in xml.findall('.//list[@name="listLoadedItem"]/object')}

def props(obj):
    return obj.find('.//object[@name="NodeInitialParams"]/object[@name="AkPropBundle<AkPropValue,unsigned char>"]')

def main():
    assert not OUT.exists(),'Preserve prior outputs.'
    report=json.loads((ROOT/'validation/sfx_v2_refinement_build.json').read_text())
    parent=ROOT/report['archive'];assert sha(parent.read_bytes())==report['sha256']
    original=(ROOT/'Braum.wad/6a0cd1a55c7df583.bnk').read_bytes()
    assert sha(original)==report['event_bank_sha256_unchanged']
    xml=ET.fromstring('<banks>'+(ROOT/'audit/evidence/base_audio_wwiser.xml').read_text()+'</banks>')[0]
    wanted={x['id'] for x in report['changed_media']};edits={};details=[]
    for oid,obj in objects(xml).items():
        media=obj.find('.//field[@name="sourceID"]')
        if media is None or int(media.get('value')) not in wanted:continue
        assert obj.get('name')=='CAkSound'
        start=int(obj.find('./field[@name="eHircType"]').get('offset'))
        length=int(obj.find('./field[@name="dwSectionSize"]').get('value'))
        raw=original[start:start+5+length];assert raw[0]==2 and struct.unpack_from('<I',raw,5)[0]==oid
        bundle=props(obj);count=bundle.find('./field[@name="cProps"]');n=int(count.get('value'));at=int(count.get('offset'))-start
        assert raw[at]==n
        ids=raw[at+1:at+1+n];values=raw[at+1+n:at+1+n+4*n]
        if 0 in ids:
            idx=ids.index(0);old=struct.unpack_from('<f',values,4*idx)[0]
            updated=bytearray(raw);struct.pack_into('<f',updated,at+1+n+idx*4,old+GAIN);updated=bytes(updated)
        else:
            old=0.0
            updated=raw[:at]+bytes([n+1,0])+ids+struct.pack('<f',GAIN)+values+raw[at+1+5*n:]
            updated=updated[:1]+struct.pack('<I',len(updated)-5)+updated[5:]
            # Strip the new property to prove every other original byte is preserved.
            restored=updated[:at]+bytes([n])+updated[at+2:at+2+n]+updated[at+2+n+4:at+2+n+4+4*n]+updated[at+2+n+4+4*n:]
            restored=restored[:1]+struct.pack('<I',length)+restored[5:];assert restored==raw
        edits[oid]=updated;details.append({'sound_id':oid,'media_id':int(media.get('value')),'old_db':old,'new_db':old+GAIN})
    assert len(edits)==20
    rebuilt=[];unchanged=0
    for tag,body in chunks(original):
        if tag==b'HIRC':
            count=struct.unpack_from('<I',body)[0];at=4;parts=[]
            for _ in range(count):
                size=struct.unpack_from('<I',body,at+1)[0];raw=body[at:at+5+size];oid=struct.unpack_from('<I',raw,5)[0]
                parts.append(edits.get(oid,raw));unchanged+=oid not in edits;at+=5+size
            assert at==len(body);body=struct.pack('<I',count)+b''.join(parts)
        rebuilt.append(tag+struct.pack('<I',len(body))+body)
    bank=b''.join(rebuilt)
    OUT.mkdir();package=OUT/'package'
    with zipfile.ZipFile(parent) as z:
        z.extractall(package);previous={n:z.read(n) for n in z.namelist()}
    bankfile=package/'WAD/Braum.wad.client'/EVENTPATH;assert not bankfile.exists();bankfile.write_bytes(bank)
    logs=[]
    def run(args):
        r=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8',errors='replace')
        logs.append({'argv':list(map(str,args)),'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        (ROOT/'validation/sfx_v3_volume_logs.json').write_text(json.dumps(logs,indent=2));assert r.returncode==0,(r.stdout,r.stderr)
    # Independent parser must recover exactly the intended sound-level Volume values.
    run([sys.executable,ROOT/'audit/scratch/wwiser-master/wwiser.py','-d','xml','-dn',OUT/'events',bankfile])
    parsed=ET.parse(OUT/'events.xml').getroot();parsed_objects=objects(parsed)
    assert len(parsed_objects)==len(objects(xml))
    for d in details:
        bundle=props(parsed_objects[d['sound_id']])
        volume=[p for p in bundle.findall('./list/object') if p.find('./field[@name="pID"]').get('value')=='0']
        assert len(volume)==1
        assert float(volume[0].find('./field[@name="pValue"]').get('value'))==d['new_db']
        assert '[Volume]' in volume[0].find('./field[@name="pID"]').get('valuefmt')
    info=package/'META/info.json';meta=json.loads(info.read_text());meta.update(Name='Clash Braum - Louder Electrical SFX v3',Version='0.1.0-sfx-v3-volume',Description='Working SFX v2 audio and refinement visuals preserved. Only the 20 custom Q/E/R sounds receive +10dB playback volume. Manual loudness/distortion check required. VO remains native.')
    info.write_text(json.dumps(meta,indent=2))
    for n,b in previous.items():
        if n!='META/info.json':assert (package/n).read_bytes()==b
    archive=OUT/'Braum_Clash_Louder_SFX_v3.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(package.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(package).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist())==set(previous)|{'WAD/Braum.wad.client/'+EVENTPATH}
        for n in z.namelist():assert z.read(n)==(package/n).read_bytes()
    # Changed event bank is the only payload requiring backend validation.
    sys.path.insert(0,str(ROOT/'audit/scratch/python_lib'));from xxhash import xxh64_hexdigest
    key=xxh64_hexdigest(EVENTPATH.encode());validation=OUT/'validation'
    run(['C:/Users/etqdo/Downloads/cslol-go/cslol-tools/mod-tools.exe','import',archive,validation/'imported'])
    run(['C:/Users/etqdo/Downloads/wadtools-0.5.7-windows-x64/wadtools.exe','--config',ROOT/'work/config/wadtools.toml','--hashtable-dir',ROOT/'work/cache/hashes','--progress=false','extract','-i',validation/'imported/WAD/Braum.wad.client','-o',validation/'extracted','--no-bin-paths','--hash',key])
    matches=[p for p in (validation/'extracted').rglob('*') if p.is_file() and p.stem==key];assert len(matches)==1 and matches[0].read_bytes()==bank
    result={'status':'PASS','archive':archive.relative_to(ROOT).as_posix(),'sha256':sha(archive.read_bytes()),'parent':report['archive'],'parent_sha256':report['sha256'],'gain_db':GAIN,'changes':details,'unchanged_hirc_objects':unchanged,'event_bank_sha256':sha(bank),'event_bank_path':EVENTPATH,'all_parent_payloads_exact':True,'independent_parser_volume_values_verified':True,'isolated_backend_changed_bank_exact':True,'reused':'User confirms v2 sounds work great, only too quiet. Audio bank/codec/cache hashes/sample timing and all visuals exact. Only sound-level Volume properties change; other HIRC objects including play/stop/actions/containers and all remaining sound fields preserved. Reuse v2 runtime/media validation; no reencoding or asset checks.','runtime':'Needs volume balance/distortion and E cleanup check; +10dB may expose source beeps or mixer peaks.'}
    (ROOT/'validation/sfx_v3_volume_build.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:result[k] for k in ['status','archive','sha256','gain_db','unchanged_hirc_objects']},indent=2))
if __name__=='__main__':main()
