"""Scene sounds for the Apple-style spot (timed to apple.js / ad6 MAP)."""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
SR = 48000; N = 40 * SR; rng = np.random.default_rng(11)
out = np.zeros((N, 2), np.float32)
bp = lambda x, lo, hi: sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)
lp = lambda x, f: sosfilt(butter(2, f, 'low', fs=SR, output='sos'), x)
hp = lambda x, f: sosfilt(butter(2, f, 'high', fs=SR, output='sos'), x)
def put(x, t, g=1.0, pan=0.0):
    i = int(t * SR); x = x[:N - i] * g
    out[i:i + len(x), 0] += x * np.sqrt((1 - pan) / 2); out[i:i + len(x), 1] += x * np.sqrt((1 + pan) / 2)
def bell(fs, dur, dec, g):
    tl = np.arange(int(dur * SR)) / SR
    return sum(np.sin(2 * np.pi * f * tl) * a for f, a in fs) * np.exp(-tl * dec) * np.minimum(1, tl / .003) * g
def tap():
    n = int(.04 * SR); tl = np.arange(n) / SR
    return (bp(rng.standard_normal(n), 1500, 6000) * np.exp(-tl * 160) + np.sin(2 * np.pi * 900 * tl) * np.exp(-tl * 120)) * .5
def whoosh(dur):
    n = int(dur * SR); tl = np.arange(n) / SR; nz = rng.standard_normal(n); o = np.zeros(n)
    for s in range(0, n, 1024):
        fc = 400 * 12 ** (s / n); o[s:s + 1024] = bp(nz[s:s + 1024], fc * .6, fc * 1.6)
    return o * np.sin(np.pi * tl / dur) ** 2 * .6
def notif():
    a = bell([(1318.5, 1), (2637, .3)], .5, 9, .4); b = bell([(1975.5, 1)], .7, 7, .4)
    o = np.zeros(int(.9 * SR)); o[:len(a)] += a; k = int(.12 * SR); o[k:k + len(b)] += b; return o
def crowd(dur, swell=None):
    n = int(dur * SR); tl = np.arange(n) / SR
    e = np.minimum(1, tl / .8) * np.minimum(1, (dur - tl) / .6)
    if swell is not None: e = e * (1 + 1.5 * np.exp(-((tl - swell) / .7) ** 2))
    return bp(rng.standard_normal(n), 250, 2600) * (.6 + .4 * np.abs(lp(rng.standard_normal(n), 3))) * e * .22
def firework():
    n = int(1.6 * SR); tl = np.arange(n) / SR
    o = lp(rng.standard_normal(n), 400) * np.exp(-tl * 6) * 1.3
    for k in range(70):
        i = int(.1 * SR + rng.random() * (n - .2 * SR)); o[i:i + 300] += hp(rng.standard_normal(300), 2500) * np.exp(-np.arange(300) / 40) * rng.random() * .4
    return o
put(lp(rng.standard_normal(10 * SR), 300) * .06 * np.minimum(1, np.arange(10 * SR) / SR), 0)     # distant city under the opening
put(tap(), 8.85, .9); put(whoosh(.6), 9.4, .7)                                                      # app icon tapped and opened
put(tap(), 16.15, .8, .2); put(whoosh(.35), 16.2, .4)                                               # vibe chip
put(tap(), 17.53, .8, -.2); put(bell([(660, 1), (990, .5)], .2, 25, .35), 17.56)                    # follow
put(bell([(1760, 1), (2637, .6), (3520, .35)], 1.1, 4.5, .45), 19.37)                               # payment approved
for k in range(22): put(bell([(2500 + rng.random() * 4500, 1)], .25, 25, .1), 20.5 + rng.random())  # confetti
put(notif(), 21.43)                                                                                 # reminder
n = int(.16 * SR); tl = np.arange(n) / SR; put(lp(np.sign(np.sin(2 * np.pi * 2093 * tl)) * .22, 6000), 23.27)  # scanner beep
put(crowd(6.2, swell=3.5), 24.0, 1.0)                                                               # the crowd
for i in range(5): put(bell([(1318.5 * 2 ** (i * 2 / 12), 1)], .5, 10, .28), 30.47 + i * .38, 1, (i - 2) / 4)  # stars
for t0 in (36.67, 36.83, 37.0, 37.6, 37.93, 38.53, 38.93, 39.2): put(firework(), t0, .8, rng.uniform(-.6, .6))
put(crowd(3.3, swell=1.0), 36.67, 1.1)
fo = int(.4 * SR); out[-fo:] *= np.linspace(1, 0, fo)[:, None]
wavfile.write('m6/sfx6.wav', SR, (np.clip(out, -1, 1) * 32767).astype(np.int16)); print('ok')
