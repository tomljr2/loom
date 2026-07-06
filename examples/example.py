from core.orchestrator import LoomOrchestrator

def main():
    # Define a rich, mixed-context file to put Loom to the test.
    # This features multiple method implementations to evaluate our chunking boundaries.
    sample_java_file = """/**
 * AccountManager handles the deployment lifecycle of user profiles.
 * It ensures all configurations are validated before running.
 */
public class AccountManager {

    public void validate() {
        System.out.println("Validating account credentials...");
    }

    public void deploy() {
        System.out.println("Deploying profile to production environment...");
    }
}
"""

    # Initialize the orchestrator using default configuration rules
    loom = LoomOrchestrator()

    print("Executing Loom Pipeline (Stages 1-3)...")
    print("-" * 50)

    # Run the file end-to-end to generate context-retained chunks
    chunks = loom.process_file(file_path="AccountManager.java", file_content=sample_java_file)

    print(f"Pipeline complete. Generated {len(chunks)} high-cohesion chunk(s).\n")

    # Inspect the final output shapes
    for idx, chunk in enumerate(chunks, 1):
        print(f"=== CHUNK {idx} ===")
        print(f"ID:         {chunk.id}")
        print(f"Origin:     {chunk.origin_file}")
        print(f"Lines:      {chunk.metadata.get('start_line')} -> {chunk.metadata.get('end_line')}")
        print(f"Nodes Fused: {chunk.metadata.get('node_count')} underlying elements")
        print("-" * 30)
        print(chunk.content)
        print("=" * 50 + "\n")

if __name__ == "__main__":
    main()