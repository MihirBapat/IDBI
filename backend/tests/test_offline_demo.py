"""The scripted golden path, end-to-end and fully offline.

Drives the exact 2-minute demo flow through the HTTP API (template mode, no LLM,
no TTS) and asserts the determinism boundary holds at every step: every numeral
the avatar speaks is a member of the engine's NumericClaimSet. This is the demo
that "cannot die" — if it is green, the stage demo runs with zero API keys and
no internet.
"""

from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from app import main, store
from app.llm.validator import validate

PID = "young_spender"


def _run(scenario):
    asyncio.run(scenario())


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test")


@pytest.fixture(autouse=True)
def _fresh_db(tmp_path, monkeypatch):
    db = str(tmp_path / "demo.sqlite")
    monkeypatch.setenv("DHANSAARTHI_DB", db)
    monkeypatch.delenv("ADVISORY_MODE", raising=False)
    monkeypatch.delenv("ENABLE_TTS", raising=False)
    store.init(db)
    yield


def test_scripted_golden_path_every_spoken_number_is_claimed():
    async def scenario():
        async with _client() as ac:
            # Consent (simulated AA grant).
            assert (await ac.post("/consent", json={"persona_id": PID})).status_code == 200

            # Four chat turns: greet, advice, why, panic.
            greet = (await ac.post("/chat", json={"persona_id": PID, "text": "hello"})).json()
            advice = (
                await ac.post("/chat", json={"persona_id": PID,
                                             "text": "what should I do with my money?"})
            ).json()
            why = (await ac.post("/chat", json={"persona_id": PID, "text": "why this advice?"})).json()
            panic = (
                await ac.post("/chat", json={"persona_id": PID,
                                             "text": "the market is crashing, should I sell everything?"})
            ).json()

            # The advice turn carries recommendations; its narration is claim-safe.
            assert advice["intent"] == "ADVICE" and advice["recommendations"]
            claims = advice["recommendations"][0]["numeric_claims"]
            assert validate(advice["spoken_text"], claims)
            assert validate(why["spoken_text"], claims)

            # Greet and panic carry no figures; panic never offers an exit path.
            assert validate(greet["spoken_text"], [])
            assert validate(panic["spoken_text"], [])
            assert panic["intent"] == "PANIC"
            assert "idbi://" not in panic["spoken_text"]

            # Future Self — both branches; every line's numerals are engine-claimed.
            good = (await ac.get("/future-self", params={"persona_id": PID, "branch": "good"})).json()
            bad = (await ac.get("/future-self", params={"persona_id": PID, "branch": "bad"})).json()
            for script in (good, bad):
                for line in script["lines"]:
                    assert validate(line["text"], line["numeric_claims"]), line["text"]
            assert good["corpus_paise"] > bad["corpus_paise"]

            # Execution intent — idempotent deep-link.
            rec_id = advice["recommendations"][0]["rec_id"]
            i1 = (await ac.post("/intent", json={"persona_id": PID, "recommendation_id": rec_id,
                                                 "idempotency_key": "demo-1"})).json()
            i2 = (await ac.post("/intent", json={"persona_id": PID, "recommendation_id": rec_id,
                                                 "idempotency_key": "demo-1"})).json()
            assert i1["deep_link"] == i2["deep_link"] and i2["duplicate"] is True

            # Governance surface recorded the advice turn with pinned versions.
            audit = (await ac.get("/audit", params={"persona_id": PID})).json()["rows"]
            adv_rows = [r for r in audit if r["intent"] == "ADVICE"]
            assert adv_rows and adv_rows[0]["shelf_sha"] and adv_rows[0]["strategy_sha"]

    _run(scenario)
