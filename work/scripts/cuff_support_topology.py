"""Local conforming forearm subdivision with explicit source-face provenance."""
import bpy
from mathutils import Vector

def smooth(a,b,t):
    u=max(0,min(1,(t-a)/(b-a)));return u*u*(3-2*u)

def apply_support(rig,regions,end=.85,attach=True,profile='smooth'):
    result={}
    for name,components in [('Object009',[('L',810),('R',652)]),('Object004',[('L',2539),('R',865)])]:
        obj=bpy.data.objects[name];old=obj.data
        names=[g.name for g in obj.vertex_groups]
        points=[v.co.copy() for v in old.vertices]
        weights=[{names[g.group]:g.weight for g in v.groups if g.weight>0} for v in old.vertices]
        ancestry=[{i:1.} for i in range(len(points))]
        side_by_vertex={i:side for side,cid in components for i in next(c['indices'] for c in regions[name] if c['id']==cid)}
        axes={side:(rig.data.bones[side+'_Elbow'].head_local,rig.data.bones[side+'_Hand'].head_local-rig.data.bones[side+'_Elbow'].head_local) for side,_ in components}
        def axial(i):
            side=side_by_vertex.get(i)
            if side is None:return None
            elbow,axis=axes[side];return (points[i]-elbow).dot(axis)/axis.length_squared
        # Each corner retains barycentric coordinates in its original triangle.
        faces=[(tuple(f.vertices),f.index,[Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))]) for f in old.polygons]
        assert all(len(f.vertices)==3 for f in old.polygons)
        if name=='Object009':
            for iteration in range(3):
                split={}
                for face,source,bary in faces:
                    for a,b in zip(face,face[1:]+face[:1]):
                        ta,tb=axial(a),axial(b)
                        if ta is not None and tb is not None and min(ta,tb)>.4 and max(ta,tb)<1.03 and (points[a]-points[b]).length>.035:
                            split[tuple(sorted((a,b)))]=None
                if not split:break
                for (a,b) in split:
                    i=len(points);split[(a,b)]=i;points.append((points[a]+points[b])*.5)
                    ancestry.append({v:(ancestry[a].get(v,0)+ancestry[b].get(v,0))*.5 for v in set(ancestry[a])|set(ancestry[b])})
                    weights.append({n:(weights[a].get(n,0)+weights[b].get(n,0))*.5 for n in set(weights[a])|set(weights[b])})
                    side_by_vertex[i]=side_by_vertex[a]
                rebuilt=[]
                for face,source,bary in faces:
                    boundary=[]
                    for k,(a,b) in enumerate(zip(face,face[1:]+face[:1])):
                        boundary.append((a,bary[k]))
                        mid=split.get(tuple(sorted((a,b))))
                        if mid is not None:boundary.append((mid,(bary[k]+bary[(k+1)%3])*.5))
                    if len(boundary)==3:rebuilt.append((face,source,bary));continue
                    # A center fan handles all split-edge combinations without
                    # T junctions or choosing degenerate collinear fan triangles.
                    center=len(points);points.append(sum((points[i] for i in face),Vector())/3)
                    ancestry.append({v:sum(ancestry[i].get(v,0) for i in face)/3 for v in set().union(*(ancestry[i] for i in face))})
                    weights.append({n:sum(weights[i].get(n,0) for i in face)/3 for n in set().union(*(weights[i] for i in face))})
                    if all(i in side_by_vertex for i in face):side_by_vertex[center]=side_by_vertex[face[0]]
                    bc=sum(bary,Vector())/3
                    for (a,ba),(b,bb) in zip(boundary,boundary[1:]+boundary[:1]):rebuilt.append(((a,b,center),source,[ba,bb,bc]))
                faces=rebuilt
        changed=[]
        if attach:
            for i,w in enumerate(weights):
                t=axial(i)
                if t is None or t<=.45 or (name=='Object004' and t>=1.02):continue
                side=side_by_vertex[i]
                desired=max(0,min(1,(t-.45)/(end-.45))) if profile=='linear' else smooth(.45,end,t)
                proximal=w.get(side+'_Elbow',0)+w.get(side+'_Hand_Twist',0)
                delta=min(proximal,max(0,desired-w.get(side+'_Hand',0)))*smooth(.45,.65,t)
                if delta<=1e-8:continue
                for n in [side+'_Elbow',side+'_Hand_Twist']:
                    if n in w:w[n]*=(proximal-delta)/proximal
                w[side+'_Hand']=w.get(side+'_Hand',0)+delta;changed.append(i)
        if name=='Object004':
            for i in changed:
                for g in list(old.vertices[i].groups):obj.vertex_groups[g.group].remove([i])
                for n,w in weights[i].items():
                    if w>0:obj.vertex_groups[n].add([i],w,'REPLACE')
        else:
            new=bpy.data.meshes.new(old.name+'_cuff_support');new.from_pydata(points,[],[f[0] for f in faces])
            for material in old.materials:new.materials.append(material)
            sharp={tuple(sorted(e.vertices)):e.use_edge_sharp for e in old.edges}
            for edge in new.edges:
                a,b=edge.vertices
                sources=set(ancestry[a])|set(ancestry[b])
                edge.use_edge_sharp=len(sources)==2 and sharp.get(tuple(sorted(sources)),False)
            normals=[]
            for f,(_,source,bary) in zip(new.polygons,faces):
                origin=old.polygons[source];f.material_index=origin.material_index;f.use_smooth=origin.use_smooth
                original_normals=[old.corner_normals[l].vector.copy() for l in origin.loop_indices]
                normals.extend(tuple(sum((n*v for n,v in zip(original_normals,b)),Vector()).normalized()) for b in bary)
            for layer in old.uv_layers:
                target=new.uv_layers.new(name=layer.name)
                for f,(_,source,bary) in zip(new.polygons,faces):
                    original_uv=[layer.data[l].uv.copy() for l in old.polygons[source].loop_indices]
                    for l,b in zip(f.loop_indices,bary):target.data[l].uv=sum((uv*v for uv,v in zip(original_uv,b)),Vector((0,0)))
            new.normals_split_custom_set(normals)
            obj.data=new
            assert len(obj.vertex_groups)==0
            for n in names:obj.vertex_groups.new(name=n)
            for i,w in enumerate(weights):
                if i<len(old.vertices) and i not in changed:
                    for n,value in w.items():obj.vertex_groups[n].add([i],value,'REPLACE')
                    continue
                w={n:v for n,v in w.items() if v>1e-7};total=sum(w.values())
                assert len(w)<=4,(i,w)
                for n,value in w.items():obj.vertex_groups[n].add([i],value/total,'REPLACE')
        obj.data.update()
        affected={p.index for p in old.polygons if any(i in changed for i in p.vertices)}
        counts={}
        for _,source,_ in faces:counts[source]=counts.get(source,0)+1
        affected.update(i for i,c in counts.items() if c>1)
        result[name]={'original_vertices':len(old.vertices),'original_faces':len(old.polygons),'vertices':len(obj.data.vertices),'faces':len(faces),
          'changed_original_vertices':[i for i in changed if i<len(old.vertices)],'affected_source_faces':sorted(affected),
          'face_source':[f[1] for f in faces],'corner_barycentric':[[list(b) for b in f[2]] for f in faces],
          'vertex_source':[{str(k):v for k,v in a.items()} for a in ancestry]}
    return result
