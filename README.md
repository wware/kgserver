## How this project is structured

This repository contains a **domain-neutral knowledge graph server**.

Important architectural note:

- The server does **not** ingest raw documents directly.
- Domain-specific ingestion pipelines produce rich JSON artifacts internally.
- A finalized, validated **bundle** is exported and loaded by the server at startup.

If you are working on ingestion, storage, or bundle loading, read:
➡️ **docs/architecture.md — Producer artifacts vs server bundle**

