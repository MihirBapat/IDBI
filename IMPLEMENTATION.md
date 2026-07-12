# IMPLEMENTATION.md — Prototype v1 build index (submission due 2026-07-13)

The build is split into **5 self-contained parts** so it can be done across sessions without exhausting a token budget mid-step. Each part ends at a gate boundary: when its gate passes, **commit, update the tracker below, and stop** — the next session opens the next part with full context. Every part file carries its own context header, so a fresh session only needs to read [CLAUDE.md](CLAUDE.md), [docs/architecture.md](docs/architecture.md), and the one part file.

**Invariants (from [CLAUDE.md](CLAUDE.md), apply to every part):** the LLM never computes — it narrates engine output validated against a NumericClaimSet; money is integer paise, formatted only in the engine; FI data enters only via consent; everything installs in the venv; offline template mode is the baseline (Gemini/edge-tts are enhancements).

**Definition of done for v1:** a judge clones the repo, runs two commands, opens one URL, and experiences: consent screen → avatar greets by name → behavioral insight spoken with real numbers → "Why this advice?" trace → Future Self transformation → "Start SIP" intent — **with zero API keys and no internet.**

---

## The 5 parts

| Part | File | Scope | Gate to pass before stopping |
|---|---|---|---|
| 1 | [PART-1-foundation.md](implementation/PART-1-foundation.md) | Scaffold (Step 0) + synthetic AA data (Step 1) | both servers boot; 5 persona files validate |
| 2 | [PART-2-core-engines.md](implementation/PART-2-core-engines.md) | Behavioral + advisory + projection + suitability engines (Steps 2–3) | golden fixtures pass; determinism byte-identical; suitability veto works |
| 3 | [PART-3-narrator-api.md](implementation/PART-3-narrator-api.md) | Narrator + validator + FastAPI endpoints (Steps 4–5) | injection/hallucination tests pass; API integration tests pass |
| 4 | [PART-4-frontend.md](implementation/PART-4-frontend.md) | Next.js avatar UI, consent flow, Future Self, governance panel (Step 6) | full golden path runs in Chrome, offline |
| 5 | [PART-5-hardening-submission.md](implementation/PART-5-hardening-submission.md) | Tests, gate-evidence docs, README, fresh-clone test (Step 7) | fresh-clone test green = submittable |

---

## Progress tracker (update at the end of each part)

- [x] **Part 1 — Foundation** · gate: servers boot + persona files validate ✅ (backend `/health` boots; 5 persona files validate + reconcile — `pytest` 18 passed)
- [x] **Part 2 — Deterministic core** · gate: golden fixtures + determinism + suitability ✅ (behavioral/advisory/projection/suitability engines; `pytest` 83 passed; data + goldens byte-identical across runs; near-retiree aggressive-equity veto works)
- [ ] **Part 3 — Narration & API** · gate: injection/hallucination + API tests
- [ ] **Part 4 — Frontend** · gate: golden path in Chrome, offline
- [ ] **Part 5 — Hardening & submission** · gate: fresh-clone test green

**Current stage:** Part 2 complete — deterministic engines (behavioral, advisory, projection, suitability) landed and gated. Next: [Part 3 — Narration & API](implementation/PART-3-narrator-api.md).

> When resuming: check the tracker for the first unchecked part, open its file, confirm the previous part's gate still passes (`pytest` from `backend/`), then continue.
