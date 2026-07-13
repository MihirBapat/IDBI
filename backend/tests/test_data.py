"""Part 1 gate: the synthetic personas parse and reconcile.

Two guarantees:
  1. every persona file validates against the ``PersonaFI`` pydantic model
     (schema is the ReBIT contract we'll swap for IDBI's sandbox);
  2. the ledger reconciles exactly — final balance == opening + credits - debits,
     every running balance is consistent, and each MF's currentValue equals
     round(units * nav). Integer paise, no float drift.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.schemas import PersonaFI
from scripts.generate_aa_data import _BUILDERS, generate_all

PERSONA_IDS = list(_BUILDERS.keys())
DATA_DIR = Path(__file__).resolve().parents[1] / "app" / "data" / "personas"


@pytest.fixture(scope="session", autouse=True)
def _ensure_generated() -> None:
    """Regenerate the persona files once before the suite runs."""
    generate_all()


def _load(persona_id: str) -> dict:
    with (DATA_DIR / f"{persona_id}.json").open(encoding="utf-8") as fh:
        return json.load(fh)


def test_all_personas_present() -> None:
    assert len(PERSONA_IDS) == 15
    for pid in PERSONA_IDS:
        assert (DATA_DIR / f"{pid}.json").exists(), f"missing {pid}.json"


@pytest.mark.parametrize("persona_id", PERSONA_IDS)
def test_persona_validates(persona_id: str) -> None:
    doc = _load(persona_id)
    model = PersonaFI.model_validate(doc)
    assert model.persona_id == persona_id
    assert model.deposit.transactions, "deposit block has no transactions"
    # 12 months of history: at least the 12 salary credits are present.
    salary = [t for t in model.deposit.transactions if t.category_code == "SALARY"]
    assert len(salary) == 12


@pytest.mark.parametrize("persona_id", PERSONA_IDS)
def test_ledger_reconciles(persona_id: str) -> None:
    dep = _load(persona_id)["deposit"]
    txns = dep["transactions"]
    credits = sum(t["amount"] for t in txns if t["type"] == "CREDIT")
    debits = sum(t["amount"] for t in txns if t["type"] == "DEBIT")

    # Final balance equals opening + credits - debits.
    assert dep["currentBalance"] == dep["openingBalance"] + credits - debits

    # Every running balance is internally consistent.
    bal = dep["openingBalance"]
    for t in txns:
        bal += t["amount"] if t["type"] == "CREDIT" else -t["amount"]
        assert t["currentBalance"] == bal, f"running balance mismatch at {t['txnId']}"

    # All amounts are positive integer paise.
    for t in txns:
        assert isinstance(t["amount"], int) and t["amount"] > 0

    # Balances stay non-negative throughout (realistic account, no overdraft).
    assert dep["openingBalance"] >= 0
    for t in txns:
        assert t["currentBalance"] >= 0, f"negative balance at {t['txnId']}"


@pytest.mark.parametrize("persona_id", PERSONA_IDS)
def test_mutual_funds_value_consistent(persona_id: str) -> None:
    for mf in _load(persona_id).get("mutualFunds", []):
        assert mf["currentValue"] == round(mf["units"] * mf["nav"])
        assert isinstance(mf["nav"], int) and isinstance(mf["currentValue"], int)


def test_expected_persona_shapes() -> None:
    """Spot-check the behavioral signatures the engines will key off of."""
    young = PersonaFI.model_validate(_load("young_spender"))
    assert young.profile.age == 27
    assert young.mutual_funds == []  # no SIP / thin
    assert any(t.category_code == "FOOD_DELIVERY" for t in young.deposit.transactions)

    saver = PersonaFI.model_validate(_load("disciplined_saver"))
    assert any(mf.sip_flag for mf in saver.mutual_funds)
    assert len([t for t in saver.deposit.transactions
                if t.category_code == "SIP_DEBIT"]) == 12

    near = PersonaFI.model_validate(_load("near_retiree"))
    assert near.profile.age == 54
    assert len(near.term_deposits) == 3
    assert near.mutual_funds == []  # no equity glide

    over = PersonaFI.model_validate(_load("over_insured"))
    assert len([t for t in over.deposit.transactions
                if t.category_code == "INSURANCE_PREMIUM"]) == 4


def test_injection_narration_quarantined_at_ingest() -> None:
    """The prompt-injection canary exists in raw narrations (it must be caught
    at ingest and never reach an LLM). Here we assert it is present in the data
    so later parts can prove the quarantine strips it."""
    found = False
    for pid in PERSONA_IDS:
        for t in _load(pid)["deposit"]["transactions"]:
            if "ignore-all-previous-instructions" in t["narration"]:
                found = True
    assert found, "expected an injection-flavoured narration in the synthetic data"
