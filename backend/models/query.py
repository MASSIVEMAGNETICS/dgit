#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — QUERY DATA MODELS
# =============================================================================

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone


class QueryRequest(BaseModel):
    """Incoming query request."""
    query: str
    context: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    """Query response returned to caller."""
    query: str
    intent: str
    results: List[Dict[str, Any]] = Field(default_factory=list)
    summary: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
