#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — INTEGRATION PATHS
# =============================================================================

from typing import List, Dict, Any

from backend.models.repo import RepoSummary


class IntegrationPaths:
    """Finds integration opportunities between repositories."""

    # Pairs of (framework/language A, framework/language B) that integrate naturally
    _NATURAL_PAIRS = [
        ('fastapi', 'react'),
        ('fastapi', 'vue'),
        ('django', 'react'),
        ('django', 'vue'),
        ('flask', 'react'),
        ('express', 'react'),
        ('express', 'vue'),
        ('python', 'javascript'),
        ('python', 'typescript'),
    ]

    def find_paths(self, summaries: List[RepoSummary]) -> List[Dict[str, Any]]:
        """
        Return a list of suggested integration paths between repos.

        Each entry contains:
            repo_a          – source repo name
            repo_b          – target repo name
            integration_type – e.g. "api_client", "shared_library", "event_bus"
            rationale        – human-readable explanation
            confidence       – 0.0–1.0
        """
        paths: List[Dict[str, Any]] = []

        for i, a in enumerate(summaries):
            for b in summaries[i + 1:]:
                candidates = self._evaluate_pair(a, b)
                paths.extend(candidates)

        paths.sort(key=lambda x: x['confidence'], reverse=True)
        return paths

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evaluate_pair(
        self, a: RepoSummary, b: RepoSummary
    ) -> List[Dict[str, Any]]:
        results = []

        fw_a = (a.metadata.framework or '').lower()
        fw_b = (b.metadata.framework or '').lower()
        lang_a = (a.metadata.primary_language or '').lower()
        lang_b = (b.metadata.primary_language or '').lower()

        # Backend + Frontend pairing
        purpose_a = (a.metadata.likely_purpose or '').lower()
        purpose_b = (b.metadata.likely_purpose or '').lower()

        if 'backend' in purpose_a and 'frontend' in purpose_b:
            results.append(self._make_path(a.metadata.name, b.metadata.name,
                                           'api_client',
                                           'Backend API can be consumed by Frontend', 0.85))

        elif 'frontend' in purpose_a and 'backend' in purpose_b:
            results.append(self._make_path(b.metadata.name, a.metadata.name,
                                           'api_client',
                                           'Backend API can be consumed by Frontend', 0.85))

        # Natural framework pairs
        for pair in self._NATURAL_PAIRS:
            if (fw_a == pair[0] and fw_b == pair[1]) or (fw_a == pair[1] and fw_b == pair[0]):
                results.append(self._make_path(a.metadata.name, b.metadata.name,
                                               'natural_stack_pair',
                                               f"{pair[0]} + {pair[1]} form a natural full-stack", 0.75))
                break

        # Shared library / SDK opportunity
        if 'library' in purpose_a or 'library' in purpose_b:
            lib, consumer = (a, b) if 'library' in purpose_a else (b, a)
            if lang_a == lang_b:
                results.append(self._make_path(lib.metadata.name, consumer.metadata.name,
                                               'shared_library',
                                               f"{lib.metadata.name} could be a shared dependency", 0.65))

        # Duplicate → merge candidate
        deps_a = set(d.lower() for d in a.metadata.dependencies)
        deps_b = set(d.lower() for d in b.metadata.dependencies)
        if deps_a and deps_b and lang_a == lang_b:
            ratio = len(deps_a & deps_b) / len(deps_a | deps_b)
            if ratio >= 0.7:
                results.append(self._make_path(a.metadata.name, b.metadata.name,
                                               'merge_candidate',
                                               f"High dependency overlap ({ratio:.0%}); consider merging", 0.60))

        return results

    @staticmethod
    def _make_path(repo_a: str, repo_b: str, integration_type: str,
                   rationale: str, confidence: float) -> Dict[str, Any]:
        return {
            'repo_a': repo_a,
            'repo_b': repo_b,
            'integration_type': integration_type,
            'rationale': rationale,
            'confidence': confidence,
        }
