"use client";

import type { ReasoningTrace } from "@/lib/types";

// The "Why this advice?" expander — shows the reasoning_trace verbatim, including
// any refusal_reason when the engine declined. This is the explainability surface.

export default function WhyTrace({ trace }: { trace: ReasoningTrace }) {
  return (
    <details className="why">
      <summary>Why this advice?</summary>
      <div className="trace">
        <div>
          <strong>Principle:</strong> {trace.source_principle}
        </div>
        <div style={{ marginTop: 8 }}>
          <strong>How the number was reached:</strong>
        </div>
        {trace.math_steps.map((s, i) => (
          <div key={i} className="step">
            • <code>{s}</code>
          </div>
        ))}
        {trace.refusal_reason && (
          <div className="refusal">⛔ Declined: {trace.refusal_reason}</div>
        )}
        <div style={{ marginTop: 8 }} className="sha">
          engine {trace.engine_ver} · shelf@{trace.shelf_sha} · strategy@
          {trace.strategy_sha}
        </div>
      </div>
    </details>
  );
}
