import xml.etree.ElementTree as E,json,collections,struct
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'audit/evidence'
roots=E.fromstring('<banks>'+(O/'base_audio_wwiser.xml').read_text()+'</banks>')
skin=json.loads((O/'bins/eb9d53354a504663.json').read_text())['Characters/Braum/Skins/Skin0']
names=[n for b in skin['SkinAudioProperties']['BankUnits'] for n in b['Events']]
def fnv(s):
    h=2166136261
    for b in s.lower().encode():h=((h*16777619)^b)&0xffffffff
    return h
namemap={fnv(s):s for s in names};output=[]
for root in roots:
    objects=root.findall('.//list[@name="listLoadedItem"]/object');nodes={}
    for obj in objects:
        hid=int(obj.find('./field[@name="ulID"]').get('value'));typ=obj.get('name')
        fields=collections.defaultdict(list)
        for f in obj.findall('.//field'):
            if f.get('type') in ['sid','tid','u32','u16','u8']:fields[f.get('name')].append(int(f.get('value')))
        nodes[hid]={'type':typ,'id':hid,'actions':fields['ulActionID'],'targets':fields['idExt'],'children':fields['ulChildID'],'media':fields['sourceID'],'plugins':fields['ulPluginID']}
    def walk(h,seen):
        if h in seen:return set(),set()
        seen.add(h);n=nodes.get(h)
        if not n:return set(),{h}
        media=set(n['media']) if n['type']=='CAkSound' else set();missing=set()
        targets=n['actions'] if n['type']=='CAkEvent' else n['targets'] if n['type']=='CAkActionPlay' else n['children']
        for x in targets:
            m,z=walk(x,seen);media|=m;missing|=z
        return media,missing
    for h,n in nodes.items():
        if n['type']!='CAkEvent':continue
        visited=set();media,missing=walk(h,visited)
        output.append({'bank':root.get('filename'),'event_id':h,'event_name':namemap.get(h),'action_ids':n['actions'],'actions':[nodes.get(a) for a in n['actions']],'media_ids':sorted(media),'unresolved_graph_nodes':sorted(missing),'reachable_nodes':sorted(visited)})
(O/'audio_event_map.json').write_text(json.dumps(output,indent=2),encoding='utf8')
print('EVENTS',len(output),'named',sum(bool(x['event_name']) for x in output),'unresolved',sum(bool(x['unresolved_graph_nodes']) for x in output))
print('TARGETS',json.dumps([x for x in output if x['event_name'] in ['Play_sfx_Braum_BraumQ_OnCast','Play_sfx_Braum_BraumQMissile_hit','Play_sfx_Braum_BraumEShieldBuff_OnBuffActivate','Play_sfx_Braum_BraumEShieldBuff_block_large','Play_sfx_Braum_BraumRWrapper_OnCast','Play_sfx_Braum_BraumBasicAttackPassiveOverride_hit']],indent=2))
