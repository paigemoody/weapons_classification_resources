"""
Build a hypothesis-filtering HTML guide from characteristic columns in classifications.csv.

Any column beyond the fixed set is treated as an observable characteristic group.
Column header = question label, cell value = option label. This produces the same
UI as csv_to_hypothesis_filtering.py but with fewer, cross-cutting questions
(e.g., one "Action mechanism" question covers both rifles and shotguns).

Usage:
  python3 src/csv_to_faceted_filtering.py \
    --classifications content/classifications.csv \
    --output classification-guide-faceted.html \
    --app-name "[DEMO] Weapons Classification Guide (Faceted Filtering)"
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

FIXED_COLS = {
    'id', 'Name', 'Class', 'Group', 'Type', 'Sub-type',
    'Description', 'Image URL', 'Image Caption',
}


def load_classifications(path: Path) -> Tuple[List[dict], List[str]]:
    """Return (rows, characteristic_columns)."""
    rows = []
    char_cols: List[str] = []

    with path.open(encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_cols = [c for c in (reader.fieldnames or []) if c is not None]
        char_cols = [c for c in all_cols if c.strip() and c not in FIXED_COLS]
        for row in reader:
            id_ = row.get('id', '').strip()
            if not id_:
                continue
            rows.append({k: (v.strip() if isinstance(v, str) else '') for k, v in row.items() if k is not None})

    return rows, char_cols


def build_model(rows: List[dict], char_cols: List[str]) -> dict:
    all_leaf_ids = [r['id'] for r in rows]

    # Build optionToLeafIds and question objects from characteristic columns
    option_to_leaf_ids: Dict[str, List[str]] = {}
    q_objs: List[dict] = []

    for col in char_cols:
        # Collect ordered unique values and their leaf IDs
        value_order: List[str] = []
        value_to_leaves: Dict[str, List[str]] = {}
        for row in rows:
            val = row.get(col, '')
            if not val:
                continue
            if val not in value_to_leaves:
                value_order.append(val)
                value_to_leaves[val] = []
            value_to_leaves[val].append(row['id'])

        if not value_order:
            continue

        opt_objs = []
        for val in value_order:
            option_id = f"{col}|{val}"
            option_to_leaf_ids[option_id] = value_to_leaves[val]
            opt_objs.append({
                'optionId': option_id,
                'titleHtml': val,
                'contextHtml': '',
                'plainLabel': val,
                'imageSrc': '',
            })

        q_objs.append({
            'nodeId': col,
            'questionHtml': col,
            'questionText': col,
            'imageSrc': '',
            'options': opt_objs,
        })

    # Build leaf display objects
    leaf_objs = []
    for row in rows:
        arcs_parts = [
            row.get(level, '')
            for level in ('Class', 'Group', 'Type', 'Sub-type')
            if row.get(level)
        ]
        characteristics = [
            {'key': col, 'value': row.get(col, '')}
            for col in char_cols
            if row.get(col)
        ]
        leaf_objs.append({
            'leafId': row['id'],
            'leafText': row.get('Name', row['id']),
            'imageSrc': row.get('Image URL', ''),
            'description': row.get('Description', ''),
            'arcsParts': arcs_parts,
            'characteristics': characteristics,
            'depth': 0,
        })

    return {
        'questions': q_objs,
        'leaves': leaf_objs,
        'optionToLeafIds': option_to_leaf_ids,
        'initialCandidates': all_leaf_ids,
    }


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
        return candidates.map(id => leafById.get(id)).filter(Boolean)
          .sort((a, b) => (a.leafText || "").localeCompare(b.leafText || ""));
      }, [candidates, leafById]);

      const questionMeta = useMemo(() => {
        const meta = new Map();
        for (const q of MODEL.questions) {
          const optionCounts = q.options.map(opt =>
            intersect(candidates, MODEL.optionToLeafIds[opt.optionId] || []).length
          );
          const isRelevant = optionCounts.some(c => c > 0);
          const canNarrow = optionCounts.some(c => c > 0 && c < candidates.length);
          meta.set(q.nodeId, { canNarrow, isRelevant });
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
          setErrorMsg("That choice conflicts with earlier answers. Try a different option, or reset a previous answer.");
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
                    <button onClick={resetAll} className="text-sm text-slate-600 hover:text-slate-900">Reset All</button>
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
                                Reset
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
                              <div className="text-base font-semibold text-slate-900">
                                {opt.plainLabel}
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build faceted hypothesis-filtering HTML from classifications.csv characteristic columns."
    )
    parser.add_argument('--classifications', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--app-name', default="Classification Guide (Faceted Filtering)")
    args = parser.parse_args()

    path = Path(args.classifications)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    rows, char_cols = load_classifications(path)
    if not rows:
        print("error: no classification rows loaded", file=sys.stderr)
        sys.exit(1)
    if not char_cols:
        print("error: no characteristic columns found in classifications.csv", file=sys.stderr)
        sys.exit(1)

    model = build_model(rows, char_cols)
    print(f"Classifications: {len(rows)}, Questions: {len(model['questions'])}")

    html = make_html(model, args.app_name)
    Path(args.output).write_text(html, encoding='utf-8')
    print(f"Wrote: {args.output}")


if __name__ == '__main__':
    main()
