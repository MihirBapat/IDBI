# PRD — "DhanSaarthi" (धनसारथी)
## Avatar-Based Behavioral AI Wealth Advisor for IDBI Bank
### IDBI Innovate 2026 — Track 01: Wealth Advisory | Conversational AI | Mobile Banking

> **This PRD is written for Claude Code.** Follow it top-to-bottom. Build order, repo structure, and milestone prompts are in Section 9. All installs go in a Python virtual environment (`python -m venv .venv`). If any dependency needs a system-level install, STOP and ask the user first.

---

## 0. The One-Line Pitch

**A digital human wealth advisor inside the IDBI mobile app that reads your real spending behavior (via India's Account Aggregator framework), converts it into SEBI-safe, explainable investment advice — and lets you talk to your own 60-year-old "Future Self" to see where your habits are taking you.**

---

## 1. Proposed Solution in Simple English

Today, a wealthy IDBI customer gets a relationship manager. Everyone else gets nothing — India has roughly **1 registered investment advisor per 200,000 investors**. IDBI's problem statement says exactly this: wealth advisory is fragmented, inaccessible, and blind to the customer's actual investment behavior and spending habits.

DhanSaarthi fixes this with three connected ideas:

**Idea 1 — An advisor with a face.** Inside the IDBI app, the customer talks (voice or text, English/Hindi) to a 3D avatar named "Saarthi" — a photorealistic digital human that speaks with lip-sync, remembers the customer, and explains money in plain language. This directly matches the expected outcome ("Avatar Based" digital wealth app). OCBC Bank launched exactly this ("Wendy" and "Wayne" avatars) in July 2026, proving the model is bank-grade — but nobody in India has shipped it yet. IDBI can be first.

**Idea 2 — Advice from behavior, not questionnaires.** Every robo-advisor in India starts with a 10-question risk quiz that customers lie on. DhanSaarthi instead pulls the customer's *actual* bank statements, mutual fund holdings, and UPI spending through India's **Account Aggregator (AA) framework** (RBI-regulated, consent-based, 284M+ linked accounts). From this it computes a live **Behavioral Financial Fingerprint**: savings ratio, spend leaks (food delivery, subscriptions), SIP discipline, idle cash in savings accounts, insurance gaps. The avatar then gives advice like: *"You keep ₹3.2 lakh idle in savings earning 3%. Moving ₹2 lakh to IDBI's FD ladder earns you ₹14,000 more per year. Also — your Swiggy spend is ₹4,800/month; half of that as a SIP becomes ₹19 lakh by your retirement."* That is advice no questionnaire can produce.

**Idea 3 — The "Future Self" (the demo moment that wins).** One tap, and the avatar ages into the customer's own future self at 60, and speaks from that future: *"Because you started a ₹6,000 SIP at 27, I retired with ₹2.4 crore. Thank you."* Or the darker branch: *"You skipped investing for 5 more years. I'm still working at 64."* Behavioral economics research (Hershfield's "future self-continuity" studies) shows people who interact with their aged self save significantly more. This is the emotional hook + AI + measurable business impact (SIP conversion) in one feature. No Indian bank has it.

**How the advice stays safe:** the LLM never invents numbers. A deterministic Python **Advisory Engine** (rule matrix + goal math + IDBI's actual product shelf) computes every recommendation; the LLM only *narrates and explains* the engine's output. Every recommendation carries an "explain why" trace. This maps directly to SEBI's 2025 AI/ML guidelines (model interpretability, investor disclosure, human-comprehensible reasoning) — a compliance story most hackathon teams won't have.

---

## 2. Feasibility, Practicality & Lean Canvas

### 2.1 Feasibility
| Dimension | Assessment |
|---|---|
| Technical | All components are proven OSS: TalkingHead.js (3D lip-sync avatar, browser-native, MIT), Gemini Flash free tier (1,500 req/day), Edge-TTS/Web Speech (free voice). Prototype in 2 days is realistic. |
| Regulatory | AA framework is live & RBI-regulated (BOI, and IDBI is an AA FIU-ready bank). SEBI's Securities Markets Code (Dec 2025) explicitly recognizes robo-advisory platforms. Deterministic engine + disclosures aligns with SEBI Intermediaries (Amendment) Regulations 2025 (Chapter on AI usage). |
| Data | Prototype uses a **synthetic AA data generator** (realistic FI-JSON in Sahamati schema). Swaps to IDBI's synthetic datasets/sandbox APIs when shortlisted — zero rework because we code against the AA schema from day 1. |
| Market timing | India robo-advisory market: ~$512M (2025) → projected ~$7B by 2034 (33% CAGR). OCBC just validated avatar banking globally (July 2026). |

### 2.2 Practicality challenges (honest view)
- Real-time photoreal avatar on low-end Android → mitigated: TalkingHead.js renders a lightweight GLB avatar in WebGL inside a WebView; falls back to 2D portrait + audio on weak devices.
- LLM latency on free tier → mitigated: engine computes advice instantly; LLM streams narration; scripted fallback lines if API is slow.
- "Is this investment advice legally?" → prototype is *guidance + bank-product distribution* (banks may distribute their own products); full RIA registration is a deployment-phase item, flagged in Future Scope.

### 2.3 Lean Canvas
| Block | Content |
|---|---|
| **Problem** | Advisory inaccessible below HNI tier; advice ignores real behavior; 1 RIA per 200k investors |
| **Segments** | Mass + mass-affluent IDBI customers (₹1L–₹5Cr assets), tier 2/3 cities, first-time investors, vernacular users |
| **UVP** | *The only advisor that has actually read your bank statement — and shows you your future self* |
| **Solution** | Avatar advisor + AA-powered behavioral fingerprint + deterministic advisory engine + Future Self simulator |
| **Channels** | IDBI mobile app (embedded WebView/SDK), later net-banking & branch kiosks |
| **Revenue (bank's)** | ↑ SIP/FD/insurance cross-sell, ↑ CASA retention, ↓ RM cost per customer, fee income from MF distribution |
| **Cost structure** | Prototype ₹0; production = cloud inference + AA FIU fees (per-fetch ~₹2–5) — trivially covered by one incremental FD |
| **Key metrics** | SIP conversion rate, assets-linked-via-AA per user, weekly active advisory sessions, idle-cash activated |
| **Unfair advantage** | Bank-grade trust + AA FIU license + customer's full transaction history — fintechs can't replicate the trust; other banks haven't built the avatar |

---

## 3. Tech Stack (Total Cost: ₹0)

| Layer | Choice | Why / Cost |
|---|---|---|
| Frontend | **Next.js (React) PWA**, mobile-first, dark IDBI-green theme | Free; embeds in bank app as WebView later |
| Avatar | **TalkingHead.js** (met4citizen, MIT) + **Ready Player Me** free avatar GLBs (young + aged variants for Future Self) | Real-time 3D lip-sync in browser, zero GPU server |
| Voice out (TTS) | **edge-tts** (free Microsoft neural voices, incl. hi-IN & en-IN) via backend; browser SpeechSynthesis fallback | Free, no key |
| Voice in (STT) | Browser **Web Speech API** (Chrome, free) | Free |
| LLM | **Gemini Flash free tier** (10 RPM / 1,500 req/day — enough for demos) | Free; strictly narration/chat, never computation |
| Advisory Engine | **Python + FastAPI**: rule matrix, goal-based math (SIP futures, FD ladders, asset-allocation buckets by behavioral profile), IDBI product shelf as YAML | Free, deterministic, auditable |
| Behavioral engine | **pandas** over synthetic AA FI-JSON: savings ratio, spend categories, SIP regularity, idle-cash detector | Free |
| Data | **SQLite** for prototype (users, consents, sessions); synthetic AA generator script | Free |
| Deployment | Local demo (laptop) — judges see localhost or free tier: Vercel (frontend) + Render/HF Spaces (API) | Free |
| Repo/CI | GitHub free | Free |

**Cost challenge accepted:** the only realistic risk to ₹0 is Gemini free-tier throttling mid-demo. Mitigations: pre-cached narration for the scripted demo path + deterministic engine works with LLM fully offline (template narration mode). The demo cannot die.

---

## 3A. Advisory Strategy Library — Codified from the World's Notable Investment Managers

The Advisory Engine is not a generic rule matrix. It ships with a **Strategy Library** (`app/data/strategy_library.yaml`): the proven playbooks of the world's most notable investment managers, translated into deterministic rules for Indian retail products. Every recommendation cites which principle produced it — the avatar can say *"this follows the same principle Yale's endowment used"* — a storytelling + trust weapon no other team will have.

| # | Manager / Source | Their strategy | How DhanSaarthi codifies it (engine rule) |
|---|---|---|---|
| 1 | **Jack Bogle** (Vanguard) | Low-cost passive indexing; three-fund portfolio; "costs matter" | Default equity vehicle = low-cost Nifty/Sensex index funds & ETFs from IDBI's MF shelf, never high-TER regular plans when a cheaper equivalent exists. Engine computes and *shows* the fee drag in ₹ over 20 years. |
| 2 | **Warren Buffett** | 90/10 rule (S&P 500 + short-term govt bonds); circle of competence; long holding periods | "Buffett Simple" model portfolio for hands-off users: 90% index equity / 10% liquid-gilt (scaled by age). Avatar enforces "circle of competence": never narrates products the user hasn't been shown the basics of. Discourages exit before 5-year horizon with holding-period math. |
| 3 | **Ray Dalio** (Bridgewater) | All-Weather / risk-parity: assets balanced across economic regimes (growth↑↓ × inflation↑↓) | "All-Weather India" bucket for conservative profiles: equity index + long-duration gilt funds + short-duration debt + **Sovereign Gold Bonds/gold ETF** — the engine's crash-resilient allocation. Used in Future Self "bad market" branch to show drawdown protection. |
| 4 | **David Swensen** (Yale) | Asset allocation > security selection; 6-asset diversified retail model (incl. REITs & inflation-linked bonds); equity orientation with diversification | Engine's core axiom: allocation decided *first* by profile, products picked second. Swensen retail model mapped to India: domestic equity index, international FoF, REITs/InvITs (listed), gilt funds, floating-rate/inflation-hedged debt. |
| 5 | **Peter Lynch** (Fidelity Magellan) | "Invest in what you know"; behavior-revealed insight | The AA twist: the engine reads spend categories the user *actually knows* (heavy UPI spend on retail, autos, pharma) and uses them as relatable examples when explaining sector/index exposure — education device, not stock-tip engine (keeps it SEBI-safe). |
| 6 | **Howard Marks** (Oaktree) | Market cycles; second-level thinking; risk management over return chasing | Cycle-aware guardrails: when user asks "markets crashed, should I exit?", engine responds with Marks-style cycle framing + the user's own goal math; blocks panic-exit deep-links and offers "talk to Future Self" instead. |
| 7 | **Harry Markowitz** (Nobel, MPT) | Diversification is the only free lunch; mean-variance efficiency | Fingerprint's `risk_capacity` maps to an efficient-frontier band of pre-computed allocations; concentration alerts when >30% of wealth sits in one asset (incl. idle savings = 100% cash concentration). |
| 8 | **Vanguard "Advisor's Alpha"** (research, ~3%/yr value of good advising) | Behavioral coaching (+1.5%), rebalancing (+0.35%), tax location/harvesting (+0.75%), low costs (+0.45%) | This is DhanSaarthi's quantified ROI story: the avatar IS the behavioral coach (panic-call interception, SIP-discipline nudges), auto-rebalancing alerts, Indian tax optimization (80C laddering, LTCG ₹1.25L harvesting window, debt-vs-FD tax math). Judges get a research-backed number for the value created. |
| 9 | **Goals-based wealth mgmt** (Brunel/Chhabra, private-banking standard) | Bucket strategy: safety / stability / aspiration buckets per life goal | Every user goal (emergency, house, education, retirement) gets its own bucket with its own allocation + glide path that de-risks as the goal date nears — exactly how private bankers serve HNIs, automated for everyone. |
| 10 | **Benjamin Graham** | Margin of safety; "Mr. Market" is manic-depressive; investor's chief problem is himself | Engine never projects with optimistic returns (uses conservative 10% equity / 6.5% debt nominal); Mr. Market metaphor is in the avatar's teaching script; behavioral fingerprint flags the user's own worst instinct (panic seller / FOMO buyer / procrastinator) and tailors coaching to it. |

**Design rule:** the LLM narrator may *quote the philosophy*; only the engine applies the math. Each strategy is a YAML entry: `trigger_conditions → allocation_template → explanation_snippet → source_principle`. This makes the library extensible (add a new manager = add YAML, no code) and fully auditable for SEBI interpretability norms.

**Honest scope note:** strategies that require stock-picking, leverage, or derivatives (Soros's reflexivity trades, Simons's quant arb, Buffett's concentrated bets, Lynch's tenbaggers as literal stock tips) are deliberately **excluded** — they are unsuitable and non-compliant for mass-retail bank advisory. We codify only what translates safely: allocation, cost discipline, diversification, cycles, behavior, and goals. Judges will respect the discernment.

---

## 4. Scalability & Security

**Scalability**
- Avatar rendering is **client-side** (WebGL) → zero server GPU cost per user; scales like a static asset.
- Stateless FastAPI advisory engine → horizontal pods behind a load balancer; engine call is pure computation (<10ms).
- LLM layer is swappable (Gemini → AWS Bedrock on IDBI's provided AWS infra) behind one interface class.
- AA data fetches are event-driven (consent grant / monthly refresh), cached per user — not per chat message.
- Vernacular scale: TTS voice + LLM system prompt are config values → adding Marathi/Tamil is configuration, not code.

**Security**
- **No credentials ever touch us**: AA framework means the customer consents at their AA app; data arrives encrypted, digitally signed, purpose-bound, revocable (RBI NBFC-AA master directions).
- Prototype ships with: JWT sessions, TLS-only, AES-256 encryption at rest for FI data, PII tokenization before any text reaches the LLM (names/amounts masked → re-hydrated in the response), consent ledger table (who shared what, when, purpose, expiry).
- **LLM guardrails**: system-prompt firewall + output validator — the model cannot output a number that the engine didn't produce; profanity/off-topic deflection; every response appended with SEBI-style disclosure.
- Audit trail: every recommendation stored with engine inputs → 5-year retention per SEBI AI/ML consultation norms; model documentation kept in `/docs/model-card.md`.
- DPDP Act 2023 alignment: purpose limitation, consent withdrawal endpoint, data-deletion endpoint.

---

## 5. Compatibility with Bank APIs & Systems like IDBI

Designed as a **sidecar, not a rewrite** of IDBI's core:

1. **Integration surface = 4 adapter interfaces** (`/adapters/`): `CustomerProfileAdapter`, `AccountsAdapter`, `ProductShelfAdapter`, `TransactionsAdapter`. Prototype implements them against synthetic data; sandbox phase re-implements them against IDBI's sandbox REST APIs — the engine and avatar never change.
2. **Mobile embedding**: the PWA runs inside IDBI GO's existing WebView with a JS bridge for SSO token handoff — the standard pattern banks use to ship features without core-app releases.
3. **Account Aggregator**: IDBI operates within the RBI AA ecosystem as FIP/FIU; DhanSaarthi acts as the FIU consumer using Sahamati's ReBIT FI schemas — the exact JSON our synthetic generator emits.
4. **Core banking (Finacle) untouched**: all execution actions (open FD, start SIP) are emitted as *deep-links / API intents* into existing IDBI journeys — advisory layer recommends, existing rails execute. Zero new transaction risk.
5. **AWS-ready**: stack maps 1:1 to the hackathon's provided AWS infra (Bedrock for LLM, S3+CloudFront for avatar assets, ECS for FastAPI, RDS for storage).

---

## 6. Future Scope

- **Full RIA compliance module** — registration path, suitability records, automated SEBI reporting.
- **Proactive nudges**: salary-credit detection → same-day "invest the surplus" push with avatar video message.
- **Family mode**: household balance sheet across AA-linked family accounts; joint goals (education, wedding).
- **Voice-first vernacular expansion** (8+ Indian languages) → branch kiosks & feature-phone IVR for financial inclusion (a stated national priority).
- **Portfolio doctor**: annual "health check" of held-away mutual funds/demat via AA — pulls assets *into* IDBI.
- **Agentic execution**: with consent, Saarthi auto-rebalances within pre-approved mandates (SEBI algo framework permitting).
- **RM co-pilot**: same engine powers relationship managers' dashboards for HNI clients — one brain, two interfaces.
- **Startup path**: the AA-behavioral-advisory engine is bank-agnostic — licensable to any FIU bank/NBFC as B2B SaaS.

---

## 7. MOST IMPORTANT — How This Addresses the Problem Effectively

The problem statement has three explicit pain points. Map each:

| Problem statement says | DhanSaarthi answers |
|---|---|
| *"Wealth advisory is fragmented and inaccessible to a large number of customers"* | Marginal cost per advised customer → ~₹0 (client-side avatar + deterministic engine). Every IDBI customer gets a private banker experience, 24×7, in their language — not just the top 2%. |
| *"Absence of comprehensive customer investment behaviour and spending habits"* | This is the core innovation: the AA-powered **Behavioral Financial Fingerprint** makes actual spending & investment behavior the *input* to advice. We don't lack behavioral data — we make it the engine's fuel, legally, with consent. |
| *"Limits timely, personalized, data-driven guidance"* | Timely: event-driven nudges on salary credit / idle cash / missed SIP. Personalized: advice references the user's own transactions. Data-driven: every number computed by an auditable engine, every explanation on demand. |
| Expected outcome: *"AI powered Digital Wealth management (Avatar Based) Application integrated into the bank's mobile application"* | Delivered literally: avatar-based, AI-powered, WebView-embeddable, plus the Future Self differentiator no competitor demo will have. |

**Why judges remember this one:** every other team will demo a chatbot with a risk quiz. This demo is: customer opens app → Saarthi greets by name → "I noticed ₹3.2L idle and ₹4,800/month on food delivery" → one tap → the avatar *ages 30 years* and the customer's future self thanks them for the SIP they're about to start → tap → SIP intent fires into the IDBI journey. Emotional, compliant, measurable, and shippable.

---

## 8. Step-by-Step Implementation Plan (2-day build, submission July 13)

**Phase 0 — Setup (30 min):** repo, `python -m venv .venv`, FastAPI skeleton, Next.js app, commit hooks.
**Phase 1 — Synthetic AA data (2 hrs):** `scripts/generate_aa_data.py` → 5 personas (young spender, disciplined saver, idle-cash accumulator, over-insured, near-retiree) in ReBIT-style FI-JSON: 12 months of transactions, MF holdings, deposits.
**Phase 2 — Behavioral engine (3 hrs):** pandas pipeline → fingerprint JSON: `savings_ratio, spend_leaks[], sip_discipline, idle_cash, insurance_gap, risk_capacity`.
**Phase 3 — Advisory engine (3 hrs):** YAML product shelf (IDBI FD rates, Suvidha SIP, insurance) + **strategy_library.yaml (Section 3A: Bogle/Buffett/Dalio/Swensen/Markowitz/goals-based templates)** + rule matrix (fingerprint → strategy → allocation buckets) + goal math (SIP future value, FD ladder, retirement corpus). Unit-tested, deterministic.
**Phase 4 — LLM narrator (2 hrs):** Gemini Flash wrapper: system prompt = persona + SEBI disclosure + "never compute numbers"; input = engine output JSON; output = warm Hinglish-capable narration. Offline template fallback.
**Phase 5 — Avatar UI (4 hrs):** Next.js page with TalkingHead.js, two GLB avatars (Saarthi + aged Future Self), edge-tts audio → lip-sync, Web Speech input, chat transcript panel, "Why this advice?" expandable trace.
**Phase 6 — Future Self mode (2 hrs):** avatar swap + camera transition + engine's 30-year projection scripts (good path / bad path).
**Phase 7 — Demo polish (2 hrs):** scripted golden path with cached narration, IDBI-branded splash, consent screen mimicking AA flow, README + architecture diagram + 2-min pitch script.
**Phase 8 — Verify (1 hr):** run unit tests, full demo dry-run offline (no-LLM mode), check every number the avatar speaks against engine output.

---

## 9. Claude Code Build Instructions

**Repo structure**
```
dhansaarthi/
├── backend/            # FastAPI (.venv here)
│   ├── app/main.py
│   ├── app/engines/behavioral.py
│   ├── app/engines/advisory.py
│   ├── app/engines/projection.py      # Future Self math
│   ├── app/llm/narrator.py            # Gemini + offline fallback
│   ├── app/adapters/                  # bank-API abstraction (Sec. 5)
│   ├── app/data/product_shelf.yaml
│   ├── app/data/strategy_library.yaml  # Sec. 3A — codified manager strategies
│   ├── scripts/generate_aa_data.py
│   └── tests/
├── frontend/            # Next.js PWA
│   ├── app/page.tsx                   # avatar screen
│   ├── components/AvatarStage.tsx     # TalkingHead.js wrapper
│   ├── components/ConsentFlow.tsx     # AA-style consent UI
│   └── public/avatars/{saarthi.glb, saarthi_aged.glb}
└── docs/{architecture.md, model-card.md, pitch.md}
```

**Milestone prompts for Claude Code (run in order):**
1. "Set up the repo structure above; create Python venv in backend/, install fastapi uvicorn pandas pyyaml edge-tts google-generativeai pytest inside it; scaffold Next.js in frontend/."
2. "Implement scripts/generate_aa_data.py per Phase 1 — 5 personas, ReBIT-style deposit/term-deposit/mutual-fund FI-JSON, 12 months data."
3. "Implement behavioral.py: compute the fingerprint fields from FI-JSON; write pytest cases for each persona."
4. "Implement advisory.py + product_shelf.yaml + strategy_library.yaml (codify the 10 strategies in PRD Section 3A as trigger_conditions → allocation_template → explanation_snippet → source_principle) + projection.py with deterministic goal math; every output must carry a `reasoning_trace` naming the strategy applied."
5. "Implement narrator.py: Gemini Flash streaming narration of engine JSON, PII masked, offline template fallback; add SEBI disclosure footer."
6. "Build AvatarStage.tsx with TalkingHead.js + Ready Player Me GLB, wire /chat endpoint: STT → engine → narrator → edge-tts → lip-sync."
7. "Add Future Self mode: avatar swap to aged GLB + projection script playback."
8. "Run all tests, run the offline demo path end-to-end, and produce docs/pitch.md."

**Rules (from RULES.MD):** everything installs in the venv; if something needs a global/system install, ask first; think from an IDBI financial manager's perspective — every feature must move a bank metric (CASA, SIP conversion, cross-sell, RM cost).

---

*Prototype cost: ₹0. Submission: July 13, 2026. Track 01 — Wealth Advisory.*
