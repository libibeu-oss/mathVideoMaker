"""Music + sound effects bed for the 30s group-chat video, cut from the 40s stems."""
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
SR = 48000
def load(p):
    sr, x = wavfile.read(p); x = x.astype(np.float32) / 32768
    return resample_poly(x, SR, sr, axis=0) if sr != SR else x
music, sfx = load('wawg2/music.wav'), load('wawg2/sfx.wav')
N = 30 * SR
def remap(src, segs, fade=0.01):
    out = np.zeros((N, 2), np.float32)
    for a, b, s in segs:
        i, j, k = int(a * SR), int(b * SR), int(s * SR)
        seg = src[k:k + (j - i)].copy(); f = int(fade * SR)
        seg[:f] *= np.linspace(0, 1, f)[:, None]; seg[-f:] *= np.linspace(1, 0, f)[:, None]
        out[i:i + len(seg)] += seg
    return out
m = remap(music, [(0, 13.5, 2.5), (13.5, 24, 16), (24, 30, 34)])
s = remap(sfx, [(13.5, 17.5, 4), (17.5, 19.0, 8.6), (19.0, 20.2, 18.2), (20.2, 21.5, 29.4), (26.9, 30, 36.9)])
t = np.arange(int(.5 * SR)) / SR
def tone(fs, dur, dec, g):
    n = int(dur * SR); tl = np.arange(n) / SR
    return sum(np.sin(2 * np.pi * f * tl) * a for f, a in fs) * np.exp(-tl * dec) * np.minimum(1, tl / .003) * g
def put(x, t0, g=1.0):
    i = int(t0 * SR); x = x[:N - i]; s[i:i + len(x)] += (x * g)[:, None]
pop = tone([(880, 1), (1320, .5)], .18, 28, .35); send = tone([(1175, 1), (1760, .4)], .2, 24, .3)
for t0, mine in [(0.3, 1), (3.9, 0), (8.5, 0), (11.1, 1), (12.1, 1), (21.6, 0), (25.55, 0), (26.25, 1)]:
    put(send if mine else pop, t0)
put(tone([(1568, 1), (2349, .5)], .9, 5, .35), 12.2)                    # link preview chime
tap = np.random.default_rng(3).standard_normal(int(.04 * SR)) * np.exp(-np.arange(int(.04 * SR)) / SR * 150) * .3
put(tap, 13.15)
put(tone([(1760, 1), (2637, .6), (3520, .3)], 1.0, 5, .4), 22.6)           # ticket arrives
out = m + .8 * s
wavfile.write('vo/bed_chat.wav', SR, (np.clip(out, -1, 1) * 32767).astype(np.int16))
print('ok')
