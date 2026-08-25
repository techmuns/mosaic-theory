// OVERVIEW — fund status at a glance. Read-only render of committed snapshots.
import {
  getSpreadStatus, getUniverseHealth, getLedger,
  getDossierIndex, getSnapshotMeta, getThemesIndex,
} from "../../lib/snapshots.js";
import { fmtInt, fmtDate, DASH, escapeHtml, queueAgeChip, runHealth } from "../../lib/format.js";

export async function render(root) {
  root.innerHTML = `<div class="notice">Loading fund status…</div>`;

  const [spread, health, ledger, dossiers, meta, themes] = await Promise.all([
    getSpreadStatus(), getUniverseHealth(), getLedger(),
    getDossierIndex(), getSnapshotMeta(), getThemesIndex(),
  ]);

  // THE QUEUE'S AGE AND THE LAST RUN'S OUTCOME, on the FIRST screen. The age chip lived only on
  // the ranker, so learning the queue was stale required opening the queue — the screen you are
  // least likely to open during an outage, because it looks unchanged. Both render only when they
  // have something to say: a fresh queue and a clean run add no furniture here.
  const rh = runHealth(health.run);
  const ageChip = queueAgeChip(health.screen.asOf);
  const runChip = health.run && health.run.conclusion !== "success"
    ? `<span class="chip ${rh.tone}" title="${escapeHtml(rh.detail)}">⚠ last weekly run: ${
        escapeHtml(rh.label)}${health.run.attemptedAt
          ? ` · ${escapeHtml(String(health.run.attemptedAt).slice(0, 10))}` : ""}</span>`
    : "";
  const statusStrip = (ageChip || runChip)
    ? `<div class="chips" style="grid-column: 1 / -1; margin-bottom:2px;">${ageChip}${runChip}</div>`
    : "";

  const gateCard = `
    <div class="card gate-card" style="grid-column: 1 / -1;">
      <h3 class="g-label">Validation gate · BUY−AVOID spread <span class="muted" style="font-weight:400; font-size:11.5px;">(screen-origin only)</span></h3>
      <div class="g-spread${spread.spread === null ? " empty" : ""}">${spread.spread === null ? DASH : spread.spread}</div>
      <div class="g-status">
        <b>${spread.resolvedCount} resolved</b> · gate not met ·
        needs ≥2 quarters of resolved verdicts, both legs, positive and large enough to be real
        <span class="muted">(${spread.loggedCount} logged so far: ${spread.buyLegs} buy · ${spread.avoidLegs} avoid, all unresolved)</span>
      </div>
      <div class="g-def">The spread is the fund's only proof: ${escapeHtml(spread.definition)}. It is empty by design until verdicts resolve forward over calendar time.</div>
    </div>`;

  const metric = (label, value, unit, foot) => `
    <div class="card metric">
      <h3>${label}</h3>
      <div class="value">${value}${unit ? ` <span class="unit">${unit}</span>` : ""}</div>
      <div class="foot">${foot}</div>
    </div>`;

  const metrics = `
    ${metric("Universe → queue",
      `${fmtInt(health.universe.count)} <span class="unit">→</span> ${fmtInt(health.queue.total)}`,
      "",
      `screened ${fmtDate(health.screen.asOf)} · ${fmtInt(health.queue.demoted)} structurally sunk`)}
    ${metric("Verdicts",
      `${fmtInt(ledger.counts.logged)}`,
      "logged",
      `${fmtInt(ledger.counts.resolved)} resolved · ${fmtInt(ledger.counts.buy)} buy / ${fmtInt(ledger.counts.avoid)} avoid${
        ledger.counts.loggedAllBooks > ledger.counts.logged
          ? ` · ${fmtInt(ledger.counts.loggedAllBooks - ledger.counts.logged)} in other books`
          : ""}`)}
    ${metric("Dossiers",
      `${fmtInt(dossiers.length)}`,
      "assembled",
      dossiers.length ? escapeHtml(dossiers.join(" · ")) : "none committed to this deploy yet")}
    ${metric("Positions", `0`, "", `capital locked until the gate clears`)}`;

  const chips = `
    <div class="chips">
      <span class="chip live"><span class="dot live"></span> Research loop · live</span>
      <span class="chip gate">Validation gate · accumulating (0 resolved)</span>
      <span class="chip locked">🔒 Capital · locked</span>
    </div>`;

  const cue = `
    <div class="cue">
      <div class="arrow">→</div>
      <div class="t"><b>Next:</b> work finalists from the ranked queue into dossiers, then log BUY/AVOID verdicts (the CLI freezes the entry price). The spread needs <b>both legs</b> and calendar time — especially BUY legs — before it can show anything.</div>
    </div>`;

  // Theme edge — a LIGHT summary; deep status lives in #/themes. Skipped if no theme artifacts.
  const td = themes.crossDriver;
  const themeCard = themes.drivers.length ? `
    <div class="card theme-edge">
      <div>
        <h3>Theme edge <span class="pill unresolved">unvalidated · research</span></h3>
        <div class="theme-edge-stat">
          <b>${fmtInt(td?.driversFrozen ?? themes.drivers.length)} drivers</b> in snapshot ·
          <b>${fmtInt(td?.totalRatified ?? 0)} buys</b> ·
          <b>${fmtInt(td?.totalWatchlist ?? 0)} watchlist</b> names to re-underwrite
        </div>
      </div>
      <a href="#/themes" class="theme-edge-link">View theme edge →</a>
    </div>` : "";

  root.innerHTML = `
    <div class="breadcrumb">Overview</div>
    <div class="header-block">
      <h1 class="page-h">Nostra Vinci · fund status</h1>
      <div class="subtitle">An AI-native, long-biased, US-first concentrated equity fund. The edge is deep human judgment on a few finalists, fed by an AI funnel that achieves breadth a human can't.</div>
      <div class="subtitle muted">Read-only dashboard — a static mirror of the last pushed snapshots. It never trades, writes, or logs; verdicts are logged via the CLI only.</div>
    </div>

    <div class="grid cols-4" style="margin-bottom:16px;">
      ${statusStrip}
      ${gateCard}
    </div>
    <div class="grid cols-4" style="margin-bottom:18px;">
      ${metrics}
    </div>
    ${themeCard}
    <div style="margin-bottom:18px;">${chips}</div>
    ${cue}

    <div class="provenance">
      <span>Snapshot source: <span class="mono">${meta.sourceCommit ? escapeHtml(meta.sourceCommit) : DASH}</span></span>
      <span>Mirror built: ${meta.generatedAt ? escapeHtml(meta.generatedAt) : DASH}</span>
      <span>Lags local state until the next <span class="mono">git push</span> — point-in-time by design.</span>
    </div>`;
}
