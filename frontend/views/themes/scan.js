// SURFACED NAMES (#/themes/scan) — per-driver surfaced/snapshot names, tiered by disclosure grade.
// A scannable table with PROGRESSIVE DISCLOSURE: each row shows decision-relevant fields + a one-line
// summary; the full grade fact + filing expand on row click. Driver = a dropdown (scales to N themes).
// The machine TIERS; it never ranks.
import { getThemesIndex, getThemeDriver } from "../../lib/snapshots.js";
import { fmtInt, escapeHtml, gradeLabel, GRADE_DEF } from "../../lib/format.js";

let DRIVERS = [];
const CACHE = {};      // slug -> driver json (immutable per page load)
let SEL = null;
let q = "";

// tier → pill colour (buy=green REAL, unresolved=grey committed, conditional=amber aspirational)
const BASIS_PILL = { binding: "buy", quantified: "buy", committed: "unresolved",
                     aspirational: "conditional", none: "locked" };
const GRADE_KEY = `<div class="grade-key">${
  ["binding", "quantified", "committed", "aspirational", "none"].map((g) =>
    `<span class="gk"><b>${gradeLabel(g)}</b> — ${GRADE_DEF[g]}</span>`).join("")}</div>`;

function oneLine(s) {
  s = String(s || "").trim();
  return s.length <= 110 ? s : s.slice(0, 110).replace(/\s+\S*$/, "") + "…";
}

export async function render(root, { item, frame }) {
  q = "";
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading surfaced names…</div>` });
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
  const selector = `<select id="th-driver" class="filter-select" aria-label="driver">${
    DRIVERS.map((dr) => `<option value="${escapeHtml(dr.slug)}" ${dr.slug === SEL ? "selected" : ""}>${escapeHtml(dr.label)}</option>`).join("")}</select>`;

  const shape = `<div class="foot" style="margin-bottom:12px;">
    ${fmtInt(d.frozenCount)} in snapshot · ${fmtInt(d.surfacedCount)} surfaced
    (${fmtInt(real)} REAL / ${fmtInt(t.committed)} committed / ${fmtInt(t.aspirational)} aspirational /
    ${t.none == null ? "—" : fmtInt(t.none)} no exposure of ${t.universe == null ? "—" : fmtInt(t.universe)} scanned)</div>`;

  const controls = `
    <div style="display:flex; gap:12px; align-items:center; margin-bottom:12px; flex-wrap:wrap;">
      <label class="foot" for="th-driver">Driver</label>${selector}
      <input id="th-q" type="search" placeholder="Filter ticker · category · fact…" autocomplete="off" value=""
        style="flex:1; min-width:180px; padding:8px 11px; border:1px solid var(--line-2); border-radius:8px; font-size:13px;" />
      <span class="muted" style="font-size:12px;">the machine tiers · click a row for detail</span>
    </div>
    ${GRADE_KEY}${shape}
    <table class="data"><thead><tr>
      <th>Ticker</th><th>Category</th><th>Driver tie</th><th>Grade</th><th>Grade fact</th>
    </tr></thead><tbody id="th-body"></tbody></table>`;

  root.innerHTML = frame(item, { bodyHtml: controls });
  rows();
  root.querySelector("#th-q").addEventListener("input", (e) => { q = e.target.value.toLowerCase(); rows(); });
  root.querySelector("#th-driver").addEventListener("change", async (e) => {
    SEL = e.target.value; q = "";
    root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading ${escapeHtml(SEL)}…</div>` });
    await ensure(SEL);
    paint(root, item, frame);
  });
}

function rows() {
  const body = document.getElementById("th-body");
  if (!body) return;
  const d = CACHE[SEL];
  const names = (d.names || []).filter((n) => !q
    || n.ticker.toLowerCase().includes(q)
    || (n.substructureTag || "").toLowerCase().includes(q)
    || (n.gradeFact || "").toLowerCase().includes(q));

  body.innerHTML = names.map((n, i) => `
    <tr class="exp" data-i="${i}">
      <td class="mono" style="font-weight:600;"><span class="caret">▸</span> ${escapeHtml(n.ticker)}</td>
      <td class="muted" style="font-size:12px; white-space:nowrap;">${escapeHtml(n.substructureTag || "")}</td>
      <td style="font-size:12px;">${escapeHtml(n.driverTie || "")}</td>
      <td><span class="pill ${BASIS_PILL[n.basis] || "unresolved"}">${escapeHtml(gradeLabel(n.basis))}</span></td>
      <td style="font-size:12px; color:var(--ink-2);">${escapeHtml(oneLine(n.gradeFact))}</td>
    </tr>
    <tr class="det" data-det="${i}" style="display:none;"><td colspan="5">
      <span class="k">grade fact</span>${escapeHtml(n.gradeFact || "—")}
      ${n.edgarUrl
        ? `<div style="margin-top:8px;"><a href="${encodeURI(n.edgarUrl)}" target="_blank" rel="noopener">EDGAR ${escapeHtml(n.accession || "")}</a></div>`
        : (n.accession ? `<div class="muted" style="margin-top:8px;">${escapeHtml(n.accession)}</div>` : "")}
    </td></tr>`).join("")
    || `<tr><td colspan="5" class="muted" style="padding:18px;">No names match the filter.</td></tr>`;

  body.querySelectorAll("tr.exp").forEach((tr) => tr.addEventListener("click", () => {
    const det = body.querySelector(`tr.det[data-det="${tr.dataset.i}"]`);
    if (!det) return;
    const open = det.style.display !== "none";
    det.style.display = open ? "none" : "table-row";
    tr.classList.toggle("open", !open);
  }));
}
