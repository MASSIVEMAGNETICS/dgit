#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — STRUCTURE ANALYZER
# =============================================================================

import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime


class StructureAnalyzer:
    """Analyzes the structural properties of a repository."""

    _SKIP_DIRS = frozenset([
        'node_modules', '__pycache__', 'venv', 'env', '.git',
        'build', 'dist', '.mypy_cache', '.tox', '.eggs',
    ])

    def analyze_depth(self, path: Path) -> Dict[str, Any]:
        """Return depth statistics of the directory tree."""
        max_depth = 0
        depth_counts: Dict[int, int] = {}

        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in self._SKIP_DIRS and not d.startswith('.')]
            rel = Path(root).relative_to(path)
            depth = len(rel.parts)
            max_depth = max(max_depth, depth)
            depth_counts[depth] = depth_counts.get(depth, 0) + len(files)

        return {
            'max_depth': max_depth,
            'files_per_depth': depth_counts,
        }

    def get_file_types(self, path: Path) -> Dict[str, int]:
        """Return a mapping of file extension -> count."""
        counts: Dict[str, int] = {}

        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in self._SKIP_DIRS and not d.startswith('.')]
            for fname in files:
                ext = Path(fname).suffix.lower() or '(no ext)'
                counts[ext] = counts.get(ext, 0) + 1

        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def get_largest_files(self, path: Path, n: int = 10) -> List[Dict[str, Any]]:
        """Return the n largest files in the repository."""
        files: List[Tuple[int, str]] = []

        for root, dirs, fnames in os.walk(path):
            dirs[:] = [d for d in dirs if d not in self._SKIP_DIRS and not d.startswith('.')]
            for fname in fnames:
                fpath = Path(root) / fname
                try:
                    size = fpath.stat().st_size
                    rel = str(fpath.relative_to(path))
                    files.append((size, rel))
                except Exception:
                    pass

        files.sort(reverse=True)
        return [{'path': rel, 'size_bytes': size} for size, rel in files[:n]]

    def get_recent_files(self, path: Path, n: int = 10) -> List[Dict[str, Any]]:
        """Return the n most recently modified files."""
        files: List[Tuple[float, str]] = []

        for root, dirs, fnames in os.walk(path):
            dirs[:] = [d for d in dirs if d not in self._SKIP_DIRS and not d.startswith('.')]
            for fname in fnames:
                fpath = Path(root) / fname
                try:
                    mtime = fpath.stat().st_mtime
                    rel = str(fpath.relative_to(path))
                    files.append((mtime, rel))
                except Exception:
                    pass

        files.sort(reverse=True)
        return [
            {
                'path': rel,
                'modified': datetime.fromtimestamp(mtime).isoformat(),
            }
            for mtime, rel in files[:n]
        ]
