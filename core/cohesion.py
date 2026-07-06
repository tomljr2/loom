import re
import uuid
from typing import List, Dict, Any
from types import SimpleNamespace
from core.models import AtomicNode
from core.relations import StructuralEdgeExtractor
from core.entities import EntityExtractor
from core.utils import count_tokens


class CohesionEngine:
    def __init__(self, similarity_threshold: float = 0.75, max_chunk_lines: int = 50, **kwargs):
        """
        Initializes the CohesionEngine.

        :param similarity_threshold: Jaccard similarity cutoff for merging fusable nodes.
        :param max_chunk_lines: The hard upper limit of lines allowed in a single chunk.
        :param kwargs: Captures orchestration/config parameters dynamically (e.g., graph_keywords).
        """
        self.similarity_threshold = similarity_threshold
        self.max_chunk_lines = max_chunk_lines

        # Node types explicitly permitted to undergo semantic similarity evaluation
        self.fusable_types = {"paragraph", "sentence", "text_segment", "raw_text"}

        # Pull dynamic extraction keywords passed down from configuration layers
        # Defaulting to a safe structural array matching current workspace testing profiles
        graph_keywords = kwargs.get("graph_keywords", ["telemetry", "pyrolysis", "hardware", "buffer"])
        self.entity_extractor = EntityExtractor(vocabulary=graph_keywords)

    def fuse_nodes(self, origin_file: str, nodes: List[AtomicNode]) -> List[Any]:
        """
        Aggregates sequential atomic nodes into contextually coherent chunks
        based on line limits, structural types, and semantic similarity.
        """
        if not nodes:
            return []

        chunks = []
        current_batch = [nodes[0]]
        current_lines = nodes[0].end_line - nodes[0].start_line + 1

        for next_node in nodes[1:]:
            current_node = current_batch[-1]
            next_lines = next_node.end_line - next_node.start_line + 1

            # Rule 1: Hard line-count threshold check
            if current_lines + next_lines > self.max_chunk_lines:
                chunks.append(self._build_chunk(current_batch, origin_file))
                current_batch = [next_node]
                current_lines = next_lines
                continue

            # Rule 2: Evaluate similarity ONLY if adjacent nodes are matching fusable types
            if (current_node.node_type == next_node.node_type and
                    current_node.node_type in self.fusable_types):

                similarity = self._calculate_jaccard_similarity(
                    current_node.content, next_node.content
                )

                if similarity >= self.similarity_threshold:
                    current_batch.append(next_node)
                    current_lines += next_lines
                    continue

            # Rule 3: Discrete boundaries (mismatched types or non-fusable tokens like log entries)
            # trigger an intentional chunk break
            chunks.append(self._build_chunk(current_batch, origin_file))
            current_batch = [next_node]
            current_lines = next_lines

        # Flush the remaining buffer
        if current_batch:
            chunks.append(self._build_chunk(current_batch, origin_file))

        # Run the structural backbone edge pass and apply dynamic entity mesh routing
        final_graph_chunks = StructuralEdgeExtractor.extract_edges(chunks, self.entity_extractor)

        return final_graph_chunks

    def _calculate_jaccard_similarity(self, text1: str, text2: str) -> float:
        """Calculates token-level Jaccard similarity between two strings."""
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        return intersection / union

    def _build_chunk(self, batch: List[AtomicNode], origin_file: str) -> SimpleNamespace:
        """Compiles a batch of atomic nodes into a unified SimpleNamespace chunk object."""
        content = "\n".join([n.content for n in batch])

        # Consolidate pre-existing syntax or graph relations across the batch
        relations = []
        for node in batch:
            if hasattr(node, 'relations') and node.relations:
                relations.extend(node.relations)

        # Resolve the dominant chunk type classification label
        dominant_type = batch[0].node_type
        if dominant_type in self.fusable_types or dominant_type == "header":
            chunk_type = "prose_section"
        else:
            chunk_type = dominant_type

        # Final metadata construction with integrated token count
        return SimpleNamespace(
            id=str(uuid.uuid4()),
            origin_file=origin_file,
            content=content,
            constituent_nodes=[str(node.id) for node in batch],
            metadata={
                "start_line": batch[0].start_line,
                "end_line": batch[-1].end_line,
                "node_count": len(batch),
                "token_count": count_tokens(content),  # The new final piece
                "chunk_type": chunk_type
            },
            relations=relations
        )