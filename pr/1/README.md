# [WIP] Weapons Classification Assistant

An interactive tool to assist in classifying Small Arms based on the **ARES Arms & Munitions Classification System (ARCS)** and the **SAS Weapons Identification Guide**.

This tool guides users through a step-by-step visual taxonomy to classify an item down to its **type** (ARCS Levels 1–3), then provides guidance on how to proceed toward **identification** (determining make, model, and variant) (this part is coming soon!).


## Project files

- `weapons-classification-flowchart.mmd`  
  Mermaid source for the decision flow.
- `src/mermaid_to_clickthrough.py`  
  Python script that converts Mermaid flowcharts into an interactive HTML click-through guide.
- `classification-guide.html`  
  Generated click-through guide (output).
- `mermaid.html`  
  Mermaid-rendered diagram page
---

## Edit the Mermaid flowchart

You can edit the `.mmd` file visually using Mermaid Live:

1. Go to: `https://mermaid.live/edit`
2. Open `weapons-classification-flowchart.mmd` in your local editor.
3. Copy the full file contents.
4. Paste into the Mermaid Live editor (left panel).
5. Edit and validate the flow/structure.
6. Copy the updated Mermaid text back into `weapons-classification-flowchart.mmd`.
7. Save and commit changes.

---

## Generate the interactive HTML

From the project root, run:

```bash
python3 src/mermaid_to_clickthrough.py \
  --input-mmd weapons-classification-flowchart.mmd \
  --output-html classification-guide.html \
  --app-name "[DEMO] Weapons Classification Guide"
```

## Preview output locally

Start a local web server from the repo root:

`python3 -m http.server 8000`

Then open in your browser:

http://localhost:8000/classification-guide.html

http://localhost:8000/mermaid.html

### Deploy / hosted site behavior

Committing to the main branch triggers the GitHub Action workflow, which updates the hosted GitHub Pages site.

#### Published URLs:

https://paigemoody.github.io/weapons_classification_resources.github.io/classification-guide.html

https://paigemoody.github.io/weapons_classification_resources.github.io/mermaid.html

## Suggested workflow

Edit weapons-classification-flowchart.mmd (optionally by copy pasting into [Mermaid Live editor](https://mermaid.live/)).

Regenerate classification-guide.html with the Python script.

Run a local server and verify both pages.

Commit to main to publish.

## Notes

The click-through experience is derived from Mermaid node/edge structure.

The generator auto-detects the starting node from the top of the chart (no manual root flag required).

If a chart has multiple top-level starting nodes, the generator creates a synthetic start question automatically.

The generator expects an acyclic decision flow; if a cycle is detected, generation stops with a warning.

Option labels come from edge labels when provided (for example: A --> |Option Text| B).

Option images are sourced from the destination node image (the node the edge points to).
