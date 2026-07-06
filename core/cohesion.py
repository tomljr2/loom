import re
from typing import List, Dict, Any
from core.models import AtomicNode, Chunk


class CohesionEngine:
    """
    Stage 3: Analyzes a chronological sequence of AtomicNodes and fuses
    them into larger, context-retained Chunks using sliding threshold rules.
    """

    def __init__(self, similarity_threshold: float = 0.80, max_chunk_lines: int = 50):
        self.similarity_threshold = similarity_threshold
        self.max_chunk_lines = max_chunk_lines

    def fuse_nodes(self, file_path: str, nodes: List[AtomicNode]) -> List[Chunk]:
        """
        Groups adjacent AtomicNodes into final semantic Chunks based on
        structural boundaries and content similarity.
        """
        if not nodes:
            return []

        chunks = []
        current_batch = [nodes[0]]

        for next_node in nodes[1:]:
            current_node = current_batch[-1]

            # Rule 1: Structural Boundary Safeguard (Max line constraints)
            total_lines_projected = next_node.end_line - current_batch[0].start_line
            if total_lines_projected > self.max_chunk_lines:
                chunks.append(self._commit_chunk(file_path, current_batch))
                current_batch = [next_node]
                continue

            # Rule 2: Multi-Modal Affinity (If code and prose touch, we lean toward joining)
            if current_node.node_type != next_node.node_type:
                # If they are tight neighbors (within 2 lines), structurally fuse them
                if next_node.start_line - current_node.end_line <= 2:
                    current_batch.append(next_node)
                else:
                    chunks.append(self._commit_chunk(file_path, current_batch))
                    current_batch = [next_node]
                continue

            # Rule 3: Structural Code Boundary (NEW)
            # If both are code blocks/methods, they represent distinct structural units. Separate them.
            if current_node.node_type != "sentence" and current_node.node_type != "paragraph":
                chunks.append(self._commit_chunk(file_path, current_batch))
                current_batch = [next_node]
                continue

            # Rule 4: Jaccard Semantic Similarity Fallback for Text Blocks
            if current_node.node_type == "sentence" and next_node.node_type == "sentence":
                sim = self._calculate_token_similarity(current_node.content, next_node.content)
                if sim >= self.similarity_threshold:
                    current_batch.append(next_node)
                else:
                    chunks.append(self._commit_chunk(file_path, current_batch))
                    current_batch = [next_node]
                continue

            # Default catch-all: Keep rolling for standard sequential text streams
            current_batch.append(next_node)

        if current_batch:
            chunks.append(self._commit_chunk(file_path, current_batch))

        return chunks

    def _calculate_token_similarity(self, text_a: str, text_b: str) -> float:
        """Lightweight token-based Jaccard similarity to avoid heavy dependencies."""
        words_a = set(re.findall(r'\w+', text_a.lower()))
        words_b = set(re.findall(r'\w+', text_b.lower()))
        if not words_a or not words_b:
            return 0.0
        intersection = words_a.intersection(words_b)
        union = words_a.union(words_b)
        return len(intersection) / len(union)

    def _commit_chunk(self, file_path: str, batch: List[AtomicNode]) -> Chunk:
        """Assembles a list of nodes into a unified Chunk payload."""
        fused_content = "\n".join([n.content for n in batch])

        return Chunk(
            content=fused_content,
            origin_file=file_path,
            constituent_nodes=[n.id for n in batch],
            metadata={
                "start_line": batch[0].start_line,
                "end_line": batch[-1].end_line,
                "node_count": len(batch)
            }
        )