# [WIP] Weapons Classification Assistant

An interactive tool to assist in classifying Small Arms based on the **ARES Arms & Munitions Classification System (ARCS)** and the **SAS Weapons Identification Guide**.

This tool guides users through a step-by-step visual taxonomy to classify an item down to its **type** (ARCS Levels 1–3), then provides guidance on how to proceed toward **identification** (determining make, model, and variant) (this part is coming soon!).

---

## Project files

- `weapons-classification-flowchart.mmd`  
  Mermaid source for the decision flow (this is the file you edit).
- `classification-guide.html`  
  Generated interactive click-through guide (this is the main output).
- `src/mermaid_to_clickthrough.py`  
  Generator script that converts the Mermaid flowchart into the interactive HTML.
- `mermaid.html`  
  A page for viewing the Mermaid diagram (if you use this in the repo).

---

## GitHub-first editing and previews (no local setup required)

This project is set up so you can make changes **directly on GitHub**, preview them on the web, and only then publish them to the main site.

### What is a “branch” and why do we use it?

A **branch** is basically a “safe workspace” for changes.

- When you create a branch, you get a copy of the project where you can experiment.
- Changes you make on your branch **do not affect the main site**.
- You’ll get a **preview link** for your branch so you can see exactly what changed.
- When everything looks good, you merge your branch into `gh-pages` to publish to the main site.

Think of it like: “draft mode” → “preview” → “publish”.

---

## Step-by-step: edit the Mermaid file in GitHub and preview it

### 1) Create your branch (your safe workspace)

1. Open this repo on GitHub.
2. Near the top-left of the file list, find the **branch dropdown** (it often shows the current branch name, like `gh-pages`).
3. Click the dropdown.
4. Type a new branch name (example: `diagram-fixes`).
5. Click the option that says **Create branch: `diagram-fixes`**.

You are now “on your branch.” Anything you do next will only affect your branch.

---

### 2) Open the Mermaid file and start editing

1. In the file list, click **`weapons-classification-flowchart.mmd`**.
2. Click the **pencil icon** (Edit) near the top-right of the file view.
3. Make your edits in the editor.

Optional (nicer editing experience): Mermaid Live
1. Go to `https://mermaid.live/edit`
2. Copy/paste the contents of `weapons-classification-flowchart.mmd` into Mermaid Live.
3. Edit and validate the diagram.
4. Copy the updated Mermaid text back into GitHub.

---

### 3) Click “Commit changes” (this saves your edits)

When you’re done editing:

1. Scroll down to the **Commit changes** section.
2. You can leave the default message, or write something like: `Update decision flow`.
3. Make sure it is committing to **your branch** (it should be, unless you changed it).
4. Click the **Commit changes** button.

✅ This is the moment your changes are saved to your branch.

---

### 4) GitHub Actions regenerates the HTML automatically

After you commit, GitHub Actions will automatically:

- regenerate `classification-guide.html` (at the repo root, next to the `.mmd`)
- commit the updated HTML back to your branch
- publish a web preview for your branch

You don’t have to run anything locally for this flow.

Tip: If you click the **Actions** tab on GitHub, you can watch this run and see whether it succeeded.

---

### 5) Open your preview link (see your changes on the web)

Your branch preview will be available at:

`https://paigemoody.github.io/weapons_classification_resources.github.io/branch-preview/<your-branch-name>/classification-guide.html`

Example:

`https://paigemoody.github.io/weapons_classification_resources.github.io/branch-preview/diagram-fixes/classification-guide.html`

If your change was just committed, it may take a minute for GitHub Pages to show the update.

---

## Publishing your changes to the main site (merge into `gh-pages`)

When your preview looks good, you can publish it so everyone sees it on the main site.

### 6) Create a Pull Request (PR)

A Pull Request is a way to say: “I’m ready to move the changes from my branch into the main branch.”

1. On GitHub, go to the **Pull requests** tab.
2. Click **New pull request**.
3. For “base”, choose `gh-pages`.
4. For “compare”, choose your branch (example: `diagram-fixes`).
5. Click **Create pull request**.

### 7) Merge the Pull Request

When you’re ready:

1. Click **Merge pull request**
2. Confirm the merge

That publishes the changes to the main site.

Main site URL:

- `https://paigemoody.github.io/weapons_classification_resources.github.io/classification-guide.html`

Note: because `gh-pages` is deployed from the branch, GitHub Pages may deploy twice:
- once for the merge commit
- once for the follow-up commit that updates `classification-guide.html`

That’s expected with the current setup.

---

## Local development (optional)

If you want to iterate locally (faster feedback, easier editing), you can.

### Generate the interactive HTML

From the repo root:

```bash
python3 src/mermaid_to_clickthrough.py \
  --input-mmd weapons-classification-flowchart.mmd \
  --output-html classification-guide.html \
  --app-name "[DEMO] Weapons Classification Guide"
