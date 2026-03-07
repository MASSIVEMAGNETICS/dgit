#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — REPOS API ENDPOINTS
# =============================================================================

from fastapi import APIRouter, HTTPException

from backend.storage.database import Database

router = APIRouter(prefix="/api/repos", tags=["repos"])


@router.get("")
async def list_repos():
    """List all repositories stored in the database."""
    try:
        db = Database()
        summaries = db.list_repos()
        return {
            "repos": [
                {
                    "name": s.metadata.name,
                    "language": s.metadata.primary_language,
                    "framework": s.metadata.framework,
                    "status": s.metadata.status.value,
                    "purpose": s.metadata.likely_purpose,
                    "dependencies_count": len(s.metadata.dependencies),
                    "scan_timestamp": s.scan_timestamp.isoformat(),
                }
                for s in summaries
            ],
            "count": len(summaries),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{repo_name}")
async def get_repo(repo_name: str):
    """Get full details for a specific repository."""
    db = Database()
    summary = db.get_repo(repo_name)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Repo '{repo_name}' not found.")

    return {
        "name": summary.metadata.name,
        "description": summary.metadata.description,
        "visibility": summary.metadata.visibility,
        "language": summary.metadata.primary_language,
        "languages": summary.metadata.languages,
        "framework": summary.metadata.framework,
        "runtime": summary.metadata.runtime,
        "package_manager": summary.metadata.package_manager,
        "status": summary.metadata.status.value,
        "purpose": summary.metadata.likely_purpose,
        "dependencies": summary.metadata.dependencies,
        "entrypoints": summary.metadata.entrypoints,
        "api_routes": summary.metadata.api_routes,
        "config_files": summary.metadata.config_files,
        "test_files": summary.metadata.test_files,
        "todo_count": len(summary.metadata.todo_markers),
        "build_instructions": summary.metadata.build_instructions,
        "scan_timestamp": summary.scan_timestamp.isoformat(),
    }


@router.delete("/{repo_name}")
async def delete_repo(repo_name: str):
    """Remove a repository from the database."""
    db = Database()
    deleted = db.delete_repo(repo_name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Repo '{repo_name}' not found.")
    return {"status": "deleted", "name": repo_name}


@router.get("/{repo_name}/summary")
async def get_repo_summary(repo_name: str):
    """Get a markdown summary for a specific repository."""
    db = Database()
    summary = db.get_repo(repo_name)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Repo '{repo_name}' not found.")
    return {"name": repo_name, "markdown": summary.to_markdown()}
