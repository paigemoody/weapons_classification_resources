#!/usr/bin/env python3
"""
Parse tree structure from plain text format and convert to JSON.
This is the canonical format that users edit.

Node types:
  - decision: intermediate decision nodes
  - classification: terminal classification nodes (leaf)
"""

import json
import re


def parse_tree_structure(structure_file):
    """
    Parse tree structure from text file with box-drawing characters.
    Returns nested dict representing the tree.
    """
    with open(structure_file) as f:
        lines = f.readlines()
    
    def parse_node(line):
        """Extract node ID and metadata from a line"""
        # Remove box-drawing characters and whitespace
        cleaned = re.sub(r'[├├─│└└─\s]+', '', line).strip()
        
        if not cleaned:
            return None
        
        # Format: NodeId (type: description) or NodeId
        match = re.match(r'(\w+)\s*(?:\(([^)]+)\))?', cleaned)
        if match:
            node_id = match.group(1)
            metadata = match.group(2) if match.group(2) else ""
            
            # Determine if decision or classification
            node_type = "decision" if ":" in metadata else "classification"
            
            return {
                "id": node_id,
                "type": node_type,
                "metadata": metadata
            }
        return None
    
    def get_indent_level(line):
        """Calculate indentation level based on leading characters"""
        match = re.match(r'^([\s│├└─]*)', line)
        if match:
            indent_str = match.group(1)
            # Count the nesting level (roughly by position)
            return len(indent_str) // 4
        return 0
    
    # Parse into tree structure
    root = None
    stack = []  # Stack of (indent_level, node)
    
    for line in lines:
        if not line.strip():
            continue
        
        node_data = parse_node(line)
        if not node_data:
            continue
        
        indent = get_indent_level(line)
        node = {
            "id": node_data["id"],
            "type": node_data["type"],
            "children": []
        }
        
        if root is None:
            root = node
            stack = [(0, root)]
        else:
            # Find the correct parent
            while len(stack) > 1 and stack[-1][0] >= indent:
                stack.pop()
            
            parent = stack[-1][1]
            parent["children"].append(node)
            stack.append((indent, node))
    
    return root


def tree_to_json(tree_root):
    """Convert tree dict to JSON format with structure property"""
    return {"tree": tree_root}


def main():
    """Parse structure file and output JSON"""
    try:
        tree = parse_tree_structure("flowchart-structure.txt")
        json_data = tree_to_json(tree)
        
        with open("flowchart-structure.json", "w") as f:
            json.dump(json_data, f, indent=2)
        
        print("✅ Parsed flowchart-structure.txt")
        print(f"   Root: {tree['id']}")
        print(f"   Generated: flowchart-structure.json")
        
    except FileNotFoundError:
        print("❌ flowchart-structure.txt not found")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()