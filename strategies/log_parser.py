import re
from typing import List, Dict, Any
from core.models import AtomicNode, Zone


class LogStrategy:
    """Intelligently groups log entries by sweeping trailing stack traces into the root error anchor."""

    def parse(self, zone: Zone, parameters: Dict[str, Any]) -> List[AtomicNode]:
        content = zone.content
        lines = content.splitlines()

        anchor_pattern = parameters.get("anchor_pattern", r"^(\d{4}-\d{2}-\d{2}|\[[A-Z]{4,5}\])")
        compiled_regex = re.compile(anchor_pattern)

        nodes = []
        current_entry_lines = []
        entry_start_line = zone.start_line

        for idx, line in enumerate(lines):
            current_line_num = zone.start_line + idx

            if compiled_regex.search(line.strip()):
                if current_entry_lines:
                    # FIX: Supply the required zone_id backlink here
                    nodes.append(AtomicNode(
                        zone_id=zone.id,
                        node_type="log_entry",
                        content="\n".join(current_entry_lines),
                        start_line=entry_start_line,
                        end_line=current_line_num - 1,
                        features={}
                    ))
                current_entry_lines = [line]
                entry_start_line = current_line_num
            else:
                if current_entry_lines:
                    current_entry_lines.append(line)
                else:
                    current_entry_lines = [line]
                    entry_start_line = current_line_num

        if current_entry_lines:
            nodes.append(AtomicNode(
                zone_id=zone.id,
                node_type="log_entry",
                content="\n".join(current_entry_lines),
                start_line=entry_start_line,
                end_line=zone.start_line + len(lines) - 1,
                features={}
            ))

        return nodes