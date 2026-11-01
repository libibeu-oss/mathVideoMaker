"""Composite real WAWG app frames onto the green phone screen (phone_v stock), 176 frames @30fps."""
import subprocess, numpy as np, cv2, glob
N = 176; W, H = 1080, 1920
CX, CY, CW, CH = 58, 80, 1520, 2702          # crop in 4K source around the phone
dec = subprocess.Popen(['ffmpeg', '-nostdin', '-loglevel', 'error', '-i', 'stock/phone_v.mov', '-an', '-vf',
    f'fps=30,crop={CW}:{CH}:{CX}:{CY},scale={W}:{H}:flags=lanczos', '-frames:v', str(N + 2), '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
frames = [np.frombuffer(dec.stdout.read(W * H * 3), np.uint8).reshape(H, W, 3).copy() for _ in range(N)]
dec.kill()
A = '../wawg2/cap/'
app = sorted(glob.glob(A + 's2/*.jpg'))[:118] + sorted(glob.glob(A + 's5/*.jpg'))[:N - 118]
def keymask(im):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    b, g, r = [im[..., i].astype(np.float32) for i in range(3)]
    # green dominance -> soft matte
    d = g - np.maximum(r, b)
    a = np.clip((d - 18) / 50, 0, 1)
    hard = cv2.inRange(hsv, (38, 70, 60), (88, 255, 255))
    return a, hard
quads = []
for im in frames:
    a, hard = keymask(im)
    cs, _ = cv2.findContours(hard, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea).reshape(-1, 2).astype(np.float32)
    s = c.sum(1); df = c[:, 0] - c[:, 1]
    q = np.array([c[s.argmin()], c[df.argmax()], c[s.argmax()], c[df.argmin()]], np.float32)  # TL TR BR BL
    quads.append(q)
Q = np.array(quads)
# temporal smoothing
K = 5; Qs = np.array([Q[max(0, i - K):i + K + 1].mean(0) for i in range(N)])
# push corners outward (rounded screen corners make extremes sit inside)
ctr = Qs.mean(1, keepdims=True); Qs = ctr + (Qs - ctr) * 1.06
enc = subprocess.Popen(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '14', '-pix_fmt', 'yuv420p', 'seg/s03.mp4'], stdin=subprocess.PIPE)
for i, im in enumerate(frames):
    ap = cv2.imread(app[min(i, len(app) - 1)])
    ah, aw = ap.shape[:2]
    src = np.float32([[0, 0], [aw, 0], [aw, ah], [0, ah]])
    M = cv2.getPerspectiveTransform(src, Qs[i])
    warp = cv2.warpPerspective(ap, M, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
    # match screen to scene: slight dim + soft reflection gradient
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    warp = warp * .93 + 14 * (1 - yy)
    a, hard = keymask(im)
    f = im.astype(np.float32)
    G = np.array(cv2.mean(im, mask=cv2.erode(hard, np.ones((15, 15), np.uint8)))[:3], np.float32)
    d2 = f[..., 1] - (f[..., 0] + f[..., 2]) / 2
    gd = G[1] - (G[0] + G[2]) / 2
    al = np.clip((d2 - 8) / (gd - 8), 0, 1)
    al = cv2.GaussianBlur(al, (3, 3), 0)[..., None]
    out = f + al * (warp - G)
    # any leftover green cast at the matte edge
    edge = (al[..., 0] > .02) & (al[..., 0] < .98)
    o1 = out[..., 1]; o1[edge] = np.minimum(o1[edge], ((out[..., 0] + out[..., 2]) / 2 + 25)[edge])
    enc.stdin.write(np.clip(out, 0, 255).astype(np.uint8).tobytes())
    if i in (0, 60, 120, 175): cv2.imwrite(f'ph_chk_{i}.jpg', out[::2, ::2])
enc.stdin.close(); enc.wait(); print('ok', len(app))
