from typing import List, Any

class StructuralEdgeExtractor:
    """Generates deterministic structural relationships across processed chunks."""

    @staticmethod
    def extract_edges(chunks: List[Any], entity_extractor: Any = None) -> List[Any]:
        if not chunks:
            return chunks

        last_header_id = None

        # --- Pass 1: Structural Linear Backbone ---
        for i, chunk in enumerate(chunks):
            if not hasattr(chunk, 'relations') or chunk.relations is None:
                chunk.relations = []

            if i < len(chunks) - 1:
                next_chunk = chunks[i + 1]
                chunk.relations.append({
                    "source_id": chunk.id,
                    "target_id": next_chunk.id,
                    "type": "PRECEDES"
                })

            chunk_type = chunk.metadata.get("chunk_type") if isinstance(chunk.metadata, dict) else getattr(chunk.metadata, 'chunk_type', None)
            if chunk_type == "header":
                last_header_id = chunk.id
            elif last_header_id and chunk_type == "prose_section":
                chunk.relations.append({
                    "source_id": last_header_id,
                    "target_id": chunk.id,
                    "type": "PARENT_OF"
                })

        # --- Pass 2: Dynamic Entity Cross-Linking ---
        if entity_extractor:
            chunks = entity_extractor.extract_cross_references(chunks)

        return chunks