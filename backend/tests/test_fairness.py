"""SEBI fairness pillar — fairness by construction, made testable.

The advice is a function of the *behavioral* fingerprint only. Holder name, PAN,
gender, caste, religion and the persona label are never inputs — indeed the FI
schema refuses to even carry sensitive attributes. So identical behaviour yields
identical advice regardless of who the customer is. These tests assert exactly
that.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from app.engines.advisory import advise
from app.engines.behavioral import compute_fingerprint
from app.schemas import PersonaFI

DATA = Path(__file__).resolve().parents[1] / "app" / "data" / "personas"


def _load(pid: str) -> dict:
    return json.loads((DATA / f"{pid}.json").read_text("utf-8"))


def _dump(recs) -> list[dict]:
    return [r.model_dump(mode="json") for r in recs]


@pytest.mark.parametrize("pid", ["young_spender", "idle_cash", "near_retiree"])
def test_holder_identity_is_not_an_advice_input(pid: str) -> None:
    fi = _load(pid)
    variant = copy.deepcopy(fi)
    variant["profile"]["holderName"] = "Anonymous Person"
    variant["profile"]["maskedPan"] = "XXXXX0000Z"

    fp1 = compute_fingerprint(fi)
    fp2 = compute_fingerprint(variant)
    # Name / PAN never enter the fingerprint …
    assert fp1.model_dump() == fp2.model_dump()
    # … and therefore never change the advice.
    assert _dump(advise(fp1)) == _dump(advise(fp2))


def test_persona_label_does_not_change_advice() -> None:
    fp = compute_fingerprint(_load("young_spender"))
    a = advise(fp.model_copy(update={"persona_id": "person_a"}))
    b = advise(fp.model_copy(update={"persona_id": "person_b"}))

    def norm(recs, who: str) -> list[dict]:
        out = []
        for r in recs:
            d = r.model_dump(mode="json")
            d["rec_id"] = d["rec_id"].replace(f"{who}:", "{id}:")
            out.append(d)
        return out

    # The only difference is the persona prefix on rec_id; strip it and the
    # strategy, amounts, allocation, math and claims are byte-identical.
    assert norm(a, "person_a") == norm(b, "person_b")


def test_sensitive_attributes_are_refused_by_the_schema() -> None:
    bad = copy.deepcopy(_load("young_spender"))
    bad["profile"]["gender"] = "female"  # a field we deliberately never collect
    with pytest.raises(Exception):
        PersonaFI.model_validate(bad)
