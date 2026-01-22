"""
Tests for query/bundle_loader.py bundle loading logic.

Tests cover:
- _find_manifest() function
- Bundle loading from directory
- Bundle loading from ZIP
- Error handling
"""

import pytest
import json
import zipfile
from datetime import datetime
from sqlalchemy import create_engine
from sqlmodel import SQLModel

from query.bundle_loader import _find_manifest, _load_from_directory, _load_from_zip
from storage.backends.sqlite import SQLiteStorage


@pytest.fixture
def sample_manifest_data():
    """Create sample manifest data."""
    return {
        "bundle_id": "test-bundle-123",
        "domain": "test",
        "created_at": datetime.now().isoformat(),
        "bundle_version": "v1",
        "entities_file": "entities.jsonl",
        "relationships_file": "relationships.jsonl",
    }


@pytest.fixture
def bundle_directory(sample_manifest_data, tmp_path):
    """Create a temporary bundle directory with manifest and data files."""
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()

    # Create manifest.json
    manifest_path = bundle_dir / "manifest.json"
    manifest_path.write_text(json.dumps(sample_manifest_data))

    # Create entities.jsonl
    entities_file = bundle_dir / "entities.jsonl"
    entities_file.write_text(json.dumps({"entity_id": "test:1", "entity_type": "test", "name": "Test 1"}) + "\n")

    # Create relationships.jsonl
    relationships_file = bundle_dir / "relationships.jsonl"
    relationships_file.write_text(
        json.dumps(
            {
                "subject_id": "test:1",
                "predicate": "test",
                "object_id": "test:2",
            }
        )
        + "\n"
    )

    return bundle_dir


@pytest.fixture
def bundle_zip(bundle_directory, tmp_path):
    """Create a ZIP file from bundle directory."""
    zip_path = tmp_path / "bundle.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for file_path in bundle_directory.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(bundle_directory)
                zf.write(file_path, arcname)
    return zip_path


@pytest.fixture
def test_engine():
    """Create a test SQLAlchemy engine."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


class TestFindManifest:
    """Test _find_manifest() function."""

    def test_find_manifest_in_root(self, bundle_directory):
        """Test finding manifest.json in root directory."""
        manifest_path = _find_manifest(bundle_directory)
        assert manifest_path is not None
        assert manifest_path.name == "manifest.json"
        assert manifest_path.parent == bundle_directory

    def test_find_manifest_in_subdirectory(self, tmp_path):
        """Test finding manifest.json in subdirectory."""
        # Create structure: root/subdir/manifest.json
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        manifest_path = subdir / "manifest.json"
        manifest_path.write_text('{"bundle_id": "test", "domain": "test", "created_at": "2024-01-01T00:00:00"}')

        found = _find_manifest(tmp_path)
        assert found is not None
        assert found == manifest_path

    def test_find_manifest_not_found(self, tmp_path):
        """Test when manifest.json is not found."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        manifest_path = _find_manifest(empty_dir)
        assert manifest_path is None

    def test_find_manifest_prefers_root(self, tmp_path):
        """Test that root manifest is preferred over subdirectory."""
        # Create manifest in root
        root_manifest = tmp_path / "manifest.json"
        root_manifest.write_text('{"bundle_id": "root", "domain": "test", "created_at": "2024-01-01T00:00:00"}')

        # Create manifest in subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        sub_manifest = subdir / "manifest.json"
        sub_manifest.write_text('{"bundle_id": "sub", "domain": "test", "created_at": "2024-01-01T00:00:00"}')

        found = _find_manifest(tmp_path)
        assert found == root_manifest


class TestLoadFromDirectory:
    """Test _load_from_directory() function."""

    def test_load_from_directory_success(self, bundle_directory, test_engine):
        """Test successfully loading bundle from directory."""
        db_url = "sqlite:///:memory:"

        # Should not raise
        _load_from_directory(test_engine, db_url, bundle_directory)

        # Verify data was loaded
        storage = SQLiteStorage(":memory:")
        # Note: SQLiteStorage creates its own engine, so we can't easily verify
        # the data was loaded. This test mainly verifies no exceptions are raised.
        storage.close()

    def test_load_from_directory_no_manifest(self, tmp_path, test_engine):
        """Test loading from directory without manifest."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        db_url = "sqlite:///:memory:"
        # Should handle gracefully (prints error but doesn't raise)
        _load_from_directory(test_engine, db_url, empty_dir)


class TestLoadFromZip:
    """Test _load_from_zip() function."""

    def test_load_from_zip_success(self, bundle_zip, test_engine):
        """Test successfully loading bundle from ZIP."""
        db_url = "sqlite:///:memory:"

        # Should not raise
        _load_from_zip(test_engine, db_url, bundle_zip)

    def test_load_from_zip_no_manifest(self, tmp_path, test_engine):
        """Test loading ZIP without manifest."""
        zip_path = tmp_path / "empty.zip"
        with zipfile.ZipFile(zip_path, "w"):
            # Create empty ZIP
            pass

        db_url = "sqlite:///:memory:"
        # Should handle gracefully (prints error but doesn't raise)
        _load_from_zip(test_engine, db_url, zip_path)
