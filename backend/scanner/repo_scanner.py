#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — REPOSITORY SCANNER
# =============================================================================

import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from backend.models.repo import RepoMetadata, RepoStructure, RepoSummary, RepoStatus
from backend.config import config


class RepoScanner:
    """Scan local and GitHub repositories for Victor Command Center."""

    def __init__(self):
        self.config = config
        self.supported_languages = {
            'python': ['.py', '.pyw'],
            'javascript': ['.js', '.jsx', '.ts', '.tsx'],
            'rust': ['.rs'],
            'go': ['.go'],
            'java': ['.java'],
            'cpp': ['.cpp', '.cc', '.cxx', '.h', '.hpp'],
            'c': ['.c', '.h'],
            'ruby': ['.rb'],
            'php': ['.php'],
            'swift': ['.swift'],
            'kotlin': ['.kt', '.kts'],
        }
        self.config_files = [
            'package.json', 'requirements.txt', 'Cargo.toml', 'go.mod',
            'pom.xml', 'build.gradle', 'setup.py', 'pyproject.toml',
            'docker-compose.yml', 'Dockerfile', 'Makefile', 'CMakeLists.txt'
        ]
        self.entrypoint_files = [
            'main.py', 'app.py', 'index.js', 'main.rs', 'main.go',
            'Application.java', 'lib.rs', 'src/main.rs'
        ]

    def scan_local_repos(self, paths: List[Path]) -> List[RepoSummary]:
        """Scan local directories for repositories."""
        summaries = []
        for path in paths:
            if path.exists():
                summary = self._scan_directory(path)
                if summary:
                    summaries.append(summary)
        return summaries

    def _scan_directory(self, path: Path) -> Optional[RepoSummary]:
        """Scan a single directory as a repository."""
        if not path.is_dir():
            return None

        metadata = self._extract_metadata(path)
        structure = self._extract_structure(path)

        return RepoSummary(
            metadata=metadata,
            structure=structure
        )

    def _extract_metadata(self, path: Path) -> RepoMetadata:
        """Extract repository metadata."""
        metadata = RepoMetadata(name=path.name)

        git_dir = path / '.git'
        if git_dir.exists():
            try:
                result = subprocess.run(
                    ['git', '-C', str(path), 'log', '-1', '--format=%ci'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    metadata.last_modified = datetime.fromisoformat(result.stdout.strip())

                result = subprocess.run(
                    ['git', '-C', str(path), 'remote', 'get-url', 'origin'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    url = result.stdout.strip()
                    # Check that github.com is the hostname, not just a substring
                    is_github = (
                        url.startswith('https://github.com/')
                        or url.startswith('git@github.com:')
                        or url.startswith('http://github.com/')
                    )
                    metadata.visibility = 'public' if is_github else 'private'
            except Exception:
                pass

        languages = {}
        dependencies = []
        entrypoints = []
        config_files = []
        todo_markers = []

        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                       ['node_modules', '__pycache__', 'venv', 'env', 'build', 'dist']]

            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(path)

                for lang, extensions in self.supported_languages.items():
                    if file_path.suffix in extensions:
                        languages[lang] = languages.get(lang, 0) + 1
                        if metadata.primary_language is None:
                            metadata.primary_language = lang
                        break

                if file in self.config_files:
                    config_files.append(str(rel_path))
                    deps = self._extract_dependencies(file_path)
                    dependencies.extend(deps)

                if file in self.entrypoint_files:
                    entrypoints.append(str(rel_path))

                todos = self._extract_todos(file_path)
                todo_markers.extend(todos)

        metadata.languages = languages
        metadata.dependencies = list(set(dependencies))[:50]
        metadata.entrypoints = entrypoints[:10]
        metadata.config_files = config_files[:20]
        metadata.todo_markers = todo_markers[:100]

        metadata.framework = self._infer_framework(dependencies, config_files)
        metadata.runtime = self._infer_runtime(metadata.primary_language, metadata.framework)
        metadata.package_manager = self._infer_package_manager(config_files)
        metadata.status = self._classify_status(path, metadata)
        metadata.likely_purpose = self._infer_purpose(path, metadata)

        return metadata

    def _extract_dependencies(self, file_path: Path) -> List[str]:
        """Extract dependencies from config file."""
        deps = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

                if file_path.name == 'package.json':
                    data = json.loads(content)
                    deps.extend(data.get('dependencies', {}).keys())
                    deps.extend(data.get('devDependencies', {}).keys())

                elif file_path.name == 'requirements.txt':
                    for line in content.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('#'):
                            deps.append(line.split('==')[0].split('>=')[0].split('<=')[0])

                elif file_path.name == 'Cargo.toml':
                    in_deps = False
                    for line in content.split('\n'):
                        if '[dependencies]' in line:
                            in_deps = True
                        elif in_deps and line.startswith('['):
                            in_deps = False
                        elif in_deps and '=' in line:
                            dep_name = line.split('=')[0].strip()
                            deps.append(dep_name)
        except Exception:
            pass

        return deps

    def _extract_todos(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract TODO/FIXME/HACK markers from file."""
        todos = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    for marker in ['TODO', 'FIXME', 'HACK', 'XXX', 'NOTE']:
                        if marker in line.upper():
                            todos.append({
                                'file': str(file_path),
                                'line': line_num,
                                'marker': marker,
                                'content': line.strip()[:200]
                            })
        except Exception:
            pass

        return todos

    def _extract_structure(self, path: Path) -> RepoStructure:
        """Extract directory structure."""
        file_count = 0
        total_size = 0
        key_dirs = []
        tree = {}

        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                       ['node_modules', '__pycache__', 'venv', 'env', 'build', 'dist']]

            rel_root = Path(root).relative_to(path)
            current = tree

            for part in rel_root.parts:
                if part not in current:
                    current[part] = {}
                current = current[part]

            for file in files:
                if not file.startswith('.'):
                    file_count += 1
                    try:
                        total_size += (Path(root) / file).stat().st_size
                    except Exception:
                        pass
                    current[file] = None

            for key in ['src', 'lib', 'app', 'backend', 'frontend', 'api', 'core', 'tests']:
                if key in dirs:
                    key_dirs.append(str(Path(root) / key))

        return RepoStructure(
            root_path=str(path),
            directory_tree=tree,
            file_count=file_count,
            total_size_bytes=total_size,
            key_directories=key_dirs[:20]
        )

    def _infer_framework(self, dependencies: List[str], config_files: List[str]) -> Optional[str]:
        """Infer framework from dependencies and config."""
        frameworks = {
            'fastapi': ['fastapi', 'uvicorn'],
            'django': ['django', 'djangorestframework'],
            'flask': ['flask'],
            'react': ['react', 'react-dom'],
            'vue': ['vue', 'vuex'],
            'angular': ['@angular/core'],
            'nextjs': ['next'],
            'express': ['express'],
            'rails': ['rails'],
            'spring': ['spring-boot'],
            'pytorch': ['torch', 'torchvision'],
            'tensorflow': ['tensorflow'],
        }

        for framework, indicators in frameworks.items():
            if any(ind in dep.lower() for dep in dependencies for ind in indicators):
                return framework

        return None

    def _infer_runtime(self, language: Optional[str], framework: Optional[str]) -> Optional[str]:
        """Infer runtime from language and framework."""
        if language == 'python':
            return 'python'
        elif language in ['javascript', 'typescript']:
            return 'node'
        elif language == 'rust':
            return 'rust'
        elif language == 'go':
            return 'go'
        elif language == 'java':
            return 'jvm'
        return None

    def _infer_package_manager(self, config_files: List[str]) -> Optional[str]:
        """Infer package manager from config files."""
        if any('package.json' in f for f in config_files):
            return 'npm'
        elif any('requirements.txt' in f or 'pyproject.toml' in f for f in config_files):
            return 'pip'
        elif any('Cargo.toml' in f for f in config_files):
            return 'cargo'
        elif any('go.mod' in f for f in config_files):
            return 'go mod'
        return None

    def _classify_status(self, path: Path, metadata: RepoMetadata) -> RepoStatus:
        """Classify repository status."""
        if metadata.name.lower().startswith('archive') or metadata.name.lower().endswith('-old'):
            return RepoStatus.ARCHIVED

        if metadata.last_modified:
            days_since_modified = (datetime.now(timezone.utc) - metadata.last_modified).days
            if days_since_modified > 365:
                return RepoStatus.ARCHIVED
            elif days_since_modified > 180:
                return RepoStatus.PARTIAL

        if len(metadata.todo_markers) > 50:
            return RepoStatus.BROKEN

        if 'experimental' in metadata.name.lower() or 'test' in metadata.name.lower():
            return RepoStatus.EXPERIMENTAL

        return RepoStatus.ACTIVE

    def _infer_purpose(self, path: Path, metadata: RepoMetadata) -> Optional[str]:
        """Infer likely purpose of repository."""
        name_lower = metadata.name.lower()

        if any(word in name_lower for word in ['api', 'server', 'backend']):
            return 'Backend API Service'
        elif any(word in name_lower for word in ['ui', 'frontend', 'web', 'app']):
            return 'Frontend Application'
        elif any(word in name_lower for word in ['lib', 'sdk', 'package', 'module']):
            return 'Library/Package'
        elif any(word in name_lower for word in ['test', 'spec', 'e2e']):
            return 'Testing Suite'
        elif any(word in name_lower for word in ['doc', 'wiki', 'guide']):
            return 'Documentation'
        elif any(word in name_lower for word in ['victor', 'agent', 'cognitive', 'ai']):
            return 'Victor Cognitive System Component'
        elif any(word in name_lower for word in ['steel', 'city', 'forge', 'aether']):
            return 'Steel City/AetherForge Project'

        return 'General Purpose Repository'
