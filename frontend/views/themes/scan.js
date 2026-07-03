// SCAN · TIERS (#/themes/scan) — per-driver surfaced/frozen names, tiered by disclosure
// concreteness (binding / quantified / committed / aspirational). A filterable table in the
// Screen·Overshoot visual language, with a driver selector. The machine TIERS; it never ranks.
import { getThemesIndex, getThemeDriver } from "../../lib/snapshots.js";
import { fmtInt, escapeHtml } from "../../lib/format.js";

let DRIVERS = [];
const CACHE = {};      // slug -> driver json (immutable per page load)
let SEL = null;
let q = "";

// tier → pill colour (buy=green REAL, unresolved=grey committed, conditional=amber aspirational)
const BASIS_PILL = { binding: "buy", quantified: "buy", committed: "unresolved",
                     aspirational: "conditional", none: "locked" };

export async function render(root, { item, frame }) {
  q = "";
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading scan tiers…</div>` });
  const idx = await getThemesIndex();
  DRIVERS = idx.drivers;
  if (!DRIVERS.length) {
    root.innerHTML = frame(item, { bodyHtml: `<div class="notice">No theme artifacts committed to this deploy yet.</div>` });
    return;
  }
  SEL = SEL && DRIVERS.some((d) => d.slug === SEL) ? SEL : DRIVERS[0].slug;
  await ensure(SEL);
  paint(root, item, frame);
}

async function ensure(slug) {
  if (!CACHE[slug]) CACHE[slug] = await getThemeDriver(slug);
  return CACHE[slug];
}

function paint(root, item, frame) {
  const d = CACHE[SEL];
  const t = d.tierShape || {};
  const real = (t.binding || 0) + (t.quantified || 0);
  const selector = DRIVERS.map((dr) =>
    `<button class="pill ${dr.slug === SEL ? "buy" : "unresolved"}" data-slug="${escapeHtml(dr.slug)}"
      style="cursor:pointer; border:none; font-family:var(--sans);">${escapeHtml(dr.label)}</button>`).join(" ");

  const shape = `<div class="foot" style="margin-bottom:10px;">
    frozen tier <b>${fmtInt(d.frozenCount)}</b> names · surfaced ${fmtInt(d.surfacedCount)}
    (${fmtInt(real)} REAL / ${fmtInt(t.committed)} committed / ${fmtInt(t.aspirational)} aspirational /
    ${t.none == null ? "—" : fmtInt(t.none)} none of ${t.universe == null ? "—" : fmtInt(t.universe)} scanned)</div>`;

  const controls = `
    <div style="display:flex; gap:10px; align-items:center; margin-bottom:10px; flex-wrap:wrap;">
      <span class="foot">driver:</span>${selector}
    </div>
    ${shape}
    <div style="display:flex; gap:14px; align-items:center; margin-bottom:12px;">
      <input id="th-q" type="search" placeholder="Filter ticker · category · fact…" autocomplete="off" value=""
        style="flex:1; min-width:200px; padding:8px 11px; border:1px solid var(--line-2); border-radius:8px; font-size:13px;" />
      <span class="muted" style="font-size:12px;">the machine TIERS · it never ranks or scores</span>
    </div>
    <table class="data"><thead><tr>
      <th>Ticker</th><th>Category</th><th>Driver tie</th><th>Tier</th><th>★ grade fact</th><th>Source</th>
    </tr></thead><tbody id="th-body"></tbody></table>`;

  root.innerHTML = frame(item, { bodyHtml: controls });
  rows();
  root.querySelector("#th-q").addEventListener("input", (e) => { q = e.target.value.toLowerCase(); rows(); });
  root.querySelectorAll("[data-slug]").forEach((b) => b.addEventListener("click", async () => {
    if (b.dataset.slug === SEL) return;
    SEL = b.dataset.slug; q = "";
    root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading ${escapeHtml(SEL)}…</div>` });
    await ensure(SEL);
    paint(root, item, frame);
  }));
}

function rows() {
  const body = document.getElementById("th-body");
  if (!body) return;
  const d = CACHE[SEL];
  const names = (d.names || []).filter((n) => !q
    || n.ticker.toLowerCase().includes(q)
    || (n.substructureTag || "").toLowerCase().includes(q)
    || (n.gradeFact || "").toLowerCase().includes(q));
  body.innerHTML = names.map((n) => `
    <tr>
      <td class="mono" style="font-weight:600;">${escapeHtml(n.ticker)}</td>
      <td class="muted" style="font-size:12px; white-space:nowrap;">${escapeHtml(n.substructureTag || "")}</td>
      <td style="font-size:12px;">${escapeHtml(n.driverTie || "")}</td>
      <td><span class="pill ${BASIS_PILL[n.basis] || "unresolved"}">${escapeHtml(n.basis)}</span></td>
      <td style="font-size:12px; max-width:440px; line-height:1.5;">${escapeHtml(n.gradeFact || "")}</td>
      <td>${n.edgarUrl
        ? `<a href="${encodeURI(n.edgarUrl)}" target="_blank" rel="noopener" style="font-size:11.5px; white-space:nowrap;">EDGAR ${escapeHtml(n.accession || "")}</a>`
        : `<span class="muted" style="font-size:11.5px;">${escapeHtml(n.accession || "—")}</span>`}</td>
    </tr>`).join("") || `<tr><td colspan="6" class="muted" style="padding:18px;">No names match the filter.</td></tr>`;
}
