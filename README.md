# Loom Parser

Loom is a modular, high-fidelity multi-modal parsing engine designed to transform raw, unstructured data—such as technical documentation, system logs, and source code—into a granular, graph-ready structure of `AtomicNodes`.

By decoupling file ingestion from data extraction, Loom provides a highly extensible pipeline for LLM-augmented retrieval and analytical systems.

## Key Features

* **Multi-Modal Ingestion:** Uniformly process Markdown, plain text, and source code through a centralized orchestrator.
* **AST-Driven Structural Analysis:** Uses `tree-sitter` for deep code analysis, capturing class hierarchies and method signatures to preserve semantic context.
* **Extensible Strategy Pattern:** Easily swap or stack parsing strategies (e.g., `ProseStrategy`, `LogStrategy`, `TreeSitterStrategy`) via YAML-based runtime configurations.
* **Graph-Ready Output:** Generates immutable `AtomicNode` objects enriched with metadata, line-tracking, and parent-child structural signatures.
* **Configurable Cohesion:** Control chunking behavior, similarity thresholds, and sliding window overlaps to optimize document fragmentation for RAG applications.

## Architecture Overview

Loom operates through a multi-stage pipeline:

1.  **Lexer/Zone Generation:** Identifies the file type and segments the file into logical zones (e.g., separating code blocks from narrative text).
2.  **Strategy Extraction:** Applies specialized strategies to each zone to produce high-granularity `AtomicNodes`.
3.  **Emitter Layer:** Converts the resulting nodes into desired formats (JSON, DB entries, or direct Python objects) for downstream consumption.

## Configuration

Loom defaults are loaded from `defaults.yml`, but you can inject runtime overrides directly into the `LoomOrchestrator` constructor:

```python
overrides = {
    "cohesion": {
        "max_prose_code_gap": 6,
        "similarity_threshold": 0.90
    }
}
orchestrator = LoomOrchestrator(config=overrides)
```

## Quick Start
```python
from core.orchestrator import LoomOrchestrator
from emitters.json_emitter import JsonEmitter

# Initialize
orchestrator = LoomOrchestrator()

# Process
chunks = orchestrator.process_file(
    file_path="example.md",
    content="...",
    emitter=JsonEmitter()
)
```

Loom is designed for developers building the next generation of context-aware AI agents.