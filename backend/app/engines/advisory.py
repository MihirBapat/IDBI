"""advisory.py — deterministic strategy selection and recommendation building.

``advise(fingerprint, goals) -> list[Recommendation]``. Strategies from
``strategy_library.yaml`` are evaluated in a fixed priority order; each triggered
strategy emits one Recommendation whose every number is computed here (and, for
projections, in projection.py) and formatted only via money.py. Each rec carries
a ``reasoning_trace`` pinning ``engine_ver``, ``shelf_sha``, ``strategy_sha`` so
the advice is replayable and any config change is a failing test diff.

The LLM never runs here. Suitability screening is a separate gate
(suitability.py) applied to this output before narration.
"""

from __future__ import annotations

from typing import Callable, Optional

from app.config import file_sha, load_yaml
from app.engines import projection
from app.engines.money import format_pct, inr_claims, year_claims
from app.schemas import Fingerprint, Recommendation, ReasoningTrace

ENGINE_VER = "advisory-1.0.0"

# Paise thresholds.
_L2 = 20_000_000    # ₹2 lakh
_L3 = 30_000_000    # ₹3 lakh
_EQUITY_THIN = 5_000_000  # ₹50k


def _shelf() -> dict:
    return load_yaml("product_shelf.yaml")


def _strategy_meta(strategy_id: str) -> dict:
    return next(s for s in load_yaml("strategy_library.yaml")["strategies"]
                if s["id"] == strategy_id)


def _best_fd() -> dict:
    """Representative FD-ladder rung (3-year, no lock-in) for idle-cash moves."""
    fds = _shelf()["fixed_deposits"]
    return next(f for f in fds if f["product_id"] == "idbi_fd_3y")


def _trace(strategy_id: str, inputs: dict, math_steps: list[str],
           ) -> ReasoningTrace:
    meta = _strategy_meta(strategy_id)
    return ReasoningTrace(
        strategy_id=strategy_id,
        source_principle=meta["source_principle"],
        inputs_used=inputs,
        math_steps=math_steps,
        engine_ver=ENGINE_VER,
        shelf_sha=file_sha("product_shelf.yaml"),
        strategy_sha=file_sha("strategy_library.yaml"),
    )


def _alloc(strategy_id: str) -> dict[str, float]:
    return {k: float(v) for k, v in _strategy_meta(strategy_id)["allocation_template"].items()}


def _pct_claims(alloc: dict[str, float]) -> list[str]:
    return [format_pct(v) for v in alloc.values()]


def _dedup(items: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for it in items:
        seen.setdefault(it, None)
    return list(seen.keys())


def _top_leak(fp: Fingerprint) -> Optional[object]:
    leaks = fp.spend_leaks.value
    return leaks[0] if leaks else None


def _food_leak(fp: Fingerprint) -> Optional[int]:
    for l in fp.spend_leaks.value:
        if l.category_code == "FOOD_DELIVERY":
            return l.monthly_amount
    return None


# --------------------------------------------------------------------------- #
# Strategy builders — each returns a Recommendation (pre-suitability)
# --------------------------------------------------------------------------- #

def _build_goals_stepup(fp: Fingerprint) -> Recommendation:
    sid = "goals_based_stepup"
    income = fp.monthly_income.value
    add = int(round(income * 0.05))
    years = max(60 - fp.age, 1)
    fv = projection.sip_future_value(add, years, projection.EQUITY_NOMINAL)
    alloc = _alloc(sid)
    claims = _dedup(inr_claims(add) + inr_claims(fv) + inr_claims(income)
                    + year_claims(years) + _pct_claims(alloc))
    return Recommendation(
        rec_id=f"{fp.persona_id}:{sid}", action="step_up_sip",
        product_ref="idbi_suvidha_sip", amount_paise=add, allocation=alloc,
        strategy_id=sid, title="Escalate your disciplined SIP toward your goals",
        numeric_claims=claims,
        reasoning_trace=_trace(sid,
            inputs={"monthly_income": income, "years": years},
            math_steps=[f"step-up = 5% of income {income} = {add} paise/mo",
                        f"FV over {years}y @10% = {fv} paise"]),
    )


def _build_bogle_sip(fp: Fingerprint) -> Recommendation:
    sid = "bogle_index_sip"
    food = _food_leak(fp) or _top_leak(fp).monthly_amount
    amount = food // 2
    years = max(60 - fp.age, 1)
    fv = projection.sip_future_value(amount, years, projection.EQUITY_NOMINAL)
    alloc = _alloc(sid)
    claims = _dedup(inr_claims(amount) + inr_claims(food) + inr_claims(fv)
                    + year_claims(years) + _pct_claims(alloc))
    return Recommendation(
        rec_id=f"{fp.persona_id}:{sid}", action="start_sip",
        product_ref="idbi_nifty_index", amount_paise=amount, allocation=alloc,
        strategy_id=sid, title="Start a low-cost index SIP from your food-delivery spend",
        numeric_claims=claims,
        reasoning_trace=_trace(sid,
            inputs={"food_leak": food, "years": years},
            math_steps=[f"food-delivery leak = {food} paise/mo",
                        f"redirect 50% = {amount} paise/mo",
                        f"FV over {years}y @10% = {fv} paise"]),
    )


def _build_dalio(fp: Fingerprint) -> Recommendation:
    sid = "dalio_all_weather"
    amount = fp.idle_cash.value
    alloc = _alloc(sid)
    buckets = {k: int(round(amount * v / 100)) for k, v in alloc.items()}
    claims = _dedup(inr_claims(amount) + _pct_claims(alloc)
                    + [c for b in buckets.values() for c in inr_claims(b)])
    return Recommendation(
        rec_id=f"{fp.persona_id}:{sid}", action="deploy_all_weather",
        product_ref="idbi_gilt_fund", amount_paise=amount, allocation=alloc,
        strategy_id=sid, title="Deploy idle cash into a capital-preserving All-Weather mix",
        numeric_claims=claims,
        reasoning_trace=_trace(sid,
            inputs={"idle_cash": amount},
            math_steps=[f"deploy idle {amount} paise across {alloc}"]),
    )


def _build_markowitz(fp: Fingerprint) -> Recommendation:
    sid = "markowitz_concentration"
    amount = fp.idle_cash.value
    fd = _best_fd()
    sb = _shelf()["savings_rate"]
    extra = int(round(amount * (fd["rate"] - sb) / 100))
    alloc = _alloc(sid)
    claims = _dedup(inr_claims(amount) + inr_claims(extra)
                    + [format_pct(fd["rate"]), format_pct(sb)] + _pct_claims(alloc))
    return Recommendation(
        rec_id=f"{fp.persona_id}:{sid}", action="move_to_fd",
        product_ref=fd["product_id"], amount_paise=amount, allocation=alloc,
        strategy_id=sid, title="Move idle savings into a laddered IDBI FD",
        numeric_claims=claims,
        reasoning_trace=_trace(sid,
            inputs={"idle_cash": amount, "fd_rate": fd["rate"], "savings_rate": sb},
            math_steps=[f"idle cash = {amount} paise (100% cash concentration)",
                        f"IDBI FD {fd['rate']}% vs SB {sb}%",
                        f"extra interest/yr = {amount}*({fd['rate']}-{sb})/100 = {extra} paise"]),
    )


def _build_swensen(fp: Fingerprint) -> Recommendation:
    sid = "swensen_diversify"
    amount = int(round(fp.monthly_income.value * 0.10))
    alloc = _alloc(sid)
    claims = _dedup(inr_claims(amount) + _pct_claims(alloc))
    return Recommendation(
        rec_id=f"{fp.persona_id}:{sid}", action="diversify_sip",
        product_ref="idbi_nifty_index", amount_paise=amount, allocation=alloc,
        strategy_id=sid, title="Diversify thin equity across a Swensen-style mix",
        numeric_claims=claims,
        reasoning_trace=_trace(sid,
            inputs={"monthly_income": fp.monthly_income.value},
            math_steps=[f"diversified SIP = 10% of income = {amount} paise/mo across {alloc}"]),
    )


def _build_buffett(fp: Fingerprint) -> Recommendation:
    sid = "buffett_9010"
    amount = fp.idle_cash.value
    alloc = _alloc(sid)
    buckets = {k: int(round(amount * v / 100)) for k, v in alloc.items()}
    claims = _dedup(inr_claims(amount) + _pct_claims(alloc)
                    + [c for b in buckets.values() for c in inr_claims(b)])
    return Recommendation(
        rec_id=f"{fp.persona_id}:{sid}", action="deploy_9010",
        product_ref="idbi_nifty_index", amount_paise=amount, allocation=alloc,
        strategy_id=sid, title="Put surplus to work with a Buffett 90/10 split",
        numeric_claims=claims,
        reasoning_trace=_trace(sid,
            inputs={"idle_cash": amount},
            math_steps=[f"deploy {amount} paise as 90/10 index/gilt"]),
    )


# --------------------------------------------------------------------------- #
# Registry — (predicate, builder), evaluated in this fixed priority order
# --------------------------------------------------------------------------- #

_REGISTRY: list[tuple[Callable[[Fingerprint], bool], Callable[[Fingerprint], Recommendation]]] = [
    (lambda fp: fp.sip_discipline.value >= 0.5 and fp.savings_ratio.value > 0.30,
     _build_goals_stepup),
    (lambda fp: (fp.sip_discipline.value < 0.5 and fp.risk_capacity.value in ("MEDIUM", "HIGH")
                 and bool(fp.spend_leaks.value) and fp.idle_cash.value < _L3),
     _build_bogle_sip),
    (lambda fp: fp.risk_capacity.value == "LOW", _build_dalio),
    (lambda fp: fp.idle_cash.value >= _L3, _build_markowitz),
    (lambda fp: fp.equity_holding.value < _EQUITY_THIN, _build_swensen),
    (lambda fp: fp.risk_capacity.value == "HIGH"
                and (fp.savings_ratio.value > 0.30 or fp.idle_cash.value >= _L2),
     _build_buffett),
]


def advise(fingerprint: Fingerprint, goals: Optional[list] = None) -> list[Recommendation]:
    """Return the deterministic list of candidate recommendations (pre-suitability)."""
    return [build(fingerprint) for predicate, build in _REGISTRY if predicate(fingerprint)]
