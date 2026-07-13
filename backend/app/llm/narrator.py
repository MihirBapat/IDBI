"""narrator.py — the firewalled rendering layer.

``narrate(recommendation, lang, mode)`` turns an engine Recommendation into warm
EN/HI prose. Two modes:

* **template** (default, the demo baseline): deterministic copy assembled purely
  from the recommendation's labeled figures — every numeral it emits is, by
  construction, a member of ``numeric_claims``. Runs with zero API keys, offline.
* **gemini**: only when ``GEMINI_API_KEY`` is set and ``mode="gemini"``. The
  prompt carries the trace/claims with PII replaced by slot tokens and **no raw
  narration strings** (injection quarantine). Output passes the numeral validator
  or is retried once, then falls back to template. Escape budget: zero.

The SEBI disclosure is appended in code, after validation — never in the prompt.
"""

from __future__ import annotations

import os
from typing import Optional

from app.engines.money import format_inr, format_pct, format_years
from app.llm.validator import validate
from app.schemas import Recommendation

NARRATOR_VER = "narrator-1.0.0"

_DISCLOSURE = {
    "en": ("Mutual fund investments are subject to market risks; read all "
           "scheme-related documents carefully. This is educational guidance "
           "based on your consented data, not individual investment advice "
           "under SEBI (Investment Advisers) Regulations."),
    "hi": ("म्यूचुअल फंड निवेश बाज़ार जोखिमों के अधीन हैं; योजना संबंधी सभी "
           "दस्तावेज़ ध्यान से पढ़ें। यह आपकी सहमति-आधारित जानकारी पर आधारित "
           "शैक्षिक मार्गदर्शन है, SEBI (निवेश सलाहकार) विनियमों के तहत "
           "व्यक्तिगत निवेश सलाह नहीं।"),
}


def disclosure(lang: str = "en") -> str:
    return _DISCLOSURE.get(lang, _DISCLOSURE["en"])


# --------------------------------------------------------------------------- #
# Template narration — claim-safe by construction
# --------------------------------------------------------------------------- #

def _m(rec: Recommendation, key: str, lang: str) -> str:
    return format_inr(rec.money_figures[key], lang)


def _y(rec: Recommendation, key: str, lang: str) -> str:
    return format_years(rec.year_figures[key], lang)


def _p(rec: Recommendation, key: str) -> str:
    return format_pct(rec.pct_figures[key])


def template_narration(rec: Recommendation, lang: str = "en") -> str:
    """Deterministic warm copy. Uses only the recommendation's labeled figures,
    so every numeral it contains is in ``numeric_claims``."""
    a = rec.action
    if a == "start_sip":
        if lang == "hi":
            return (f"आप हर महीने लगभग {_m(rec,'leak',lang)} खाने की डिलीवरी पर खर्च "
                    f"करते हैं। उसमें से सिर्फ़ {_m(rec,'amount',lang)} एक कम-लागत इंडेक्स "
                    f"SIP में लगाइए — {_y(rec,'horizon',lang)} में यह लगभग "
                    f"{_m(rec,'projection',lang)} बन सकता है। छोटी आदत, बड़ा भविष्य।")
        return (f"You're spending about {_m(rec,'leak',lang)} a month on food "
                f"delivery. Redirect just {_m(rec,'amount',lang)} of it into a "
                f"low-cost index SIP — over {_y(rec,'horizon',lang)} that could grow "
                f"to around {_m(rec,'projection',lang)}. A small habit, a big future.")
    if a == "step_up_sip":
        if lang == "hi":
            return (f"आप पहले से अनुशासन से निवेश करते हैं। सिर्फ़ {_m(rec,'stepup',lang)} "
                    f"प्रति माह और बढ़ाइए — {_y(rec,'horizon',lang)} में यह आपके लक्ष्यों में "
                    f"लगभग {_m(rec,'projection',lang)} जोड़ सकता है। गति ही आपकी ताक़त है।")
        return (f"You already invest with real discipline. Step up by just "
                f"{_m(rec,'stepup',lang)} a month and over {_y(rec,'horizon',lang)} "
                f"that could add about {_m(rec,'projection',lang)} toward your goals. "
                f"Momentum is on your side.")
    if a == "move_to_fd":
        if lang == "hi":
            return (f"लगभग {_m(rec,'amount',lang)} आपके बचत खाते में {_p(rec,'savings_rate')} "
                    f"पर बेकार पड़ा है। इसे {_p(rec,'fd_rate')} वाली IDBI FD सीढ़ी में लगाइए — "
                    f"हर साल लगभग {_m(rec,'extra',lang)} अधिक, वही सुरक्षा। ")
        return (f"About {_m(rec,'amount',lang)} is sitting idle in your savings, "
                f"earning just {_p(rec,'savings_rate')}. A laddered IDBI FD at "
                f"{_p(rec,'fd_rate')} would earn you roughly {_m(rec,'extra',lang)} more "
                f"every year — the same safety, more return.")
    if a == "deploy_all_weather":
        if lang == "hi":
            return (f"आप अपने लक्ष्य के क़रीब हैं, तो उसे सुरक्षित रखते हैं। यह ऑल-वेदर मिश्रण "
                    f"{_m(rec,'amount',lang)} को इक्विटी, गिल्ट, सोना और लिक्विड में बाँटता है, "
                    f"ताकि कोई एक झटका आपको पटरी से न उतारे।")
        return (f"You're close to your goal, so let's protect it. This All-Weather "
                f"mix spreads {_m(rec,'amount',lang)} across equity, gilt, gold and "
                f"liquid funds so that no single shock can derail you.")
    if a == "diversify_sip":
        if lang == "hi":
            return (f"आपकी इक्विटी बहुत कम है। {_m(rec,'amount',lang)} प्रति माह की एक "
                    f"विविध SIP से इसे भारत और वैश्विक इक्विटी, गिल्ट और रीट में फैलाइए।")
        return (f"Your equity exposure is thin. A diversified {_m(rec,'amount',lang)} "
                f"a month SIP spreads it across domestic and global equity, gilt and "
                f"REITs — Swensen's endowment idea, made simple.")
    if a == "deploy_9010":
        if lang == "hi":
            return (f"अपने अधिशेष {_m(rec,'amount',lang)} को काम पर लगाइए — 90% कम-लागत "
                    f"इंडेक्स, 10% गिल्ट, जैसा बफे ने खुद सुझाया।")
        return (f"Put your surplus {_m(rec,'amount',lang)} to work with a simple "
                f"90/10 split — low-cost index and short-term gilt, exactly the mix "
                f"Buffett left in his own instructions.")
    # Generic fallback for any future action.
    return f"{rec.title}."


# --------------------------------------------------------------------------- #
# PII-masked prompt (gemini mode) — no raw narrations ever
# --------------------------------------------------------------------------- #

def build_prompt(rec: Recommendation, lang: str = "en") -> dict:
    """Assemble the LLM payload: only category codes, engine figures and claims —
    identity replaced by the ``{NAME}`` slot token, no raw merchant/UPI strings."""
    system = (
        "You are Saarthi, a warm IDBI Bank wealth guide. Narrate the given "
        "recommendation in 2-3 sentences. You MUST NOT state any number that is "
        "not present verbatim in `numeric_claims`. Do not compute or invent "
        f"figures. Address the customer as {{NAME}}. Language: {lang}."
    )
    return {
        "system": system,
        "recommendation": {
            "strategy_id": rec.strategy_id,
            "source_principle": rec.reasoning_trace.source_principle,
            "action": rec.action,
            "allocation": rec.allocation,
            "math_steps": rec.reasoning_trace.math_steps,
            "numeric_claims": rec.numeric_claims,
        },
        "slots": {"NAME": "{NAME}"},
    }


def _resolve_mode(mode: Optional[str]) -> str:
    if mode == "gemini" and os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    return "template"


def _call_gemini(prompt: dict, lang: str) -> str:  # pragma: no cover - network
    """Real Gemini call. Never invoked in tests (mocked); never on a hot loop."""
    import google.generativeai as genai

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash",
                                  system_instruction=prompt["system"])
    resp = model.generate_content(str(prompt["recommendation"]))
    return resp.text


def _gemini_model() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-flash-latest")


def _gemini_generate(system: str, user: str) -> str:  # pragma: no cover - network
    """Single grounded Gemini call for the conversational chat."""
    import google.generativeai as genai

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(_gemini_model(), system_instruction=system)
    resp = model.generate_content(user)
    return resp.text


def _clean(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
    for prefix in ("Saarthi:", "SAARTHI:"):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    return text


def converse(user_text: str, context: str, claimset: list[str], lang: str = "en",
             history: Optional[list[dict]] = None) -> Optional[str]:
    """Grounded conversational reply (the 'feels real' path).

    Uses Gemini to phrase a natural answer to the customer's actual message, but
    strictly grounded in ``context`` (their real financial facts + engine
    recommendations). The numeral validator enforces that no figure outside
    ``claimset`` survives — one retry, then ``None`` so the caller falls back to
    the deterministic template. Returns ``None`` whenever Gemini is unavailable.
    """
    if not os.environ.get("GEMINI_API_KEY"):
        return None

    system = (
        "You are Saarthi, a warm, concise wealth guide for IDBI Bank speaking to a "
        "customer. Answer their message directly in 2-4 short, friendly sentences in "
        f"{lang}. You MUST only state numbers (rupee amounts, %, years, ages) that "
        "appear verbatim in the CONTEXT; NEVER invent or recompute a figure. If you "
        "lack a number, speak qualitatively. Do not give tips on individual stocks; "
        "keep to the recommendations and facts provided."
    )
    convo = ""
    if history:
        convo = "\n".join(
            f"{'Customer' if m.get('role') == 'user' else 'Saarthi'}: {m.get('text', '')}"
            for m in history[-6:]
        )
    user = (f"CONTEXT:\n{context}\n\n"
            + (f"Conversation so far:\n{convo}\n\n" if convo else "")
            + f"Customer: {user_text}\nSaarthi:")

    try:
        for _ in range(2):  # initial + one retry
            candidate = _clean(_gemini_generate(system, user))
            if validate(candidate, claimset):
                return candidate
    except Exception:
        return None
    return None


def narrate(rec: Recommendation, lang: str = "en", mode: Optional[str] = None) -> str:
    """Render a recommendation to validated prose with the disclosure appended."""
    resolved = _resolve_mode(mode)
    body: Optional[str] = None

    if resolved == "gemini":
        prompt = build_prompt(rec, lang)
        for _ in range(2):  # initial attempt + one retry
            candidate = _call_gemini(prompt, lang)
            candidate = candidate.replace("{NAME}", "")  # slot unused in prototype
            if validate(candidate, rec.numeric_claims):
                body = candidate.strip()
                break
        if body is None:  # validator double-failure -> deterministic fallback
            body = template_narration(rec, lang)
    else:
        body = template_narration(rec, lang)

    return f"{body}\n\n{disclosure(lang)}"
