# Weapons Classification Assistant

An interactive tool for classifying small arms based on the **ARES Arms & Munitions Classification System (ARCS)** and the **SAS Weapons Identification Guide**.

Select observable physical characteristics of a weapon (how it's held, bore type, loading mechanism, action) and matching weapon classifications are filtered in real time.

**Live site**: https://paigemoody.github.io/weapons_classification_resources.github.io/

---

## Prerequisites

- Node.js v24+

---

## Local setup

```bash
npm install
npm run fetch-data      # pull latest CSVs from Google Sheets
npm run validate-data   # confirm the downloaded data is valid
npm run dev
```

Then open `http://localhost:5173`.

---

## Editing content

All data is managed in the public Google Sheet:

**[Weapons_Classifications__Small_Arms](https://docs.google.com/spreadsheets/d/1owsUDceWy-sG258SE8Z-gwTDLOQwIqAr6ADdfOln-2E/edit?gid=0#gid=0)**

| Sheet tab | Purpose |
|---|---|
| `classification_options` | Weapon records — ARCS taxonomy levels, characteristic values, descriptions, and source page refs |
| `characteristic_options` | Available options for each characteristic (e.g. `one_hand`, `rifled`) |
| `characteristic_definitions` | Guidance text for visually identifying each characteristic |
| `classification_definitions` | ARCS taxonomy level definitions (Class → Group → Type → Sub-type) |
| `sources` | Reference sources and their PDF page offsets |

### How changes get published

1. Edit the Google Sheet
2. Push any change to a branch — CI fetches the latest sheet data, validates it, then builds
3. A branch preview is automatically deployed to:
   ```
   https://paigemoody.github.io/weapons_classification_resources.github.io/branch-preview/<branch-name>/
   ```
4. Open a PR to `gh-pages` to publish to production

If the fetched data fails validation, the CI build is aborted — nothing broken can be deployed.

### Updating data during local development

After editing the Google Sheet, pull the latest data and verify it locally before pushing:

```bash
npm run fetch-data      # overwrites src/imports_new/ with latest sheet data
npm run validate-data   # exits with an error if anything looks wrong
```

The dev server hot-reloads automatically after the CSV files are updated.

---

## CI pipeline

Every push runs these steps in order — each must pass before the next runs:

1. **Fetch** — `npm run fetch-data` pulls all sheet tabs from Google Sheets
2. **Validate** — `npm run validate-data` checks structure and cross-references
3. **Build** — `vite build` bundles the app with the correct base path
4. **Deploy** — production (`gh-pages` branch) or branch preview (all other branches)

---

## Deployment

GitHub Pages is configured to use **GitHub Actions** as its source (repo Settings → Pages). The workflow builds the app and deploys it — files are never served directly from the branch.

### Production (`gh-pages` branch)
Pushing to `gh-pages` triggers the full pipeline and deploys to the live site.

### Branch previews (any other branch)
Pushing to a feature branch deploys the built app to a subfolder on the `gh-pages` branch. Only that subfolder is modified — the production root is never touched.

When a PR is closed or a branch is deleted, the preview folder is automatically removed via a cleanup workflow.

---

## File reference

| File/Directory | Purpose |
|---|---|
| `src/app/App.tsx` | Main app component and filtering logic |
| `src/app/data/weaponData.ts` | CSV parsing (PapaParse) and typed data layer |
| `src/app/components/` | UI components (CharacteristicCard, OptionPanel, ResultsPanel, etc.) |
| `src/imports_new/` | CSV data files (fetched from Google Sheets) |
| `src/styles/` | Tailwind / theme styles |
| `scripts/fetch-csvs.js` | Fetches sheet tabs from Google Sheets into `src/imports_new/` |
| `scripts/validate-csvs.js` | Validates CSV structure and cross-references |

---

### Attributions

Includes components from [shadcn/ui](https://ui.shadcn.com/) used under [MIT license](https://github.com/shadcn-ui/ui/blob/main/LICENSE.md).

Includes photos from [Unsplash](https://unsplash.com) used under [license](https://unsplash.com/license).
