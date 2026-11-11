"""A TEST THAT LAUNCHES NODE SKIPS WHERE NODE IS ABSENT — IT NEVER CRASHES (fix request 2, RH-D6).

THE DEFECT. Four tests in `tests/test_sleeves.py` meant to skip without node by reading the child's
stderr. But `subprocess.run(["node", ...])` raises `FileNotFoundError` before any stderr exists, so
on a machine without node they FAILED (measured by the audit: `{'failed': 4}` with node removed
from PATH). A fifth, the decision-log render, had the same sniff behind an earlier skip that hid
it. The sniff was also wrong in the other direction: with node PRESENT, a script whose error read
"not found" (a missing export, a moved module) was skipped as "node unavailable", and one test
skipped on ANY non-zero exit, so a broken page passed as a skip.

THE INVARIANT. Every call in tests/ that launches node sits in a function that checks for node
first: `shutil.which` in its body or its decorators, an `except FileNotFoundError`, a module-level
`pytestmark` that checks — or a helper whose every caller in its module does. Measured on the
corpus at main `173b4818`: 89 launches in 41 files, 5 unguarded, all in `tests/test_sleeves.py`.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_LAUNCHERS = {"run", "check_output", "check_call", "call", "Popen"}


def _launches_node(call: ast.Call) -> bool:
    f = call.func
    name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
    if name not in _LAUNCHERS or not call.args:
        return False
    first = call.args[0]
    return (isinstance(first, (ast.List, ast.Tuple)) and bool(first.elts)
            and isinstance(first.elts[0], ast.Constant) and first.elts[0].value == "node")


def _is_node_which(call: ast.Call) -> bool:
    """`shutil.which("node")` (or `which(<a variable>)`) — a `which` for another tool is not a
    check for node."""
    f = call.func
    if not ((isinstance(f, ast.Attribute) and f.attr == "which")
            or (isinstance(f, ast.Name) and f.id == "which")):
        return False
    first = call.args[0] if call.args else None
    return not isinstance(first, ast.Constant) or first.value == "node"


def _checks_for_node(node: ast.AST, site: int | None = None) -> bool:
    """A `which("node")` in it — BEFORE line ``site`` when one is given (a decorator's line is
    before its body) — or a `try` whose body holds line ``site`` and whose handler catches
    FileNotFoundError."""
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and _is_node_which(n) and (site is None or n.lineno < site):
            return True
        if (isinstance(n, ast.Try) and n.body
                and (site is None or n.body[0].lineno <= site <= (n.body[-1].end_lineno or 0))
                and any(h.type is not None and any(
                    isinstance(x, ast.Name) and x.id == "FileNotFoundError"
                    for x in ast.walk(h.type)) for h in n.handlers)):
            return True
    return False


def unguarded_node_launches(source: str) -> list[tuple[int, str]]:
    """``(line, function)`` of every node launch no node check covers, in one module's source."""
    tree = ast.parse(source)
    if any(isinstance(s, ast.Assign) and any(getattr(t, "id", "") == "pytestmark"
                                            for t in s.targets) and _checks_for_node(s)
           for s in tree.body):
        return []
    # A list, not a dict by name: two functions of one name (methods of two classes) are both read.
    funcs = [f for f in ast.walk(tree) if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))]
    sites: dict[str, list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, int]]] = {
        f.name: [] for f in funcs}
    for f in funcs:
        for n in ast.walk(f):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in sites:
                sites[n.func.id].append((f, n.lineno))

    def covered(fn: ast.FunctionDef | ast.AsyncFunctionDef, site: int,
                seen: frozenset[str] = frozenset()) -> bool:
        if _checks_for_node(fn, site):
            return True
        if fn.name.startswith("test_") or fn.name in seen or not sites[fn.name]:
            return False
        return all(covered(c, line, seen | {fn.name}) for c, line in sites[fn.name])

    out = []
    for f in funcs:
        for n in ast.walk(f):
            if isinstance(n, ast.Call) and _launches_node(n) and not covered(f, n.lineno):
                out.append((n.lineno, f.name))
    return sorted(set(out))


def test_every_node_launch_in_the_suite_checks_for_node_first() -> None:
    """POSITIVE, on the live corpus: no test file launches node unguarded."""
    found = {p.relative_to(ROOT).as_posix(): bad
             for p in sorted((ROOT / "tests").rglob("*.py"))
             if (bad := unguarded_node_launches(p.read_text()))}
    launches = sum(1 for p in (ROOT / "tests").rglob("*.py")
                   for n in ast.walk(ast.parse(p.read_text()))
                   if isinstance(n, ast.Call) and _launches_node(n))
    assert launches > 50, f"only {launches} node launches found — the scan stopped seeing them"
    assert not found, (
        f"node is launched with no check that it exists: {found}. Without node, "
        "subprocess raises FileNotFoundError before any stderr exists, so the test FAILS instead "
        "of skipping. Put `if not shutil.which(\"node\"): pytest.skip(\"node unavailable\")` "
        "before the launch.")


def test_the_scan_refuses_each_unguarded_shape() -> None:
    """NEGATIVE PINS, each the real failure shape: a stderr sniff after the launch; a helper whose
    one caller does not check; and the controls it must accept — a check in the body, in a
    decorator, an `except FileNotFoundError`, a module mark, a helper whose callers all check."""
    sniff = ('import subprocess\ndef test_x():\n    p = subprocess.run(["node", "-e", "1"])\n'
             '    if "not found" in p.stderr:\n        pytest.skip("node unavailable")\n')
    assert unguarded_node_launches(sniff) == [(3, "test_x")]
    helper = ('import subprocess, shutil\ndef _web():\n    return subprocess.run(["node"])\n'
              '@pytest.mark.skipif(not shutil.which("node"), reason="")\n'
              'def test_a():\n    _web()\ndef test_b():\n    _web()\n')
    assert unguarded_node_launches(helper) == [(3, "_web")]
    # A check that does not cover the launch: a `which` for another tool, a `which("node")` after
    # it, a FileNotFoundError handler on a `try` that does not hold it — and a launch in the second
    # of two same-named methods, which a by-name map dropped.
    for bad, line in (
        ('import shutil, subprocess\ndef test_x():\n    shutil.which("git")\n'
         '    subprocess.run(["node"])\n', 4),
        ('import shutil, subprocess\ndef test_x():\n    subprocess.run(["node"])\n'
         '    shutil.which("node")\n', 3),
        ('import subprocess\ndef test_x():\n    try:\n        open("f")\n'
         '    except FileNotFoundError:\n        pass\n    subprocess.run(["node"])\n', 7),
        ('import shutil, subprocess\nclass A:\n    def test_r(self):\n'
         '        subprocess.run(["node"])\nclass B:\n    def test_r(self):\n'
         '        if not shutil.which("node"):\n            return\n'
         '        subprocess.run(["node"])\n', 4),
    ):
        assert [ln for ln, _ in unguarded_node_launches(bad)] == [line], bad
    for ok in (
        'import shutil, subprocess\ndef test_x():\n    if not shutil.which("node"):\n'
        '        pytest.skip("")\n    subprocess.run(["node"])\n',
        'import subprocess\ndef test_x():\n    try:\n        subprocess.run(["node"])\n'
        '    except FileNotFoundError:\n        pytest.skip("")\n',
        'import shutil, subprocess\npytestmark = pytest.mark.skipif(not shutil.which("node"),'
        ' reason="")\ndef test_x():\n    subprocess.run(["node"])\n',
        helper.replace("def test_b():\n    _web()\n", ""),
        'import subprocess\ndef test_x():\n    subprocess.run(["python", "-c", "1"])\n',
    ):
        assert unguarded_node_launches(ok) == [], ok
