"""Test helpers for pages whose transcript words are off them (RG-D19, the page pass).

This repo is public, so a committed page's transcript driver row carries its FACT and its LOCATOR,
not its words. The words are in the operator's private store. A test reads only what it needs:

- **The fact** — figures, change, bound, period, status — is on the page. Pin on it, in CI.
- **The words** — a row's own quote, for the up/down check against a real sentence — are read
  from the licensed CIQ call ON DISK by the row's locator, `passage`.
  - The locator gives the call file, its sha256, the paragraph and the quote's sha256, and each
    is checked.
  - No export on disk means a SKIP that names it, as every licensed-CIQ test skips in CI.
  - CI never reads the private store.
- **A replay's mechanics** need a page the replay accepts. `replayable` is the committed page
  without the transcript rows whose words are off it: the replay refuses a page that cannot
  rebuild the request its build sent (`capture_child.pre_synthesis_mech`).
- **The pass and the store's mechanics** run on `synthetic_page`: a real page whose transcript
  rows are replaced by invented ones that still hold their words, never licensed text.

`VINCI_CIQ_ROOT` points `passage` at a CIQ folder read in place (read only), for a checkout
that holds none.
"""

from __future__ import annotations

import functools
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import pytest

from vinci.config import get_config
from vinci.dossier.driver_extract import _following_paragraph, quote_key

ROOT = Path(__file__).resolve().parents[1]
_PARAGRAPH_BREAK = re.compile(r"\n[ \t]*\n")
#: The longest quote searched for: the longest committed transcript quote was 73 words.
_MAX_QUOTE_CHARS = 900


def committed_page(ticker: str) -> dict[str, Any]:
    page: dict[str, Any] = json.loads((ROOT / f"data/dossiers/{ticker}/dossier.json").read_text())
    return page


def replayable(page: dict[str, Any]) -> dict[str, Any]:
    """``page`` without the transcript rows whose words are off it — identity on a page that
    still holds them."""
    od = (page.get("mechanical") or {}).get("operating_drivers")
    if not od:
        return page
    rows = [r for r in od.get("rows", []) if not (r.get("tier") == "llm-fenced"
                                                  and not r.get("verbatim"))]
    return {**page, "mechanical": {**page["mechanical"],
                                   "operating_drivers": {**od, "rows": rows}}}


def replayable_text(ticker: str) -> str:
    """The committed page as a replay accepts it, as text (the form the tests read)."""
    return json.dumps(replayable(committed_page(ticker)))


def ciq_root() -> Path:
    env = os.environ.get("VINCI_CIQ_ROOT")
    root = Path(env) if env else get_config().data_dir / "manual" / "ciq"
    if not root.is_dir() or not any(root.iterdir()):
        pytest.skip("licensed CIQ bundles unavailable (never committed): a transcript row's words "
                    "are read from its call on disk")
    return root


@functools.cache
def _calls(ticker: str, root: str) -> tuple[dict[str, str], dict[str, str]]:
    from vinci.dossier.driver_pass import _calls_on_disk
    return _calls_on_disk(ticker, Path(root))


def _find_quote(text: str, want: str) -> str | None:
    """The span of ``text`` whose quote key is ``want``: starts at a word, any length up to the
    longest quote. Whitespace-collapsed and lower-cased, as the key is."""
    flat = re.sub(r"\s+", " ", text).strip()
    low = flat.lower()
    starts = [0] + [m.end() for m in re.finditer(" ", low)]
    # a quote ends where a word does: before a space, a punctuation mark or the end
    ends = [e for e in range(1, len(low) + 1)
            if low[e - 1] != " " and (e == len(low) or not low[e].isalnum())]
    for s in starts:
        for e in ends:
            if e <= s:
                continue
            if e - s > _MAX_QUOTE_CHARS:
                break
            if hashlib.sha256(low[s:e].encode("utf-8")).hexdigest() == want:
                return flat[s:e]
    return None


def passage(ticker: str, row: dict[str, Any]) -> tuple[str, str | None]:
    """``(quote, following paragraph)`` of a transcript row, from its call on disk by its locator
    — checked by the call file's sha256 and the quote's; skipped, naming what is missing, when the
    export is not on disk. A row that still holds its words returns them."""
    if row.get("verbatim"):
        return row["verbatim"], row.get("following_context")
    loc = row.get("locator") or {}
    call, root = loc.get("call"), ciq_root()
    bodies, shas = _calls(ticker, str(root))
    if call not in bodies:
        pytest.skip(f"{ticker}: the call {call!r} is not on disk (re-exported or retired); its "
                    "words are only in the private store")
    if loc.get("transcript_sha256") and shas.get(call) != loc["transcript_sha256"]:
        pytest.skip(f"{ticker}: {call!r} on disk is sha256 {str(shas.get(call))[:12]}, not the "
                    f"{loc['transcript_sha256'][:12]} the row was located in")
    body = bodies[call]
    if loc.get("paragraph") is None:
        pytest.skip(f"{ticker}: a call-only locator ({call!r}) names no paragraph to search")
    paragraphs = _PARAGRAPH_BREAK.split(body)
    quote = _find_quote(paragraphs[loc["paragraph"]], loc["quote_sha256"])
    assert quote is not None, (f"{ticker}: no span of paragraph {loc['paragraph']} of {call!r} "
                               "hashes to the row's quote_sha256 — the locator is wrong")
    assert quote_key(quote) == loc["quote_sha256"]
    return quote, _following_paragraph(quote, body)


#: Invented transcript rows: each holds its words, as an assembly's own rows do, and none is
#: licensed text. A real call's name and figures are never used.
_CALL = "Acme, Inc., Q3 2026 Earnings Call, Aug 04, 2026.rtf"
SYNTHETIC_ROWS: tuple[dict[str, Any], ...] = (
    {"kind": "leading_indicator", "metric": "widget shipments", "period": None,
     "value": "down 7%",
     "verbatim": "Widget shipments were down 7% in the quarter, as we expected.",
     "following_context": "They recovered in October.", "source_ref": f"CIQ transcript: {_CALL}",
     "tier": "llm-fenced"},
    {"kind": "leading_indicator", "metric": "widget shipments", "period": None,
     "value": "7%", "verbatim": "Widget shipments were down 7% in the quarter, as we expected.",
     "following_context": "They recovered in October.", "source_ref": f"CIQ transcript: {_CALL}",
     "tier": "llm-fenced"},
    {"kind": "leading_indicator", "metric": "widget shipments", "period": None,
     "value": "up 7%",
     "verbatim": "Widget shipments were down 7% in the quarter, as we expected.",
     "following_context": "They recovered in October.", "source_ref": f"CIQ transcript: {_CALL}",
     "tier": "llm-fenced"},
    {"kind": "competitive_position", "metric": "membership", "period": None,
     "value": "relatively flat", "verbatim": "Membership was relatively flat on a constant "
     "currency basis.", "following_context": None, "source_ref": f"CIQ transcript: {_CALL}",
     "tier": "llm-fenced"},
)


def synthetic_page(ticker: str = "BRBR") -> dict[str, Any]:
    """A committed page whose transcript rows are the invented `SYNTHETIC_ROWS`, holding their
    words: the shape the pass and the assembly take in, with no licensed text in it."""
    page = committed_page(ticker)
    od = page["mechanical"]["operating_drivers"]
    rows = [r for r in od["rows"] if r.get("tier") != "llm-fenced"] + [dict(r) for r in
                                                                        SYNTHETIC_ROWS]
    return {**page, "mechanical": {**page["mechanical"],
                                   "operating_drivers": {**od, "rows": rows}}}


def committed_pages() -> list[tuple[str, dict[str, Any]]]:
    return [(p.parent.name, json.loads(p.read_text()))
            for p in sorted((ROOT / "data/dossiers").glob("*/dossier.json"))]


def rows_with_words() -> tuple[list[tuple[str, dict[str, Any], str]], int]:
    """``([(ticker, row, its quote)], how many rows were skipped)`` over every committed
    transcript row whose words can be read: its own, or its call's on disk (`passage`). A row whose
    call is not on disk is counted, not checked. With no CIQ folder at all (CI) the caller's test
    SKIPS, naming why — before the pass took the words off, every row had its own."""
    out: list[tuple[str, dict[str, Any], str]] = []
    skipped = 0
    for ticker, page in committed_pages():
        for r in (page["mechanical"].get("operating_drivers") or {}).get("rows", []):
            if r.get("tier") != "llm-fenced":
                continue
            try:
                quote, _ = passage(ticker, r)
            except pytest.skip.Exception:
                if not r.get("verbatim") and not out and skipped == 0:
                    ciq_root()   # no CIQ folder at all: skip the whole test, naming why
                skipped += 1
                continue
            out.append((ticker, r, quote))
    return out, skipped
