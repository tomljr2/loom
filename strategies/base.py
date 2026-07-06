from abc import ABC, abstractmethod
from typing import List, Dict, Any
from core.models import Zone, AtomicNode


class BaseStrategy(ABC):
    """
    The core interface for all Loom extraction strategies.
    Takes a single file Zone and dissects it into granular AtomicNodes.
    """

    @abstractmethod
    def parse(self, zone: Zone, parameters: Dict[str, Any]) -> List[AtomicNode]:
        """
        Executes the extraction logic on the given zone content.

        :param zone: The Zone object emitted from Stage 1 (Lexer).
        :param parameters: Strategy-specific configurations passed from the YAML rule.
        :return: A list of granular, immutable AtomicNode objects.
        """
        pass