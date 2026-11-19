"""THE COMMITTED COVENANT QUOTES, CHECKED AGAINST THE EXHIBITS THEY CITE — read from the cache,
never from SEC (engineering report P2-14, the covenant half; W64, 2026-11-19).

Every PRESENT covenant term on a committed page (`mechanical.capital_structure.covenant_term_rows`)
stores the clause it was read from in its note (`covenant_extract.note_quote`) and cites the
exhibit (`covenant_extract._exhibit_of`: accession and file, set by code, never by the model). A
rate component kept by a clause of its own stores that clause too (`component_quotes`). Since #804
(2026-10-26) the extractor refuses, at extraction, a quote that is not a span of the exhibit text it
sent. Nothing re-read the COMMITTED quotes against their exhibits after that: a page built before
#804 was never checked, and a page built since was checked through the converter of its day.

For every quote this says one of three things, and a miss is always a row, never dropped:

- ``found``: the quote is a span (`vinci.verbatim`, verbatim or elided) of its own exhibit;
- ``not_found``: its exhibit is held, and the quote is not a span of it;
- ``uncached``: no cache root holds its exhibit.

No searching: the row names its document. Each exhibit is read once, through
`filings.html_to_text` (the extractor's own conversion), whole, as the extractor sent it.

A ``not_found`` row names its CAUSE, read off the documents, never guessed (`CAUSES`):

- ``wrong_exhibit``: the whole quote is a span of ANOTHER exhibit the page cites, not of its own;
- ``reordered``: every piece between its ellipses is a span of the exhibit, out of the exhibit's
  order, and the same pieces in another order are a span;
- ``editorial_bracket``: a piece reads in the exhibit once its bracketed insertions are taken out
  ("[Term Loan payment schedule]"), or is one: words the model added, which the filing does not
  print. A bracket a template prints itself ("[Borrower]") would be taken out too; no miss on any
  corpus measured has one, so the rule does not ask;
- ``label_added``: a piece reads in the exhibit once a section number the model put before it is
  taken away ("2.03(b) If the Administrative Agent notifies …");
- ``unmarked_join``: a piece reads in the exhibit as two or more sentences, in order, joined with no
  ellipsis between them;
- ``not_a_span``: anything else: a word added, dropped or corrected; struck text; a section label
  with another defect beside it (TJX's "2.06(c): If …", whose clause still does not read once the
  label is gone); a piece repeated where the exhibit prints it once; or pieces in the exhibit's
  order that miss only at punctuation. The first piece that is not a span is printed.

PAGE FURNITURE IS NOT A CAUSE HERE. Since #829 (2026-10-28) `html_to_text` drops a page number or
running header from the text, and no miss on either corpus measured (W64's record) reads across one.

LIMITS, stated. A span check proves PRESENCE, never SUPPORT (`vinci.verbatim`). Beside the outcome
each row carries ``value_unstated``: the figures its VALUE states that its quote does not
(`covenant_extract.unstated_in_quote`, the extractor's own E2-D19 rule over the same clauses). The
answer is relative to `html_to_text` and `vinci.verbatim` at the commit it runs on.

NEVER A FETCH. Each cache root is read through `graph.evidence_check`'s `_HeldOnly`, which answers
from the cache whatever a copy's age and refuses to send anything. A document is read from the first
root that holds it, and the row names that root and the sha256 of the copy it read.
"""

from __future__ import annotations

import argparse
import dataclasses
import functools
import hashlib
import itertools
import json
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vinci.dossier.covenant_extract import (
    _exhibit_of,
    _quoted_clauses,
    note_quote,
    unstated_in_quote,
)
from vinci.dossier.schemas import CovenantTerm, SourceStatus
from vinci.graph.evidence_check import _HeldOnly, held_reader
from vinci.graph.filings import html_to_text
from vinci.verbatim import SourceText, SpanMatch

FOUND, NOT_FOUND, UNCACHED = "found", "not_found", "uncached"
OUTCOMES = (FOUND, NOT_FOUND, UNCACHED)
WRONG_EXHIBIT, REORDERED, EDITORIAL_BRACKET, LABEL_ADDED, UNMARKED_JOIN, NOT_A_SPAN = (
    "wrong_exhibit", "reordered", "editorial_bracket", "label_added", "unmarked_join",
    "not_a_span")
CAUSES = (WRONG_EXHIBIT, REORDERED, EDITORIAL_BRACKET, LABEL_ADDED, UNMARKED_JOIN, NOT_A_SPAN)
#: The quote a row stores in its note; any other value of ``quote_of`` is a rate component's name.
ROW_QUOTE = "row"
_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
#: A quote's pieces, as `vinci.verbatim` splits them: at "…", "..." or "[...]", spaces allowed.
_ELLIPSIS = re.compile(r"\[?\s*(?:…|\.\s*\.\s*\.)\s*\]?")
#: An insertion in square brackets that is not an ellipsis: words the model added.
_BRACKET = re.compile(r"\[[^\]…]*[^\W\d_][^\]…]*\]")
#: A section number the model put before a clause: "2.03(b) ", "Section 2.08(c): ".
_LABEL = re.compile(r"^(?:section\s+)?\d+(?:\.\d+)*(?:\([a-z0-9]+\))*\s*:?\s+", re.I)
#: A sentence's end inside a piece: a stop, semicolon or colon followed by whitespace.
_SENTENCE = re.compile(r"(?<=[.;:])\s+")


@dataclass(frozen=True)
class QuoteCheck:
    """One committed quote's answer."""

    ticker: str
    term: str
    quote_of: str  # ROW_QUOTE, or the rate component whose own clause this is ("floor_pct")
    source_ref: str
    accession: str
    filename: str
    outcome: str
    quote: str
    match: str = ""  # the `SpanMatch` value; "" when the exhibit is not held
    cache_root: str = ""  # the root the exhibit was read from; "" when no root holds it
    document_sha256: str = ""  # sha256 of the held copy's text; "" when no root holds it
    cause: str = ""  # a not_found row's cause (`CAUSES`); "" otherwise
    unfound_piece: str = ""  # a not_found row's first piece that is not a span, in full
    in_other_exhibits: tuple[str, ...] = ()  # other cited exhibits the whole quote is a span of
    value_unstated: tuple[str, ...] = ()  # figures the term's value states that its quote does not

    @property
    def quote_sha256(self) -> str:
        return hashlib.sha256(self.quote.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class _Quote:
    term: str
    quote_of: str
    quote: str
    source_ref: str
    accession: str
    filename: str
    value_unstated: tuple[str, ...]


def page_quotes(page: Mapping[str, Any]) -> Iterator[_Quote]:
    """Every quote a committed page's PRESENT covenant terms store, in the page's order: each term's
    own quote, then each of its components' own clauses. A PRESENT term that stores no quote, or
    names no exhibit, raises: every PRESENT term is written with both."""
    cs = (page.get("mechanical") or {}).get("capital_structure") or {}
    block = cs.get("covenant_term_rows") or {}
    for raw in block.get("value") or []:
        row = CovenantTerm.model_validate(raw)
        if row.value.status is not SourceStatus.PRESENT:
            continue
        quote = note_quote(row.value.note)
        accession, filename = _exhibit_of(row)
        if quote is None or not accession:
            raise ValueError(f"{page.get('ticker')}: PRESENT covenant term {row.name!r} stores no "
                             f"quote or names no exhibit ({row.value.source_ref!r})")
        src = str(row.value.source_ref)
        unstated = tuple(unstated_in_quote(str(row.value.value),
                                           _quoted_clauses(quote, dict(row.component_quotes))))
        yield _Quote(row.name, ROW_QUOTE, quote, src, accession, filename, unstated)
        for comp, clause in row.component_quotes.items():
            yield _Quote(row.name, comp, clause, src, accession, filename, ())


class _Held:
    """Each exhibit's text, read once from the first root that holds it."""

    def __init__(self, readers: Sequence[tuple[Path, _HeldOnly]]) -> None:
        self._readers = readers
        self._docs: dict[str, tuple[str, str, SourceText] | None] = {}

    def get(self, cik: str, accession: str, filename: str) -> tuple[str, str, SourceText] | None:
        """(root, sha256 of the copy, its text as compared) — None when no root holds it."""
        url = _ARCHIVE.format(cik=int(cik), acc=accession.replace("-", ""), doc=filename)
        if url not in self._docs:
            self._docs[url] = None
            for root, reader in self._readers:
                raw = reader.held_text(url)
                if raw is not None:
                    sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
                    self._docs[url] = (str(root), sha, SourceText(html_to_text(raw)))
                    break
        return self._docs[url]


def _pieces(quote: str) -> list[str]:
    return [p.strip(" .,;:") for p in _ELLIPSIS.split(quote) if p.strip(" .,;:")]


def _in_order(source: SourceText, parts: Sequence[str]) -> bool:
    """Every part a span of ``source``, in the source's order (`vinci.verbatim`'s elision rule)."""
    return bool(parts) and source.match(" ... ".join(parts)).found


#: Up to this many pieces every order is tried; past it, one order sorted by which piece precedes
#: which. A sort cannot place a piece the exhibit prints everywhere ("(a)"), so it is the fallback.
_EVERY_ORDER = 7


def _orders(source: SourceText, pieces: Sequence[str]) -> Iterable[Sequence[str]]:
    """The other orders of ``pieces`` a reordering may be: all of them, or one sorted."""
    if len(pieces) <= _EVERY_ORDER:
        return itertools.permutations(pieces)

    def before(a: str, b: str) -> int:
        ab, ba = _in_order(source, [a, b]), _in_order(source, [b, a])
        return -1 if ab and not ba else 1 if ba and not ab else 0

    return [sorted(pieces, key=functools.cmp_to_key(before))]


def _all_pieces_found(quote: str, pieces: Sequence[str],
                      source: SourceText) -> tuple[str, str]:
    """The cause when every trimmed piece is a span. ``reordered`` only when the quote's order is
    not the exhibit's and another order of the same pieces is. A quote whose pieces are already in
    order misses only at the punctuation this trim forgives and `vinci.verbatim` does not (a cut's
    punctuation is trimmed at its end only), and a piece repeated where the exhibit prints it once
    has no order at all: both are ``not_a_span``, naming the piece that is not a span."""
    if _in_order(source, pieces):
        raw = [p for p in _ELLIPSIS.split(quote) if p.strip(" .,;:")]
        return NOT_A_SPAN, next((p.strip() for p in raw if not source.match(p).found), quote)

    if any(_in_order(source, order) for order in _orders(source, pieces)):
        return REORDERED, ""
    breaks = next(i for i in range(1, len(pieces) + 1) if not _in_order(source, pieces[:i]))
    return NOT_A_SPAN, pieces[breaks - 1]


def _cause(quote: str, source: SourceText, others: tuple[str, ...]) -> tuple[str, str]:
    """(cause, the first piece that is not a span) for a quote ``source`` does not hold."""
    if others:
        return WRONG_EXHIBIT, ""
    pieces = _pieces(quote)
    unfound = [p for p in pieces if not source.match(p).found]
    if not unfound:
        return _all_pieces_found(quote, pieces, source)
    first = unfound[0]
    bare = [p.strip(" .,;:") for p in _BRACKET.split(first) if p.strip(" .,;:")]
    if _BRACKET.search(first) and (not bare or _in_order(source, bare)):
        return EDITORIAL_BRACKET, first
    label = _LABEL.match(first)
    if label and source.match(first[label.end():]).found:
        return LABEL_ADDED, first
    sentences = [s for s in _SENTENCE.split(first) if s.strip()]
    if len(sentences) > 1 and _in_order(source, sentences):
        return UNMARKED_JOIN, first
    return NOT_A_SPAN, first


def check_pages(pages: Mapping[str, Mapping[str, Any]],
                readers: Sequence[tuple[Path, _HeldOnly]]) -> list[QuoteCheck]:
    """Every committed quote's answer, page by page in ``pages``' order."""
    held = _Held(readers)
    out: list[QuoteCheck] = []
    for ticker, page in pages.items():
        cik = str(page["cik"])
        quotes = list(page_quotes(page))
        exhibits = sorted({(q.source_ref, q.accession, q.filename) for q in quotes})
        for q in quotes:
            got = held.get(cik, q.accession, q.filename)
            row = QuoteCheck(ticker=ticker, term=q.term, quote_of=q.quote_of,
                             source_ref=q.source_ref, accession=q.accession, filename=q.filename,
                             outcome=UNCACHED, quote=q.quote, value_unstated=q.value_unstated)
            if got is None:
                out.append(row)
                continue
            root, sha, source = got
            m = source.match(q.quote)
            row = dataclasses.replace(row, cache_root=root, document_sha256=sha, match=m.value)
            if m.found:
                out.append(dataclasses.replace(row, outcome=FOUND))
                continue
            others = []
            for ref, acc, fn in exhibits:
                if (acc, fn) == (q.accession, q.filename):
                    continue
                other = held.get(cik, acc, fn)
                if other is not None and other[2].match(q.quote).found:
                    others.append(ref)
            cause, piece = _cause(q.quote, source, tuple(others))
            out.append(dataclasses.replace(row, outcome=NOT_FOUND, cause=cause,
                                           unfound_piece=piece, in_other_exhibits=tuple(others)))
    return out


def report_lines(results: Sequence[QuoteCheck], *, pages_dir: str, commit: str,
                 roots: Sequence[Path]) -> list[str]:
    """The read, in full: the counts with their boundary, per page, then every row that is not a
    find, each printed whole, and every row whose value states a figure its quote does not."""
    rows = [r for r in results if r.quote_of == ROW_QUOTE]
    comps = [r for r in results if r.quote_of != ROW_QUOTE]
    tickers = list(dict.fromkeys(r.ticker for r in results))
    exhibits = {(r.ticker, r.accession, r.filename) for r in results}
    held = {(r.ticker, r.accession, r.filename) for r in results if r.outcome != UNCACHED}

    def counts(rs: Sequence[QuoteCheck]) -> str:
        c = Counter(r.outcome for r in rs)
        m = Counter(r.match for r in rs if r.outcome == FOUND)
        return (" · ".join(f"{o} {c.get(o, 0)}" for o in OUTCOMES)
                + f" (found: verbatim {m.get(SpanMatch.VERBATIM.value, 0)}, elided "
                  f"{m.get(SpanMatch.ELIDED.value, 0)})")

    lines = [
        f"covenant quotes vs their exhibits — the pages in {pages_dir}, read by the code at "
        f"{commit}: {len(rows)} quoted PRESENT "
        f"terms and {len(comps)} component clauses on {len(tickers)} pages, citing "
        f"{len(exhibits)} exhibits ({len(held)} held); cache roots, first holder wins (never "
        "fetched): " + "; ".join(str(r) for r in roots),
        f"  terms: {counts(rows)}",
        f"  component clauses: {counts(comps)}",
        f"  by page ({len(tickers)} of {len(tickers)}):",
    ]
    for t in tickers:
        mine = [r for r in results if r.ticker == t]
        c = Counter(r.outcome for r in mine)
        lines.append(f"    {t}: {len(mine)} quotes — "
                     + " · ".join(f"{o} {c.get(o, 0)}" for o in OUTCOMES if c.get(o)))
    misses = [r for r in results if r.outcome == NOT_FOUND]
    by_cause = Counter(r.cause for r in misses)
    lines.append(f"  not_found: {len(misses)}"
                 + (" — " + " · ".join(f"{k} {by_cause[k]}" for k in CAUSES if by_cause.get(k))
                    if misses else ""))
    for r in misses:
        where = (f"; a span of {'; '.join(r.in_other_exhibits)}" if r.in_other_exhibits else "")
        lines.append(f"    {r.ticker} | {r.term} | {r.quote_of} | {r.source_ref} | "
                     f"{r.cause}{where}")
        lines.append(f"      quote: {r.quote}")
        if r.unfound_piece:
            lines.append(f"      first piece not in the exhibit: {r.unfound_piece}")
    uncached = [r for r in results if r.outcome == UNCACHED]
    lines.append(f"  uncached: {len(uncached)}, in "
                 f"{len({(r.ticker, r.accession, r.filename) for r in uncached})} exhibits")
    for r in uncached:
        lines.append(f"    {r.ticker} | {r.term} | {r.quote_of} | {r.source_ref}")
    unstated = [r for r in results if r.value_unstated]
    lines.append(f"  a term's value states a figure its quote does not: {len(unstated)}")
    for r in unstated:
        lines.append(f"    {r.ticker} | {r.term} | {r.source_ref} ({r.outcome}): "
                     + ", ".join(r.value_unstated))
    return lines


def rows_json(results: Sequence[QuoteCheck]) -> list[dict[str, Any]]:
    """Every quote's answer, one object each, in the read's order: what `--json` writes."""
    return [{**dataclasses.asdict(r), "quote_sha256": r.quote_sha256} for r in results]


def load_pages(pages_dir: Path, tickers: Iterable[str] | None = None) -> dict[str, dict[str, Any]]:
    """Every ``<T>/dossier.json`` under ``pages_dir`` (or the named ones), by ticker, sorted."""
    names = sorted(tickers) if tickers is not None else sorted(
        p.parent.name for p in pages_dir.glob("*/dossier.json"))
    return {t: json.loads((pages_dir / t / "dossier.json").read_text()) for t in names}


def default_cache_roots(repo: Path) -> list[Path]:
    """This checkout's ``data/cache`` and the primary checkout's (a worktree's git common dir's
    parent), each where it has an SEC namespace, this checkout's first."""
    roots = [repo / "data" / "cache"]
    try:
        common = subprocess.run(["git", "-C", str(repo), "rev-parse", "--path-format=absolute",
                                 "--git-common-dir"], capture_output=True, text=True,
                                check=True).stdout.strip()
        roots.append(Path(common).parent / "data" / "cache")
    except (OSError, subprocess.CalledProcessError):
        pass
    out: list[Path] = []
    for r in roots:
        if (r / "sec").is_dir() and r.resolve() not in {o.resolve() for o in out}:
            out.append(r)
    return out


def readers_for(roots: Sequence[Path]) -> list[tuple[Path, _HeldOnly]]:
    return [(r, held_reader(r)) for r in roots]


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m vinci.dossier.covenant_evidence_check",
                                 description=__doc__.split("\n\n")[0] if __doc__ else None)
    ap.add_argument("--pages", type=Path, default=Path("data/dossiers"))
    ap.add_argument("--ticker", action="append", default=None, help="only these pages")
    ap.add_argument("--cache-root", type=Path, action="append", default=None,
                    help="a data/cache to read (repeatable, first holder wins; read only, nothing "
                         "is fetched). Default: this checkout's and the primary checkout's")
    ap.add_argument("--json", type=Path, default=None, help="also write every quote's row here")
    a = ap.parse_args(list(argv) if argv is not None else None)
    repo = Path.cwd()
    roots = a.cache_root or default_cache_roots(repo)
    if not roots:
        print("no SEC cache: pass --cache-root <a checkout's data/cache>", file=sys.stderr)
        return 2
    try:
        commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short=8", "HEAD"],
                                capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "an unknown commit"
    results = check_pages(load_pages(a.pages, a.ticker), readers_for(roots))
    print("\n".join(report_lines(results, pages_dir=str(a.pages), commit=commit, roots=roots)))
    if a.json is not None:
        a.json.write_text(json.dumps({"pages": str(a.pages), "commit": commit,
                                      "cache_roots": [str(r) for r in roots],
                                      "rows": rows_json(results)}, indent=1) + "\n")
        print(f"wrote {len(results)} rows to {a.json}")
    return 1 if any(r.outcome == NOT_FOUND for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
