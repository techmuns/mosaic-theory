"""Test support (W73, 2026-11-19): the two reads `compute_anchor` requires, stated by each test.

Since W73 the anchor takes the company's filings after the close R1 prices (the EVENT RULE,
`anchor.close_verdict`) and the store's EOD closes (the price-drift FLAG, `anchor.close_drift`)
as REQUIRED keywords, so every caller says what it read. A pin whose subject is something else
states the plain reading:

* ``NO_FILINGS`` — the filings WERE read and nothing was filed: every dated close at or before the
  page's date passes the event rule (a close after it is still refused, W68);
* ``NO_BARS`` — the store WAS read and holds no bar: the multiple row states the move "not
  measured" (a close on the page's own date is the page's close, so it measures 0 with no bar).

The event rule's and the drift flag's own pins (`tests/test_w73_dated_multiple.py`) read the real
filings (`tests/fixtures/event_rule_filings.json`) and real EOD closes instead.
"""
from __future__ import annotations

import copy
import json
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from vinci.dossier.freshness import FilingEvent

NO_FILINGS: tuple[FilingEvent, ...] = ()
NO_BARS: tuple[tuple[date, float], ...] = ()
_NOW = datetime(2026, 11, 19, tzinfo=UTC)

_FILINGS = Path(__file__).resolve().parent / "fixtures" / "event_rule_filings.json"


def page_filings(ticker: str) -> list[FilingEvent]:
    """The filer's real 10-Qs, 10-Ks and 8-K item 2.02 releases, 2026-08-01..2026-11-19, as frozen
    from EDGAR's submissions feed (public metadata) through `mechanical.read_filing_events`."""
    events = json.loads(_FILINGS.read_text())["filings"][ticker]["events"]
    return [FilingEvent(form=e["form"], filing_date=e["filing_date"], accession=e["accession"],
                        items=tuple(e.get("items") or ())) for e in events]


_FACTS = Path(__file__).resolve().parent / "fixtures" / "companyfacts"


def rederived(doc: dict[str, Any], *, filings: Sequence[FilingEvent] = NO_FILINGS,
              eod_closes: Sequence[tuple[date, float]] = NO_BARS) -> dict[str, Any]:
    """``doc`` with the anchor W73's `anchor-backfill` writes on it, through the real path:
    `compute_anchor` on the page's own mechanical layer and its committed companyfacts fixture
    (`tests/fixtures/companyfacts/<T>.json`), the R4 machine proposal, and the committed
    operator's tag kept (`preserve_operator_tag`). For a pin whose subject reads the anchor's
    W73 verdict — the scenario proposal takes R1's own dated close only where the anchor recorded
    the event rule passing it — on a page whose committed anchor predates W73."""
    from vinci.dossier import recipe_proposal
    from vinci.dossier.anchor import (
        Anchor,
        anchor_absent_fields,
        compute_anchor,
        preserve_operator_tag,
    )

    t = str(doc["ticker"])
    facts = json.loads((_FACTS / f"{t}.json").read_text())
    ref = doc.get("reference_date")
    a = compute_anchor(doc["mechanical"], facts=facts, computed_at=_NOW, filings=filings,
                       eod_closes=eod_closes,
                       reference_date=date.fromisoformat(str(ref)[:10]) if ref else None)
    a = recipe_proposal.propose(doc, a)
    held = doc.get("anchor")
    a, _notes = preserve_operator_tag(Anchor.model_validate(held) if held else None, a)
    out = copy.deepcopy(doc)
    out["anchor"] = json.loads(a.model_dump_json(exclude=anchor_absent_fields(a) or None))
    return out
