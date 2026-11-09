"""THE FIX LOG CANNOT ROT SILENTLY — `docs/fix-log-teamnostra-2.md`, TeamNostra's fix request 2.

The log is the one place two agents on two machines, and TeamNostra, read who has which ID and what
is done. A log nobody checks drifts the way STATE.md §5 did: a row says `fixed` for work that never
landed, an ID is dropped, a status is invented. So this reads it and refuses:

1. a duplicate ID, an ID in the record's scope with no row, a row whose ID is outside the scope,
   or a row whose Order is not the scope's. The scope is the ``fix-log-scope`` block of
   `docs/records/2026-11-09-teamnostra-fix-request-2.md`, which is immutable once merged;
2. a status outside the five the record allows;
3. a `fixed` row that does not name a commit reachable from `origin/main` or a PR merged there, or
   does not name a test node that exists under `tests/` (a `test*` function, or a `test*` method of
   a `Test*` class — what pytest collects; a parametrize id is not checked).

Each check has a negative pin: a planted bad row it must reject. The git checks use real shapes:
`4449189d`, #923's squashed branch head, which a test named and no clone could reach (#928); and
#917, closed unmerged on 2026-11-05.

The git checks need `origin/main` and full history. On a shallow clone they SKIP with the reason
rather than error, because a test erroring on a shallow clone is TeamNostra's RH-D5. CI checks out
full history (`gate.yml`, `fetch-depth: 0`), so there they run.
"""
from __future__ import annotations

import ast
import functools
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "docs" / "fix-log-teamnostra-2.md"
RECORD = ROOT / "docs" / "records" / "2026-11-09-teamnostra-fix-request-2.md"

HEADER = "| ID | Order | Status | Commit or PR | Test | Pages rebuilt |"
RULE = "|---|---|---|---|---|---|"
#: Document 14's R-IDs, the verifiers' V-IDs, and document 11's IDs (F-S1..3 are its F notes).
ID = re.compile(r"R(?:A|BC|D|E1|E2|F|FL|G|H)-D\d+|V[12]-[NO]\d+|(?:A|BC|D|E1|E2|G|H)-D\d+|F-S\d+")
STATUS = re.compile(r"open|in progress \(#\d+\)|fixed|not fixing: \S.*|disagree: \S.*")
SHA = re.compile(r"\b[0-9a-f]{7,40}\b")
PR = re.compile(r"#(\d+)\b")
NODE = re.compile(r"(tests/[\w/]+\.py)((?:::[\w]+(?:\[[^\]]*\])?)+)")
SCOPE_BLOCK = re.compile(r"^```fix-log-scope\n(.*?)^```", re.M | re.S)
RUN = re.compile(r"(.+-D)(\d+)\.\.(\d+)")


@dataclass(frozen=True)
class Row:
    line: int
    id: str
    order: str
    status: str
    ref: str
    test: str
    pages: str


def parse_log(text: str) -> tuple[list[Row], list[str]]:
    """The table's rows, and every structural problem: no header, a row that is not six cells (a
    `|` inside a cell splits it), or table lines after the table ends. A malformed row is REPORTED,
    never skipped."""
    lines = text.splitlines()
    if HEADER not in lines:
        return [], [f"the log has no header line {HEADER!r}"]
    h = lines.index(HEADER)
    problems: list[str] = []
    if h + 1 >= len(lines) or lines[h + 1].strip() != RULE:
        problems.append(f"line {h + 2}: the header is not followed by {RULE!r}")
    rows: list[Row] = []
    end = len(lines)
    for n in range(h + 2, len(lines)):
        line = lines[n].strip()
        if not line.startswith("|"):
            end = n
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not line.endswith("|") or len(cells) != 6:
            problems.append(f"line {n + 1}: {len(cells)} cells, not 6 — a '|' inside a cell? "
                            f"{line!r}")
            continue
        rows.append(Row(n + 1, *cells))
    stray = [n + 1 for n in range(end, len(lines)) if lines[n].lstrip().startswith("|")]
    if stray:
        problems.append(f"table lines after the log's table ends, which nothing checks: {stray}")
    return rows, problems


def scope(record_text: str) -> dict[str, list[str]]:
    """ID → the order labels the record's ``fix-log-scope`` blocks give it; ``P-Dn..m`` is a
    run of IDs.

    EVERY block, not the first. The record's body is immutable once merged, and its scope must
    still be able to grow: document 15 §6 also asks for a row for any document 11 ID TeamNostra
    marks fixed that we dispute. Such an ID enters by a dated entry under the record's
    ``## Amendments`` heading, carrying its own block — the one change the ledger allows."""
    blocks = SCOPE_BLOCK.findall(record_text)
    if not blocks:
        raise LookupError("the record has no ```fix-log-scope block — the scope is unreadable")
    out: dict[str, list[str]] = {}
    for line in "".join(blocks).splitlines():
        if not line.strip():
            continue
        label, colon, tokens = line.partition(":")
        if not colon:
            raise ValueError(f"scope line {line!r} has no '<order>:' label")
        for tok in tokens.split():
            run = RUN.fullmatch(tok)
            if run and int(run.group(2)) >= int(run.group(3)):
                raise ValueError(f"scope run {tok!r} is empty or backwards")
            ids = ([f"{run.group(1)}{i}" for i in range(int(run.group(2)), int(run.group(3)) + 1)]
                   if run else [tok])
            for x in ids:
                if not ID.fullmatch(x):
                    raise ValueError(f"scope token {tok!r} is not an ID")
                out.setdefault(x, []).append(label.strip())
    return out


@functools.cache
def _test_names(path: str) -> frozenset[str]:
    """Every `test*` function and `Test*::test*` method a test file defines — pytest's default
    collection names (`pyproject.toml` sets no other) — read by `ast` (never imported). A helper
    such as `_row`, or a non-test class, is not a test node."""
    tree = ast.parse((ROOT / path).read_text())
    func = (ast.FunctionDef, ast.AsyncFunctionDef)
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, func) and node.name.startswith("test"):
            names.add(node.name)
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            names.update(f"{node.name}::{f.name}" for f in node.body
                         if isinstance(f, func) and f.name.startswith("test"))
    return frozenset(names)


def _node_problem(node: str) -> str | None:
    m = NODE.fullmatch(node)
    if not m:
        return f"{node!r} is not a test node id (tests/<file>.py::<test>)"
    path, rest = m.group(1), m.group(2)
    if not (ROOT / path).is_file():
        return f"{path} does not exist"
    name = re.sub(r"\[[^\]]*\]$", "", rest[2:])
    if name not in _test_names(path):
        return f"{path} defines no test {name!r}"
    return None


def problems(rows: list[Row], in_scope: dict[str, list[str]]) -> list[str]:
    """Every check that needs no git: IDs, the scope, statuses, and a `fixed` row's test node."""
    out: list[str] = []
    seen: dict[str, int] = {}
    for r in rows:
        if not ID.fullmatch(r.id):
            out.append(f"line {r.line}: {r.id!r} is not an ID")
        if r.id in seen:
            out.append(f"line {r.line}: duplicate ID {r.id} (first at line {seen[r.id]})")
        seen.setdefault(r.id, r.line)
        if r.id not in in_scope:
            out.append(f"line {r.line}: {r.id} is not in the record's scope")
        elif {o.strip() for o in r.order.split(",")} != set(in_scope[r.id]):
            out.append(f"line {r.line}: {r.id}'s Order {r.order!r} is not the scope's "
                       f"{', '.join(in_scope[r.id])!r}")
        if not STATUS.fullmatch(r.status):
            out.append(f"line {r.line}: {r.id} has status {r.status!r} — allowed: open, "
                       f"in progress (#N), fixed, not fixing: <reason>, disagree: <evidence>")
        if r.status == "fixed":
            nodes = [m.group(0) for m in NODE.finditer(r.test.replace("`", ""))]
            if not nodes:
                out.append(f"line {r.line}: {r.id} is fixed and names no test node")
            out += [f"line {r.line}: {r.id}'s test: {p}"
                    for p in map(_node_problem, nodes) if p]
            if not SHA.findall(r.ref) and not PR.findall(r.ref):
                out.append(f"line {r.line}: {r.id} is fixed and names no commit or PR")
    missing = sorted(set(in_scope) - set(seen))
    if missing:
        out.append(f"{len(missing)} scope ID(s) with no row: {missing}")
    return out


class MainHistory:
    """`origin/main` as this checkout holds it. Raises `LookupError` when it cannot be read whole
    (no git, no `origin/main`, or a shallow clone, where an old commit would look unreachable)."""

    def __init__(self) -> None:
        def git(*args: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                                  timeout=60)
        self._git = git
        try:
            head = git("rev-parse", "--verify", "--quiet", "origin/main^{commit}")
            shallow = git("rev-parse", "--is-shallow-repository")
            if head.returncode:
                raise LookupError("no origin/main in this checkout — fetch it")
            if shallow.stdout.strip() == "true":
                raise LookupError("a shallow clone: a real old commit would read as unreachable")
            # First parent only: main's own commits, never a merged branch's working commits.
            log = git("log", "--first-parent", "origin/main", "--format=%s")
        except (OSError, subprocess.SubprocessError) as exc:
            raise LookupError(f"git unavailable: {exc}") from exc
        if log.returncode:
            raise LookupError(f"git log origin/main failed: {log.stderr.strip()}")
        subjects = log.stdout.splitlines()
        squash = (re.search(r"\(#(\d+)\)\s*$", s) for s in subjects)
        merge = (re.match(r"Merge pull request #(\d+)\b", s) for s in subjects)
        self.merged_prs = frozenset(int(m.group(1)) for m in (*squash, *merge) if m)

    def reachable(self, sha: str) -> bool | None:
        """True or False: an ancestor of origin/main or not. None: git cannot resolve `sha` to
        one commit here (unknown, or an ambiguous prefix) — reported as its own cause."""
        return {0: True, 1: False}.get(
            self._git("merge-base", "--is-ancestor", sha, "origin/main").returncode)


def landed_problems(rows: list[Row], main: MainHistory) -> list[str]:
    """A `fixed` row's every commit is reachable from origin/main and its every PR merged there."""
    out: list[str] = []
    for r in rows:
        if r.status != "fixed":
            continue
        for sha in SHA.findall(r.ref):
            ok = main.reachable(sha)
            if ok is None:
                out.append(f"line {r.line}: {r.id} names commit {sha}, not reachable from "
                           f"origin/main (git cannot resolve it to one commit here)")
            elif not ok:
                out.append(f"line {r.line}: {r.id} names commit {sha}, not reachable from "
                           f"origin/main")
        out += [f"line {r.line}: {r.id} names PR #{n}, not merged on origin/main"
                for n in map(int, PR.findall(r.ref)) if n not in main.merged_prs]
    return out


@functools.lru_cache(maxsize=1)
def _main() -> MainHistory:
    try:
        return MainHistory()
    except LookupError as exc:
        pytest.skip(f"origin/main cannot be read whole here: {exc}")


def _live() -> tuple[str, dict[str, list[str]]]:
    return LOG.read_text(), scope(RECORD.read_text())


def _row(status: str, ref: str = "—", test: str = "—", rid: str = "RBC-D1") -> str:
    return f"| {rid} | 2 | {status} | {ref} | {test} | — |"


def _with(text: str, rid: str, new: str | None) -> str:
    """The live log with `rid`'s row replaced by `new` (or deleted when None). Fails loudly if the
    row is not there, so a pin can never pass because it planted nothing."""
    lines = text.splitlines()
    hits = [i for i, x in enumerate(lines) if x.startswith(f"| {rid} |")]
    assert len(hits) == 1, f"the live log has {len(hits)} rows for {rid}"
    if new is None:
        del lines[hits[0]]
    else:
        lines[hits[0]] = new
    return "\n".join(lines) + "\n"


SELF = "tests/test_fix_log.py::test_the_live_log_is_clean"


# ── the live log, and the scope it is read against ────────────────────────────────────────────


def test_the_live_log_is_clean() -> None:
    text, in_scope = _live()
    rows, structure = parse_log(text)
    assert not structure + problems(rows, in_scope)
    if any(r.status == "fixed" for r in rows):
        assert not landed_problems(rows, _main())


def test_the_scope_block_is_read_as_the_record_counts_it() -> None:
    """The parser against the record's own numbers (§1): 178 IDs; the per-order counts; the two
    over-range IDs reached only through `A-D17..24`; RG-D22 folded into RH-D5."""
    in_scope = scope(RECORD.read_text())
    assert len(in_scope) == 178
    counts = {lab: sum(lab in labs for labs in in_scope.values())
              for lab in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "§4", "—")}
    assert counts == {"1": 7, "2": 7, "3": 26, "4": 44, "5": 19, "6": 15, "7": 5, "8": 8, "9": 10,
                      "10": 5, "§4": 30, "—": 5}
    assert {"A-D23", "A-D24"} <= set(in_scope) and "RG-D22" not in in_scope
    assert sorted(x for x, labs in in_scope.items() if len(labs) > 1) == [
        "E2-D10", "E2-D11", "E2-D15"]


# ── negative pins: a planted bad row each check must reject ───────────────────────────────────


def test_a_duplicate_id_is_rejected() -> None:
    text, in_scope = _live()
    planted = text.rstrip("\n") + "\n" + _row("open") + "\n"
    rows, structure = parse_log(planted)
    assert not structure
    assert any("duplicate ID RBC-D1" in p for p in problems(rows, in_scope))


@pytest.mark.parametrize("rid", ["RBC-D1", "A-D24"])  # A-D24 is in scope only through a run
def test_a_scope_id_with_no_row_is_rejected(rid: str) -> None:
    text, in_scope = _live()
    rows, _ = parse_log(_with(text, rid, None))
    assert any("with no row" in p and rid in p for p in problems(rows, in_scope))


def test_an_id_outside_the_scope_is_rejected() -> None:
    """RG-D22 is folded into RH-D5 (record §6, item 1) and must have no row of its own."""
    text, in_scope = _live()
    planted = text.rstrip("\n") + "\n" + _row("open", rid="RG-D22").replace("| 2 |", "| 6 |") + "\n"
    rows, structure = parse_log(planted)
    assert not structure
    assert any("RG-D22 is not in the record's scope" in p for p in problems(rows, in_scope))


@pytest.mark.parametrize("rid, order", [("RBC-D1", "9"), ("E2-D10", "1"), ("E2-D10", "1, 4")])
def test_an_order_that_is_not_the_scopes_is_rejected(rid: str, order: str) -> None:
    text, in_scope = _live()
    rows, _ = parse_log(_with(text, rid, f"| {rid} | {order} | open | — | — | — |"))
    assert any(f"{rid}'s Order" in p for p in problems(rows, in_scope))


@pytest.mark.parametrize("block", ["1: RE2-D4..1", "1: RE2-D4..4", "1 RE2-D1 RE2-D2"])
def test_a_malformed_scope_line_is_refused(block: str) -> None:
    with pytest.raises(ValueError):
        scope(f"```fix-log-scope\n{block}\n```\n")


def test_an_amendment_block_extends_the_scope() -> None:
    """A disputed document 11 ID joins through an appended block (G-D6 here is only an example);
    were the second block ignored, its row would be refused as outside the scope."""
    record = RECORD.read_text() + "\n## Amendments\n\n```fix-log-scope\n—: G-D6\n```\n"
    in_scope = scope(record)
    assert in_scope["G-D6"] == ["—"] and len(in_scope) == 179
    text, _ = _live()
    planted = text.rstrip("\n") + "\n| G-D6 | — | disagree: example | — | — | — |\n"
    rows, _ = parse_log(planted)
    assert not problems(rows, in_scope)
    assert any("G-D6 is not in the record's scope" in p
               for p in problems(rows, scope(RECORD.read_text())))


@pytest.mark.parametrize("status", [
    "done", "Fixed", "closed", "in progress", "in progress (932)", "in progress #932",
    "not fixing:", "not fixing", "disagree", "disagree: ", "OPEN"])
def test_a_status_outside_the_five_is_rejected(status: str) -> None:
    text, in_scope = _live()
    rows, _ = parse_log(_with(text, "RBC-D1", _row(status)))
    assert any("RBC-D1 has status" in p for p in problems(rows, in_scope))


@pytest.mark.parametrize("status", [
    "open", "in progress (#932)", "not fixing: no production caller; removed instead",
    "disagree: the page already reads it (record §3)"])
def test_the_four_unconditional_statuses_pass(status: str) -> None:
    text, in_scope = _live()
    rows, _ = parse_log(_with(text, "RBC-D1", _row(status)))
    assert not problems(rows, in_scope)


def test_a_pipe_inside_a_cell_is_reported_not_dropped() -> None:
    text, in_scope = _live()
    _rows, structure = parse_log(_with(text, "RBC-D1", _row("not fixing: a | b")))
    assert any("7 cells, not 6" in p for p in structure)


@pytest.mark.parametrize("test, why", [
    ("—", "names no test node"),
    ("`tests/test_no_such_file.py::test_x`", "does not exist"),
    ("`tests/test_fix_log.py::test_no_such_test`", "defines no test 'test_no_such_test'"),
    ("`tests/test_fix_log.py::_row`", "defines no test '_row'"),            # a helper
    ("`tests/test_fix_log.py::MainHistory::reachable`", "defines no test"),  # not a Test* class
])
def test_a_fixed_row_must_name_a_test_that_exists(test: str, why: str) -> None:
    text, in_scope = _live()
    rows, _ = parse_log(_with(text, "RBC-D1", _row("fixed", "622786a2 (#927)", test)))
    assert any(why in p for p in problems(rows, in_scope))


def test_a_fixed_row_must_name_a_commit_or_pr() -> None:
    text, in_scope = _live()
    rows, _ = parse_log(_with(text, "RBC-D1", _row("fixed", "—", f"`{SELF}`")))
    assert any("names no commit or PR" in p for p in problems(rows, in_scope))


def test_a_fixed_row_naming_landed_work_and_a_real_test_passes() -> None:
    text, in_scope = _live()
    rows, _ = parse_log(_with(text, "RBC-D1", _row(
        "fixed", "622786a2 (#927)", f"`{SELF}`, `tests/test_fix_log.py::"
                                    "test_a_scope_id_with_no_row_is_rejected[A-D24]`")))
    assert not problems(rows, in_scope)
    assert not landed_problems(rows, _main())


@pytest.mark.parametrize("ref, why", [
    ("4449189d", "commit 4449189d, not reachable"),   # #923's squashed branch head (#928)
    ("#917", "PR #917, not merged"),                  # closed unmerged, 2026-11-05
    ("622786a2 (#917)", "PR #917, not merged"),       # one good ref does not excuse a bad one
])
def test_a_fixed_row_naming_work_that_never_landed_is_rejected(ref: str, why: str) -> None:
    text, _ = _live()
    rows, _ = parse_log(_with(text, "RBC-D1", _row("fixed", ref, f"`{SELF}`")))
    assert any(why in p for p in landed_problems(rows, _main()))
