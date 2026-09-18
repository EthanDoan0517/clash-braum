"""Read supplied SFX and relevant native media; no installed game modifications."""
from pathlib import Path
import json, struct, subprocess, wave, hashlib, xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/sfx_source_review'
DEC = ROOT / 'work/cache/audio_tools/vgmstream-r2117/vgmstream-cli.exe'

def readwav(path):
    with wave.open(str(path)) as w:
        assert w.getsampwidth() == 2
        return np.frombuffer(w.readframes(w.getnframes()), '<i2').reshape(-1,w.getnchannels()).astype(float)/32768, w.getframerate()

def chunks(b, start=0, riff=False):
    at=start
    while at+8 <= len(b):
        tag=b[at:at+4]; n=struct.unpack_from('<I',b,at+4)[0]
        assert at+8+n <= len(b)
        yield tag,b[at+8:at+8+n]
        at+=8+n+(n%2 if riff else 0)
    assert at==len(b)

def main():
    OUT.mkdir(exist_ok=True)
    source=ROOT/'clash electricity sfx.wav'
    x,sr=readwav(source); mono=x.mean(axis=1)
    n=4096; hop=512
    spec=abs(np.fft.rfft(np.lib.stride_tricks.sliding_window_view(mono,n)[::hop]*np.hanning(n),axis=1))
    db=20*np.log10(np.maximum(spec,1e-8))
    scaled=np.clip((db+45)/75,0,1)
    rgb=np.stack([scaled**.7,scaled**1.5,scaled**3],axis=2)
    im=Image.fromarray((rgb.transpose(1,0,2)[::-1]*255).astype('uint8')).resize((1100,600))
    canvas=Image.new('RGB',(1200,680),'white'); canvas.paste(im,(70,30));d=ImageDraw.Draw(canvas)
    for sec in range(14): d.text((70+int(sec/(len(x)/sr)*1100),635),str(sec),fill='black')
    for hz in [0,4000,8000,12000,16000,20000,24000]:d.text((2,625-int(hz/24000*600)),str(hz),fill='black')
    canvas.save(OUT/'source_spectrogram.png')
    # Strong narrowband peaks, grouped by second, to distinguish beeps from crackle.
    summary=[]
    for sec in range(int(len(x)/sr)):
        p=np.mean(spec[(np.arange(len(spec))*hop/sr>=sec)&(np.arange(len(spec))*hop/sr<sec+1)]**2,axis=0)
        peaks=np.argsort(p)[-8:][::-1]
        summary.append({'second':sec,'rms':float(np.sqrt(np.mean(mono[sec*sr:(sec+1)*sr]**2))), 'peaks_hz':np.round(peaks*sr/n,1).tolist()})
    bank=(ROOT/'Braum.wad/668ac17b89a8d8ea.bnk').read_bytes(); c=dict(chunks(bank))
    events=json.loads((ROOT/'audit/evidence/audio_event_map.json').read_text())
    selected=[e for e in events if e['bank']=='6a0cd1a55c7df583.bnk' and any(s in (e['event_name'] or '') for s in ['BraumEShieldBuff','BraumQMissile_hit','BraumQMissile_OnMissileCast','BraumRWrapper_OnCast'])]
    ids={i for e in selected for i in e['media_ids']}; media=[]
    for mid,off,size in struct.iter_unpack('<III',c[b'DIDX']):
        if mid not in ids:continue
        wem=OUT/f'{mid}.wem'; wav=OUT/f'{mid}.wav'; wem.write_bytes(c[b'DATA'][off:off+size])
        result=subprocess.run([str(DEC),'-i','-o',str(wav),str(wem)],capture_output=True,text=True,check=True)
        a,rate=readwav(wav)
        media.append({'id':mid,'seconds':len(a)/rate,'rms':float(np.sqrt(np.mean(a*a))),'peak':float(abs(a).max()),'metadata':result.stdout,'events':[e['event_name'] for e in events if mid in e['media_ids']]})
    report={'source':source.name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'seconds':len(x)/sr,'sample_rate':sr,'channels':x.shape[1],'peak':float(abs(x).max()),'seconds_analysis':summary,'native_media':media}
    (ROOT/'validation/sfx_source_review.json').write_text(json.dumps(report,indent=2))
    roots=ET.fromstring('<banks>'+(ROOT/'audit/evidence/base_audio_wwiser.xml').read_text()+'</banks>')
    e_events=[e for e in events if 'EShieldBuff_OnBuffActivate' in (e['event_name'] or '') or 'Stop_sfx_Braum_BraumE' in (e['event_name'] or '')]
    nodes={n for e in e_events for n in e['reachable_nodes']}
    objects=[o for o in roots[0].findall('.//list[@name="listLoadedItem"]/object') if int(o.find('./field[@name="ulID"]').get('value')) in nodes]
    (OUT/'e_event_graph.xml').write_text('\n'.join(ET.tostring(o,encoding='unicode') for o in objects))
    print(json.dumps(e_events,indent=2))

if __name__=='__main__':main()
