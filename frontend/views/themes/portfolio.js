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
// The verdict/scan key is GONE with the columns it described (2026-09-01): firm/partial/early/none
// left the table when rows regrouped by stage, and a legend for absent columns misdirects. What
// survives of it — that Buy/Avoid are the ANALYST's call — is one line under the table, where the
// reader is when the question occurs to them.

// STAGE — where a driver sits in the pipeline, and the ONE thing standing between it and the next
// stage. The index is a work queue before it is a scoreboard: a reader's first question is "what
// needs me", and before this the page could not answer it. `measuring` is the only stage with legs,
// which is why the three archived July drivers read 0 Buys — they have no ratification ledger, not
// a failed thesis, and the two states used to look identical here.
const STAGE_CHIP = { measuring: ["live", "Measuring"], scanned: ["", "Scanned"],
                     declared: ["", "Declared"], archived: ["locked", "Archived"] };

const STAGES = [
  ["measuring", "Clock running",
    (d) => `First test ${d.firstTest ? fmtDate(d.firstTest) : "— date not declared"}`],
  ["scanned", "Scanned, not yet reviewed",
    (d) => {
      // ABSENCE vs ZERO. A scanned-but-unfrozen driver has NO frozenTiers at all, which is when
      // frozenCount is the right stand-in; a driver that HAS tiers and sums to 0 must report 0.
      // `a + b || fallback` conflated the two, and a missing key made the sum NaN — also falsy —
      // so both silently reported the fallback instead.
      const ft = d.frozenTiers;
      const n = ft ? (ft.firm ?? 0) + (ft.partial ?? 0) : (d.frozenCount ?? 0);
      return `Send worksheet — ${fmtInt(n)} names`;
    }],
  ["declared", "Declared, not yet scanned", () => "Run the scan"],
  ["archived", "Archived — scanned earlier, no verdicts on file",
    () => "Declare a thesis card first"],
];

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

  // POOLED forward — ONE compact honest strip; verbose enumeration behind "methodology".
  const nThemes = idx.drivers.length;
  const measuring = idx.drivers.filter((d) => d.stage === "measuring");
  const nMeasuring = measuring.length;
  const nBuy = measuring.reduce((n, d) => n + (d.ratifiedCount || 0), 0);
  const nAvoid = measuring.reduce((n, d) => n + (d.passedCount || 0), 0);
  // RATIFIED IS NOT PRICED. Ratifying confirms the EXPOSURE is real; the investment gate is the
  // underwrite (reward-to-risk vs a 2:1 bar, IRR vs a 15% floor, at spot) and it is a separate
  // step. Showing the count keeps a 168-name buy leg from reading as 168 investment decisions.
  const nUW = measuring.reduce((n, d) => n + (d.underwrittenCount || 0), 0);
  // the soonest declared first-confirming date across the running clocks — the next moment this
  // page can say anything it cannot say today
  const nextTest = measuring.map((d) => d.firstTest).filter(Boolean).sort()[0] || null;
  const strip = `
    <div class="pooled-strip">
      <div class="th-band">
        <div class="th-stat"><div class="th-lab">Buy−Avoid spread</div>
          <div class="th-val th-undef">UNDEFINED</div></div>
        <div class="th-stat"><div class="th-lab">Clocks running</div>
          <div class="th-val">${fmtInt(nMeasuring)} <span class="th-of">of ${nThemes}</span></div></div>
        <div class="th-stat"><div class="th-lab">Names under test</div>
          <div class="th-val">${fmtInt(nBuy)} <span class="th-of">buy</span> · ${fmtInt(nAvoid)} <span class="th-of">avoid</span></div></div>
        <div class="th-stat"><div class="th-lab">Priced</div>
          <div class="th-val ${nUW ? "" : "th-undef"}">${fmtInt(nUW)} <span class="th-of">of ${fmtInt(nBuy)} ratified</span></div></div>
        <div class="th-stat"><div class="th-lab">Next read-out</div>
          <div class="th-val">${nextTest ? fmtDate(nextTest) : DASH}</div></div>
      </div>
      <details class="ps-why">
        <summary>Both legs are sealed; the spread stays <b>UNDEFINED</b> (never 0.0) until verdicts resolve forward · methodology</summary>
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
  const row = (d, needs) => {
    const t = d.tierShape || {};
    const legs = d.stage === "measuring";
    const [chipTone, chipText] = STAGE_CHIP[d.stage] || ["", "—"];
    return `
      <tr>
        <td><a href="#/themes/${escapeHtml(d.slug)}" style="font-weight:650;">${escapeHtml(d.label)}</a>
          <div class="foot">${d.freezeDate ? `froze ${fmtDate(d.freezeDate)}` : "not frozen"}</div></td>
        <td><span class="chip ${chipTone}">${escapeHtml(chipText)}</span></td>
        <td class="num v-num">${legs ? fmtInt(d.ratifiedCount) : `<span class="muted">${DASH}</span>`}</td>
        <td class="num v-num">${legs && d.passedCount != null ? fmtInt(d.passedCount) : `<span class="muted">${DASH}</span>`}</td>
        <td class="num scan-num">${t.universe == null ? `<span class="muted">${DASH}</span>` : fmtInt(t.universe)}</td>
        <td class="th-needs">${escapeHtml(needs(d))}</td>
      </tr>`;
  };

  const body = STAGES.map(([key, title, needs]) => {
    const rows = idx.drivers.filter((d) => (d.stage || "archived") === key);
    if (!rows.length) return "";
    return `<tr class="th-grp"><td colspan="6">${escapeHtml(title)} · ${rows.length}</td></tr>`
      + rows.map((d) => row(d, needs)).join("");
  }).join("");

  const table = `
    <table class="data th-table"><thead>
      <tr>
        <th>Driver</th><th>Stage</th>
        <th class="num">Buy</th><th class="num">Avoid</th><th class="num">Screened</th>
        <th>Needs next</th>
      </tr>
    </thead><tbody>${body}</tbody></table>
    <div class="foot" style="margin-top:8px;">Buy and Avoid are the analyst's verdicts on
      <b>exposure</b>, never the machine's — a ratified name has not yet been priced. The
      underwrite (reward-to-risk, IRR at spot) is the separate gate the Priced count tracks.</div>`;

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

  root.innerHTML = frame(item, { bodyHtml: strip + table + wlSection + intake });

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
