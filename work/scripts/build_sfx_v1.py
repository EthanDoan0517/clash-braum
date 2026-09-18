"""Clash recording -> native-sized Vorbis replacements in an isolated SFX candidate.

Requires inspect_sfx_source.py evidence and the pinned portable tools recorded below.
Replaces only media bytes, keeping DIDX offsets/sizes and every event-bank byte intact.
"""
from pathlib import Path
import hashlib, json, struct, subprocess, wave, zipfile
import numpy as np
from inspect_sfx_source import readwav, chunks

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/sfx_v1'
TOOLS=ROOT/'work/cache/audio_tools'
ENC=TOOLS/'wav2wem.exe'
DEC=TOOLS/'vgmstream-r2117/vgmstream-cli.exe'
BANKPATH='assets/sounds/wwise2016/sfx/characters/braum/skins/base/braum_base_sfx_audio.bnk'
sha=lambda b:hashlib.sha256(b).hexdigest()

def writewav(path,x,sr=44100):
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(np.round(np.clip(x,-.999,.999)*32767).astype('<i2').tobytes())

def pad_wem(b,size):
    # Keep all native byte extents, so HIRC uInMemoryMediaSize stays accurate.
    assert b[:4]==b'RIFF' and b[8:12]==b'WAVE'
    gap=size-len(b)
    assert gap>=8
    # Wwise walks chunk sizes without standard RIFF padding. Insert before DATA,
    # not after the encoder's possibly odd-length DATA plus its terminal pad.
    at=12
    while b[at:at+4]!=b'data':
        at+=8+struct.unpack_from('<I',b,at+4)[0]
    b=b[:at]+b'JUNK'+struct.pack('<I',gap-8)+bytes(gap-8)+b[at:]
    b=b[:4]+struct.pack('<I',len(b)-8)+b[8:]
    assert len(b)==size
    return b

def main():
    assert not OUT.exists(),'Preserve prior candidate.'
    source=ROOT/'clash electricity sfx.wav'
    review=json.loads((ROOT/'validation/sfx_source_review.json').read_text())
    assert sha(source.read_bytes())==review['sha256']
    parent=ROOT/'build/readability_v1/Braum_Clash_Readability_v1.fantome'
    assert sha(parent.read_bytes())=='94b1270c8e3dd297b1d5d2f00c2a0cfabb3d19e9c72d39a2c2f7f20cc832b939'
    bank=(ROOT/'Braum.wad/668ac17b89a8d8ea.bnk').read_bytes()
    events_bank=(ROOT/'Braum.wad/6a0cd1a55c7df583.bnk').read_bytes()
    events=json.loads((ROOT/'audit/evidence/audio_event_map.json').read_text())
    native={a['id']:a for a in review['native_media']}
    bankchunks=list(chunks(bank)); assert dict(bankchunks)[b'BKHD'][:4]==struct.pack('<I',145)
    assert b''.join(tag+struct.pack('<I',len(raw))+raw for tag,raw in bankchunks)==bank
    # Derive the DATA position by walking, never trust a substring in media.
    at=0
    for tag,raw in bankchunks:
        if tag==b'DATA':data_start=at+8
        at+=8+len(raw)
    records=list(struct.iter_unpack('<III',dict(bankchunks)[b'DIDX']))
    OUT.mkdir(); (OUT/'masters').mkdir(); (OUT/'wem').mkdir(); (OUT/'decoded').mkdir()
    logs=[]
    def run(args):
        result=subprocess.run(list(map(str,args)),capture_output=True,text=True)
        logs.append({'argv':list(map(str,args)),'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        (ROOT/'validation/sfx_v1_build_logs.json').write_text(json.dumps(logs,indent=2))
        assert result.returncode==0,result.stderr
        return result.stdout
    original,sr=readwav(source); original=original.mean(axis=1)
    # Preserve authentic electrical material. Exclude initial beep-only/quiet sections.
    segment=original[round(4.6*sr):round(7.2*sr)]
    segment=np.interp(np.arange(round(len(segment)*44100/sr))*sr/44100,np.arange(len(segment)),segment)
    fade=round(.1*44100); t=np.linspace(0,1,fade)
    cycle=np.concatenate([segment[fade:-fade],segment[-fade:]*(1-t)+segment[:fade]*t])
    cycle-=np.mean(cycle)
    cycle/=max(np.sqrt(np.mean(cycle**2)),1e-8)
    resultbank=bytearray(bank); changes=[]
    for mid,offset,size in records:
        if mid not in native:continue
        refs=[e for e in events if mid in e['media_ids']]
        assert len(refs)==1 and refs[0]['bank']=='6a0cd1a55c7df583.bnk'
        event=refs[0]['event_name']
        assert any(s in event for s in ['BraumEShieldBuff','BraumQMissile_hit','BraumQMissile_OnMissileCast','BraumRWrapper_OnCast'])
        old,rate=readwav(ROOT/f'build/sfx_source_review/{mid}.wav');old=old[:,0];assert rate==44100
        # Preserve the native amplitude envelope, onset, total duration and tail.
        step=882
        centers=np.arange(0,len(old),step)
        envelope=np.array([np.sqrt(np.mean(old[i:min(i+step,len(old))]**2)) for i in centers])
        env=np.interp(np.arange(len(old)),np.minimum(centers+step/2,len(old)-1),envelope)
        shift=(mid%1000)*17%len(cycle)
        signal=np.resize(np.roll(cycle,shift),len(old))*env*.708
        edge=min(220,len(signal)//2); signal[:edge]*=np.linspace(0,1,edge);signal[-edge:]*=np.linspace(1,0,edge)
        limit=min(1,.78/max(abs(signal).max(),1e-8));signal*=limit
        master=OUT/f'masters/{mid}.wav';writewav(master,signal)
        wem=OUT/f'wem/{mid}.wem'
        for quality in [4,2,0,-1]:
            run([ENC,'-q',quality,'-no-hash','-o',wem,master])
            encoded=wem.read_bytes()
            if len(encoded)+8<=size:break
        assert len(encoded)+8<=size,(mid,'Encoded media does not fit native extent')
        padded=pad_wem(encoded,size);wem.write_bytes(padded)
        decoded=OUT/f'decoded/{mid}.wav'
        metadata=run([DEC,'-i','-o',decoded,wem])
        decoded_signal,decoded_rate=readwav(decoded); decoded_signal=decoded_signal[:,0]
        assert decoded_rate==44100 and len(decoded_signal)==len(signal)
        assert abs(decoded_signal).max()<.99
        correlation=float(np.corrcoef(signal,decoded_signal)[0,1]);assert correlation>.9,(mid,correlation)
        assert 'Custom Vorbis' in metadata and 'channels: 1' in metadata
        resultbank[data_start+offset:data_start+offset+size]=padded
        changes.append({'id':mid,'event':event,'seconds':len(signal)/rate,'native_extent_bytes':size,'encoded_bytes_before_padding':len(encoded),'quality':quality,'sha256':sha(padded),'native_sha256':sha(bank[data_start+offset:data_start+offset+size]),'decoded_rms':float(np.sqrt(np.mean(decoded_signal**2))),'native_rms':native[mid]['rms'],'decoded_peak':float(abs(decoded_signal).max()),'decoded_correlation':correlation})
    assert len(changes)==20
    resultbank=bytes(resultbank);assert len(resultbank)==len(bank)
    after=dict(chunks(resultbank));before=dict(bankchunks)
    assert set(after)==set(before)
    for tag in before:
        if tag!=b'DATA':assert before[tag]==after[tag]
    modified={c['id'] for c in changes}
    for mid,offset,size in records:
        if mid not in modified:assert before[b'DATA'][offset:offset+size]==after[b'DATA'][offset:offset+size]
    # Verify every other byte, including padding between native media, is unchanged.
    restored=bytearray(resultbank)
    for mid,offset,size in records:
        if mid in modified:restored[data_start+offset:data_start+offset+size]=bank[data_start+offset:data_start+offset+size]
    assert bytes(restored)==bank
    package=OUT/'package'
    with zipfile.ZipFile(parent) as z:
        assert z.testzip() is None; z.extractall(package)
        previous={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
    bankfile=package/'WAD/Braum.wad.client'/BANKPATH
    assert not bankfile.exists();bankfile.parent.mkdir(parents=True,exist_ok=True);bankfile.write_bytes(resultbank)
    info=package/'META/info.json';meta=json.loads(info.read_text())
    meta.update(Name='Clash Braum - Electrical SFX v1',Version='0.1.0-sfx-v1',Description='Readability v1 visuals plus authentic supplied Clash electrical recording on selected Q/E/R cues. English VO not yet replaced. Manual gameplay test required; residual source beeps may remain.')
    info.write_text(json.dumps(meta,indent=2))
    for name,b in previous.items():
        if name!='META/info.json':assert (package/name).read_bytes()==b
    archive=OUT/'Braum_Clash_Electrical_SFX_v1.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(package.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(package).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for p in package.rglob('*'):
            if p.is_file():assert z.read(p.relative_to(package).as_posix())==p.read_bytes()
    # A short local listening preview; not embedded in the mod.
    preview=[]
    for mid in [190232138,103689118,541689440,169392210,21321056,309351640]:
        a,_=readwav(OUT/f'decoded/{mid}.wav');preview.extend([a[:,0],np.zeros(22050)])
    writewav(OUT/'Q_E_R_preview.wav',np.concatenate(preview))
    report={'status':'PASS','archive':archive.relative_to(ROOT).as_posix(),'sha256':sha(archive.read_bytes()),'parent':parent.relative_to(ROOT).as_posix(),'parent_sha256':sha(parent.read_bytes()),'source':source.name,'source_sha256':review['sha256'],'source_segment_seconds':[4.6,7.2],'processing':'Mono; 44.1kHz; 100ms crossfaded periodic electrical segment; native 20ms RMS envelope; -3dB starting gain; peak ceiling 0.78. No claimed beep removal or subjective audition.','changed_media':changes,'bank_sha256':sha(resultbank),'original_bank_sha256':sha(bank),'event_bank_sha256_unchanged':sha(events_bank),'bank_path':BANKPATH,'bank_version':145,'native_media_count':len(records),'unchanged_media_count':len(records)-len(changes),'all_nonmedia_bytes_exact':True,'all_parent_payloads_exact':True,'shared_event_impact':'Each replaced media ID reaches exactly one audited event. Q generic cast shared with basic attacks remains unchanged. Native event/switch/stop/attenuation graph remains untouched.','tools':[{'name':'wav2wem v0.1','url':'https://github.com/pas2k/wav2wem/releases/tag/v0.1','sha256':sha(ENC.read_bytes())},{'name':'vgmstream r2117','url':'https://github.com/vgmstream/vgmstream/releases/tag/r2117','sha256':sha(DEC.read_bytes())}],'reused_evidence':'readability_v1 validation: every preexisting payload is byte-identical; no geometry/texture/VFX rechecks required.','remaining':'Manual Q/E/R playback, volume, beeps and E stop/death behavior; W/general attacks/native VO unchanged; overall VFX acceptance pending.'}
    (ROOT/'validation/sfx_v1_build.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:report[k] for k in ['status','archive','sha256','unchanged_media_count']},indent=2))

if __name__=='__main__':main()
