from typing import List, Dict, Any


class StructuralEdgeExtractor:
    """Generates deterministic structural relationships (PRECEDES, PARENT_OF) across processed chunks."""

    @staticmethod
    def extract_edges(chunks: List[Any]) -> List[Any]:
        if not chunks or len(chunks) < 1:
            return chunks

        last_header_id = None

        for i, chunk in enumerate(chunks):
            # Ensure the chunk has a initialized relations list
            if not hasattr(chunk, 'relations') or chunk.relations is None:
                chunk.relations = []

            # 1. Establish linear PRECEDES edges between sequential chunks
            if i < len(chunks) - 1:
                next_chunk = chunks[i + 1]
                chunk.relations.append({
                    "source_id": chunk.id,
                    "target_id": next_chunk.id,
                    "type": "PRECEDES"
                })

            # 2. Establish hierarchical PARENT_OF edges from Headers to Sections
            chunk_type = chunk.metadata.get("chunk_type") if isinstance(chunk.metadata, dict) else getattr(
                chunk.metadata, 'chunk_type', None)

            if chunk_type == "header":
                # Track this chunk as the active structural parent anchor
                last_header_id = chunk.id
            elif last_header_id and chunk_type == "prose_section":
                # Link the active parent header directly to this body chunk
                chunk.relations.append({
                    "source_id": last_header_id,
                    "target_id": chunk.id,
                    "type": "PARENT_OF"
                })

        return chunks