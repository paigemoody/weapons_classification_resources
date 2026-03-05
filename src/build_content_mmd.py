"""
Merge taxonomy-structure.mmd + content CSVs -> weapons-classification-flowchart.mmd

Pipeline:
  taxonomy-structure.mmd        (structure: node IDs and edges only)
  content/questions.csv         (prompts and images for decision nodes)
  content/options.csv           (names, descriptions, images for edge options)
  content/classifications.csv   (names, ARCS levels, descriptions, images for leaf nodes)
      |
      v
  weapons-classification-flowchart.mmd  (input to mermaid_to_clickthrough.py)

Usage:
  python3 src/build_content_mmd.py \
    --structure taxonomy-structure.mmd \
    --questions content/questions.csv \
    --options content/options.csv \
    --classifications content/classifications.csv \
    --output weapons-classification-flowchart.mmd
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


EDGE_RE = re.compile(r'^\s*([A-Za-z0-9_]+)\s*-->\s*([A-Za-z0-9_]+)\s*$')
NODE_RE = re.compile(r'^\s*([A-Za-z0-9_]+)\s*$')


def parse_structure(text: str) -> Tuple[List[str], List[Tuple[str, str]]]:
    """Parse a structure-only mmd. Returns (nodes_in_order, edges)."""
    nodes_seen: List[str] = []
    nodes_set: Set[str] = set()
    edges: List[Tuple[str, str]] = []

    def ensure(nid: str) -> None:
        if nid not in nodes_set:
            nodes_seen.append(nid)
            nodes_set.add(nid)

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('%%') or line.startswith('flowchart'):
            continue
        m = EDGE_RE.match(line)
        if m:
            src, dst = m.groups()
            ensure(src)
            ensure(dst)
            edges.append((src, dst))
            continue
        m = NODE_RE.match(line)
        if m:
            ensure(m.group(1))

    return nodes_seen, edges


def load_csv(path: Path, key_col: str) -> Dict[str, dict]:
    result: Dict[str, dict] = {}
    with path.open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            key = row.get(key_col, '').strip()
            if key:
                result[key] = {k: (v.strip() if isinstance(v, str) else '') for k, v in row.items() if k is not None}
    return result


def html_label(title: str, description: str = '', image_url: str = '') -> str:
    img = f"<img src='{image_url}' />" if image_url else "<img src='' />"
    return f"<h1>{title}</h1><p>{description}</p>{img}"


def build_mmd(
    nodes: List[str],
    edges: List[Tuple[str, str]],
    questions: Dict[str, dict],
    options: Dict[str, dict],
    classifications: Dict[str, dict],
) -> str:
    has_children: Set[str] = {src for src, _ in edges}
    leaves: Set[str] = set(nodes) - has_children

    lines = ['flowchart TB', '']

    for nid in nodes:
        if nid in leaves:
            c = classifications.get(nid)
            if not c:
                print(f"  warning: no classification content for leaf: {nid}", file=sys.stderr)
            c = c or {}
            label = html_label(
                title=c.get('Name', nid),
                description=c.get('Description', ''),
                image_url=c.get('Image URL', ''),
            )
        else:
            q = questions.get(nid)
            if not q:
                print(f"  warning: no question content for decision node: {nid}", file=sys.stderr)
            q = q or {}
            label = html_label(
                title=q.get('Prompt', nid),
                image_url=q.get('Image URL', ''),
            )
        lines.append(f'  {nid}["{label}"]')

    lines.append('')

    for src, dst in edges:
        opt = options.get(dst)
        if not opt:
            print(f"  warning: no option content for edge {src} -> {dst}", file=sys.stderr)
        opt = opt or {}
        arcs_level = opt.get('ARCS Level', '')
        arcs_name = opt.get('ARCS Name', '')
        arcs_ref = f' (ARCS {arcs_level}: {arcs_name})' if arcs_level and arcs_name else ''
        edge_label = html_label(
            title=opt.get('Option Name', dst),
            description=opt.get('Description', '') + arcs_ref,
            image_url=opt.get('Image URL', ''),
        )
        lines.append(f'  {src} --> |"{edge_label}"| {dst}')

    lines.append('')
    return '\n'.join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge taxonomy structure + content CSVs into an enriched Mermaid file."
    )
    parser.add_argument('--structure', required=True)
    parser.add_argument('--questions', required=True)
    parser.add_argument('--options', required=True)
    parser.add_argument('--classifications', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    structure_path = Path(args.structure)
    if not structure_path.exists():
        print(f"error: structure file not found: {structure_path}", file=sys.stderr)
        sys.exit(1)

    nodes, edges = parse_structure(structure_path.read_text(encoding='utf-8'))
    if not nodes:
        print("error: no nodes parsed from structure file", file=sys.stderr)
        sys.exit(1)

    questions = load_csv(Path(args.questions), 'id')
    options = load_csv(Path(args.options), 'id')
    classifications = load_csv(Path(args.classifications), 'id')

    leaves = set(nodes) - {src for src, _ in edges}
    print(f"Structure: {len(nodes)} nodes, {len(edges)} edges, {len(leaves)} leaves")

    mmd = build_mmd(nodes, edges, questions, options, classifications)

    out_path = Path(args.output)
    out_path.write_text(mmd, encoding='utf-8')
    print(f"Wrote: {out_path}")


if __name__ == '__main__':
    main()
