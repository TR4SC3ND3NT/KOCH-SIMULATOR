# ortho_crop.py src X0 X1 Y0 Y1 out [grid] [overlay json of polylines]
import sys, json
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS=None
S='/tmp/claude-0/-home-user-KOCH-SIMULATOR/4c46a856-9b83-58ac-a5d2-3a1adfa042aa/scratchpad'
src={'google':('ortho_google_z20.png',(-215,-125,260,110),0.1),'bing':('ortho_bing_z19.png',(-430,-260,360,290),0.25),'esri':('ortho_esri_z19.png',(-430,-260,360,290),0.25),'googleN':('ortho_googleN_z20.png',(100,85,265,200),0.1)}
fn,ext,mpp=src[sys.argv[1]]
X0,X1,Y0,Y1=map(float,sys.argv[2:6]); out=sys.argv[6]; g=float(sys.argv[7]) if len(sys.argv)>7 else 5
im=Image.open(S+'/agent_scratch/audit_plan_buildings/ortho/'+fn).convert('RGB')
x0,y0,x1,y1=ext
c=im.crop((int((X0-x0)/mpp),int((y1-Y1)/mpp),int((X1-x0)/mpp),int((y1-Y0)/mpp)))
sc=1200/c.size[0]; c=c.resize((1200,int(c.size[1]*sc)))
dr=ImageDraw.Draw(c)
P=lambda x,y:((x-X0)/mpp*sc,(Y1-y)/mpp*sc)
import math
gx=math.ceil(X0/g)*g
while gx<=X1:
    X=P(gx,0)[0]; dr.line([(X,0),(X,c.size[1])],fill=(255,255,0),width=1); dr.text((X+2,2),str(int(gx)),fill=(255,255,0)); gx+=g
gy=math.ceil(Y0/g)*g
while gy<=Y1:
    Y=P(0,gy)[1]; dr.line([(0,Y),(c.size[0],Y)],fill=(255,255,0),width=1); dr.text((2,Y+2),str(int(gy)),fill=(255,255,0)); gy+=g
if len(sys.argv)>8:
    for name,pts,col in json.load(open(sys.argv[8])):
        dr.line([P(*p) for p in pts],fill=tuple(col),width=2)
c.save(out,quality=90); print(out,c.size)
