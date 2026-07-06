import os
import yaml
from core.orchestrator import LoomOrchestrator
from emitters.json_emitter import JsonEmitter


def run_markdown_example():
    print("--- Running Example 01: Multi-Modal Markdown Parsing ---")

    # 1. Provide inline mock sample mimicking an architectural README
    markdown_content = """# Data Ingestion Engine

The Ingestion Worker acts as the core entry point for incoming streams. It handles socket allocation and passes payloads straight down to raw message buffers.

```java
public class IngestionWorker {
    public void openSocket() {
        System.out.println("Listening on port 8080...");
    }
}
```"""

    # 2. Instantiate Loom (Loads internal defaults.yml automatically)
    orchestrator = LoomOrchestrator()
    json_emitter = JsonEmitter()

    # 3. Process the content
    chunks = orchestrator.process_file(
        file_path="README.md",
        file_content=markdown_content,
        emitter=json_emitter
    )

    print(chunks)


if __name__ == "__main__":
    run_markdown_example()