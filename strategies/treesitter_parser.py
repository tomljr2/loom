from typing import List, Dict, Any, Optional
import tree_sitter_language_pack
from tree_sitter import Parser, Language, Query, QueryCursor
from core.models import Zone, AtomicNode
from strategies.base import BaseStrategy


class TreeSitterStrategy(BaseStrategy):
    """
    Stage 2: Code Strategy. Parses code blocks into structural AST nodes
    (like classes, interfaces, or methods) using stateless hierarchical lookup.
    """

    def parse(self, zone: Zone, parameters: Dict[str, Any]) -> List[AtomicNode]:
        language_name = parameters.get("language") or zone.metadata.get("language")
        if not language_name:
            raise ValueError(f"TreeSitterStrategy requires a language parameter for Zone {zone.id}")

        try:
            lang: Language = tree_sitter_language_pack.get_language(language_name)
            parser = Parser(lang)
        except Exception as e:
            raise RuntimeError(f"Failed to load Tree-sitter grammar for language: {language_name}") from e

        tree = parser.parse(bytes(zone.content, "utf8"))
        root_node = tree.root_node

        # Update: Capture both classes and methods to build our structural graph
        default_query = """
        (class_declaration) @capture
        (method_declaration) @capture
        """
        query_str = parameters.get("query", default_query)

        try:
            query = Query(lang, query_str)
            query_cursor = QueryCursor(query)
            captures_dict = query_cursor.captures(root_node)
        except Exception as e:
            raise ValueError(f"Invalid Tree-sitter query syntax for {language_name}: {query_str}") from e

        atomic_nodes = []

        for capture_name, nodes in captures_dict.items():
            for node in nodes:
                # Truncate class content to just its header declaration to avoid text duplication
                if node.type == "class_declaration":
                    body_node = node.child_by_field_name("body") or next(
                        (c for c in node.children if c.type == "class_body"), None)
                    if body_node:
                        node_content = zone.content[node.start_byte:body_node.start_byte + 1]
                        end_line_offset = body_node.start_point[0]
                    else:
                        node_content = zone.content[node.start_byte:node.end_byte]
                        end_line_offset = node.end_point[0]
                else:
                    node_content = zone.content[node.start_byte:node.end_byte]
                    end_line_offset = node.end_point[0]

                absolute_start_line = zone.start_line + node.start_point[0]
                absolute_end_line = zone.start_line + end_line_offset

                # Generate a unique structural signature for this physical AST position
                node_signature = f"{node.type}_{node.start_byte}"

                # Stateless Ancestry Lookup: Crawl up the physical AST tree to find an encapsulating class
                parent_signature = None
                curr = node.parent
                while curr:
                    if curr.type == "class_declaration":
                        parent_signature = f"class_declaration_{curr.start_byte}"
                        break
                    curr = curr.parent

                features = {
                    "capture_tag": capture_name,
                    "ast_type": node.type,
                    "is_named": node.is_named,
                    "node_signature": node_signature
                }

                if parent_signature:
                    features["parent_signature"] = parent_signature

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