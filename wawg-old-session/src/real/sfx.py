import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
SR = 48000; N = 32 * SR; rng = np.random.default_rng(5)
out = np.zeros((N, 2))
def ld(n):
    sr, a = wavfile.read(f'sfx/{n}.wav'); return a.astype(float) / 32768
def put(x, t, g):
    i = int(t * SR); x = x[:N - i] * g; out[i:i + len(x)] += x
bp = lambda x, lo, hi: sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x, axis=0)
lp = lambda x, f: sosfilt(butter(2, f, 'low', fs=SR, output='sos'), x, axis=0)
def env(n, a, r):
    tl = np.arange(n) / SR; d = n / SR
    return (np.minimum(1, tl / a) * np.minimum(1, (d - tl) / r))[:, None]
# room tone on the sofa, city at night under the walk
n = int(3.3 * SR); put(lp(rng.standard_normal((n, 2)), 300) * env(n, .3, .2) * .05, 0, 1)
n = int(5.9 * SR); put(bp(rng.standard_normal((n, 2)), 120, 1500) * env(n, .2, .4) * .06, 9.15, 1)
# crowd under the drop (stereo, slow swell)
n = int(8.1 * SR); tl = np.arange(n) / SR
cr = bp(rng.standard_normal((n, 2)), 300, 3000) * (.6 + .4 * np.abs(lp(rng.standard_normal((n, 1)), 2) * 8).clip(0, 1))
cr *= env(n, .25, .9) * (1 + .8 * np.exp(-((tl - .4) / .5) ** 2))[:, None]
put(cr * .09, 14.9, 1)
put(ld('riser-cine'), 15.0 - 4.86, .55)
put(ld('impact-deep-whoosh'), 14.97, .6)
put(ld('ui-select-click'), 9.12, .8)
put(ld('air-woosh-quick'), 5.1, .35)
put(ld('shimmer-sparkle-sweep'), 26.95, .35)
wavfile.write('sfx.wav', SR, (out * 32767).clip(-32768, 32767).astype(np.int16))
print('peak', np.abs(out).max())
