"""Pure parsing of the SEC ``submissions`` payload's registrant-name fields.

WHY ITS OWN MODULE. Two consumers read the ``formerNames`` array — the dossier's rename marker
(via :class:`vinci.edgar.client.EdgarClient`) and the resolver's issuer enrichment — and two
parsers of one source is the twin-drift class this repo keeps finding (the ``share_count_change``
precedent). The obvious shared home, ``edgar/client.py``, cannot be it: that module imports
``pad_cik`` from ``vinci.resolver.index``, so a resolver-side import of it closes a cycle. This
module depends on nothing but the stdlib and pydantic, so BOTH sides can read it.

NO HTTP HERE. Fetching belongs to the client; this file only interprets a payload it is handed,
which is also what makes it testable against a real captured response.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel


class FormerName(BaseModel, frozen=True):
    """One prior registrant name on a CIK, with the span it was in force (submissions JSON)."""

    name: str
    from_date: date | None  # absent on some very old rows — the END of the span is what matters
    to_date: date  # the day the registrant stopped filing under this name


class RegistrantHistory(BaseModel, frozen=True):
    """A CIK's registrant names: the CURRENT one and every prior span.

    The two travel together because a former name is only interpretable against the name in force
    — and the caller must not substitute its own idea of the current name. ``identity.name`` is
    resolver output from ``company_tickers.json`` and is persisted inside stored records, so it can
    predate a rename; the submissions payload states the authoritative name in the SAME response
    that carries the former ones, and dropping it was a real defect (review, #558).
    """

    current: str
    former: tuple[FormerName, ...]


def parse_former_names(data: dict[str, Any]) -> tuple[FormerName, ...]:
    """The ONE parse of the submissions ``formerNames`` array.

    Rows missing a name or an end date are SKIPPED, never guessed: an unreadable rename row must
    not fabricate a vintage. A malformed DATE raises ``ValueError`` to the caller rather than being
    swallowed here — a systematic EDGAR format change must stay diagnosable as a parse failure
    instead of being reported as one flaky request.
    """
    out: list[FormerName] = []
    for row in data.get("formerNames") or []:
        name = (row.get("name") or "").strip()
        to_raw = (row.get("to") or "").split("T")[0]
        if not name or not to_raw:
            continue
        from_raw = (row.get("from") or "").split("T")[0]
        out.append(FormerName(
            name=name,
            from_date=date.fromisoformat(from_raw) if from_raw else None,
            to_date=date.fromisoformat(to_raw),
        ))
    return tuple(out)


def parse_registrant_history(data: dict[str, Any]) -> RegistrantHistory:
    """Current + former registrant names from one submissions payload."""
    return RegistrantHistory(
        current=(data.get("name") or "").strip(), former=parse_former_names(data))
