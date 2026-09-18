"""Lift crushed body shadows, including true black, while preserving brighter colors."""
import json, zipfile
import numpy as np
from PIL import Image, ImageDraw
import build_lightning_trial as p
ROOT = p.ROOT
OUT = ROOT / 'build/color_pop_v2'


def main():
    assert not OUT.exists(), 'Preserve existing candidate.'
    parent = ROOT / 'build/e_motion_v3/Braum_Clash_E_Motion_v3.fantome'
    assert p.sha(parent) == '9bb6c58c921ab4478b2b78194a5521fb44e8062494fbe5ef0162810ba3a810f3'
    src = ROOT / 'build/color_pop_v1/body.png'
    assert p.sha(src) == '4d2ff9ac79d900a206822c81def031c2d0cad02f922c87f8b4c095ed09401922'
    OUT.mkdir(parents=True)
    package = OUT / 'package'
    with zipfile.ZipFile(parent) as z:
        assert z.testzip() is None
        z.extractall(package)
        before = {n: z.read(n) for n in z.namelist() if not n.endswith('/')}
    a = np.array(Image.open(src).convert('RGBA'))
    rgb = a[:, :, :3].astype(np.float64)/255
    peak = rgb.max(axis=2, keepdims=True)
    # Soft additive slate-charcoal floor. The first pass preserved true black;
    # this explicitly makes it visible, with no change above 45% texture value.
    weight = np.maximum(1 - peak/.45, 0)**2
    out = rgb + weight * np.array([.18, .195, .22])
    b = a.copy()
    b[:, :, :3] = np.rint(np.minimum(out, 1)*255).astype(np.uint8)
    assert np.array_equal(a[:, :, 3], b[:, :, 3])
    assert np.all(b[:, :, :3] >= a[:, :, :3])
    assert np.array_equal(a[:, :, :3][peak[:, :, 0] >= .45], b[:, :, :3][peak[:, :, 0] >= .45])
    png = OUT / 'body.png'
    Image.fromarray(b).save(png)
    target = package / 'WAD/Braum.wad.client' / p.ASSET / 'body.tex'
    p.run([p.TEX, 'encode', png, '-o', target, '-f', 'bc3', '--generate-mipmaps'])
    checks = []
    for mip in (0, 2, 4):
        decoded = OUT / f'body_mip{mip}.png'
        p.run([p.TEX, 'decode', target, '-o', decoded, '--mipmap', mip])
        old = np.array(Image.open(ROOT / f'build/color_pop_v1/body_mip{mip}.png').convert('RGBA'))
        new = np.array(Image.open(decoded).convert('RGBA'))
        assert old.shape == new.shape
        assert np.array_equal(old[:, :, 3], new[:, :, 3])
        opaque = new[:, :, 3] >= 250
        # BC3 shares RGB endpoints across each 4x4 block; sparse boundaries can
        # undershoot the source floor. Reject true near-black, not minor error.
        assert np.all(new[:, :, :3].max(2)[opaque] >= 16), (mip, 'opaque texture still near-black')
        checks.append(dict(mip=mip, alpha_exact=True, opaque_peak_min=int(new[:, :, :3].max(2)[opaque].min())))
    sheet = Image.new('RGB', (1024, 540), '#191d24')
    draw = ImageDraw.Draw(sheet)
    for col, folder in enumerate(['color_pop_v1', 'color_pop_v2']):
        img = Image.open(ROOT / f'build/{folder}/body_mip2.png').convert('RGBA')
        bg = Image.new('RGBA', img.size, '#191d24')
        bg.alpha_composite(img)
        sheet.paste(bg.convert('RGB'), (col*512, 28))
        draw.text((col*512+12, 8), folder, fill='white')
    sheet.save(OUT / 'comparison.png')
    meta = package / 'META/info.json'
    info = json.loads(meta.read_text())
    info.update(Name='Clash Braum Color Pop v2 + E Motion TRIAL', Version='0.2.4-shadow',
                Description='Readable slate-charcoal body shadows plus counter-scrolling E lightning. Manual gameplay approval pending. Enable only one candidate.')
    meta.write_text(json.dumps(info, indent=2))
    actual = {f.relative_to(package).as_posix(): f.read_bytes() for f in package.rglob('*') if f.is_file()}
    assert actual.keys() == before.keys()
    assert {k for k in actual if actual[k] != before[k]} == {'META/info.json', 'WAD/Braum.wad.client/'+p.ASSET+'body.tex'}
    archive = OUT / 'Braum_Clash_Color_Pop_v2_E_Motion.fantome'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, data in sorted(actual.items()): z.writestr(n, data)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert all(z.read(n) == data for n, data in actual.items())
    report = dict(status='PASS affected texture checks; gameplay pending', archive=str(archive.relative_to(ROOT)),
                  sha256=p.sha(archive), parent_sha256=p.sha(parent), source_sha256=p.sha(src),
                  body_tex_sha256=p.sha(target), formula='RGB += max(1-max(RGB)/0.45,0)^2 * (0.18,0.195,0.22); alpha exact',
                  checks=checks, bright_pixels_exact=True, channel_values_never_decreased=True,
                  protected='All payloads except body.tex byte-identical to E Motion v3, including shield, BIN, geometry and rig.',
                  reused='validation/e_motion_v3_validation.json: identical BIN and paths; Color Pop v1 shield evidence: identical bytes.',
                  diagnosis='User identifies lower body, upper arms and strap as black. First color pass preserved true black and low-value fabric. Shadow floor addresses texture darkness; runtime lighting/material cause not excluded.',
                  preview='build/color_pop_v2/comparison.png')
    (ROOT / 'validation/color_pop_v2_build.json').write_text(json.dumps(report, indent=2))
    (ROOT / 'validation/color_pop_v2_build_logs.json').write_text(json.dumps(p.logs, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
