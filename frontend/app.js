// ============================================================================
// App shell — information architecture (nav), client-side router, and the
// shared sub-screen frame. No backend; hash routing over a static mirror.
//
// The nav is organized into ZONES (Shared / Edge 2 · Overshoot / Theme edge),
// then the validation gate, then Capital. Each item carries a state:
//   live        — a functional read-only sub-screen (green dot)
//   locked      — inert; clicking shows WHAT the stage will do + its TRIGGER
//   conditional — built only if the manual loop reveals it is needed
// ============================================================================
import { escapeHtml } from "./lib/format.js";

const GATE_DEF = "the BUY−AVOID spread that must prove positive before capital deploys";

const NAV = [
  {
    label: "Shared",
    items: [
      { route: "overview", label: "Overview", state: "home" },
      { route: "dossier", label: "Dossier", state: "live",
        does: "Assembled facts · no verdict. A source-bound mechanical layer plus a fenced bull/bear framing — the framing, not the answer." },
      { route: "decision-log", label: "Decision log", state: "live",
        does: "The immutable, append-only ledger of logged verdicts — each a frozen leg of the BUY−AVOID spread. Displayed here; logged only via the CLI." },
    ],
  },

  {
    label: "Edge 2 · Overshoot",
    items: [
      { route: "ingestion", label: "Ingestion & universe", state: "live",
        does: "Data freshness across the funnel — the resolved universe, the screen output, and the EOD price date the screen ran on. Honest staleness, point-in-time." },
      { route: "screen-overshoot", label: "Screen · Overshoot", state: "live",
        does: "The overshoot screen. Three gates: a deep drawdown (G1), idiosyncratic vs the market (G2), and a multiple at the name's own floor (G3)." },
      { route: "screen-neglected", label: "Screen · Neglected", state: "locked",
        lock: {
          what: "Surfaces orphaned / under-covered (“neglected”) names — the fund's second edge, where mispricing is neglect rather than overreaction.",
          trigger: "Unlocks when the validation gate clears: ≥2 quarters of resolved verdicts showing the discriminator adds value.",
        } },
      { route: "ranker", label: "Ranker", state: "live",
        does: "Orders the screen's candidates into a priority queue by structural profile. Orders, never decides — a lagging description of the setup, not a return prediction." },
      { route: "graph", label: "Cross-sector graph", state: "live",
        does: "Entity → exposed-names lookup with 10-K provenance. A research input only — it gates nothing and predicts nothing." },
      { route: "verification", label: "Verification", state: "conditional",
        cond: {
          what: "A structured bull / bear / judge step over a finalist.",
          trigger: "Conditional · built only if operating the manual loop reveals it is needed. May never be built.",
        } },
    ],
  },

  {
    label: "Theme edge",
    sublabel: "unvalidated research surface · watchlists, not buys",
    items: [
      { route: "themes", label: "Themes overview", state: "live",
        does: "Theme-edge fund status across both drivers. 0 RATIFIED — the edge surfaces watchlists, not buys (yet)." },
      { route: "themes/scan", label: "Scan · tiers", state: "live",
        does: "Per-driver surfaced names, tiered by disclosure concreteness (binding / quantified / committed / aspirational). The machine tiers; it never ranks." },
      { route: "themes/watchlist", label: "Watchlist · triggers", state: "live",
        does: "The names to re-underwrite when a trigger fires — the manual-monitoring surface. Each carries its verbatim re-underwrite trigger." },
      { route: "themes/forward", label: "Forward-track", state: "live",
        does: "The validation-gate analogue: frozen cohorts, RATIFIED-dependent spreads UNDEFINED (zero RATIFIED), diagnostics pending forward. Not a validated edge." },
    ],
  },

  { gate: true },

  {
    label: "Capital",
    sublabel: "locked until the gate clears",
    items: [
      { route: "sizing", label: "Sizing & risk", state: "locked",
        lock: {
          what: "Position sizing, risk limits, and portfolio construction for the concentrated book.",
          trigger: "Unlocks when the validation gate clears (the spread proves positive) — you can't size until the edge is shown real.",
        } },
      { route: "execution", label: "Execution · manual", state: "locked",
        lock: {
          what: "Human-authorized, paper-gated order placement. No code path reaches a live broker autonomously.",
          trigger: "Unlocks when sizing is built AND the spread is positive AND the regulatory gate (HK SFC Type 9) clears for real money.",
        } },
      { route: "monitoring", label: "Monitoring", state: "locked",
        lock: {
          what: "Thesis-break alerts, decay tracking, and position monitoring once capital is deployed.",
          trigger: "Unlocks when live positions exist (i.e. after execution).",
        } },
    ],
  },
];

// View modules registered as they are built, keyed by the BASE route (first hash
// segment). A `live` route with no module yet renders the consistent sub-screen
// frame with a "next pass" notice. The Theme-edge sub-routes (#/themes/scan …) all
// resolve to the ONE `themes` module, which sub-routes on params[0].
const VIEWS = {
  overview: () => import("./views/shared/overview.js"),
  dossier: () => import("./views/shared/dossier.js"),
  "decision-log": () => import("./views/shared/decision-log.js"),
  ingestion: () => import("./views/edge2/ingestion.js"),
  "screen-overshoot": () => import("./views/edge2/screen-overshoot.js"),
  ranker: () => import("./views/edge2/ranker.js"),
  graph: () => import("./views/edge2/graph.js"),
  themes: () => import("./views/themes/index.js"),
};

const ITEMS = NAV.flatMap((g) => g.items || []);

// Resolve the nav item for a full path by LONGEST route-prefix, so a sub-route
// (#/themes/scan) highlights its own item while a detail path (#/dossier/TICKER)
// still highlights its section. Path-segment aware: "themes" matches "themes/scan"
// but not a hypothetical "themestuff".
function resolveItem(route, params) {
  const full = [route, ...params].join("/");
  let best = null;
  for (const it of ITEMS) {
    if (it.route && (full === it.route || full.startsWith(it.route + "/"))) {
      if (!best || it.route.length > best.route.length) best = it;
    }
  }
  return best;
}

// --- sidebar -----------------------------------------------------------------
function renderSidebar() {
  const stateNode = (it) =>
    it.state === "live" ? `<span class="ni-state"><span class="dot live" title="live"></span></span>`
    : it.state === "locked" ? `<span class="ni-state lock-ico" title="locked">🔒</span>`
    : it.state === "conditional" ? `<span class="ni-state cond-ico" title="conditional">◑</span>`
    : "";

  const item = (it) => `
    <a class="nav-item ${it.state === "locked" ? "locked" : ""}" data-route="${it.route}" href="#/${it.route}">
      <span class="ni-label">${escapeHtml(it.label)}</span>${stateNode(it)}
    </a>`;

  const block = (g) => {
    if (g.gate) {
      return `<div class="nav-gate">
        <div class="g-title">⟐ Validation gate</div>
        <div class="g-def">${escapeHtml(GATE_DEF)}.</div>
      </div>`;
    }
    const head = g.label
      ? `<div class="label">${escapeHtml(g.label)}</div>${g.sublabel ? `<div class="sublabel">${escapeHtml(g.sublabel)}</div>` : ""}`
      : "";
    return `<div class="nav-group">${head}${g.items.map(item).join("")}</div>`;
  };

  document.getElementById("sidebar").innerHTML = `
    <div class="brand">
      <div class="mark">Nostra Vinci</div>
      <div class="sub">research &amp; decision ops · read-only</div>
    </div>
    ${NAV.map(block).join("")}`;
}

function setActive(route) {
  document.querySelectorAll(".nav-item").forEach((el) =>
    el.classList.toggle("active", el.dataset.route === route));
}

// --- shared sub-screen frame -------------------------------------------------
// `bare` omits the generic header block (the section h1 + its subtitles) — used by the dossier DETAIL
// page, where renderDossier() supplies its own ticker header (with the no-verdict framing) and the
// breadcrumb already names the section, so the generic block is pure duplication. The dossier INDEX
// keeps the full header — there it is the only orientation.
export function frame(item, { crumbExtra = "", bodyHtml = "", bare = false } = {}) {
  const subtitle = item.does ? `<div class="subtitle">${escapeHtml(item.does)}</div>` : "";
  const persistent = item.route === "dossier"
    ? `<div class="subtitle muted">assembled facts · no verdict</div>` : "";
  const headerBlock = bare ? "" : `
    <div class="header-block">
      <h1 class="page-h">${escapeHtml(item.label)}</h1>
      ${subtitle}${persistent}
    </div>`;
  // On a sub-page (crumbExtra present, e.g. a dossier detail) the section label is a MIDDLE crumb, so
  // link it back to the section index; on a top-level page it is the current page → plain text.
  const sectionCrumb = crumbExtra
    ? `<a href="#/${item.route}">${escapeHtml(item.label)}</a>`
    : escapeHtml(item.label);
  return `
    <div class="breadcrumb"><a href="#/overview">Overview</a><span class="sep">/</span>${sectionCrumb}${crumbExtra}</div>${headerBlock}
    ${bodyHtml}`;
}

// --- locked / conditional placeholders (NOT functional pages) ----------------
function renderLocked(root, item) {
  const L = item.lock;
  root.innerHTML = `
    <div class="breadcrumb"><a href="#/overview">Overview</a><span class="sep">/</span>${escapeHtml(item.label)}</div>
    <div class="header-block"><h1 class="page-h">${escapeHtml(item.label)}</h1>
      <div class="subtitle muted">Locked stage — not yet built. This page describes the stage's future existence; it is not the stage.</div>
    </div>
    <div class="placeholder locked">
      <span class="lock-badge">🔒 Locked</span>
      <div class="what">${escapeHtml(L.what)}</div>
      <div class="trigger"><span class="k">Unlock trigger</span>${escapeHtml(L.trigger)}</div>
      <div class="note">Inert placeholder — no functionality is built here, by design.</div>
    </div>`;
}

function renderConditional(root, item) {
  const C = item.cond;
  root.innerHTML = `
    <div class="breadcrumb"><a href="#/overview">Overview</a><span class="sep">/</span>${escapeHtml(item.label)}</div>
    <div class="header-block"><h1 class="page-h">${escapeHtml(item.label)}</h1>
      <div class="subtitle muted">Conditional stage — not gated behind the spread; built only if the loop needs it.</div>
    </div>
    <div class="placeholder conditional">
      <span class="lock-badge">◑ Conditional</span>
      <div class="what">${escapeHtml(C.what)}</div>
      <div class="trigger"><span class="k">When</span>${escapeHtml(C.trigger)}</div>
    </div>`;
}

// --- router ------------------------------------------------------------------
function parseHash() {
  const h = (location.hash || "#/overview").replace(/^#\/?/, "");
  const [route, ...rest] = h.split("/");
  return { route: route || "overview", params: rest };
}

async function dispatch() {
  const root = document.getElementById("main");
  const { route, params } = parseHash();
  const item = resolveItem(route, params);

  if (!item) { location.hash = "#/overview"; return; }
  setActive(item.route);
  window.scrollTo(0, 0);

  try {
    if (item.state === "locked") return renderLocked(root, item);
    if (item.state === "conditional") return renderConditional(root, item);

    const loader = VIEWS[route];   // base route (first hash segment) → the view module
    if (loader) {
      const mod = await loader();
      return mod.render(root, params, { item, frame });
    }
    // live route, module not built yet (phase 2/3) — show the consistent frame.
    root.innerHTML = frame(item, {
      bodyHtml: `<div class="notice">This live sub-screen is built in the next pass. The frame, breadcrumb, and persistent orientation above are final.</div>`,
    });
  } catch (e) {
    root.innerHTML = `<div class="error"><b>Could not render ${escapeHtml(item.label)}.</b><br>${escapeHtml(e.message)}<br><span class="muted">If snapshots are missing locally, run <code>python3 frontend/build.py</code> first.</span></div>`;
  }
}

renderSidebar();
window.addEventListener("hashchange", dispatch);
dispatch();
