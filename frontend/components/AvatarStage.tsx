"use client";

import { useEffect, useState } from "react";

// 2D-portrait avatar (mandatory fallback, shipped first per the build plan). A
// WebGL capability probe runs so a future TalkingHead.js 3D GLB can be layered
// in; if WebGL is missing the experience is unchanged. The mouth animates while
// Saarthi speaks and the ring reflects speaking/listening state.

function AvatarSVG({ aged, speaking }: { aged: boolean; speaking: boolean }) {
  const skin = aged ? "#c9a07c" : "#d8a06a";
  const hair = aged ? "#c8d0cb" : "#0f6f4c";
  const hairEdge = aged ? "#aeb8b2" : "#0a4d35";
  return (
    <svg viewBox="0 0 200 200" width="220" height="220" aria-label="Saarthi avatar">
      <defs>
        <radialGradient id="bg" cx="50%" cy="35%" r="75%">
          <stop offset="0%" stopColor="#153a2a" />
          <stop offset="100%" stopColor="#0a1712" />
        </radialGradient>
      </defs>
      <circle cx="100" cy="100" r="98" fill="url(#bg)" />
      {/* shoulders */}
      <path d="M35 200 C45 158 70 150 100 150 C130 150 155 158 165 200 Z"
        fill={aged ? "#26463a" : "#124a35"} />
      {/* neck */}
      <rect x="88" y="120" width="24" height="26" rx="10" fill={skin} />
      {/* head */}
      <circle cx="100" cy="96" r="42" fill={skin} />
      {/* hair / turban wrap */}
      <path d="M58 92 C58 60 142 60 142 92 C142 78 128 62 100 62 C72 62 58 78 58 92 Z"
        fill={hair} stroke={hairEdge} strokeWidth="2" />
      <path d="M60 90 C70 82 130 82 140 90" fill="none" stroke={hairEdge} strokeWidth="2" opacity="0.6" />
      {/* eyes */}
      <g className="eyes">
        <circle cx="86" cy="96" r="4.2" fill="#20140c" />
        <circle cx="114" cy="96" r="4.2" fill="#20140c" />
      </g>
      {/* brows */}
      <path d="M79 87 q7 -5 14 0" fill="none" stroke="#3a2416" strokeWidth="2" strokeLinecap="round" />
      <path d="M107 87 q7 -5 14 0" fill="none" stroke="#3a2416" strokeWidth="2" strokeLinecap="round" />
      {/* nose */}
      <path d="M100 100 l-4 12 q4 3 8 0" fill="none" stroke="#a9713f" strokeWidth="2" strokeLinecap="round" />
      {/* aged beard */}
      {aged && (
        <path d="M72 116 C78 140 122 140 128 116 C122 126 78 126 72 116 Z"
          fill="#d6ded9" opacity="0.9" />
      )}
      {/* mouth (animated while speaking) */}
      <ellipse className={`mouth ${speaking ? "talk" : ""}`} cx="100" cy="122"
        rx="12" ry="5" fill="#7a2f2f" />
    </svg>
  );
}

export default function AvatarStage({
  speaking,
  listening,
  aged = false,
  caption,
  disclosure,
}: {
  speaking: boolean;
  listening: boolean;
  aged?: boolean;
  caption?: string;
  disclosure?: string;
}) {
  const [webgl, setWebgl] = useState<boolean | null>(null);

  useEffect(() => {
    try {
      const c = document.createElement("canvas");
      setWebgl(Boolean(c.getContext("webgl") || c.getContext("experimental-webgl")));
    } catch {
      setWebgl(false);
    }
  }, []);

  return (
    <div className="stage">
      <div className="avatar-wrap">
        <div
          className={`avatar-ring ${speaking ? "speaking" : ""} ${
            listening ? "listening" : ""
          }`}
        />
        <AvatarSVG aged={aged} speaking={speaking} />
      </div>
      <div className="mode-badge">
        {aged ? "Future Self · " : ""}2D portrait avatar
        {webgl ? " · WebGL ready" : ""}
        {listening ? " · listening…" : speaking ? " · speaking…" : ""}
      </div>
      {caption !== undefined && (
        <div className="caption">
          {caption || "…"}
          {disclosure && <span className="disc">{disclosure}</span>}
        </div>
      )}
    </div>
  );
}
