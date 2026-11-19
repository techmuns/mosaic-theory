"""D13 on the live corpus: is `G3_EPS_TOO_OLD`'s claim — "a more recent annual figure exists and is
negative" — true for each committed page and candidate record that prints it?

POPULATION (main at the worktree's HEAD): every `data/dossiers/*/dossier.json` whose
`mechanical.valuation.pe.note` carries the text, and every `data/snapshots/candidate_records.jsonl`
record whose `data_record.fundamentals.pe.note` does. Each is judged at ITS OWN date: a page's
`reference_date`, a record's `data_record.as_of`. The companyfacts are cut there (`facts_as_of`, on
`filed`), as the screen cuts them (`screens.assemble.enrich_with_fundamentals`; its cut is the
newest price bar on or before that date — taken here as the date itself, an approximation stated
in the output).

THE READER'S VIEW, REPLAYED: `served_series(facts_cut, "eps_diluted", currency=REPORTING, as_of=d)`,
its annual points on `d` — the exact list `pe_current_and_percentile` receives. The note is
REPRODUCED when `annual_eps_point_as_of` (470-day bound) returns None while the unbounded read
returns a positive point P. Then "newer" = an ANNUAL point (`ConceptPoint.is_annual`, 350–380 days)
filed on or before `d` whose period ends after P's.

CLASSES:
- TRUE  — a newer annual figure exists IN THE READER'S SERVED SERIES and every one is negative;
- FALSE — none exists in the served series AND none under any other EPS tag searched (the tag
  stopped), or the only newer figures are under another tag and are POSITIVE (the tag changed; the
  business still earns) — the note's claim is false either way;
- OTHER — anything else, stated: the replay does not reproduce the note; a newer figure exists only
  under another tag and is negative (true of the business, not of the series the reader served); a
  newer zero; companyfacts unreadable.

TAGS SEARCHED beyond the served series: every us-gaap / ifrs-full EPS tag whose name matches
EarningsPerShare*, IncomeLossFromContinuingOperationsPer*Share*,
*PerOutstandingLimitedPartnershipUnit*,
*PerLimitedPartnershipUnit*, *EarningsLossPerShare (IFRS) — diluted, basic, basic-and-diluted and
per-unit alike, in the filer's reporting currency (`points_for_tag(..., currency=REPORTING)`).
Pro-forma (BusinessAcquisitionProForma*) and dividend/distribution tags are excluded by name."""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from typing import Any

from probe_common import OUT, WT, edgar

TXT = "older than one filing cycle"
EPS_TAG = re.compile(
    r"(EarningsPerShare|EarningsLossPerShare|IncomeLossFromContinuingOperationsPer.*Share"
    r"|PerOutstandingLimitedPartnershipUnit|PerLimitedPartnershipUnit)"
)
EXCLUDE = re.compile(r"(ProForma|Dividend|Distribution|Antidilutive|Increase|Adjustment|Effect)")


def population() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for p in sorted((WT / "data" / "dossiers").glob("*/dossier.json")):
        d = json.loads(p.read_text())
        note = (((d.get("mechanical") or {}).get("valuation") or {}).get("pe") or {}).get(
            "note"
        ) or ""
        if TXT in note:
            items.append(
                {
                    "kind": "page",
                    "ticker": d["ticker"],
                    "cik": d["cik"],
                    "date": d["reference_date"],
                    "where": f"data/dossiers/{d['ticker']}/dossier.json",
                }
            )
    for line in (WT / "data" / "snapshots" / "candidate_records.jsonl").read_text().splitlines():
        if TXT not in line:
            continue
        o = json.loads(line)
        rec = json.loads(o["payload"])["data_record"]
        if TXT in (rec["fundamentals"]["pe"].get("note") or ""):
            items.append(
                {
                    "kind": "record",
                    "ticker": rec["identity"]["ticker"],
                    "cik": rec["identity"]["cik"],
                    "date": rec["as_of"][:10],
                    "where": o["candidate_id"],
                }
            )
    return items


def pt(p: Any) -> dict[str, Any]:
    return {
        "tag": p.tag,
        "end": str(p.period_end),
        "start": str(p.period_start),
        "value": p.value,
        "unit": p.unit,
        "filed": str(p.filed),
        "form": p.form,
        "accession": p.accession,
    }


def raw_annual(cut: dict[str, Any], d: dt.date, after: dt.date) -> list[dict[str, Any]]:
    """Every ANNUAL (350–380 day) per-share fact under an EPS tag in us-gaap AND ifrs-full, filed by
    ``d``, ending after ``after`` — read raw, because `points_for_tag` walks dei/us-gaap only. Units
    are the filer's own (USD/shares, KRW/shares, …); no currency is converted or judged."""
    out = []
    for ns in ("us-gaap", "ifrs-full"):
        for tag, node in ((cut.get("facts") or {}).get(ns) or {}).items():
            if not EPS_TAG.search(tag) or EXCLUDE.search(tag):
                continue
            for unit, rows in (node.get("units") or {}).items():
                if "/shares" not in unit and "shares" not in unit.lower():
                    continue
                for r in rows:
                    if not r.get("start") or not r.get("end") or not r.get("filed"):
                        continue
                    st, en, fi = (dt.date.fromisoformat(r[k]) for k in ("start", "end", "filed"))
                    if 350 <= (en - st).days <= 380 and fi <= d and en > after:
                        out.append(
                            {
                                "tag": f"{ns}:{tag}",
                                "end": str(en),
                                "start": str(st),
                                "value": r["val"],
                                "unit": unit,
                                "filed": str(fi),
                                "form": r.get("form"),
                                "accession": r.get("accn"),
                            }
                        )
    return out


def newest(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    return max(rows, key=lambda r: (r["end"], r["filed"])) if rows else None


def judge(item: dict[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    from vinci.edgar.concepts import REPORTING, facts_as_of, served_series
    from vinci.screens.assemble import annual_eps_point_as_of

    d = dt.date.fromisoformat(item["date"])
    cut = facts_as_of(facts, d)
    hist = served_series(cut, "eps_diluted", currency=REPORTING, as_of=d)
    annual = [p for p in hist.on(d) if p.is_annual]
    bounded = annual_eps_point_as_of(annual, d)
    pos = annual_eps_point_as_of(annual, d, max_age_days=None)
    out: dict[str, Any] = {
        "served_tags": sorted({p.tag for p in annual}),
        "n_annual_served": len(annual),
    }
    if bounded is not None or pos is None:
        out.update(
            cls="OTHER",
            why=(
                "replay does NOT reproduce the note: "
                + (
                    "a positive annual EPS within 470 days exists"
                    if bounded is not None
                    else "no positive annual EPS at all in the served series"
                )
            ),
            latest_positive=pt(pos) if pos else None,
        )
        return out
    out["latest_positive"] = pt(pos)
    out["age_days"] = (d - pos.period_end).days
    newer = sorted((p for p in annual if p.period_end > pos.period_end), key=lambda p: p.period_end)
    if newer:
        neg = [p for p in newer if p.value < 0]
        if len(neg) == len(newer):
            out.update(cls="TRUE", newer=[pt(p) for p in newer], newest=pt(newer[-1]))
            later = [
                r
                for r in raw_annual(cut, d, newer[-1].period_end)
                if r["tag"].split(":", 1)[1] not in out["served_tags"]
            ]
            nl = newest(later)
            if nl is not None:
                out["newest_any_tag"] = nl
                if nl["value"] > 0:
                    out.update(
                        cls="OTHER",
                        why=(
                            f"the served series' newer figure is negative, but a still "
                            f"newer annual EPS under {nl['tag']} ({nl['end']}) is POSITIVE"
                        ),
                    )
        else:
            out.update(
                cls="OTHER",
                why="a newer annual figure in the served series is zero",
                newer=[pt(p) for p in newer],
            )
        return out
    # nothing newer in the served series — search every EPS tag the filer carries
    wide = raw_annual(cut, d, pos.period_end)  # every EPS tag, both namespaces
    if not wide:
        out.update(
            cls="FALSE",
            why=f"the tag stopped: no annual EPS under any EPS tag ends after "
            f"{pos.period_end} (filed by {d})",
        )
        return out
    by_tag: dict[str, Any] = {}
    for r in sorted(wide, key=lambda r: (r["tag"], r["end"], r["filed"])):
        by_tag[r["tag"]] = r  # the newest per tag
    out["newest_any_tag"] = newest(wide)
    signs = {t: v["value"] for t, v in by_tag.items()}
    out["newer_other_tags"] = by_tag
    nv = out["newest_any_tag"]["value"]
    if all(v > 0 for v in signs.values()):
        out.update(
            cls="FALSE",
            why="the tag changed: newer annual EPS exists only under "
            f"{', '.join(sorted(signs))}, and it is POSITIVE",
        )
    elif all(v < 0 for v in signs.values()):
        out.update(
            cls="OTHER",
            why="a newer NEGATIVE annual EPS exists, but only under "
            f"{', '.join(sorted(signs))}, which the reader's served series does not carry",
        )
    else:
        out.update(
            cls="OTHER",
            why=(
                f"newer annual EPS under other tags with mixed signs {signs}; the newest "
                f"({out['newest_any_tag']['tag']}, {out['newest_any_tag']['end']}) is "
                f"{'POSITIVE' if nv > 0 else 'negative'}"
            ),
        )
    return out


def main() -> None:
    import vinci

    print("vinci:", vinci.__file__)
    items = population()
    controls = [
        {
            "kind": "control",
            "ticker": "EPD",
            "cik": "0001061219",
            "date": "2026-10-16",
            "where": "5a: EPD's per-unit tag (expected FALSE, tag changed, positive)",
        }
    ]
    items += controls
    print(
        f"population: {sum(i['kind'] == 'page' for i in items)} page(s), "
        f"{sum(i['kind'] == 'record' for i in items)} record(s)",
        flush=True,
    )
    e = edgar()
    res = []
    for n, it in enumerate(items, 1):
        try:
            facts = e.companyfacts(it["cik"])
            r = judge(it, facts)
        except Exception as exc:  # noqa: BLE001 — an unreadable filer is OTHER, stated
            r = {
                "cls": "OTHER",
                "why": f"companyfacts unreadable: {type(exc).__name__}: {str(exc)[:160]}",
            }
        res.append({**it, **r})
        if n % 10 == 0:
            print(f"  {n}/{len(items)}", flush=True)
    (OUT / "d13audit.json").write_text(json.dumps(res, indent=1, default=str))
    from collections import Counter

    for kind in ("page", "record", "control"):
        c = Counter(r["cls"] for r in res if r["kind"] == kind)
        print(kind, dict(c))


if __name__ == "__main__":
    sys.exit(main())
