// mermaid-page.js
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";

mermaid.initialize({
  startOnLoad: false,
  securityLevel: "loose", // needed for HTML labels / <img> in nodes
  flowchart: { htmlLabels: true, useMaxWidth: true },
});

async function loadDiagram() {
  const container = document.getElementById("diagram");
  if (!container) return;

  try {
    const res = await fetch("./weapons-classification-flowchart.mmd", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status} loading .mmd file`);
    const mmd = await res.text();

    const id = "weaponsFlowSvg";
    const { svg } = await mermaid.render(id, mmd);
    container.innerHTML = svg;
  } catch (err) {
    container.innerHTML = `
      <div style="color:#991b1b;background:#fef2f2;border:1px solid #fecaca;border-radius:6px;padding:12px;font-size:14px;">
        Could not load Mermaid file: <code>weapons-classification-flowchart.mmd</code><br>
        <span style="opacity:.8">${String(err.message || err)}</span>
      </div>
    `;
    console.error(err);
  }
}

window.addEventListener("DOMContentLoaded", loadDiagram);
