"""Orthographic engineering views of digit shells and native finger pivots."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[2]
d = json.loads((ROOT/'validation/rig_regions.json').read_text())
im = Image.new('RGB',(1800,760),'white'); draw=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
colors=['#777777','#ac4e12','#1d8134','#164dcc','#a72592','#159d9d']
for panel, (a,b) in enumerate([(0,1),(0,2),(1,2)]):
    limits=[(.66,.91),(-.35,-.02),(.84,1.18)]
    def xy(p):
        return (panel*600+40+(p[a]-limits[a][0])*1500, 650-(p[b]-limits[b][0])*1500)
    draw.text((panel*600+35,50),f"Draft left hand: {'xyz'[a]}/{'xyz'[b]}",fill='black',font=font)
    ci=0
    for name in ['Object004','Object009']:
        points = d['hand_geometry'][name]['points']
        for c in d['objects'][name]:
            if c['bounds'][0][0] < .69 or c['bounds'][2][1] > 1.17:
                continue
            p = [points[i] for i in c['indices']]
            col=colors[ci%len(colors)];ci+=1
            for v in p:
                x,y=xy(v);draw.ellipse((x-1,y-1,x+1,y+1),fill=col)
            center=[sum(v[k] for v in p)/len(p) for k in range(3)]
            draw.text(xy(center),str(c['id']),fill=col,font=font)
    for digit in ['Thumb','Index','Middle','Ring','Pinky']:
        p=[d['bones'][f'L_{digit}{i}']['head'] for i in [1,2]]
        draw.line([xy(v) for v in p],fill='black',width=2)
        draw.text(xy(p[0]),digit,fill='black',font=font)
    p=d['bones']['L_Hand']['head']
    draw.text(xy(p),'Wrist',fill='red',font=font)
im.save(ROOT/'validation/previews/hand_fit_diagnostic.png')
