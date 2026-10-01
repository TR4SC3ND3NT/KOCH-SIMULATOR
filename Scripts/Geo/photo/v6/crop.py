# crop.py <img> <out> x0 y0 x1 y1 scale grid : zoomed crop with original-pixel ticks
import sys
from PIL import Image, ImageDraw
im = Image.open(sys.argv[1]); x0,y0,x1,y1 = map(int, sys.argv[3:7]); s = float(sys.argv[7]); g = int(sys.argv[8])
c = im.crop((x0,y0,x1,y1)).resize((int((x1-x0)*s), int((y1-y0)*s)), Image.LANCZOS); d = ImageDraw.Draw(c)
for x in range(0, x1-x0, g): d.line([(x*s,0),(x*s,10)], fill='red'); d.text((x*s+2,10), str(x0+x), fill='red')
for y in range(0, y1-y0, g): d.line([(0,y*s),(10,y*s)], fill='red'); d.text((12,y*s), str(y0+y), fill='red')
c.save(sys.argv[2], quality=92)
