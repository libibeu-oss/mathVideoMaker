"""Punches, card whooshes and collage ticks for the 32s spot."""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
SR = 48000; N = 32 * SR; rng = np.random.default_rng(9); out = np.zeros(N)
bp = lambda x, a, b: sosfilt(butter(2, [a, b], 'band', fs=SR, output='sos'), x)
def put(x, t, g=1): i = int(t * SR); x = x[:N - i]; out[i:i + len(x)] += x * g
def punch():
    n = int(.3 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(60 + 160 * np.exp(-t * 30)) / SR) * np.exp(-t * 14) + bp(rng.standard_normal(n), 800, 4000) * np.exp(-t * 40) * .4
def whoosh(d=.4):
    n = int(d * SR); t = np.arange(n) / SR; nz = rng.standard_normal(n); o = np.zeros(n)
    for s in range(0, n, 1024): fc = 500 * 10 ** (s / n); o[s:s + 1024] = bp(nz[s:s + 1024], fc * .6, fc * 1.6)
    return o * np.sin(np.pi * t / d) ** 2 * .5
def tick(f):
    t = np.arange(int(.12 * SR)) / SR; return np.sin(2 * np.pi * f * t) * np.exp(-t * 35) * .3
for k in range(6):
    s = 2 + 4 * k; put(punch(), s + .5, .8); put(whoosh(.35), s + 1.85, .7)
for i in range(6): put(tick(880 * 2 ** (i / 6)), 26 + i * .13)
wavfile.write('m7/sfx7.wav', SR, (np.clip(out, -1, 1) * 32767).astype(np.int16)); print('ok')
