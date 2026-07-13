"use client";

import { useEffect, useState } from "react";

import SaarthiAvatar from "./SaarthiAvatar";

// Full "stage" presentation of Saarthi (used for immersive / Future-Self views).
// The identity is the emotive orb (no human face); a WebGL probe stays so a
// future TalkingHead.js GLB could layer in without changing this fallback. The
// ring reflects speaking/listening state.

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
        <SaarthiAvatar size={220} speaking={speaking} aged={aged} />
      </div>
      <div className="mode-badge">
        {aged ? "Future Self · " : ""}Saarthi
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
