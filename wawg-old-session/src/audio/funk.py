"""32s disco-funk score for "כל אחד והלאן שלו" (120 BPM, synthesized)."""
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile
SR = 48000; DUR = 32; N = DUR * SR; rng = np.random.default_rng(5)
L = np.zeros(N); R = np.zeros(N)
lp = lambda x, f: sosfilt(butter(2, f, 'low', fs=SR, output='sos'), x)
hp = lambda x, f: sosfilt(butter(2, f, 'high', fs=SR, output='sos'), x)
bp = lambda x, a, b: sosfilt(butter(2, [a, b], 'band', fs=SR, output='sos'), x)
mf = lambda m: 440 * 2 ** ((m - 69) / 12)
def saw(f, n): t = np.arange(n) / SR; return 2 * np.mod(f * t + rng.random(), 1) - 1
def add(x, t, g=1, pan=0):
    i = int(t * SR)
    if i >= N: return
    x = x[:N - i] * g; L[i:i + len(x)] += x * np.sqrt((1 - pan) / 2); R[i:i + len(x)] += x * np.sqrt((1 + pan) / 2)
def env(n, a, d):
    t = np.arange(n) / SR; return np.minimum(1, t / a) * np.exp(-t * d)
def kick():
    n = int(.35 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(50 + 120 * np.exp(-t * 35)) / SR) * np.exp(-t * 9)
def clap():
    n = int(.25 * SR); t = np.arange(n) / SR; e = np.exp(-t * 20)
    for d in (0, .01, .02): e = e + np.where(t >= d, np.exp(-(t - d) * 140), 0) * .5
    return bp(rng.standard_normal(n), 1000, 5000) * e * .5
def hat(o=False):
    n = int((.18 if o else .04) * SR); t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7500) * np.exp(-t * (16 if o else 100)) * .3
def crash():
    n = int(1.6 * SR); t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 3500) * np.exp(-t * 2.4) * .35
CH = [[57, 60, 64, 67], [50, 54, 57, 60, 64], [53, 57, 60, 64], [52, 56, 59, 62]]   # Am7 D9 Fmaj7 E7
RT = [45, 38, 41, 40]
def stab(ch, dur=.16, g=.12):
    n = int(dur * SR); x = sum(saw(mf(m + 12), n) + saw(mf(m + 12) * 1.005, n) for m in ch) / (2 * len(ch))
    return lp(x, 3500) * env(n, .004, 18) * g * 8
def bassnote(m, dur):
    n = int(dur * SR); x = saw(mf(m), n) * .5 + np.sin(2 * np.pi * mf(m) * np.arange(n) / SR)
    return lp(x, 700) * env(n, .003, 6) * .45
# intro (0-2): three stabs on the words, then a snare fill into the groove
for t0 in (.05, .55, 1.05): add(stab(CH[0], .25), t0, 1.2); add(kick(), t0, .9)
for k in range(8): add(clap(), 1.5 + k * .0625, .25 + .6 * k / 8)
# groove (2-29)
for i in range(int(2 / .5), int(29 / .5)):
    t = i * .5; bar = int((t - 2) // 2) % 4; pos = i % 4
    add(kick(), t, 1.0)
    if pos in (1, 3): add(clap(), t, .9)
    add(hat(True), t + .25, .7, .3)
    for s in (0, .125, .375): add(hat(), t + s + (.02 if s == .125 else 0), .5, -.3)
    # syncopated funk bass
    root = RT[bar]
    for off, oc, d in ((0, 0, .2), (.375, 12, .1), (.75, 0, .2) if pos % 2 == 0 else (.625, 7, .12)):
        if t + off < 29: add(bassnote(root + oc, d), t + off, 1.0)
    # chord stabs on the and-of-2 and on 4
    if pos == 1: add(stab(CH[bar]), t + .25, 1.0, .2)
    if pos == 3: add(stab(CH[bar]), t, .8, -.2)
# a crash on every hard cut, a punch on every answer
for k in range(7): add(crash(), 2 + 4 * k, 1.0)
# button ending: the logo hit at 29.05 with a long final chord
n = int(3 * SR); t = np.arange(n) / SR
fin = sum(saw(mf(m), n) + saw(mf(m) * 1.004, n) for m in (45, 57, 60, 64, 67, 71)) / 12
add(lp(fin, 4500) * np.minimum(1, t / .01) * np.exp(-t * .9), 29.05, 1.4); add(kick(), 29.05, 1.2); add(crash(), 29.05, 1.3)
ir = rng.standard_normal(int(1.5 * SR)) * np.exp(-np.arange(int(1.5 * SR)) / SR * 4); ir = lp(ir, 5000); ir /= np.sqrt((ir ** 2).sum())
L += fftconvolve(L, ir)[:N] * .12; R += fftconvolve(R, ir)[:N] * .12
fo = int(.3 * SR); L[-fo:] *= np.linspace(1, 0, fo); R[-fo:] *= np.linspace(1, 0, fo)
st = np.stack([L, R], 1); st = np.tanh(st * 1.1); st *= .9 / np.abs(st).max()
wavfile.write('m7/music7.wav', SR, (st * 32767).astype(np.int16)); print('ok')
