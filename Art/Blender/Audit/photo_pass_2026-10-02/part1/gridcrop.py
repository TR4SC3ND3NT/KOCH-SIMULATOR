# gridcrop.py ID x0 y0 x1 y1 out scale step : crop at integer upscale with full-res pixel grid labels every step px
import sys,json
from PIL import Image, ImageOps, ImageDraw
S='/tmp/claude-0/-home-user-KOCH-SIMULATOR/4c46a856-9b83-58ac-a5d2-3a1adfa042aa/scratchpad'
d={p['id']:p for p in json.load(open(S+'/batch1_part1.json'))}
i=sys.argv[1]; x0,y0,x1,y1=map(int,sys.argv[2:6]); out=sys.argv[6]; k=float(sys.argv[7]); st=int(sys.argv[8])
im=ImageOps.exif_transpose(Image.open(d[i]['path'])).crop((x0,y0,x1,y1)).convert('RGB')
im=im.resize((int(im.width*k),int(im.height*k)),Image.LANCZOS); dr=ImageDraw.Draw(im)
for y in range((y0//st+1)*st,y1,st):
    yy=(y-y0)*k; dr.line([(0,yy),(12,yy)],fill=(0,255,255)); dr.text((14,yy-6),str(y),fill=(0,255,255))
for x in range((x0//st+1)*st,x1,st):
    xx=(x-x0)*k; dr.line([(xx,0),(xx,12)],fill=(255,255,0)); dr.text((xx+2,14),str(x),fill=(255,255,0))
im.save(S+'/agent_scratch/pass1_part1/crop/'+out,quality=92); print(im.size)
