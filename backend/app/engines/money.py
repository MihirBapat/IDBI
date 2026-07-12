"""money.py — the ONE place currency/number formatting happens.

INVARIANT (architecture §5, CLAUDE.md §3): money is integer paise everywhere;
₹/lakh/crore formatting occurs here and nowhere else — never in another engine,
never in the LLM. The narrator may only utter display strings produced here (the
NumericClaimSet); the output validator rejects any numeral outside that set.

Every amount has an English and a Hindi display form (Hinglish digits, Devanagari
unit words), because the narrator speaks EN/HI/Hinglish and the validator must
accept whichever it renders.
"""

from __future__ import annotations

_LAKH = 100_000        # rupees
_CRORE = 10_000_000    # rupees


def _indian_group(rupees: int) -> str:
    """Group an integer rupee amount with Indian thousands/lakh separators."""
    s = str(rupees)
    if len(s) <= 3:
        return s
    last3, rest = s[-3:], s[:-3]
    parts: list[str] = []
    while len(rest) > 2:
        parts.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        parts.insert(0, rest)
    return ",".join(parts) + "," + last3


def _trim(x: float) -> str:
    """Two-decimal string with trailing zeros and dot stripped (2.50 -> '2.5')."""
    return f"{x:.2f}".rstrip("0").rstrip(".")


def format_inr(paise: int, lang: str = "en") -> str:
    """Format integer paise as an Indian-convention rupee string.

    < ₹1 lakh -> grouped rupees ("₹14,000"); ₹1 lakh..< ₹1 crore -> "₹3.2 lakh"
    / "₹3.2 लाख"; >= ₹1 crore -> "₹2.4 crore" / "₹2.4 करोड़".
    """
    neg = paise < 0
    rupees_f = abs(paise) / 100
    if rupees_f < _LAKH:
        body = "₹" + _indian_group(int(round(rupees_f)))
    elif rupees_f < _CRORE:
        unit = "lakh" if lang == "en" else "लाख"
        body = f"₹{_trim(rupees_f / _LAKH)} {unit}"
    else:
        unit = "crore" if lang == "en" else "करोड़"
        body = f"₹{_trim(rupees_f / _CRORE)} {unit}"
    return ("-" + body) if neg else body


def format_pct(rate: float) -> str:
    """Format a percentage: 10.0 -> '10%', 6.5 -> '6.5%'."""
    return f"{_trim(rate)}%"


def format_years(n: int, lang: str = "en") -> str:
    """Format a tenor in years: '20 years' / '20 साल'."""
    return f"{n} {'years' if lang == 'en' else 'साल'}"


def inr_claims(paise: int) -> list[str]:
    """Both language forms of an amount, de-duplicated (equal below ₹1 lakh)."""
    en, hi = format_inr(paise, "en"), format_inr(paise, "hi")
    return [en] if en == hi else [en, hi]


def year_claims(n: int) -> list[str]:
    en, hi = format_years(n, "en"), format_years(n, "hi")
    return [en] if en == hi else [en, hi]
