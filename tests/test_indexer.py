#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — INDEXER TESTS
# =============================================================================

import pytest
import numpy as np
from pathlib import Path


# =============================================================================
# VectorStore
# =============================================================================

class TestVectorStore:
    def test_add_and_search(self):
        from backend.indexer.vector_store import VectorStore
        vs = VectorStore()
        v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        v2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        vs.add('a', v1)
        vs.add('b', v2)
        results = vs.search(v1, top_k=2)
        assert results[0][0] == 'a'
        assert results[0][1] > 0.9

    def test_search_empty_store(self):
        from backend.indexer.vector_store import VectorStore
        vs = VectorStore()
        results = vs.search(np.array([1.0, 0.0]), top_k=5)
        assert results == []

    def test_len(self):
        from backend.indexer.vector_store import VectorStore
        vs = VectorStore()
        assert len(vs) == 0
        vs.add('x', np.array([1.0, 2.0]))
        assert len(vs) == 1

    def test_update_existing_key(self):
        from backend.indexer.vector_store import VectorStore
        vs = VectorStore()
        vs.add('k', np.array([1.0, 0.0]))
        vs.add('k', np.array([0.0, 1.0]))
        assert len(vs) == 1  # no duplicate

    def test_save_and_load(self, tmp_path):
        from backend.indexer.vector_store import VectorStore
        vs = VectorStore()
        vs.add('repo1', np.array([1.0, 2.0, 3.0], dtype=np.float32))
        save_path = tmp_path / 'vs.json'
        vs.save(save_path)

        vs2 = VectorStore()
        vs2.load(save_path)
        assert len(vs2) == 1
        results = vs2.search(np.array([1.0, 2.0, 3.0], dtype=np.float32), top_k=1)
        assert results[0][0] == 'repo1'

    def test_load_nonexistent_is_noop(self, tmp_path):
        from backend.indexer.vector_store import VectorStore
        vs = VectorStore()
        vs.load(tmp_path / 'missing.json')  # should not raise
        assert len(vs) == 0

    def test_zero_vector_normalisation(self):
        from backend.indexer.vector_store import VectorStore
        vs = VectorStore()
        vs.add('zero', np.array([0.0, 0.0, 0.0]))
        # Should not crash
        results = vs.search(np.array([1.0, 0.0, 0.0]), top_k=1)
        assert len(results) == 1


# =============================================================================
# CodeParser
# =============================================================================

class TestCodeParser:
    def _write_py(self, tmp_path, content):
        f = tmp_path / 'sample.py'
        f.write_text(content)
        return f

    def test_parse_simple_file(self, tmp_path):
        from backend.indexer.code_parser import CodeParser
        code = """
import os
from pathlib import Path

class MyClass(object):
    def method_a(self, x):
        pass

def top_level_func(a, b):
    return a + b
"""
        fpath = self._write_py(tmp_path, code)
        parser = CodeParser()
        result = parser.parse_file(fpath)
        assert result['errors'] == []
        assert any(c['name'] == 'MyClass' for c in result['classes'])
        assert any(f['name'] == 'top_level_func' for f in result['functions'])
        assert any('os' in imp for imp in result['imports'])

    def test_parse_empty_file(self, tmp_path):
        from backend.indexer.code_parser import CodeParser
        fpath = self._write_py(tmp_path, '')
        result = CodeParser().parse_file(fpath)
        assert result['errors'] == []
        assert result['classes'] == []
        assert result['functions'] == []

    def test_parse_syntax_error(self, tmp_path):
        from backend.indexer.code_parser import CodeParser
        fpath = self._write_py(tmp_path, 'def broken(:')
        result = CodeParser().parse_file(fpath)
        assert len(result['errors']) >= 1

    def test_parse_async_function(self, tmp_path):
        from backend.indexer.code_parser import CodeParser
        code = "async def fetch(url: str): pass\n"
        fpath = self._write_py(tmp_path, code)
        result = CodeParser().parse_file(fpath)
        func = next((f for f in result['functions'] if f['name'] == 'fetch'), None)
        assert func is not None
        assert func['is_async'] is True

    def test_parse_nonexistent_file(self, tmp_path):
        from backend.indexer.code_parser import CodeParser
        result = CodeParser().parse_file(tmp_path / 'nope.py')
        assert len(result['errors']) >= 1

    def test_class_methods(self, tmp_path):
        from backend.indexer.code_parser import CodeParser
        code = """
class Service:
    def start(self): pass
    def stop(self): pass
"""
        fpath = self._write_py(tmp_path, code)
        result = CodeParser().parse_file(fpath)
        cls = result['classes'][0]
        assert len(cls['methods']) == 2


# =============================================================================
# SemanticIndexer
# =============================================================================

class TestSemanticIndexer:
    def _make_summary(self, name, lang='python', framework=None, deps=None, purpose=None):
        from backend.models.repo import RepoMetadata, RepoSummary
        meta = RepoMetadata(
            name=name,
            primary_language=lang,
            framework=framework,
            dependencies=deps or [],
            likely_purpose=purpose,
        )
        return RepoSummary(metadata=meta)

    def test_index_and_search(self):
        from backend.indexer.semantic_indexer import SemanticIndexer
        indexer = SemanticIndexer()
        indexer.index_repo(self._make_summary('fastapi-service', lang='python', framework='fastapi'))
        indexer.index_repo(self._make_summary('react-app', lang='javascript', framework='react'))
        results = indexer.search('python fastapi', top_k=2)
        assert len(results) >= 1
        assert results[0]['repo_name'] == 'fastapi-service'

    def test_get_indexed_repos(self):
        from backend.indexer.semantic_indexer import SemanticIndexer
        indexer = SemanticIndexer()
        indexer.index_repo(self._make_summary('alpha'))
        indexer.index_repo(self._make_summary('beta'))
        names = indexer.get_indexed_repos()
        assert 'alpha' in names
        assert 'beta' in names

    def test_search_empty_returns_empty(self):
        from backend.indexer.semantic_indexer import SemanticIndexer
        indexer = SemanticIndexer()
        results = indexer.search('anything', top_k=5)
        assert results == []
