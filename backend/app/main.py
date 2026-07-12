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
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import store
from app.engines.advisory import advise
from app.engines.projection import future_self
from app.engines.suitability import for_narration, screen
from app.llm.narrator import disclosure, narrate, template_narration

@asynccontextmanager
async def lifespan(_app: FastAPI):
    store.init()
    yield


app = FastAPI(
    title="DhanSaarthi API",
    description="Avatar-based, AA-powered wealth advisory sidecar for IDBI Bank.",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "offline", "advisory_mode": store.ADVISORY_MODE}


# --------------------------------------------------------------------------- #
# Request models
# --------------------------------------------------------------------------- #

class ConsentReq(BaseModel):
    persona_id: str


class ChatReq(BaseModel):
    persona_id: str
    text: str
    lang: str = "en"


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


def _advice_response(persona_id: str, fp, lang: str) -> dict:
    if store.ADVISORY_MODE == "info_only":
        spoken = ("In principle, a low-cost, diversified, goal-based plan tends to "
                  "serve most investors well. I can explain the ideas, but "
                  "recommendations are paused under governance review.")
        nh = store.narration_hash(spoken)
        store.write_audit(persona_id, "ADVICE", strategy_id=None, engine_ver=None,
                          shelf_sha=None, strategy_sha=None, narration_hash=nh,
                          suitability_outcome="info_only")
        return {"intent": "ADVICE", "spoken_text": spoken, "recommendations": [],
                "reasoning_trace": None, "disclosure": disclosure(lang),
                "narration_hash": nh}

    recs = for_narration(screen(fp, advise(fp)))
    primary = recs[0]
    spoken = narrate(primary, lang)
    nh = store.narration_hash(spoken)
    t = primary.reasoning_trace
    store.write_audit(persona_id, "ADVICE", strategy_id=primary.strategy_id,
                      engine_ver=t.engine_ver, shelf_sha=t.shelf_sha,
                      strategy_sha=t.strategy_sha, narration_hash=nh,
                      suitability_outcome=primary.status)
    return {
        "intent": "ADVICE", "spoken_text": spoken,
        "recommendations": [r.model_dump(mode="json") for r in recs],
        "reasoning_trace": t.model_dump(mode="json"),
        "disclosure": disclosure(lang), "narration_hash": nh,
    }


@app.post("/chat")
def chat(req: ChatReq) -> dict:
    _require_consent(req.persona_id)
    fp = store.get_fingerprint(req.persona_id)
    if fp is None:  # consent live but cache cold — re-ingest defensively
        store.grant_consent(req.persona_id)
        fp = store.get_fingerprint(req.persona_id)

    intent = classify_intent(req.text)
    lang = req.lang
    name = store.load_fi(req.persona_id)["profile"]["holderName"].split()[0]

    if intent == "ADVICE":
        resp = _advice_response(req.persona_id, fp, lang)
        resp["transcript"] = req.text
        return resp

    if intent == "WHY":
        recs = for_narration(screen(fp, advise(fp)))
        if store.ADVISORY_MODE == "info_only" or not recs:
            spoken = "The reasoning behind any suggestion is always shown to you, but recommendations are paused under governance review."
            trace = None
        else:
            spoken = _why_text(recs[0], lang)
            trace = recs[0].reasoning_trace.model_dump(mode="json")
        nh = store.narration_hash(spoken)
        store.write_audit(req.persona_id, "WHY",
                          strategy_id=(recs[0].strategy_id if recs and trace else None),
                          engine_ver=None, shelf_sha=None, strategy_sha=None,
                          narration_hash=nh, suitability_outcome=None)
        return {"intent": "WHY", "spoken_text": spoken, "transcript": req.text,
                "recommendations": [], "reasoning_trace": trace,
                "disclosure": disclosure(lang), "narration_hash": nh}

    if intent == "GREET":
        spoken = (f"Namaste {name}! I'm Saarthi, your IDBI wealth guide. "
                  "I've read your consented accounts — ask me what to do with your money, "
                  "or say 'show me my future self'.")
        nh = store.narration_hash(spoken)
        store.write_audit(req.persona_id, "GREET", strategy_id=None, engine_ver=None,
                          shelf_sha=None, strategy_sha=None, narration_hash=nh,
                          suitability_outcome=None)
        return {"intent": "GREET", "spoken_text": spoken, "transcript": req.text,
                "recommendations": [], "reasoning_trace": None,
                "disclosure": disclosure(lang), "narration_hash": nh}

    if intent == "FUTURE_SELF":
        spoken = ("Let's meet the you of tomorrow. Tap to see how today's choices "
                  "shape your retirement.")
        nh = store.narration_hash(spoken)
        store.write_audit(req.persona_id, "FUTURE_SELF", strategy_id=None,
                          engine_ver=None, shelf_sha=None, strategy_sha=None,
                          narration_hash=nh, suitability_outcome=None)
        return {"intent": "FUTURE_SELF", "spoken_text": spoken, "transcript": req.text,
                "recommendations": [], "reasoning_trace": None,
                "disclosure": disclosure(lang), "narration_hash": nh,
                "future_self_url": f"/future-self?persona_id={req.persona_id}"}

    if intent == "PANIC":
        # Marks cycle guardrail: never an exit path — reframe to cycles + goals.
        spoken = ("Markets move in cycles, and reacting to a dip usually locks in the "
                  "loss. Your plan was built for exactly this. Let's revisit your goals "
                  "and meet your future self before changing anything — no exits today.")
        nh = store.narration_hash(spoken)
        store.write_audit(req.persona_id, "PANIC", strategy_id="marks_cycle_guardrail",
                          engine_ver=None, shelf_sha=None, strategy_sha=None,
                          narration_hash=nh, suitability_outcome=None)
        return {"intent": "PANIC", "spoken_text": spoken, "transcript": req.text,
                "recommendations": [], "reasoning_trace": None,
                "disclosure": disclosure(lang), "narration_hash": nh}

    # OFFTOPIC
    spoken = ("I'm your money guide, so I'll stay on your finances. "
              "Ask me about your savings, spending, or investments.")
    nh = store.narration_hash(spoken)
    store.write_audit(req.persona_id, "OFFTOPIC", strategy_id=None, engine_ver=None,
                      shelf_sha=None, strategy_sha=None, narration_hash=nh,
                      suitability_outcome=None)
    return {"intent": "OFFTOPIC", "spoken_text": spoken, "transcript": req.text,
            "recommendations": [], "reasoning_trace": None,
            "disclosure": disclosure(lang), "narration_hash": nh}


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
            communicate = edge_tts.Communicate(text, voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    chunks.extend(chunk["data"])
            return bytes(chunks)

        audio = asyncio.run(_synth())
        return Response(content=audio, media_type="audio/mpeg")
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"TTS unavailable: {exc}")
