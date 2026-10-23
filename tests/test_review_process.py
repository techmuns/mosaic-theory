"""THE BOUNDED PR-REVIEW PROCESS — its configuration pinned, positive and negative.

WHY (2026-10-23). Codex and Gemini Code Assist review this repo's PRs as comment-only second
reviewers, and the PR's own Claude session triages their findings with
`.claude/skills/pr-feedback` (FIX only behind a failing test, at most 2 rounds). The process
lives in four files — `.gemini/config.yaml`, `.gemini/styleguide.md`, the `## Code Review Rules`
in `AGENTS.md`, and the skill — plus one CLAUDE.md line. Each pin here guards a way those files
can silently disagree: two reviewers given different rules, a round cap that says 2 in one file
and 3 in another, or an ignore list that hides code from review.

`.gemini/config.yaml` is read as text: the repo carries no YAML dependency, and the file is flat
enough that a line match states exactly what Gemini will read.
"""
from __future__ import annotations

import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".gemini" / "config.yaml"
STYLEGUIDE = ROOT / ".gemini" / "styleguide.md"
AGENTS = ROOT / "AGENTS.md"
SKILL = ROOT / ".claude" / "skills" / "pr-feedback" / "SKILL.md"
CHECK_HEADINGS = ("### The decision line", "### Data integrity", "### Public repo")


def _setting(key: str) -> str:
    match = re.search(rf"^\s*{re.escape(key)}:\s*(\S+)\s*$", CONFIG.read_text(), re.M)
    assert match, f"{key} is not set in .gemini/config.yaml"
    return match.group(1)


def _ignore_patterns() -> list[str]:
    block = CONFIG.read_text().split("ignore_patterns:", 1)[1].split("\ncode_review:", 1)[0]
    return re.findall(r'^\s*-\s*"([^"]+)"\s*$', block, re.M)


def _glob(pattern: str) -> re.Pattern[str]:
    """gitignore-style: `*` and `?` stay inside one path segment, `**` crosses segments. Python's
    `fnmatch` lets `*` cross `/`, which made `frontend/*.json` look like it covered nested files."""
    out = ""
    for part in re.split(r"(\*\*/|\*\*|\*|\?)", pattern):
        out += {"**/": "(?:.*/)?", "**": ".*", "*": "[^/]*", "?": "[^/]"}.get(part, re.escape(part))
    return re.compile(out + r"\Z")


def _ignored(path: str) -> bool:
    return any(_glob(p).match(path) for p in _ignore_patterns())


def _checks(text: str) -> dict[str, list[str]]:
    """The bullets under each shared check heading, in order."""
    out: dict[str, list[str]] = {}
    for heading in CHECK_HEADINGS:
        block = text.split(heading, 1)[1].split("\n\n", 1)[0]
        out[heading] = [line for line in block.splitlines() if line.startswith("- ")]
    return out


# ── Gemini: severity floor, no silent cap, review on open only ───────────────────────────────────

def test_gemini_comments_only_at_high_severity_and_never_truncates_silently() -> None:
    assert _setting("comment_severity_threshold") == "HIGH"
    # a comment cap drops findings without saying so; the severity floor bounds volume instead
    assert _setting("max_review_comments") == "-1"
    assert _setting("summary") == "false" and _setting("help") == "false"
    assert _setting("code_review") == "true" and _setting("disable") == "false"
    assert _setting("include_drafts") == "true"   # a draft PR is reviewed when it opens too


def test_gemini_skips_artifacts_and_prose_but_reviews_code() -> None:
    for skipped in ("data/dossiers/VRRM/dossier.json", "data/snapshots/decision_ledger.jsonl",
                    "docs/records/2026-10-22-pr-review-gate.md", "STATE.md",
                    "scenarios/GOOGL.json", "frontend/dossiers/VRRM.md",
                    "frontend/theme-intelligence/index.html", "frontend/manifest.json",
                    "frontend/scenarios/AORT.json"):
        assert _ignored(skipped), skipped
    for reviewed in ("vinci/dossier/verdict.py", "tests/test_rank.py", "frontend/build.py",
                     "frontend/views/dossier.js", ".claude/hooks/fast_gate.py",
                     ".github/workflows/gate.yml", "CLAUDE.md", "AGENTS.md", "bin/commit"):
        assert not _ignored(reviewed), reviewed


def test_no_committed_code_is_hidden_from_review_and_the_skip_list_finds_artifacts() -> None:
    """On the committed tree: every code file stays reviewed, and the ignore list does match the
    artifacts it exists for (a pattern list that matches nothing is suspect, not safe)."""
    tracked = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True,
                             check=True).stdout.splitlines()
    code = [p for p in tracked if re.search(r"\.(py|js|mjs|ts|sh|toml|ya?ml)$", p)
            and not p.startswith(("frontend/theme-intelligence/", "frontend/dossiers/"))]
    hidden = [p for p in code if _ignored(p)]
    assert not hidden, f"{len(hidden)} code file(s) hidden from review, first: {hidden[:5]}"
    dossiers = [p for p in tracked if p.startswith("data/dossiers/")]
    assert dossiers and all(_ignored(p) for p in dossiers)


# ── one rule list, two reviewers ─────────────────────────────────────────────────────────────────

def test_codex_and_gemini_are_given_the_same_checks() -> None:
    codex = _checks(AGENTS.read_text().split("## Code Review Rules", 1)[1])
    gemini = _checks(STYLEGUIDE.read_text())
    assert all(codex[h] for h in CHECK_HEADINGS), "a check group in AGENTS.md is empty"
    assert codex == gemini, "AGENTS.md and .gemini/styleguide.md give the reviewers different rules"


def test_neither_reviewer_is_allowed_to_write() -> None:
    for text in (AGENTS.read_text().split("## Code Review Rules", 1)[1], STYLEGUIDE.read_text()):
        assert re.search(r"never push|Do not push", text, re.I)


# ── the skill and its one constant ───────────────────────────────────────────────────────────────

def test_the_round_cap_is_one_number_in_both_places_it_is_stated() -> None:
    skill = re.search(r"^ROUND CAP: (\d+)$", SKILL.read_text(), re.M)
    claude = re.search(r"PR feedback is bounded.*?at most (\d+) rounds",
                       (ROOT / "CLAUDE.md").read_text(), re.S)
    assert skill and claude, "the round cap is missing from the skill or from CLAUDE.md"
    assert skill.group(1) == claude.group(1)


def test_the_skill_is_discoverable_and_names_every_outcome() -> None:
    text = SKILL.read_text()
    front = text.split("---", 2)[1]
    assert re.search(r"^name: pr-feedback$", front, re.M)
    description = re.search(r"^description: (.+)$", front, re.M)
    assert description and "Codex" in description.group(1) and "Gemini" in description.group(1)
    for outcome in ("**FIX**", "**DISMISS**", "**DEFER**"):
        assert outcome in text, outcome
    assert "## Review dispositions" in text and "`@codex fix`" in text
