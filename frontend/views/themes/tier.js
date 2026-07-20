// TIER ALTITUDE (#/themes/<theme>/<tier>) — ONLY that theme's that-tier names, as the scannable
// table: ticker, category, driver-tie, clean grade, one-line fact summary; the full grade fact +
// EDGAR filing expand on ROW CLICK (progressive disclosure — never inline paragraphs). Framed by
// the shared stage frame (tabs persist while drilling); a filter box + the grade key. You never
// face more than one tier of one theme.
import { getThemeDriver } from "../../lib/snapshots.js";
import { fmtInt, escapeHtml, gradeLabel, GRADE_DEF } from "../../lib/format.js";

// magnitude bucket → the underlying grade tiers (unchanged; the tiers are the source of truth)
const TIER_BASES = { firm: ["binding", "quantified"], partial: ["committed"], early: ["aspirational"] };
const TIER_LABEL = { firm: "firm · REAL", partial: "partial · committed", early: "early · aspirational" };
const BASIS_PILL = { binding: "buy", quantified: "buy", committed: "unresolved",
                     aspirational: "conditional", none: "locked" };
const GRADE_KEY = `<div class="grade-key">${
  ["binding", "quantified", "committed", "aspirational", "none"].map((g) =>
    `<span class="gk"><b>${gradeLabel(g)}</b> — ${GRADE_DEF[g]}</span>`).join("")}</div>`;

let NAMES = [];
let q = "";

function oneLine(s) {
  s = String(s || "").trim();
  return s.length <= 110 ? s : s.slice(0, 110).replace(/\s+\S*$/, "") + "…";
}
const crumbX = (slug, label, tier) =>
  `<span class="sep">/</span><a href="#/themes/${escapeHtml(slug)}">${escapeHtml(label || slug)}</a>` +
  `<span class="sep">/</span>${escapeHtml(TIER_LABEL[tier] || tier)}`;

let FRAME = null;

export async function render(root, { item, frame }, slug, tier) {
  q = "";
  FRAME = (label, title, bodyHtml) => frame(item, {
    title, crumbExtra: crumbX(slug, label, tier), bodyHtml });
  root.innerHTML = FRAME(slug, slug, `<div class="notice">Loading names…</div>`);
  const d = await getThemeDriver(slug);
  if (!d) {
    root.innerHTML = FRAME(slug, slug,
      `<div class="notice">Theme not found. <a href="#/themes">Back to the themes landing</a>.</div>`);
    return;
  }
  const bases = TIER_BASES[tier];
  if (!bases) {
    root.innerHTML = FRAME(d.label, d.label, `<div class="notice">The <b>${escapeHtml(tier)}</b> tier
      has no per-name detail in the snapshot (unsurfaced / not carried forward).
      <a href="#/themes/${escapeHtml(slug)}">Back to ${escapeHtml(d.label)}</a>.</div>`);
    return;
  }
  NAMES = (d.names || []).filter((n) => bases.includes(n.basis));
  paint(root, d, slug, tier);
}

function paint(root, d, slug, tier) {
  const controls = `
    <div class="subtitle muted" style="margin:-6px 0 12px;">Click a row for the full grade fact + filing</div>
    <div style="display:flex; gap:12px; align-items:center; margin-bottom:12px; flex-wrap:wrap;">
      <input id="th-q" type="search" placeholder="Filter ticker · category · fact…" autocomplete="off" value=""
        style="flex:1; min-width:180px; padding:8px 11px; border:1px solid var(--line-2); border-radius:8px; font-size:13px;" />
    </div>
    ${GRADE_KEY}
    <table class="data"><thead><tr>
      <th>Ticker</th><th>Category</th><th>Driver tie</th><th>Grade</th><th>Grade fact</th>
    </tr></thead><tbody id="th-body"></tbody></table>`;

  root.innerHTML = FRAME(d.label, `${d.label} · ${TIER_LABEL[tier] || tier}`, controls);
  rows();
  root.querySelector("#th-q").addEventListener("input", (e) => { q = e.target.value.toLowerCase(); rows(); });
}

function rows() {
  const body = document.getElementById("th-body");
  if (!body) return;
  const names = NAMES.filter((n) => !q
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
