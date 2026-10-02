import sys, json
from PIL import Image
S='/tmp/claude-0/-home-user-KOCH-SIMULATOR/4c46a856-9b83-58ac-a5d2-3a1adfa042aa/scratchpad'
d={p['id']:p for p in json.load(open(S+'/batch1_part0.json'))}
pid=sys.argv[1]; x0,y0,x1,y1=map(int,sys.argv[2:6]); out=sys.argv[6] if len(sys.argv)>6 else None
im=Image.open(d[pid]['path'])
c=im.crop((x0,y0,x1,y1))
mx=int(sys.argv[7]) if len(sys.argv)>7 else 1600
if max(c.size)>mx: c.thumbnail((mx,mx))
o=out or f'{S}/agent_scratch/pass1_part0/c/{pid}_{x0}_{y0}.jpg'
c.save(o,quality=90); print(o, c.size)
