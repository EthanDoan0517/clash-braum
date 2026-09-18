"""Unscaled contact sheets and per-pixel differences, preserving gameplay size."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageChops
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
cases=json.loads((ROOT/'validation/cuff_seam_individual_search.json').read_text())['cases']
rows=[]
for view in ('front','reverse'):
    for start in range(0,len(cases),4):
        group=cases[start:start+4];sheet=Image.new('RGB',(1080,len(group)*390),(235,235,235));draw=ImageDraw.Draw(sheet)
        for row,(clip,frame) in enumerate(group):
            images=[]
            for col,variant in enumerate(('parent','single','ties')):
                path=ROOT/f'validation/previews/gameplay_{variant}_{view}/{clip}_{frame:03}_body.png'
                im=Image.open(path).convert('RGB');assert im.size==(360,360);images.append(im)
                sheet.paste(im,(col*360,row*390+30));draw.text((col*360+5,row*390+5),f'{variant} | {clip}:{frame}',fill='black')
            for variant,im in zip(('single','ties'),images[1:]):
                delta=np.abs(np.array(im,dtype=int)-np.array(images[0],dtype=int)).max(axis=2)
                rows.append({'view':view,'clip':clip,'frame':frame,'variant':variant,'pixels_delta_over_8':int((delta>8).sum()),'pixels_delta_over_32':int((delta>32).sum()),'max_channel_delta':int(delta.max())})
        sheet.save(ROOT/f'validation/previews/gameplay_{view}_{start//4+1}.png')
(ROOT/'validation/cuff_gameplay_pixel_comparison.json').write_text(json.dumps({'note':'Pixel differences are evidence only, not an automatic visual quality verdict. Sheets retain native 360px renders without scaling.', 'rows':rows},indent=2))
