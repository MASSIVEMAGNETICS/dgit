#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — QUERY API ENDPOINTS
# =============================================================================

from fastapi import APIRouter, HTTPException

from backend.models.query import QueryRequest, QueryResponse
from backend.gateway.query_engine import QueryEngine
from backend.storage.database import Database

router = APIRouter(prefix="/api/query", tags=["query"])

_engine = QueryEngine()


@router.post("", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a natural-language query about the repos."""
    try:
        db = Database()
        summaries = db.list_repos()
        _engine.index_summaries(summaries)
        response = _engine.query(request.query, summaries)
        db.save_query(request, response)
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/history")
async def query_history(limit: int = 50):
    """Return recent query history."""
    try:
        db = Database()
        return {"history": db.get_query_history(limit=limit)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
