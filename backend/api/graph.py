#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — GRAPH API ENDPOINTS
# =============================================================================

from fastapi import APIRouter, HTTPException

from backend.mapper.relationship_graph import RelationshipGraph
from backend.storage.database import Database

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("")
async def get_graph():
    """Return the full repository relationship graph."""
    try:
        db = Database()
        summaries = db.list_repos()
        graph = RelationshipGraph()
        graph.build_from_summaries(summaries)
        return graph.get_graph_data()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{repo_name}/neighbors")
async def get_neighbors(repo_name: str):
    """Return repos directly connected to *repo_name* in the graph."""
    db = Database()
    summaries = db.list_repos()

    names = {s.metadata.name for s in summaries}
    if repo_name not in names:
        raise HTTPException(status_code=404, detail=f"Repo '{repo_name}' not found.")

    graph = RelationshipGraph()
    graph.build_from_summaries(summaries)
    related = graph.find_related(repo_name)
    deps = graph.find_dependencies(repo_name)

    return {
        "repo": repo_name,
        "related": related,
        "dependencies": deps,
    }
