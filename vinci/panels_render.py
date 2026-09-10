"""(phase 3) Rendering the universal seven as a panel grid — from COMMITTED data only.

THE TWO NEGATIVE STATES LOOK NOTHING ALIKE HERE, which is the whole point of the grid existing at
this layer: a `not_in_set` panel emits NO TILE AT ALL (not a hidden one, not an empty one — the
string is never produced), while a `refused` tile is bordered, badged, and prints the requirement
that failed together with the upstream refusal verbatim. A reader scanning seven tiles reads
silence as "fine", so silence is reserved for panels that were never asked for.

EVERY TILE CARRIES WHAT WOULD CHANGE THE CALL, in the MAIN BODY rather than an on-demand tier. It
is decision text, not provenance: the design's guard is that a panel which cannot answer it is
decoration, and hiding the answer behind a disclosure triangle would make the guard unreadable at
exactly the moment it matters.

EXHIBITS CITE VIA ENDNOTES, NEVER AN INLINE CAPTION — house rule, recurred on three exhibits and
guarded by a `>Source:`-scan test. Each SVG carries a `citeMark` resolving to the tile's Sources
list; nothing prints `Source: …` beneath a chart.
"""
from __future__ import annotations

import html
from typing import Any

from vinci.panels import PanelDecision, PanelRegistry
from vinci.panels_universal import universal_registry

DASH = "—"


def _esc(x: object) -> str:
    return html.escape(str(x), quote=True)


def _sparkline(series: list[tuple[str, float]], *, current: float, width: int = 180,
               height: int = 34) -> str:
    """A value's own history, as a path. STRUCTURED INPUT ONLY — the series arrives as (date, value)
    pairs from the dossier, never parsed back out of a rendered string."""
    if len(series) < 2:
        return ""
    vals = [v for _, v in series]
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    step = width / (len(vals) - 1)
    pts = " ".join(
        f"{i * step:.1f},{height - (v - lo) / span * height:.1f}" for i, v in enumerate(vals))
    cy = height - (current - lo) / span * height
    return (f'<svg class="spark" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
            f'role="img" aria-label="history of the multiple, {len(vals)} closes">'
            f'<polyline points="{pts}" fill="none" stroke="currentColor" stroke-width="1.2"/>'
            f'<circle cx="{width}" cy="{max(0.0, min(float(height), cy)):.1f}" r="2.6" '
            f'fill="var(--hot)"/></svg>')


def _range_bar(*, low: float, high: float, median: float, current: float) -> str:
    """Where the multiple sits in its own range — the encoding the design's first draft got wrong by
    labelling distances its bar lengths contradicted. Positions here are computed from the same
    numbers that are printed, so the bar cannot disagree with its label."""
    lo, hi = min(low, current), max(high, current)
    span = (hi - lo) or 1.0
    def x(v: float) -> float:
        return (v - lo) / span * 100.0
    return (f'<svg class="rangebar" viewBox="0 0 100 12" preserveAspectRatio="none" role="img" '
            f'aria-label="range position">'
            f'<line x1="0" y1="6" x2="100" y2="6" stroke="currentColor"'
            f' stroke-width="0.7" opacity="0.35"/>'
            f'<line x1="{x(median):.2f}" y1="1.5" x2="{x(median):.2f}" y2="10.5" '
            f'stroke="currentColor" stroke-width="0.9" opacity="0.55"/>'
            f'<circle cx="{x(current):.2f}" cy="6" r="3" fill="var(--hot)"/></svg>')


def _bars(items: list[tuple[str, float]]) -> str:
    """Signed magnitudes on a shared scale — position, benchmark, excess. A shared scale is the
    point: three bars each normalised to themselves would make a 0.4pp excess look like a 29pp
    one."""
    if not items:
        return ""
    scale = max(abs(v) for _, v in items) or 1.0
    out = ['<div class="bars">']
    for label, v in items:
        w = abs(v) / scale * 50.0
        side = "left:50%" if v >= 0 else f"left:{50 - w:.2f}%"
        cls = "pos" if v >= 0 else "neg"
        out.append(
            f'<div class="barrow"><span class="blab">{_esc(label)}</span>'
            f'<span class="btrack"><i class="bfill {cls}" style="{side};width:{w:.2f}%"></i></span>'
            f'<span class="bval">{v * 100:+.2f}pp</span></div>')
    out.append("</div>")
    return "".join(out)


def _timeline(*, last: str | None, newer: list[str], nxt: str | None) -> str:
    """Read → filed-since → expected. The gap IS the panel, so it is drawn as distance."""
    dots = []
    if last:
        dots.append(f'<li class="read"><b>{_esc(last)}</b><span>last read</span></li>')
    for n in newer[:4]:
        head = _esc(n.split(" acc ")[0])
        dots.append(f'<li class="unread"><b>{head}</b><span>filed since</span></li>')
    if nxt:
        dots.append(f'<li class="next"><b>{_esc(nxt)}</b><span>next (est)</span></li>')
    return f'<ol class="timeline">{"".join(dots)}</ol>' if dots else ""


def _tile(dec: PanelDecision, *, title: str, changes: str, caveat: str, body: str,
          sources: list[str]) -> str:
    """One tile. A REFUSAL IS A TILE — bordered, badged, and carrying its reason in full."""
    if dec.state == "refused":
        req = "".join(
            f'<li><code>{_esc(r.kind)}</code> {_esc(r.detail)}<span>{_esc(r.why)}</span></li>'
            for r in dec.missing)
        body = (f'<p class="why">This panel applies to this name and <b>cannot be computed</b>.</p>'
                f'<ul class="missing">{req}</ul>'
                f'<p class="upstream">{_esc(dec.reason)}</p>')
        caveat = ""
        sources = []
    badge = "REFUSED" if dec.state == "refused" else ""
    src = ("".join(f"<li>{_esc(s)}</li>" for s in sources) if sources else "")
    return (
        f'<section class="panel {dec.state}">'
        f'<h3>{_esc(title)}<span class="badge">{badge}</span></h3>'
        f'<div class="body">{body}</div>'
        + (f'<p class="caveat">{_esc(caveat)}</p>' if caveat else "")
        + f'<p class="changes"><span>What would change the call</span>{_esc(changes)}</p>'
        + (f'<details class="prov"><summary>Sources</summary><ol>{src}</ol></details>'
           if src else "")
        + "</section>")


def render_grid(decisions: list[PanelDecision], payloads: dict[str, dict[str, Any]], *,
                ticker: str, as_of: str, registry: PanelRegistry | None = None) -> str:
    """The grid for one name. `not_in_set` panels produce NO STRING — see the module docstring."""
    reg = registry or universal_registry()
    tiles: list[str] = []
    for dec in decisions:
        if dec.state == "not_in_set":
            continue
        spec = reg.get(dec.key)
        assert spec is not None  # decide() already refused an unregistered key, loudly
        p = payloads.get(dec.key) or {}
        tiles.append(_tile(
            dec, title=spec.title, changes=spec.changes_the_call, caveat=spec.caveat,
            body=str(p.get("body") or ""), sources=list(p.get("sources") or [])))
    return (f'<article class="grid" data-ticker="{_esc(ticker)}" data-as-of="{_esc(as_of)}">'
            f'{"".join(tiles)}</article>')


# --------------------------------------------------------------------------------------------
# Payloads — the structured value each READY panel draws. Never a parsed display string.
# --------------------------------------------------------------------------------------------

def payloads_for(*, dossier: dict[str, Any] | None, row: dict[str, Any] | None,
                 freshness: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Build each ready panel's body from the committed artifacts.

    Reads STRUCTURED values throughout — `own_history`'s numeric series, the row's float returns —
    never a re-parse of a rendered line. The house rule exists because a thousands-blind re-parse of
    a `$1,101.80M` display string once read it as `1`.
    """
    m = (dossier or {}).get("mechanical") or {}
    val = m.get("valuation") or {}
    out: dict[str, dict[str, Any]] = {}

    if row:
        ret, bmk = row.get("position_return"), row.get("benchmark_return")
        out["the_call"] = {
            "body": (f'<p class="big">{_esc(row.get("verdict"))}'
                     f'<small>{_esc(row.get("sleeve"))} · entered {_esc(row.get("entry_date"))} at '
                     f'{float(row["entry_price"]):,.2f}</small></p>'
                     f'<p class="sub">now {float(row["current_price"]):,.2f} · '
                     f'{"CLOSED" if row.get("closed") else "held"} · horizon '
                     f'{_esc(row.get("horizon_date"))}</p>'),
            "sources": [f'monitor snapshot row · entry {row.get("entry_date")} '
                        f'· benchmark {row.get("benchmark")} (cap band, assigned at entry)'],
        }
        if ret is not None and bmk is not None:
            out["attribution"] = {
                "body": _bars([("position", float(ret)), ("benchmark "
                               f'{row.get("benchmark")}', float(bmk)),
                               ("excess", float(row.get("excess") or 0.0))]),
                "sources": ["Polygon daily closes, price return both sides (dividends excluded on "
                            "the position AND the benchmark alike)"],
            }

    hist = ((val.get("own_history") or {}).get("value") or [])
    ev = (val.get("ev_ebitda") or {})
    if hist and ev.get("value") is not None:
        h = hist[0]
        series = [(str(d), float(v)) for d, v in (h.get("series") or [])]
        out["multiple_and_price"] = {
            "body": (f'<p class="big">{float(h["current"]):.1f}x'
                     f'<small>{_esc(h.get("metric"))} · {float(h["percentile"]) * 100:.0f}%ile of '
                     f'its own range</small></p>'
                     + _range_bar(low=float(h["low"]), high=float(h["high"]),
                                  median=float(h["median"]), current=float(h["current"]))
                     + f'<p class="sub">range {float(h["low"]):.1f}–{float(h["high"]):.1f}x · '
                       f'median {float(h["median"]):.1f}x · {int(h["n_closes"])} closes</p>'
                     + _sparkline(series, current=float(h["current"]))),
            "sources": [str(ev.get("source_ref") or ""),
                        str((val.get("own_history") or {}).get("source_ref") or "")],
        }

    if freshness:
        out["filing_watch"] = {
            "body": (_timeline(last=freshness.get("last_evidence_date"),
                               newer=list(freshness.get("newer_filings") or []),
                               nxt=freshness.get("next_expected_print"))
                     + ('<p class="flag">UNREAD PRINT — the call is being made on evidence older '
                        'than the latest filing</p>' if freshness.get("unread_print") else "")),
            "sources": [f'last evidence via {freshness.get("last_evidence_source")}',
                        str(freshness.get("next_expected_basis") or "")],
        }

    dil = (m.get("dilution_pipeline") or {})
    if (dil.get("line") or {}).get("value"):
        forms: dict[str, int] = {}
        for f in dil.get("filings") or []:
            forms[str(f.get("form"))] = forms.get(str(f.get("form")), 0) + 1
        top = sorted(forms.items(), key=lambda kv: -kv[1])[:5]
        mx = max((n for _, n in top), default=1)
        rows = "".join(
            f'<div class="barrow"><span class="blab">{_esc(k)}</span>'
            f'<span class="btrack"><i class="bfill pos" style="left:0;width:{n / mx * 100:.0f}%">'
            f'</i></span><span class="bval">{n}</span></div>' for k, n in top)
        out["dilution"] = {
            "body": f'<div class="bars">{rows}</div><p class="sub">'
                    f'{_esc(dil["line"]["value"])}</p>',
            "sources": [str((dil.get("line") or {}).get("source_ref") or "")],
        }

    filing = ((m.get("primary_source") or {}).get("filing") or {})
    if filing.get("source_ref"):
        refs = [str(filing.get("source_ref"))]
        for r in (m.get("primary_source") or {}).get("releases") or []:
            if r.get("source_ref"):
                refs.append(str(r["source_ref"]))
        out["sources"] = {
            "body": f'<p class="big">{len(refs)}<small>primary filings behind the numbers '
                    f'above</small></p>'
                    + "".join(f'<p class="mono">{_esc(r)}</p>' for r in refs[:5]),
            "sources": refs,
        }
    return out
