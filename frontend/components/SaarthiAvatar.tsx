"use client";

import { useId } from "react";

// Saarthi's identity is an emotive "spark" orb — deliberately NOT a human face
// (no uncanny valley). It breathes gently when idle and comes alive with a
// voice-equalizer + reactive glow while speaking. Green for the present-day
// guide; warm gold for the aged Future Self. Props are unchanged so callers
// need no edits.

export default function SaarthiAvatar({
  size = 48,
  speaking = false,
  aged = false,
}: {
  size?: number;
  speaking?: boolean;
  aged?: boolean;
}) {
  // Unique gradient/filter ids per instance (many orbs render at once).
  const uid = useId().replace(/:/g, "");

  // Palette: present-day Saarthi (green) vs aged Future Self (amber/gold).
  const c = aged
    ? { core: "#f4d38a", mid: "#d99a3c", edge: "#a86a1e", glow: "#e9b85a", spark: "#fff2d6" }
    : { core: "#8ff0c2", mid: "#1aa564", edge: "#0a5c3c", glow: "#25c078", spark: "#eafff5" };

  // Five equalizer bars; staggered so the "voice" looks organic while speaking.
  const bars = [
    { x: 78, delay: "0s" },
    { x: 88, delay: "0.18s" },
    { x: 98, delay: "0.06s" },
    { x: 108, delay: "0.24s" },
    { x: 118, delay: "0.12s" },
  ];

  return (
    <svg
      viewBox="0 0 200 200"
      width={size}
      height={size}
      className={`saarthi-orb ${speaking ? "speaking" : ""} ${aged ? "aged" : ""}`}
      aria-label="Saarthi"
      role="img"
    >
      <defs>
        <radialGradient id={`core-${uid}`} cx="42%" cy="38%" r="72%">
          <stop offset="0%" stopColor={c.core} />
          <stop offset="45%" stopColor={c.mid} />
          <stop offset="100%" stopColor={c.edge} />
        </radialGradient>
        <radialGradient id={`glow-${uid}`} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={c.glow} stopOpacity="0.55" />
          <stop offset="70%" stopColor={c.glow} stopOpacity="0.12" />
          <stop offset="100%" stopColor={c.glow} stopOpacity="0" />
        </radialGradient>
        <filter id={`soft-${uid}`} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2.2" />
        </filter>
      </defs>

      {/* Outer aura — breathes when idle, flares while speaking. */}
      <circle className="orb-aura" cx="100" cy="100" r="96" fill={`url(#glow-${uid})`} />

      {/* Rotating orbit rings give the orb a sense of life and "attention". */}
      <g className="orb-rings" stroke={c.glow} fill="none" strokeLinecap="round">
        <circle className="ring ring-a" cx="100" cy="100" r="82" strokeWidth="1.6"
          strokeDasharray="8 200" opacity="0.85" />
        <circle className="ring ring-b" cx="100" cy="100" r="72" strokeWidth="1.4"
          strokeDasharray="6 120" opacity="0.5" />
      </g>

      {/* Core orb. */}
      <circle className="orb-core" cx="100" cy="100" r="62" fill={`url(#core-${uid})`} />
      {/* Glossy highlight + a drifting inner "thought" blob. */}
      <ellipse className="orb-shine" cx="82" cy="80" rx="26" ry="18" fill={c.spark} opacity="0.35"
        filter={`url(#soft-${uid})`} />
      <circle className="orb-blob" cx="112" cy="116" r="16" fill={c.spark} opacity="0.18"
        filter={`url(#soft-${uid})`} />

      {/* Voice equalizer — animates only while speaking; a calm dot when idle. */}
      <g className="orb-eq" fill={c.spark}>
        {bars.map((b, i) => (
          <rect
            key={i}
            className="eq-bar"
            x={b.x}
            y="90"
            width="5"
            height="20"
            rx="2.5"
            style={{ animationDelay: b.delay }}
          />
        ))}
      </g>
      <circle className="orb-idle-dot" cx="100" cy="100" r="5" fill={c.spark} opacity="0.9" />
    </svg>
  );
}
