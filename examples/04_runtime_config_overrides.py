import json
from core.orchestrator import LoomOrchestrator


def run_config_override_example():
    print("\n--- Running Example 04: Runtime Configuration Overrides ---")

    # A markdown file with abnormally wide paragraph layout gaps
    spaced_markdown = """# System Schematics

The physical console layout relies on solid aluminum plating.


```java
public class ConsoleChassis {}
```"""

    # Create a precise runtime override payload
    overrides = {
        "cohesion": {
            "max_prose_code_gap": 6,  # Expand looking window to bridge big gaps
            "similarity_threshold": 0.90  # Enforce hyper-strict text matching boundaries
        }
    }

    # Pass the override structure straight to constructor
    orchestrator = LoomOrchestrator(config=overrides)

    # Process without emitter to receive raw python dict/object structures directly
    raw_chunks = orchestrator.process_file(
        file_path="blueprint.md",
        file_content=spaced_markdown
    )

    # Inspecting relationships to ensure the wider line gap successfully linked the graph
    print(f"Generated Chunks Count: {len(raw_chunks)}")
    for chunk in raw_chunks:
        print(f"Type: {chunk.metadata['chunk_type']} | Relations: {chunk.relations}")


if __name__ == "__main__":
    run_config_override_example()