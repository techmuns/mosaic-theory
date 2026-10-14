"""The weekly runner's pages say what the runner cannot read (2026-10-13, before merge of PR #703).

The registry of record travels as a JSONL export WITHOUT article text (state.py). On the weekly
runner, business groups — read from the paragraphs holding a thesis's evidence — therefore could
not be found, and every surface said "none" / "the source names no company or sector": a false
statement on every weekly readout. Now a paragraph whose text is not held is NOT CHECKABLE ON
THIS MACHINE, said so on the card (HTML, Markdown, JSON), the weekly report and the desk; with the
text held, nothing changes. A HYPOTHETICAL article; no network, no model call.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup

from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence.report import groups_unread, write_run_outputs
from vinci.theme_intelligence.schemas import RunStatus
from vinci.theme_intelligence.store import Store

AS_OF = date(2026, 10, 12)
LINE = "Memory suppliers raised HBM contract prices 12% in 3Q26."
NOT_CHECKABLE = "Not checkable on this machine"


def _registry(tmp_path: Path) -> tuple[Store, str]:
    pipe = make_pipeline(tmp_path)
    run = pipe.start_run("ingest", as_of=AS_OF)
    art = Hypo("groups-parity", "Test Publisher", date(2026, 10, 6), [("paragraph", LINE)])
    ingest(pipe, art.doc(), extraction(
        [claim("c1", "b001", LINE.rstrip("."), "HBM contract prices +12% 3Q26",
               metric="HBM contract price change", value=12, value_text="12%", unit="%",
               period="3Q26")],
        [hyp("h1", "HBM contract prices rise", node="ai_infrastructure.memory",
             mechanism="pricing_cycle", supporting=["c1"])]), as_of=AS_OF,
        publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    return pipe.store, run.run_id


def _runner(store: Store, tmp_path: Path) -> Store:
    store.export_jsonl(tmp_path / "jsonl")  # what the state branch carries: no article text
    return Store.import_jsonl(tmp_path / "jsonl", tmp_path / "runner.db")


def test_the_runner_says_business_groups_are_not_checkable_never_none(tmp_path: Path) -> None:
    local, run_id = _registry(tmp_path)
    (t,) = local.theses()
    assert groups_unread(local, local.links(t.thesis_id)) == 0  # the text is held here
    runner = _runner(local, tmp_path)
    assert groups_unread(runner, runner.links(t.thesis_id)) == 1

    here = Path(write_run_outputs(local, run_id, tmp_path / "local")["dir"])
    there = Path(write_run_outputs(runner, run_id, tmp_path / "runner")["dir"])
    for out, checkable in ((here, True), (there, False)):
        card = BeautifulSoup((out / "cards" / f"{t.thesis_id}.html").read_text(), "html.parser")
        s05 = card.select_one('[data-field="s05_affected"]').get_text(" ")
        page = BeautifulSoup((out / "theses" / f"{t.thesis_id}.html").read_text(),
                             "html.parser").select_one(".expo").get_text(" ")
        md = (out / "cards" / f"{t.thesis_id}.md").read_text()
        js = json.loads((out / "cards" / f"{t.thesis_id}.json").read_text())
        if checkable:  # positive pin: with the text held the group is read, nothing is hedged
            assert "suppliers" in s05 and "suppliers" in page and "- suppliers —" in md
            assert NOT_CHECKABLE not in s05 + page + md
            assert js["named_business_groups_unchecked_paragraphs"] == 0
        else:  # the runner: never "none", always "not checkable"
            assert NOT_CHECKABLE in s05 and NOT_CHECKABLE in page and NOT_CHECKABLE in md
            assert "None named in the paragraphs" not in s05
            assert "none" not in page.split("Business groups the source names")[1].split(
                NOT_CHECKABLE)[0].lower()
            assert js["named_business_groups_unchecked_paragraphs"] == 1
