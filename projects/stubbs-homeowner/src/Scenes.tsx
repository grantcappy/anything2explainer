import React from 'react';
import {Easing, interpolate} from 'remotion';
import {C, BODY, HEAD, Calendar, Chat, Check, Envelope, House, Laptop, Person, Phone, Voicemail, clamp, lerp, pop} from './kit';

/** Every illustration is drawn in an 800×600 box centered on (0,0); f = frames since the scene's line starts. */
type Ill = React.FC<{f: number; dur: number}>;

const Tile: React.FC<{x: number; y: number; t: number; label: string; children: React.ReactNode}> = ({x, y, t, label, children}) => (
  <g transform={`translate(${x} ${y}) scale(${0.6 + 0.4 * t})`} opacity={Math.min(1, t * 1.4)}>
    <rect x={-170} y={-125} width={340} height={250} rx={26} fill={C.bg2} stroke={t > 0.95 ? C.yellow : C.white} strokeWidth={5} />
    <g transform="translate(0 -22)">{children}</g>
    <text x={0} y={92} textAnchor="middle" fontFamily={BODY} fontWeight={800} fontSize={34} fill={C.white} letterSpacing={1}>
      {label}
    </text>
  </g>
);

// STEP 1 — reach out: four channels pop in roughly on their words
export const Ill1: Ill = ({f}) => {
  const at = [4, 26, 40, 56];
  const items: [string, React.ReactNode][] = [
    ['ONLINE', <Laptop />],
    ['CALL', <Phone />],
    ['TEXT', <Chat />],
    ['VOICEMAIL', <Voicemail />],
  ];
  return (
    <g>
      {items.map(([label, icon], i) => (
        <Tile key={label} x={i % 2 ? 190 : -190} y={i < 2 ? -140 : 140} t={pop(f, at[i])} label={label}>
          {icon}
        </Tile>
      ))}
    </g>
  );
};

// STEP 2 — specialist calls you, a site visit lands on the calendar
export const Ill2: Ill = ({f}) => {
  const ph = pop(f, 0);
  const ring = (f % 24) / 24;
  const cal = pop(f, 34);
  const mark = lerp(f, 52, 64, 0, 1);
  return (
    <g>
      <g transform={`translate(-190 0) scale(${ph}) rotate(${Math.sin(f / 2.2) * (f < 40 ? 3 : 0)})`}>
        <rect x={-120} y={-230} width={240} height={440} rx={36} fill={C.bg2} stroke={C.white} strokeWidth={7} />
        <Person x={0} y={-50} s={1.25} hat />
        <text x={0} y={60} textAnchor="middle" fontFamily={BODY} fontWeight={800} fontSize={26} fill={C.white}>
          STUBBS ASPHALT
        </text>
        <text x={0} y={94} textAnchor="middle" fontFamily={BODY} fontWeight={600} fontSize={22} fill={C.gray}>
          Asphalt Specialist
        </text>
        <circle cx={0} cy={158} r={30} fill={C.yellow} />
        <path d="M -12 150 C -12 166 0 174 14 172 L 14 164 L 6 160 L 2 164 C -4 162 -6 158 -6 154 L -2 150 L -6 142 L -12 142 Z" fill={C.bg} />
        {f < 40 &&
          [0, 1].map((k) => {
            const p = (ring + k * 0.5) % 1;
            return (
              <g key={k} opacity={1 - p}>
                <path d={`M ${140 + p * 40} -120 A ${80 + p * 50} ${80 + p * 50} 0 0 1 ${140 + p * 40} 20`} fill="none" stroke={C.yellow} strokeWidth={7} strokeLinecap="round" />
              </g>
            );
          })}
      </g>
      <g transform={`translate(190 20) scale(${cal})`} opacity={Math.min(1, cal * 1.5)}>
        <Calendar mark={mark} label="SITE VISIT" />
      </g>
    </g>
  );
};

// STEP 3 — meet on site: house + driveway, pin drops, checklist ticks
export const Ill3: Ill = ({f}) => {
  const h = pop(f, 0);
  const pin = lerp(f, 8, 22, -260, 0, Easing.bounce);
  const ppl = pop(f, 18);
  const items = ['Project details', 'Measurements', 'Recommendations'];
  return (
    <g>
      <g transform={`translate(-150 40) scale(${0.85 * h})`} opacity={Math.min(1, h * 1.4)}>
        <House />
        <path d="M 60 0 L 130 0 L 210 220 L -10 220 Z" fill={C.road} stroke={C.white} strokeWidth={5} strokeDasharray="14 12" />
        <g transform={`translate(110 ${120 + pin})`}>
          <path d="M 0 0 C -10 -24 -36 -44 -36 -72 A 36 36 0 0 1 36 -72 C 36 -44 10 -24 0 0 Z" fill={C.yellow} />
          <circle cx={0} cy={-72} r={13} fill={C.bg} />
        </g>
      </g>
      <g opacity={ppl} transform={`translate(${-330 + 30 * (1 - ppl)} 0)`}>
        <Person x={0} y={200} s={0.9} hat />
      </g>
      <g opacity={ppl} transform={`translate(${-210 - 30 * (1 - ppl)} 0)`}>
        <Person x={0} y={205} s={0.85} />
      </g>
      <g transform={`translate(220 -10) scale(${pop(f, 14)})`}>
        <rect x={-165} y={-190} width={330} height={380} rx={20} fill={C.bg2} stroke={C.white} strokeWidth={6} />
        <rect x={-50} y={-206} width={100} height={34} rx={10} fill={C.yellow} />
        {items.map((it, i) => {
          const t = pop(f, 26 + i * 12);
          return (
            <g key={it} transform={`translate(-125 ${-100 + i * 105})`}>
              <rect x={-26} y={-26} width={52} height={52} rx={10} fill="none" stroke={C.gray} strokeWidth={5} />
              <Check x={0} y={0} r={26} t={t} />
              <text x={44} y={10} fontFamily={BODY} fontWeight={800} fontSize={25} fill={t > 0.5 ? C.white : C.gray}>
                {it}
              </text>
            </g>
          );
        })}
      </g>
    </g>
  );
};

// STEP 4 — price: on the spot OR within a day or two
export const Ill4: Ill = ({f}) => {
  const a = pop(f, 0);
  const b = pop(f, 36);
  const or = lerp(f, 30, 40, 0, 1);
  return (
    <g>
      <g transform={`translate(-200 0) scale(${a}) rotate(${(1 - a) * -12})`}>
        <path d="M -120 -150 H 70 L 150 -70 V 150 H -120 Z" fill={C.yellow} />
        <circle cx={88} cy={-60} r={18} fill={C.bg} />
        <text x={0} y={46} textAnchor="middle" fontFamily={HEAD} fontSize={170} fill={C.bg}>
          $
        </text>
        <text x={15} y={118} textAnchor="middle" fontFamily={BODY} fontWeight={900} fontSize={30} fill={C.bg} letterSpacing={1}>
          ON THE SPOT
        </text>
      </g>
      <text x={0} y={14} textAnchor="middle" fontFamily={HEAD} fontSize={52} fill={C.gray} opacity={or}>
        OR
      </text>
      <g transform={`translate(205 0) scale(${b})`} opacity={Math.min(1, b * 1.5)}>
        <rect x={-130} y={-150} width={260} height={300} rx={22} fill={C.bg2} stroke={C.white} strokeWidth={6} />
        <g transform="translate(-30 -60) scale(0.75)">
          <Envelope />
        </g>
        <g transform="translate(50 -20) scale(0.6)">
          <Chat />
        </g>
        <text x={0} y={80} textAnchor="middle" fontFamily={HEAD} fontSize={56} fill={C.yellow}>
          1–2 DAYS
        </text>
        <text x={0} y={120} textAnchor="middle" fontFamily={BODY} fontWeight={700} fontSize={24} fill={C.gray}>
          by email or text
        </text>
      </g>
    </g>
  );
};

// STEP 5 — sign off, then on the schedule
export const Ill5: Ill = ({f}) => {
  const doc = pop(f, 0);
  const sig = lerp(f, 8, 26, 1, 0, Easing.inOut(Easing.quad));
  const stamp = pop(f, 26);
  const cal = pop(f, 36);
  const mark = lerp(f, 48, 58, 0, 1);
  return (
    <g>
      <g transform={`translate(-190 0) scale(${doc}) rotate(-4)`}>
        <rect x={-150} y={-200} width={300} height={400} rx={14} fill={C.white} />
        <rect x={-110} y={-160} width={150} height={20} rx={6} fill={C.bg} />
        {[-110, -80, -50, -20, 10].map((y, i) => (
          <rect key={y} x={-110} y={y} width={i === 4 ? 140 : 220} height={11} rx={5} fill="#c9c8c2" />
        ))}
        <path d="M -110 140 H 110" stroke={C.bg} strokeWidth={4} />
        <path d="M -100 120 C -80 70 -70 140 -50 110 S -20 80 0 120 S 40 100 60 110 S 90 120 100 104" fill="none" stroke="#1d3fbf"
          strokeWidth={6} strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={sig} />
        <g transform={`translate(40 40) rotate(-14) scale(${1.6 - 0.6 * stamp})`} opacity={stamp}>
          <rect x={-115} y={-36} width={230} height={72} rx={10} fill="none" stroke={C.yellow} strokeWidth={8} />
          <text x={0} y={18} textAnchor="middle" fontFamily={HEAD} fontSize={50} fill={C.yellow} letterSpacing={3}>
            APPROVED
          </text>
        </g>
      </g>
      <g transform={`translate(200 20) scale(${cal})`} opacity={Math.min(1, cal * 1.5)}>
        <Calendar mark={mark} label="JOB DAY" />
      </g>
    </g>
  );
};

// STEP 6 — paving: roller lays fresh asphalt over the old cracked driveway, then COMPLETE
export const Ill6: Ill = ({f, dur}) => {
  const h = pop(f, 0);
  const end = Math.max(30, dur - 14);
  const p = lerp(f, 6, end, 0, 1, Easing.inOut(Easing.quad));
  const top = -150, bot = 250, y = top + (bot - top) * p;
  const done = pop(f, end + 2);
  return (
    <g transform={`translate(0 -10) scale(${0.95 * h})`} opacity={Math.min(1, h * 1.4)}>
      <g transform="translate(0 -150) scale(0.5)">
        <House />
      </g>
      <defs>
        <clipPath id="drive">
          <path d={`M -95 ${top} H 95 L 175 ${bot} H -175 Z`} />
        </clipPath>
      </defs>
      <g clipPath="url(#drive)">
        <rect x={-200} y={top} width={400} height={bot - top} fill="#6b6c6e" />
        <path d="M -60 -100 l 30 40 l -20 30 l 40 50 M 50 20 l -25 45 l 30 30 l -15 60 M -120 160 l 50 20 l 10 40" fill="none" stroke="#3b3c3e" strokeWidth={5} />
        <rect x={-200} y={top} width={400} height={y - top} fill={C.fresh} />
        <rect x={-200} y={y - 20} width={400} height={20} fill="#232426" opacity={0.8} />
      </g>
      <path d={`M -95 ${top} H 95 L 175 ${bot} H -175 Z`} fill="none" stroke={C.white} strokeWidth={5} />
      {p < 1 && (
        <g transform={`translate(0 ${y})`}>
          <rect x={-70} y={-110} width={140} height={78} rx={12} fill={C.yellow} />
          <rect x={-34} y={-96} width={68} height={34} rx={6} fill={C.bg} opacity={0.6} />
          <rect x={-120} y={-34} width={240} height={40} rx={20} fill="#c9c8c2" stroke={C.white} strokeWidth={4} />
        </g>
      )}
      <g transform="translate(250 140)">
        <Check x={0} y={0} r={70} t={done} />
      </g>
      <text x={250} y={250} textAnchor="middle" fontFamily={HEAD} fontSize={46} fill={C.yellow} opacity={Math.min(1, done)}>
        COMPLETE
      </text>
    </g>
  );
};

export const ILLS = [Ill1, Ill2, Ill3, Ill4, Ill5, Ill6];
export const STEPS = [
  {title: 'Reach Out', sub: 'Request online, call, text, or leave a voicemail with a few details about your job.'},
  {title: 'We Call You', sub: 'Your asphalt specialist gathers the details and schedules an on-site visit.'},
  {title: 'Meet On Site', sub: 'Walk the project together: details, options, and our recommendations.'},
  {title: 'Get Your Price', sub: 'On the spot when possible — otherwise by email or text within a day or two.'},
  {title: 'Approve & Schedule', sub: 'Sign off on the job and we lock in your date.'},
  {title: 'Job Done', sub: 'We show up, do the work, and complete your project.'},
];

export const fadeUp = (f: number, start: number, d = 14) => ({
  opacity: interpolate(f, [start, start + d * 0.7], [0, 1], clamp),
  transform: `translateY(${lerp(f, start, start + d, 40, 0)}px)`,
});
