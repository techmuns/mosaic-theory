// THEMES LANDING (#/themes) — the GLANCE. Pooled forward honesty on top (cross-theme facts live
// here), then ONE ROW PER THEME with the verdict/scan split — the theme name is the SINGLE drill
// affordance (tier counts are plain numbers; tier tables are reached via the theme page, one path).
// Below the table: the cross-theme WATCHLIST as a collapsed, trigger-led section (compact rows
// only — full fidelity lives on the theme page; drivers lazy-load on first expand so the glance
// stays cheap at 10+ themes), and the RADAR INTAKE strip (pre-freeze funnel state + the way in).
import { getThemesIndex, getThemeDriver, getRadarCandidates, getRadarInbox } from "../../lib/snapshots.js";
import { fmtInt, fmtDate, DASH, escapeHtml, gradeBucket, tierPill } from "../../lib/format.js";

// The verdict/scan key — the grade-vs-verdict distinction. VERDICT is the ANALYST's call; SCAN is the
// MACHINE's read of firmness.
// THE BAR SENTENCE WAS STALE FROM THE DAY THE LADDER SHIPPED (review, #489): it asserted a single
// ≥2:1 line while #487 made ≥1.75:1 the ELIGIBILITY line and ≥2:1 the PREFERRED rung, so a name
// that is eligible-but-not-preferred read as failing here and passing on its own card. Both lines
// are now named, and neither is stated as the thing a Buy "cleared" — the analyst's verdict is.
const VS_KEY = `<div class="vs-key">
  <div class="vs-key-row"><span class="vs-key-tag verdict">Verdict · analyst</span>
    <span><b>Buys</b> are the analyst's call; the machine's reward-to-risk read is tiered —
    eligible ≥1.75:1, preferred ≥2:1 · <b>Watch</b> = real exposure that
    failed only on price / materiality, carries a re-underwrite trigger</span></div>
  <div class="vs-key-row"><span class="vs-key-tag scan">Scan · machine read</span>
    <span><b>firm</b> = contracted / quantified · <b>partial</b> = real activity, not contracted ·
    <b>early</b> = stated intent · <b>none</b> = no exposure disclosed</span></div>
</div>`;

// One compact watchlist row: ticker · theme · firmness · the one-line trigger. A recorded verdict
// SUPERSEDES the freeze trigger (pill + first re-underwrite trigger); the theme page has the rest.
function wlLine(n, meta) {
  const c = n.scenarioCard;
  const v = (c && c.verdict) || {};
  const trig = c && (v.reunderwriteTriggers || []).length
    // TIER FIRST, legacy boolean second — the same precedence uw-card.js uses, so one name cannot
    // read red here and green on its card. A pre-ladder record has no tier and keeps its PASS/FAIL.
    ? `${v.status ? `<span class="pill conditional">${escapeHtml(v.status)}</span> ` : ""}${c.asymmetryTier
        ? `${tierPill(c.asymmetryTier)} `
        : c.passFail
          ? `<span class="pill ${c.passFail === "PASS" ? "buy" : "avoid"}">${escapeHtml(c.passFail)}</span> ` : ""}` +
      escapeHtml(v.reunderwriteTriggers[0])
    : escapeHtml(oneLine(n.trigger));
  return `<div class="wl-line">
    <b class="mono">${escapeHtml(n.ticker)}</b>
    <a class="muted" href="#/themes/${escapeHtml(meta.slug)}" style="font-size:12px;">${escapeHtml(meta.label)}</a>
    <span class="gt ${gradeBucket(n.basis)}">${escapeHtml(gradeBucket(n.basis))}</span>
    <span class="wl-line-t">${trig}</span>
  </div>`;
}

function oneLine(s) {
  s = String(s || DASH).trim();
  return s.length <= 140 ? s : s.slice(0, 140).replace(/\s+\S*$/, "") + "…";
}

export async function render(root, { item, frame }) {
  root.innerHTML = frame(item, { bodyHtml: `<div class="notice">Loading themes…</div>` });
  const [idx, cands, inbox] = await Promise.all([
    getThemesIndex(),
    getRadarCandidates().then((r) => r.candidates || []).catch(() => []),
    getRadarInbox().catch(() => null),
  ]);
  if (!idx.drivers.length) {
    root.innerHTML = frame(item, { bodyHtml: `
      <div class="notice">No theme artifacts committed to this deploy yet. Produce them with
      <code>python3 frontend/build.py --themes-src &lt;snapshot dir(s)&gt;</code>.</div>` });
    return;
  }

  const pf = idx.pooledForward || {};
  const cd = idx.crossDriver || {};

  // POOLED forward — ONE compact honest strip; verbose enumeration behind "methodology".
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

  // Tier counts are PLAIN NUMBERS here — the tier tables are reached via the theme page (one
  // path), so the theme name is the single drill affordance per row.
  const row = (d) => {
    const ft = d.frozenTiers || {}, t = d.tierShape || {};
    return `
      <tr>
        <td><a href="#/themes/${escapeHtml(d.slug)}" style="font-weight:650;">${escapeHtml(d.label)}</a>
          <div class="foot">snapshot ${fmtDate(d.freezeDate)} · ${fmtInt(d.surfacedCount)} surfaced of ${t.universe == null ? DASH : fmtInt(t.universe)} scanned</div></td>
        <td class="num v-num">${fmtInt(d.ratifiedCount)}</td>
        <td class="num v-num">${fmtInt(d.watchlistCount)}</td>
        <td class="num scan-num scan-first">${fmtInt(ft.firm || 0)}</td>
        <td class="num scan-num">${fmtInt(ft.partial || 0)}</td>
        <td class="num scan-num">${fmtInt(ft.early || 0)}</td>
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
    <div class="foot" style="margin-top:8px;">Tap a theme to drill in — brief, names, flags, and the first-analysis cards.</div>`;

  // Cross-theme watchlist — COLLAPSED; the per-theme drivers fetch on first expand (lazy).
  const totalWatch = fmtInt(pf.totalWatchlist ?? idx.drivers.reduce((s, d) => s + (d.watchlistCount || 0), 0));
  const wlSection = `
    <details class="wl-section" id="landing-watchlist" style="margin-top:16px;">
      <summary><b>Watchlist</b> <span class="muted">· ${totalWatch} across themes · re-underwrite on trigger</span></summary>
      <div class="wl-section-body" id="landing-watchlist-body">
        <div class="notice">Loading watchlist…</div>
      </div>
    </details>`;

  // Radar intake strip — the pre-freeze funnel state + the single way into the intake stage.
  const counts = { live: 0, watch: 0, parked: 0 };
  for (const c of cands) if (c.status in counts) counts[c.status] += 1;
  const inboxN = inbox && Array.isArray(inbox.inbox) ? inbox.inbox.length : 0;
  const intake = `
    <div class="card intake-strip" style="margin-top:16px;">
      <h3 style="margin:0;">Radar intake</h3>
      <span class="mono intake-counts">${fmtInt(counts.live)} live · ${fmtInt(counts.watch)} watch · ${fmtInt(counts.parked)} parked</span>
      <span class="muted">inbox ${fmtInt(inboxN)}</span>
      <a href="#/themes/radar" style="margin-left:auto;">Radar →</a>
    </div>`;

  root.innerHTML = frame(item, { bodyHtml: strip + VS_KEY + table + wlSection + intake });

  // Lazy watchlist: fetch every theme's driver JSON only when the section first opens.
  const det = root.querySelector("#landing-watchlist");
  let loaded = false;
  det?.addEventListener("toggle", async () => {
    if (!det.open || loaded) return;
    loaded = true;
    const body = root.querySelector("#landing-watchlist-body");
    try {
      const drivers = await Promise.all(idx.drivers.map((m) => getThemeDriver(m.slug)));
      const rows = idx.drivers.flatMap((meta, i) =>
        ((drivers[i] && drivers[i].watchlist) || []).map((n) => wlLine(n, meta)));
      body.innerHTML = (rows.join("") || `<div class="foot">none</div>`) +
        `<div class="foot" style="margin-top:7px;">Compact rows — open a theme for triggers in full and the underwrite cards.</div>`;
    } catch (e) {
      body.innerHTML = `<div class="notice">Could not load the watchlist: ${escapeHtml(e.message)}</div>`;
    }
  });
}
