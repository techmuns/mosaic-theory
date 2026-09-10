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

const GATE_DEF = "the BUY−AVOID spread that must prove positive before capital deploys "
  + "(screen-origin overshoot only — other books carry their own curves)";

// --- SHARED zone: edge-agnostic, always-visible direct links -----------------
const SHARED = [
  { route: "overview", label: "Overview", state: "home" },
  { route: "dossier", label: "Dossier", state: "live",
    does: "Per-name research records — assembled-facts dossiers and first-cut underwrites, typed and kept distinct; the human's confirm/override is the verdict of record." },
  { route: "decision-log", label: "Decision log", state: "live",
    does: "The immutable, append-only ledger of logged verdicts — each a frozen leg of the BUY−AVOID spread, sealed beside the machine's proposal (confirm / override / no-proposal tracked). Displayed here; logged only via the CLI." },
  { route: "monitor-panels", label: "Monitor panels", state: "live",
    does: "What has happened to each followed name since it was underwritten, one panel per question — the call, its kill criteria, the multiple, what has printed since, dilution, attribution, and the sources behind all of it. A panel that does not apply to a name is absent; one that applies and cannot be computed says so and names what is missing. The machine surfaces an indicator; the human concludes." },
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
      // Two tabs, funnel order: the themes landing (glance — table, watchlist, intake strip),
      // then the radar intake (candidates -> inbox -> log). Theme pages and tier tables are
      // DRILL-DOWNS from the landing (#/themes/<theme>[/<tier>]), framed with these same tabs.
      { route: "themes", label: "Themes",
        does: "Where each driver stands, and what it needs next." },
      { route: "themes/radar", label: "Radar",
        does: "Every theme idea on one map — how real the evidence is vs how much price has already moved." },
    ],
  },
  {
    key: "calls", label: "Calls tape", state: "live",
    stages: [
      // No `does` on purpose: the frame prints it as a persistent subtitle, and on a cockpit that
      // is a paragraph of vertical space describing what the screen visibly is. The orientation
      // lives in the Spec key and the hint bar, where it is asked for rather than always on.
      { route: "calls", label: "Tape" },
      { route: "calls/scoreboard", label: "Scoreboard", state: "conditional",
        cond: {
          what: "Hit-rate, excess return and target-touch aggregates over the labelled calls.",
          trigger: "Conditional · unlocks at ~500 hand labels. Below that, 8,102 of the 8,185 rows carry a MACHINE guess rather than a human reading, so a headline number would describe the labeller rather than the author. (The build brief reports that labeller at ~55% on bias and ~62% on targets; that figure cannot be re-derived from this corpus — a hand label REPLACES the machine row at the same key, so the machine's own guess for the 83 read rows is retained nowhere. It is taken on trust, not verified here.)",
        } },
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
  "monitor-panels": () => import("./views/shared/panels.js"),
  ingestion: () => import("./views/edge2/ingestion.js"),
  "screen-overshoot": () => import("./views/edge2/screen-overshoot.js"),
  ranker: () => import("./views/edge2/ranker.js"),
  graph: () => import("./views/edge2/graph.js"),
  themes: () => import("./views/themes/index.js"),
  calls: () => import("./views/calls/tape.js"),
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
      <span class="brand-logo" aria-hidden="true"></span>
      <div class="mark">Nostra Vinci</div>
      <button class="theme-tog" id="theme-tog" type="button" aria-label="Toggle dark mode" title="Toggle dark mode"></button>
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
export function frame(item, { crumbExtra = "", title = "", bodyHtml = "", bare = false } = {}) {
  const subtitle = item.does ? `<div class="subtitle">${escapeHtml(item.does)}</div>` : "";
  const edge = edgeOfItem(item);

  if (edge && edge.stages && edge.stages.length && !bare) {
    const tabs = edge.stages.map((s) => {
      const active = s.route === item.route;
      const ico = s.state === "conditional" ? ` <span class="cond-ico" title="conditional">◑</span>` : "";
      return `<a class="tab ${active ? "active" : ""}" data-route="${s.route}" href="#/${s.route}">${escapeHtml(s.label)}${ico}</a>`;
    }).join("");
    // A drill-down (crumbExtra set) keeps the stage tabs but takes its OWN h1 (`title`) and
    // extends the breadcrumb — the edge label becomes the link back to the stage landing. The
    // drill-down supplies its own subtitle inside bodyHtml, so the stage subtitle is dropped.
    const drill = Boolean(crumbExtra);
    const crumbEdge = drill
      ? `<a href="#/${edge.stages[0].route}">${escapeHtml(edge.label)}</a>`
      : escapeHtml(edge.label);
    return `
      <div class="breadcrumb"><a href="#/overview">Overview</a><span class="sep">/</span>${crumbEdge}${crumbExtra}</div>
      <div class="edge-head">
        <h1 class="page-h">${escapeHtml(drill && title ? title : edge.label)}</h1>
        <nav class="tabs">${tabs}</nav>
      </div>
      ${!drill && subtitle ? `<div class="stage-sub">${subtitle}</div>` : ""}
      ${bodyHtml}`;
  }

  const headerBlock = bare ? "" : `
    <div class="header-block">
      <h1 class="page-h">${escapeHtml(item.label)}</h1>
      ${subtitle}
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
  let h = (location.hash || "#/overview").replace(/^#\/?/, "");
  // Legacy-route normalizer — old URLs keep working after the IA fold-in (radar joined the
  // themes sub-router; the flat watchlist/scan/forward screens folded into the landing).
  if (h === "radar" || h.startsWith("radar/")) h = "themes/" + h;
  else if (h === "themes/watchlist" || h === "themes/scan" || h === "themes/forward") h = "themes";
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

// --- theme toggle -----------------------------------------------------------
// The head script (index.html) stamps data-theme before first paint; this only
// keeps the icon in sync and flips + persists on click. Icon-only, per design:
// show the theme you'd switch TO (moon while light, sun while dark).
const MOON = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;
const SUN = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 1.6v2.4M12 20v2.4M3.5 3.5l1.7 1.7M18.8 18.8l1.7 1.7M1.6 12h2.4M20 12h2.4M3.5 20.5l1.7-1.7M18.8 5.2l1.7-1.7"/></svg>`;

function currentTheme() {
  const t = document.documentElement.getAttribute("data-theme");
  if (t === "light" || t === "dark") return t;
  return matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}
function applyTheme(t) {
  const root = document.documentElement;
  // suppress the component transitions (nav/tabs/rows) for the one frame the token flip paints —
  // otherwise those few elements fade while everything else snaps, giving a staggered switch.
  root.classList.add("theme-switching");
  root.setAttribute("data-theme", t);
  try { localStorage.setItem("nv-theme", t); } catch (e) { /* private mode */ }
  const btn = document.getElementById("theme-tog");
  if (btn) btn.innerHTML = t === "dark" ? SUN : MOON;
  requestAnimationFrame(() => requestAnimationFrame(() => root.classList.remove("theme-switching")));
}
function wireThemeToggle() {
  const btn = document.getElementById("theme-tog");
  if (!btn) return;
  btn.innerHTML = currentTheme() === "dark" ? SUN : MOON;
  btn.addEventListener("click", () => applyTheme(currentTheme() === "dark" ? "light" : "dark"));
}

renderSidebar();
wireThemeToggle();
window.addEventListener("hashchange", dispatch);
dispatch();
