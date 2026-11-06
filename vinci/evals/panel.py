"""The evaluation panel — chosen by a RULE over page attributes, never by the pages behind a fix.

A prompt change is drawn on a fixed set of pages. Choosing them by hand invites the pages whose
failures motivated the change, which then improve by construction (and by regression to the mean).
So the panel is the output of an exhaustive search over every six-page subset of the ELIGIBLE
pages, under pre-registered constraints, maximising a pre-registered objective, with ties broken
by a salted hash — nothing in it reads a metric, a draw or a forward return.

THE ATTRIBUTES, each read from the committed page (``page_row``):
- ``sleeve`` — the book the page is framed under (``quality`` / ``overshoot`` are stratified;
  ``ultra_short_term`` pages are not eligible: two pages, and the brief stratifies the two books);
- ``sector`` — the page's own ``sector`` label;
- ``material`` — a financial-summary row carries ``material: true`` (the 19c rows the prompt
  names and the guard demands), read from the structured rows, never the rendered table;
- ``forward_basis`` — a CIQ forward multiple is on the page: ``valuation.forward_multiples``
  present with an entry, or a ``forward_multiple_history`` series that is not context-only and has
  points (the fact the "trailing only" label contradicts);
- ``window_change`` — the price change over the drawdown detector's own window
  (``drawdown_cause.gap_window_days``), read off ``stock_performance`` from its last point back;
  RISING at +5% or more, FALLING at -5% or less, FLAT between (the case STATE row 47 names is a
  rising window labelled a bleed);
- ``five_draw`` — the page was built under the five-draw gate (``draw_agreement`` present);
- ``draws`` — that build's lean tally, from which two boundaries are read:
  ``modal_boundary`` — a 3-2 tally between ``mixed`` and a committed lean, ONE draw from changing
  the page's modal lean (UBER, BRBR, AMZN, BURL, ROST on the freeze commit);
  ``proposal_boundary`` — one draw from changing the PROPOSAL itself, which production withholds
  unless the draws are unanimous (`verdict.derive_proposal`): a unanimous committed lean (5-0,
  one dissent withholds it) or a 4-1 committed lean (one more agreeing draw makes it propose);
- ``transcripts`` — the CIQ transcripts the replay will read (a page needs at least one);
- ``motivated`` — the page MOTIVATED A FIX: its ticker is named in the subject OR BODY of a
  commit on main that changed ``vinci/dossier/synthesis.py`` or ``vinci/dossier/mechanical.py``,
  or in the title of a ``docs/records/`` file such a commit added, or anywhere in the record of a
  fix in flight at the freeze (``motivated_from_git``, ``in_flight_names``). APPLIED AS WRITTEN
  (review round 2, #924) it names ALL 28 pages: fix 3a's record, committed eleven minutes before
  the pre-registration, names 27, and commit bodies name the 28th. No page of this corpus is held
  out from the fixes the diagnosis produced, so the attribute is reported, never a constraint,
  and holding out is PER CHANGE (`compare.register`: the panel pages the change's own commits and
  records do not name).

ELIGIBLE: sleeve quality or overshoot, built under the five-draw gate, at least one transcript.

CONSTRAINTS (all must hold): 3 quality and 3 overshoot; 1 or 2 modal-boundary pages; at least 2
pages with a material row and 2 without; at least 2 rising and 2 falling windows; at least one
page without a forward basis WHEN an eligible page lacks one (none does on the freeze commit — the
constraint is then vacuous, and the frozen file says so). The v1 constraint "at least 2 held out
and 2 motivated" is DROPPED, stated in the frozen file: under its own rule as written no page is
held out, so it admits no panel (review round 2).

OBJECTIVE, lexicographic: (1) the most distinct sectors; (2) at least one proposal-boundary page;
(3) the smallest material / non-material imbalance; (4) the smallest rising / falling imbalance.
TIE-BREAK: the smallest sha256 of ``salt + ",".join(sorted(tickers))``, the salt being the
FREEZE COMMIT's full sha — a value nobody chose. v1's hand-written salt string was steerable:
salt variants reached all seven tied panels (review round 2).
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from itertools import combinations
from pathlib import Path
from typing import Any

PANEL_SIZE = 6
WINDOW_BAND = 0.05
ELIGIBLE_SLEEVES = ("quality", "overshoot")
#: The files whose change moves the synthesis request: its builder, and the layer whose words it
#: carries.
PROMPT_FILES = ("vinci/dossier/synthesis.py", "vinci/dossier/mechanical.py")

_COMMITTED = ("strongly-bullish", "strongly-bearish")


@dataclass(frozen=True)
class PanelRow:
    ticker: str
    sleeve: str
    sector: str
    material: bool
    forward_basis: bool
    window_change: float | None
    window_dir: str | None
    five_draw: bool
    draws: dict[str, int] | None
    modal_boundary: bool
    proposal_boundary: bool
    transcripts: int
    motivated: bool

    @property
    def eligible(self) -> bool:
        return self.sleeve in ELIGIBLE_SLEEVES and self.five_draw and self.transcripts >= 1

    def exclusion(self) -> str | None:
        """Why the row is not eligible, or None."""
        if self.sleeve not in ELIGIBLE_SLEEVES:
            return f"sleeve {self.sleeve} is not stratified"
        if not self.five_draw:
            return "built before the five-draw gate (no draw_agreement)"
        if self.transcripts < 1:
            return "no CIQ transcript for the replay to read"
        return None


def _has_material_row(mech: dict[str, Any]) -> bool:
    fs = mech.get("financial_summary") or {}
    for table in ("annual", "quarterly"):
        block = fs.get(table) or {}
        value = block.get("value") if isinstance(block, dict) else None
        for row in (value or {}).get("rows") or []:
            if row.get("material") is True:
                return True
    return False


def has_forward_basis(page: dict[str, Any]) -> bool:
    """A CIQ forward multiple is on the page (see the module docstring). Shared with the LABEL
    metric, which reads "trailing only" against the same fact."""
    fm = ((page.get("mechanical") or {}).get("valuation") or {}).get("forward_multiples") or {}
    if fm.get("status") == "present" and fm.get("value"):
        return True
    fmh = page.get("forward_multiple_history") or {}
    return any(not s.get("context_only") and s.get("points") for s in fmh.get("series") or [])


def window_change(page: dict[str, Any]) -> float | None:
    """The price change over the gap-down detector's window, from ``stock_performance``'s last
    point back ``gap_window_days`` calendar days (the first point on or after that day). None when
    either is missing — never a guessed window."""
    mech = page.get("mechanical") or {}
    pts = (mech.get("stock_performance") or {}).get("points") or []
    win = (mech.get("drawdown_cause") or {}).get("gap_window_days")
    if not pts or not win:
        return None
    end = date.fromisoformat(pts[-1]["date"])
    start = end - timedelta(days=int(win))
    first = next((p for p in pts if date.fromisoformat(p["date"]) >= start), None)
    if first is None or not first.get("name"):
        return None
    return float(pts[-1]["name"]) / float(first["name"]) - 1.0


def _direction(change: float | None) -> str | None:
    if change is None:
        return None
    if change >= WINDOW_BAND:
        return "rising"
    if change <= -WINDOW_BAND:
        return "falling"
    return "flat"


def _boundaries(draws: dict[str, int] | None) -> tuple[bool, bool]:
    if not draws:
        return False, False
    total = sum(draws.values())
    committed = {k: v for k, v in draws.items() if k in _COMMITTED}
    mixed = draws.get("mixed", 0)
    modal = (total == 5 and len(draws) == 2 and mixed in (2, 3)
             and sum(committed.values()) == 5 - mixed)
    top = max(committed.values(), default=0)
    proposal = total == 5 and top in (4, 5) and len(committed) == 1
    return modal, proposal


def page_row(page: dict[str, Any], *, transcripts: int, motivated: bool) -> PanelRow:
    mech = page.get("mechanical") or {}
    da = (page.get("synthesis") or {}).get("draw_agreement")
    draws = dict(da["labels"]) if da else None
    modal, proposal = _boundaries(draws)
    change = window_change(page)
    return PanelRow(
        ticker=str(page["ticker"]), sleeve=str(page.get("sleeve")),
        sector=str(page.get("sector") or "UNKNOWN"), material=_has_material_row(mech),
        forward_basis=has_forward_basis(page),
        window_change=None if change is None else round(change, 4),
        window_dir=_direction(change), five_draw=da is not None, draws=draws,
        modal_boundary=modal, proposal_boundary=proposal, transcripts=transcripts,
        motivated=motivated)


def _satisfies(sub: Sequence[PanelRow], pool: Sequence[PanelRow]) -> bool:
    sleeves = [r.sleeve for r in sub]
    if sleeves.count("quality") != 3 or sleeves.count("overshoot") != 3:
        return False
    if not 1 <= sum(r.modal_boundary for r in sub) <= 2:
        return False
    mat = sum(r.material for r in sub)
    if mat < 2 or len(sub) - mat < 2:
        return False
    dirs = [r.window_dir for r in sub]
    if dirs.count("rising") < 2 or dirs.count("falling") < 2:
        return False
    return not (any(not r.forward_basis for r in pool) and all(r.forward_basis for r in sub))


def _score(sub: Sequence[PanelRow]) -> tuple[int, int, int, int]:
    mat = sum(r.material for r in sub)
    dirs = [r.window_dir for r in sub]
    return (len({r.sector for r in sub}), int(any(r.proposal_boundary for r in sub)),
            -abs(mat - (len(sub) - mat)), -abs(dirs.count("rising") - dirs.count("falling")))


def tie_key(tickers: Iterable[str], salt: str) -> str:
    return hashlib.sha256((salt + ",".join(sorted(tickers))).encode()).hexdigest()


@dataclass(frozen=True)
class Selection:
    panel: tuple[str, ...]
    eligible: int
    subsets: int
    feasible: int
    best_score: tuple[int, int, int, int]
    tied_at_best: int
    tied: tuple[tuple[str, ...], ...] = ()


def select_panel(rows: Sequence[PanelRow], *, salt: str, size: int = PANEL_SIZE) -> Selection:
    """The rule (module docstring), exhaustively. Raises when no subset satisfies it — a panel
    is never relaxed silently."""
    pool = sorted((r for r in rows if r.eligible), key=lambda r: r.ticker)
    best: list[tuple[tuple[int, int, int, int], str, tuple[str, ...]]] = []
    n = feasible = 0
    for sub in combinations(pool, size):
        n += 1
        if not _satisfies(sub, pool):
            continue
        feasible += 1
        names = tuple(r.ticker for r in sub)
        best.append((_score(sub), tie_key(names, salt), names))
    if not best:
        raise ValueError(f"no {size}-page subset of {len(pool)} eligible pages meets the rule")
    top = max(s for s, _, _ in best)
    tied = sorted((k, names) for s, k, names in best if s == top)
    return Selection(panel=tied[0][1], eligible=len(pool), subsets=n, feasible=feasible,
                     best_score=top, tied_at_best=len(tied), tied=tuple(names for _, names in tied))


# ------------------------------------------------------------------ motivated, from git history

def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          check=True).stdout


def _named(text: str, tickers: Iterable[str]) -> set[str]:
    return {t for t in tickers
            if re.search(rf"(?<![A-Za-z0-9]){re.escape(t)}(?![A-Za-z0-9])", text)}


def motivated_from_git(repo: Path, ref: str, tickers: Sequence[str]) -> dict[str, list[str]]:
    """ticker → the commits (short sha) whose subject or BODY, or whose added record title, names
    it,
    over every commit on ``ref`` that changed one of ``PROMPT_FILES``. Needs full history: a
    shallow clone raises rather than reading a partial log as "nobody was ever named"."""
    if _git(repo, "rev-parse", "--is-shallow-repository").strip() == "true":
        raise RuntimeError("shallow clone: the motivated set needs the full history")
    out: dict[str, list[str]] = {}
    for line in _git(repo, "log", ref, "--format=%h%x09%s", "--", *PROMPT_FILES).splitlines():
        sha, _, subject = line.partition("\t")
        named = _named(subject + "\n" + _git(repo, "log", "-1", "--format=%b", sha), tickers)
        added = _git(repo, "show", "--name-only", "--diff-filter=A", "--format=", sha).split()
        for rec in (p for p in added if p.startswith("docs/records/") and p.endswith(".md")):
            body = _git(repo, "show", f"{sha}:{rec}")
            title = next((x for x in body.splitlines() if x.startswith("# ")), "")
            named |= _named(title, tickers)
        for t in named:
            out.setdefault(t, []).append(sha)
    return out


def in_flight_names(repo: Path, records: Sequence[str], tickers: Sequence[str]) -> set[str]:
    """The tickers named ANYWHERE in the records of fixes in flight (``ref:path`` each) — a fix
    not yet merged has no commit on main to read, but its record says which pages it rests on."""
    out: set[str] = set()
    for spec in records:
        out |= _named(_git(repo, "show", spec), tickers)
    return out


def rows_json(rows: Sequence[PanelRow]) -> list[dict[str, Any]]:
    return [{**asdict(r), "eligible": r.eligible, "exclusion": r.exclusion()} for r in rows]


def rows_from_json(items: Sequence[dict[str, Any]]) -> list[PanelRow]:
    fields = PanelRow.__dataclass_fields__
    return [PanelRow(**{k: v for k, v in it.items() if k in fields}) for it in items]


def load_panel(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data
