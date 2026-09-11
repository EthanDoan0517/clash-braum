"""Continue saved draft with landmark hand fit and deliberately rigid equipment.

Writes a separate revision; input review scene and all native ANMs stay unchanged.
Physical digit IDs come from inspect_rig_regions.py, not nearest stock surfaces.
"""
from pathlib import Path
import sys, json, math, hashlib
import bpy
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
from collections import Counter

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'work/tools'),str(ROOT/'work/scripts')]
from native_export import assert_native_rig

SOURCE=ROOT/'work/scenes/clash_braum_animation_review.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False,use_scripts=False)
rig=bpy.data.objects['Braum_Native']
regions=json.loads((ROOT/'validation/rig_regions.json').read_text())
report={'input':str(SOURCE.relative_to(ROOT)), 'input_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'hands':[], 'rigid_components':[], 'cloth_smoothing':[], 'status':'Stage 3 refinement revision; deformation review required'}

def smooth(a,b,x):
    t=max(0.,min(1.,(x-a)/(b-a)))
    return t*t*(3-2*t)

def set_weights(obj,vi,weights):
    for g in list(obj.data.vertices[vi].groups):
        obj.vertex_groups[g.group].remove([vi])
    weights={k:v for k,v in weights.items() if v>1e-6}
    total=sum(weights.values())
    assert total>0 and len(weights)<=4
    for name,w in weights.items():
        (obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)).add([vi],w/total,'REPLACE')

def weights_of(obj,v):
    return {obj.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0}

def distance_to_segment(p,a,b):
    t=max(0.,min(1.,(p-a).dot(b-a)/(b-a).length_squared))
    return (p-(a+(b-a)*t)).length

digits=['Thumb','Index','Middle','Ring','Pinky']
skin=bpy.data.objects['Object009']
glove=bpy.data.objects['Object004']
for side,ids in [('L',[326,377,382,388,585]),('R',[0,51,57,60,65])]:
    sign=1 if side=='L' else -1
    shells={digit:next(c['indices'] for c in regions['objects']['Object009'] if c['id']==i) for digit,i in zip(digits,ids)}
    labels={i:digit for digit,indices in shells.items() for i in indices}
    centers={digit:sum((skin.data.vertices[i].co for i in indices),Vector())/len(indices) for digit,indices in shells.items()}
    wrist=rig.data.bones[side+'_Hand'].head_local.copy()
    # Reviewed cuff center in the draft, blended back to unchanged forearm.
    source_wrist=Vector((sign*.746,-.092,1.116))
    chains={digit:[rig.data.bones[f'{side}_{digit}{j}'].head_local.copy() for j in [1,2]] for digit in digits}
    targets={digit:b+(b-a)*.35 for digit,(a,b) in chains.items()}
    source=np.array([list(source_wrist)]+[list(centers[d]) for d in digits])
    target=np.array([list(wrist)]+[list(targets[d]) for d in digits])
    sc,tc=source.mean(axis=0),target.mean(axis=0)
    u,s,vt=np.linalg.svd((source-sc).T@(target-tc))
    rot=vt.T@u.T
    if np.linalg.det(rot)<0:
        vt[-1]*=-1;rot=vt.T@u.T
    scale=float(sum(s)/np.sum((source-sc)**2))
    rotation=Matrix(rot.tolist())
    translation=Vector(tc)-rotation@Vector(sc)*scale
    mapped=lambda p:rotation@p*scale+translation
    fit_errors={d:(mapped(centers[d])-targets[d]).length for d in digits}
    hand_axis=(sum(centers.values(),Vector())/5-source_wrist).normalized()
    changed=0
    for obj in [skin,glove]:
        for v in obj.data.vertices:
            p=v.co.copy()
            if sign*p.x<.62 or p.z>1.23:
                continue
            along=(p-source_wrist).dot(hand_axis)
            amount=smooth(-.075,.035,along)
            if amount==0:
                continue
            new=p.lerp(mapped(p),amount)
            v.co=new
            old=weights_of(obj,v)
            if obj==skin and v.index in labels:
                digit=labels[v.index]
            else:
                digit=min(digits,key=lambda d:distance_to_segment(new,chains[d][0],chains[d][1]+(chains[d][1]-chains[d][0])*.9))
            a,b=chains[digit]
            t=(new-a).dot(b-a)/(b-a).length_squared
            finger=smooth(-.40,.15,t)
            distal=smooth(.65,1.2,t)
            desired={side+'_Hand':1-finger,side+'_'+digit+'1':finger*(1-distal),side+'_'+digit+'2':finger*distal}
            mixed={n:w*(1-amount) for n,w in old.items()}
            for n,w in desired.items():mixed[n]=mixed.get(n,0)+amount*w
            keep=dict(sorted(mixed.items(),key=lambda p:-p[1])[:4])
            set_weights(obj,v.index,keep)
            changed+=1
    report['hands'].append({'side':side,'digit_shell_ids':dict(zip(digits,ids)),
        'source_wrist':list(source_wrist),'native_wrist':list(wrist),'uniform_scale':scale,
        'rotation':rot.tolist(),'translation':list(translation),'digit_center_fit_errors':fit_errors,
        'vertices_changed':changed,'method':'Orientation-preserving similarity fit; digit-specific two-joint weights; smooth cuff transition'})

# Compact equipment shells reviewed by their physical bounds, distinct from
# continuous cloth/straps. Keep attached small hardware on the same bone.
rigid={
    'Object004':{87:'R_Elbow',804:'L_Elbow'},
    'Object002':{1021:'Spine1',1218:'L_Clavicle',1235:'L_Clavicle',1540:'R_Clavicle',1557:'R_Clavicle'},
    'hjhjh_2':{0:'Root',192:'Root',208:'Root',295:'Root',348:'Root',407:'Root',431:'Root',449:'Root',
                688:'Spine2',739:'Spine2',794:'Spine2',797:'Spine2',803:'L_Hip'},
    'Object007':{0:'Spine3',24:'Spine3',49:'Spine3',113:'Spine3',116:'Spine3',122:'Spine3',
                 133:'Spine1',156:'Spine1',250:'Spine1',536:'Spine3',558:'Spine3',592:'Spine3',
                 603:'Spine3',606:'Spine3',613:'Spine3',783:'Spine3',
                 1428:'Root',1445:'Root',1453:'Root',1668:'Spine2',1672:'Spine2',1676:'Spine2',1680:'Spine2',
                 1996:'R_Hip',2022:'R_Hip',2623:'L_Hip',2798:'R_Clavicle',3328:'Root'},
    'Object001':{548:'L_Hip',1235:'R_Hip'},
    'Object006':{34:'L_Hip',45:'L_Hip',145:'L_Hip',268:'L_Hip',298:'L_Hip',
                 326:'R_Hip',334:'R_Hip',500:'R_Hip',534:'R_Hip',539:'R_Hip',603:'R_Hip',
                 754:'L_Hip',769:'L_Hip',813:'L_Hip',826:'L_Hip',1094:'L_Hip',
                 1190:'Spine3',1194:'Spine3',1239:'Spine3',1317:'R_Clavicle',1320:'R_Clavicle',
                 1388:'Root',1656:'Root',2607:'Root',2681:'Spine3',2693:'Spine3',
                 3329:'L_Clavicle',3337:'L_Clavicle'},
}
for name,assignments in rigid.items():
    obj=bpy.data.objects[name]
    for component,bone in assignments.items():
        shell=next(c for c in regions['objects'][name] if c['id']==component)
        for i in shell['indices']:set_weights(obj,i,{bone:1.})
        report['rigid_components'].append({'object':name,'component':component,'vertices':len(shell['indices']),'bone':bone})

# Small fasteners adjacent to an authored component must follow that component.
# Only short shells with strong, close geometric agreement inherit its weight.
for name in ['Object006','Object007']:
    obj=bpy.data.objects[name]
    assigned={c['component']:c['bone'] for c in report['rigid_components'] if c['object']==name}
    donors=[(i,assigned[c['id']]) for c in regions['objects'][name] if c['id'] in assigned for i in c['indices']]
    tree=KDTree(len(donors))
    for k,(i,bone) in enumerate(donors):tree.insert(obj.data.vertices[i].co,k)
    tree.balance()
    for shell in regions['objects'][name]:
        if shell['id'] in assigned or shell['vertices']>40 or max(b-a for a,b in shell['bounds'])>.11:
            continue
        hits=[tree.find(obj.data.vertices[i].co) for i in shell['indices']]
        bone,count=Counter(donors[k][1] for _,k,_ in hits).most_common(1)[0]
        if count/len(hits)<.8 or max(dist for _,_,dist in hits)>.04:
            continue
        for i in shell['indices']:set_weights(obj,i,{bone:1.})
        report['rigid_components'].append({'object':name,'component':shell['id'],'vertices':shell['vertices'],
            'bone':bone,'method':'Adjacent fastener: >=80% agree, <=0.04 distance, <=0.11 span',
            'max_attachment_distance':max(dist for _,_,dist in hits)})

# Remove nearest-surface discontinuities in selected continuous cloth shells.
# Welded-position adjacency is used only to share weights; geometry, UVs and
# hard-normal splits remain untouched. Hand digits/equipment are excluded.
smooth_shells={'Object002':[0], 'Object001':[0], 'hjhjh_4':[0],
               'Object004':[0,12,217,253], 'Object009':[652,810]}
for name,ids in smooth_shells.items():
    obj=bpy.data.objects[name]
    for cid in ids:
        indices=next(c['indices'] for c in regions['objects'][name] if c['id']==cid)
        index_set=set(indices);groups={};vertex_nodes={}
        for i in indices:
            # Use ORIGINAL coincident positions so cuff fitting cannot separate seams.
            original=regions.get('hand_geometry',{}).get(name,{}).get('points')
            co=original[i] if original else obj.data.vertices[i].co
            key=tuple(round(x,5) for x in co)
            groups.setdefault(key,[]).append(i);vertex_nodes[i]=key
        keys=list(groups);node_index={k:i for i,k in enumerate(keys)}
        neighbors=[set() for _ in keys]
        for edge in obj.data.edges:
            a,b=edge.vertices
            if a in index_set and b in index_set:
                a,b=node_index[vertex_nodes[a]],node_index[vertex_nodes[b]]
                if a!=b:neighbors[a].add(b);neighbors[b].add(a)
        weights=np.zeros((len(keys),len(obj.vertex_groups)))
        for k,node in node_index.items():
            for vi in groups[k]:
                for g in obj.data.vertices[vi].groups:weights[node,g.group]+=g.weight/len(groups[k])
        fixed=set()
        for k,node in node_index.items():
            p=Vector(k)
            if name=='hjhjh_4':
                if p.z>1.74:fixed.add(node)
                # A realistic neck must not borrow the native jaw/clavicle helper motion.
                for old,new in [('Jaw','Head'),('L_Clavicle','Spine3'),('R_Clavicle','Spine3')]:
                    a,b=obj.vertex_groups[old].index,obj.vertex_groups[new].index
                    weights[node,b]+=weights[node,a];weights[node,a]=0
            if name=='Object009' and abs(p.x)>.71:fixed.add(node)
        for _ in range(8):
            updated=weights.copy()
            for node,adj in enumerate(neighbors):
                if node not in fixed and adj:
                    updated[node]=.55*weights[node]+.45*weights[list(adj)].mean(axis=0)
            weights=updated
        for k,node in node_index.items():
            if node in fixed:continue
            keep=np.argsort(weights[node])[-4:]
            authored={obj.vertex_groups[int(i)].name:float(weights[node,i]) for i in keep if weights[node,i]>1e-6}
            for vi in groups[k]:set_weights(obj,vi,authored)
        report['cloth_smoothing'].append({'object':name,'component':cid,'vertices':len(indices),
            'iterations':8,'neighbor_blend':.45,'fixed_nodes':len(fixed),'position_weld_tolerance':.00001})

for obj in bpy.context.scene.objects:
    if 'source_obj_group' in obj:
        obj['rig_status']='Refinement 2: authored hands/equipment and smoothed cloth/neck weights; see rig_refinement.json'
        obj.data.update()
assert_native_rig(rig)
rig.animation_data.action=bpy.data.actions['braum_idle_01_loop']
rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.context.scene.frame_set(17)
bpy.context.scene['stage']=report['status']
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'work/scenes/clash_braum_rig_refined.blend'))
(ROOT/'validation/rig_refinement.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'hands':report['hands'],'rigid_components':len(report['rigid_components'])},indent=2))
