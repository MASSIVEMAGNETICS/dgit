#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — DUPLICATION DETECTOR
# =============================================================================

from typing import List, Dict, Any

from backend.models.repo import RepoSummary


class DuplicationDetector:
    """Finds repositories with overlapping dependencies or similar code patterns."""

    def find_duplicate_deps(self, summaries: List[RepoSummary]) -> List[Dict[str, Any]]:
        """
        Return pairs of repos that share a significant number of dependencies.
        Each result dict has: repo_a, repo_b, shared_deps, overlap_ratio.
        """
        results: List[Dict[str, Any]] = []

        for i, a in enumerate(summaries):
            deps_a = set(d.lower() for d in a.metadata.dependencies)
            if not deps_a:
                continue

            for b in summaries[i + 1:]:
                deps_b = set(d.lower() for d in b.metadata.dependencies)
                if not deps_b:
                    continue

                shared = deps_a & deps_b
                if not shared:
                    continue

                union = deps_a | deps_b
                overlap_ratio = len(shared) / len(union)

                if overlap_ratio >= 0.3 or len(shared) >= 5:
                    results.append({
                        'repo_a': a.metadata.name,
                        'repo_b': b.metadata.name,
                        'shared_deps': sorted(shared),
                        'overlap_ratio': round(overlap_ratio, 3),
                    })

        results.sort(key=lambda x: x['overlap_ratio'], reverse=True)
        return results

    def find_similar_repos(self, summaries: List[RepoSummary]) -> List[Dict[str, Any]]:
        """
        Return pairs of repos that appear similar based on language, framework,
        and name tokens.  Each result dict has: repo_a, repo_b, reasons, score.
        """
        results: List[Dict[str, Any]] = []

        for i, a in enumerate(summaries):
            for b in summaries[i + 1:]:
                reasons = []
                score = 0.0

                # Same primary language
                if (a.metadata.primary_language and
                        a.metadata.primary_language == b.metadata.primary_language):
                    reasons.append(f"same language: {a.metadata.primary_language}")
                    score += 0.2

                # Same framework
                if a.metadata.framework and a.metadata.framework == b.metadata.framework:
                    reasons.append(f"same framework: {a.metadata.framework}")
                    score += 0.3

                # Overlapping name tokens
                tokens_a = set(a.metadata.name.lower().replace('-', '_').split('_'))
                tokens_b = set(b.metadata.name.lower().replace('-', '_').split('_'))
                common_tokens = tokens_a & tokens_b - {'', 'v2', 'v3', 'new', 'old'}
                if len(common_tokens) >= 2:
                    reasons.append(f"shared name tokens: {', '.join(sorted(common_tokens))}")
                    score += 0.3

                # High dependency overlap (reuse result from find_duplicate_deps)
                deps_a = set(d.lower() for d in a.metadata.dependencies)
                deps_b = set(d.lower() for d in b.metadata.dependencies)
                if deps_a and deps_b:
                    ratio = len(deps_a & deps_b) / len(deps_a | deps_b)
                    if ratio >= 0.5:
                        reasons.append(f"high dependency overlap: {ratio:.0%}")
                        score += 0.2

                if score >= 0.4:
                    results.append({
                        'repo_a': a.metadata.name,
                        'repo_b': b.metadata.name,
                        'reasons': reasons,
                        'score': round(score, 3),
                    })

        results.sort(key=lambda x: x['score'], reverse=True)
        return results
