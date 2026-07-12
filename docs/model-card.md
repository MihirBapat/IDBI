# Model Card — DhanSaarthi Advisory "Model"

**DHS-MC-001 · v1.0 · 2026-07-12** · Companion to [architecture.md](architecture.md) and
[compliance-gate.md](compliance-gate.md).

## What the "model" is

DhanSaarthi's advice is **not** a learned model. It is a **deterministic rule matrix**
over a behavioral fingerprint, plus a suitability screen, plus an *optional* LLM used
only to phrase the result. This is a deliberate governance choice: the component that
decides *what* is advised is fully interpretable and testable; the probabilistic
component demonstrably **cannot change a recommendation**.

| Layer | Type | Role | Can it change a number? |
|---|---|---|---|
| Behavioral engine (`engines/behavioral.py`) | deterministic pandas | FI-JSON → fingerprint | produces numbers |
| Advisory engine (`engines/advisory.py`) + `strategy_library.yaml` | deterministic rules | fingerprint → recommendations | produces numbers |
| Projection engine (`engines/projection.py`) | deterministic math | goal / Future-Self projections | produces numbers |
| Suitability gate (`engines/suitability.py`) + `suitability_rules.yaml` | deterministic rules | PASS / SOFTEN / VETO | can only *remove/soften* |
| Narrator (`llm/narrator.py`) | template **or** Gemini | phrasing only | **no** — validator-gated |

## Inputs, outputs, and what is *not* an input

- **Inputs:** consented AA FI-JSON only → a behavioral fingerprint
  (`savings_ratio, spend_leaks[], sip_discipline, idle_cash, equity_holding,
  insurance_gap, risk_capacity, monthly_income, age`), each with staleness metadata.
- **Explicitly not inputs:** name, PAN, gender, caste, religion, address. The FI schema
  refuses to carry sensitive attributes (`test_fairness.py` asserts this). Identical
  behaviour ⇒ identical advice regardless of who the customer is.
- **Outputs:** a list of `Recommendation`s, each with an `allocation`, an
  `amount_paise`, a `NumericClaimSet`, and a `reasoning_trace`.

## Assumptions & limits

- Projections use **conservative** nominal returns (10% equity / 6.5% debt) — Graham's
  margin of safety encoded; never optimistic.
- Advice is restricted to the **IDBI product shelf** and to allocation/cost/diversification/
  cycle/behaviour/goal strategies. No stock tips, leverage, or derivatives.
- Insurance gap is a documented **heuristic proxy**, flagged as low-confidence, not a
  needs-analysis.
- Prototype data is synthetic (ReBIT schema); real AA fetch is a single adapter swap.

## SEBI Responsible AI/ML — five-pillar mapping (June 2025 guidelines)

| Pillar | How v1 satisfies it |
|---|---|
| **Governance & accountability** | Determinism boundary caps what AI can do; sole-liability posture (Reg 16C). Config behind version pins + a documented CAB ([change-log.md](change-log.md)). Kill-switch `ADVISORY_MODE=info_only`. |
| **Interpretability / explainability** | Every recommendation ships a printed `reasoning_trace` (strategy, math steps, principle) exposed in-UI as "Why this advice?". The advice "model" is a readable rule matrix. |
| **Testing & model risk** | 5 personas × strategy library = golden fixtures in CI; determinism tests (byte-identical reruns); numeral-validator (`test_narrator`); suitability veto (`test_suitability`); fairness (`test_fairness`). 116 tests, offline. |
| **Fairness & bias** | Fairness *by construction*: sensitive attributes are never collected or input; `test_fairness.py` proves name/PAN/label don't move the advice. |
| **Investor protection & disclosure** | SEBI disclosure appended **in code** on every narration; suitability gate vetoes unsuitable advice and records a `refusal_reason`; panic intents route to cycle-framing, never an exit path. |

## Monitoring

Append-only audit store (`GET /audit`, in-app Governance panel) records per turn:
`ts, intent, strategy_id, engine_ver, shelf@sha, strategy@sha, suitability_outcome,
narration_hash, advisory_mode` — supporting bit-for-bit replay (SEBI 5-year record test)
and periodic accuracy/again-review reporting.
