"""Run the verbatim-span check (`vinci.verbatim`) over the COMMITTED corpus — measure only.

Two corpora carry quotes an LLM returned and nothing checked until `vinci.verbatim` existed:
- covenant terms (`data/dossiers/*/dossier.json` → capital_structure.covenant_term_rows): each
  PRESENT row's quote sits in its note as ``verbatim: “…”`` and its source_ref names the exhibit;
  the maturity event (capital_structure.maturity_event) is a verbatim from an 8-K body;
- graph edges (`data/graph_coverage.json`): each edge's ``evidence`` phrase from a 10-K.

THE GRAPH FILE CARRIES NO ACCESSION (flagged when it was committed, be4268e6), so the 10-K an edge
was read from is RECONSTRUCTED: the focal's latest 10-K filed on or before ``--graph-cut``, reduced
to the same keyword excerpts the extractor sent (`relevant_excerpts`). A miss there is reported with
whether the prior 10-K's excerpts carry it — a vintage question, not a verdict on the quote.

Each quote gets one status: ``verbatim`` / ``elided`` (found), ``not_found``, ``empty``, or
``uncheckable:<why>`` when its source cannot be fetched. ``tier`` says which rule found it:
``driver_rule`` (the operating-driver extractor's whitespace-and-case containment) or
``reduction`` (only after the shared key's quote/dash folding, whitespace removal or cut-stop trim)
or ``elision``. Nothing is written back to any artifact.

    PYTHONPATH=. python scripts/audit_verbatim_corpus.py --out <path.json>

(`PYTHONPATH=.` imports THIS checkout's `vinci`, not the one the venv was installed from.)
"""

from __future__ import annotations

import argparse
import functools
import glob
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from vinci.dossier.covenant_extract import _MAX_EXHIBIT_CHARS, _primary_body
from vinci.dossier.mechanical import _exhibit_names
from vinci.graph.filings import html_to_text, relevant_excerpts
from vinci.netcache import CachedHttp
from vinci.resolver.index import pad_cik
from vinci.verbatim import SourceText, SpanMatch

_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
_REF = re.compile(r"^(.*?) (\d{10}-\d{2}-\d{6}) · (.+)$")
_ACC = re.compile(r"\b(\d{10}-\d{2}-\d{6})\b")
_NOTE_PREFIX, _NOTE_SUFFIX = "verbatim: “", "”"


@functools.lru_cache(maxsize=4)
def _driver_norm(s: str) -> str:
    """`driver_extract`'s whitespace-and-case rule, restated so the tiers say what the new key
    adds. Cached: one exhibit (up to 1.2M chars) is asked about every term read from it."""
    return re.sub(r"\s+", " ", s).strip().lower()


def _driver_rule(quote: str, source: str) -> bool:
    return _driver_norm(quote) in _driver_norm(source)


def _status(quote: str, source: str, src: SourceText) -> tuple[str, str | None]:
    m = src.match(quote)
    if not m.found:
        return m.value, None
    if m is SpanMatch.ELIDED:
        return m.value, "elision"
    return m.value, "driver_rule" if _driver_rule(quote, source) else "reduction"


def _exhibit_text(http: CachedHttp, cik: str, acc: str, doc: str) -> str:
    url = _ARCHIVE.format(cik=int(pad_cik(cik)), acc=acc.replace("-", ""), doc=doc)
    return html_to_text(http.get_text(url, ttl_seconds=None))


def covenant_items(http: CachedHttp, dossier_glob: str) -> list[dict[str, Any]]:
    texts: dict[tuple[str, str, str], str | None] = {}
    out: list[dict[str, Any]] = []
    for path in sorted(glob.glob(dossier_glob)):
        d = json.loads(Path(path).read_text())
        cik, ticker = d["cik"], d["ticker"]
        cs = d["mechanical"]["capital_structure"]
        rows = cs.get("covenant_term_rows") or {}
        for r in (rows.get("value") or []) if rows.get("status") == "present" else []:
            v = r["value"]
            if v["status"] != "present":
                continue
            note = v.get("note") or ""
            quote = (note[len(_NOTE_PREFIX):-len(_NOTE_SUFFIX)]
                     if note.startswith(_NOTE_PREFIX) and note.endswith(_NOTE_SUFFIX) else "")
            item = {"corpus": "covenant_term", "ticker": ticker, "item": r["name"],
                    "source": v["source_ref"], "quote": quote}
            m = _REF.match(v["source_ref"] or "")
            if m is None:
                item["status"], item["tier"] = "uncheckable:unparsed source_ref", None
                out.append(item)
                continue
            key = (cik, m.group(2), m.group(3))
            if key not in texts:
                try:
                    texts[key] = _exhibit_text(http, *key)
                except Exception as exc:  # noqa: BLE001 — a fetch failure is reported, not fatal
                    print(f"fetch failed {key}: {exc}", file=sys.stderr)
                    texts[key] = None
            text = texts[key]
            if text is None:
                item["status"], item["tier"] = "uncheckable:exhibit fetch failed", None
            else:
                item["status"], item["tier"] = _status(quote, text, SourceText(text))
            out.append(item)
        me = cs.get("maturity_event")
        if me and me.get("status") == "present":
            item = {"corpus": "maturity_event", "ticker": ticker, "item": "maturity event",
                    "source": me["source_ref"], "quote": me["value"]}
            am = _ACC.search(me["source_ref"] or "")
            body = _primary_body(_exhibit_names(http, cik, am.group(1))) if am else None
            if am is None or body is None:
                item["status"], item["tier"] = "uncheckable:no 8-K body located", None
            else:
                text = _exhibit_text(http, cik, am.group(1), body)[:_MAX_EXHIBIT_CHARS]
                item["status"], item["tier"] = _status(me["value"], text, SourceText(text))
            out.append(item)
    return out


def _tenks(http: CachedHttp, cik: str) -> list[tuple[str, str, str]]:
    """(filing date, accession, primary doc) of every 10-K in the submissions' recent block. A day's
    TTL, as `EdgarClient` uses: a cached copy older than the cut would miss the 10-K it needs."""
    sub = json.loads(http.get_text(_SUBMISSIONS.format(cik=pad_cik(cik)), ttl_seconds=86_400))
    r = sub["filings"]["recent"]
    return sorted((r["filingDate"][i], r["accessionNumber"][i], r["primaryDocument"][i])
                  for i in range(len(r["form"])) if r["form"][i] == "10-K")


def graph_items(http: CachedHttp, graph_path: str, cut: date) -> list[dict[str, Any]]:
    edges = json.loads(Path(graph_path).read_text())["edges"]
    srcs: dict[str, dict[str, Any]] = {}
    out: list[dict[str, Any]] = []
    for e in edges:
        cik = e["focal_cik"]
        if cik not in srcs:
            try:
                pre = [k for k in _tenks(http, cik) if date.fromisoformat(k[0]) <= cut]
                if not pre:
                    srcs[cik] = {"why": f"no 10-K filed on or before {cut}"}
                else:
                    fd, acc, doc = pre[-1]
                    ex = relevant_excerpts(_exhibit_text(http, cik, acc, doc))
                    prior = None
                    if len(pre) > 1:
                        p = pre[-2]
                        prior = SourceText(relevant_excerpts(_exhibit_text(http, cik, p[1], p[2])))
                    srcs[cik] = {"acc": acc, "filed": fd, "text": ex, "src": SourceText(ex),
                                 "prior": prior, "prior_acc": pre[-2][1] if prior else None}
            except Exception as exc:  # noqa: BLE001 — reported as uncheckable, never fatal
                srcs[cik] = {"why": f"10-K fetch failed: {type(exc).__name__}"}
        s = srcs[cik]
        item: dict[str, Any] = {"corpus": "graph_edge", "ticker": e["focal_ticker"],
                                "item": e["counterparty_name"], "verdict": e["verdict"],
                                "quote": e["evidence"]}
        if "why" in s:
            item.update(status=f"uncheckable:{s['why']}", tier=None, source=None)
        else:
            item["source"] = f"10-K {s['acc']} (filed {s['filed']}, reconstructed)"
            item["status"], item["tier"] = _status(e["evidence"], s["text"], s["src"])
            if item["status"] == SpanMatch.NOT_FOUND.value and s["prior"] is not None:
                item["in_prior_10k"] = s["prior"].match(e["evidence"]).found
                item["prior_10k"] = s["prior_acc"]
        out.append(item)
    return out


def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
    by: dict[str, Any] = {}
    for corpus in sorted({i["corpus"] for i in items}):
        rows = [i for i in items if i["corpus"] == corpus]
        by[corpus] = {
            "quotes": len(rows),
            "names": len({i["ticker"] for i in rows}),
            "status": dict(Counter(i["status"] for i in rows)),
            "found_by_tier": dict(Counter(i["tier"] for i in rows if i["tier"])),
        }
    return by


def run(http: CachedHttp, *, dossier_glob: str, graph_path: str, cut: date) -> dict[str, Any]:
    items = covenant_items(http, dossier_glob) + graph_items(http, graph_path, cut)
    return {"graph_cut": cut.isoformat(), "summary": summarize(items),
            "refused": [i for i in items if i["status"] not in ("verbatim", "elided")]}


def main() -> int:
    from vinci.sec import build_sec_http

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dossiers", default="data/dossiers/*/dossier.json")
    ap.add_argument("--graph", default="data/graph_coverage.json")
    ap.add_argument("--graph-cut", default="2026-06-26",
                    help="reconstruct each focal's 10-K as the latest filed on or before this date "
                         "(default: the day graph_coverage.json was committed, be4268e6)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rep = run(build_sec_http(), dossier_glob=a.dossiers, graph_path=a.graph,
              cut=date.fromisoformat(a.graph_cut))
    Path(a.out).write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(json.dumps(rep["summary"], indent=1))
    print(f"{len(rep['refused'])} refused or uncheckable quotes written to {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
