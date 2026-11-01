"""30s score with a tension/intro section, a dead stop, a drop and a logo hit.
usage: score.py out.wav --stop A B --hit H [--intro tension|filtered] [--key 45]"""
import sys, argparse, numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--stop', nargs=2, type=float); ap.add_argument('--hit', type=float)
ap.add_argument('--intro', default='tension'); ap.add_argument('--key', type=int, default=45); ap.add_argument('--dur', type=float, default=30); ap.add_argument('--seed', type=int, default=3)
a = ap.parse_args(); SR = 48000; N = int(a.dur * SR); rng = np.random.default_rng(a.seed); BEAT = 60 / 124
L = np.zeros(N); R = np.zeros(N)
lp = lambda x, f: sosfilt(butter(2, f, 'low', fs=SR, output='sos'), x)
hp = lambda x, f: sosfilt(butter(2, f, 'high', fs=SR, output='sos'), x)
bp = lambda x, l, h: sosfilt(butter(2, [l, h], 'band', fs=SR, output='sos'), x)
mf = lambda m: 440 * 2 ** ((m - 69) / 12)
def saw(f, n): t = np.arange(n) / SR; return 2 * np.mod(f * t + rng.random(), 1) - 1
def add(x, t, g=1, pan=0, bl=None, br=None):
    bl = L if bl is None else bl; br = R if br is None else br
    i = int(t * SR)
    if i >= N or i < 0: return
    x = x[:N - i] * g; bl[i:i + len(x)] += x * np.sqrt((1 - pan) / 2); br[i:i + len(x)] += x * np.sqrt((1 + pan) / 2)
def kick(g=1):
    n = int(.35 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(48 + 130 * np.exp(-t * 34)) / SR) * np.exp(-t * 8) * g
def clap():
    n = int(.25 * SR); t = np.arange(n) / SR; e = np.exp(-t * 18)
    for d in (0, .01, .021): e = e + np.where(t >= d, np.exp(-(t - d) * 140), 0) * .5
    return bp(rng.standard_normal(n), 900, 5000) * e * .45
def hat(o=False):
    n = int((.2 if o else .04) * SR); t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7500) * np.exp(-t * (14 if o else 100)) * .3
def env(n, a_, d): t = np.arange(n) / SR; return np.minimum(1, t / a_) * np.exp(-t * d)
K = a.key; CH = [[K + 12, K + 15, K + 19], [K + 8, K + 12, K + 15], [K + 10, K + 14, K + 17], [K + 7, K + 11, K + 14]]
s0, s1 = a.stop; drop = s1
# intro
if a.intro == 'tension':
    # accelerating ticks + rising pad + low pulse that speeds up toward the stop
    t = .1; k = 0
    while t < s0:
        add(hat(), t, .9, (k % 2) - .5); add(kick(.35), t, 1) if k % 2 == 0 else None
        t += max(.09, .55 * (1 - t / s0) ** 1.2); k += 1
    n = int(s0 * SR); tl = np.arange(n) / SR
    pad = sum(saw(mf(m) * (1 + .03 * tl / s0), n) for m in (K, K + 7, K + 12)) / 3
    add(lp(pad, 900) * (tl / s0) ** 2 * .35, 0)
else:
    # filtered house groove before the stop
    for i in range(int(s0 / BEAT)):
        t = i * BEAT; add(kick(.7), t); add(hat(True), t + BEAT / 2, .5)
    n = int(s0 * SR); tl = np.arange(n) / SR
    pad = np.zeros(n)
    for b in range(int(s0 / (4 * BEAT)) + 1):
        i0 = int(b * 4 * BEAT * SR); m_ = CH[b % 4]; seg = sum(saw(mf(m), min(n - i0, int(4 * BEAT * SR))) for m in m_) / 3
        if i0 < n: pad[i0:i0 + len(seg)] += seg
    add(lp(pad, 600) * .3, 0)
# riser into the stop
n = int(1.2 * SR); tl = np.arange(n) / SR; nz = rng.standard_normal(n); ris = np.zeros(n)
for s in range(0, n, 1024): fc = 300 * 25 ** (s / n); ris[s:s + 1024] = bp(nz[s:s + 1024], fc * .7, min(fc * 1.4, 20000))
add(ris * (tl / 1.2) ** 2 * .6, s0 - 1.2)
# drop groove from `drop` until the logo hit
D_end = a.hit
i = 0
while drop + i * BEAT < D_end - .02:
    t = drop + i * BEAT; bar = int(i // 4) % 4; pos = i % 4
    add(kick(1), t)
    if pos in (1, 3): add(clap(), t, .9)
    add(hat(True), t + BEAT / 2, .6, .3)
    for s in (0, .25, .75): add(hat(), t + s * BEAT, .45, -.3)
    root = K - 12 + [0, -4, -2, -5][bar]
    for s in (.5, .75):
        n = int(.18 * SR); x = (saw(mf(root + 12 * (s == .75)), n) * .6 + np.sin(2 * np.pi * mf(root) * np.arange(n) / SR)) * env(n, .003, 9)
        add(lp(x, 800) * .5, t + s * BEAT)
    if pos == 0:
        n = int(.22 * SR); st = sum(saw(mf(m + 12), n) for m in CH[bar]) / 3
        add(lp(st, 3200) * env(n, .003, 14) * .5, t + .75 * BEAT, 1, .2)
    i += 1
# crash at the drop, the big hit on the logo
def crash(): n = int(1.8 * SR); t = np.arange(n) / SR; return hp(rng.standard_normal(n), 3500) * np.exp(-t * 2.2) * .4
add(crash(), drop); add(kick(1.2), drop)
n = int((a.dur - a.hit) * SR); tl = np.arange(n) / SR
fin = sum(saw(mf(m), n) + saw(mf(m) * 1.005, n) for m in (K - 12, K, K + 7, K + 12, K + 15, K + 19)) / 12
add(lp(fin, 5000) * np.minimum(1, tl / .01) * np.exp(-tl * 1.0), a.hit, 1.3); add(kick(1.3), a.hit); add(crash(), a.hit, 1.2)
ir = rng.standard_normal(int(1.4 * SR)) * np.exp(-np.arange(int(1.4 * SR)) / SR * 4); ir = lp(ir, 5000); ir /= np.sqrt((ir ** 2).sum())
L += fftconvolve(L, ir)[:N] * .12; R += fftconvolve(R, ir)[:N] * .12
g = np.ones(N); g[int(s0 * SR):int(s1 * SR)] = 0; L *= g; R *= g   # the dead stop
fo = int(.3 * SR); L[-fo:] *= np.linspace(1, 0, fo); R[-fo:] *= np.linspace(1, 0, fo)
st = np.stack([L, R], 1); st = np.tanh(st * 1.1); st *= .9 / np.abs(st).max()
wavfile.write(a.out, SR, (st * 32767).astype(np.int16)); print('ok', a.out)
