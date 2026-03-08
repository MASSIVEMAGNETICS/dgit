#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — ACTION LAYER
# =============================================================================

from typing import List, Dict, Any, Optional

from backend.models.repo import RepoSummary


class ActionLayer:
    """Implements concrete actions triggered by the intent router."""

    # ------------------------------------------------------------------
    # Public actions
    # ------------------------------------------------------------------

    def show(self, target: Optional[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Show details about a specific repo, or list all repos."""
        summaries: List[RepoSummary] = context.get('repo_summaries', [])

        if target:
            matched = [s for s in summaries if s.metadata.name.lower() == target.lower()]
            if matched:
                s = matched[0]
                return {
                    'action': 'show',
                    'target': target,
                    'repo': self._summary_dict(s),
                    'markdown': s.to_markdown(),
                }
            return {'action': 'show', 'target': target, 'error': f"Repo '{target}' not found."}

        # List all
        return {
            'action': 'show',
            'repos': [self._brief(s) for s in summaries],
            'count': len(summaries),
        }

    def find(self, criteria: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Find repos matching a keyword criteria."""
        summaries: List[RepoSummary] = context.get('repo_summaries', [])
        criteria_lower = criteria.lower()
        matched = []

        for s in summaries:
            text = ' '.join([
                s.metadata.name,
                s.metadata.description or '',
                s.metadata.primary_language or '',
                s.metadata.framework or '',
                s.metadata.likely_purpose or '',
                ' '.join(s.metadata.dependencies[:20]),
            ]).lower()
            if any(token in text for token in criteria_lower.split() if len(token) > 2):
                matched.append(self._brief(s))

        return {
            'action': 'find',
            'criteria': criteria,
            'results': matched,
            'count': len(matched),
        }

    def map_repos(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build and return the relationship graph data."""
        from backend.mapper.relationship_graph import RelationshipGraph
        summaries: List[RepoSummary] = context.get('repo_summaries', [])
        graph = RelationshipGraph()
        graph.build_from_summaries(summaries)
        return {
            'action': 'map',
            'graph': graph.get_graph_data(),
        }

    def compare(
        self,
        repo_a: Optional[str],
        repo_b: Optional[str],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compare two repositories side-by-side."""
        summaries: List[RepoSummary] = context.get('repo_summaries', [])
        index = {s.metadata.name.lower(): s for s in summaries}

        a = index.get((repo_a or '').lower())
        b = index.get((repo_b or '').lower())

        if not a or not b:
            missing = []
            if not a:
                missing.append(repo_a or '<unspecified>')
            if not b:
                missing.append(repo_b or '<unspecified>')
            return {'action': 'compare', 'error': f"Could not find repos: {', '.join(missing)}"}

        shared_deps = set(a.metadata.dependencies) & set(b.metadata.dependencies)

        return {
            'action': 'compare',
            'repo_a': self._summary_dict(a),
            'repo_b': self._summary_dict(b),
            'shared_dependencies': sorted(shared_deps),
            'differences': {
                'language': {
                    'a': a.metadata.primary_language,
                    'b': b.metadata.primary_language,
                },
                'framework': {
                    'a': a.metadata.framework,
                    'b': b.metadata.framework,
                },
                'status': {
                    'a': a.metadata.status.value,
                    'b': b.metadata.status.value,
                },
            },
        }

    def plan(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a simple action plan based on current repo state."""
        summaries: List[RepoSummary] = context.get('repo_summaries', [])
        suggestions: List[str] = []

        broken = [s.metadata.name for s in summaries if s.metadata.status.value == 'broken']
        if broken:
            suggestions.append(f"Fix broken repos: {', '.join(broken)}")

        high_todos = [s.metadata.name for s in summaries if len(s.metadata.todo_markers) > 10]
        if high_todos:
            suggestions.append(f"Address TODOs in: {', '.join(high_todos)}")

        no_tests = [s.metadata.name for s in summaries if not s.metadata.test_files]
        if no_tests:
            suggestions.append(f"Add tests to: {', '.join(no_tests[:5])}")

        from backend.mapper.duplication_detector import DuplicationDetector
        duplicates = DuplicationDetector().find_duplicate_deps(summaries)
        if duplicates:
            pair = duplicates[0]
            suggestions.append(
                f"Consider consolidating {pair['repo_a']} and {pair['repo_b']} "
                f"(shared deps: {len(pair['shared_deps'])})"
            )

        return {
            'action': 'plan',
            'goal': goal,
            'suggestions': suggestions,
            'repo_count': len(summaries),
        }

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _brief(s: RepoSummary) -> Dict[str, Any]:
        return {
            'name': s.metadata.name,
            'language': s.metadata.primary_language,
            'framework': s.metadata.framework,
            'status': s.metadata.status.value,
            'purpose': s.metadata.likely_purpose,
        }

    @staticmethod
    def _summary_dict(s: RepoSummary) -> Dict[str, Any]:
        return {
            'name': s.metadata.name,
            'description': s.metadata.description,
            'language': s.metadata.primary_language,
            'languages': s.metadata.languages,
            'framework': s.metadata.framework,
            'runtime': s.metadata.runtime,
            'package_manager': s.metadata.package_manager,
            'status': s.metadata.status.value,
            'purpose': s.metadata.likely_purpose,
            'dependencies_count': len(s.metadata.dependencies),
            'dependencies': s.metadata.dependencies[:20],
            'entrypoints': s.metadata.entrypoints,
            'api_routes': s.metadata.api_routes,
            'config_files': s.metadata.config_files,
            'test_files': s.metadata.test_files,
            'todo_count': len(s.metadata.todo_markers),
        }
