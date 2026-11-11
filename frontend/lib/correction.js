// A DECISION'S ENTRY, AS THE LEDGER READS IT (RF-D7, operator ruling 2026-11-09).
//
// A decision sealed on a stale close is corrected by an APPENDED row; `getLedger` reads the
// decision at it (`entry.correction` carries the sealed entry). Every surface that prints a
// decision's entry prints it through here, so the decision log and the dossier say one thing:
//   - MAIN BODY: the entry the decision is read at, labelled corrected when it is;
//   - ON-DEMAND (`<details>`, collapsed on screen, force-opened in print): the sealed entry, the
//     row that corrects it and its reason — provenance, never a decision value.
import { fmtPrice, fmtDate, escapeHtml } from "./format.js";

export function entryCell(e) {
  const label = e.correction ? "Entry (corrected)" : "Frozen entry";
  return `<div><span class="muted">${label}</span> <span class="mono" style="font-weight:600;">${fmtPrice(e.entryPrice)}</span> <span class="muted">@ ${fmtDate(e.entryPriceAsOf)}</span></div>`;
}

export function correctionTier(e) {
  const fx = e.correction;
  if (!fx) return "";
  return `<details class="ds-correction" style="margin-top:8px; font-size:12.5px;">
      <summary class="muted">Entry correction — the sealed entry, and why it is not read</summary>
      <div style="margin-top:6px; color:var(--ink-2);">
        Sealed at <span class="mono">${fmtPrice(fx.sealedPrice)}</span> on ${fmtDate(fx.sealedAsOf)},
        a close older than the decision. Read at <span class="mono">${fmtPrice(e.entryPrice)}</span>
        on ${fmtDate(e.entryPriceAsOf)}, the last close completed when the decision was made, by the
        appended row <span class="mono">${escapeHtml(fx.correctionId)}</span>; the horizon runs from
        that date. The sealed row is unchanged.
        ${fx.reason ? `<div class="muted" style="margin-top:4px;">Reason — ${escapeHtml(fx.reason)}</div>` : ""}
      </div>
    </details>`;
}
