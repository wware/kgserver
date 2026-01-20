# Flexible server for knowledge graphs

This repository contains a **domain-neutral knowledge graph server**.

Important architectural note:

- The server does **not** ingest raw documents directly.
- Domain-specific ingestion pipelines produce rich JSON artifacts internally.
- A finalized, validated bundle is exported and loaded by the server as-is at startup.

If you are working on ingestion, storage, or bundle loading, read:
➡️ **docs/architecture.md — Producer artifacts vs server bundle**

## How to run this thing

### Local testing (SQLite)

```bash
BUNDLE_PATH=/home/wware/S.zip uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

### With Docker Compose (PostgreSQL)

Update docker-compose.yml to add bundle volume and environment variable.
This assumes you've packaged a bundle `S.zip` with the info for your
knowledge graph.

```yaml
api:
    environment:
        DATABASE_URL: postgresql://postgres:postgres@postgres:5432/medlit
        BUNDLE_PATH: /bundle/S.zip
    volumes:
        - /home/wware/S.zip:/bundle/S.zip:ro
```

Then run:
```bash
docker-compose up --build
```

### API endpoints:

- Health: `GET /health`
- Entities: `GET /api/v1/entities?limit=10`
- Relationships: `GET /api/v1/relationships?limit=10`
- GraphQL: `POST /graphql`
- GraphiQL UI: `GET /graphiql`
- API Docs: `GET /docs`

## Bundle format

Let's peek inside a working bundle, from our
Sherlock Holmes example in the `wware/kgraph` repository.

```bash
$ unzip -l ~/S.zip
Archive:  /home/wware/S.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
        0  2026-01-20 15:56   sherlock_bundle/
    11051  2026-01-20 15:56   sherlock_bundle/relationships.jsonl
      499  2026-01-20 15:56   sherlock_bundle/manifest.json
     5239  2026-01-20 15:56   sherlock_bundle/entities.jsonl
---------                     -------
    16789                     4 files
```

### What is intentionally *not* in a bundle

Bundles do not include:
- Raw source documents
- NLP artifacts (NER spans, embeddings, token offsets)
- Alias resolution logic
- Ontology definitions

Those belong to producer pipelines.

### `manifest.json`

```json
{
  "bundle_version": "v1",
  "bundle_id": "93f67722-203c-487c-8927-b530b7100c2f",
  "domain": "sherlock",
  "label": "sherlock-holmes-stories",
  "created_at": "2026-01-20T20:56:04.272851+00:00",
  "entities": {
    "path": "entities.jsonl",
    "format": "jsonl"
  },
  "relationships": {
    "path": "relationships.jsonl",
    "format": "jsonl"
  },
  "metadata": {
    "entity_count": 21,
    "relationship_count": 42,
    "description": "Knowledge graph bundle of Sherlock Holmes stories"
  }
}
```

### `entities.jsonl`
```json
{"entity_id":"holmes:story:AScandalInBohemia","entity_type":"story","name":"A Scandal In Bohemia","status":"canonical","confidence":1.0,"usage_count":1,"created_at":"2026-01-20T20:56:03.338354+00:00","source":"sherlock:curated","properties":{}}
{"entity_id":"holmes:char:SherlockHolmes","entity_type":"character","name":"Mr. Sherlock Holmes","status":"canonical","confidence":0.95,"usage_count":731,"created_at":"2026-01-20T20:56:03.338446+00:00","source":"sherlock:curated","properties":{}}
{"entity_id":"holmes:char:MrsHudson","entity_type":"character","name":"The landlady","status":"canonical","confidence":0.95,"usage_count":4,"created_at":"2026-01-20T20:56:03.338590+00:00","source":"sherlock:curated","properties":{}}
{"entity_id":"holmes:loc:BakerStreet221B","entity_type":"location","name":"Baker Street","status":"canonical","confidence":0.95,"usage_count":27,"created_at":"2026-01-20T20:56:03.338620+00:00","source":"sherlock:curated","properties":{}}
{"entity_id":"holmes:char:IreneAdler","entity_type":"character","name":"Irene Adler","status":"canonical","confidence":1.0,"usage_count":53,"created_at":"2026-01-20T20:56:03.338682+00:00","source":"sherlock:curated","properties":{}}
{"entity_id":"holmes:char:JohnWatson","entity_type":"character","name":"Watson","status":"canonical","confidence":0.8,"usage_count":124,"created_at":"2026-01-20T20:56:03.339025+00:00","source":"sherlock:curated","properties":{}}
...lots more...
```

Each entity looks like this.
```json
{
    "entity_id": "holmes:story:AScandalInBohemia",
    "entity_type": "story",
    "name": "A Scandal In Bohemia",
    "status": "canonical",
    "confidence": 1.0,
    "usage_count": 1,
    "created_at": "2026-01-20T20:56:03.338354+00:00",
    "source": "sherlock:curated",
    "properties": {}
}
```

Notes:

- Fields shown at the top level are part of the **server schema**.
- `properties` is an **opaque JSON object**:
  - Its contents are not interpreted by the server
  - It may vary freely by domain
  - It may be empty

### `relationships.jsonl`
```json
{"subject_id":"holmes:char:SherlockHolmes","object_id":"holmes:story:AScandalInBohemia","predicate":"appears_in","confidence":0.95,"source_documents":["8480d4da-80da-48c8-ada4-e48aff54d2a6"],"created_at":"2026-01-20T20:56:03.339275+00:00","properties":{}}
{"subject_id":"holmes:char:MrsHudson","object_id":"holmes:story:AScandalInBohemia","predicate":"appears_in","confidence":0.95,"source_documents":["8480d4da-80da-48c8-ada4-e48aff54d2a6"],"created_at":"2026-01-20T20:56:03.339297+00:00","properties":{}}
{"subject_id":"holmes:char:IreneAdler","object_id":"holmes:story:AScandalInBohemia","predicate":"appears_in","confidence":0.95,"source_documents":["8480d4da-80da-48c8-ada4-e48aff54d2a6"],"created_at":"2026-01-20T20:56:03.339303+00:00","properties":{}}
{"subject_id":"holmes:char:JohnWatson","object_id":"holmes:story:AScandalInBohemia","predicate":"appears_in","confidence":0.95,"source_documents":["8480d4da-80da-48c8-ada4-e48aff54d2a6"],"created_at":"2026-01-20T20:56:03.339306+00:00","properties":{}}
{"subject_id":"holmes:char:IreneAdler","object_id":"holmes:char:JohnWatson","predicate":"co_occurs_with","confidence":0.7,"source_documents":["8480d4da-80da-48c8-ada4-e48aff54d2a6"],"created_at":"2026-01-20T20:56:03.370337+00:00","properties":{"co_occurrence_count":1}}
{"subject_id":"holmes:char:JohnWatson","object_id":"holmes:char:MrsHudson","predicate":"co_occurs_with","confidence":0.9,"source_documents":["8480d4da-80da-48c8-ada4-e48aff54d2a6"],"created_at":"2026-01-20T20:56:03.370389+00:00","properties":{"co_occurrence_count":3}}
{"subject_id":"holmes:char:IreneAdler","object_id":"holmes:char:SherlockHolmes","predicate":"co_occurs_with","confidence":0.95,"source_documents":["8480d4da-80da-48c8-ada4-e48aff54d2a6"],"created_at":"2026-01-20T20:56:03.370400+00:00","properties":{"co_occurrence_count":5}}
...lots more...
```

Each relationship looks like this.
```json
{
    "subject_id": "holmes:char:SherlockHolmes",
    "object_id": "holmes:story:AScandalInBohemia",
    "predicate": "appears_in",
    "confidence": 0.95,
    "source_documents": [
        "8480d4da-80da-48c8-ada4-e48aff54d2a6"
    ],
    "created_at": "2026-01-20T20:56:03.339275+00:00",
    "properties": {}
}
```

Relationships are directed: `subject_id --predicate--> object_id`.

### Bundle contract (important)

The bundle format is a **strict, validated contract** between producer pipelines and the server.

- Bundles **must already be normalized** when exported.
- The server **does not rename fields**, infer structure, or reinterpret metadata.
- If a bundle does not match the declared format, **the server should fail fast at startup**.

Producer pipelines are responsible for:
- Flattening fields to their canonical locations
- Choosing stable identifiers
- Ensuring all required fields are present

The server’s responsibility is limited to validation, loading, and querying.

## **OOPS** -- stuff I forgot, add it later

**mkdocs build at startup**

Conceptually, this lives **entirely outside the bundle contract**.

Think in three layers:

### 1. **Bundle (immutable input)**

* Contains:

  * graph data (`entities.jsonl`, `relationships.jsonl`)
  * optional docs sources (`docs/*.md`, images, etc.)
* Is treated as **read-only**
* Is validated, not transformed

### 2. **Startup build step (derived artifacts)**

* On server startup:

  * If `docs` is present in the manifest:

    * Run `mkdocs build`
    * Output to a **server-managed directory**, e.g.:

      ```
      /var/lib/kgraph/bundles/<bundle_id>/site/
      ```
* This output is:

  * derived
  * disposable
  * cacheable
  * safe to delete/rebuild

### 3. **Serving layer**

* Static site server mounts:

  ```
  /docs → /var/lib/kgraph/bundles/<bundle_id>/site/
  ```
* No knowledge of mkdocs internals needed after startup

This preserves:

* immutability of the bundle
* determinism (same bundle → same site)
* a clean separation of concerns

---

## Why *not* think about it right now (you were right)

Because it adds:

* subprocess management
* filesystem layout decisions
* failure modes (what if docs build fails?)
* caching policy questions

None of that should pollute:

* the bundle schema
* ingestion logic
* graph querying

So parking it was the right instinct.

---

## One thing you *might* jot down now (so Future You doesn’t curse Past You)

Add a **one-line TODO comment** in `docs/architecture.md`, something like:

> **TODO:** At server startup, optional documentation sources included in a bundle may be compiled (e.g. via `mkdocs build`) into derived static artifacts served by the API. These derived artifacts are not part of the bundle itself.

That’s enough to:

* preserve intent
* avoid premature design
* keep the boundary clear

---

Nothing in:

* your README
* the bundle format
* the “fail fast” rule
* the producer/server split

needs to change to support this later.
