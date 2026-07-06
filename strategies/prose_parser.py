import re
from typing import List, Dict, Any
from core.models import Zone, AtomicNode
from strategies.base import BaseStrategy


class ProseStrategy(BaseStrategy):
    """
    Stage 2: Prose Strategy. Slices conversational text or documentation
    into granular paragraphs or sentences using regex boundaries.
    """

    def parse(self, zone: Zone, parameters: Dict[str, Any]) -> List[AtomicNode]:
        granularity = parameters.get("granularity", "sentence")  # "paragraph" or "sentence"
        content = zone.content

        if not content.strip():
            return []

        # Build line offsets relative to this specific zone content
        line_offsets = [0] + [m.end() for m in re.finditer(r'\n', content)]

        def get_relative_line(char_idx: int) -> int:
            return next((i for i, offset in enumerate(line_offsets) if offset > char_idx), len(line_offsets))

        atomic_nodes = []

        # Option A: Split by Paragraphs (Double newlines)
        if granularity == "paragraph":
            pattern = re.compile(r'(?:\r?\n){2,}')
            last_idx = 0

            for match in pattern.finditer(content):
                start, end = match.span()
                text_block = content[last_idx:start].strip()
                if text_block:
                    atomic_nodes.append(
                        self._create_node(zone, text_block, last_idx, start, get_relative_line, "paragraph"))
                last_idx = end

            if last_idx < len(content):
                text_block = content[last_idx:].strip()
                if text_block:
                    atomic_nodes.append(
                        self._create_node(zone, text_block, last_idx, len(content), get_relative_line, "paragraph"))

        # Option B: Split by Sentences (Standard punctuation tracking)
        else:
            # Smart regex split that respects standard abbreviations but catches sentence terminals (. ! ?)
            sentence_end = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+')
            last_idx = 0

            # Find the split points
            splits = [match.span() for match in sentence_end.finditer(content)]

            for start, end in splits:
                text_block = content[last_idx:start].strip()
                if text_block:
                    atomic_nodes.append(
                        self._create_node(zone, text_block, last_idx, start, get_relative_line, "sentence"))
                last_idx = end

            if last_idx < len(content):
                text_block = content[last_idx:].strip()
                if text_block:
                    atomic_nodes.append(
                        self._create_node(zone, text_block, last_idx, len(content), get_relative_line, "sentence"))

        return atomic_nodes

    def _create_node(self, zone: Zone, text: str, start_idx: int, end_idx: int, line_fn: Any,
                     node_type: str) -> AtomicNode:
        """Helper to compute absolute file lines and generate the AtomicNode."""
        rel_start = line_fn(start_idx)
        rel_end = line_fn(end_idx)

        # Translate to global document lines
        abs_start = zone.start_line + max(0, rel_start - 1)
        abs_end = zone.start_line + max(0, rel_end - 1)

        return AtomicNode(
            zone_id=zone.id,
            node_type=node_type,
            content=text,
            start_line=abs_start,
            end_line=max(abs_start, abs_end),
            features={"character_count": len(text)}
        )