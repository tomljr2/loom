from typing import List, Dict, Any, Optional, Union
from core.models import AtomicNode, Zone, Chunk
from core.lexer import ZoneLexer
from core.cohesion import CohesionEngine
from strategies.treesitter_parser import TreeSitterStrategy
from strategies.prose_parser import ProseStrategy
from emitters.base import BaseEmitter


class LoomOrchestrator:
    """
    The main entry point for the Loom library.
    Coordinates Stage 1 (Lexing), Stage 2 (Extraction),
    Stage 3 (Cohesion), and Stage 4 (Emission).
    """

    def __init__(self, user_config: Optional[Dict[str, Any]] = None):
        self.user_config = user_config or {}

        self._strategy_registry = {
            "tree_sitter": TreeSitterStrategy(),
            "prose": ProseStrategy(),
            "code_block": TreeSitterStrategy(),
            "prose_section": ProseStrategy(),
            "raw_text": ProseStrategy()
        }

    def register_strategy(self, name: str, strategy_instance: Any):
        """Allows users to inject custom parsing strategies at runtime."""
        self._strategy_registry[name] = strategy_instance

    def process_file(
            self,
            file_path: str,
            file_content: str,
            emitter: Optional[BaseEmitter] = None,
            **emitter_kwargs
    ) -> Union[List[Chunk], Any]:
        """Processes a single file through the configured multi-stage Loom pipeline."""
        file_rules = self._find_matching_rules(file_path)
        zones: List[Zone] = ZoneLexer.slice_file(file_path, file_content, file_rules)

        all_atomic_nodes: List[AtomicNode] = []

        for zone in zones:
            strategy_name = self._determine_strategy_name(zone, file_rules)
            strategy = self._strategy_registry.get(strategy_name)

            if not strategy:
                strategy = self._strategy_registry["prose"]

            # 1. Fetch static fallback parameters from defaults.yml
            processor_params = self._get_processor_params(strategy_name, file_rules)

            # 2. Dynamic Override: If the lexer already extracted a language token
            # (like 'java' or 'py' from a markdown fence), prioritize it!
            if zone.metadata and "language" in zone.metadata:
                # Create a shallow copy to prevent mutating shared configuration dictionaries
                processor_params = {**processor_params, "language": zone.metadata["language"]}

            # 3. Parse using the combined contextual parameters
            extracted_nodes = strategy.parse(zone, processor_params)
            all_atomic_nodes.extend(extracted_nodes)

        sorted_nodes = sorted(all_atomic_nodes, key=lambda n: n.start_line)

        # Stage 3 Configuration Parsing
        cohesion_config = self.user_config.get("cohesion", {})
        similarity_threshold = cohesion_config.get("similarity_threshold", 0.80)
        max_chunk_lines = cohesion_config.get("max_chunk_lines", 50)
        max_prose_code_gap = cohesion_config.get("max_prose_code_gap", 4)  # Extract default fallback

        # Initialize engine using declarative configurations
        engine = CohesionEngine(
            similarity_threshold=similarity_threshold,
            max_chunk_lines=max_chunk_lines,
            max_prose_code_gap=max_prose_code_gap
        )

        final_chunks = engine.fuse_nodes(file_path, sorted_nodes)

        if emitter:
            return emitter.emit(final_chunks, **emitter_kwargs)

        return final_chunks

    def _find_matching_rules(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Checks the user config to see if the file matches any glob patterns."""
        for file_rule in self.user_config.get("files", []):
            match_pattern = file_rule.get("match", "")
            if match_pattern and match_pattern.replace("*.", "") in file_path:
                return file_rule
        return None

    def _determine_strategy_name(self, zone: Zone, file_rules: Optional[Dict[str, Any]]) -> str:
        """Finds what strategy should process this zone type."""
        if file_rules and "processors" in file_rules:
            for processor in file_rules["processors"]:
                if processor.get("segment") == zone.zone_type:
                    return processor.get("strategy", "prose")
        return zone.zone_type

    def _get_processor_params(self, strategy_name: str, file_rules: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Pulls parameter options from config."""
        if file_rules and "processors" in file_rules:
            for processor in file_rules["processors"]:
                if processor.get("strategy") == strategy_name:
                    return processor.get("parameters", {})
        return {}