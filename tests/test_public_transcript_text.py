"""THE RULE FOR PUBLIC TRANSCRIPT TEXT (CLAUDE.md; operator ruling 2026-11-10, relayed by the
coordinator: "yes to all").

The rule is NO PUBLIC FIELD QUOTES MORE THAN 12 CONSECUTIVE TRANSCRIPT WORDS, AND A DRIVER ROW
QUOTES NONE. This repo is public. A transcript is licensed text, and its evidence lives in the
operator's private store (`vinci/dossier/driver_evidence.py`), not in git.

Held here on every committed page, its frontend mirror and every test fixture (`SCANNED`), where
code knows a field is transcript text:
- **A transcript driver row** (`tier == "llm-fenced"`) carries no `verbatim`,
  `following_context` or `value` at all. Its `period`, which is stated in its quote, holds at most
  12 words. Its `metric` is the extractor's label, not a quote, and holds at most 15: a shape
  guard, so a sentence cannot enter that way.
- **A synthesis item citing a transcript** quotes, between quotation marks, at most 12 words in a
  run.
- **What a row keeps instead**: its fact (`value_status`) and its locator, which names its call
  and the hashes of its quote and its stated value (`value_sha256`: the words were filed before
  they left, `driver_evidence.spool_dossier`).

CIQ Key Developments' text is NOT held here. It is CIQ's own text, not a transcript, and it is
the operator's separate, unruled question (STATE row 60, item 3b).

CORPUS BEFORE SYNTHETIC. Before the page pass, this test fired on the committed pages, and the
count is in `docs/records/2026-11-10-driver-facts-page-pass.md`. The pins below show each half
firing on the shapes it must refuse.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
#: The number (CLAUDE.md): the most of a transcript, in consecutive words, any public field quotes.
MAX_QUOTED_WORDS = 12
#: A driver row's label is the extractor's words, not a quote; this only stops a sentence.
MAX_LABEL_WORDS = 15
PRIVATE = ("verbatim", "following_context", "value")
#: A quoted run: between straight or curly double quotes.
_QUOTED = re.compile(r"[\"“]([^\"”]{1,2000})[\"”]")


def _words(s: object) -> int:
    return len(str(s).split()) if s else 0


def violations(page: dict[str, Any], name: str) -> list[str]:
    """Every way ``page`` publishes transcript text beyond the rule."""
    out: list[str] = []
    rows = ((page.get("mechanical") or {}).get("operating_drivers") or {}).get("rows") or []
    for i, r in enumerate(rows):
        if r.get("tier") != "llm-fenced":
            continue
        for k in PRIVATE:
            if r.get(k):
                out.append(f"{name} driver row {i}: `{k}` publishes {_words(r[k])} transcript "
                           "word(s); a driver row quotes none")
        if _words(r.get("period")) > MAX_QUOTED_WORDS:
            out.append(f"{name} driver row {i}: `period` quotes {_words(r['period'])} words")
        if _words(r.get("metric")) > MAX_LABEL_WORDS:
            out.append(f"{name} driver row {i}: `metric` runs to {_words(r['metric'])} words")

    def walk(o: Any, where: str) -> None:
        if isinstance(o, dict):
            if "transcript" in str(o.get("source_ref", "")).lower():
                for k, v in o.items():
                    if isinstance(v, str):
                        for m in _QUOTED.finditer(v):
                            if _words(m.group(1)) > MAX_QUOTED_WORDS:
                                out.append(f"{name} {where}.{k}: quotes {_words(m.group(1))} "
                                           "consecutive words of a transcript")
            for k, v in o.items():
                walk(v, f"{where}.{k}")
        elif isinstance(o, list):
            for j, v in enumerate(o):
                walk(v, f"{where}[{j}]")

    walk(page.get("synthesis") or {}, "synthesis")
    return out


#: Where a committed page is: the pages, their frontend mirrors, and every test fixture (the frozen
#: pages among them are public files too — coordinator, 2026-11-10).
SCANNED = ("data/dossiers", "frontend/dossiers", "tests/fixtures")


def _public_pages() -> list[tuple[str, Any]]:
    out = []
    for tree in SCANNED:
        for p in sorted((ROOT / tree).rglob("*.json")):
            try:
                doc = json.loads(p.read_text())
            except (UnicodeDecodeError, ValueError):
                continue
            if isinstance(doc, dict) and "mechanical" in doc:
                out.append((str(p.relative_to(ROOT)), doc))
    return out


def test_no_committed_page_publishes_transcript_text_beyond_the_rule() -> None:
    pages = _public_pages()
    assert len(pages) >= 60, "the committed pages, mirrors and fixtures are not where they were"
    assert any(n.startswith("tests/fixtures/frozen_pages/") for n, _ in pages)
    bad = [v for name, page in pages for v in violations(page, name)]
    shown = bad[:8]
    assert bad == [], (f"{len(bad)} violation(s) of the transcript-text rule (showing "
                       f"{len(shown)} of {len(bad)}):\n" + "\n".join(shown))


def test_every_committed_transcript_row_keeps_its_fact_and_its_locator() -> None:
    """A row whose words are off the page is still read: by its fact, and back to its call by its
    locator. One without both would be a row the pass emptied rather than filed."""
    rows = [(name, i, r) for name, page in _public_pages() for i, r in enumerate(
        ((page.get("mechanical") or {}).get("operating_drivers") or {}).get("rows") or [])
        if r.get("tier") == "llm-fenced"]
    assert len(rows) >= 1000, "the committed transcript rows are not where they were"
    bad = [f"{n} driver row {i}" for n, i, r in rows
           if not r.get("value_status") or not (r.get("locator") or {}).get("call")
           or not (r.get("locator") or {}).get("quote_sha256")
           or not (r.get("locator") or {}).get("value_sha256")]
    shown = bad[:8]
    assert bad == [], (f"{len(bad)} of {len(rows)} transcript row(s) lack a fact or a locator "
                       f"(showing {len(shown)} of {len(bad)}):\n" + "\n".join(shown))


# --- each half bites on the shape it must refuse ------------------------------------------------

def _page(row: dict[str, Any] | None = None, point: dict[str, Any] | None = None
          ) -> dict[str, Any]:
    return {"mechanical": {"operating_drivers": {"rows": [row] if row else []}},
            "synthesis": {"bull_points": [point] if point else []}}


_ROW = {"kind": "leading_indicator", "metric": "widget shipments", "tier": "llm-fenced",
        "source_ref": "CIQ transcript: Acme, Inc., Q3 2026 Earnings Call, Aug 04, 2026.rtf"}


def test_a_driver_row_with_any_word_of_its_quote_context_or_value_is_refused() -> None:
    assert violations(_page(_ROW), "x") == []
    for k in PRIVATE:
        assert len(violations(_page({**_ROW, k: "down 7%"}), "x")) == 1, k
    # an anchored row's text is a filing's or CIQ's: not this rule's
    assert violations(_page({**_ROW, "tier": "anchored", "verbatim": "x " * 60}), "x") == []


def test_a_long_label_or_period_is_refused() -> None:
    assert violations(_page({**_ROW, "period": "the third quarter of fiscal 2026"}), "x") == []
    assert violations(_page({**_ROW, "period": " ".join(["word"] * 13)}), "x")
    assert violations(_page({**_ROW, "metric": " ".join(["word"] * 16)}), "x")


def test_a_synthesis_point_citing_a_call_quotes_at_most_twelve_words() -> None:
    ref = {"source_ref": "CIQ transcript: Acme, Inc., Q3 2026 Earnings Call, Aug 04, 2026.rtf"}
    twelve = " ".join(["word"] * 12)
    assert violations(_page(point={**ref, "claim": f'Management said "{twelve}".'}), "x") == []
    long_quote = f"Management said “{twelve} more”."
    assert violations(_page(point={**ref, "claim": long_quote}), "x")
    # a point citing a filing is not a transcript's text
    assert violations(_page(point={"source_ref": "EDGAR 10-Q", "claim": f'"{twelve} more"'}),
                      "x") == []
