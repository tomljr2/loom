from typing import List, Dict, Any, Optional
from core.models import AtomicNode, Zone
from core.lexer import ZoneLexer
from strategies.treesitter_parser import TreeSitterStrategy
from strategies.prose_parser import ProseStrategy


class LoomOrchestrator:
    """
    The main entry point for the Loom library.
    Coordinates Stage 1 (Lexing) and Stage 2 (Extraction).
    """

    def __init__(self, user_config: Optional[Dict[str, Any]] = None):
        self.user_config = user_config or {}

        # Internal Strategy Registry
        # Maps configuration strings to concrete execution classes
        self._strategy_registry = {
            "tree_sitter": TreeSitterStrategy(),
            "prose": ProseStrategy(),
            "code_block": TreeSitterStrategy(),  # Default mapping helpers
            "prose_section": ProseStrategy(),
            "raw_text": ProseStrategy()
        }

    def register_strategy(self, name: str, strategy_instance: Any):
        """Allows users to inject custom parsing strategies at runtime."""
        self._strategy_registry[name] = strategy_instance

    def process_file(self, file_path: str, file_content: str) -> List[AtomicNode]:
        """
        Processes a single file through the extraction pipeline.

        :param file_path: Path of the target file (used for extension matching)
        :param file_content: Raw string content of the file
        :return: Chronologically sorted list of extracted AtomicNodes
        """
        # 1. Match configuration rules for this specific file path
        file_rules = self._find_matching_rules(file_path)

        # 2. Stage 1: Slice file into physical/logical Zones
        zones: List[Zone] = ZoneLexer.slice_file(file_path, file_content, file_rules)

        all_atomic_nodes: List[AtomicNode] = []

        # 3. Stage 2: Loop through zones and dispatch to strategies
        for zone in zones:
            # Determine which strategy to use: User override -> Default mapping
            strategy_name = self._determine_strategy_name(zone, file_rules)
            strategy = self._strategy_registry.get(strategy_name)

            if not strategy:
                # Fallback to pure prose processing if an unmapped strategy name occurs
                strategy = self._strategy_registry["prose"]

            # Extract processor parameters from the config if they exist
            processor_params = self._get_processor_params(strategy_name, file_rules)

            # Execute the extraction strategy
            extracted_nodes = strategy.parse(zone, processor_params)
            all_atomic_nodes.extend(extracted_nodes)

        # Ensure everything is returned in exact order of appearance in the file
        return sorted(all_atomic_nodes, key=lambda n: n.start_line)

    def _find_matching_rules(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Checks the user config to see if the file matches any glob patterns."""
        # Simplistic match for now; can be expanded with full 'fnmatch' glob support later
        for file_rule in self.user_config.get("files", []):
            match_pattern = file_rule.get("match", "")
            # Basic extension check fallback for prototyping
            if match_pattern and match_pattern.replace("*.", "") in file_path:
                return file_rule
        return None

    def _determine_strategy_name(self, zone: Zone, file_rules: Optional[Dict[str, Any]]) -> str:
        """Finds what strategy should process this zone type."""
        if file_rules and "processors" in file_rules:
            for processor in file_rules["processors"]:
                if processor.get("segment") == zone.zone_type:
                    return processor.get("strategy", "prose")

        # Fallback to the zone type name itself, which maps directly in our internal registry
        return zone.zone_type

    def _get_processor_params(self, strategy_name: str, file_rules: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Pulls parameter options (like tree-sitter queries or prose granularity) from config."""
        if file_rules and "processors" in file_rules:
            for processor in file_rules["processors"]:
                if processor.get("strategy") == strategy_name:
                    return processor.get("parameters", {})
        return {}