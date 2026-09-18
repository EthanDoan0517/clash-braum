"""Full English media replacement plus +6dB Q/R, preserving approved E audio."""
from pathlib import Path
import collections,hashlib,json,struct,subprocess,sys,zipfile,xml.etree.ElementTree as ET
from diagnose_sfx_silence import wem_info,fnv
from build_sfx_v3_volume import objects,props,EVENTPATH
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/clash_vo_v1'
VOPATH='assets/sounds/wwise2016/vo/en_us/characters/braum/skins/base/braum_base_vo_audio.wpk'
sha=lambda b:hashlib.sha256(b).hexdigest()

def wpk_entries(b):
    assert b[:4]==b'r3d2'
    version,count=struct.unpack_from('<II',b,4);assert version==1
    entries=[]
    for table in struct.unpack_from('<'+'I'*count,b,12):
        assert table
        start,size,n=struct.unpack_from('<III',b,table)
        name=b[table+12:table+12+n*2].decode('utf-16-le').rstrip('\0')
        assert start+size<=len(b)
        entries.append(dict(table=table,start=start,size=size,name=name,id=int(Path(name).stem)))
    return entries

def repack(original,replacements):
    entries=wpk_entries(original);first=min(e['start'] for e in entries)
    out=bytearray(original[:first])
    for e in sorted(entries,key=lambda e:e['start']):
        out+=bytes((-len(out))%8)
        media=replacements.get(e['id'],original[e['start']:e['start']+e['size']])
        struct.pack_into('<II',out,e['table'],len(out),len(media));out+=media
    return bytes(out)

def pool_for(event):
    if 'BraumBasicAttack' in event or 'BraumCritAttack' in event:return 'attack_grunt'
    if 'BraumEDummyVO' in event:return 'e'
    if 'BraumQ_cast' in event:return 'q'
    if 'BraumE_cast' in event:return 'e'
    if 'BraumRWrapper_cast' in event:return 'r'
    if 'BraumWDummySpell_cast' in event:return 'w'
    if 'BuyItem2DWard' in event:return 'ward'
    if 'Move2DStandard' in event:return 'move'
    if 'Move2DFirst' in event:return 'first_move'
    if 'Attack2DGeneral' in event:return 'attack_command'
    if 'Death3D' in event:return 'death'
    if 'FirstEncounter' in event:return 'encounter'
    if 'BuyItem' in event or 'UseItem' in event:return 'item'
    for key,pool in [('Joke','joke'),('Laugh','laugh'),('Taunt','taunt'),('Dance','dance'),('Recall','recall'),('Respawn','respawn')]:
        if key in event:return pool
    raise ValueError(event)

def main():
    assert not OUT.exists()
    base_report=json.loads((ROOT/'validation/directional_sfx_v3_build.json').read_text())
    parent=ROOT/base_report['archive'];assert sha(parent.read_bytes())==base_report['sha256']
    clips=json.loads((ROOT/'validation/clash_vo_clips_v1.json').read_text())
    choices=json.loads((ROOT/'work/audio/clash_vo_choices.json').read_text())
    assert clips['choices_sha256']==sha((ROOT/'work/audio/clash_vo_choices.json').read_bytes())
    assert clips['source_sha256']==sha((ROOT/clips['source']).read_bytes())
    events=[e for e in json.loads((ROOT/'audit/evidence/audio_event_map.json').read_text()) if e['bank']=='17802985c2cae524.bnk']
    assigned={};pool_indexes=collections.Counter()
    for event in events:
        for mid in event['media_ids']:
            pool=pool_for(event['event_name'])
            if mid not in assigned:
                names=choices['pools'][pool];name=names[pool_indexes[pool]%len(names)];pool_indexes[pool]+=1
                assigned[mid]={'clip':name,'pool':pool,'events':[]}
            assert assigned[mid]['pool']==pool
            assigned[mid]['events'].append(event['event_name'])
    native=(ROOT/'audit/scratch/voice_original/4826a53ff12ced20.wpk').read_bytes()
    entries=wpk_entries(native);assert len(entries)==115 and {e['id'] for e in entries}==set(assigned)
    assert repack(native,{})==native,'Native no-op WPK must be byte-exact.'
    replacements={};used=set();uid_setup={}
    for mid,assignment in assigned.items():
        name=assignment['clip'];b=(ROOT/f'build/clash_vo_clips_v1/wem/{name}.wem').read_bytes()
        assert sha(b)==clips['clips'][name]['wem_sha256']
        p=wem_info(b);assert p['uid']==fnv(p['setup'])
        assert p['uid'] not in uid_setup or uid_setup[p['uid']]==p['setup_sha256'];uid_setup[p['uid']]=p['setup_sha256']
        replacements[mid]=b;used.add(name)
        assignment.update(phrase=clips['clips'][name]['phrase'],source_start=clips['clips'][name]['start'],source_end=clips['clips'][name]['end'],seconds=clips['clips'][name]['seconds'],wem_sha256=sha(b))
    wpk=repack(native,replacements);new_entries=wpk_entries(wpk)
    assert [e['name'] for e in new_entries]==[e['name'] for e in entries]
    for entry in new_entries:assert wpk[entry['start']:entry['start']+entry['size']]==replacements[entry['id']]
    # No embedded/preloaded VO samples are being left behind in an audio bank.
    roots=ET.fromstring('<banks>'+(ROOT/'audit/evidence/base_audio_wwiser.xml').read_text()+'</banks>')
    vo_xml=next(r for r in roots if r.get('filename')=='17802985c2cae524.bnk')
    voiced_objects=0
    for obj in objects(vo_xml).values():
        media=obj.find('.//field[@name="sourceID"]')
        if media is None:continue
        assert int(media.get('value')) in replacements
        assert obj.find('.//field[@name="StreamType"]').get('value')=='2'
        assert obj.find('.//field[@name="bPrefetch"]').get('value')=='0'
        voiced_objects+=1
    assert voiced_objects==115
    OUT.mkdir();package=OUT/'package'
    with zipfile.ZipFile(parent) as z:
        assert z.testzip() is None;z.extractall(package);previous={n:z.read(n) for n in z.namelist()}
    eventfile=package/'WAD/Braum.wad.client'/EVENTPATH
    original_events=eventfile.read_bytes()
    volume_report=json.loads((ROOT/'validation/sfx_v3_volume_build.json').read_text())
    assert sha(original_events)==volume_report['event_bank_sha256']
    sfx_report=json.loads((ROOT/'validation/sfx_v2_refinement_build.json').read_text())
    louder_ids={e['id'] for e in sfx_report['changed_media'] if 'BraumQMissile' in e['event'] or 'BraumRWrapper_OnCast' in e['event']};assert len(louder_ids)==7
    xml=ET.parse(ROOT/'build/sfx_v3_volume/events.xml').getroot();new_events=bytearray(original_events);volume_changes=[]
    for oid,obj in objects(xml).items():
        media=obj.find('.//field[@name="sourceID"]')
        if media is None or int(media.get('value')) not in louder_ids:continue
        v=next(p for p in props(obj).findall('./list/object') if p.find('./field[@name="pID"]').get('value')=='0').find('./field[@name="pValue"]')
        offset=int(v.get('offset'));assert struct.unpack_from('<f',original_events,offset)[0]==10
        struct.pack_into('<f',new_events,offset,16)
        volume_changes.append({'media_id':int(media.get('value')),'sound_id':oid,'offset':offset,'old_db':10,'new_db':16})
    assert len(volume_changes)==7
    restore=bytearray(new_events)
    for c in volume_changes:struct.pack_into('<f',restore,c['offset'],10)
    assert bytes(restore)==original_events;eventfile.write_bytes(new_events)
    vofile=package/'WAD/Braum.en_US.wad.client'/VOPATH;assert not vofile.exists();vofile.parent.mkdir(parents=True);vofile.write_bytes(wpk)
    info=package/'META/info.json';meta=json.loads(info.read_text());meta.update(Name='Clash Braum - English VO v1 + Louder QR',Version='0.1.0-clash-vo-v1',Description='115 English voice media replaced with authentic supplied Clash lines. Q/R +6dB over SFX v3; approved E sound unchanged. Directional visuals preserved. Manual voice/context/volume test required.')
    info.write_text(json.dumps(meta,indent=2))
    for n,b in previous.items():
        if n not in ['META/info.json','WAD/Braum.wad.client/'+EVENTPATH]:assert (package/n).read_bytes()==b
    archive=OUT/'Braum_Clash_English_VO_v1.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(package.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(package).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n in z.namelist():assert z.read(n)==(package/n).read_bytes()
    # Persistent exact clip/event mapping; reproduction does not depend on chat.
    mapping={'source':clips['source'],'source_sha256':clips['source_sha256'],'media':assigned,'notes':['Ward lines use native BuyItem2DWard, not ward placement.','Laugh emote uses sarcastic spoken lines; death uses short No/Bloody hell/Shit exclamations; no synthetic screams.','Shared attack media maps consistently across all eight native attack-cast events.','Native first-move pool is retained; no invented long-move or kill triggers.']}
    (ROOT/'work/audio/clash_vo_mapping_v1.json').write_text(json.dumps(mapping,indent=2))
    summary=['# Clash English voice mapping v1','', 'Native English event triggers retained. Ward lines fire on purchase. Laugh uses spoken sarcasm; death uses short recorded exclamations.','', '| Event | Clash lines |','|---|---|']
    for e in events:
        phrases=list(dict.fromkeys(assigned[mid]['phrase'] for mid in e['media_ids']))
        summary.append('| '+e['event_name'].removeprefix('Play_vo_Braum_')+' | '+' / '.join(phrases or ['Native stop/end event; no media'])+' |')
    (ROOT/'work/audio/CLASH_VO_MAPPING_V1.md').write_text('\n'.join(summary)+'\n')
    result={'status':'PASS build; targeted package validation pending','archive':archive.relative_to(ROOT).as_posix(),'sha256':sha(archive.read_bytes()),'parent':base_report['archive'],'parent_sha256':base_report['sha256'],'vo_path':VOPATH,'wpk_sha256':sha(wpk),'native_wpk_sha256':sha(native),'media_count':115,'unique_clips_used':len(used),'event_count':len(events),'source':clips['source'],'source_sha256':clips['source_sha256'],'vo_events_unchanged':True,'all_vo_streamed_without_prefetch':True,'wpk_noop_exact':True,'sfx_volume_changes':volume_changes,'sfx_event_bank_sha256':sha(new_events),'approved_e_audio_and_fields_exact':True,'reused':'All preexisting media and visuals exact; only seven SFX Volume values changed. 69 prepared clips independently decoded with corrected setup hashes; package uses a subset in 115 slots. VO event graph/timing/spatial/random/stop behavior unchanged.','runtime':'English VO context/cut boundaries/volume/repetition/death/emotes and Q/R loudness require user gameplay. E volume remains accepted.'}
    (ROOT/'validation/clash_vo_v1_build.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:result[k] for k in ['archive','sha256','media_count','unique_clips_used','event_count']},indent=2))
if __name__=='__main__':main()
