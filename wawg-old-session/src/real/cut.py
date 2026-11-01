"""cut.py name src start dur cx speed z0 z1 : stock clip -> 1080x1920 30fps with slow push + handheld drift"""
import sys, subprocess, json, numpy as np, cv2, math
n, src, ss, d, cx = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
sp, z0, z1 = float(sys.argv[6]), float(sys.argv[7]), float(sys.argv[8])
p = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'json', f'stock/{src}.mov']))['streams'][0]
W, H = p['width'], p['height']
crop = ''
if W > H:
    cw = H * 9 // 16; x = min(max(cx - cw // 2, 0), W - cw); crop = f'crop={cw}:{H}:{x}:0,'
BW, BH = 1188, 2112
N = round(d * 30)
dec = subprocess.Popen(['ffmpeg', '-nostdin', '-loglevel', 'error', '-ss', str(ss), '-t', str(d * sp + .3), '-i', f'stock/{src}.mov', '-an',
    '-vf', f'setpts=(PTS-STARTPTS)/{sp},{crop}scale={BW}:{BH}:flags=lanczos,fps=30', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '1080x1920', '-r', '30', '-i', '-',
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '14', '-pix_fmt', 'yuv420p', f'seg/{n}.mp4'], stdin=subprocess.PIPE)
last = None
for i in range(N):
    buf = dec.stdout.read(BW * BH * 3)
    if len(buf) == BW * BH * 3: last = np.frombuffer(buf, np.uint8).reshape(BH, BW, 3)
    t = i / 30; k = t / d; e = k * k * (3 - 2 * k) * .35 + k * .65
    sc = (z0 + (z1 - z0) * e)  # 1.0 = source (1.1x of frame) fills with 10% margin for drift
    dx = 7 * math.sin(t * 1.7) + 4 * math.sin(t * 3.3 + .5); dy = 6 * math.sin(t * 1.3 + 1) + 3 * math.sin(t * 2.9)
    M = np.float32([[sc, 0, 540 - sc * BW / 2 + dx], [0, sc, 960 - sc * BH / 2 + dy]])
    out = cv2.warpAffine(last, M, (1080, 1920), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
    enc.stdin.write(out.tobytes())
enc.stdin.close(); enc.wait(); dec.kill()
print(n, N)
