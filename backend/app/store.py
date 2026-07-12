"""store.py — prototype data & session state (SQLite + fingerprint cache).

The prototype's DATA PLANE (architecture §4): an append-only-ish consent ledger,
an advice audit store, an idempotent intent log, and an in-process fingerprint
cache. SQLite here maps 1:1 to RDS Postgres in production; the fingerprint cache
maps to Redis. Consent is checked at **read time** on every turn, and revocation
evicts the fingerprint (DPDP erasure).

Money stays integer paise. No engine math lives here — the store orchestrates
ingest (compute_fingerprint) and persistence only.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from app.engines.behavioral import compute_fingerprint
from app.schemas import Fingerprint

_PERSONA_DIR = Path(__file__).resolve().parent / "data" / "personas"

CONSENT_PURPOSE = "102"          # AA purpose code: wealth management
CONSENT_FI_TYPES = ["DEPOSIT", "TERM_DEPOSIT", "RECURRING_DEPOSIT", "MUTUAL_FUNDS"]
CONSENT_DAYS = 365

_conn: Optional[sqlite3.Connection] = None
_fp_cache: dict[str, Fingerprint] = {}
ADVISORY_MODE = "on"             # "on" | "info_only" (governance kill-switch)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def init(db_path: Optional[str] = None) -> None:
    """(Re)initialise the store. Called on app startup and by tests with a temp DB."""
    global _conn, ADVISORY_MODE
    path = db_path or os.environ.get("DHANSAARTHI_DB", "dhansaarthi.sqlite")
    _conn = sqlite3.connect(path, check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    ADVISORY_MODE = os.environ.get("ADVISORY_MODE", "on")
    _conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            persona_id TEXT PRIMARY KEY, holder_name TEXT, age INTEGER, created_at TEXT);
        CREATE TABLE IF NOT EXISTS consents (
            id INTEGER PRIMARY KEY AUTOINCREMENT, persona_id TEXT, purpose TEXT,
            fi_types TEXT, status TEXT, granted_at TEXT, expiry TEXT, revoked_at TEXT);
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, persona_id TEXT, started_at TEXT);
        CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT, persona_id TEXT, ts TEXT, intent TEXT,
            strategy_id TEXT, engine_ver TEXT, shelf_sha TEXT, strategy_sha TEXT,
            narration_hash TEXT, suitability_outcome TEXT, advisory_mode TEXT);
        CREATE TABLE IF NOT EXISTS intents (
            idempotency_key TEXT PRIMARY KEY, persona_id TEXT, recommendation_id TEXT,
            deep_link TEXT, created_at TEXT);
        """
    )
    _conn.commit()
    _fp_cache.clear()


def _db() -> sqlite3.Connection:
    if _conn is None:
        init()
    assert _conn is not None
    return _conn


# --------------------------------------------------------------------------- #
# Ingest / consent
# --------------------------------------------------------------------------- #

def load_fi(persona_id: str) -> Optional[dict]:
    path = _PERSONA_DIR / f"{persona_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def grant_consent(persona_id: str) -> Optional[dict]:
    """Simulated AA grant: record consent, ingest FI, cache the fingerprint."""
    fi = load_fi(persona_id)
    if fi is None:
        return None
    db = _db()
    prof = fi["profile"]
    db.execute(
        "INSERT OR REPLACE INTO users(persona_id, holder_name, age, created_at) "
        "VALUES (?,?,?,?)",
        (persona_id, prof["holderName"], prof["age"], _now().isoformat()))
    # Supersede any prior live consent, then grant fresh.
    db.execute("UPDATE consents SET status='revoked', revoked_at=? "
               "WHERE persona_id=? AND status='active'", (_now().isoformat(), persona_id))
    expiry = (_now() + timedelta(days=CONSENT_DAYS)).isoformat()
    db.execute(
        "INSERT INTO consents(persona_id, purpose, fi_types, status, granted_at, expiry, "
        "revoked_at) VALUES (?,?,?,?,?,?,NULL)",
        (persona_id, CONSENT_PURPOSE, ",".join(CONSENT_FI_TYPES), "active",
         _now().isoformat(), expiry))
    db.commit()
    _fp_cache[persona_id] = compute_fingerprint(fi)
    return {
        "persona_id": persona_id, "holder_name": prof["holderName"],
        "purpose": CONSENT_PURPOSE, "fi_types": CONSENT_FI_TYPES,
        "status": "active", "expiry": expiry,
    }


def revoke_consent(persona_id: str) -> bool:
    """Revoke consent and evict the fingerprint (DPDP erasure)."""
    db = _db()
    cur = db.execute("UPDATE consents SET status='revoked', revoked_at=? "
                     "WHERE persona_id=? AND status='active'",
                     (_now().isoformat(), persona_id))
    db.commit()
    _fp_cache.pop(persona_id, None)
    return cur.rowcount > 0


def consent_live(persona_id: str) -> bool:
    """Read-time consent check: active, un-revoked, unexpired."""
    row = _db().execute(
        "SELECT expiry FROM consents WHERE persona_id=? AND status='active' "
        "AND revoked_at IS NULL ORDER BY id DESC LIMIT 1", (persona_id,)).fetchone()
    if row is None:
        return False
    return datetime.fromisoformat(row["expiry"]) > _now()


def get_fingerprint(persona_id: str) -> Optional[Fingerprint]:
    return _fp_cache.get(persona_id)


# --------------------------------------------------------------------------- #
# Audit / intents
# --------------------------------------------------------------------------- #

def narration_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_audit(persona_id: str, intent: str, *, strategy_id: Optional[str],
                engine_ver: Optional[str], shelf_sha: Optional[str],
                strategy_sha: Optional[str], narration_hash: str,
                suitability_outcome: Optional[str]) -> None:
    db = _db()
    db.execute(
        "INSERT INTO audit(persona_id, ts, intent, strategy_id, engine_ver, shelf_sha, "
        "strategy_sha, narration_hash, suitability_outcome, advisory_mode) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (persona_id, _now().isoformat(), intent, strategy_id, engine_ver, shelf_sha,
         strategy_sha, narration_hash, suitability_outcome, ADVISORY_MODE))
    db.commit()


def get_audit(persona_id: str) -> list[dict]:
    rows = _db().execute("SELECT * FROM audit WHERE persona_id=? ORDER BY id",
                         (persona_id,)).fetchall()
    return [dict(r) for r in rows]


def log_intent(idempotency_key: str, persona_id: str, recommendation_id: str,
               deep_link: str) -> tuple[dict, bool]:
    """Idempotent intent log: a repeated key returns the original deep-link."""
    db = _db()
    existing = db.execute("SELECT * FROM intents WHERE idempotency_key=?",
                          (idempotency_key,)).fetchone()
    if existing is not None:
        return {"deep_link": existing["deep_link"],
                "recommendation_id": existing["recommendation_id"],
                "idempotency_key": idempotency_key}, True
    db.execute("INSERT INTO intents(idempotency_key, persona_id, recommendation_id, "
               "deep_link, created_at) VALUES (?,?,?,?,?)",
               (idempotency_key, persona_id, recommendation_id, deep_link,
                _now().isoformat()))
    db.commit()
    return {"deep_link": deep_link, "recommendation_id": recommendation_id,
            "idempotency_key": idempotency_key}, False
