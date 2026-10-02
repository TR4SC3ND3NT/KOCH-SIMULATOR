# crop + scale + grid with source-pixel labels: grid.py ID x0 y0 x1 y1 step [scale]
import sys, json
from PIL import Image, ImageDraw
S='/tmp/claude-0/-home-user-KOCH-SIMULATOR/4c46a856-9b83-58ac-a5d2-3a1adfa042aa/scratchpad'
d={p['id']:p for p in json.load(open(S+'/batch1_part0.json'))}
pid=sys.argv[1]; x0,y0,x1,y1,st=map(int,sys.argv[2:7]); sc=float(sys.argv[7]) if len(sys.argv)>7 else 1.0
im=Image.open(d[pid]['path']).convert('RGB').crop((x0,y0,x1,y1))
im=im.resize((int((x1-x0)*sc),int((y1-y0)*sc)))
dr=ImageDraw.Draw(im)
for x in range((x0//st+1)*st,x1,st):
    X=(x-x0)*sc; dr.line([(X,0),(X,im.size[1])],fill=(0,255,255) if x%(st*5)==0 else (0,120,255),width=1); dr.text((X+2,2),str(x),fill=(0,255,255))
for y in range((y0//st+1)*st,y1,st):
    Y=(y-y0)*sc; dr.line([(0,Y),(im.size[0],Y)],fill=(255,0,255) if y%(st*5)==0 else (255,120,0),width=1); dr.text((2,Y+2),str(y),fill=(255,0,255))
o=f'{S}/agent_scratch/pass1_part0/c/g_{pid}_{x0}_{y0}.jpg'; im.save(o,quality=90); print(o,im.size)
