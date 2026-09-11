import sys,json,math
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,r'C:\Users\etqdo\Downloads\Aventurine-3.1.5')
from Aventurine.io.import_anm import read_anm
from Aventurine.utils.binary_utils import Hash
R=Path(__file__).resolve().parents[2];O=R/'audit/evidence';paths=json.loads((O/'path_map.json').read_text());sk=json.loads((O/'braum_skeleton.json').read_text())
names={int(j['hash'],16):j['name'] for j in sk['joints']}
rows=[]
for h,p in paths.items():
    if '/braum/skins/base/animations/' not in p:continue
    a=read_anm(str(R/'Braum.wad'/(h+'.anm')))
    unknown=[f'{t.joint_hash:08x}' for t in a.tracks if t.joint_hash not in names]
    row={'path':p,'hash':h,'fps':a.fps,'duration':a.duration,'frames':a.frame_count,'tracks':len(a.tracks),'unknown_tracks':unknown,'shield_track':any(names.get(t.joint_hash)=='Shield' for t in a.tracks)}
    for t in a.tracks:
        if names.get(t.joint_hash) in ['Shield','Origin','L_Hand','R_Hand']:
            ps=list(t.poses.values());tr=[list(p.translation) for p in ps if p.translation is not None];sc=[list(p.scale) for p in ps if p.scale is not None]
            row[names[t.joint_hash]]={'samples':len(ps),'translation_bounds':[[min(v[i] for v in tr),max(v[i] for v in tr)] for i in range(3)] if tr else None,'scale_bounds':[[min(v[i] for v in sc),max(v[i] for v in sc)] for i in range(3)] if sc else None}
    rows.append(row)
(O/'animation_audit.json').write_text(json.dumps(rows,indent=2),encoding='utf8');print('ANM',len(rows),'unknown',[(r['path'],r['unknown_tracks']) for r in rows if r['unknown_tracks']]);print('SHIELD TRACKS',sum(r['shield_track'] for r in rows))
