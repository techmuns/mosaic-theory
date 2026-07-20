// THE citation system — one implementation, importable by ANY surface.
//
// Lifted out of views/shared/dossier.js, where it lived as ~25 private lines. That privacy was the
// defect: uw-card.js could not reach it, so the underwrite card hardcoded the inline form for every
// cite — including its MAIN-BODY ones, which the dossier's own convention says are endnotes. A good
// implementation locked inside one module forces the next surface to ship a lesser one.
//
// TWO SANCTIONED MODES, and the choice is not stylistic:
//   withEndnotes()     MAIN BODY / decision tier — numbered [n] markers + a Sources list at the end.
//   auditCitesInline() ON-DEMAND <details> audit blocks — inline, because those blocks are
//                      print-EXCLUDED and an endnote there would leave an orphan [n] in the Sources
//                      list of a printed "Full" dossier, pointing at a marker the reader can't see.
//
// A HOST THAT EMITS citeMark PLACEHOLDERS MUST RUN ONE OF THE TWO PASSES over the result; an
// unconsumed placeholder renders as a literal "[?]". Components that may be embedded in a host with
// no pass should default to the inline form (see uwCard's `cites` option).

import { escapeHtml } from "./format.js";

// (A2) PER-TIER endnotes — each cite becomes a numbered [n] marker (a superscript with a hover
// tooltip) resolving to that tier's own Sources list at its end. Per-tier, NOT one global list: the
// tabs + PDF-scope dropdown must each be self-contained (a [n] on the Brief tab can't resolve into a
// hidden Analysis tab; a "Brief" PDF lists only the Brief's sources). citeMark emits a placeholder;
// withEndnotes numbers them in READING order (two-pass) so the [n] are monotonic down the page even
// though cards may pre-compute their cites out of DOM order.
export function citeMark(sourceRef) {
  if (!sourceRef) return "";  // a PRESENT fact always has a ref; guard defensively (no marker if absent)
  return `<sup class="cite-n" data-ref="${escapeHtml(sourceRef)}">[?]</sup>`;  // numbered by withEndnotes
}
// (review #9) ONE definition of the citeMark placeholder shape, parsed by BOTH withEndnotes and
// auditCitesInline — so a change to citeMark's markup can't leave one consumer's ad-hoc regex stale
// ("two divergent parsers of one string" is the documented bug class). A FRESH /g regex per call (no
// shared lastIndex across .replace). Capture group 1 = the (already HTML-escaped) source_ref.
export const citePlaceholders = () => /<sup class="cite-n" data-ref="([^"]*)">\[\?\]<\/sup>/g;

export function withEndnotes(prefix, fn) {
  // (L2) tier-prefix the markers ([B4]/[A4]/[X4]) so they stay UNAMBIGUOUS when all tiers print
  // together in a "Full dossier" PDF, while each tab / print-scope keeps its own self-contained list.
  const order = [];
  const body = fn().replace(citePlaceholders(), (_m, ref) => {
    let i = order.indexOf(ref);  // ref is already HTML-escaped (from citeMark) — dedup by exact string
    if (i < 0) { order.push(ref); i = order.length - 1; }
    return `<sup class="cite-n" title="${ref}">[${prefix}${i + 1}]</sup>`;
  });
  if (!order.length) return body;
  const items = order.map((r, i) =>
    `<li><span class="src-n">[${prefix}${i + 1}]</span> <span class="mono">${r}</span></li>`).join("");
  return body + `<div class="card ds-section ds-sources"><div class="ds-title">Sources</div><ol>${items}</ol></div>`;
}

// (L3) An on-demand audit <details> is print-EXCLUDED; render ITS provenance cites INLINE (source_ref
// shown) rather than as endnotes, so they leave no orphan [n] Sources entry with no visible marker in
// a printed "Full" dossier. Converts only this block's cite placeholders; the main body still endnotes.
export function auditCitesInline(html) {
  return html.replace(citePlaceholders(), (_m, ref) => ` <span class="cite">${ref}</span>`);
}
