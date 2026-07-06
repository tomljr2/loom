from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import uuid

@dataclass(frozen=True)
class Zone:
    """
    Stage 1 Output: A raw, unparsed section of a file bounded by rules.
    """
    source_file: str       # Path to the originating file
    zone_type: str         # e.g., "code_block", "prose_section"
    content: str           # The raw, untouched string slice
    start_line: int
    end_line: int
    # Defaulted fields must live at the bottom
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AtomicNode:
    """
    Stage 2 Output: An unbreakable, granular piece of structural or semantic context.
    """
    zone_id: str           # Lineage back to the originating Zone
    node_type: str         # e.g., "method_declaration", "sentence"
    content: str           # The specific sliced text/code snippet
    start_line: int
    end_line: int
    # Defaulted fields must live at the bottom
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    features: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    """
    Stage 3/4 Output: The final, context-retained block committed to the DB.
    """
    content: str                        # The consolidated, readable string window
    origin_file: str                    # Preserved for easy RAG referencing
    # Defaulted fields must live at the bottom
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    constituent_nodes: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    relations: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)