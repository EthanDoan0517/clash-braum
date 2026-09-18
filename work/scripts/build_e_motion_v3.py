"""Animate the two sustained E lightning surfaces; preserve Color Pop textures."""
import json, re, zipfile
import build_lightning_trial as p
ROOT = p.ROOT
OUT = ROOT / 'build/e_motion_v3'


def main():
    assert not OUT.exists(), 'Preserve existing candidate.'
    parent = ROOT / 'build/color_pop_v1/Braum_Clash_Color_Pop_v1.fantome'
    assert p.sha(parent) == 'bbe5ae6f3ccf59ccb2cb1ec979c1ce47186198b9ce5a39d3ab7730a3d403d001'
    text = (ROOT / 'build/e_electric_v2/skin0.ritobin').read_text()
    key = 'Characters/Braum/Skins/Skin0/Particles/Clash_v1_Braum_E_Shield_cas'
    before = p.entries(text)
    old = before[key]
    entry = old
    rates = {'Inchant_shield': (0.18, 1.35), 'Inchant_shield_2': (-0.14, -1.05)}
    found = set()
    for lo, hi, block in reversed(list(p.blocks(entry, r'^            VfxEmitterDefinitionData \{'))):
        name = re.search(r'EmitterName: string = "([^"]+)"', block).group(1)
        if name not in rates:
            continue
        uv = list(p.blocks(block, r'^                BirthUvScrollRate: embed = ValueVector2 \{'))
        assert len(uv) == 1
        a, b, previous = uv[0]
        assert '{ 0, 0 }' in previous
        u, v = rates[name]
        replacement = ('                BirthUvScrollRate: embed = ValueVector2 {\n'
                       f'                    ConstantValue: vec2 = {{ {u}, {v} }}\n'
                       '                }')
        new = block[:a] + replacement + block[b:]
        assert new[:a] + previous + new[a+len(replacement):] == block
        entry = entry[:lo] + new + entry[hi:]
        found.add(name)
    assert found == rates.keys()
    text = text.replace(old, entry)
    after = p.entries(text)
    assert before.keys() == after.keys()
    assert {k for k in before if before[k] != after[k]} == {key}
    OUT.mkdir(parents=True)
    package = OUT / 'package'
    with zipfile.ZipFile(parent) as z:
        assert z.testzip() is None
        z.extractall(package)
        original = {n: z.read(n) for n in z.namelist() if not n.endswith('/')}
    wad = package / 'WAD/Braum.wad.client'
    target = wad / 'data/characters/braum/skins/skin0.bin'
    p.run([p.RITO, '-i', 'text', '-o', 'bin', '-k', ROOT / 'build/e_electric_v2/skin0.ritobin', OUT / 'parent.bin'])
    assert p.sha(OUT / 'parent.bin') == p.sha(target)
    source = OUT / 'skin0.ritobin'
    source.write_text(text)
    p.run([p.RITO, '-i', 'text', '-o', 'bin', '-k', source, target])
    p.run([p.RITO, '-i', 'bin', '-o', 'text', target, OUT / 'verified.ritobin'])
    p.run([p.RITO, '-i', 'text', '-o', 'bin', '-k', OUT / 'verified.ritobin', OUT / 'verified.bin'])
    assert p.sha(target) == p.sha(OUT / 'verified.bin')
    meta = package / 'META/info.json'
    info = json.loads(meta.read_text())
    info.update(Name='Clash Braum E Motion v3 TRIAL', Version='0.2.3-motion',
                Description='Counter-scrolling sustained E lightning; Color Pop textures unchanged. Reported black model regions remain under investigation. Enable only one trial.')
    meta.write_text(json.dumps(info, indent=2))
    files = {f.relative_to(package).as_posix(): f.read_bytes() for f in package.rglob('*') if f.is_file()}
    assert files.keys() == original.keys()
    assert {k for k in files if files[k] != original[k]} == {'META/info.json', 'WAD/Braum.wad.client/data/characters/braum/skins/skin0.bin'}
    archive = OUT / 'Braum_Clash_E_Motion_v3.fantome'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()): z.writestr(name, data)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert all(z.read(n) == b for n, b in files.items())
    report = dict(status='PASS targeted offline; runtime pending; black model defect unresolved',
                  archive=str(archive.relative_to(ROOT)), sha256=p.sha(archive), parent_sha256=p.sha(parent),
                  changes=dict(system=key, uv_scroll_cycles_per_second=rates),
                  protected='Only two BirthUvScrollRate blocks changed. Timing, alpha, scale, attachments, references, other entries and all texture/model bytes unchanged.',
                  animation='Continuous opposing UV scrolling of existing single-frame lightning; no flipbook or new assets.',
                  reused='Color Pop encoding/alpha/mip checks and accepted geometry evidence: identical bytes.',
                  payloads=[dict(path=f.relative_to(wad).as_posix(), sha256=p.sha(f)) for f in sorted(wad.rglob('*')) if f.is_file()])
    (ROOT / 'validation/e_motion_v3_build.json').write_text(json.dumps(report, indent=2))
    (ROOT / 'validation/e_motion_v3_build_logs.json').write_text(json.dumps(p.logs, indent=2))
    print(json.dumps({k: report[k] for k in ['status', 'archive', 'sha256', 'changes']}, indent=2))


if __name__ == '__main__': main()
