# Risk & Compliance Review — pre-design gate (one page)

**DHS-CG-001 · v1.0 · 2026-07-12** · The compliance position taken *before* build, and the
architectural controls that enforce it. Companions: [model-card.md](model-card.md),
[change-log.md](change-log.md), [architecture.md](architecture.md) §10.

## 1. Data-privacy basis (DPDP Act 2023 · RBI NBFC-AA)

- **Lawful basis:** explicit, purpose-bound consent via the RBI Account Aggregator
  framework (purpose `102`, wealth management; FI types Deposit/TD/RD/Mutual Funds;
  monthly frequency; 12-month expiry). No datum exists without a live consent artefact.
- **Purpose limitation & minimisation:** only category-coded, derived features reach any
  prompt; raw merchant strings are quarantined at ingest; sensitive attributes
  (name/PAN/gender/…) are **never collected** (schema refuses them).
- **Read-time enforcement:** consent is re-checked on **every** turn, not just at fetch;
  a revocation blocks the next turn and **evicts the fingerprint** (crypto-erasure path;
  DPDP ≤72h in production). Endpoint: `DELETE /consent`.
- **Security:** TLS 1.3 + AES-256-GCM envelope in production; prototype keeps no secrets
  in-repo, `.env` gitignored, `pip-audit` clean on pinned deps.

## 2. SEBI model-risk position

- The advice engine is a **deterministic rule matrix + suitability screen** — interpretable
  **by construction**, not by post-hoc explanation. The probabilistic (LLM) layer is a
  rendering surface that provably cannot alter a number (validator + audit).
- Maps to SEBI Responsible AI/ML (June 2025) five pillars and Intermediaries (Amendment)
  Regs 2025 Reg 16C sole-liability — evidenced continuously by CI ([model-card.md](model-card.md)).

## 3. Advice-vs-distribution perimeter

- v1 is scoped to **guidance + distribution of IDBI's own products** (permitted for banks),
  **not** RIA advice. No products outside the IDBI shelf; no stock tips; no optimistic math.
- Full RIA registration + suitability records + automated reporting is an explicit
  **future-scope** module, not claimed here.

## 4. Controls that enforce the position

| Risk | Control | Where |
|---|---|---|
| AI states a fabricated number | Numeral-membership validator → 1 retry → template; escape budget **zero** | `llm/validator.py`, `test_narrator.py` |
| Prompt injection via merchant text | Closed-vocabulary quarantine at ingest; only category codes reach prompts | `data/category_map.yaml`, `test_behavioral.py`, `test_narrator.py` |
| Unsuitable advice (e.g. aggressive equity to a near-retiree) | Suitability **VETO** with recorded `refusal_reason`; vetoed recs never reach the narrator | `engines/suitability.py`, `test_suitability.py` |
| Panic-selling in a downturn | Marks cycle guardrail: panic intents → goal math / Future Self, never an exit deep-link | `main.py` (PANIC), `test_api.py` |
| Governance stop | **Kill-switch** `ADVISORY_MODE=info_only`: explains concepts, returns no recs, refuses intents | `main.py`, `test_api.py` |
| Silent config drift | Every trace pins `shelf@sha` + `strategy@sha`; a rate change is a failing golden diff | `engines/advisory.py`, `tests/golden/`, [change-log.md](change-log.md) |
| Unfair/discriminatory advice | Sensitive attributes never inputs; fairness proven | `test_fairness.py` |

## 5. Residual risks accepted for the prototype

Synthetic (not live) AA data; illustrative product rates; insurance-gap is a heuristic;
no JWT/SSO, Redis, or real erasure pipeline (documented, production seams drawn). None
affect the advice-plane correctness that the gates evidence.
