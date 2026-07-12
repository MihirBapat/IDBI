"""suitability.py — the investor-protection gate.

``screen(fingerprint, recommendations) -> list[Recommendation]``: runs AFTER
advisory and BEFORE narration. Each candidate is scored PASS / SOFTEN / VETO
against ``suitability_rules.yaml``. A VETO records a ``refusal_reason`` on the
recommendation's ``reasoning_trace`` — the engine can decline and explain, not
only recommend. Callers narrate only non-VETO recommendations (``for_narration``).

Rules enforced:
  * Equity ceiling by risk capacity, with age ≥ threshold forcing the LOW cap
    (short horizon dominates). Equity % above the ceiling -> VETO.
  * Lump-sum amount must not exceed the investor's idle surplus -> SOFTEN
    (amount clamped to idle) when it would.
"""

from __future__ import annotations

import copy

from app.config import load_yaml
from app.engines.money import format_pct
from app.schemas import Fingerprint, Recommendation

_LUMP_ACTIONS = {"move_to_fd", "deploy_all_weather", "deploy_9010"}


def _rules() -> dict:
    return load_yaml("suitability_rules.yaml")


def _equity_pct(rec: Recommendation, equity_assets: list[str]) -> float:
    return sum(v for k, v in rec.allocation.items() if k in equity_assets)


def _equity_cap(fp: Fingerprint, rules: dict) -> int:
    caps = rules["equity_cap_by_risk"]
    cap = caps[fp.risk_capacity.value]
    if fp.age >= rules["age_low_risk_threshold"]:
        cap = min(cap, caps["LOW"])
    return cap


def screen(fingerprint: Fingerprint,
           recommendations: list[Recommendation]) -> list[Recommendation]:
    """Annotate each recommendation with a suitability verdict."""
    rules = _rules()
    equity_assets = rules["equity_assets"]
    cap = _equity_cap(fingerprint, rules)
    out: list[Recommendation] = []

    for rec in recommendations:
        rec = copy.deepcopy(rec)
        equity_pct = _equity_pct(rec, equity_assets)

        if equity_pct > cap:
            rec.status = "VETO"
            rec.reasoning_trace.refusal_reason = (
                f"{format_pct(equity_pct)} equity exceeds the {cap}% ceiling for a "
                f"{fingerprint.risk_capacity.value} risk-capacity investor aged "
                f"{fingerprint.age}."
            )
            out.append(rec)
            continue

        # Lump-sum amount must fit within idle surplus.
        if (rules.get("enforce_amount_within_idle") and rec.action in _LUMP_ACTIONS
                and rec.amount_paise and rec.amount_paise > fingerprint.idle_cash.value):
            rec.status = "SOFTEN"
            rec.reasoning_trace.refusal_reason = (
                f"amount clamped to idle surplus of {fingerprint.idle_cash.value} paise."
            )
            rec.amount_paise = fingerprint.idle_cash.value

        out.append(rec)

    return out


def for_narration(recommendations: list[Recommendation]) -> list[Recommendation]:
    """Only PASS/SOFTEN recommendations are eligible to reach the narrator."""
    return [r for r in recommendations if r.status != "VETO"]
