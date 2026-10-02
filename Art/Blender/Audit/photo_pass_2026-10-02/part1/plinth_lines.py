# plinth_lines.py ID xs y0 y1 : for each column, find maroon band (R-G > thr) top and bottom
import sys,json,numpy as np
from PIL import Image, ImageOps
S='/tmp/claude-0/-home-user-KOCH-SIMULATOR/4c46a856-9b83-58ac-a5d2-3a1adfa042aa/scratchpad'
d={p['id']:p for p in json.load(open(S+'/batch1_part1.json'))}
i=sys.argv[1]; xs=[int(v) for v in sys.argv[2].split(',')]; y0,y1=int(sys.argv[3]),int(sys.argv[4]); thr=float(sys.argv[5]) if len(sys.argv)>5 else 25
im=np.asarray(ImageOps.exif_transpose(Image.open(d[i]['path'])).convert('RGB')).astype(float)
for x in xs:
    c=im[y0:y1,x-3:x+4].mean(1); rg=c[:,0]-c[:,1]
    rg=np.convolve(rg,np.ones(5)/5,'same'); m=rg>thr
    idx=np.where(m)[0]
    if len(idx)==0: print(x,'none'); continue
    # longest run
    runs=np.split(idx,np.where(np.diff(idx)>3)[0]+1); r=max(runs,key=len)
    print(x, y0+r[0], y0+r[-1], len(r))
