from pathlib import Path
import json,collections,html,hashlib
R=Path(__file__).resolve().parents[2];O=R/'audit/evidence';D=R/'audit'
def load(n):return json.loads((O/(n+'.json')).read_text())
def table(headers,rows):
    esc=lambda x:str(x).replace('|','\\|').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(esc(x) for x in r)+' |' for r in rows])+'\n'
P=load('path_map');vfx=load('base_vfx_dependencies');bones=load('braum_skeleton');animations=load('animation_audit');clips=load('base_animation_clips')['mClipDataMap'];events=load('audio_event_map')
parts=['# BRAUM → CLASH — TECHNICAL APPENDICES\n','All paths and identifiers in these tables come from the supplied files or exact hash matches. Working-directory root: `'+str(R)+'`. An owner hash refers to the identically named file in `Braum.wad`. These are audit records, not replacement assets.\n','## 1. Core and shared BIN owners\n']
owners=sorted({x['owner_hash'] for x in vfx}|{'eb9d53354a504663','0b01eaec2c944f55','52d36b20890112f7','e63e7a9cbb51a42f','720e9ea8efb108f9'})
parts.append(table(['Supplied filename','Verified WAD-relative path','Base VFX definitions'],[(h+'.bin',P[h],sum(x['owner_hash']==h for x in vfx)) for h in owners]))
parts+=['## 2. Complete base skeleton\n','The SKN byte indices address the SKL influence palette; they are not joint indices. Blank palette entries indicate bones without an original weighted influence. Preserve these bones too.\n',table(['Joint index','Name','Parent index / name','Original palette index'],[(j['index'],j['name'],str(j['parent_index'])+' / '+str(j['parent']),bones['influence_palette'].index(j['index']) if j['index'] in bones['influence_palette'] else '') for j in bones['joints']])]
parts+=['## 3. Base animation files and graph bindings\n','59 files parse successfully; all contain a Shield track. The graph has 79 clip records and 1,806 blend-table records. Unresolved clip-key labels remain numeric hashes. Existing tracks absent from the supplied skeleton are recorded as stock-data facts, not evidence of a newly broken rig.\n']
bindings=collections.defaultdict(list)
for key,c in clips.items():
    p=c.get('mAnimationResourceData',{}).get('mAnimationFilePath')
    if p:bindings[p.lower()].append(key)
parts.append(table(['WAD-relative ANM path','Supplied file','Graph keys','FPS / duration seconds','Track count / unmatched'],[(a['path'],a['hash']+'.anm',', '.join(bindings[a['path'].lower()]),f"{a['fps']:g} / {a['duration']:.3f}",str(a['tracks'])+' / '+str(len(a['unknown_tracks']))) for a in animations]))
parts+=['### Graph events and non-atomic clips\n',table(['Clip key','Type','File / child structure / events'],[(key,c.get('__type'),json.dumps(c,ensure_ascii=False)) for key,c in clips.items() if c.get('mEventDataMap') or c.get('__type')!='AtomicClipData'])]
parts+=['## 4. Complete base VFX resolver and dependencies\n','72 non-null resolver bindings, 13 owner BINs, 135 unique explicit file dependencies. All 135 are supplied. The three null bindings are Braum_J_Ground_crack, Braum_R_cas, and Braum_Emote_Joke3_Sound. A logical reference is distinct from a WAD-relative file path. Full owner paths are in section 1.\n']
for v in vfx:
    parts += ['### '+v['resource_key']+'\n',f"Logical entry: `{v['entry']}`. Owner: `{v['owner_hash']}.bin`. Emitters: {len(v['emitters'])}.\n"]
    parts.append(table(['Field','Actual dependency path','Supplied filename'],[(d['field'],d['path'],d['local'] or 'MISSING') for d in v['dependencies']]))
    if v['sound_fields']:parts.append('Sound fields: '+json.dumps(v['sound_fields'])+'\n')
parts+=['## 5. Complete base audio event → action → media map\n','Wwise names were matched using lowercase FNV-1. Reachable media is the union of container variants, not a claim that every variant plays on each cast. All 114 referenced SFX media and 115 referenced VO media are present; every inspected payload is mono 44,100 Hz Wwise Vorbis (RIFF format tag 0xffff). 21 SFX media IDs and 7 VO media IDs are shared across events.\n','One unresolved target remains: Play_sfx_Braum_BraumRWrapper_OnHit, event 4008465767 → action 792732449 → object 222662794. The object is absent from every supplied BNK. It may be external or stale; do not invent its media or patch the event.\n']
parts.append(table(['Event name','Event ID','Events bank','Action IDs → types / target IDs','Reachable media IDs'],[(x['event_name'],x['event_id'],x['bank'],'; '.join(str(a['id'])+' '+a['type']+' → '+','.join(map(str,a['targets'])) for a in x['actions'] if a),', '.join(map(str,x['media_ids'])) or ('UNRESOLVED '+str(x['unresolved_graph_nodes']) if x['unresolved_graph_nodes'] else 'No media: control/stop event')) for x in sorted(events,key=lambda x:x['event_name'])]))
am=load('audio_media_audit')
for name in ['sfx','vo']:
    parts+=['### Shared '+name.upper()+' media — replacement affects every listed event\n',table(['Media ID','Events'],[(m,'; '.join(e)) for m,e in am[name+'_coverage']['shared_media'].items()])]
parts+=['## 6. Clash archive contents\n',table(['Original archive / member','Type','Bytes','Image dimensions / mode / compression','SHA-256'],[(x['archive']+' / '+x['member'],x['extension'],x['bytes'],str(x.get('size',''))+' '+str(x.get('mode',''))+' '+str(x.get('fourcc','')),x['sha256']) for x in load('clash_archive_inventory')])]
parts+=['## 7. Aventurine supplied ZIP members\n',table(['Archive member','Bytes','CRC32'],[(x['member'],x['bytes'],x['crc32']) for x in load('addon_archive_inventory')])]
parts+=['## 8. Unresolved original WAD paths\n','These 50 original entries remain identified by their exact hashes and types. They are not required by the 135 explicit base VFX dependency paths. That does not prove they are globally irrelevant; retain the originals and do not ship guessed replacements.\n',table(['Original filename','Bytes','Likely purpose'],[(x['file'],x['bytes'],x['purpose']) for x in load('project_inventory') if x['wad_hash'] and not x['resolved_game_path']])]
(D/'TECHNICAL_APPENDICES.md').write_text('\n\n'.join(parts),encoding='utf8')
rows=load('project_inventory');css='body{font:14px/1.5 system-ui;margin:28px;color:#171717}h1{font-size:28px}input{font:inherit;padding:10px;width:70%;margin:12px 0}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#eee;position:sticky;top:0}tr:nth-child(even){background:#fafafa}.n{white-space:nowrap}'
cols=[('file','File'),('extension','Type'),('original_path','Original path'),('resolved_game_path','Verified game path'),('purpose','Likely purpose'),('relevance','Relevance'),('referenced_by','BIN references'),('bytes','Bytes'),('sha256','SHA-256')]
out=['<!doctype html><meta charset="utf-8"><title>Braum Clash — original file inventory</title><style>'+css+'</style><h1>Braum → Clash — original file inventory</h1><p>1,849 original files. Search any filename, path, hash, purpose or reference. Archive members are listed separately in TECHNICAL_APPENDICES.md. No original source file is changed by this inventory.</p><input id="q" placeholder="Filter inventory" aria-label="Filter inventory"><p id="count">1849 files</p><table><thead><tr>'+''.join('<th>'+label+'</th>' for k,label in cols)+'</tr></thead><tbody>']
for r in rows:out.append('<tr>'+''.join('<td>'+html.escape(str(r.get(k,'')))+'</td>' for k,label in cols)+'</tr>')
out.append('</tbody></table><script>const q=document.querySelector("#q"),rows=[...document.querySelectorAll("tbody tr")];q.addEventListener("input",()=>{let n=0;for(const r of rows){r.hidden=!r.textContent.toLowerCase().includes(q.value.toLowerCase());if(!r.hidden)n++}document.querySelector("#count").textContent=n+" files"});</script>')
(D/'ORIGINAL_FILE_INVENTORY.html').write_text(''.join(out),encoding='utf8')
changed=[];missing=[]
for r in rows:
    p=Path(r['original_path'])
    if not p.is_file():missing.append(str(p))
    elif hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:changed.append(str(p))
(O/'preservation_check.json').write_text(json.dumps({'original_files_checked':len(rows),'changed':changed,'missing':missing},indent=2))
print('Appendix and inventory written. Original files checked:',len(rows),'changed',changed,'missing',missing)
