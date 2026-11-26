"""Draws the kill-feed icons (white silhouettes, CS style, our own art): AK-47, pistol, pump shotgun, SMG, LMG, headshot.
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

def canvas(width_mm, top_mm, bottom_mm, scale=0.56):
    """Blank supersampled mask plus a mm->px mapper; x from the butt (0) to the muzzle, y up."""
    k = scale*SS
    W, H = int((width_mm + 20)*k), int((top_mm - bottom_mm + 20)*k)
    img = Image.new("L", (W, H), 0)
    P = lambda pts: [((x + 10)*k, (top_mm + 10 - y)*k) for x, y in pts]
    return img, ImageDraw.Draw(img), P, k

def pistol(out):
    img, d, P, k = canvas(200, 40, -110, scale=1.2)
    d.polygon(P([(0, 0), (0, 32), (190, 32), (195, 26), (195, 4), (60, 4), (60, 0)]), fill=255)         # slide
    d.polygon(P([(14, 2), (62, 2), (52, -100), (8, -104), (2, -96)]), fill=255)                           # grip (raked)
    d.line(P([(62, 0), (70, -26), (104, -26), (112, 0)]), fill=255, width=int(6*k))                       # trigger guard
    d.polygon(P([(60, 4), (150, 4), (150, -4), (66, -4)]), fill=255)                                      # frame + rail
    d.rectangle(P([(180, 36), (186, 32)]), fill=255)                                                      # front sight
    save(img, out, 0, 0)

def shotgun(out):
    img, d, P, k = canvas(800, 40, -110)
    d.polygon(P([(0, -4), (220, 18), (230, -14), (150, -44), (0, -100)]), fill=255)                        # stock
    d.polygon(P([(225, -16), (225, 26), (420, 28), (430, -18)]), fill=255)                                # receiver
    d.polygon(P([(250, -16), (282, -16), (264, -78), (232, -74)]), fill=255)                              # grip
    d.line(P([(282, -18), (290, -40), (330, -40), (340, -18)]), fill=255, width=int(6*k))                 # guard
    d.rectangle(P([(420, 26), (800, 10)]), fill=255)                                                      # barrel
    d.rectangle(P([(420, 6), (720, -10)]), fill=255)                                                       # magazine tube
    d.polygon(P([(500, 10), (650, 10), (646, -26), (504, -26)]), fill=255)                                # pump
    for x in range(516, 640, 24):
        d.line(P([(x, 8), (x, -24)]), fill=0, width=max(1, int(2*k)))                                    # pump grooves
    save(img, out, 0, 0)

def smg(out):
    img, d, P, k = canvas(700, 60, -200)
    d.line(P([(0, -30), (0, 20)]), fill=255, width=int(10*k))                                             # butt plate
    d.line(P([(0, 14), (190, 24)]), fill=255, width=int(7*k)); d.line(P([(0, -26), (190, 0)]), fill=255, width=int(7*k))  # stock struts
    d.polygon(P([(180, -10), (180, 38), (480, 40), (490, -12)]), fill=255)                                # receiver
    d.polygon(P([(200, 40), (420, 40), (420, 52), (200, 52)]), fill=255)                                  # top rail
    d.polygon(P([(230, -10), (268, -10), (250, -96), (214, -92)]), fill=255)                              # grip
    d.line(P([(268, -12), (276, -40), (312, -40), (322, -12)]), fill=255, width=int(6*k))                 # guard
    mag_f = bezier((372, -12), (380, -100), (420, -176)); mag_b = bezier((340, -12), (346, -104), (388, -186))
    d.polygon(P(mag_f + mag_b[::-1]), fill=255)                                                           # curved mag
    d.polygon(P([(480, -6), (480, 34), (600, 30), (600, -2)]), fill=255)                                  # handguard
    d.rectangle(P([(600, 22), (700, 8)]), fill=255)                                                       # barrel
    save(img, out, 0, 0)

def lmg(out):
    img, d, P, k = canvas(1050, 90, -160)
    d.polygon(P([(0, 4), (0, -70), (60, -50), (240, -12), (240, 30)]), fill=255)                          # skeleton stock
    d.polygon(P([(236, -16), (236, 44), (560, 46), (570, -18)]), fill=255)                                # receiver + feed cover
    d.polygon(P([(330, 46), (470, 46), (470, 74), (440, 84), (360, 84), (330, 74)]), fill=255)            # carry handle
    d.rectangle(P([(368, 76), (432, 60)]), fill=0)
    d.polygon(P([(270, -16), (306, -16), (288, -96), (254, -92)]), fill=255)                              # grip
    d.line(P([(306, -18), (314, -44), (350, -44), (360, -18)]), fill=255, width=int(6*k))                 # guard
    d.polygon(P([(380, -18), (520, -18), (520, -130), (380, -130)]), fill=255)                            # box magazine
    d.polygon(P([(566, -10), (566, 30), (760, 28), (760, -6)]), fill=255)                                 # handguard
    d.rectangle(P([(760, 20), (1050, 6)]), fill=255)                                                      # barrel
    d.rectangle(P([(1010, 30), (1030, 20)]), fill=255)                                                    # front sight
    d.line(P([(820, 4), (870, -140)]), fill=255, width=int(7*k)); d.line(P([(820, 4), (770, -140)]), fill=255, width=int(7*k))  # bipod
    save(img, out, 0, 0)

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
    pistol(os.path.join(out_dir, "T_KillIcon_Pistol.png"))
    shotgun(os.path.join(out_dir, "T_KillIcon_Shotgun.png"))
    smg(os.path.join(out_dir, "T_KillIcon_SMG.png"))
    lmg(os.path.join(out_dir, "T_KillIcon_LMG.png"))
    headshot(os.path.join(out_dir, "T_KillIcon_Headshot.png"))
