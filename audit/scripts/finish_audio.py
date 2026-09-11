import json,struct,collections
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'audit/evidence'
banks=json.loads((O/'audio_banks.json').read_text());events=json.loads((O/'audio_event_map.json').read_text())
def wave(b):
    d={'magic':b[:4].decode(errors='replace'),'bytes':len(b)}
    if b[:4]!=b'RIFF':return d
    at=12
    while at+8<=len(b):
        tag=b[at:at+4];n=struct.unpack_from('<I',b,at+4)[0];raw=b[at+8:at+8+n]
        if tag==b'fmt ' and len(raw)>=16:
            code,ch,rate,avg,align,bits=struct.unpack_from('<HHIIHH',raw)
            d.update(format_tag=hex(code),channels=ch,sample_rate=rate,bits=bits,fmt_size=n)
        at+=8+n+(n%2)
    return d
result={'sfx_media':[],'vo_media':[]}
p=R/'Braum.wad/668ac17b89a8d8ea.bnk';b=p.read_bytes();at=0;data=None;ids=[]
while at+8<=len(b):
    tag=b[at:at+4];n=struct.unpack_from('<I',b,at+4)[0];raw=b[at+8:at+8+n]
    if tag==b'DATA':data=raw
    if tag==b'DIDX':ids=[struct.unpack_from('<III',raw,i) for i in range(0,n,12)]
    at+=8+n
for hid,offset,length in ids:result['sfx_media'].append({'media_id':hid,'offset':offset,**wave(data[offset:offset+length])})
p=R/'audit/scratch/voice_original/4826a53ff12ced20.wpk';b=p.read_bytes();ver,count=struct.unpack_from('<II',b,4);result['wpk_header']={'magic':b[:4].decode(),'version':ver,'entry_slots':count}
for offset in struct.unpack_from('<'+'I'*count,b,12):
    if not offset:continue
    start,length,nchars=struct.unpack_from('<III',b,offset);name=b[offset+12:offset+12+nchars*2].decode('utf-16-le').rstrip('\0')
    result['vo_media'].append({'name':name,'media_id':int(Path(name).stem),'offset':start,**wave(b[start:start+length])})
for name,bank in [('sfx','6a0cd1a55c7df583.bnk'),('vo','17802985c2cae524.bnk')]:
    relevant=[x for x in events if x['bank']==bank];available={x['media_id'] for x in result[name+'_media']};used={m for x in relevant for m in x['media_ids']}
    result[name+'_coverage']={'available':len(available),'referenced':len(used),'missing_media_ids':sorted(used-available),'unreferenced_media_ids':sorted(available-used),'shared_media':{str(m):[x['event_name'] for x in relevant if m in x['media_ids']] for m in used if sum(m in x['media_ids'] for x in relevant)>1}}
result['unresolved_targets']=[{'event':x['event_name'],'id':h,'found_in_supplied_banks':[a['path'] for a in banks if any(z['id']==h for z in a['hirc'])]} for x in events for h in x['unresolved_graph_nodes']]
(O/'audio_media_audit.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if not k.endswith('_media')},indent=2)[:5000])
for name in ['sfx','vo']:print(name,collections.Counter((x.get('format_tag'),x.get('sample_rate'),x.get('channels')) for x in result[name+'_media']))
