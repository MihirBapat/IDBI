"""Step 5 gate: API integration (httpx AsyncClient over the ASGI app).

Covers the consent→chat happy path (claims-consistent narration), read-time
consent enforcement (chat before consent 403; revoke evicts + blocks), idempotent
execution intents, the audit/governance surface (narration_hash round-trip), the
ADVISORY_MODE=info_only kill-switch, and the PANIC no-exit guardrail.
"""

from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from app import main, store
from app.llm.validator import validate


def _run(scenario):
    asyncio.run(scenario())


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test")


@pytest.fixture(autouse=True)
def _fresh_db(tmp_path, monkeypatch):
    db = str(tmp_path / "test.sqlite")
    monkeypatch.setenv("DHANSAARTHI_DB", db)
    monkeypatch.delenv("ADVISORY_MODE", raising=False)
    monkeypatch.delenv("ENABLE_TTS", raising=False)
    store.init(db)
    yield


def test_consent_then_chat_happy_path():
    async def scenario():
        async with _client() as ac:
            c = await ac.post("/consent", json={"persona_id": "young_spender"})
            assert c.status_code == 200
            assert c.json()["consent"]["status"] == "active"

            r = await ac.post("/chat", json={"persona_id": "young_spender",
                                             "text": "what should I do with my money?"})
            assert r.status_code == 200
            body = r.json()
            assert body["intent"] == "ADVICE"
            assert body["recommendations"], "expected recommendations"
            # Narration is claim-consistent with the primary recommendation.
            primary = body["recommendations"][0]
            assert validate(body["spoken_text"], primary["numeric_claims"])
            assert body["narration_hash"]
    _run(scenario)


def test_chat_before_consent_is_403():
    async def scenario():
        async with _client() as ac:
            r = await ac.post("/chat", json={"persona_id": "idle_cash", "text": "advise me"})
            assert r.status_code == 403
    _run(scenario)


def test_unknown_persona_is_404():
    async def scenario():
        async with _client() as ac:
            r = await ac.post("/consent", json={"persona_id": "nobody"})
            assert r.status_code == 404
    _run(scenario)


def test_revoke_evicts_fingerprint_and_blocks_next_turn():
    async def scenario():
        async with _client() as ac:
            await ac.post("/consent", json={"persona_id": "disciplined_saver"})
            assert (await ac.post("/chat", json={"persona_id": "disciplined_saver",
                                                 "text": "advise"})).status_code == 200
            assert store.get_fingerprint("disciplined_saver") is not None

            d = await ac.delete("/consent", params={"persona_id": "disciplined_saver"})
            assert d.status_code == 200 and d.json()["revoked"] is True
            assert store.get_fingerprint("disciplined_saver") is None  # erased

            blocked = await ac.post("/chat", json={"persona_id": "disciplined_saver",
                                                   "text": "advise"})
            assert blocked.status_code == 403
    _run(scenario)


def test_duplicate_intent_is_idempotent():
    async def scenario():
        async with _client() as ac:
            await ac.post("/consent", json={"persona_id": "idle_cash"})
            body = {"persona_id": "idle_cash",
                    "recommendation_id": "idle_cash:markowitz_concentration",
                    "idempotency_key": "abc-123"}
            first = await ac.post("/intent", json=body)
            second = await ac.post("/intent", json=body)
            assert first.status_code == second.status_code == 200
            assert first.json()["deep_link"] == second.json()["deep_link"]
            assert first.json()["duplicate"] is False
            assert second.json()["duplicate"] is True
    _run(scenario)


def test_audit_narration_hash_round_trips():
    async def scenario():
        async with _client() as ac:
            await ac.post("/consent", json={"persona_id": "young_spender"})
            chat = await ac.post("/chat", json={"persona_id": "young_spender",
                                                "text": "help me invest"})
            nh = chat.json()["narration_hash"]

            audit = await ac.get("/audit", params={"persona_id": "young_spender"})
            rows = audit.json()["rows"]
            match = [r for r in rows if r["narration_hash"] == nh]
            assert match, "audit row with the chat narration_hash not found"
            row = match[0]
            assert row["strategy_id"] and row["shelf_sha"] and row["strategy_sha"]
            assert row["advisory_mode"] == "on"
    _run(scenario)


def test_info_only_mode_gives_no_recs_and_refuses_intent(monkeypatch):
    monkeypatch.setenv("ADVISORY_MODE", "info_only")
    store.init()  # re-read env (DB path + ADVISORY_MODE=info_only)
    assert store.ADVISORY_MODE == "info_only"

    async def scenario():
        async with _client() as ac:
            await ac.post("/consent", json={"persona_id": "young_spender"})
            chat = await ac.post("/chat", json={"persona_id": "young_spender",
                                                "text": "what should I do?"})
            assert chat.status_code == 200
            assert chat.json()["recommendations"] == []
            assert chat.json()["reasoning_trace"] is None

            intent = await ac.post("/intent", json={
                "persona_id": "young_spender",
                "recommendation_id": "x", "idempotency_key": "k1"})
            assert intent.status_code == 403
    _run(scenario)
    store.ADVISORY_MODE = "on"


def test_panic_returns_no_exit_path():
    async def scenario():
        async with _client() as ac:
            await ac.post("/consent", json={"persona_id": "near_retiree"})
            r = await ac.post("/chat", json={
                "persona_id": "near_retiree",
                "text": "the market is falling, should I sell everything and exit?"})
            body = r.json()
            assert body["intent"] == "PANIC"
            assert body["recommendations"] == []
            assert "idbi://" not in body["spoken_text"]  # never an exit deep-link
    _run(scenario)


def test_future_self_good_beats_bad():
    async def scenario():
        async with _client() as ac:
            await ac.post("/consent", json={"persona_id": "young_spender"})
            good = await ac.get("/future-self", params={"persona_id": "young_spender",
                                                        "branch": "good"})
            bad = await ac.get("/future-self", params={"persona_id": "young_spender",
                                                       "branch": "bad"})
            assert good.json()["take_advice"] is True
            assert good.json()["corpus_paise"] > bad.json()["corpus_paise"]
    _run(scenario)


def test_tts_offline_returns_503():
    async def scenario():
        async with _client() as ac:
            r = await ac.get("/tts", params={"text": "hello"})
            assert r.status_code == 503
    _run(scenario)
