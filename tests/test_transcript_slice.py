"""The earnings calls the model reads are whole, and a call it does not get is named (audit G-D3,
G-D4; operator ruling 2026-10-29, "Whole transcripts").

Transcript text is licensed and never committed, so each call here is INVENTED and written as a
real RTF file, then read through the production path: `CiqBundle.from_files` classifies it,
`ciq.read_text` decodes it with striprtf, `_transcript_prose` strips the boilerplate, and
`transcript_for_synthesis` builds the slice that both the driver phase and the synthesis receive.
The prompt pins read the prompt the model is SENT, not the helper's return.
"""

from __future__ import annotations

import typing
from pathlib import Path

from vinci.dossier import ciq
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.driver_extract import extract_transcript_drivers
from vinci.dossier.flags import partition
from vinci.graph.llm import LlmClient

#: Said in the Q&A, well past the 12,000 characters the slice used to stop at.
_IN_THE_QA = "Our largest customer told us it will cut orders by a third next quarter."
_FILLER = ("We continue to execute against our plan across every region and channel, and the "
           "team remains focused on the priorities we set out at the start of the year. ")


def _rtf(text: str) -> str:
    body = "".join("\\pard " + line.replace("\\", "\\\\") + "\\par\n" for line in text.split("\n"))
    return "{\\rtf1\\ansi\\deff0{\\fonttbl{\\f0\\fswiss Arial;}}\n" + body + "}"


def _call(remarks_chars: int, qa: str = _IN_THE_QA, qa_chars: int = 4_000) -> str:
    """An invented call: the operator's hand-off, prepared remarks of about `remarks_chars`, then
    the Q&A with `qa` in it."""
    remarks = (_FILLER * (remarks_chars // len(_FILLER) + 1))[:remarks_chars]
    rest = (_FILLER * (qa_chars // len(_FILLER) + 1))[:qa_chars]
    return ("Forward-looking statements legalese that the prose strip removes.\n"
            "I will now turn the call over to our Chief Executive Officer.\n"
            f"{remarks}\n\nQuestion and Answer\n\nOperator: our first question.\n"
            f"{qa} {rest}")


def _bundle(tmp_path: Path, calls: dict[str, str]) -> ciq.CiqBundle:
    paths = []
    for name, text in calls.items():
        p = tmp_path / name
        p.write_text(text, encoding="utf-8")
        paths.append(p)
    return ciq.CiqBundle.from_files("ACME", paths)


_Q1 = "Acme, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf"
_Q4 = "Acme, Inc., Q4 2025 Earnings Call, Feb 12, 2026.rtf"


def test_the_q_and_a_past_twelve_thousand_characters_reaches_the_slice(tmp_path: Path) -> None:
    """FAILED on 8a38005a: every call was cut at 12,000 characters with no marker, so a call whose
    remarks run past that sent no Q&A at all — 37 of the 48 committed calls."""
    b = _bundle(tmp_path, {_Q1: _rtf(_call(remarks_chars=20_000))})
    s = cs.transcript_for_synthesis(b)
    assert s is not None
    assert "Question and Answer" in s and _IN_THE_QA in s
    assert cs._CUT_MARKER not in s
    assert cs.unparsed_transcript_flag(b, s) is None


def test_a_call_past_the_ceiling_ends_in_a_marker_and_is_flagged(tmp_path: Path) -> None:
    """The safety ceiling is the only cut, and it says so where it cuts — in the text the model
    reads, and in a QA flag naming the call."""
    b = _bundle(tmp_path, {_Q1: _rtf(_call(remarks_chars=130_000))})
    s = cs.transcript_for_synthesis(b)
    assert s is not None
    body = s.split("\n", 1)[1]
    assert cs._CUT_MARKER in body
    assert body.index(cs._CUT_MARKER) == cs._TRANSCRIPT_CEILING + 1  # cut at the ceiling, then said
    assert _IN_THE_QA not in s
    flag = cs.unparsed_transcript_flag(b, s)
    assert flag is not None and flag.startswith("transcript cut at the ceiling") and _Q1 in flag
    caveats, qa = partition([flag])
    assert qa == [flag] and caveats == []


def test_a_call_that_does_not_read_beside_one_that_does_is_named(tmp_path: Path) -> None:
    """FAILED on 8a38005a: the flag fired only when NO call read, so a failed read beside a sibling
    that read left the model a call short in silence (audit G-D4). An RTF that striprtf reads as
    almost no words is the reader's own "OLE-disguised" refusal — the shape a LibreOffice
    conversion failure takes too."""
    unreadable = "{\\rtf1\\ansi " + "\\par " * 1_500 + "}"
    b = _bundle(tmp_path, {_Q1: _rtf(_call(remarks_chars=5_000)), _Q4: unreadable})
    s = cs.transcript_for_synthesis(b)
    assert s is not None and f"--- {_Q1} ---" in s and _Q4 not in s
    flag = cs.unparsed_transcript_flag(b, s)
    assert flag is not None and "1 of 2" in flag and _Q4 in flag and _Q1 not in flag
    caveats, qa = partition([flag])
    assert qa == [flag] and caveats == []


def test_every_call_read_whole_raises_no_flag(tmp_path: Path) -> None:
    """The negative half: two calls on file, both read, neither past the ceiling — no flag."""
    b = _bundle(tmp_path, {_Q1: _rtf(_call(remarks_chars=5_000)),
                           _Q4: _rtf(_call(remarks_chars=6_000))})
    s = cs.transcript_for_synthesis(b)
    assert s is not None and f"--- {_Q1} ---" in s and f"--- {_Q4} ---" in s
    assert cs.unparsed_transcript_flag(b, s) is None


class _Capture(LlmClient):
    def __init__(self, reply: dict[str, typing.Any]) -> None:
        self.reply, self.users = reply, []  # type: list[str]

    @property
    def model(self) -> str:
        return "capture"

    def extract(self, *, system: str, user: str, tool: dict[str, typing.Any],
                cache: bool = False) -> dict[str, typing.Any]:
        self.users.append(user)
        return self.reply


def test_both_model_phases_are_sent_the_q_and_a_and_the_prompt_says_whole(tmp_path: Path) -> None:
    """End to end, on the prompts the model is SENT: the driver extraction and the synthesis both
    receive the Q&A sentence, and the synthesis is told the calls are whole — on 8a38005a it read
    "Prepared remarks + Q&A, mechanically bounded" over a slice that held no Q&A."""
    from tests.test_dossier import _minimal_mech
    from vinci.dossier import synthesis as syn

    s = cs.transcript_for_synthesis(_bundle(tmp_path, {_Q1: _rtf(_call(remarks_chars=20_000))}))
    drivers = _Capture({"drivers": []})
    extract_transcript_drivers(s, llm=drivers, ticker="ACME", name="Acme")
    assert _IN_THE_QA in drivers.users[0]
    synthesis = _Capture({"evidence_balance": "mixed — test", "bull_points": [], "bear_points": [],
                          "twin_reference_cases": [], "key_unknowns": [],
                          "decisive_question": {"question": "q?", "evidence_for": [],
                                                "evidence_against": []}})
    syn.synthesize(_minimal_mech(), llm=synthesis, ticker="ACME", name="Acme", transcript=s)
    sent = synthesis.users[0]
    assert _IN_THE_QA in sent
    assert "Each call is WHOLE" in sent and "mechanically bounded" not in sent
