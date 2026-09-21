/* HTML weaver client: theme, collapse, popovers, search, math, mermaid, scroll-spy. */
/* NOTE: Copied from `web/app.js` in XekriRedmane's `ultima1_reveng`; see `scripts/PROVENANCE.md`. */
(function () {
  "use strict";
  var root = document.documentElement;

  /* ---- theme (persisted) ---- */
  var saved = null;
  try { saved = localStorage.getItem("theme"); } catch (e) {}
  if (saved) root.setAttribute("data-theme", saved);
  var themeBtn = document.getElementById("theme-toggle");
  if (themeBtn) themeBtn.addEventListener("click", function () {
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (e) {}
  });

  /* ---- mobile menu ---- */
  var menuBtn = document.getElementById("menu-toggle");
  var left = document.getElementById("left");
  if (menuBtn && left) menuBtn.addEventListener("click", function () {
    left.classList.toggle("open");
  });

  /* ---- keep the left sidebar's scroll position across page loads ---- */
  if (left) {
    try {
      var saved = sessionStorage.getItem("nwLeftScroll");
      if (saved !== null) left.scrollTop = +saved;
    } catch (e) {}
    left.addEventListener("scroll", function () {
      try { sessionStorage.setItem("nwLeftScroll", left.scrollTop); } catch (e) {}
    });
    // Mark the current page's TOC entry.
    var here = location.pathname.split("/").pop() || "index.html";
    left.querySelectorAll("a").forEach(function (a) {
      if ((a.getAttribute("href") || "") === here) a.classList.add("current");
    });
  }

  /* ---- collapsible chunks ---- */
  document.querySelectorAll(".chunk .collapse").forEach(function (btn) {
    btn.addEventListener("click", function () {
      btn.closest(".chunk").classList.toggle("collapsed");
    });
  });

  /* ---- KaTeX (auto-render \( \) and \[ \]) ---- */
  function renderMath() {
    if (typeof renderMathInElement !== "function") return;
    renderMathInElement(document.getElementById("main"), {
      delimiters: [
        { left: "\\(", right: "\\)", display: false },
        { left: "\\[", right: "\\]", display: true },
      ],
      throwOnError: false,
    });
  }

  /* ---- Mermaid (theme-aware) ---- */
  function renderMermaid() {
    if (typeof mermaid === "undefined") return;
    var dark = root.getAttribute("data-theme") === "dark";
    try {
      mermaid.initialize({ startOnLoad: false, theme: dark ? "dark" : "neutral" });
      mermaid.run({ querySelector: ".mermaid" });
    } catch (e) {}
  }

  /* ---- popovers (chunk/identifier previews, cross-page via CHUNK_META) ---- */
  var pop = document.getElementById("popover");
  var meta = window.CHUNK_META || {};
  function showPop(el) {
    var key = el.getAttribute("data-pop");
    var m = meta[key];
    if (!m || !pop) return;
    pop.innerHTML =
      '<div><span class="pop-name">&#x27E8;' + escapeHtml(m.n) + "&#x27E9;</span> " +
      '<span class="pop-page">&middot; ' + escapeHtml(m.p) + "</span></div>" +
      (m.s ? "<pre>" + escapeHtml(m.s) + "</pre>" : "");
    pop.hidden = false;
    var r = el.getBoundingClientRect();
    var top = window.scrollY + r.bottom + 6;
    var leftPx = Math.min(window.scrollX + r.left, window.scrollX + window.innerWidth - pop.offsetWidth - 12);
    pop.style.top = top + "px";
    pop.style.left = Math.max(8, leftPx) + "px";
  }
  function hidePop() { if (pop) pop.hidden = true; }
  document.querySelectorAll("[data-pop]").forEach(function (el) {
    el.addEventListener("mouseenter", function () { showPop(el); });
    el.addEventListener("mouseleave", hidePop);
  });

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  /* ---- full-site search (single inlined index, built once) ---- */
  var q = document.getElementById("q");
  var results = document.getElementById("results");
  var mini = null;
  function ensureIndex() {
    if (mini || typeof MiniSearch === "undefined") return mini;
    mini = new MiniSearch({
      fields: ["t", "b"], storeFields: ["t", "u", "k"],
      searchOptions: { boost: { t: 3 }, prefix: true, fuzzy: 0.2 },
    });
    mini.addAll((window.SEARCH_INDEX || []).map(function (d, i) {
      return { id: i, t: d.t, b: d.b, u: d.u, k: d.k };
    }));
    return mini;
  }
  function runSearch() {
    if (!results) return;
    var idx = ensureIndex();
    var term = q.value.trim();
    if (!idx || term.length < 2) { results.classList.remove("show"); return; }
    var hits = idx.search(term).slice(0, 25);
    results.innerHTML = hits.map(function (h) {
      return '<a href="' + escapeHtml(h.u) + '"><span class="k">' + escapeHtml(h.k) +
        "</span><br>" + escapeHtml(h.t) + "</a>";
    }).join("") || '<a class="noresult">No matches</a>';
    results.classList.add("show");
  }
  if (q) {
    q.addEventListener("input", runSearch);
    q.addEventListener("focus", runSearch);
    document.addEventListener("click", function (e) {
      if (!e.target.closest(".search")) results.classList.remove("show");
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "/" && document.activeElement !== q) { e.preventDefault(); q.focus(); }
      if (e.key === "Escape") { results.classList.remove("show"); q.blur(); }
    });
  }

  /* ---- scroll-spy for the on-this-page outline ---- */
  var links = {};
  document.querySelectorAll(".outline a").forEach(function (a) {
    links[a.getAttribute("href").slice(1)] = a;
  });
  var targets = Object.keys(links).map(function (id) { return document.getElementById(id); }).filter(Boolean);
  if (targets.length && "IntersectionObserver" in window) {
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var a = links[en.target.id];
        if (!a) return;
        if (en.isIntersecting) {
          Object.values(links).forEach(function (x) { x.classList.remove("active"); });
          a.classList.add("active");
        }
      });
    }, { rootMargin: "0px 0px -75% 0px" });
    targets.forEach(function (t) { obs.observe(t); });
  }

  renderMath();
  renderMermaid();
})();
