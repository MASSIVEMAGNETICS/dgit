#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — INTENT ROUTER
# =============================================================================

import re
from typing import Dict, Any, List, Optional

from backend.models.repo import RepoSummary


# Intent keyword patterns (order matters — first match wins)
_INTENT_PATTERNS: List[tuple] = [
    ('compare', re.compile(r'\b(compare|diff|difference|versus|vs\.?)\b', re.I)),
    ('map',     re.compile(r'\b(map|graph|relationship|connect|network|depend)\b', re.I)),
    ('find',    re.compile(r'\b(find|search|locate|where|which|look for|any)\b', re.I)),
    ('plan',    re.compile(r'\b(plan|todo|roadmap|next.?step|improve|fix|prioriti)', re.I)),
    ('show',    re.compile(r'\b(show|display|list|tell me about|what is|describe|detail)\b', re.I)),
]

_DEFAULT_INTENT = 'show'


class IntentRouter:
    """Routes natural-language queries to the appropriate handler."""

    def detect_intent(self, query_text: str) -> str:
        """Return the intent label for *query_text*."""
        for intent, pattern in _INTENT_PATTERNS:
            if pattern.search(query_text):
                return intent
        return _DEFAULT_INTENT

    def route(self, intent: str, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch *query* to the correct handler based on *intent*.

        *context* should contain:
            repo_summaries: List[RepoSummary]   (optional)
            target: str                          (optional repo name)
        """
        from backend.gateway.action_layer import ActionLayer
        layer = ActionLayer()
        summaries: List[RepoSummary] = context.get('repo_summaries', [])

        if intent == 'show':
            target = self._extract_target(query, summaries)
            return layer.show(target, context)

        elif intent == 'find':
            return layer.find(query, context)

        elif intent == 'map':
            return layer.map_repos(context)

        elif intent == 'compare':
            repo_a, repo_b = self._extract_pair(query, summaries)
            return layer.compare(repo_a, repo_b, context)

        elif intent == 'plan':
            return layer.plan(query, context)

        return layer.show(None, context)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_target(query: str, summaries: List[RepoSummary]) -> Optional[str]:
        """Try to find a repo name mentioned in the query."""
        q_lower = query.lower()
        for s in summaries:
            if s.metadata.name.lower() in q_lower:
                return s.metadata.name
        return None

    @staticmethod
    def _extract_pair(query: str, summaries: List[RepoSummary]) -> tuple:
        """Return up to two repo names mentioned in the query."""
        q_lower = query.lower()
        found = []
        for s in summaries:
            if s.metadata.name.lower() in q_lower:
                found.append(s.metadata.name)
            if len(found) == 2:
                break
        while len(found) < 2:
            found.append(None)
        return found[0], found[1]
