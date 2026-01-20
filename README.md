# Flexible server for knowledge graphs

This repository contains a **domain-neutral knowledge graph server**.

Important architectural note:

- The server does **not** ingest raw documents directly.
- Domain-specific ingestion pipelines produce rich JSON artifacts internally.
- A finalized, validated **bundle** is exported and loaded by the server at startup.

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
