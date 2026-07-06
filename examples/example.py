from core.orchestrator import LoomOrchestrator

# Initialize the engine (using convention/defaults out-of-the-box)
loom = LoomOrchestrator()

code_file = """
/**
 * Calculates user accounts
 */
public class AccountManager {
    public void deploy() {
        System.out.println("Deploying...");
    }
}
"""

# Process the file cleanly
nodes = loom.process_file("AccountManager.java", code_file)

for node in nodes:
    print(f"[{node.node_type}] Lines {node.start_line}-{node.end_line}: {node.content}")