import re
from typing import List, Dict, Any, Optional
from core.models import Zone


class ZoneLexer:
    """
    Stage 1: Slices raw file content into distinct semantic Zones
    based on regex boundaries or default file extension rules.
    """

    # Built-in fallback conventions for standard file types
    DEFAULT_EXTENSIONS = {
        "java": "code_block",
        "py": "code_block",
        "ts": "code_block",
        "js": "code_block",
        "go": "code_block",
        "txt": "prose_section",
        "log": "prose_section"
    }

    @classmethod
    def slice_file(cls, source_file: str, content: str, file_rules: Optional[Dict[str, Any]] = None) -> List[Zone]:
        """
        Main entry point. Inspects rules, runs segmentations,
        and maps text slices to Zone objects.
        """
        # 1. If no custom rules match, fallback to standard extension conventions
        if not file_rules:
            ext = source_file.split(".")[-1].lower()
            zone_type = cls.DEFAULT_EXTENSIONS.get(ext, "raw_text")

            # Count lines for the metadata
            total_lines = len(content.splitlines()) if content else 1
            return [
                Zone(
                    source_file=source_file,
                    zone_type=zone_type,
                    content=content,
                    start_line=1,
                    end_line=max(1, total_lines),
                    metadata={"language": ext} if zone_type == "code_block" else {}
                )
            ]

        # 2. If hierarchical configuration rules *are* provided, run the regex segmentation
        return cls._run_segmentation(source_file, content, file_rules)

    @classmethod
    def _run_segmentation(cls, source_file: str, content: str, rules: Dict[str, Any]) -> List[Zone]:
        zones = []
        last_index = 0

        # Track line numbers accurately during slicing
        line_offsets = [0] + [m.end() for m in re.finditer(r'\n', content)]

        def get_line_number(char_idx: int) -> int:
            return next((i for i, offset in enumerate(line_offsets) if offset > char_idx), len(line_offsets))

        # Iterate through the segmentation definitions (e.g., matching code blocks first)
        for segment_rule in rules.get("segmentation", []):
            pattern = re.compile(segment_rule["pattern"])

            for match in pattern.finditer(content):
                # Handle any uncaptured text *before* the match as a default fallback zone
                start_back, end_back = match.span()
                if start_back > last_index:
                    prose_text = content[last_index:start_back]
                    if prose_text.strip():
                        zones.append(Zone(
                            source_file=source_file,
                            zone_type="prose_section",
                            content=prose_text,
                            start_line=get_line_number(last_index),
                            end_line=get_line_number(start_back)
                        ))

                # Capture the explicit match group details
                caps = segment_rule.get("capture_groups", {})
                zone_content = match.group(caps.get("content", 0))
                lang_group = caps.get("language", None)
                lang = match.group(lang_group) if lang_group else "unknown"

                zones.append(Zone(
                    source_file=source_file,
                    zone_type=segment_rule["name"],
                    content=zone_content,
                    start_line=get_line_number(start_back),
                    end_line=get_line_number(end_back),
                    metadata={"language": lang} if lang != "unknown" else {}
                ))
                last_index = end_back

        # Catch any trailing text at the end of the file
        if last_index < len(content):
            trailing_text = content[last_index:]
            if trailing_text.strip():
                zones.append(Zone(
                    source_file=source_file,
                    zone_type="prose_section",
                    content=trailing_text,
                    start_line=get_line_number(last_index),
                    end_line=get_line_number(len(content))
                ))

        # Sort zones by order of appearance in the file to preserve chronological context
        return sorted(zones, key=lambda z: z.start_line)