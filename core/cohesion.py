import re
from typing import List
from core.models import AtomicNode, Chunk


class CohesionEngine:
    """
    Stage 3: Analyzes a chronological sequence of AtomicNodes and fuses
    them into larger, context-retained Chunks using sliding threshold rules.
    Resolves explicit hierarchical graph edges via a two-pass architecture.
    """

    def __init__(self, similarity_threshold: float = 0.80, max_chunk_lines: int = 50):
        self.similarity_threshold = similarity_threshold
        self.max_chunk_lines = max_chunk_lines
        # Rigid structural code blocks that should never be fused together
        self._structural_types = {"class_declaration", "interface_declaration", "method_declaration"}

    def fuse_nodes(self, file_path: str, nodes: List[AtomicNode]) -> List[Chunk]:
        """Groups adjacent AtomicNodes into final semantic Chunks and binds graph relations."""
        if not nodes:
            return []

        chunks = []
        current_batch = [nodes[0]]

        # Pass 1: Linear Chunk Segmentation & Boundary Enforcement
        for next_node in nodes[1:]:
            current_node = current_batch[-1]

            # Rule 1: Max line constraints
            total_lines_projected = next_node.end_line - current_batch[0].start_line
            if total_lines_projected > self.max_chunk_lines:
                chunks.append(self._commit_chunk(file_path, current_batch))
                current_batch = [next_node]
                continue

            # Rule 2: Structural Code Boundary Safeguard
            # If either block is a structural code unit, force a clean chunk break
            if current_node.node_type in self._structural_types or next_node.node_type in self._structural_types:
                chunks.append(self._commit_chunk(file_path, current_batch))
                current_batch = [next_node]
                continue

            # Rule 3: Multi-Modal Affinity (Prose and Code boundary tracking)
            if current_node.node_type != next_node.node_type:
                if next_node.start_line - current_node.end_line <= 2:
                    current_batch.append(next_node)
                else:
                    chunks.append(self._commit_chunk(file_path, current_batch))
                    current_batch = [next_node]
                continue

            # Rule 4: Jaccard Semantic Similarity for sequential prose streams
            if current_node.node_type == "sentence" and next_node.node_type == "sentence":
                sim = self._calculate_token_similarity(current_node.content, next_node.content)
                if sim >= self.similarity_threshold:
                    current_batch.append(next_node)
                else:
                    chunks.append(self._commit_chunk(file_path, current_batch))
                    current_batch = [next_node]
                continue

            current_batch.append(next_node)

        if current_batch:
            chunks.append(self._commit_chunk(file_path, current_batch))

        # Pass 2: Global Graph Relation Resolution
        # 2a. Map physical AST signatures straight to their parent Chunk UUIDs
        signature_to_chunk_id = {}
        for chunk in chunks:
            for sig in chunk.metadata.get("_node_signatures", []):
                signature_to_chunk_id[sig] = chunk.id

        # 2b. Stitch together the CHILD_OF edge relationships
        for chunk in chunks:
            parent_sigs = chunk.metadata.pop("_parent_signatures", [])
            # Clean up the internal routing array from finalized public metadata
            chunk.metadata.pop("_node_signatures", None)

            for parent_sig in parent_sigs:
                target_uuid = signature_to_chunk_id.get(parent_sig)
                # Ensure we don't accidentally link a chunk back to itself
                if target_uuid and target_uuid != chunk.id:
                    chunk.relations.append({
                        "target_id": target_uuid,
                        "type": "CHILD_OF"
                    })

        return chunks

    def _calculate_token_similarity(self, text_a: str, text_b: str) -> float:
        words_a = set(re.findall(r'\w+', text_a.lower()))
        words_b = set(re.findall(r'\w+', text_b.lower()))
        if not words_a or not words_b:
            return 0.0
        intersection = words_a.intersection(words_b)
        union = words_a.union(words_b)
        return len(intersection) / len(union)

    def _commit_chunk(self, file_path: str, batch: List[AtomicNode]) -> Chunk:
        fused_content = "\n".join([n.content for n in batch])

        # Track signatures internally through the compilation phase
        node_sigs = [n.features["node_signature"] for n in batch if "node_signature" in n.features]
        parent_sigs = [n.features["parent_signature"] for n in batch if "parent_signature" in n.features]

        return Chunk(
            content=fused_content,
            origin_file=file_path,
            constituent_nodes=[n.id for n in batch],
            metadata={
                "start_line": batch[0].start_line,
                "end_line": batch[-1].end_line,
                "node_count": len(batch),
                "_node_signatures": node_sigs,
                "_parent_signatures": parent_sigs
            }
        )