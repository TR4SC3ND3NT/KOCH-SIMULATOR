# ortho_crop.py src x0 y0 x1 y1 out [grid_m] [maxpx] : crop a north-up ortho in local world coords, draw grid + BLD outlines
import sys,json,math,glob
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS=None
S='/tmp/claude-0/-home-user-KOCH-SIMULATOR/4c46a856-9b83-58ac-a5d2-3a1adfa042aa/scratchpad'
src=sys.argv[1]; x0,y0,x1,y1=map(float,sys.argv[2:6]); out=sys.argv[6]
grid=float(sys.argv[7]) if len(sys.argv)>7 else 10; mx=int(sys.argv[8]) if len(sys.argv)>8 else 1600
base=S+'/agent_scratch/audit_plan_buildings/ortho/'+src
meta=json.load(open(base+'.json')); X0,Y0,X1,Y1=meta['extent_local']; r=meta['m_per_px']
im=Image.open(base+'.png').convert('RGB')
c=im.crop((int((x0-X0)/r),int((Y1-y1)/r),int((x1-X0)/r),int((Y1-y0)/r)))
k=mx/max(c.size); c=c.resize((int(c.width*k),int(c.height*k)))
s=k/r; d=ImageDraw.Draw(c)
P=lambda x,y:((x-x0)*s,(y1-y)*s)
g=math.ceil(x0/grid)*grid
while g<x1: d.line([P(g,y0),P(g,y1)],fill=(255,255,0) if g%50==0 else (90,90,90)); d.text(P(g,y1),str(int(g)),fill=(255,255,0)); g+=grid
g=math.ceil(y0/grid)*grid
while g<y1: d.line([P(x0,g),P(x1,g)],fill=(255,255,0) if g%50==0 else (90,90,90)); d.text(P(x0,g),str(int(g)),fill=(255,255,0)); g+=grid
if '--bld' in sys.argv:
  for f in glob.glob('/home/user/KOCH-SIMULATOR/Art/Blender/Specs/BLD_*.json'):
    sp=json.load(open(f)); a=sp['anchor']; dx,dy=a['x_dir']; n=math.hypot(dx,dy); dx/=n; dy/=n; ox,oy=a['world_xy']
    sc=sp.get('scale',1.0); ring=sp['ring']
    cx=sum(p[0] for p in ring)/len(ring); cy=sum(p[1] for p in ring)/len(ring)
    ring=[(cx+(p[0]-cx)*sc, cy+(p[1]-cy)*sc) for p in ring]
    w=[P(ox+dx*x-dy*y, oy+dy*x+dx*y) for x,y in ring]
    d.line(w+w[:1],fill=(255,40,40),width=2)
c.save(S+'/agent_scratch/pass1_part1/crop/'+out,quality=90); print(c.size, s,'px/m')
