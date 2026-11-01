"""Scene sounds for the producers (p) and artists (a) spots."""
import sys, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
SR = 48000; N = 30 * SR; rng = np.random.default_rng(4)
bp = lambda x, a, b: sosfilt(butter(2, [a, b], 'band', fs=SR, output='sos'), x)
def mk():
    return np.zeros(N)
def put(o, x, t, g=1): i = int(t * SR); x = x[:N - i]; o[i:i + len(x)] += x * g
def tone(fs, d, dec, g):
    t = np.arange(int(d * SR)) / SR; return sum(np.sin(2 * np.pi * f * t) * a for f, a in fs) * np.exp(-t * dec) * np.minimum(1, t / .003) * g
def click():
    n = int(.03 * SR); t = np.arange(n) / SR; return bp(rng.standard_normal(n), 2000, 7000) * np.exp(-t * 200) * .35
def thump():
    n = int(.35 * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(55 + 140 * np.exp(-t * 30)) / SR) * np.exp(-t * 12)
ping = lambda: tone([(1568, 1), (2349, .4)], .6, 7, .35)
# producers
p = mk(); NC = 34
for k in range(NC):
    t0 = .25 + 6.2 * (1 - (1 - k / NC) ** .55)
    put(p, tone([(1046 + (k % 5) * 90, 1)], .15, 30, .18), t0)
for i in range(4):
    for j in range(14): put(p, click(), 8.5 + i * .5 + j * .028)
put(p, ping(), 11.0)
for r in range(6):
    for j in range(9): put(p, click(), 12.4 + r * .85 + j * .06, .8)
    put(p, tone([(880, 1), (1320, .5)], .25, 18, .2), 13.3 + r * .85)
put(p, thump(), 23.3, .9)
# artists
a = mk()
for i in range(4): put(a, thump(), .3 + i * .9, .45)
for i in range(6): put(a, tone([(700 + i * 60, 1)], .12, 30, .22), 5.1 + i * .38)
put(a, click(), 10.4, 1.4); put(a, tone([(990, 1), (1480, .4)], .3, 14, .3), 10.45)
for s in np.arange(14.3, 22, 2.62): put(a, tone([(1200, 1)], .35, 10, .12), s)
put(a, tone([(784, 1), (1175, .6), (1568, .4)], .8, 5, .35), 16.4)
put(a, ping(), 22.1); put(a, click(), 23.6, 1.4); put(a, tone([(1318, 1), (1976, .5)], .7, 6, .35), 23.75)
for name, o in (('p', p), ('a', a)):
    wavfile.write(f'm8/sfx_{name}.wav', SR, (np.clip(o, -1, 1) * 32767).astype(np.int16))
print('ok')
