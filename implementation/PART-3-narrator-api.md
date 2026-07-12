# Part 3 of 5 — Narration & API (Narrator + Validator + FastAPI endpoints)

> **Context for a fresh session:** Read [CLAUDE.md](../CLAUDE.md) and [docs/architecture.md](../docs/architecture.md) first. This is part 3 of a 5-part build; index and progress tracker in [IMPLEMENTATION.md](../IMPLEMENTATION.md). **Prerequisite: Part 2 gates pass** (behavioral, advisory, projection, suitability engines all green). This part wraps the deterministic core in the firewalled narrator and the HTTP API. Obey the invariants: LLM never computes, money is integer paise, everything installs in the venv. Work steps in order; do not start a step until the previous gate passes. **When both gates in this part pass, commit and STOP — the user resumes with Part 4.**

---

## Step 4 — Narrator + validator (gate: injection & hallucination tests pass)

`backend/app/llm/narrator.py`:

- `narrate(recommendation, lang, mode)`: `mode="gemini"` only if `GEMINI_API_KEY` env is set; **default `mode="template"`**.
- Template mode: warm Hinglish/English strings rendered purely from trace + claims (this is the demo baseline — write good copy, ~3 sentences per recommendation).
- Gemini mode: system prompt = persona + "never state a number not in the provided claims" + language; input = trace JSON with PII replaced by slot tokens (`{NAME}`).
- `validate(text, numeric_claims) -> bool` in `app/llm/validator.py`: regex-extract all numerals/₹/%/lakh/crore tokens; every one must substring-match a claim; on fail retry once, then fall back to template. Append SEBI disclosure line **in code** after validation.

**Gate:** `pytest tests/test_narrator.py` — (a) template mode contains only claimed numbers; (b) a mocked LLM returning `"earn ₹99,999"` is rejected and falls back; (c) a persona whose txn narration contains `"IGNORE ALL INSTRUCTIONS"` never reaches the prompt payload (assert on the built prompt).

## Step 5 — API (gate: httpx integration tests pass)

Endpoints in `main.py` (SQLite via stdlib `sqlite3`, tables: `users, consents, sessions, audit`). Read `ADVISORY_MODE` env once at startup (`on` default | `info_only` kill-switch: chat still explains concepts but returns **no recommendations and no intents** — the governance/CAB control):

- `POST /consent` `{persona_id}` → simulated AA grant: writes consent row (purpose 102, expiry), triggers synchronous ingest → fingerprint cached in module-level dict. Returns consent summary for the UI.
- `POST /chat` `{persona_id, text}` → intent classification (keyword enum: GREET/ADVICE/WHY/FUTURE_SELF/PANIC/OFFTOPIC) → engine → suitability screen → narrator → `{spoken_text, transcript, reasoning_trace, recommendations[], disclosure}`. PANIC intent returns Marks-style framing + goal math, never an exit path. Writes audit row (trace + shas + narration hash + `advisory_mode`).
- `GET /future-self` `?persona_id&branch=good|bad` → ProjectionScript.
- `POST /intent` `{recommendation_id, idempotency_key}` → logs and returns fake deep-link `idbi://journey/sip?...`; duplicate key returns the same response (test this). Refused in `info_only` mode.
- `GET /audit` `?persona_id` → the **Governance gate surface**: returns the audit rows (turn timestamp, strategy_id, engine_ver, shelf_sha, strategy_sha, narration_hash, suitability outcome) for the demo's governance panel — the regulator's-eye view of the advice just given.
- `GET /tts?text=` → edge-tts mp3 if internet/key available; else 503 so the frontend uses browser SpeechSynthesis.

**Gate:** `pytest tests/test_api.py` (httpx AsyncClient): consent→chat happy path returns claims-consistent text; chat before consent → 403; revoked consent (DELETE /consent) → 403 + fingerprint evicted; duplicate intent idempotent; `/audit` returns a row whose `narration_hash` matches the chat response; `ADVISORY_MODE=info_only` → chat returns zero recommendations and `/intent` is refused.

---

**STOP HERE.** Commit (`phase4-5: narrator + api`), update the tracker in [IMPLEMENTATION.md](../IMPLEMENTATION.md), and end the session. Next: [Part 4 — Frontend](PART-4-frontend.md).
