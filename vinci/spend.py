"""THE MONTHLY SPEND REPORT — each paid bucket's list-price spend in one calendar month, read from
the records that already exist. It REPORTS AND REFUSES NOTHING (operator, 2026-11-13: "Report
only"); per-run control is unchanged — every paid run still spends only under the operator's
approved cap (`python -m vinci.evals budget-open --cap … --approval "…"`, `graph-rejudge
--budget-usd`, the theme desk's run budget).

    python -m vinci.spend --month 2026-11 [--evals-ledger FILE …] [--evals-root DIR …]
                          [--theme-ref REF] [--json]

WHERE EACH BUCKET IS READ FROM, AND WHAT IT CANNOT SEE (each bucket prints both):

- **pages** — `data/snapshots/assembly_runs/*.jsonl` (committed; the repo's own `data/`, wherever
  the command runs): one line per name a build attempted, refused and failed included; `usd` is
  list price over its METERED calls, `null` for an unpriced model (counted apart, never as zero).
  Dated by the line's `started_at`. No run file at all is NOT READ. Cannot see a build whose run
  file was not committed.
- **confirmations** — `data/snapshots/proposal_confirmations.jsonl` (the seal-time ten-draw
  confirmation). Its rows carry `drawn_at` but NO cost, and a confirmation refused after its draws
  writes no row at all, so this bucket's spend is NOT RECORDED: the rows are counted, never priced.
- **evals** — the budget ledgers (`vinci.evals.replay.Budget`), which live OUTSIDE the repo by
  design, so only the ledgers this run is given are read (`--evals-ledger`, or every ledger under
  `--evals-root`, by default the folders in ``VINCI_LEDGER_ROOTS``). The report PRINTS every root
  it searched and every ledger it read, never a wider claim. A draw row carries no time, so it
  is BOUNDED, never guessed: it lies after the stamp above it (the approval's `opened_at`, a
  `build_start`'s `started_at`, a `build_end`'s `t`) and before its own build's `build_end` below
  it (matched by label), or the ledger file's last write. (A `build_start` bounds only what
  follows it: its time is taken before its request is captured, so a concurrent build's draw can
  be appended above it later; and a `build_end` bounds only its own build's draws, since another
  command's draw can be appended between its `t` and its row.) Bounds in one month place it
  there; bounds spanning months (a `run-compare` resumed in a later month) do not place it, and
  the month's figure becomes a floor naming it. A ledger on
  another machine, or not passed, is not seen; with none passed the bucket is NOT READ, never $0.
  A ledger that is another's bytes, or an earlier prefix of them (a copy taken before more draws),
  counts once.
- **theme desk** — `registry/llm_calls.jsonl` on the `theme-intelligence-state` branch, which the
  weekly CI run and a local `state push` write: one row per call, `cost_usd` and `at`. That is
  what makes CI's spend visible here. A local run not yet pushed to the branch, or a push since
  the local ref was fetched, is not seen; the source names the commit read.
- **graph judge** — `judged_by` in the committed `data/graph_coverage.json` (`graph-rejudge`). Each
  run OVERWRITES it and a re-judge that STOPPED writes nothing, so only the latest recorded
  re-judge is seen: its month is a floor ("≥"), every other month is NOT READ, and so is a map
  with no `judged_by` (a `graph-coverage --json` run writes one). `graph-coverage` records no cost.
- **validate-keys** — a one-token billable ping per CI run, recorded nowhere: NOT RECORDED.

Each bucket prints what its `rows` column counts, since the units differ. The total is neither a
floor nor exact for one month: it leaves out what each bucket cannot see, and a page build is
dated by its start. Months are UTC calendar months. Every figure is list price
(`vinci.config.LLM_PRICE_PER_MTOK`), as each writer priced it. A malformed record raises — a
report that skipped what it could not read would print a total smaller than the spend.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

THEME_REF = "origin/theme-intelligence-state"
THEME_CALLS = "registry/llm_calls.jsonl"
#: The folders searched for budget ledgers when no `--evals-root` is given, `os.pathsep`-joined.
#: The ledgers live outside the repo on purpose, so their folders are a machine's, never code's.
LEDGER_ROOTS_ENV = "VINCI_LEDGER_ROOTS"


class SpendRecordError(ValueError):
    """A spend record this report cannot read. Raised, never skipped."""


@dataclass
class Bucket:
    """One bucket's month. ``usd`` is None when the bucket's spend is not recorded or was not
    read — a missing number, never a zero."""

    name: str
    usd: float | None
    rows: int
    source: str
    cannot_see: str
    unpriced: int = 0
    note: str = ""
    sources_read: list[str] = field(default_factory=list)
    #: What the ``rows`` column counts for this bucket — the units differ by bucket.
    counts: str = ""
    #: Further lines printed under the bucket: for evals, every root searched and ledger read.
    detail: list[str] = field(default_factory=list)
    #: Spend that may belong to this month and is NOT in ``usd`` (each a phrase naming it). Any
    #: entry makes ``usd`` a floor: printed "≥", and the total "at least".
    unknown: list[str] = field(default_factory=list)


def _instant(stamp: str, where: str) -> datetime:
    """An ISO timestamp as an aware UTC instant; a naive stamp is refused."""
    try:
        t = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise SpendRecordError(f"{where}: {stamp!r} is not an ISO timestamp") from exc
    if t.tzinfo is None:
        raise SpendRecordError(f"{where}: {stamp!r} carries no UTC offset, so its month is unknown")
    return t.astimezone(UTC)


def _month_of(stamp: str, where: str) -> str:
    """The UTC calendar month (``YYYY-MM``) of an ISO timestamp; a naive stamp is refused."""
    return f"{_instant(stamp, where):%Y-%m}"


def _jsonl(text: str, where: str) -> list[dict[str, Any]]:
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SpendRecordError(f"{where}:{i}: not JSON ({exc.msg})") from exc
        if not isinstance(row, dict):
            raise SpendRecordError(f"{where}:{i}: a row is not an object")
        out.append(row)
    return out


def _usd(value: Any, where: str, *, nullable: bool = False) -> float | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SpendRecordError(f"{where}: usd is {value!r}, not a number")
    return float(value)


def pages(snapshots: Path, month: str) -> Bucket:
    """The dossier builds: every line of every committed assembly run, dated by ``started_at``."""
    runs = sorted((snapshots / "assembly_runs").glob("*.jsonl"))
    if not runs:
        return Bucket("pages", None, 0, f"{snapshots}/assembly_runs/*.jsonl", _PAGES_CANNOT,
                      note="NOT READ: no assembly run file there", counts=_PAGES_COUNTS)
    usd, rows, unpriced = 0.0, 0, 0
    read: set[str] = set()
    for path in runs:
        for i, r in enumerate(_jsonl(path.read_text(encoding="utf-8"), path.name), 1):
            where = f"{path.name}:{i}"
            if "usd" not in r or "started_at" not in r:
                raise SpendRecordError(f"{where}: an assembly line without usd or started_at")
            if _month_of(str(r["started_at"]), where) != month:
                continue
            rows += 1
            read.add(path.name)
            cost = _usd(r["usd"], where, nullable=True)
            if cost is None:
                unpriced += 1
            else:
                usd += cost
    return Bucket("pages", round(usd, 4), rows, "data/snapshots/assembly_runs/*.jsonl",
                  _PAGES_CANNOT, unpriced=unpriced,
                  note=f"{len(read)} of {len(runs)} run files carry a line in the month",
                  sources_read=sorted(read), counts=_PAGES_COUNTS)


_PAGES_CANNOT = "a build whose run file was not committed"
_PAGES_COUNTS = "build lines, one per name a build attempted"


def confirmations(snapshots: Path, month: str) -> Bucket:
    """The seal-time confirmations: counted by ``drawn_at``, never priced — no cost is written."""
    path = snapshots / "proposal_confirmations.jsonl"
    rows = 0
    if path.exists():
        for i, r in enumerate(_jsonl(path.read_text(encoding="utf-8"), path.name), 1):
            if _month_of(str(r.get("drawn_at")), f"{path.name}:{i}") == month:
                rows += 1
    return Bucket("confirmations", None, rows, f"data/snapshots/{path.name}",
                  "every cost: a row carries no usd or usage, and a confirmation refused after "
                  "its draws writes no row",
                  note=("NOT RECORDED" if path.exists() else
                        f"NOT RECORDED; no {path.name} is committed"),
                  counts="confirmation rows")


def is_ledger(path: Path) -> bool:
    """A budget ledger's first line is its approval (`Budget.open`)."""
    with path.open(encoding="utf-8") as f:
        first = f.readline()
    try:
        row = json.loads(first)
    except json.JSONDecodeError:
        return False
    return isinstance(row, dict) and "approval" in row


_EVALS_CANNOT = ("a ledger not passed here, or kept on another machine; and the month of an "
                 "undated draw whose bounding stamps (or the ledger's last write) span months — "
                 "named as may-belong, never placed")


def evals(ledgers: Iterable[Path], month: str, *, roots: Sequence[str] = ()) -> Bucket:
    """The evals harness's budget ledgers, each undated draw bounded by the stamps around it.

    No ledger at all is NOT READ (``usd`` None), never $0. A ledger whose text is another's, or
    an earlier prefix of it (a copy taken before the budget drew more), is that ledger and counts
    once: the ledger only ever grows by appending. Every root searched and every ledger read is
    printed, so the report never claims a search wider than the one it made."""
    usd, rows, draws, read = 0.0, 0, 0, []
    searched = [f"searched: {r}" for r in roots] or ["searched: no root (--evals-root, or "
                                                     f"{LEDGER_ROOTS_ENV})"]
    texts: dict[Path, str] = {p: p.read_text(encoding="utf-8")
                              for p in sorted({p.resolve() for p in ledgers})}
    if not texts:
        return Bucket("evals", None, 0, "budget ledgers passed to this run", _EVALS_CANNOT,
                      note="NOT READ: no budget ledger found (--evals-ledger, --evals-root, or "
                           f"{LEDGER_ROOTS_ENV})", counts=_EVALS_COUNTS, detail=searched)
    kept: dict[Path, str] = {}
    for path, text in texts.items():
        if any(other.startswith(text) and (len(other) > len(text) or (other == text and o < path))
               for o, other in texts.items() if o != path):
            continue
        kept[path] = text
    # THE TIGHTEST LAST WRITE OF A LEDGER'S BYTES: a byte-identical copy was complete by its own
    # file time too, so the earliest of them bounds the draws, whichever path sorts first
    mtimes: dict[str, float] = {}
    for p, t in texts.items():
        mtimes[t] = min(mtimes.get(t, float("inf")), p.stat().st_mtime)
    duplicates = len(texts) - len(kept)
    detail = searched + [f"copy of another ledger, not counted again: {p}"
                         for p in texts if p not in kept]
    unplaced, unplaced_usd = 0, 0.0
    for path, text in kept.items():
        body = _jsonl(text, path.name)
        if not body or not isinstance(body[0].get("approval"), dict):
            raise SpendRecordError(f"{path}: not a budget ledger (its first line is no approval)")
        rows_ = body[1:]
        for i, r in enumerate(rows_, 2):
            if "usd" not in r:
                raise SpendRecordError(f"{path.name}:{i}: a ledger row without usd")
        # EVERY ROW'S TIME IS BOUNDED, NEVER GUESSED (Codex P1 on #1061): a stamped row (the
        # approval, a `build_start`, a `build_end`) is dated by its own stamp; a draw carries none,
        # so it lies after the stamp above it and before its own build's `build_end` below it —
        # or the file's last write, the latest any row in it can have been appended. A
        # `build_start` is no UPPER bound: its time is taken before its request is captured,
        # under a lock a concurrent build's draws do not take, so a draw appended above it can be
        # later than its stamp.
        # Within one month a row is that month's; a span across months is NOT placed: a resumed
        # `run-compare` must not land in the month its ledger was opened.
        stamps = [_row_stamp(r, f"{path.name}:{i}") for i, r in enumerate(rows_, 2)]
        opened = _instant(str(body[0]["approval"].get("opened_at")), f"{path.name}:1")
        lower: list[datetime] = []          # the latest stamp at or above each row
        below = opened
        for own_ in stamps:
            below = below if own_ is None else own_
            lower.append(below)
        # the first `build_end` below each row OF ITS OWN BUILD, matched by label, or the last
        # write: a `build_end`'s `t` is taken before its row is written, with no lock held over
        # the draws, so another command's draw appended just above it can be later (Codex P2)
        upper: list[datetime] = []
        last_write = datetime.fromtimestamp(mtimes[text], UTC)
        ends_below: dict[str, datetime] = {}
        for k in reversed(range(len(rows_))):
            label = rows_[k].get("label")
            upper.append(ends_below.get(label, last_write) if isinstance(label, str)
                         else last_write)
            end, at = rows_[k].get("build_end"), stamps[k]
            if isinstance(end, dict) and isinstance(end.get("label"), str) and at is not None:
                ends_below[end["label"]] = at
        upper.reverse()
        in_month = False
        led_usd, led_draws, led_unplaced = 0.0, 0, 0
        for k, r in enumerate(rows_):
            where = f"{path.name}:{k + 2}"
            cost = _usd(r["usd"], where)
            assert cost is not None
            own = stamps[k]
            lo, hi = (own, own) if own is not None else (lower[k], upper[k])
            first, last = sorted((f"{lo:%Y-%m}", f"{hi:%Y-%m}"))
            if first == last == month:
                in_month = True
                usd += cost
                led_usd += cost
                rows += 1
                if "draw" in r:
                    draws += 1
                    led_draws += 1
            elif first != last and first <= month <= last and cost:
                unplaced += 1
                unplaced_usd += cost
                led_unplaced += 1
        if in_month:
            read.append(path.name)
        detail.append(f"read: {path} — {led_draws} draw(s) in the month, ${led_usd:,.2f}"
                      + (f"; {led_unplaced} undated row(s) may belong to it" if led_unplaced
                         else ""))
    return Bucket("evals", round(usd, 4), rows, "budget ledgers passed to this run", _EVALS_CANNOT,
                  note=(f"{len(read)} of {len(kept)} ledger(s) read carry a row in the month; "
                        f"{draws} of the {rows} row(s) are draws, the rest zero-cost "
                        "registration and build rows"
                        + (f"; {duplicates} copy(ies) of another ledger (byte-identical or its "
                           "earlier prefix) counted once" if duplicates else "")),
                  sources_read=read, counts=_EVALS_COUNTS, detail=detail,
                  unknown=([f"{unplaced} undated row(s) in evals (${unplaced_usd:,.2f}) that ran "
                            "across a month boundary and may belong to this month"]
                           if unplaced else []))


def _row_stamp(r: dict[str, Any], where: str) -> datetime | None:
    """A ledger row's own time, or None: a `build_start`'s ``started_at``, or a `build_end`'s
    ``t`` (epoch seconds, `time.time`). A draw row carries none."""
    start = r.get("build_start")
    if isinstance(start, dict) and start.get("started_at"):
        return _instant(str(start["started_at"]), where)
    end = r.get("build_end")
    if isinstance(end, dict) and isinstance(end.get("t"), (int, float)) \
            and not isinstance(end.get("t"), bool):
        return datetime.fromtimestamp(float(end["t"]), UTC)
    return None


_EVALS_COUNTS = "ledger rows (draws, and zero-cost registration and build rows)"


def theme_desk(repo: Path, month: str, ref: str = THEME_REF) -> Bucket:
    """The theme desk's per-call rows, read from its state branch with `git show`."""
    proc = subprocess.run(["git", "show", f"{ref}:{THEME_CALLS}"], cwd=repo,
                          capture_output=True, text=True, timeout=60)
    if proc.returncode:
        err = proc.stderr.strip()
        err = err if len(err) <= 160 else f"{err[:160]}… (first 160 of {len(err)} characters)"
        return Bucket("theme desk", None, 0, f"{ref}:{THEME_CALLS}", _THEME_CANNOT,
                      note=f"NOT READ: {err} — fetch the branch "
                           "(`git fetch origin theme-intelligence-state`)",
                      counts="call rows, one per model call (cache hits included)")
    sha = subprocess.run(["git", "rev-parse", "--short=8", ref], cwd=repo, capture_output=True,
                         text=True, timeout=60, check=True).stdout.strip()
    return theme_calls(proc.stdout, month, source=f"{ref}@{sha}:{THEME_CALLS}")


_THEME_CANNOT = ("a local theme run not yet pushed to the state branch, and any push since the "
                 "local ref was last fetched")


def theme_calls(text: str, month: str, *, source: str) -> Bucket:
    """The month's rows of an exported ``llm_calls.jsonl``: each row's ``payload`` (a JSON string)
    carries ``at`` and ``cost_usd``. The desk's own rule (`pipeline.py`): a cache hit spends nothing
    now; a live call with no cost is unpriced, counted apart and never as zero."""
    usd, rows, cached, unpriced = 0.0, 0, 0, 0
    for i, r in enumerate(_jsonl(text, THEME_CALLS), 1):
        where = f"{THEME_CALLS}:{i}"
        try:
            call = json.loads(r["payload"]) if isinstance(r.get("payload"), str) else r
        except json.JSONDecodeError as exc:
            raise SpendRecordError(f"{where}: its payload is not JSON") from exc
        if "cost_usd" not in call or "at" not in call:
            raise SpendRecordError(f"{where}: a call row without cost_usd or at")
        if _month_of(str(call["at"]), where) != month:
            continue
        rows += 1
        cached += bool(call.get("cached"))
        cost = _usd(call["cost_usd"], where, nullable=True)
        if cost is not None:
            usd += cost
        elif not call.get("cached"):
            unpriced += 1       # a cache hit with no cost spent nothing now; it is not unpriced
    return Bucket("theme desk", round(usd, 4), rows, source, _THEME_CANNOT, unpriced=unpriced,
                  note=f"{cached} of {rows} call row(s) served from its cache",
                  counts="call rows, one per model call (cache hits included)")


def graph_judge(data_dir: Path, month: str) -> Bucket:
    """The graph re-judge's one recorded run, from the committed coverage map. Only the month the
    recorded re-judge is in is read, and as a floor; every other month, and a map with no
    ``judged_by`` (a `graph-coverage --json` run rewrites the map without one), is NOT READ,
    never $0."""
    path = data_dir / "graph_coverage.json"
    cannot = ("an earlier re-judge (each run overwrites the last), a re-judge STOPPED before it "
              "wrote (over budget, or a judge error), and any `graph-coverage` run")
    counts = "re-judge runs recorded"

    def bucket(usd: float | None, rows: int, note: str) -> Bucket:
        return Bucket("graph judge", usd, rows, f"data/{path.name}", cannot, note=note,
                      counts=counts)

    if not path.exists():
        return bucket(None, 0, f"NOT READ: no {path.name}")
    judged = json.loads(path.read_text(encoding="utf-8")).get("judged_by")
    if not isinstance(judged, dict):
        return bucket(None, 0, "NOT READ: the map records no re-judge (a `graph-coverage` run "
                               "rewrites it without one), so a re-judge's cost may be overwritten")
    on = f"{judged.get('on', '')}"[:7]
    if month < on:
        return bucket(None, 0, f"NOT READ: the re-judge of {judged.get('on')} overwrote any "
                               "earlier one")
    if month > on:
        # a re-judge that STOPPED (over budget, or a judge error) spent and wrote nothing, so no
        # later month can be shown to be $0 (Codex P1 on #1061)
        return bucket(None, 0, f"NOT READ: the latest recorded re-judge is {judged.get('on')}; "
                               "a later one that stopped wrote no record")
    cost = _usd(judged.get("cost_usd"), f"{path.name}: judged_by")
    b = bucket(cost, 1, f"the re-judge of {judged.get('on')}, {judged.get('billed_calls')} "
                        "billed call(s)")
    # the same month holds the same blind spot: an earlier re-judge it overwrote, or a stopped one
    b.unknown = ["any earlier or stopped re-judge in graph judge this month"]
    return b


def validate_keys() -> Bucket:
    return Bucket("validate-keys", None, 0, "none", "every run: a one-token billable ping per "
                  "CI run is recorded nowhere", note="NOT RECORDED", counts="nothing is recorded")


#: The six buckets, in the order the report prints them.
BUCKETS = ("pages", "confirmations", "evals", "theme desk", "graph judge", "validate-keys")


def report(month: str, *, repo: Path, snapshots: Path, data_dir: Path,
           ledgers: Sequence[Path], theme_ref: str = THEME_REF,
           roots: Sequence[str] = ()) -> list[Bucket]:
    if (len(month) != 7 or month[4] != "-" or not (month[:4] + month[5:]).isdigit()
            or not 1 <= int(month[5:]) <= 12):
        raise SpendRecordError(f"--month {month!r}: expected YYYY-MM")
    return [pages(snapshots, month), confirmations(snapshots, month),
            evals(ledgers, month, roots=roots), theme_desk(repo, month, theme_ref),
            graph_judge(data_dir, month), validate_keys()]


def render(month: str, buckets: Sequence[Bucket]) -> str:
    lines = [f"spend report, {month} (UTC calendar month, list price) — reports, refuses nothing",
             "", f"{'bucket':<14} {'usd':>10} {'rows':>6}  source"]
    for b in buckets:
        # a bucket with unpriced rows knows only a floor of its spend: "≥", never a plain figure
        floor = bool(b.unpriced or b.unknown)
        usd = ("—" if b.usd is None else f"≥${b.usd:,.2f}" if floor else f"${b.usd:,.2f}")
        lines.append(f"{b.name:<14} {usd:>10} {b.rows:>6}  {b.source}")
        extra = [b.note] if b.note else []
        if b.unpriced:
            extra.append(f"{b.unpriced} row(s) unpriced, not counted as zero")
        if b.counts:
            extra.append(f"rows: {b.counts}")
        for x in [*extra, *b.detail]:
            lines.append(f"{'':<33}{x}")
        lines.append(f"{'':<33}cannot see: {b.cannot_see}")
    seen = [b for b in buckets if b.usd is not None]
    blind = [b.name for b in buckets if b.usd is None]
    total = sum(b.usd for b in seen if b.usd is not None)
    partial = [x for b in seen for x in
               ([f"{b.unpriced} unpriced row(s) in {b.name}"] if b.unpriced else []) + b.unknown]
    figure = (f"at least ${total:,.2f} — {', '.join(partial)} are not in it" if partial
              else f"${total:,.2f}")
    lines += ["", f"total of the {len(seen)} bucket(s) read: {figure}"
              + (f" — NOT included: {', '.join(blind)}" if blind else ""),
              "neither a floor nor exact for one month: it leaves out what each bucket cannot "
              "see, and a page build is dated by its start, so one running past midnight on the "
              "month's last day is the earlier month's"]
    return "\n".join(lines)


def ledger_roots(roots: Sequence[str]) -> list[str]:
    """The roots to search: those given, else the ``VINCI_LEDGER_ROOTS`` folders."""
    if roots:
        return list(roots)
    return [r for r in os.environ.get(LEDGER_ROOTS_ENV, "").split(os.pathsep) if r.strip()]


def _ledgers(paths: Sequence[str], roots: Sequence[str]) -> list[Path]:
    out = [Path(p) for p in paths]
    for root in roots:
        out += [p for p in sorted(Path(root).rglob("*.jsonl")) if is_ledger(p)]
    return out


def main(argv: Sequence[str] | None = None) -> int:
    from vinci.config import get_config

    p = argparse.ArgumentParser(prog="python -m vinci.spend", description=__doc__.split("\n")[0])
    p.add_argument("--month", required=True, help="YYYY-MM (UTC)")
    p.add_argument("--evals-ledger", action="append", default=[], help="a budget ledger file")
    p.add_argument("--evals-root", action="append", default=[],
                   help="every budget ledger (*.jsonl whose first line is an approval) under it; "
                        f"default: the {LEDGER_ROOTS_ENV} folders")
    p.add_argument("--theme-ref", default=THEME_REF)
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    repo = Path(__file__).resolve().parents[1]
    # THE REPO'S OWN DATA, wherever the command is run from: the config's `data` is relative, and
    # read from another folder it found no run file and printed the pages as $0.00 (review).
    data = get_config().data_dir
    data_dir = data if data.is_absolute() else repo / data
    roots = ledger_roots(a.evals_root)
    buckets = report(a.month, repo=repo, snapshots=data_dir / "snapshots", data_dir=data_dir,
                     ledgers=_ledgers(a.evals_ledger, roots), theme_ref=a.theme_ref, roots=roots)
    if a.json:
        print(json.dumps({"month": a.month, "buckets": [asdict(b) for b in buckets]}, indent=1))
    else:
        print(render(a.month, buckets))
    return 0


if __name__ == "__main__":
    sys.exit(main())
