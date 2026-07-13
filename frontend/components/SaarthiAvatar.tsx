"use client";

// Compact Saarthi avatar (the "spark" identity for the Gemini-style chat).
// 2D SVG portrait; mouth animates while speaking; aged variant for Future Self.

export default function SaarthiAvatar({
  size = 48,
  speaking = false,
  aged = false,
}: {
  size?: number;
  speaking?: boolean;
  aged?: boolean;
}) {
  const skin = aged ? "#c9a07c" : "#d8a06a";
  const hair = aged ? "#c8d0cb" : "#0f6f4c";
  const hairEdge = aged ? "#aeb8b2" : "#0a4d35";
  return (
    <svg
      viewBox="0 0 200 200"
      width={size}
      height={size}
      className={`saarthi-av ${speaking ? "speaking" : ""}`}
      aria-label="Saarthi"
    >
      <defs>
        <radialGradient id="sav-bg" cx="50%" cy="30%" r="80%">
          <stop offset="0%" stopColor="#1c8f5f" />
          <stop offset="55%" stopColor="#0f6f4c" />
          <stop offset="100%" stopColor="#0a4d35" />
        </radialGradient>
      </defs>
      <circle cx="100" cy="100" r="98" fill="url(#sav-bg)" />
      <path d="M35 200 C45 158 70 150 100 150 C130 150 155 158 165 200 Z"
        fill={aged ? "#2a4a3d" : "#0c3c2b"} />
      <rect x="88" y="120" width="24" height="26" rx="10" fill={skin} />
      <circle cx="100" cy="96" r="42" fill={skin} />
      <path d="M58 92 C58 60 142 60 142 92 C142 78 128 62 100 62 C72 62 58 78 58 92 Z"
        fill={hair} stroke={hairEdge} strokeWidth="2" />
      <g className="eyes">
        <circle cx="86" cy="96" r="4.2" fill="#20140c" />
        <circle cx="114" cy="96" r="4.2" fill="#20140c" />
      </g>
      <path d="M79 87 q7 -5 14 0" fill="none" stroke="#3a2416" strokeWidth="2" strokeLinecap="round" />
      <path d="M107 87 q7 -5 14 0" fill="none" stroke="#3a2416" strokeWidth="2" strokeLinecap="round" />
      <path d="M100 100 l-4 12 q4 3 8 0" fill="none" stroke="#a9713f" strokeWidth="2" strokeLinecap="round" />
      {aged && (
        <path d="M72 116 C78 140 122 140 128 116 C122 126 78 126 72 116 Z"
          fill="#d6ded9" opacity="0.9" />
      )}
      <ellipse className={`mouth ${speaking ? "talk" : ""}`} cx="100" cy="122"
        rx="12" ry="5" fill="#7a2f2f" />
    </svg>
  );
}
