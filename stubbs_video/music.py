"""Original background track synthesized from scratch (no samples) -> assets/music.wav.
Steady, confident corporate-style bed: pads + pluck arpeggio + sub bass + soft drums."""
import os
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile

SR = 44100
DUR = 106.0
BPM = 92
beat = 60 / BPM
bar = 4 * beat
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(1)

def midi(m):
    return 440 * 2 ** ((m - 69) / 12)

# A minor - F - C - G
CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
ROOTS = [33, 29, 36, 31]

def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)

def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)

def env_adsr(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e

def saw(f, tt):
    # band-limited-ish via a few harmonics
    out = np.zeros_like(tt)
    for k in range(1, 9):
        out += ((-1) ** (k + 1)) * np.sin(2 * np.pi * f * k * tt) / k
    return out

pad = np.zeros(N); arp = np.zeros(N); bass = np.zeros(N); drums = np.zeros(N)
nbars = int(DUR / bar) + 1
for b in range(nbars):
    s0 = int(b * bar * SR)
    if s0 >= N:
        break
    n = min(int(bar * SR), N - s0)
    tt = np.arange(n) / SR
    ch = CHORDS[b % 4]
    # pad: detuned saws, slow attack
    p = np.zeros(n)
    for m in ch + [ch[0] + 12]:
        for det in (-0.12, 0.12):
            p += saw(midi(m + det), tt)
    pad[s0:s0 + n] += p * env_adsr(n, 0.6, 0.5) * 0.05
    # bass on beats 1 and 3 (+ & of 4)
    for pos in (0, 2, 3.5):
        bs = s0 + int(pos * beat * SR)
        bn = min(int(beat * 0.9 * SR), N - bs)
        if bn <= 0:
            continue
        bt = np.arange(bn) / SR
        f = midi(ROOTS[b % 4] + 12)
        x = np.sin(2 * np.pi * f * bt) + 0.3 * np.sin(2 * np.pi * 2 * f * bt)
        bass[bs:bs + bn] += x * np.exp(-bt * 3) * env_adsr(bn, 0.01, 0.05) * 0.22
    # arpeggio 8ths
    notes = ch + [ch[0] + 12, ch[1] + 12, ch[2], ch[1], ch[0] + 12]
    for k in range(8):
        a_s = s0 + int(k * beat / 2 * SR)
        an = min(int(beat / 2 * SR * 1.6), N - a_s)
        if an <= 0:
            continue
        at = np.arange(an) / SR
        f = midi(notes[k] + 12)
        x = np.sin(2 * np.pi * f * at) + 0.4 * np.sin(2 * np.pi * 2 * f * at) * np.exp(-at * 8)
        arp[a_s:a_s + an] += x * np.exp(-at * 5) * 0.06
    # drums
    for k in range(4):
        ks = s0 + int(k * beat * SR)
        if ks >= N:
            continue
        kn = min(int(0.35 * SR), N - ks)
        kt = np.arange(kn) / SR
        fk = 50 + 90 * np.exp(-kt * 30)
        drums[ks:ks + kn] += np.sin(2 * np.pi * np.cumsum(fk) / SR) * np.exp(-kt * 9) * 0.5
        # hat on off-beat
        hs = ks + int(beat / 2 * SR)
        hn = min(int(0.06 * SR), N - hs)
        if hn > 0:
            drums[hs:hs + hn] += rng.standard_normal(hn) * np.exp(-np.arange(hn) / SR * 60) * 0.06
        # clap/snare on 2 and 4
        if k in (1, 3):
            sn = min(int(0.2 * SR), N - ks)
            drums[ks:ks + sn] += rng.standard_normal(sn) * np.exp(-np.arange(sn) / SR * 18) * 0.12

pad = lp(pad, 1800)
arp = lp(arp, 4000)
drums_hp = hp(drums, 30)

# arrangement: intro pad only, drums enter at layers build, break at freeze, full at failure, calm outro
def ramp(a, b, x):
    return np.clip((x - a) / max(b - a, 1e-6), 0, 1)

drum_gain = ramp(13.5, 15.5, t) * (1 - 0.6 * ramp(75, 76.5, t) * (1 - ramp(85, 87, t))) * (1 - ramp(98.5, 100.5, t))
arp_gain = 0.4 + 0.6 * ramp(4.5, 6, t)
bass_gain = ramp(5, 7, t) * (1 - 0.5 * ramp(99, 101, t))

mix = pad * 1.0 + arp * arp_gain + bass * bass_gain + drums_hp * drum_gain * 0.8
mix *= np.clip(t / 1.5, 0, 1) * np.clip((DUR - t) / 4.0, 0, 1)
# light stereo widening via a short delay on pad/arp
left = mix + 0.15 * np.roll(arp, int(0.011 * SR))
right = mix + 0.15 * np.roll(pad, int(0.017 * SR))
st = np.stack([left, right], 1)
st /= np.abs(st).max() / 0.85
os.makedirs(os.path.join(os.path.dirname(__file__), "assets"), exist_ok=True)
wavfile.write(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "music.wav"), SR,
              (st * 32767).astype(np.int16))
print("ok")
