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

    def process_file(
            self,
            file_path: str,
            file_content: str,
            emitter: Optional[BaseEmitter] = None,
            **emitter_kwargs
    ) -> Union[List[Chunk], Any]:
        """
        Processes a single file through the entire multi-stage Loom pipeline.

        :param file_path: Path of the target file (used for extension matching)
        :param file_content: Raw string content of the file
        :param emitter: Optional Stage 4 Emitter instance (e.g., JsonEmitter)
        :param emitter_kwargs: Key-value arguments passed directly to the emitter's emit method
        :return: Extracted Chunks list, or the formatted emitter output if an emitter is provided
        """
        # 1. Match configuration rules for this specific file path
        file_rules = self._find_matching_rules(file_path)

        # 2. Stage 1: Slice file into physical/logical Zones
        zones: List[Zone] = ZoneLexer.slice_file(file_path, file_content, file_rules)

        all_atomic_nodes: List[AtomicNode] = []

        # 3. Stage 2: Loop through zones and dispatch to extraction strategies
        for zone in zones:
            strategy_name = self._determine_strategy_name(zone, file_rules)
            strategy = self._strategy_registry.get(strategy_name)

            if not strategy:
                strategy = self._strategy_registry["prose"]

            processor_params = self._get_processor_params(strategy_name, file_rules)
            extracted_nodes = strategy.parse(zone, processor_params)
            all_atomic_nodes.extend(extracted_nodes)

        # Ensure everything is sorted in exact chronological order before fusing
        sorted_nodes = sorted(all_atomic_nodes, key=lambda n: n.start_line)

        # 4. Stage 3: Pass the sorted nodes to the Cohesion Engine for fusion
        cohesion_config = self.user_config.get("cohesion", {})
        similarity_threshold = cohesion_config.get("similarity_threshold", 0.80)
        max_chunk_lines = cohesion_config.get("max_chunk_lines", 50)

        engine = CohesionEngine(
            similarity_threshold=similarity_threshold,
            max_chunk_lines=max_chunk_lines
        )

        final_chunks = engine.fuse_nodes(file_path, sorted_nodes)

        # 5. Stage 4: Emission Layer
        # If an emitter is provided, run the chunks through it and return its specific output format
        if emitter:
            return emitter.emit(final_chunks, **emitter_kwargs)

        # Default fallback: Return the raw internal Chunk payloads
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