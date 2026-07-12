# DhanSaarthi — 2-minute pitch script

**DHS-PITCH-001 · v1.0** · The exact demo path + talking points. Setup: backend on
`:8000`, frontend on `:3000`, Chrome. Runs fully offline. See [README.md](../README.md).

---

## The hook (15s)

> "Today a wealthy IDBI customer gets a relationship manager. Everyone else gets a
> risk quiz they lie on. India has roughly **one advisor per 200,000 investors**.
> DhanSaarthi gives every customer a private banker — one that has actually *read their
> bank statement*, and that can show them their own future."

## The walk-through (90s)

1. **Consent (10s).** Pick **Aarav Sharma (27)**. Approve the Account-Aggregator consent
   sheet. → *"Data enters only with consent — purpose-bound, revocable, RBI-regulated. No
   credentials ever touch us."*

2. **Behavioural insight (20s).** Ask **"What should I do with my money?"** Saarthi:
   *"You're spending about **₹4,800/month** on food delivery. Redirect just **₹2,400** into
   a low-cost index SIP — over **33 years** that grows to about **₹74.76 lakh**."*
   → *"No questionnaire can produce that. It read his actual spending. And notice — the
   avatar spoke, but a deterministic engine computed every rupee."*

3. **Why this advice? (15s).** Expand the trace: **Bogle principle**, the exact math, the
   config hashes `shelf@… strategy@…`. → *"Every recommendation is explainable and
   bit-for-bit replayable — SEBI's interpretability and audit pillars, in the UI."*

4. **Future Self (20s).** **"Show me my future self."** The avatar ages to 60 and thanks
   him for the SIP. Toggle **If you wait** for the darker branch. → *"Hershfield's
   future-self research shows this measurably raises savings. Emotional hook, compliant
   engine, and a bank metric — SIP conversion — in one feature."*

5. **Execute (10s).** Tap **Start SIP →**. A deep-link intent fires. → *"We recommend;
   IDBI's existing Finacle rails execute. Zero new transaction risk. Tap twice — it's
   idempotent."*

6. **Governance (15s).** Open the 🛡️ **Governance** drawer. → *"This is the regulator's-eye
   view of the advice you just heard — strategy, config versions, suitability outcome, a
   hash of the exact words spoken."*

## The mic-drop (15s)

Switch to **Mohan (54, near-retiree)**, ask **"the market is crashing, should I sell?"**
→ Saarthi reframes to market cycles, offers no exit. → *"And behind the scenes, the
suitability gate silently **vetoed** an aggressive-equity recommendation for a
54-year-old and recorded why. The system can decline and explain — not just sell.
That is what makes it bank-grade."*

---

## If asked "is this real AI?"

*"The LLM is a rendering layer — it phrases, it never computes. A validator rejects any
number the engine didn't produce; escape budget is zero. That's the compliance story most
teams won't have: the AI demonstrably cannot give unsafe advice."*

## If asked about scale / cost

*"Avatar renders on the customer's GPU; the engine is a sub-10ms pure function; the only
per-turn variable cost is optional LLM narration — and template mode makes even that
discretionary. Marginal cost per advised customer approaches zero."*
