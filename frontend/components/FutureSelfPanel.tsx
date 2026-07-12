"use client";

import type { ProjectionScript } from "@/lib/types";

// Future Self: the aged avatar (swapped in the stage) narrates the 30-year
// projection line-by-line. Numbers come straight from the engine's script text,
// so nothing is formatted or invented here.

export default function FutureSelfPanel({
  script,
  branch,
  onBranch,
  onReplay,
  busy,
}: {
  script: ProjectionScript | null;
  branch: "good" | "bad";
  onBranch: (b: "good" | "bad") => void;
  onReplay: () => void;
  busy: boolean;
}) {
  return (
    <div className="card" style={{ marginTop: 16 }}>
      <div className="section-title">Future Self · at 60</div>
      <div className="branch-toggle">
        <button
          className={`btn ${branch === "good" ? "btn-gold" : ""}`}
          onClick={() => onBranch("good")}
        >
          If you invest
        </button>
        <button
          className={`btn ${branch === "bad" ? "btn-gold" : ""}`}
          onClick={() => onBranch("bad")}
        >
          If you wait
        </button>
        <button className="btn btn-ghost" onClick={onReplay} disabled={busy}>
          ▶ Replay
        </button>
      </div>

      {script && (
        <>
          <div style={{ color: "var(--muted)", fontSize: 13, marginTop: 12 }}>
            {script.horizon_years}-year outlook · conservative 10% assumption
          </div>
          <div className="future-lines">
            {script.lines.map((l, i) => (
              <div key={i} className="future-line">
                {l.text}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
