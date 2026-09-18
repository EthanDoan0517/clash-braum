"""Cut selected authentic lines using local word alignment and encode corrected WEMs."""
from pathlib import Path
import json,re,hashlib,struct,subprocess,wave
import numpy as np
from inspect_sfx_source import readwav
from diagnose_sfx_silence import wem_info,fnv
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/clash_vo_clips_v1'
sha=lambda b:hashlib.sha256(b).hexdigest()
norm=lambda s:re.sub(r'[^a-z0-9]','',s.lower())
def main():
    assert not OUT.exists()
    transcript=json.loads((ROOT/'work/audio/clash_vo_transcript.json').read_text())
    choices=json.loads((ROOT/'work/audio/clash_vo_choices.json').read_text())
    source=ROOT/transcript['source'];assert sha(source.read_bytes())==transcript['sha256']
    words=[w for s in transcript['segments'] for w in s['words'] if norm(w['word'])]
    tokens=[norm(w['word']) for w in words];matches={};errors=[]
    for name,(phrase,near) in choices['clips'].items():
        needle=[norm(s) for s in phrase.split()]
        possible=[i for i in range(len(tokens)-len(needle)+1) if tokens[i:i+len(needle)]==needle and abs(words[i]['start']-near)<7]
        if not possible:errors.append((name,phrase,near));continue
        i=min(possible,key=lambda i:abs(words[i]['start']-near));j=i+len(needle)-1
        start=max(0,words[i]['start']-.07,words[i-1]['end']+.005 if i else 0)
        end=min(transcript['duration'],words[j]['end']+.1,words[j+1]['start']-.005 if j+1<len(words) else transcript['duration'])
        if end<=start or words[j]['end']-words[i]['start']<.1:errors.append((name,'unusable alignment'));continue
        matches[name]={'phrase':phrase,'start':start,'end':end,'word_start':words[i]['start'],'word_end':words[j]['end'],'mean_word_confidence':float(np.mean([w['probability'] for w in words[i:j+1]]))}
    assert not errors,errors
    OUT.mkdir();(OUT/'wav').mkdir();(OUT/'wem').mkdir();(OUT/'decoded').mkdir()
    audio,sr=readwav(source);audio=audio.mean(axis=1);logs=[]
    def run(args):
        r=subprocess.run(list(map(str,args)),capture_output=True,text=True);logs.append({'argv':list(map(str,args)),'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        (ROOT/'validation/clash_vo_clips_v1_logs.json').write_text(json.dumps(logs,indent=2));assert r.returncode==0,r.stderr
    for name,clip in matches.items():
        x=audio[round(clip['start']*sr):round(clip['end']*sr)].copy();x-=np.mean(x)
        # Speech-level match with peak headroom; no time stretching or synthesis.
        rms=np.sqrt(np.mean(x*x));assert rms>.0001,(name,'silent source')
        gain=min(.126/rms,.88/max(abs(x).max(),1e-8));x*=gain
        fade=min(round(.004*sr),len(x)//2);x[:fade]*=np.linspace(0,1,fade);x[-fade:]*=np.linspace(1,0,fade)
        wav=OUT/f'wav/{name}.wav'
        with wave.open(str(wav),'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(np.round(x*32767).astype('<i2').tobytes())
        wem=OUT/f'wem/{name}.wem'
        run([ROOT/'work/cache/audio_tools/wav2wem.exe','-q','4','-no-hash','-resample','44100','-o',wem,wav])
        b=bytearray(wem.read_bytes());p=wem_info(bytes(b));struct.pack_into('<I',b,80,fnv(p['setup']));wem.write_bytes(b)
        decoded=OUT/f'decoded/{name}.wav';run([ROOT/'work/cache/audio_tools/vgmstream-r2117/vgmstream-cli.exe','-i','-o',decoded,wem])
        y,rate=readwav(decoded);assert rate==44100 and abs(len(y)/rate-len(x)/sr)<.001 and abs(y).max()<.995
        q=wem_info(bytes(b));assert q['uid']==fnv(q['setup'])
        clip.update(seconds=len(y)/rate,source_gain_db=float(20*np.log10(gain)),decoded_rms=float(np.sqrt(np.mean(y*y))),decoded_peak=float(abs(y).max()),wem_sha256=sha(bytes(b)),wem_bytes=len(b))
    report={'status':'PASS','source':source.name,'source_sha256':transcript['sha256'],'choices_sha256':sha((ROOT/'work/audio/clash_vo_choices.json').read_bytes()),'clips':matches,'notes':'Automatic local word alignment cross-checked against user transcript; no claim of subjective listening. Boundary/timing quality needs user review. All clips decoded and corrected Vorbis cache hashes verified.'}
    (ROOT/'validation/clash_vo_clips_v1.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({n:{k:c[k] for k in ['start','end','mean_word_confidence']} for n,c in matches.items()},indent=2))
if __name__=='__main__':main()
