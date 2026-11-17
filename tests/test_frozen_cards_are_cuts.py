"""A FROZEN UNDERWRITE CARD IS A COMMITTED CARD, BYTE FOR BYTE.

A render pin that needs a card in some STATE (an undecided record, say) reads a frozen copy of
`frontend/scenarios/<key>.json`, so that a verdict recorded or a record reissued cannot take the
state out from under it (`tests/fixtures/frozen_cards/README.md`). The copy is trusted in place
of the card only because it IS one: every file under `tests/fixtures/frozen_cards/cut-<sha8>/`
must equal `frontend/scenarios/<file>` at the commit its folder names, the same git blob. This
test refuses:

- a copy hand-edited, or hand-rolled to the shape a pin needs;
- a card that commit never had;
- a cut whose commit is unknown;
- a copy the README does not head with its source, commit and blob, or a README row with no copy.

It is the twin of `tests/test_frozen_pages_are_cuts.py`, whose git helpers it uses, for the one
other kind of file a render pin reads. As there, CI checks out the whole history (`fetch-depth:
0`), a git checkout lacking the commit FAILS, and only a tree that is not a checkout (the impact
harness's `git archive` export) skips.

CORPUS BEFORE SYNTHETIC: the first pin checks every committed copy; the negatives then edit the
real bytes.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path

from tests.frozen_support import ROOT
from tests.test_frozen_pages_are_cuts import _blob_of, _cut_files, _git, needs_git

FROZEN_CARDS = ROOT / "tests" / "fixtures" / "frozen_cards"

_ROW = re.compile(r"^\| `(?P<copy>cut-(?P<sha8>[0-9a-f]{8})/(?P<name>[^`/]+))` \| "
                  r"`frontend/scenarios/(?P<src>[^`]+)` \| `(?P<sha>[0-9a-f]{40})` \| "
                  r"`(?P<blob>[0-9a-f]{40})` \|")


def card_problems(root: Path) -> tuple[list[str], int]:
    """(every way a copy under ``root`` is not its commit's card, copies checked)."""
    problems: list[str] = []
    checked = 0
    have: dict[Path, str] = {}
    for cut in sorted(root.glob("cut-*")):
        sha8 = cut.name.removeprefix("cut-")
        files = _cut_files(cut)
        nested = [p for p in files if p.parent != cut]
        problems += [f"{p.relative_to(root)}: a cut holds cards only, never a folder"
                     for p in nested]
        cards = [p for p in files if p.parent == cut]
        # the copies are held whether or not the commit resolves, so a README row for one is
        # never reported as heading a copy that is not there
        blobs = _blob_of(cards) if cards else {}
        have.update(blobs)
        try:
            sha = _git("rev-parse", "--verify", "--quiet", f"{sha8}^{{commit}}").strip()
        except subprocess.CalledProcessError:
            problems.append(f"{cut.name}: no commit {sha8} in this checkout")
            continue
        if not cards:
            continue
        specs = [f"{sha}:frontend/scenarios/{p.name}" for p in cards]
        batch = _git("cat-file", "--batch-check=%(objectname) %(objecttype)",
                     stdin="".join(f"{s}\n" for s in specs)).splitlines()
        for p, spec, line in zip(cards, specs, batch, strict=True):
            checked += 1
            if not line.endswith(" blob"):
                problems.append(f"{p.relative_to(root)}: not a card at {sha8} ({spec})")
            elif line.split()[0] != blobs[p]:
                problems.append(f"{p.relative_to(root)}: differs from {spec} (blob "
                                f"{blobs[p][:12]} vs committed {line.split()[0][:12]})")
    problems += _header_problems(root, have)
    return problems, checked


def _header_problems(root: Path, have: dict[Path, str]) -> list[str]:
    readme = root / "README.md"
    if not readme.exists():
        return ["no README.md heading the copies"]
    matched = [m for ln in readme.read_text().splitlines() if (m := _ROW.match(ln))]
    rows = {m["copy"]: m for m in matched}
    out: list[str] = []
    seen = Counter(m["copy"] for m in matched)
    out += [f"{c}: the README heads it more than once" for c in sorted(seen) if seen[c] > 1]
    copies = {p.relative_to(root).as_posix(): p for p in have}
    out += [f"{c}: a copy the README does not head" for c in sorted(set(copies) - set(rows))]
    out += [f"{c}: the README heads it, and there is no such copy"
            for c in sorted(set(rows) - set(copies))]
    for c in sorted(set(copies) & set(rows)):
        m = rows[c]
        if m["src"] != m["name"] or not m["sha"].startswith(m["sha8"]):
            out.append(f"{c}: its README row names another source or commit")
        if m["blob"] != have[copies[c]]:
            out.append(f"{c}: its README states blob {m['blob'][:12]}, the copy is "
                       f"{have[copies[c]][:12]}")
    return out


@needs_git
def test_every_frozen_card_is_its_commits_card_byte_for_byte() -> None:
    """(+ · the committed copies) Every copy is the card as committed at its cut's commit, and
    every copy is headed. Both committed copies are checked, so the walk is not vacuous."""
    problems, checked = card_problems(FROZEN_CARDS)
    assert not problems, problems
    assert checked == len(list(FROZEN_CARDS.glob("cut-*/*.json"))) == 2, checked


def _copy(tmp_path: Path) -> Path:
    root = tmp_path / "frozen_cards"
    shutil.copytree(FROZEN_CARDS, root)
    return root


@needs_git
def test_an_unedited_copy_of_the_cards_passes(tmp_path: Path) -> None:
    """(+ · control) The tmp copy the negatives edit passes as it stands, so each negative's
    failure is its edit's."""
    assert card_problems(_copy(tmp_path)) == ([], 2)


@needs_git
def test_a_one_byte_edit_to_a_card_is_refused(tmp_path: Path) -> None:
    """(−) A card edited by one byte, the shape a status set by hand would leave, is not the
    card: here the pending record's verdict status, the field the opener pin reads it for."""
    root = _copy(tmp_path)
    card = root / "cut-4889ddba" / "EPAM-2026-07-21.json"
    raw = card.read_bytes()
    at = b'"verdict": {\n  "status": "pending_analyst"'
    assert raw.count(at) == 1
    card.write_bytes(raw.replace(at, at[:-1] + b' "'))
    problems, _ = card_problems(root)
    assert any(p.startswith("cut-4889ddba/EPAM-2026-07-21.json: differs from")
               for p in problems), problems
    assert any("its README states blob" in p for p in problems), problems


@needs_git
def test_a_card_the_commit_never_had_is_refused(tmp_path: Path) -> None:
    """(−) A copy under a name no card had at that commit is not a cut: the SMPL card filed as
    the pending record a test would want."""
    root = _copy(tmp_path)
    (root / "cut-f2c6e7aa" / "SMPL.json").rename(root / "cut-f2c6e7aa" / "SMPL-2026-08-05.json")
    problems, _ = card_problems(root)
    assert "cut-f2c6e7aa/SMPL-2026-08-05.json: not a card at f2c6e7aa " \
           "(f2c6e7aa763bf3b5cb32da7759551d502c212aef:frontend/scenarios/SMPL-2026-08-05.json)" \
           in problems, problems
    assert "cut-f2c6e7aa/SMPL-2026-08-05.json: a copy the README does not head" in problems
    assert "cut-f2c6e7aa/SMPL.json: the README heads it, and there is no such copy" in problems


@needs_git
def test_a_cut_of_an_unknown_commit_is_refused(tmp_path: Path) -> None:
    """(−) A folder named for no commit is a working-tree copy, never a cut."""
    root = _copy(tmp_path)
    (root / "cut-f2c6e7aa").rename(root / "cut-0000dead")
    problems, _ = card_problems(root)
    assert "cut-0000dead: no commit 0000dead in this checkout" in problems, problems


@needs_git
def test_a_headed_cut_of_an_unknown_commit_is_not_called_missing(tmp_path: Path) -> None:
    """(−) A cut whose commit this checkout lacks (a shallow clone) still HOLDS its copies: the
    refusal names the commit, and never claims the README heads a copy that is not there."""
    root = _copy(tmp_path)
    (root / "cut-f2c6e7aa").rename(root / "cut-0000dead")
    readme = root / "README.md"
    readme.write_text(readme.read_text()
                      .replace("`cut-f2c6e7aa/", "`cut-0000dead/")
                      .replace("`f2c6e7aa763bf3b5cb32da7759551d502c212aef`",
                               "`0000dead763bf3b5cb32da7759551d502c212aef`"))
    problems, _ = card_problems(root)
    assert "cut-0000dead: no commit 0000dead in this checkout" in problems, problems
    assert not any("no such copy" in p for p in problems), problems


@needs_git
def test_a_copy_its_readme_heads_twice_is_refused(tmp_path: Path) -> None:
    """(−) Two README rows for one copy: the second silently replaced the first, so a stale row
    beside a correct one passed."""
    root = _copy(tmp_path)
    readme = root / "README.md"
    lines = readme.read_text().splitlines()
    row = next(ln for ln in lines if ln.startswith("| `cut-f2c6e7aa/SMPL.json`"))
    readme.write_text("\n".join([*lines, row]) + "\n")
    problems, _ = card_problems(root)
    assert "cut-f2c6e7aa/SMPL.json: the README heads it more than once" in problems, problems


@needs_git
def test_a_copy_its_readme_does_not_head_is_refused(tmp_path: Path) -> None:
    """(−) A copy with no README row, or a row naming another source, is unheaded."""
    root = _copy(tmp_path)
    readme = root / "README.md"
    lines = readme.read_text().splitlines()
    readme.write_text("\n".join(
        ln.replace("`frontend/scenarios/SMPL.json`", "`frontend/scenarios/BRBR.json`")
        for ln in lines if not ln.startswith("| `cut-4889ddba/EPAM-2026-07-21.json`")) + "\n")
    problems, _ = card_problems(root)
    assert "cut-4889ddba/EPAM-2026-07-21.json: a copy the README does not head" in problems, \
        problems
    assert "cut-f2c6e7aa/SMPL.json: its README row names another source or commit" in problems, \
        problems
