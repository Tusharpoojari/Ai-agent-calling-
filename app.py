"""
Campus++ AI Voice Calling Backend
==================================
Production-ready FastAPI backend that integrates with Twilio
to provide AI-powered voice academic insights for students.

Run with:
    uvicorn app:app --reload --port 8000
"""

import logging
from fastapi import FastAPI
from routes.call import router as call_router

# ── Logging Setup ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("campus++")

# ── FastAPI App ────────────────────────────────────────────────
app = FastAPI(
    title="Campus++ AI Voice Calling Backend",
    description=(
        "An AI-powered phone call assistant that lets students "
        "call a number and receive personalized academic performance "
        "insights via voice — even without a smartphone."
    ),
    version="1.0.0",
)

# ── Register Routes ───────────────────────────────────────────
app.include_router(call_router, prefix="/api/call", tags=["Voice Call"])


# ── Health Check ──────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def health_check():
    """Simple health-check endpoint."""
    return {
        "status": "ok",
        "service": "Campus++ AI Voice Backend",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"healthy": True}


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting Campus++ AI Voice Backend on port 8000")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
