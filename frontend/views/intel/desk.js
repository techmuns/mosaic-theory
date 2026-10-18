// ============================================================================
// THEME INTELLIGENCE — the research desk inside the app (PR #703, option C).
//
// ONE RENDERER. The desk's screens are rendered by the Python package
// (vinci/theme_intelligence/desk.py) and published as static pages with
// `python -m vinci.theme_intelligence publish` into frontend/theme-intelligence/.
// This view shows a published page inside the app's frame: it fetches the page,
// keeps its content, maps its links onto the app's routes, styles it with the
// app's own tokens (intel.css, generated beside it) and wires its controls with
// the desk's own script (desk.js). Nothing here re-implements a screen, so the
// app and the standalone desk can never disagree.
//
// Routes:  #/intel                       This week
//          #/intel/themes                Themes (…/area/<area> · …/sort/<key>)
//          #/intel/themes/TH-…           a thesis's reading page (under Themes)
//          #/intel/articles[/<week>]     Articles
//          #/intel/review · /uploads · /sources
// The Full record (the nine-section card) and the weekly report open as the
// published standalone pages, in a new tab.
// ============================================================================
import { escapeHtml } from "../../lib/format.js";

const BASE = "theme-intelligence/";
const SCREENS = {
  "": "index.html", themes: "themes.html", articles: "articles.html",
  review: "review.html", uploads: "uploads.html", sources: "sources.html",
};

// the published page a route shows, and the filter it opens with
export function target(params) {
  const [p0 = "", p1 = "", p2 = ""] = params.map((x) => decodeURIComponent(x));
  const q = new URLSearchParams();
  if (p0 === "themes" && /^TH-[0-9A-F]+$/.test(p1)) {
    return { file: `theses/${p1}.html`, q, thesis: p1 };
  }
  if (p0 === "themes" && (p1 === "area" || p1 === "sort") && p2) q.set(p1, p2);
  if (p0 === "articles" && /^[\w.-]+$/.test(p1)) return { file: `articles-${p1}.html`, q };
  return { file: SCREENS[p0] || SCREENS[""], q };
}

// a standalone page's link → the app's route, or the published page in a new tab
export function mapHref(href, file) {
  if (/^(https?:|mailto:)/.test(href)) return { href, external: true };
  if (href.startsWith("#")) return { scroll: href.slice(1) };
  const u = new URL(href, "https://desk.invalid/site/" + file);
  const path = u.pathname.replace(/^\/site\//, "");
  let m;
  if (path === "index.html") return { href: "#/intel" };
  if (path === "themes.html") {
    const area = u.searchParams.get("area");
    const sort = u.searchParams.get("sort");
    return { href: "#/intel/themes" + (area ? "/area/" + encodeURIComponent(area)
      : sort ? "/sort/" + encodeURIComponent(sort) : "") };
  }
  if ((m = path.match(/^articles(?:-([\w.-]+))?\.html$/))) {
    return { href: "#/intel/articles" + (m[1] ? "/" + m[1] : "") };
  }
  if ((m = path.match(/^(review|uploads|sources)\.html$/))) return { href: "#/intel/" + m[1] };
  if ((m = path.match(/^theses\/(TH-[0-9A-F]+)\.html$/))) return { href: "#/intel/themes/" + m[1] };
  // a card (the Full record), the weekly report, the printable report: the published page itself
  return { href: BASE + "site/" + path + u.search + u.hash, external: true };
}

let assets = null;
function loadAssets() {
  if (!assets) {
    assets = new Promise((resolve, reject) => {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = BASE + "intel.css";
      document.head.appendChild(link);
      const s = document.createElement("script");
      s.src = BASE + "desk.js";
      s.onload = () => resolve();
      s.onerror = () => { assets = null; reject(new Error("theme-intelligence/desk.js is missing")); };
      document.head.appendChild(s);
    });
  }
  return assets;
}

function notPublished(frame, item, why) {
  return frame(item, { bodyHtml: `
    <div class="notice"><b>No theme-intelligence run is published yet.</b>
      <span class="muted">(${escapeHtml(why)})</span><br>
      Publish one from the registry of record, then commit the folder as an artifact-only commit
      and push — the site shows it on the next deploy:
      <pre>python -m vinci.theme_intelligence state pull
python -m vinci.theme_intelligence publish
git add frontend/theme-intelligence &amp;&amp; git commit -m "theme intelligence: publish"</pre>
    </div>` });
}

export async function render(root, params, { item, frame }) {
  const t = target(params);
  let html;
  try {
    const r = await fetch(BASE + "site/" + t.file, { cache: "no-cache" });
    if (!r.ok) throw new Error(`${t.file}: HTTP ${r.status}`);
    html = await r.text();
  } catch (e) {
    root.innerHTML = notPublished(frame, item, e.message);
    return;
  }
  const doc = new DOMParser().parseFromString(html, "text/html");
  const main = doc.querySelector("main.wrap");
  if (!main) {
    // Cloudflare Pages answers a missing file with the app's own index (HTTP 200)
    // (lib/snapshots.js): the page is not in the published desk
    root.innerHTML = t.file === SCREENS[""]
      ? notPublished(frame, item, `${t.file} is not in the published folder`)
      : frame(item, { bodyHtml: `<div class="notice"><b>This page is not in the published research
          desk.</b> <span class="muted">(${escapeHtml(t.file)} — it may belong to an earlier
          publication)</span><br><a href="#/intel">Open This week</a></div>` });
    return;
  }
  const banner = doc.querySelector(".testdata");
  for (const a of main.querySelectorAll("a[href]")) {
    const to = mapHref(a.getAttribute("href"), t.file);
    if (to.scroll !== undefined) {
      a.setAttribute("href", "#");
      a.dataset.scroll = to.scroll;
      continue;
    }
    a.setAttribute("href", to.href);
    if (to.external) { a.target = "_blank"; a.rel = "noopener"; }
  }
  const title = t.thesis ? ((main.querySelector("h1") || {}).textContent || t.thesis) : "";
  root.innerHTML = frame(item, {
    crumbExtra: t.thesis ? `<span class="sep">/</span>${escapeHtml(title)}` : "",
    title,
    bodyHtml: `<input type="checkbox" id="intel-audit" hidden>`
      + `<div class="intel-bar"><label for="intel-audit" class="intel-auditbar" `
      + `title="Show engine ids, codes and the decision trace">Audit view</label></div>`
      + `<div class="intel">${banner ? banner.outerHTML : ""}${main.innerHTML}</div>`,
  });
  const box = root.querySelector(".intel");
  // an in-page link (a page's own "#review") scrolls — the hash is the app's router
  box.addEventListener("click", (ev) => {
    const a = ev.target.closest ? ev.target.closest("a[data-scroll]") : null;
    if (!a) return;
    ev.preventDefault();
    const el = box.querySelector("#" + CSS.escape(a.dataset.scroll));
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  await loadAssets();
  window.deskInit(box, t.q);
}
