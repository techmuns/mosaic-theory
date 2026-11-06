"""Rebuild a panel page's synthesis request at $0, prove it against a logged build, and run paid
draws only under a budget guard. Re-derived from #920's record (§1-§2, §7) — its scripts were local.

$0, ALWAYS FIRST. ``capture`` builds the exact request production would send for a page
(`capture_child.capture_calls`) and nothing leaves the machine. ``capture_at`` does the same at
another commit's code, in a child process. ``prove`` compares a capture with a logged build's
SYSTEM, USER, model and max_tokens by length, full sha256 and a unified diff.

PAID, ONLY BEHIND ``GuardedSdk``. Before forwarding each request the guard (1) asserts it EQUALS
the request captured at $0 for that page and code, and (2) refuses it when spend so far plus the
worst case of one more draw would cross the cap. After each response it checks the served model,
prices the call with production's ``cost_usd`` and appends to a spend ledger outside the repo.
``BudgetStop`` is a ``BaseException``, so ``synthesize`` — which survives an ``LlmError`` draw —
cannot swallow it: the run stops.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vinci.config import LLM_PRICE_PER_MTOK
from vinci.dossier.schemas import MechanicalLayer
from vinci.evals.capture_child import DEFAULT_MAX_TOKENS, DEFAULT_MODEL, capture_calls, jsonable
from vinci.graph.llm import cost_usd

ROOT = Path(__file__).resolve().parents[2]
PANEL_FILE = Path(__file__).resolve().parent / "synthesis_panel.json"
#: The assembler's CIQ copy, which every build reads (RUNBOOKS preamble).
DEFAULT_CIQ_ROOT = Path.home() / "Documents/GitHub/mosaic-theory-ta/data/manual/ciq"

#: The most characters any logged prompt packed into one token, less a margin: the guard's bound
#: on a prompt's size before its first response reports the real count. Measured over the eight
#: logged builds (record §RESULTS, "chars per token"); a SMALLER ratio is the conservative side.
CHARS_PER_TOKEN_FLOOR = 2.0

#: #865: from this commit on, ``assemble`` marks material rows BEFORE ``synthesize`` reads them.
#: A capture at an older ref clears the committed page's marks (`capture_child.pre_synthesis_mech`).
MATERIAL_MARKED_BEFORE_SYNTHESIS = "a15a2abf"


class ReplayError(RuntimeError):
    """The replay's inputs are not the frozen ones, or two captures disagree."""


class BudgetStop(BaseException):  # noqa: N818 — a stop, not an error; must escape `synthesize`
    """A paid draw refused: over the cap, or a request that is not the one captured at $0."""


# --------------------------------------------------------------------------------------- inputs

def git_show(ref: str, path: str, repo: Path = ROOT) -> bytes:
    return subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{path}"],
                          capture_output=True, check=True).stdout


def git_blob(ref: str, path: str, repo: Path = ROOT) -> str:
    return subprocess.run(["git", "-C", str(repo), "rev-parse", f"{ref}:{path}"],
                          capture_output=True, text=True, check=True).stdout.strip()


def page_at(ticker: str, ref: str, *, expect_blob: str | None = None,
            repo: Path = ROOT) -> dict[str, Any]:
    """``data/dossiers/<T>/dossier.json`` as committed at ``ref``; refuses a blob other than the
    frozen one when ``expect_blob`` is given."""
    path = f"data/dossiers/{ticker}/dossier.json"
    if expect_blob is not None and (got := git_blob(ref, path, repo)) != expect_blob:
        raise ReplayError(f"{ticker}: {path} at {ref} is blob {got}, the panel froze {expect_blob}")
    page: dict[str, Any] = json.loads(git_show(ref, path, repo))
    return page


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def transcript_for(ticker: str, *, ciq_root: Path = DEFAULT_CIQ_ROOT,
                   expected: Sequence[dict[str, str]] | None = None,
                   page: dict[str, Any] | None = None) -> str | None:
    """The transcript text the build fed the synthesis, read by production's
    ``ciq_sheets.transcript_for_synthesis`` from ``ciq_root/<T>``.

    REFUSES CHANGED INPUTS: each transcript file's sha256 must equal ``expected`` (the panel's
    freeze) and, where the page's own input record lists transcripts, that record too. A re-exported
    call would otherwise reach the replay as if it were the frozen one."""
    from vinci.dossier import ciq_sheets
    from vinci.dossier.ciq import CiqBundle

    folder = ciq_root / ticker
    files = sorted(p for p in folder.iterdir() if p.is_file()) if folder.is_dir() else []
    bundle = CiqBundle.from_files(ticker, files)
    got = {w.path.name: _sha256(w.path) for w in bundle.all_workbooks("transcript")}
    checks: list[tuple[str, dict[str, str]]] = []
    if expected is not None:
        checks.append(("the panel", {e["file"]: e["sha256"] for e in expected}))
    recorded = {c["file"]: c["sha256"] for c in ((page or {}).get("inputs") or {}).get("ciq") or []
                if c.get("kind") == "transcript"}
    if recorded:
        checks.append(("the page's input record", recorded))
    for who, want in checks:
        if got != want:
            raise ReplayError(f"{ticker}: transcripts on disk {sorted(got)} differ from {who} "
                              f"{sorted(want)} (names or sha256)")
    return ciq_sheets.transcript_for_synthesis(bundle)


# -------------------------------------------------------------------------------------- capture

@dataclass(frozen=True)
class Request:
    """One synthesis request as the SDK would receive it."""

    kwargs: dict[str, Any]

    @property
    def system(self) -> str:
        return str(self.kwargs["system"])

    @property
    def user(self) -> str:
        return str(self.kwargs["messages"][0]["content"])

    @property
    def model(self) -> str:
        return str(self.kwargs["model"])

    @property
    def max_tokens(self) -> int:
        return int(self.kwargs["max_tokens"])

    def chars(self) -> int:
        """Characters the prompt carries — SYSTEM, USER and the tool schema as JSON."""
        return len(self.system) + len(self.user) + len(json.dumps(self.kwargs.get("tools")))


def _one(calls: list[dict[str, Any]], draws: int) -> Request:
    if len(calls) != draws:
        raise ReplayError(f"captured {len(calls)} requests for {draws} draws")
    first = jsonable(calls[0])
    if any(jsonable(c) != first for c in calls[1:]):
        raise ReplayError("the draws of one capture sent different requests")
    return Request(first)


def capture(page: dict[str, Any], transcript: str | None, *, model: str = DEFAULT_MODEL,
            max_tokens: int = DEFAULT_MAX_TOKENS, draws: int = 5,
            transform: Callable[[MechanicalLayer], MechanicalLayer] | None = None) -> Request:
    """The request production builds for ``page`` with the code this module is imported from."""
    return _one(capture_calls(page, transcript, model=model, max_tokens=max_tokens, draws=draws,
                              transform=transform), draws)


def capture_at(code_ref: str, page: dict[str, Any], transcript: str | None, *,
               model: str = DEFAULT_MODEL, max_tokens: int = DEFAULT_MAX_TOKENS, draws: int = 5,
               repo: Path = ROOT) -> Request:
    """``capture`` with the code at ``code_ref``: its ``vinci/`` is extracted by ``git archive``
    into a temporary folder and `capture_child.py` runs there in a child process (``-P``: the
    script's own folder is not put on the path), refusing to run against any other ``vinci``. A ref
    older than #865 clears the material marks its synthesis never read."""
    older = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor",
                            MATERIAL_MARKED_BEFORE_SYNTHESIS, code_ref]).returncode != 0
    with tempfile.TemporaryDirectory(prefix="evals-code-") as tmp:
        root = Path(tmp)
        tar = subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", code_ref, "vinci"],
                             capture_output=True, check=True).stdout
        tar_path = root / "code.tar"
        tar_path.write_bytes(tar)
        with tarfile.open(tar_path) as tf:
            tf.extractall(root / "code", filter="data")
        (root / "page.json").write_text(json.dumps(page), encoding="utf-8")
        args = [sys.executable, "-P", str(Path(__file__).with_name("capture_child.py")),
                "--page", str(root / "page.json"), "--out", str(root / "out.json"),
                "--model", model, "--max-tokens", str(max_tokens), "--draws", str(draws),
                "--expect-root", str(root / "code")] + (["--unmark-material"] if older else [])
        if transcript is not None:
            (root / "transcript.txt").write_text(transcript, encoding="utf-8")
            args += ["--transcript", str(root / "transcript.txt")]
        env = {**os.environ, "PYTHONPATH": str(root / "code")}
        done = subprocess.run(args, env=env, capture_output=True, text=True)
        if done.returncode != 0:
            raise ReplayError(f"capture at {code_ref} failed: {done.stderr.strip()[-2000:]}")
        calls = json.loads((root / "out.json").read_text(encoding="utf-8"))["calls"]
    return _one(calls, draws)


# --------------------------------------------------------------------------------- logged builds

@dataclass(frozen=True)
class LoggedDraw:
    n: int
    usage: dict[str, Any] | None
    raw: dict[str, Any] | None
    status: str  # "ok" | "error" | "incomplete"


@dataclass(frozen=True)
class LoggedBuild:
    """The synthesis section of a build's ``llm_call.log`` (`synthesize`'s ``log_parts``)."""

    model: str
    sleeve: str
    system: str
    user: str
    draws: tuple[LoggedDraw, ...]
    agreement: dict[str, Any] | None


_HEAD = re.compile(r"(?:^|\n)model: (\S+)\n\n=== SLEEVE === (\S+)\n\n=== SYSTEM ===\n(.*?)\n\n"
                   r"=== USER ===\n(.*?)\n\n=== DRAW 1/(\d+) ===", re.S)


def parse_log(text: str) -> LoggedBuild:
    """Split a build log into its synthesis SYSTEM, USER and draws. The section's own markers
    (`synthesize` writes them) delimit it; JSON blocks are read with ``raw_decode`` from where they
    start, never by guessing where they end. Raises when the section is absent."""
    m = _HEAD.search(text)
    if m is None:
        raise ReplayError("no multi-draw synthesis section in this log")
    model, sleeve, system, user, total = m.groups()
    dec = json.JSONDecoder()
    draws: list[LoggedDraw] = []
    for n in range(1, int(total) + 1):
        at = text.find(f"=== DRAW {n}/{total} ===", m.start(4))
        if at < 0:
            raise ReplayError(f"draw {n}/{total} missing from the log")
        line_end = text.index("\n", at)
        kind = text[at:line_end].rsplit("===", 1)[-1].strip()
        if kind == "ERROR":
            draws.append(LoggedDraw(n, None, None, "error"))
            continue
        usage: dict[str, Any] | None = None
        if kind == "USAGE":
            usage, _ = dec.raw_decode(text, line_end + 1)
            at = text.index(f"=== DRAW {n}/{total} === RAW OUTPUT", line_end)
            line_end = text.index("\n", at)
        raw, end = dec.raw_decode(text, line_end + 1)
        incomplete = text.startswith(f"\n\n=== DRAW {n}/{total} === INCOMPLETE", end)
        draws.append(LoggedDraw(n, usage, raw, "incomplete" if incomplete else "ok"))
    agreement: dict[str, Any] | None = None
    if (g := text.find("=== DRAW AGREEMENT ===\n", m.start(4))) >= 0:
        agreement, _ = dec.raw_decode(text, g + len("=== DRAW AGREEMENT ===\n"))
    return LoggedBuild(model, sleeve, system, user, tuple(draws), agreement)


@dataclass(frozen=True)
class FieldProof:
    name: str
    rebuilt_chars: int
    logged_chars: int
    rebuilt_sha256: str
    logged_sha256: str
    diff_lines: int
    first_difference: int | None

    @property
    def equal(self) -> bool:
        return self.rebuilt_sha256 == self.logged_sha256


@dataclass(frozen=True)
class Proof:
    fields: tuple[FieldProof, ...]
    model_equal: bool
    max_tokens_equal: bool | None
    notes: tuple[str, ...] = field(default=())

    @property
    def identical(self) -> bool:
        return (all(f.equal for f in self.fields) and self.model_equal
                and self.max_tokens_equal is not False)


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _field(name: str, rebuilt: str, logged: str) -> FieldProof:
    diff = list(difflib.unified_diff(logged.splitlines(), rebuilt.splitlines(), lineterm="", n=0))
    first = next((i for i, (a, b) in enumerate(zip(rebuilt, logged, strict=False)) if a != b),
                 None if len(rebuilt) == len(logged) else min(len(rebuilt), len(logged)))
    return FieldProof(name, len(rebuilt), len(logged), _sha(rebuilt), _sha(logged), len(diff),
                      first)


def prove(rebuilt: Request, logged: LoggedBuild) -> Proof:
    """#920 §2's proof: SYSTEM and USER by length, full sha256 and a 0-line diff; model; and
    max_tokens against each logged draw's usage (the log holds no tool schema — stated)."""
    budgets = {d.usage.get("max_tokens") for d in logged.draws if d.usage}
    mt = None if not budgets else budgets == {rebuilt.max_tokens}
    return Proof(fields=(_field("SYSTEM", rebuilt.system, logged.system),
                         _field("USER", rebuilt.user, logged.user)),
                 model_equal=rebuilt.model == logged.model, max_tokens_equal=mt,
                 notes=("the log holds no tool schema; the tool is the code version's "
                        "tool_for(sleeve)",))


# ------------------------------------------------------------------------------- the paid guard

@dataclass
class Budget:
    """A hard cap in USD over a spend ledger (one JSON line per paid call), kept OUTSIDE the
    repository: the cap holds across processes, and raw draws — which can quote licensed
    transcripts — never land in a tracked folder."""

    cap_usd: float
    ledger: Path

    def __post_init__(self) -> None:
        here = self.ledger.resolve()
        if ROOT in here.parents:
            raise ReplayError(f"the spend ledger {here} is inside the repository; keep it outside")

    def spent(self) -> float:
        if not self.ledger.exists():
            return 0.0
        return sum(float(json.loads(x)["usd"])
                   for x in self.ledger.read_text(encoding="utf-8").splitlines() if x.strip())

    def record(self, row: dict[str, Any]) -> None:
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def worst_case_usd(model: str, prompt_tokens: int, max_tokens: int) -> float:
    """One draw at its most expensive: the whole prompt WRITTEN to cache (1.25x input) and every
    output token spent. Raises for a model with no list price — never a zero."""
    if model not in LLM_PRICE_PER_MTOK:
        raise ReplayError(f"no list price for {model}; the guard will not guess one")
    pin, pout = LLM_PRICE_PER_MTOK[model]
    return (prompt_tokens * pin * 1.25 + max_tokens * pout) / 1_000_000


class GuardedSdk:
    """Wraps the real SDK object (``client._client``) for ONE page and code version."""

    def __init__(self, inner: Any, expected: Request, budget: Budget, *, label: str,
                 draws_out: Path) -> None:
        if ROOT in draws_out.resolve().parents:
            raise ReplayError(f"raw draws {draws_out} would land inside the repository")
        self.inner, self.expected, self.budget, self.label = inner, expected, budget, label
        self.draws_out = draws_out
        self.messages = self
        self.n = 0
        self.prompt_tokens: int | None = None   # known after the first response

    def create(self, **kwargs: Any) -> Any:
        self.n += 1
        if jsonable(kwargs) != self.expected.kwargs:
            raise BudgetStop(f"{self.label} draw {self.n}: the request differs from the one "
                             "captured at $0 — STOP")
        bound = (self.prompt_tokens if self.prompt_tokens is not None
                 else int(self.expected.chars() / CHARS_PER_TOKEN_FLOOR) + 1)
        worst = worst_case_usd(self.expected.model, bound, self.expected.max_tokens)
        spent = self.budget.spent()
        if spent + worst > self.budget.cap_usd:
            raise BudgetStop(f"{self.label} draw {self.n}: ${spent:.4f} spent + worst case "
                             f"${worst:.4f} would cross the ${self.budget.cap_usd:.2f} cap — STOP")
        t0 = time.monotonic()
        msg = self.inner.messages.create(**kwargs)
        u = getattr(msg, "usage", None)
        usage = {k: int(getattr(u, k, 0) or 0) for k in
                 ("input_tokens", "output_tokens", "cache_creation_input_tokens",
                  "cache_read_input_tokens")}
        self.prompt_tokens = (usage["input_tokens"] + usage["cache_creation_input_tokens"]
                              + usage["cache_read_input_tokens"])
        usd = cost_usd(self.expected.model, {**usage, "max_tokens": self.expected.max_tokens})
        if usd is None:
            raise BudgetStop(f"{self.label}: no price for {self.expected.model}")
        served = str(getattr(msg, "model", ""))
        row = {"label": self.label, "draw": self.n, "usage": usage, "usd": round(usd, 6),
               "served_model": served, "stop_reason": getattr(msg, "stop_reason", None),
               "seconds": round(time.monotonic() - t0, 1)}
        self.budget.record(row)
        raw = next((dict(b.input) for b in getattr(msg, "content", [])
                    if getattr(b, "type", None) == "tool_use"), None)
        self.draws_out.parent.mkdir(parents=True, exist_ok=True)
        with self.draws_out.open("a", encoding="utf-8") as f:
            f.write(json.dumps({**row, "raw": raw}) + "\n")
        if served != self.expected.model:
            raise BudgetStop(f"{self.label} draw {self.n}: served by {served!r}, asked for "
                             f"{self.expected.model!r} — STOP")
        return msg


def run_paid(page: dict[str, Any], transcript: str | None, *, budget: Budget, label: str,
             draws_out: Path, model: str = DEFAULT_MODEL, max_tokens: int = DEFAULT_MAX_TOKENS,
             draws: int = 5, transform: Callable[[MechanicalLayer], MechanicalLayer] | None = None,
             sdk: Any | None = None) -> tuple[Any, list[str], str]:
    """``draws`` PAID draws of ``page`` through production's ``synthesize``, every one behind
    ``GuardedSdk``. The request is first captured at $0 from the same inputs; the guard then
    refuses anything else. ``sdk`` replaces the real SDK object (tests); without it the client
    reads ``ANTHROPIC_API_KEY`` from the environment and the call costs money."""
    from vinci.dossier.synthesis import synthesize
    from vinci.evals.capture_child import pre_synthesis_mech
    from vinci.graph.llm import AnthropicLlmClient

    expected = capture(page, transcript, model=model, max_tokens=max_tokens, draws=draws,
                       transform=transform)
    client = AnthropicLlmClient(model=model, max_tokens=max_tokens,
                                api_key="test-sdk-not-a-key" if sdk is not None else None)
    inner = sdk if sdk is not None else client._client
    client._client = GuardedSdk(inner, expected, budget, label=label,  # type: ignore[assignment]
                                draws_out=draws_out)
    mech = pre_synthesis_mech(page)
    if transform is not None:
        mech = transform(mech)
    return synthesize(mech, llm=client, ticker=str(page["ticker"]), name=str(page["name"]),
                      transcript=transcript, sleeve=str(page["sleeve"]), draws=draws)


def load_panel_file(path: Path = PANEL_FILE) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def panel_inputs(ticker: str, *, panel: dict[str, Any] | None = None,
                 ciq_root: Path = DEFAULT_CIQ_ROOT) -> tuple[dict[str, Any], str | None]:
    """A panel page and its transcripts exactly as frozen: the page blob and every transcript's
    sha256 are checked, so the replay can never silently read today's inputs."""
    p = panel or load_panel_file()
    if ticker not in p["pages"]:
        raise ReplayError(f"{ticker} is not in the frozen panel file")
    meta = p["pages"][ticker]
    page = page_at(ticker, p["freeze_ref"], expect_blob=meta["dossier_blob"])
    return page, transcript_for(ticker, ciq_root=ciq_root, expected=meta["transcripts"], page=page)
