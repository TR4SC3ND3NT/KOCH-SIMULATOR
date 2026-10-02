# usage: crop.py ID x0 y0 x1 y1 out [maxside]  (coords in full-res oriented pixels)
import sys,json
from PIL import Image, ImageOps
S='/tmp/claude-0/-home-user-KOCH-SIMULATOR/4c46a856-9b83-58ac-a5d2-3a1adfa042aa/scratchpad'
d={p['id']:p for p in json.load(open(S+'/batch1_part1.json'))}
i,x0,y0,x1,y1,out=sys.argv[1],*map(int,sys.argv[2:6]),sys.argv[6]
m=int(sys.argv[7]) if len(sys.argv)>7 else 1400
im=ImageOps.exif_transpose(Image.open(d[i]['path'])).crop((x0,y0,x1,y1))
im.thumbnail((m,m)); im.save(S+'/agent_scratch/pass1_part1/crop/'+out,quality=90); print(im.size)
