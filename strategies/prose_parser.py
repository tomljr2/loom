from typing import List, Dict, Any
from core.models import AtomicNode, Zone


class ProseStrategy:
    """Chunks unstructured text by structural paragraph layouts instead of sentence-splitting."""

    def parse(self, zone: Zone, parameters: Dict[str, Any]) -> List[AtomicNode]:
        content = zone.content
        blocks = content.split("\n\n")

        nodes = []
        current_line = zone.start_line

        for block in blocks:
            stripped = block.strip()
            if not stripped:
                current_line += block.count("\n")
                continue

            lines_in_block = block.count("\n")
            end_line = current_line + lines_in_block
            node_type = "header" if stripped.startswith("#") else "paragraph"

            # FIX: Supply the required zone_id backlink
            nodes.append(AtomicNode(
                zone_id=zone.id,
                node_type=node_type,
                content=stripped,
                start_line=current_line,
                end_line=end_line,
                features={}
            ))

            current_line = end_line + 1

        return nodes