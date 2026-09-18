"""Matched close-up shield and directional-E grip images, no saved changes."""
from pathlib import Path
import sys,runpy,argparse
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--trial',default='clash_braum_shield_collapse_trial.blend');parser.add_argument('--label',default='trial');parser.add_argument('--skip-parent',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
variants=[] if args.skip_parent else [('parent','clash_braum_gameplay_accepted.blend')]
variants.append((args.label,args.trial))
for variant,scene in variants:
    for view,direction in [('front','3,-7,3'),('back','-3,7,3')]:
        sys.argv=['render_rig_refinement.py','--','--scene',scene,'--label',f'shield_review_{variant}_{view}','--direction='+direction,
                  '--isolate-grip','--resolution','720',
                  '--case','braum_spell3_run0:14:L_Hand','--case','braum_spell3_idle180:29:R_Hand','--case','braum_spell4:15:L_Hand']
        runpy.run_path(str(ROOT/'work/scripts/render_rig_refinement.py'),run_name='__main__')
        sys.argv=['render_rig_refinement.py','--','--scene',scene,'--label',f'shield_surface_{variant}_{view}','--direction='+direction,
                  '--resolution','720','--case','braum_idle_01_loop:17:body','--scale','1.6']
        for name in ('13.001','14.001','15.001','16','21.001','22.001','23.001'):sys.argv+=['--only-object','CCE_mesh_'+name]
        runpy.run_path(str(ROOT/'work/scripts/render_rig_refinement.py'),run_name='__main__')
