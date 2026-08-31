"""The monitor's theme-falsifier sweep (brief Item 2, 2026-08-29).

Load-bearing pins: a PASSED deadline flags with the same wording discipline as the scenario
``dated_triggers`` ("re-underwrite due" — a closed window, never an adjudication that the
falsifier FIRED); a FUTURE deadline lists without the flag; zero cards renders the STATED
"no thesis cards declared" line, never a silent absence; and the new snapshot field defaults, so
every committed pre-Item-2 monitor day still validates (corpus pin on the real 2026-08-11 file).

Also pinned here: the ADJACENT FIX shipped with this item — scenario ``passed_trigger_deadlines``
were typed and persisted since the catalyst calendar but never rendered in the terminal view
(latent: every committed day carries the field empty). The render line now exists and is pinned,
because an artifact-only flag the console never shows is the recorded-criterion-nobody-reads
class this whole brief exists to end.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from vinci.monitor import (
    FreshnessRow,
    MonitorSnapshot,
    SpreadDiagnostic,
    ThemeFalsifierRow,
    render_table,
    theme_falsifier_rows,
)
from vinci.scenarios import DatedTrigger
from vinci.themes.thesis import ThemeThesis, ThesisMechanism, load_all_theses, stamped, write_thesis

_REPO = Path(__file__).resolve().parents[1]


def _card(**over: object) -> ThemeThesis:
    base: dict[str, object] = {
        "driver_key": "ai-datacenter",
        "declared_date": date(2026, 8, 29),
        "mechanism": ThesisMechanism.SUPPLY_SIDE,
        "market_mistake": "m", "null_thesis": "n",
        "first_confirming": DatedTrigger(trigger="confirming datapoint", deadline="2026-11-15",
                                         basis="guidance cycle"),
        "falsifiers": (DatedTrigger(trigger="past-due falsifier", deadline="2026-08-15"),
                       DatedTrigger(trigger="future falsifier", deadline="2027-01-31")),
    }
    base.update(over)
    return ThemeThesis.model_validate(base)


def _snap(theme_rows: list[ThemeFalsifierRow]) -> MonitorSnapshot:
    return MonitorSnapshot(as_of=date(2026, 8, 29), spread=SpreadDiagnostic(buy_n=0, avoid_n=0),
                           theme_falsifiers=theme_rows)


def test_sweep_flags_passed_and_lists_future_deadlines() -> None:
    rows = theme_falsifier_rows([_card()], today=date(2026, 8, 29))
    by = {(r.kind, r.trigger): r for r in rows}
    assert by[("first-confirming", "confirming datapoint")].deadline_passed is False
    assert by[("falsifier", "past-due falsifier")].deadline_passed is True
    assert by[("falsifier", "future falsifier")].deadline_passed is False
    assert by[("first-confirming", "confirming datapoint")].basis == "guidance cycle"


def test_render_carries_the_flag_wording_and_never_adjudicates() -> None:
    md = render_table(_snap(theme_falsifier_rows([_card()], today=date(2026, 8, 29))))
    assert "THEME FALSIFIERS (thesis cards; machine flags deadlines — the human concludes)" in md
    # the kind LEADS the flag (review 2026-08-31) — see the passed-first-confirming pin below
    assert "⚑ falsifier: past-due falsifier — deadline 2026-08-15 PASSED → re-underwrite due" in md
    # the future rows list WITHOUT the flag — a window still open is not a flag
    assert "falsifier: future falsifier (by 2027-01-31)" in md
    assert "future falsifier — deadline 2027-01-31 PASSED" not in md
    # the flag says the WINDOW closed; "fired" is the human's word and must not appear
    assert "fired" not in md.lower()


def test_a_passed_first_confirming_flags_with_its_kind_visible() -> None:
    """REVIEW FINDING (2026-08-31, medium review of the first declared card): the passed-deadline
    branch dropped ``tf.kind``, so a passed FIRST-CONFIRMING printed byte-identically to a passed
    falsifier — the console reported a confirmation window closing as if a falsifier's had. The
    first real card (confirming due 2026-12-15) would have hit this the day the window closed.
    The kind now leads BOTH branches; this pin runs the sweep past the confirming deadline."""
    md = render_table(_snap(theme_falsifier_rows([_card()], today=date(2026, 12, 16))))
    assert ("⚑ first-confirming: confirming datapoint — deadline 2026-11-15 PASSED "
            "→ re-underwrite due") in md
    # and the two kinds are distinguishable in the same render
    assert "⚑ falsifier: past-due falsifier — deadline 2026-08-15 PASSED" in md


def test_zero_cards_renders_a_stated_absence() -> None:
    md = render_table(_snap([]))
    assert "no thesis cards declared" in md


def test_committed_pre_item2_snapshot_still_validates() -> None:
    """CORPUS PIN — the field defaults, so the real committed 2026-08-11 day (written before
    theme_falsifiers existed) loads unchanged."""
    p = _REPO / "data" / "monitor" / "2026-08-11.json"
    snap = MonitorSnapshot.model_validate_json(p.read_text())
    assert snap.theme_falsifiers == []


def test_load_all_theses_skips_archive_and_sorts(tmp_path: Path) -> None:
    write_thesis(stamped(_card()), data_dir=tmp_path)
    write_thesis(stamped(_card(driver_key="defense-demand-shift")), data_dir=tmp_path)
    # a superseded card in archive/ must never feed the sweep — a stale falsifier flagged as
    # live is the class the sweep exists to end
    arch = tmp_path / "themes/thesis/archive"
    arch.mkdir(parents=True)
    (arch / "ai-datacenter-2026-01-01.json").write_text(
        stamped(_card()).model_dump_json())
    cards, problems = load_all_theses(data_dir=tmp_path)
    assert [c.driver_key for c in cards] == ["ai-datacenter", "defense-demand-shift"]
    assert problems == []


def test_one_unreadable_card_does_not_take_the_whole_run_down(tmp_path: Path) -> None:
    """REVIEW FINDING (2nd pass) — a single hand-edited theme file raised out of the loader, so
    `vinci monitor` died before marking the book: the position rows and the BUY−AVOID diagnostic
    were lost to a file that has nothing to do with them. The broken card is now REPORTED, not
    swallowed and not fatal — an unreadable card is a watch that is not happening, and the
    operator must see exactly that."""
    write_thesis(stamped(_card()), data_dir=tmp_path)
    (tmp_path / "themes/thesis/defense-demand-shift.json").write_text('{"driver_key": OOPS')
    cards, problems = load_all_theses(data_dir=tmp_path)
    assert [c.driver_key for c in cards] == ["ai-datacenter"]   # the good card still sweeps
    assert len(problems) == 1
    assert "defense-demand-shift.json" in problems[0] and "UNREADABLE" in problems[0]
    assert "NOT being watched" in problems[0]
    # the blast radius really is one file — the good card's rows are unaffected
    assert theme_falsifier_rows(cards, today=date(2026, 8, 29))


def test_scenario_passed_deadlines_now_render_in_the_terminal_view() -> None:
    """THE ADJACENT FIX, pinned at the surface where the harm occurred: a FreshnessRow's passed
    flags were persisted but invisible in the console."""
    fr = FreshnessRow(ticker="SMPL", verdict="BUY",
                      passed_trigger_deadlines=[
                          "OWYN net sales turn negative — deadline 2026-08-01 PASSED "
                          "→ re-underwrite due"])
    md = render_table(MonitorSnapshot(as_of=date(2026, 8, 29),
                                      spread=SpreadDiagnostic(buy_n=0, avoid_n=0),
                                      freshness=[fr]))
    assert "⚑ OWYN net sales turn negative — deadline 2026-08-01 PASSED" in md


def test_cmd_monitor_wires_the_sweep_into_the_snapshot() -> None:
    """SOURCE-ORDER PIN (the surface-where-harm-occurs discipline): the CLI must build the theme
    rows AND pass them into the snapshot it writes — a sweep computed but not persisted would be
    the artifact-only inverse of the render gap fixed above."""
    src = (_REPO / "vinci/cli.py").read_text()
    fn = src.split("def _cmd_monitor(", 1)[1].split("\ndef ", 1)[0]
    assert "load_all_theses" in fn
    assert "theme_falsifier_rows" in fn
    assert "theme_falsifiers=theme_rows" in fn
    # REVIEW PIN (2026-08-31): the sweep runs on the SNAPSHOT'S clock (now_date, last trading
    # day), never the calendar ref — sweeping on ref let a weekend run commit
    # deadline_passed=true into a day file dated BEFORE the deadline.
    assert "theme_falsifier_rows(cards, today=now_date)" in fn
    assert "theme_falsifier_rows(cards, today=ref)" not in fn
