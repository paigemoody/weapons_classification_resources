# [WIP] Weapons Classification Assistant

A simple, interactive tool for classifying Small Arms based on the **ARES Arms & Munitions Classification System (ARCS)** and the **SAS Weapons Identification Guide**.

This tool guides users through a step-by-step visual taxonomy to classify an item down to its **type** (ARCS Levels 1–3), then provides guidance on how to proceed toward **identification** (determining make, model, and variant).


## How to Update the Classification Tree

The entire classification tree is defined in **`config.json`**. Non-technical editors can update this file directly on GitHub using the web editor.

### Structure

The config file has a `nodes` object. Each node is either a **question** or a **result**.

#### Question nodes

```json
"my_node_id": {
  "question": "What does the item look like?",
  "help": "Optional guidance text (shown when user clicks 'Guidance')",
  "options": [
    {
      "label": "Option A",
      "description": "Brief description of this option",
      "image": "images/my-image.svg",
      "next": "next_node_id"
    },
    {
      "label": "Option B",
      "description": "Brief description of this option",
      "image": "images/other-image.svg",
      "next": "another_node_id"
    }
  ]
}
```

#### Result nodes (terminal / classification complete)

```json
"result_my_thing": {
  "result": true,
  "classification": {
    "class": "Small Arm",
    "group": "Long Gun",
    "subgroup": "Rifled Long Gun",
    "type": "Self-loading Rifle"
  },
  "summary": "You have classified this item as a **self-loading rifle**...",
  "next_steps": "To move towards **identification**:\n\n1. Look at markings...\n2. Note physical features...",
  "references": [
    {
      "name": "SAS Weapons ID Guide",
      "url": "https://www.smallarmssurvey.org/sites/default/files/SAS-HB-06-Weapons-ID-Guide-Full.pdf"
    }
  ]
}
```

### Key rules

- Every `"next"` value in an option must match an existing node ID
- The tree must start with a node called `"start"`
- Result nodes have `"result": true` — they are terminal (no further options)
- You can have 2, 3, 4, or more options per question
- Text supports `**bold**` formatting and numbered lists (`1. First\n2. Second`)
- Node IDs should use lowercase with underscores (e.g. `sa_longgun_bore`)

### Adding a new branch

1. Add a new question node with a unique ID
2. Point an existing option's `"next"` to your new node ID
3. Add options in the new node, each pointing to further nodes or results
4. Test by reloading the page

### Adding images

1. Add image files to the `images/` folder (SVG, PNG, or JPG)
2. Reference them in the config as `"image": "images/your-file.png"`
3. Recommended: use clear, well-lit reference photos or simple diagrams
4. Images should be roughly 4:3 aspect ratio for best display

## Replacing Placeholder Images

The included SVG images are simple silhouette placeholders. For a production deployment, replace them with real images

Replace the SVG files in `images/` or change the file references in `config.json`.

## Sources

- [ARES Arms & Munitions Classification System (ARCS) v1.3](https://armamentresearch.com/wp-content/uploads/2022/08/The-ARES-Arms-Munitions-Classification-System-ARCS-ver1.3-public-release.pdf)
- [SAS Introductory Guide to the Identification of Small Arms, Light Weapons, and Associated Ammunition](https://www.smallarmssurvey.org/sites/default/files/SAS-HB-06-Weapons-ID-Guide-Full.pdf)

## Technical Details

- **Zero dependencies** — single HTML file with inline CSS and JS
- **No build step** — works as static files on any web server
- **Offline capable** — once loaded, no network requests needed
- **Responsive** — works on desktop, tablet, and mobile
- **Accessible** — keyboard navigable, semantic HTML
- **Print friendly** — navigation hidden when printing results
