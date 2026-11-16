"""(STATE row 63) The E5 loop writes what it did with each located exhibit, and the page says it.

Since #1073 the covenant block's not-extracted line states NO cause. The reason lived only in an
`(E5)` QA-flag string, which a page may not parse, so the line could not say whether an exhibit
was refused, past the cost bound or never fetched. On the 16 pages #1073 measured (main
6652a242), E5 had refused 22 of the 29 exhibits the line named as no debt agreement, 7 were cost
bound and 0 had failed to fetch.

`extract_covenant_terms` now writes one `CovenantExhibitOutcome` per located exhibit, at the branch
of its loop that decides it. The outcomes are attached beside `covenant_term_rows`, and both
renderers print each unextracted exhibit's own cause from them. A page without the field (every
committed page until its next paid re-assembly) keeps the neutral line, byte for byte.

THE LOOP'S BRANCHES, read off the code (`covenant_extract.extract_covenant_terms`), one outcome
each: past the cost bound → `cost_bound`; no text → `fetch_failed`; a heading that is no debt
contract → `not_debt_agreement`; over the size limit → `too_large`; an `LlmError` →
`llm_error`; a call that returns no term rows → `no_terms_returned`; else `extracted`.

THE FIXTURES ARE THE REAL TYPE. The branch pins run the real loop over BURL's committed pointer
rows (`tests/fixtures/covenant_unextracted/BURL.json`, frozen by #1073), stubbed only at the
fetch and model boundary. The render pins host each frozen block in its real committed dossier
with a frozen outcome list (`tests/fixtures/covenant_exhibit_outcomes/<T>.json`), which the
preview of this change wrote through the same real loop, reading each exhibit from the EDGAR
cache and stubbing only the model (the fixture's README says how).
"""

from __future__ import annotations

import html
import json
import pathlib
import re
import shutil
import subprocess
import typing

import pytest

from vinci.dossier import covenant_extract as ce
from vinci.dossier.schemas import (
    CapitalStructure,
    CovenantExhibitOutcomeKind,
    CovenantPointer,
    Dossier,
    Sourced,
    SourceStatus,
    dossier_json,
)
from vinci.graph.llm import LlmError

ROOT = pathlib.Path(__file__).resolve().parents[1]
UNEXTRACTED = ROOT / "tests" / "fixtures" / "covenant_unextracted"
OUTCOMES = ROOT / "tests" / "fixtures" / "covenant_exhibit_outcomes"
JS = ROOT / "frontend" / "views" / "shared" / "dossier.js"

_ALL_KINDS = set(typing.get_args(CovenantExhibitOutcomeKind))
_DEBT = "CREDIT AGREEMENT dated as of March 16, 2018 among the Borrower and the Lenders."
_LEASE = "LEASE AGREEMENT dated as of June 1, 2021 between the Landlord and the Tenant."

#: BURL's seven located exhibits, in the order the loop takes them (`_core_agreement_exhibits`),
#: and the branch each is driven down: the stub serves the text, the model answers.
_PLAN: list[tuple[str, str, CovenantExhibitOutcomeKind]] = [
    ("0001193125-20-109457", "d883886dex101.htm", "extracted"),
    ("0001193125-25-168007", "d946952dex101.htm", "fetch_failed"),
    ("0001564590-18-016500", "burl-ex101_6.htm", "too_large"),
    ("0001193125-26-116001", "burl-ex10_39.htm", "not_debt_agreement"),
    ("0001193125-21-364998", "d275638dex101.htm", "llm_error"),
    ("0001193125-22-200058", "d393601dex101.htm", "no_terms_returned"),
    ("0001193125-14-313404", "d772516dex101.htm", "cost_bound"),
]
_TEXT: dict[str, str | None] = {
    "d883886dex101.htm": _DEBT, "d946952dex101.htm": None, "burl-ex101_6.htm": _DEBT + " x" * 400,
    "burl-ex10_39.htm": _LEASE, "d275638dex101.htm": _DEBT, "d393601dex101.htm": _DEBT,
    "d772516dex101.htm": _DEBT,
}


class _Http:
    """Serves each exhibit's planned text; a planned None is a failed fetch."""

    def __init__(self, text: dict[str, str | None]) -> None:
        self.text = text
        self.got: list[str] = []

    def get_text(self, url: str, **_: typing.Any) -> str:
        name = url.rsplit("/", 1)[1]
        self.got.append(name)
        body = self.text.get(name, _DEBT)
        if body is None:
            raise OSError(f"stub: {url} unavailable")
        return body


class _Llm:
    """The model boundary: an error, no rows, or one row, by the exhibit the prompt names."""

    def __init__(self, error: frozenset[str] = frozenset(),
                 empty: frozenset[str] = frozenset()) -> None:
        self.error, self.empty = error, empty

    def extract(self, *, system: str, user: str, tool: dict[str, typing.Any],
                cache: bool = False) -> dict[str, typing.Any]:
        m = re.search(r"Exhibit: .*? · (\S+?)\. Extract", user)
        assert m is not None, user[:200]
        if m.group(1) in self.error:
            raise LlmError("stub: the call failed")
        if m.group(1) in self.empty:
            return {"terms": []}
        return {"terms": [{"name": "Maturity date", "present": False}]}


def _burl() -> CapitalStructure:
    raw = json.loads((UNEXTRACTED / "BURL.json").read_text())
    return CapitalStructure.model_validate(raw["capital_structure"])


def _run_burl(monkeypatch: pytest.MonkeyPatch) -> tuple[typing.Any, ...]:
    monkeypatch.setattr(ce, "_MAX_EXHIBITS", 2)  # two calls, then the cost bound
    monkeypatch.setattr(ce, "_MAX_EXHIBIT_CHARS", 400)
    llm = _Llm(error=frozenset({"d275638dex101.htm"}), empty=frozenset({"d393601dex101.htm"}))
    return ce.extract_covenant_terms(
        _burl(), llm=llm, http=_Http(_TEXT), cik="0001579298",  # type: ignore[arg-type]
        ticker="BURL", name="Burlington Stores, Inc.")


# --- the field: one outcome per located exhibit, written at each branch --------------------------


def test_the_plan_is_the_order_the_loop_takes_burls_exhibits() -> None:
    """(precondition) The stub drives each exhibit down a planned branch by its filename, so the
    plan must be BURL's real target list in the loop's own order."""
    cs = _burl()
    assert cs.covenant_pointer_rows is not None and cs.covenant_pointer_rows.value
    got = [(r.accession, f) for r, f in ce._core_agreement_exhibits(cs.covenant_pointer_rows.value)]
    assert got == [(a, f) for a, f, _ in _PLAN]
    assert {k for _, _, k in _PLAN} == _ALL_KINDS, "the plan drives every branch once"


def test_every_branch_of_the_loop_writes_its_outcome(monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) One run of the real loop down all seven branches: each exhibit's outcome is the branch
    it took, with its accession, filename and the pointer's family, and the heading E5 read where
    it read one."""
    _rows, _summary, _flags, _log, outcomes = _run_burl(monkeypatch)
    assert isinstance(outcomes, Sourced) and outcomes.status is SourceStatus.PRESENT
    assert outcomes.source_ref
    got = list(outcomes.value or [])
    assert [(o.accession, o.filename, o.outcome) for o in got] == _PLAN
    family = {r.accession: r.family for r in _burl().covenant_pointer_rows.value or []}  # type: ignore[union-attr]
    assert all(o.family == family[o.accession] for o in got)
    title = {o.outcome: o.declared_title for o in got}
    # never read: no heading
    assert title["cost_bound"] is None and title["fetch_failed"] is None
    # read: the heading `agreement_title` takes from it
    assert title["not_debt_agreement"] == ce.agreement_title(_LEASE) == "LEASE AGREEMENT"
    for k in ("extracted", "too_large", "llm_error", "no_terms_returned"):
        assert title[k] == ce.agreement_title(_DEBT) == "CREDIT AGREEMENT", k


def test_the_outcomes_are_the_located_exhibits_each_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) None dropped, none counted twice: the outcomes, as a list, are exactly the exhibits the
    loop targets."""
    *_, outcomes = _run_burl(monkeypatch)
    cs = _burl()
    assert cs.covenant_pointer_rows is not None
    targets = [(r.accession, f) for r, f in ce._core_agreement_exhibits(
        list(cs.covenant_pointer_rows.value or []))]
    assert [(o.accession, o.filename) for o in outcomes.value] == targets


def test_a_no_terms_answer_is_not_an_extraction(monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) A call that returns no rows writes `no_terms_returned`, never `extracted`, and still
    spends one of the cost bound's calls, as it did before the field."""
    *_, outcomes = _run_burl(monkeypatch)
    kinds = [o.outcome for o in outcomes.value]
    assert kinds.count("extracted") == 1 and kinds.count("no_terms_returned") == 1
    assert kinds[-1] == "cost_bound", "two calls spent the bound of two"


def test_every_committed_page_gets_one_outcome_per_located_exhibit() -> None:
    """(+ · living corpus) Over every committed page with pointer rows, the real loop writes one
    outcome per exhibit it targets, in order, and every located pointer accession has one. The stub
    serves a debt heading for each exhibit and the model one row, so a page with more than four
    exhibits also runs the cost bound."""
    pages = exhibits = 0
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        raw = json.loads(p.read_text()).get("mechanical", {}).get("capital_structure")
        cs = CapitalStructure.model_validate(raw) if raw else None
        if cs is None or cs.covenant_pointer_rows is None or not cs.covenant_pointer_rows.value:
            continue
        ptrs = list(cs.covenant_pointer_rows.value)
        *_, outcomes = ce.extract_covenant_terms(
            cs, llm=_Llm(), http=_Http({}), cik="0000000001",  # type: ignore[arg-type]
            ticker=p.parent.name, name=p.parent.name)
        targets = [(r.accession, f) for r, f in ce._core_agreement_exhibits(ptrs)]
        got = [(o.accession, o.filename) for o in (outcomes.value if outcomes else [])]
        assert got == targets, p.parent.name
        assert {a for a, _ in got} == {r.accession for r in ptrs if r.accession}, p.parent.name
        pages += 1
        exhibits += len(got)
    assert pages and exhibits > pages, (pages, exhibits)


def test_no_located_exhibit_writes_no_field() -> None:
    """(−) Nothing located, nothing written: no pointer rows, or pointers with no accession (an
    aggregate line), leave the field unset, as the term rows are."""
    base = _burl()
    notes = [CovenantPointer(family="Operating Lease Liabilities", filing="—", filing_date="",
                             accession="", exhibits=[], note="no contract-level filing expected")]
    for cs in (base.model_copy(update={"covenant_pointer_rows": None}),
               base.model_copy(update={"covenant_pointer_rows": Sourced.present(
                   notes, source_ref="efts")})):
        out = ce.extract_covenant_terms(cs, llm=_Llm(), http=_Http({}),  # type: ignore[arg-type]
                                        cik="0001579298", ticker="BURL", name="Burlington")
        assert out[0] is None and out[4] is None


# --- where the field goes: after the synthesis, beside the term rows, absent until built ---------


def test_assembly_attaches_the_outcomes_after_the_synthesis_has_read_its_layer() -> None:
    """(+) `assemble_one` attaches the outcomes `extract_covenant_terms` returns, and only after
    `synthesize` is called, as it attaches the term rows: the synthesis never reads them, so the
    request it sends is the one every committed page was built with."""
    import ast

    tree = ast.parse((ROOT / "vinci" / "dossier" / "assemble.py").read_text())
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "assemble_one")
    unpacked = next(n for n in ast.walk(fn) if isinstance(n, ast.Assign)
                    and isinstance(n.value, ast.Call)
                    and ast.unparse(n.value.func) == "extract_covenant_terms")
    target = unpacked.targets[0]
    assert isinstance(target, ast.Tuple) and len(target.elts) == 5
    name = ast.unparse(target.elts[4])
    synth = min(n.lineno for n in ast.walk(fn) if isinstance(n, ast.Call)
                and ast.unparse(n.func) == "synthesize")
    attached = [n.lineno for n in ast.walk(fn) if isinstance(n, ast.Dict)
                and any(isinstance(k, ast.Constant) and k.value == "covenant_exhibit_outcomes"
                        and ast.unparse(v) == name for k, v in zip(n.keys, n.values, strict=True))]
    assert attached and min(attached) > synth, (attached, synth)


def _with_outcomes(page: dict[str, typing.Any], outcomes: list[dict[str, typing.Any]]
                   ) -> dict[str, typing.Any]:
    page = json.loads(json.dumps(page))
    page["mechanical"]["capital_structure"]["covenant_exhibit_outcomes"] = {
        "value": outcomes, "source_ref": ce.OUTCOMES_SOURCE_REF, "status": "present"}
    return page


_ONE = [{"accession": "0001193125-26-116001", "filename": "burl-ex10_39.htm",
         "family": "material contracts (10-K exhibit index)", "outcome": "not_debt_agreement"}]


def test_the_field_is_absent_until_built_and_written_once_built() -> None:
    """(− / +) The one serializer writes no key on a page without the field, so every committed
    page round-trips byte for byte, and writes it on a page that has it."""
    p = ROOT / "data" / "dossiers" / "BURL" / "dossier.json"
    if not p.exists():
        pytest.skip("no committed BURL dossier")
    text = p.read_text()
    assert "covenant_exhibit_outcomes" not in text
    assert dossier_json(Dossier.model_validate_json(text)) == text
    built = Dossier.model_validate(_with_outcomes(json.loads(text), _ONE))
    written = json.loads(dossier_json(built))["mechanical"]["capital_structure"]
    assert written["covenant_exhibit_outcomes"]["value"][0]["outcome"] == "not_debt_agreement"
    assert "declared_title" in written["covenant_exhibit_outcomes"]["value"][0]


def test_the_synthesis_input_a_replay_rebuilds_carries_no_outcomes() -> None:
    """(+) Both rebuilds of the layer `synthesize` received (the replay harness and the
    confirmation's) clear the outcomes, as they clear the term rows: a page built with the field
    rebuilds the same request as the same page without it."""
    from tests.stripped_pages import replayable
    from vinci.dossier.confirmation import layer_as_synthesized
    from vinci.evals.capture_child import pre_synthesis_mech

    p = ROOT / "data" / "dossiers" / "BURL" / "dossier.json"
    if not p.exists():
        pytest.skip("no committed BURL dossier")
    page = replayable(json.loads(p.read_text()))  # the rows whose words are off the page, out
    built = _with_outcomes(page, _ONE)
    for rebuild in (pre_synthesis_mech, layer_as_synthesized):
        assert rebuild(built).model_dump_json() == rebuild(page).model_dump_json(), rebuild
        cs = rebuild(built).capital_structure
        assert cs is not None and cs.covenant_exhibit_outcomes is None


def test_the_pre_spend_forecast_says_the_field_is_written_where_an_exhibit_is_located() -> None:
    """(+ / −) The $0 check forecasts the field PRESENT where an exhibit is located, so a page that
    carries it is never read as losing it, and ABSENT where none is."""
    from vinci.dossier.prespend import ABSENT, forecast_llm_fields

    p = ROOT / "data" / "dossiers" / "BURL" / "dossier.json"
    if not p.exists():
        pytest.skip("no committed BURL dossier")
    page = Dossier.model_validate(json.loads(p.read_text()))
    path = "mechanical.capital_structure.covenant_exhibit_outcomes"
    fc = forecast_llm_fields(page, http=_Http(dict.fromkeys(_TEXT)))
    assert fc[path].status == SourceStatus.PRESENT.value and "(7)" in fc[path].why
    assert page.mechanical is not None and page.mechanical.capital_structure is not None
    none = page.model_copy(update={"mechanical": page.mechanical.model_copy(update={
        "capital_structure": page.mechanical.capital_structure.model_copy(
            update={"covenant_pointer_rows": None})})})
    assert forecast_llm_fields(none, http=_Http({}))[path].status == ABSENT


# --- the render: each exhibit's own cause where the field is present, none where it is absent ----

_HEAD = "located agreement exhibit(s) not extracted this run"
_NEUTRAL = "this page does not state why"


class _Case(typing.NamedTuple):
    ticker: str
    causes: dict[str, str]  # each unextracted accession → the cause its line must state


#: The operator's ruling on a refusal with no title read (2026-11-16, "State both readings
#: (Recommended)"): both readings, the pointer's family verbatim.
_NO_TITLE_10K = ("refused: no agreement title was read from its head; it was located as material "
                 "contracts (10-K exhibit index)")

#: #1073's four frozen cases, each exhibit's cause as the committed record states it
CASES = [
    _Case("EPAM", {"0001352010-26-000015": _NO_TITLE_10K}),
    _Case("NCNO", {"0001902733-26-000022":
                   "refused: not a debt agreement (it declares itself “OFFICE LEASE”)"}),
    _Case("AMZN", {"0001104659-26-072140": "not sent: past the cost bound on exhibits per page",
                   "0001193125-18-139368": "not sent: past the cost bound on exhibits per page"}),
    _Case("BURL", {"0001193125-26-116001": _NO_TITLE_10K,
                   "0001193125-14-313404": "not sent: past the cost bound on exhibits per page",
                   "0001193125-22-200058": "not sent: past the cost bound on exhibits per page"}),
]
_IDS = [c.ticker for c in CASES]


def _committed(ticker: str) -> dict[str, typing.Any]:
    p = ROOT / "data" / "dossiers" / ticker / "dossier.json"
    if not p.exists():
        pytest.skip(f"no committed {ticker} dossier to host the frozen block")
    page: dict[str, typing.Any] = json.loads(p.read_text())
    return page


def _hosted(ticker: str, outcomes: list[dict[str, typing.Any]] | None) -> dict[str, typing.Any]:
    """`ticker`'s committed dossier with its frozen #1073 block, plus the frozen outcomes."""
    page = _committed(ticker)
    page["mechanical"]["capital_structure"] = json.loads(
        (UNEXTRACTED / f"{ticker}.json").read_text())["capital_structure"]
    return _with_outcomes(page, outcomes) if outcomes is not None else page


def _frozen_outcomes(ticker: str) -> list[dict[str, typing.Any]]:
    out: list[dict[str, typing.Any]] = json.loads((OUTCOMES / f"{ticker}.json").read_text())
    return out


def _md_line(page: dict[str, typing.Any]) -> str:
    from vinci.dossier.render import render_markdown

    lines = [ln for ln in render_markdown(Dossier.model_validate(page)).splitlines()
             if _HEAD in ln]
    assert len(lines) == 1, lines
    return lines[0].strip().removeprefix("- _").removesuffix("_")


def _web_line(tmp_path: pathlib.Path, page: dict[str, typing.Any]) -> str:
    """The page through the production `renderDossier`, in node."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    src = tmp_path / "page.json"
    src.write_text(json.dumps(page))
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { renderDossier } = await import(pathToFileURL(process.argv[1]).href);
process.stdout.write(renderDossier(JSON.parse(readFileSync(process.argv[2])), null));
"""
    html_page = subprocess.run(["node", "--input-type=module", "-e", driver, str(JS), str(src)],
                               capture_output=True, text=True, check=True).stdout
    lines = [m for m in re.findall(r"<i>(.*?)</i>", html_page, re.DOTALL) if _HEAD in m]
    assert len(lines) == 1, lines
    return html.unescape(lines[0])


def _stated(line: str) -> dict[str, str]:
    """accession → the cause the line states for it (one exhibit per accession here)."""
    return dict(re.findall(r"(\d{10}-\d{2}-\d{6}) · \S+ — (.+?)(?=; \d{10}-|$)", line))


@pytest.mark.parametrize("c", CASES, ids=_IDS)
def test_a_page_with_the_field_states_each_exhibits_own_cause_e2e(
        tmp_path: pathlib.Path, c: _Case) -> None:
    """(+) Frozen committed block + frozen outcomes → `render_markdown` and the production web
    renderer: the line lists every unextracted accession with ITS cause, claims no "does not state
    why", and reads the same on both."""
    page = _hosted(c.ticker, _frozen_outcomes(c.ticker))
    md = _md_line(page)
    assert _stated(md) == c.causes, md
    assert _NEUTRAL not in md
    assert _web_line(tmp_path, page) == md


def test_every_cause_the_loop_writes_reaches_both_renderers_e2e(
        monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    """(+) The real loop's own JSON, end to end: BURL driven down all seven branches, its term rows
    and outcomes hosted in BURL's committed page. The one extracted exhibit is cited and not
    listed; the other six are, each with the cause of the branch it took."""
    rows, _summary, _flags, _log, outcomes = _run_burl(monkeypatch)
    page = _committed("BURL")
    cs = page["mechanical"]["capital_structure"]
    cs["covenant_term_rows"] = json.loads(rows.model_dump_json())
    cs["covenant_exhibit_outcomes"] = json.loads(outcomes.model_dump_json())
    md = _md_line(page)
    assert _stated(md) == {
        "0001193125-25-168007": "could not be fetched",
        "0001564590-18-016500": "too large for single-pass extraction; extract by hand",
        "0001193125-26-116001":
            "refused: not a debt agreement (it declares itself “LEASE AGREEMENT”)",
        "0001193125-21-364998": "the extraction call failed (LLM error)",
        "0001193125-22-200058": "read, and the model returned no terms",
        "0001193125-14-313404": "not sent: past the cost bound on exhibits per page",
    }, md
    assert "0001193125-20-109457" not in md, "the extracted exhibit is cited, not listed"
    assert _web_line(tmp_path, page) == md


def test_an_exhibit_with_no_outcome_says_so_and_borrows_no_cause(tmp_path: pathlib.Path) -> None:
    """(−) The renderers never infer a cause: an unextracted accession the field holds no outcome
    for reads "no outcome recorded", and its QA flag is not read in its place."""
    outcomes = [o for o in _frozen_outcomes("BURL") if o["accession"] != "0001193125-26-116001"]
    page = _hosted("BURL", outcomes)
    md = _md_line(page)
    assert "0001193125-26-116001 · no outcome recorded" in md, md
    assert len(_stated(md)) == 2, md
    assert _web_line(tmp_path, page) == md


@pytest.mark.parametrize("c", CASES, ids=_IDS)
def test_a_page_without_the_field_keeps_the_neutral_line_e2e(
        tmp_path: pathlib.Path, c: _Case) -> None:
    """(−) The same frozen block with no outcomes — every committed page today — prints the
    neutral line, byte for byte as #1073 left it, on both renderers."""
    page = _hosted(c.ticker, None)
    md = _md_line(page)
    assert md == (f"{len(c.causes)} {_HEAD}; this page does not state why (the extraction's "
                  f"notes are QA flags in dossier.json) — see the pointer table: "
                  f"{', '.join(sorted(c.causes))}")
    assert _web_line(tmp_path, page) == md



def test_two_exhibits_under_one_accession_each_carry_it(tmp_path: pathlib.Path) -> None:
    """(−) Two pointers can share an accession, each targeting its own exhibit. Each exhibit is
    printed with its accession, so a reader never has to guess which accession an exhibit after a
    "; " belongs to (code-review round 0; no committed page has such a pair at b64be6f1)."""
    extra = {**_frozen_outcomes("BURL")[3], "filename": "burl-ex10_40.htm",
             "outcome": "fetch_failed", "declared_title": None}
    page = _hosted("BURL", [*_frozen_outcomes("BURL"), extra])
    md = _md_line(page)
    assert md.count("0001193125-26-116001 · ") == 2, md
    assert "0001193125-26-116001 · burl-ex10_40.htm — could not be fetched" in md, md
    assert md.startswith("3 located agreement exhibit(s)"), "the count stays accessions"
    assert _web_line(tmp_path, page) == md


def test_both_renderers_label_every_outcome_kind() -> None:
    """(+) The label table covers every kind the schema allows, on both renderers (code-review
    round 0): a kind added to one side only reds here rather than crashing one render."""
    from vinci.dossier.render import _EXHIBIT_OUTCOME

    assert set(_EXHIBIT_OUTCOME) == _ALL_KINDS
    js = JS.read_text()
    table = js[js.index("const _EXHIBIT_OUTCOME = {"):]
    table = table[:table.index("};")]
    assert set(re.findall(r"^\s+(\w+):", table, re.M)) == _ALL_KINDS
    for kind, label in _EXHIBIT_OUTCOME.items():
        assert f'{kind}: "{label}"' in table, kind
    from vinci.dossier.render import _NO_TITLE_READ  # the untitled refusal's first reading
    assert f'const _NO_TITLE_READ = "{_NO_TITLE_READ}";' in js


# --- independent review, round 1 ----------------------------------------------------------------

_DIGEST = "Covenant terms (from the filed agreement)"
_TECX_ACC = "0001193125-26-076793"


def _tecx(with_field: bool) -> dict[str, typing.Any]:
    """TECX's frozen block (committed 2026-11-16): one located exhibit, refused by E5 before any
    model call, so it carries no term rows and its stored digest says the extraction failed. With
    the field, the real loop's outcome for it (the frozen fixture)."""
    page = _hosted("TECX", _frozen_outcomes("TECX") if with_field else None)
    assert page["mechanical"]["capital_structure"].get("covenant_term_rows") is None
    return page


def test_a_page_whose_exhibits_gave_no_rows_states_each_cause_not_the_digest_e2e(
        tmp_path: pathlib.Path) -> None:
    """(+) Review round 1 (LLY, ORKA, TECX, VITL). With no term rows both renderers returned the
    stored digest, "extraction failed: no covenant terms extracted from located exhibits", which
    is false for an exhibit E5 refused before any call. With the field they state each located
    exhibit's own cause there too, on both renderers alike."""
    page = _tecx(with_field=True)
    md = _md_line(page)
    stated = _stated(md)
    assert stated == {_TECX_ACC: _NO_TITLE_10K}, md
    from vinci.dossier.render import render_markdown
    full = render_markdown(Dossier.model_validate(page))
    digest = page["mechanical"]["capital_structure"]["covenant_terms"]["value"]
    assert digest not in full and _DIGEST not in full, "the stored digest is not printed"
    assert _web_line(tmp_path, page) == md


def test_without_the_field_a_no_rows_page_keeps_its_stored_digest_e2e(
        tmp_path: pathlib.Path) -> None:
    """(−) The same page without the field — LLY, ORKA, TECX and VITL as committed — prints its
    stored digest as before, on both renderers, and no unextracted line."""
    from vinci.dossier.render import render_markdown

    page = _tecx(with_field=False)
    digest = page["mechanical"]["capital_structure"]["covenant_terms"]["value"]
    md = render_markdown(Dossier.model_validate(page))
    assert f"**{_DIGEST}:** {digest}" in md
    assert _HEAD not in md
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    src = tmp_path / "page.json"
    src.write_text(json.dumps(page))
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { renderDossier } = await import(pathToFileURL(process.argv[1]).href);
process.stdout.write(renderDossier(JSON.parse(readFileSync(process.argv[2])), null));
"""
    web = html.unescape(subprocess.run(
        ["node", "--input-type=module", "-e", driver, str(JS), str(src)],
        capture_output=True, text=True, check=True).stdout)
    assert digest in web and _HEAD not in web


def test_the_outcomes_are_never_in_the_synthesis_facts_dump() -> None:
    """(−) Review round 1. `synthesis.NOT_SENT` keeps the field out of the facts the model reads,
    on a page carrying it and on one without (where a dump would hold its null): every synthesis
    request stays byte-identical to the one built before the field (row 53). Precedent:
    `test_customer_count.py::test_the_count_is_never_sent_to_the_synthesis`."""
    from vinci.dossier.synthesis import NOT_SENT

    for page in (_tecx(with_field=True), _tecx(with_field=False)):
        mech = Dossier.model_validate(page).mechanical
        assert mech is not None
        assert "covenant_exhibit_outcomes" not in mech.model_dump(
            exclude=NOT_SENT)["capital_structure"]


def test_a_refusal_with_no_title_states_both_readings_e2e(tmp_path: pathlib.Path) -> None:
    """(+) The operator's ruling (2026-11-16, "State both readings (Recommended)"). E5 read no
    title from the head of VRRM's `0000950170-25-072679 · vrrm-ex10_1.htm` (its head reads
    "Amendment No. 4 to REVOLVING CREDIT Agreement", a recall defect for its own PR). The old label,
    "its head declares no agreement", was false. Both readings print: no title was read, and the
    pointer located it as its family, verbatim. Real outcomes (the frozen fixture) in VRRM's frozen
    block; `vrrm-ex10_1.htm` is also the filename of an EXTRACTED exhibit under another accession,
    so the line must key by accession. The titled refusal on the same line is unchanged."""
    page = _hosted("VRRM", _frozen_outcomes("VRRM"))
    md = _md_line(page)
    assert _stated(md) == {
        "0000950170-25-072679": "refused: no agreement title was read from its head; it was "
                                "located as Revolving Credit Facility",
        "0001104659-18-041476": "refused: not a debt agreement (it declares itself “GORES II "
                                "SUBSCRIPTION AGREEMENT”)",
    }, md
    assert "0000950170-25-072679 · vrrm-ex10_1.htm — refused" in md
    assert _web_line(tmp_path, page) == md


@pytest.mark.parametrize("family", ["", "   "], ids=["empty", "blank"])
def test_a_refusal_with_no_title_and_no_family_states_the_first_reading_alone_e2e(
        tmp_path: pathlib.Path, family: str) -> None:
    """(−) The ruling's second half: with no family to name, the first clause prints alone — a
    family is never invented."""
    outcomes = [{**o, "family": family} for o in _frozen_outcomes("TECX")]
    page = _hosted("TECX", outcomes)
    md = _md_line(page)
    assert _stated(md) == {_TECX_ACC: "refused: no agreement title was read from its head"}, md
    assert "located as" not in md
    assert _web_line(tmp_path, page) == md
