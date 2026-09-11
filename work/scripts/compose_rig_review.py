"""Assemble labeled contact sheets from the recorded Blender review renders."""
from pathlib import Path
import json, hashlib, math
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
manifest=json.loads((ROOT/'validation/refined_render_manifest.json').read_text())
scene=ROOT/'work/scenes'/manifest['scene']
assert hashlib.sha256(scene.read_bytes()).hexdigest()==manifest['scene_sha256']
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
body=[r for r in manifest['renders'] if r['focus']=='body']
for start in range(0,len(body),12):
    subset=body[start:start+12]
    sheet=Image.new('RGB',(min(4,len(subset))*360,math.ceil(len(subset)/4)*404),'#f5f5f5');draw=ImageDraw.Draw(sheet)
    for k,row in enumerate(subset):
        x=(k%4)*360;y=(k//4)*404
        with Image.open(ROOT/row['file']) as im:sheet.paste(im.resize((360,360)),(x,y))
        draw.text((x+6,y+362),row['clip'].removeprefix('braum_'),fill='#111111',font=font)
        draw.text((x+6,y+381),f"Frame {row['frame']}",fill='#111111',font=font)
    sheet.save(ROOT/'validation/previews'/f'rig_refined_contact_{start//12+1}.png')

sheet=Image.new('RGB',(1200,1280),'#f5f5f5');draw=ImageDraw.Draw(sheet)
for r,name in enumerate(['braum_idle_01_loop_017_L_Hand.png','braum_spell3_idle0_017_R_Hand.png']):
    for c,(folder,label) in enumerate([('before_refinement','Previous draft'),('refined','Current refinement')]):
        with Image.open(ROOT/'validation/previews'/folder/name) as im:sheet.paste(im.resize((600,600)),(c*600,r*640+40))
        draw.text((c*600+12,r*640+12),f'{label} - {"left idle hand" if r==0 else "right E grip"}',fill='#111111',font=font)
sheet.save(ROOT/'validation/previews/rig_hand_comparison.png')
print('Contact sheets created from',len(manifest['renders']),'recorded renders')
