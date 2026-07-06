import re
from typing import List, Dict, Any


class EntityExtractor:
    """Scans chunk text for configurable system keywords to build cross-chunk links."""

    def __init__(self, vocabulary: List[str] = None):
        """
        Initializes the extractor with a dynamic list of keywords.
        :param vocabulary: A list of string terms to track dynamically (e.g., ["telemetry", "pyrolysis"])
        """
        # Fallback to a safe empty list if no runtime config is provided
        vocab_list = vocabulary or []

        # Compile case-insensitive word-boundary regexes dynamically on instantiation
        self.compiled_patterns = {
            term: re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
            for term in vocab_list
        }

    def extract_cross_references(self, chunks: List[Any]) -> List[Any]:
        if not chunks or not self.compiled_patterns:
            return chunks

        # Map to record entity occurrences across chunks: {entity_term: [chunk_ids]}
        entity_registry: Dict[str, List[str]] = {term: [] for term in self.compiled_patterns}

        # Pass 1: Catalog occurrences dynamically
        for chunk in chunks:
            content = getattr(chunk, 'content', '')
            for term, regex in self.compiled_patterns.items():
                if regex.search(content):
                    entity_registry[term].append(chunk.id)

        # Pass 2: Mesh-link chunks sharing the exact same entity concept
        for term, matching_ids in entity_registry.items():
            if len(matching_ids) < 2:
                continue

            for source_id in matching_ids:
                for target_id in matching_ids:
                    if source_id == target_id:
                        continue

                    source_chunk = next((c for c in chunks if c.id == source_id), None)
                    if source_chunk:
                        # Defensive check to avoid duplicating edge arrays
                        exists = any(
                            r.get("target_id") == target_id and
                            r.get("type") == "REFERENCES" and
                            r.get("metadata", {}).get("concept") == term
                            for r in source_chunk.relations
                        )
                        if not exists:
                            source_chunk.relations.append({
                                "source_id": source_id,
                                "target_id": target_id,
                                "type": "REFERENCES",
                                "metadata": {"concept": term}
                            })
        return chunks