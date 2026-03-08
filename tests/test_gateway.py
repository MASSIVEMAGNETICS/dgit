#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — GATEWAY TESTS
# =============================================================================

import pytest
from backend.models.repo import RepoMetadata, RepoSummary, RepoStatus


def _make_summary(name, language='python', framework=None, deps=None,
                  purpose=None, status=RepoStatus.ACTIVE):
    meta = RepoMetadata(
        name=name,
        primary_language=language,
        framework=framework,
        dependencies=deps or [],
        likely_purpose=purpose,
        status=status,
    )
    return RepoSummary(metadata=meta)


# =============================================================================
# IntentRouter
# =============================================================================

class TestIntentRouter:
    @pytest.fixture(autouse=True)
    def router(self):
        from backend.gateway.intent_router import IntentRouter
        self.router = IntentRouter()

    def test_detect_show(self):
        assert self.router.detect_intent('show me all repos') == 'show'
        assert self.router.detect_intent('list repositories') == 'show'
        assert self.router.detect_intent('what is the backend service') == 'show'

    def test_detect_find(self):
        assert self.router.detect_intent('find all python repos') == 'find'
        assert self.router.detect_intent('search for react projects') == 'find'
        assert self.router.detect_intent('which repos use fastapi') == 'find'

    def test_detect_map(self):
        assert self.router.detect_intent('map the dependencies') == 'map'
        assert self.router.detect_intent('show relationship graph') == 'map'
        assert self.router.detect_intent('graph all connections') == 'map'

    def test_detect_compare(self):
        assert self.router.detect_intent('compare repoA and repoB') == 'compare'
        assert self.router.detect_intent('what is the difference between X and Y') == 'compare'

    def test_detect_plan(self):
        assert self.router.detect_intent('plan the next steps') == 'plan'
        assert self.router.detect_intent('what should I fix first') == 'plan'
        assert self.router.detect_intent('prioritize issues') == 'plan'

    def test_default_intent(self):
        # Unrecognised query falls back to 'show'
        assert self.router.detect_intent('zxqy abcdef') == 'show'

    def test_route_show_returns_dict(self):
        summaries = [_make_summary('alpha'), _make_summary('beta')]
        result = self.router.route('show', 'show all repos', {'repo_summaries': summaries})
        assert isinstance(result, dict)
        assert result.get('action') == 'show'

    def test_route_find_returns_dict(self):
        summaries = [_make_summary('python-service', language='python')]
        result = self.router.route('find', 'find python repos', {'repo_summaries': summaries})
        assert isinstance(result, dict)
        assert 'results' in result

    def test_route_map_returns_graph(self):
        summaries = [_make_summary('a'), _make_summary('b')]
        result = self.router.route('map', 'map repos', {'repo_summaries': summaries})
        assert 'graph' in result

    def test_route_plan_returns_suggestions(self):
        summaries = [_make_summary('broken-svc', status=RepoStatus.BROKEN)]
        result = self.router.route('plan', 'plan what to fix', {'repo_summaries': summaries})
        assert 'suggestions' in result


# =============================================================================
# ActionLayer
# =============================================================================

class TestActionLayer:
    @pytest.fixture(autouse=True)
    def layer(self):
        from backend.gateway.action_layer import ActionLayer
        self.layer = ActionLayer()

    def _ctx(self, summaries):
        return {'repo_summaries': summaries}

    def test_show_all(self):
        summaries = [_make_summary('x'), _make_summary('y')]
        result = self.layer.show(None, self._ctx(summaries))
        assert result['action'] == 'show'
        assert result['count'] == 2

    def test_show_specific(self):
        summaries = [_make_summary('my-service')]
        result = self.layer.show('my-service', self._ctx(summaries))
        assert result['action'] == 'show'
        assert result['target'] == 'my-service'
        assert 'repo' in result

    def test_show_not_found(self):
        result = self.layer.show('ghost', self._ctx([]))
        assert 'error' in result

    def test_find_by_keyword(self):
        summaries = [
            _make_summary('api-server', language='python', purpose='Backend API Service'),
            _make_summary('ui-client',  language='javascript', purpose='Frontend Application'),
        ]
        result = self.layer.find('python backend', self._ctx(summaries))
        assert result['action'] == 'find'
        names = [r['name'] for r in result['results']]
        assert 'api-server' in names

    def test_map_repos(self):
        summaries = [_make_summary('a'), _make_summary('b')]
        result = self.layer.map_repos(self._ctx(summaries))
        assert result['action'] == 'map'
        assert 'graph' in result

    def test_compare_two_repos(self):
        a = _make_summary('serviceA', language='python', framework='fastapi', deps=['fastapi', 'pydantic'])
        b = _make_summary('serviceB', language='python', framework='django',  deps=['django', 'pydantic'])
        result = self.layer.compare('serviceA', 'serviceB', self._ctx([a, b]))
        assert result['action'] == 'compare'
        assert 'pydantic' in result['shared_dependencies']

    def test_compare_missing_repo(self):
        summaries = [_make_summary('alpha')]
        result = self.layer.compare('alpha', 'ghost', self._ctx(summaries))
        assert 'error' in result

    def test_plan_with_broken_repos(self):
        summaries = [
            _make_summary('broken-svc', status=RepoStatus.BROKEN),
            _make_summary('ok-svc',     status=RepoStatus.ACTIVE),
        ]
        result = self.layer.plan('fix everything', self._ctx(summaries))
        assert result['action'] == 'plan'
        assert len(result['suggestions']) >= 1
        assert any('broken-svc' in s for s in result['suggestions'])

    def test_plan_empty_repos(self):
        result = self.layer.plan('what now', self._ctx([]))
        assert result['action'] == 'plan'


# =============================================================================
# QueryEngine
# =============================================================================

class TestQueryEngine:
    def test_query_returns_response(self):
        from backend.gateway.query_engine import QueryEngine
        engine = QueryEngine()
        summaries = [_make_summary('alpha', language='python')]
        response = engine.query('show all repos', summaries)
        assert response.query == 'show all repos'
        assert response.intent in ('show', 'find', 'map', 'compare', 'plan')
        assert isinstance(response.results, list)
        assert isinstance(response.summary, str)

    def test_query_empty_repos(self):
        from backend.gateway.query_engine import QueryEngine
        engine = QueryEngine()
        response = engine.query('list repos', [])
        assert response.intent is not None
