"""Original 40s melodic-house score + UI sound effects for the WAWG ad (120 BPM, synthesized, no samples)."""
import sys
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 44100
DUR = 40.0
N = int(SR * DUR)
BEAT = 0.5
rng = np.random.default_rng(7)

def mf(m):
    return 440.0 * 2 ** ((m - 69) / 12)

def lp(x, f, order=2):
    return sosfilt(butter(order, f, 'low', fs=SR, output='sos'), x)

def hp(x, f, order=2):
    return sosfilt(butter(order, f, 'high', fs=SR, output='sos'), x)

def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], 'band', fs=SR, output='sos'), x)

def saw(freq, n, phase=0.0):
    t = np.arange(n) / SR
    return 2 * np.mod(freq * t + phase, 1.0) - 1

def env_adsr(n, a, d, s, r):
    e = np.ones(n) * s
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na = min(na, n); e[:na] = np.linspace(0, 1, na)
    nd = min(nd, n - na); e[na:na + nd] = np.linspace(1, s, nd)
    if nr > 0 and nr < n:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e

L = np.zeros(N); R = np.zeros(N)

def add(sig, t0, gain=1.0, pan=0.0, bufL=None, bufR=None):
    bufL = L if bufL is None else bufL
    bufR = R if bufR is None else bufR
    i = int(t0 * SR)
    if i >= N:
        return
    if i < 0:
        sig = sig[-i:]; i = 0
    sig = sig[:N - i]
    gl = gain * np.sqrt((1 - pan) / 2); gr = gain * np.sqrt((1 + pan) / 2)
    bufL[i:i + len(sig)] += sig * gl
    bufR[i:i + len(sig)] += sig * gr

# chord progression: Am F C G, one per bar (2 s)
PROG = [[57, 60, 64, 69], [53, 57, 60, 65], [55, 60, 64, 67], [55, 59, 62, 67]]
ROOT = [33, 29, 36, 31]
def bar_of(t):
    return int(t // 2)

# ---------------- drums ----------------
def kick(g=1.0):
    n = int(.42 * SR); t = np.arange(n) / SR
    f = 46 + 110 * np.exp(-t * 32)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t * 7.5)
    click = hp(rng.standard_normal(n), 3000) * np.exp(-t * 300) * .25
    return (x + click) * g

def clap():
    n = int(.3 * SR); t = np.arange(n) / SR
    nz = bp(rng.standard_normal(n), 900, 5000)
    e = np.exp(-t * 18)
    for d in (0.0, .011, .022):
        e = e + np.where(t >= d, np.exp(-(t - d) * 120), 0) * .6
    return nz * e * .5

def hat(open_=False):
    n = int((.22 if open_ else .05) * SR); t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7000) * np.exp(-t * (14 if open_ else 90)) * .35

def shaker():
    n = int(.08 * SR); t = np.arange(n) / SR
    return bp(rng.standard_normal(n), 5000, 11000) * np.sin(np.pi * t / t[-1]) ** 2 * .2

D_L = np.zeros(N); D_R = np.zeros(N)
kicks = []
for i in range(int(DUR / BEAT)):
    t = i * BEAT
    if t >= 36:  # stop for the riser / final hit
        break
    if 15.5 <= t < 16:  # one-beat gap before the drop
        continue
    if t < 8:
        g = .45 if t >= 2 else .3
    elif t < 16:
        g = .8
    else:
        g = 1.0
    add(kick(g), t, 1.0, 0, D_L, D_R); kicks.append(t)
    if t >= 12 and (i % 2 == 1) and not (15.5 <= t < 16):
        add(clap(), t, .8 if t < 16 else 1.0, 0, D_L, D_R)
    off = t + BEAT / 2
    if t >= 4:
        add(hat(open_=t >= 16), off, .55 if t < 16 else .7, .25, D_L, D_R)
    if t >= 16:
        for s in (0, 1, 3):
            add(hat(), t + s * BEAT / 4, .35, -.3, D_L, D_R)
    elif t >= 2:
        add(shaker(), off, .6, -.2, D_L, D_R)

# snare roll 14-15.5 accelerating
for k in range(24):
    t = 14 + 1.5 * (1 - (1 - k / 24) ** 1.6)
    add(clap(), t, .25 + .5 * k / 24, 0, D_L, D_R)

# ---------------- sidechain envelope ----------------
sc = np.ones(N)
tt = np.arange(N) / SR
for kt in kicks:
    if kt >= 8:
        i = int(kt * SR); m = min(N, i + int(.45 * SR))
        depth = .65 if kt >= 16 else .4
        sc[i:m] = np.minimum(sc[i:m], 1 - depth * np.exp(-(tt[i:m] - kt) / .11))

# ---------------- pads ----------------
P_L = np.zeros(N); P_R = np.zeros(N)
for b in range(18):  # up to 36 s
    t0 = b * 2.0; n = int(2.05 * SR)
    for m in PROG[b % 4]:
        for side, buf in ((0, P_L), (1, P_R)):
            x = np.zeros(n)
            for d in (-.12, -.06, 0, .07, .13):
                x += saw(mf(m) * 2 ** ((d + (.03 if side else -.03)) / 12), n, rng.random())
            x *= env_adsr(n, .25 if b < 4 else .05, .3, .8, .15) / 5
            add(x, t0, .16, 0, buf, buf)
# brightness: dark intro opening up, full from 16s
cut_dark = lp(P_L, 700), lp(P_R, 700)
cut_bright = lp(P_L, 4200), lp(P_R, 4200)
mix = np.clip((tt - 1) / 15, 0, 1) ** 1.5
P_L = cut_dark[0] * (1 - mix) + cut_bright[0] * mix
P_R = cut_dark[1] * (1 - mix) + cut_bright[1] * mix

# ---------------- bass (offbeat house bass from 8s) ----------------
B = np.zeros(N)
for i in range(int(8 / .25), int(36 / .25)):
    t = i * .25
    if 15.5 <= t < 16:
        continue
    pos = i % 4
    if t < 16 and pos != 2:
        continue
    if t >= 16 and pos not in (2, 3):
        continue
    root = ROOT[bar_of(t) % 4]
    m = root + (12 if (t >= 16 and pos == 3) else 0)
    n = int(.22 * SR)
    x = saw(mf(m), n) * .6 + np.sin(2 * np.pi * mf(m) * np.arange(n) / SR)
    x = lp(x, 900) * env_adsr(n, .005, .08, .6, .05)
    add(x, t, .38, 0, B, B)

# ---------------- pluck arp (from 8s) ----------------
A_L = np.zeros(N); A_R = np.zeros(N)
pat = [0, 1, 2, 3, 2, 1, 3, 2]
for i in range(int(8 / .25), int(36 / .25)):
    t = i * .25
    if 15.5 <= t < 16:
        continue
    ch = PROG[bar_of(t) % 4]
    m = ch[pat[i % 8]] + 12
    n = int(.3 * SR); tl = np.arange(n) / SR
    x = (saw(mf(m), n) + saw(mf(m) * 1.004, n)) * .5
    x = lp(x, 2600) * np.exp(-tl * 14)
    pan = .45 if i % 2 else -.45
    add(x, t, .2 if t < 16 else .24, pan, A_L, A_R)

# ---------------- lead melody 28-36 ----------------
LD = np.zeros(N)
mel = {14: [72, 76, None, 79, 76, None, 72, 74], 15: [71, 74, None, 79, 74, None, 71, 74],
       16: [72, 76, None, 81, 76, None, 72, 76], 17: [72, 77, None, 81, 79, 77, None, 76]}
for b, notes in mel.items():
    for k, m in enumerate(notes):
        if m is None:
            continue
        t = b * 2 + k * .25
        n = int(.45 * SR)
        x = sum(saw(mf(m) * dd, n, rng.random()) for dd in (1, 1.006, .994)) / 3
        x = lp(x, 3800) * env_adsr(n, .01, .15, .55, .12)
        add(x, t, .3, 0, LD, LD)
    # softer echo of the motif in the second half of the bar
    for k, m in enumerate(notes):
        if m is None:
            continue
        n = int(.2 * SR)
        x = lp(saw(mf(m + 12), n), 3000) * env_adsr(n, .005, .08, .4, .05)
        add(x, b * 2 + 1 + k * .125, .07, 0, LD, LD)

# ---------------- risers ----------------
FX_L = np.zeros(N); FX_R = np.zeros(N)
def riser(dur, f0=300, f1=6000, g=.5):
    n = int(dur * SR); tl = np.arange(n) / SR
    nz = rng.standard_normal(n)
    out = np.zeros(n); step = 1024
    for s in range(0, n, step):
        k = s / n
        fc = f0 * (f1 / f0) ** k
        seg = nz[s:s + step]
        out[s:s + step] = bp(seg, fc * .7, min(fc * 1.4, SR / 2 - 100), 1)
    sweep = np.sin(2 * np.pi * np.cumsum(200 * (8 ** (tl / dur))) / SR) * .25
    return (out + sweep) * (tl / dur) ** 2 * g
add(riser(2.0), 14.0, .9, 0, FX_L, FX_R)
add(riser(1.4, 400, 9000), 36.0, 2.2, 0, FX_L, FX_R)
# reverse cymbal into the drop
add(riser(.9, 3000, 12000, .4), 15.1, .8, 0, FX_L, FX_R)

# ---------------- impacts ----------------
def impact(dur=2.5, g=1.0):
    n = int(dur * SR); tl = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(30 + 60 * np.exp(-tl * 6)) / SR) * np.exp(-tl * 2.2)
    crash = hp(rng.standard_normal(n), 4000) * np.exp(-tl * 2.5) * .35
    return (boom + crash) * g
add(impact(2.5, .9), 16.0, 1.0, 0, FX_L, FX_R)

# final chord at 37.5 (C major add9), long tail
FC_L = np.zeros(N); FC_R = np.zeros(N)
n = int(2.5 * SR); tl = np.arange(n) / SR
for m in (36, 48, 55, 60, 64, 67, 74):
    for side, buf in ((-1, FC_L), (1, FC_R)):
        x = sum(saw(mf(m) * 2 ** ((d + side * .04) / 12), n, rng.random()) for d in (-.14, -.07, 0, .07, .14)) / 5
        x = lp(x, 5200) * np.exp(-tl * 1.1) * np.minimum(1, tl / .01)
        add(x, 37.5, .2, 0, buf, buf)
add(impact(2.5, 1.2), 37.5, 1.0, 0, FX_L, FX_R)

# ---------------- UI / scene sound effects ----------------
S_L = np.zeros(N); S_R = np.zeros(N)
def bell(freqs, dur=.8, decay=6, g=.5):
    n = int(dur * SR); tl = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * tl) * a for f, a in freqs)
    return x * np.exp(-tl * decay) * np.minimum(1, tl / .003) * g
def notif():
    a = bell([(1318.5, 1), (2637, .3)], .5, 9, .45)
    b = bell([(1975.5, 1), (3951, .25)], .7, 7, .45)
    out = np.zeros(int(.9 * SR)); out[:len(a)] += a; o = int(.12 * SR); out[o:o + len(b)] += b
    return out
def ping():
    return bell([(1760, 1), (2637, .6), (3520, .35), (5274, .15)], 1.2, 4.5, .55)
def beep():
    n = int(.16 * SR); tl = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * 2093 * tl)) * .25
    return lp(x, 6000) * np.minimum(1, tl / .004) * np.minimum(1, (tl[-1] - tl) / .01)
def tap():
    n = int(.04 * SR); tl = np.arange(n) / SR
    return (bp(rng.standard_normal(n), 1500, 6000) * np.exp(-tl * 160) + np.sin(2 * np.pi * 900 * tl) * np.exp(-tl * 120)) * .5
def whoosh(dur=.5, up=True):
    n = int(dur * SR); tl = np.arange(n) / SR; nz = rng.standard_normal(n); out = np.zeros(n)
    for s in range(0, n, 1024):
        k = s / n; k = k if up else 1 - k
        fc = 400 * (12 ** k); out[s:s + 1024] = bp(nz[s:s + 1024], fc * .6, fc * 1.6, 1)
    return out * np.sin(np.pi * tl / dur) ** 2 * .7
def pop():
    n = int(.12 * SR); tl = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(400 + 900 * tl / tl[-1]) / SR) * np.exp(-tl * 30) * .5
def sparkle(dur=1.2):
    out = np.zeros(int(dur * SR))
    for k in range(26):
        t = rng.random() * dur * .8; f = 2500 + rng.random() * 4500
        b = bell([(f, 1)], .25, 25, .12); i = int(t * SR); out[i:i + len(b)] += b[:len(out) - i]
    return out
def crackle(dur=1.0, dens=60):
    out = np.zeros(int(dur * SR))
    for k in range(int(dens * dur)):
        i = int(rng.random() * (len(out) - 400)); out[i:i + 300] += hp(rng.standard_normal(300), 2500) * np.exp(-np.arange(300) / 40) * (rng.random() * .5)
    return out * np.linspace(1, .2, len(out))
def firework():
    n = int(1.6 * SR); tl = np.arange(n) / SR
    boom = lp(rng.standard_normal(n), 400) * np.exp(-tl * 6) * 1.4
    c = np.pad(crackle(1.2), (int(.1 * SR), 0)); out = boom.copy(); out[:min(n, len(c))] += c[:n]; return out
def whistle(dur=.35):
    n = int(dur * SR); tl = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(1200 + 1800 * tl / dur) / SR) * .08 * np.sin(np.pi * tl / dur)
def crowd(dur, swell_at=None):
    n = int(dur * SR); tl = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 250, 2600)
    am = .6 + .4 * np.abs(lp(rng.standard_normal(n), 3))
    e = np.minimum(1, tl / .8)
    if swell_at is not None:
        e = e * (1 + 1.6 * np.exp(-((tl - swell_at) / .7) ** 2))
    return x * am * e * .25
def typing(dur=3.0):
    out = np.zeros(int(dur * SR)); t = .3
    while t < dur - .1:
        b = tap() * .35; i = int(t * SR); out[i:i + len(b)] += b; t += .09 + rng.random() * .25
    return out
def street(dur=4.0):
    n = int(dur * SR); tl = np.arange(n) / SR
    return lp(rng.standard_normal(n), 350) * .12 * np.minimum(1, (dur - tl) / .5)

add(street(4.2), 0, 1, 0, S_L, S_R)
add(typing(3.2), .2, .8, .1, S_L, S_R)
add(whoosh(.45), 3.8, .9, 0, S_L, S_R)                      # app opens
add(bell([(784, 1), (1568, .4)], 1.0, 4, .3), 4.3, 1, 0, S_L, S_R)  # logo chime
for i in range(6):
    add(bell([(2093 + i * 120, 1)], .3, 14, .25), 5.1 + i * .22, 1, (i - 2.5) / 4, S_L, S_R)  # map pins
add(tap(), 8.95, .9, .2, S_L, S_R)   # chips
add(whoosh(.4), 9.0, .5, 0, S_L, S_R)                       # list reshuffle
add(tap(), 12.9, .9, 0, S_L, S_R); add(pop(), 12.95, .9, 0, S_L, S_R)  # follow + heart
add(notif(), 14.0, 1, 0, S_L, S_R)                          # notification
add(tap(), 16.75, .9, 0, S_L, S_R)                          # pay button
add(whoosh(.35), 17.0, .5, 0, S_L, S_R)                     # sheet up
add(ping(), 19.0, 1, 0, S_L, S_R)                           # payment approved
add(whoosh(.35), 19.55, .45, 0, S_L, S_R)                   # receipt slides in
add(notif(), 21.65, .9, 0, S_L, S_R)                           # coupon pops
add(sparkle(1.3), 22.0, 1, 0, S_L, S_R)                     # confetti
add(notif(), 26.0, 1, 0, S_L, S_R)                          # reminder
add(notif(), 26.7, .6, 0, S_L, S_R)
add(beep(), 30.0, 1, 0, S_L, S_R)                           # scanner beep
add(bell([(1046.5, 1), (1568, .6)], .6, 7, .3), 30.18, 1, 0, S_L, S_R)
add(crowd(2.1), 30.0, .7, 0, S_L, S_R)                      # club noise after entry
for i in range(5):
    add(bell([(1318.5 * 2 ** (i * 2 / 12), 1), (2637 * 2 ** (i * 2 / 12), .3)], .5, 10, .3), 32.6 + i * .4, 1, (i - 2) / 4, S_L, S_R)  # stars
add(sparkle(.8), 34.9, .7, 0, S_L, S_R)                     # likes
add(crowd(4.0, swell_at=1.6), 36.0, 1.2, 0, S_L, S_R)       # festival crowd
for t0 in (.25, .6, 1.5, 1.62, 1.75, 2.2, 2.45, 2.9, 3.2, 3.4):
    add(whistle(), 36 + t0 - .35, 1, rng.uniform(-.5, .5), S_L, S_R)
    add(firework(), 36 + t0, .9 if t0 not in (1.5,) else 1.2, rng.uniform(-.6, .6), S_L, S_R)

# ---------------- mix ----------------
def rev(x, dur=2.2, seed=1):
    r = np.random.default_rng(seed); n = int(dur * SR); tl = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-tl * 3.2); ir = lp(ir, 6000); ir /= np.sqrt(np.sum(ir ** 2))
    return fftconvolve(x, ir)[:len(x)]

music_L = D_L + B + (P_L + A_L + LD) * sc + FX_L + FC_L
music_R = D_R + B + (P_R + A_R + LD) * sc + FX_R + FC_R
send_L = P_L * sc * .5 + A_L * .6 + LD * .7 + FC_L * .6
send_R = P_R * sc * .5 + A_R * .6 + LD * .7 + FC_R * .6
music_L += rev(send_L, seed=1) * .35; music_R += rev(send_R, seed=2) * .35
# short silence after the final riser: 37.25-37.5
gate = np.ones(N); i0, i1 = int(37.28 * SR), int(37.5 * SR); gate[i0:i1] = 0; gate[i0 - 300:i0] = np.linspace(1, 0, 300)
music_L *= gate; music_R *= gate
# fade music tail to 40
fo = int(.4 * SR); music_L[-fo:] *= np.linspace(1, 0, fo); music_R[-fo:] *= np.linspace(1, 0, fo)

sfx_L = S_L + rev(S_L, 1.2, 3) * .15; sfx_R = S_R + rev(S_R, 1.2, 4) * .15
sfx_L[-fo:] *= np.linspace(1, 0, fo); sfx_R[-fo:] *= np.linspace(1, 0, fo)

def save(name, l, r, peak=.9):
    st = np.stack([l, r], 1); st = np.tanh(st * 1.2) / np.tanh(1.2)
    st *= peak / (np.max(np.abs(st)) + 1e-9)
    wavfile.write(name, SR, (st * 32767).astype(np.int16))

out = sys.argv[1] if len(sys.argv) > 1 else '.'
save(f'{out}/music.wav', music_L, music_R)
save(f'{out}/sfx.wav', sfx_L, sfx_R)
print('ok')
