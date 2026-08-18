"""Schedule 13D/G beneficial ownership — the block, and the vocabulary defect it exists to avoid.

CORPUS FIRST. Every pin here was measured on the live EDGAR index for the 14 committed names
before it was written. The counts quoted in the docstrings are that measurement, not a guess.
"""

from __future__ import annotations

import datetime as dt

import pytest

from vinci.dossier.mechanical import (
    _OWNERSHIP_ACTIVIST,
    _OWNERSHIP_PASSIVE,
    _OWNERSHIP_SCAN_DAYS,
    _ownership_events,
    _ownership_line,
)
from vinci.dossier.schemas import SourceStatus
from vinci.edgar.client import Filing
from vinci.netcache import HttpError

REF = dt.date(2026, 8, 14)


def _f(form: str, on: dt.date) -> Filing:
    """Built from the REAL `Filing` type (#305) — a hand-rolled shape would dictate the
    production signature instead of testing it."""
    return Filing(cik="0000000000", form=form, filing_date=on,
                  accession=f"acc-{form}-{on.isoformat()}", items=[], primary_doc=None)


def test_both_edgar_vocabularies_are_counted() -> None:
    """THE DEFECT THIS BLOCK EXISTS FOR. EDGAR renamed the form types — `SC 13D` through 2024,
    `SCHEDULE 13D` after — and `recent_filings` matches EXACTLY, so a one-vocabulary list drops
    the other silently. Because the rename is chronological the dropped half is the RECENT half.

    Measured on the live fleet: an `SC 13`-only list sees 153 of 306 in-window filings. AORT's
    only activist filing is a `SCHEDULE 13D/A` and both of FUBO's are `SCHEDULE 13D`/`13D/A` —
    both names read "no activist interest" under the old vocabulary alone, which is a false CLEAN.

    MUTATION: drop either vocabulary from either tuple and this reddens."""
    for vocab in ("SC 13D", "SCHEDULE 13D", "SC 13D/A", "SCHEDULE 13D/A"):
        assert vocab in _OWNERSHIP_ACTIVIST, f"{vocab} missing — activist filings go unseen"
    for vocab in ("SC 13G", "SCHEDULE 13G", "SC 13G/A", "SCHEDULE 13G/A"):
        assert vocab in _OWNERSHIP_PASSIVE, f"{vocab} missing — passive filings go unseen"

    _, line = _ownership_line(
        [_f("SC 13D", REF - dt.timedelta(days=800)),
         _f("SCHEDULE 13D", REF - dt.timedelta(days=10))],
        REF)
    assert "Schedule 13D filings 2" in line, f"both vocabularies must reach ONE count: {line}"


def test_the_two_schedules_are_never_summed() -> None:
    """13D is intent-to-influence; 13G is the passive short form. Fleet-wide the split is 51
    activist against 430 passive, so merging them reports an index fund's re-weight as an
    activist stake. The counts stay in separate clauses."""
    _, line = _ownership_line(
        [_f("SC 13D", REF - dt.timedelta(days=5))]
        + [_f("SC 13G", REF - dt.timedelta(days=d)) for d in (6, 7, 8)],
        REF)
    assert "Schedule 13D filings 1" in line and "Schedule 13G filings 3" in line, line
    assert "4" not in line.split("—")[0], f"a summed 4 appeared: {line}"


def test_a_filing_after_the_as_of_never_enters_the_counts() -> None:
    """`recent_filings` takes only a `since` LOWER bound, so the upper bound is this block's job
    — the post-as-of leak class item 9 measured. A 13D filed the day after the record's as-of
    belongs to a later record."""
    _, line = _ownership_line([_f("SC 13D", REF + dt.timedelta(days=1))], REF)
    assert "no Schedule 13D/G" in line, f"a post-as-of filing leaked in: {line}"


def test_a_filing_older_than_the_window_never_enters_the_counts() -> None:
    older = REF - dt.timedelta(days=_OWNERSHIP_SCAN_DAYS + 1)
    _, line = _ownership_line([_f("SC 13D", older)], REF)
    assert "no Schedule 13D/G" in line, line


class _Boom:
    """An EdgarClient stand-in whose fetch fails, for the UNKNOWN leg."""

    def recent_filings(self, *a: object, **k: object) -> list[Filing]:
        raise HttpError("EDGAR 503")


class _Empty:
    def recent_filings(self, *a: object, **k: object) -> list[Filing]:
        return []


@pytest.mark.parametrize(
    ("client", "cik", "status"),
    [(_Empty(), "0000320193", SourceStatus.PRESENT),   # nothing on file — a FINDING
     (_Empty(), None, SourceStatus.UNKNOWN),           # no CIK — could not look
     (_Boom(), "0000320193", SourceStatus.UNKNOWN)],   # fetch failed — could not look
)
def test_none_in_window_and_unknown_never_render_alike(
    client: object, cik: str | None, status: SourceStatus) -> None:
    """PINNED AT THE WRAPPER, not the composer — the `dilution_pipeline` lesson. Its first cut
    pinned the empty state on the pure composer only, and a wrapper mutation collapsing the two
    states passed green. "No 13D on file" is a fact about the register; UNKNOWN means nobody
    looked, and a human reading them alike would treat an unread register as a clean one."""
    oe = _ownership_events(client, cik, REF)  # type: ignore[arg-type]
    assert oe.line.status is status
    assert oe.filings == []


class _MechStub:
    """Duck-typed mechanical layer — only the field the render helper reads."""

    def __init__(self, oe: object) -> None:
        self.ownership_events = oe


def test_the_label_names_the_schedule_and_claims_no_ownership() -> None:
    """REVIEW OF #470. The label read "Beneficial ownership" over a line reading
    "activist/control", so a 13D/A disclosing an EXIT rendered as an activist stake. Both
    claims came from the form type alone, which cannot support either. The label names the
    SCHEDULE and the activity; the reader opens the accession for what it says."""
    from vinci.dossier.render import _ownership_events_lines
    from vinci.dossier.schemas import OwnershipEvents, OwnershipFiling, Sourced

    oe = OwnershipEvents(
        filings=[OwnershipFiling(form="SCHEDULE 13D/A", filing_date="2026-07-08",
                                 accession="0001403161-26-000001")],
        window_days=_OWNERSHIP_SCAN_DAYS,
        line=Sourced.present("Schedule 13D filings 9 (SC 13D/SCHEDULE 13D/A, last 2026-07-08)",
                             source_ref="EDGAR filing index"))
    lines = _ownership_events_lines(_MechStub(oe))  # type: ignore[arg-type]
    assert len(lines) == 1
    assert "Schedule 13D/G filing activity" in lines[0], (
        f"the label stopped naming the schedule, or re-asserted ownership: {lines[0]}")
    assert "ownership" not in lines[0].lower(), (
        f"the label claims ownership again — the index cannot support it: {lines[0]}")


def test_the_web_renderer_shows_ownership_too() -> None:
    """THE #457 P1 LESSON, HONOURED AT WRITE TIME. The md renderer grew `dilution_pipeline` and
    the JS twin did not, so the block printed in the PDF and was SILENTLY ABSENT from the
    deployed page — the surface the human actually reads. This pin ships with the block.

    DRIVEN THROUGH THE REAL `renderDossier` ON A REAL COMMITTED DOSSIER: the block is reachable
    only inside `capitalAllocation`, so a hand-built bare record renders nothing and would pass
    against a still-broken twin. THE ABSENT CASE IS CONSTRUCTED, not borrowed from whichever
    dossier happens to lack the field today — that borrowing is what reddened #457's pin on a
    name being rebuilt rather than on the renderer changing."""
    import json as _json
    import pathlib
    import shutil
    import subprocess
    import tempfile

    if not shutil.which("node"):
        pytest.skip("node not available")
    root = pathlib.Path(__file__).resolve().parents[1]
    committed = sorted((root / "data" / "dossiers").glob("*/dossier.json"))
    if not committed:
        pytest.skip("no committed dossiers in this checkout")
    doc = _json.loads(committed[0].read_text())

    dj = (root / "frontend" / "views" / "shared" / "dossier.js").resolve().as_uri()
    line = ("Schedule 13D filings 9 (SC 13D/SCHEDULE 13D/A, last 2026-07-08) · "
            "Schedule 13G filings 12 (SC 13G, last 2026-08-13) — 3y window to 2026-08-14")
    events = {"filings": [], "window_days": _OWNERSHIP_SCAN_DAYS,
              "line": {"value": line, "source_ref": "EDGAR filing index",
                       "status": "present", "note": None}}
    with tempfile.TemporaryDirectory() as td:
        # TO DISK, NOT argv — a full committed dossier in `node -e` blows Linux's ARG_MAX.
        doc_path = pathlib.Path(td) / "doc.json"
        doc_path.write_text(_json.dumps(doc))
        bare = {**doc, "mechanical": {k: v for k, v in doc["mechanical"].items()
                                      if k != "ownership_events"}}
        bare_path = pathlib.Path(td) / "bare.json"
        bare_path.write_text(_json.dumps(bare))
        oe_path = pathlib.Path(td) / "oe.json"
        oe_path.write_text(_json.dumps(events))
        driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
const {{ readFileSync }} = await import("node:fs");
const {{ renderDossier }} = await import("{dj}");
const doc = JSON.parse(readFileSync({_json.dumps(str(doc_path))}, "utf8"));
const oe = JSON.parse(readFileSync({_json.dumps(str(oe_path))}, "utf8"));
const bare = JSON.parse(readFileSync({_json.dumps(str(bare_path))}, "utf8"));
const out = {{}};
out.absent = renderDossier(bare, null);
out.present = renderDossier(
  {{ ...doc, mechanical: {{ ...doc.mechanical, ownership_events: oe }} }}, null);
console.log(JSON.stringify(out));
"""
        res = subprocess.run(["node", "--input-type=module", "-e", driver],
                             capture_output=True, text=True)
    assert res.returncode == 0, res.stderr[-800:]
    got = _json.loads(res.stdout)
    assert "Schedule 13D/G" in got["present"], (
        "populated ownership events are invisible on the deployed page — PDF only, which is the "
        "exact #457 defect this pin exists to prevent recurring")
    assert "Schedule 13D/G" not in got["absent"], (
        "a dossier without the field renders the block anyway — the back-compat path is broken")


def test_the_block_reaches_the_rendered_page_not_just_the_helper() -> None:
    """PIN THE ARTIFACT, NOT THE HELPER. `test_the_rendered_line_separates_activist_from_passive`
    calls `_ownership_events_lines` directly, so deleting its CALL SITE in `_capital_allocation`
    leaves that pin green while the block vanishes from every PDF — verified: the call-site
    deletion reddened nothing until this test existed.

    Drives the REAL `render_markdown` over a REAL committed dossier, and asserts the
    PHRASING-INDEPENDENT invariant (the label is present) rather than the composed line, which is
    a living artifact's weather."""
    import json as _json
    import pathlib

    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier

    root = pathlib.Path(__file__).resolve().parents[1]
    committed = sorted((root / "data" / "dossiers").glob("*/dossier.json"))
    if not committed:
        pytest.skip("no committed dossiers in this checkout")
    doc = _json.loads(committed[0].read_text())
    doc["mechanical"]["ownership_events"] = {
        "filings": [], "window_days": _OWNERSHIP_SCAN_DAYS,
        "line": {"value": "no 13D on file · Schedule 13G filings 21 (SC 13G, last 2026-08-14)"
                          " — 3y window to 2026-08-14",
                 "source_ref": "EDGAR filing index", "status": "present", "note": None}}
    md = render_markdown(Dossier.model_validate(doc))
    assert "Schedule 13D/G filing activity" in md, (
        "the block is absent from the rendered page — the call site is gone even though the "
        "helper still works")


class _Attributed:
    """An EdgarClient stand-in: returns two filings and a header index that attributes ONE of them
    to another issuer — the real UBER/Grab shape, built from the REAL `Filing` type."""

    def __init__(self, subject: str, foreign_acc: str) -> None:
        self._subject, self._foreign = subject, foreign_acc
        self._http = self

    def recent_filings(self, *a: object, **k: object) -> list[Filing]:
        return [_f2("SCHEDULE 13D/A", dt.date(2026, 7, 8), self._foreign),
                _f2("SCHEDULE 13D", dt.date(2026, 6, 1), "0000000000-26-000001")]

    def get_text(self, url: str, **k: object) -> str:
        cik = "1855612" if self._foreign.replace("-", "") in url else self._subject
        return f"SUBJECT COMPANY:\n  COMPANY DATA:\n    CENTRAL INDEX KEY: {cik.zfill(10)}\n"


def _f2(form: str, on: dt.date, acc: str) -> Filing:
    return Filing(cik="0001543151", form=form, filing_date=on, accession=acc,
                  items=[], primary_doc=None)


def test_a_filing_this_company_made_about_another_issuer_is_not_counted() -> None:
    """THE #470 REVIEW FINDING, AND THE #458 DEFECT REBUILT. The submissions index is NOT
    issuer-only: it also returns filings where the company is the REPORTING PERSON on somebody
    else's stock. UBER's `SCHEDULE 13D/A` 2026-07-08 (`0001552781-26-000379`) has issuer **Grab
    Holdings**; counted as inbound it said nine parties were accumulating UBER when Uber was
    disclosing stakes it HOLDS. Direction inverted, from real data.

    Attribution moved UBER from "9 activist filings" to "no 13D on file" on the live corpus.

    MUTATION: drop the `subject == str(int(cik))` test and this reddens."""
    client = _Attributed("1543151", "0001552781-26-000379")
    oe = _ownership_events(client, "1543151", dt.date(2026, 8, 14))  # type: ignore[arg-type]
    assert len(oe.filings) == 1, (
        f"a filing about another issuer was counted as inbound: {[f.form for f in oe.filings]}")
    assert oe.filings[0].accession == "0000000000-26-000001"
    assert "13D filings 1" in oe.line.value, oe.line.value


def test_an_unreadable_header_is_excluded_and_reported_never_silently_kept() -> None:
    """UNATTRIBUTABLE IS NOT "OURS". Defaulting a failed header read to keep would restore the
    inverted-direction defect silently, which is worse than the shortfall — so the filing leaves
    the counts AND the line says how many did."""

    class _NoHeader(_Attributed):
        def get_text(self, url: str, **k: object) -> str:
            raise HttpError("EDGAR 403")

    oe = _ownership_events(_NoHeader("1543151", "x-26-1"), "1543151",  # type: ignore[arg-type]
                           dt.date(2026, 8, 14))
    assert oe.filings == []
    assert "not attributable" in oe.line.value, oe.line.value
    assert "2 filing(s)" in oe.line.value, oe.line.value
