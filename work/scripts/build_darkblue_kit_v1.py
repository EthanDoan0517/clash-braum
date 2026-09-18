"""Reference-led Q/W/R electricity, corrected E shell selection, and loading portrait."""
import json, re, zipfile
from PIL import Image, ImageOps
import build_lightning_trial as p
ROOT=p.ROOT
OUT=ROOT/'build/darkblue_kit_v1'
PREFIX='Characters/Braum/Skins/Skin0/Particles/Clash_v1_'
LIGHTNING=p.ASSET+'lightning_trail.tex'
# Explicit per-system removals and electric texture replacements; other
# surviving emitters receive RGB-only color treatment, except distortion.
PLAN={
 'Braum_Q_mis': (['Ice_head','Ice_shard','Ice_dust'], ['ground_shape','tail','Trail','Trail_2','Spark']),
 'Braum_Q_hit_tar': (['ice_shard','smoke'], ['flash2','slow_trail','swirls','orbit']),
 'Braum_Q_Hit_Monster_tar': (['ice_shard','smoke'], ['spark','flash2','slow_trail','orbit']),
 'Braum_W_Dash_Land': (['smoke','rockshards'], ['line','Crack_90','Crack_180','Crack_270','Crack_360']),
 'Braum_W_Shield_buf': (['wispy'], ['armor_sparkle','frost_circle']),
 'Braum_R_mis': (['iceshard_center','cold_smoke','spatter','shards'], ['Frozen','line','cracks_left','cracks_right']),
 'Braum_R_Small_mis': (['iceshard_center','cold_smoke','spatter','shards'], ['Frozen','line','cracks_left','cracks_right']),
 'Braum_R_PBAOE_Cas': (['RockShards'], ['Frozen','line']),
 'Braum_R_Firstknockup_tar': (['wind'], ['Tornado','Lightning_Flash']),
 'Braum_R_Slow_Freeze_tar': ([], ['slow_trail','swirls']),
 'Braum_R_Slow_tar': ([], ['flash2','orbit']),
 'Braum_R_small_knockup_tar': ([], ['Tornado']),
}


def name(block): return re.search(r'EmitterName: string = "([^"]+)"',block).group(1)


def tint(block, accent):
    ratios=(.30,.58,1) if accent else (.12,.30,.78)
    colors=list(p.blocks(block,r'^                Color: embed = ValueColor \{'))
    for lo,hi,color in reversed(colors):
        def rgb(m):
            vals=[float(x) for x in m.group(1).split(',')]; peak=max(vals[:3])
            return '{ '+', '.join(format(peak*x,'.9g') for x in ratios)+', '+m.group(1).split(',')[3].strip()+' }'
        color=re.sub(r'\{\s*([-+\d.eE]+\s*,\s*[-+\d.eE]+\s*,\s*[-+\d.eE]+\s*,\s*[-+\d.eE]+)\s*\}',rgb,color)
        block=block[:lo]+color+block[hi:]
    if not colors:
        block=block[:-1]+'    Color: embed = ValueColor {\n                    ConstantValue: vec4 = { '+', '.join(map(str,ratios))+', 1 }\n                }\n            }'
    return block


def protected(block):
    # Compare all fields outside explicit color/texture/UV appearance changes.
    for field in ['Color','TextureMult','BirthUvScrollRate']:
        for lo,hi,_ in reversed(list(p.blocks(block,rf'^                {field}: [^\n]*\{{'))):
            block=block[:lo]+block[hi:]
    block=re.sub(r'(?m)^                (?:Texture|TexDiv|NumFrames|IsRandomStartFrame):[^\n]*','',block)
    return re.sub(r'\s+',' ',block).strip()


def transform(entry, remove, electric):
    found=set(); edited=[]
    for lo,hi,old in reversed(list(p.blocks(entry,r'^            VfxEmitterDefinitionData \{'))):
        n=name(old); found.add(n)
        if n in remove:
            assert not re.search(r'(?i)(sound|audio|event)',old),n
            if re.search(r'(?i)child',old):
                assert re.findall(r'EffectKey: hash = "([^"]+)"',old)==['Braum_R_Rock_Mis_Child']
                empty=p.entries((ROOT/'build/lightning_v1/f2ef4463d62600e6.ritobin').read_text())['Characters/Braum/Skins/Skin0/Particles/Braum_Base_R_Rock_Mis_Child']
                assert 'EmitterDefinitionData' not in empty and not re.search(r'(?i)(sound|audio|event)',empty)
            new=''
        elif 'distort' in n.lower(): continue
        else:
            new=tint(old, n in electric or 'flash' in n.lower() or 'spark' in n.lower())
            if n in electric:
                assert not re.search(r'\b(?:StartFrame|FrameRate):',new),(n,'animated atlas needs separate handling')
                new,count=re.subn(r'(?m)^(                Texture: string = )"[^"]+"',r'\1"'+LIGHTNING+'"',new)
                assert count==1,n
                new=re.sub(r'(?m)^                (?:TexDiv|NumFrames|IsRandomStartFrame):[^\n]*\n','',new)
                for field in ['TextureMult','BirthUvScrollRate']:
                    for a,b,_ in reversed(list(p.blocks(new,rf'^                {field}: [^\n]*\{{'))): new=new[:a]+new[b:]
                new=new[:-1]+'    BirthUvScrollRate: embed = ValueVector2 {\n                    ConstantValue: vec2 = { 0.08, 1.25 }\n                }\n            }'
            assert protected(old)==protected(new),(n,'protected field changed')
            # Existing alpha values are retained verbatim by tint; no timeline,
            # attachment, scale, spawn-rate, child or event field is authorized.
        entry=entry[:lo]+new+entry[hi:]
        edited.append(dict(emitter=n,action='remove frost/shard' if n in remove else 'electric texture + RGB + scroll' if n in electric else 'RGB only'))
    assert set(remove+electric)<=found, (remove,electric,found)
    return entry,edited


def main():
    assert not OUT.exists(),'Preserve existing candidate.'
    parent=ROOT/'build/color_pop_v3/Braum_Clash_Color_Pop_v3_Clean_Shield.fantome'
    assert p.sha(parent)=='0d3c8e039d6d6383b669e38526b5b71940e26dbe9e86850bc2e1a3cc573d52d0'
    OUT.mkdir(parents=True); package=OUT/'package'
    with zipfile.ZipFile(parent) as z:
        assert z.testzip() is None; z.extractall(package)
        before_files={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
    wad=package/'WAD/Braum.wad.client'; binpath=wad/'data/characters/braum/skins/skin0.bin'
    source=ROOT/'build/color_pop_v3/skin0.ritobin'; text=source.read_text(); before=p.entries(text)
    p.run([p.RITO,'-i','text','-o','bin','-k',source,OUT/'parent.bin']); assert p.sha(OUT/'parent.bin')==p.sha(binpath)
    # Restore inner animated surfaces exactly from the known motion candidate.
    motion=p.entries((ROOT/'build/e_motion_v3/skin0.ritobin').read_text())
    inner=PREFIX+'Braum_E_Shield_cas'; text=text.replace(before[inner],motion[inner])
    outer=PREFIX+'Braum_E_shield_first_block'; entry=before[outer]
    shells=list(p.blocks(entry,r'^            VfxEmitterDefinitionData \{'))
    assert len(shells)==1 and name(shells[0][2])=='First_block'
    a,b,shell=shells[0]; assert 'braum_base_e_shield_first_block.scb' in shell and 'BirthUvScrollRate' not in shell
    text=text.replace(entry,entry[:a]+entry[b:])
    rows={r['resource_key']:r for r in json.loads((ROOT/'audit/evidence/base_vfx_dependencies.json').read_text())}
    changes=[]; new_entries=[]; rewires=[]
    for key,(remove,electric) in PLAN.items():
        path=PREFIX+key
        if path in before: original=before[path]
        else:
            row=rows[key]; owner=ROOT/'build/lightning_v1'/(row['owner_hash']+'.ritobin')
            assert owner.exists()
            native=p.entries(owner.read_text())[row['entry']]
            original=native.replace('"'+row['entry']+'"','"'+path+'"')
            original=re.sub(r'(ParticleName: string = )"[^"]+"',r'\1"Clash_v1_'+key+'"',original)
            old='"'+key+'" = "'+row['entry']+'"'; new='"'+key+'" = "'+path+'"'
            assert text.count(old)==1; text=text.replace(old,new); rewires.append((old,new))
        converted,edits=transform(original,remove,electric)
        if path in before: text=text.replace(before[path],converted)
        else: new_entries.append(converted)
        changes.append(dict(system=key,emitters=edits))
    text=text.rstrip()[:-1]+'\n'+'\n'.join(new_entries)+'\n}\n'
    after=p.entries(text)
    allowed={inner,outer}|{PREFIX+k for k in PLAN}
    for key,entry in before.items():
        if key in allowed:continue
        if key.endswith('/Resources'):
            for old,new in rewires:entry=entry.replace(old,new)
        assert after[key]==entry,('unrelated entry',key)
    assert len(after)==len(before)+len(new_entries)
    trial=OUT/'skin0.ritobin'; trial.write_text(text)
    p.run([p.RITO,'-i','text','-o','bin','-k',trial,binpath])
    p.run([p.RITO,'-i','bin','-o','text',binpath,OUT/'verified.ritobin'])
    p.run([p.RITO,'-i','text','-o','bin','-k',OUT/'verified.ritobin',OUT/'verified.bin']); assert p.sha(binpath)==p.sha(OUT/'verified.bin')
    # Native loading slot is 308x560; crop the supplied landscape around Clash.
    reference=ROOT/'clash new.avif'
    portrait=ImageOps.fit(Image.open(reference).convert('RGB'),(308,560),Image.Resampling.LANCZOS,centering=(.50,.50))
    portrait.save(OUT/'loading_portrait.png')
    splash=wad/'assets/characters/braum/skins/base/braumloadscreen.tex'
    p.run([p.TEX,'encode',OUT/'loading_portrait.png','-o',splash,'-f','bc3','--generate-mipmaps'])
    p.run([p.TEX,'decode',splash,'-o',OUT/'loading_decoded.png'])
    decoded=Image.open(OUT/'loading_decoded.png').convert('RGBA'); assert decoded.size==(308,560) and decoded.getextrema()[3]==(255,255)
    meta=package/'META/info.json'; info=json.loads(meta.read_text())
    info.update(Name='Clash Braum Dark Blue Kit v1 TRIAL',Version='0.3.0-blue',Description='Animated inner E restored; static outer first-block shell removed. Q/W/R dark-blue electricity and supplied Clash loading portrait. Manual gameplay approval pending.')
    meta.write_text(json.dumps(info,indent=2))
    actual={f.relative_to(package).as_posix():f.read_bytes() for f in package.rglob('*') if f.is_file()}
    new_path='WAD/Braum.wad.client/assets/characters/braum/skins/base/braumloadscreen.tex'
    assert actual.keys()-before_files.keys()=={new_path}
    assert not before_files.keys()-actual.keys()
    assert {n for n in before_files if actual[n]!=before_files[n]}=={'META/info.json','WAD/Braum.wad.client/data/characters/braum/skins/skin0.bin'}
    archive=OUT/'Braum_Clash_Dark_Blue_Kit_v1.fantome'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for n,data in sorted(actual.items()):z.writestr(n,data)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None and all(z.read(n)==data for n,data in actual.items())
    report=dict(status='PASS targeted build; gameplay pending',archive=str(archive.relative_to(ROOT)),sha256=p.sha(archive),parent_sha256=p.sha(parent),
        changes=changes,E='Restored scrolling inner enchant emitters; removed non-scrolling First_block mesh only. Other block/expiry effects retained.',
        loading=dict(source='clash new.avif',source_sha256=p.sha(reference),path=new_path,dimensions=[308,560],crop='centered portrait'),
        protected='Body/shield textures, model/rig, team telegraphs/endcaps, sound/recall and unrelated entries exact; surviving emitter timelines/alpha/scale/attachments/rates exact.',
        limitations='R ice meshes removed; electrical ground/travel effects retain footprint/timing, but visual readability must be tested. E outer-shell identification follows corrected user description and requires confirmation.',
        reused='Model/color and shared lightning texture checks: exact unchanged bytes.',
        payloads=[dict(path=f.relative_to(wad).as_posix(),sha256=p.sha(f)) for f in sorted(wad.rglob('*')) if f.is_file()])
    (ROOT/'validation/darkblue_kit_v1_build.json').write_text(json.dumps(report,indent=2))
    (ROOT/'validation/darkblue_kit_v1_build_logs.json').write_text(json.dumps(p.logs,indent=2))
    print(json.dumps({k:report[k] for k in ['status','archive','sha256','E','loading']},indent=2))


if __name__=='__main__':main()
