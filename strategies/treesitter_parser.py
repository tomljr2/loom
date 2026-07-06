from typing import List, Dict, Any
import tree_sitter_language_pack
from tree_sitter import Parser, Language, Query, QueryCursor
from core.models import Zone, AtomicNode
from strategies.base import BaseStrategy


class TreeSitterStrategy(BaseStrategy):
    """
    Stage 2: Code Strategy. Parses code blocks into structural AST nodes
    (like methods, functions, or classes) using Tree-sitter tree queries.
    """

    def parse(self, zone: Zone, parameters: Dict[str, Any]) -> List[AtomicNode]:
        language_name = parameters.get("language") or zone.metadata.get("language")
        if not language_name:
            raise ValueError(f"TreeSitterStrategy requires a language parameter for Zone {zone.id}")

        # 1. Safely retrieve the compiled Language instance and pass it directly to the Parser constructor
        try:
            lang: Language = tree_sitter_language_pack.get_language(language_name)
            parser = Parser(lang)
        except Exception as e:
            raise RuntimeError(f"Failed to load Tree-sitter grammar for language: {language_name}") from e

        # 2. Parse the raw string into an AST tree
        tree = parser.parse(bytes(zone.content, "utf8"))
        root_node = tree.root_node

        # 3. Load the SCM tree query using the modern Query and QueryCursor API
        default_query = "(method_declaration) @capture"
        query_str = parameters.get("query", default_query)

        try:
            # Fix: Instantiate Query and QueryCursor explicitly
            query = Query(lang, query_str)
            query_cursor = QueryCursor(query)
            # Modern API returns a dictionary: { "capture_tag": [Node, Node, ...] }
            captures_dict = query_cursor.captures(root_node)
        except Exception as e:
            raise ValueError(f"Invalid Tree-sitter query syntax for {language_name}: {query_str}") from e

        atomic_nodes = []

        # 4. Map AST captures directly to Loom's AtomicNode lifecycle
        # Fix: Unpack the new dictionary format instead of a flat list of tuples
        for capture_name, nodes in captures_dict.items():
            for node in nodes:
                node_content = zone.content[node.start_byte:node.end_byte]

                # Offset the lines relative to where this Zone actually starts in the file
                absolute_start_line = zone.start_line + node.start_point[0]
                absolute_end_line = zone.start_line + node.end_point[0]

                features = {
                    "capture_tag": capture_name,
                    "ast_type": node.type,
                    "is_named": node.is_named
                }

                name_node = node.child_by_field_name("name")
                if name_node:
                    features["identifier"] = zone.content[name_node.start_byte:name_node.end_byte]

                atomic_nodes.append(
                    AtomicNode(
                        zone_id=zone.id,
                        node_type=node.type,
                        content=node_content,
                        start_line=absolute_start_line,
                        end_line=absolute_end_line,
                        features=features
                    )
                )

        return atomic_nodes