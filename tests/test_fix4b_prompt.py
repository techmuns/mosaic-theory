"""Fix 4b (2026-11-17): rule 7 no longer hands the model a rebuttal to copy, rule 13's example is
neutral, and rule 9 says what a path word claims.

#920 (`docs/records/2026-11-05-nflx-synthesis-causality-test.md`) drew NFLX's synthesis five times
per variant. The bear points that stayed closed by a rebuttal under its neutral example (V3) used
RULE 7's template — "a genuine counter-point, OUTWEIGHED by …" — in `mixed`-lean draws, where rule
7 never prescribed it; and its negative control (PATH) found "EBITDA margin has RISEN every step"
over a series that dips in FY2022. Every assertion here reads the prompt the request carries
(`system_for` / `tool_for`, which `vinci.evals.replay` pins equal to the captured request) or a
guard's behaviour. None reads LLM-composed text.

The drawdown anchor's question (item 2) is pinned in `tests/test_anchored_drawdown.py`.
"""
from __future__ import annotations

import hashlib
import json
import re

import pytest

from vinci.dossier import synthesis as syn
from vinci.dossier.schemas import FIGURE_OPERATIONS
from vinci.evals.metrics import PATH_WORDS
from vinci.sleeves import SLEEVES

#: RULE 7'S OLD REBUTTAL TEMPLATE — a closed list; each entry pinned live below. "outweigh" also
#: covers the tool schema's two restatements and the old rule-13 example's "genuine, but
#: outweighed by 121.4x coverage …".
OLD_REBUTTAL = ("outweigh", "genuine counter-point", "SURVIVES, qualified")

#: RULE 7 ITSELF, a code-written constant, so its exact text is pinned (as rule 8's is,
#: `tests/test_gap_test.py`). Moving it is a prompt change, measured on the panel (RUNBOOKS §n).
RULE_7_SHA256 = "19aea74a04ba6a1175c3ea9cdc0fad59cb532fe38aa6b9a16219b24f7e56a184"


def old_rebuttal(text: str) -> list[str]:
    return [w for w in OLD_REBUTTAL if w.lower() in text.lower()]


def _rule(sleeve: str, n: str, nxt: str) -> str:
    return f"({n}) " + syn.system_for(sleeve).split(f"({n}) ", 1)[1].split(f" ({nxt}) ", 1)[0]


def _example(sleeve: str) -> dict[str, object]:
    """Rule 13's one literal example, parsed from the prompt the request carries."""
    tail = syn.system_for(sleeve).split("one literal example: ", 1)[1]
    out = json.loads(tail)
    assert isinstance(out, dict)
    return out


@pytest.mark.parametrize("sleeve", sorted(SLEEVES))
def test_rule_7s_rebuttal_template_cannot_return(sleeve: str) -> None:
    """No book's system prompt or tool schema hands the model the rebuttal to copy."""
    assert old_rebuttal(syn.system_for(sleeve) + json.dumps(syn.tool_for(sleeve))) == []


@pytest.mark.parametrize("phrase", OLD_REBUTTAL)
def test_every_entry_of_the_old_rebuttal_list_is_live(phrase: str) -> None:
    assert old_rebuttal(syn.system_for("overshoot") + f" {phrase} ") == [phrase]


@pytest.mark.parametrize("sleeve", sorted(SLEEVES))
def test_rule_7_is_exactly_the_reworded_rule(sleeve: str) -> None:
    rule = _rule(sleeve, "7", "7b")
    assert hashlib.sha256(rule.encode()).hexdigest() == RULE_7_SHA256, rule


@pytest.mark.parametrize("sleeve", sorted(SLEEVES))
def test_the_framing_rule_7_prescribes_is_one_the_false_balance_guard_reads(sleeve: str) -> None:
    """Rule 7 still sizes a committed lean's minority, and the guard that checks the sizing
    (`_validate`'s G.2, `_OUTWEIGHED`) still recognises the framing rule 7 now asks for — so
    removing the rebuttal did not leave the guard asking for words the prompt no longer gives."""
    rule = _rule(sleeve, "7", "7b")
    prescribed = re.search(r"EACH stated as (what would have to be true for the <minority> case)",
                           rule)
    assert prescribed is not None, rule
    assert syn._OUTWEIGHED.search(prescribed.group(1).replace("<minority>", "bull"))
    for side in ("bull_points", "bear_points"):
        desc = str(syn.tool_for(sleeve)["input_schema"]["properties"][side]["description"])
        framing = re.search(r"state each as (what would have to be true for the \w+ case)", desc)
        assert framing is not None, desc
        assert syn._OUTWEIGHED.search(framing.group(1))


@pytest.mark.parametrize("sleeve", sorted(SLEEVES))
def test_rule_13s_example_is_neutral_and_its_shape_holds(sleeve: str) -> None:
    """The example states figures, closes on no counter, and keeps the shape rule 13 asks for:
    one entry per figure in claim order, each cited or derived from two figures the claim
    writes — and its derived figure computes."""
    ex = _example(sleeve)
    claim = str(ex["claim"])
    assert not re.search(r"\boutweigh\w*|\bgenuine\b|\bbut\b|\bthough\b|\boffset\w*", claim, re.I)
    figures = ex["figures"]
    assert isinstance(figures, list) and len(figures) == 7
    written = [str(f["figure"]) for f in figures]
    at = [claim.index(w) for w in written]
    assert at == sorted(at), "the entries follow the claim's order"
    derived = [f for f in figures if "derived" in f]
    assert len(derived) == 1 and all("source_ref" in f for f in figures if "derived" not in f)
    d = derived[0]
    assert d["derived"] in FIGURE_OPERATIONS and all(i in written for i in d["inputs"])

    def num(s: str) -> float:
        return float(s.strip("$Mx").replace(",", ""))

    a, b = (num(i) for i in d["inputs"])
    assert d["derived"] == "difference" and abs((a - b) - num(str(d["figure"]))) < 0.5


@pytest.mark.parametrize("sleeve", sorted(SLEEVES))
def test_rule_9_names_what_a_path_word_claims_and_m_path_counts_every_word_it_names(
        sleeve: str) -> None:
    """The path clause sits in rule 9, and each path word it names is one M-PATH counts — so
    the panel reads the words the rule is about."""
    rule = _rule(sleeve, "9", "10")
    clause = rule.split("A PATH word (", 1)[1].split(")", 1)[0]
    words = re.findall(r"'([^']+)'", clause)
    assert "every step" in words and len(words) >= 3
    assert all(PATH_WORDS.fullmatch(w) for w in words), words
    assert "every period the facts carry" in rule
