# Part 1 of 5 — Foundation (Scaffold + Synthetic AA data)

> **Context for a fresh session:** Read [CLAUDE.md](../CLAUDE.md) and [docs/architecture.md](../docs/architecture.md) first. This is part 1 of a 5-part build; the index and progress tracker are in [IMPLEMENTATION.md](../IMPLEMENTATION.md). Obey the invariants at every step — LLM never computes, money is integer paise, everything installs in the venv. Work steps in order; do not start a step until the previous gate passes. **When both gates in this part pass, commit and STOP — the user resumes with Part 2.**

---

## Step 0 — Scaffold (gate: both servers boot)

1. `git init` in `D:\IDBI`; create `.gitignore` (`.venv/`, `node_modules/`, `.env`, `__pycache__/`, `.next/`, `*.sqlite`).
2. Create the PRD §9 tree: `backend/app/{engines,llm,adapters,data}/`, `backend/scripts/`, `backend/tests/`, `frontend/`, `docs/`.
3. `cd backend && python -m venv .venv`; install in venv: `fastapi uvicorn[standard] pandas pyyaml pydantic edge-tts google-generativeai pytest httpx`.
4. `backend/app/main.py`: FastAPI app, CORS for `http://localhost:3000`, `GET /health` → `{"status":"ok","mode":"offline"}`.
5. Scaffold frontend: `npx create-next-app@latest frontend --ts --app --no-tailwind` (ask user only if npx needs a global install). Add `npm run dev` proxy or use full URLs to `http://localhost:8000`.
6. Commit: `phase0: scaffold`.

**Gate:** `uvicorn app.main:app` serves `/health`; `npm run dev` renders the default page.

## Step 1 — Synthetic AA data (gate: 5 persona files validate)

`backend/scripts/generate_aa_data.py` → writes `backend/app/data/personas/{persona_id}.json` in ReBIT-style FI-JSON:

- Blocks: `deposit` (12 months of transactions with `type CREDIT|DEBIT`, `amount` (paise), `narration`, `valueDate`, `txnId`, running `currentBalance`), `term_deposit[]`, `mutual_funds[]` (scheme, folio, units, nav, costValue, currentValue, sipFlag + sipHistory), `profile` (maskedAccNumber, holder name, age).
- 5 personas, deterministic via fixed `random.seed(persona_id)`: `young_spender` (27y, ₹4.8k/mo Swiggy+Zomato, no SIP, ₹40k balance), `disciplined_saver` (34y, regular ₹10k SIP, 30% savings ratio), `idle_cash` (41y, ₹3.2L idle in savings, sporadic FDs), `over_insured` (38y, 4 insurance debits, thin equity), `near_retiree` (54y, ₹18L FDs, no equity glide).
- Include realistic salary credits (1st of month), UPI merchant narrations (these test the quarantine rule), subscription debits (Netflix, Spotify).
- Add `backend/app/schemas.py`: pydantic models for the FI-JSON + `Fingerprint` + `Recommendation` + `ReasoningTrace`.

**Gate:** `pytest tests/test_data.py` — all 5 files parse into pydantic models; totals reconcile (balances = opening + credits − debits).

---

**STOP HERE.** Commit (`phase1: synthetic AA data`), update the tracker in [IMPLEMENTATION.md](../IMPLEMENTATION.md), and end the session. Next: [Part 2 — Deterministic core](PART-2-core-engines.md).
