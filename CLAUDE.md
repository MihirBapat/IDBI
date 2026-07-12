# CLAUDE.md — DhanSaarthi

## 1. Project overview

DhanSaarthi: avatar-based, Account-Aggregator-powered wealth advisor for IDBI Bank (IDBI Innovate 2026, Track 01; prototype submission **2026-07-13**, cost must stay ₹0). Stack: Python/FastAPI backend (deterministic advisory engines + Gemini narration) + Next.js PWA frontend (TalkingHead.js 3D avatar). Spec: [PRD.md](PRD.md). Architecture: [docs/architecture.md](docs/architecture.md).

## 2. Setup & commands

Scaffold exists as of Part 1. Verified working commands (Windows host):

- Backend venv: `cd backend && python -m venv .venv && .venv\Scripts\activate`. Deps are pinned in `backend/requirements.txt` (`pip install -r requirements.txt`).
- **Never install anything system-wide or globally. If something truly needs a system-level install, STOP and ask the user first** (RULES.MD).
- Run API: `uvicorn app.main:app --reload` from `backend/` → `GET /health` returns `{"status":"ok","mode":"offline"}`.
- Tests: `pytest` from `backend/` (18 passing as of Part 1). Tests must stay in offline/template mode — never call Gemini or edge-tts.
- Regenerate synthetic AA data: `python scripts/generate_aa_data.py` from `backend/` → writes `app/data/personas/{persona_id}.json` (deterministic, byte-identical across runs).
- Frontend: `cd frontend && npm install && npm run dev` (Next.js App Router, TS, no Tailwind).

## 3. Architecture

Full detail in [docs/architecture.md](docs/architecture.md) — read it before structural changes. Four invariants override everything, including new feature requests; if a change violates one, the change is wrong:

1. **Determinism boundary.** The LLM never computes; the engine never speaks. Every number comes from the deterministic engines and travels with a `reasoning_trace` + `NumericClaimSet`. An output validator rejects any LLM output containing a numeral outside the claim set → one retry → template fallback. Nothing ever flows from narrator back to engine.
2. **Sidecar, not rewrite.** Bank integration only through the adapter ports in `backend/app/adapters/` (CustomerProfile, Accounts, Transactions, ProductShelf) + AA FIU client. Execution actions are idempotency-keyed deep-link intents into existing IDBI journeys — never direct transaction writes.
3. **Consent is the schema.** FI data enters only via the AA framework (synthetic generator emits ReBIT-schema FI-JSON from day 1). Check consent at read time on every turn, not just at fetch. Revocation → erasure (DPDP).
4. **Graceful degradation.** Every dependency has a tested fallback (L0–L4 ladder): LLM→templates, edge-tts→browser speech, WebGL→2D portrait, no-AA→declared-data mode. The demo must run fully offline (no-LLM mode).

Repo layout (PRD §9): `backend/app/engines/` (behavioral, advisory, projection — pure, deterministic, unit-tested), `backend/app/llm/narrator.py` (Gemini + offline fallback), `backend/app/data/*.yaml` (product shelf + strategy library — config as product, every trace pins their versions), `backend/scripts/generate_aa_data.py` (5 personas), `frontend/components/AvatarStage.tsx`.

Non-obvious decisions (rationale in architecture doc §11): modular monolith, not microservices; client-side avatar rendering only; money is integer paise everywhere — no floats, ₹ lakh/crore formatting happens in the engine, never in the LLM; raw merchant strings are quarantined at ingest (prompt-injection surface) — only closed-vocabulary category codes reach prompts; projections use conservative returns only (10% equity / 6.5% debt nominal).

## 4. Conventions & workflow

- Build order: follow PRD §8 phases / §9 milestone prompts strictly, in order. Current stage: **Part 1 (Foundation) complete** — scaffold + synthetic AA data (5 personas) landed and gated; next is Part 2 (deterministic engines), see [IMPLEMENTATION.md](IMPLEMENTATION.md). Update this line as parts complete.
- Every feature must move a bank metric (SIP conversion, CASA, cross-sell, RM cost) — think as an IDBI financial manager (RULES.MD).
- Every engine output must carry a `reasoning_trace` naming the strategy applied (PRD §3A); write pytest cases per persona for each engine before moving on.
- Every LLM-facing response gets the SEBI disclosure footer appended **in code, not in the prompt**.
- No git repo exists yet; when initializing, commit at each phase boundary.

## 5. Boundaries

- `PRD.md`, `RULES.MD`, `PROBLEM STATEMENT.txt` — source-of-truth inputs; never edit without explicit user instruction.
- `backend/.venv/` — never commit, never edit by hand.
- `backend/app/data/*.yaml` — treat as versioned config: change via deliberate edits the user reviews, never as a side effect of a code fix.
- `.env` / API keys — gitignored; never hardcode keys.

## 6. Domain glossary

- **AA / FIP / FIU** — RBI Account Aggregator framework; we act as the FIU (data consumer). FIPs are banks/RTAs/insurers. The AA relay is data-blind.
- **Fingerprint** — Behavioral Financial Fingerprint: `savings_ratio, spend_leaks[], sip_discipline, idle_cash, insurance_gap, risk_capacity` computed by `engines/behavioral.py`, each field with staleness metadata.
- **NumericClaimSet** — the set of pre-formatted numerals the engine permits in a narration; the validator's whitelist.
- **reasoning_trace** — per-recommendation audit record: strategy, inputs, math, `engine_ver`, `shelf@sha`, `strategy@sha`.
- **Strategy Library** — `strategy_library.yaml`: 10 codified manager playbooks (Bogle, Buffett, Dalio, Swensen, Lynch, Marks, Markowitz, Vanguard Advisor's Alpha, goals-based, Graham) as `trigger_conditions → allocation_template → explanation_snippet → source_principle`.
- **Future Self** — avatar swap to aged GLB + deterministic 30-year projection script (good/bad branches) from `engines/projection.py`.
- **Saarthi** — the advisor avatar persona (Hindi: charioteer/guide).
- **ReBIT FI-JSON** — the AA data schema; the synthetic generator emits exactly this so the sandbox swap is one adapter.
- **Golden path** — the scripted demo flow with pre-cached narration/audio; must survive total LLM outage.

## 7. Gotchas

- **Gemini free tier: 10 RPM / 1,500 req/day.** Never put the LLM on a hot loop or in tests; tests must run in offline template mode.
- Web Speech STT works in Chrome only — demo in Chrome; STT is on-device, only text crosses the wire.
- edge-tts needs internet; the offline demo path must pre-cache golden-path audio and fall back to browser SpeechSynthesis.
- Windows host: activate venv with `.venv\Scripts\activate`; Claude's Bash tool is Git Bash (`source .venv/Scripts/activate`), PowerShell differs.
- The "advice" is legally guidance + bank-product distribution, not RIA advice — never add products outside the IDBI shelf, never stock tips, never optimistic return assumptions.
- Deadline is 2026-07-13: prefer the PRD's scoped 2-day plan over gold-plating; polish the golden path before adding breadth.

Revise this file as real friction points emerge during the build — it is a living document, not a final spec.
