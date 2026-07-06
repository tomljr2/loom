from abc import ABC, abstractmethod
from typing import List, Any
from core.models import Chunk

class BaseEmitter(ABC):
    """
    Stage 4 Base Contract. Handles formatting and discharging
    finalized Chunks into downstream storage/indexing layers.
    """

    @abstractmethod
    def emit(self, chunks: List[Chunk], **kwargs) -> Any:
        """Executes the formatting and distribution logic for a list of chunks."""
        pass