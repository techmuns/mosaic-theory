// ============================================================================
// App shell — information architecture (nav), client-side router, and the
// shared sub-screen frame. No backend; hash routing over a static mirror.
//
// The nav IS the fund pipeline in sequence. Each item carries a state:
//   live        — a functional read-only sub-screen (green dot)
//   locked      — inert; clicking shows WHAT the stage will do + its TRIGGER
//   conditional — built only if the manual loop reveals it is needed
// ============================================================================
import { escapeHtml } from "./lib/format.js";

const GATE_DEF = "the BUY−AVOID spread that must prove positive before capital deploys";

const NAV = [
  { items: [{ route: "overview", label: "Overview", state: "home" }] },

  {
    label: "Research & decision loop",
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
      { route: "dossier", label: "Dossier", state: "live",
        does: "Assembled facts · no verdict. A source-bound mechanical layer plus a fenced bull/bear framing — the framing, not the answer." },
      { route: "verification", label: "Verification", state: "conditional",
        cond: {
          what: "A structured bull / bear / judge step over a finalist.",
          trigger: "Conditional · built only if operating the manual loop reveals it is needed. May never be built.",
        } },
      { route: "decision-log", label: "Decision log", state: "live",
        does: "The immutable, append-only ledger of logged verdicts — each a frozen leg of the BUY−AVOID spread. Displayed here; logged only via the CLI." },
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

// View modules registered as they are built. A `live` route with no module yet
// renders the consistent sub-screen frame with a "next pass" notice.
const VIEWS = {
  overview: () => import("./views/overview.js"),
  ingestion: () => import("./views/ingestion.js"),
  "screen-overshoot": () => import("./views/screen-overshoot.js"),
  ranker: () => import("./views/ranker.js"),
  graph: () => import("./views/graph.js"),
  "decision-log": () => import("./views/decision-log.js"),
  dossier: () => import("./views/dossier.js"),
};

const ITEMS = NAV.flatMap((g) => g.items || []);
const find = (route) => ITEMS.find((i) => i.route === route);

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
export function frame(item, { crumbExtra = "", bodyHtml = "" } = {}) {
  const subtitle = item.does ? `<div class="subtitle">${escapeHtml(item.does)}</div>` : "";
  const persistent = item.route === "dossier"
    ? `<div class="subtitle muted">assembled facts · no verdict</div>` : "";
  return `
    <div class="breadcrumb"><a href="#/overview">Overview</a><span class="sep">/</span>${escapeHtml(item.label)}${crumbExtra}</div>
    <div class="header-block">
      <h1 class="page-h">${escapeHtml(item.label)}</h1>
      ${subtitle}${persistent}
    </div>
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
  const item = find(route);

  if (!item) { location.hash = "#/overview"; return; }
  setActive(route);
  window.scrollTo(0, 0);

  try {
    if (item.state === "locked") return renderLocked(root, item);
    if (item.state === "conditional") return renderConditional(root, item);

    const loader = VIEWS[route];
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
