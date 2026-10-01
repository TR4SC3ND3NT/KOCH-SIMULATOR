# panel.py <img> <out> <x,y,half,scale> ... : zoomed crops around points, original-pixel ticks every 10/20 px
import sys
from PIL import Image, ImageDraw
im = Image.open(sys.argv[1]); tiles = []
for a in sys.argv[3:]:
    x, y, hw, s = map(float, a.split(',')); x0, y0 = int(x-hw), int(y-hw)
    c = im.crop((x0, y0, int(x+hw), int(y+hw))).resize((int(2*hw*s),)*2, Image.LANCZOS); d = ImageDraw.Draw(c)
    st = 10 if hw <= 80 else 20
    for k in range(0, int(2*hw)+1, st):
        d.line([(k*s,0),(k*s,6 if k % (2*st) else 14)], fill='red'); d.line([(0,k*s),(6 if k % (2*st) else 14,k*s)], fill='red')
        if k % (2*st) == 0: d.text((k*s+2,14), str(x0+k), fill='red'); d.text((16,k*s), str(y0+k), fill='red')
    tiles.append(c)
W = max(t.width for t in tiles); n = len(tiles); cols = 3; rows = (n+cols-1)//cols
P = Image.new('RGB', (W*cols, W*rows), 'white')
for i, t in enumerate(tiles): P.paste(t, ((i % cols)*W, (i//cols)*W))
P.save(sys.argv[2], quality=90)
