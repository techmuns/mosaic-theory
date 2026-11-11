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

from vinci.dossier import assemble, ciq, ciq_sheets, driver_extract, requirements, synthesis
from vinci.graph import extract, llm

ROOT = Path(__file__).resolve().parents[1]


def _doc(name: str) -> str:
    return (ROOT / "docs" / name).read_text(encoding="utf-8")


def _flat(text: str) -> str:
    """The text with every run of whitespace one space, so a claim reads the same however the
    paragraph is wrapped."""
    return " ".join(text.split())


def _live(text: str) -> str:
    """The flattened text without its struck spans (`~~…~~`). A correction strikes the old claim
    and keeps it in view; what stays is what the doc asserts."""
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
    for header in ("Date | Company | Type | Headline | Other Parties",
                   "Date | Type | Headline | Other Parties"):
        assert f"`{header}`" in notes, header
        assert ciq_sheets._kd_columns([header]) is not None, header
    assert "The reader refuses a spreadsheet and says so in a QA flag" in notes


def test_g_d13_the_notes_state_the_clients_output_cap_and_the_six_required_fields() -> None:
    """The cap is the client's default `max_tokens`, and the forced tool requires six fields
    (the notes said 8,192 and five). The driver step reads figures from the transcript slice,
    which the notes said derived no numbers."""
    cap = inspect.signature(llm.AnthropicLlmClient.__init__).parameters["max_tokens"].default
    notes = _live(_doc("ciq_extraction_notes.md"))
    assert f"The output cap is **{cap:,} tokens**" in notes
    assert "The output cap is 8192 tokens." not in notes
    required = synthesis._TOOL_TEMPLATE["input_schema"]["required"]
    assert len(required) == 6 and "The forced tool marks SIX fields required" in notes
    assert all(f"`{f}`" in notes for f in required), required
    assert "check_fact(" in inspect.getsource(driver_extract.extract_transcript_drivers)
    assert "(`driver_extract.extract_transcript_drivers`, run before the synthesis) DOES" in notes


def test_g_d14_no_checklist_md_is_tracked_and_no_doc_claims_a_verification_date() -> None:
    """The notes and the source inventory pointed at a `checklist.md` this repository never held,
    and the inventory's "Last verified" line was a placeholder."""
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True,
                             check=True).stdout.splitlines()
    assert tracked and not [p for p in tracked if p.rsplit("/", 1)[-1] == "checklist.md"]
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


def test_g_d15_runbooks_quotes_the_19c_guards_own_rerun_instruction() -> None:
    """RUNBOOKS barred re-rolling a synthesis. A WRITTEN synthesis is still never re-rolled, but
    a build the 19c guard refuses wrote no page, and the guard's error says to re-run it. The
    runbook quotes that instruction, so it must stay the code's."""
    quote = "Re-run: synthesis varies between runs"
    assert quote in inspect.getsource(assemble)
    runbooks = _flat(_doc("RUNBOOKS.md"))
    assert f'its error ends "{quote}"' in runbooks
    assert "**A build the 19c guard REFUSES is re-run:**" in runbooks
    assert "**Do NOT re-roll a WRITTEN synthesis" in runbooks
