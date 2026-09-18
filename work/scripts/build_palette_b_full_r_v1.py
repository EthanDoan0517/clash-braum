"""Combine B/silver with full-density legacy electric R above the dark ground."""
import json,re,zipfile,hashlib
import build_lightning_trial as p
from build_readability_v1 import emitters,name,guard,PREFIX
ROOT=p.ROOT;OUT=ROOT/'build/palette_b_full_r_v1'
BIN='WAD/Braum.wad.client/data/characters/braum/skins/skin0.bin'

def read_package(label,expected):
    record=json.loads((ROOT/f'validation/{label}_build.json').read_text())
    archive=ROOT/record['archive'];assert p.sha(archive)==expected==record['sha256']
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        files={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
    raw=OUT/(label+'.bin');raw.write_bytes(files[BIN])
    source_label='strike_v1' if label=='palette_b_silver_v1' else label
    text=ROOT/f'build/{source_label}/skin0.ritobin'
    bound=OUT/(label+'_source_bound.bin')
    p.run([p.RITO,'-i','text','-o','bin','-k',text,bound]);assert bound.read_bytes()==files[BIN]
    return files,text.read_text(),expected

def main():
    assert not (OUT/'Braum_Clash_Palette_B_Silver_Full_Lightning_R_v1.fantome').exists(),'Preserve candidate.'
    OUT.mkdir(parents=True,exist_ok=True)
    before,text,parenthash=read_package('palette_b_silver_v1','ec4705fd8caf2a556e16bd4dec3e652212e7c7eafe0ae9f091b029566d6def72')
    _,full,_=read_package('crackle_v1','bc51d5d16093f3d5c46fc75de43a1862fef1480302a3356b229fd081a1a7e44e')
    _,dark,_=read_package('refinement_v2','570c9b9c1a2689818b483363aa459f3eb157afa3c68268e0ef311c3d1e1f2e90')
    original=p.entries(text);legacy=p.entries(full);ground=p.entries(dark);changes=[]
    for suffix in ['Braum_R_mis','Braum_R_Small_mis','Braum_R_PBAOE_Cas']:
        key=PREFIX+suffix;e=legacy[key]
        dark_emitters={name(b):b for _,_,b in emitters(ground[key])}
        extra=[]
        for a,z,b in reversed(emitters(e)):
            if name(b)=='Frozen':
                electric=b.replace('EmitterName: string = "Frozen"','EmitterName: string = "Clash_R_Ground_Arc"')
                electric=electric.replace('Pass: i16 = -52','Pass: i16 = -51')
                guard(b,electric,['EmitterName','Pass']);extra.append(electric)
                e=e[:a]+dark_emitters['Frozen']+e[z:]
            elif name(b)=='GroundBurn':e=e[:a]+dark_emitters['GroundBurn']+e[z:]
        marker='        ComplexEmitterDefinitionData: list[pointer] = {'
        assert len(extra)==1
        e=e.replace(marker,marker+'\n'+extra[0],1)
        finalemit={name(b):b for _,_,b in emitters(e)}
        for n in ['Frozen','GroundBurn']:
            if n in dark_emitters:assert finalemit[n]==dark_emitters[n]
            else:assert n not in finalemit
        for _,_,b in emitters(legacy[key]):
            if name(b) not in ['Frozen','GroundBurn']:assert finalemit[name(b)]==b
        assert 'ConstantValue: f32 = 80' in finalemit['line']
        assert not any(n.startswith(('Clash_R_Strike','Clash_R_Connected','Clash_R_Crater')) for n in finalemit)
        text=text.replace(original[key],e);changes.append(key)
    after_entries=p.entries(text)
    assert after_entries.keys()==original.keys()
    assert {k for k in original if after_entries[k]!=original[k]}==set(changes)
    available={n.lower() for n in before}
    refs=set(re.findall(r'"(assets/characters/braum/skins/base/braum_clash/[^\"]+)"',text,re.I))
    assert all(('WAD/Braum.wad.client/'+r).lower() in available for r in refs)
    source=OUT/'skin0.ritobin';source.write_text(text)
    compiled=OUT/'skin0.bin';p.run([p.RITO,'-i','text','-o','bin','-k',source,compiled])
    decoded=OUT/'verified.ritobin';p.run([p.RITO,'-i','bin','-o','text',compiled,decoded])
    roundtrip=OUT/'verified.bin';p.run([p.RITO,'-i','text','-o','bin','-k',decoded,roundtrip]);assert p.sha(compiled)==p.sha(roundtrip)
    after=before.copy();after[BIN]=compiled.read_bytes()
    info=json.loads(after['META/info.json']);info.update(Name='Clash Braum Palette B Silver + Full Lightning R',Version='0.4.3-b-full-r',Description='Indigo/gold body, metallic silver shield, painted close crop; restores full-density electric R over dark ground. Accepted E and current Q/W, audio and English VO preserved. Gameplay approval pending.')
    after['META/info.json']=json.dumps(info,indent=2).encode()
    assert {n for n in before if before[n]!=after[n]}=={BIN,'META/info.json'}
    archive=OUT/'Braum_Clash_Palette_B_Silver_Full_Lightning_R_v1.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(after.items()):z.writestr(n,b)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None and set(z.namelist())==set(before) and all(z.read(n)==b for n,b in after.items())
    report=dict(status='PASS R source/ground guards, references, BIN roundtrip and ZIP identity; gameplay pending',archive=archive.relative_to(ROOT).as_posix(),sha256=p.sha(archive),parent_sha256=parenthash,changed_entries=changes,R='Crackle-v1 emitters restored at original full intensity/density (line 80); Frozen electric layer retained at original alpha as Ground_Arc above exact refinement-v2 dark Frozen/GroundBurn. New track/strike/crater emitters removed.',protected='Every other BIN entry and package member exact except metadata. E/Q/W and Q/R cast ice-removal remain exact; geometry, B textures, hair, SFX and VO exact.',reused='palette_b_silver_v1 texture mip/alpha and mapped review; unchanged geometry/audio and non-R VFX evidence by member identity.',payloads=[dict(path=n.removeprefix('WAD/Braum.wad.client/'),sha256=hashlib.sha256(b).hexdigest()) for n,b in after.items() if n.startswith('WAD/Braum.wad.client/')])
    (ROOT/'validation/palette_b_full_r_v1_build.json').write_text(json.dumps(report,indent=2))
    (ROOT/'validation/palette_b_full_r_v1_build_logs.json').write_text(json.dumps(p.logs,indent=2))
    print(json.dumps({k:report[k] for k in ['status','archive','sha256']},indent=2))

if __name__=='__main__':main()
