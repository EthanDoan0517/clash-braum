"""Preserve directional visuals and the concurrently completed volume-only SFX v3."""
import json,zipfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sha=lambda b:hashlib.sha256(b).hexdigest()

def read(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        return {n:z.read(n) for n in z.namelist() if not n.endswith('/')}

def main():
    out=ROOT/'build/directional_sfx_v3';assert not out.exists()
    visual=json.loads((ROOT/'validation/directional_v1_build.json').read_text())
    audio=json.loads((ROOT/'validation/sfx_v3_volume_build.json').read_text())
    vp=ROOT/visual['archive'];ap=ROOT/audio['archive']
    assert sha(vp.read_bytes())==visual['sha256'] and sha(ap.read_bytes())==audio['sha256']
    base=read(ROOT/'build/sfx_v2_refinement/Braum_Clash_Refinement_SFX_v2.fantome')
    v=read(vp);a=read(ap)
    changes={n for n in a if a[n]!=base.get(n) and n!='META/info.json'}
    assert len(changes)==1 and all(n.endswith('.bnk') for n in changes)
    combined=dict(v)
    for n in changes:
        assert v.get(n)==base.get(n)
        combined[n]=a[n]
    meta=json.loads(v['META/info.json']);meta.update(Name='Clash Braum Directional v1 + Louder SFX v3',Version='0.3.5-directional-sfx3',Description='Directional 3D Q, balanced E edges, connected glowing W and two main R bolt layers. Preserves louder SFX v3 exactly. Manual gameplay review required.')
    combined['META/info.json']=json.dumps(meta,indent=2).encode()
    assert all(combined[n]==b for n,b in v.items() if n not in changes|{'META/info.json'})
    assert all(combined[n]==b for n,b in a.items() if n.endswith('.bnk'))
    out.mkdir();archive=out/'Braum_Clash_Directional_v1_SFX_v3.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(combined.items()):z.writestr(n,b)
    assert read(archive)==combined
    prefix='WAD/Braum.wad.client/'
    report=dict(visual,archive=archive.relative_to(ROOT).as_posix(),sha256=sha(archive.read_bytes()),visual_parent_sha256=visual['sha256'],audio_parent_sha256=audio['sha256'],reused='Directional visual assets exact; all SFX v3 banks exact. Reuse scoped visual checks and volume checks; validate combined packaging once.',payloads=[dict(path=n[len(prefix):],sha256=sha(b)) for n,b in sorted(combined.items()) if n.startswith(prefix)])
    (ROOT/'validation/directional_sfx_v3_build.json').write_text(json.dumps(report,indent=2))
    print(report['archive'],report['sha256'])

if __name__=='__main__':main()
