"""Y18 (operator 2026-11-18, "Reword it now"): the drawdown anchor's no-cause ASK names no shape.

Fix 4b (#1094) asked an at-anchor part with no gap-down "the part at the follow shows no discrete
gap-down, so it names no cause". On the panel, 2 of 5 MCK draws restated that and filled it with
"a gradual bleed" ("bleed/run-up", "bleed/rise"): a shape named as if it were a cause, the label
#923 removed from the mechanical layer. MCK's frozen panel page still carries that label in its
ROLLING `drawdown_cause.shape` ("gradual bleed — no discrete gap-down detected", committed before
#923), so the ASK's phrase pointed at the one line of the request that holds the word.

The reworded ASK says the part names no cause, never what its price did. It asks for what is dated
and sourced after the anchor, or a plain statement that the page identifies no cause. A part whose
drops carry no company filing, or which could not be read, keeps its reason, and every no-cause
branch asks the same question after it. A part that names its cause keeps #1094's question byte for
byte.

Structure and guard behaviour only. The ASK is code-composed text, never an LLM string; nothing
here pins what a draw writes (CLAUDE.md TEST-LAYER RULE).
"""
from __future__ import annotations

import re
import subprocess
from typing import Any

import pytest

from tests.frozen_support import covered_where
from tests.test_anchored_drawdown import _ask, _brief_with_at_anchor, _built
from vinci.dossier.schemas import Dossier, Sourced
from vinci.dossier.synthesis import NOT_SENT, _drawdown_anchor_digest, _mark_drawdown_guidance
from vinci.evals import replay as rp
from vinci.evals.capture_child import capture_calls
from vinci.evals.metrics import _GRADUAL, LABEL_FAMILIES

#: The words that describe a price PATH: the gap-down detector's own vocabulary ("no discrete
#: gap-down") and the M-LABEL `bleed` family the registered scorer counts (its regex and its
#: "gradual" clause test, imported, never restated).
_GAP_WORDS = re.compile(r"gap-down|\bdiscrete\b", re.I)
_PLAIN = "say plainly that the page identifies no cause"


def _shape_words(text: str) -> list[str]:
    return [m.group(0) for rx in (_GAP_WORDS, LABEL_FAMILIES["bleed"], _GRADUAL)
            for m in rx.finditer(text)]


def _no_gap() -> dict[str, Any]:
    """SMPL's own `since` window: a real no-gap-down `DrawdownWindow`, read (shape PRESENT)."""
    since: dict[str, Any] = _built()["mechanical"]["drawdown_cause"]["anchor"]["since"]
    assert since["gaps"] == [] and since["shape"]["status"] == "present"
    return since


def _no_filing() -> dict[str, Any]:
    """SMPL's at-underwrite drops with their 8-K accessions removed: NCNO's and TECX's case."""
    at = _built()["mechanical"]["drawdown_cause"]["anchor"]["at_anchor"]
    out: dict[str, Any] = {**at, "filings": [], "gaps": [
        {**g, "cause": "no company filing", "accession": None} for g in at["gaps"]]}
    assert out["gaps"]
    return out


def _unread() -> dict[str, Any]:
    at = _built()["mechanical"]["drawdown_cause"]["anchor"]["at_anchor"]
    return {**at, "gaps": [],
            "gap_down_dates": Sourced[list[str]].unknown(note="EDGAR unavailable").model_dump(),
            "shape": Sourced[str].unknown(note="EDGAR filing index unavailable").model_dump()}


# ─── the three no-cause branches, on SMPL's real anchored build ──────────────────────────────

def test_a_part_with_no_gap_down_is_told_it_names_no_cause_and_nothing_about_its_shape() -> None:
    """(−) The defect: "shows no discrete gap-down" described an absence as a shape. The ASK now
    states only that the part names no cause: no reason clause, no word for the price's path."""
    ask = _ask(_brief_with_at_anchor(_no_gap()))
    assert ask.startswith("ASK: the part at the underwrite names no cause — never state or "
                          "assume one.")
    assert _shape_words(ask) == [], _shape_words(ask)


def test_every_no_cause_branch_asks_one_question_after_its_reason() -> None:
    """(+) What is dated and sourced after the anchor, or a plain statement that the page
    identifies no cause: the same words after each branch's reason, so the three cannot drift."""
    asks = {k: _ask(_brief_with_at_anchor(at())) for k, at in
            (("no gap-down", _no_gap), ("no filing", _no_filing), ("unread", _unread))}
    head = "ASK: the part at the underwrite names no cause"
    tails = set()
    for k, ask in asks.items():
        assert ask.startswith(head), (k, ask)
        assert "cause named at the" not in ask, k
        assert "dated and sourced after the underwrite" in ask, k
        assert _PLAIN in ask, k
        tails.add(ask[ask.index(" — never state or assume one."):])
    assert len(tails) == 1, tails


def test_a_part_whose_drops_have_no_filing_says_the_drops_are_there() -> None:
    """(−) NCNO's underwrite and TECX's follow each hold a gap-down with no company filing. Its
    reason names the missing FILING. It never says "no gap-down": the part has one, and an absence
    read off it is the misreading the reword removes."""
    ask = _ask(_brief_with_at_anchor(_no_filing()))
    assert "(none of its drops carries a company filing)" in ask
    assert "no gap-down" not in ask and "discrete" not in ask


def test_an_unread_part_says_why_and_never_that_it_had_no_drop() -> None:
    """(−) An UNKNOWN shape is a part that could not be read, not a part with no drop."""
    ask = _ask(_brief_with_at_anchor(_unread()))
    assert "(it could not be read: UNKNOWN)" in ask
    assert _shape_words(ask) == []


def test_the_no_gap_ask_reads_the_parts_structure_never_its_shape_string() -> None:
    """(guard) The pre-#923 label MCK's and NFLX's committed pages still carry ("gradual bleed —
    no discrete gap-down detected") and the current one give the SAME ask, and it quotes neither:
    the branch is read from `gaps` and the shape's status, never from its words."""
    legacy = {**_no_gap(), "shape": {**_no_gap()["shape"],
                                      "value": "gradual bleed — no discrete gap-down detected"}}
    now = _ask(_brief_with_at_anchor(_no_gap()))
    assert _ask(_brief_with_at_anchor(legacy)) == now
    assert _shape_words(now) == []


# ─── end to end: the request the frozen panel pages send ─────────────────────────────────────

_PANEL = rp.load_panel_file()


def _panel_request_user(ticker: str) -> str:
    """The USER text ``synthesize`` sends for the frozen panel page, captured at $0. The
    drawdown digest reads no transcript, so none is passed."""
    if subprocess.run(["git", "-C", str(rp.ROOT), "cat-file", "-e",
                       f"{_PANEL['freeze_ref']}^{{commit}}"], capture_output=True).returncode:
        pytest.skip("the panel's freeze commit is not in this history")
    page = rp.page_at(ticker, _PANEL["freeze_ref"],
                      expect_blob=_PANEL["pages"][ticker]["dossier_blob"])
    (call,) = capture_calls(page, None, draws=1)
    return "\n".join(c if isinstance(c := m["content"], str)
                     else "\n".join(str(b["text"]) for b in c if "text" in b)
                     for m in call["messages"])


def test_mcks_panel_request_asks_its_no_cause_question_without_a_shape_word() -> None:
    """(− · e2e) MCK, the panel page the defect was drawn on. The CHECK FINDS the word in this very
    request first — the frozen rolling label still says "gradual bleed" — so its silence on the ASK
    line is the ASK's, not a blind check (CORPUS BEFORE SYNTHETIC)."""
    user = _panel_request_user("MCK")
    assert "gradual bleed" in user                     # the facts' JSON escapes the dash
    assert _shape_words(user)                          # the check can find it here
    (ask,) = [ln for ln in user.splitlines() if ln.startswith("ASK: ")]
    assert ask.startswith("ASK: the part at the follow names no cause — never state or assume "
                          "one.")
    assert "dated and sourced after the follow" in ask and _PLAIN in ask
    assert _shape_words(ask) == [], _shape_words(ask)


def test_smpls_panel_request_keeps_its_named_question() -> None:
    """(+ · e2e) SMPL names its drops: the question every earlier build sent, unchanged."""
    user = _panel_request_user("SMPL")
    (ask,) = [ln for ln in user.splitlines() if ln.startswith("ASK: ")]
    assert ask.startswith("ASK: has the cause named at the underwrite played out?")
    assert _PLAIN not in ask


# ─── the invariant on every covered page with an anchor ──────────────────────────────────────

def _committed_ask(page: dict[str, Any]) -> str:
    doc = Dossier.model_validate(page)
    assert doc.mechanical is not None
    dumped = doc.mechanical.model_dump(exclude=NOT_SENT)
    _mark_drawdown_guidance(dumped, doc.mechanical.primary_source)
    digest = _drawdown_anchor_digest(dumped)
    assert digest is not None
    return _ask(digest)


def test_every_anchored_page_asks_a_no_cause_question_with_no_shape_word() -> None:
    """(roster walk) Each covered page carrying an anchor gets one ASK at its next build. One that
    names no cause is asked for what is dated and sourced after it, never told its part's shape;
    one that names its cause keeps the played-out question. Both sides must be present."""
    rows = covered_where(lambda _t, d: isinstance(
        ((d.get("mechanical") or {}).get("drawdown_cause") or {}).get("anchor"), dict),
        "carries a drawdown anchor")
    named, unnamed = [], []
    for t, page in rows:
        ask = _committed_ask(page)
        if ask.startswith("ASK: has the cause named at the "):
            named.append(t)
            continue
        unnamed.append(t)
        assert " names no cause" in ask and _PLAIN in ask, (t, ask)
        assert _shape_words(ask) == [], (t, _shape_words(ask))
    assert named and unnamed, (named, unnamed)
