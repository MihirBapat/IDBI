"""Step 3 gate (projection): deterministic goal math + Future Self branches."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.engines.behavioral import compute_fingerprint
from app.engines.projection import (EQUITY_NOMINAL, fd_maturity, future_self,
                                    retirement_corpus, sip_future_value)
from scripts.generate_aa_data import _BUILDERS

PERSONA_DIR = Path(__file__).resolve().parents[1] / "app" / "data" / "personas"
PERSONAS = list(_BUILDERS.keys())


def _fp(pid: str):
    return compute_fingerprint(json.loads((PERSONA_DIR / f"{pid}.json").read_text("utf-8")))


def test_sip_future_value_closed_form():
    # ₹1,000/mo (100000 paise) for 1 year, annuity-due @ 12% nominal.
    # i = 0.01, n = 12; FV = P * ((1.01^12 - 1)/0.01) * 1.01
    fv = sip_future_value(100000, 1, 12.0)
    expected = round(100000 * (((1.01 ** 12) - 1) / 0.01) * 1.01)
    assert fv == expected
    assert fv > 100000 * 12  # exceeds sum of contributions


def test_sip_future_value_edges():
    assert sip_future_value(0, 10, 10) == 0
    assert sip_future_value(100000, 0, 10) == 0
    # Longer horizon -> strictly larger corpus (compounding).
    assert sip_future_value(100000, 30, 10) > sip_future_value(100000, 20, 10)


def test_fd_maturity_compounds():
    m = fd_maturity(10_000_000, 7.0, 3)              # ₹1L @ 7% for 3y
    assert m == round(10_000_000 * (1.07 ** 3))
    assert m > 10_000_000


def test_retirement_corpus_uses_horizon_to_60():
    assert retirement_corpus(240000, 27) == sip_future_value(240000, 33, EQUITY_NOMINAL)


@pytest.mark.parametrize("pid", PERSONAS)
def test_future_self_good_beats_bad(pid):
    fp = _fp(pid)
    good = future_self(fp, take_advice=True)
    bad = future_self(fp, take_advice=False)
    assert good.take_advice is True and bad.take_advice is False
    assert good.corpus_paise >= bad.corpus_paise      # procrastination costs money
    # Both branches carry conservative-assumption traces and speak only claims.
    for script in (good, bad):
        assert script.reasoning_trace.strategy_id == "graham_margin_of_safety"
        assert script.lines and all(line.numeric_claims for line in script.lines)
        assert script.numeric_claims


def test_future_self_deterministic():
    fp = _fp("young_spender")
    assert future_self(fp, True).model_dump() == future_self(fp, True).model_dump()


def test_future_self_young_is_dramatic():
    """The young saver's good branch builds a materially larger corpus than bad."""
    fp = _fp("young_spender")
    good = future_self(fp, True)
    bad = future_self(fp, False)
    assert good.corpus_paise > bad.corpus_paise * 1.2
    assert good.horizon_years == 60 - fp.age
