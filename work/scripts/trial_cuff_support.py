"""Create an isolated topology trial, never overwrite an existing scene."""
from pathlib import Path
import bpy,json,hashlib,sys,argparse
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'work/scripts'))
from cuff_support_topology import apply_support
p=argparse.ArgumentParser();p.add_argument('--control',action='store_true');p.add_argument('--label');p.add_argument('--profile',choices=['smooth','linear'],default='smooth');args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
label=args.label or ('cuff_support_control' if args.control else 'cuff_support_trial')
assert label.replace('_','').isalnum()
out=ROOT/'work/scenes'/f'clash_braum_{label}.blend';assert not out.exists()
source=ROOT/'work/scenes/clash_braum_torso.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native'];regions=json.loads((ROOT/'validation/rig_regions.json').read_text())['objects']
print('ACTUAL INPUT',[(n,len(bpy.data.objects[n].data.vertices),[(a.name,a.domain,a.data_type) for a in bpy.data.objects[n].data.attributes]) for n in ['Object004','Object009']],flush=True)
mapping=apply_support(rig,regions,attach=not args.control,profile=args.profile)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
report={'status':'UNACCEPTED diagnostic topology trial','profile':args.profile,'control':args.control,'parent_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scene':out.name,'scene_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'objects':mapping}
(ROOT/'validation'/f'{label}.json').write_text(json.dumps(report,indent=2))
print({n:{k:v for k,v in m.items() if k in ['original_vertices','vertices','original_faces','faces']} for n,m in mapping.items()})
