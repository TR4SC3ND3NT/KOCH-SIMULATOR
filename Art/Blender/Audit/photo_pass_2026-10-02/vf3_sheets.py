# Contact sheets of the 3 fps frames: 6 frames per sheet (3 x 2), labelled video / frame / time (s).
import os, sys, glob
from PIL import Image, ImageDraw
S = sys.argv[1]; OUT = os.path.join(S, "vf3_sheets"); os.makedirs(OUT, exist_ok=True)
idx = []
for line in open(os.path.join(S, "vf3", "manifest.tsv")):
    stem, n, src = line.rstrip("\n").split("\t")
    fr = sorted(glob.glob(os.path.join(S, "vf3", stem, "f_*.jpg")))
    for s0 in range(0, len(fr), 6):
        chunk = fr[s0:s0 + 6]
        ims = [Image.open(p).convert("RGB") for p in chunk]
        portrait = ims[0].height > ims[0].width
        tw = 520 if not portrait else 300
        th = int(tw * ims[0].height / ims[0].width)
        cols = 3 if not portrait else 6
        rows = (len(ims) + cols - 1) // cols
        sh = Image.new("RGB", (cols * tw, rows * (th + 16)), (20, 20, 20))
        d = ImageDraw.Draw(sh)
        for k, (p, im) in enumerate(zip(chunk, ims)):
            x, y = (k % cols) * tw, (k // cols) * (th + 16)
            sh.paste(im.resize((tw, th)), (x, y + 16))
            n_ = int(os.path.basename(p)[2:6]); t = 0.1667 + (n_ - 1) / 3
            d.text((x + 3, y + 2), f"{stem[-12:]} f{n_} t{t:.1f}", fill=(255, 255, 0))
        name = f"{stem}_{s0 // 6:03d}.jpg"
        sh.save(os.path.join(OUT, name), quality=85)
        idx.append((stem, name, os.path.basename(chunk[0]), os.path.basename(chunk[-1])))
with open(os.path.join(OUT, "index.tsv"), "w") as f:
    for r in idx:
        f.write("\t".join(r) + "\n")
print(len(idx), "sheets")
