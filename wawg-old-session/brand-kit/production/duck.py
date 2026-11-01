"""duck.py <bed.wav> <vo.wav> <out.wav> [duck_db]: lower the bed while the voice speaks, then add the voice."""
import sys, numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
bed_p, vo_p, out_p = sys.argv[1:4]; duck_db = float(sys.argv[4]) if len(sys.argv) > 4 else 12
SR = 48000
sr, b = wavfile.read(bed_p); b = b.astype(np.float32) / 32768
if b.ndim == 1: b = np.stack([b, b], 1)
if sr != SR: b = resample_poly(b, SR, sr, axis=0)
_, v = wavfile.read(vo_p); v = v.astype(np.float32) / 32768
n = min(len(b), len(v)); b, v = b[:n], v[:n]
# voice activity from a 20 ms RMS envelope, held across short gaps between words
hop = 960; frames = -(-len(v) // hop)
rms = np.array([np.sqrt((v[i*hop:(i+1)*hop] ** 2).mean() + 1e-12) for i in range(frames)])
act = (rms > 10 ** (-40 / 20)).astype(float)
hold = 15  # 300 ms
for i in range(frames):
    if act[i]: act[i:i + hold] = np.maximum(act[i:i + hold], 0.999)
# smooth: 60 ms attack (ramp starts slightly before speech), 350 ms release
g = np.zeros(frames); a_up, a_dn = 1 - np.exp(-1 / 3), 1 - np.exp(-1 / 17.5)
lead = np.roll(act, -3); lead[-3:] = act[-3:]
for i in range(frames):
    prev = g[i - 1] if i else 0; tgt = max(act[i], lead[i])
    g[i] = prev + (tgt - prev) * (a_up if tgt > prev else a_dn)
gain = 10 ** (-duck_db * g / 20)
gain = np.interp(np.arange(n), np.arange(frames) * hop + hop / 2, gain)
out = b * gain[:, None] + 1.5 * v[:, None]
wavfile.write(out_p, SR, (np.clip(out, -1, 1) * 32767).astype(np.int16))
db = lambda x: 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
sp = np.repeat(act, hop)[:n] > .5
print(f'voice-over-music while speaking: {db(1.5*v[sp]) - db((b*gain[:,None]).mean(1)[sp]):.1f} dB')
