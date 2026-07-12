# DhanSaarthi (धनसारthी) — Avatar Wealth Advisor for IDBI Bank

> **IDBI Innovate 2026 · Track 01 — Wealth Advisory** · prototype cost **₹0** · runs **fully offline**

A digital-human wealth advisor inside the IDBI app that reads a customer's **real
spending behaviour** through India's Account Aggregator framework, turns it into
**SEBI-safe, explainable** advice — and lets them talk to their own 60-year-old
**"Future Self"** to feel where today's habits lead.

The core idea that makes it trustworthy: **a deterministic Python engine computes
every number; a firewalled LLM only narrates.** The avatar can never say a rupee
figure the engine did not produce.

---

## The demo in one screen

> Aarav (27) opens the app → approves an AA consent sheet → Saarthi greets him by
> name → *"You're spending about **₹4,800/month** on food delivery. Redirect just
> **₹2,400** into a low-cost index SIP — over **33 years** that grows to about
> **₹74.76 lakh**."* → **Why this advice?** shows the Bogle principle + the exact
> math + the config version hashes → one tap and his **Future Self at 60** thanks
> him → **Start SIP →** fires an idempotent deep-link into an IDBI journey.
>
> Every number is engine-computed, validated, and audit-logged. No API keys. No
> internet.

---

## Quickstart (two commands)

**Backend** — FastAPI advisory engine (Python 3.11+):

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate      # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```
`GET http://localhost:8000/health` → `{"status":"ok","mode":"offline","advisory_mode":"on"}`

**Frontend** — Next.js avatar PWA (Node 18+), in a second terminal:

```bash
cd frontend
npm install
npm run dev
```
Open **http://localhost:3000** in **Chrome** (voice input is Chrome-only). Pick a
persona → Approve consent → chat. That's the whole golden path, offline.

> Optional flags (all default to the offline path): `GEMINI_API_KEY` enables LLM
> narration (validated against the engine, falls back to templates); `ENABLE_TTS=1`
> enables neural edge-tts voice (else the browser speaks); `ADVISORY_MODE=info_only`
> is the governance kill-switch (chat explains concepts, returns no recommendations).

---

## Architecture

Full design: **[docs/architecture.md](docs/architecture.md)** (interactive version with the
container diagram + failure catalogue is linked at the top of that file).

Four invariants govern every decision:

1. **Determinism boundary** — the LLM never computes; the engine never speaks. Every
   figure travels with a `reasoning_trace` + a `NumericClaimSet`; an output validator
   rejects any numeral outside that set → one retry → template fallback.
2. **Sidecar, not rewrite** — bank integration only through adapter ports + an AA FIU
   client; execution is idempotent deep-link *intents*, never core-banking writes.
3. **Consent is the schema** — FI data enters only via the AA framework; consent is
   checked at **read time** every turn; revocation triggers erasure (DPDP).
4. **Graceful degradation** — LLM→templates, edge-tts→browser speech, WebGL→2D
   portrait, no-AA→declared data. The demo runs with every third party removed.

**Stack:** Python/FastAPI + pandas engines · SQLite · firewalled Gemini narrator
(offline template default) · Next.js PWA + 2D SVG avatar (TalkingHead-ready) ·
Web Speech STT · edge-tts / browser TTS. Money is **integer paise** everywhere.

---

## How v1 carries its SDLC gate evidence

This prototype is built so the hackathon's software-delivery gates have artefacts,
not promises:

| Gate | Evidence in this repo |
|---|---|
| **Risk & Compliance Review** (pre-design) | [docs/compliance-gate.md](docs/compliance-gate.md) — DPDP basis, SEBI model-risk position (deterministic ⇒ interpretable by construction), advice-vs-distribution perimeter, suitability-veto + kill-switch controls. Model card: [docs/model-card.md](docs/model-card.md). |
| **QA / Security** | `pytest` **116 tests** green offline (determinism, golden fixtures, numeral-validator, prompt-injection quarantine, fairness). `pip-audit` on pinned `requirements.txt`: **no known vulnerabilities**. No secrets in repo; `.env` gitignored. |
| **Monitoring & Governance** | Append-only **audit store** + in-app **Governance panel** (`GET /audit`): every turn logs strategy, `engine_ver`, `shelf@sha`, `strategy@sha`, suitability outcome, narration hash — bit-for-bit replayable. Config change control: [docs/change-log.md](docs/change-log.md) (CAB). |

---

## Judge script (2 minutes)

Full version with talking points: **[docs/pitch.md](docs/pitch.md)**.

1. **Consent** — pick *Aarav (young_spender)*, approve the AA sheet. "Data enters only with consent, purpose-bound."
2. **Insight** — "What should I do with my money?" → the food-delivery → SIP line with real numbers. "The LLM narrated; the engine computed."
3. **Why** — expand *Why this advice?* → principle + math + version hashes. "Every recommendation is explainable and replayable — SEBI's interpretability pillar."
4. **Future Self** — "Show me my future self" → the aged avatar thanks him; toggle *If you wait* for the darker branch. "Behavioural economics, not a chatbot."
5. **Start SIP** — tap it → the deep-link intent. "We recommend; IDBI's existing rails execute. Zero transaction risk."
6. **Governance** — open the 🛡️ drawer. "This is the regulator's-eye view of the advice you just heard."
7. **Guardrail** — switch to *Mohan (near_retiree)* and ask "the market is crashing, should I sell?" → Marks cycle framing, no exit. The suitability gate silently withholds aggressive-equity advice from a 54-year-old.

---

## What's real vs. synthetic (honest scope)

- **Real & production-shaped:** the deterministic engines, the determinism-boundary
  validator, the suitability veto, the consent/audit model, the ReBIT FI-JSON schema,
  the adapter-port seams, integer-paise money math.
- **Synthetic for the prototype:** AA data comes from a deterministic generator emitting
  ReBIT-schema FI-JSON for 5 personas (`scripts/generate_aa_data.py`) — swapping to IDBI's
  sandbox is one adapter. Product rates in `product_shelf.yaml` are illustrative.
- **Out of scope for v1 (documented, not built):** JWT/SSO bridge, Redis, SQS, real AA
  integration, Bedrock, full PII tokenizer, maker-checker tooling, cloud deployment.
- The "advice" is **guidance + IDBI-product distribution**, not RIA advice; full RIA
  registration is an explicit future-scope module.

---

## Tests & regeneration

```bash
cd backend && .venv\Scripts\activate
pytest                                   # 116 tests, offline/template mode only
python scripts/generate_aa_data.py       # regenerate the 5 persona FI-JSON files (deterministic)
python scripts/build_goldens.py          # regenerate advice golden fixtures (reviewable diff)
python scripts/build_golden_script.py    # regenerate the cached demo narration
```

## Repo layout

```
backend/   app/engines/ (behavioral · advisory · projection · suitability · money)
           app/llm/     (narrator + numeral validator)
           app/data/    (*.yaml config-as-product + personas/*.json)
           app/main.py  (FastAPI: consent · chat · future-self · intent · audit · tts)
           tests/       (116 tests + golden/ fixtures)
frontend/  app/ components/ lib/   (Next.js avatar PWA)
docs/      architecture · model-card · compliance-gate · change-log · pitch
```

*Prototype cost: ₹0 · Submission: 2026-07-13 · Track 01 — Wealth Advisory.*
