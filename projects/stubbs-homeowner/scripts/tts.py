"""Build voiceover + timeline from script/narration.txt using local kokoro-onnx.
Env: KOKORO_MODEL, KOKORO_VOICES, VOICE (default am_michael), SPEED (default 1.08)."""
import os, json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
FPS = 30
LEAD, GAP, TAIL = 12, 9, 75  # frames: before first line, between lines, after last line (logo hold)
k = Kokoro(os.environ['KOKORO_MODEL'], os.environ['KOKORO_VOICES'])
voice = os.environ.get('VOICE', 'am_michael'); speed = float(os.environ.get('SPEED', '1.08'))
lines = [l.strip() for l in open('script/narration.txt') if l.strip()]
sr = 24000; out = [np.zeros(int(LEAD / FPS * sr), np.float32)]; tl = []; f = LEAD
for i, text in enumerate(lines):
    s, sr = k.create(text, voice=voice, speed=speed, lang='en-us')
    s = np.asarray(s, np.float32)
    # trim leading/trailing silence
    nz = np.where(np.abs(s) > 0.01)[0]; s = s[max(nz[0] - 600, 0): nz[-1] + 1200]
    dur = int(np.ceil(len(s) / sr * FPS))
    pad = dur * sr // FPS - len(s)
    out.append(s); out.append(np.zeros(max(pad, 0) + int(GAP / FPS * sr), np.float32))
    tl.append({'id': f'S{i}', 'text': text, 'from': f, 'dur': dur}); f += dur + GAP
total = f - GAP + TAIL
audio = np.concatenate(out); audio = np.pad(audio, (0, max(0, int(total / FPS * sr) - len(audio))))
os.makedirs('public', exist_ok=True); sf.write('public/voice.wav', audio * 0.95, sr)
json.dump({'fps': FPS, 'total': total, 'lines': tl}, open('src/timeline.json', 'w'), indent=1)
for t in tl: print(f"{t['id']} {t['from']:4d}+{t['dur']:3d}  {t['text']}")
print('total', total, 'frames =', round(total / FPS, 2), 's;', sum(len(l.split()) for l in lines), 'words')
