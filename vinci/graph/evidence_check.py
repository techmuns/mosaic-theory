"""THE COMMITTED EXPOSURE MAP'S EVIDENCE, CHECKED AGAINST ITS FILINGS — read from the cache, never
from SEC (engineering report P2-14, the graph half; 2026-11-18).

`data/graph_coverage.json` gives every edge the verbatim 10-K phrase the extractor returned
(`evidence`), but no accession: `coverage.graph_coverage` drops `GraphEdge.accession` when it writes
the map (#804's record). Since #804, `extract.extract_graph_edges` refuses at extraction any edge
whose phrase is not a span of the excerpts it was read from. The committed map PREDATES that check.
#937 re-judged it with its extraction held fixed, and nothing has re-read the map against its
filings since #804 measured it once (13 of 339 refused, 2026-10-26).

For every edge this says one of three things, and a miss is always a row, never dropped:

- ``found``: the phrase is a span (`vinci.verbatim`, verbatim or elided) of a held annual report,
  and the accession is named;
- ``not_found``: every candidate report is held, and none carries it;
- ``uncached``: a candidate ORIGINAL report, or the focal's submissions feed, is not held, and no
  held report carries the phrase.

A row's ``note`` says when there was nothing to check: a held feed listing no annual report by the
cut-off (``not_found``, since the cache lacks nothing), or a feed that pages older filings out of
`filings.recent` while fewer than two originals are listed there.

THE CANDIDATES. The map has no accession, so the source is searched for. The candidates are the
focal's two newest ORIGINAL annual reports (10-K, 20-F, 40-F) filed on or before ``filed_by``,
taken from its cached submissions feed (`filings.recent`), plus any /A of them that is held. Two,
not one: EXTR's edges sit in the report before its newest (#804's record), so its true source is
the prior year's report. An /A that is not held is NAMED on the row, but it does not by itself make
the row ``uncached``. Under the operator's /A rule (`filings.latest_10k_excerpts`) the narrative
stays the original's unless the /A re-files it, and an unread /A cannot be judged. That is an
assumption, and the row states it.

THE TEXT. Each document goes through `filings.html_to_text`, the extractor's own conversion, and the
phrase is matched against the WHOLE document, not `relevant_excerpts`: the claim being checked is
that the phrase is in the filing. A ``not_found`` row also says whether the phrase IS a span of a
candidate's excerpts (``in_excerpts``). The excerpt keeps only the sentences that match its
keywords, so two sentences the filing separates can sit side by side in it, and a phrase quoted
across them reads as verbatim to the extractor. It does not read as verbatim in the filing.
The cause is named; it is not forgiven.

NEVER A FETCH. `_HeldOnly` reads a cached copy whatever its age, and refuses to send anything. A
copy it does not hold is an ``uncached`` row.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sys
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import httpx

from vinci.edgar.concepts import ANNUAL_REPORT_FORMS
from vinci.graph.filings import html_to_text, relevant_excerpts
from vinci.netcache import CachedHttp, HttpError
from vinci.verbatim import SourceText

FOUND, NOT_FOUND, UNCACHED = "found", "not_found", "uncached"
OUTCOMES = (FOUND, NOT_FOUND, UNCACHED)
#: How many original annual reports a focal is searched in, newest first (docstring: EXTR).
DEPTH = 2
_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik10}.json"
_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"


class NotHeldError(HttpError):
    """The cache holds no copy of this URL. The checker never sends a request to get one."""


class _HeldOnly(CachedHttp):
    """`CachedHttp` that answers from the cache alone, whatever a copy's age, and never sends."""

    def _fetch_with_retries(self, url: str, *, json_body: dict[str, Any] | None = None) -> str:
        raise NotHeldError(f"not in the cache, and never fetched: {url}")

    def _send(self, url: str, json_body: dict[str, Any] | None) -> httpx.Response:
        raise NotHeldError(f"the cache-only reader sends nothing: {url}")  # belt and braces

    def held_text(self, url: str) -> str | None:
        try:
            return self.get_text(url, ttl_seconds=None)
        except NotHeldError:
            return None


def held_reader(cache_root: Path) -> _HeldOnly:
    """The SEC namespace of the cache under ``cache_root`` (a checkout's `data/cache`)."""
    if not (cache_root / "sec").is_dir():
        raise FileNotFoundError(f"no SEC cache under {cache_root} (expected {cache_root}/sec)")
    return _HeldOnly(cache_dir=cache_root, user_agent="vinci-cache-only-reader",
                     min_interval_sec=0.0, max_retries=0, namespace="sec")


@dataclass(frozen=True)
class Report:
    """One candidate annual report of a focal."""

    form: str
    filing_date: date
    accession: str
    url: str
    held: bool

    @property
    def label(self) -> str:
        return f"{self.form} {self.accession} ({self.filing_date.isoformat()})"


@dataclass(frozen=True)
class EdgeCheck:
    """One edge's answer. ``found_in`` is every held report the phrase is a span of."""

    focal: str
    counterparty: str
    outcome: str
    found_in: tuple[str, ...]
    checked: tuple[str, ...]
    not_held: tuple[str, ...]
    newest: str | None  # the newest original candidate, the report the extractor would read
    in_excerpts: tuple[str, ...] = ()  # a not_found phrase that IS a span of these excerpts
    note: str = ""  # why there is no candidate to check, or what the feed does not list
    feed_held: bool = True  # whether the focal's submissions feed is in the cache (structured)
    #: where a found phrase is, read off the reports themselves: "newest" (the newest original
    #: among them), "older" (an older original, no newest), "amendment" (only /As), "" (not found)
    found_where: str = ""


def candidates(submissions: Mapping[str, Any], cik: str, *, filed_by: date,
               held: Any) -> list[Report]:
    """The focal's two newest original annual reports filed on or before ``filed_by``, and every
    /A of the same form filed after the older of them and on or before ``filed_by`` — newest
    first. ``held(url)`` says whether the cache holds a URL's copy."""
    recent = submissions.get("filings", {}).get("recent", {})
    rows = list(zip(recent.get("form", []), recent.get("filingDate", []),
                    recent.get("accessionNumber", []), recent.get("primaryDocument", []),
                    strict=True))
    annual = sorted(((date.fromisoformat(d), f, a, doc) for f, d, a, doc in rows
                     if f.removesuffix("/A") in ANNUAL_REPORT_FORMS and doc
                     and date.fromisoformat(d) <= filed_by), reverse=True)
    originals = [r for r in annual if not r[1].endswith("/A")][:DEPTH]
    if not originals:
        return []
    floor, forms = originals[-1][0], {r[1] for r in originals}
    keep = [r for r in annual if r in originals
            or (r[1].endswith("/A") and r[1].removesuffix("/A") in forms and r[0] >= floor)]
    out = []
    for d, f, a, doc in keep:
        url = _ARCHIVE.format(cik=int(cik), acc=a.replace("-", ""), doc=doc)
        out.append(Report(form=f, filing_date=d, accession=a, url=url, held=held(url)))
    return out


def check_edges(edges: Sequence[Mapping[str, Any]], http: _HeldOnly, *,
                filed_by: date) -> list[EdgeCheck]:
    """Every edge's answer, in the map's order. Each focal's documents are read once."""
    by_focal: dict[str, tuple[list[Report], dict[str, str]]] = {}
    keys: dict[tuple[str, str], SourceText] = {}  # (accession, "doc" | "excerpts") -> its key
    notes: dict[str, str] = {}
    feeds_held: dict[str, bool] = {}
    out: list[EdgeCheck] = []
    for e in edges:
        cik = str(e["focal_cik"])
        if cik not in by_focal:
            raw = http.held_text(_SUBMISSIONS.format(cik10=f"{int(cik):010d}"))
            feed = None if raw is None else json.loads(raw)
            feeds_held[cik] = feed is not None
            reports = ([] if feed is None else candidates(
                feed, cik, filed_by=filed_by, held=lambda u: http.fetched_at(u) is not None))
            originals = sum(1 for r in reports if not r.form.endswith("/A"))
            notes[cik] = (
                "no submissions feed in the cache" if feed is None
                else "the feed lists no annual report filed by the cut-off" if not reports
                else "the feed pages older filings out of `recent`, unread"
                if originals < DEPTH and feed.get("filings", {}).get("files") else "")
            texts = {}
            for r in reports:
                if r.held:
                    doc = http.held_text(r.url)
                    if doc is not None:
                        texts[r.accession] = html_to_text(doc)
                        keys[(r.accession, "doc")] = SourceText(texts[r.accession])
            by_focal[cik] = (reports, texts)
        reports, texts = by_focal[cik]
        evidence = str(e.get("evidence") or "")
        hits = [r for r in reports
                if r.accession in texts and keys[(r.accession, "doc")].match(evidence).found]
        found = tuple(r.label for r in hits)
        first = next((r for r in reports if not r.form.endswith("/A")), None)
        found_where = ("" if not hits else "newest" if first in hits
                       else "amendment" if all(r.form.endswith("/A") for r in hits) else "older")
        in_excerpts: tuple[str, ...] = ()
        if not found:
            for r in reports:
                if r.accession in texts and (r.accession, "excerpts") not in keys:
                    keys[(r.accession, "excerpts")] = SourceText(
                        relevant_excerpts(texts[r.accession]))
            in_excerpts = tuple(r.label for r in reports if r.accession in texts
                                and keys[(r.accession, "excerpts")].match(evidence).found)
        checked = tuple(r.label for r in reports if r.accession in texts)
        not_held = tuple(r.label for r in reports if r.accession not in texts)
        # UNCACHED is what the cache lacks: the feed, or a candidate original. A feed that lists
        # no annual report by the cut-off is held and has nothing to check: NOT_FOUND, noted.
        originals_missing = not feeds_held[cik] or any(
            r.accession not in texts and not r.form.endswith("/A") for r in reports)
        outcome = FOUND if found else (UNCACHED if originals_missing else NOT_FOUND)
        newest = None if first is None else first.label
        out.append(EdgeCheck(focal=str(e["focal_ticker"]), counterparty=str(e["counterparty_name"]),
                             outcome=outcome, found_in=found, checked=checked, not_held=not_held,
                             newest=newest, in_excerpts=in_excerpts, note=notes[cik],
                             feed_held=feeds_held[cik], found_where=found_where))
    return out


def report_lines(results: Sequence[EdgeCheck], *, map_path: str, map_sha256: str,
                 filed_by: date, cache_root: Path) -> list[str]:
    """The read, in full: the counts with their boundary; for every focal, the accession each of
    its found phrases is in; then every row that is not a plain find in the newest report. Each
    one is printed, and none is cut."""
    n = len(results)
    counts = Counter(r.outcome for r in results)
    focals = sorted({r.focal for r in results})
    lines = [
        f"graph evidence vs filings — {map_path} (sha256 {map_sha256[:12]}): {n} edges from "
        f"{len(focals)} focals; candidates = the {DEPTH} newest original annual reports filed on "
        f"or before {filed_by.isoformat()} (+ their held /As), from the cache at {cache_root} "
        "(never fetched)",
        "  " + " · ".join(f"{o} {counts.get(o, 0)}" for o in OUTCOMES),
        f"  found, by focal ({len(focals)} of {len(focals)}): the accession each found phrase is "
        "in, with how many",
    ]
    for focal in focals:
        rows = [r for r in results if r.focal == focal]
        found = [r for r in rows if r.outcome == FOUND]
        where = Counter(label for r in found for label in r.found_in)
        lines.append(f"    {focal}: {len(found)} of {len(rows)} found"
                     + (" — " + "; ".join(f"{k} {v}" for k, v in sorted(
                         where.items(), key=lambda kv: kv[0].split("(")[-1], reverse=True))
                        if where else ""))
    for label, place in (("found only in a report older than the newest", "older"),
                         ("found only in an amendment of a candidate", "amendment")):
        rows = [r for r in results if r.found_where == place]
        lines.append(f"  {label}: {len(rows)}")
        for r in rows:
            lines.append(f"    {r.focal} → {r.counterparty}: in {'; '.join(r.found_in)}; "
                         f"newest {r.newest}")
    for outcome in (NOT_FOUND, UNCACHED):
        rows = [r for r in results if r.outcome == outcome]
        joined = sum(1 for r in rows if r.in_excerpts)
        lines.append(f"  {outcome}: {len(rows)}"
                     + (f", of which {joined} are a span of a report's excerpts" if rows else ""))
        for r in rows:
            cause = (f" — a span of the excerpts of {'; '.join(r.in_excerpts)}, not of the filing"
                     if r.in_excerpts else "")
            note = f" ({r.note})" if r.note else ""
            lines.append(f"    {r.focal} → {r.counterparty}: checked "
                         f"{'; '.join(r.checked) or 'none'}; not held "
                         f"{'; '.join(r.not_held) or 'none'}{cause}{note}")
    return lines


def rows_json(results: Sequence[EdgeCheck]) -> list[dict[str, Any]]:
    """Every edge's answer, one object each, in the map's order: what `--json` writes."""
    return [dataclasses.asdict(r) for r in results]


def _load_edges(path: Path) -> list[dict[str, Any]]:
    edges = json.loads(path.read_text()).get("edges")
    if not isinstance(edges, list):
        raise ValueError(f"{path}: no `edges` list")
    return edges


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m vinci.graph.evidence_check",
                                 description=__doc__.split("\n\n")[0] if __doc__ else None)
    ap.add_argument("--map", type=Path, default=Path("data/graph_coverage.json"))
    ap.add_argument("--cache-root", type=Path, required=True,
                    help="a checkout's data/cache (read only; nothing is fetched)")
    ap.add_argument("--filed-by", type=date.fromisoformat, required=True,
                    help="the newest filing date a source can have: the map's extraction date")
    ap.add_argument("--json", type=Path, default=None,
                    help="also write every edge's row (its outcome and accessions) to this file")
    a = ap.parse_args(list(argv) if argv is not None else None)
    results = check_edges(_load_edges(a.map), held_reader(a.cache_root), filed_by=a.filed_by)
    sha = hashlib.sha256(a.map.read_bytes()).hexdigest()
    print("\n".join(report_lines(results, map_path=str(a.map), map_sha256=sha,
                                 filed_by=a.filed_by, cache_root=a.cache_root)))
    if a.json is not None:
        a.json.write_text(json.dumps({"map": str(a.map), "map_sha256": sha,
                                      "filed_by": a.filed_by.isoformat(),
                                      "rows": rows_json(results)}, indent=1) + "\n")
        print(f"wrote {len(results)} rows to {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
