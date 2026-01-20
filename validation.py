from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ----------------------------
# Shared helpers
# ----------------------------

def _validate_relative_path(p: str) -> str:
    """
    Keep bundle file references safe and predictable:
    - must be relative
    - must not traverse upward
    - must not be empty
    """
    p = p.strip()
    if not p:
        raise ValueError("path must be a non-empty string")

    # Disallow absolute paths and Windows drive prefixes
    if p.startswith("/") or (len(p) >= 2 and p[1] == ":"):
        raise ValueError(f"path must be relative, got {p!r}")

    # Disallow traversal
    parts = p.replace("\\", "/").split("/")
    if any(part == ".." for part in parts):
        raise ValueError(f"path must not contain '..', got {p!r}")

    return p


class BundleBaseModel(BaseModel):
    """
    Base class for bundle contract models:
    - Allow forward-compat fields via extra="allow"
    """
    model_config = ConfigDict(extra="allow")


# ----------------------------
# Manifest
# ----------------------------

class BundleManifestV1(BundleBaseModel):
    bundle_version: Literal[1] = 1
    bundle_id: UUID
    domain: str = Field(..., min_length=1)

    # Optional but useful for humans / provenance
    created_at: Optional[datetime] = None
    label: Optional[str] = Field(default=None, description="Human-friendly label (not an ID)")

    # File references (relative to /bundle)
    entities_file: str = Field(default="entities.jsonl")
    relationships_file: str = Field(default="relationships.jsonl")
    documents_file: Optional[str] = Field(default=None)

    # Domain-specific / extra manifest fields live here (or as extra fields)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("entities_file", "relationships_file", "documents_file")
    @classmethod
    def validate_bundle_file_paths(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return _validate_relative_path(v)

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("domain must be a non-empty string")
        return v


# ----------------------------
# JSONL rows
# ----------------------------

class EntityRow(BundleBaseModel):
    """
    Minimal, generic entity row.
    Everything domain-specific should go in metadata (or extra fields).
    """
    entity_id: str = Field(..., min_length=1)
    entity_type: str = Field(..., min_length=1)

    name: Optional[str] = None
    canonical_id: Optional[str] = None

    confidence: Optional[float] = Field(
        default=None,
        description="Optional confidence in [0, 1]",
    )

    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("entity_id", "entity_type")
    @classmethod
    def non_empty_str(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must be a non-empty string")
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        if not (0.0 <= v <= 1.0):
            raise ValueError("confidence must be in [0, 1]")
        return v


class RelationshipRow(BundleBaseModel):
    """
    Minimal, generic relationship row.
    IDs are entity_id values (within the same bundle).
    """
    source_entity_id: str = Field(..., min_length=1)
    target_entity_id: str = Field(..., min_length=1)
    predicate: str = Field(..., min_length=1)

    relationship_id: Optional[str] = Field(
        default=None,
        description="Optional producer-supplied ID; server uses internal PK regardless",
    )

    confidence: Optional[float] = Field(default=None, description="Optional confidence in [0, 1]")
    evidence_document_id: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_entity_id", "target_entity_id", "predicate")
    @classmethod
    def non_empty_str(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must be a non-empty string")
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        if not (0.0 <= v <= 1.0):
            raise ValueError("confidence must be in [0, 1]")
        return v


class DocumentRow(BundleBaseModel):
    """
    Optional document row (only used if documents_file is present).
    """
    document_id: str = Field(..., min_length=1)

    title: Optional[str] = None
    source_url: Optional[str] = None
    published_at: Optional[datetime] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("document_id")
    @classmethod
    def non_empty_str(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("document_id must be a non-empty string")
        return v

