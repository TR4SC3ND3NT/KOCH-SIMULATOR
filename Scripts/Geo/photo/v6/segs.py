# LSD segments of one photo, saved as npy + overlay for review. Usage: segs.py <img> <tag>
import cv2, numpy as np, sys
img = cv2.imread(sys.argv[1]); g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_ADV)
L = lsd.detect(g)[0].reshape(-1, 4)
ln = np.hypot(L[:,2]-L[:,0], L[:,3]-L[:,1]); L = L[ln > 60]
np.save(sys.argv[2]+'_segs.npy', L)
ov = img.copy()
for x1,y1,x2,y2 in L:
    a = np.degrees(np.arctan2(abs(y2-y1), abs(x2-x1)))
    c = (0,0,255) if a > 70 else (255,0,0) if a < 20 else (0,200,0)
    cv2.line(ov, (int(x1),int(y1)), (int(x2),int(y2)), c, 3)
cv2.imwrite(sys.argv[2]+'_segs.jpg', cv2.resize(ov, None, fx=0.4, fy=0.4))
print(len(L))
