"use client";

import { useState } from "react";
import { grantConsent, ApiError } from "@/lib/api";
import { PERSONAS, type PersonaCard } from "@/lib/personas";
import type { ConsentSummary } from "@/lib/types";

// Screen 1: persona picker + an Account-Aggregator-style consent sheet. Approving
// simulates the AA grant (purpose 102) and triggers the backend ingest.

export default function ConsentFlow({
  onGranted,
}: {
  onGranted: (persona: PersonaCard, consent: ConsentSummary) => void;
}) {
  const [selected, setSelected] = useState<PersonaCard | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function approve() {
    if (!selected) return;
    setBusy(true);
    setError(null);
    try {
      const { consent } = await grantConsent(selected.id);
      onGranted(selected, consent);
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? `${e.status}: ${e.message}`
          : "Could not reach the DhanSaarthi API. Is the backend running on :8000?";
      setError(msg);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="hero">
        <h2>Meet Saarthi — your wealth guide</h2>
        <p>
          Choose a customer to step into. Saarthi reads their consented accounts
          through the Account Aggregator framework and gives SEBI-safe,
          explainable advice — no questionnaires, just real behaviour.
        </p>
      </div>

      <div className="persona-grid">
        {PERSONAS.map((p) => (
          <button
            key={p.id}
            className="persona-card"
            onClick={() => {
              setSelected(p);
              setError(null);
            }}
          >
            <div className="persona-emoji">{p.emoji}</div>
            <div className="pname">{p.name}</div>
            <div className="meta">
              Age {p.age} · {p.id}
            </div>
            <div className="tag">{p.tagline}</div>
          </button>
        ))}
      </div>

      {selected && (
        <div className="overlay" onClick={() => !busy && setSelected(null)}>
          <div className="sheet" onClick={(e) => e.stopPropagation()}>
            <h3>Share financial information?</h3>
            <div className="aa">Account Aggregator consent · data-blind relay</div>
            <div style={{ marginTop: 14 }}>
              <div className="consent-row">
                <span className="k">Consumer (FIU)</span>
                <span>IDBI DhanSaarthi</span>
              </div>
              <div className="consent-row">
                <span className="k">Customer</span>
                <span>
                  {selected.name} · {selected.id}
                </span>
              </div>
              <div className="consent-row">
                <span className="k">Purpose</span>
                <span>102 · Wealth management</span>
              </div>
              <div className="consent-row">
                <span className="k">FI types</span>
                <span>Deposit · Term Deposit · RD · Mutual Funds</span>
              </div>
              <div className="consent-row">
                <span className="k">Frequency · Expiry</span>
                <span>Monthly · 12 months</span>
              </div>
            </div>
            {error && (
              <div style={{ color: "var(--danger)", fontSize: 13, marginTop: 12 }}>
                {error}
              </div>
            )}
            <div className="consent-actions">
              <button
                className="btn btn-ghost"
                onClick={() => setSelected(null)}
                disabled={busy}
              >
                Deny
              </button>
              <button className="btn btn-primary" onClick={approve} disabled={busy}>
                {busy ? <span className="spinner" /> : "Approve & continue"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
