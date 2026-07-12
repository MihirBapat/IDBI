"""behavioral.py — the Behavioral Financial Fingerprint.

``compute_fingerprint(fi_json) -> Fingerprint``: a pure, deterministic pandas
pipeline over one persona's ReBIT FI-JSON. No I/O beyond loading the versioned
``category_map.yaml``; no network; no LLM.

Raw narration strings are attacker-controlled (prompt-injection surface). They
are categorized against the closed vocabulary in ``category_map.yaml`` **inside
this module** and never leave it — only category codes and derived numbers flow
onward (architecture §4E, §5).

Field definitions
-----------------
* ``savings_ratio``  = (credits − debits) / credits over the trailing 3 months.
* ``spend_leaks``    = average monthly spend per *discretionary* category
  (``leak_categories`` in the map), sorted desc, kept when ≥ ₹1,000/mo.
* ``sip_discipline`` = fraction of the last 12 months containing an on-time SIP
  debit (SIP_DEBIT category), 0..1.
* ``idle_cash``      = max(0, average running balance − 2 × average monthly
  expenses) — cash beyond a 2-month buffer, sitting idle.
* ``insurance_gap``  = max(0, 10 × annual income − estimated cover), where cover
  is proxied from annual insurance premium (see ``_INSURANCE_COVER_MULTIPLE``).
  A rough heuristic, deliberately conservative; flagged, not authoritative.
* ``risk_capacity``  rubric (ability to absorb loss, not appetite):
      age ≥ 50                    -> LOW   (short horizon)
      40 ≤ age < 50               -> MEDIUM
      age < 40 and (savings_ratio ≥ 0.10 or sip_discipline ≥ 0.5) -> HIGH
      age < 40 otherwise          -> MEDIUM

Every field is returned as a ``Metric`` carrying ``as_of`` (latest transaction
date) and a ``confidence`` score.
"""

from __future__ import annotations

import re
from datetime import datetime

import pandas as pd

from app.config import load_yaml
from app.schemas import Fingerprint, Metric, PersonaFI, SpendLeak

ENGINE_VER = "behavioral-1.0.0"

_LEAK_MIN_MONTHLY = 100_000          # ₹1,000 in paise
_INSURANCE_COVER_MULTIPLE = 80       # crude term-cover proxy: annual premium × N
_TERM_COVER_MULTIPLE = 10            # recommended cover = 10 × annual income
_CONFIDENCE = 0.9                    # synthetic full-year data: fairly complete


def _load_rules() -> tuple[list[tuple[str, re.Pattern]], list[str]]:
    cfg = load_yaml("category_map.yaml")
    rules = [(r["category"], re.compile(r["pattern"], re.IGNORECASE))
             for r in cfg["rules"]]
    return rules, cfg["leak_categories"]


def categorize(narration: str, rules=None) -> str:
    """Map a raw narration to a closed-vocabulary category (first match wins)."""
    rules = rules or _load_rules()[0]
    for category, pattern in rules:
        if pattern.search(narration):
            return category
    return "OTHERS"


def _frame(persona: PersonaFI, rules) -> pd.DataFrame:
    rows = []
    for t in persona.deposit.transactions:
        rows.append({
            "date": pd.Timestamp(t.value_date),
            "type": t.type,
            "amount": t.amount,
            "balance": t.current_balance,
            "category": categorize(t.narration, rules),
        })
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    df["ym"] = df["date"].dt.to_period("M")
    return df


def _savings_ratio(df: pd.DataFrame) -> float:
    last3 = sorted(df["ym"].unique())[-3:]
    w = df[df["ym"].isin(last3)]
    credits = int(w.loc[w["type"] == "CREDIT", "amount"].sum())
    debits = int(w.loc[w["type"] == "DEBIT", "amount"].sum())
    if credits == 0:
        return 0.0
    return round((credits - debits) / credits, 4)


def _spend_leaks(df: pd.DataFrame, leak_categories: list[str]) -> list[SpendLeak]:
    n_months = df["ym"].nunique()
    debits = df[df["type"] == "DEBIT"]
    leaks: list[SpendLeak] = []
    for cat in leak_categories:
        c = debits[debits["category"] == cat]
        if c.empty:
            continue
        monthly = int(round(int(c["amount"].sum()) / n_months))
        if monthly >= _LEAK_MIN_MONTHLY:
            leaks.append(SpendLeak(category_code=cat, monthly_amount=monthly,
                                   txn_count=int(len(c))))
    # Deterministic order: largest leak first, category name as tie-breaker.
    leaks.sort(key=lambda l: (-l.monthly_amount, l.category_code))
    return leaks


def _sip_discipline(df: pd.DataFrame) -> float:
    months = sorted(df["ym"].unique())[-12:]
    sip = df[df["category"] == "SIP_DEBIT"]
    hit = {ym for ym in sip["ym"].unique()}
    on_time = sum(1 for ym in months if ym in hit)
    return round(on_time / len(months), 4) if months else 0.0


def _monthly_expenses(df: pd.DataFrame) -> int:
    n_months = df["ym"].nunique()
    debits = int(df.loc[df["type"] == "DEBIT", "amount"].sum())
    return int(round(debits / n_months))


def _idle_cash(df: pd.DataFrame, monthly_expenses: int) -> int:
    avg_balance = int(round(float(df["balance"].mean())))
    return max(0, avg_balance - 2 * monthly_expenses)


def _annual_income(df: pd.DataFrame) -> int:
    return int(df.loc[df["category"] == "SALARY", "amount"].sum())


def _insurance_gap(df: pd.DataFrame, annual_income: int) -> int:
    annual_premium = int(df.loc[df["category"] == "INSURANCE_PREMIUM", "amount"].sum())
    estimated_cover = annual_premium * _INSURANCE_COVER_MULTIPLE
    recommended = annual_income * _TERM_COVER_MULTIPLE
    return max(0, recommended - estimated_cover)


def _risk_capacity(age: int, savings_ratio: float, sip_discipline: float) -> str:
    if age >= 50:
        return "LOW"
    if age >= 40:
        return "MEDIUM"
    if savings_ratio >= 0.10 or sip_discipline >= 0.5:
        return "HIGH"
    return "MEDIUM"


def compute_fingerprint(fi_json: dict | PersonaFI) -> Fingerprint:
    """Compute the deterministic Behavioral Financial Fingerprint."""
    persona = fi_json if isinstance(fi_json, PersonaFI) else PersonaFI.model_validate(fi_json)
    rules, leak_categories = _load_rules()
    df = _frame(persona, rules)

    as_of = df["date"].max().to_pydatetime()

    savings_ratio = _savings_ratio(df)
    sip_discipline = _sip_discipline(df)
    monthly_expenses = _monthly_expenses(df)
    idle_cash = _idle_cash(df, monthly_expenses)
    equity_holding = int(sum(mf.current_value for mf in persona.mutual_funds))
    annual_income = _annual_income(df)
    insurance_gap = _insurance_gap(df, annual_income)
    leaks = _spend_leaks(df, leak_categories)
    risk = _risk_capacity(persona.profile.age, savings_ratio, sip_discipline)

    def metric(value):
        return Metric(value=value, as_of=as_of, confidence=_CONFIDENCE)

    return Fingerprint(
        persona_id=persona.persona_id,
        age=persona.profile.age,
        monthly_income=metric(int(round(annual_income / 12))),
        savings_ratio=metric(savings_ratio),
        spend_leaks=metric(leaks),
        sip_discipline=metric(sip_discipline),
        idle_cash=metric(idle_cash),
        equity_holding=metric(equity_holding),
        insurance_gap=metric(insurance_gap),
        risk_capacity=metric(risk),
    )
