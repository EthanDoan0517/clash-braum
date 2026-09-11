"""Verify immutable inputs, stage the supplied addon, and record reproducible tools."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    for name in ('work/tools', 'work/scenes', 'work/textures', 'work/config',
                 'build/roundtrip', 'validation'):
        (ROOT / name).mkdir(parents=True, exist_ok=True)
    rows = json.loads((ROOT / 'audit/evidence/project_inventory.json').read_text())
    errors = []
    for row in rows:
        path = ROOT / row['relative_path']
        if not path.is_file() or sha(path) != row['sha256']:
            errors.append(row['relative_path'])
    extracted = json.loads((ROOT / 'audit/evidence/clash_archive_inventory.json').read_text())
    extraction_errors = [row['member'] for row in extracted
                         if sha(ROOT / 'audit/scratch' / row['member']) != row['sha256']]
    report = dict(checked_at=datetime.now(timezone.utc).isoformat(),
                  original_files=len(rows), mismatches=errors,
                  clash_extracted_files=len(extracted), extraction_mismatches=extraction_errors,
                  live_main_wad_present=Path('C:/Riot Games/League of Legends/Game/DATA/FINAL/Champions/Braum.wad.client').is_file())
    (ROOT / 'validation/source_integrity.json').write_text(json.dumps(report, indent=2))
    if errors or extraction_errors:
        raise RuntimeError(f'Input preservation failed: {report}')
    addon_dir = ROOT / 'work/tools'
    with zipfile.ZipFile(ROOT / 'Aventurine-3.1.5.zip') as archive:
        for info in archive.infolist():
            dest = (addon_dir / info.filename).resolve()
            if not dest.is_relative_to(addon_dir.resolve()):
                raise ValueError(f'Unsafe addon member: {info.filename}')
            if not info.is_dir() and not dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(archive.read(info))
    preset = dict(addon='work/tools/Aventurine', blender='C:/Program Files/Blender Foundation/Blender 5.2/blender.exe',
                  bone_orient='NATIVE', import_scale=0.01, model_scale=1.0,
                  disable_scaling=False, disable_transforms=False, use_visual_pose=False,
                  apply_object_transform=True, clean_names=False,
                  notes='Identity armature object; no animation export or game-record edits. Always pass the SKN palette to SKL export.')
    (ROOT / 'work/config/export_preset.json').write_text(json.dumps(preset, indent=2))
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
