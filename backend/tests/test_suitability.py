"""Step 3 gate (suitability): the investor-protection veto and its audit trail.

Central requirement: the near-retiree is never handed an aggressive-equity
recommendation, and the refusal is recorded with a reason in the trace.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.config import load_yaml
from app.engines.advisory import advise
from app.engines.behavioral import compute_fingerprint
from app.engines.suitability import for_narration, screen

PERSONA_DIR = Path(__file__).resolve().parents[1] / "app" / "data" / "personas"
EQUITY_ASSETS = load_yaml("suitability_rules.yaml")["equity_assets"]


def _fp(pid: str):
    return compute_fingerprint(json.loads((PERSONA_DIR / f"{pid}.json").read_text("utf-8")))


def _equity_pct(rec) -> float:
    return sum(v for k, v in rec.allocation.items() if k in EQUITY_ASSETS)


def test_near_retiree_never_gets_aggressive_equity():
    fp = _fp("near_retiree")
    screened = screen(fp, advise(fp))

    # An aggressive-equity candidate WAS produced and WAS vetoed with a reason.
    vetoed = [r for r in screened if r.status == "VETO"]
    assert vetoed, "expected suitability to veto at least one candidate"
    aggressive = next(r for r in vetoed if _equity_pct(r) > 30)
    assert aggressive.reasoning_trace.refusal_reason
    assert "ceiling" in aggressive.reasoning_trace.refusal_reason

    # Nothing aggressive survives to narration.
    for rec in for_narration(screened):
        assert _equity_pct(rec) <= 30, f"{rec.strategy_id} leaked past the gate"


def test_vetoed_recs_excluded_from_narration():
    fp = _fp("near_retiree")
    screened = screen(fp, advise(fp))
    narrated_ids = {r.rec_id for r in for_narration(screened)}
    veto_ids = {r.rec_id for r in screened if r.status == "VETO"}
    assert veto_ids and narrated_ids.isdisjoint(veto_ids)


@pytest.mark.parametrize("pid", ["young_spender", "disciplined_saver", "over_insured"])
def test_high_risk_keeps_equity_recs(pid):
    """HIGH risk-capacity investors are allowed their equity-tilted advice."""
    fp = _fp(pid)
    screened = screen(fp, advise(fp))
    equity_recs = [r for r in screened if _equity_pct(r) > 30]
    assert equity_recs, "expected at least one equity-tilted rec"
    assert all(r.status != "VETO" for r in equity_recs)


def test_screen_does_not_mutate_input():
    fp = _fp("near_retiree")
    candidates = advise(fp)
    before = [r.status for r in candidates]
    screen(fp, candidates)
    assert [r.status for r in candidates] == before  # deep-copied, inputs untouched
