import json
from typing import List
from emitters.base import BaseEmitter
from core.models import Chunk

class JsonEmitter(BaseEmitter):
    """
    Stage 4 Implementation. Serializes chunks into standardized,
    highly metadata-rich JSON payloads.
    """

    def emit(self, chunks: List[Chunk], output_path: str = None) -> str:
        """
        Formats chunks into a structured JSON array. Optionally writes to a file.
        """
        serialized_data = []

        for chunk in chunks:
            serialized_data.append({
                "id": chunk.id,
                "origin_file": chunk.origin_file,
                "content": chunk.content,
                "constituent_nodes": chunk.constituent_nodes,
                "metadata": {
                    "start_line": chunk.metadata.get("start_line"),
                    "end_line": chunk.metadata.get("end_line"),
                    "node_count": chunk.metadata.get("node_count"),
                    **chunk.metadata  # Capture any additional downstream properties
                },
                "relations": chunk.relations
            })

        json_output = json.dumps(serialized_data, indent=4)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_output)

        return json_output