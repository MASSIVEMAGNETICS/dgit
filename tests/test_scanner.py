#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — SCANNER TESTS
# =============================================================================

import pytest
from pathlib import Path


@pytest.fixture()
def sample_repo(tmp_path):
    """Create a minimal fake repository directory."""
    # Python source
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("# TODO: implement\nprint('hello')\n")
    (src / "utils.py").write_text("def helper(): pass\n")

    # requirements.txt
    (tmp_path / "requirements.txt").write_text("fastapi>=0.109.0\nuvicorn>=0.27.0\nnumpy>=1.26.0\n")

    # package.json (JS side)
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"react": "^18.0.0", "axios": "^1.6.0"}, "devDependencies": {"jest": "^29.0.0"}}'
    )

    # Makefile
    (tmp_path / "Makefile").write_text("run:\n\tuvicorn src.main:app\n")

    # README
    (tmp_path / "README.md").write_text("# Sample Repo\n\n## Installation\n\npip install -r requirements.txt\n")

    # test file
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text("def test_hello(): assert True\n")

    return tmp_path


def test_scan_local_repos(sample_repo):
    """RepoScanner should return a summary for a valid directory."""
    from backend.scanner.repo_scanner import RepoScanner
    scanner = RepoScanner()
    summaries = scanner.scan_local_repos([sample_repo])
    assert len(summaries) == 1
    assert summaries[0].metadata.name == sample_repo.name


def test_scan_missing_path(tmp_path):
    """RepoScanner should skip non-existent paths gracefully."""
    from backend.scanner.repo_scanner import RepoScanner
    scanner = RepoScanner()
    missing = tmp_path / "does_not_exist"
    summaries = scanner.scan_local_repos([missing])
    assert summaries == []


def test_metadata_primary_language(sample_repo):
    """Primary language should be detected from source files."""
    from backend.scanner.repo_scanner import RepoScanner
    scanner = RepoScanner()
    summaries = scanner.scan_local_repos([sample_repo])
    meta = summaries[0].metadata
    assert meta.primary_language in ('python', 'javascript')


def test_dependency_extraction(sample_repo):
    """Dependencies from requirements.txt should be extracted."""
    from backend.scanner.repo_scanner import RepoScanner
    scanner = RepoScanner()
    summaries = scanner.scan_local_repos([sample_repo])
    deps = summaries[0].metadata.dependencies
    assert any('fastapi' in d.lower() for d in deps)


def test_todo_extraction(sample_repo):
    """TODO markers should be detected."""
    from backend.scanner.repo_scanner import RepoScanner
    scanner = RepoScanner()
    summaries = scanner.scan_local_repos([sample_repo])
    assert len(summaries[0].metadata.todo_markers) >= 1


def test_structure_extraction(sample_repo):
    """Structure should report correct file count."""
    from backend.scanner.repo_scanner import RepoScanner
    scanner = RepoScanner()
    summaries = scanner.scan_local_repos([sample_repo])
    structure = summaries[0].structure
    assert structure is not None
    assert structure.file_count > 0
    assert structure.root_path == str(sample_repo)


def test_package_manager_detection(sample_repo):
    """Package manager should be detected as pip (requirements.txt present)."""
    from backend.scanner.repo_scanner import RepoScanner
    scanner = RepoScanner()
    summaries = scanner.scan_local_repos([sample_repo])
    pm = summaries[0].metadata.package_manager
    assert pm in ('pip', 'npm')


def test_metadata_extractor_readme(sample_repo):
    """MetadataExtractor should find and return README content."""
    from backend.scanner.metadata_extractor import MetadataExtractor
    extractor = MetadataExtractor()
    readme = extractor.extract_readme(sample_repo)
    assert readme is not None
    assert 'Sample Repo' in readme


def test_metadata_extractor_test_files(sample_repo):
    """MetadataExtractor should detect test files."""
    from backend.scanner.metadata_extractor import MetadataExtractor
    extractor = MetadataExtractor()
    test_files = extractor.detect_test_files(sample_repo)
    assert len(test_files) >= 1
    assert any('test_main.py' in f for f in test_files)


def test_metadata_extractor_build_instructions(sample_repo):
    """MetadataExtractor should return Makefile as build instructions."""
    from backend.scanner.metadata_extractor import MetadataExtractor
    extractor = MetadataExtractor()
    instructions = extractor.extract_build_instructions(sample_repo)
    assert instructions is not None
    assert 'Makefile' in instructions or 'uvicorn' in instructions


def test_structure_analyzer_depth(sample_repo):
    """StructureAnalyzer should report max_depth >= 1."""
    from backend.scanner.structure_analyzer import StructureAnalyzer
    analyzer = StructureAnalyzer()
    result = analyzer.analyze_depth(sample_repo)
    assert result['max_depth'] >= 1


def test_structure_analyzer_file_types(sample_repo):
    """StructureAnalyzer should count .py extension."""
    from backend.scanner.structure_analyzer import StructureAnalyzer
    analyzer = StructureAnalyzer()
    types = analyzer.get_file_types(sample_repo)
    assert '.py' in types
    assert types['.py'] >= 2


def test_structure_analyzer_largest_files(sample_repo):
    """StructureAnalyzer should return largest files list."""
    from backend.scanner.structure_analyzer import StructureAnalyzer
    analyzer = StructureAnalyzer()
    files = analyzer.get_largest_files(sample_repo, n=5)
    assert isinstance(files, list)
    assert all('path' in f and 'size_bytes' in f for f in files)


def test_structure_analyzer_recent_files(sample_repo):
    """StructureAnalyzer should return recently modified files."""
    from backend.scanner.structure_analyzer import StructureAnalyzer
    analyzer = StructureAnalyzer()
    files = analyzer.get_recent_files(sample_repo, n=5)
    assert isinstance(files, list)
    assert all('path' in f and 'modified' in f for f in files)
