"""NO TEST WRITES A PATH IN THE CHECKOUT: IT WRITES IN A TEMP DIRECTORY OR IN pytest's `tmp_path`.

2026-11-20. WHY. Four tests wrote a node driver and its JSON into a fixed folder in the checkout
root, `ROOT / ".pytest_wNN_tmp"`, ran node on it, then removed it with `rmtree` (W50, W61, W62 and
W73; W62's test has since been deleted). A measurement on main `ac3c9479` (2026-11-19) named the
costs:
- on workers (pytest-xdist) one test's `rmtree` can delete another's driver mid-run. W61's `_web()`
  is `@cache`d per process, and its 4 callers can land on two workers;
- the folder is not git-ignored, so a killed run leaves it untracked, and the next `bin/commit`
  refuses the checkout;
- CI's ctime check cannot see a folder that is made and removed inside the run (#1072).

The guard reads the AST of every module under `tests/` (the hand-run generators in
`tests/fixtures/` aside) and refuses two shapes:
- a call that WRITES (mkdir, write_text, rmtree, open for writing, a copy's destination, …) on a
  path built from the module's own location: `Path(__file__)…`, or a name bound to one, such as
  `ROOT`. It keys on what the call does, not on the folder's name, so `ROOT / "build_w90"` is
  refused as `ROOT / ".pytest_w61_tmp"` was;
- a path in the checkout that names a `.pytest_*` folder (pytest's own `.pytest_cache` aside). Such
  a name is a scratch folder by intent, even where a child process does the writing.

Not covered: a child process that writes relative to its `cwd=ROOT` (a static scan cannot see
inside it), and a path built from a value the module does not bind to its own location.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: Path methods that write, create or remove what they are called on.
_PATH_WRITES = frozenset({"mkdir", "write_text", "write_bytes", "touch", "symlink_to",
                          "hardlink_to", "unlink", "rmdir", "rename"})
#: Module functions that write their argument at this index.
_FUNC_WRITES = {("shutil", "rmtree"): 0, ("shutil", "copy"): 1, ("shutil", "copy2"): 1,
                ("shutil", "copyfile"): 1, ("shutil", "copytree"): 1, ("shutil", "move"): 1,
                ("os", "makedirs"): 0, ("os", "mkdir"): 0, ("os", "remove"): 0,
                ("os", "unlink"): 0, ("os", "rmdir"): 0, ("os", "rename"): 1,
                ("os", "replace"): 1}
#: Path methods and attributes that return another path in the same tree, or paths under it.
_PATH_STEPS = frozenset({"resolve", "absolute", "joinpath", "with_name", "with_suffix",
                         "with_stem", "parent", "parents", "glob", "rglob", "iterdir"})


def _is_own_location(node: ast.AST) -> bool:
    """`Path(__file__)`."""
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "Path" and len(node.args) == 1
            and isinstance(node.args[0], ast.Name) and node.args[0].id == "__file__")


def _in_checkout(node: ast.AST, names: set[str]) -> bool:
    """True when `node` is a path built from the module's own location: `Path(__file__)` or a name
    bound to one, through `/`, `.parent`, `.parents[i]`, `.resolve()` and `.joinpath(…)`."""
    while True:
        if _is_own_location(node):
            return True
        if isinstance(node, ast.Name):
            return node.id in names
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            node = node.left
        elif isinstance(node, ast.Subscript) or (isinstance(node, ast.Attribute)
                                                 and node.attr in _PATH_STEPS):
            node = node.value
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
              and node.func.attr in _PATH_STEPS):
            node = node.func.value
        else:
            return False


def _bound(scope: ast.AST, names: set[str]) -> set[str]:
    """`names` plus every name `scope` binds to a path in the checkout, to a fixed point."""
    out = set(names)
    while True:
        before = len(out)
        for node in ast.walk(scope):
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if _in_checkout(node.value, out):
                    out |= {t.id for t in targets if isinstance(t, ast.Name)}
            elif isinstance(node, ast.For) and isinstance(node.target, ast.Name):
                if _in_checkout(node.iter, out):
                    out.add(node.target.id)
        if len(out) == before:
            return out


def _opens_for_writing(call: ast.Call, at: int) -> bool:
    """`call`'s mode, positional at `at` or `mode=`, writes, appends, creates or updates."""
    mode = call.args[at] if len(call.args) > at else next(
        (k.value for k in call.keywords if k.arg == "mode"), None)
    return (isinstance(mode, ast.Constant) and isinstance(mode.value, str)
            and any(c in mode.value for c in "wax+"))


def _scratch_name(node: ast.AST, names: set[str]) -> str | None:
    """The `.pytest_*` folder `node` joins onto a checkout path, by `/` or `.joinpath(…)`."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        base, parts = node.left, [node.right]
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
            and node.func.attr == "joinpath":
        base, parts = node.func.value, list(node.args)
    else:
        return None
    for p in parts:
        if isinstance(p, ast.Constant) and isinstance(p.value, str) \
                and p.value.startswith(".pytest_") and p.value != ".pytest_cache" \
                and _in_checkout(base, names):
            return p.value
    return None


def _findings(scope: ast.AST, names: set[str]) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for node in ast.walk(scope):
        scratch = _scratch_name(node, names)
        if scratch is not None and isinstance(node, ast.expr):
            out.append((node.lineno, f"names the scratch folder {scratch!r}"))
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if isinstance(f, ast.Attribute) and f.attr in _PATH_WRITES \
                and _in_checkout(f.value, names):
            out.append((node.lineno, f".{f.attr}() on a path in the checkout"))
        elif isinstance(f, ast.Attribute) and f.attr == "open" \
                and _in_checkout(f.value, names) and _opens_for_writing(node, 0):
            out.append((node.lineno, ".open() for writing on a path in the checkout"))
        elif isinstance(f, ast.Name) and f.id == "open" and node.args \
                and _in_checkout(node.args[0], names) and _opens_for_writing(node, 1):
            out.append((node.lineno, "open() for writing on a path in the checkout"))
        elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
            i = _FUNC_WRITES.get((f.value.id, f.attr))
            if i is not None and len(node.args) > i and _in_checkout(node.args[i], names):
                out.append((node.lineno, f"{f.value.id}.{f.attr}() on a path in the checkout"))
    return out


def checkout_writes(source: str) -> list[tuple[int, str]]:
    """Every (line, what) in `source` that writes a path in the checkout, or names a `.pytest_*`
    folder there. Names are bound per function, so a `tmp` that is a temp dir in one test and a
    checkout path in another is judged in each by its own binding, and a parameter that shadows a
    module name (`def f(ROOT)`) is whatever its caller passes, not the module's path."""
    tree = ast.parse(source)
    scopes = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    top = ast.Module(body=[n for n in tree.body if not isinstance(n, scopes)], type_ignores=[])
    module_names = _bound(top, set())
    found = set(_findings(top, module_names))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = node.args
            params = {p.arg for p in [*a.posonlyargs, *a.args, *a.kwonlyargs]}
            found |= set(_findings(node, _bound(node, module_names - params)))
    return sorted(found)


def _test_modules() -> list[Path]:
    fixtures = ROOT / "tests" / "fixtures"
    return sorted(p for p in (ROOT / "tests").rglob("*.py") if fixtures not in p.parents)


# ── the live suite ─────────────────────────────────────────────────────────────────────────────

def test_no_module_under_tests_writes_a_path_in_the_checkout() -> None:
    """(+) Red on main `51c84843` at its three live sites: test_anchor_gap_split_render.py:102,
    test_w50_anchor_current.py:285, test_w73_dated_multiple.py:487 (W62's fourth was deleted by
    #1144). (−) Green once each writes in `tempfile.TemporaryDirectory()`."""
    modules = _test_modules()
    assert len(modules) > 500, f"the scan found only {len(modules)} modules under tests/"
    bad = [f"{p.relative_to(ROOT)}:{line}: {what}"
           for p in modules for line, what in checkout_writes(p.read_text())]
    assert not bad, (f"{len(bad)} write(s) to a path in the checkout; write in "
                     "tempfile.TemporaryDirectory() or tmp_path instead:\n" + "\n".join(bad))


# ── what the guard refuses, and what it lets through ──────────────────────────────────────────

#: The shape W61's `_web()` had on main `51c84843` (test_anchor_gap_split_render.py:99–110).
_W61_AS_IT_WAS = '''
ROOT = Path(__file__).resolve().parents[1]

@cache
def _web():
    tmp = ROOT / ".pytest_w61_tmp"
    tmp.mkdir(exist_ok=True)
    try:
        (tmp / "drv.mjs").write_text(driver)
        (tmp / "pages.json").write_text(json.dumps(pages))
        res = subprocess.run(["node", str(tmp / "drv.mjs"), str(tmp / "pages.json")], cwd=ROOT,
                             capture_output=True, text=True, check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
'''

#: The same driver run after the fix: a temp directory, node still run from the checkout.
_W61_AS_FIXED = '''
ROOT = Path(__file__).resolve().parents[1]

@cache
def _web():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        (tmp / "drv.mjs").write_text(driver)
        (tmp / "pages.json").write_text(json.dumps(pages))
        res = subprocess.run(["node", str(tmp / "drv.mjs"), str(tmp / "pages.json")], cwd=ROOT,
                             capture_output=True, text=True, check=True)
'''


def test_the_shape_w61_had_is_refused_at_every_write() -> None:
    """(+) The real observed shape: the folder name, the mkdir, both write_texts and the rmtree."""
    assert checkout_writes(_W61_AS_IT_WAS) == [
        (6, "names the scratch folder '.pytest_w61_tmp'"),
        (7, ".mkdir() on a path in the checkout"),
        (9, ".write_text() on a path in the checkout"),
        (10, ".write_text() on a path in the checkout"),
        (14, "shutil.rmtree() on a path in the checkout"),
    ]


def test_the_fixed_shape_passes_with_node_still_run_from_the_checkout() -> None:
    """(−) A temp directory written, `cwd=ROOT` kept: nothing is refused."""
    assert checkout_writes(_W61_AS_FIXED) == []


@pytest.mark.parametrize("src", [
    'ROOT = Path(__file__).resolve().parents[1]\ndef t():\n    (ROOT / "build_w90").mkdir()\n',
    'HERE = Path(__file__).parent\ndef t():\n    out = HERE / "out.json"\n'
    '    out.write_text("x")\n',
    'ROOT = Path(__file__).resolve().parent.parent\nDATA = ROOT / "data"\n'
    'def t():\n    with open(DATA / "x.jsonl", "a") as f:\n        f.write("x")\n',
    'ROOT = Path(__file__).resolve().parents[1]\n'
    'def t(tmp_path):\n    shutil.copy(tmp_path / "a", ROOT / "frontend" / "a")\n',
    'def t():\n    shutil.rmtree(Path(__file__).parent / "scratch")\n',
    'ROOT = Path(__file__).resolve().parents[1]\n'
    'def t():\n    for p in (ROOT / "data").glob("*.json"):\n        p.unlink()\n',
    'ROOT = Path(__file__).resolve().parents[1]\n'
    'def t():\n    with (ROOT / "x.txt").open("w") as f:\n        f.write("x")\n',
    'ROOT = Path(__file__).resolve().parents[1]\n'
    'def t(tmp_path):\n    os.replace(tmp_path / "a.json", ROOT / "data" / "a.json")\n',
    'ROOT = Path(__file__).resolve().parents[1]\n'
    'def t():\n    d = ROOT.joinpath(".pytest_w90_tmp")\n    subprocess.run(["node", str(d)])\n',
], ids=["mkdir-another-name", "write-text-beside-the-test", "append-under-a-bound-subdir",
        "copy-into-the-checkout", "rmtree-on-own-location", "unlink-each-globbed-file",
        "path-open-for-writing", "os-replace-into-the-checkout", "joinpath-a-scratch-name"])
def test_a_write_in_the_checkout_is_refused_whatever_the_folder_is_called(src: str) -> None:
    """(+) Keyed on the call, not on the `.pytest_` name: none of these names one."""
    assert checkout_writes(src), src


@pytest.mark.parametrize("src", [
    'ROOT = Path(__file__).resolve().parents[1]\ndef t(tmp_path):\n    (tmp_path / "a").write_text('
    '(ROOT / "frontend" / "a").read_text())\n',
    'ROOT = Path(__file__).resolve().parents[1]\ndef t():\n    with open(ROOT / "STATE.md") as f:\n'
    '        f.read()\n',
    'ROOT = Path(__file__).resolve().parents[1]\ndef t(tmp_path):\n'
    '    (tmp_path / (ROOT / "STATE.md").name).write_text("x")\n',
    'ROOT = Path(__file__).resolve().parents[1]\ndef t(tmp_path):\n'
    '    shutil.copy(ROOT / "STATE.md", tmp_path / "STATE.md")\n',
    'ROOT = Path(__file__).resolve().parents[1]\ndef a():\n    tmp = ROOT / "frontend"\n'
    '    return tmp.read_text()\ndef b(tmp_path):\n    tmp = tmp_path / "x"\n    tmp.mkdir()\n',
    'ROOT = Path(__file__).resolve().parents[1]\ndef t():\n'
    '    assert (ROOT / ".pytest_cache").name\n',
    'ROOT = Path(__file__).resolve().parents[1]\ndef _seed(ROOT):\n    (ROOT / "x").mkdir()\n'
    'def t(tmp_path):\n    _seed(tmp_path)\n',
], ids=["read-from-the-checkout-write-to-tmp", "open-for-reading", "a-checkout-name-under-tmp",
        "copy-out-of-the-checkout", "one-name-two-functions", "pytests-own-cache",
        "a-parameter-shadows-root"])
def test_reads_of_the_checkout_and_writes_elsewhere_pass(src: str) -> None:
    """(−) Reading the checkout, or writing tmp_path, is what tests do: none is refused."""
    assert checkout_writes(src) == [], src
