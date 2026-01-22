"""
Tests for query/bundle.py Pydantic models.

Tests cover:
- FileRef path validation
- BundleManifestV1 validation and normalization
- DocumentRow validation
- Version string conversion
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from query.bundle import (
    BundleFormat,
    FileRef,
    BundleManifestV1,
    DocumentRow,
    IdFields,
)


class TestFileRef:
    """Test FileRef model validation."""

    def test_valid_relative_path(self):
        """Test that valid relative paths are accepted."""
        ref = FileRef(path="entities.jsonl")
        assert ref.path == "entities.jsonl"
        assert ref.format == BundleFormat.JSONL

    def test_relative_path_with_subdirectory(self):
        """Test relative paths with subdirectories."""
        ref = FileRef(path="data/entities.jsonl")
        assert ref.path == "data/entities.jsonl"

    def test_absolute_path_rejected(self):
        """Test that absolute paths are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            FileRef(path="/absolute/path/entities.jsonl")
        assert "path must be relative" in str(exc_info.value)

    def test_path_with_parent_directory_rejected(self):
        """Test that paths with '..' are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            FileRef(path="../entities.jsonl")
        assert "path must not contain" in str(exc_info.value)

    def test_path_with_nested_parent_directory_rejected(self):
        """Test that paths with nested '..' are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            FileRef(path="data/../../entities.jsonl")
        assert "path must not contain" in str(exc_info.value)

    def test_format_json(self):
        """Test JSON format specification."""
        ref = FileRef(path="entities.json", format=BundleFormat.JSON)
        assert ref.format == BundleFormat.JSON

    def test_format_jsonl(self):
        """Test JSONL format specification."""
        ref = FileRef(path="entities.jsonl", format=BundleFormat.JSONL)
        assert ref.format == BundleFormat.JSONL


class TestBundleManifestV1:
    """Test BundleManifestV1 model validation and normalization."""

    def test_minimal_valid_manifest(self):
        """Test creating a minimal valid manifest."""
        manifest = BundleManifestV1(
            bundle_id="test-bundle-123",
            domain="test",
            created_at=datetime.now(),
        )
        assert manifest.bundle_id == "test-bundle-123"
        assert manifest.domain == "test"
        assert manifest.bundle_version == "v1"

    def test_domain_validation_nonempty(self):
        """Test that domain must be non-empty."""
        with pytest.raises(ValidationError) as exc_info:
            BundleManifestV1(
                bundle_id="test",
                domain="",
                created_at=datetime.now(),
            )
        assert "domain must be non-empty" in str(exc_info.value)

    def test_domain_validation_whitespace_stripped(self):
        """Test that domain whitespace is stripped."""
        manifest = BundleManifestV1(
            bundle_id="test",
            domain="  test  ",
            created_at=datetime.now(),
        )
        assert manifest.domain == "test"

    def test_version_string(self):
        """Test version as string."""
        manifest = BundleManifestV1(
            bundle_id="test",
            domain="test",
            created_at=datetime.now(),
            bundle_version="v1",
        )
        assert manifest.get_version_str() == "v1"

    def test_version_integer(self):
        """Test version as integer."""
        manifest = BundleManifestV1(
            bundle_id="test",
            domain="test",
            created_at=datetime.now(),
            bundle_version=1,
        )
        assert manifest.get_version_str() == "v1"

    def test_version_integer_2(self):
        """Test version as integer 2."""
        manifest = BundleManifestV1(
            bundle_id="test",
            domain="test",
            created_at=datetime.now(),
            bundle_version=2,
        )
        assert manifest.get_version_str() == "v2"

    def test_entities_file_normalization(self):
        """Test that entities_file is normalized to FileRef."""
        manifest = BundleManifestV1(
            bundle_id="test",
            domain="test",
            created_at=datetime.now(),
            entities_file="entities.jsonl",
        )
        assert manifest.entities is not None
        assert manifest.entities.path == "entities.jsonl"
        assert manifest.entities.format == BundleFormat.JSONL

    def test_entities_file_json_normalization(self):
        """Test that entities_file with .json extension is normalized correctly."""
        manifest = BundleManifestV1(
            bundle_id="test",
            domain="test",
            created_at=datetime.now(),
            entities_file="entities.json",
        )
        assert manifest.entities is not None
        assert manifest.entities.format == BundleFormat.JSON

    def test_relationships_file_normalization(self):
        """Test that relationships_file is normalized to FileRef."""
        manifest = BundleManifestV1(
            bundle_id="test",
            domain="test",
            created_at=datetime.now(),
            relationships_file="relationships.jsonl",
        )
        assert manifest.relationships is not None
        assert manifest.relationships.path == "relationships.jsonl"

    def test_documents_file_normalization(self):
        """Test that documents_file is normalized to FileRef."""
        manifest = BundleManifestV1(
            bundle_id="test",
            domain="test",
            created_at=datetime.now(),
            documents_file="documents.jsonl",
        )
        assert manifest.documents is not None
        assert manifest.documents.path == "documents.jsonl"

    def test_file_ref_takes_precedence(self):
        """Test that FileRef objects take precedence over string paths."""
        manifest = BundleManifestV1(
            bundle_id="test",
            domain="test",
            created_at=datetime.now(),
            entities=FileRef(path="custom.jsonl"),
            entities_file="entities.jsonl",
        )
        assert manifest.entities.path == "custom.jsonl"

    def test_metadata_field(self):
        """Test that metadata field works."""
        manifest = BundleManifestV1(
            bundle_id="test",
            domain="test",
            created_at=datetime.now(),
            metadata={"key": "value"},
        )
        assert manifest.metadata == {"key": "value"}

    def test_extra_fields_allowed(self):
        """Test that extra fields are allowed."""
        manifest = BundleManifestV1(
            bundle_id="test",
            domain="test",
            created_at=datetime.now(),
            custom_field="value",
        )
        assert hasattr(manifest, "custom_field")
        assert manifest.custom_field == "value"


class TestIdFields:
    """Test IdFields model."""

    def test_default_values(self):
        """Test default field names."""
        id_fields = IdFields()
        assert id_fields.entity_id == "entity_id"
        assert id_fields.entity_type == "entity_type"
        assert id_fields.name == "name"
        assert id_fields.subject_id == "subject_id"
        assert id_fields.predicate == "predicate"
        assert id_fields.object_id == "object_id"

    def test_custom_field_names(self):
        """Test custom field names."""
        id_fields = IdFields(
            entity_id="id",
            entity_type="type",
            name="label",
        )
        assert id_fields.entity_id == "id"
        assert id_fields.entity_type == "type"
        assert id_fields.name == "label"


class TestDocumentRow:
    """Test DocumentRow model validation."""

    def test_valid_document_row(self):
        """Test creating a valid document row."""
        row = DocumentRow(
            document_id="doc123",
            title="Test Document",
        )
        assert row.document_id == "doc123"
        assert row.title == "Test Document"

    def test_document_id_nonempty(self):
        """Test that document_id must be non-empty."""
        with pytest.raises(ValidationError):
            DocumentRow(document_id="")

    def test_document_id_whitespace_stripped(self):
        """Test that document_id whitespace is stripped."""
        row = DocumentRow(document_id="  doc123  ")
        assert row.document_id == "doc123"

    def test_document_id_whitespace_only_rejected(self):
        """Test that whitespace-only document_id is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentRow(document_id="   ")
        assert "document_id must be a non-empty string" in str(exc_info.value)

    def test_optional_fields(self):
        """Test that optional fields work."""
        row = DocumentRow(
            document_id="doc123",
            title="Title",
            source_url="https://example.com",
            published_at=datetime.now(),
            metadata={"key": "value"},
        )
        assert row.title == "Title"
        assert row.source_url == "https://example.com"
        assert row.metadata == {"key": "value"}

    def test_extra_fields_allowed(self):
        """Test that extra fields are allowed."""
        row = DocumentRow(
            document_id="doc123",
            custom_field="value",
        )
        assert hasattr(row, "custom_field")
        assert row.custom_field == "value"
