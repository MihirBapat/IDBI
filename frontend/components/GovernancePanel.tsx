"use client";

import { useEffect, useState } from "react";
import { getAudit } from "@/lib/api";
import type { AuditRow } from "@/lib/types";

// The judge-facing Monitoring & Governance surface: the session's audit trail,
// as the regulator would see it — strategy, pinned config shas, suitability
// outcome, and a hash of the exact narration spoken.

export default function GovernancePanel({
  personaId,
  onClose,
}: {
  personaId: string;
  onClose: () => void;
}) {
  const [rows, setRows] = useState<AuditRow[] | null>(null);

  useEffect(() => {
    getAudit(personaId)
      .then((r) => setRows(r.rows))
      .catch(() => setRows([]));
  }, [personaId]);

  return (
    <div className="gov-drawer">
      <h3>
        🛡️ Governance &amp; audit
        <button
          className="btn btn-ghost"
          style={{ marginLeft: "auto" }}
          onClick={onClose}
        >
          Close
        </button>
      </h3>
      <p style={{ color: "var(--muted)", fontSize: 13, marginTop: 6 }}>
        Every turn is recorded as a regulator would see it — strategy, pinned
        config versions, suitability outcome, and a hash of the exact words
        spoken (bit-for-bit replayable, SEBI 5-year test).
      </p>

      {rows === null && (
        <div className="gov-empty">
          <span className="spinner" /> loading…
        </div>
      )}
      {rows && rows.length === 0 && (
        <div className="gov-empty">No turns recorded yet.</div>
      )}
      {rows && rows.length > 0 && (
        <table className="gov-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Intent</th>
              <th>Strategy</th>
              <th>Versions</th>
              <th>Suitability</th>
              <th>Narration</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{new Date(r.ts).toLocaleTimeString()}</td>
                <td>{r.intent}</td>
                <td>{r.strategy_id ?? "—"}</td>
                <td className="sha">
                  {r.engine_ver ?? "—"}
                  {r.shelf_sha && (
                    <>
                      <br />
                      shelf@{r.shelf_sha}
                    </>
                  )}
                  {r.strategy_sha && (
                    <>
                      <br />
                      strat@{r.strategy_sha}
                    </>
                  )}
                </td>
                <td>
                  {r.suitability_outcome ?? "—"} · {r.advisory_mode}
                </td>
                <td className="sha">{r.narration_hash.slice(0, 12)}…</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
