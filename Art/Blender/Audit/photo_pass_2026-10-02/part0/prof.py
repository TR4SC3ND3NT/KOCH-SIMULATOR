import sys,json,numpy as np
from PIL import Image
S='/tmp/claude-0/-home-user-KOCH-SIMULATOR/4c46a856-9b83-58ac-a5d2-3a1adfa042aa/scratchpad'
d={p['id']:p for p in json.load(open(S+'/batch1_part0.json'))}
pid=sys.argv[1]; y0,y1=int(sys.argv[2]),int(sys.argv[3]); cols=[int(c) for c in sys.argv[4].split(',')]
im=np.asarray(Image.open(d[pid]['path']).convert('RGB')).astype(float)
for c in cols:
    col=im[y0:y1,c-3:c+4].mean(1)
    # paint mask: yellow (R,G high, B low) or white (all high, low saturation)
    r,g,b=col[:,0],col[:,1],col[:,2]
    yel=(r>150)&(g>120)&(b<110)
    wht=(r>175)&(g>175)&(b>170)
    m=yel|wht
    runs=[];start=None
    for i,v in enumerate(m):
        if v and start is None: start=i
        if not v and start is not None:
            if i-start>=6: runs.append((y0+start,y0+i-1,'Y' if yel[start:i].mean()>0.5 else 'W'))
            start=None
    if start is not None: runs.append((y0+start,y1-1,'?'))
    print(c, [(a,b,b-a+1,t) for a,b,t in runs])
