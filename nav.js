(async function () {
  const slot = document.getElementById("nav-slot");
  if (!slot) return;

  const navPath = slot.dataset.navPath || "nav.html";
  const title = slot.dataset.title || "";
  const subtitle = slot.dataset.subtitle || "";
  const linkHref = slot.dataset.linkHref || "";
  const linkText = slot.dataset.linkText || "";

  try {
    const res = await fetch(navPath, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    slot.innerHTML = await res.text();

    if (title) document.getElementById("nav-title").textContent = title;
    if (subtitle) document.getElementById("nav-subtitle").textContent = subtitle;
    if (linkHref) document.getElementById("nav-link").setAttribute("href", linkHref);
    if (linkText) document.getElementById("nav-link").textContent = linkText;
  } catch (err) {
    slot.innerHTML = "<nav><strong>Navigation failed to load.</strong><hr /></nav>";
  }
})();
