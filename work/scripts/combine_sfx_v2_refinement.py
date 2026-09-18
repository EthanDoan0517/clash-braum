"""Combine verified cache-ID repair with newer visual refinement, without regeneration."""
from pathlib import Path
import json,zipfile,copy,hashlib
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/sfx_v2_refinement'
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
    assert not OUT.exists()
    audio=json.loads((ROOT/'validation/sfx_v2_build.json').read_text())
    visual=json.loads((ROOT/'validation/refinement_v2_build.json').read_text())
    parent=ROOT/visual['archive'];assert sha(parent.read_bytes())==visual['sha256']
    repaired=ROOT/audio['archive'];assert sha(repaired.read_bytes())==audio['sha256']
    OUT.mkdir();package=OUT/'package'
    with zipfile.ZipFile(parent) as z:
        assert z.testzip() is None;z.extractall(package);previous={n:z.read(n) for n in z.namelist()}
    path='WAD/Braum.wad.client/'+audio['bank_path'];assert path not in previous
    with zipfile.ZipFile(repaired) as z:bank=z.read(path)
    assert sha(bank)==audio['bank_sha256']
    bankfile=package/path;bankfile.parent.mkdir(parents=True,exist_ok=True);bankfile.write_bytes(bank)
    info=package/'META/info.json';meta=json.loads(info.read_text());meta.update(Name='Clash Braum - Refinement + SFX v2',Version='0.1.0-refinement-sfx-v2',Description='Latest refinement v2 visuals plus repaired authentic Q/E/R electrical SFX. Manual bank playback/cleanup test required. VO remains native.')
    info.write_text(json.dumps(meta,indent=2))
    for n,b in previous.items():
        if n!='META/info.json':assert (package/n).read_bytes()==b
    archive=OUT/'Braum_Clash_Refinement_SFX_v2.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(package.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(package).as_posix())
    report=copy.deepcopy(audio);report.update(archive=archive.relative_to(ROOT).as_posix(),sha256=sha(archive.read_bytes()),parent=parent.relative_to(ROOT).as_posix(),parent_sha256=visual['sha256'],audio_parent=repaired.relative_to(ROOT).as_posix(),audio_parent_sha256=audio['sha256'],reused_evidence='All refinement v2 visual payloads exact; repaired SFX v2 bank exact. No new encoding, VFX/texture/geometry regeneration.')
    (ROOT/'validation/sfx_v2_refinement_build.json').write_text(json.dumps(report,indent=2))
    print(report['archive'],report['sha256'])
if __name__=='__main__':main()
