"""Independent WAD path/hash checks and backend round trips for all four trials."""
from pathlib import Path
import json, hashlib, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'audit/scratch/python_lib'))
from xxhash import xxh64_hexdigest
MOD=Path('C:/Users/etqdo/Downloads/cslol-go/cslol-tools/mod-tools.exe')
WAD=Path('C:/Users/etqdo/Downloads/wadtools-0.5.7-windows-x64/wadtools.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8',errors='replace')
 assert p.returncode==0,(p.stdout,p.stderr)
report=json.loads((ROOT/'validation/lightning_v1_build.json').read_text());results=[]
for build in report['builds']:
 archive=ROOT/build['archive'];assert sha(archive)==build['sha256'];out=archive.parent/'validation'
 assert not out.exists(),'Preserve previous validation';out.mkdir()
 run([MOD,'import',archive,out/'imported'])
 run([MOD,'export',out/'imported',out/'reexported.fantome'])
 run([MOD,'import',out/'reexported.fantome',out/'reimported'])
 run([WAD,'--config',ROOT/'work/config/wadtools.toml','--hashtable-dir',ROOT/'work/cache/hashes','--progress=false','extract',
      '-i',out/'reimported/WAD/Braum.wad.client','-o',out/'payloads','--no-bin-paths'])
 files={p.stem:p for p in (out/'payloads').rglob('*') if p.is_file()}
 assert len(files)==len(build['payloads'])
 for payload in build['payloads']:
  key=xxh64_hexdigest(payload['path'].lower().encode())
  assert key in files,(key,payload['path'])
  assert sha(files[key])==payload['sha256'],payload['path']
 results.append(dict(label=build['label'],package_sha256=sha(archive),payload_count=len(files),backend_roundtrip=True,exact_wad_paths_and_bytes=True))
(ROOT/'validation/lightning_v1_validation.json').write_text(json.dumps(dict(status='PASS offline; runtime pending',builds=results),indent=2))
print(json.dumps(results,indent=2))
