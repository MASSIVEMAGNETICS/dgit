#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — SCAN API ENDPOINTS
# =============================================================================

from pathlib import Path
from typing import List
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.scanner.repo_scanner import RepoScanner
from backend.storage.database import Database

router = APIRouter(prefix="/api/scan", tags=["scan"])

# Simple in-memory scan status tracker
_scan_status = {
    "last_scan": None,
    "repos_scanned": 0,
    "in_progress": False,
}


class LocalScanRequest(BaseModel):
    paths: List[str]


class GithubScanRequest(BaseModel):
    org: str = ""
    token: str = ""


@router.post("/local")
async def scan_local(request: LocalScanRequest):
    """Scan local directories and persist results."""
    global _scan_status
    _scan_status["in_progress"] = True
    try:
        scanner = RepoScanner()
        db = Database()
        paths = [Path(p) for p in request.paths]
        summaries = scanner.scan_local_repos(paths)

        for summary in summaries:
            db.save_repo(summary)

        _scan_status["last_scan"] = datetime.now(timezone.utc).isoformat()
        _scan_status["repos_scanned"] = len(summaries)
        _scan_status["in_progress"] = False

        return {
            "status": "ok",
            "repos_scanned": len(summaries),
            "repos": [s.metadata.name for s in summaries],
        }
    except Exception as exc:
        _scan_status["in_progress"] = False
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/github")
async def scan_github(request: GithubScanRequest):
    """Scan GitHub organisation repositories (requires token)."""
    from backend.config import config
    import requests as http_requests

    token = request.token or config.github_token
    org = request.org or config.github_org

    if not token:
        raise HTTPException(status_code=400, detail="GitHub token required.")
    if not org:
        raise HTTPException(status_code=400, detail="GitHub organisation required.")

    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/orgs/{org}/repos?per_page=100"

    try:
        response = http_requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        repos_data = response.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"GitHub API error: {exc}")

    from backend.models.repo import RepoMetadata, RepoSummary, RepoStatus
    from datetime import datetime, timezone

    db = Database()
    saved = []
    for repo in repos_data:
        metadata = RepoMetadata(
            name=repo.get("name", ""),
            description=repo.get("description"),
            visibility=repo.get("visibility", "private"),
            primary_language=repo.get("language"),
            status=RepoStatus.ACTIVE if not repo.get("archived") else RepoStatus.ARCHIVED,
        )
        summary = RepoSummary(metadata=metadata)
        db.save_repo(summary)
        saved.append(metadata.name)

    return {"status": "ok", "repos_scanned": len(saved), "repos": saved}


@router.get("/status")
async def scan_status():
    """Return current scan status."""
    return _scan_status
