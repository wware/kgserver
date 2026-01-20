# bundle_schema.py
from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BundleFormat(str, Enum):
    JSON = "json"
    JSONL = "jsonl"


class FileRef(BaseModel):
    """Reference to a file in the mounted bundle directory."""
    model_config = ConfigDict(frozen=True)

    path: str = Field(..., description="Relative path within the bundle directory")
    format: BundleFormat

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

    subject_id: str = "subject_id"
    predicate: str = "predicate"
    object_id: str = "object_id"


class BundleManifestV1(BaseModel):
    """
    The one file the server reads first: /bundle/manifest.json
    It tells the server what data files exist and how to interpret them.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    bundle_version: Literal["v1"] = "v1"
    domain: str = Field(..., description="Human-readable domain name, e.g. 'sherlock'")
    created_at: datetime = Field(..., description="When this bundle was generated")

    # Optional but very useful for idempotent loads
    bundle_id: str = Field(
        ...,
        description="Stable identifier for this bundle build (hash or UUID)",
        examples=["sha256:..."],
    )

    id_fields: IdFields = Field(default_factory=IdFields)

    entities: FileRef
    relationships: FileRef

    documents: FileRef | None = None
    embeddings: FileRef | None = None

    # Anything else you want to preserve without schema churn
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("domain")
    @classmethod
    def _domain_nonempty(cls, v: str) -> str:
        v2 = v.strip()
        if not v2:
            raise ValueError("domain must be non-empty")
        return v2


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