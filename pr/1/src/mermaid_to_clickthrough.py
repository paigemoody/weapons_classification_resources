"""
Convert a Mermaid flowchart into an interactive click-through HTML guide.

Features
--------
- Input: .mmd or .mermaid
- Output: standalone .html
- Auto-root detection (in-degree 0 nodes)
- Synthetic start question when multiple roots exist
- Option labels prefer edge labels (`A --> |Label| B`)
- Rich edge labels supported (HTML like <h1>, <p>, <img>)
- Cycle detection with clear error/warning and exit
- Preserves HTML/markdown-ish label formatting (including <img>)
- Breadcrumb path shown; click any breadcrumb to jump back
- Option images precedence:
    1) Edge label image (<img> on edge label)
    2) Destination node image (<img> in destination node label)

Usage
-----
python3 src/mermaid_to_clickthrough.py \
  --input-mmd weapons-classification-flowchart.mmd \
  --output-html classification-guide.html \
  --app-name "[DEMO] Weapons Classification Guide"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional


# Edge formats supported:
#   A --> B
#   A --> |Label| B
#   A --> |"Label with HTML"| B
EDGE_RE = re.compile(
    r"""^\s*([A-Za-z0-9_]+)\s*-->\s*(?:\|((?:"[^"]*"|[^|])*)\|\s*)?([A-Za-z0-9_]+)\s*$""",
    re.DOTALL,
)

# Node format:
#   NodeId["Some <br/> Label"]
NODE_RE = re.compile(
    r'^\s*([A-Za-z0-9_]+)\s*\[\s*"([\s\S]*?)"\s*\]\s*$',
    re.DOTALL,
)

IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE | re.DOTALL)
SRC_RE = re.compile(r"""src\s*=\s*(['"])(.*?)\1""", re.IGNORECASE | re.DOTALL)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
P_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)


def extract_first_img_tag(html: str) -> Optional[str]:
    m = IMG_TAG_RE.search(html or "")
    return m.group(0) if m else None


def extract_img_src(img_tag: str) -> str:
    m = SRC_RE.search(img_tag or "")
    return m.group(2).strip() if m else ""


def strip_img_tags(html: str) -> str:
    return re.sub(r"<img\b[^>]*>", "", html or "", flags=re.IGNORECASE | re.DOTALL).strip()


def mmd_label_to_html(raw: str) -> str:
    """
    Keep HTML formatting and basic markdown-bold conversion.
    - Converts '**x**' -> '<strong>x</strong>'
    - Leaves <img>, <br>, and other HTML intact
    """
    txt = (raw or "").strip()
    # Unescape \" if present in quoted edge labels
    txt = txt.replace('\\"', '"')
    txt = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", txt, flags=re.DOTALL)
    return txt


def strip_html_for_plain(text: str) -> str:
    """Create plain text fallback from html-ish label."""
    t = re.sub(r"<br\s*/?>", " ", text or "", flags=re.IGNORECASE)
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def fallback_label(node_id: str) -> str:
    return node_id.replace("_", " ")


def parse_edge_label(edge_html: str, fallback_text: str) -> Dict[str, str]:
    """
    Parse edge label into:
      - titleHtml: option title markup
      - contextHtml: optional supporting <p> blocks
      - plainLabel: fallback plain text
      - edgeImageTag / edgeImageSrc: optional image from edge label

    Rules:
      - If <h1> exists, title is first <h1> content
      - context is concatenated <p> blocks
      - otherwise title is whole edge label (minus <img>)
    """
    html = mmd_label_to_html(edge_html or "")

    edge_img_tag = extract_first_img_tag(html) or ""
    edge_img_src = extract_img_src(edge_img_tag) if edge_img_tag else ""

    html_wo_img = strip_img_tags(html)

    if not html_wo_img:
        plain = strip_html_for_plain(fallback_text) or fallback_text
        return {
            "titleHtml": plain,
            "contextHtml": "",
            "plainLabel": plain,
            "edgeImageTag": edge_img_tag,
            "edgeImageSrc": edge_img_src,
        }

    h1_match = H1_RE.search(html_wo_img)
    p_matches = P_RE.findall(html_wo_img)

    if h1_match:
        title_html = h1_match.group(1).strip()
    else:
        title_html = html_wo_img.strip()

    context_html = ""
    if p_matches:
        context_html = "".join(f"<p>{p.strip()}</p>" for p in p_matches)

    plain = strip_html_for_plain(title_html) or strip_html_for_plain(html_wo_img) or fallback_text

    return {
        "titleHtml": title_html,
        "contextHtml": context_html,
        "plainLabel": plain,
        "edgeImageTag": edge_img_tag,
        "edgeImageSrc": edge_img_src,
    }


class Graph:
    def __init__(self) -> None:
        self.node_html: Dict[str, str] = {}                # node_id -> html label
        self.children: Dict[str, List[str]] = {}           # node_id -> [child_ids in file order]
        self.edge_label: Dict[Tuple[str, str], str] = {}   # (src,dst) -> raw html label
        self.indegree: Dict[str, int] = {}
        self.nodes_in_order: List[str] = []                # first-seen order

    def ensure_node(self, nid: str) -> None:
        if nid not in self.children:
            self.children[nid] = []
        if nid not in self.indegree:
            self.indegree[nid] = 0
        if nid not in self.node_html:
            self.node_html[nid] = fallback_label(nid)
        if nid not in self.nodes_in_order:
            self.nodes_in_order.append(nid)

    def add_node_label(self, nid: str, raw_label: str) -> None:
        self.ensure_node(nid)
        self.node_html[nid] = mmd_label_to_html(raw_label)

    def add_edge(self, src: str, dst: str, lbl: Optional[str]) -> None:
        self.ensure_node(src)
        self.ensure_node(dst)
        self.children[src].append(dst)
        self.indegree[dst] += 1
        if lbl is not None:
            cleaned = lbl.strip()
            # strip wrapping quotes if edge was |"..."|
            if len(cleaned) >= 2 and cleaned[0] == '"' and cleaned[-1] == '"':
                cleaned = cleaned[1:-1]
            self.edge_label[(src, dst)] = mmd_label_to_html(cleaned)


def parse_mermaid(text: str) -> Graph:
    g = Graph()

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        s = line.strip()

        if not s:
            continue
        if s.startswith("%%"):
            continue
        if s.startswith("flowchart"):
            continue

        m_node = NODE_RE.match(line)
        if m_node:
            nid, raw = m_node.groups()
            g.add_node_label(nid, raw)
            continue

        m_edge = EDGE_RE.match(line)
        if m_edge:
            src, edge_lbl, dst = m_edge.groups()
            g.add_edge(src, dst, edge_lbl)
            continue

    return g


def detect_cycle(g: Graph) -> Optional[List[str]]:
    """
    DFS cycle detection.
    Returns one cycle path if found, else None.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {n: WHITE for n in g.children}
    parent: Dict[str, Optional[str]] = {n: None for n in g.children}

    def dfs(u: str) -> Optional[List[str]]:
        color[u] = GRAY
        for v in g.children.get(u, []):
            if color[v] == WHITE:
                parent[v] = u
                found = dfs(v)
                if found:
                    return found
            elif color[v] == GRAY:
                cycle = [v]
                cur = u
                while cur is not None and cur != v:
                    cycle.append(cur)
                    cur = parent[cur]
                cycle.append(v)
                cycle.reverse()
                return cycle
        color[u] = BLACK
        return None

    for n in g.nodes_in_order:
        if color[n] == WHITE:
            found = dfs(n)
            if found:
                return found
    return None


def top_nodes(g: Graph) -> List[str]:
    return [n for n in g.nodes_in_order if g.indegree.get(n, 0) == 0]


def option_label(g: Graph, src: str, dst: str) -> str:
    # Prefer parsed edge label plain text
    edge_html = g.edge_label.get((src, dst), "")
    if edge_html:
        parsed = parse_edge_label(edge_html, fallback_text=fallback_label(dst))
        return parsed["plainLabel"]

    # Fallback to child node label plain text
    child_html = g.node_html.get(dst, fallback_label(dst))
    plain = strip_html_for_plain(child_html)
    return plain or fallback_label(dst)


def build_node(g: Graph, node_id: str) -> dict:
    kids = g.children.get(node_id, [])
    question_html = g.node_html.get(node_id, fallback_label(node_id))

    node_obj = {
        "nodeId": node_id,
        "questionHtml": question_html,
        "questionText": strip_html_for_plain(question_html),
        "options": [],
    }

    for child in kids:
        child_kids = g.children.get(child, [])
        child_html = g.node_html.get(child, fallback_label(child))

        # Parse edge label into title/context/image
        raw_edge_html = g.edge_label.get((node_id, child), "")
        edge_parts = parse_edge_label(raw_edge_html, fallback_text=strip_html_for_plain(child_html))

        # Destination node image
        node_img_tag = extract_first_img_tag(child_html) or ""
        node_img_src = extract_img_src(node_img_tag) if node_img_tag else ""

        # Precedence: edge image first, then destination-node image
        final_img_tag = edge_parts["edgeImageTag"] or node_img_tag
        final_img_src = edge_parts["edgeImageSrc"] or node_img_src

        opt = {
            "label": edge_parts["plainLabel"] or option_label(g, node_id, child),
            "titleHtml": edge_parts["titleHtml"] or option_label(g, node_id, child),
            "contextHtml": edge_parts["contextHtml"] or "",
            "nextNodeId": child,
            "imageTag": final_img_tag,
            "imageSrc": final_img_src,
        }

        if child_kids:
            opt["next"] = build_node(g, child)
        else:
            opt["resultHtml"] = child_html
            opt["resultText"] = strip_html_for_plain(child_html)

        node_obj["options"].append(opt)

    return node_obj


def build_tree(g: Graph) -> dict:
    roots = top_nodes(g)
    if not roots:
        raise ValueError("No top-level node detected (no in-degree-0 nodes found).")

    if len(roots) == 1:
        return build_node(g, roots[0])

    # Synthetic start when multiple top roots
    synthetic = {
        "nodeId": "__synthetic_start__",
        "questionHtml": "Where do you want to start?",
        "questionText": "Where do you want to start?",
        "options": [],
    }
    for r in roots:
        r_html = g.node_html.get(r, fallback_label(r))
        r_img_tag = extract_first_img_tag(r_html) or ""
        r_img_src = extract_img_src(r_img_tag) if r_img_tag else ""
        label_plain = strip_html_for_plain(r_html) or fallback_label(r)

        synthetic["options"].append(
            {
                "label": label_plain,
                "titleHtml": label_plain,
                "contextHtml": "",
                "nextNodeId": r,
                "imageTag": r_img_tag,
                "imageSrc": r_img_src,
                "next": build_node(g, r),
            }
        )

    return synthetic


def make_html(tree: dict, app_name: str) -> str:
    tree_json = json.dumps(tree, ensure_ascii=False, indent=2)

    template = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>__APP_NAME_ESC__</title>
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
  <div id="root"></div>

  <script type="text/babel">
    const { useMemo, useState } = React;

    const APP_NAME = __APP_NAME_JSON__;
    const TREE = __TREE_JSON__;

    function ClassificationGuide() {
      const [path, setPath] = useState([]); // each item: { optionIndex, optionLabel, nodeQuestionText }
      const [result, setResult] = useState(null); // { text, html }

      const getCurrentNode = () => {
        let node = TREE;
        for (const step of path) {
          const opt = node?.options?.[step.optionIndex];
          if (!opt) return node;
          if (opt.next) node = opt.next;
          else return node;
        }
        return node;
      };

      const currentNode = result ? null : getCurrentNode();

      const choose = (idx) => {
        const node = getCurrentNode();
        if (!node) return;
        const opt = node.options?.[idx];
        if (!opt) return;

        const nextPath = [
          ...path,
          {
            optionIndex: idx,
            optionLabel: opt.label || "Option",
            nodeQuestionText: node.questionText || "Step"
          }
        ];

        if (opt.resultHtml || opt.resultText) {
          setPath(nextPath);
          setResult({
            text: opt.resultText || "",
            html: opt.resultHtml || opt.resultText || ""
          });
        } else if (opt.next) {
          setPath(nextPath);
        }
      };

      const goToStep = (stepIndex) => {
        if (stepIndex < 0) {
          setPath([]);
          setResult(null);
          return;
        }

        const newPath = path.slice(0, stepIndex + 1);
        setResult(null);
        setPath(newPath);
      };

      const backOne = () => {
        if (result) {
          setResult(null);
          return;
        }
        if (path.length > 0) {
          setPath(path.slice(0, -1));
        }
      };

      const reset = () => {
        setPath([]);
        setResult(null);
      };

      const breadcrumbItems = useMemo(() => {
        return path.map((p, i) => ({
          label: p.optionLabel,
          stepIndex: i
        }));
      }, [path]);

      return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h1 className="text-3xl font-bold text-slate-800 mb-4 text-center">{APP_NAME}</h1>

              <div className="mb-6">
                <div className="text-xs uppercase tracking-wide text-slate-500 mb-2">Path</div>
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <button
                    onClick={() => goToStep(-1)}
                    className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700"
                  >
                    Start
                  </button>
                  {breadcrumbItems.map((b, i) => (
                    <React.Fragment key={i}>
                      <span className="text-slate-400">→</span>
                      <button
                        onClick={() => goToStep(i)}
                        className="px-2 py-1 rounded bg-blue-50 hover:bg-blue-100 text-blue-800"
                        title={`Go back to step ${i + 1}`}
                      >
                        {b.label}
                      </button>
                    </React.Fragment>
                  ))}
                </div>
              </div>

              {result && (
                <div className="text-center">
                  <h2 className="text-xl font-semibold text-slate-700 mb-4">Classification Complete</h2>
                  <div
                    className="inline-block bg-blue-100 text-blue-900 px-5 py-4 rounded-lg text-lg font-semibold"
                    dangerouslySetInnerHTML={{ __html: result.html }}
                  />
                  <div className="mt-8 flex gap-3 justify-center">
                    <button
                      onClick={backOne}
                      className="px-4 py-2 text-slate-700 hover:text-slate-900"
                    >
                      ← Back
                    </button>
                    <button
                      onClick={reset}
                      className="px-4 py-2 rounded bg-slate-700 text-white hover:bg-slate-800"
                    >
                      Start Over
                    </button>
                  </div>
                </div>
              )}

              {!result && currentNode && (
                <div>
                  <h2
                    className="text-xl font-semibold text-slate-800 mb-6 text-center"
                    dangerouslySetInnerHTML={{ __html: currentNode.questionHtml }}
                  />

                  <div className="space-y-3">
                    {currentNode.options.map((opt, idx) => (
                      <button
                        key={idx}
                        onClick={() => choose(idx)}
                        className="w-full bg-white border-2 border-slate-300 rounded-lg p-4 hover:border-blue-500 hover:bg-blue-50 transition-all text-left"
                      >
                        <div className="flex items-start gap-4">
                          <div className="w-24 h-24 bg-slate-100 rounded flex-shrink-0 flex items-center justify-center overflow-hidden">
                            {opt.imageSrc ? (
                              <img
                                src={opt.imageSrc}
                                alt={opt.label}
                                className="w-full h-full object-contain"
                              />
                            ) : opt.imageTag ? (
                              <span
                                className="w-full h-full flex items-center justify-center"
                                dangerouslySetInnerHTML={{ __html: opt.imageTag }}
                              />
                            ) : (
                              <span className="text-slate-400 text-xs">No image</span>
                            )}
                          </div>

                          <div className="min-w-0">
                            <div
                              className="text-lg font-semibold text-slate-800"
                              dangerouslySetInnerHTML={{ __html: opt.titleHtml || opt.label }}
                            />
                            {opt.contextHtml && (
                              <div
                                className="mt-1 text-sm text-slate-600"
                                dangerouslySetInnerHTML={{ __html: opt.contextHtml }}
                              />
                            )}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>

                  <div className="mt-8 flex gap-3">
                    <button
                      onClick={backOne}
                      disabled={path.length === 0}
                      className={`px-4 py-2 ${path.length === 0 ? "text-slate-300 cursor-not-allowed" : "text-slate-700 hover:text-slate-900"}`}
                    >
                      ← Back
                    </button>
                    <button
                      onClick={reset}
                      className="ml-auto px-4 py-2 text-slate-700 hover:text-slate-900"
                    >
                      Start Over
                    </button>
                  </div>
                </div>
              )}

              {!result && !currentNode && (
                <div className="text-center">
                  <div className="text-red-600 mb-4">
                    Could not render this step.
                  </div>
                  <div className="flex gap-3 justify-center">
                    <button onClick={backOne} className="px-4 py-2 text-slate-700 hover:text-slate-900">
                      ← Back
                    </button>
                    <button onClick={reset} className="px-4 py-2 rounded bg-slate-700 text-white hover:bg-slate-800">
                      Start Over
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      );
    }

    const root = ReactDOM.createRoot(document.getElementById("root"));
    root.render(<ClassificationGuide />);
  </script>
</body>
</html>
"""
    return (
        template
        .replace("__APP_NAME_ESC__", app_name)
        .replace("__APP_NAME_JSON__", json.dumps(app_name, ensure_ascii=False))
        .replace("__TREE_JSON__", tree_json)
    )


def ensure_output_html(path_str: str) -> Path:
    p = Path(path_str)
    if p.suffix.lower() != ".html":
        p = p.with_suffix(".html")
    return p


def validate_input_path(path_str: str) -> Path:
    p = Path(path_str)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {p}")
    if p.suffix.lower() not in {".mmd", ".mermaid"}:
        raise ValueError("Input must be a .mmd or .mermaid file")
    return p


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Mermaid flowchart to click-through HTML.")
    parser.add_argument("--input-mmd", required=True, help="Path to .mmd or .mermaid file")
    parser.add_argument("--output-html", required=True, help="Output HTML path")
    parser.add_argument("--app-name", default="Classification Guide", help="UI title")
    args = parser.parse_args()

    try:
        in_path = validate_input_path(args.input_mmd)
        out_path = ensure_output_html(args.output_html)

        text = in_path.read_text(encoding="utf-8")
        g = parse_mermaid(text)

        if not g.nodes_in_order:
            raise ValueError("No Mermaid nodes were parsed from input file.")

        cycle = detect_cycle(g)
        if cycle:
            cycle_str = " -> ".join(cycle)
            print(f"⚠️  Cycle detected in Mermaid chart: {cycle_str}", file=sys.stderr)
            print("⚠️  Aborting. Click-through UI requires an acyclic decision flow.", file=sys.stderr)
            sys.exit(1)

        tree = build_tree(g)
        html = make_html(tree, args.app_name)

        out_path.write_text(html, encoding="utf-8")
        print(f"✅ Wrote: {out_path}")

        roots = top_nodes(g)
        if len(roots) > 1:
            print(f"ℹ️  Multiple top nodes detected ({len(roots)}). Used synthetic start question.")
        else:
            print(f"ℹ️  Root detected: {roots[0]}")

    except Exception as exc:
        print(f"❌ Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
