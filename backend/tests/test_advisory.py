"""Step 3 gate (advisory): golden fixtures, exact amounts, pinned shas, determinism.

The golden files are the regression anchors — a fresh advise+screen run must
reproduce them byte-for-byte. On top of that we hard-assert the primary strategy
and the headline amounts per persona (non-circular), and verify every trace pins
the live config shas.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.config import file_sha
from app.engines.advisory import advise
from app.engines.behavioral import compute_fingerprint
from app.engines.suitability import screen

BACKEND = Path(__file__).resolve().parents[1]
PERSONA_DIR = BACKEND / "app" / "data" / "personas"
GOLDEN_DIR = BACKEND / "tests" / "golden"

PERSONAS = ["young_spender", "disciplined_saver", "idle_cash",
            "over_insured", "near_retiree"]


def _fp(pid: str):
    return compute_fingerprint(json.loads((PERSONA_DIR / f"{pid}.json").read_text("utf-8")))


def _screened(pid: str):
    fp = _fp(pid)
    return fp, screen(fp, advise(fp))


@pytest.mark.parametrize("pid", PERSONAS)
def test_matches_golden(pid):
    golden = json.loads((GOLDEN_DIR / f"{pid}.json").read_text("utf-8"))
    _, recs = _screened(pid)
    live = [r.model_dump(mode="json") for r in recs]
    assert live == golden["recommendations"]


@pytest.mark.parametrize("pid,primary", [
    ("young_spender", "bogle_index_sip"),
    ("disciplined_saver", "goals_based_stepup"),
    ("idle_cash", "markowitz_concentration"),
    ("over_insured", "bogle_index_sip"),
    ("near_retiree", "dalio_all_weather"),
])
def test_primary_strategy(pid, primary):
    _, recs = _screened(pid)
    assert recs[0].strategy_id == primary


def test_exact_amounts_to_the_paisa():
    """Headline amounts are exact integer paise, independent of the golden echo."""
    _, young = _screened("young_spender")
    bogle = next(r for r in young if r.strategy_id == "bogle_index_sip")
    # young food-delivery leak is ₹4,800/mo -> redirect half -> ₹2,400 = 240000 paise.
    assert bogle.amount_paise == 240000

    fp_idle, idle = _screened("idle_cash")
    mk = next(r for r in idle if r.strategy_id == "markowitz_concentration")
    assert mk.amount_paise == fp_idle.idle_cash.value  # moves exactly the idle cash


@pytest.mark.parametrize("pid", PERSONAS)
def test_traces_pin_both_shas(pid):
    shelf, strat = file_sha("product_shelf.yaml"), file_sha("strategy_library.yaml")
    _, recs = _screened(pid)
    assert recs
    for r in recs:
        t = r.reasoning_trace
        assert t.shelf_sha == shelf and len(t.shelf_sha) == 12
        assert t.strategy_sha == strat and len(t.strategy_sha) == 12
        assert t.engine_ver and t.source_principle
        assert t.math_steps


@pytest.mark.parametrize("pid", PERSONAS)
def test_deterministic(pid):
    fp = _fp(pid)
    a = [r.model_dump(mode="json") for r in screen(fp, advise(fp))]
    b = [r.model_dump(mode="json") for r in screen(fp, advise(fp))]
    assert a == b


@pytest.mark.parametrize("pid", PERSONAS)
def test_all_products_on_shelf(pid):
    from app.config import load_yaml
    shelf = load_yaml("product_shelf.yaml")
    ids = {p["product_id"] for group in shelf.values() if isinstance(group, list)
           for p in group}
    _, recs = _screened(pid)
    for r in recs:
        if r.product_ref:
            assert r.product_ref in ids, f"{r.product_ref} not on IDBI shelf"
