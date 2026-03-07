#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — METADATA EXTRACTOR
# =============================================================================

import re
import os
from pathlib import Path
from typing import List, Dict, Any, Optional


class MetadataExtractor:
    """Extracts deeper metadata from repository files."""

    # Patterns for API route detection per framework
    _ROUTE_PATTERNS = [
        # FastAPI / Flask / Starlette decorators
        re.compile(r'@(?:app|router)\.(get|post|put|patch|delete|head|options)\s*\(\s*["\']([^"\']+)["\']', re.IGNORECASE),
        # Express.js
        re.compile(r'(?:app|router)\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']', re.IGNORECASE),
        # Django urls.py path() / re_path()
        re.compile(r'(?:path|re_path)\s*\(\s*["\']([^"\']+)["\']', re.IGNORECASE),
    ]

    def extract_readme(self, path: Path) -> Optional[str]:
        """Read and return README content (first 4 KB)."""
        for name in ['README.md', 'README.rst', 'README.txt', 'README']:
            candidate = path / name
            if candidate.exists():
                try:
                    return candidate.read_text(encoding='utf-8', errors='ignore')[:4096]
                except Exception:
                    pass
        return None

    def extract_api_routes(self, path: Path) -> List[str]:
        """Scan source files for API route declarations."""
        routes: List[str] = []
        extensions = {'.py', '.js', '.ts', '.jsx', '.tsx'}

        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in
                       ('node_modules', '__pycache__', 'venv', 'env', '.git', 'build', 'dist')]
            for fname in files:
                if Path(fname).suffix not in extensions:
                    continue
                fpath = Path(root) / fname
                try:
                    content = fpath.read_text(encoding='utf-8', errors='ignore')
                    for pattern in self._ROUTE_PATTERNS:
                        for match in pattern.finditer(content):
                            # Last group is the path string
                            route = match.group(len(match.groups()))
                            if route and route not in routes:
                                routes.append(route)
                except Exception:
                    pass

        return routes[:100]

    def detect_test_files(self, path: Path) -> List[str]:
        """Find test files in the repository."""
        test_files: List[str] = []
        test_indicators = ('test_', '_test', 'spec_', '_spec', '.test.', '.spec.')

        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in
                       ('node_modules', '__pycache__', 'venv', 'env', '.git', 'build', 'dist')]
            for fname in files:
                fname_lower = fname.lower()
                if any(ind in fname_lower for ind in test_indicators):
                    rel = str(Path(root).relative_to(path) / fname)
                    test_files.append(rel)
                elif Path(root).name in ('tests', 'test', '__tests__', 'spec'):
                    rel = str(Path(root).relative_to(path) / fname)
                    test_files.append(rel)

        return list(dict.fromkeys(test_files))[:100]

    def extract_build_instructions(self, path: Path) -> Optional[str]:
        """Extract build/run instructions from Makefile, scripts, or README."""
        # Try Makefile first
        makefile = path / 'Makefile'
        if makefile.exists():
            try:
                content = makefile.read_text(encoding='utf-8', errors='ignore')
                # Return first 1 KB of Makefile
                return f"[Makefile]\n{content[:1024]}"
            except Exception:
                pass

        # Try run scripts
        for script in ('run.sh', 'start.sh', 'build.sh', 'install.sh'):
            candidate = path / script
            if candidate.exists():
                try:
                    return f"[{script}]\n{candidate.read_text(encoding='utf-8', errors='ignore')[:1024]}"
                except Exception:
                    pass

        # Fall back to README install/usage section
        readme = self.extract_readme(path)
        if readme:
            for keyword in ('## Installation', '## Usage', '## Getting Started', '## Build'):
                idx = readme.find(keyword)
                if idx != -1:
                    return readme[idx:idx + 512]

        return None
