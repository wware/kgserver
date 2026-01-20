# query/bundle_loader.py
"""
Bundle loading utilities for the KG server.
Handles loading bundles from directories or ZIP files at startup.
"""

import json
import os
import tempfile
import zipfile
from pathlib import Path

from sqlmodel import Session, SQLModel, delete

from .bundle import BundleManifestV1
from storage.backends.postgres import PostgresStorage

# from storage.backends.sqlite import SQLiteStorage
from storage.models.entity import Entity
from storage.models.relationship import Relationship


def load_bundle_at_startup(engine, db_url: str) -> None:
    """
    Load a bundle at server startup if BUNDLE_PATH is set.

    Environment variables:
        BUNDLE_PATH: Path to a bundle directory or ZIP file
    """
    bundle_path = os.getenv("BUNDLE_PATH")
    if not bundle_path:
        print("BUNDLE_PATH not set, skipping bundle load.")
        return

    bundle_path = Path(bundle_path)
    if not bundle_path.exists():
        print(f"Warning: BUNDLE_PATH '{bundle_path}' does not exist, skipping bundle load.")
        return

    print(f"Loading bundle from: {bundle_path}")

    # Ensure tables exist
    SQLModel.metadata.create_all(engine)

    # Handle ZIP file vs directory
    if bundle_path.suffix == ".zip":
        _load_from_zip(engine, db_url, bundle_path)
    elif bundle_path.is_dir():
        _load_from_directory(engine, db_url, bundle_path)
    else:
        print(f"Warning: BUNDLE_PATH '{bundle_path}' is not a directory or ZIP file.")


def _load_from_zip(engine, db_url: str, zip_path: Path) -> None:
    """Extract and load a bundle from a ZIP file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmpdir)

        # Find the manifest - could be at root or in a subdirectory
        tmpdir_path = Path(tmpdir)
        manifest_path = _find_manifest(tmpdir_path)
        if not manifest_path:
            print(f"Error: No manifest.json found in ZIP file {zip_path}")
            return

        bundle_dir = manifest_path.parent
        _do_load(engine, db_url, bundle_dir, manifest_path)


def _load_from_directory(engine, db_url: str, bundle_dir: Path) -> None:
    """Load a bundle from a directory."""
    manifest_path = _find_manifest(bundle_dir)
    if not manifest_path:
        print(f"Error: No manifest.json found in {bundle_dir}")
        return

    bundle_dir = manifest_path.parent
    _do_load(engine, db_url, bundle_dir, manifest_path)


def _find_manifest(search_dir: Path) -> Path | None:
    """Find manifest.json in a directory (possibly in a subdirectory)."""
    # Check directly in the directory
    direct = search_dir / "manifest.json"
    if direct.exists():
        return direct

    # Check one level of subdirectories
    for subdir in search_dir.iterdir():
        if subdir.is_dir():
            manifest = subdir / "manifest.json"
            if manifest.exists():
                return manifest

    return None


def _do_load(engine, db_url: str, bundle_dir: Path, manifest_path: Path) -> None:
    """Actually load the bundle into storage."""
    # Parse manifest
    with open(manifest_path, "r") as f:
        manifest_data = json.load(f)

    manifest = BundleManifestV1(**manifest_data)
    print(f"Loaded manifest for bundle: {manifest.bundle_id} (domain: {manifest.domain})")

    # Get the appropriate storage backend
    with Session(engine) as session:
        # Clear existing data before loading
        print("Clearing existing data from Relationship and Entity tables...")
        session.exec(delete(Relationship))
        session.exec(delete(Entity))
        session.commit()
        print("Data cleared.")

        if db_url.startswith("postgresql://"):
            storage = PostgresStorage(session)
        else:
            # For SQLite we need to use the session-based approach here
            storage = PostgresStorage(session)  # PostgresStorage works with any SQLModel session

        storage.load_bundle(manifest, str(bundle_dir))
        print(f"Bundle {manifest.bundle_id} loaded successfully.")
