#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — CODE PARSER
# =============================================================================

import ast
from pathlib import Path
from typing import Dict, Any, List


class CodeParser:
    """Parses Python source files using the ast module."""

    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a Python file and return its structural metadata.

        Returns a dict with keys:
            classes   – list of class dicts {name, methods, bases, lineno}
            functions – list of function dicts {name, args, lineno, is_async}
            imports   – list of imported module/name strings
            errors    – list of parse error messages (empty on success)
        """
        result: Dict[str, Any] = {
            'classes': [],
            'functions': [],
            'imports': [],
            'errors': [],
        }

        try:
            source = Path(file_path).read_text(encoding='utf-8', errors='ignore')
        except Exception as exc:
            result['errors'].append(f"Read error: {exc}")
            return result

        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as exc:
            result['errors'].append(f"SyntaxError: {exc}")
            return result

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                result['imports'].extend(self._extract_import(node))

        # Only top-level and class-level definitions
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                result['classes'].append(self._extract_class(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result['functions'].append(self._extract_function(node))

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_import(self, node: ast.stmt) -> List[str]:
        names: List[str] = []
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                names.append(f"{module}.{alias.name}" if module else alias.name)
        return names

    def _extract_class(self, node: ast.ClassDef) -> Dict[str, Any]:
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{ast.unparse(base)}")

        methods: List[Dict[str, Any]] = []
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self._extract_function(child))

        return {
            'name': node.name,
            'bases': bases,
            'methods': methods,
            'lineno': node.lineno,
        }

    def _extract_function(self, node: ast.stmt) -> Dict[str, Any]:
        args: List[str] = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in node.args.args:
                args.append(arg.arg)
            return {
                'name': node.name,
                'args': args,
                'lineno': node.lineno,
                'is_async': isinstance(node, ast.AsyncFunctionDef),
            }
        return {}
