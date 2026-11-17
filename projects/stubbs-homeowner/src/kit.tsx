import React from 'react';
import {continueRender, delayRender, Easing, interpolate, spring, staticFile} from 'remotion';

// ---------- brand tokens ----------
export const C = {
  bg: '#1b1c1e',
  bg2: '#25272a',
  road: '#2c2e31',
  yellow: '#FFC629',
  white: '#F4F3EE',
  gray: '#9A9DA1',
  dim: '#55585c',
  fresh: '#0e0f10',
};
export const HEAD = 'Anton, Impact, sans-serif';
export const BODY = 'Inter, Arial, sans-serif';

// ---------- fonts ----------
const fonts: [string, string, string][] = [
  ['Anton', 'fonts/anton.woff2', '400'],
  ['Inter', 'fonts/inter-600.woff2', '600'],
  ['Inter', 'fonts/inter-800.woff2', '800'],
  ['Inter', 'fonts/inter-900.woff2', '900'],
];
if (typeof document !== 'undefined') {
  const h = delayRender('fonts');
  Promise.all(
    fonts.map(([fam, file, weight]) => {
      const f = new FontFace(fam, `url(${staticFile(file)}) format('woff2')`, {weight});
      return f.load().then((l) => (document.fonts as unknown as {add: (f: FontFace) => void}).add(l));
    }),
  ).then(() => continueRender(h));
}

// ---------- motion helpers ----------
export const EASE = Easing.bezier(0.22, 1, 0.36, 1);
export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
export const lerp = (f: number, a: number, b: number, from: number, to: number, ease = EASE) =>
  interpolate(f, [a, b], [from, to], {...clamp, easing: ease});
export const pop = (f: number, start: number, fps = 30) =>
  spring({frame: f - start, fps, config: {damping: 13, stiffness: 170, mass: 0.7}});
/** 0→1 in, then 1→0 over the last `out` frames before `end` */
export const life = (f: number, start: number, end: number, inDur = 12, out = 9) =>
  Math.min(lerp(f, start, start + inDur, 0, 1), lerp(f, end - out, end, 1, 0, Easing.in(Easing.cubic)));

// ---------- icons (all drawn in a local coordinate box, white line art) ----------
const S = {fill: 'none', stroke: C.white, strokeWidth: 6, strokeLinecap: 'round', strokeLinejoin: 'round'} as const;

/** Specialist / person avatar. hat = yellow hard hat */
export const Person: React.FC<{x: number; y: number; s?: number; hat?: boolean; color?: string}> = ({x, y, s = 1, hat, color = C.white}) => (
  <g transform={`translate(${x} ${y}) scale(${s})`}>
    <circle cx={0} cy={-30} r={26} fill={C.bg2} stroke={color} strokeWidth={6} />
    <path d="M -46 48 C -46 10 -22 4 0 4 C 22 4 46 10 46 48 Z" fill={C.bg2} stroke={color} strokeWidth={6} strokeLinejoin="round" />
    {hat && (
      <g>
        <path d="M -30 -40 C -30 -70 30 -70 30 -40 Z" fill={C.yellow} />
        <rect x={-38} y={-44} width={76} height={9} rx={4} fill={C.yellow} />
        <rect x={-4} y={-66} width={8} height={22} rx={3} fill="#d9a400" />
      </g>
    )}
  </g>
);

export const Check: React.FC<{x: number; y: number; r?: number; t?: number}> = ({x, y, r = 34, t = 1}) => (
  <g transform={`translate(${x} ${y}) scale(${Math.max(0.001, t)})`}>
    <circle r={r} fill={C.yellow} />
    <path d={`M ${-r * 0.42} 0 L ${-r * 0.1} ${r * 0.32} L ${r * 0.45} ${-r * 0.3}`} fill="none" stroke={C.bg} strokeWidth={r * 0.2} strokeLinecap="round" strokeLinejoin="round" />
  </g>
);

export const Laptop: React.FC = () => (
  <g>
    <rect x={-62} y={-48} width={124} height={80} rx={8} {...S} />
    <path d="M -80 46 H 80 L 70 32 H -70 Z" {...S} />
    <path d="M -40 -26 H 40 M -40 -8 H 22 M -40 10 H 10" {...S} strokeWidth={5} stroke={C.yellow} />
  </g>
);
export const Phone: React.FC = () => (
  <g>
    <rect x={-36} y={-62} width={72} height={124} rx={14} {...S} />
    <path d="M -12 48 H 12" {...S} />
    <path d="M -12 -14 C -12 6 4 22 22 22 L 22 10 L 12 4 L 6 10 C -2 6 -6 2 -8 -6 L -2 -12 L -6 -22 L -12 -22 Z" fill={C.yellow} />
  </g>
);
export const Chat: React.FC = () => (
  <g>
    <path d="M -66 -46 H 66 Q 78 -46 78 -34 V 22 Q 78 34 66 34 H -18 L -46 58 V 34 H -66 Q -78 34 -78 22 V -34 Q -78 -46 -66 -46 Z" {...S} />
    {[-30, 0, 30].map((cx) => (
      <circle key={cx} cx={cx} cy={-6} r={8} fill={C.yellow} />
    ))}
  </g>
);
export const Voicemail: React.FC = () => (
  <g>
    <circle cx={-38} cy={0} r={28} {...S} />
    <circle cx={38} cy={0} r={28} {...S} />
    <path d="M -38 28 H 38" {...S} />
    <circle cx={64} cy={-40} r={12} fill={C.yellow} />
  </g>
);
export const Envelope: React.FC = () => (
  <g>
    <rect x={-70} y={-46} width={140} height={92} rx={8} {...S} />
    <path d="M -70 -40 L 0 12 L 70 -40" {...S} />
  </g>
);

/** Calendar card. `mark` 0..1 = highlight a date with yellow + check. */
export const Calendar: React.FC<{mark: number; label?: string}> = ({mark, label}) => {
  const cells = [];
  for (let r = 0; r < 4; r++)
    for (let c = 0; c < 5; c++) {
      const hit = r === 2 && c === 3;
      cells.push(
        <rect key={`${r}${c}`} x={-118 + c * 48} y={-30 + r * 40} width={36} height={28} rx={5}
          fill={hit ? C.yellow : C.dim} opacity={hit ? Math.max(0.35, mark) : 0.55} />,
      );
    }
  return (
    <g>
      <rect x={-140} y={-110} width={280} height={250} rx={18} fill={C.bg2} stroke={C.white} strokeWidth={6} />
      <path d="M -140 -56 H 140" stroke={C.white} strokeWidth={6} />
      <rect x={-140} y={-110} width={280} height={54} rx={18} fill={C.yellow} opacity={0.9} />
      <rect x={-140} y={-74} width={280} height={18} fill={C.yellow} opacity={0.9} />
      <path d="M -80 -128 V -94 M 80 -128 V -94" stroke={C.white} strokeWidth={9} strokeLinecap="round" />
      {cells}
      <Check x={-118 + 3 * 48 + 18} y={-30 + 2 * 40 + 14} r={30} t={mark} />
      {label && (
        <text x={0} y={-74} textAnchor="middle" fontFamily={BODY} fontWeight={900} fontSize={26} fill={C.bg} letterSpacing={2}>
          {label}
        </text>
      )}
    </g>
  );
};

/** simple house elevation, origin = ground center */
export const House: React.FC<{s?: number}> = ({s = 1}) => (
  <g transform={`scale(${s})`}>
    <path d="M -170 0 V -150 L 0 -260 L 170 -150 V 0" fill={C.bg2} stroke={C.white} strokeWidth={6} strokeLinejoin="round" />
    <path d="M -195 -134 L 0 -284 L 195 -134" fill="none" stroke={C.white} strokeWidth={8} strokeLinecap="round" strokeLinejoin="round" />
    <rect x={-130} y={-120} width={150} height={120} rx={4} fill="none" stroke={C.white} strokeWidth={6} />
    {[-96, -64, -32].map((y) => (
      <path key={y} d={`M -130 ${y} H 20`} stroke={C.gray} strokeWidth={4} />
    ))}
    <rect x={60} y={-110} width={70} height={110} rx={4} fill="none" stroke={C.white} strokeWidth={6} />
    <rect x={-40} y={-215} width={80} height={56} rx={4} fill={C.yellow} opacity={0.85} />
  </g>
);
