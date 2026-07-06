from core.orchestrator import LoomOrchestrator
from emitters.json_emitter import JsonEmitter

def run_log_clustering_example():
    print("\n--- Running Example 03: Log Stack-Trace Clustering ---")

    # Simulating standard system outputs interrupted by a massive multiline trace
    log_stream = """2026-07-06 09:40:01 [INFO] com.loom.engine.Runner - Initialization complete.
2026-07-06 09:40:02 [INFO] com.loom.engine.Runner - Listening for active telemetry pipelines.
2026-07-06 09:40:05 [ERROR] com.loom.engine.Buffer - Critical memory allocations collapsed!
java.lang.NullPointerException: Cannot invoke pipeline emitter array because target is null
    at com.loom.engine.Buffer.flushActiveGates(Buffer.java:42)
    at com.loom.engine.Buffer.processPayload(Buffer.java:18)
    at com.loom.engine.Runner.executeLoop(Runner.java:104)
2026-07-06 09:40:06 [INFO] com.loom.engine.Runner - Attempting automatic warm-restart protocols."""

    orchestrator = LoomOrchestrator()
    json_emitter = JsonEmitter()

    chunks = orchestrator.process_file(
        file_path="sys_output.log",
        file_content=log_stream,
        emitter=json_emitter
    )

    print(chunks)

if __name__ == "__main__":
    run_log_clustering_example()