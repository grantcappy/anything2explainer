import React from 'react';
import {AbsoluteFill, Audio, Easing, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, BODY, HEAD, Person, lerp, life, pop} from './kit';
import {ILLS, STEPS, fadeUp} from './Scenes';
import TL from './timeline.json';

const L = TL.lines;
const IN = (i: number) => L[i].from - 6; // a scene starts just before its line
const STEP_START = (k: number) => IN(k); // steps 1..6 = lines 1..6
const STEP_END = (k: number) => IN(k + 1);
const OUTRO = IN(7);
const ENDCARD = L[7].from + L[7].dur + 6;
export const TOTAL = TL.total;

const useLayout = () => {
  const {width, height} = useVideoConfig();
  const v = height > width;
  return v
    ? {v, W: width, H: height, road: {y: 1600, h: 120}, ill: {x: 40, y: 250, w: 1000, h: 750}, text: {x: 80, y: 1040, w: 920, align: 'center' as const}, badge: {x: 540, y: 130}}
    : {v, W: width, H: height, road: {y: 960, h: 120}, ill: {x: 900, y: 120, w: 940, h: 705}, text: {x: 130, y: 320, w: 740, align: 'left' as const}, badge: {x: 300, y: 150}};
};

// ---------- background: asphalt grain + vignette ----------
const Background: React.FC = () => (
  <AbsoluteFill style={{background: C.bg}}>
    <svg width="100%" height="100%" style={{position: 'absolute', opacity: 0.22}}>
      <filter id="grain">
        <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={4} />
        <feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 1.2 -0.35" />
      </filter>
      <rect width="100%" height="100%" filter="url(#grain)" />
    </svg>
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 40%, rgba(0,0,0,0) 40%, rgba(0,0,0,0.55) 100%)'}} />
  </AbsoluteFill>
);

// ---------- logo lockup (typographic placeholder — swap for the real logo) ----------
const Logo: React.FC<{f: number; scale?: number}> = ({f, scale = 1}) => {
  const a = pop(f, 0), b = pop(f, 6), line = lerp(f, 4, 22, 0, 1);
  return (
    <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', transform: `scale(${scale})`}}>
      <div style={{fontFamily: HEAD, fontSize: 200, lineHeight: 0.95, color: C.white, letterSpacing: 6, transform: `translateY(${(1 - a) * -60}px)`, opacity: a}}>
        STUBBS
      </div>
      <div style={{display: 'flex', alignItems: 'center', gap: 22, marginTop: 10}}>
        <div style={{width: 150 * line, height: 14, background: C.yellow, borderRadius: 4}} />
        <div style={{fontFamily: HEAD, fontSize: 92, color: C.yellow, letterSpacing: 14, opacity: b, transform: `translateY(${(1 - b) * 40}px)`}}>ASPHALT</div>
        <div style={{width: 150 * line, height: 14, background: C.yellow, borderRadius: 4}} />
      </div>
    </div>
  );
};

// ---------- the road: step tracker along the bottom ----------
const Road: React.FC<{f: number; step: number; traveler?: number}> = ({f, step, traveler}) => {
  const {W, road, v} = useLayout();
  const show = lerp(f, IN(1) - 4, IN(1) + 10, 0, 1);
  const margin = v ? 110 : 260;
  const xs = Array.from({length: 6}, (_, i) => margin + ((W - 2 * margin) * i) / 5);
  const cy = road.h / 2;
  const dashOff = -(f * 6) % 80;
  return (
    <svg width={W} height={road.h} style={{position: 'absolute', left: 0, top: road.y, transform: `translateY(${(1 - show) * 160}px)`, opacity: show}}>
      <rect x={0} y={0} width={W} height={road.h} fill={C.road} />
      <path d={`M 0 6 H ${W} M 0 ${road.h - 6} H ${W}`} stroke={C.white} strokeWidth={5} opacity={0.75} />
      <path d={`M 0 ${cy} H ${W}`} stroke={C.yellow} strokeWidth={7} strokeDasharray="44 36" strokeDashoffset={dashOff} opacity={0.55} />
      {xs.map((x, i) => {
        const n = i + 1;
        const lit = traveler !== undefined ? traveler >= i : step >= n;
        const cur = traveler === undefined && step === n;
        const r = cur ? 38 : 30;
        return (
          <g key={n} transform={`translate(${x} ${cy})`}>
            {cur && <circle r={r + 12 + Math.sin(f / 5) * 3} fill="none" stroke={C.yellow} strokeWidth={4} opacity={0.5} />}
            <circle r={r} fill={lit ? C.yellow : C.road} stroke={lit ? C.yellow : C.gray} strokeWidth={5} />
            <text y={r * 0.42} textAnchor="middle" fontFamily={HEAD} fontSize={r * 1.25} fill={lit ? C.bg : C.gray}>
              {n}
            </text>
          </g>
        );
      })}
      {traveler !== undefined && (
        <g transform={`translate(${xs[0] + (xs[5] - xs[0]) * (traveler / 5)} ${cy - 6})`}>
          <Person x={0} y={0} s={0.62} hat color={C.yellow} />
        </g>
      )}
    </svg>
  );
};

// ---------- persistent specialist badge: same person, every step ----------
const Badge: React.FC<{f: number}> = ({f}) => {
  const {badge, v} = useLayout();
  const o = life(f, IN(2) + 20, OUTRO + 4, 14, 10);
  if (o <= 0) return null;
  return (
    <div style={{position: 'absolute', left: badge.x, top: badge.y, transform: `translate(-50%, -50%) scale(${0.85 + 0.15 * o})`, opacity: o,
      display: 'flex', alignItems: 'center', gap: 16, padding: '10px 26px 10px 12px', borderRadius: 60, background: 'rgba(37,39,42,0.92)', border: `3px solid ${C.yellow}`}}>
      <svg width={70} height={70} viewBox="-55 -75 110 130"><Person x={0} y={0} s={1} hat /></svg>
      <div style={{fontFamily: BODY, lineHeight: 1.15}}>
        <div style={{fontWeight: 900, fontSize: v ? 28 : 26, color: C.yellow, letterSpacing: 1.5}}>YOUR SPECIALIST</div>
        <div style={{fontWeight: 600, fontSize: v ? 24 : 22, color: C.white}}>Same contact, every step</div>
      </div>
    </div>
  );
};

// ---------- one step scene ----------
const Step: React.FC<{k: number; f: number}> = ({k, f}) => {
  const {ill, text, v} = useLayout();
  const s = STEP_START(k), e = STEP_END(k);
  if (f < s || f >= e) return null;
  const local = f - L[k].from;
  const out = lerp(f, e - 9, e, 0, 1, Easing.in(Easing.cubic));
  const Ill = ILLS[k - 1];
  const st = STEPS[k - 1];
  return (
    <AbsoluteFill style={{opacity: 1 - out}}>
      <div style={{position: 'absolute', left: text.x, top: text.y, width: text.w, textAlign: text.align, transform: `translateX(${v ? 0 : -60 * out}px)`}}>
        <div style={{...fadeUp(f, s), fontFamily: BODY, fontWeight: 900, fontSize: v ? 40 : 38, color: C.yellow, letterSpacing: 6}}>STEP {k}</div>
        <div style={{...fadeUp(f, s + 3), fontFamily: HEAD, fontSize: v ? 128 : 122, lineHeight: 1.02, color: C.white, textTransform: 'uppercase', marginTop: 8}}>
          {st.title}
        </div>
        <div style={{...fadeUp(f, s + 3), width: v ? 140 : 120, height: 10, background: C.yellow, borderRadius: 4, margin: v ? '26px auto' : '26px 0'}} />
        <div style={{...fadeUp(f, s + 8), fontFamily: BODY, fontWeight: 600, fontSize: v ? 44 : 42, lineHeight: 1.3, color: C.white, opacity: 0.88 * fadeUp(f, s + 8).opacity}}>
          {st.sub}
        </div>
      </div>
      <svg width={ill.w} height={ill.h} viewBox="-400 -300 800 600" style={{position: 'absolute', left: ill.x, top: ill.y, transform: `scale(${1 - 0.05 * out})`}}>
        <Ill f={local} dur={L[k].dur + 9} />
      </svg>
    </AbsoluteFill>
  );
};

// ---------- intro / outro / end card ----------
const Intro: React.FC<{f: number}> = ({f}) => {
  const {v} = useLayout();
  const o = life(f, 0, IN(1), 1, 9);
  if (o <= 0) return null;
  const tag = lerp(f, 18, 30, 0, 1);
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', opacity: o, transform: `scale(${1 + 0.03 * (f / IN(1))})`}}>
      <Logo f={f} scale={v ? 0.95 : 1} />
      <div style={{marginTop: 50, fontFamily: BODY, fontWeight: 800, fontSize: 46, color: C.white, opacity: tag, transform: `translateY(${(1 - tag) * 20}px)`, textAlign: 'center'}}>
        Your project, step by step
      </div>
      <div style={{marginTop: 22, padding: '8px 22px', borderRadius: 8, background: C.yellow, color: C.bg, fontFamily: BODY, fontWeight: 900, fontSize: 30, letterSpacing: 4, opacity: lerp(f, 26, 36, 0, 1)}}>
        FOR HOMEOWNERS
      </div>
    </AbsoluteFill>
  );
};

const Outro: React.FC<{f: number}> = ({f}) => {
  const {v, road} = useLayout();
  if (f < OUTRO) return null;
  const o = Math.min(lerp(f, OUTRO, OUTRO + 12, 0, 1), lerp(f, ENDCARD - 8, ENDCARD, 1, 0));
  if (o <= 0) return null;
  const sz = v ? 150 : 170;
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', paddingBottom: v ? 1920 - road.y : 120, opacity: o}}>
      <svg width={260} height={260} viewBox="-90 -110 180 190" style={{transform: `scale(${pop(f, OUTRO)})`}}>
        <circle cx={0} cy={-10} r={86} fill="none" stroke={C.yellow} strokeWidth={5} opacity={0.6} />
        <Person x={0} y={0} s={1.15} hat />
      </svg>
      <div style={{...fadeUp(f, OUTRO + 4), fontFamily: HEAD, fontSize: sz, lineHeight: 1, color: C.white, textAlign: 'center', marginTop: 20}}>
        ONE POINT OF CONTACT
      </div>
      <div style={{...fadeUp(f, OUTRO + 26), fontFamily: HEAD, fontSize: sz * 0.62, color: C.yellow, marginTop: 14, letterSpacing: 3}}>START TO FINISH.</div>
    </AbsoluteFill>
  );
};

const EndCard: React.FC<{f: number}> = ({f}) => {
  const {v} = useLayout();
  if (f < ENDCARD) return null;
  const lf = f - ENDCARD;
  const cta = lerp(lf, 16, 28, 0, 1);
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', background: C.bg}}>
      <Background />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        <Logo f={lf} scale={v ? 0.95 : 1} />
        <div style={{marginTop: 56, fontFamily: BODY, fontWeight: 800, fontSize: v ? 44 : 46, color: C.white, opacity: cta, transform: `translateY(${(1 - cta) * 20}px)`, textAlign: 'center', padding: '0 60px'}}>
          Request your estimate today
        </div>
        <div style={{marginTop: 18, fontFamily: BODY, fontWeight: 700, fontSize: v ? 34 : 34, color: C.gray, letterSpacing: 3, opacity: lerp(lf, 24, 36, 0, 1)}}>
          ONLINE · CALL · TEXT
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Video: React.FC = () => {
  const f = useCurrentFrame();
  let step = 0;
  for (let k = 1; k <= 6; k++) if (f >= STEP_START(k)) step = k;
  const traveler = f >= OUTRO ? lerp(f, OUTRO + 6, OUTRO + 50, 0, 5, Easing.inOut(Easing.quad)) : undefined;
  return (
    <AbsoluteFill>
      <Background />
      <Intro f={f} />
      {[1, 2, 3, 4, 5, 6].map((k) => (
        <Step key={k} k={k} f={f} />
      ))}
      <Outro f={f} />
      <Badge f={f} />
      {f < ENDCARD && <Road f={f} step={step} traveler={traveler} />}
      <EndCard f={f} />
      <Audio src={staticFile('voice.wav')} />
    </AbsoluteFill>
  );
};
