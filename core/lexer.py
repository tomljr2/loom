import re
from typing import List, Dict, Any, Optional
from core.models import Zone


class ZoneLexer:
    """
    Stage 1: Analyzes raw multi-modal files (like Markdown) and slices them
    into logical physical boundaries (Zones), stripping layout formatting wrappers.
    """

    @staticmethod
    def slice_file(file_path: str, file_content: str, file_rules: Optional[Dict[str, Any]] = None) -> List[Zone]:
        lines = file_content.splitlines()
        zones = []

        # Target Markdown files for structured multi-modal fence extraction
        if file_path.endswith(".md") or file_path.endswith(".markdown"):
            in_code_block = False
            current_zone_lines = []
            zone_start_line = 1
            current_lang = None
            zone_counter = 1

            for line_idx, line in enumerate(lines, 1):
                # Detect Markdown code block boundaries
                if line.strip().startswith("```"):
                    if not in_code_block:
                        # 1. Close out the preceding prose section if it has content
                        if current_zone_lines:
                            zones.append(Zone(
                                id=f"zone_{zone_counter}",
                                source_file=file_path,  # Fixed: Added tracking back to source file
                                zone_type="prose_section",
                                content="\n".join(current_zone_lines),
                                start_line=zone_start_line,
                                end_line=line_idx - 1,
                                metadata={}
                            ))
                            zone_counter += 1

                        # 2. Extract language token (e.g., ```java -> java)
                        current_lang = line.strip().replace("```", "").strip().lower() or "text"
                        in_code_block = True
                        current_zone_lines = []
                        zone_start_line = line_idx + 1  # Content starts *after* the backticks fence
                    else:
                        # 3. Close out the active code block zone
                        if current_zone_lines:
                            zones.append(Zone(
                                id=f"zone_{zone_counter}",
                                source_file=file_path,  # Fixed: Added tracking back to source file
                                zone_type="code_block",
                                content="\n".join(current_zone_lines),
                                start_line=zone_start_line,
                                end_line=line_idx - 1,
                                metadata={"language": current_lang}
                            ))
                            zone_counter += 1
                        in_code_block = False
                        current_zone_lines = []
                        zone_start_line = line_idx + 1
                else:
                    current_zone_lines.append(line)

            # Clean up any trailing segments at the bottom of the file
            if current_zone_lines:
                zones.append(Zone(
                    id=f"zone_{zone_counter}",
                    source_file=file_path,  # Fixed: Added tracking back to source file
                    zone_type="code_block" if in_code_block else "prose_section",
                    content="\n".join(current_zone_lines),
                    start_line=zone_start_line,
                    end_line=len(lines),
                    metadata={"language": current_lang} if in_code_block else {}
                ))
            return zones

        # Standard monolithic fallback rule for pure source code or flat text files
        default_type = "code_block" if any(
            file_path.endswith(ext) for ext in [".java", ".py", ".cpp", ".go"]) else "raw_text"
        fallback_lang = file_path.split(".")[-1] if "." in file_path else "text"

        return [
            Zone(
                id="zone_1",
                source_file=file_path,  # Fixed: Added tracking back to source file
                zone_type=default_type,
                content=file_content,
                start_line=1,
                end_line=len(lines) if lines else 1,
                metadata={"language": fallback_lang}
            )
        ]