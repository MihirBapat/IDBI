"use client";

import { useEffect, useState } from "react";

// Reveals text progressively on mount (the Gemini-style "streaming" feel).
// Used only for the most recent assistant message; older ones render in full.

export default function Streamed({
  text,
  speed = 14,
  onTick,
}: {
  text: string;
  speed?: number;
  onTick?: () => void;
}) {
  const [shown, setShown] = useState(0);

  useEffect(() => {
    setShown(0);
    let i = 0;
    const id = setInterval(() => {
      i += 1;
      setShown(i);
      onTick?.();
      if (i >= text.length) clearInterval(id);
    }, speed);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text]);

  return <>{text.slice(0, shown)}</>;
}
