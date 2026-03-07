#!/usr/bin/env python3
# =============================================================================
# VICTOR COMMAND CENTER — CONFIGURATION
# =============================================================================

from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
import json

class VictorConfig(BaseModel):
    """System configuration for Victor Command Center."""

    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    storage_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "storage")
    artifacts_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "storage" / "artifacts")
    vector_index_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "storage" / "vector_index")

    # Database
    database_path: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "storage" / "victor.db")

    # Scanning
    scan_paths: List[Path] = Field(default_factory=list)
    github_token: Optional[str] = None
    github_org: Optional[str] = "MASSIVEMAGNETICS"

    # Indexing
    embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 768
    chunk_size: int = 512
    chunk_overlap: int = 50

    # LLM
    llm_endpoint: str = "http://localhost:11434"
    llm_model: str = "llama3.1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # Victor Integration
    victor_cognitive_enabled: bool = True
    attention_engine_enabled: bool = True
    qualia_tracking: bool = True

    def create_directories(self):
        """Create all required directories."""
        for dir_path in [self.storage_dir, self.artifacts_dir, self.vector_index_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def save(self, path: Optional[Path] = None):
        """Save configuration to file."""
        path = path or (self.base_dir / "config" / "victor_config.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            config_dict = self.model_dump()
            config_dict['base_dir'] = str(config_dict['base_dir'])
            config_dict['storage_dir'] = str(config_dict['storage_dir'])
            config_dict['artifacts_dir'] = str(config_dict['artifacts_dir'])
            config_dict['vector_index_dir'] = str(config_dict['vector_index_dir'])
            config_dict['database_path'] = str(config_dict['database_path'])
            config_dict['scan_paths'] = [str(p) for p in config_dict['scan_paths']]
            json.dump(config_dict, f, indent=2)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> 'VictorConfig':
        """Load configuration from file."""
        path = path or (Path(__file__).parent.parent / "config" / "victor_config.json")
        if path.exists():
            with open(path, 'r') as f:
                config_dict = json.load(f)
                config_dict['base_dir'] = Path(config_dict['base_dir'])
                config_dict['storage_dir'] = Path(config_dict['storage_dir'])
                config_dict['artifacts_dir'] = Path(config_dict['artifacts_dir'])
                config_dict['vector_index_dir'] = Path(config_dict['vector_index_dir'])
                config_dict['database_path'] = Path(config_dict['database_path'])
                config_dict['scan_paths'] = [Path(p) for p in config_dict['scan_paths']]
                return cls(**config_dict)
        return cls()


# Global config instance
config = VictorConfig.load()
config.create_directories()
