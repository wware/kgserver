# query/bundle.py
from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BundleFormat(str, Enum):
    JSON = "json"
    JSONL = "jsonl"


class FileRef(BaseModel):
    """Reference to a file in the mounted bundle directory."""

    model_config = ConfigDict(frozen=True)

    path: str = Field(..., description="Relative path within the bundle directory")
    format: BundleFormat = BundleFormat.JSONL

    @field_validator("path")
    @classmethod
    def _path_must_be_relative(cls, v: str) -> str:
        p = Path(v)
        if p.is_absolute():
            raise ValueError("path must be relative to the bundle root")
        if ".." in p.parts:
            raise ValueError("path must not contain '..'")
        return v


class IdFields(BaseModel):
    """Declare the field names used by entity and relationship rows."""

    model_config = ConfigDict(frozen=True)

    entity_id: str = "entity_id"
    entity_type: str = "entity_type"
    name: str = "name"

    # Support both naming conventions for relationships
    subject_id: str = "subject_id"
    predicate: str = "predicate"
    object_id: str = "object_id"
    # Alternative field names (source_entity_id/target_entity_id)
    source_entity_id: str = "source_entity_id"
    target_entity_id: str = "target_entity_id"


class BundleManifestV1(BaseModel):
    """
    The one file the server reads first: /bundle/manifest.json
    It tells the server what data files exist and how to interpret them.
    Supports both v1 format styles (FileRef objects or simple file paths).
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    bundle_version: Union[int, str] = Field(default="v1", description="Bundle format version (1 or 'v1')")
    domain: str = Field(..., description="Human-readable domain name, e.g. 'sherlock'")
    created_at: datetime = Field(..., description="When this bundle was generated")

    # Optional but very useful for idempotent loads
    bundle_id: str = Field(
        ...,
        description="Stable identifier for this bundle build (hash or UUID)",
        examples=["sha256:..."],
    )

    id_fields: IdFields = Field(default_factory=IdFields)

    # Support both FileRef objects and simple string paths
    entities: FileRef | None = None
    relationships: FileRef | None = None
    # Alternative: simple file path strings
    entities_file: str | None = None
    relationships_file: str | None = None

    documents: FileRef | None = None
    documents_file: str | None = None
    embeddings: FileRef | None = None

    # Optional label field
    label: str | None = None

    # Anything else you want to preserve without schema churn
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("domain")
    @classmethod
    def _domain_nonempty(cls, v: str) -> str:
        v2 = v.strip()
        if not v2:
            raise ValueError("domain must be non-empty")
        return v2

    @model_validator(mode="after")
    def _normalize_file_refs(self) -> "BundleManifestV1":
        """Convert string file paths to FileRef objects for uniform access."""
        # We can't mutate frozen model, so we use object.__setattr__
        if self.entities is None and self.entities_file:
            fmt = BundleFormat.JSONL if self.entities_file.endswith(".jsonl") else BundleFormat.JSON
            object.__setattr__(self, "entities", FileRef(path=self.entities_file, format=fmt))
        if self.relationships is None and self.relationships_file:
            fmt = BundleFormat.JSONL if self.relationships_file.endswith(".jsonl") else BundleFormat.JSON
            object.__setattr__(self, "relationships", FileRef(path=self.relationships_file, format=fmt))
        if self.documents is None and self.documents_file:
            fmt = BundleFormat.JSONL if self.documents_file.endswith(".jsonl") else BundleFormat.JSON
            object.__setattr__(self, "documents", FileRef(path=self.documents_file, format=fmt))
        return self

    def get_version_str(self) -> str:
        """Return version as string for storage."""
        if isinstance(self.bundle_version, int):
            return f"v{self.bundle_version}"
        return self.bundle_version


# --- Optional row-level models for validation during ingest ---


class EntityRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")

    entity_id: str
    entity_type: str
    name: str | None = None
    status: str | None = None
    confidence: float | None = None
    usage_count: int | None = None
    created_at: datetime | None = None
    source: str | None = None
    synonyms: list[str] | None = None


class RelationshipRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")

    subject_id: str
    predicate: str
    object_id: str
    confidence: float | None = None
    source_documents: list[str] | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class DocumentRow(BaseModel):
    """
    Optional document row (only used if documents_file is present).
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    document_id: str = Field(..., min_length=1)

    title: str | None = None
    source_url: str | None = None
    published_at: datetime | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("document_id")
    @classmethod
    def non_empty_str(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("document_id must be a non-empty string")
        return v
