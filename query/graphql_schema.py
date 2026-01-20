"""
GraphQL schema for the Knowledge Graph API.

This schema uses proper Strawberry types for type safety and better GraphQL introspection.
"""

import strawberry
from typing import List, Optional, Any
from strawberry.types import Info

from storage.models.entity import Entity as EntityModel
from storage.models.relationship import Relationship as RelationshipModel


@strawberry.type
class Entity:
    """Generic entity GraphQL type."""
    entity_id: str
    entity_type: str
    name: Optional[str] = None
    status: Optional[str] = None
    confidence: Optional[float] = None
    usage_count: Optional[int] = None
    source: Optional[str] = None
    synonyms: List[str] = []
    properties: Any = None # Use Any for JSON/dict


@strawberry.type
class Relationship:
    """Generic relationship GraphQL type."""
    id: strawberry.ID
    subject_id: str
    predicate: str
    object_id: str
    confidence: Optional[float] = None
    source_documents: List[str] = []
    properties: Any = None # Use Any for JSON/dict


@strawberry.type
class Query:
    @strawberry.field
    def entity(self, info: Info, entity_id: str) -> Optional[Entity]:
        """Retrieve a single entity by its ID."""
        storage = info.context["storage"]
        entity_model = storage.get_entity(entity_id=entity_id)
        if entity_model:
            return Entity(
                entity_id=entity_model.entity_id,
                entity_type=entity_model.entity_type,
                name=entity_model.name,
                status=entity_model.status,
                confidence=entity_model.confidence,
                usage_count=entity_model.usage_count,
                source=entity_model.source,
                synonyms=entity_model.synonyms,
                properties=entity_model.properties,
            )
        return None

    @strawberry.field
    def entities(
        self,
        info: Info,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Entity]:
        """List all entities with pagination."""
        storage = info.context["storage"]
        entity_models = storage.get_entities(limit=limit, offset=offset)

        return [
            Entity(
                entity_id=e.entity_id,
                entity_type=e.entity_type,
                name=e.name,
                status=e.status,
                confidence=e.confidence,
                usage_count=e.usage_count,
                source=e.source,
                synonyms=e.synonyms,
                properties=e.properties,
            )
            for e in entity_models
        ]

    @strawberry.field
    def relationship(
        self,
        info: Info,
        subject_id: str,
        predicate: str,
        object_id: str,
    ) -> Optional[Relationship]:
        """Retrieve a single relationship by its triple."""
        storage = info.context["storage"]
        relationship_model = storage.get_relationship(
            subject_id=subject_id,
            predicate=predicate,
            object_id=object_id,
        )
        if relationship_model:
            return Relationship(
                id=relationship_model.id,
                subject_id=relationship_model.subject_id,
                predicate=relationship_model.predicate,
                object_id=relationship_model.object_id,
                confidence=relationship_model.confidence,
                source_documents=relationship_model.source_documents,
                properties=relationship_model.properties,
            )
        return None

    @strawberry.field
    def relationships(
        self,
        info: Info,
        subject_id: Optional[str] = None,
        predicate: Optional[str] = None,
        object_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Relationship]:
        """Find relationships based on subject, predicate, or object."""
        storage = info.context["storage"]
        relationship_models = storage.find_relationships(
            subject_id=subject_id,
            predicate=predicate,
            object_id=object_id,
            limit=limit,
        )

        return [
            Relationship(
                id=r.id,
                subject_id=r.subject_id,
                predicate=r.predicate,
                object_id=r.object_id,
                confidence=r.confidence,
                source_documents=r.source_documents,
                properties=r.properties,
            )
            for r in relationship_models
        ]