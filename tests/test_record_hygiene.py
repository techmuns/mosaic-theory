"""SHELL QUOTING LEAKED INTO THE COMMITTED RECORD, and nothing noticed for four PRs.

THE INCIDENT (2026-07-31). STATE.md is written by an agent through `git commit -F -` heredocs and
`python - <<'EOF'` blocks. Inside a single-quoted shell string an apostrophe is escaped by closing
the quote, emitting a quoted apostrophe, and reopening — correct in the command, and **verbatim in
the file** when the escaping is applied one layer too late. Seven accumulated across four PRs in
D16, D17 and D19, each rendering as escape noise where an apostrophe belongs.

WHY IT SURVIVED FOUR REVIEW PASSES: every one was CORRECT in the heredoc that produced it. The
review read the INPUT, not the committed artifact — so the defect was invisible to the only check
being applied. Found by accident, while verifying that an unrelated correction had landed.

THE INVARIANT RULE says an incident closes with a machine check or a recorded acceptance. Repairing
the seven instances is not closing it — the eighth arrives the next time an apostrophe is typed
inside a heredoc. This is the check, and it reads the COMMITTED BYTES, which is exactly the thing
the human pass does not do.

MATCHES THE IDIOM, NOT THE INSTANCES (operator, on review of the first cut). The first version
listed three literal strings that had actually been seen — a pin that catches only what already
happened, which is the seen-instances defect the repo keeps finding elsewhere. The scan now matches
the shell-quoting SHAPE, and derives its file set from a glob rather than a hand-kept list, so a new
committed document is covered on the day it is added.
"""
from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: THE IDIOM, not three sightings of it. `'\''` and `'"'"'` are the two ways a POSIX shell escapes
#: an apostrophe inside a single-quoted string, and neither can occur in English prose: both require
#: a quote character immediately adjacent to a quote character. Written as a regex over that shape
#: so a variant nobody has seen yet is still caught.
QUOTE_ESCAPE = re.compile(r"""'\\''|'"'"'""")
#: A heredoc sentinel that reached the file means the block was pasted rather than executed.
HEREDOC_SENTINEL = re.compile(r"<<-?\s*'?[A-Z_]{2,}'?\s*$", re.MULTILINE)

PATTERNS = {
    "shell single-quote escape": QUOTE_ESCAPE,
    "unexecuted heredoc sentinel": HEREDOC_SENTINEL,
}


def _committed_docs() -> list[pathlib.Path]:
    """Every committed prose surface an agent writes through shell heredocs — GLOBBED, not listed,
    so a new handbook is covered the day it lands rather than the day someone remembers it."""
    found = [p for p in (ROOT.glob("*.md")) if p.is_file()]
    found += [p for p in ROOT.glob("docs/**/*.md") if p.is_file()]
    return sorted(found)


@pytest.mark.parametrize("path", _committed_docs(), ids=lambda p: str(p.name))
def test_no_shell_quoting_artefacts_in_the_committed_record(path: pathlib.Path) -> None:
    """THE RED. Seven instances of the escape idiom were live in STATE.md when this was written."""
    text = path.read_text()
    found = []
    for label, rx in PATTERNS.items():
        hits = list(rx.finditer(text))
        if hits:
            line = text[: hits[0].start()].count("\n") + 1
            found.append(f"{label} ×{len(hits)} (first at {path.name}:{line})")
    assert not found, (
        f"shell quoting leaked into {path.name}: {'; '.join(found)}. These are correct inside the "
        "heredoc that produced them and WRONG in the file — which is why a review that reads the "
        "command instead of the committed artifact cannot see them.")


def test_the_scan_fires_on_the_idiom_including_shapes_never_yet_seen() -> None:
    """A hygiene check that cannot fail is worse than none — it certifies the record clean while
    reading nothing. Both POSIX escape spellings must match, including the one that has NOT occurred
    here, which is the whole point of matching the idiom rather than the sightings."""
    seen = "the bound'\"'\"'s own evidence"          # the shape that actually leaked
    unseen = "the bound'\\''s own evidence"          # the other POSIX spelling, never seen here
    for sample in (seen, unseen):
        assert QUOTE_ESCAPE.search(sample), sample
    assert not QUOTE_ESCAPE.search("an ordinary apostrophe's prose, and \"a quotation\".")
    assert HEREDOC_SENTINEL.search("run: python - <<'PYEOF'")
    assert not HEREDOC_SENTINEL.search("the value is << the threshold")


def test_the_corpus_is_real_and_not_an_empty_glob() -> None:
    """The glob must not silently resolve to nothing — an empty parametrisation passes as loudly as
    a clean corpus, which is the vacuous-pin class this file exists to close."""
    docs = _committed_docs()
    names = {p.name for p in docs}
    assert {"STATE.md", "CLAUDE.md"} <= names, f"core records not scanned: {sorted(names)}"
    assert len(docs) >= 3, f"only {len(docs)} document(s) globbed — the scan is near-vacuous"
    assert any(p.read_text().strip() for p in docs), "every globbed document read empty"
