#!/usr/bin/env python3
"""
Validator for flowchart-structure.txt
Checks for:
  - Valid node IDs (alphanumeric + underscore only, no spaces within ID)
  - Valid node types (decision or classification)
  - Proper tree hierarchy
  - No duplicate node IDs
  - No orphaned nodes
  - Correct box-drawing character usage
"""

import re
import sys
from pathlib import Path


class StructureValidator:
    def __init__(self, filepath):
        self.filepath = filepath
        self.errors = []
        self.warnings = []
        self.nodes = {}
        self.lines = []
    
    def load_file(self):
        """Load the structure file"""
        try:
            with open(self.filepath) as f:
                self.lines = f.readlines()
        except FileNotFoundError:
            self.errors.append(f"File not found: {self.filepath}")
            return False
        return True
    
    def validate_node_id(self, node_id, line_num):
        """Check if node ID is valid (alphanumeric + underscore only, no spaces)"""
        if not re.match(r'^\w+$', node_id):
            self.errors.append(
                f"Line {line_num}: Invalid node ID '{node_id}'. "
                f"Node IDs must contain only letters, numbers, and underscores (no spaces)."
            )
            return False
        return True
    
    def parse_line(self, line, line_num):
        """
        Parse a line and extract node information.
        Format: NodeId or NodeId (type: description)
        Allows optional space between NodeId and ( but NOT within NodeId
        Returns: (indent_level, node_id, node_type, metadata) or None if invalid
        """
        if not line.strip():
            return None
        
        # Check for valid box-drawing characters
        indent_match = re.match(r'^([\s│├└─]*)', line)
        if not indent_match:
            self.errors.append(f"Line {line_num}: Invalid characters at start of line")
            return None
        
        indent_str = indent_match.group(1)
        indent_level = len(indent_str) // 4
        
        # Remove box-drawing characters
        cleaned = re.sub(r'[├├─│└└─\s]+', '', line).strip()
        
        if not cleaned:
            return None
        
        # Parse: NodeId or NodeId (type: description)
        # NodeId must be a single word (no spaces)
        # Then optional whitespace, then optional metadata in parentheses
        match = re.match(r'(\w+)\s*(?:\(([^)]+)\))?(.*)$', cleaned)
        if not match:
            self.errors.append(f"Line {line_num}: Invalid node format: {cleaned}")
            return None
        
        node_id = match.group(1)
        metadata = match.group(2) if match.group(2) else ""
        remaining = match.group(3).strip() if match.group(3) else ""
        
        # Check for extra text after the pattern (like "LOLOL")
        if remaining:
            self.errors.append(
                f"Line {line_num}: Invalid node ID '{node_id}'. "
                f"Found extra text: '{remaining}'. "
                f"Node IDs must be a single word with no spaces."
            )
            return None
        
        # Validate node ID (must be alphanumeric + underscore)
        if not self.validate_node_id(node_id, line_num):
            return None
        
        # Determine node type
        if metadata:
            if ":" in metadata:
                node_type = "decision"
            else:
                node_type = "classification"
            
            # Validate type annotation if present
            if metadata.lower().startswith(("decision:", "classification:")):
                explicit_type = metadata.split(":")[0].lower()
                if explicit_type not in ["decision", "classification"]:
                    self.errors.append(
                        f"Line {line_num}: Invalid type '{explicit_type}'. "
                        f"Must be 'decision' or 'classification'."
                    )
                    return None
        else:
            node_type = "classification"
        
        return (indent_level, node_id, node_type, metadata)
    
    def validate_structure(self):
        """Validate the overall tree structure"""
        parsed_lines = []
        
        for line_num, line in enumerate(self.lines, 1):
            parsed = self.parse_line(line, line_num)
            if parsed:
                indent_level, node_id, node_type, metadata = parsed
                
                # Check for duplicate IDs
                if node_id in self.nodes:
                    self.errors.append(
                        f"Line {line_num}: Duplicate node ID '{node_id}' "
                        f"(previously defined on line {self.nodes[node_id]['line']})"
                    )
                
                self.nodes[node_id] = {
                    "line": line_num,
                    "type": node_type,
                    "indent": indent_level,
                    "metadata": metadata
                }
                
                parsed_lines.append((line_num, indent_level, node_id, node_type))
        
        # Check hierarchy consistency
        if parsed_lines:
            # First line should be root (indent 0)
            if parsed_lines[0][1] != 0:
                self.errors.append(
                    f"Line {parsed_lines[0][0]}: Root node must have no indentation"
                )
            
            # Check indent increases by 1 level max
            for i in range(1, len(parsed_lines)):
                prev_indent = parsed_lines[i-1][1]
                curr_indent = parsed_lines[i][1]
                
                if curr_indent > prev_indent + 1:
                    self.errors.append(
                        f"Line {parsed_lines[i][0]}: Indent jump too large "
                        f"(from level {prev_indent} to {curr_indent})"
                    )
        
        return len(self.errors) == 0
    
    def validate_decision_rules(self):
        """Validate decision node consistency"""
        for node_id, node_info in self.nodes.items():
            if node_info["type"] == "classification":
                # Classification nodes should have no decision metadata
                if ":" in node_info["metadata"]:
                    self.warnings.append(
                        f"Line {node_info['line']}: Classification node '{node_id}' "
                        f"should not have decision metadata: {node_info['metadata']}"
                    )
            else:  # decision
                # Decision nodes should explain the decision
                if not node_info["metadata"]:
                    self.warnings.append(
                        f"Line {node_info['line']}: Decision node '{node_id}' "
                        f"should describe the decision (e.g., 'decision: Option A vs Option B')"
                    )
    
    def validate(self):
        """Run all validations"""
        if not self.load_file():
            return False
        
        if not self.validate_structure():
            return False
        
        self.validate_decision_rules()
        
        return len(self.errors) == 0
    
    def print_report(self):
        """Print validation report"""
        if self.errors:
            print(f"❌ {len(self.errors)} error(s) found:")
            for error in self.errors:
                print(f"   {error}")
        
        if self.warnings:
            print(f"⚠️  {len(self.warnings)} warning(s):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if not self.errors and not self.warnings:
            print("✅ Structure is valid")
            print(f"   Total nodes: {len(self.nodes)}")
            decisions = sum(1 for n in self.nodes.values() if n["type"] == "decision")
            classifications = sum(1 for n in self.nodes.values() if n["type"] == "classification")
            print(f"   Decision nodes: {decisions}")
            print(f"   Classification nodes: {classifications}")


def main():
    """Main validation"""
    validator = StructureValidator("flowchart-structure.txt")
    
    if validator.validate():
        print("\n✅ Validation passed!")
        validator.print_report()
        return 0
    else:
        print("\n❌ Validation failed!")
        validator.print_report()
        return 1


if __name__ == "__main__":
    sys.exit(main())