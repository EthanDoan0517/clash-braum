import xml.etree.ElementTree as E,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'audit/evidence'
roots=E.fromstring('<banks>'+(O/'base_audio_wwiser.xml').read_text()+'</banks>')
for r in roots:
    print('BANK',r.attrib)
    seen=set()
    for o in r.findall('.//list[@name="listLoadedItem"]/object'):
        if o.get('name') in ['CAkEvent','CAkActionPlay','CAkActionStop','CAkSwitchCntr','CAkLayerCntr'] and o.get('name') not in seen:
            seen.add(o.get('name'));print(E.tostring(o,encoding='unicode')[:4500])
