#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — REPO DATA MODELS
# =============================================================================

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class RepoStatus(str, Enum):
    """Repository status classification."""
    ACTIVE = "active"
    PARTIAL = "partial"
    BROKEN = "broken"
    ARCHIVED = "archived"
    EXPERIMENTAL = "experimental"
    UNKNOWN = "unknown"


class RepoMetadata(BaseModel):
    """Repository metadata extracted during scan."""
    name: str
    description: Optional[str] = None
    visibility: str = "private"
    primary_language: Optional[str] = None
    languages: Dict[str, int] = Field(default_factory=dict)
    framework: Optional[str] = None
    runtime: Optional[str] = None
    package_manager: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    entrypoints: List[str] = Field(default_factory=list)
    api_routes: List[str] = Field(default_factory=list)
    config_files: List[str] = Field(default_factory=list)
    test_files: List[str] = Field(default_factory=list)
    todo_markers: List[Dict[str, Any]] = Field(default_factory=list)
    build_instructions: Optional[str] = None
    likely_purpose: Optional[str] = None
    status: RepoStatus = RepoStatus.UNKNOWN
    last_modified: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RepoStructure(BaseModel):
    """Repository directory structure."""
    root_path: str
    directory_tree: Dict[str, Any]
    file_count: int
    total_size_bytes: int
    key_directories: List[str] = Field(default_factory=list)


class RepoRelationship(BaseModel):
    """Relationship between two repositories."""
    source_repo: str
    target_repo: str
    relationship_type: str  # dependency, duplicate, shared_code, integration
    confidence: float
    details: Dict[str, Any] = Field(default_factory=dict)


class RepoSummary(BaseModel):
    """Complete repository summary."""
    metadata: RepoMetadata
    structure: Optional[RepoStructure] = None
    relationships: List[RepoRelationship] = Field(default_factory=list)
    scan_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_markdown(self) -> str:
        """Generate markdown summary."""
        md = f"# {self.metadata.name}\n\n"
        md += f"**Status:** {self.metadata.status.value}\n\n"
        if self.metadata.description:
            md += f"**Description:** {self.metadata.description}\n\n"
        md += f"**Primary Language:** {self.metadata.primary_language or 'Unknown'}\n\n"
        md += f"**Framework:** {self.metadata.framework or 'Unknown'}\n\n"
        md += f"**Dependencies:** {len(self.metadata.dependencies)}\n\n"
        md += f"**Entrypoints:** {', '.join(self.metadata.entrypoints[:5])}\n\n"
        if self.metadata.todo_markers:
            md += f"**TODOs:** {len(self.metadata.todo_markers)}\n\n"
        return md
