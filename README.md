# DhanSaarthi (धनसारथी) — your friendly wealth guide for IDBI Bank

**In one line:** DhanSaarthi is a talking on-screen advisor named *Saarthi* who looks
at a customer's real banking habits and gives simple, honest money advice — and even
lets them meet their own **"future self" at age 60** to see where today's habits lead.

It runs on your own computer, needs **no internet and no paid accounts**, and every
rupee figure it says is calculated by a careful, checkable program (not made up by AI).

> This is a working demo built for **IDBI Innovate 2026**. It uses **make-believe (sample)
> customers**, so no real bank data is involved.

---

## What you'll see when it runs

1. A welcome screen with **five sample customers** — pick one (e.g. *Aarav, age 27*).
2. A consent screen (like India's Account Aggregator) — click **Approve**.
3. Saarthi greets the customer by name and gives advice such as:
   *"You spend about **₹4,800/month** on food delivery. Put just **₹2,400** of it into a
   simple index fund and in **33 years** it could grow to about **₹74.76 lakh**."*
4. Buttons to ask **"Why this advice?"**, **"Show me my future self"**, and **"Start SIP"**.
5. A **Governance** panel that shows, like a regulator would see, exactly how each piece
   of advice was produced.

There is a full click-by-click walkthrough further down.

---

## Part 1 — One-time setup (do this once)

You need two free tools installed on the computer. If they're already installed, skip ahead.

### 1a. Install Python (the "brain" of the app)
- Download from **https://www.python.org/downloads/** and run the installer.
- **Important:** on the first screen, tick the box **"Add Python to PATH"**, then click Install.

### 1b. Install Node.js (the "face"/screen of the app)
- Download the **LTS** version from **https://nodejs.org/** and run the installer (defaults are fine).

### 1c. Check they installed
Open **PowerShell** (press the Windows key, type `PowerShell`, press Enter) and type these
two lines, pressing Enter after each. You should see version numbers, not errors:
```powershell
python --version
node --version
```

### 1d. Install the app's parts
Copy-paste this block into the same PowerShell window and press Enter. It prepares the
"brain". (It downloads some files the first time — that's normal.)
```powershell
cd D:\IDBI\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
Then prepare the "face". Copy-paste this and press Enter:
```powershell
cd D:\IDBI\frontend
npm install
```

That's the whole setup. You won't need to repeat Part 1.

---

## Part 2 — Starting the app (every time you want to use it)

The app has two halves that must **both** be running, so you open **two** PowerShell windows.

### Window 1 — the "brain"
Open PowerShell and paste:
```powershell
cd D:\IDBI\backend
.venv\Scripts\activate
uvicorn app.main:app --port 8000
```
Wait until you see **`Application startup complete`**. Leave this window open.

### Window 2 — the "face"
Open a **second** PowerShell window and paste:
```powershell
cd D:\IDBI\frontend
npm run dev
```
Wait until you see **`Ready`**. Leave this window open too.

### Open the app
Open **Google Chrome** and go to:
```
http://localhost:3000
```
> Please use **Chrome** — the microphone (voice) feature only works there. Everything
> else works in any browser.

**Tip:** always start Window 1 (the brain) **before** Window 2 (the face).

---

## Part 3 — How to use it (click by click)

1. **Pick a customer.** Click one of the five cards (try **Aarav Sharma**).
2. **Approve consent.** A sheet appears explaining what data is shared. Click **Approve & continue**.
3. **Say hello.** Saarthi greets the customer by name.
4. **Ask for advice.** Click the suggestion **"What should I do with my money?"** (or type
   your own question and press **Send**). Saarthi speaks the advice and shows advice cards.
   *(If a button doesn't respond, wait a second for Saarthi to finish talking, then click again.)*
5. **See the reasoning.** Click **"Why this advice?"** under a card to see, in plain steps,
   how the number was worked out.
6. **Meet the future self.** Click **"Show me my future self"** — Saarthi turns into the
   customer at age 60 and speaks. Use **If you invest** / **If you wait** to compare paths.
7. **Start a plan.** Click **"Start SIP →"** on a card — it shows the handoff link that would
   open IDBI's existing app journey (nothing real is bought).
8. **See the audit trail.** Click the **🛡️ Governance** button (bottom-right) to see the
   record of everything Saarthi just did — the "regulator's view".
9. **Try another customer.** Click **Switch customer** at the top to start over.
   *(Try Mohan, the near-retiree, and ask "the market is crashing, should I sell?" — Saarthi
   will calmly talk him out of panic-selling rather than offering an exit.)*

---

## Part 4 — Stopping the app

In each PowerShell window, click on it and press **Ctrl + C**. Then you can close the windows.
Your computer is left exactly as before.

---

## If something doesn't work

| What you see | What to do |
|---|---|
| The web page says it can't reach the service / advice doesn't load | Make sure **Window 1 (the brain)** is running and shows `Application startup complete`. Start it first. |
| `python` or `node` "not recognized" | They aren't installed yet (or Python wasn't added to PATH). Redo **Part 1** and re-tick "Add Python to PATH". |
| `http://localhost:3000` won't open | Make sure **Window 2 (the face)** shows `Ready`. Give it 10–20 seconds the first time. |
| "Port already in use" | The app is already running in another window, or a previous run didn't close. Close old PowerShell windows and try again. |
| The microphone/voice doesn't work | Use **Google Chrome**, and allow microphone access when asked. (Typing always works too.) |
| Saarthi has no voice | That's expected offline — it uses your browser's built-in voice, which some computers don't have. The text still appears on screen. |

---

## Good to know

- **It's a demo with sample data.** The five customers are invented; no real bank or personal
  data is used. Product rates shown are illustrative.
- **It works completely offline** — no API keys, no sign-ups, no internet needed.
- **The advice is trustworthy by design:** a careful program calculates every number; the
  talking avatar only puts it into words and can never invent a figure. It also *refuses*
  to give unsuitable advice (e.g. risky stock-heavy plans to someone near retirement) and
  explains why.

---

## For developers, reviewers & judges

Technical details, the 2-minute demo script, and the compliance/governance evidence live in
[`docs/`](docs/):

- **Architecture:** [docs/architecture.md](docs/architecture.md) · design & invariants ([PRD.md](PRD.md))
- **How the "model" works + SEBI five-pillar mapping:** [docs/model-card.md](docs/model-card.md)
- **Risk & Compliance review (one page):** [docs/compliance-gate.md](docs/compliance-gate.md)
- **Config change control (versions/@sha):** [docs/change-log.md](docs/change-log.md)
- **2-minute pitch script:** [docs/pitch.md](docs/pitch.md)

Quick technical facts: Python/FastAPI backend (deterministic advisory engines + a firewalled
Gemini narrator that defaults to offline templates) · Next.js avatar PWA (Gemini-style chat +
live financial side panel from `GET /financials`) · SQLite · money is integer paise everywhere.
Run the test suite from `backend/` (with the venv active): `pytest` (**117 tests**, offline).

**Enable live Gemini chat (optional):** copy `backend/.env.example` to `backend/.env` and set
`GEMINI_API_KEY` (a standard AI Studio key, `AIza…`, from https://aistudio.google.com/apikey;
optionally `GEMINI_MODEL`, default `gemini-flash-latest`). The chat then phrases replies with
Gemini, **grounded** in the customer's real data — the numeral validator still rejects any
figure the engine didn't produce, and it falls back to offline templates if the key is
absent/invalid or quota is exhausted. Other flags: `ENABLE_TTS=1` (neural voice),
`ADVISORY_MODE=info_only` (governance kill-switch).

*Prototype cost: ₹0 · Submission: 2026-07-13 · IDBI Innovate 2026, Track 01 — Wealth Advisory.*
