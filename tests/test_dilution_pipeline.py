"""FORWARD dilution capacity — the registered-offering pipeline from the EDGAR filing index.

THE GAP THIS CLOSES (audit 2026-08-13, the BioCatch/M&A seam applied forward). The stack measured
REALIZED dilution (share-count trend) and buybacks, but nothing watched the PIPELINE — an effective
shelf, prospectus supplements drawing on it, a fresh S-1. For a drawdown name, issuance into the
drawdown is the recovery-killer, and it is announced in exactly the filings nothing fetched:
S-3/F-3 shelfs, 424B supplements, S-1/F-1, S-8. Verified zero references anywhere before this.

MEASURED ON THE LIVE FLEET before these tests were written (window-bounded at 2026-08-12):
FUBO — 2 shelfs + 3 supplements (424B5/424B7, the equity machinery) + 3 S-8; MVST — S-3 + 424B5;
VRRM — nothing on file at all; BRBR/NCNO/SMPL/VITL — S-8 only. And the case that sets the LABEL:
**V's six supplements are 424B2/424B3 BOND takedowns** — the index cannot distinguish an ATM draw
from a debt deal, so the rendered label says "equity/debt not distinguished" rather than asserting
dilution for what may be bonds.

ASSEMBLE-AND-CITE ONLY: counts, forms and dates. Which pipeline is a risk is the human's call.
"""
from __future__ import annotations

from datetime import date

from vinci.dossier.mechanical import (
    _DILUTION_SCAN_DAYS,
    _dilution_line,
    _dilution_pipeline,
)
from vinci.edgar.client import Filing


def _f(form: str, d: str, acc: str = "0000000000-26-000001") -> Filing:
    """A REAL `Filing` (the type the submissions feed yields) — never a hand-rolled dict."""
    return Filing(cik="0000000000", form=form, filing_date=date.fromisoformat(d),
                  accession=acc, items=[], primary_doc=None)


REF = date(2026, 8, 12)


def test_the_fubo_shape_counts_by_group_and_keeps_s8_out_of_the_headline() -> None:
    """THE POSITIVE PIN, on the live FUBO shape: shelfs and supplements headline; S-8 is REAL
    dilution but routine, so it is counted on its own tail and never mixed into the headline —
    a reader scanning for the ATM machinery must not have to subtract employee plans first."""
    filings = [
        _f("S-3ASR", "2026-01-23"), _f("S-3ASR", "2024-02-01"),
        _f("424B5", "2026-01-23"), _f("424B7", "2025-06-11"), _f("424B5", "2024-03-09"),
        _f("S-8", "2026-08-05"), _f("S-8", "2025-08-01"), _f("S-8", "2024-08-02"),
    ]
    inwin, line = _dilution_line(filings, REF)
    assert len(inwin) == 8
    assert "shelf registrations 2 (S-3ASR, last 2026-01-23)" in line
    assert "prospectus supplements 3 (424B5/424B7, last 2026-01-23)" in line
    assert "employee-plan (S-8) 3" in line and "routine" in line
    head = line.split("employee-plan")[0]
    assert "S-8" not in head, "S-8 leaked into the headline groups"
    assert "3y window to 2026-08-12" in line, "the window must be stated on the face of the value"


def test_a_filing_after_the_as_of_never_enters_the_counts() -> None:
    """THE AS-OF BOUND, pinned as its own case — the post-as-of leak class item 9 measured (NFLX
    58 / UBER 91 dates past their own reference_date). `recent_filings` has only a lower bound, so
    the upper bound lives in `_dilution_line` and this is the pin that keeps it there."""
    filings = [_f("S-3ASR", "2026-01-23"), _f("424B5", "2026-08-13")]  # one day past the as-of
    inwin, line = _dilution_line(filings, REF)
    assert [f.form for f in inwin] == ["S-3ASR"], "a post-as-of filing entered the window"
    assert "prospectus supplements" not in line, (
        "a 424B5 filed AFTER the record's as-of is being counted — lookahead past the record")


def test_nothing_on_file_is_a_stated_finding_not_silence() -> None:
    """THE VRRM SHAPE. An empty register is decision-relevant (no standing capacity) and must
    print as a stated fact naming its window — never as a blank, and never as UNKNOWN."""
    inwin, line = _dilution_line([], REF)
    assert inwin == []
    assert line == ("no registration statements or prospectus supplements on file in the "
                    "3y to 2026-08-12")


def test_s8_only_names_state_the_absence_of_the_headline_groups() -> None:
    """THE BRBR/NCNO SHAPE — routine employee plans and nothing else. The headline must say the
    shelf/supplement/fresh groups are empty rather than letting the S-8 count read as pipeline."""
    _, line = _dilution_line([_f("S-8", "2026-03-31")], REF)
    assert line.startswith("no shelf/supplement/fresh registration"), line
    assert "employee-plan (S-8) 1" in line and "routine" in line


def test_a_failed_read_is_unknown_and_never_renders_like_none_on_file() -> None:
    """TWO STATES THAT MUST NOT RENDER ALIKE: "the register is empty" (a finding, PRESENT) vs
    "the register could not be read" (no CIK / fetch failure, UNKNOWN).

    BOTH STATES GO THROUGH THE WRAPPER, deliberately. The first cut asserted the empty state on
    the pure composer only, and a mutation that made the WRAPPER return UNKNOWN for an empty
    register passed green — the pure half stayed honest while the shipped object lied. The stub
    drives the same path production takes (pin the artifact, not the helper)."""
    dp = _dilution_pipeline(None, None, REF)  # type: ignore[arg-type]  # edgar unused on this path
    assert dp.line.value is None and dp.filings == []
    assert "no CIK" in (dp.line.note or "")

    class _EmptyIndex:
        """An EdgarClient whose submissions feed has no matching filings — the VRRM shape."""

        def recent_filings(self, cik, *, forms, since):  # noqa: ANN001, ANN201
            return []

    empty = _dilution_pipeline(_EmptyIndex(), "0000000000", REF)  # type: ignore[arg-type]
    assert empty.line.value is not None, (
        "an EMPTY register came back UNKNOWN — the finding and the failed read collapsed into "
        "one state, and a reader cannot tell 'no capacity on file' from 'could not check'")
    assert "no registration statements" in empty.line.value
    assert (dp.line.note or "") != empty.line.value


def test_committed_dossiers_round_trip_with_the_field_absent() -> None:
    """BACK-COMPAT: every committed dossier predates the field; it must parse (defaulting None)
    and render byte-identically — the pages change on their next assembly, not on this merge."""
    import pathlib

    import pytest

    from vinci.dossier.render import _dilution_pipeline_lines
    from vinci.dossier.schemas import Dossier

    committed = sorted(pathlib.Path("data/dossiers").glob("*/dossier.json"))
    if not committed:
        pytest.skip("no committed dossiers in this checkout")
    d = Dossier.model_validate_json(committed[0].read_text())
    assert d.mechanical.dilution_pipeline is None, (
        "a committed dossier parsed with a NON-None pipeline — the default is wrong and old "
        "records are inventing a block they never carried")
    assert _dilution_pipeline_lines(d.mechanical) == [], (
        "a None field rendered lines — committed pages would change on merge, not on assembly")
    # and the md really does not carry the label yet
    md = committed[0].with_name("dossier.md").read_text()
    assert "Registered offering pipeline" not in md


def test_the_rendered_line_carries_the_equity_debt_disclaimer() -> None:
    """THE LABEL IS THE LIMITATION. V's six supplements are BOND takedowns (424B2/424B3) and the
    index cannot tell them from an ATM draw — a label reading "dilution" would assert equity
    issuance the source cannot support. The disclaimer lives in the LABEL so it prints on every
    name, not in a note that curates away."""
    from vinci.dossier.render import _dilution_pipeline_lines
    from vinci.dossier.schemas import DilutionPipeline, RegistrationFiling, Sourced

    dp = DilutionPipeline(
        filings=[RegistrationFiling(form="424B2", filing_date="2026-04-13",
                                    accession="0001403161-26-000001")],
        window_days=_DILUTION_SCAN_DAYS,
        line=Sourced.present("prospectus supplements 1 (424B2, last 2026-04-13)",
                             source_ref="EDGAR filing index"))
    lines = _dilution_pipeline_lines(_MechStub(dp))  # type: ignore[arg-type]
    assert len(lines) == 1
    assert "equity/debt not distinguished" in lines[0], (
        "the disclaimer left the label — a 424B2 bond deal now reads as dilution")


class _MechStub:
    """Duck-typed mechanical layer for the render helper — only the field it reads."""

    def __init__(self, dp) -> None:  # noqa: ANN001
        self.dilution_pipeline = dp


# ─── the deployed twin (review of #457) ─────────────────────────────────────────────────────────
def test_the_web_renderer_shows_the_pipeline_too() -> None:
    """REVIEW FINDING (#457) — the md renderer grew this block and the JS twin did not.

    The site renders `dossier.json` through `frontend/views/shared/dossier.js`, and its
    `capitalAllocation()` never read `dilution_pipeline`. A populated pipeline therefore printed in
    the PDF and was **silently absent from the deployed page** — the surface the human actually
    reads. The parity is explicit in that file (its own comment cites `render._capital_allocation`)
    and it broke the moment one side moved alone.

    DRIVEN THROUGH THE REAL `renderDossier` ON A REAL COMMITTED DOSSIER, because the block is
    reachable only inside `financialSnapshot()` — which returns early without a financial summary.
    A hand-built bare record renders nothing and would have "passed" against a still-broken twin;
    the committed record is the only fixture that reaches the code under test.
    """
    import json as _json
    import pathlib
    import shutil
    import subprocess

    import pytest

    if not shutil.which("node"):
        pytest.skip("node not available")
    root = pathlib.Path(__file__).resolve().parents[1]
    committed = sorted((root / "data" / "dossiers").glob("*/dossier.json"))
    if not committed:
        pytest.skip("no committed dossiers in this checkout")
    doc = _json.loads(committed[0].read_text())

    dj = (root / "frontend" / "views" / "shared" / "dossier.js").resolve().as_uri()
    line = "shelf registrations 1 (S-3ASR, last 2026-01-23) — 3y window to 2026-08-12"
    pipeline = {"filings": [], "window_days": _DILUTION_SCAN_DAYS,
                "line": {"value": line, "source_ref": "EDGAR filing index",
                         "status": "present", "note": None}}
    # THE DOSSIER GOES TO DISK, NOT INTO argv (CI fix). Embedding a full committed dossier in
    # `node -e` blew Linux's ARG_MAX — `OSError: [Errno 7] Argument list too long` — so this test
    # reddened every gate run on main from #457 while passing locally on macOS, whose limit is
    # far higher. The driver reads the JSON with `fs.readFileSync` instead.
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        doc_path = pathlib.Path(td) / "doc.json"
        doc_path.write_text(_json.dumps(doc))
        pipe_path = pathlib.Path(td) / "dp.json"
        pipe_path.write_text(_json.dumps(pipeline))
        driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
const {{ readFileSync }} = await import("node:fs");
const {{ renderDossier }} = await import("{dj}");
const doc = JSON.parse(readFileSync({_json.dumps(str(doc_path))}, "utf8"));
const dp = JSON.parse(readFileSync({_json.dumps(str(pipe_path))}, "utf8"));
const out = {{}};
out.absent = renderDossier(doc, null);
out.present = renderDossier(
  {{ ...doc, mechanical: {{ ...doc.mechanical, dilution_pipeline: dp }} }}, null);
console.log(JSON.stringify(out));
"""
        res = subprocess.run(["node", "--input-type=module", "-e", driver],
                             capture_output=True, text=True)
    assert res.returncode == 0, res.stderr[-800:]
    got = _json.loads(res.stdout)

    assert "Registered offering pipeline" in got["present"], (
        "a populated pipeline is invisible on the deployed page — it renders in the PDF only")
    assert "equity/debt not distinguished" in got["present"], (
        "the web label dropped the disclaimer the md label carries — the two surfaces disagree "
        "about what the number means")
    assert "shelf registrations 1" in got["present"], "the value itself never reached the HTML"
    assert "Registered offering pipeline" not in got["absent"], (
        "a dossier without the field rendered the block — committed pages would change on merge, "
        "not on their next assembly")


def test_the_form_taxonomy_covers_the_registration_families() -> None:
    """THE ALLOWLIST IS EXACT-MATCH, so a form missing from it is invisible BEFORE `_dilution_line`
    runs — and the failure direction is a FALSE CLEAN register, not an under-count (review finding,
    #457). Two gaps were found: MEF variants (Rule 462(b), adding securities to an already-effective
    registration) and **S-4 — measured and PRESENT: V carries five in-window**, shares issued to a
    target's holders diluting exactly like a secondary.

    Pins the FAMILIES rather than a frozen list, so adding `424B9` is fine and dropping the whole
    merger group is not."""
    from vinci.dossier.mechanical import (
        _DILUTION_EMPLOYEE,
        _DILUTION_FRESH,
        _DILUTION_MERGER,
        _DILUTION_SHELF,
        _DILUTION_SUPPLEMENT,
    )

    every = set(_DILUTION_SHELF + _DILUTION_SUPPLEMENT + _DILUTION_FRESH
                + _DILUTION_MERGER + _DILUTION_EMPLOYEE)
    for form in ("S-3", "S-3ASR", "S-3MEF", "F-3", "F-3MEF",       # shelf + 462(b) top-ups
                 "424B2", "424B5", "424B7",                        # draws
                 "S-1", "S-1MEF", "F-1",                           # fresh
                 "S-4", "S-4/A", "F-4",                            # acquisition-funded
                 "S-8"):                                           # employee plans
        assert form in every, (
            f"{form!r} is outside the taxonomy, so `recent_filings` drops it before the composer "
            f"sees it — a name whose only registered capacity is a {form} reports 'no "
            f"registration statements on file', a FALSE CLEAN")

    # the groups stay DISJOINT — a form counted twice would double the headline
    groups = (_DILUTION_SHELF, _DILUTION_SUPPLEMENT, _DILUTION_FRESH,
              _DILUTION_MERGER, _DILUTION_EMPLOYEE)
    seen: set[str] = set()
    for g in groups:
        assert not (seen & set(g)), f"a form appears in two groups: {sorted(seen & set(g))}"
        seen |= set(g)


def test_an_s4_only_register_is_not_reported_as_clean() -> None:
    """THE V SHAPE, as a behavioural pin rather than a membership check: five S-4/S-4A in-window,
    and before the taxonomy fix the same register composed as 'no registration statements … on
    file'. That wording on a name registering acquisition shares is the false clean this guards."""
    _, line = _dilution_line([_f("S-4", "2026-03-05"), _f("S-4/A", "2026-04-06")], REF)
    assert "no registration statements" not in line, (
        "a register holding two S-4s reported as empty — the false-clean direction")
    assert "merger registrations 2 (S-4/S-4/A, last 2026-04-06)" in line
