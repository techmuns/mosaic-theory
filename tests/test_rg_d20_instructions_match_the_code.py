"""RG-D20 (fix request 2, #1009): each of the thirteen instructions that contradicted another, or
the code, is pinned against what it describes. An edit to either side that reopens one reds here.

WHY. #1009 changed comments, docstrings and docs only, so no test failed before it. The fix log's
rule 3 has a `fixed` row name a test that failed before the fix and passes after, and there was
none to name. Each case reads the value or behaviour the instruction states and compares it with
the code's constant or behaviour. It does not merely check that the old sentence is gone. The
strings pinned are written by code and docs, never by an LLM, so exact pins are safe.

THE FAIL-FIRST. Eleven cases fail on #1009's parent `d6001465` and pass on `d8147e97`. The other
two, (b) and (j), pass on both, because #998 corrected them first as G-D15 and G-D14, which
#1009's record says; those two fail on #998's parent `7edbfa36`.

TWO ARE PINNED DOC AGAINST DOC. (e) holds CLAUDE.md's loop list against RUNBOOKS's live
sections; RUNBOOKS is the authority for those loops. (i) holds the CIQ notes' rule 4 against
the row numbers the notes quote. Neither has a code counterpart, and the fix log's rule 3 lets
such pure guidance read `fixed` on a document-level test (operator 2026-11-11, verbatim: "Allow
the narrow exception (Recommended)").

THE ITEMS are #1009's record's table, a to m
(`docs/records/2026-11-11-fix2-rg-d20-instructions-say-what-the-code-does.md`).
"""
from __future__ import annotations

import ast
import re
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from vinci.dossier import driver_extract, flags, synthesis
from vinci.evals.compare import BARRED_TARGETS, Registration
from vinci.graph import llm
from vinci.verbatim import comparison_key

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text()


def _flat(text: str) -> str:
    """One space for every run of whitespace, and a blockquote's `> ` removed, so a sentence
    wrapped across lines compares as one."""
    return " ".join(re.sub(r"(?m)^\s*>\s?", "", text).split())


def _messages_create_sites() -> set[str]:
    """Every file under `vinci/` holding a `….messages.create(…)` CALL (a docstring naming it
    is not a call)."""
    sites = set()
    for p in sorted((ROOT / "vinci").rglob("*.py")):
        for n in ast.walk(ast.parse(p.read_text())):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "create" and isinstance(n.func.value, ast.Attribute)
                    and n.func.value.attr == "messages"):
                sites.add(p.relative_to(ROOT).as_posix())
    return sites


def a_one_client_and_two_other_call_sites() -> None:
    """(a) llm.py's note names every other `messages.create` site the code has."""
    src = _read("vinci/graph/llm.py")
    start = src.index("#: Every LLM phase in the package")
    note = src[start:src.index("#: WHY ANYONE WOULD TRY.", start)]
    assert "runs through this one call site" not in note
    named = set(re.findall(r"`(vinci/[\w/]+\.py)`", note))
    assert _messages_create_sites() == {"vinci/graph/llm.py"} | named, (
        f"the code's call sites {sorted(_messages_create_sites())} are not the ones llm.py's "
        f"note names, {sorted(named)}")


def b_pass_no_sampling_parameter() -> None:
    """(b) engineering.md's rule names exactly the parameters the client refuses."""
    m = re.search(r"\*\*pass no sampling parameter\*\* — no ((?:`\w+`(?:, | or )?)+)",
                  _read("docs/engineering.md"))
    assert m, "engineering.md no longer says to pass no sampling parameter"
    assert tuple(re.findall(r"`(\w+)`", m.group(1))) == llm._REJECTED_SAMPLING_PARAMS


def c_the_directional_lint_reads_words_never_a_sign() -> None:
    """(c) The number trace's comment names the readers that compare a sign, and the lint it
    says reads words matches recommendation words and no signed figure. (Since fix request 2,
    RG-D1, the trace itself compares a PRINTED sign; a sign in words is still only compared for a
    material figure and a computed one, and the comment says so.)"""
    src = _read("vinci/dossier/synthesis.py")
    marker = "# Trace AS WRITTEN (RG-D1 to RG-D5"
    assert marker in src
    start = src.index(marker)
    block = re.match(r"(?:[ \t]*#.*\n)+", src[src.rindex("\n", 0, start) + 1:])
    assert block is not None
    comment = "".join(re.findall(r"(?m)^\s*#(.*)$", block.group()))
    assert "A printed sign must be the fact's (RG-D1)" in comment
    names = set(re.findall(r"`(\w+)`", comment)) - {"_ClaimFigure"}
    assert names == {"_DIRECTIONAL", "_recompute", "material_direction_flags"}
    assert all(callable(getattr(synthesis, n, None)) for n in names - {"_DIRECTIONAL"})
    assert synthesis._DIRECTIONAL.search("we recommend a buy here")
    for signed in ("revenue fell -12%", "+8% growth", "a decline of 27%", "margin −3.1 pts"):
        assert not synthesis._DIRECTIONAL.search(signed), signed


def d_a_transcript_figure_is_kept_and_flagged_machine_tier() -> None:
    """(d) synthesize()'s docstring says what the code does with a figure cited to a call. Since
    fix request 2, RG-D7 (2026-11-11): it is KEPT, traced to the call's validated figures, and one
    none of them states is a SHOWN UNTRACEABLE caveat naming the call — no longer a machine-tier
    TRANSCRIPT-FIGURE note. The old note stays in the QA list, for the flags older pages store."""
    doc = _flat(synthesis.synthesize.__doc__ or "")
    assert "no numbers are derived from it" not in doc
    assert "is KEPT, not refused, and traced to that call's VALIDATED figures" in doc
    assert "UNTRACEABLE caveat naming the call, shown on the page" in doc
    src = _read("vinci/dossier/synthesis.py")
    assert "[from the call {ref}]" in src and "f\"TRANSCRIPT-FIGURE '" not in src
    assert not flags.is_qa("UNTRACEABLE figure '12' in bull_point [from the call X]: 'x'")
    assert "TRANSCRIPT-FIGURE" in flags._QA_MARKERS
    assert flags.is_qa("TRANSCRIPT-FIGURE '12' in bull_points[0]: 'x' — from the cited call")


def _runbook_sections() -> dict[str, str]:
    return dict(re.findall(r"(?m)^## ([a-z](?:–[a-z])?)\. (.+)$", _read("docs/RUNBOOKS.md")))


def e_claude_md_names_only_live_runbook_loops() -> None:
    """(e) Doc against doc: every loop CLAUDE.md's header names is a live RUNBOOKS section, and
    the retired ones it says are retired are retired there."""
    claude = _flat(_read("CLAUDE.md"))
    m = re.search(r"\*\*The operating loops \((.+?)\) live in docs/RUNBOOKS\.md", claude)
    assert m, "CLAUDE.md's header no longer names the RUNBOOKS loops"
    sections = _runbook_sections()
    live = [h.lower().replace("-", " ") for h in sections.values() if "RETIRED" not in h]
    for loop in (x.strip() for x in m.group(1).split(",")):
        hits = [h for h in live if loop.lower().replace("-", " ") in h]
        assert len(hits) == 1, f"CLAUDE.md names {loop!r}; live RUNBOOKS sections matching: {hits}"
    assert "The theme loops §a–d and the calendar §h retired 2026-11-04" in claude
    assert "RETIRED 2026-11-04" in sections["a–d"] and "RETIRED 2026-11-04" in sections["h"]


def f_agents_md_names_its_exceptions_and_the_test_holding_one() -> None:
    """(f) AGENTS.md names the test that holds its review rules equal to the styleguide's, and
    that test reads those two files."""
    agents = _flat(_read("AGENTS.md"))
    assert "TWO DELIBERATE EXCEPTIONS" in agents
    node = "tests/test_review_process.py::test_codex_and_gemini_are_given_the_same_checks"
    assert f"`{node}`" in agents
    tree = ast.parse(_read("tests/test_review_process.py"))
    fn = next(n for n in tree.body
              if isinstance(n, ast.FunctionDef) and n.name == node.rsplit("::", 1)[1])
    used = {x.id for x in ast.walk(fn) if isinstance(x, ast.Name)}
    assert {"AGENTS", "STYLEGUIDE"} <= used
    consts = {t.id: ast.unparse(n.value) for n in tree.body if isinstance(n, ast.Assign)
              for t in n.targets if isinstance(t, ast.Name)}
    assert "'AGENTS.md'" in consts["AGENTS"] and "'styleguide.md'" in consts["STYLEGUIDE"]


def g_the_gemini_config_is_inert() -> None:
    """(g) The Gemini config says it is inert, and nothing the repo runs invokes Gemini."""
    assert "INERT: it is NOT installed" in _read(".gemini/config.yaml")
    runners = [*(ROOT / ".github" / "workflows").glob("*.yml"),
               *(ROOT / ".claude" / "hooks").glob("*.py"), ROOT / ".claude" / "settings.json"]
    assert runners and not [p.name for p in runners if "gemini" in p.read_text().lower()]


def _registers_as_a_target(metric: str) -> bool:
    """Whether `register` takes `metric` as a target. Two refusals: `register` refuses a target
    in `BARRED_TARGETS` before it builds anything (order 8, RG-D13), and `Registration` refuses
    an unknown one with a ValueError; any other error means `Registration`'s shape moved, and
    this helper must follow it. A barred target still CONSTRUCTS, so #927's registration loads as
    history, which is why the constructor alone no longer answers the question."""
    if metric in BARRED_TARGETS:
        return False
    try:
        Registration(base_ref="a", cand_ref="b", transforms=(), pages=("BURL",), draws=2,
                     targets=(metric,), held_out=(), scorer="s")
    except ValueError:
        return False
    return True


def h_runbooks_names_m_gap_as_a_target_exactly_when_register_takes_it() -> None:
    """(h) RUNBOOKS §n step 1 names M-GAP as a target if and only if `register` accepts it."""
    runbooks = _read("docs/RUNBOOKS.md")
    step1 = runbooks[runbooks.index("1. **Declare the TARGET"):]
    step1 = _flat(step1[:step1.index("\n2. ")])
    assert "today only `M-LABEL`" not in step1
    assert ("`M-GAP` joined it" in step1) == _registers_as_a_target("M-GAP")
    assert ("barred as a target" in step1) == (not _registers_as_a_target("M-GAP"))
    assert _registers_as_a_target("M-LABEL") and "`M-LABEL`" in step1


_ROW = re.compile(r"\b((?:header )?rows? ~?\d+(?:-\d+)?)\b")


def i_every_quoted_row_number_is_marked_orientation() -> None:
    """(i) Doc against doc: rule 4 says not to hardcode positions, and lists, as orientation only,
    exactly the row numbers the notes quote elsewhere."""
    lines = _read("docs/ciq_extraction_notes.md").splitlines()
    rule4_head = "4. **Header position is not fixed.**"
    at = next(i for i, x in enumerate(lines) if x.startswith(rule4_head))
    rule4 = lines[at]
    assert "Do not hardcode positions." in rule4 and "for orientation only" in rule4
    assert "find each row by its label, never by the number" in rule4
    listed = set(re.findall(r'"((?:header )?rows? ~?\d+(?:-\d+)?)"', rule4))
    quoted = {r for i, x in enumerate(lines) if i != at for r in _ROW.findall(x)}
    assert quoted and quoted == listed, f"quoted but not marked: {sorted(quoted - listed)}"


def j_no_checklist_md_is_tracked() -> None:
    """(j) The notes say checklist.md is not in this repository, and git tracks none."""
    assert "**`checklist.md` is not in this repository**" in _read("docs/ciq_extraction_notes.md")
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True,
                             check=True).stdout.splitlines()
    assert not [f for f in tracked if f.rsplit("/", 1)[-1] == "checklist.md"]


def _imports(rel: str) -> set[str]:
    """Every module a file imports, `from x import y` read as `x` and as `x.y`."""
    out = set()
    for n in ast.walk(ast.parse(_read(rel))):
        if isinstance(n, ast.Import):
            out |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            out |= {n.module} | {f"{n.module}.{a.name}" for a in n.names}
    return out


def k_driver_extract_keeps_its_own_norm() -> None:
    """(k) Covenants check quotes through the shared helper, while driver_extract keeps its own
    `_norm` (whitespace and case only), so a curly quote matches in one and not the other."""
    assert "`driver_extract` has NOT moved onto it" in _flat(_read("vinci/verbatim.py"))
    assert "own `_norm` folds whitespace and case only" in _flat(driver_extract.__doc__ or "")
    assert "vinci.verbatim" in _imports("vinci/dossier/covenant_extract.py")
    assert "vinci.verbatim" not in _imports("vinci/dossier/driver_extract.py")
    curly, straight = "“Growth”  ROSE", '"growth" rose'
    assert comparison_key(curly) == comparison_key(straight)
    assert driver_extract._norm(curly) != driver_extract._norm(straight)
    assert driver_extract._norm("A \n B") == driver_extract._norm("a b")


def l_the_trigger_doc_reads_by_symbol() -> None:
    """(l) The cloud-trigger doc says its `file:line` references are dated, and cites no
    `config.py` line that is not `require_env`'s."""
    doc = _read("docs/CLOUD_DOSSIER_TRIGGER.md")
    assert "references in this proposal are as of 2026-06-26 and have moved since" in _flat(doc)
    line = next(i for i, x in enumerate(_read("vinci/config.py").splitlines(), 1)
                if x.startswith("def require_env("))
    stale = [n for n in re.findall(r"config\.py:(\d+)", doc) if int(n) != line]
    assert not stale, f"config.py:{stale} cited; require_env is at line {line}"


def m_the_mypy_count_is_the_one_mypy_prints() -> None:
    """(m) engineering.md's gate count names its commit, and equals that commit's `vinci/`
    source files, the count `mypy --strict vinci` prints."""
    m = re.search(r"(\d+) files at `([0-9a-f]{7,40})`", _read("docs/engineering.md"))
    assert m, "engineering.md states no mypy file count at a named commit"
    if subprocess.run(["git", "cat-file", "-e", f"{m.group(2)}^{{commit}}"], cwd=ROOT,
                      capture_output=True).returncode:
        pytest.skip(f"{m.group(2)} is not in this clone (shallow?)")
    names = subprocess.run(["git", "ls-tree", "-r", "--name-only", m.group(2), "vinci"], cwd=ROOT,
                           capture_output=True, text=True, check=True).stdout.splitlines()
    assert int(m.group(1)) == sum(n.endswith(".py") for n in names)


CASES: dict[str, Callable[[], None]] = {f.__name__[0]: f for f in (
    a_one_client_and_two_other_call_sites, b_pass_no_sampling_parameter,
    c_the_directional_lint_reads_words_never_a_sign,
    d_a_transcript_figure_is_kept_and_flagged_machine_tier,
    e_claude_md_names_only_live_runbook_loops,
    f_agents_md_names_its_exceptions_and_the_test_holding_one, g_the_gemini_config_is_inert,
    h_runbooks_names_m_gap_as_a_target_exactly_when_register_takes_it,
    i_every_quoted_row_number_is_marked_orientation, j_no_checklist_md_is_tracked,
    k_driver_extract_keeps_its_own_norm, l_the_trigger_doc_reads_by_symbol,
    m_the_mypy_count_is_the_one_mypy_prints)}


def test_all_thirteen_items_are_pinned() -> None:
    assert sorted(CASES) == list("abcdefghijklm")


@pytest.mark.parametrize("item", sorted(CASES))
def test_rg_d20_each_instruction_says_what_the_code_does(item: str) -> None:
    CASES[item]()
