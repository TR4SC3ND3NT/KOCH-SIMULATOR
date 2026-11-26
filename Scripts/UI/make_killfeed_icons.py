"""Draws the kill-feed icons (white silhouettes, CS style, our own art): AK-47 side view and headshot.
Usage: python3 Scripts/UI/make_killfeed_icons.py <out_dir>. Geometry in mm, muzzle to the right."""
import math, sys, os
from PIL import Image, ImageDraw

SS = 4  # supersampling factor

def bezier(p0, p1, p2, n=24):
    return [((1-t)**2*p0[0] + 2*(1-t)*t*p1[0] + t*t*p2[0], (1-t)**2*p0[1] + 2*(1-t)*t*p1[1] + t*t*p2[1])
            for t in (i/n for i in range(n+1))]

def ak47(out, width=512, height=160):
    x0, y0, scale = -10.0, 70.0, 0.56  # mm origin offset (top-left) and px per mm at final size
    W, H, k = width*SS, height*SS, scale*SS
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    P = lambda pts: [((x - x0)*k, (y0 - y)*k) for x, y in pts]
    white, cut = 255, 0
    # stock: butt low, rising wrist into the receiver
    d.polygon(P([(0, 4), (250, 30), (255, -12), (180, -30), (40, -62), (0, -74)]), fill=white)
    # receiver + dust cover + rear sight block
    d.polygon(P([(245, -16), (245, 34), (300, 38), (470, 40), (480, 47), (525, 47), (530, 30), (530, -18)]), fill=white)
    # pistol grip, raked back
    d.polygon(P([(300, -14), (338, -14), (314, -104), (276, -100)]), fill=white)
    # trigger guard (loop)
    d.line(P([(336, -16), (342, -44), (380, -46), (392, -16)]), fill=white, width=int(7*k))
    # curved "banana" magazine
    front = bezier((428, -18), (446, -110), (500, -186))
    back = bezier((382, -18), (392, -112), (446, -202))
    d.polygon(P(front + back[::-1]), fill=white)
    # lower handguard (tapers forward) and upper handguard over the gas tube
    d.polygon(P([(528, -18), (528, 26), (690, 24), (695, -6), (680, -16)]), fill=white)
    d.polygon(P([(528, 30), (535, 46), (676, 44), (686, 30)]), fill=white)
    # gas block, barrel, cleaning rod, front sight, slant muzzle brake
    d.polygon(P([(686, 2), (686, 50), (712, 50), (716, 30), (712, 2)]), fill=white)
    d.rectangle(P([(700, 21), (868, 7)]), fill=white)
    d.rectangle(P([(712, 1), (840, -4)]), fill=white)
    d.polygon(P([(824, 14), (828, 52), (840, 56), (848, 52), (850, 14)]), fill=white)
    d.polygon(P([(864, 24), (892, 26), (888, 4), (864, 4)]), fill=white)
    # thin cuts so parts read separately at small size
    for a, b in [((250, 34), (250, -14)), ((528, 46), (528, -20)), ((420, -20), (380, -20))]:
        d.line(P([a, b]), fill=cut, width=max(1, int(1.6*k)))
    save(img, out, width, height)

def headshot(out, size=128):
    S = size*SS
    img = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(img)
    c = S/2
    # head profile facing right: cranium, jaw, neck
    d.ellipse([c-0.36*S, c-0.42*S, c+0.30*S, c+0.20*S], fill=255)
    d.polygon([(c+0.18*S, c+0.02*S), (c+0.30*S, c+0.10*S), (c+0.20*S, c+0.30*S), (c-0.04*S, c+0.34*S), (c-0.14*S, c+0.12*S)], fill=255)
    d.rectangle([c-0.16*S, c+0.20*S, c+0.02*S, c+0.46*S], fill=255)
    # bullet hole with cracks (cut out)
    hx, hy, r = c+0.02*S, c-0.14*S, 0.07*S
    d.ellipse([hx-r, hy-r, hx+r, hy+r], fill=0)
    for ang in (20, 110, 200, 290):
        a = math.radians(ang)
        d.line([(hx, hy), (hx+math.cos(a)*0.2*S, hy+math.sin(a)*0.2*S)], fill=0, width=int(0.025*S))
    save(img, out, size, size)

def save(mask, out, w, h):
    # trim to the silhouette (+4 px), so the widget's aspect-correct icon has no empty margins
    box = mask.getbbox()
    pad = 4*SS
    mask = mask.crop((max(0, box[0]-pad), max(0, box[1]-pad), min(mask.width, box[2]+pad), min(mask.height, box[3]+pad)))
    w, h = max(1, mask.width//SS), max(1, mask.height//SS)
    alpha = mask.resize((w, h), Image.LANCZOS)
    rgba = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    rgba.putalpha(alpha)
    rgba.save(out)

if __name__ == "__main__":
    out_dir = sys.argv[1]
    ak47(os.path.join(out_dir, "T_KillIcon_AK47.png"))
    headshot(os.path.join(out_dir, "T_KillIcon_Headshot.png"))
