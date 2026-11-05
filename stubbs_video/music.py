"""Original soundtrack + sound design, synthesized from scratch (no samples, no licences needed).
-> assets/music_<FORMAT>.wav

Music: upbeat, confident "contractor promo" groove, 116 BPM, D major (D - Bm - G - A),
plucked-guitar arpeggios (Karplus-Strong), punchy kick/clap, 16th hats, pulsing bass.
SFX: whoosh on every camera push/pull, low impact on hard cuts, crackle when the crack
opens, rain bed while it rains, ice crunches on freezes, impact on the pothole,
sealant hiss, shimmer on logo reveals.
"""
import os
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
from timemap import FORMAT, duration, story_time
from camera import sfx_events

SR = 44100
DUR = duration()
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(3)
BPM = 116
beat = 60 / BPM
bar = 4 * beat

def midi(m):
    return 440 * 2 ** ((m - 69) / 12)

def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)

def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)

def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)

def add(buf, start, x):
    s = int(start * SR)
    if s >= len(buf) or s + len(x) <= 0:
        return
    if s < 0:
        x, s = x[-s:], 0
    n = min(len(x), len(buf) - s)
    buf[s:s + n] += x[:n]

def pluck(freq, dur, bright=0.5, decay=0.996):
    """Karplus-Strong plucked string, vectorized one period at a time."""
    p = max(2, int(SR / freq))
    n = int(dur * SR)
    out = np.zeros(n + p)
    burst = rng.uniform(-1, 1, p)
    burst = lp(burst, 1500 + 6000 * bright)
    out[:p] = burst
    for i in range(p, n + p, p):
        prev = out[i - p:i]
        nxt = 0.5 * (prev + np.roll(prev, 1)) * decay
        out[i:i + p] = nxt[: len(out[i:i + p])]
    x = out[:n]
    x *= np.linspace(1, 0, n) ** 0.5
    return x

# story-time per sample (for arrangement) and helpers to place story events in output time
story = np.interp(t, t[::441], np.array([story_time(x) for x in t[::441]]))

def out_time(st):
    return float(np.interp(st, story, t))

def ramp(a, b, x):
    return np.clip((x - a) / max(b - a, 1e-6), 0, 1)

# ------------------------------------------------------------------ music
CH = [[62, 66, 69], [59, 62, 66], [55, 59, 62], [57, 61, 64]]   # D, Bm, G, A
ROOT = [38, 35, 31, 33]
gtr = np.zeros(N); bass = np.zeros(N); kick = np.zeros(N); clap = np.zeros(N)
hats = np.zeros(N); pad = np.zeros(N)

nbars = int(DUR / bar) + 1
pattern = [0, 1, 2, 3, 2, 1, 2, 3]          # arpeggio order over 8ths (index into chord + octave)
for b in range(nbars):
    b0 = b * bar
    ch = CH[b % 4]
    notes = ch + [ch[0] + 12]
    # plucked guitar 8ths, slight swing-free groove, accent on downbeats
    for k in range(8):
        f = midi(notes[pattern[k]])
        add(gtr, b0 + k * beat / 2, pluck(f, 0.55, bright=0.7 if k % 2 == 0 else 0.45) * (1.0 if k % 4 == 0 else 0.7))
    # pad (soft, sustained)
    n = int(bar * SR)
    tt = np.arange(n) / SR
    pv = sum(np.sin(2 * np.pi * midi(m) * tt) + 0.3 * np.sin(2 * np.pi * midi(m) * 2.003 * tt) for m in ch)
    env = np.minimum(1, tt / 0.3) * np.minimum(1, (bar - tt) / 0.3)
    add(pad, b0, pv * env * 0.05)
    # bass: driving 8ths on the root, octave pop on the "and" of 4
    for k in range(8):
        m = ROOT[b % 4] + (12 if k == 7 else 0)
        bn = int(beat / 2 * SR * 0.9)
        bt = np.arange(bn) / SR
        f = midi(m)
        x = np.sign(np.sin(2 * np.pi * f * bt)) * 0.35 + np.sin(2 * np.pi * f * bt)
        add(bass, b0 + k * beat / 2, x * np.exp(-bt * 6) * 0.25)
    # drums
    for k in range(4):
        kt = np.arange(int(0.4 * SR)) / SR
        fk = 48 + 110 * np.exp(-kt * 35)
        kx = np.sin(2 * np.pi * np.cumsum(fk) / SR) * np.exp(-kt * 8)
        kx[:60] += rng.uniform(-1, 1, 60) * 0.4          # beater click
        add(kick, b0 + k * beat, kx * 0.8)
        if k in (1, 3):
            cn = int(0.25 * SR)
            ct = np.arange(cn) / SR
            noise = bp(rng.standard_normal(cn), 900, 5000)
            env = np.exp(-ct * 22) + 0.6 * np.exp(-np.maximum(ct - 0.012, 0) * 22) * (ct > 0.012)
            add(clap, b0 + k * beat, noise * env * 0.35)
    if b % 4 == 3:                                           # little kick pickup into the next phrase
        add(kick, b0 + 3.5 * beat, kx * 0.55)
    for k in range(16):
        hn = int(0.05 * SR)
        hx = hp(rng.standard_normal(hn), 7000) * np.exp(-np.arange(hn) / SR * (90 if k % 2 else 60))
        add(hats, b0 + k * beat / 4, hx * (0.10 if k % 4 == 2 else 0.05))

# arrangement in story time
drums_on = ramp(4.8, 5.4, story) * (1 - ramp(75.4, 76.0, story) * (1 - ramp(85.6, 86.2, story))) \
    * (1 - ramp(99.4, 100.2, story))
hats_on = drums_on * ramp(14, 16, story)
bass_on = ramp(4.8, 5.4, story) * (1 - 0.6 * ramp(99.4, 100.5, story))
gtr_on = 0.55 + 0.45 * ramp(4.8, 5.4, story)
# darker, filtered feel while things fail (56-75): less hats, lower pad
hats_on *= 1 - 0.5 * ramp(36, 37, story) * (1 - ramp(85, 86, story))

music = (lp(gtr, 6000) * 0.55 * gtr_on + lp(bass, 900) * bass_on + kick * drums_on +
         clap * drums_on + hats * hats_on + lp(pad, 2500) * 1.0)
music *= np.clip(t / 0.8, 0, 1)

# ------------------------------------------------------------------ sound design
sfx = np.zeros(N)

def whoosh(dur=0.55, up=True, gain=0.35):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    tt = np.linspace(0, 1, n)
    env = np.sin(np.pi * tt) ** 1.5
    out = np.zeros(n)
    steps = 24
    for i in range(steps):          # sweep a band-pass across the noise
        a, b = i * n // steps, (i + 1) * n // steps
        u = (i + 0.5) / steps
        fc = 300 * (12 ** (u if up else 1 - u))
        seg = bp(x[max(0, a - 512):b], fc * 0.7, min(fc * 1.6, SR / 2 - 100))
        out[a:b] = seg[-(b - a):]
    return out * env * gain

def impact(gain=0.7):
    n = int(0.9 * SR)
    tt = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(40 + 60 * np.exp(-tt * 12)) / SR) * np.exp(-tt * 4)
    hit = lp(rng.standard_normal(n), 2500) * np.exp(-tt * 25)
    return (boom + 0.4 * hit) * gain

def crackle(dur, gain=0.25):
    n = int(dur * SR)
    x = np.zeros(n)
    for _ in range(int(dur * 40)):
        p = rng.integers(0, n - 400)
        x[p:p + 400] += rng.standard_normal(400) * np.exp(-np.arange(400) / 60) * rng.uniform(0.3, 1)
    return hp(x, 1500) * gain

def hiss(dur, gain=0.12):
    n = int(dur * SR)
    tt = np.linspace(0, 1, n)
    return bp(rng.standard_normal(n), 2500, 9000) * np.minimum(1, tt * 8) * np.minimum(1, (1 - tt) * 8) * gain

def shimmer(gain=0.12):
    n = int(1.6 * SR)
    tt = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * midi(m) * tt) for m in (86, 90, 93, 98))
    return x * np.exp(-tt * 2.2) * np.minimum(1, tt / 0.05) * gain

for st0, kind in sfx_events():
    if 75.6 < st0 < 85.6:       # camera reset while the comparison is on screen: silent
        continue
    ot = out_time(st0)
    if kind == "cut":
        add(sfx, ot - 0.18, whoosh(0.25, True, 0.25))
        add(sfx, ot, impact(0.45))
    else:
        add(sfx, ot - 0.1, whoosh(0.6, kind == "push", 0.32))

add(sfx, out_time(16.8), crackle(1.6, 0.3))           # crack opens
add(sfx, out_time(21.0), crackle(1.4, 0.18))          # crack deepens
for c in (38.5, 44.1, 49.7):                          # freezes: ice crunch
    add(sfx, out_time(c + 0.3), crackle(1.2, 0.22))
add(sfx, out_time(72.6), impact(0.8))                 # pothole collapse
add(sfx, out_time(89.0), hiss(out_time(91.8) - out_time(89.0), 0.10))   # sealant
add(sfx, out_time(1.2), shimmer())                    # logo reveals
add(sfx, out_time(100.4), shimmer())
add(sfx, out_time(75.8), whoosh(0.6, True, 0.3))     # into comparison
add(sfx, out_time(85.6), whoosh(0.6, False, 0.3))    # back to the section

# rain bed
rain_env = (ramp(25, 26, story) * (1 - ramp(35.8, 36.8, story)) +
            0.6 * ramp(72.4, 73, story) * (1 - ramp(75, 75.8, story)) +
            ramp(92.8, 93.5, story) * (1 - ramp(99, 99.8, story)))
rain = lp(hp(rng.standard_normal(N), 400), 6000) * 0.05
sfx += rain * rain_env

# ------------------------------------------------------------------ mix
# duck music slightly under impacts
duck = 1 - 0.35 * np.clip(lp(np.abs(sfx), 8) * 6, 0, 1)
mix_l = music * duck * 0.9 + sfx
mix_r = music * duck * 0.9 + sfx
# stereo width: guitar left-ish, hats right-ish
mix_l += lp(gtr, 6000) * 0.12 * gtr_on
mix_r += hats * hats_on * 0.4
fade = np.clip((DUR - t) / 2.5, 0, 1)
stereo = np.stack([mix_l * fade, mix_r * fade], 1)
stereo /= np.abs(stereo).max() / 0.89
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", f"music_{FORMAT}.wav")
wavfile.write(path, SR, (stereo * 32767).astype(np.int16))
print("wrote", path)
