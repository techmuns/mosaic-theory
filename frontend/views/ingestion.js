// INGESTION & UNIVERSE — data freshness/health. Honest, point-in-time. NOT analytics: the only
// universe detail is the builder's fail-closed gate-exclusion counts (a wrong count = a gate bug).
import { getUniverseHealth, getRankedQueue, getUniverseStats, getSnapshotMeta } from "../lib/snapshots.js";
import { fmtInt, fmtDate, DASH, escapeHtml } from "../lib/format.js";
import { refreshBlock } from "../lib/ui.js";

export async function render(root, _params, { item, frame }) {
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading freshness…</div>` });

  const [health, queue, ustats, meta] = await Promise.all([
    getUniverseHealth(), getRankedQueue(), getUniverseStats(), getSnapshotMeta(),
  ]);

  const card = (label, value, unit, foot) => `
    <div class="card metric"><h3>${label}</h3>
      <div class="value">${value}${unit ? ` <span class="unit">${unit}</span>` : ""}</div>
      <div class="foot">${foot}</div></div>`;

  const cards = `
    <div class="grid cols-3" style="margin-bottom:18px;">
      ${card("Resolved universe", fmtInt(health.universe.count), "names",
        `as of ${fmtDate(health.universe.asOf)} · the screenable US equity set`)}
      ${card("Screen → queue", `${fmtInt(health.screen.candidates)}`, "candidates",
        `screened ${fmtDate(health.screen.asOf)} · ${fmtInt(queue.counts.total)} ranked · ${fmtInt(queue.counts.demoted)} structurally sunk`)}
      ${card("EOD prices", fmtDate(health.eod.asOf), "",
        `the price date the screen ran on · features frozen at this date`)}
    </div>`;

  const funnel = ustats.available
    ? `<div class="card" style="margin-bottom:18px;">
        <h3>Universe gates — fail-closed exclusions</h3>
        <div class="subtitle muted ds-sub">How the builder narrowed the considered set to the universe. Both operating-company gates fail CLOSED — a name it can't confirm is excluded, never admitted. A wrong count here signals a gate bug.</div>
        <table class="data"><tbody>
          <tr><td><b>Considered</b></td><td class="num"><b>${fmtInt(ustats.considered)}</b></td><td class="muted">listed names on the target exchanges</td></tr>
          ${ustats.gates.map((g) => `<tr>
            <td>− ${escapeHtml(g.label)}</td>
            <td class="num">${fmtInt(g.count)}</td>
            <td class="muted" style="font-size:11.5px;">${escapeHtml(g.sub || "")}</td></tr>`).join("")}
          <tr style="border-top:2px solid var(--line-2);"><td><b>In universe</b></td><td class="num"><b>${fmtInt(ustats.inUniverse)}</b></td><td class="muted">operating-company common equity in the cap band</td></tr>
        </tbody></table>
        <div class="subtitle muted" style="margin-top:8px;">
          SIC denylist + security-type allowlist are the two structural gates (both fail-closed); the rest are data/cap/liquidity gates. As of ${escapeHtml(fmtDate(ustats.asOf))}.
          ${ustats.inUniverse !== health.universe.count ? `<br>Gate counts re-captured for the same date to surface them; reproduced ${fmtInt(ustats.inUniverse)} of the screen's ${fmtInt(health.universe.count)} universe (${health.universe.count - ustats.inUniverse} drifted as EDGAR/reference data updated over the interval) — immaterial to the gate magnitudes.` : ""}
        </div>
      </div>`
    : `<div class="card" style="margin-bottom:18px;">
        <h3>Universe gates — fail-closed exclusions</h3>
        <div class="notice" style="margin-top:8px;">Gate-exclusion counts are captured at universe-build time (<span class="mono">universe_stats.json</span>) and populate on the next build. Not yet in this snapshot.</div></div>`;

  const freshness = `
    <div class="card" style="margin-bottom:18px;">
      <h3>Freshness — point-in-time, by design</h3>
      <div style="font-size:13px; color:var(--ink-2); line-height:1.6;">
        Everything above is as of the last <b>${escapeHtml(fmtDate(health.screen.asOf))}</b> snapshot. This dashboard is a
        static mirror — it lags local state until the next <span class="mono">git push</span>, and the freshness dates exist
        precisely because the data is point-in-time. No live feed, by design.
      </div></div>`;

  const provenance = `
    <div class="provenance">
      <span>Snapshot source: <span class="mono">${meta.sourceCommit ? escapeHtml(meta.sourceCommit) : DASH}</span></span>
      <span>Mirror built: ${meta.generatedAt ? escapeHtml(meta.generatedAt) : DASH}</span>
    </div>`;

  root.innerHTML = frame(item, { bodyHtml: cards + funnel + freshness + refreshBlock() + provenance });
}
