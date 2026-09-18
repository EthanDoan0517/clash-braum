"""Reproducible isolated brightness/E/EQ/core trials. Never edits source assets."""
from pathlib import Path
import hashlib, json, re, shutil, subprocess, zipfile
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'build/model_runtime_trial'
OUT = ROOT / 'build/lightning_v1'
TEX = ROOT / 'work/tools/ltk-tex-utils.exe'
RITO = Path('C:/Users/etqdo/Downloads/cslol-go/cslol-tools/ritobin_cli.exe')
ASSET = 'assets/characters/braum/skins/base/braum_clash/'
logs = []

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def run(args):
    p = subprocess.run(list(map(str, args)), capture_output=True, text=True, encoding='utf8', errors='replace')
    logs.append(dict(argv=list(map(str,args)), returncode=p.returncode, stdout=p.stdout, stderr=p.stderr))
    assert p.returncode == 0, (p.stdout,p.stderr)

def blocks(text, pattern):
    """Balanced text blocks, ignoring braces in quoted strings."""
    for m in re.finditer(pattern, text, re.M):
        depth = 0
        for token in re.finditer(r'"(?:\\.|[^"\\])*"|[{}]', text[m.end()-1:]):
            t = token.group()
            if t == '{': depth += 1
            elif t == '}':
                depth -= 1
                if depth == 0:
                    end = m.end()-1 + token.end()
                    yield m.start(), end, text[m.start():end]
                    break
        else: raise ValueError('Unbalanced block')

def entries(s):
    return {re.search(r'"([^"]+)"', b).group(1): b for _,_,b in blocks(s,r'^    "[^"\n]+" = \w+ \{')}

# Explicit emitter allowlist: all other emitters, including telegraphs, stay exact.
# Texture substitutions use an existing single-frame lightning trail, without a flipbook.
SPELLS = {
 'E': {
  'Braum_E_Shield_cas': ['Inchant_shield','Inchant_shield_2','line'],
  'Braum_E_Block_BA_cas':['flash'], 'Braum_E_Block_BA_cas2':['shield_blink'],
  'Braum_E_Block_Spell_cas':['flash','splash'], 'Braum_E_Block_Spell_cas2':['shield_blink'],
  'Braum_E_Block_Spell_self':['splash'], 'Braum_E_shield_end':['spark2'],
  'Braum_E_shield_first_block':['First_block'], 'Braum_E_Shield_first_block_end':['spark2'],
 },
 'Q': {'Braum_Q_mis':['Trail','Trail_2','Spark'], 'Braum_Q_hit_tar':['flash2'],
       'Braum_Q_Hit_Monster_tar':['spark','flash2']},
 'R': {'Braum_R_mis':['line'], 'Braum_R_Small_mis':['line'],
       'Braum_R_PBAOE_Cas':['line'], 'Braum_R_Firstknockup_tar':['Lightning_Flash']},
 'W': {'Braum_W_Dash_Land':['line'], 'Braum_W_Shield_buf':['armor_sparkle']},
}

def transform(entry, names, spell):
    edits = []
    found = []
    for lo,hi,b in blocks(entry, r'^            VfxEmitterDefinitionData \{'):
        name = re.search(r'EmitterName: string = "([^"]+)"',b).group(1)
        if name not in names: continue
        found.append(name)
        # No animated atlas can silently be paired with a single-frame texture.
        assert not re.search(r'\b(StartFrame|FrameRate):',b), (spell,name,'animated atlas emitter')
        old=b
        b=re.sub(r'(?m)^                (?:TexDiv|NumFrames|IsRandomStartFrame):[^\n]*\n','',b)
        b,n = re.subn(r'(?m)^(                Texture: string = )"[^"]+"',
                     r'\1"'+ASSET+'lightning_trail.tex"',b)
        assert n==1,(spell,name,'texture')
        # Steel-blue energy relates to the accepted blue armor. Keep original
        # value animation and alpha; W remains subdued through native envelopes.
        for a,z,color in reversed(list(blocks(b,r'^                Color: embed = ValueColor \{'))):
            def tint(m):
                v=[float(x) for x in m.group(1).split(',')]
                peak=max(v[:3]); rgb=[peak*.60,peak*.78,peak]
                return '{ '+', '.join(format(x,'.9g') for x in rgb)+', '+m.group(1).split(',')[3].strip()+' }'
            colored=re.sub(r'\{\s*([-+\d.eE]+\s*,\s*[-+\d.eE]+\s*,\s*[-+\d.eE]+\s*,\s*[-+\d.eE]+)\s*\}',tint,color)
            b=b[:a]+colored+b[z:]
        # Prove only Texture and RGB color components changed at emitter scope.
        def normalize(s):
            s=re.sub(r'(?m)^                (?:TexDiv|NumFrames|IsRandomStartFrame):[^\n]*\n','',s)
            s=re.sub(r'(?m)^                Texture: string = .*$', '',s)
            for a,z,c in reversed(list(blocks(s,r'^                Color: embed = ValueColor \{'))):
                c=re.sub(r'\{\s*([-+\d.eE]+\s*,\s*[-+\d.eE]+\s*,\s*[-+\d.eE]+\s*,\s*[-+\d.eE]+)\s*\}',
                         lambda m:'{ RGB, '+format(float(m.group(1).split(',')[3]),'.9g')+' }',c)
                s=s[:a]+c+s[z:]
            return s
        assert normalize(old)==normalize(b),(spell,name,'protected emitter fields changed')
        edits.append((lo,hi,b))
    assert sorted(found)==sorted(names),(spell,found,names)
    for lo,hi,b in reversed(edits):entry=entry[:lo]+b+entry[hi:]
    return entry

def main():
    assert not OUT.exists(), 'Preserve existing trial; use a new version directory for changes.'
    OUT.mkdir(parents=True)
    accepted=BASE/'Braum_Clash_Model_Trial.fantome'
    assert sha(accepted)=='f3b055eff6f590f9a8a265aa1a878d4f2f20abf77d52049d495538945f868554'
    checkpoint=ROOT/'work/checkpoints/model_runtime_accepted';checkpoint.mkdir(parents=True,exist_ok=True)
    recovery=checkpoint/accepted.name
    if recovery.exists(): assert sha(recovery)==sha(accepted)
    else: shutil.copyfile(accepted,recovery)
    texture_dir=ROOT/'work/textures/brightness_v1';texture_dir.mkdir(parents=True,exist_ok=True)
    brightness={}
    for name,src in [('body','body_atlas_trial/clash_body_basecolor.png'),('shield_frame','shield_material_trial/clash_shield_basecolor.png')]:
        source=ROOT/'work/textures'/src
        a=np.array(Image.open(source).convert('RGBA')); rgb=a[:,:,:3].astype(np.float64)/255
        gain=1+.18*(1-rgb.max(axis=2,keepdims=True))
        b=a.copy(); b[:,:,:3]=np.rint(rgb*gain*255).astype(np.uint8)
        assert np.array_equal(a[:,:,3],b[:,:,3]) and np.all(b[:,:,:3]>=a[:,:,:3])
        dest=texture_dir/(name+'.png');Image.fromarray(b).save(dest)
        brightness[name]=dict(source=src,source_sha256=sha(source),output_sha256=sha(dest),
            mean_rgb_increase=float((b[:,:,:3].astype(float)-a[:,:,:3]).mean()),
            max_channel_increase=int((b[:,:,:3].astype(int)-a[:,:,:3]).max()),alpha_identical=True)
        run([TEX,'encode',dest,'-o',OUT/(name+'.tex'),'-f','bc3','--generate-mipmaps'])
        for mip in (0,2,4):run([TEX,'decode',OUT/(name+'.tex'),'-o',OUT/f'{name}_mip{mip}.png','--mipmap',mip])
    source_text=(BASE/'skin0_trial.ritobin').read_text()
    mapping=json.loads((ROOT/'audit/evidence/base_vfx_dependencies.json').read_text())
    bykey={r['resource_key']:r for r in mapping}
    owners={}; clones={}; changes=[]
    for spell,systems in SPELLS.items():
        for key,names in systems.items():
            row=bykey[key]; owner=row['owner_hash']
            if owner not in owners:
                p=OUT/(owner+'.ritobin')
                run([RITO,'-i','bin','-o','text','-d',ROOT/'audit/sources',ROOT/'Braum.wad'/(owner+'.bin'),p])
                noop=OUT/(owner+'_noop.bin');run([RITO,'-i','text','-o','bin','-k',p,noop])
                assert sha(noop)==sha(ROOT/'Braum.wad'/(owner+'.bin'))
                owners[owner]=entries(p.read_text())
            original=owners[owner][row['entry']]
            newpath='Characters/Braum/Skins/Skin0/Particles/Clash_v1_'+key
            clone=transform(original,names,spell).replace('"'+row['entry']+'"','"'+newpath+'"')
            clone=re.sub(r'(ParticleName: string = )"[^"]+"',r'\1"Clash_v1_'+key+'"',clone)
            clones[key]=(row['entry'],newpath,clone)
            changes.append(dict(spell=spell,key=key,source_entry=row['entry'],source_owner=owner,
                                clone=newpath,emitters=names,source_sha256=sha(ROOT/'Braum.wad'/(owner+'.bin'))))
    builds=[]
    for label,enabled in [('brightness',[]),('e',['E']),('eq',['E','Q']),('core',['E','Q','R','W'])]:
        stage=OUT/label;pkg=stage/'package';shutil.copytree(BASE/'package',pkg)
        wad=pkg/'WAD/Braum.wad.client';assets=wad/ASSET
        for name in brightness:shutil.copyfile(OUT/(name+'.tex'),assets/(name+'.tex'))
        text=source_text;added=[]
        for spell in enabled:
            for key in SPELLS[spell]:
                old,new,clone=clones[key]
                a='"'+key+'" = "'+old+'"';b='"'+key+'" = "'+new+'"'
                assert text.count(a)==1,key
                text=text.replace(a,b);added.append(clone)
        if added:
            assert text.rstrip().endswith('}')
            text=text.rstrip()[:-1]+'\n'+'\n'.join(added)+'\n}\n'
            shutil.copyfile(ROOT/'Braum.wad/d840318cf56171b6.tex',assets/'lightning_trail.tex')
        candidate=stage/'skin0.ritobin';candidate.write_text(text)
        binpath=wad/'data/characters/braum/skins/skin0.bin'
        run([RITO,'-i','text','-o','bin','-k',candidate,binpath])
        # Hashed reparse/no-op proves the candidate writer output is stable.
        decoded=stage/'verified.ritobin';run([RITO,'-i','bin','-o','text',binpath,decoded])
        noop=stage/'verified.bin';run([RITO,'-i','text','-o','bin','-k',decoded,noop]);assert sha(noop)==sha(binpath)
        before=entries(source_text);after=entries(text)
        for k,b in before.items():
            if k.endswith('/Resources'):
                for spell in enabled:
                    for key in SPELLS[spell]:
                        old,new,_=clones[key];b=b.replace('"'+key+'" = "'+old+'"','"'+key+'" = "'+new+'"')
            assert after[k]==b,(label,k,'unrelated entry changed')
        assert len(after)==len(before)+len(added)
        for ext in ('skn','skl'):assert sha(assets/('braum_clash.'+ext))==sha(BASE/'package/WAD/Braum.wad.client'/ASSET/('braum_clash.'+ext))
        meta=dict(Name='Clash Braum '+label.upper()+' v1 TRIAL',Author='Ethan',Version='0.2.0-'+label,
                  Description='Gameplay-accepted geometry; slight value lift; isolated lightning VFX candidate. Runtime approval pending. Enable only one Clash trial.')
        (pkg/'META/info.json').write_text(json.dumps(meta,indent=2))
        archive=stage/('Braum_Clash_'+label.title()+'_v1.fantome')
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for p in sorted(pkg.rglob('*')):
                if p.is_file():z.write(p,p.relative_to(pkg).as_posix())
        with zipfile.ZipFile(archive) as z:assert z.testzip() is None
        builds.append(dict(label=label,archive=str(archive.relative_to(ROOT)),sha256=sha(archive),
                           spells=enabled,clones=len(added),payloads=[dict(path=p.relative_to(wad).as_posix(),sha256=sha(p)) for p in sorted(wad.rglob('*')) if p.is_file()]))
    result=dict(status='OFFLINE BUILT; runtime not yet accepted',baseline_sha256=sha(accepted),
        baseline_user_feedback='Model looks good; colors slightly too dark. Geometry accepted.',
        brightness_formula='RGB *= 1 + 0.18*(1-max(RGB)); normalized encoded diffuse values; alpha unchanged',
        brightness=brightness,changes=changes,builds=builds,
        protected='Original entries except selected resolver targets exact; emitter changes only texture/RGB and removal of static 2x2 random-frame sampling for the single-frame texture. Alpha curves, timing, rates, geometry, attachments, telegraphs and audio unchanged.',
        limitations=['R retains animated ice and ground meshes.','E retains original particle shield mesh and material override; lightning alignment needs gameplay review.','Normal map remains unbound.','No runtime VFX acceptance claimed.'])
    (ROOT/'validation/lightning_v1_build.json').write_text(json.dumps(result,indent=2))
    (ROOT/'validation/lightning_v1_build_logs.json').write_text(json.dumps(logs,indent=2))
    print(json.dumps(dict(builds=builds,brightness=brightness),indent=2))

if __name__=='__main__':main()
