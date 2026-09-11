"""Exercise the user's cslol-go binaries against isolated development fixtures."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[2]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manager',type=Path,default=Path('C:/Users/etqdo/Downloads/cslol-go'))
    parser.add_argument('--wadtools',type=Path,default=Path('C:/Users/etqdo/Downloads/wadtools-0.5.7-windows-x64/wadtools.exe'))
    args=parser.parse_args()
    target=(ROOT/'build/manager_compat').resolve()
    assert target.is_relative_to(ROOT.resolve())
    target.mkdir(parents=True,exist_ok=True)
    logs=[]
    def run(argv):
        result=subprocess.run([str(x) for x in argv],cwd=ROOT,capture_output=True,text=True,encoding='utf8',errors='replace')
        logs.append(dict(argv=[str(x) for x in argv],returncode=result.returncode,stdout=result.stdout,stderr=result.stderr))
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    rito=args.manager/'cslol-tools/ritobin_cli.exe'
    mod=args.manager/'cslol-tools/mod-tools.exe'
    tools={str(p.relative_to(args.manager)):dict(path=str(p),sha256=sha(p)) for p in (args.manager/'ModLoader.dll',rito,mod)}
    source=ROOT/'Braum.wad/eb9d53354a504663.bin'
    bin_dir=ROOT/'build/bin_roundtrip';bin_dir.mkdir(exist_ok=True)
    run([rito,'-i','bin','-o','text','-k',source,bin_dir/'skin0.ritobin'])
    run([rito,'-i','text','-o','bin','-k',bin_dir/'skin0.ritobin',bin_dir/'skin0.bin'])
    assert source.read_bytes()==(bin_dir/'skin0.bin').read_bytes()
    (ROOT/'validation/bin_roundtrip.json').write_text(json.dumps(dict(byte_identical=True,sha256=sha(source),tools=tools),indent=2))
    fixture=target/'vanilla_roundtrip_validation.fantome'
    with zipfile.ZipFile(fixture,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('META/info.json',json.dumps(dict(Name='Braum vanilla roundtrip VALIDATION ONLY',Author='Ethan',Version='0.0.0',Description='Offline importer fixture. Not the Clash release.')))
        for extension in ('skn','skl'):
            archive.write(ROOT/f'build/roundtrip/braum_base.{extension}',f'WAD/Braum.wad.client/assets/characters/braum/skins/base/braum_base.{extension}')
    run([mod,'import',fixture,target/'imported'])
    run([mod,'export',target/'imported',target/'reexported.fantome'])
    run([mod,'import',target/'reexported.fantome',target/'reimported'])
    archive_reports=[]
    for path in (fixture,target/'reexported.fantome'):
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            names=archive.namelist()
            assert len(names)==len(set(n.lower() for n in names))
            assert all(n.startswith(('META/','WAD/')) for n in names)
            archive_reports.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),members=names,crc_ok=True))
    wad=target/'reimported/WAD/Braum.wad.client'
    data=wad.read_bytes();count=struct.unpack_from('<I',data,268)[0]
    assert data[:3]==b'RW\3' and count==2
    hashes={f'{struct.unpack_from("<Q",data,272+i*32)[0]:016x}' for i in range(count)}
    assert hashes=={'fbf88fcfc8ec8dc4','9b8248658ce51711'}
    config=ROOT/'work/config/wadtools.toml';config.write_text('# Project-local defaults\n')
    cache=ROOT/'work/cache/hashes';cache.mkdir(parents=True,exist_ok=True)
    run([args.wadtools,'--config',config,'--hashtable-dir',cache,'--progress=false','extract','-i',wad,
         '-o',target/'extracted','-H',ROOT/'audit/sources/project.hashes.txt','--no-bin-paths','--overwrite'])
    payloads=[]
    for extension in ('skn','skl'):
        original=ROOT/f'build/roundtrip/braum_base.{extension}'
        extracted=target/f'extracted/assets/characters/braum/skins/base/braum_base.{extension}'
        assert original.read_bytes()==extracted.read_bytes()
        payloads.append(dict(path=f'assets/characters/braum/skins/base/braum_base.{extension}',sha256=sha(extracted)))
    report=dict(status='PASS: supplied cslol-go backend import/export/reimport and independent payload extraction',
                scope='Offline vanilla fixture only. GUI import and League runtime remain untested.',tools=tools,
                archives=archive_reports,wad_version=list(data[2:4]),entry_hashes=sorted(hashes),payloads=payloads)
    (ROOT/'validation/manager_compatibility.json').write_text(json.dumps(report,indent=2))
    (ROOT/'validation/manager_checks.log.json').write_text(json.dumps(logs,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
