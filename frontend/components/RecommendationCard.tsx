"use client";

import { useState } from "react";
import { ApiError, emitIntent } from "@/lib/api";
import type { Recommendation } from "@/lib/types";
import WhyTrace from "./WhyTrace";

const CTA: Record<string, string> = {
  start_sip: "Start SIP",
  step_up_sip: "Step up SIP",
  move_to_fd: "Open FD",
  deploy_all_weather: "Deploy",
  diversify_sip: "Start SIP",
  deploy_9010: "Invest",
};

// A recommendation card with allocation chips, a suitability badge, the "Why"
// trace, and a "Start →" button that fires an idempotency-keyed /intent
// (re-clicking returns the same deep-link — exactly-once at the port).

export default function RecommendationCard({
  rec,
  personaId,
  execDisabled,
}: {
  rec: Recommendation;
  personaId: string;
  execDisabled?: boolean;
}) {
  const [link, setLink] = useState<string | null>(null);
  const [dup, setDup] = useState(false);
  const [busy, setBusy] = useState(false);
  const vetoed = rec.status === "VETO";

  async function start() {
    setBusy(true);
    try {
      // Stable key per recommendation → a second tap is idempotent.
      const res = await emitIntent(personaId, rec.rec_id, rec.rec_id);
      setLink(res.deep_link);
      setDup(res.duplicate);
    } catch (e) {
      setLink(e instanceof ApiError ? `Error ${e.status}: ${e.message}` : "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rec-card">
      <div className="rec-head">
        <div>
          <div className="rec-title">{rec.title}</div>
          <div className="rec-strategy">{rec.strategy_id}</div>
        </div>
        <span className={`status ${rec.status}`}>{rec.status}</span>
      </div>

      <div className="chips">
        {Object.entries(rec.allocation).map(([k, v]) => (
          <span key={k} className="chip">
            {k} {v}%
          </span>
        ))}
      </div>

      <div className="rec-actions">
        {!vetoed && (
          <button
            className="btn btn-primary"
            onClick={start}
            disabled={busy || execDisabled}
            title={execDisabled ? "Execution paused under governance review" : ""}
          >
            {busy ? <span className="spinner" /> : `${CTA[rec.action] ?? "Start"} →`}
          </button>
        )}
        {vetoed && (
          <span className="deep-link">
            Withheld by the suitability gate — not suitable for this customer.
          </span>
        )}
      </div>

      {link && (
        <div className="deep-link" style={{ marginTop: 8 }}>
          {dup ? "(idempotent) " : ""}
          {link}
        </div>
      )}

      <WhyTrace trace={rec.reasoning_trace} />
    </div>
  );
}
