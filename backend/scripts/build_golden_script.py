"""Pre-cache the golden-path narration to app/data/golden_script.yaml.

The scripted 2-minute demo runs on the deterministic template narrator, so the
exact spoken lines are known ahead of time. Caching them means the stage demo
can fall back to canned text even if templates are tweaked at the last minute —
"the demo cannot die" (PRD §3). Deterministic: regenerating is byte-identical.

Run:  python backend/scripts/build_golden_script.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/ on path

os.environ["DHANSAARTHI_DB"] = ":memory:"
# Force offline/template mode: empty (but present) so the lifespan .env loader
# (override=False) won't re-enable Gemini, keeping this script deterministic.
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("ENABLE_TTS", None)

from starlette.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

_OUT = Path(__file__).resolve().parents[1] / "app" / "data" / "golden_script.yaml"
PERSONA = "young_spender"


def _body(text: str) -> str:
    return text.split("\n\n")[0].strip()


def build() -> dict:
    with TestClient(app) as c:
        c.post("/consent", json={"persona_id": PERSONA})
        turns = []
        for intent, prompt in [
            ("GREET", "hello"),
            ("ADVICE", "what should I do with my money?"),
            ("WHY", "why this advice?"),
            ("PANIC", "the market is crashing, should I sell everything?"),
        ]:
            r = c.post("/chat", json={"persona_id": PERSONA, "text": prompt}).json()
            turns.append({"intent": r["intent"], "prompt": prompt,
                          "text": _body(r["spoken_text"])})
        disclosure = c.post(
            "/chat", json={"persona_id": PERSONA, "text": "advise me"}
        ).json()["disclosure"]
        future = {}
        for branch in ("good", "bad"):
            script = c.get("/future-self",
                           params={"persona_id": PERSONA, "branch": branch}).json()
            future[branch] = [ln["text"] for ln in script["lines"]]
    return {
        "persona": PERSONA,
        "note": "Deterministic template-mode narration for the scripted demo. "
                "Regenerate with scripts/build_golden_script.py.",
        "disclosure": disclosure,
        "turns": turns,
        "future_self": future,
    }


if __name__ == "__main__":
    data = build()
    with _OUT.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False, width=100)
    print(f"wrote {_OUT}")
