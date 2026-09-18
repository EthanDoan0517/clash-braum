"""Hash-bound gameplay comparison sheets; differences are diagnostic, not acceptance."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
rows=[]
for view in ('front','reverse'):
    manifests=[json.loads((ROOT/f'validation/atlas_{kind}_{view}_render_manifest.json').read_text()) for kind in ('source','baked')]
    for m in manifests:
        assert hashlib.sha256((ROOT/'work/scenes'/m['scene']).read_bytes()).hexdigest()==m['scene_sha256']
    sheet=Image.new('RGB',(1080,390*len(manifests[0]['renders'])),(235,235,235));draw=ImageDraw.Draw(sheet)
    for row,(a,b) in enumerate(zip(*[m['renders'] for m in manifests])):
        assert (a['clip'],a['frame'])==(b['clip'],b['frame'])
        ims=[Image.open(ROOT/r['file']).convert('RGB') for r in (a,b)]
        delta=np.abs(np.asarray(ims[1],dtype=int)-np.asarray(ims[0],dtype=int))
        for col,im in enumerate(ims+[Image.fromarray(np.uint8(np.clip(delta*4,0,255)))]):
            sheet.paste(im,(360*col,390*row+30));draw.text((360*col+5,390*row+5),f"{('source','baked','difference x4')[col]} {a['clip']}:{a['frame']}",fill='black')
        d=delta.max(axis=2)
        rows.append(dict(view=view,clip=a['clip'],frame=a['frame'],pixels_over_8=int((d>8).sum()),pixels_over_32=int((d>32).sum()),max_delta=int(d.max()),mean_absolute_delta=float(delta.mean())))
    sheet.save(ROOT/f'validation/previews/body_atlas_comparison_{view}.png')
(ROOT/'validation/body_atlas_gameplay_comparison.json').write_text(json.dumps(dict(rows=rows,scope='8 matched native-size 360px / orthographic scale5 views; pixel differences are not an automatic acceptance gate.'),indent=2))
