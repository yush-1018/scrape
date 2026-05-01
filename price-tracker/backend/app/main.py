"""
Price Tracker API — FastAPI Application Entry Point

A backend service that scrapes e-commerce product pages,
tracks price history, and serves data to the frontend dashboard.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.models.database import init_db
from app.routes.products import router as products_router
from app.routes.auth import router as auth_router
from app.routes.compare import router as compare_router

# ── Logging ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ───────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info("🔧 Initializing database...")
    init_db()
    logger.info("✅ Database ready")

    # Start the scheduler
    try:
        import sys
        import os
        # Add project root (price-tracker/) to path so scheduler can be imported
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(backend_dir)
        # Also ensure the backend dir is in path for app imports from scheduler
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from scheduler.cron import start_scheduler, stop_scheduler
        start_scheduler()
    except Exception as e:
        logger.warning(f"Scheduler not started: {e}")
        stop_scheduler = None

    yield

    # Shutdown
    if stop_scheduler:
        stop_scheduler()
    logger.info("👋 Application shutdown complete")


# ── FastAPI App ─────────────────────────────────────────────────────────

app = FastAPI(
    title="Price Tracker API",
    description="Track product prices across Amazon, Flipkart, Blinkit & Zepto",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow the frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(compare_router)


# ── Health check ────────────────────────────────────────────────────────

@app.get("/", tags=["health"])
def health_check():
    return {
        "status": "healthy",
        "service": "Price Tracker API",
        "version": "2.0.0",
    }


@app.get("/api/health", tags=["health"])
def api_health():
    return {"status": "ok"}
