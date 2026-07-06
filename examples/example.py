from core.orchestrator import LoomOrchestrator
from emitters.json_emitter import JsonEmitter

# 1. Initialize our engine
loom = LoomOrchestrator()
json_emitter = JsonEmitter()

sample_code = """
public class Tool {
    public void execute() {
        System.out.println("Running...");
    }
}
"""

# 2. Process file and trigger Stage 4 Emission directly
# This returns a clean JSON string and writes 'output.json' to disk
json_string = loom.process_file(
    file_path="Tool.java",
    file_content=sample_code,
    emitter=json_emitter,
    output_path="output.json"
)

print(json_string)