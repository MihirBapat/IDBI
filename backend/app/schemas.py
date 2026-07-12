"""Pydantic models — the typed contracts of DhanSaarthi.

Two families live here:

1. **FI-JSON** — the ReBIT-style Account Aggregator payload our synthetic
   generator emits and the ingest path validates. Field names mirror the AA
   wire schema (camelCase) via aliases, so swapping the synthetic generator for
   IDBI's sandbox is one adapter, not a rewrite (architecture §11).

2. **Engine contracts** — ``Fingerprint``, ``Recommendation``, ``ReasoningTrace``
   produced by the deterministic engines (Part 2) and consumed by the narrator.

INVARIANT: every monetary quantity is an **integer number of paise**. No floats
touch money. NAV is stored as paise-per-unit; unit counts are dimensionless
fractions (not currency) and may be float. ₹/lakh/crore formatting happens only
in the engine, never here and never in the LLM.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Generic, Literal, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field


# Accept AA-wire camelCase aliases while exposing snake_case attributes.
_AA = ConfigDict(populate_by_name=True, extra="forbid")


# --------------------------------------------------------------------------- #
# FI-JSON — Account Aggregator ReBIT-style payload
# --------------------------------------------------------------------------- #

TxnType = Literal["CREDIT", "DEBIT"]


class Transaction(BaseModel):
    """A single deposit-account ledger entry.

    ``category_code`` is a closed-vocabulary code assigned at ingest. The raw
    ``narration`` (an attacker-controlled UPI/merchant string) is retained for
    the ledger but is quarantined — only ``category_code`` may reach an LLM
    prompt (determinism-boundary / prompt-injection defence).
    """

    model_config = _AA

    txn_id: str = Field(alias="txnId")
    type: TxnType
    amount: int = Field(description="Transaction amount in paise (always > 0).")
    narration: str
    value_date: date = Field(alias="valueDate")
    current_balance: int = Field(
        alias="currentBalance", description="Running account balance in paise."
    )
    mode: Optional[str] = None
    category_code: Optional[str] = Field(default=None, alias="categoryCode")


class DepositBlock(BaseModel):
    """Savings/current deposit account: opening balance + 12 months of txns."""

    model_config = _AA

    masked_acc_number: str = Field(alias="maskedAccNumber")
    opening_balance: int = Field(
        alias="openingBalance", description="Balance before the first txn, in paise."
    )
    current_balance: int = Field(
        alias="currentBalance", description="Latest balance in paise."
    )
    transactions: list[Transaction]


class TermDeposit(BaseModel):
    """A fixed / recurring deposit holding."""

    model_config = _AA

    masked_acc_number: str = Field(alias="maskedAccNumber")
    principal: int = Field(description="Deposited principal in paise.")
    interest_rate: float = Field(alias="interestRate", description="Annual % p.a.")
    tenure_months: int = Field(alias="tenureMonths")
    start_date: date = Field(alias="startDate")
    maturity_date: date = Field(alias="maturityDate")
    maturity_amount: int = Field(
        alias="maturityAmount", description="Value at maturity in paise."
    )


class SipHistoryEntry(BaseModel):
    """One executed SIP installment."""

    model_config = _AA

    date: date
    amount: int = Field(description="Installment amount in paise.")


class MutualFund(BaseModel):
    """A mutual-fund folio holding.

    ``nav`` is paise-per-unit (integer) to keep money off floats; ``units`` is a
    dimensionless fractional count. ``current_value`` should equal
    round(units * nav) and is validated on reconciliation.
    """

    model_config = _AA

    scheme: str
    folio: str
    units: float
    nav: int = Field(description="Net asset value in paise per unit.")
    cost_value: int = Field(alias="costValue", description="Invested amount in paise.")
    current_value: int = Field(
        alias="currentValue", description="Current market value in paise."
    )
    sip_flag: bool = Field(alias="sipFlag")
    sip_history: list[SipHistoryEntry] = Field(
        default_factory=list, alias="sipHistory"
    )


class Profile(BaseModel):
    """FIP-declared account holder profile."""

    model_config = _AA

    masked_acc_number: str = Field(alias="maskedAccNumber")
    holder_name: str = Field(alias="holderName")
    age: int
    masked_pan: Optional[str] = Field(default=None, alias="maskedPan")


class PersonaFI(BaseModel):
    """Top-level synthetic FI-JSON document for one persona."""

    model_config = _AA

    persona_id: str = Field(alias="personaId")
    generated_at: datetime = Field(alias="generatedAt")
    schema_version: str = Field(default="rebit-1.0", alias="schemaVersion")
    profile: Profile
    deposit: DepositBlock
    term_deposits: list[TermDeposit] = Field(default_factory=list, alias="termDeposits")
    mutual_funds: list[MutualFund] = Field(default_factory=list, alias="mutualFunds")


# --------------------------------------------------------------------------- #
# Engine contracts — Fingerprint / Recommendation / ReasoningTrace
# --------------------------------------------------------------------------- #


T = TypeVar("T")

RiskCapacity = Literal["LOW", "MEDIUM", "HIGH"]
Verdict = Literal["PASS", "SOFTEN", "VETO"]


class Metric(BaseModel, Generic[T]):
    """A fingerprint field wrapped with freshness metadata.

    ``as_of`` dates the underlying data; ``confidence`` (0..1) drops when AA
    data is partial or stale so the narrator can hedge honestly rather than
    silently imputing.
    """

    value: T
    as_of: datetime
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class SpendLeak(BaseModel):
    """A recurring discretionary spend cluster, keyed by closed-vocab category."""

    category_code: str
    monthly_amount: int = Field(description="Average monthly spend in paise.")
    txn_count: int


class Fingerprint(BaseModel):
    """Behavioral Financial Fingerprint — output of ``engines/behavioral.py``.

    Computed deterministically from FI-JSON. Every field is a ``Metric`` so it
    travels with its own ``as_of``/``confidence`` staleness metadata.
    """

    persona_id: str
    age: int
    monthly_income: Metric[int]
    savings_ratio: Metric[float]
    spend_leaks: Metric[list[SpendLeak]]
    sip_discipline: Metric[float]
    idle_cash: Metric[int]
    equity_holding: Metric[int]
    insurance_gap: Metric[int]
    risk_capacity: Metric[RiskCapacity]


class ReasoningTrace(BaseModel):
    """Per-recommendation audit record — the 'Why this advice?' payload.

    Pins the versions that produced the number so a turn is bit-for-bit
    replayable (SEBI 5-year record test). ``refusal_reason`` is populated by the
    suitability gate when a recommendation is softened or vetoed.
    """

    strategy_id: str
    source_principle: str
    inputs_used: dict = Field(default_factory=dict)
    math_steps: list[str] = Field(
        default_factory=list, description="Ordered human-readable calc steps."
    )
    engine_ver: str
    shelf_sha: str
    strategy_sha: str
    refusal_reason: Optional[str] = None


class Recommendation(BaseModel):
    """A single deterministic recommendation + its NumericClaimSet.

    ``numeric_claims`` is the whitelist of pre-formatted numerals the narrator
    is permitted to speak; the output validator rejects any numeral outside it.
    ``status`` is set by the suitability gate — only PASS/SOFTEN reach narration.
    """

    rec_id: str
    action: str
    product_ref: Optional[str] = None
    amount_paise: Optional[int] = None
    allocation: dict[str, float] = Field(default_factory=dict)
    strategy_id: str
    title: str = ""
    numeric_claims: list[str] = Field(default_factory=list)
    reasoning_trace: ReasoningTrace
    status: Verdict = "PASS"


class ProjectionLine(BaseModel):
    """One first-person line spoken by the aged 'Future Self' avatar."""

    text: str
    numeric_claims: list[str] = Field(default_factory=list)


class ProjectionScript(BaseModel):
    """Deterministic 30-year Future Self narration (good or bad branch)."""

    persona_id: str
    take_advice: bool
    horizon_years: int
    corpus_paise: int
    lines: list[ProjectionLine] = Field(default_factory=list)
    numeric_claims: list[str] = Field(default_factory=list)
    reasoning_trace: ReasoningTrace
