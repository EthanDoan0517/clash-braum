"""Remove E's oversized enchant surfaces and boost colors without crushing shadows."""
import json, re, zipfile
import numpy as np
from PIL import Image, ImageDraw
import build_lightning_trial as p
ROOT = p.ROOT
OUT = ROOT / 'build/color_pop_v3'


def main():
    assert not OUT.exists(), 'Preserve existing candidate.'
    parent = ROOT / 'build/color_pop_v2/Braum_Clash_Color_Pop_v2_E_Motion.fantome'
    assert p.sha(parent) == 'bddbf8ca5b05ffae78f45361307aeab71c88d73fdf70ef07de7b7c658adb4748'
    OUT.mkdir(parents=True)
    package = OUT / 'package'
    with zipfile.ZipFile(parent) as z:
        assert z.testzip() is None
        z.extractall(package)
        before = {n: z.read(n) for n in z.namelist() if not n.endswith('/')}
    wad = package / 'WAD/Braum.wad.client'
    text = (ROOT / 'build/e_motion_v3/skin0.ritobin').read_text()
    target = wad / 'data/characters/braum/skins/skin0.bin'
    p.run([p.RITO, '-i', 'text', '-o', 'bin', '-k', ROOT / 'build/e_motion_v3/skin0.ritobin', OUT / 'parent.bin'])
    assert p.sha(OUT / 'parent.bin') == p.sha(target)
    key = 'Characters/Braum/Skins/Skin0/Particles/Clash_v1_Braum_E_Shield_cas'
    original = p.entries(text)
    entry = original[key]
    removed = []
    for lo, hi, block in reversed(list(p.blocks(entry, r'^            VfxEmitterDefinitionData \{'))):
        name = re.search(r'EmitterName: string = "([^"]+)"', block).group(1)
        if name in {'Inchant_shield', 'Inchant_shield_2'}:
            assert 'Braum_Base_E_shield_inchant.scb' in block
            assert not re.search(r'(?i)(sound|audio|child|event)', block)
            entry = entry[:lo] + entry[hi:]
            removed.append(name)
    assert set(removed) == {'Inchant_shield', 'Inchant_shield_2'}
    # Removing whole balanced blocks preserves every surviving emitter exactly.
    assert all(b in entry for _, _, b in p.blocks(original[key], r'^            VfxEmitterDefinitionData \{')
               if re.search(r'EmitterName: string = "([^"]+)"', b).group(1) not in removed)
    text = text.replace(original[key], entry)
    after = p.entries(text)
    assert after.keys() == original.keys()
    assert {k for k in original if original[k] != after[k]} == {key}
    source = OUT / 'skin0.ritobin'; source.write_text(text)
    p.run([p.RITO, '-i', 'text', '-o', 'bin', '-k', source, target])
    p.run([p.RITO, '-i', 'bin', '-o', 'text', target, OUT / 'verified.ritobin'])
    p.run([p.RITO, '-i', 'text', '-o', 'bin', '-k', OUT / 'verified.ritobin', OUT / 'verified.bin'])
    assert p.sha(target) == p.sha(OUT / 'verified.bin')
    checks = []
    sheet = Image.new('RGB', (1024, 1080), '#191d24'); draw = ImageDraw.Draw(sheet)
    for row, (name, folder, gain) in enumerate([('body', 'color_pop_v2', .32), ('shield_frame', 'color_pop_v1', .25)]):
        src = ROOT / f'build/{folder}/{name}.png'
        # Source image encoding is bound to the actual parent payload.
        bound = OUT / f'{name}_parent.tex'
        p.run([p.TEX, 'encode', src, '-o', bound, '-f', 'bc3', '--generate-mipmaps'])
        tex = wad / p.ASSET / (name+'.tex')
        assert p.sha(bound) == p.sha(tex)
        a = np.array(Image.open(src).convert('RGBA'))
        rgb = a[:, :, :3].astype(float)/255
        peak = rgb.max(2, keepdims=True)
        low = rgb.min(2, keepdims=True)
        # Add chroma to stronger channels instead of subtracting from shadows.
        vivid = rgb + .25*(rgb-low)*(1-peak)
        vivid *= 1 + gain*(1-peak)
        b = a.copy(); b[:, :, :3] = np.rint(np.minimum(vivid, 1)*255).astype(np.uint8)
        assert np.array_equal(a[:, :, 3], b[:, :, 3])
        assert np.all(b[:, :, :3] >= a[:, :, :3])
        png = OUT / (name+'.png'); Image.fromarray(b).save(png)
        p.run([p.TEX, 'encode', png, '-o', tex, '-f', 'bc3', '--generate-mipmaps'])
        for mip in (0, 2, 4):
            decoded = OUT / f'{name}_mip{mip}.png'
            p.run([p.TEX, 'decode', tex, '-o', decoded, '--mipmap', mip])
            old = np.array(Image.open(ROOT / f'build/{folder}/{name}_mip{mip}.png').convert('RGBA'))
            new = np.array(Image.open(decoded).convert('RGBA'))
            assert new.shape == old.shape and np.array_equal(new[:, :, 3], old[:, :, 3])
            if name == 'body': assert new[:, :, :3].max(2)[new[:, :, 3]>=250].min() >= 16
            checks.append(dict(texture=name, mip=mip, alpha_exact=True))
        for col, path in enumerate([ROOT/f'build/{folder}/{name}_mip2.png', OUT/f'{name}_mip2.png']):
            img = Image.open(path).convert('RGBA'); bg = Image.new('RGBA', img.size, '#191d24'); bg.alpha_composite(img)
            sheet.paste(bg.convert('RGB'), (col*512, row*540+28))
            draw.text((col*512+12,row*540+8),name+(' previous' if col==0 else ' stronger color'), fill='white')
    sheet.save(OUT / 'comparison.png')
    meta = package / 'META/info.json'; info = json.loads(meta.read_text())
    info.update(Name='Clash Braum Color Pop v3 Clean Shield TRIAL', Version='0.2.5-color',
                Description='Stronger colors with readable shadows; oversized E enchant wave removed. Smaller block/activation effects retained. Enable only one candidate.')
    meta.write_text(json.dumps(info, indent=2))
    actual = {f.relative_to(package).as_posix(): f.read_bytes() for f in package.rglob('*') if f.is_file()}
    assert actual.keys() == before.keys()
    assert {k for k in actual if actual[k]!=before[k]} == {'META/info.json', 'WAD/Braum.wad.client/data/characters/braum/skins/skin0.bin'} | {'WAD/Braum.wad.client/'+p.ASSET+n+'.tex' for n in ['body','shield_frame']}
    archive = OUT / 'Braum_Clash_Color_Pop_v3_Clean_Shield.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for n,data in sorted(actual.items()): z.writestr(n,data)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and all(z.read(n)==b for n,b in actual.items())
    report = dict(status='PASS targeted offline; gameplay pending',archive=str(archive.relative_to(ROOT)),sha256=p.sha(archive),
                  parent_sha256=p.sha(parent),removed_emitters=removed,texture_checks=checks,
                  colors='Additive chroma .25; body midtone gain .32, shield .25. Source RGB channels never decrease; alpha exact.',
                  protected='All other entries/emitters and payloads exact. Accepted geometry/rig, Q/W/R, audio and remaining E timings unchanged.',
                  reused='Unchanged geometry/rig evidence; new texture checks and changed-BIN package check only.',
                  payloads=[dict(path=f.relative_to(wad).as_posix(),sha256=p.sha(f)) for f in sorted(wad.rglob('*')) if f.is_file()])
    (ROOT/'validation/color_pop_v3_build.json').write_text(json.dumps(report,indent=2))
    (ROOT/'validation/color_pop_v3_build_logs.json').write_text(json.dumps(p.logs,indent=2))
    print(json.dumps({k:report[k] for k in ['status','archive','sha256','removed_emitters']},indent=2))


if __name__ == '__main__': main()
