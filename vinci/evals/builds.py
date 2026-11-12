"""One request per page, drawn as SEPARATE BUILDS under a registration written before any draw.

The vote-rule design's independence measurement (`docs/records/2026-11-10-the-proposal-vote-rule-
design.md` §7) draws each panel page's request in several production-shaped builds — each its own
run of N draws, opening on an uncached draw as a production build does — and asks whether the
per-build lean counts are overdispersed against the binomial. `compare` cannot serve it: there is
one condition, not two, and `compare` refuses when no page's request differs.

So a ``RunRegistration`` pins, before any draw:

- the commit the requests are captured at (`code_ref`, resolved), the named transforms
  (`variants.py`) and the CIQ root the frozen inputs were read from (`inputs`);
- each page's request as sent (`requests`: sha256 of `Request.wire`);
- the draws per build, the builds per page, and the least time between two builds of one page
  (`min_gap_s`, at least the prompt cache's lifetime, `synthesis._CACHE_TTL_S`).

`run_build` draws ONE build of ONE page, and refuses — before any spend — a page or build the
registration does not name, a build already drawn under it, a page's builds out of order, a
re-capture whose bytes are not the pinned ones, and a build starting sooner than `min_gap_s`
after that page's previous build ended. Each build writes a start row and, even when it stops, an
end row into the approval's ledger: when it started, the gap since that page's previous build, and
the first draw's cache-read tokens (0 is an uncached opening, shown rather than assumed).

The gap is per REQUEST: the prompt cache is keyed by the prompt, so only a build of the same
request can warm it; builds of other pages may run between. Under one approval's ledger a request
is drawn under ONE registration (a second registration of the same bytes is refused, whatever its
note), and one build is checked and claimed at a time (a lock beside the ledger). A build of the
same bytes under ANOTHER approval's ledger is not visible here; the index refuses a registration
whose every request another registration drew (`registry.claim_draw`, #1030 review round 2), and
the first draw's recorded cache-read tokens are what show whether a build opened uncached.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import subprocess
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vinci.dossier.synthesis import _CACHE_TTL_S
from vinci.evals import replay as rp


def request_sha(req: rp.Request) -> str:
    """The pin: the sha256 of the request serialised in order (`Request.wire`), as `compare`'s."""
    return hashlib.sha256(req.wire().encode()).hexdigest()


@dataclass(frozen=True)
class RunRegistration:
    """What a one-condition, multi-build run draws — written once, before any draw."""

    code_ref: str
    transforms: tuple[str, ...]
    pages: tuple[str, ...]
    draws: int
    builds: int
    min_gap_s: float
    requests: dict[str, str]
    inputs: dict[str, Any] = field(default_factory=dict)
    #: What the registration states in words before the draw. Part of the sha.
    note: str | None = None

    def __post_init__(self) -> None:
        if self.draws < 2 or self.builds < 2:
            raise ValueError("a build registration needs at least two draws a build and two "
                             "builds a page: one build cannot show variation between builds")
        if not self.pages or len(set(self.pages)) != len(self.pages):
            raise ValueError(f"pages {list(self.pages)}: at least one, none twice")
        if self.min_gap_s < _CACHE_TTL_S:
            raise ValueError(f"a gap of {self.min_gap_s:.0f}s between a page's builds is inside "
                             f"the prompt cache lifetime ({_CACHE_TTL_S:.0f}s): the next build "
                             "would open on a cached draw, which a production build never does")
        if set(self.requests) != set(self.pages):
            raise ValueError("every registered page needs exactly one pinned request")
        if not self.inputs.get("ciq_root"):
            # Codex round 1 (#958): without it `run` would read at a root never registered
            raise ValueError("a build registration records the CIQ root its requests were "
                             "captured from (inputs.ciq_root); `register-run` writes it")

    def to_json(self) -> str:
        return json.dumps({"kind": "builds", **self.__dict__}, sort_keys=True, default=list)

    @property
    def sha(self) -> str:
        return hashlib.sha256(self.to_json().encode()).hexdigest()

    @classmethod
    def from_json(cls, text: str) -> RunRegistration:
        d: dict[str, Any] = json.loads(text)
        if d.pop("kind", None) != "builds":
            raise rp.ReplayError("not a build registration (`register-run` writes one)")
        fields: dict[str, Any] = {k: tuple(v) if isinstance(v, list) else v for k, v in d.items()}
        return cls(**fields)


def draw_key(reg: RunRegistration) -> str:
    """A build registration's DESIGN, the index's drawn-once key (#1030 review round 1, item 1):
    everything but its words (`note`) and its record of what was read (`inputs`, a path's
    spelling included), so one design re-registered with new words is refused under a second
    approval once its first has drawn. Its pages are a set: the order they were given in draws
    nothing different (#1030 review round 2, F2)."""
    d = {k: v for k, v in json.loads(reg.to_json()).items() if k not in ("note", "inputs")}
    d["pages"] = sorted(d["pages"])
    return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()


def _resolve(code_ref: str, repo: Path = rp.ROOT) -> str:
    done = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify",
                           f"{code_ref}^{{commit}}"], capture_output=True, text=True)
    if done.returncode != 0:
        raise rp.ReplayError(f"{code_ref!r} is not a commit here: {done.stderr.strip()}")
    return done.stdout.strip()


def capture_request(code_ref: str, ticker: str, *, transforms: Sequence[str], draws: int,
                    ciq_root: Path) -> rp.Request:
    """The page's request at ``code_ref``'s code, from the frozen inputs read at ``ciq_root`` —
    the transcripts and, where a transform reads them, the page's own comps export and CIQ folder
    (as `compare`)."""
    page, tx = rp.panel_inputs(ticker, ciq_root=ciq_root)
    comps = rp.comps_export(ticker, ciq_root=ciq_root) if transforms else None
    ciq = (Path(ciq_root) / ticker) if transforms and (Path(ciq_root) / ticker).is_dir() else None
    return rp.capture_at(code_ref, page, tx, draws=draws, transforms=transforms, comps=comps,
                         ciq=ciq)


def register_run(*, code_ref: str, pages: Sequence[str], transforms: Sequence[str], draws: int,
                 builds: int, min_gap_s: float, ciq_root: Path,
                 note: str | None = None) -> RunRegistration:
    """$0: capture each page's request and pin it. The ref is resolved to its commit, so the
    registration names the code it pinned, never a branch that may move."""
    sha = _resolve(code_ref)
    reqs = {t: capture_request(sha, t, transforms=transforms, draws=draws, ciq_root=ciq_root)
            for t in pages}
    return RunRegistration(code_ref=sha, transforms=tuple(transforms), pages=tuple(pages),
                           draws=draws, builds=builds, min_gap_s=float(min_gap_s),
                           requests={t: request_sha(r) for t, r in reqs.items()},
                           inputs={"ciq_root": str(Path(ciq_root).resolve())}, note=note)


def write_registration(reg: RunRegistration, path: Path) -> None:
    rp.refuse_inside_repo(path, "the registration")
    if path.exists():
        raise rp.ReplayError(f"{path} exists: a registration is written once, before any draw")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(reg.to_json(), encoding="utf-8")


def _build_rows(budget: rp.Budget, sha: str, key: str) -> list[dict[str, Any]]:
    return [r[key] for r in budget.rows() if key in r and r[key].get("registration") == sha]


def build_row(budget: rp.Budget, reg: RunRegistration, key: str, ticker: str,
              build: int) -> dict[str, Any]:
    """The ledger's ``build_start`` or ``build_end`` row for one build (one each, by
    construction: a build is drawn once)."""
    (row,) = [r for r in _build_rows(budget, reg.sha, key)
              if r["ticker"] == ticker and r["build"] == build]
    return row


@dataclass(frozen=True)
class PreparedBuild:
    """A build every refusal has passed, with its pinned request — nothing drawn yet."""

    request: rp.Request
    label: str
    gap_s: float | None
    t: float


def prepare_build(reg: RunRegistration, ticker: str, build: int, *, budget: rp.Budget,
                  ciq_root: Path, clock: Callable[[], float] = time.time) -> PreparedBuild:
    """$0: every refusal `run_build` makes before a draw, and the capture checked against its pin.
    `run` without ``--paid`` stops here."""
    if ticker not in reg.pages:
        raise rp.ReplayError(f"{ticker} is not a registered page ({list(reg.pages)})")
    if not 1 <= build <= reg.builds:
        raise rp.ReplayError(f"build {build}: the registration registers {reg.builds} builds a "
                             "page, numbered from 1")
    pin = reg.requests[ticker]
    # ONE APPROVAL DRAWS A REQUEST ONCE (review round 0): a second registration of the same bytes —
    # a reworded note gives it a new sha — is the same design, as `compare.run_compare` holds.
    elsewhere = sorted({r["build_start"]["registration"][:12] for r in budget.rows()
                        if "build_start" in r and r["build_start"].get("request") == pin
                        and r["build_start"]["registration"] != reg.sha})
    if elsewhere:
        raise rp.ReplayError(f"{ticker}'s request was drawn under {elsewhere} in this ledger: a "
                             "request is drawn once per approval, whatever registration names it")
    started = [r for r in _build_rows(budget, reg.sha, "build_start") if r["ticker"] == ticker]
    if any(r["build"] == build for r in started):
        raise rp.ReplayError(f"{ticker} build {build} under {reg.sha[:12]} is in the ledger: a "
                             "build is drawn once — re-drawing it is result-shopping")
    if len(started) != build - 1:
        raise rp.ReplayError(f"{ticker}: build {build} before build {len(started) + 1} — a "
                             "page's builds are drawn in order")
    ended = {r["build"]: r for r in _build_rows(budget, reg.sha, "build_end")
             if r["ticker"] == ticker}
    now = clock()
    if build > 1 and build - 1 not in ended:
        raise rp.ReplayError(f"{ticker} build {build - 1} has no end in the ledger, so the "
                             "gap since its last draw cannot be shown")
    # The cache is keyed by the request, not the registration: every build of these bytes the
    # ledger records counts (review round 0; another registration's are refused above).
    ends = [float(r["build_end"]["t"]) for r in budget.rows()
            if "build_end" in r and r["build_end"].get("request") == pin]
    ends += [float(ended[build - 1]["t"])] if build > 1 else []
    gap: float | None = now - max(ends) if ends else None
    if gap is not None and gap < reg.min_gap_s:
        raise rp.ReplayError(f"{ticker} build {build} would start {gap:.0f}s after the last "
                             "build of its request ended, inside the registered "
                             f"{reg.min_gap_s:.0f}s: it would open on a cached draw")
    req = capture_request(reg.code_ref, ticker, transforms=reg.transforms, draws=reg.draws,
                          ciq_root=ciq_root)
    if request_sha(req) != reg.requests[ticker]:
        raise rp.ReplayError(f"{ticker}: the captured request is not the registered bytes — the "
                             "code or inputs moved since registration; a new registration, never "
                             "a draw under this one")
    return PreparedBuild(req, f"{reg.sha[:12]}:{ticker}:build{build}", gap, now)


@contextmanager
def _claim(ledger: Path) -> Iterator[None]:
    """One build checked and claimed at a time under a ledger (review round 0): without it two
    `run`s of one build both pass the drawn-once check during their captures and both draw. A
    second claim is refused at once, never queued behind the first."""
    with ledger.with_name(ledger.name + ".lock").open("a") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise rp.ReplayError(f"another run holds {ledger}: one build is checked and claimed "
                                 "at a time — wait for it, then run again") from exc
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def run_build(reg: RunRegistration, ticker: str, build: int, *, budget: rp.Budget,
              draws_out: Path, ciq_root: Path, sdk: Any | None = None,
              clock: Callable[[], float] = time.time,
              claim: Callable[[], object] | None = None) -> list[dict[str, Any] | None]:
    """PAID: build ``build`` of ``ticker`` — ``reg.draws`` draws of the pinned request through
    `replay.run_request`, every refusal (`prepare_build`) made before the first one is sent. The
    end row is written even when the build stops, so the next build's gap is measured from it.
    ``claim`` (the index's `registry.claim_draw`) is called under the lock once every $0 refusal
    has passed, so a refused build never consumes its unit."""
    from vinci.evals import gold as gd
    gd.verify_committed_gold()   # RG-D11: the gold's hashes, before any paid draw (gap 4)
    with _claim(budget.ledger):   # the check and the claim (the start row) are one step
        pb = prepare_build(reg, ticker, build, budget=budget, ciq_root=ciq_root, clock=clock)
        if claim is None and rp.paid_draw(sdk):   # RG-D9 in the library (B's review of #1030)
            raise rp.ReplayError(f"{pb.label}: a paid build needs its index claim "
                                 "(`registry.claim_draw`, after `registry.require_on_main`) — "
                                 "unclaimed, it could be drawn twice, so nothing is drawn")
        if claim is not None:
            claim()
        head = {"registration": reg.sha, "ticker": ticker, "build": build, "label": pb.label,
                "request": reg.requests[ticker]}
        budget.record({"build_start": {**head, "t": pb.t, "gap_s": pb.gap_s,
                                       "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z",
                                                                   time.localtime(pb.t))},
                       "usd": 0.0})
    raws: list[dict[str, Any] | None] = []
    stopped = True
    try:
        raws = rp.run_request(pb.request, draws=reg.draws, budget=budget, label=pb.label,
                              draws_out=draws_out, sdk=sdk, registration=reg.sha)
        stopped = False
    finally:
        drawn = [r for r in budget.rows() if r.get("label") == pb.label and "usage" in r]
        first = next((r for r in drawn if r.get("draw") == 1), None)
        budget.record({"build_end": {
            **head, "t": clock(), "draws": len(drawn),
            # a stopped build's usable count is not known: run_request did not return
            "usable": None if stopped else sum(x is not None for x in raws),
            "first_draw_cache_read": (first["usage"].get("cache_read_input_tokens")
                                      if first is not None else None),
            "stopped": stopped}, "usd": 0.0})
    return raws
