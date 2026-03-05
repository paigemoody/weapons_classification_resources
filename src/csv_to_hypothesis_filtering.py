"""
Generate a hypothesis-filtering HTML guide directly from content CSVs.

No intermediate Mermaid file needed. The tree structure is derived from
questions.csv (each question row lists its child option IDs), and content
comes from options.csv and classifications.csv.

Usage:
  python3 src/csv_to_hypothesis_filtering.py \
    --questions content/questions.csv \
    --options content/options.csv \
    --classifications content/classifications.csv \
    --output classification-guide-hypothesis-filtering.html \
    --app-name "[DEMO] Weapons Classification Guide (Hypothesis Filtering)"
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import deque
from pathlib import Path
from typing import Dict, List, Set, Tuple


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------

def load_questions(path: Path) -> Tuple[Dict[str, dict], Dict[str, List[str]]]:
    """
    Returns:
      questions: id -> row dict
      children:  id -> [child option ids in order]
    """
    questions: Dict[str, dict] = {}
    children: Dict[str, List[str]] = {}

    with path.open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            qid = row.get('id', '').strip()
            if not qid:
                continue
            questions[qid] = {k: (v.strip() if isinstance(v, str) else '') for k, v in row.items() if k is not None}
            kids = [
                v.strip()
                for k, v in row.items()
                if k and k.startswith('Option') and isinstance(v, str) and v.strip()
            ]
            children[qid] = kids

    return questions, children


def load_csv(path: Path, key_col: str) -> Dict[str, dict]:
    result: Dict[str, dict] = {}
    with path.open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            key = row.get(key_col, '').strip()
            if key:
                result[key] = {k: (v.strip() if isinstance(v, str) else '') for k, v in row.items() if k is not None}
    return result


# ---------------------------------------------------------------------------
# Graph helpers
# ---------------------------------------------------------------------------

def find_roots(questions: Dict[str, dict], children: Dict[str, List[str]]) -> List[str]:
    all_children: Set[str] = {c for kids in children.values() for c in kids}
    return [qid for qid in questions if qid not in all_children]


def find_leaves(children: Dict[str, List[str]], question_ids: Set[str]) -> Set[str]:
    return {c for kids in children.values() for c in kids if c not in question_ids}


def compute_depths(roots: List[str], children: Dict[str, List[str]]) -> Dict[str, int]:
    depths: Dict[str, int] = {}
    queue: deque = deque((r, 0) for r in roots)
    while queue:
        nid, d = queue.popleft()
        if nid in depths:
            continue
        depths[nid] = d
        for child in children.get(nid, []):
            queue.append((child, d + 1))
    return depths


def compute_leaf_sets(
    roots: List[str],
    children: Dict[str, List[str]],
    leaves: Set[str],
) -> Dict[str, Set[str]]:
    memo: Dict[str, Set[str]] = {}

    def leaf_set(nid: str) -> Set[str]:
        if nid in memo:
            return memo[nid]
        if nid in leaves:
            memo[nid] = {nid}
            return memo[nid]
        result: Set[str] = set()
        for child in children.get(nid, []):
            result |= leaf_set(child)
        memo[nid] = result
        return result

    for r in roots:
        leaf_set(r)
    return memo


def compute_leaf_characteristics(
    roots: List[str],
    children: Dict[str, List[str]],
    leaves: Set[str],
    options: Dict[str, dict],
) -> Dict[str, List[dict]]:
    """
    For each leaf, collect the characteristics implied by every option
    on its path from the root. Each characteristic is {key, value}.
    Order follows the path from root to leaf.
    """
    result: Dict[str, List[dict]] = {}

    def dfs(nid: str, path_options: List[str]) -> None:
        if nid in leaves:
            chars = []
            for opt_id in path_options:
                opt = options.get(opt_id, {})
                key = opt.get('Defining Characteristic', '')
                value = opt.get('Characteristic Value', '')
                if key and value:
                    chars.append({'key': key, 'value': value})
            result[nid] = chars
            return
        for child in children.get(nid, []):
            dfs(child, path_options + [child])

    for root in roots:
        dfs(root, [])

    return result


# ---------------------------------------------------------------------------
# Model builder
# ---------------------------------------------------------------------------

def build_model(
    questions: Dict[str, dict],
    children: Dict[str, List[str]],
    options: Dict[str, dict],
    classifications: Dict[str, dict],
) -> dict:
    question_ids = set(questions.keys())
    roots = find_roots(questions, children)
    leaves = find_leaves(children, question_ids)
    depths = compute_depths(roots, children)
    leaf_sets = compute_leaf_sets(roots, children, leaves)
    leaf_characteristics = compute_leaf_characteristics(roots, children, leaves, options)

    q_objs: List[dict] = []
    option_to_leaf_ids: Dict[str, List[str]] = {}

    for qid, q_row in questions.items():
        opt_objs: List[dict] = []
        for child_id in children.get(qid, []):
            opt = options.get(child_id, {})
            option_id = f"{qid}__TO__{child_id}"

            arcs_level = opt.get('ARCS Level', '')
            arcs_name = opt.get('ARCS Name', '')
            context_parts = []
            if opt.get('Description'):
                context_parts.append(f"<p>{opt['Description']}</p>")
            if arcs_level and arcs_name:
                context_parts.append(
                    f'<p class="text-xs text-slate-400 mt-1">Points toward ARCS {arcs_level}: {arcs_name}</p>'
                )
            opt_objs.append({
                'optionId': option_id,
                'dstNodeId': child_id,
                'titleHtml': opt.get('Option Name', child_id),
                'contextHtml': ''.join(context_parts),
                'plainLabel': opt.get('Option Name', child_id),
                'imageSrc': opt.get('Image URL', ''),
            })

            option_to_leaf_ids[option_id] = sorted(leaf_sets.get(child_id, set()))

        q_objs.append({
            'nodeId': qid,
            'questionHtml': q_row.get('Prompt', qid),
            'questionText': q_row.get('Prompt', qid),
            'imageSrc': q_row.get('Image URL', ''),
            'options': opt_objs,
        })

    leaf_objs: List[dict] = []
    for leaf_id in sorted(leaves):
        c = classifications.get(leaf_id, {})
        name = c.get('Name', leaf_id)

        arcs_parts = [
            c[level]
            for level in ('Class', 'Group', 'Type', 'Sub-type')
            if c.get(level)
        ]

        leaf_objs.append({
            'leafId': leaf_id,
            'leafText': name,
            'imageSrc': c.get('Image URL', ''),
            'description': c.get('Description', ''),
            'arcsParts': arcs_parts,
            'characteristics': leaf_characteristics.get(leaf_id, []),
            'depth': depths.get(leaf_id, 0),
        })

    all_candidates: Set[str] = set()
    for r in roots:
        all_candidates |= leaf_sets.get(r, set())

    return {
        'roots': roots,
        'questions': q_objs,
        'leaves': leaf_objs,
        'optionToLeafIds': option_to_leaf_ids,
        'initialCandidates': sorted(all_candidates),
    }


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

def make_html(model: dict, app_name: str) -> str:
    model_json = json.dumps(model, ensure_ascii=False, indent=2)

    template = r"""<!DOCTYPE html>
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
<body class="bg-slate-50">
  <div id="root"></div>

  <script type="text/babel">
    const { useEffect, useMemo, useState } = React;

    const APP_NAME = __APP_NAME_JSON__;
    const MODEL = __MODEL_JSON__;

    function intersect(a, b) {
      const setB = new Set(b);
      return a.filter(x => setB.has(x));
    }

    function sortHypotheses(hyps) {
      return [...hyps].sort((x, y) => {
        if (y.depth !== x.depth) return y.depth - x.depth;
        return (x.leafText || "").localeCompare(y.leafText || "");
      });
    }

    function App() {
      const [activeQuestionId, setActiveQuestionId] = useState(MODEL.questions[0]?.nodeId || null);
      const [answers, setAnswers] = useState({});
      const [unknowns, setUnknowns] = useState({});
      const [errorMsg, setErrorMsg] = useState("");

      const candidates = useMemo(() => {
        let cur = MODEL.initialCandidates;
        for (const [, optionId] of Object.entries(answers)) {
          cur = intersect(cur, MODEL.optionToLeafIds[optionId] || []);
        }
        return cur;
      }, [answers]);

      const leafById = useMemo(() => {
        const m = new Map();
        for (const lf of MODEL.leaves) m.set(lf.leafId, lf);
        return m;
      }, []);

      const rankedHypotheses = useMemo(() => {
        return sortHypotheses(candidates.map(id => leafById.get(id)).filter(Boolean));
      }, [candidates, leafById]);


      const questionMeta = useMemo(() => {
        const meta = new Map();
        for (const q of MODEL.questions) {
          const seen = new Set();
          for (const opt of q.options) {
            for (const id of intersect(candidates, MODEL.optionToLeafIds[opt.optionId] || [])) {
              seen.add(id);
            }
          }
          const union = [...seen];
          meta.set(q.nodeId, {
            canNarrow: union.length > 0 && union.length < candidates.length,
            isRelevant: union.length > 0,
          });
        }
        return meta;
      }, [candidates]);

      useEffect(() => {
        if (!activeQuestionId) return;
        const meta = questionMeta.get(activeQuestionId);
        if (meta && meta.isRelevant) return;
        const next = MODEL.questions.find(q => questionMeta.get(q.nodeId)?.isRelevant);
        if (next) setActiveQuestionId(next.nodeId);
      }, [activeQuestionId, questionMeta]);

      const resetAll = () => {
        setAnswers({});
        setUnknowns({});
        setErrorMsg("");
        setActiveQuestionId(MODEL.questions[0]?.nodeId || null);
      };

      const chooseOption = (nodeId, optionId) => {
        setErrorMsg("");
        let cur = MODEL.initialCandidates;
        for (const [nid, oid] of Object.entries({ ...answers, [nodeId]: optionId })) {
          cur = intersect(cur, MODEL.optionToLeafIds[oid] || []);
        }
        if (cur.length === 0) {
          setErrorMsg("That choice conflicts with earlier answers. Try a different option, or remove a previous answer.");
          return;
        }
        setAnswers(prev => ({ ...prev, [nodeId]: optionId }));
        setUnknowns(prev => { const n = { ...prev }; delete n[nodeId]; return n; });
      };

      const markUnknown = (nodeId) => {
        setErrorMsg("");
        setAnswers(prev => { const n = { ...prev }; delete n[nodeId]; return n; });
        setUnknowns(prev => ({ ...prev, [nodeId]: true }));
      };

      const removeAnswer = (nodeId) => {
        setErrorMsg("");
        setAnswers(prev => { const n = { ...prev }; delete n[nodeId]; return n; });
        setUnknowns(prev => { const n = { ...prev }; delete n[nodeId]; return n; });
      };

      const activeQuestion = useMemo(
        () => MODEL.questions.find(q => q.nodeId === activeQuestionId) || null,
        [activeQuestionId]
      );

      const answerChips = useMemo(() => {
        return MODEL.questions.flatMap(q => {
          const optId = answers[q.nodeId];
          if (!optId) return [];
          const opt = q.options.find(o => o.optionId === optId);
          return [{ nodeId: q.nodeId, questionText: q.questionText, optionLabel: opt?.plainLabel || "Selected" }];
        });
      }, [answers]);

      return (
        <div className="min-h-screen p-5 md:p-8">
          <div className="max-w-6xl mx-auto">

            <div className="mb-6">
              <h1 className="text-2xl md:text-3xl font-bold text-slate-900">{APP_NAME}</h1>
              <p className="text-slate-600 mt-2 max-w-3xl">
                Start anywhere. Answer only what you can observe. Each answer narrows the list of possible classifications.
              </p>
            </div>

            {errorMsg && (
              <div className="mb-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-800">
                {errorMsg}
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

              {/* Left: Question menu */}
              <div className="lg:col-span-4">
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                  <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
                    <div className="font-semibold text-slate-800">Questions</div>
                    <button onClick={resetAll} className="text-sm text-slate-600 hover:text-slate-900">Reset</button>
                  </div>
                  <div className="max-h-[70vh] overflow-auto">
                    {MODEL.questions.map((q) => {
                      const isAnswered = !!answers[q.nodeId];
                      const isUnknown = !!unknowns[q.nodeId];
                      const meta = questionMeta.get(q.nodeId) || { canNarrow: true, isRelevant: true };
                      const isActive = q.nodeId === activeQuestionId;
                      const selectedOption = isAnswered
                        ? q.options.find(o => o.optionId === answers[q.nodeId])
                        : null;
                      return (
                        <div
                          key={q.nodeId}
                          className={[
                            "px-4 py-3 border-b border-slate-100 cursor-pointer",
                            isActive ? "bg-blue-50" : "bg-white hover:bg-slate-50",
                            !meta.isRelevant ? "opacity-50" : "",
                          ].join(" ")}
                          onClick={() => setActiveQuestionId(q.nodeId)}
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <div className="text-sm font-medium text-slate-900 truncate">
                                {q.questionText || q.nodeId}
                              </div>
                              <div className="mt-1 flex items-center gap-2">
                                {isAnswered ? (
                                  <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 truncate max-w-[16rem]">
                                    {selectedOption?.plainLabel || "Answered"}
                                  </span>
                                ) : (
                                  <>
                                    <span className={`text-xs px-2 py-0.5 rounded-full ${isUnknown ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-700"}`}>
                                      {isUnknown ? "Unknown" : "Unanswered"}
                                    </span>
                                    <span className={`text-xs px-2 py-0.5 rounded-full ${meta.canNarrow ? "bg-blue-100 text-blue-800" : "bg-slate-100 text-slate-600"}`}>
                                      {meta.canNarrow ? "Can narrow" : "Won't narrow"}
                                    </span>
                                  </>
                                )}
                              </div>
                            </div>
                            {(isAnswered || isUnknown) && (
                              <button
                                className="text-xs text-slate-600 hover:text-slate-900"
                                onClick={(e) => { e.stopPropagation(); removeAnswer(q.nodeId); }}
                              >
                                Remove
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="mt-4 bg-white rounded-xl shadow-sm border border-slate-200 p-4">
                  <div className="font-semibold text-slate-800 mb-2">Your answers</div>
                  {answerChips.length === 0 ? (
                    <div className="text-sm text-slate-600">No answers yet. Pick any question to start.</div>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {answerChips.map((a) => (
                        <button
                          key={a.nodeId}
                          onClick={() => setActiveQuestionId(a.nodeId)}
                          className="text-left text-xs px-3 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800"
                        >
                          <div className="font-semibold">{a.optionLabel}</div>
                          <div className="text-slate-600 truncate max-w-[14rem]">{a.questionText}</div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Center: Active question */}
              <div className="lg:col-span-5">
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 md:p-6">
                  {!activeQuestion ? (
                    <div className="text-slate-700">No question selected.</div>
                  ) : (
                    <div>
                      {activeQuestion.imageSrc && (
                        <img
                          src={activeQuestion.imageSrc}
                          alt={activeQuestion.questionText}
                          className="w-full max-h-48 object-contain rounded-lg mb-4 bg-slate-50"
                        />
                      )}
                      <div className="text-lg font-semibold text-slate-900 mb-5">
                        {activeQuestion.questionText}
                      </div>
                      <div className="space-y-3">
                        {activeQuestion.options.map((opt) => {
                          const isSelected = answers[activeQuestion.nodeId] === opt.optionId;
                          return (
                            <button
                              key={opt.optionId}
                              onClick={() => chooseOption(activeQuestion.nodeId, opt.optionId)}
                              className={[
                                "w-full text-left rounded-xl border p-4 transition",
                                isSelected
                                  ? "border-blue-500 bg-blue-50"
                                  : "border-slate-200 hover:border-blue-400 hover:bg-slate-50",
                              ].join(" ")}
                            >
                              <div className="flex gap-4 items-start">
                                {opt.imageSrc && (
                                  <div className="w-20 h-20 bg-slate-100 rounded-lg flex items-center justify-center overflow-hidden flex-shrink-0">
                                    <img
                                      src={opt.imageSrc}
                                      alt={opt.plainLabel}
                                      className="w-full h-full object-contain"
                                    />
                                  </div>
                                )}
                                <div className="min-w-0">
                                  <div className="text-base font-semibold text-slate-900"
                                    dangerouslySetInnerHTML={{ __html: opt.titleHtml || opt.plainLabel }}
                                  />
                                  {opt.contextHtml && (
                                    <div className="mt-1 text-sm text-slate-600"
                                      dangerouslySetInnerHTML={{ __html: opt.contextHtml }}
                                    />
                                  )}
                                </div>
                              </div>
                            </button>
                          );
                        })}
                      </div>
                      <div className="mt-5">
                        <button
                          onClick={() => markUnknown(activeQuestion.nodeId)}
                          className="px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800"
                        >
                          I don't know
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Right: Hypotheses */}
              <div className="lg:col-span-3">
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                  <div className="px-4 py-3 border-b border-slate-200">
                    <div className="font-semibold text-slate-800">Possible Classifications</div>
                    <div className="text-sm text-slate-600 mt-1">
                      {candidates.length} remaining
                    </div>
                  </div>
                  <div className="p-4 space-y-3">
                    {rankedHypotheses.length === 0 ? (
                      <div className="text-sm text-slate-700">No classifications remain.</div>
                    ) : (
                      rankedHypotheses.map((h) => (
                        <div key={h.leafId} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                          {h.imageSrc && (
                            <img
                              src={h.imageSrc}
                              alt={h.leafText}
                              className="w-full max-h-24 object-contain rounded mb-2 bg-white"
                            />
                          )}
                          <div className="text-sm font-semibold text-slate-900">{h.leafText}</div>
                          {h.arcsParts.length > 0 && (
                            <div className="mt-1 text-xs text-slate-500">
                              {h.arcsParts.join(" \u203a ")}
                            </div>
                          )}
                          {h.characteristics.length > 0 && (
                            <div className="mt-2 space-y-1">
                              {h.characteristics.map((c, i) => (
                                <div key={i} className="flex gap-1 items-baseline">
                                  <span className="text-xs text-slate-500 shrink-0">{c.key}:</span>
                                  <span className="text-xs text-slate-700">{c.value}</span>
                                </div>
                              ))}
                            </div>
                          )}
                          {h.description && (
                            <div className="mt-2 text-xs text-slate-600">{h.description}</div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>
      );
    }

    const root = ReactDOM.createRoot(document.getElementById("root"));
    root.render(<App />);
  </script>
</body>
</html>
"""
    return (
        template
        .replace("__APP_NAME_ESC__", app_name)
        .replace("__APP_NAME_JSON__", json.dumps(app_name, ensure_ascii=False))
        .replace("__MODEL_JSON__", model_json)
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate hypothesis-filtering HTML from content CSVs."
    )
    parser.add_argument('--questions', required=True)
    parser.add_argument('--options', required=True)
    parser.add_argument('--classifications', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--app-name', default="Classification Guide (Hypothesis Filtering)")
    args = parser.parse_args()

    questions, children = load_questions(Path(args.questions))
    options = load_csv(Path(args.options), 'id')
    classifications = load_csv(Path(args.classifications), 'id')

    if not questions:
        print("error: no questions loaded", file=sys.stderr)
        sys.exit(1)

    model = build_model(questions, children, options, classifications)

    print(f"Questions: {len(model['questions'])}, Leaves: {len(model['leaves'])}")

    html = make_html(model, args.app_name)
    out_path = Path(args.output)
    out_path.write_text(html, encoding='utf-8')
    print(f"Wrote: {out_path}")


if __name__ == '__main__':
    main()
