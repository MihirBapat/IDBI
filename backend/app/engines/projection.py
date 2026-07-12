"""projection.py — deterministic goal math and the Future Self script.

Pure integer-paise arithmetic. Return assumptions are deliberately conservative
(Graham's margin of safety, CLAUDE.md §3): 10% nominal equity, 6.5% nominal debt
— never optimistic. Every figure the aged avatar speaks is emitted here and
carried in ``numeric_claims`` so the narrator can only voice engine-produced
numbers.
"""

from __future__ import annotations

from app.config import file_sha, load_yaml
from app.engines.money import format_years, inr_claims, year_claims
from app.schemas import ProjectionLine, ProjectionScript, ReasoningTrace

ENGINE_VER = "projection-1.0.0"

EQUITY_NOMINAL = 10.0   # % p.a., conservative
DEBT_NOMINAL = 6.5      # % p.a., conservative
RETIREMENT_AGE = 60
PROCRASTINATION_YEARS = 5  # the "bad branch" delay


def sip_future_value(monthly_paise: int, years: int, annual_rate: float) -> int:
    """Future value of a monthly SIP (annuity-due) in integer paise.

    Contributions are made at the start of each month and compound monthly.
    """
    if years <= 0 or monthly_paise <= 0:
        return 0
    i = annual_rate / 100.0 / 12.0
    n = years * 12
    fv = monthly_paise * (((1 + i) ** n - 1) / i) * (1 + i)
    return int(round(fv))


def fd_maturity(principal_paise: int, annual_rate: float, years: float) -> int:
    """Annually-compounded FD maturity value in integer paise."""
    return int(round(principal_paise * (1 + annual_rate / 100.0) ** years))


def retirement_corpus(monthly_sip_paise: int, current_age: int,
                      annual_rate: float = EQUITY_NOMINAL) -> int:
    """Corpus at age 60 from a monthly equity SIP started now."""
    return sip_future_value(monthly_sip_paise, max(RETIREMENT_AGE - current_age, 0),
                            annual_rate)


def _trace(inputs: dict, math_steps: list[str]) -> ReasoningTrace:
    strat = next(s for s in load_yaml("strategy_library.yaml")["strategies"]
                 if s["id"] == "graham_margin_of_safety")
    return ReasoningTrace(
        strategy_id="graham_margin_of_safety",
        source_principle=strat["source_principle"],
        inputs_used=inputs,
        math_steps=math_steps,
        engine_ver=ENGINE_VER,
        shelf_sha=file_sha("product_shelf.yaml"),
        strategy_sha=file_sha("strategy_library.yaml"),
    )


def future_self(fingerprint, take_advice: bool) -> ProjectionScript:
    """Build the 30-year Future Self narration for one branch.

    The SIP amount is grounded in the user's own behavior: half of the food-
    delivery leak if present, else 5% of monthly income. The good branch starts
    today; the bad branch procrastinates ``PROCRASTINATION_YEARS`` years.
    """
    age = fingerprint.age
    leaks = {l.category_code: l.monthly_amount for l in fingerprint.spend_leaks.value}
    if "FOOD_DELIVERY" in leaks:
        monthly = leaks["FOOD_DELIVERY"] // 2
    else:
        monthly = int(round(fingerprint.monthly_income.value * 0.05))
    horizon = max(RETIREMENT_AGE - age, 1)

    if take_advice:
        corpus = sip_future_value(monthly, horizon, EQUITY_NOMINAL)
        lines = [
            ProjectionLine(
                text=(f"Because you started a {{amt}}/month SIP at {age}, "
                      f"I retired at {RETIREMENT_AGE} with {{corpus}}."),
                numeric_claims=inr_claims(monthly) + inr_claims(corpus),
            ),
            ProjectionLine(
                text=f"That was {format_years(horizon)} of small, automatic investing. Thank you.",
                numeric_claims=year_claims(horizon),
            ),
        ]
        math = [
            f"SIP = {monthly} paise/mo (half the food-delivery leak)",
            f"horizon = 60 - {age} = {horizon} years",
            f"FV @ {EQUITY_NOMINAL}% nominal = {corpus} paise",
        ]
        corpus_out = corpus
        claims = inr_claims(monthly) + inr_claims(corpus) + year_claims(horizon)
    else:
        effective = max(horizon - PROCRASTINATION_YEARS, 0)
        corpus = sip_future_value(monthly, effective, EQUITY_NOMINAL)
        good = sip_future_value(monthly, horizon, EQUITY_NOMINAL)
        cost = good - corpus
        lines = [
            ProjectionLine(
                text=(f"You waited {format_years(PROCRASTINATION_YEARS)} before investing. "
                      f"I reached {RETIREMENT_AGE} with only {{corpus}}."),
                numeric_claims=inr_claims(corpus) + year_claims(PROCRASTINATION_YEARS),
            ),
            ProjectionLine(
                text="Those years cost us {cost}. I am still working.",
                numeric_claims=inr_claims(cost),
            ),
        ]
        math = [
            f"SIP = {monthly} paise/mo, delayed {PROCRASTINATION_YEARS} years",
            f"effective horizon = {effective} years",
            f"FV @ {EQUITY_NOMINAL}% = {corpus} paise; delay cost = {cost} paise",
        ]
        corpus_out = corpus
        claims = (inr_claims(monthly) + inr_claims(corpus) + inr_claims(cost)
                  + year_claims(PROCRASTINATION_YEARS))

    # De-duplicate claim strings, preserving order.
    seen: dict[str, None] = {}
    for c in claims:
        seen.setdefault(c, None)

    return ProjectionScript(
        persona_id=fingerprint.persona_id,
        take_advice=take_advice,
        horizon_years=horizon,
        corpus_paise=corpus_out,
        lines=lines,
        numeric_claims=list(seen.keys()),
        reasoning_trace=_trace(
            inputs={"age": age, "monthly_sip_paise": monthly, "horizon_years": horizon},
            math_steps=math,
        ),
    )
