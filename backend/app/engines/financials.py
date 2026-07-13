"""financials.py — the customer's financial snapshot (for the side panel + as
grounding context for the conversational narrator).

Two products from one place:

* ``summary(persona, fingerprint)`` — a rich, display-ready snapshot (balance,
  metrics, spending-by-category, holdings, recent activity) for the UI's
  financial side panel. Raw transaction narrations ARE included here — they are
  the customer's own records, shown only to the customer.
* ``grounding_context`` / ``grounding_claims`` — a numbers-only view for the LLM:
  no raw merchant strings (kept quarantined), and an explicit whitelist of the
  exact display figures the narrator is permitted to utter (the validator's set).

All formatting goes through money.py; money stays integer paise.
"""

from __future__ import annotations

from collections import defaultdict

from app.engines.behavioral import _load_rules, categorize
from app.engines.money import format_inr, format_pct
from app.schemas import Fingerprint, PersonaFI, Recommendation

# Categories that are transfers/investments, not "spending", excluded from the
# discretionary spend breakdown.
_NON_SPEND = {"SALARY", "INTEREST_CREDIT", "SIP_DEBIT", "FD_CREATION"}


def summary(persona: PersonaFI, fp: Fingerprint) -> dict:
    rules = _load_rules()[0]
    txns = persona.deposit.transactions

    months = {(t.value_date.year, t.value_date.month) for t in txns}
    n_months = len(months) or 1

    tot: dict[str, int] = defaultdict(int)
    cnt: dict[str, int] = defaultdict(int)
    for t in txns:
        if t.type == "DEBIT":
            c = categorize(t.narration, rules)
            if c in _NON_SPEND:
                continue
            tot[c] += t.amount
            cnt[c] += 1
    spending = sorted(
        ({"category": c, "monthly_paise": round(v / n_months),
          "monthly_display": format_inr(round(v / n_months)), "txn_count": cnt[c]}
         for c, v in tot.items()),
        key=lambda x: -x["monthly_paise"],
    )

    recent = sorted(txns, key=lambda t: t.value_date, reverse=True)[:10]
    recent_out = [{
        "date": t.value_date.isoformat(),
        "category": categorize(t.narration, rules),
        "type": t.type,
        "amount_display": ("+ " if t.type == "CREDIT" else "− ") + format_inr(t.amount),
        "narration": t.narration,  # display-only; never sent to the LLM
    } for t in recent]

    fds = [{
        "name": f"IDBI FD · {td.tenure_months // 12}y" if td.tenure_months % 12 == 0
                else f"IDBI FD · {td.tenure_months}m",
        "principal_display": format_inr(td.principal),
        "rate_display": format_pct(td.interest_rate),
        "maturity_display": format_inr(td.maturity_amount),
    } for td in persona.term_deposits]

    mfs = [{
        "scheme": mf.scheme,
        "current_display": format_inr(mf.current_value),
        "cost_display": format_inr(mf.cost_value),
        "sip": mf.sip_flag,
    } for mf in persona.mutual_funds]

    sr_pct = round(fp.savings_ratio.value * 100, 1)
    sip_pct = round(fp.sip_discipline.value * 100)

    return {
        "name": persona.profile.holder_name,
        "age": persona.profile.age,
        "risk_capacity": fp.risk_capacity.value,
        "balance_paise": persona.deposit.current_balance,
        "balance_display": format_inr(persona.deposit.current_balance),
        "monthly_income_display": format_inr(fp.monthly_income.value),
        "savings_ratio_pct": sr_pct,
        "sip_discipline_pct": sip_pct,
        "idle_cash_display": format_inr(fp.idle_cash.value),
        "equity_holding_display": format_inr(fp.equity_holding.value),
        "insurance_gap_display": format_inr(fp.insurance_gap.value),
        "spend_leaks": [
            {"category": l.category_code, "monthly_display": format_inr(l.monthly_amount)}
            for l in fp.spend_leaks.value
        ],
        "spending": spending,
        "holdings": {"fixed_deposits": fds, "mutual_funds": mfs},
        "recent": recent_out,
    }


# --------------------------------------------------------------------------- #
# LLM grounding — numbers only, no raw narrations
# --------------------------------------------------------------------------- #

def grounding_context(summary_: dict, recs: list[Recommendation]) -> str:
    """Plain-text context block for the narrator prompt. No raw merchant strings."""
    lines = [
        f"Customer: {summary_['name']}, age {summary_['age']}. "
        f"Risk capacity: {summary_['risk_capacity']}.",
        f"Current savings balance: {summary_['balance_display']}.",
        f"Monthly income: {summary_['monthly_income_display']}. "
        f"Savings rate: {summary_['savings_ratio_pct']}%. "
        f"SIP discipline: {summary_['sip_discipline_pct']}%.",
        f"Idle cash beyond buffer: {summary_['idle_cash_display']}. "
        f"Current equity holdings: {summary_['equity_holding_display']}. "
        f"Estimated term-insurance gap: {summary_['insurance_gap_display']}.",
    ]
    if summary_["spending"]:
        parts = ", ".join(f"{s['category']} {s['monthly_display']}/mo"
                          for s in summary_["spending"][:6])
        lines.append(f"Monthly spending by category: {parts}.")
    if summary_["holdings"]["fixed_deposits"]:
        fd = "; ".join(f"{h['principal_display']} at {h['rate_display']}"
                       for h in summary_["holdings"]["fixed_deposits"])
        lines.append(f"Fixed deposits: {fd}.")
    if summary_["holdings"]["mutual_funds"]:
        mf = "; ".join(f"{h['scheme']} worth {h['current_display']}"
                       for h in summary_["holdings"]["mutual_funds"])
        lines.append(f"Mutual funds: {mf}.")
    if recs:
        lines.append("Recommended actions the engine has prepared:")
        for r in recs:
            amt = format_inr(r.amount_paise) if r.amount_paise else "—"
            alloc = ", ".join(f"{k} {int(v)}%" for k, v in r.allocation.items())
            lines.append(f"- {r.title}: {amt} ({alloc}). "
                         f"Principle: {r.reasoning_trace.source_principle}.")
    lines.append("You may ONLY cite numbers from this context; never invent figures.")
    return "\n".join(lines)


def grounding_claims(summary_: dict, recs: list[Recommendation]) -> list[str]:
    """Whitelist of every display figure the narrator may utter for this turn."""
    claims: list[str] = [
        summary_["balance_display"], summary_["monthly_income_display"],
        summary_["idle_cash_display"], summary_["equity_holding_display"],
        summary_["insurance_gap_display"],
        f"{summary_['savings_ratio_pct']}%", f"{summary_['sip_discipline_pct']}%",
        str(summary_["age"]), "60",
    ]
    for s in summary_["spending"]:
        claims.append(s["monthly_display"])
    for l in summary_["spend_leaks"]:
        claims.append(l["monthly_display"])
    for h in summary_["holdings"]["fixed_deposits"]:
        claims += [h["principal_display"], h["rate_display"], h["maturity_display"]]
    for h in summary_["holdings"]["mutual_funds"]:
        claims += [h["current_display"], h["cost_display"]]
    for r in recs:
        claims += r.numeric_claims
        if r.amount_paise:
            claims.append(format_inr(r.amount_paise))
        for v in r.allocation.values():
            claims.append(format_pct(v))
    # De-duplicate, preserve order.
    seen: dict[str, None] = {}
    for c in claims:
        seen.setdefault(c, None)
    return list(seen.keys())
