"""Single isolated backend import and changed-BIN extraction; never touches manager state."""
from pathlib import Path
import hashlib, json, subprocess, sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'audit/scratch/python_lib'))
from xxhash import xxh64_hexdigest


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else 'e_electric_v2'
    assert label in {'e_electric_v2', 'e_motion_v3', 'color_pop_v3', 'clash_passive_v1', 'crackle_v1', 'readability_v1', 'refinement_v2', 'directional_sfx_v3', 'strike_v1', 'strike_vo_v1', 'palette_b_full_r_v1'}
    report = json.loads((ROOT / f'validation/{label}_build.json').read_text())
    archive = ROOT / report['archive']
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(archive) == report['sha256']
    out = archive.parent / 'validation'
    assert not out.exists(), 'Preserve existing validation.'
    out.mkdir()
    logs = []
    def run(args):
        p = subprocess.run(list(map(str, args)), capture_output=True, text=True, encoding='utf8', errors='replace')
        logs.append(dict(argv=list(map(str, args)), returncode=p.returncode, stdout=p.stdout, stderr=p.stderr))
        (ROOT / f'validation/{label}_package_logs.json').write_text(json.dumps(logs, indent=2))
        assert p.returncode == 0, (p.stdout, p.stderr)
    run(['C:/Users/etqdo/Downloads/cslol-go/cslol-tools/mod-tools.exe', 'import', archive, out / 'imported'])
    path = 'data/characters/braum/skins/skin0.bin'
    key = xxh64_hexdigest(path.encode())
    extract_args = ['C:/Users/etqdo/Downloads/wadtools-0.5.7-windows-x64/wadtools.exe',
         '--config', ROOT / 'work/config/wadtools.toml', '--hashtable-dir', ROOT / 'work/cache/hashes',
         '--progress=false', 'extract', '-i', out / 'imported/WAD/Braum.wad.client',
         '-o', out / 'payloads', '--no-bin-paths']
    if label not in {'clash_passive_v1', 'crackle_v1', 'readability_v1', 'refinement_v2', 'directional_sfx_v3', 'strike_v1', 'strike_vo_v1'}: extract_args += ['--hash', key]
    run(extract_args)
    matches = [p for p in (out / 'payloads').rglob('*') if p.is_file() and p.stem == key]
    assert len(matches) == 1
    expected = next(p['sha256'] for p in report['payloads'] if p['path'] == path)
    assert sha(matches[0]) == expected
    result = dict(status='PASS', package_sha256=sha(archive), changed_path=path, path_hash=key,
                  extracted_sha256=sha(matches[0]), isolated_backend_import=True,
                  reused='Parent unchanged payload evidence; builder proves unchanged bytes. No manager launch or installed-state changes.',
                  runtime='Awaiting user E gameplay feedback')
    if label in {'clash_passive_v1', 'crackle_v1', 'readability_v1', 'refinement_v2', 'directional_sfx_v3', 'strike_v1', 'strike_vo_v1'}:
        extracted = {p.stem: p for p in (out / 'payloads').rglob('*') if p.is_file()}
        assert len(extracted) == len(report['payloads'])
        for payload in report['payloads']:
            digest = xxh64_hexdigest(payload['path'].lower().encode())
            assert digest in extracted and sha(extracted[digest]) == payload['sha256'], payload['path']
        result.update(all_payload_paths_and_bytes_exact=True, payload_count=len(extracted),
                      runtime='Awaiting user E/Q/W/R/passive/loading feedback')
    if label=='palette_b_full_r_v1':result['runtime']='Awaiting user Palette B/silver and full-lightning R/dark ground/cleanup feedback; E accepted.'
    (ROOT / f'validation/{label}_validation.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
