"""Texture-only stylized color lift on the E Electric v2 candidate."""
import hashlib, json, zipfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import build_lightning_trial as pipeline

ROOT = pipeline.ROOT
OUT = ROOT / 'build/color_pop_v1'


def main():
    assert not OUT.exists(), 'Preserve existing candidate; choose a new version.'
    parent = ROOT / 'build/e_electric_v2/Braum_Clash_E_Electric_v2.fantome'
    assert pipeline.sha(parent) == 'c316e44b068ac844e36265c86263ef701aeecc3d64b4ab17abb2ebd708607dab'
    OUT.mkdir(parents=True)
    package = OUT / 'package'
    with zipfile.ZipFile(parent) as z:
        assert z.testzip() is None
        z.extractall(package)
        parent_bytes = {n: z.read(n) for n in z.namelist() if not n.endswith('/')}
    assets = package / 'WAD/Braum.wad.client' / pipeline.ASSET
    changes = []
    preview = Image.new('RGB', (1024, 1080), '#191d24')
    draw = ImageDraw.Draw(preview)
    for row, (name, exponent, saturation) in enumerate([('body', .70, 1.45), ('shield_frame', .78, 1.30)]):
        src = ROOT / 'work/textures/brightness_v1' / (name + '.png')
        # Match the source PNG to the existing recorded brightness pass.
        prior = json.loads((ROOT / 'validation/lightning_v1_build.json').read_text())
        assert pipeline.sha(src) == prior['brightness'][name]['output_sha256']
        a = np.array(Image.open(src).convert('RGBA'))
        rgb = a[:, :, :3].astype(np.float64) / 255
        peak = rgb.max(axis=2, keepdims=True)
        # Boost chroma around luminance, normalize peak to avoid clipped channels,
        # then lift the value curve. Pure black stays black; alpha is untouched.
        lum = (rgb * [0.2126, 0.7152, 0.0722]).sum(axis=2, keepdims=True)
        vivid = np.maximum(lum + saturation * (rgb - lum), 0)
        chroma = vivid / np.maximum(vivid.max(axis=2, keepdims=True), 1e-12)
        value = np.minimum(1.06 * peak ** exponent, 1)
        b = a.copy()
        b[:, :, :3] = np.rint(255 * chroma * value).astype(np.uint8)
        assert np.array_equal(a[:, :, 3], b[:, :, 3])
        assert np.all(b[:, :, :3].max(axis=2) >= a[:, :, :3].max(axis=2))
        assert np.all(b[:, :, :3][peak[:, :, 0] == 0] == 0)
        png = OUT / (name + '.png')
        Image.fromarray(b).save(png)
        target = assets / (name + '.tex')
        pipeline.run([pipeline.TEX, 'encode', png, '-o', target, '-f', 'bc3', '--generate-mipmaps'])
        mip_checks = []
        for mip in (0, 2, 4):
            decoded = OUT / f'{name}_mip{mip}.png'
            pipeline.run([pipeline.TEX, 'decode', target, '-o', decoded, '--mipmap', mip])
            new = np.array(Image.open(decoded).convert('RGBA'))
            old = np.array(Image.open(ROOT / 'build/lightning_v1' / decoded.name).convert('RGBA'))
            assert new.shape == old.shape
            assert np.array_equal(new[:, :, 3], old[:, :, 3]), (name, mip, 'encoded alpha changed')
            mip_checks.append(dict(mip=mip, dimensions=list(new.shape[:2]), alpha_exact=True))
        active = (peak[:, :, 0] > .02) & (a[:, :, 3] > 0)
        changes.append(dict(texture=name, source_sha256=pipeline.sha(src), png_sha256=pipeline.sha(png),
                            tex_sha256=pipeline.sha(target), value_exponent=exponent, saturation=saturation,
                            active_mean_peak_before=float(peak[:, :, 0][active].mean()),
                            active_mean_peak_after=float(b[:, :, :3].max(axis=2)[active].mean()/255),
                            encoded_mips=mip_checks))
        old_img = Image.open(ROOT / f'build/lightning_v1/{name}_mip2.png').convert('RGB')
        new_img = Image.open(OUT / f'{name}_mip2.png').convert('RGB')
        draw.text((12, row*540+8), name + ' - previous', fill='white')
        draw.text((524, row*540+8), name + ' - color pop', fill='white')
        preview.paste(old_img, (0, row*540+28))
        preview.paste(new_img, (512, row*540+28))
    preview.save(OUT / 'comparison.png')
    meta = package / 'META/info.json'
    info = json.loads(meta.read_text())
    info.update(Name='Clash Braum Color Pop v1 TRIAL', Version='0.2.2-color',
                Description='Stronger model midtones and saturation; E Electric v2 effects retained. Manual gameplay comparison pending. Enable only one Clash candidate.')
    meta.write_text(json.dumps(info, indent=2))
    allowed = {'META/info.json'} | {'WAD/Braum.wad.client/' + pipeline.ASSET + n + '.tex' for n in ('body', 'shield_frame')}
    actual = {p.relative_to(package).as_posix(): p.read_bytes() for p in package.rglob('*') if p.is_file()}
    assert actual.keys() == parent_bytes.keys()
    changed = {n for n in actual if actual[n] != parent_bytes[n]}
    assert changed == allowed, changed
    archive = OUT / 'Braum_Clash_Color_Pop_v1.fantome'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(actual.items()):
            z.writestr(name, data)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert all(z.read(n) == b for n, b in actual.items())
    report = dict(status='PASS texture/package checks; gameplay pending', archive=str(archive.relative_to(ROOT)),
                  sha256=pipeline.sha(archive), parent_sha256=pipeline.sha(parent), textures=changes,
                  changed_members=sorted(changed), protected='All other members byte-identical, including geometry, rig, BIN and VFX.',
                  reused='E v2 BIN/backend evidence and v1 geometry evidence: relevant bytes unchanged. No new paths or BIN changes; no repeated backend/geometry checks.',
                  preview='build/color_pop_v1/comparison.png')
    (ROOT / 'validation/color_pop_v1_build.json').write_text(json.dumps(report, indent=2))
    (ROOT / 'validation/color_pop_v1_build_logs.json').write_text(json.dumps(pipeline.logs, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
