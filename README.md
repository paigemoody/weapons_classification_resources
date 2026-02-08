# [WIP] Weapons Classification Assistant

A simple, interactive tool for classifying Small Arms based on the **ARES Arms & Munitions Classification System (ARCS)** and the **SAS Weapons Identification Guide**.

This tool guides users through a step-by-step visual taxonomy to classify an item down to its **type** (ARCS Levels 1–3), then provides guidance on how to proceed toward **identification** (determining make, model, and variant).

---

## Project files

- `weapons-classification-flowchart.mmd`  
  Mermaid source for the decision flow.
- `src/mermaid_to_clickthrough.py`  
  Python script that converts the Mermaid flow into an interactive HTML classifier.
- `classification-guide.html`  
  Generated click-through guide (output).
- `mermaid.html`  
  Mermaid-rendered diagram page (if present in repo).

---

## Edit the Mermaid flowchart

You can edit the `.mmd` file visually using Mermaid Live:

1. Go to: `https://mermaid.live/edit`
2. Open `weapons-classification-flowchart.mmd` file
3. Copy the full file contents
4. Paste into [Mermaid Live editor](https://mermaid.live/edit) (left panel)
5. Edit and validate the flow/structure.
6. Copy the updated Mermaid text back into `weapons-classification-flowchart.mmd`
7. Save the file and push to github repo

## Generate the interactive HTML

From the project root, run:

```bash
python3 src/mermaid_to_clickthrough.py \
  --input weapons-classification-flowchart.mmd \
  --output classification-guide.html \
  --root SmallArms \
  --title "[DEMO] Weapons Classification Guide"
```

## Preview output locally

Start a local web server from the repo root:

```
python3 -m http.server 8000
```

Then open in any browser you can open:

http://localhost:8000/classification-guide.html

http://localhost:8000/mermaid.html

## Deploy / hosted site behavior

Committing to the main branch triggers the GitHub Action workflow, which updates the hosted GitHub Pages site.

#### Published URLs:

https://paigemoody.github.io/weapons_classification_resources.github.io/classification-guide.html

https://paigemoody.github.io/weapons_classification_resources.github.io/mermaid.html

## Suggested workflow

Edit weapons-classification-flowchart.mmd (optionally via [Mermaid Live editor](https://mermaid.live/edit)).

Regenerate classification-guide.html with the Python script.

Run local server and check both pages.

Commit changes to main to publish.

## Notes

The click-through experience is derived from Mermaid node/edge structure.

Keep key node IDs stable (for example: SmallArms, Handguns, LongGuns) unless you also update generator args.

If you rename the root node, update --root accordingly.