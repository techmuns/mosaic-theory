"""SHELL QUOTING LEAKED INTO THE COMMITTED RECORD, and nothing noticed for four PRs.

THE INCIDENT (2026-07-31). STATE.md is written by an agent through `git commit -F -` heredocs and
`python - <<'EOF'` blocks. Inside a single-quoted shell string an apostrophe is escaped as
``'\"'\"'`` — correct in the command, and **verbatim in the file** when the escaping is applied one
layer too late. Seven of them accumulated across four PRs in D16, D17 and D19, each rendering as
escape noise where an apostrophe belongs.

WHY IT SURVIVED FOUR REVIEW PASSES: every one was CORRECT in the heredoc that produced it. The
review read what was written, not what was committed — so the defect was invisible to the only
check being applied. It was found by accident, while verifying that an unrelated correction had
landed.

THE INVARIANT RULE says an incident closes with a machine check or a recorded acceptance. Repairing
the seven instances is not closing it — the eighth arrives the next time an apostrophe is typed
inside a heredoc. This is the check: it reads the COMMITTED bytes, which is exactly the thing the
human pass does not do.
"""
from __future__ import annotations

import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: Sequences that are shell/heredoc artefacts, never legitimate prose. Kept literal and narrow —
#: a broad "no backslashes" rule would fire on real content and get disabled.
LEAKED = {
    "shell single-quote escape": "'\"'\"'",
    "escaped-dollar heredoc leak": "\\$(",
    "unexpanded heredoc sentinel": "<<'PYEOF'",
}

#: The committed prose surfaces an agent writes through shell heredocs.
DOCS = ("STATE.md", "CLAUDE.md", "docs/engineering.md", "docs/RUNBOOKS.md")


@pytest.mark.parametrize("name", DOCS)
def test_no_shell_quoting_artefacts_in_the_committed_record(name: str) -> None:
    """THE RED. Seven instances of the first pattern were live in STATE.md when this was written."""
    path = ROOT / name
    if not path.is_file():
        pytest.skip(f"{name} absent from this checkout")
    text = path.read_text()
    found = []
    for label, needle in LEAKED.items():
        n = text.count(needle)
        if n:
            line = next((i for i, ln in enumerate(text.splitlines(), 1) if needle in ln), None)
            found.append(f"{label} ×{n} (first at {name}:{line})")
    assert not found, (
        f"shell quoting leaked into {name}: {'; '.join(found)}. These are correct inside the "
        "heredoc that produced them and WRONG in the file — which is why a review that reads the "
        "command instead of the committed bytes cannot see them.")


def test_the_scan_actually_fires_on_the_shape_it_names() -> None:
    """A hygiene check that cannot fail is worse than none — it certifies the record as clean while
    reading nothing. Drive each pattern through the same matching the corpus test uses."""
    for label, needle in LEAKED.items():
        sample = f"prose {needle} more prose"
        assert needle in sample, label
        assert sample.count(needle) == 1, label
    # and the corpus files are genuinely being read, not skipped into a vacuous pass
    present = [n for n in DOCS if (ROOT / n).is_file()]
    assert len(present) >= 2, f"only {present} found — the scan is near-vacuous"
    assert any((ROOT / n).read_text().strip() for n in present), "every doc read empty"
