# edge.py ID x y0 y1 [w] : vertical luminance profile at column x (+-w), prints strongest gradient rows
import sys,json,numpy as np
from PIL import Image, ImageOps
S='/tmp/claude-0/-home-user-KOCH-SIMULATOR/4c46a856-9b83-58ac-a5d2-3a1adfa042aa/scratchpad'
d={p['id']:p for p in json.load(open(S+'/batch1_part1.json'))}
i=sys.argv[1]; x,y0,y1=map(int,sys.argv[2:5]); w=int(sys.argv[5]) if len(sys.argv)>5 else 4
im=np.asarray(ImageOps.exif_transpose(Image.open(d[i]['path'])).convert('RGB')).astype(float)
c=im[y0:y1,x-w:x+w+1].mean(1); L=c.mean(1); RG=c[:,0]-c[:,1]
g=np.convolve(L,[1,1,0,-1,-1],'same'); g2=np.convolve(RG,[1,1,0,-1,-1],'same')
for name,gg in (('L',g),('R-G',g2)):
  idx=np.argsort(-np.abs(gg[3:-3]))[:8]+3
  print(name, sorted([(int(y0+j), int(gg[j])) for j in idx]))
