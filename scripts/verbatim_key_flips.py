"""Does a change to the verbatim-span key move a committed answer? Old key against new, measured.

`vinci.verbatim.comparison_key` is read by four consumers. This script asks each one's committed
corpus the same question twice, once under the key as it stood before audit G-D7 (`_pre_gd7_key`,
copied from 9503c4fa) and once under the key this checkout carries, and lists every answer that
differs. Nothing is written back to any artifact.

- covenant terms, the maturity event and graph edges, read exactly as
  `scripts/audit_verbatim_corpus.py` reads them (its own functions);
- each rate component's own clause (`component_quotes`) against its term's exhibit;
- synthesis citations (bull, bear, decisive evidence, twin source) against the page's mechanical
  refs, as `synthesis._traces` compares them;
- theme-exposure fact refs, as `exposure._cited_filing_text` reads them (the key path is taken only
  by a ref with no accession).

CACHE ONLY. Every SEC document is read from ``--cache-dir`` at any age; a document not there is a
loud error, never a request, so the run cannot probe SEC's rate limit. Point it at a checkout whose
``data/cache`` holds the exhibits (the primary checkout's does).

    PYTHONPATH=. python scripts/verbatim_key_flips.py --cache-dir <checkout>/data/cache \\
        --exclude <TICKER> ... --out <path.json>

(`PYTHONPATH=.` imports THIS checkout's `vinci`, not the one the venv was installed from. The
script runs from the repo root, so a relative path argument is read from there.)
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys
import tempfile
import unicodedata
from collections import Counter
from collections.abc import Callable, Iterator
from datetime import date
from pathlib import Path
from typing import Any

import audit_verbatim_corpus as avc

from vinci import verbatim
from vinci.dossier import synthesis
from vinci.netcache import CachedHttp
from vinci.themes import exposure

Key = Callable[[str], str]

#: The key before audit G-D7 (9503c4fa), kept here as the fixed reference: every whitespace run
#: and invisible character removed, so a gap between two digits joined them.
_PRE_GD7_DROP = re.compile("[\\s­​‌‍⁠﻿]+")


def _pre_gd7_key(text: str) -> str:
    return _PRE_GD7_DROP.sub(
        "", unicodedata.normalize("NFKC", text).translate(verbatim._FOLD).casefold())


_CURRENT_KEY: Key = verbatim.comparison_key


class CacheMissError(RuntimeError):
    """A document the cache does not hold — this script never fetches one."""


class CacheOnlyHttp(CachedHttp):
    """Reads a `CachedHttp` cache at any age; never sends a request and never writes."""

    def __init__(self, cache_dir: Path) -> None:
        super().__init__(cache_dir=cache_dir, user_agent="cache-only", min_interval_sec=0,
                         namespace="sec")

    def _read_cache(self, url: str, ttl_seconds: float | None) -> str | None:
        return super()._read_cache(url, None)

    def _fetch_with_retries(self, url: str, **kw: Any) -> str:
        raise CacheMissError(url)

    def _write_cache(self, url: str, text: str) -> None:
        raise AssertionError(f"cache-only client asked to write {url}")


@contextlib.contextmanager
def _keyed(key: Key) -> Iterator[None]:
    """Every consumer reads ``key`` for the duration: the module global SourceText calls, and the
    names synthesis and exposure imported."""
    modules = (verbatim, synthesis, exposure)
    saved = [getattr(m, "comparison_key") for m in modules]  # noqa: B009 — a patched global
    for m in modules:
        setattr(m, "comparison_key", key)  # noqa: B010
    try:
        yield
    finally:
        for m, k in zip(modules, saved, strict=True):
            setattr(m, "comparison_key", k)  # noqa: B010


def _gap(quote: str) -> bool:
    """The key change bites this quote: its two keys differ."""
    return bool(quote) and _pre_gd7_key(quote) != _CURRENT_KEY(quote)


def _dossier_paths(root: Path, exclude: set[str]) -> list[Path]:
    """Every committed dossier but the excluded — chosen by FOLDER, so an excluded name's page and
    exhibits are never opened."""
    return [p for p in sorted(root.glob("data/dossiers/*/dossier.json"))
            if p.parent.name.upper() not in exclude]


def _dossiers(root: Path, exclude: set[str]) -> list[dict[str, Any]]:
    return [json.loads(p.read_text()) for p in _dossier_paths(root, exclude)]


def quote_corpora(http: CachedHttp, root: Path, exclude: set[str], cut: date) -> dict[str, Any]:
    """Covenant terms, maturity events, graph edges and rate-component clauses, old vs new."""
    graph = json.loads((root / "data/graph_coverage.json").read_text())
    graph["edges"] = [e for e in graph["edges"] if e["focal_ticker"].upper() not in exclude]
    runs: dict[str, list[dict[str, Any]]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        kept_graph = Path(tmp) / "graph_coverage.json"
        kept_graph.write_text(json.dumps(graph))
        for label, key in (("old", _pre_gd7_key), ("new", _CURRENT_KEY)):
            with _keyed(key):
                items = [i for p in _dossier_paths(root, exclude)
                         for i in avc.covenant_items(http, str(p))]  # a literal path globs itself
                items += avc.graph_items(http, str(kept_graph), cut)
                items += _rate_items(http, root, exclude)
            runs[label] = items
    out: dict[str, Any] = {}
    for corpus in ("covenant_term", "maturity_event", "graph_edge", "rate_component"):
        old = [i for i in runs["old"] if i["corpus"] == corpus]
        new = [i for i in runs["new"] if i["corpus"] == corpus]
        assert [(i["ticker"], i["item"], i["quote"]) for i in old] == \
            [(i["ticker"], i["item"], i["quote"]) for i in new], corpus
        out[corpus] = {
            "quotes": len(new), "names": len({i["ticker"] for i in new}),
            "status_old": dict(Counter(i["status"] for i in old)),
            "status_new": dict(Counter(i["status"] for i in new)),
            "carrying_a_digit_gap": [
                {"ticker": n["ticker"], "item": n["item"], "status": n["status"]}
                for n in new if _gap(n["quote"])],
            "flips": [{"ticker": n["ticker"], "item": n["item"], "old": o["status"],
                       "new": n["status"], "quote": n["quote"]}
                      for o, n in zip(old, new, strict=True) if o["status"] != n["status"]],
        }
    return out


def _rate_items(http: CachedHttp, root: Path, exclude: set[str]) -> list[dict[str, Any]]:
    out = []
    for d in _dossiers(root, exclude):
        rows = (d["mechanical"]["capital_structure"].get("covenant_term_rows") or {})
        for r in rows.get("value") or []:
            for comp, quote in (r.get("component_quotes") or {}).items():
                m = avc._REF.match(r["value"].get("source_ref") or "")
                if m is None:
                    raise ValueError(f"{d['ticker']} {r['name']}: unparsed source_ref")
                text = avc._exhibit_text(http, d["cik"], m.group(2), m.group(3))
                out.append({"corpus": "rate_component", "ticker": d["ticker"],
                            "item": f"{r['name']} / {comp}", "quote": quote,
                            "status": verbatim.SourceText(text).match(quote).value})
    return out


def _layer_refs(o: Any, acc: set[str]) -> set[str]:
    """`synthesis._refs_in`, over the committed JSON rather than the model."""
    if isinstance(o, dict):
        for k in ("source_ref", "accession", "url"):
            if o.get(k):
                acc.add(str(o[k]))
        for v in o.values():
            _layer_refs(v, acc)
    elif isinstance(o, list):
        for v in o:
            _layer_refs(v, acc)
    return acc


def synthesis_citations(root: Path, exclude: set[str]) -> dict[str, Any]:
    """Each citation `_validate` checks, cited or not under each key (`synthesis._traces`)."""
    c: Counter[str] = Counter()
    flips = []
    for d in _dossiers(root, exclude):
        s = d.get("synthesis") or {}
        dq = s.get("decisive_question") or {}
        cites = [("bull", p.get("source_ref", "")) for p in s.get("bull_points") or []]
        cites += [("bear", p.get("source_ref", "")) for p in s.get("bear_points") or []]
        cites += [("decisive", p.get("source_ref", ""))
                  for p in (dq.get("evidence_for") or []) + (dq.get("evidence_against") or [])]
        cites += [("twin", t.get("source", "")) for t in s.get("twin_reference_cases") or []]
        universe = _layer_refs(d["mechanical"], set())
        c["layer_refs"] += len(universe)
        c["layer_refs_carrying_a_digit_gap"] += sum(_gap(u) for u in universe)
        # `_values_by_ref` keys numbers by ref: two refs one key under the old rule, two under new
        split: dict[str, set[str]] = {}
        for u in universe:
            split.setdefault(_pre_gd7_key(u), set()).add(_CURRENT_KEY(u))
        c["values_by_ref_keys_split"] += sum(len(v) > 1 for v in split.values())
        for where, ref in cites:
            got = {}
            for label, key in (("old", _pre_gd7_key), ("new", _CURRENT_KEY)):
                with _keyed(key):
                    got[label] = synthesis._traces(ref, universe)
            c["citations"] += 1
            c["citations_carrying_a_digit_gap"] += _gap(ref)
            c[f"cited_old={got['old']}"] += 1
            c[f"cited_new={got['new']}"] += 1
            if got["old"] != got["new"]:
                flips.append({"ticker": d["ticker"], "where": where, "ref": ref, **got})
    return dict(c) | {"flips": flips}


def exposure_facts(root: Path) -> dict[str, Any]:
    """Every committed exposure fact ref: how many resolve by accession, and how many take the
    key path at all (`exposure._cited_filing_text`)."""
    c: Counter[str] = Counter()
    for p in sorted(root.glob("data/scan_history/*/*.jsonl")):
        c["files"] += 1
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            for f in json.loads(line).get("disclosed_facts") or []:
                ref = str(f.get("source_ref", ""))
                n = len(set(exposure._ACC_RE.findall(ref)))
                c["facts"] += 1
                c["one_accession" if n == 1 else "several_accessions" if n else "key_path"] += 1
                c["key_path_carrying_a_digit_gap"] += n == 0 and _gap(ref)
    return dict(c)


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--root", default=".", help="the checkout whose committed artifacts are read")
    ap.add_argument("--cache-dir", required=True, help="a data/cache holding the SEC documents")
    ap.add_argument("--exclude", action="append", default=[], help="a ticker left out (repeat)")
    ap.add_argument("--graph-cut", default="2026-06-26",
                    help="each focal's 10-K is the latest filed on or before this date "
                         "(the audit script's default)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    root = Path(a.root).resolve()
    exclude = {t.upper() for t in a.exclude}
    http = CacheOnlyHttp(Path(a.cache_dir))
    rep = {
        "excluded": len(exclude),
        "graph_cut": a.graph_cut,
        **quote_corpora(http, root, exclude, date.fromisoformat(a.graph_cut)),
        "synthesis_citation": synthesis_citations(root, exclude),
        "exposure_fact": exposure_facts(root),
    }
    Path(a.out).write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    flips = sum(len(v["flips"]) for v in rep.values() if isinstance(v, dict) and "flips" in v)
    print(json.dumps(rep, indent=1, ensure_ascii=False))
    print(f"{flips} answers moved; written to {a.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    # From the repo root, as every data-tree script here runs (tests/test_script_cwd_convention.py),
    # so a relative --root/--cache-dir/--out means the same thing wherever it is started. In
    # __main__ only: importing this module never moves a caller's working directory.
    os.chdir(Path(__file__).resolve().parents[1])
    raise SystemExit(main())
