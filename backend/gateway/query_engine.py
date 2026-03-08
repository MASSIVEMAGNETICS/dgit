#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — QUERY ENGINE
# =============================================================================

from typing import List, Dict, Any

from backend.models.repo import RepoSummary
from backend.models.query import QueryRequest, QueryResponse
from backend.gateway.intent_router import IntentRouter
from backend.indexer.semantic_indexer import SemanticIndexer


class QueryEngine:
    """
    Processes natural-language queries about repositories.
    Uses keyword-based intent detection and TF-IDF semantic search;
    Ollama/LLM is optional and not required.
    """

    def __init__(self):
        self._router = IntentRouter()
        self._indexer = SemanticIndexer()

    def index_summaries(self, summaries: List[RepoSummary]) -> None:
        """Pre-index all repo summaries for semantic search."""
        for summary in summaries:
            self._indexer.index_repo(summary)

    def query(self, text: str, repo_summaries: List[RepoSummary]) -> QueryResponse:
        """
        Process a natural-language query and return a structured response.

        Steps:
            1. Detect intent
            2. Use semantic indexer to find candidate repos
            3. Route to action layer
            4. Build QueryResponse
        """
        # Ensure summaries are indexed
        indexed = set(self._indexer.get_indexed_repos())
        for s in repo_summaries:
            if s.metadata.name not in indexed:
                self._indexer.index_repo(s)

        intent = self._router.detect_intent(text)

        # Semantic search for candidate repos
        semantic_hits = self._indexer.search(text, top_k=10)
        candidate_names = {h['repo_name'] for h in semantic_hits}

        # Prefer semantically relevant summaries but always pass all
        context: Dict[str, Any] = {
            'repo_summaries': repo_summaries,
            'semantic_candidates': list(candidate_names),
        }

        action_result = self._router.route(intent, text, context)

        # Build summary string
        summary = self._build_summary(intent, action_result, repo_summaries)

        results: list = []
        if 'repos' in action_result:
            results = action_result['repos']
        elif 'results' in action_result:
            results = action_result['results']
        elif 'repo' in action_result:
            results = [action_result['repo']]
        elif 'graph' in action_result:
            results = [action_result['graph']]
        elif 'suggestions' in action_result:
            results = [{'suggestion': s} for s in action_result['suggestions']]
        elif 'repo_a' in action_result and 'repo_b' in action_result:
            results = [action_result]

        return QueryResponse(
            query=text,
            intent=intent,
            results=results,
            summary=summary,
        )

    # ------------------------------------------------------------------

    @staticmethod
    def _build_summary(intent: str, result: Dict[str, Any], summaries: List[RepoSummary]) -> str:
        count = len(summaries)
        if intent == 'show':
            if 'count' in result:
                return f"Showing {result['count']} repositories out of {count} total."
            if 'repo' in result:
                name = result.get('target', 'repo')
                return f"Details for repository '{name}'."
        elif intent == 'find':
            return f"Found {result.get('count', 0)} matching repositories."
        elif intent == 'map':
            nodes = len(result.get('graph', {}).get('nodes', []))
            edges = len(result.get('graph', {}).get('edges', []))
            return f"Relationship graph: {nodes} nodes, {edges} edges."
        elif intent == 'compare':
            a = result.get('repo_a', {}).get('name', '?') if isinstance(result.get('repo_a'), dict) else '?'
            b = result.get('repo_b', {}).get('name', '?') if isinstance(result.get('repo_b'), dict) else '?'
            return f"Comparison between '{a}' and '{b}'."
        elif intent == 'plan':
            n = len(result.get('suggestions', []))
            return f"Generated {n} planning suggestions for {count} repositories."
        return f"Query processed. {count} repos in context."
