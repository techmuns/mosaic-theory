"""The machine proposal's vote rule, as decided (`docs/records/2026-11-10-the-proposal-vote-rule-
design.md` §9: Option A + C(iii) + C(iv); independence not falsified,
`docs/records/2026-11-11-vote-rule-independence-measured.md`).

- **R1:** the gate is a one-sided exact binomial test that the lean is the input's majority read,
  at 5%. At five draws it passes only 5 of 5, which is today's rule exactly.
- **R3:** a failed, unparsed or unrecognized draw is dissent. The denominator is the draws
  ATTEMPTED, so a build with 1 of 5 completed no longer reads as agreement (§2's first hole).
- **The spelling key:** the tally keys a label as the mapping does, so two spellings of one lean
  are one lean (§2's second hole).
- **R4/R5:** the split rides on the tally and is printed beside the proposal; old artifacts decide
  as they always did.
- **C(iii):** proposed, borderline or none.

Run against main `e73e7a54`, every test here fails except two GUARDS that pass there by design:
`test_an_old_tally_serializes_as_it_was_written` and `test_an_old_page_renders_as_it_did` pin
that what was built before the rule is unchanged by it.
"""
from __future__ import annotations

import json
import typing
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

_LEANS = {
    "bull": "strongly-bullish — the runway outruns the multiple.",
    "Bull": "Strongly bullish — the same lean, spelled the other way.",
    "mixed": "mixed — two-sided and unresolved.",
    "odd": "mixed-to-bullish — not one of the three.",
}


def _payload(lean: str, draw: int) -> dict[str, typing.Any]:
    return {
        "evidence_balance": lean,
        "bull_points": [{"claim": f"c-draw{draw}", "source_ref": "r"}],
        "bear_points": [{"claim": "c", "source_ref": "r"}],
        "twin_reference_cases": [],
        "decisive_question": {"question": "q?", "evidence_for": [], "evidence_against": []},
        "key_unknowns": ["u"],
    }


class _Scripted:
    """One scripted lean per draw; ``"fail"`` raises the way a broken tool call does."""

    def __init__(self, leans: list[str]) -> None:
        self._leans, self.calls = leans, 0

    @property
    def model(self) -> str:
        return "scripted"

    def extract(self, *, system: str, user: str, tool: dict[str, typing.Any],
                cache: bool = False) -> dict[str, typing.Any]:
        from vinci.graph.llm import LlmError
        lean = self._leans[self.calls]
        self.calls += 1
        if lean == "fail":
            raise LlmError("tool call incomplete")
        return _payload(_LEANS[lean], self.calls)


def _synth(leans: list[str]) -> tuple[typing.Any, list[str]]:
    from tests.test_dossier import _minimal_mech
    from vinci.dossier import synthesis as syn
    s, flags, _ = syn.synthesize(_minimal_mech(), llm=_Scripted(leans), ticker="X", name="X Co",
                                 sleeve="quality", draws=len(leans))
    return s, flags


# ------------------------------------------------------------------- R1 and the spelling key


def test_r1_is_the_one_sided_binomial_test_and_is_today_s_rule_at_five() -> None:
    from vinci.dossier import verdict as v
    assert [v.r1_required(n) for n in (5, 9, 10, 20)] == [5, 8, 9, 15]
    # (−) below five draws no tally can pass a 5% test: four of four is 1 in 16
    assert v.r1_required(4) == 5


def test_one_key_for_the_tally_and_the_mapping() -> None:
    from vinci.dossier import verdict as v
    assert v.lean_key("Strongly bullish") == v.lean_key("strongly-bullish") == "strongly-bullish"
    assert v.lean_key("  Mixed ") == "mixed"


@pytest.mark.parametrize(("labels", "attempted", "want"), [
    (["strongly-bullish"] * 5, 5, ("strongly-bullish", 5, True, "proposed")),
    (["strongly-bullish"] * 4 + ["mixed"], 5, ("strongly-bullish", 4, False, "borderline")),
    (["strongly-bullish"] * 3 + ["mixed"] * 2, 5, ("strongly-bullish", 3, False, "borderline")),
    (["mixed"] * 5, 5, ("mixed", 5, False, "none")),                 # mixed proposes nothing
    (["strongly-bullish"], 5, ("strongly-bullish", 1, False, "none")),     # 1 of 5 completed
    (["strongly-bullish"] * 4, 5, ("strongly-bullish", 4, False, "borderline")),  # one failed
    (["Strongly bullish"] * 2 + ["strongly-bullish"] * 3, 5,
     ("strongly-bullish", 5, True, "proposed")),                     # two spellings, one lean
    (["strongly-bearish"] * 9 + ["mixed"], 10, ("strongly-bearish", 9, True, "proposed")),
    ([], 5, ("", 0, False, "none")),
])
def test_the_gate_on_one_build(labels: list[str], attempted: int,
                               want: tuple[str, int, bool, str]) -> None:
    from vinci.dossier import verdict as v
    g = v.draw_gate(labels, attempted)
    assert (g.lean, g.count, g.passes, g.state) == want
    assert g.required == v.r1_required(attempted) and g.attempted == attempted


# ------------------------------------------------------------------- through synthesize


def test_one_completed_draw_of_five_no_longer_proposes() -> None:
    """(−) §2's first hole: four failed draws and one bullish one recorded unanimous and
    proposed. The tally still records that the completed draw agreed with itself; the gate reads
    the draws ATTEMPTED and withholds, and the page says why."""
    from vinci.dossier.verdict import derive_proposal
    s, flags = _synth(["fail", "fail", "bull", "fail", "fail"])
    a = s.draw_agreement
    assert (a.attempted, a.completed, a.unanimous) == (5, 1, True)
    assert (a.passes, a.gate().state, a.modal_count, a.required) == (False, "none", 1, 5)
    prop = derive_proposal(s.evidence_balance, sleeve="quality", gate=a.gate())
    assert prop.action is None and prop.state == "none"
    assert any("1 of 5 draws" in f and "dissent" in f for f in flags)


def test_two_spellings_of_one_lean_are_one_lean() -> None:
    """(+) §2's second hole: "Strongly bullish" and "strongly-bullish" both map to BUY, but the
    tally made them two buckets, so a build split only by spelling was withheld."""
    from vinci.dossier.verdict import derive_proposal
    s, _ = _synth(["Bull", "bull", "Bull", "bull", "bull"])
    a = s.draw_agreement
    assert a.labels == {"strongly-bullish": 5} and a.unanimous and a.passes
    assert derive_proposal(s.evidence_balance, sleeve="quality", gate=a.gate()).action is not None


def test_an_unrecognized_lean_is_dissent() -> None:
    from vinci.dossier.verdict import derive_proposal
    s, _ = _synth(["bull", "bull", "odd", "bull", "bull"])
    a = s.draw_agreement
    assert (a.modal_count, a.passes, a.gate().state) == (4, False, "borderline")
    prop = derive_proposal(s.evidence_balance, sleeve="quality", gate=a.gate())
    assert prop.action is None and prop.state == "borderline"
    assert "4 of 5" in prop.note and "borderline" in prop.note


def test_a_proposal_carries_its_split() -> None:
    """(+) R4: the split rides beside every proposal, as a count with its rule — never a rate."""
    from vinci.dossier.verdict import derive_proposal
    s, _ = _synth(["bull"] * 5)
    prop = derive_proposal(s.evidence_balance, sleeve="quality", gate=s.draw_agreement.gate())
    assert prop.action is not None and prop.state == "proposed"
    assert prop.split == "5 of 5 draws strongly-bullish (the 5-of-5 rule)"


# ------------------------------------------------------------------- C7: nothing on file moves


def _pages() -> list[dict[str, typing.Any]]:
    out = []
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        doc = json.loads(p.read_text())
        if (doc.get("synthesis") or {}).get("draw_agreement"):
            out.append(doc)
    return out


#: The UTC day the vote rule landed on main (`83258405`; `docs/records/2026-11-11-the-vote-rule-
#: implemented.md`): a page assembled before it cannot have been built with R1's gate.
RULE_DAY = "2026-11-11"


def _decides_as_it_did(doc: dict[str, typing.Any]) -> bool:
    """One committed page's C7 check; True when it is a page built after the rule.

    A page written before the rule carries no `passes`, so its proposal is read from `unanimous`
    exactly as before — and R1 on its own tally agrees with it. A page built after the rule (from
    the 2026-11-14 rebuild on) records R1's gate, and that gate is the one R1 computes from the
    same page's tally — so its proposal is the rule's, never a stored verdict the tally does not
    reproduce. WHICH OF THE TWO is the page's assembly date, not the presence of `passes`: an old
    page that gained the rule's fields would otherwise be read as a new one (#1067's review)."""
    from vinci.dossier import verdict as v

    def decision(g: v.DrawGate) -> tuple[object, ...]:
        # the decision fields; `labels` is the printed split, whose tie order the two readers
        # break differently (by name on the record, by draw order on a live build)
        return (g.lean, g.count, g.attempted, g.required, g.passes, g.state)

    t, assembled = doc["ticker"], str(doc.get("assembled_at") or "")
    s, da = doc["synthesis"], doc["synthesis"]["draw_agreement"]
    sleeve = doc.get("sleeve") or "overshoot"
    labels = [lab for lab, n in da["labels"].items() for _ in range(n)]
    gate = v.draw_gate(labels, da["attempted"])
    new = v.derive_proposal(s.get("evidence_balance"), sleeve=sleeve, gate=gate)
    if assembled[:10] >= RULE_DAY:   # built after the rule: R1's gate, on the recorded tally
        assert "passes" in da, f"{t}: assembled {assembled}, after the rule, records no gate"
        recorded = v.DrawGate.from_record(da)
        assert recorded is not None, t
        assert decision(recorded) == decision(gate), t
        assert v.derive_proposal(s.get("evidence_balance"), sleeve=sleeve,
                                 gate=recorded).action == new.action, t
        return True
    assert "passes" not in da, (
        f"{t}: assembled {assembled}, before the rule ({RULE_DAY}), carries R1's gate")
    old = v.derive_proposal(s.get("evidence_balance"), sleeve=sleeve,
                            draws_unanimous=da["unanimous"])
    assert old.action == new.action, t
    return False


def test_every_committed_page_decides_as_it_did() -> None:
    """(+) C7 on the live corpus, page by page (`_decides_as_it_did`)."""
    pages = _pages()
    assert len(pages) >= 19
    post_rule = [doc["ticker"] for doc in pages if _decides_as_it_did(doc)]
    # NON-VACUITY: the post-rule branch ran on real pages (NCNO, SMPL and TJX from 2026-11-14), so
    # a reader that stopped finding them would red here rather than pass by skipping the branch
    assert len(post_rule) >= 3, post_rule


def test_a_page_built_before_the_rule_that_carries_its_gate_is_refused() -> None:
    """(-) #1067's review mutant: ROST's 2026-10-29 page (frozen), its own tally given R1's fields
    consistent with it — an OLD page that gained the rule's fields. Chosen by `passes` alone, the
    check read it as a post-rule page and passed it; read by its assembly date, it is refused."""
    from vinci.dossier import verdict as v

    doc = json.loads((ROOT / "tests" / "fixtures" / "frozen_pages" / "2026-10-29" / "ROST"
                      / "dossier.json").read_text())
    assert _decides_as_it_did(doc) is False   # (+) as frozen: a pre-rule page, deciding as it did
    da = doc["synthesis"]["draw_agreement"]
    labels = [lab for lab, n in da["labels"].items() for _ in range(n)]
    g = v.draw_gate(labels, da["attempted"])
    da.update(modal_count=g.count, required=g.required, passes=g.passes,
              rule="R1: one-sided exact binomial test that the lean is the majority read, at 5%")
    assert v.DrawGate.from_record(da) is not None   # a valid gate, consistent with the tally
    with pytest.raises(AssertionError, match="before the rule"):
        _decides_as_it_did(doc)


def test_an_old_tally_serializes_as_it_was_written() -> None:
    """(+) The new fields are omitted while unset, so a page written before them re-serializes
    byte for byte (the refresh's no-op rule)."""
    from vinci.dossier.schemas import DrawAgreement
    da = DrawAgreement(attempted=5, completed=5, labels={"mixed": 5}, unanimous=True)
    assert set(json.loads(da.model_dump_json())) == {"attempted", "completed", "labels",
                                                     "unanimous"}


# ------------------------------------------------------------------- R4 on both renderers


def _with_gate(doc: dict[str, typing.Any], labels: dict[str, int], attempted: int = 5,
               completed: int | None = None) -> dict[str, typing.Any]:
    """A committed page whose tally is rewritten as a build under R1 would record it — the gate
    computed by `verdict.draw_gate`, never hand-set."""
    from vinci.dossier import verdict as v
    seq = [lab for lab, n in labels.items() for _ in range(n)]
    g = v.draw_gate(seq, attempted)
    doc = json.loads(json.dumps(doc))
    doc["synthesis"]["draw_agreement"] = {
        "attempted": attempted, "completed": len(seq) if completed is None else completed,
        "labels": labels, "unanimous": len(labels) == 1, "modal_count": g.count,
        "required": g.required, "passes": g.passes, "rule": v.GATE_RULE}
    return doc


@pytest.mark.parametrize(("labels", "want"), [
    ({"strongly-bullish": 5}, "the rule is met"),
    ({"strongly-bullish": 4, "mixed": 1}, "BORDERLINE"),
    ({"strongly-bullish": 2}, "a failed draw counts as dissent"),
])
def test_the_markdown_and_the_web_print_the_same_split(labels: dict[str, int], want: str) -> None:
    """(+) R4 on both renderers of a committed page: the same split, from one rule. The web is
    the JS twin (`drawGateSplit`), checked against `DrawGate.split` itself."""
    import shutil
    import subprocess

    from vinci.dossier.render import _draw_agreement_md
    from vinci.dossier.schemas import Synthesis
    from vinci.dossier.verdict import DrawGate
    doc = _with_gate(json.loads((ROOT / "data/dossiers/LLY/dossier.json").read_text()), labels)
    split = DrawGate.from_record(doc["synthesis"]["draw_agreement"]).split
    md = "\n".join(_draw_agreement_md(Synthesis.model_validate(doc["synthesis"])))
    assert split in md and want in md
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const dj = pathToFileURL(path.resolve("frontend/views/shared/dossier.js")).href;
const { renderDossier } = await import(dj);
const html = renderDossier(JSON.parse(readFileSync(0, "utf8")), null);
console.log(JSON.stringify(html.replace(/\s+/g, " ")));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver], input=json.dumps(doc),
                         capture_output=True, text=True, check=True, cwd=ROOT)
    html = json.loads(out.stdout)
    assert " ".join(split.split()) in html and want in html


def test_an_old_page_renders_as_it_did() -> None:
    """(+) C7: a pre-rule page's tally (no `passes`) prints the old line, word for word. LLY's
    2026-11-03 page, frozen: its living page, rebuilt 2026-11-14, records R1's gate."""
    from vinci.dossier.render import _draw_agreement_md
    from vinci.dossier.schemas import Synthesis
    doc = json.loads((ROOT / "tests/fixtures/frozen_pages/2026-11-03/LLY/dossier.json").read_text())
    md = "\n".join(_draw_agreement_md(Synthesis.model_validate(doc["synthesis"])))
    assert "Reproducibility" in md and "rule" not in md
