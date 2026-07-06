from core.orchestrator import LoomOrchestrator
from emitters.json_emitter import JsonEmitter


def run_text_fusion_example():
    print("\n--- Running Example 02: Context-Aware Flat Text Fusion ---")

    # Sample technical summary with two distinct thematic shifts
    prose_content = """Methane pyrolysis represents a highly promising pathway for carbon-negative hydrogen production. By splitting gas molecules at extreme temperatures using transition metal catalysts, we can isolate pure solid carbon. This thermal process bypasses traditional combustion greenhouse emissions entirely.

    Separately, telemetry engineering profiles for Apollo-era launch instrumentation required robust hardware matrices. The control chassis utilized precision analog switches alongside physical aluminum layouts. Ground telemetry arrays tracked voltage dips uniformly across launch phases to preserve early mission data."""

    # We can pass an inline dictionary config to tighten similarity rules for pure text
    custom_config = {
        "cohesion": {
            "similarity_threshold: ": 0.85,
            "max_chunk_lines": 15
        }
    }

    orchestrator = LoomOrchestrator(config=custom_config)
    json_emitter = JsonEmitter()

    chunks = orchestrator.process_file(
        file_path="research_notes.txt",
        file_content=prose_content,
        emitter=json_emitter
    )

    print(chunks)


if __name__ == "__main__":
    run_text_fusion_example()