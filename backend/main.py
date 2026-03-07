#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — MAIN APPLICATION
# =============================================================================

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import config
from backend.api import scan, query, repos, graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup & shutdown."""
    # Ensure storage directories exist on startup
    config.create_directories()
    yield
    # Shutdown tasks (if any) go here


app = FastAPI(
    title="Victor Command Center",
    description="Cognitive repository intelligence dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount API routers
app.include_router(scan.router)
app.include_router(query.router)
app.include_router(repos.router)
app.include_router(graph.router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "Victor Command Center"}


# Serve frontend static files
_frontend_dir = Path(__file__).parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_frontend_dir)), name="static")

    @app.get("/")
    async def root():
        return FileResponse(str(_frontend_dir / "index.html"))
