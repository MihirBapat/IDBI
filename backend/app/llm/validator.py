"""validator.py — the numeral-membership gate.

The determinism boundary's hard edge (architecture §5, §8): a narration may only
contain numbers the engine produced. ``validate(text, numeric_claims)`` extracts
every numeral-bearing token from the prose and requires each to be a substring of
some claim in the NumericClaimSet. Any escape → reject (caller retries once, then
falls back to template mode). Escape budget: zero.
"""

from __future__ import annotations

import re

# Ordered alternation: prefer ₹-amounts (with optional lakh/crore), then
# unit-suffixed numbers (%/years/साल), then bare numbers. Left-to-right, longest
# meaningful token wins so "₹19 lakh" and "33 years" are captured whole.
_TOKEN = re.compile(
    r"₹\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:lakh|crore|लाख|करोड़))?"
    r"|\d[\d,]*(?:\.\d+)?\s?(?:%|years|साल|लाख|करोड़|lakh|crore)"
    r"|\d[\d,]*(?:\.\d+)?"
)


def _norm(s: str) -> str:
    """Collapse internal whitespace so '₹19  lakh' == '₹19 lakh'."""
    return re.sub(r"\s+", " ", s).strip()


def extract_numerals(text: str) -> list[str]:
    """Every numeral-bearing token in the text, normalized."""
    return [_norm(m) for m in _TOKEN.findall(text)]


def validate(text: str, numeric_claims: list[str]) -> bool:
    """True iff every numeral in ``text`` is a substring of some claim.

    Non-numeric prose is unrestricted; a text with no numerals passes trivially.
    """
    claims = [_norm(c) for c in numeric_claims]
    for token in extract_numerals(text):
        if not any(token in claim for claim in claims):
            return False
    return True
