"""Repair v1 Vorbis setup hashes using the contract proven on all native media."""
from pathlib import Path
import copy,json,struct,zipfile
from diagnose_sfx_silence import wem_info,fnv,sha
from inspect_sfx_source import chunks

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/sfx_v2'

def main():
    assert not OUT.exists(),'Preserve previous candidates.'
    original_report=json.loads((ROOT/'validation/sfx_v1_build.json').read_text())
    diagnosis=json.loads((ROOT/'validation/sfx_silence_diagnosis.json').read_text())
    assert diagnosis['native_hash_algorithm_matches']['setup/fnv1']==114
    assert all(diagnosis['installed_banks_match_supplied'].values())
    v1=ROOT/original_report['archive'];assert sha(v1.read_bytes())==original_report['sha256']
    OUT.mkdir();package=OUT/'package';(OUT/'wem').mkdir()
    with zipfile.ZipFile(v1) as z:
        assert z.testzip() is None;z.extractall(package)
        oldfiles={name:z.read(name) for name in z.namelist()}
    path='WAD/Braum.wad.client/'+original_report['bank_path']
    bank=oldfiles[path];c=dict(chunks(bank));at=0;data_start=None
    for tag,raw in chunks(bank):
        if tag==b'DATA':data_start=at+8
        at+=8+len(raw)
    assert data_start is not None
    result=bytearray(bank);changed={x['id'] for x in original_report['changed_media']};hashes={};repairs=[]
    for mid,offset,size in struct.iter_unpack('<III',c[b'DIDX']):
        old=c[b'DATA'][offset:offset+size];p=wem_info(old)
        if mid not in changed:
            assert p['uid']==fnv(p['setup']);continue
        fixed=bytearray(old);assert old[12:16]==b'fmt '
        uid=fnv(p['setup']);assert uid!=p['uid'];struct.pack_into('<I',fixed,20+60,uid)
        fixed=bytes(fixed);q=wem_info(fixed)
        assert q['uid']==fnv(q['setup']) and q['setup']==p['setup']
        assert fixed[:80]==old[:80] and fixed[84:]==old[84:]
        result[data_start+offset:data_start+offset+size]=fixed
        (OUT/f'wem/{mid}.wem').write_bytes(fixed);hashes[mid]=sha(fixed)
        repairs.append({'id':mid,'old_uid':p['uid'],'correct_uid':uid,'setup_sha256':q['setup_sha256']})
    result=bytes(result);assert len(repairs)==20 and len(result)==len(bank)
    (package/path).write_bytes(result)
    info=package/'META/info.json';meta=json.loads(info.read_text())
    meta.update(Name='Clash Braum - Electrical SFX v2',Version='0.1.0-sfx-v2',Description='Repairs SFX v1 encoder Vorbis setup hashes; authentic Q/E/R electrical SFX, readability v1 visuals. Manual playback/cleanup test required. VO remains native.')
    info.write_text(json.dumps(meta,indent=2))
    for name,b in oldfiles.items():
        if name not in [path,'META/info.json']:assert (package/name).read_bytes()==b
    archive=OUT/'Braum_Clash_Electrical_SFX_v2.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(package.rglob('*')):
            if f.is_file():z.write(f,f.relative_to(package).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name in z.namelist():assert z.read(name)==(package/name).read_bytes()
    report=copy.deepcopy(original_report)
    report.update(archive=archive.relative_to(ROOT).as_posix(),sha256=sha(archive.read_bytes()),bank_sha256=sha(result),repair_parent=v1.relative_to(ROOT).as_posix(),repair_parent_sha256=sha(v1.read_bytes()),repair='uHashCodebook = FNV-1 of compressed setup bytes (excluding packet-size prefix); exact algorithm matches all 114 original media. Only 4 header bytes per replaced WEM changed from v1.',repairs=repairs,reused_decode_evidence='v1 masters, all compressed packets, sample counts and decoding metadata except setup cache hash byte-identical; reuse existing per-media decode/correlation/peak results. Native engine cache identifier verified separately across entire bank.',runtime='Awaiting user test; do not equate vgmstream decoding with engine cache compatibility.')
    for media in report['changed_media']:media['sha256']=hashes[media['id']]
    (ROOT/'validation/sfx_v2_build.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'archive':report['archive'],'sha256':report['sha256'],'repaired_media':len(repairs)},indent=2))

if __name__=='__main__':main()
