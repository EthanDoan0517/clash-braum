"""Offline package backend roundtrip, payload identity and installed baseline compatibility."""
from pathlib import Path
import json,hashlib,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'build/model_runtime_trial'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):
    r=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,text=True,encoding='utf8',errors='replace')
    assert r.returncode==0,(r.stdout,r.stderr)
mod=Path('C:/Users/etqdo/Downloads/cslol-go/cslol-tools/mod-tools.exe')
wad=Path('C:/Users/etqdo/Downloads/wadtools-0.5.7-windows-x64/wadtools.exe')
run([mod,'export',OUT/'imported',OUT/'reexported.fantome'])
run([mod,'import',OUT/'reexported.fantome',OUT/'reimported'])
run([wad,'--config',ROOT/'work/config/wadtools.toml','--hashtable-dir',ROOT/'work/cache/hashes','--progress=false','extract','-i',OUT/'reimported/WAD/Braum.wad.client','-o',OUT/'verified_payloads','--no-bin-paths'])
# Extraction without new-path hash table deliberately produces hashed payloads.
payloads={sha(p):p for p in (OUT/'verified_payloads').rglob('*') if p.is_file()}
expected=[p for p in (OUT/'package/WAD/Braum.wad.client').rglob('*') if p.is_file()]
assert len(payloads)==len(expected)==6
assert all(sha(p) in payloads for p in expected)
comparisons=[]
for relative,hashed in [('data/characters/braum/skins/skin0.bin','eb9d53354a504663.bin'),('data/characters/braum/animations/skin0.bin','0b01eaec2c944f55.bin'),('assets/characters/braum/skins/base/braum_base.skn','fbf88fcfc8ec8dc4.skn'),('assets/characters/braum/skins/base/braum_base.skl','9b8248658ce51711.skl')]:
    live=OUT/'live_baseline'/relative;original=ROOT/'Braum.wad'/hashed
    comparisons.append(dict(path=relative,live_sha256=sha(live),source_sha256=sha(original),identical=live.read_bytes()==original.read_bytes()))
result=dict(status='PASS offline package roundtrip/payload identity; runtime pending',package_sha256=sha(OUT/'Braum_Clash_Model_Trial.fantome'),six_wad_payloads_byte_identical=True,installed_baseline= comparisons,installed_key_assets_match_source=all(c['identical'] for c in comparisons),limits='Four key installed assets compared, not whole-WAD pristine provenance. No manager installation or game session performed. Normal/alpha, culling, animation transitions, Poro joke and performance require runtime observation.')
(ROOT/'validation/model_runtime_trial_validation.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
