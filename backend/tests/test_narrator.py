"""Step 4 gate: the narration firewall.

(a) template mode utters only claimed numbers, for every persona/rec and both
    languages; (b) a hallucinating LLM ("earn ₹99,999") is rejected and the
    narrator falls back to the deterministic template; (c) a persona whose raw
    narrations contain an injection string never leaks it into the LLM prompt.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.engines.advisory import advise
from app.engines.behavioral import compute_fingerprint
from app.engines.suitability import screen
from app.llm import narrator
from app.llm.narrator import (build_prompt, disclosure, narrate,
                              template_narration)
from app.llm.validator import extract_numerals, validate

from scripts.generate_aa_data import _BUILDERS

PERSONA_DIR = Path(__file__).resolve().parents[1] / "app" / "data" / "personas"
PERSONAS = list(_BUILDERS.keys())


def _recs(pid: str):
    fp = compute_fingerprint(json.loads((PERSONA_DIR / f"{pid}.json").read_text("utf-8")))
    return screen(fp, advise(fp))


# --------------------------------------------------------------------------- #
# Validator unit behavior
# --------------------------------------------------------------------------- #

def test_validator_accepts_claimed_rejects_unclaimed():
    claims = ["₹2,400", "₹19.2 lakh", "33 years", "10%"]
    assert validate("Redirect ₹2,400 for 33 years to reach ₹19.2 lakh.", claims)
    assert validate("No numbers here at all.", claims)
    assert not validate("You could earn ₹99,999 easily.", claims)
    assert not validate("A guaranteed 25% return.", claims)


def test_extract_numerals_captures_units():
    got = extract_numerals("₹19 lakh over 33 years at 10% (₹2,400/mo)")
    assert "₹19 lakh" in got and "33 years" in got and "10%" in got and "₹2,400" in got


# --------------------------------------------------------------------------- #
# (a) Template mode is claim-consistent everywhere
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("pid", PERSONAS)
@pytest.mark.parametrize("lang", ["en", "hi"])
def test_template_only_claimed_numbers(pid, lang):
    for rec in _recs(pid):
        body = template_narration(rec, lang)
        assert validate(body, rec.numeric_claims), f"{rec.rec_id} [{lang}]: {body}"
        # And the full narration (with disclosure) still validates.
        assert validate(narrate(rec, lang), rec.numeric_claims)


def test_disclosure_is_appended_in_code():
    rec = _recs("young_spender")[0]
    out = narrate(rec, "en")
    assert disclosure("en") in out
    assert out.endswith(disclosure("en"))


# --------------------------------------------------------------------------- #
# (b) Hallucinated LLM output is rejected and falls back to template
# --------------------------------------------------------------------------- #

def test_hallucination_rejected_and_falls_back(monkeypatch):
    rec = _recs("young_spender")[0]
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    calls = {"n": 0}

    def fake_llm(prompt, lang):
        calls["n"] += 1
        return "You could earn ₹99,999 next year, guaranteed!"

    monkeypatch.setattr(narrator, "_call_gemini", fake_llm)
    out = narrate(rec, "en", mode="gemini")

    assert calls["n"] == 2                       # initial attempt + one retry
    assert "₹99,999" not in out                  # hallucination never surfaces
    assert out == narrate(rec, "en", mode="template")  # fell back to template
    assert validate(out, rec.numeric_claims)


def test_valid_llm_output_is_used(monkeypatch):
    rec = _recs("young_spender")[0]
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    claim = rec.money_figures["amount"]
    from app.engines.money import format_inr
    good = f"Let's begin with {format_inr(claim, 'en')} a month, {{NAME}}."
    monkeypatch.setattr(narrator, "_call_gemini", lambda p, l: good)
    out = narrate(rec, "en", mode="gemini")
    assert format_inr(claim, "en") in out
    assert "{NAME}" not in out                    # slot token stripped


def test_default_mode_is_template_without_key(monkeypatch):
    rec = _recs("young_spender")[0]
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    def boom(prompt, lang):
        raise AssertionError("LLM must not be called in template/default mode")

    monkeypatch.setattr(narrator, "_call_gemini", boom)
    # Neither the default nor an explicit gemini request (no key) hits the LLM.
    assert narrate(rec, "en") == narrate(rec, "en", mode="gemini")


# --------------------------------------------------------------------------- #
# (c) Injection strings never reach the prompt payload
# --------------------------------------------------------------------------- #

def test_converse_is_offline_without_key(monkeypatch):
    """The grounded conversational path must no-op (return None) with no key, so
    the deterministic template is used and tests never touch the network."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    def boom(system, user):
        raise AssertionError("Gemini must not be called without a key")

    monkeypatch.setattr(narrator, "_gemini_generate", boom)
    assert narrator.converse("what should I do?", "CONTEXT: balance ₹40,000",
                             ["₹40,000"], "en") is None


def test_injection_never_in_prompt():
    # young_spender's raw AA narrations include the injection canary.
    raw = (PERSONA_DIR / "young_spender.json").read_text("utf-8")
    assert "ignore-all-previous-instructions" in raw   # it IS in the source data

    for rec in _recs("young_spender"):
        payload = json.dumps(build_prompt(rec, "en"), ensure_ascii=False).lower()
        assert "ignore-all-previous-instructions" not in payload
        assert "swiggy" not in payload and "zomato" not in payload  # no raw merchants
        assert "aarav" not in payload                              # no holder PII
