// CROSS-SECTOR GRAPH — entity → exposed-names lookup with 10-K provenance.
// RESEARCH INPUT ONLY. The graph-as-signal is falsified; it gates nothing and
// predicts nothing. Having client-side data must never imply it drives a decision.
import { getGraphCoverage, getGraphExposure } from "../../lib/snapshots.js";
import { fmtInt, escapeHtml } from "../../lib/format.js";

const BANNER = `
  <div class="banner-research">
    <b>Research input — gates nothing, predicts nothing.</b> This is a 10-K-disclosed exposure lookup for
    the human to research, never a trade signal. The graph-as-mechanical-signal was tested and falsified;
    nothing here orders, scores, or drives a verdict.
  </div>`;

export async function render(root, _params, { item, frame }) {
  root.innerHTML = frame(item, { bodyHtml: BANNER + `<div class="notice">Loading exposure map…</div>` });
  const cov = await getGraphCoverage();

  if (!cov.available) {
    root.innerHTML = frame(item, { bodyHtml: BANNER + `
      <div class="notice">The exposure map is not part of this deploy (the derived <span class="mono">graph_coverage.json</span>
      is committed only to the private/authed repo). The lookup is available locally and via the <span class="mono">graph-exposure</span> CLI.</div>` });
    return;
  }

  const s = cov.stats;
  const search = `
    <div style="margin-bottom:6px;">
      <input id="gr-q" type="search" placeholder="Entity ticker or name (e.g. TSM, FUBO)…" autocomplete="off"
        style="width:100%; max-width:420px; padding:9px 12px; border:1px solid var(--line-2); border-radius:8px; font-size:13px;" />
    </div>
    <div class="subtitle muted" style="margin-bottom:14px;">
      ${fmtInt(s.totalEdges)} named relationships across ${fmtInt(s.withEdges)} of ${fmtInt(s.names)} names ·
      each edge carries the verbatim 10-K phrase it was read from. Model: ${escapeHtml(cov.model || "—")}.
    </div>
    <div id="gr-results"></div>`;

  root.innerHTML = frame(item, { bodyHtml: BANNER + search });
  renderDefault();

  const input = root.querySelector("#gr-q");
  let t = null;
  input.addEventListener("input", (e) => {
    clearTimeout(t);
    const q = e.target.value.trim();
    t = setTimeout(() => (q ? renderLookup(q) : renderDefault()), 160);
  });
}

function renderDefault() {
  getGraphCoverage().then((cov) => {
    const box = document.getElementById("gr-results");
    if (!box) return;
    const conns = (cov.superConnectors || []).slice(0, 24);
    const shared = (cov.sharedNodes || []).slice(0, 12);
    box.innerHTML = `
      <div class="card" style="margin-bottom:14px;">
        <h3>Most-shared counterparties (cross-section)</h3>
        <div class="subtitle muted" style="margin:0 0 10px;">Names multiple focal issuers disclose exposure to — where a shared dependency lives. A research starting point, not a signal.</div>
        ${shared.length ? `<table class="data"><thead><tr><th>Counterparty</th><th>Ticker</th><th class="num">Focals exposed</th><th>Names</th></tr></thead><tbody>
          ${shared.map((n) => `<tr>
            <td>${escapeHtml(n.name || "")}</td>
            <td class="mono">${escapeHtml(n.ticker || "—")}</td>
            <td class="num">${fmtInt(n.degree)}</td>
            <td class="mono muted" style="font-size:11.5px;">${escapeHtml((n.focals || []).join(", "))}</td>
          </tr>`).join("")}
        </tbody></table>` : `<div class="muted">No shared counterparties.</div>`}
      </div>
      ${conns.length ? `<div class="card"><h3>Super-connectors</h3>
        <div class="subtitle muted" style="margin:0 0 8px;">Focal names with the most disclosed relationships.</div>
        <div class="chips">${conns.map((c) => `<span class="chip mono" style="cursor:pointer;" data-look="${escapeHtml(c)}">${escapeHtml(c)}</span>`).join("")}</div></div>` : ""}`;
    box.querySelectorAll("[data-look]").forEach((el) =>
      el.addEventListener("click", () => {
        const inp = document.getElementById("gr-q");
        inp.value = el.dataset.look; renderLookup(el.dataset.look);
      }));
  });
}

function edgeRow(e, who) {
  return `<tr>
    <td><span class="mono" style="font-weight:600;">${escapeHtml(who)}</span></td>
    <td><span class="pill ${e.direction === "downstream" ? "live" : "unresolved"}">${escapeHtml(e.direction || "")}</span>
        <span class="muted" style="font-size:11.5px;"> ${escapeHtml(e.relType || "")}</span></td>
    <td style="max-width:520px;"><div>${escapeHtml(e.counterparty || e.focal || "")}${e.ticker ? ` <span class="mono muted">(${escapeHtml(e.ticker)})</span>` : ""}</div>
      ${e.evidence ? `<span class="cite">${escapeHtml(e.evidence.slice(0, 260))}${e.evidence.length > 260 ? "…" : ""}</span>` : ""}</td>
  </tr>`;
}

function renderLookup(q) {
  getGraphExposure(q).then((g) => {
    const box = document.getElementById("gr-results");
    if (!box) return;
    if (!g.found) {
      box.innerHTML = `<div class="notice">No 10-K-disclosed relationships found for <b>${escapeHtml(q)}</b> in the covered set.</div>`;
      return;
    }
    const asFocal = g.asFocal || [], namedBy = g.namedBy || [], co = g.coExposed || [];
    box.innerHTML = `
      ${asFocal.length ? `<div class="card" style="margin-bottom:14px;"><h3>${escapeHtml(g.entity)} discloses exposure to (${asFocal.length})</h3>
        <table class="data"><tbody>${asFocal.map((e) => edgeRow(e, g.entity)).join("")}</tbody></table></div>` : ""}
      ${namedBy.length ? `<div class="card" style="margin-bottom:14px;"><h3>Named by (${namedBy.length}) — who discloses exposure to ${escapeHtml(g.entity)}</h3>
        <table class="data"><tbody>${namedBy.map((e) => edgeRow(e, e.focal)).join("")}</tbody></table></div>` : ""}
      ${co.length ? `<div class="card"><h3>Co-exposed cross-section (${co.length})</h3>
        <div class="subtitle muted" style="margin:0 0 8px;">Other names sharing a counterparty with ${escapeHtml(g.entity)} — for the human to research, not a signal.</div>
        <div class="chips">${co.slice(0, 30).map((c) => `<span class="chip mono">${escapeHtml(c.ticker)}<span class="muted"> · ${escapeHtml((c.via || "").slice(0, 24))}</span></span>`).join("")}</div></div>` : ""}`;
  });
}
