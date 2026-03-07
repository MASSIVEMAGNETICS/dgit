#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — SEMANTIC INDEXER
# =============================================================================

import re
import math
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional

import numpy as np

from backend.models.repo import RepoSummary
from backend.indexer.vector_store import VectorStore

# faiss is optional
try:
    import faiss  # noqa: F401
    _HAS_FAISS = True
except ImportError:
    _HAS_FAISS = False


class SemanticIndexer:
    """
    Manages TF-IDF-style semantic indexing of repository content.
    Uses numpy + VectorStore; faiss is optional and unused (fallback path).
    """

    def __init__(self):
        self._store = VectorStore()
        self._corpus: Dict[str, str] = {}   # repo_name -> text representation
        self._vocab: List[str] = []
        self._idf: np.ndarray = np.array([])
        self._dirty = True                  # vocab/idf needs rebuild

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def index_repo(self, repo_summary: RepoSummary) -> None:
        """Index a repository by converting its metadata to a TF-IDF vector."""
        text = self._summary_to_text(repo_summary)
        self._corpus[repo_summary.metadata.name] = text
        self._dirty = True
        self._rebuild_index()

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search indexed repos by semantic similarity.
        Returns list of {repo_name, score} dicts.
        """
        if not self._corpus:
            return []

        if self._dirty:
            self._rebuild_index()

        q_vec = self._vectorize(query)
        hits = self._store.search(q_vec, top_k=top_k)
        return [{'repo_name': key, 'score': round(score, 4)} for key, score in hits]

    def get_indexed_repos(self) -> List[str]:
        """Return names of all indexed repositories."""
        return list(self._corpus.keys())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _summary_to_text(summary: RepoSummary) -> str:
        parts = [
            summary.metadata.name,
            summary.metadata.description or '',
            summary.metadata.primary_language or '',
            summary.metadata.framework or '',
            summary.metadata.likely_purpose or '',
            ' '.join(summary.metadata.dependencies[:30]),
            ' '.join(summary.metadata.entrypoints),
        ]
        return ' '.join(p for p in parts if p)

    @staticmethod
    def _tokenise(text: str) -> List[str]:
        return re.findall(r'[a-zA-Z0-9]+', text.lower())

    def _rebuild_index(self) -> None:
        """Recompute vocabulary, IDF, and re-vectorize all documents."""
        if not self._corpus:
            return

        tokenised = {name: self._tokenise(text) for name, text in self._corpus.items()}
        # Build vocabulary
        all_tokens: Counter = Counter()
        for tokens in tokenised.values():
            all_tokens.update(set(tokens))
        self._vocab = [tok for tok, _ in all_tokens.most_common(2000)]
        vocab_index = {tok: i for i, tok in enumerate(self._vocab)}
        N = len(tokenised)

        # IDF
        idf = np.zeros(len(self._vocab), dtype=np.float32)
        for i, tok in enumerate(self._vocab):
            df = all_tokens[tok]
            idf[i] = math.log((N + 1) / (df + 1)) + 1.0
        self._idf = idf

        # Store TF-IDF vectors
        for name, tokens in tokenised.items():
            tf_vec = np.zeros(len(self._vocab), dtype=np.float32)
            token_counts = Counter(tokens)
            total = len(tokens) or 1
            for tok, cnt in token_counts.items():
                if tok in vocab_index:
                    tf_vec[vocab_index[tok]] = cnt / total
            tfidf = tf_vec * self._idf
            self._store.add(name, tfidf)

        self._dirty = False

    def _vectorize(self, text: str) -> np.ndarray:
        """Convert query text to a TF-IDF vector aligned with current vocab."""
        tokens = self._tokenise(text)
        vocab_index = {tok: i for i, tok in enumerate(self._vocab)}
        vec = np.zeros(len(self._vocab), dtype=np.float32)
        token_counts = Counter(tokens)
        total = len(tokens) or 1
        for tok, cnt in token_counts.items():
            if tok in vocab_index:
                vec[vocab_index[tok]] = cnt / total
        return vec * self._idf
