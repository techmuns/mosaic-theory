"""THE STATED CURRENCY of every CIQ money panel a page reads (2026-10-27).

Every CIQ money figure on a page is read as USD ($M), and until this build nothing checked that the
export says so — a CIQ chart export (MSCI World Net) had already arrived in EUR, unlabelled. The
pins run on FROZEN header rows of real exports (`tests/fixtures/ciq_currency_headers.json`: the
'Currency' rows, section headers and 'Currency:' cells the reader examines, and no CIQ figure),
built into the REAL `CiqBundle`, never on a living page:

* AMZN — a US filer: every money panel states USD; its Consensus also carries BOVESPA (BRL) and
  SET (THB) depositary-receipt sections no page reads;
* ONON — a Swiss filer: the Financials and Estimates state CHF while Historical Capitalization and
  the comps book state USD, so a page would mix the two under one dollar sign. It is REFUSED;
* BRBR — revenue guidance under a header with no currency on it;
* HLF — a EUR listing section beside its own.

What they hold, in order: the reader (positive and negative per rule), the refusal at assembly's
CALL SITE, the back-fill's proofs, and the scorecard check.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import json
import pathlib
import textwrap
import typing
from collections.abc import Callable
from datetime import date

import pytest

from vinci.dossier import ciq_sheets as cs
from vinci.dossier import statement_recon as sr
from vinci.dossier.ciq import CiqAmbiguousError, CiqBundle, CiqFormat, CiqWorkbook
from vinci.dossier.refresh import ciq_currency_transform
from vinci.dossier.schemas import (
    CHECK_AGREE,
    CHECK_DIFFER,
    CHECK_NOT_RUN,
    CiqCurrency,
    PanelCurrency,
)
from vinci.quality import core
from vinci.quality.sources import ciq as qciq

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX: dict[str, typing.Any] = json.loads(
    (ROOT / "tests" / "fixtures" / "ciq_currency_headers.json").read_text())
Rows = list[list[typing.Any]]
Sheets = dict[str, Rows]


def _bundle(ticker: str, edit: Callable[[Sheets], None] | None = None, *,
            drop: tuple[str, ...] = (), root: pathlib.Path | None = None) -> CiqBundle:
    """The frozen header rows as a REAL bundle: one workbook per (kind, freq), its sheets served
    from the bundle's own cache. With ``root``, each workbook is a real file there, so its sha256
    — what a page stamps — can be computed."""
    sheets: Sheets = copy.deepcopy(FIX["names"][ticker]["sheets"])
    if edit is not None:
        edit(sheets)
    by_wb: dict[tuple[str, str | None], Sheets] = {}
    for key, rows in sheets.items():
        kind, freq, sheet = key.split("|")
        by_wb.setdefault((kind, freq or None), {})[sheet] = rows
    workbooks: list[CiqWorkbook] = []
    cache: dict[pathlib.Path, Sheets] = {}
    for (kind, freq), sh in by_wb.items():
        if kind in drop:
            continue
        base = root if root is not None else pathlib.Path("/frozen")
        path = base / f"{ticker}-{kind}-{freq or 'one'}.xls"
        if root is not None:
            path.write_bytes(f"{ticker} {kind} {freq}".encode())
        workbooks.append(CiqWorkbook(kind=kind, path=path, fmt=CiqFormat.BIFF_XLS, freq=freq))
        cache[path] = sh
    return CiqBundle(ticker=ticker, workbooks=tuple(workbooks), _cache=cache)


def _read(ticker: str, edit: Callable[[Sheets], None] | None = None) -> CiqCurrency:
    cur = cs.stated_currency(_bundle(ticker, edit))
    assert cur is not None
    return cur


def _panel(cur: CiqCurrency, panel: str) -> PanelCurrency:
    return next(p for p in cur.panels if p.panel == panel)


def _cells(ticker: str, key: str) -> set[str]:
    return {str(c) for r in FIX["names"][ticker]["sheets"][key] for c in r}


# --- the reader --------------------------------------------------------------------------------


def test_a_us_filer_states_usd_on_every_money_panel() -> None:
    """(+) AMZN: all eighteen money panels are read and every one states USD — the comps book by
    name ('US Dollar') — so the page agrees, nothing is refused and nothing is flagged."""
    cur = _read("AMZN")
    assert cur.check == CHECK_AGREE
    assert [p.panel for p in cur.panels] == [p for p, _how, _read in cs._MONEY_PANELS]
    assert all(p.check == CHECK_AGREE for p in cur.panels)
    assert _panel(cur, "Comps→Financial Data").stated == ["US Dollar"]
    assert all(p.stated == ["USD"] for p in cur.panels if not p.panel.startswith("Comps"))
    cs.require_usd(cur, "AMZN")
    assert cs.currency_flag(cur) is None


def test_a_chf_export_differs_panel_by_panel_and_is_refused() -> None:
    """(−) ONON: fifteen panels state CHF; Historical Capitalization (its TRADING currency) and the
    comps book (converted at spot) state USD. One page would set CHF EBITDA under a USD TEV. The
    refusal names every CHF panel — none is cut."""
    cur = _read("ONON")
    assert cur.check == CHECK_DIFFER
    agree = {p.panel for p in cur.panels if p.check == CHECK_AGREE}
    differ = [p for p in cur.panels if p.check == CHECK_DIFFER]
    assert agree == {"Financials (quarterly)→Historical Capitalization", "Comps→Financial Data",
                     "Comps→Implied Valuation"}
    assert len(differ) == 15 and all(p.stated == ["CHF"] for p in differ)
    with pytest.raises(cs.CiqCurrencyError) as exc:
        cs.require_usd(cur, "ONON")
    assert all(p.panel in str(exc.value) for p in differ)


def test_another_listings_section_is_not_one_the_page_reads() -> None:
    """(+) AMZN's Consensus heads its depositary receipts 'BOVESPA:AMZO34 (GDR)' and 'SET:AMZN80
    (GDR)', and HLF's carries a Frankfurt listing, 'DB:HOO (EUR)' — each a section header the reader
    would take as a non-USD currency. A page reads Company Level and the name's own listing only,
    so each panel states USD. The cases exist in the frozen rows — asserted first."""
    assert {"BOVESPA:AMZO34 (GDR)", "SET:AMZN80 (GDR)"} <= _cells("AMZN", "estimates||Consensus")
    assert "DB:HOO (EUR)" in _cells("HLF", "estimates||Consensus")
    assert _panel(_read("AMZN"), "Estimates→Consensus").stated == ["USD"]
    assert _panel(_read("HLF"), "Estimates→Consensus").stated == ["USD"]


def test_a_section_the_page_reads_in_another_currency_differs() -> None:
    """(−) AMZN's Trends with its Company Level headers restated in EUR: a section the page DOES
    read now disagrees, and the panel differs with both currencies named."""
    def eur(sheets: Sheets) -> None:
        sheets["estimates||Trends"] = [
            [str(c).replace("Company Level (USD)", "Company Level (EUR)") for c in r]
            for r in sheets["estimates||Trends"]]

    p = _panel(_read("AMZN", eur), "Estimates→Trends")
    assert p.check == CHECK_DIFFER and set(p.stated) == {"USD", "EUR"}


def test_a_guidance_block_without_a_currency_header_reads_the_reported_currency() -> None:
    """(+) BRBR's revenue guidance sits under a BLANK header. The sheet states 'Currency: Reported
    Currency' and the same export's Company Level sections state which currency that is — USD —
    so the panel reads USD and says how it got there."""
    rows = FIX["names"]["BRBR"]["sheets"]["estimates||Guidance"]
    assert not any(cs._SECTION_CURRENCY.match(str(c).strip()) for r in rows for c in r)
    p = _panel(_read("BRBR"), "Estimates→Guidance")
    assert p.stated == ["USD"] and p.check == CHECK_AGREE and "Reported Currency" in p.where


def test_the_reported_currency_is_the_exports_own_never_a_default() -> None:
    """(−) ONON's guidance has the same blank header and its Company Level states CHF: the panel
    reads CHF and differs. A header naming a currency outright is taken verbatim — 'US Dollar'
    agrees, 'Euro' differs."""
    assert _panel(_read("ONON"), "Estimates→Guidance").stated == ["CHF"]

    def header(name: str) -> Callable[[Sheets], None]:
        def edit(sheets: Sheets) -> None:
            sheets["estimates||Guidance"][0][0] = f"Currency: {name}"
        return edit

    # no Consensus sheet to resolve 'Reported Currency' through: unstated, never a default
    def no_consensus(sheets: Sheets) -> None:
        del sheets["estimates||Consensus"]

    gone = _panel(_read("BRBR", no_consensus), "Estimates→Guidance")
    assert (gone.stated, gone.check) == ([], CHECK_NOT_RUN)
    usd = _panel(_read("BRBR", header("US Dollar")), "Estimates→Guidance")
    eur = _panel(_read("BRBR", header("Euro")), "Estimates→Guidance")
    assert (usd.stated, usd.check) == (["US Dollar"], CHECK_AGREE)
    assert (eur.stated, eur.check) == (["Euro"], CHECK_DIFFER)


def test_a_panel_that_states_no_currency_is_not_run_flagged_and_never_usd() -> None:
    """(−) AMZN's quarterly Income Statement with its 'Currency' row gone states nothing: the panel
    and the page are not_run and the QA flag names the panel. Refusal is for a STATED other
    currency, so assembly is not refused — it is told the read is unverified."""
    def strip(sheets: Sheets) -> None:
        key = "financials|quarterly|Income Statement"
        sheets[key] = [r for r in sheets[key] if not (r and str(r[0]).strip() == "Currency")]

    cur = _read("AMZN", strip)
    p = _panel(cur, "Financials (quarterly)→Income Statement")
    assert (p.stated, p.check, cur.check) == ([], CHECK_NOT_RUN, CHECK_NOT_RUN)
    cs.require_usd(cur, "AMZN")
    flag = cs.currency_flag(cur)
    assert flag is not None and "Financials (quarterly)→Income Statement" in flag
    # a STATED other currency outranks an unstated panel: ONON stripped the same way still differs
    onon = _read("ONON", strip)
    assert _panel(onon, "Financials (quarterly)→Income Statement").check == CHECK_NOT_RUN
    assert onon.check == CHECK_DIFFER


def test_a_no_data_available_shell_carries_no_money_and_is_not_listed() -> None:
    """(+/−) A header-only 'No Data Available' sheet (AORT's July 2026 re-export shape,
    `ciq_sheets._no_data_available`) holds no figure, so it is not listed — while the same sheet
    with its 'Currency' row and no shell marker is listed, not_run."""
    def shell(sheets: Sheets) -> None:
        sheets["financials|annual|Segments"] = [["No Data Available"]]

    def bare(sheets: Sheets) -> None:
        sheets["financials|annual|Segments"] = [["In Millions of the reported currency."]]

    assert "Financials (annual)→Segments" not in {p.panel for p in _read("AMZN", shell).panels}
    assert _panel(_read("AMZN", bare), "Financials (annual)→Segments").check == CHECK_NOT_RUN


def test_an_instrument_repayable_in_euros_does_not_restate_the_panel() -> None:
    """(+) AMZN carries euro notes. An instrument row whose 'Repayment Currency' is EUR (the real
    sheet's column) leaves the panel at the currency its 'Principal Due (USD)' header states."""
    def euro_note(sheets: Sheets) -> None:
        key = "financials|annual|Capital Structure Details"
        hdr = next(r for r in sheets[key] if "Repayment Currency" in r)
        row = [""] * len(hdr)
        row[0], row[hdr.index("Repayment Currency")] = "Euro Senior Notes", "EUR"
        sheets[key].append(row)

    p = _panel(_read("AMZN", euro_note), "Financials (annual)→Capital Structure Details")
    assert (p.stated, p.check) == (["USD"], CHECK_AGREE)


def test_the_comps_label_must_name_the_dollar_exactly() -> None:
    """(+/−) 'US Dollar' agrees; an unfamiliar spelling of the dollar differs — refused loudly,
    never passed on a guess."""
    def spell(sheets: Sheets) -> None:
        for r in sheets["comps||Financial Data"]:
            if r and r[0] == "Currency:":
                r[1] = "U.S. Dollar"

    assert _panel(_read("AMZN"), "Comps→Financial Data").check == CHECK_AGREE
    p = _panel(_read("AMZN", spell), "Comps→Financial Data")
    assert (p.stated, p.check) == (["U.S. Dollar"], CHECK_DIFFER)


def test_a_folder_with_no_money_panel_reads_none() -> None:
    assert cs.stated_currency(CiqBundle(ticker="X", workbooks=())) is None


# --- assembly: the call site, not the helper ----------------------------------------------------


class _Tripwire:
    """Any attribute read means assembly went past the currency guard."""

    def __getattr__(self, name: str) -> typing.Any:
        raise AssertionError(f"assembly read .{name} before refusing the currency")


def test_assembly_refuses_a_stated_foreign_currency_before_it_reads_anything() -> None:
    """(−) `assemble_mechanical` on ONON's exports raises before it touches the store, EDGAR, the
    network, the graph or the price — each passed here is a tripwire."""
    from vinci.dossier.mechanical import assemble_mechanical

    record = typing.cast(typing.Any, type("R", (), {"identity": type("I", (), {
        "ticker": "ONON", "cik": None, "internal_id": None})()})())
    trip = typing.cast(typing.Any, _Tripwire())
    with pytest.raises(cs.CiqCurrencyError, match="ONON: 15 CIQ money panel"):
        assemble_mechanical(record, store=trip, edgar=trip, http=trip, finra=trip, graph=trip,
                            resolver=trip, bundle=_bundle("ONON"),
                            reference_date=date(2026, 10, 27))


def test_assembly_stores_the_read_and_flags_an_unstated_panel() -> None:
    """(+) The same function stores what it read on the layer and raises the unstated-panel flag
    — both pinned on its source, since a full assembly needs EDGAR (a helper-level test stays green
    when a call site is deleted)."""
    from vinci.dossier import mechanical

    tree = ast.parse(textwrap.dedent(inspect.getsource(mechanical.assemble_mechanical)))
    layer = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id == "MechanicalLayer"]
    assert len(layer) == 1
    kw = {k.arg: k.value for k in layer[0].keywords}
    assert isinstance(kw.get("ciq_currency"), ast.Name) and kw["ciq_currency"].id == "currency"
    calls = [n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
             and n.func.value.id == "ciq_sheets"]
    assert {"stated_currency", "require_usd", "currency_flag"} <= set(calls)


# --- the back-fill -----------------------------------------------------------------------------


def _sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


def _page(bundle: CiqBundle, **extra: typing.Any) -> dict[str, typing.Any]:
    """A committed-page shape stamping the bundle's own quarterly Financials and Estimates."""
    fin = bundle.workbook("financials", freq="quarterly")
    est = bundle.workbook("estimates")
    assert fin is not None and est is not None
    return {"ticker": bundle.ticker, "ev_bridge": {"source_sha256": _sha(fin.path)},
            "forward_consensus": {"source_sha256": _sha(est.path)},
            "mechanical": {"financial_summary": {"annual": {"value": {"columns": [], "rows": []}}},
                           **extra}}


def _run(page: dict[str, typing.Any], bundle: CiqBundle | Exception,
         ) -> tuple[dict[str, typing.Any], list[str]]:
    refused: list[str] = []

    def bundle_for(_t: str) -> CiqBundle:
        if isinstance(bundle, Exception):
            raise bundle
        return bundle

    out = ciq_currency_transform(page, refused=refused, bundle_for=bundle_for)(page["mechanical"])
    return out, refused


def test_the_backfill_writes_the_assemblers_own_read_behind_its_proofs(
        tmp_path: pathlib.Path) -> None:
    """(+) Every workbook proved the page's own: the block written is exactly
    `stated_currency(bundle)`, nothing refused."""
    bundle = _bundle("AMZN", drop=("comps",), root=tmp_path)
    out, refused = _run(_page(bundle), bundle)
    want = cs.stated_currency(bundle)
    assert refused == [] and want is not None
    assert out["ciq_currency"] == json.loads(want.model_dump_json())


def test_each_backfill_proof_refuses_on_its_own(tmp_path: pathlib.Path) -> None:
    """(−) The page stamps another quarterly Financials; another Estimates; an annual table the
    export does not reproduce; a comps book whose peer grid is not the page's; a folder that will
    not load; a block already on the page. Each leaves the block as it was and names why."""
    bundle = _bundle("AMZN", drop=("comps",), root=tmp_path)
    cases: list[tuple[dict[str, typing.Any], CiqBundle | Exception, str]] = []
    p = _page(bundle)
    p["ev_bridge"]["source_sha256"] = "0000000000"
    cases.append((p, bundle, "quarterly Financials is not the export the page stamps"))
    p = _page(bundle)
    p["forward_consensus"]["source_sha256"] = "0000000000"
    cases.append((p, bundle, "Estimates is not the export the page stamps"))
    p = _page(bundle)
    p["mechanical"]["financial_summary"]["annual"]["value"] = {
        "columns": ["FY2025"], "is_estimate": [False],
        "rows": [{"label": sr.LINES[0].label, "values": [1.0]}]}
    cases.append((p, bundle, "does not reproduce the page's annual table"))
    (tmp_path / "c").mkdir()
    with_comps = _bundle("AMZN", root=tmp_path / "c")
    cases.append((_page(with_comps), with_comps, "comps book does not reproduce"))
    cases.append((_page(bundle), CiqAmbiguousError("two Financials exports"),
                  "no CIQ export to read the currencies from"))
    held = {"panels": [], "check": CHECK_NOT_RUN}
    cases.append((_page(bundle, ciq_currency=held), bundle, "kept, never overwritten"))
    for page, b, why in cases:
        before = copy.deepcopy(page["mechanical"].get("ciq_currency"))
        out, refused = _run(page, b)
        assert len(refused) == 1 and why in refused[0], (why, refused)
        assert out.get("ciq_currency") == before, why


def test_a_stamped_export_missing_from_the_folder_refuses_the_backfill(
        tmp_path: pathlib.Path) -> None:
    """(−) Codex, #819 round 1: the page stamps a Financials and an Estimates export, and the folder
    no longer holds one of them. Building the block from what remains would leave that export's
    panels unreported, so the page is refused and keeps no block."""
    full = _bundle("AMZN", drop=("comps",), root=tmp_path)
    for i, gone in enumerate(("financials", "estimates")):
        (tmp_path / str(i)).mkdir()
        rest = _bundle("AMZN", drop=("comps", gone), root=tmp_path / str(i))
        out, refused = _run(_page(full), rest)
        assert len(refused) == 1 and "the folder does not hold" in refused[0], (gone, refused)
        assert "ciq_currency" not in out, gone


def test_every_committed_block_agrees_with_its_own_panels() -> None:
    """END TO END on the committed pages, phrasing-free: where a page carries the block, every
    panel's outcome is what its stated currencies give, and the page's is what its panels give."""
    blocks = {f.parent.name: b for f in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))
              if (b := json.loads(f.read_text())["mechanical"].get("ciq_currency")) is not None}
    for t, b in blocks.items():
        cur = CiqCurrency.model_validate(b)
        for p in cur.panels:
            assert p.check == cs._panel_check(p.stated), (t, p.panel)
        checks = {p.check for p in cur.panels}
        page = (CHECK_DIFFER if CHECK_DIFFER in checks
                else CHECK_NOT_RUN if CHECK_NOT_RUN in checks else CHECK_AGREE)
        assert cur.check == page, t


# --- the scorecard -----------------------------------------------------------------------------


def _scored(block: dict[str, typing.Any] | None) -> core.ItemResult:
    mech: dict[str, typing.Any] = {} if block is None else {"ciq_currency": block}
    return qciq._currency_stated_usd({"ticker": "T", "mechanical": mech})


def test_the_scorecard_counts_one_unit_per_panel_and_absent_is_not_run() -> None:
    """(+/−) agree confirms, differ is unexplained, not_run is unchecked — one unit per panel; a
    page without the block did not run (never a pass); an outcome it was not taught raises."""
    panels = [{"panel": f"p{i}", "stated": [], "where": "", "check": c}
              for i, c in enumerate([CHECK_AGREE, CHECK_AGREE, CHECK_DIFFER, CHECK_NOT_RUN])]
    r = _scored({"panels": panels, "check": CHECK_DIFFER})
    assert r.counts == {core.CONFIRMED: 2, core.DIFFERS_UNEXPLAINED: 1, core.UNCHECKED: 1}
    assert _scored(None).not_run is not None and not _scored(None).counts
    with pytest.raises(ValueError, match="not an outcome"):
        _scored({"panels": [{**panels[0], "check": "maybe"}], "check": CHECK_AGREE})


def test_the_currency_check_guards_the_unit_class_of_every_money_family() -> None:
    """The check is INTERNAL (CIQ's own label against the page's unit) and declares wrong_unit
    alone — currency, not scale. It sits on every family whose panels it reads, so each shows an
    internal guard on the unit class; the ratio families and the peer grid stay off it."""
    check = next(c for c in qciq.CHECKS if c.id == "currency_stated_usd")
    assert check.independence == core.INTERNAL and check.catches == ("wrong_unit",)
    fam = {f.id: f for f in qciq.FAMILIES}
    on = {f.id for f in qciq.FAMILIES if "currency_stated_usd" in f.checks}
    assert {"estimates.consensus", "financials.segments", "estimates.surprise",
            "comps.market_cap", "financials.capital_structure"} <= on
    assert not on & {"financials.ratios", "estimates.forward_multiples", "comps.peer_grid"}
    for fid in on:
        assert core.failure_guard(qciq.SOURCE, fam[fid])["wrong_unit"] in (
            core.INDEPENDENT, core.INTERNAL), fid
