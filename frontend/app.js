// ============================================================================
// App shell — information architecture (nav), client-side router, and the
// shared sub-screen frame. No backend; hash routing over a static mirror.
//
// EDGE-FIRST nav (data-driven, scales to N edges/themes):
//   left rail = a SHARED zone (always-visible direct links) + an EDGES list
//   (named edges). Selecting an edge shows ITS stages as TOP-TABS across the
//   content area. Adding an edge or a stage is a DATA change to the registries
//   below — never a nav rewrite. Then the validation gate, then Capital.
//
// Each item/edge carries a state:
//   live | home  — a functional read-only screen (green dot)
//   locked       — inert; clicking shows WHAT it will do + its TRIGGER
//   conditional  — built only if the manual loop reveals it is needed
// ============================================================================
import { escapeHtml } from "./lib/format.js";

const GATE_DEF = "the BUY−AVOID spread that must prove positive before capital deploys";

// --- SHARED zone: edge-agnostic, always-visible direct links -----------------
const SHARED = [
  { route: "overview", label: "Overview", state: "home" },
  { route: "dossier", label: "Dossier", state: "live",
    does: "Assembled facts · no verdict. A source-bound mechanical layer plus a fenced bull/bear framing — the framing, not the answer." },
  { route: "decision-log", label: "Decision log", state: "live",
    does: "The immutable, append-only ledger of logged verdicts — each a frozen leg of the BUY−AVOID spread. Displayed here; logged only via the CLI." },
];

// --- EDGE REGISTRY: adding an edge / a stage is a DATA change here ------------
// Each edge: { key, label, state, stages:[{route,label,does,state?,cond?}], route?, lock? }.
// A LIVE edge lists its stages as top-tabs; a LOCKED edge (no stages) is an inert
// placeholder reached at its own `route`.
const EDGES = [
  {
    key: "overshoot", label: "Overshoot", state: "live",
    stages: [
      { route: "ingestion", label: "Ingestion & universe",
        does: "Data freshness across the funnel — the resolved universe, the screen output, and the EOD price date the screen ran on. Honest staleness, point-in-time." },
      { route: "screen-overshoot", label: "Screen",
        does: "The overshoot screen. Three gates: a deep drawdown (G1), idiosyncratic vs the market (G2), and a multiple at the name's own floor (G3)." },
      { route: "ranker", label: "Ranker",
        does: "Orders the screen's candidates into a priority queue by structural profile. Orders, never decides — a lagging description of the setup, not a return prediction." },
      { route: "graph", label: "Cross-sector graph",
        does: "Entity → exposed-names lookup with 10-K provenance. A research input only — it gates nothing and predicts nothing." },
      { route: "verification", label: "Verification", state: "conditional",
        cond: {
          what: "A structured bull / bear / judge step over a finalist.",
          trigger: "Conditional · built only if operating the manual loop reveals it is needed. May never be built.",
        } },
    ],
  },
  {
    key: "themes", label: "Themes", state: "live",
    stages: [
      { route: "themes", label: "Overview",
        does: "Theme-edge status across both drivers. 0 buys — the edge surfaces watchlists, not buys (yet)." },
      { route: "themes/scan", label: "Surfaced names",
        does: "Per-driver surfaced names, tiered by disclosure grade. The machine tiers; it never ranks. Click a row for the full grade fact + filing." },
      { route: "themes/watchlist", label: "Watchlist",
        does: "The names to re-underwrite when a trigger fires — the manual-monitoring surface. Each name is led by its verbatim trigger." },
      { route: "themes/forward", label: "Forward performance",
        does: "The validation-gate analogue: snapshot cohorts, buy-dependent spreads UNDEFINED (zero buys), diagnostics pending forward. Not a validated edge." },
    ],
  },
  {
    key: "neglected", label: "Neglected", state: "locked", route: "screen-neglected",
    lock: {
      what: "Surfaces orphaned / under-covered (“neglected”) names — its own edge, where mispricing is neglect rather than overreaction.",
      trigger: "Unlocks when the validation gate clears: ≥2 quarters of resolved verdicts showing the discriminator adds value.",
    },
  },
];

// --- CAPITAL zone: locked until the gate clears ------------------------------
const CAPITAL = [
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
];

// View modules registered by BASE route (first hash segment). The Theme-edge
// sub-routes (#/themes/scan …) all resolve to the ONE `themes` module.
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

// Every routable item: shared + each live edge's stages + each locked edge's own
// landing + capital. resolveItem searches this; the registries above stay the
// single source of truth (this is just the flattened index).
const ITEMS = [
  ...SHARED,
  ...EDGES.flatMap((e) =>
    e.stages && e.stages.length ? e.stages
    : [{ route: e.route, label: e.label, state: e.state, lock: e.lock, cond: e.cond }]),
  ...CAPITAL,
];

// where clicking an edge in the rail goes (its first live stage, or its own landing)
function edgeLanding(edge) {
  if (edge.stages && edge.stages.length) {
    const s = edge.stages.find((st) => st.state !== "locked") || edge.stages[0];
    return s.route;
  }
  return edge.route;
}

// the edge that OWNS a resolved item (by a stage route, or a locked edge's own
// landing) — for the top-tabs + the rail highlight. null for shared / capital.
function edgeOfItem(item) {
  for (const e of EDGES) {
    if ((e.stages || []).some((s) => s.route === item.route)) return e;
    if (e.route && e.route === item.route) return e;
  }
  return null;
}

// Resolve the nav item for a full path by LONGEST route-prefix, so a sub-route
// (#/themes/scan) resolves to its own stage while a detail path (#/dossier/TICKER)
// still resolves to its section. Path-segment aware ("themes" matches "themes/scan"
// but not "themestuff").
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

// --- sidebar (the left rail) -------------------------------------------------
const stateNode = (state) =>
  state === "live" ? `<span class="ni-state"><span class="dot live" title="live"></span></span>`
  : state === "locked" ? `<span class="ni-state lock-ico" title="locked">🔒</span>`
  : state === "conditional" ? `<span class="ni-state cond-ico" title="conditional">◑</span>`
  : "";

function renderSidebar() {
  const sharedItem = (it) => `
    <a class="nav-item" data-route="${it.route}" href="#/${it.route}">
      <span class="ni-label">${escapeHtml(it.label)}</span>${stateNode(it.state)}
    </a>`;
  const edgeItem = (e) => `
    <a class="nav-item ${e.state === "locked" ? "locked" : ""}" data-edge="${e.key}" href="#/${edgeLanding(e)}">
      <span class="ni-label">${escapeHtml(e.label)}</span>${stateNode(e.state)}
    </a>`;
  const capItem = (it) => `
    <a class="nav-item locked" data-route="${it.route}" href="#/${it.route}">
      <span class="ni-label">${escapeHtml(it.label)}</span>${stateNode("locked")}
    </a>`;

  document.getElementById("sidebar").innerHTML = `
    <div class="brand">
      <div class="mark">Nostra Vinci</div>
      <div class="sub">research &amp; decision ops · read-only</div>
    </div>
    <div class="nav-group"><div class="label">Shared</div>${SHARED.map(sharedItem).join("")}</div>
    <div class="nav-group"><div class="label">Edges</div>${EDGES.map(edgeItem).join("")}</div>
    <div class="nav-gate">
      <div class="g-title">⟐ Validation gate</div>
      <div class="g-def">${escapeHtml(GATE_DEF)}.</div>
    </div>
    <div class="nav-group">
      <div class="label">Capital</div><div class="sublabel">locked until the gate clears</div>
      ${CAPITAL.map(capItem).join("")}
    </div>`;
}

// highlight the rail: the owning EDGE (data-edge) for an edge item, else the
// shared/capital item (data-route).
function setActive(item) {
  const edge = edgeOfItem(item);
  document.querySelectorAll(".nav-item").forEach((el) => {
    const on = el.dataset.edge
      ? (edge && edge.key === el.dataset.edge)
      : (el.dataset.route === item.route);
    el.classList.toggle("active", !!on);
  });
}

// --- shared sub-screen frame -------------------------------------------------
// For an EDGE stage, the header is the edge name + a TOP-TAB bar of the edge's
// stages (the active one highlighted), then the stage's own subtitle. For a
// SHARED view it is the classic breadcrumb + header-block. `bare` (the dossier
// DETAIL) omits the header-block; the dossier supplies its own ticker header.
export function frame(item, { crumbExtra = "", bodyHtml = "", bare = false } = {}) {
  const subtitle = item.does ? `<div class="subtitle">${escapeHtml(item.does)}</div>` : "";
  const persistent = item.route === "dossier"
    ? `<div class="subtitle muted">assembled facts · no verdict</div>` : "";
  const edge = edgeOfItem(item);

  if (edge && edge.stages && edge.stages.length && !bare) {
    const tabs = edge.stages.map((s) => {
      const active = s.route === item.route;
      const ico = s.state === "conditional" ? ` <span class="cond-ico" title="conditional">◑</span>` : "";
      return `<a class="tab ${active ? "active" : ""}" data-route="${s.route}" href="#/${s.route}">${escapeHtml(s.label)}${ico}</a>`;
    }).join("");
    return `
      <div class="breadcrumb"><a href="#/overview">Overview</a><span class="sep">/</span>${escapeHtml(edge.label)}</div>
      <div class="edge-head">
        <h1 class="page-h">${escapeHtml(edge.label)}</h1>
        <nav class="tabs">${tabs}</nav>
      </div>
      ${subtitle || persistent ? `<div class="stage-sub">${subtitle}${persistent}</div>` : ""}
      ${bodyHtml}`;
  }

  const headerBlock = bare ? "" : `
    <div class="header-block">
      <h1 class="page-h">${escapeHtml(item.label)}</h1>
      ${subtitle}${persistent}
    </div>`;
  const sectionCrumb = crumbExtra
    ? `<a href="#/${item.route}">${escapeHtml(item.label)}</a>`
    : escapeHtml(item.label);
  return `
    <div class="breadcrumb"><a href="#/overview">Overview</a><span class="sep">/</span>${sectionCrumb}${crumbExtra}</div>${headerBlock}
    ${bodyHtml}`;
}

// --- locked / conditional placeholders (routed through frame → get any tabs) --
function renderLocked(root, item) {
  const L = item.lock;
  root.innerHTML = frame(item, { bodyHtml: `
    <div class="subtitle muted" style="margin-bottom:14px;">Locked — not yet built. This page describes the stage's future existence; it is not the stage.</div>
    <div class="placeholder locked">
      <span class="lock-badge">🔒 Locked</span>
      <div class="what">${escapeHtml(L.what)}</div>
      <div class="trigger"><span class="k">Unlock trigger</span>${escapeHtml(L.trigger)}</div>
      <div class="note">Inert placeholder — no functionality is built here, by design.</div>
    </div>` });
}

function renderConditional(root, item) {
  const C = item.cond;
  root.innerHTML = frame(item, { bodyHtml: `
    <div class="subtitle muted" style="margin-bottom:14px;">Conditional — not gated behind the spread; built only if the loop needs it.</div>
    <div class="placeholder conditional">
      <span class="lock-badge">◑ Conditional</span>
      <div class="what">${escapeHtml(C.what)}</div>
      <div class="trigger"><span class="k">When</span>${escapeHtml(C.trigger)}</div>
    </div>` });
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
  setActive(item);
  window.scrollTo(0, 0);

  try {
    if (item.state === "locked") return renderLocked(root, item);
    if (item.state === "conditional") return renderConditional(root, item);

    const loader = VIEWS[route];   // base route (first hash segment) → the view module
    if (loader) {
      const mod = await loader();
      return mod.render(root, params, { item, frame });
    }
    root.innerHTML = frame(item, {
      bodyHtml: `<div class="notice">This live screen is built in the next pass. The frame, breadcrumb, and orientation above are final.</div>`,
    });
  } catch (e) {
    root.innerHTML = `<div class="error"><b>Could not render ${escapeHtml(item.label)}.</b><br>${escapeHtml(e.message)}<br><span class="muted">If snapshots are missing locally, run <code>python3 frontend/build.py</code> first.</span></div>`;
  }
}

renderSidebar();
window.addEventListener("hashchange", dispatch);
dispatch();
