"""Local word-timed transcription of the supplied recording for reproducible cuts."""
from pathlib import Path
import sys,json,hashlib,os
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'work/cache/voice_python'))
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING']='1'
from faster_whisper import WhisperModel

def main():
    out=ROOT/'work/audio/clash_vo_transcript.json';assert not out.exists()
    source=ROOT/'Clash voice line.wav'
    model=WhisperModel('small.en',device='cpu',compute_type='int8',cpu_threads=8,download_root=str(ROOT/'work/cache/whisper_models'))
    segments,info=model.transcribe(str(source),language='en',word_timestamps=True,condition_on_previous_text=False,beam_size=5,vad_filter=True)
    result={'source':source.name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'model':'small.en','duration':info.duration,'segments':[]}
    out.parent.mkdir(parents=True,exist_ok=True)
    for s in segments:
        result['segments'].append({'start':s.start,'end':s.end,'text':s.text,'words':[{'start':w.start,'end':w.end,'word':w.word,'probability':w.probability} for w in s.words]})
        print(f'{s.start:.2f}-{s.end:.2f} {s.text}',flush=True)
    out.write_text(json.dumps(result,indent=2));print('Saved',out,flush=True)
if __name__=='__main__':main()
