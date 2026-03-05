# Weapons Classification Assistant

An interactive tool for classifying small arms based on the **ARES Arms & Munitions Classification System (ARCS)** and the **SAS Weapons Identification Guide**.

Two guides are generated from the same source data:

- **`classification-guide.html`** — click-through guide: start at the top and answer questions in sequence
- **`classification-guide-hypothesis-filtering.html`** — hypothesis-filtering guide: see all possible classifications and filter by observable characteristics

---

## How it works

The tool has two kinds of source files:

| What | File(s) | Who edits it |
|---|---|---|
| Taxonomy structure (which nodes exist and how they connect) | `taxonomy-structure.mmd` | Developer |
| Content (question prompts, option names/descriptions, classification names/descriptions, images) | `content/questions.csv`, `content/options.csv`, `content/classifications.csv` | Content editor |

The HTML guides are generated from these sources. They are **not edited directly**.

---

## For content editors

All content lives in three CSV files under `content/`. You can edit them in Excel, Google Sheets, or any spreadsheet tool.

See **[docs/CONTENT_EDITING_GUIDE.md](docs/CONTENT_EDITING_GUIDE.md)** for a step-by-step guide to editing content and previewing changes.

---

## For developers

### Local setup

The project runs in a dev container with Python 3 pre-installed. No additional dependencies are required.

### Generate the HTML files locally

```bash
make
```

This runs the full pipeline:
1. `src/build_content_mmd.py` — merges `taxonomy-structure.mmd` + content CSVs → `weapons-classification-flowchart.mmd`
2. `src/mermaid_to_clickthrough.py` — generates `classification-guide.html`
3. `src/csv_to_hypothesis_filtering.py` — generates `classification-guide-hypothesis-filtering.html`

`make` only rebuilds what is out of date. Run `make clean` to remove all generated files.

### Preview locally

```bash
python3 -m http.server 8000
```

Then open:
- `http://localhost:8000/classification-guide.html`
- `http://localhost:8000/classification-guide-hypothesis-filtering.html`

### Pipeline overview

```
taxonomy-structure.mmd  ─┐
content/questions.csv    ├─→ build_content_mmd.py → weapons-classification-flowchart.mmd → mermaid_to_clickthrough.py → classification-guide.html
content/options.csv      │
content/classifications.csv ─→ csv_to_hypothesis_filtering.py → classification-guide-hypothesis-filtering.html
```

The hypothesis-filtering guide reads structure directly from `questions.csv` (the Option columns encode parent-child relationships) and does not need the intermediate Mermaid file.

### Taxonomy structure

The taxonomy mirrors the ARCS classification levels 1–4 (Class → Group → Type → Sub-type). `taxonomy-structure.mmd` is the authoritative source for which nodes exist and how they connect. Content editors do not need to touch it.

See **[docs/NOTES.md](docs/NOTES.md)** for the reasoning behind structural and content decisions.

### CI/CD

GitHub Actions (`.github/workflows/pr-preview.yml`) automatically regenerates the HTML files and commits them back to the branch whenever source files change. For non-`gh-pages` branches it also publishes a preview at:

```
https://paigemoody.github.io/weapons_classification_resources.github.io/branch-preview/<branch-name>/classification-guide.html
https://paigemoody.github.io/weapons_classification_resources.github.io/branch-preview/<branch-name>/classification-guide-hypothesis-filtering.html
```

---

## File reference

| File | Purpose |
|---|---|
| `taxonomy-structure.mmd` | Taxonomy structure — developer maintained |
| `content/questions.csv` | Decision node prompts and options |
| `content/options.csv` | Option names, descriptions, images, characteristics |
| `content/classifications.csv` | Leaf node names, ARCS levels, descriptions, images |
| `src/build_content_mmd.py` | Merges structure + CSVs → enriched Mermaid |
| `src/mermaid_to_clickthrough.py` | Enriched Mermaid → click-through HTML |
| `src/csv_to_hypothesis_filtering.py` | CSVs → hypothesis-filtering HTML |
| `weapons-classification-flowchart.mmd` | Generated — do not edit directly |
| `classification-guide.html` | Generated — do not edit directly |
| `classification-guide-hypothesis-filtering.html` | Generated — do not edit directly |
| `docs/NOTES.md` | Architecture decisions and rationale |
| `docs/CONTENT_EDITING_GUIDE.md` | Guide for content editors |
