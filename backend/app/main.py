"""DhanSaarthi FastAPI application entrypoint.

Phase 0 scaffold: exposes only a health probe. The advice-plane and narration
endpoints are added in Part 3. Per the graceful-degradation invariant, the
service reports ``mode: offline`` — Gemini/edge-tts are enhancements layered on
top of a baseline that runs with zero API keys and no internet.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="DhanSaarthi API",
    description="Avatar-based, AA-powered wealth advisory sidecar for IDBI Bank.",
    version="0.1.0",
)

# The frontend PWA runs on localhost:3000 during development. CORS is locked to
# that origin here; production locks it to the IDBI GO WebView origin instead.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe. ``mode`` reflects the baseline (LLM-independent) plane."""
    return {"status": "ok", "mode": "offline"}
