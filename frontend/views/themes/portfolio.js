// PORTFOLIO ALTITUDE (#/themes) — the theme-edge landing. The POOLED forward state (0 buys, on-watch,
// undefined-spread honesty + pending diagnostics) sits at the top — cross-theme facts, so they live
// here, not in a per-driver tab. Then ONE ROW PER THEME, its counts split into TWO labeled blocks: the
// VERDICT · analyst block (Buys, Watch — the analyst's call, primary) and the SCAN · machine read block
// (Firm/Partial/Early/none — the machine's firmness read, muted inventory). The Scan counts ARE the
// drill affordance (tap → that theme's that-tier names). No individual names here. N themes = N rows.
import { getThemesIndex } from "../../lib/snapshots.js";
import { fmtInt, fmtDate, DASH, escapeHtml } from "../../lib/format.js";

// The verdict/scan key — the grade-vs-verdict distinction. VERDICT is the ANALYST's call; SCAN is the
// MACHINE's read of firmness. The Buy bar is the fund's ≥2:1 reward-to-risk bar (never 3:1).
const VS_KEY = `<div class="vs-key">
  <div class="vs-key-row"><span class="vs-key-tag verdict">Verdict · analyst</span>
    <span><b>Buys</b> cleared the fund's ≥2:1 bar (reward-to-risk) · <b>Watch</b> = real exposure that
    failed only on price / materiality, carries a re-underwrite trigger</span></div>
  <div class="vs-key-row"><span class="vs-key-tag scan">Scan · machine read</span>
    <span><b>firm</b> = contracted / quantified · <b>partial</b> = real activity, not contracted ·
    <b>early</b> = stated intent · <b>none</b> = no exposure disclosed</span></div>
</div>`;

export async function render(root, { item, frame }) {
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading theme-edge portfolio…</div>` });
  const idx = await getThemesIndex();
  if (!idx.drivers.length) {
    root.innerHTML = frame(item, { bodyHtml: `
      <div class="notice">No theme artifacts committed to this deploy yet. Produce them with
      <code>python3 frontend/build.py --themes-src &lt;snapshot dir(s)&gt;</code>.</div>` });
    return;
  }

  const pf = idx.pooledForward || {};
  const cd = idx.crossDriver || {};

  // POOLED forward — ONE compact honest strip. The load-bearing honesty stays on the surface (0 buys,
  // spreads UNDEFINED · never 0.0, diagnostics pending, "unvalidated research surface"); the verbose
  // enumeration (the per-measure list, diagnostic notes, the verbatim label) is detail-on-demand behind
  // "methodology". No power-floor bar here — it restated the same "not readable yet" fact via the LEAST-
  // binding gate (theme count), overstated readiness (50% while 0 buys / 0 days forward), and would
  // saturate at scale; §4 power stays enforced in the backend, surfacing on the forward view once
  // spreads are DEFINED. powerFloor is still carried in index.json for that later consumer.
  const nThemes = fmtInt(cd.driversFrozen ?? idx.drivers.length);
  const strip = `
    <div class="pooled-strip">
      <div class="ps-row">
        <div>
          <div class="ps-tag">Theme edge · unvalidated research surface</div>
          <div style="margin-top:2px;"><b class="ps-buys">${fmtInt(pf.totalBuys ?? 0)} Buys</b><span class="ps-sub">across ${nThemes} themes · ${fmtInt(pf.totalWatchlist ?? 0)} on watch</span></div>
        </div>
      </div>
      <details class="ps-why">
        <summary>Spread not measurable yet — no Buy verdicts, so no buy leg (<b>UNDEFINED</b>, never 0.0) · diagnostics not ready · methodology</summary>
        <div class="ps-why-body">
          <ul class="kv-list" style="margin-bottom:9px;">${(pf.undefinedMeasures || []).map(([m, r]) =>
            `<li><b>${escapeHtml(m)}</b> — <span class="muted">UNDEFINED: ${escapeHtml(r)}</span></li>`).join("")}
          </ul>
          <div class="foot" style="margin-bottom:5px;">Beta-confounded diagnostics — pooled across themes, 0 days forward → pending:</div>
          ${(pf.diagnostics || []).map((d) => `
            <div style="padding:3px 0;"><b>${escapeHtml(d.name)}</b>
              <span class="pill unresolved">${escapeHtml(d.status || "PENDING")}</span>
              <span class="foot"> ${escapeHtml(d.note || "")}</span></div>`).join("")}
          <div class="cite">${escapeHtml(pf.honestyLabel || "")}</div>
        </div>
      </details>
    </div>`;

  const drill = (slug, tier, n) => n > 0
    ? `<a class="tier-count" href="#/themes/${escapeHtml(slug)}/${tier}">${fmtInt(n)}</a>`
    : `<span class="tier-count zero">0</span>`;
  const row = (d) => {
    const ft = d.frozenTiers || {}, t = d.tierShape || {};
    return `
      <tr>
        <td><a href="#/themes/${escapeHtml(d.slug)}" style="font-weight:650;">${escapeHtml(d.label)}</a>
          <div class="foot">snapshot ${fmtDate(d.freezeDate)} · ${fmtInt(d.surfacedCount)} surfaced of ${t.universe == null ? DASH : fmtInt(t.universe)} scanned</div></td>
        <td class="num v-num">${fmtInt(d.ratifiedCount)}</td>
        <td class="num v-num">${fmtInt(d.watchlistCount)}</td>
        <td class="num scan-num scan-first">${drill(d.slug, "firm", ft.firm || 0)}</td>
        <td class="num scan-num">${drill(d.slug, "partial", ft.partial || 0)}</td>
        <td class="num scan-num">${drill(d.slug, "early", ft.early || 0)}</td>
        <td class="num scan-num muted">${t.none == null ? DASH : fmtInt(t.none)}</td>
      </tr>`;
  };

  const table = `
    <table class="data vs-table"><thead>
      <tr>
        <th rowspan="2">Theme</th>
        <th class="grp grp-verdict" colspan="2">Verdict · analyst</th>
        <th class="grp grp-scan scan-first" colspan="4">Scan · machine read</th>
      </tr>
      <tr>
        <th class="num">Buys</th><th class="num">Watch</th>
        <th class="num scan-first">Firm</th><th class="num">Partial</th><th class="num">Early</th><th class="num">None</th>
      </tr>
    </thead><tbody>${idx.drivers.map(row).join("")}</tbody></table>
    <div class="foot" style="margin-top:8px;">Tap a Scan tier count for that tier's names · tap a theme to drill in.</div>`;

  root.innerHTML = frame(item, { bodyHtml: strip + VS_KEY + table });
}
