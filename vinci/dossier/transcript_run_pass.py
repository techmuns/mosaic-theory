"""The $0 cut of a committed synthesis's copied transcript runs (operator ruling 2026-11-11,
"$0 guard + redaction now"; CLAUDE.md's 12-word rule).

NO PUBLIC FIELD QUOTES MORE THAN 12 CONSECUTIVE TRANSCRIPT WORDS. Three committed synthesis claims
did, without quotation marks (LLY `bull_points[5].claim`, 15 words; VITL `bull_points[2].claim`,
14; WERN `bull_points[5].claim`, 14 — Codex, round 2 of #1006). The build now refuses such a page
(`assemble._refuse_transcript_runs`); this pass brings the committed pages under the rule.

For each committed page, with no model call, no network and no re-assembly:
1. Its calls are read from disk, read only, as the build fed them to the synthesis
   (`confirmation.page_transcripts`). A page is REFUSED, unwritten, when a call on disk does not
   read (LibreOffice fails a conversion while another runs, and a failed read would hide a run),
   when the calls on disk differ from the page's input record, or when its driver rows cite a
   call that is not on disk.
2. Every synthesis string is read against them (`synthesis.transcript_runs`), as the guard reads it.
3. Each run is CUT: its first 12 words are kept and the rest of the run becomes "…". Nothing is
   reworded, nothing is added and no LLM is asked; the text after the run is kept as it was. The
   cut page is read again, and must hold no run.
4. The page is written through `layer_refresh.write_recorded` as writer ``transcript-run-cut``.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vinci.dossier import layer_refresh
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.confirmation import ConfirmationError, page_transcripts
from vinci.dossier.driver_extract import transcript_sha256s
from vinci.dossier.schemas import Dossier, Synthesis, write_dossier
from vinci.dossier.synthesis import MAX_TRANSCRIPT_RUN, TranscriptRun, transcript_runs

WRITER = "transcript-run-cut"
ELLIPSIS = "…"


@dataclass
class CutOutcome:
    ticker: str
    status: str  # "written" | "unchanged" | "refused" | "would write" (dry run)
    detail: str
    #: (where, before, after) for each string cut
    cuts: list[tuple[str, str, str]] = field(default_factory=list)


def cut_text(text: str, runs: list[TranscriptRun]) -> str:
    """``text`` with each run cut to its first `MAX_TRANSCRIPT_RUN` words and "…": the text before
    the run and after it is kept, character for character."""
    for r in sorted(runs, key=lambda r: r.start, reverse=True):
        text = text[:r.keep] + ELLIPSIS + text[r.end:]
    return text


def describe_cut(before: str, after: str) -> str:
    """A cut as a log may carry it: word counts, the character span it removed from ``before``,
    and each string's sha256 — never a word of it, because ``before`` holds the copied run, which
    no log, fixture or PR body may carry (CLAUDE.md's 12-word rule)."""
    head = 0
    while head < min(len(before), len(after)) and before[head] == after[head]:
        head += 1
    tail = 0
    while (tail < min(len(before), len(after)) - head
           and before[len(before) - 1 - tail] == after[len(after) - 1 - tail]):
        tail += 1
    return (f"{len(before.split())} → {len(after.split())} words; characters {head}–"
            f"{len(before) - tail} of {len(before)} cut to {ELLIPSIS!r}; sha256 "
            f"{hashlib.sha256(before.encode()).hexdigest()[:16]} → "
            f"{hashlib.sha256(after.encode()).hexdigest()[:16]}")


_STEP = re.compile(r"([^.\[\]]+)|\[(\d+)\]")


def _path(where: str) -> list[str | int]:
    return [int(i) if i else str(k) for k, i in _STEP.findall(where)]


def _get(o: Any, path: list[str | int]) -> Any:
    for step in path:
        o = o[step]
    return o


def _set(o: Any, path: list[str | int], value: str) -> None:
    for step in path[:-1]:
        o = o[step]
    o[path[-1]] = value


def cited_calls(page: dict[str, Any]) -> set[str]:
    """The sha256 of every call the page's transcript driver rows cite (each row's locator)."""
    rows = ((page.get("mechanical") or {}).get("operating_drivers") or {}).get("rows") or []
    return {str(sha) for r in rows if r.get("tier") == "llm-fenced"
            if (sha := (r.get("locator") or {}).get("transcript_sha256"))}


def page_transcript(page: dict[str, Any], ciq_root: Path) -> tuple[str | None, list[str]]:
    """(the text the build fed the page's synthesis, what stops the read), read as the vote-rule
    confirmation reads it (`confirmation.page_transcripts`, review round 0): production's reader,
    refused where the calls on disk differ from the page's input record or one does not read.
    A call the page's driver rows cite (`cited_calls`, by sha256) that is not on disk stops it too,
    for a page whose input record names no transcript: read against the calls that ARE there, it
    would be called clean against text it was not built from."""
    ticker = str(page.get("ticker"))
    try:
        text, _verified = page_transcripts(ticker, ciq_root=ciq_root, page=page)
    except ConfirmationError as exc:
        return None, [str(exc)]
    missing = sorted(cited_calls(page) - _on_disk_shas(ticker, ciq_root))
    return text, [f"cited call {s[:12]} is not on disk" for s in missing]


def _on_disk_shas(ticker: str, ciq_root: Path) -> set[str]:
    """The sha256 of every call of ``ticker`` on disk (no file is converted)."""
    folder = ciq_root / ticker
    files = sorted(p for p in folder.iterdir() if p.is_file()) if folder.is_dir() else []
    return set(transcript_sha256s(
        w.path for w in CiqBundle.from_files(ticker, files).all_workbooks("transcript")).values())


def prepare(page: dict[str, Any],
            transcript: str) -> tuple[dict[str, Any], list[tuple[str, str, str]]]:
    """``page`` with every copied run of its synthesis cut, and each cut as (where, before,
    after). The page is not changed in place. Raises when a cut leaves a run: a bug, never a
    page written with one."""
    out = json.loads(json.dumps(page))
    synth = Synthesis.model_validate(out["synthesis"])
    by_where: dict[str, list[TranscriptRun]] = {}
    for r in transcript_runs(synth, transcript):
        by_where.setdefault(r.where, []).append(r)
    cuts: list[tuple[str, str, str]] = []
    for where, runs in by_where.items():
        path = _path(where)
        before = _get(out["synthesis"], path)
        after = cut_text(before, runs)
        _set(out["synthesis"], path, after)
        cuts.append((where, before, after))
    left = transcript_runs(Synthesis.model_validate(out["synthesis"]), transcript)
    if left:
        raise RuntimeError(f"{page.get('ticker')}: the cut left {len(left)} run(s) of more than "
                           f"{MAX_TRANSCRIPT_RUN} words ({left[0].where}) — page not written")
    return out, cuts


def run(jp: Path, ciq_root: Path, *, dry_run: bool, record: bool = True) -> CutOutcome:
    """One committed page through the pass. ``record=False`` is for a frozen test fixture."""
    raw = jp.read_text(encoding="utf-8")
    page = json.loads(raw)
    ticker = str(page.get("ticker") or jp.parent.name)
    if not page.get("synthesis"):
        return CutOutcome(ticker, "unchanged", "no synthesis")
    transcript, problems = page_transcript(page, ciq_root)
    if problems:
        return CutOutcome(ticker, "refused", f"the page's calls cannot all be read: "
                          f"{'; '.join(problems)} (LibreOffice fails a conversion while another "
                          "runs, so re-run alone; a cited call not on disk needs its export)")
    if not transcript:
        return CutOutcome(ticker, "unchanged", "no call on disk")
    cut, cuts = prepare(page, transcript)
    if not cuts:
        return CutOutcome(ticker, "unchanged", "no synthesis string shares more than "
                          f"{MAX_TRANSCRIPT_RUN} consecutive words with its calls")
    detail = f"{len(cuts)} string(s) cut: " + "; ".join(w for w, _, _ in cuts)
    if dry_run:
        return CutOutcome(ticker, "would write", detail + " (dry run: nothing written)", cuts)
    model = Dossier.model_validate(cut)
    if record:
        layer_refresh.write_recorded(jp, raw, model, WRITER)
    else:
        write_dossier(jp, model)
    return CutOutcome(ticker, "written", detail, cuts)
