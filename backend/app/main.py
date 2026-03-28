import html
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import API_TITLE, API_VERSION
from app.core.database import get_recent_logs, get_stats, init_db
from app.core.loader import get_models_info
from app.routes import analyze

# ── Logging ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-24s  %(levelname)-7s  %(message)s",
)

_ROOT_META = {
    "service": "TrustVault AI",
    "version": API_VERSION,
    "docs": "/docs",
    "health": "/health",
    "analyze": "POST /analyze",
    "audit": "GET /audit",
    "stats": "GET /stats",
    "models": "GET /models/info",
}

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


# ── Lifecycle ───────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logging.getLogger("trustvault").info("Database initialized")
    yield


app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)


# ── Root ────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False, response_class=HTMLResponse)
def root():
    pretty = json.dumps(_ROOT_META, indent=2, ensure_ascii=False)
    tpl = (_TEMPLATE_DIR / "root.html").read_text(encoding="utf-8")
    page = tpl.replace("{{ version }}", html.escape(API_VERSION)).replace(
        "{{ json_pretty }}", html.escape(pretty)
    )
    return HTMLResponse(content=page)


@app.get("/info", include_in_schema=True)
def root_metadata():
    """Service metadata and available endpoints."""
    return _ROOT_META


# ── Health ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "healthy", "version": API_VERSION, "message": "TrustVault AI is running"}


# ── Audit ───────────────────────────────────────────────────────────────

@app.get("/audit", tags=["observability"])
def audit_log(limit: int = 50):
    """Return the most recent audit log entries."""
    return {"entries": get_recent_logs(limit=min(limit, 200))}


# ── Stats ───────────────────────────────────────────────────────────────

@app.get("/stats", tags=["observability"])
def stats():
    """Aggregated risk statistics across all audited requests."""
    return get_stats()


# ── Model info ──────────────────────────────────────────────────────────

@app.get("/models/info", tags=["observability"])
def models_info():
    """Metadata for every loaded ML model (training date, scores, params)."""
    return {"models": get_models_info()}


# ── Entrypoint ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "5000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
