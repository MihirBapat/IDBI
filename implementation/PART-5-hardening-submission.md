# Part 5 of 5 — Hardening & submission (tests, gate-evidence docs, README, clone-test)

> **Context for a fresh session:** Read [CLAUDE.md](../CLAUDE.md) and [docs/architecture.md](../docs/architecture.md) first. This is the final part of a 5-part build; index and progress tracker in [IMPLEMENTATION.md](../IMPLEMENTATION.md). **Prerequisite: Part 4 gate passes** (full golden path runs in Chrome, offline). This part hardens the demo, writes the gate-evidence docs, and produces the submission. The final gate — the fresh-clone test — is the submission gate; nothing ships until it's green.

---

## Step 7 — Tests, demo hardening, submission (gate: fresh-clone test)

1. `pytest` full suite green; add `backend/tests/test_offline_demo.py`: scripted golden path (consent → 4 chat turns → future-self → intent) end-to-end via httpx asserting every spoken number ∈ claims.
2. Add `backend/tests/test_fairness.py` (SEBI fairness pillar): assert the same fingerprint yields byte-identical advice regardless of holder name/gender/persona label — passes because those fields are never inputs, which is the fairness story made testable.
3. Pre-cache golden-path narration text in `data/golden_script.yaml` (used if even templates need tweaking on stage).
4. Write `README.md`: 2-command quickstart (`backend: pip install -r requirements.txt && uvicorn app.main:app` / `frontend: npm i && npm run dev`), architecture diagram link, screenshot/GIF, judge script (the exact 2-minute demo path), honest scope notes. **Frame the demo around the SDLC gates**: one line each showing how v1 carries evidence for Risk & Compliance Review, QA/Security, and Monitoring & Governance. Generate `requirements.txt` via `pip freeze`.
5. Write the gate-evidence docs:
   - `docs/model-card.md` — model = rule matrix + suitability screen + optional Gemini narration; SEBI five-pillar mapping (pull from docs/architecture.md §10).
   - `docs/compliance-gate.md` — the pre-design **Risk & Compliance Review** on one page: DPDP privacy basis, SEBI model-risk position (deterministic = interpretable by construction), advice-vs-distribution perimeter, and the suitability-veto + kill-switch controls.
   - `docs/change-log.md` — the **CAB** control: config (`strategy_library.yaml`, `product_shelf.yaml`) is versioned, maker-checker reviewed, and pinned by `@sha` in every trace.
   - `docs/pitch.md` — 2-min script.
6. Security-gate pass: pin `requirements.txt`, run `pip-audit` once (install in venv) and record the result, confirm no secrets in the repo and `.env` is gitignored, confirm the prompt-injection quarantine test (Step 4 / Part 3) is green.
7. Update CLAUDE.md stage line; final commit; verify: **clone the repo to a temp dir, follow README verbatim on a clean venv, run the golden path**. Fix anything that breaks; that clone test is the submission gate.

---

## Cutlines if time runs short (drop from the bottom, never the top)

1. 3D GLB avatar → ship the 2D portrait + captions fallback as primary (feature-complete, still "avatar based").
2. Gemini mode → template mode only (already the default; note it as a flag in README).
3. Hindi narration → English + Hinglish snippets only.
4. edge-tts → browser SpeechSynthesis only.

**Never cut:** determinism tests, the validator, consent gating, the suitability veto, "Why this advice?" trace, the governance/audit panel, Future Self projection, README clone-test. These are the gate evidence — they are the differentiator, not polish.

## Out of scope for v1 (do not build)

JWT/SSO bridge, Redis, SQS/EventBridge, real AA integration, Bedrock, PII tokenizer beyond `{NAME}` slots, real maker-checker workflow tooling (documented as a control, not built), deployment to Vercel/Render (localhost is the submission target; deploy only if time remains after Step 7).

---

**DONE.** When the fresh-clone test is green, the repo is submittable. Update the tracker in [IMPLEMENTATION.md](../IMPLEMENTATION.md) to mark all parts complete.
