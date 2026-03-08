#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — MAPPER TESTS
# =============================================================================

import pytest
from backend.models.repo import RepoMetadata, RepoSummary, RepoStatus


def _make_summary(name, language='python', framework=None, deps=None, status=RepoStatus.ACTIVE):
    meta = RepoMetadata(
        name=name,
        primary_language=language,
        framework=framework,
        dependencies=deps or [],
        status=status,
    )
    return RepoSummary(metadata=meta)


# =============================================================================
# RelationshipGraph
# =============================================================================

class TestRelationshipGraph:
    def test_add_repo_creates_node(self):
        from backend.mapper.relationship_graph import RelationshipGraph
        g = RelationshipGraph()
        s = _make_summary('repo-a')
        g.add_repo(s)
        data = g.get_graph_data()
        assert any(n['id'] == 'repo-a' for n in data['nodes'])

    def test_build_from_summaries(self):
        from backend.mapper.relationship_graph import RelationshipGraph
        summaries = [_make_summary('a'), _make_summary('b'), _make_summary('c')]
        g = RelationshipGraph()
        g.build_from_summaries(summaries)
        data = g.get_graph_data()
        assert len(data['nodes']) == 3

    def test_find_related_returns_list(self):
        from backend.mapper.relationship_graph import RelationshipGraph
        from backend.models.repo import RepoRelationship
        s_a = _make_summary('alpha')
        s_b = _make_summary('beta')
        s_a.relationships.append(RepoRelationship(
            source_repo='alpha', target_repo='beta',
            relationship_type='dependency', confidence=0.9
        ))
        g = RelationshipGraph()
        g.add_repo(s_a)
        g.add_repo(s_b)
        related = g.find_related('alpha')
        assert 'beta' in related

    def test_find_dependencies(self):
        from backend.mapper.relationship_graph import RelationshipGraph
        from backend.models.repo import RepoRelationship
        s_a = _make_summary('serviceA')
        s_b = _make_summary('libB')
        s_a.relationships.append(RepoRelationship(
            source_repo='serviceA', target_repo='libB',
            relationship_type='dependency', confidence=1.0
        ))
        g = RelationshipGraph()
        g.add_repo(s_a)
        g.add_repo(s_b)
        deps = g.find_dependencies('serviceA')
        assert 'libB' in deps

    def test_get_graph_data_structure(self):
        from backend.mapper.relationship_graph import RelationshipGraph
        g = RelationshipGraph()
        g.add_repo(_make_summary('x'))
        data = g.get_graph_data()
        assert 'nodes' in data
        assert 'edges' in data
        assert isinstance(data['nodes'], list)
        assert isinstance(data['edges'], list)

    def test_to_graph_data_model(self):
        from backend.mapper.relationship_graph import RelationshipGraph
        from backend.models.graph import GraphData
        g = RelationshipGraph()
        g.add_repo(_make_summary('m'))
        gd = g.to_graph_data()
        assert isinstance(gd, GraphData)


# =============================================================================
# DuplicationDetector
# =============================================================================

class TestDuplicationDetector:
    def test_no_duplicates_empty(self):
        from backend.mapper.duplication_detector import DuplicationDetector
        dd = DuplicationDetector()
        result = dd.find_duplicate_deps([])
        assert result == []

    def test_finds_high_overlap(self):
        from backend.mapper.duplication_detector import DuplicationDetector
        deps = ['fastapi', 'uvicorn', 'numpy', 'pydantic', 'httpx', 'requests']
        a = _make_summary('repoA', deps=deps)
        b = _make_summary('repoB', deps=deps)
        dd = DuplicationDetector()
        result = dd.find_duplicate_deps([a, b])
        assert len(result) >= 1
        assert result[0]['overlap_ratio'] > 0.5

    def test_no_overlap_different_deps(self):
        from backend.mapper.duplication_detector import DuplicationDetector
        a = _make_summary('repoA', deps=['fastapi', 'uvicorn'])
        b = _make_summary('repoB', deps=['rails', 'rack'])
        dd = DuplicationDetector()
        result = dd.find_duplicate_deps([a, b])
        assert result == []

    def test_find_similar_repos_same_framework(self):
        from backend.mapper.duplication_detector import DuplicationDetector
        a = _make_summary('frontend-alpha', language='javascript', framework='react')
        b = _make_summary('frontend-beta',  language='javascript', framework='react')
        dd = DuplicationDetector()
        result = dd.find_similar_repos([a, b])
        assert len(result) >= 1
        assert any(any('react' in reason for reason in r['reasons']) for r in result)

    def test_find_similar_repos_empty(self):
        from backend.mapper.duplication_detector import DuplicationDetector
        dd = DuplicationDetector()
        result = dd.find_similar_repos([])
        assert result == []


# =============================================================================
# IntegrationPaths
# =============================================================================

class TestIntegrationPaths:
    def test_finds_backend_frontend_path(self):
        from backend.mapper.integration_paths import IntegrationPaths
        back = _make_summary('my-backend-api', language='python', framework='fastapi')
        back.metadata.likely_purpose = 'Backend API Service'
        front = _make_summary('my-frontend-ui', language='javascript', framework='react')
        front.metadata.likely_purpose = 'Frontend Application'

        ip = IntegrationPaths()
        paths = ip.find_paths([back, front])
        assert len(paths) >= 1
        assert any(p['integration_type'] in ('api_client', 'natural_stack_pair') for p in paths)

    def test_empty_returns_empty(self):
        from backend.mapper.integration_paths import IntegrationPaths
        ip = IntegrationPaths()
        assert ip.find_paths([]) == []
