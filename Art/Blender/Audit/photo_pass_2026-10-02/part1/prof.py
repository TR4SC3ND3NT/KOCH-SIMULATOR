# prof.py ID x0 x1 y0 y1 : mean-luminance row profile over columns x0..x1, prints local minima (mortar joints are light here -> maxima too)
import sys,json,numpy as np
from PIL import Image, ImageOps
S='/tmp/claude-0/-home-user-KOCH-SIMULATOR/4c46a856-9b83-58ac-a5d2-3a1adfa042aa/scratchpad'
d={p['id']:p for p in json.load(open(S+'/batch1_part1.json'))}
i=sys.argv[1]; x0,x1,y0,y1=map(int,sys.argv[2:6])
im=np.asarray(ImageOps.exif_transpose(Image.open(d[i]['path'])).convert('RGB')).astype(float)
reg=im[y0:y1,x0:x1]; L=reg.mean(axis=(1,2)); R=reg[:,:,0].mean(1); G=reg[:,:,1].mean(1)
from numpy import convolve
k=np.ones(5)/5; Ls=convolve(L,k,'same')
pk=[y0+j for j in range(3,len(Ls)-3) if Ls[j]==Ls[j-3:j+4].max() and Ls[j]>np.percentile(Ls,60)]
print('maxima', pk)
print('diffs', np.diff(pk))
for j in range(0,len(L),10): print(y0+j, int(L[j]), int(R[j]-G[j]))
