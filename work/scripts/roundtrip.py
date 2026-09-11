"""Run with Blender --background --factory-startup --python-exit-code 1 --python."""
from pathlib import Path
import json
import sys
import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'work/tools'))
sys.path.insert(0, str(ROOT / 'work/scripts'))
from Aventurine.io import import_skl, import_skn, export_skn, export_skl
from asset_formats import read_skl, read_skn, validate_pair, compare_roundtrip
from native_export import import_baseline, export_pair

bpy.ops.wm.read_factory_settings(use_empty=True)
rig, mesh = import_baseline()
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'work/scenes/braum_native_baseline.blend'))
out = ROOT / 'build/roundtrip/braum_base'
_, count, palette = export_pair(out, [mesh], rig)
src_mesh = read_skn(ROOT / 'Braum.wad/fbf88fcfc8ec8dc4.skn')
src_skl = read_skl(ROOT / 'Braum.wad/9b8248658ce51711.skl')
new_mesh, new_skl = read_skn(out.with_suffix('.skn')), read_skl(out.with_suffix('.skl'))
report = dict(blender=bpy.app.version_string, source=validate_pair(src_mesh, src_skl),
              result=validate_pair(new_mesh, new_skl), comparison=compare_roundtrip(src_mesh, src_skl, new_mesh, new_skl),
              runtime_test='Pending pristine patch-matched main WAD and mod manager')
assert report['comparison']['max_corner_errors']['normal'] < 0.001
(ROOT / 'validation/vanilla_roundtrip.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
