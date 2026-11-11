"""Fix request 2, order 9 (G-D8 to G-D15): the CIQ notes and two handbooks say what the code does.

THE SHAPE THIS GUARDS. `docs/ciq_extraction_notes.md` came into this repo on 2026-06-18 from the
chat-session framework, and by 2026-11-09 it contradicted the code eight ways (document 15, order
9): it said "`NM` is a REAL value, not missing", listed three missing-data markers of the code's
eight, gave an 8,192-token output cap against the client's 16,384, and described a relationship
filter that the live reader does not apply. `docs/engineering.md` advised a low temperature that
the client refuses, and `docs/RUNBOOKS.md` read as barring the re-run that the 19c guard's own
error asks for.

Each test ties one corrected claim to the code it describes. The doc must state the claim and the
code must still hold it, so a doc that drifts from the code, or code that moves under the doc,
fails the test of that ID. The docs are read as text, with line wrapping flattened. Each code fact
is read from the symbol itself, never from a copy of its value.
"""
from __future__ import annotations

import inspect
import re
import subprocess
from pathlib import Path

from vinci.dossier import (
    assemble,
    ciq,
    ciq_sheets,
    confirmation,
    driver_extract,
    requirements,
    synthesis,
    verdict,
)
from vinci.graph import extract, llm

ROOT = Path(__file__).resolve().parents[1]
#: A count as the docs spell it; a count with no entry fails the test that reads it.
_COUNT_WORDS = {3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 10: "ten"}


def _doc(name: str) -> str:
    return (ROOT / "docs" / name).read_text(encoding="utf-8")


def _flat(text: str) -> str:
    """The text with every run of whitespace one space, so a claim reads the same however the
    paragraph is wrapped."""
    return " ".join(text.split())


def _live(text: str) -> str:
    """The flattened text without its struck spans (`~~…~~`). A correction strikes the old claim
    and keeps it in view; what stays is what the doc asserts. An unpaired `~~` would strike
    everything up to the next one, and a "not in" check on that text would pass on nothing, so
    the markers must pair."""
    assert text.count("~~") % 2 == 0, "an unpaired ~~ strikes to the next one"
    return _flat(re.sub(r"~~.*?~~", "", text, flags=re.S))


def test_g_d8_the_notes_say_the_surprise_sheet_has_quarters_and_company_level_blocks() -> None:
    """The company-level fiscal-year read stops at the next section's banner, which names the
    quarterly sections, and `surprise_history` cuts its fiscal table at 'Calendar Years'. The
    notes said the sheet had no quarterly view and no Revenue or EBITDA surprise."""
    assert ciq_sheets._SURPRISE_BANNER.fullmatch("Fiscal Quarters")
    assert '"Calendar Years"' in inspect.getsource(ciq_sheets.surprise_history)
    notes = _live(_doc("ciq_extraction_notes.md"))
    assert "(no quarterly view)" not in notes
    assert "**NO Revenue surprise**" not in notes
    assert "'Fiscal Quarters'" in notes and "**Company Level**" in notes
    assert "`surprise_history()` reads the FISCAL-YEAR table only" in notes


def test_g_d9_no_code_reads_a_holders_export_and_the_notes_mark_its_rules_superseded() -> None:
    """A holders, Public Ownership or Insider Trading export has no kind, and no CIQ module
    names ownership, so no rule in the notes' holders section describes a reader here."""
    for name in ("ACME Holders.xls", "ACME Public Ownership.xls", "ACME Insider Trading.xls"):
        assert ciq.workbook_kind(name) is None, name
    assert not [m.module for m in requirements.CIQ_MODULES
                if re.search(r"ownership|holder|insider", f"{m.module} {m.workbook_kind}", re.I)]
    notes = _flat(_doc("ciq_extraction_notes.md"))
    assert "**Holders file — SUPERSEDED (G-D9, 2026-11-11)." in notes
    assert "The original rules, kept as history:" in notes


def test_g_d10_the_roster_filters_no_relationship_type_and_the_notes_say_so() -> None:
    """The five supply-chain types belong to the 10-K extraction tool. The live Customers reader
    keeps every type, and the notes no longer describe the removed parser's filter as current."""
    reader = inspect.getsource(ciq_sheets.customer_roster) + inspect.getsource(
        ciq_sheets._relationship_table)
    assert "SUPPLY_CHAIN_TYPES" not in reader
    assert extract.SUPPLY_CHAIN_TYPES
    # The behaviour, not only the symbol: two types the removed parser dropped (Creditor, Landlord,
    # both in its 2026-06 census) are kept, in the four-column header the Customers files carry.
    rel = ciq_sheets._relationship_table([
        ["Customer Name", "Relationship Type", "Primary Industry", "Source"],
        ["Acme Bank", "Creditor", "Banks", "10-K"],
        ["Landco", "Landlord", "REITs", "10-K"]])
    assert rel is not None and [ln.split(" — ")[0] for ln in rel.recent] == ["Acme Bank", "Landco"]
    assert not {"Creditor", "Landlord"} & set(extract.SUPPLY_CHAIN_TYPES)
    notes = _live(_doc("ciq_extraction_notes.md"))
    assert "**Relationship-type filter (keep supply-chain only).**" not in notes
    assert "**No relationship-type filter.**" in notes
    assert "`vinci/graph/extract.py:SUPPLY_CHAIN_TYPES`" in notes


def test_g_d11_the_notes_list_the_codes_missing_data_markers_and_nm_is_one() -> None:
    """Universal rule 1 names every marker of `ciq._UNAVAILABLE_CELLS` (it named three), and no
    line of the notes still calls `NM` a real value."""
    lines = _doc("ciq_extraction_notes.md").splitlines()
    rule = next(ln for ln in lines if ln.startswith("1. **Missing data:**"))
    named = set(re.findall(r"`([^`]+)`", rule))
    markers = {m for m in ciq._UNAVAILABLE_CELLS if m}
    assert markers <= named, sorted(markers - named)
    assert "" in ciq._UNAVAILABLE_CELLS and "blank" in rule
    assert "NM" in ciq._UNAVAILABLE_CELLS
    assert not [ln for ln in lines if ln.startswith("**`NM` is a REAL value")]


def test_g_d12_the_notes_find_key_development_columns_by_label() -> None:
    """Both header forms the notes give are read by `_kd_columns`, which finds the columns by
    label. The notes gave one fixed header under the heading "real RTF"."""
    notes = _flat(_doc("ciq_extraction_notes.md"))
    assert "**Key Developments (real RTF):**" not in notes
    assert "(`_kd_columns`), never by position" in notes
    five, four = ("Date | Company | Type | Headline | Other Parties",
                  "Date | Type | Headline | Other Parties")
    for header in (five, four):
        assert f"`{header}`" in notes, header
    # By label: the Type column moves with the header and Company is read only where it is, and
    # a header without a Headline column is not read at all.
    cols5, cols4 = ciq_sheets._kd_columns([five]), ciq_sheets._kd_columns([four])
    assert cols5 is not None and cols4 is not None
    assert cols5[0] != cols4[0] and cols5[2] is not None and cols4[2] is None
    assert ciq_sheets._kd_columns(["Date | Company | Type | Other Parties"]) is None
    assert "The reader refuses a spreadsheet and says so in a QA flag" in notes
    # The behaviour, not only the doc: a spreadsheet export gives no rows and a flag naming it.
    # The refusal returns before the file is opened, so the path need not exist.
    xls = Path("ACME Inc NYSE ACME Key Developments.xls")
    bundle = ciq.CiqBundle("ACME", (ciq.CiqWorkbook("key_developments", xls,
                                                    ciq.CiqFormat.BIFF_XLS, None),))
    rows, flag = ciq_sheets.key_developments(bundle)
    assert rows == [] and flag is not None and xls.name in flag and "spreadsheet" in flag


def test_g_d13_the_notes_state_the_clients_output_cap_and_the_six_required_fields() -> None:
    """The cap is the client's default `max_tokens`, and the forced tool requires six fields
    (the notes said 8,192 and five). The driver step reads figures from the transcript slice,
    which the notes said derived no numbers."""
    cap = inspect.signature(llm.AnthropicLlmClient.__init__).parameters["max_tokens"].default
    notes = _live(_doc("ciq_extraction_notes.md"))
    assert f"The output cap is **{cap:,} tokens**" in notes
    assert "The output cap is 8192 tokens." not in notes
    # "… builds through `from_config` without overriding it": the default is the cap only while
    # `from_config` passes no `max_tokens`.
    assert "max_tokens" not in inspect.getsource(llm.AnthropicLlmClient.from_config)
    assert "through `from_config` without overriding it" in notes
    required = synthesis._TOOL_TEMPLATE["input_schema"]["required"]
    assert len(required) == 6 and "The forced tool marks SIX fields required" in notes
    assert all(f"`{f}`" in notes for f in required), required
    assert "check_fact(" in inspect.getsource(driver_extract.extract_transcript_drivers)
    assert "(`driver_extract.extract_transcript_drivers`, run before the synthesis) DOES" in notes
    # A skipped draw still counts as attempted (#982's vote rule): with one of five failed, the
    # other four agreeing on a committed lean do not reach the bar.
    n = synthesis.SYNTHESIS_DRAWS
    assert not verdict.draw_gate(["strongly-bullish"] * (n - 1), n).passes
    assert f"({verdict.r1_required(n)} of {n} attempted to propose, `verdict.draw_gate`)" in notes


def test_g_d14_no_checklist_md_is_tracked_and_no_doc_claims_a_verification_date() -> None:
    """The notes and the source inventory pointed at a `checklist.md` this repository never held,
    and the inventory's "Last verified" line was a placeholder."""
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True,
                             check=True).stdout.splitlines()
    assert tracked and not [p for p in tracked if p.rsplit("/", 1)[-1].lower() == "checklist.md"]
    assert "**`checklist.md` is not in this repository**" in _flat(_doc("ciq_extraction_notes.md"))
    sources = _flat(_doc("data_sources.md"))
    assert "**Last verified:** YYYY-MM-DD" not in sources
    assert "**Last verified:** never recorded." in sources


def test_g_d15_engineering_passes_no_sampling_parameter_as_the_client_refuses_them() -> None:
    """engineering.md advised a low temperature. The client refuses every sampling parameter,
    and the handbook now names each one."""
    eng = _flat(_doc("engineering.md"))
    assert "pin what you can (low/0 temperature" not in eng
    assert "**pass no sampling parameter**" in eng
    assert "`vinci/graph/llm.py:_REJECTED_SAMPLING_PARAMS`" in eng
    assert llm._REJECTED_SAMPLING_PARAMS
    missing = [p for p in llm._REJECTED_SAMPLING_PARAMS if f"`{p}`" not in eng]
    assert not missing, missing
    # The draw count the handbook states is the code's (a KeyError here is a count with no word).
    word = _COUNT_WORDS[synthesis.SYNTHESIS_DRAWS]
    assert f"{word} draws, and the machine proposal is withheld" in eng
    # The vote rule's bar (#982): every attempted draw at five, 9 of 10 at the confirmation's ten.
    n, ten = synthesis.SYNTHESIS_DRAWS, confirmation.CONFIRM_DRAWS
    assert f"{verdict.r1_required(n)} of {n} attempted, so a failed draw counts as dissent" in eng
    assert f"a {_COUNT_WORDS[ten]}-draw confirmation, {verdict.r1_required(ten)} of {ten}" in eng


def test_g_d15_runbooks_quotes_the_19c_guards_own_rerun_instruction() -> None:
    """RUNBOOKS barred re-rolling a synthesis. A WRITTEN synthesis is still never re-rolled, but
    a build the 19c guard refuses wrote no page, and the guard's error says to re-run it. The
    runbook quotes that instruction, so it must stay the code's."""
    quote = "Re-run: synthesis varies between runs"
    src = inspect.getsource(assemble)
    # The quote must be the 19c guard's own error, not any message in the module.
    guard = src[src.index("uncited_material_figures(synthesis, mech)"):]
    guard = guard[:guard.index("_materiality_check(")]
    assert quote in guard
    comment = "the bad roll FAILS and is re-rolled; the good one ships"
    assert comment in src
    runbooks = _flat(_doc("RUNBOOKS.md"))
    assert f'its error ends "{quote}"' in runbooks
    assert f'reads "{comment}"' in runbooks
    for other in ("Re-run when the model is answering", "Re-run WITH a client"):
        assert other in src and f'"{other}"' in runbooks, other
    word = _COUNT_WORDS[synthesis.SYNTHESIS_DRAWS]
    assert f"the {word} draws are fixed in advance (`synthesis.SYNTHESIS_DRAWS`)" in runbooks
    assert "**A build the 19c guard REFUSES is re-run:**" in runbooks
    assert "**Do NOT re-roll a WRITTEN synthesis" in runbooks
