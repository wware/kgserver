# API Architecture: Multi-Protocol Service Design

## Overview

The Medical Knowledge Graph API is a **read-only query service** designed to support multiple client types and use cases through a unified FastAPI service exposing three complementary protocols:

- **GraphQL** - Complex graph queries with flexible field selection
- **REST** - Simple queries and legacy client support

All protocols are served from a single FastAPI application, providing a self-documenting, production-ready API service.

**Note**: This is a **query-only API**. Data ingestion happens through separate batch pipelines (not exposed via public API).

## Endpoint Structure

```
example.com/
├── /docs                    # FastAPI auto-generated documentation (Swagger UI)
│                            # Documents all REST endpoints automatically
│
├── /graphql                 # GraphQL-over-HTTP (read-only, spec-compliant)
│   ├── POST                 # Complex queries (avoids URL length limits)
│   └── GET                  # Simple queries (cacheable)
│
├── /graphiql                # GraphiQL interactive UI (browser-based query builder)
│                            # Includes dropdown menu with example queries
│                            # Available in development, optional in production
│
└── /api/v1/                 # Traditional REST endpoints (read-only)
    ├── /treatments          # Find treatments for diseases
    ├── /entities            # Entity queries
    ├── /relationships       # Relationship queries
    └── /search              # Search and discovery
```

## Why This Works Well

### 1. **Self-Documenting APIs**

Each protocol provides built-in documentation:

- **REST**: `/docs` endpoint (FastAPI Swagger UI) automatically documents all REST endpoints with request/response schemas
- **GraphQL**: `/graphiql` provides interactive schema exploration, query building, and documentation via GraphiQL with example queries dropdown

This satisfies the CLAUDE.md requirement for self-documenting services (like FastAPI's /docs endpoint).

### 2. **Each Protocol Serves Its Purpose**

**GraphQL** (`/graphql`):
- Complex multi-hop graph traversals (drug → protein → gene → disease)
- Flexible field selection (clients request exactly what they need)
- Batch queries (fetch multiple entity types in one request)
- Perfect for web/mobile UIs and research tools

**REST** (`/api/v1/...`):
- Simple read queries (single entity lookups, basic filters)
- Standard HTTP caching (GET requests)
- Legacy client support
- Quick lookups without GraphQL overhead

**All protocols are read-only.** Data ingestion happens through separate batch pipelines.

### 3. **Production-Ready Standards**

- **GraphQL-over-HTTP**: Follows the [formal specification](https://graphql.github.io/graphql-over-http/draft/) (RFC track)
- **FastAPI**: Industry-standard Python web framework with excellent async support

### 4. **Single Deployment Unit**

All protocols run in one FastAPI application:
- Shared PostgreSQL connection pool
- Shared business logic (GraphQuery client)
- Shared authentication/authorization middleware
- Unified logging and monitoring
- Single Docker container (simpler deployment)

### 5. **Compliant with Project Requirements**

From `CLAUDE.md`:
- ✅ **Self-documenting** - `/docs`, `/graphiql` (GraphiQL with example queries)
- ✅ **Clear APIs** - Each protocol has distinct responsibilities
- ✅ **Docker-compose prototyping** - Single service container
- ✅ **AWS deployment ready** - Standard HTTP service
- ✅ **Separation of concerns** - APIs accessed by static resources

## Design: Read-Only API

**Architectural Decision**: The entire public API is read-only. No write operations are exposed via GraphQL or REST.

**Rationale**:

1. **Separation of concerns**
   - **Query API**: Public-facing, read-only, for researchers and applications
   - **Ingestion pipelines**: Internal, write-only, for processing papers and extracting knowledge

2. **Security benefits**
   - Zero risk of unauthorized data modification via API
   - No need for write authentication/authorization in API layer
   - Smaller attack surface (read-only APIs can't corrupt data)
   - Easier to audit (no write endpoints to secure)

3. **Read-heavy workload**
   - Medical knowledge graphs are read-heavy (researchers querying, not authoring)
   - Primary use cases: drug discovery, differential diagnosis, mechanism exploration
   - Most operations are traversals, searches, and analytics
   - Writes happen in controlled batch ingestion processes

4. **Simpler implementation**
   - No mutation resolvers (GraphQL)
   - No POST/PUT/DELETE endpoints (REST)
   - No write transaction handling
   - Easier caching strategy (all responses cacheable)
   - No write-after-write consistency concerns

5. **Data quality control**
   - Knowledge graph data comes from peer-reviewed papers (vetted sources)
   - Ingestion involves complex NLP, entity resolution, validation
   - Not suitable for ad-hoc API writes
   - Batch pipelines ensure data quality and consistency

**Where writes happen**:
- **Batch ingestion pipelines**: Internal processes that parse papers, extract entities/relationships, validate, and load into database
- **Admin tools**: Internal-only interfaces for curating and maintaining the knowledge graph
- **Not exposed via public API**: Researchers query the knowledge graph but don't modify it directly

## Protocol Comparison

| Protocol | Best For | Read/Write | Standardization | Client Support |
|----------|----------|------------|-----------------|----------------|
| **GraphQL** | Complex multi-hop queries, flexible field selection | **Read-only** | ✅ Formal spec (RFC track) | Excellent (Apollo, Relay, urql) |
| **REST** | Simple queries, legacy clients, standard HTTP caching | **Read-only** | ✅ Mature standard | Universal |

**All protocols are read-only.** Data modification happens through internal batch ingestion pipelines.

## Rate Limiting and Middleware

### Middleware Architecture

FastAPI provides excellent middleware support for cross-cutting concerns:

```python
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Apply rate limits based on user, IP, or API key
    response = await call_next(request)
    return response

# Authentication middleware
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Verify JWT tokens, API keys, etc.
    response = await call_next(request)
    return response

# Logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # Log requests, responses, timing
    response = await call_next(request)
    return response
```

### Rate Limiting Strategies

**By User/API Key**:
```python
# Different limits for different user tiers
RATE_LIMITS = {
    "free": "100/hour",
    "pro": "1000/hour",
    "enterprise": "10000/hour"
}
```

**By Endpoint**:
```python
# GraphQL queries can be expensive (multi-hop traversals)
@app.post("/graphql")
@limiter.limit("500/hour")
async def graphql_query(): ...

# REST queries are simpler, more permissive
@app.get("/api/v1/entities")
@limiter.limit("1000/hour")
async def get_entities(): ...

@app.get("/api/v1/treatments/{disease}")
@limiter.limit("1000/hour")
async def get_treatments(): ...
```

**By Protocol**:
```python
# GraphQL queries can be expensive (multi-hop traversals)
@app.post("/graphql")
@limiter.limit("500/hour")
async def graphql_endpoint(): ...

# REST queries are cheaper (single entity lookups)
@app.get("/api/v1/entities/{id}")
@limiter.limit("1000/hour")
async def get_entity(): ...
```

**By Complexity**:
```python
# Semantic search is expensive (vector operations)
@app.post("/api/v1/search/semantic")
@limiter.limit("100/hour")
async def semantic_search(): ...

# Simple lookups are cheap
@app.get("/api/v1/entities/{id}")
@limiter.limit("2000/hour")
async def get_entity(): ...
```

### Middleware Applies to All Protocols

Because all protocols run through FastAPI, **one middleware layer** handles:
- Rate limiting (per user, IP, or API key)
- Authentication (JWT, API keys, OAuth) - if API requires auth
- CORS (cross-origin requests)
- Request logging
- Error handling
- Metrics collection (Prometheus, DataDog)
- Query complexity analysis (prevent expensive queries)

This is much simpler than managing separate middleware for separate services.

**Note on read-only security**: Since the API is read-only, authentication/authorization can focus on:
- Rate limiting abusive clients
- Tracking usage for billing/quotas
- Access control for sensitive datasets (if applicable)
- **Not** on preventing data corruption (impossible via read-only API)

## Implementation Notes

### GraphQL-over-HTTP Compliance

The implementation follows the [GraphQL-over-HTTP specification](https://graphql.github.io/graphql-over-http/draft/) for read-only queries:

- ✅ POST requests for complex queries (avoids URL length limits)
- ✅ GET requests for simple queries (cacheable)
- ✅ **No mutations** - GraphQL schema defines only Query type (no Mutation type)
- ✅ Support `application/graphql-response+json` media type
- ✅ Support `application/json` for legacy clients
- ✅ URL path ends with `/graphql`

**Deviation from spec**: The spec allows mutations, but we intentionally omit them. This is a **query-only API** - data modification happens through separate internal ingestion pipelines.

### Technology Stack

**Web Framework**: FastAPI
- Async/await support (high concurrency)
- Automatic OpenAPI/Swagger documentation
- Pydantic integration (matches domain models)
- Excellent middleware support

**GraphQL**: Strawberry (recommended) or Graphene
- Native FastAPI integration
- Pydantic model support
- Type-safe schema definition
- GraphQL Playground included

**Database**: PostgreSQL with pgvector
- Relational data + vector search
- Excellent with SQLModel/SQLAlchemy
- Production-ready (ACID compliance)

_The EntityCollection is used only during the ingestion phase so no specific provision is needed for it here. Entity canonical IDs are stored in one of the PostgreSQL tables._

## Docker Compose Configuration

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: medlit
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: .
    command: uvicorn main:app --host 0.0.0.0 --port 8000
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/medlit
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    volumes:
      - ./:/app

volumes:
  pgdata:
```

Access the service:
- API docs: http://localhost:8000/docs (FastAPI Swagger UI)
- GraphQL IDE: http://localhost:8000/graphiql (GraphiQL with example queries dropdown)
- GraphQL endpoint: http://localhost:8000/graphql (POST or GET)
- REST endpoints: http://localhost:8000/api/v1/... (GET only)

**Note**: All endpoints are read-only. For data ingestion, see the `ingest/` directory for batch pipeline tools.

## Future Considerations

### If Real-Time Becomes Critical

Consider adding:
1. **Redis** for pub-sub messaging
2. **WebSocket support** for GraphQL subscriptions
3. **Message queue** (RabbitMQ, Kafka) for event streaming

### If Scale Requires Separation

If different protocols need independent scaling:
1. Split into separate services (api-gateway pattern)
2. Shared database with separate connection pools
3. Load balancer routes by path (`/graphql`, `/api`)

### If Multi-Region Deployment

Consider:
1. **API Gateway** (AWS API Gateway, Kong) for routing
2. **CDN caching** for read-heavy REST endpoints
3. **GraphQL query caching** (Apollo Server, Redis)
4. **Database read replicas** for geographic distribution

## References

- [GraphQL-over-HTTP Specification](https://graphql.github.io/graphql-over-http/draft/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Strawberry GraphQL](https://strawberry.rocks/)
- [Project Architecture](./ARCHITECTURE.md)
- [Storage Layer](./storage/README.md)
- [Query Interface](./query/README.md)
