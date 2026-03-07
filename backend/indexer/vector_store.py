#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — VECTOR STORE
# =============================================================================

import json
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import numpy as np


class VectorStore:
    """
    Simple in-memory vector store backed by numpy cosine-similarity search.
    Optionally persists to/loads from a JSON file.
    Does NOT require faiss.
    """

    def __init__(self):
        self._keys: List[str] = []
        self._vectors: List[np.ndarray] = []

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def add(self, key: str, vector: np.ndarray) -> None:
        """Insert or update a vector for *key*."""
        vector = self._normalise(vector)
        if key in self._keys:
            idx = self._keys.index(key)
            self._vectors[idx] = vector
        else:
            self._keys.append(key)
            self._vectors.append(vector)

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """Return the top-k (key, score) pairs ranked by cosine similarity."""
        if not self._keys:
            return []

        q = self._normalise(query_vector)
        matrix = np.stack(self._vectors)          # (N, D)
        scores = matrix @ q                        # cosine sim (vectors are normalised)
        top_indices = np.argsort(scores)[::-1][:top_k]

        return [(self._keys[i], float(scores[i])) for i in top_indices]

    def save(self, path: Path) -> None:
        """Persist the store to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            'keys': self._keys,
            'vectors': [v.tolist() for v in self._vectors],
        }
        path.write_text(json.dumps(data), encoding='utf-8')

    def load(self, path: Path) -> None:
        """Load vectors from a previously saved JSON file."""
        path = Path(path)
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding='utf-8'))
        self._keys = data.get('keys', [])
        self._vectors = [np.array(v, dtype=np.float32) for v in data.get('vectors', [])]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(vector: np.ndarray) -> np.ndarray:
        v = np.array(vector, dtype=np.float32)
        norm = np.linalg.norm(v)
        if norm == 0:
            return v
        return v / norm

    def __len__(self) -> int:
        return len(self._keys)
