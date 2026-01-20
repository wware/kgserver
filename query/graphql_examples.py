"""
Example GraphQL queries for the Knowledge Graph API.

These queries are displayed in the GraphiQL interface to help users get started.
"""

EXAMPLE_QUERIES = {
    "Get Entity by ID": """# Retrieve a specific entity by its ID
query GetEntity {
  entity(entityId: "holmes:char:JohnWatson") {
    entityId
    name
    entityType
    synonyms
    properties
  }
}""",
    "Search Entities": """# Search for entities with pagination
query SearchEntities {
  entities(limit: 5, offset: 0) {
    entityId
    name
    entityType
  }
}""",
    "Find Relationships": """# Find relationships (e.g., predicate "co_occurs_with")
query FindRelationships {
  relationships(
    predicate: "co_occurs_with"
    limit: 5
  ) {
    id
    subjectId
    predicate
    objectId
    confidence
    sourceDocuments
    properties
  }
}""",
    "Filter Relationships by Subject": """# Find all relationships for a specific entity
query FilterBySubject {
  relationships(
    subjectId: "holmes:char:JohnWatson"
    limit: 5
  ) {
    id
    subjectId
    predicate
    objectId
  }
}""",
    "Multiple Queries": """# Get an entity and its relationships in one request
query EntityWithRelationships {
  entity(entityId: "holmes:char:JohnWatson") {
    entityId
    name
    entityType
  }
  relationships(
    subjectId: "holmes:char:JohnWatson"
    limit: 5
  ) {
    id
    subjectId
    predicate
    objectId
  }
}""",
}

# Default query shown when GraphiQL first loads
DEFAULT_QUERY = EXAMPLE_QUERIES["Search Entities"]
