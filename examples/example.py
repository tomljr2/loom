import yaml
from core.orchestrator import LoomOrchestrator
from emitters.json_emitter import JsonEmitter

# 1. Load declarative configuration file from disk
with open("../config/defaults.yml", "r", encoding="utf-8") as f:
    config_payload = yaml.safe_load(f)

# 2. Instantiate Loom with our parsed runtime properties
loom = LoomOrchestrator(user_config=config_payload)
json_emitter = JsonEmitter()

markdown_sample = """# Core Architecture

The main execution engine relies on a central tool runner.

```java
public class Tool {
    public void execute() {
        System.out.println("Running...");
    }
}
```"""

# 3. Process and Emit graph context arrays
json_output = loom.process_file(
    file_path="README.md",
    file_content=markdown_sample,
    emitter=json_emitter,
    output_path="output.json"
)

print(json_output)