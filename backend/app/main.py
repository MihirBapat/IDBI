"""DhanSaarthi FastAPI application — BFF / turn orchestrator.

Stateless request handling over the deterministic engines + firewalled narrator.
Consent is verified at read time on every advice turn; a revocation blocks the
very next turn (architecture §3, §4). The ``ADVISORY_MODE=info_only`` kill-switch
(governance/CAB control) lets chat keep explaining concepts while returning zero
recommendations and refusing execution intents.

Money stays integer paise; the LLM never computes; nothing flows narrator→engine.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import store
from app.engines import financials
from app.engines.advisory import advise
from app.engines.projection import future_self
from app.engines.suitability import for_narration, screen
from app.llm import narrator
from app.llm.narrator import disclosure, narrate, template_narration
from app.schemas import PersonaFI


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Load backend/.env (secrets like GEMINI_API_KEY) at startup only, so the
    # test transports (which don't run lifespan) stay fully offline.
    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    except Exception:
        pass
    store.init()
    _warm_gemini()  # prime the transport channel so the first turn isn't cold
    yield


def _warm_gemini() -> None:
    """Fire a tiny Gemini call in the background to warm the connection."""
    if not _gemini_on():
        return
    import threading

    def _warm():
        try:
            narrator._gemini_generate("You are a helper.", "Say ok.")
        except Exception:
            pass

    threading.Thread(target=_warm, daemon=True).start()


def _gemini_on() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


app = FastAPI(
    title="DhanSaarthi API",
    description="Avatar-based, AA-powered wealth advisory sidecar for IDBI Bank.",
    version="0.3.0",
    lifespan=lifespan,
)

# Allowed browser origins. Local dev is always allowed; extra origins (e.g. the
# deployed Vercel URL) come from ALLOWED_ORIGINS (comma-separated). Any
# *.vercel.app preview/prod deploy is allowed via regex so links keep working.
_ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"] + [
    o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "mode": "gemini" if _gemini_on() else "offline",
            "advisory_mode": store.ADVISORY_MODE, "gemini": _gemini_on()}


# --------------------------------------------------------------------------- #
# Request models
# --------------------------------------------------------------------------- #

class ConsentReq(BaseModel):
    persona_id: str


class ChatReq(BaseModel):
    persona_id: str
    text: str
    lang: str = "en"
    history: Optional[list[dict]] = None  # [{role: 'user'|'saarthi', text: str}]


class IntentReq(BaseModel):
    persona_id: str
    recommendation_id: str
    idempotency_key: str


# --------------------------------------------------------------------------- #
# Intent classification (keyword enum — user free text reduced to an intent)
# --------------------------------------------------------------------------- #

_KEYWORDS = [
    ("PANIC", ("crash", "panic", "sell everything", "exit", "withdraw", "falling",
               "market down", "losing", "pull out")),
    ("WHY", ("why", "explain", "how did", "reason", "justify")),
    ("FUTURE_SELF", ("future self", "future", "older", "retire", "when i am 60",
                     "aged")),
    ("GREET", ("hello", "hi ", "hey", "namaste", "good morning", "good evening")),
    ("OFFTOPIC", ("weather", "joke", "cricket", "movie", "song", "politics")),
]


def classify_intent(text: str) -> str:
    t = f" {text.lower().strip()} "
    for intent, keys in _KEYWORDS:
        if any(k in t for k in keys):
            return intent
    return "ADVICE"  # default: they consented for advice


# --------------------------------------------------------------------------- #
# Consent
# --------------------------------------------------------------------------- #

@app.post("/consent")
def grant_consent(req: ConsentReq) -> dict:
    summary = store.grant_consent(req.persona_id)
    if summary is None:
        raise HTTPException(status_code=404, detail=f"unknown persona '{req.persona_id}'")
    return {"consent": summary}


@app.delete("/consent")
def revoke_consent(persona_id: str = Query(...)) -> dict:
    revoked = store.revoke_consent(persona_id)
    return {"revoked": revoked, "persona_id": persona_id}


def _require_consent(persona_id: str) -> None:
    if not store.consent_live(persona_id):
        raise HTTPException(status_code=403, detail="no live consent for this persona")


# --------------------------------------------------------------------------- #
# Chat
# --------------------------------------------------------------------------- #

def _why_text(rec, lang: str) -> str:
    """Claim-safe 'why' explanation built from the rec's figures + principle."""
    return (f"{rec.title}. This applies {rec.reasoning_trace.source_principle}. "
            + template_narration(rec, lang))


def _panic_reply(lang: str) -> str:
    return ("Markets move in cycles, and reacting to a dip usually locks in the loss. "
            "Your plan was built for exactly this. Let's revisit your goals and meet "
            "your future self before changing anything — no exits today.")


def _deterministic_reply(intent: str, name: str, recs: list, info_only: bool,
                         lang: str) -> str:
    """The offline / fallback wording when Gemini is unavailable or rejected."""
    if info_only:
        return ("In principle, a low-cost, diversified, goal-based plan serves most "
                "investors well. I can explain the ideas, but recommendations are "
                "paused under governance review.")
    if intent == "GREET":
        return (f"Namaste {name}! I'm Saarthi, your IDBI wealth guide. I've read your "
                "consented accounts — ask me what to do with your money, your spending, "
                "or say 'show me my future self'.")
    if intent == "WHY" and recs:
        return _why_text(recs[0], lang)
    if recs:  # ADVICE / general
        return narrate(recs[0], lang)  # already includes the disclosure
    return (f"Namaste {name}! Ask me what to do with your money, how you're spending, "
            "or say 'show me my future self'.")


@app.post("/chat")
def chat(req: ChatReq) -> dict:
    _require_consent(req.persona_id)
    fp = store.get_fingerprint(req.persona_id)
    if fp is None:  # consent live but cache cold — re-ingest defensively
        store.grant_consent(req.persona_id)
        fp = store.get_fingerprint(req.persona_id)

    intent = classify_intent(req.text)
    lang = req.lang
    fi = store.load_fi(req.persona_id)
    name = fi["profile"]["holderName"].split()[0]
    info_only = store.ADVISORY_MODE == "info_only"

    # ---- Safety guardrails: fully deterministic, never routed to the LLM ----
    if intent in ("PANIC", "OFFTOPIC", "FUTURE_SELF"):
        if intent == "PANIC":
            spoken, strat = _panic_reply(lang), "marks_cycle_guardrail"
        elif intent == "FUTURE_SELF":
            spoken, strat = ("Let's meet the you of tomorrow. Tap to see how today's "
                             "choices shape your retirement."), None
        else:
            spoken, strat = ("I'm your money guide, so I'll stay on your finances. Ask "
                             "me about your savings, spending, or investments."), None
        nh = store.narration_hash(spoken)
        store.write_audit(req.persona_id, intent, strategy_id=strat, engine_ver=None,
                          shelf_sha=None, strategy_sha=None, narration_hash=nh,
                          suitability_outcome=None)
        out = {"intent": intent, "spoken_text": spoken, "transcript": req.text,
               "recommendations": [], "reasoning_trace": None,
               "disclosure": disclosure(lang), "narration_hash": nh}
        if intent == "FUTURE_SELF":
            out["future_self_url"] = f"/future-self?persona_id={req.persona_id}"
        return out

    # ---- Conversational: GREET / WHY / ADVICE / general (grounded Gemini) ----
    recs = []
    if not info_only and intent in ("ADVICE", "WHY"):
        recs = for_narration(screen(fp, advise(fp)))

    spoken = None
    if not info_only:
        persona = PersonaFI.model_validate(fi)
        summ = financials.summary(persona, fp)
        claimset = financials.grounding_claims(summ, recs)
        context = financials.grounding_context(summ, recs)
        spoken = narrator.converse(req.text, context, claimset, lang, req.history)

    used_gemini = spoken is not None
    if spoken is None:
        spoken = _deterministic_reply(intent, name, recs, info_only, lang)
    if info_only:
        recs = []

    # Append the SEBI disclosure for money-advice turns (narrate already has it).
    disc = disclosure(lang)
    if intent in ("ADVICE", "WHY") and not info_only and disc not in spoken:
        spoken = f"{spoken}\n\n{disc}"

    primary = recs[0] if recs else None
    trace = primary.reasoning_trace.model_dump(mode="json") if primary else None
    nh = store.narration_hash(spoken)
    store.write_audit(
        req.persona_id, intent,
        strategy_id=(primary.strategy_id if primary else None),
        engine_ver=(primary.reasoning_trace.engine_ver if primary else None),
        shelf_sha=(primary.reasoning_trace.shelf_sha if primary else None),
        strategy_sha=(primary.reasoning_trace.strategy_sha if primary else None),
        narration_hash=nh,
        suitability_outcome=(primary.status if primary else
                             ("info_only" if info_only else None)),
    )
    return {"intent": intent, "spoken_text": spoken, "transcript": req.text,
            "recommendations": [r.model_dump(mode="json") for r in recs],
            "reasoning_trace": trace, "disclosure": disc, "narration_hash": nh,
            "source": "gemini" if used_gemini else "template"}


# --------------------------------------------------------------------------- #
# Financial snapshot (side panel: history, records & state)
# --------------------------------------------------------------------------- #

@app.get("/financials")
def financials_endpoint(persona_id: str = Query(...)) -> dict:
    _require_consent(persona_id)
    fp = store.get_fingerprint(persona_id)
    if fp is None:
        store.grant_consent(persona_id)
        fp = store.get_fingerprint(persona_id)
    persona = PersonaFI.model_validate(store.load_fi(persona_id))
    return financials.summary(persona, fp)


# --------------------------------------------------------------------------- #
# Future Self
# --------------------------------------------------------------------------- #

@app.get("/future-self")
def future_self_endpoint(persona_id: str = Query(...),
                         branch: str = Query("good")) -> dict:
    _require_consent(persona_id)
    fp = store.get_fingerprint(persona_id)
    if fp is None:
        store.grant_consent(persona_id)
        fp = store.get_fingerprint(persona_id)
    script = future_self(fp, take_advice=(branch == "good"))
    return script.model_dump(mode="json")


# --------------------------------------------------------------------------- #
# Execution intent (idempotent deep-link)
# --------------------------------------------------------------------------- #

@app.post("/intent")
def emit_intent(req: IntentReq) -> dict:
    _require_consent(req.persona_id)
    if store.ADVISORY_MODE == "info_only":
        raise HTTPException(status_code=403,
                            detail="execution intents are disabled under governance review")
    deep_link = (f"idbi://journey/start?rec_id={req.recommendation_id}"
                 f"&idem={req.idempotency_key}")
    payload, duplicate = store.log_intent(req.idempotency_key, req.persona_id,
                                          req.recommendation_id, deep_link)
    payload["duplicate"] = duplicate
    return payload


# --------------------------------------------------------------------------- #
# Governance / audit surface
# --------------------------------------------------------------------------- #

@app.get("/audit")
def audit(persona_id: str = Query(...)) -> dict:
    return {"persona_id": persona_id, "rows": store.get_audit(persona_id)}


# --------------------------------------------------------------------------- #
# TTS (neural voice when online; else 503 -> browser SpeechSynthesis fallback)
# --------------------------------------------------------------------------- #

@app.get("/tts")
def tts(text: str = Query(...), voice: str = Query("en-IN-NeerjaNeural")) -> Response:
    if not os.environ.get("ENABLE_TTS"):
        raise HTTPException(status_code=503, detail="TTS offline; use browser speech")
    try:  # pragma: no cover - requires internet
        import asyncio
        import edge_tts

        async def _synth() -> bytes:
            chunks = bytearray()
            # Gentle prosody so the neural voice sounds warm, not flat/monotone.
            communicate = edge_tts.Communicate(text, voice, rate="-3%", pitch="+3Hz")
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    chunks.extend(chunk["data"])
            return bytes(chunks)

        audio = asyncio.run(_synth())
        return Response(content=audio, media_type="audio/mpeg")
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"TTS unavailable: {exc}")
