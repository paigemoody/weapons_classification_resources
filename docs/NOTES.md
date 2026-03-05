# Project Notes

Design decisions and context for the weapons classification tool.

---

## Sources

- **ARES (Arms & Munitions Classification System)** is the authoritative source for taxonomy *structure*
- **SAS (Small Arms Survey Weapons Identification Guide)** is used for content — definitions, descriptions, images

The two sources have structural differences (e.g. where Sub-machine Guns sit in the hierarchy). ARES takes precedence for structure.

**Why split sources this way?** ARES provides a rigorous, stable classification framework designed specifically for this purpose. SAS provides accessible descriptions and imagery suited to non-specialist users. Using ARES for structure means the hierarchy reflects a defensible authoritative standard; using SAS for content means the descriptions are practical and user-facing.

---

## Architecture

### Core principle: separate structure from content

The taxonomy hierarchy changes rarely (it reflects an authoritative published standard). Content — prompts, descriptions, and images — changes frequently as the tool is refined. These two concerns are kept in separate files so that content editors never need to touch structural files, and structural changes never require content re-entry.

### Two audiences, two workflows

**Developers** maintain the taxonomy structure in `taxonomy-structure.mmd`. Mermaid is machine-readable, version-controllable, and easy to diff — appropriate for a developer workflow.

**Content editors** work only with CSV files in `content/`. CSVs are familiar to non-technical users (open in Excel or Google Sheets), require no knowledge of Mermaid syntax, and have a clear row-per-item structure.

### Pipeline

**Click-through guide:**
```
taxonomy-structure.mmd + content CSVs
  → src/build_content_mmd.py
  → weapons-classification-flowchart.mmd
  → src/mermaid_to_clickthrough.py
  → classification-guide.html
```

**Hypothesis-filtering guide:**
```
content CSVs only
  → src/csv_to_hypothesis_filtering.py
  → classification-guide-hypothesis-filtering.html
```

The click-through guide uses an intermediate enriched Mermaid file because `mermaid_to_clickthrough.py` already existed and expected that format. The hypothesis-filtering guide derives tree structure entirely from `questions.csv` (Option 1–5 columns), so it does not need the Mermaid file at all — the parent-child relationships are fully encoded in the CSV.

**Why two separate HTML outputs?** The two guides serve different use cases. The click-through guide walks users through one decision at a time. The hypothesis-filtering guide shows all possible end classifications and lets users filter them down by observable characteristics. They share the same source data but have different rendering logic, so they are separate generators.

### Files

| File | Purpose | Edited by |
|---|---|---|
| `taxonomy-structure.mmd` | Authoritative taxonomy structure — node IDs and edges only, no content | Developer |
| `content/questions.csv` | Decision node prompts and images | Content editor |
| `content/options.csv` | Option names, descriptions, images, and characteristics | Content editor |
| `content/classifications.csv` | Leaf node names, ARCS levels, descriptions, images | Content editor |
| `weapons-classification-flowchart.mmd` | Generated — do not edit directly | Build artifact |
| `archive/weapons-classification-flowchart_old.mmd` | Original hand-authored Mermaid — historical reference only | (archived) |

---

## Taxonomy structure

The tool covers ARCS classification levels 1–4 (Class → Group → Type → Sub-type) plus Method of Operation for rifles and shotguns. This corresponds to the "Classifying" portion of Figure 1.1 in the ARES guide.

Sub-machine Guns and Man-portable Machine Guns sit under Long Guns (Type level), consistent with both the SAS table and the visual position in ARES Figure 2.3. An earlier version of the Mermaid diagram placed them elsewhere; ARES is the tiebreaker.

The old `archive/weapons-classification-flowchart_old.mmd` added barrel type (Rifled / Smooth bore) as intermediate navigation nodes. These do not exist in the ARCS taxonomy and are not in `taxonomy-structure.mmd`. The barrel type question prompt ("Which barrel type best fits what you see?") is preserved on the `Handguns` decision node in `questions.csv` as it remains a useful observational prompt — it is just not a structural branch in the taxonomy.

### Why `taxonomy-structure.mmd` contains no content

The structure file uses bare node IDs and edges only (no HTML labels). This keeps it readable as a pure structural artefact, easy to diff, and free of content that belongs in the CSVs. It is the source of truth for which nodes exist and how they connect — nothing more.

---

## Content CSV design

### questions.csv — decision nodes

Each row is a decision point in the tree. The `Option 1` through `Option 5` columns list the IDs of the child nodes that can be reached from that question. This makes the parent-child relationships explicit and human-readable without requiring editors to understand graph notation.

**Why list options as columns rather than separate rows?** A single row per question makes it immediately clear which options belong together and preserves the order in which they appear to the user. A separate join table would require editors to maintain a foreign key relationship, which is error-prone without tooling.

**Why up to 5 options?** The widest node in the current taxonomy has 5 children (Long Guns). The fixed-column approach works for the current taxonomy; if the taxonomy ever grows beyond 5 options at a node, the column range would need expanding.

### options.csv — choices presented to the user

Each row is a selectable option (an edge in the tree, from parent question to child node). The `id` matches a child node ID used in `questions.csv`. Options carry their own display name, description, and image separate from the question that presents them.

**Why options are separate from questions:** The same child node could in principle be reachable from multiple parents. Keeping option content on the option row means it is defined once and referenced by ID.

### classifications.csv — leaf nodes

Each row is a final classification (a leaf in the tree). The ARCS level columns (Class, Group, Type, Sub-type) record where the classification sits in the formal taxonomy. Levels that do not apply to a given classification are left blank.

---

## Characteristic annotations (options.csv)

Characteristics are annotated on **options** (edges), not on leaf classifications. Each classification's full set of observable characteristics is derived by walking its path from the root through the tree, collecting the `Defining Characteristic` and `Characteristic Value` from each option along the way.

**Why on options rather than on classifications?** It avoids redundant data entry. For example, "Loading: Manual" applies to every manually operated rifle and shotgun sub-type. Annotating it once on the `ManuallyOperatedRifles` option means it is automatically inherited by all six sub-types beneath it. If the wording ever changes, there is one place to update.

### Annotation choices

- **`Handguns`** — How held: "One hand (no shoulder stock)". This is the primary observable distinction from long guns.
- **`LongGuns`** — How held: "Two hands with shoulder stock". Symmetric counterpart to Handguns.
- **`Revolvers`** — Action type: "Rotating cylinder". The most visually distinctive feature.
- **`SubMachineGuns`** — Loading: "Self-loading". Distinguishes from other long gun types at this branch.
- **`Shotguns`** — Bore type: "Smooth bore". The defining structural distinction from rifles.
- **`SelfLoadingRifles` / `SelfLoadingShotguns`** — Loading: "Self-loading (cycles automatically after each shot)".
- **`ManuallyOperatedRifles` / `ManuallyOperatedShotguns`** — Loading: "Manual (must be cycled by hand between shots)".
- **`AutomaticRifles` / `AutomaticShotguns`** — Fires per trigger pull: "Multiple rounds (fully automatic)".
- **`SemiAutomaticRifles` / `SemiAutomaticShotguns`** — Fires per trigger pull: "One round (semi-automatic)".
- **Break / Bolt / Lever / Pump action options** — Action type: named accordingly with a brief description of the observable feature.

### Options with no characteristic

- **`Rifles`** — No characteristic. At that branch point, rifled barrel is already implied by the long gun path; it is not the distinguishing observation between rifles and other long gun types at that step.
- **`SelfLoadingPistols`** — No characteristic. "Self-loading" is the default for non-revolver handguns and adds no additional discriminating information at that branch.
- **`ManPortableMachineGuns`** — No characteristic. No single observable feature cleanly distinguishes these from other long guns without prior knowledge of the weapon type.
- **`OtherHandguns`**, **`OtherLongGuns`**, **`OtherManuallyOperatedRifles`**, **`OtherManuallyOperatedShotguns`** — No characteristic. These are catch-all categories with no single defining observable trait.

---

## CI/CD

The GitHub Actions workflow (`pr-preview.yml`) runs whenever source files change on any branch. It regenerates the two HTML outputs and commits them back to the same branch. For non-`gh-pages` branches it also publishes a preview under `branch-preview/<branch-name>/` on the `gh-pages` branch.

A loop guard (`if: github.actor != 'github-actions[bot]'`) prevents the bot's own commits from re-triggering the workflow.
