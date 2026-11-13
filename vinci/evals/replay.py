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
cannot swallow it, and neither can ``run_request``'s per-draw ``LlmError`` handling: the run stops.
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

import anthropic

from vinci.config import LLM_PRICE_PER_MTOK
from vinci.dossier.schemas import MechanicalLayer
from vinci.evals.capture_child import DEFAULT_MAX_TOKENS, capture_calls, jsonable
from vinci.graph.llm import AnthropicLlmClient, LlmError, cost_usd, sdk_version

ROOT = Path(__file__).resolve().parents[2]


def _checkouts() -> tuple[Path, ...]:
    """This checkout and the primary one it is a worktree of (the git common dir's parent), so a
    path in either — or in any worktree under the primary — counts as inside the repository."""
    out = [ROOT]
    done = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--path-format=absolute",
                           "--git-common-dir"], capture_output=True, text=True)
    if done.returncode == 0 and done.stdout.strip():
        out.append(Path(done.stdout.strip()).resolve().parent)
    return tuple(out)


def _inside_repo(path: Path) -> bool:
    here = path.resolve()
    return any(c == here or c in here.parents for c in _checkouts())


def refuse_inside_repo(path: Path, what: str) -> None:
    """Requests, logs, ledgers and raw draws carry licensed transcript text: never in the repo."""
    if _inside_repo(path):
        raise ReplayError(f"{what} {path} is inside the repository; keep it outside")


#: Credentials a capture child must never hold: it builds requests, it sends none.
_SECRET_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE",
               "ANTHROPIC_IDENTITY_TOKEN", "ANTHROPIC_IDENTITY_TOKEN_FILE")


def child_env(code_root: str) -> dict[str, str]:
    """The $0 capture child's environment: this one, less every Anthropic credential, with the
    extracted code first on the path."""
    env = {k: v for k, v in os.environ.items() if k not in _SECRET_ENV}
    env["PYTHONPATH"] = code_root
    return env
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

def wire(kwargs: dict[str, Any]) -> str:
    """``kwargs`` serialised in insertion order — NOT the SDK's exact bytes. The SDK builds its
    own body (its own separators, its own top-level key order), and passes each kwarg's VALUE
    through as given. So this is exact on what the request carries inside its kwargs — the tool
    schema's field order included — and FAILS SAFE on the top level: two requests whose kwargs
    differ only in top-level order compare unequal here though the SDK may send them alike."""
    return json.dumps(kwargs, default=str, ensure_ascii=False)


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

    def wire(self) -> str:
        """The request's kwargs serialised in order (`wire`: exact inside each kwarg, fail-safe
        on the top level; not the SDK's own bytes). Two requests are the same only if this is:
        dict equality ignores order, and that is how PR 2's alphabetised tool schema passed an
        order-blind guard."""
        return wire(self.kwargs)

    def chars(self) -> int:
        """Characters the prompt carries — SYSTEM, USER and the tool schema as JSON."""
        return len(self.system) + len(self.user) + len(json.dumps(self.kwargs.get("tools")))


def _one(calls: list[dict[str, Any]], draws: int) -> Request:
    if len(calls) != draws:
        raise ReplayError(f"captured {len(calls)} requests for {draws} draws")
    first = jsonable(calls[0])
    if any(wire(jsonable(c)) != wire(first) for c in calls[1:]):
        raise ReplayError("the draws of one capture sent different requests")
    return Request(first)


def capture(page: dict[str, Any], transcript: str | None, *, model: str | None = None,
            max_tokens: int = DEFAULT_MAX_TOKENS, draws: int = 5,
            transform: Callable[[MechanicalLayer], MechanicalLayer] | None = None,
            transforms: Sequence[str] = (), comps: Path | None = None) -> Request:
    """The request production builds for ``page`` with the code this module is imported from;
    ``transforms`` are named variants (`variants.py`), applied in order; ``comps`` is the page's
    own comps export, for the transforms that read it."""
    return _one(capture_calls(page, transcript, model=model, max_tokens=max_tokens, draws=draws,
                              transform=transform, transforms=transforms, comps=comps), draws)


def capture_at(code_ref: str, page: dict[str, Any], transcript: str | None, *,
               model: str | None = None, max_tokens: int = DEFAULT_MAX_TOKENS, draws: int = 5,
               transforms: Sequence[str] = (), comps: Path | None = None,
               ciq: Path | None = None, repo: Path = ROOT) -> Request:
    """``capture`` with the code at ``code_ref``: its ``vinci/`` is extracted by ``git archive``
    into a temporary folder and `capture_child.py` runs there in a child process (``-P``: the
    script's own folder is not put on the path), refusing to run against any other ``vinci``. A ref
    older than #865 clears the material marks its synthesis never read. ``ciq`` is the page's own
    CIQ folder, read only, for a transform that re-reads its exports (`variants.Context.ciq`)."""
    out = _child_at(code_ref, page, transcript, model=model, max_tokens=max_tokens, draws=draws,
                    transforms=transforms, comps=comps, ciq=ciq, repo=repo)
    return _one(out["calls"], draws)


def layer_at(code_ref: str, page: dict[str, Any], *, transforms: Sequence[str] = (),
             comps: Path | None = None, ciq: Path | None = None,
             repo: Path = ROOT) -> dict[str, Any]:
    """THE LAYER A REQUEST AT ``code_ref`` CARRIED, as JSON: the committed layer as ``synthesize``
    received it, with ``transforms`` run by the code at ``code_ref`` exactly as `capture_at` runs
    them (the same child, the same inputs), and no request built. What an arm's draws are scored
    against (STATE row 53 item 6): each condition's own layer, never BASE's for both."""
    out: dict[str, Any] = _child_at(code_ref, page, None, model=None,
                                    max_tokens=DEFAULT_MAX_TOKENS, draws=1, transforms=transforms,
                                    comps=comps, ciq=ciq, repo=repo, layer_only=True)["layer"]
    return out


def _child_at(code_ref: str, page: dict[str, Any], transcript: str | None, *,
              model: str | None, max_tokens: int, draws: int, transforms: Sequence[str],
              comps: Path | None, ciq: Path | None, repo: Path,
              layer_only: bool = False) -> dict[str, Any]:
    """`capture_child.py` against the code at ``code_ref``, and its output."""
    rc = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor",
                         MATERIAL_MARKED_BEFORE_SYNTHESIS, code_ref],
                        capture_output=True).returncode
    if rc not in (0, 1):   # an unknown ref, or #865 absent from a shallow history: never a guess
        raise ReplayError(f"cannot tell whether {code_ref} is before #865 "
                          f"({MATERIAL_MARKED_BEFORE_SYNTHESIS}): git merge-base exited {rc}")
    older = rc == 1
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
                "--max-tokens", str(max_tokens), "--draws", str(draws),
                "--expect-root", str(root / "code")] + (["--unmark-material"] if older else [])
        if model is not None:   # unset: the model the code at `code_ref` configures (RG-D15)
            args += ["--model", model]
        if layer_only:
            args += ["--layer-only"]
        for t in transforms:
            args += ["--transform", t]
        if comps is not None:
            args += ["--comps", str(comps.resolve())]
        if ciq is not None:   # the page's own CIQ folder, for a transform that re-reads it
            args += ["--ciq", str(ciq.resolve())]
        if transcript is not None:
            (root / "transcript.txt").write_text(transcript, encoding="utf-8")
            args += ["--transcript", str(root / "transcript.txt")]
        env = child_env(str(root / "code"))   # no key: it captures, it never sends
        done = subprocess.run(args, env=env, capture_output=True, text=True)
        if done.returncode != 0:
            raise ReplayError(f"capture at {code_ref} failed: {done.stderr.strip()[-2000:]}")
        out: dict[str, Any] = json.loads((root / "out.json").read_text(encoding="utf-8"))
    return out


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
    """A hard cap in USD over ONE spend ledger per operator-approved budget, kept OUTSIDE the
    repository. The ledger's first line records the approval — its cap, its words, when it was
    opened (`Budget.open`) — and every run and resume under that approval reads and appends the
    same file (`Budget.load`), so the cap is the budget's, never one run's: three $3 runs cannot
    spend $4.90 under a $3 approval. A cap above the recorded approval is refused."""

    cap_usd: float
    ledger: Path

    def __post_init__(self) -> None:
        refuse_inside_repo(self.ledger, "the spend ledger")
        approved = self.approved_cap(self.ledger)
        if self.cap_usd > approved:
            raise ReplayError(f"a cap of ${self.cap_usd:.2f} is above the approved "
                              f"${approved:.2f} recorded in {self.ledger}")

    @staticmethod
    def approved_cap(ledger: Path) -> float:
        first = (ledger.read_text(encoding="utf-8").splitlines()[:1]
                 if ledger.exists() else [])
        row = json.loads(first[0]) if first else {}
        if "approval" not in row:
            raise ReplayError(f"no approved budget at {ledger}: open one with the operator's "
                              "approval and cap (`python -m vinci.evals budget-open`)")
        return float(row["approval"]["cap_usd"])

    @classmethod
    def open(cls, ledger: Path, *, cap_usd: float, approval: str) -> Budget:
        refuse_inside_repo(ledger, "the spend ledger")
        if ledger.exists():
            raise ReplayError(f"{ledger} already exists: one ledger per approval — resume with "
                              "`--budget-ledger`, or open a new approval in a new file")
        if not approval.strip() or cap_usd <= 0:
            raise ReplayError("an approval needs the operator's words and a positive cap")
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_text(json.dumps({"approval": {
            "cap_usd": cap_usd, "approved": approval.strip(),
            "opened_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}}) + "\n", encoding="utf-8")
        return cls(cap_usd=cap_usd, ledger=ledger)

    @classmethod
    def load(cls, ledger: Path, cap_usd: float | None = None) -> Budget:
        """The approved budget at ``ledger``; ``cap_usd`` may only LOWER its cap."""
        approved = cls.approved_cap(ledger)
        return cls(cap_usd=approved if cap_usd is None else cap_usd, ledger=ledger)

    def rows(self) -> list[dict[str, Any]]:
        return [json.loads(x) for x in self.ledger.read_text(encoding="utf-8").splitlines()
                if x.strip()]

    def spent(self) -> float:
        return sum(float(r.get("usd", 0.0)) for r in self.rows())

    def record(self, row: dict[str, Any]) -> None:
        with self.ledger.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def one_sdk(rows: Sequence[dict[str, Any]], what: str) -> str | None:
    """The one `anthropic` SDK every draw row of a scored run went through, or None when no row
    states one (rows written before `GuardedSdk` stamped `sdk_version`, 2026-11-13).

    REFUSES A RUN DRAWN ACROSS A RE-SYNC (review of #1049, round 1). The API version moves with
    the SDK (0.112.0 sends `2023-06-01`, 2.6.0 `2026-10-21`), so a registration whose builds or
    arms straddle a venv re-sync carries a second difference that its test reads as the one it
    measures: dispersion between builds, or a move between BASE and CAND. Rows on more than one
    SDK are refused, naming them; so are rows of which some state an SDK and some do not, because
    which SDK the older ones used is unknown. Re-sync between registrations, never during one."""
    stated = [r for r in rows if "sdk_version" in r]
    if stated and len(stated) != len(rows):
        raise ReplayError(f"{what}: {len(rows) - len(stated)} of {len(rows)} draw rows state no "
                          "SDK and the rest do — the run was drawn across the pin, and the "
                          "older rows' SDK is unknown; it is not scored")
    versions = sorted({str(r["sdk_version"]) for r in stated})
    if len(versions) > 1:
        raise ReplayError(f"{what}: its draws went through {len(versions)} SDKs "
                          f"({', '.join(versions)}) — the API version moved with them, so the "
                          "score would read it as the effect it measures; it is not scored. "
                          "Re-sync a venv between registrations, never during one")
    return versions[0] if versions else None


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
                 draws_out: Path, client: AnthropicLlmClient) -> None:
        refuse_inside_repo(draws_out, "raw draws")
        self.inner, self.expected, self.budget, self.label = inner, expected, budget, label
        self.client = client   # its `_record_usage` reads a response's tokens — one reader
        self.draws_out = draws_out
        self.messages = self
        self.n = 0
        self.prompt_tokens: int | None = None   # known after the first response

    def _write(self, row: dict[str, Any]) -> None:
        self.draws_out.parent.mkdir(parents=True, exist_ok=True)
        with self.draws_out.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    def create(self, **kwargs: Any) -> Any:
        self.n += 1
        if wire(jsonable(kwargs)) != self.expected.wire():   # in order (`wire`)
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
        try:
            msg = self.inner.messages.create(**kwargs)
        except anthropic.APIError as exc:   # no response body to price: a failed draw, recorded
            self._write({"label": self.label, "draw": self.n, "usd": 0.0, "raw": None,
                         "stop_reason": None, "error": f"{type(exc).__name__}: {exc}"[:400],
                         "sdk_version": sdk_version()})
            raise
        self.client._record_usage(msg)        # production's reader; `extract` repeats it
        recorded = self.client.last_usage
        if recorded is None:
            raise BudgetStop(f"{self.label} draw {self.n}: the response carried no usage — the "
                             "call cannot be priced, so the run stops")
        usage = {k: v for k, v in recorded.items() if k != "max_tokens"}
        self.prompt_tokens = (usage["input_tokens"] + usage["cache_creation_input_tokens"]
                              + usage["cache_read_input_tokens"])
        usd = cost_usd(self.expected.model, {**usage, "max_tokens": self.expected.max_tokens})
        if usd is None:
            raise BudgetStop(f"{self.label}: no price for {self.expected.model}")
        served = str(getattr(msg, "model", ""))
        row = {"label": self.label, "draw": self.n, "usage": usage, "usd": round(usd, 6),
               "served_model": served, "stop_reason": getattr(msg, "stop_reason", None),
               "seconds": round(time.monotonic() - t0, 1),
               # the SDK the draw went through (operator, 2026-11-13: "Check, then pin newest")
               "sdk_version": sdk_version()}
        self.budget.record(row)
        raw = next((dict(b.input) for b in getattr(msg, "content", [])
                    if getattr(b, "type", None) == "tool_use"), None)
        self._write({**row, "raw": raw})
        if served != self.expected.model:
            raise BudgetStop(f"{self.label} draw {self.n}: served by {served!r}, asked for "
                             f"{self.expected.model!r} — STOP")
        return msg


def _a_real_client(sdk: Any) -> bool:
    """Whether an injected ``sdk`` is the real Anthropic SDK client — a paid draw like none."""
    try:
        import anthropic
    except ImportError:   # pragma: no cover - the SDK is a dependency
        return False
    return isinstance(sdk, anthropic.Anthropic)


def paid_draw(sdk: Any | None) -> bool:
    """Whether a draw through ``sdk`` costs money: no SDK injected (the client reads
    ``ANTHROPIC_API_KEY``) or the real Anthropic client injected. Every guard on a paid draw asks
    this one question."""
    return sdk is None or _a_real_client(sdk)


def run_request(req: Request, *, draws: int, budget: Budget, label: str, draws_out: Path,
                sdk: Any | None = None,
                registration: str | None = None) -> list[dict[str, Any] | None]:
    """``draws`` PAID draws of ONE request captured at $0, sent sequentially (the build's own
    loop: the first writes the prompt cache, the rest read it) through production's
    ``AnthropicLlmClient.extract``, each behind ``GuardedSdk``. Returns each draw's raw tool
    output, or None for a draw the model answered unusably (``LlmError``, as `synthesize` counts
    it). The request may have been built at any code ref (`capture_at`), so main and a branch are
    drawn by one process under one cap. ``sdk`` replaces the real SDK object (tests); without it
    the client reads ``ANTHROPIC_API_KEY`` and the call costs money."""
    if registration is None and paid_draw(sdk):
        # RG-D10, IN THE LIBRARY (B's check of order 8, gap 2): G-D10's own reproduction called
        # this function with no registration; the CLI refused, the library did not
        raise ReplayError(f"{label}: a paid draw needs the registration it is drawn under "
                          "(RG-D10) — every paid draw goes through run-compare, run or the judge")
    tools = req.kwargs.get("tools") or []
    if len(tools) != 1:
        raise ReplayError(f"{label}: a synthesis request carries one tool, this one {len(tools)}")
    client = AnthropicLlmClient(model=req.model, max_tokens=req.max_tokens,
                                api_key="test-sdk-not-a-key" if sdk is not None else None)
    inner = sdk if sdk is not None else client._client
    # ONE GUARDED CALL IS ONE HTTP ATTEMPT. The SDK retries on its own (max_retries=2): each
    # retry is a request the guard never saw. Retries are off; a failed attempt is a failed draw,
    # recorded, and the next draw is checked like any other.
    if hasattr(inner, "with_options"):
        inner = inner.with_options(max_retries=0)
    client._client = GuardedSdk(inner, req, budget, label=label,  # type: ignore[assignment]
                                draws_out=draws_out, client=client)
    out: list[dict[str, Any] | None] = []
    for _ in range(draws):
        try:
            out.append(client.extract(system=req.system, user=req.user, tool=tools[0],
                                      cache=draws > 1))
        except (LlmError, anthropic.APIError):
            out.append(None)
    return out


def comps_export(ticker: str, *, ciq_root: Path = DEFAULT_CIQ_ROOT) -> Path | None:
    """The one CIQ comps export in ``ciq_root/<ticker>`` (the reader's own filename rule), or None
    when there is none. Two are refused, never chosen between. Whether it is the PAGE's own is
    proved where it is read (`variants.own_comps`), by the code under test."""
    from vinci.dossier.ciq import workbook_kind
    folder = ciq_root / ticker
    found = sorted(f for f in folder.glob("*") if f.is_file() and not f.name.startswith((".", "~$"))
                   and workbook_kind(f.name) == "comps") \
        if folder.is_dir() else []
    if len(found) > 1:
        raise ReplayError(f"{ticker}: {len(found)} comps exports in {folder}: "
                          f"{[f.name for f in found]}")
    return found[0] if found else None


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
