"""Place voiceover lines on a timeline: python3 mixvo.py <vo_dir> <out.wav> <duration> id:start ..."""
import sys, numpy as np
from scipy.io import wavfile
vo, out, dur = sys.argv[1], sys.argv[2], float(sys.argv[3])
SR = 48000
track = np.zeros(int(dur * SR), np.float32)
for item in sys.argv[4:]:
    name, t0 = item.split(':'); t0 = float(t0)
    sr, x = wavfile.read(f'{vo}/{name}.wav'); assert sr == SR
    x = x.astype(np.float32) / 32768
    i = int(t0 * SR); x = x[:len(track) - i]
    if i + len(x) > len(track) or len(x) == 0: raise SystemExit(f'{name} does not fit')
    track[i:i + len(x)] += x
    print(f'{name}: {t0:.2f}-{t0 + len(x) / SR:.2f}')
wavfile.write(out, SR, (np.clip(track, -1, 1) * 32767).astype(np.int16))
