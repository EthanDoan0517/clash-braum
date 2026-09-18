"""Remove residual E frost layers from the validated v1 core; isolated output only."""
from pathlib import Path
import json, re, shutil, zipfile
import build_lightning_trial as v1

ROOT = v1.ROOT
BASE = ROOT / 'build/lightning_v1/core'
OUT = ROOT / 'build/e_electric_v2'
PREFIX = 'Characters/Braum/Skins/Skin0/Particles/Clash_v1_'
REMOVE = {
    'Braum_E_Shield_cas': {'Inchant_shield_ice', 'Ice_Override', 'smoke'},
    'Braum_E_Block_Spell_cas': {'smoke', 'debris'},
    'Braum_E_shield_end': {'shield_break1', 'shield_break2'},
    'Braum_E_shield_first_block': {'smoke'},
    'Braum_E_Shield_first_block_end': {'shield_break1', 'shield_break2'},
}


def main():
    assert not OUT.exists(), 'Preserve previous output; choose a new candidate version.'
    archive = BASE / 'Braum_Clash_Core_v1.fantome'
    assert v1.sha(archive) == '2a8653b83ae63f704db7e4a398330e84e6d2104aa0e16eb647b4fe3b4bafdae8'
    report = json.loads((ROOT / 'validation/lightning_v1_build.json').read_text())
    parent = next(b for b in report['builds'] if b['label'] == 'core')
    source = (BASE / 'skin0.ritobin').read_text()
    original = v1.entries(source)
    changed = {}
    edits = []
    for key, names in REMOVE.items():
        entry = original[PREFIX + key]
        found = set()
        for lo, hi, block in reversed(list(v1.blocks(entry, r'^            VfxEmitterDefinitionData \{'))):
            name = re.search(r'EmitterName: string = "([^"]+)"', block).group(1)
            if name in names:
                # Removed layers must not carry audio, child effects or gameplay events.
                assert not re.search(r'(?i)(sound|audio|child|event)', block), name
                found.add(name)
                entry = entry[:lo] + entry[hi:]
        assert found == names, (key, found)
        changed[PREFIX + key] = entry
        edits.append(dict(system=key, removed_emitters=sorted(found)))

    key = PREFIX + 'Braum_E_Shield_cas'
    entry = changed[key]
    # The enchant surface already uses lightning, but its second texture still
    # multiplies it by a moving ice mask. Remove that mask, retaining UV/timing.
    masks = 0
    for lo, hi, block in reversed(list(v1.blocks(entry, r'^            VfxEmitterDefinitionData \{'))):
        name = re.search(r'EmitterName: string = "([^"]+)"', block).group(1)
        if name not in {'Inchant_shield', 'Inchant_shield_2'}:
            continue
        fields = list(v1.blocks(block, r'^                TextureMult: pointer = VfxTextureMultDefinitionData \{'))
        assert len(fields) == 1, name
        a, b, old = fields[0]
        assert 'Braum_Base_E_shield_inchant_mult.tex' in old
        new = block[:a] + block[b:]
        assert new[:a] + old + new[a:] == block
        entry = entry[:lo] + new + entry[hi:]
        masks += 1
    assert masks == 2
    entry = v1.transform(entry, ['Inchant_flash'], 'E v2 activation')
    changed[key] = entry
    for key, replacement in changed.items():
        assert source.count(original[key]) == 1
        source = source.replace(original[key], replacement)
    after = v1.entries(source)
    assert after.keys() == original.keys()
    for key in original:
        if key not in changed:
            assert after[key] == original[key], key
        else:
            # Compare surviving emitters by name, independently of removal offsets.
            def emitters(e):
                return {re.search(r'EmitterName: string = "([^"]+)"', b).group(1): b
                        for _, _, b in v1.blocks(e, r'^            VfxEmitterDefinitionData \{')}
            before_e, after_e = emitters(original[key]), emitters(after[key])
            assert before_e.keys() - after_e.keys() == REMOVE[key[len(PREFIX):]]
            for name, block in after_e.items():
                if key == PREFIX + 'Braum_E_Shield_cas' and name in {'Inchant_shield', 'Inchant_shield_2', 'Inchant_flash'}:
                    expected = before_e[name]
                    if name == 'Inchant_flash':
                        expected = v1.transform(expected, [name], 'E v2 guard')
                    else:
                        for a, b, _ in reversed(list(v1.blocks(expected, r'^                TextureMult: pointer = VfxTextureMultDefinitionData \{'))):
                            expected = expected[:a] + expected[b:]
                    assert block == expected
                else:
                    assert block == before_e[name], (key, name)

    OUT.mkdir(parents=True)
    package = OUT / 'package'
    # Use the hash-bound archive itself, not potentially edited staging assets.
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        z.extractall(package)
    wad = package / 'WAD/Braum.wad.client'
    for payload in parent['payloads']:
        assert v1.sha(wad / payload['path']) == payload['sha256']
    candidate = OUT / 'skin0.ritobin'
    candidate.write_text(source)
    binpath = wad / 'data/characters/braum/skins/skin0.bin'
    # Bind the readable parent to the validated BIN before using it as input.
    v1.run([v1.RITO, '-i', 'text', '-o', 'bin', '-k', BASE / 'skin0.ritobin', OUT / 'parent.bin'])
    assert v1.sha(OUT / 'parent.bin') == v1.sha(binpath)
    v1.run([v1.RITO, '-i', 'text', '-o', 'bin', '-k', candidate, binpath])
    v1.run([v1.RITO, '-i', 'bin', '-o', 'text', binpath, OUT / 'verified.ritobin'])
    v1.run([v1.RITO, '-i', 'text', '-o', 'bin', '-k', OUT / 'verified.ritobin', OUT / 'verified.bin'])
    assert v1.sha(binpath) == v1.sha(OUT / 'verified.bin')
    for payload in parent['payloads']:
        if payload['path'] != 'data/characters/braum/skins/skin0.bin':
            assert v1.sha(wad / payload['path']) == payload['sha256']
    meta = package / 'META/info.json'
    info = json.loads(meta.read_text())
    info.update(Name='Clash Braum E Electric v2 TRIAL', Version='0.2.1-e',
                Description='Core v1 plus E frost-overlay, smoke and shatter removal; electrical activation. Manual gameplay acceptance pending. Enable only one Clash trial.')
    meta.write_text(json.dumps(info, indent=2))
    output = OUT / 'Braum_Clash_E_Electric_v2.fantome'
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(package.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(package).as_posix())
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None
        for p in package.rglob('*'):
            if p.is_file():
                assert z.read(p.relative_to(package).as_posix()) == p.read_bytes()
    result = dict(status='PASS targeted offline; gameplay pending', archive=str(output.relative_to(ROOT)),
                  sha256=v1.sha(output), parent_sha256=v1.sha(archive), changes=edits,
                  removed_ice_masks=masks, activation='Inchant_flash texture/RGB converted with v1 protected-field guard',
                  guards=['Parent text compiles to hash-bound v1 BIN', 'Only five E entries changed',
                          'Surviving emitter fields exact except two ice masks and activation texture/RGB',
                          'All other payloads exact, including accepted geometry, brightness and lightning texture',
                          'Candidate BIN byte-stable roundtrip', 'ZIP CRC and all member bytes exact'],
                  reused_evidence=['validation/lightning_v1_validation.json: unchanged non-BIN payload paths/bytes and toolchain; no repeat geometry or texture checks'],
                  limitations=['Existing enchant/block mesh carriers remain; E silhouette/alignment and intensity require gameplay.',
                               'Q/W/R remain v1; no custom SFX/VO; no runtime acceptance.'],
                  payloads=[dict(path=p.relative_to(wad).as_posix(), sha256=v1.sha(p)) for p in sorted(wad.rglob('*')) if p.is_file()])
    (ROOT / 'validation/e_electric_v2_build.json').write_text(json.dumps(result, indent=2))
    (ROOT / 'validation/e_electric_v2_build_logs.json').write_text(json.dumps(v1.logs, indent=2))
    print(json.dumps({k: result[k] for k in ['status', 'archive', 'sha256', 'changes']}, indent=2))


if __name__ == '__main__':
    main()
