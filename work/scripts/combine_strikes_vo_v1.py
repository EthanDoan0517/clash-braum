"""Carry newer audio/VO into the verified strike visuals without regeneration."""
import json,zipfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        return {n:z.read(n) for n in z.namelist() if not n.endswith('/')}
def main():
    out=ROOT/'build/strike_vo_v1';assert not out.exists()
    visual=json.loads((ROOT/'validation/strike_v1_build.json').read_text())
    vp=ROOT/visual['archive'];ap=ROOT/'build/clash_vo_v1/Braum_Clash_English_VO_v1.fantome'
    assert sha(vp.read_bytes())==visual['sha256']
    assert sha(ap.read_bytes())=='03482d67b41b4ca3636e7a0770363654689c1e88306bb10249f191bad9d92bec'
    base=read(ROOT/'build/directional_sfx_v3/Braum_Clash_Directional_v1_SFX_v3.fantome');v=read(vp);a=read(ap)
    changes={n for n in a if a[n]!=base.get(n) and n!='META/info.json'}
    assert len(changes)==2 and all(n.endswith(('.bnk','.wpk')) for n in changes)
    combined=dict(v)
    for n in changes:
        assert v.get(n)==base.get(n);combined[n]=a[n]
    assert all(combined[n]==b for n,b in v.items() if n not in changes|{'META/info.json'})
    assert all(combined[n]==b for n,b in a.items() if n.endswith(('.bnk','.wpk')))
    meta=json.loads(v['META/info.json']);meta.update(Name='Clash Braum Travelling Strikes + English VO v1',Version='0.3.6-strikes-vo',Description='Stronger W glow, connected R tracks/strikes/scorch marks, Q/R ice cast removal. Accepted E exact. Latest English VO and Q/R audio volume preserved.')
    combined['META/info.json']=json.dumps(meta,indent=2).encode();out.mkdir();archive=out/'Braum_Clash_Travelling_Strikes_English_VO_v1.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(combined.items()):z.writestr(n,b)
    assert read(archive)==combined
    prefix='WAD/Braum.wad.client/'
    report=dict(visual,archive=archive.relative_to(ROOT).as_posix(),sha256=sha(archive.read_bytes()),visual_parent_sha256=visual['sha256'],audio_parent_sha256=sha(ap.read_bytes()),reused='All strike visuals exact; all latest English VO and Q/R-volume banks exact. Scoped visual and VO checks reused.',payloads=[dict(path=n[len(prefix):],sha256=sha(b)) for n,b in sorted(combined.items()) if n.startswith(prefix)])
    (ROOT/'validation/strike_vo_v1_build.json').write_text(json.dumps(report,indent=2));print(report['archive'],report['sha256'])
if __name__=='__main__':main()
