"""
PostgreSQL implementation of the storage interface.
"""
import json
from typing import List, Optional
from sqlmodel import Session, select
from storage.interfaces import StorageInterface
from storage.models.entity import Entity
from storage.models.relationship import Relationship
from bundle_schema import BundleManifestV1


class PostgresStorage(StorageInterface):
    """
    PostgreSQL implementation of the storage interface.
    """

    def __init__(self, session: Session):
        self._session = session

    def load_bundle(self, bundle_manifest: BundleManifestV1, bundle_path: str) -> None:
        """
        Load a data bundle into the storage.
        This is an idempotent operation. If the bundle is already loaded, it will do nothing.
        """
        # For now, we'll just log that we are loading the bundle.
        # The actual implementation will read the files and load them into the database.
        print(f"Loading bundle {bundle_manifest.bundle_id} from {bundle_path}")

        # Check if bundle is already loaded
        # This is a placeholder for a real check.
        # with self._session.begin():
        #     if self._session.query(BundleMetadata).filter_by(bundle_id=bundle_manifest.bundle_id).first():
        #         print(f"Bundle {bundle_manifest.bundle_id} already loaded.")
        #         return

        # Load entities
        entities_file = f"{bundle_path}/{bundle_manifest.entities.path}"
        with open(entities_file, "r") as f:
            for line in f:
                entity_data = json.loads(line)
                entity = Entity(**entity_data)
                self._session.merge(entity)

        # Load relationships
        relationships_file = f"{bundle_path}/{bundle_manifest.relationships.path}"
        with open(relationships_file, "r") as f:
            for line in f:
                relationship_data = json.loads(line)
                relationship = Relationship(**relationship_data)
                self._session.merge(relationship)

        self._session.commit()

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """
        Get an entity by its ID.
        """
        return self._session.get(Entity, entity_id)

    def get_entities(self, limit: int = 100, offset: int = 0) -> List[Entity]:
        """
        List all entities.
        """
        statement = select(Entity).limit(limit).offset(offset)
        return self._session.exec(statement).all()

    def find_relationships(
        self,
        subject_id: Optional[str] = None,
        predicate: Optional[str] = None,
        object_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Relationship]:
        """
        Find relationships matching criteria.
        """
        statement = select(Relationship)
        if subject_id:
            statement = statement.where(Relationship.subject_id == subject_id)
        if predicate:
            statement = statement.where(Relationship.predicate == predicate)
        if object_id:
            statement = statement.where(Relationship.object_id == object_id)
        if limit:
            statement = statement.limit(limit)
        return self._session.exec(statement).all()

    def get_relationship(self, subject_id: str, predicate: str, object_id: str) -> Optional[Relationship]:
        """
        Get a relationship by its canonical triple (subject_id, predicate, object_id).
        """
        statement = select(Relationship).where(
            Relationship.subject_id == subject_id,
            Relationship.predicate == predicate,
            Relationship.object_id == object_id,
        )
        return self._session.exec(statement).first()

    def get_relationships(self, limit: int = 100, offset: int = 0) -> List[Relationship]:
        """
        List all relationships.
        """
        statement = select(Relationship).limit(limit).offset(offset)
        return self._session.exec(statement).all()

    def close(self) -> None:
        """
        Close connections and clean up resources.
        """
        self._session.close()