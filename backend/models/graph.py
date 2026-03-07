#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — GRAPH DATA MODELS
# =============================================================================

from pydantic import BaseModel, Field
from typing import List, Dict, Any


class GraphNode(BaseModel):
    """A node in the relationship graph."""
    id: str
    label: str
    type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """An edge in the relationship graph."""
    source: str
    target: str
    relationship: str
    weight: float = 1.0


class GraphData(BaseModel):
    """Complete graph data for the frontend."""
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
