#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — RELATIONSHIP GRAPH
# =============================================================================

from typing import List, Dict, Any, Optional

try:
    import networkx as nx
    _HAS_NX = True
except ImportError:
    _HAS_NX = False

from backend.models.repo import RepoSummary, RepoRelationship
from backend.models.graph import GraphData, GraphNode, GraphEdge


class RelationshipGraph:
    """Builds and queries a graph of relationships between repositories."""

    def __init__(self):
        self._graph = nx.DiGraph() if _HAS_NX else None
        # Fallback plain-dict adjacency when networkx is absent
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def add_repo(self, repo_summary: RepoSummary) -> None:
        """Add a repository node (and its declared relationships) to the graph."""
        name = repo_summary.metadata.name
        attrs = {
            'language': repo_summary.metadata.primary_language or 'unknown',
            'framework': repo_summary.metadata.framework or 'unknown',
            'status': repo_summary.metadata.status.value,
            'purpose': repo_summary.metadata.likely_purpose or '',
            'dependencies': repo_summary.metadata.dependencies,
        }
        self._nodes[name] = attrs
        if _HAS_NX:
            self._graph.add_node(name, **attrs)

        for rel in repo_summary.relationships:
            self._add_edge(rel.source_repo, rel.target_repo, rel.relationship_type, rel.confidence)

    def _add_edge(self, source: str, target: str, rel_type: str, weight: float = 1.0) -> None:
        edge = {'source': source, 'target': target, 'relationship': rel_type, 'weight': weight}
        # Deduplicate
        for existing in self._edges:
            if existing['source'] == source and existing['target'] == target and existing['relationship'] == rel_type:
                return
        self._edges.append(edge)
        if _HAS_NX:
            self._graph.add_edge(source, target, relationship=rel_type, weight=weight)

    def build_from_summaries(self, summaries: List[RepoSummary]) -> None:
        """Populate graph from a list of RepoSummary objects."""
        for summary in summaries:
            self.add_repo(summary)

        # Auto-detect dependency edges from metadata
        dep_index: Dict[str, str] = {}
        for summary in summaries:
            for dep in summary.metadata.dependencies:
                dep_lower = dep.lower()
                dep_index[dep_lower] = summary.metadata.name

        for summary in summaries:
            for dep in summary.metadata.dependencies:
                target = dep_index.get(dep.lower())
                if target and target != summary.metadata.name:
                    self._add_edge(summary.metadata.name, target, 'dependency', 0.9)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def find_dependencies(self, repo_name: str) -> List[str]:
        """Return repos that *repo_name* depends on."""
        if _HAS_NX and repo_name in self._graph:
            return [t for _, t, d in self._graph.out_edges(repo_name, data=True)
                    if d.get('relationship') == 'dependency']
        return [e['target'] for e in self._edges
                if e['source'] == repo_name and e['relationship'] == 'dependency']

    def find_related(self, repo_name: str) -> List[str]:
        """Return all repos connected to *repo_name* (any direction, any type)."""
        if _HAS_NX and repo_name in self._graph:
            neighbors = set(self._graph.successors(repo_name))
            neighbors.update(self._graph.predecessors(repo_name))
            neighbors.discard(repo_name)
            return list(neighbors)
        related = set()
        for e in self._edges:
            if e['source'] == repo_name:
                related.add(e['target'])
            elif e['target'] == repo_name:
                related.add(e['source'])
        related.discard(repo_name)
        return list(related)

    def get_graph_data(self) -> Dict[str, Any]:
        """Return serialisable graph dict with nodes and edges lists."""
        nodes = [
            {'id': name, 'label': name, 'type': 'repo', 'metadata': attrs}
            for name, attrs in self._nodes.items()
        ]
        edges = list(self._edges)
        return {'nodes': nodes, 'edges': edges}

    def to_graph_data(self) -> GraphData:
        """Return a GraphData pydantic model."""
        raw = self.get_graph_data()
        return GraphData(
            nodes=[GraphNode(**n) for n in raw['nodes']],
            edges=[GraphEdge(**e) for e in raw['edges']],
        )
