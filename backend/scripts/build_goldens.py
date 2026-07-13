"""Regenerate golden advice fixtures for every synthetic persona.

Writes ``tests/golden/{persona}.json`` = the deterministic, suitability-screened
recommendation list (plus the fingerprint) for each persona. These are the CI
regression anchors: a change in an engine or a config YAML (which shifts a
pinned sha) becomes a reviewable golden diff, exactly as intended for
config-as-product (architecture §5, §11).

Run:  python backend/scripts/build_goldens.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/ on path

from app.engines.advisory import advise
from app.engines.behavioral import compute_fingerprint
from app.engines.suitability import screen
from scripts.generate_aa_data import _BUILDERS

# Single source of truth: every persona the generator knows about gets a golden.
PERSONAS = list(_BUILDERS.keys())
BACKEND = Path(__file__).resolve().parents[1]
PERSONA_DIR = BACKEND / "app" / "data" / "personas"
GOLDEN_DIR = BACKEND / "tests" / "golden"


def build_one(persona_id: str) -> dict:
    fi = json.loads((PERSONA_DIR / f"{persona_id}.json").read_text(encoding="utf-8"))
    fp = compute_fingerprint(fi)
    recs = screen(fp, advise(fp))
    return {
        "persona_id": persona_id,
        "fingerprint": fp.model_dump(mode="json"),
        "recommendations": [r.model_dump(mode="json") for r in recs],
    }


def main() -> None:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    for pid in PERSONAS:
        path = GOLDEN_DIR / f"{pid}.json"
        with path.open("w", encoding="utf-8") as fh:
            json.dump(build_one(pid), fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
