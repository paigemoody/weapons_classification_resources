# Content Editing Guide

This guide is for content editors. You do not need to understand code or diagram syntax to edit the tool's content.

All content lives in three CSV files under `content/`. Edit them in Excel, Google Sheets, or any spreadsheet application.

---

## The three files

### `content/questions.csv` — decision prompts

Each row is a question shown to the user at a decision point in the tree.

| Column | What it is |
|---|---|
| `id` | Internal identifier — do not change |
| `Prompt` | The question text shown to the user |
| `Image URL` | Optional image shown with the question |
| `Image Caption` | Caption for the image |
| `Option 1` – `Option 5` | The IDs of the choices available at this step |

The Option columns reference rows in `options.csv`. You will rarely need to change these — they define the structure of the tree, which only changes if the taxonomy changes.

**What to edit here:** Question prompts and images.

---

### `content/options.csv` — choices presented to users

Each row is a selectable option (a branch the user can take). When a user picks an option, they either reach another question or a final classification.

| Column | What it is |
|---|---|
| `id` | Internal identifier — do not change |
| `Option Name` | The label shown on the button/choice |
| `Description` | A longer description shown with the option |
| `Image URL` | Optional image shown with the option |
| `Image Caption` | Caption for the image |
| `Defining Characteristic` | The observable feature that distinguishes this option (e.g. "Action type") |
| `Characteristic Value` | The value of that feature (e.g. "Bolt-action (handle on side of receiver)") |

Characteristics are used by the hypothesis-filtering guide to help users narrow down classifications by what they can observe. Leave both columns blank if no single observable feature cleanly applies.

**What to edit here:** Option names, descriptions, images, and characteristic labels.

---

### `content/classifications.csv` — final classifications

Each row is a final classification — a leaf node at the end of the decision tree.

| Column | What it is |
|---|---|
| `id` | Internal identifier — do not change |
| `Name` | The human-readable classification name |
| `Class` | ARCS level 1 |
| `Group` | ARCS level 2 |
| `Type` | ARCS level 3 |
| `Sub-type` | ARCS level 4 (leave blank if not applicable) |
| `Description` | A description of this weapon type |
| `Image URL` | Optional image |
| `Image Caption` | Caption for the image |

**What to edit here:** Classification names, descriptions, ARCS levels, and images.

---

## How the files relate

```
questions.csv                   options.csv              classifications.csv
─────────────                   ───────────              ──────────────────
Question: "Which long gun?"     Option: "Rifles"
  Option 1 = Rifles  ───────→    id = Rifles
  Option 2 = Shotguns            Description = ...
  ...                            Characteristic = ...
                                   ↓
                                 leads to another question,
                                 or to a classification row
                                                          Classification: "Bolt-action Rifles"
                                                            id = BoltActionRifles
                                                            Name = Bolt-action Rifles
                                                            ...
```

The `id` columns are the join keys. The Option columns in `questions.csv` reference `id` values from `options.csv`. Options ultimately lead to either another question `id` or a classification `id`.

You do not need to change any `id` values. Changing an `id` would break the links between files.

---

## How to add an image

Images are hosted directly from the GitHub repository. To add an image:

1. Upload the image file to `sources/` under the appropriate subfolder:
   - `sources/ARES_arms_munitions_classification_system/visuals/` for ARES figures
   - `sources/small_arms_survey/visuals/` for SAS figures

2. Construct the URL:
   ```
   https://github.com/paigemoody/weapons_classification_resources.github.io/blob/gh-pages/sources/<subfolder>/<filename>?raw=true
   ```

3. Paste that URL into the `Image URL` column of the relevant CSV row.

---

## Editing workflow

### Option A: Edit on GitHub (no local setup needed)

1. On GitHub, create a new branch from `gh-pages`
2. Navigate to the CSV file you want to edit
3. Click the pencil icon to edit
4. Make your changes and commit to your branch
5. GitHub Actions will automatically regenerate the HTML and publish a preview

**Preview links** (replace `<your-branch>` with your branch name):
```
https://paigemoody.github.io/weapons_classification_resources.github.io/branch-preview/<your-branch>/classification-guide.html
https://paigemoody.github.io/weapons_classification_resources.github.io/branch-preview/<your-branch>/classification-guide-hypothesis-filtering.html
```

6. When the preview looks right, open a Pull Request and merge to `gh-pages` to publish

### Option B: Edit locally (faster iteration)

1. Open the CSV in Excel or Google Sheets
2. Edit and save
3. Run `make` from the repo root to regenerate the HTML files
4. Open `classification-guide.html` or `classification-guide-hypothesis-filtering.html` in your browser to preview
5. Commit your CSV changes and push to your branch

---

## What you should and should not change

| You can freely change | Do not change |
|---|---|
| Any `Prompt`, `Option Name`, `Description`, `Image URL`, `Image Caption` | Any `id` column value |
| `Defining Characteristic` and `Characteristic Value` | The `Option 1`–`Option 5` columns in `questions.csv` (these define the tree structure) |
| `Name`, `Class`, `Group`, `Type`, `Sub-type` in `classifications.csv` | The set of rows (adding or removing rows changes the taxonomy structure — coordinate with a developer) |

---

## Questions?

See [NOTES.md](NOTES.md) for the reasoning behind content decisions already made (e.g. why certain options have no characteristic annotation).
