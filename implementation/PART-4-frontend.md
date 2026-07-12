# Part 4 of 5 — Frontend (Avatar UI, consent flow, Future Self, governance panel)

> **Context for a fresh session:** Read [CLAUDE.md](../CLAUDE.md) and [docs/architecture.md](../docs/architecture.md) first. This is part 4 of a 5-part build; index and progress tracker in [IMPLEMENTATION.md](../IMPLEMENTATION.md). **Prerequisite: Part 3 gates pass** (narrator + validator + all API endpoints green). This part is the Next.js PWA that talks to the API from Part 3. Obey the invariants. **Ship the 2D fallback before the 3D avatar** so "avatar based" is satisfied even if TalkingHead fights you. **When the gate passes, commit and STOP — the user resumes with Part 5.**

---

## Step 6 — Frontend (gate: manual E2E on localhost)

Keep it three screens in `frontend/app/`, dark IDBI-green theme:

1. `ConsentFlow.tsx` — persona picker (5 cards) + AA-style consent sheet (scope/frequency/expiry, Approve/Deny) → `POST /consent`.
2. `page.tsx` + `AvatarStage.tsx` — TalkingHead.js with Ready Player Me GLB in `public/avatars/saarthi.glb`; **capability probe first**: if WebGL fails or GLB missing, render 2D portrait PNG + animated captions (this fallback is mandatory, ship it first, then add 3D).
3. Chat panel: text input + mic button (Web Speech, Chrome); render transcript; "Why this advice?" expander showing `reasoning_trace` fields verbatim (including any `refusal_reason` when the engine declined); recommendation cards with "Start SIP →" calling `/intent`.
4. Future Self button: swap to `saarthi_aged.glb` (or aged 2D portrait) + play `/future-self` script line-by-line with TTS.
5. Audio: try `GET /tts`; on 503/error use `speechSynthesis` — never block on audio.
6. `GovernancePanel.tsx` — a collapsible "Governance" drawer calling `GET /audit`: shows the audit trail for the session (strategy, versions/shas, suitability outcome, narration hash). This is the judge-facing evidence for the Monitoring & Governance gate — the advice they just heard, as the regulator would see it.

**Gate:** manual run-through of the full golden path in Chrome with backend in template mode, network devtools showing zero external calls.

---

**STOP HERE.** Commit (`phase6: frontend`), update the tracker in [IMPLEMENTATION.md](../IMPLEMENTATION.md), and end the session. Next: [Part 5 — Hardening & submission](PART-5-hardening-submission.md).
