"""A release quote never ends before the figure it backs (#829).

THE DEFECT. `release_parse._verbatim` snaps a quote back to its bullet or sentence start, joins it
to the match's end — the figure — and then kept the FIRST 200 characters. A long lead-in pushed
the figure out of its own quote:
- WERN's 8-K `0000793074-26-000165` EX-99.1 (held build, 2026-11-14) stored adjusted EPS −0.03 under
  "…non-GAAP adjusted diluted earnings per share of $0.16 compared to non-GAAP diluted loss per
  share of", and `test_release_parse::test_committed_dossiers_carry_no_ratio_as_a_currency_amount`
  refused the page;
- TJX's 8-K `0000109198-26-000004` EX-99.1, committed today, stores its Fiscal 2027 EPS guide
  ($4.93 to $5.02) under "…and diluted earnings per share to be".

Fixtures are REAL: each passage is the exhibit as `normalize_text(html_to_text())` reads it from
the SEC cache, cut to the paragraph that carries the rows (`tests/fixtures/release_verbatim_cap/`).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vinci.dossier.schemas import ReleaseExtract
from vinci.edgar import release_parse as rp

CASES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "fixtures" / "release_verbatim_cap" / "cases.json").read_text())


def _parse(key: str) -> ReleaseExtract:
    case = CASES[key]
    return rp.parse_release(case["text"], source_ref=case["source_ref"])


def _flat(key: str) -> str:
    return " ".join(CASES[key]["text"].split())


def test_a_reconciliation_figure_is_quoted_with_its_figure() -> None:
    """(-) WERN's Q3 2025 comparative, −0.03: its sentence runs past the cap, and the quote kept
    the sentence's start and lost the figure. It now ends at the figure, inside the cap, and is a
    span of the release."""
    row = next(r for r in _parse("wern_q3_2026").reconciliation if r.value == -0.03)
    assert rp.figure_stated(row.verbatim, -0.03, ("$",)) is not None, row.verbatim
    assert row.verbatim.endswith("diluted loss per share of $0.03")
    assert len(row.verbatim) <= rp.VERBATIM_CAP
    assert row.verbatim in _flat("wern_q3_2026")


def test_a_guide_range_is_quoted_with_both_of_its_bounds() -> None:
    """(-) TJX's Fiscal 2027 EPS guide: the quote stopped at "…earnings per share to be", before
    either bound. It now states both."""
    g = next(x for x in _parse("tjx_fy27_outlook").guidance if x.low == 4.93)
    assert g.high == 5.02
    for bound in (4.93, 5.02):
        assert rp.figure_stated(g.verbatim, bound, ("$",)) is not None, g.verbatim
    assert len(g.verbatim) <= rp.VERBATIM_CAP
    assert g.verbatim in _flat("tjx_fy27_outlook")


def test_a_quote_that_fits_the_cap_is_unchanged() -> None:
    """(+) NEGATIVE PIN: a window inside the cap keeps its bullet or sentence start, as before —
    the two WERN rows beside the cut one, and TJX's first-quarter guide."""
    recon = {r.value: r.verbatim for r in _parse("wern_q3_2026").reconciliation}
    assert recon[21.0] == ("Operating income of $17.0 million compared to an operating loss of "
                           "$13.0 million in the prior year; non-GAAP adjusted operating income of "
                           "$21.0 million")
    assert recon[0.16] == ("Diluted earnings per share of $0.11 compared to diluted loss per share "
                           "of $0.34 in the prior year; non-GAAP adjusted diluted earnings per "
                           "share of $0.16")
    q1 = next(x for x in _parse("tjx_fy27_outlook").guidance if x.low == 0.97)
    assert q1.verbatim == "diluted earnings per share to be in the range of $.97 to $.99"


def test_a_long_window_keeps_its_end_and_starts_on_a_whole_word() -> None:
    """(-) The rule on its own: over the cap, a STORED quote drops words from its START, never
    from its end, and never opens on half a word."""
    text = "• " + "abcdefghi " * 16 + "beta gamma delta epsilon zeta of the sum $1.25"
    assert len(" ".join(text[1:].split())) == 206          # six over: the cut lands mid-word
    vb = rp._verbatim(text, text.index("beta"), len(text), keep_end=True)
    assert vb.endswith("of the sum $1.25") and len(vb) <= rp.VERBATIM_CAP
    assert vb.split(" ")[0] == "abcdefghi"


def test_the_window_the_guidance_readers_decide_on_still_keeps_its_start() -> None:
    """(+) NEGATIVE PIN: the default window is the one the guidance readers decide on (its period,
    a superseded or withdrawn guide, the metrics its sentence names), so it is unchanged: over the
    cap it still keeps the sentence's start. Moving it dropped TJX's Fiscal 2027 guide, unflagged,
    in this fix's first draft (the period is read from the sentence's opening words)."""
    text = "Results. Outlook: " + "the company expects steady demand " * 12
    vb = rp._verbatim(text, text.index("Outlook"), len(text))
    assert vb.startswith("Outlook: the company expects") and len(vb) == rp.VERBATIM_CAP
