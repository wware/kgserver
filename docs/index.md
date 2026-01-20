# Knowledge Graph Server

## Mental model (read this first)

This project intentionally separates **knowledge extraction** from **knowledge serving**.

- Ingestion pipelines (e.g. Sherlock, med-lit) produce **domain-specific JSON artifacts** that are the single source of truth.
- A deterministic export step produces a **domain-neutral bundle**.
- The KG server loads that bundle at startup and serves it from Postgres as a materialized index.

If you are confused about what data lives where, or why Postgres can be rebuilt at any time, read:

➡️ **[Producer artifacts vs server bundle](architecture.md#producer-artifacts-vs-server-bundle)**

Everything else builds on that distinction.

---

I’ll stay at the **architectural / product-review** level as requested and not start coding. I’ll structure this as:

1. What you have (as I understand it)
2. What’s strong / already well thought-out
3. Friction points when splitting into its own repo
4. Thoughts on Ollama + Streamlit + MCP direction
5. A suggested “shape” for the new repo (no code, just intent)

---

## 1. What you have now (high-confidence understanding)

From the zip contents, this repo is already doing **a lot of the right things**:

### Runtime stack

* **docker-compose** with:

  * Postgres (persistent storage)
  * FastAPI app container
  * Ollama container (local LLM inference)
* The server is **read-only** from a data perspective (important simplification).

### Application structure

* `query/` is effectively the **application package**

  * `server.py` boots FastAPI
  * `routers/`

    * REST API
    * GraphQL API
    * MCP-style API
    * Custom GraphiQL UI
  * `storage_factory.py` abstracts storage backend
  * `graphql_schema.py` clearly separated (good)
* Client + examples exist but are not entangled with the server runtime.

### Documentation

* This is the biggest pleasant surprise:

  * `docs/` is already split into:

    * user guide
    * developer guide
    * research notes
  * There is *thinking* here, not just usage notes.
* There are explicit architecture and epistemology notes, which puts this well above “toy project” level.

---

## 2. What’s already strong (and should be preserved)

### A. The API surface is plural, not confused

You have **three distinct interaction modes**, and they are cleanly separated:

* REST (boring, reliable)
* GraphQL (expressive querying)
* MCP-like / agent-facing API (experimental, future-facing)

That’s exactly the right posture for a KG server intended to be extended.

### B. Docker-first is the right call

Given:

* Postgres
* Ollama
* FastAPI
* (future) Streamlit

Trying to make this “pip-installable” would be a mistake. Treating Docker as the *primary interface* is correct.

### C. Read-only constraint is a gift

You should lean into this more explicitly.

Read-only means:

* No auth required initially
* No migration UX
* No write contention
* No partial failure semantics

This dramatically simplifies correctness and makes this a perfect **query / exploration / reasoning server**.

---

## 3. Friction points when giving it its own repo

These are not criticisms — they’re *natural seams* that appear when a project graduates.

### A. Naming ambiguity: “query”

Right now, `query/` means:

* the server
* the API
* the application package

In a standalone repo, that name will feel increasingly wrong.

You don’t need to rename it today, but mentally you should start treating it as:

> “the knowledge graph server”

Even if the directory stays `query/`, your **README and mental model** should shift.

---

### B. Docs are good — but they’re repo-internal, not user-facing (yet)

You already have:

* `docs/user-guide/quickstart.md`
* `DOCKER_SETUP.md`
* `DOCKER_COMPOSE_GUIDE.md`

But there is no *single* document that answers:

> “I just cloned this repo. What do I do first, and why would I want this?”

That’s the README gap — not missing information, but missing **orientation**.

---

### C. Ollama’s role is unclear (by design, but needs framing)

Right now:

* Ollama exists
* Some APIs gesture toward agent use
* MCP router exists

But from a reader’s perspective:

* Is Ollama *required*?
* Is it optional?
* Is it “experimental but kept around”?

This is fine technically, but the **repo needs to say this explicitly**, or users will infer the wrong thing.

---

## 4. Ollama + Streamlit + MCP: you’re on a good path

Your instinct here is solid.

### Ollama

Keeping it **even in a read-only server** makes sense if you frame it as:

* Optional
* Local
* Used for:

  * natural-language-to-query experiments
  * explanation generation
  * MCP experimentation

Do *not* frame it as “the core of the server”. It’s an **adjunct reasoning layer**.

### Streamlit

Streamlit is a great choice here because:

* It lowers friction for experimentation
* It makes MCP demos tangible
* It keeps UI separate from API correctness

I would treat Streamlit as:

> “A sandbox UI for humans and agents to poke at the graph.”

Not as a “frontend”.

### MCP

This repo is *perfectly positioned* to become:

> “What an MCP server for a knowledge graph actually looks like.”

Even if you never fully formalize it, the presence of:

* a KG
* a query API
* an LLM
* a constrained interface

…is exactly the right playground.

---

## 5. Suggested shape for the standalone repo (conceptual only)

No renames required yet — this is about *framing*.

### Repo identity

This should read as:

> **A read-only, query-focused knowledge graph server with multiple API surfaces and optional LLM augmentation.**

Everything else flows from that.

### README should answer, in order:

1. What this server *is*
2. What it is *not*
3. What you can do with it in 5 minutes
4. What you can experiment with if you have more time
5. Where the sharp edges / experimental bits are

### Ollama framing (important)

Something like:

* “Ollama is included for local reasoning experiments”
* “The server functions fully without it”
* “MCP and Streamlit integrations assume it is running”

This avoids future confusion.

---

## Bottom line

You are **well past** the “should this be its own repo?” threshold.

My high-level take:

* The technical foundation is solid
* The conceptual framing is strong
* The next step is **orientation, not refactoring**

If you want, next time we can:

* Draft the README for *this* repo the same way we did for Sherlock
* Or map how this server could *consume* Sherlock-style domain packages
* Or talk through how MCP *should* constrain queries in a KG context

But for now: yes, this is worth splitting, and you’re making good calls.

# Next idea

> map how this server could consume Sherlock-style domain packages

My thought on this is that the server mounts to a data directory containing JSON files:
* a https://json-schema.org/ style schema describing entities, relationships, etc -- unnecessary? data files could just be pre-validated, links are whatever the server finds there
* a manifest of the graph data files, markdown files, embeddings, metadata, must identify which file is the entity collection
* the data files themselves (all of the above)
This should work for whatever KG arises in at least the near future. The storage mechanism should probably stick with Postgres for now because it's working. If it's not a burden, keep the Jupyter notebook service, very handy for tinkering.

Let's assume the whole thing runs in a single container:
$ docker run ... -v ./bundle:/bundle ...
and the server loads bundle at startup (or on demand) into Postgres, but this means the same container has to hold Postgres PLUS the app code PLUS possibly Ollama PLUS ... worry a bit about feasibility.

The Sherlock code can produce this bundle of static files (with validation as needed). Maybe it gets a script that produces the bundle and does the docker-run command, but this should be a very small addition to what we've got from last night.

# Response

Your bundle idea is solid, and it *does* line up nicely with “Sherlock-style domain packages”: Sherlock becomes a **bundle producer**, the server becomes a **bundle consumer**.

The two things to keep straight are:

1. **Bundle format + contract** (portable, stable)
2. **Runtime topology** (single container vs compose) (practical, operational)

---

## 1) Bundle contract: what to put in `./bundle/`

### A. Do you need JSON Schema files?

Optional. I’d treat it as **nice-to-have metadata**, not something the server *requires*.

Why:

* JSON Schema is useful for tooling and validation, but your *server* can validate using its own domain-neutral rules (required keys, types, indices) and reject bad bundles.
* Enforcing a specific JSON Schema dialect/feature set turns into a maintenance tax quickly.

Best compromise:

* Bundle can include `schema/` (JSON Schema, or Pydantic-generated, whatever) for **humans and CI**.
* Server validates with its own “minimum contract” regardless.

### B. Manifest is the real cornerstone

Yes: you want a manifest that tells the server what’s inside and how to load it.

I’d make the manifest explicitly answer:

* What is this bundle? (name, version, created_at, tool that produced it)
* What collections exist? (entities, relationships, documents/markdown, embeddings)
* For each collection:

  * file paths
  * format (`jsonl`, `json`, `parquet`, `md`, etc.)
  * entity/edge types (optional)
  * primary key field name
  * counts + checksums (optional but useful)
* Compatibility:

  * a `bundle_format_version`
  * a `kgraph_version` / producer version hint

### C. Prefer JSONL for large collections

If you have even moderate-sized graphs, a single huge JSON array becomes painful.

Recommended:

* `entities.jsonl`
* `relationships.jsonl`
* optional `documents.jsonl` or `docs/` with markdown files + an index

JSONL also makes streaming load into Postgres trivial.

### D. Embeddings: keep them separate and explicit

Don’t bury embeddings inside entity records unless you’re sure you’ll always want them loaded.

Better:

* `embeddings.jsonl` keyed by `entity_id` (and maybe embedding “model” + dim)
* or `embeddings.bin` + `embeddings.index.json` if you later optimize

But keep it explicit in the manifest so the server can:

* skip embeddings entirely
* load them to Postgres
* or load to a vector index later

---

## 2) Loading model: startup vs on-demand

You basically have three modes:

### Mode 1 — “Load on startup” (simple, good for single bundle)

* Container starts
* Checks if Postgres already contains bundle `<bundle_id>`
* If not, bulk loads
* Starts API

This is easiest for “docker run -v ./bundle:/bundle”.

### Mode 2 — “Load on demand via admin endpoint” (flexible)

* API comes up
* You call `/admin/load_bundle`
* Server loads bundle into Postgres

Useful when you want to swap bundles without restarting the world.

### Mode 3 — “Preload outside the server”

* A separate loader job runs, populates Postgres
* API container runs read-only

Operationally clean, but not as “single command” friendly.

For your stated goal (“small addition”, “tinkering”), Mode 1 is the sweet spot.

---

## 3) Single container feasibility (Postgres + app + Ollama + Jupyter)

This is the part I’d *strongly* separate conceptually:

### A. Technically possible? Yes.

You can build a “kitchen sink” container that runs multiple processes:

* Postgres
* Uvicorn/FastAPI
* (optional) Ollama
* (optional) Jupyter

But then you’re signing up for:

* process supervision (s6, supervisord, runit, etc.)
* health checks per process
* log multiplexing
* bigger image
* more failure modes (“Postgres died but app lives”)
* harder upgrades (Postgres version bump becomes an app redeploy concern)

### B. Practically advisable? Usually no.

Docker’s ergonomics and failure model are much nicer when each service is one container.

### C. The best compromise for your `docker run -v ./bundle:/bundle` dream

Keep **compose** for “full stack”, but also provide a **one-liner** wrapper that feels like a single command.

Example mental model:

* “single command experience” ✅
* “single container” ❌ (unless you truly need it)

So:

* `docker compose up` runs:

  * `db` (Postgres)
  * `api` (FastAPI server)
  * `ollama` (optional profile)
  * `jupyter` (optional profile)
* `api` mounts `/bundle` and does the “load-on-start” flow
* You still get `-v ./bundle:/bundle` behavior, but without the multi-process container pain.

If you absolutely want “docker run …” as the primary interface, consider:

* A thin “api” container + “db” as a managed service (or local Postgres)
  But if your target audience is “me tinkering”, compose is going to be friendlier.

---

## 4) How Sherlock produces bundles cleanly

This fits your “small addition” goal nicely.

Add one script in Sherlock along the lines of:

* `uv run python -m examples.sherlock.scripts.bundle --out ./bundle`

  * writes:

    * `manifest.json`
    * `entities.jsonl`
    * `relationships.jsonl`
    * `docs/` (optional)
    * `embeddings.jsonl` (optional)
  * runs validation (basic, and maybe JSON Schema export if you want)

Then the KG server side just needs:

* a bundle loader that reads the manifest
* validates + bulk inserts into Postgres
* records `bundle_id`/`bundle_version` in a metadata table

That’s genuinely small and composable with what you already built.

---

## 5) One detail to decide early: identity and idempotency

You’ll thank yourself later if the manifest contains:

* `bundle_id`: stable hash of content or a UUID
* `created_at`
* `producer`: `"kgraph-sherlock"`
* `bundle_format_version`

Then loader can do:

* if DB already has `bundle_id`, skip
* else load in a transaction (or staged tables then swap)
* set “active bundle” pointer

This makes your “load at startup” safe and repeatable.

---

## Recommendation summary

* Bundle format: **manifest + JSONL collections** (+ optional schema + docs + embeddings)
* Loader: **startup load with idempotent bundle_id check**
* Runtime: keep **Postgres separate** (compose), and treat Ollama/Jupyter as **optional profiles**
* UX: still achieve your “single command” feel via a tiny wrapper script or compose profiles, without forcing a single-container multi-process system.

If you want, paste (or describe) the current Postgres schema / tables you’re using for entities/relationships, and I’ll sanity-check that it can naturally accept a bundle loader without you painting yourself into a corner.

# Next idea

I think it's probably a good idea to defer the ollama/MCP business to later. Iirc it's not really implemented right now and I'd want to mull it over and not rush it. Not urgent but should be done right when it's done. For now it's a to-do item.

# Response

That’s a *very* good instinct, and I think you’re making exactly the right call.

What you’ve just done is draw a clean architectural boundary instead of letting an interesting but half-baked idea leak into the foundation.

Here’s how I’d frame it so it stays calm and contained instead of nagging you.

---

## 1. You’re not postponing work — you’re **protecting invariants**

Right now, the server’s core invariants want to be:

* **Deterministic**
* **Read-only**
* **Schema-agnostic but contract-driven**
* **Bundle-in → query-out**

Ollama / MCP / chat interfaces *break* at least two of those:

* they introduce **stateful, probabilistic behavior**
* they blur the line between “data API” and “agent”

That doesn’t mean they’re bad — it means they deserve their own layer.

Deferring them keeps the server honest.

---

## 2. The right mental model: “capabilities, not features”

Instead of thinking:

> “The server should support Ollama / MCP / chat”

Think:

> “The server should expose enough structure that *something else* can build an MCP interface on top of it.”

That pushes you toward:

* clean query endpoints
* graph traversal APIs
* metadata introspection
* explainability (why this edge exists)

All of which are valuable *even if* you never add Ollama.

When you later add MCP:

* it becomes a **consumer** of the API, not a tentacle inside it

That’s a much healthier direction.

---

## 3. How to mark this as a TODO without polluting the design

I’d suggest exactly one of these, and no more:

### A. A README “Future Work” section

Something like:

> ### Future work
>
> * Optional MCP / chat interface powered by LLMs (e.g. Ollama)
> * Treated as a *consumer* of the graph API, not part of core server
> * Will likely live in a separate container or service

That’s enough to signal intent without commitment.

### B. A stub directory with a README

If you want something tangible but inert:

```text
llm/
└── README.md   # “Design notes for future MCP / LLM integration”
```

No code. No imports. Just a parking lot for thoughts.

---

## 4. Why this is especially wise given Sherlock

Sherlock has already taught you something important:

> Tight contracts + explicit phases beat clever integration every time.

If you rushed Ollama in now, you’d almost certainly:

* bind to a particular prompting style too early
* leak domain assumptions into the server
* regret it when MCP stabilizes or changes shape

Let Sherlock-style bundles and queries settle first.
Let the server earn the right to be *talked to*.

---

## 5. When you *do* come back to it, you’ll be in a much stronger position

Because then you’ll be able to say:

* “Here is the graph API”
* “Here is the bundle format”
* “Here is what a query can return”
* “Here is what explanation metadata looks like”

At that point, designing an MCP interface is *much* more like writing an adapter than inventing a system.

---

### Bottom line

You’re doing the hard, unglamorous work first — the part that makes everything else easier later.

Putting Ollama/MCP on ice right now is not procrastination.
It’s architectural discipline.

Mark it, park it, and move on with a clean conscience.


# Next thing

Option A + multi-container + “Jupyter later” is a very clean path.

Yep: defining the bundle contract as **Pydantic models** is perfect. Two common patterns:

* **Strict manifest model** (validated at startup)
* **Loose “data row” models** (validated as you ingest JSONL rows)

Below is a concrete, copy/paste-able *example* you can adapt. It’s intentionally “bundle v1” and read-only friendly.

```python
# bundle_schema.py
from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BundleFormat(str, Enum):
    JSON = "json"
    JSONL = "jsonl"


class FileRef(BaseModel):
    """Reference to a file in the mounted bundle directory."""
    model_config = ConfigDict(frozen=True)

    path: str = Field(..., description="Relative path within the bundle directory")
    format: BundleFormat

    @field_validator("path")
    @classmethod
    def _path_must_be_relative(cls, v: str) -> str:
        p = Path(v)
        if p.is_absolute():
            raise ValueError("path must be relative to the bundle root")
        if ".." in p.parts:
            raise ValueError("path must not contain '..'")
        return v


class IdFields(BaseModel):
    """Declare the field names used by entity and relationship rows."""
    model_config = ConfigDict(frozen=True)

    entity_id: str = "entity_id"
    entity_type: str = "entity_type"
    name: str = "name"

    subject_id: str = "subject_id"
    predicate: str = "predicate"
    object_id: str = "object_id"


class BundleManifestV1(BaseModel):
    """
    The one file the server reads first: /bundle/manifest.json
    It tells the server what data files exist and how to interpret them.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    bundle_version: Literal["v1"] = "v1"
    domain: str = Field(..., description="Human-readable domain name, e.g. 'sherlock'")
    created_at: datetime = Field(..., description="When this bundle was generated")

    # Optional but very useful for idempotent loads
    bundle_id: str = Field(
        ...,
        description="Stable identifier for this bundle build (hash or UUID)",
        examples=["sha256:..."],
    )

    id_fields: IdFields = Field(default_factory=IdFields)

    entities: FileRef
    relationships: FileRef

    documents: FileRef | None = None
    embeddings: FileRef | None = None

    # Anything else you want to preserve without schema churn
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("domain")
    @classmethod
    def _domain_nonempty(cls, v: str) -> str:
        v2 = v.strip()
        if not v2:
            raise ValueError("domain must be non-empty")
        return v2


# --- Optional row-level models for validation during ingest ---

class EntityRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")

    entity_id: str
    entity_type: str
    name: str | None = None
    status: str | None = None
    confidence: float | None = None
    usage_count: int | None = None
    created_at: datetime | None = None
    source: str | None = None
    synonyms: list[str] | None = None


class RelationshipRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")

    subject_id: str
    predicate: str
    object_id: str
    confidence: float | None = None
    source_documents: list[str] | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] | None = None
```

### How this gets used in practice

**1) At startup**

* read `/bundle/manifest.json`
* validate with `BundleManifestV1`
* check all referenced files exist under the bundle root
* load entities + relationships into Postgres

**2) For JSONL ingestion**

* stream lines
* for each line:

  * parse JSON dict
  * optionally validate with `EntityRow`/`RelationshipRow`
  * insert/upsert into Postgres

### A minimal `manifest.json` that matches this

```json
{
  "bundle_version": "v1",
  "domain": "sherlock",
  "created_at": "2026-01-20T12:00:00Z",
  "bundle_id": "sha256:deadbeef...",
  "entities": { "path": "entities.jsonl", "format": "jsonl" },
  "relationships": { "path": "relationships.jsonl", "format": "jsonl" },
  "documents": { "path": "documents.jsonl", "format": "jsonl" },
  "metadata": {
    "generator": "examples.sherlock",
    "generator_version": "0.1.0"
  }
}
```

### Notes tailored to your goals

* **Schema.json is optional.** The Pydantic manifest *is* your contract. A JSON Schema can be added later for external tooling, but you don’t need it to ship the server.
* `bundle_id` is the lever for “load-on-start, idempotent”. Store it in Postgres and no-op if already loaded.
* Keeping `EntityRow`/`RelationshipRow` with `extra="allow"` is nice early on: you can evolve fields without breaking ingestion.

If you paste a quick sketch of what your Postgres tables look like today (or how you want them to look), I’ll map this manifest cleanly onto a load process and point out the few places where “read-only + idempotent + fast startup” usually needs one extra table/index.

