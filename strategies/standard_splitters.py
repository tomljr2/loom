from typing import List, Dict, Any
import re
from core.models import AtomicNode, Zone


class DelimiterStrategy:
    """Splits a zone's content by a prioritized list of string delimiters (e.g., paragraphs, sentences)."""

    def parse(self, zone: Zone, parameters: Dict[str, Any]) -> List[AtomicNode]:
        # Pull delimiters from config, defaulting to double newlines (paragraphs)
        delimiters = parameters.get("delimiters", ["\n\n"])
        content = zone.content

        # Escape delimiters for safe regex compilation
        regex_pattern = "|".join([re.escape(d) for d in delimiters])
        if not regex_pattern:
            return [self._create_node(zone, content, zone.start_line, zone.end_line)]

        raw_chunks = re.split(regex_pattern, content)
        nodes = []
        current_line = zone.start_line

        for raw_chunk in raw_chunks:
            stripped = raw_chunk.strip()
            if not stripped:
                continue

            # Approximate line span for the chunk
            newlines_in_chunk = raw_chunk.count("\n")
            end_line = current_line + newlines_in_chunk

            nodes.append(self._create_node(zone, stripped, current_line, end_line))
            current_line = end_line + 1

        return nodes

    def _create_node(self, zone: Zone, content: str, start: int, end: int) -> AtomicNode:
        return AtomicNode(
            node_type="text_segment",
            content=content,
            start_line=start,
            end_line=end,
            features={}
        )


class FixedSizeStrategy:
    """Splits text into fixed-size character blocks with a configurable sliding window overlap."""

    def parse(self, zone: Zone, parameters: Dict[str, Any]) -> List[AtomicNode]:
        chunk_size = parameters.get("chunk_size", 1000)
        chunk_overlap = parameters.get("chunk_overlap", 200)
        content = zone.content

        if chunk_overlap >= chunk_size:
            chunk_overlap = chunk_size // 2

        nodes = []
        start_idx = 0
        text_len = len(content)

        # Simple line mapping assistant
        line_breaks = [0] + [m.start() for m in re.finditer(r'\n', content)] + [text_len]

        while start_idx < text_len:
            end_idx = min(start_idx + chunk_size, text_len)
            chunk_text = content[start_idx:end_idx]

            # Dynamically approximate document line placement based on string indices
            start_line = zone.start_line + sum(1 for b in line_breaks if b < start_idx)
            end_line = zone.start_line + sum(1 for b in line_breaks if b < end_idx)

            nodes.append(AtomicNode(
                node_type="fixed_block",
                content=chunk_text.strip(),
                start_line=start_line,
                end_line=end_line,
                features={"overlap_block": start_idx > 0}
            ))

            if end_idx == text_len:
                break

            start_idx += (chunk_size - chunk_overlap)

        return nodes