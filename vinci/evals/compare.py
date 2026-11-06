"""Main against a branch — the harness's first comparison (design record §6, RUNBOOKS §n).

THREE STEPS, the first two at $0:

1. ``compare_requests`` — every panel page's request captured at BASE's code and at CAND's
   (`replay.capture_at`), with the same frozen inputs and the same named transforms. It reports per
   page whether the two requests differ, where, and each section's size. **When no page's request
   differs, the comparison is REFUSED**: the change does not reach the synthesis request by replay
   (a `mechanical.py` label change without its transform is exactly this), and drawing it would buy
   two samples of one prompt.
2. ``run_compare`` — PAID: the captured requests are drawn page by page, BASE then CAND, five
   draws each, every draw behind the guard and one cap (`replay.run_request`). Requests and raw
   draws are written OUTSIDE the repository (they carry licensed transcript text).
3. ``score_run`` — $0: every draw's prose units scored by the deterministic metrics, and the
   pre-registered rule applied: the declared target improves at ``p_lower <= 0.05``; no other
   metric worsens at ``p_upper <= 0.05``; lean tallies, modal leans and proposals per page;
   instruction echo and prompt size reported; the held-out pages read on their own.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
import subprocess
import time
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vinci.dossier.synthesis import SYNTHESIS_TOOL, _decode_escapes
from vinci.dossier.verdict import derive_proposal, split_lean
from vinci.evals import metrics as mt
from vinci.evals import replay as rp
from vinci.evals import stats as sx
from vinci.evals.capture_child import pre_synthesis_mech
from vinci.evals.units import draw_units

CONDITIONS = ("BASE", "CAND")
ALPHA = 0.05


@dataclass(frozen=True)
class PageDiff:
    ticker: str
    identical: bool
    user_diff_lines: int
    system_equal: bool
    base_sizes: dict[str, int]
    cand_sizes: dict[str, int]


@dataclass
class Captured:
    base_ref: str
    cand_ref: str
    transforms: tuple[str, ...]
    requests: dict[tuple[str, str], rp.Request] = field(default_factory=dict)
    diffs: list[PageDiff] = field(default_factory=list)

    @property
    def reaches(self) -> bool:
        return any(not d.identical for d in self.diffs)


def compare_requests(base_ref: str, cand_ref: str, *, tickers: Sequence[str] | None = None,
                     transforms: Sequence[str] = (), panel: dict[str, Any] | None = None,
                     ciq_root: Path = rp.DEFAULT_CIQ_ROOT) -> Captured:
    """Step 1, $0. Inputs are the frozen panel's (blob and transcript sha256s checked)."""
    p = panel or rp.load_panel_file()
    out = Captured(base_ref, cand_ref, tuple(transforms))
    for t in tickers or p["panel"]:
        page, tx = rp.panel_inputs(t, panel=p, ciq_root=ciq_root)
        base = rp.capture_at(base_ref, page, tx, transforms=transforms)
        cand = rp.capture_at(cand_ref, page, tx, transforms=transforms)
        out.requests[(t, "BASE")], out.requests[(t, "CAND")] = base, cand
        out.diffs.append(page_diff(t, base, cand))
    return out


def page_diff(ticker: str, base: rp.Request, cand: rp.Request) -> PageDiff:
    """Two requests compared WHOLE and as SENT (every kwarg, key order included: SYSTEM, USER,
    tools, tool_choice, cache) — a change to the system prompt alone, or to the order of the tool
    schema's fields, reaches the comparison as surely as one to the facts."""
    diff = list(difflib.unified_diff(base.user.splitlines(), cand.user.splitlines(),
                                     lineterm="", n=0))
    return PageDiff(ticker, base.wire() == cand.wire(), len(diff), base.system == cand.system,
                    mt.prompt_size(base), mt.prompt_size(cand))


def refuse_if_unreached(c: Captured) -> None:
    if not c.reaches:
        raise rp.ReplayError(
            f"{c.cand_ref} sends the request {c.base_ref} sends on every page "
            f"({', '.join(d.ticker for d in c.diffs)}): the change does not reach the synthesis "
            "request by replay. A change to the mechanical layer's words needs its transform "
            "(variants.py; RUNBOOKS §n step 2) — drawing this would compare one prompt with itself")


# ------------------------------------------------------------------------- the registration

#: The files whose definitions decide a score: the harness's scorer and the production modules it
#: reads its definitions from (`TRAILING_ONLY_NOTE`, `material_direction_flags`, `SYNTHESIS_TOOL`,
#: `split_lean`/`derive_proposal`). A score is refused unless they are byte-identical to the
#: registered ones.
SCORER_FILES = ("vinci/evals/metrics.py", "vinci/evals/units.py", "vinci/evals/compare.py",
                "vinci/evals/stats.py", "vinci/evals/panel.py", "vinci/dossier/synthesis.py",
                "vinci/dossier/mechanical.py", "vinci/dossier/verdict.py")


def scorer_fingerprint(root: Path = rp.ROOT) -> str:
    h = hashlib.sha256()
    for f in SCORER_FILES:
        h.update(f.encode() + b"\0" + (root / f).read_bytes() + b"\0")
    return h.hexdigest()


@dataclass(frozen=True)
class Registration:
    """Written BEFORE any paid draw (record §6): what is compared, how often, which metric(s)
    must improve, and with what scorer. Its sha256 is recorded in the budget ledger; ``score``
    reads it, never a target given at score time."""

    base_ref: str
    cand_ref: str
    transforms: tuple[str, ...]
    pages: tuple[str, ...]
    draws: int
    targets: tuple[str, ...]
    held_out: tuple[str, ...]
    scorer: str
    alpha: float = ALPHA
    rule: str = ("design record §6: each target p_lower <= alpha after Holm across the targets; "
                 "no other class metric p_upper <= alpha; every lean, proposal and the panel's "
                 "committed-lean count explained if moved")

    def __post_init__(self) -> None:
        bad = [t for t in self.targets if t not in mt.UNIT_METRICS]
        if bad or not self.targets:
            raise ValueError(f"target(s) {bad or '(none)'} not a deterministic metric "
                             f"({sorted(mt.UNIT_METRICS)})")
        if self.draws < 2 or not self.pages:
            raise ValueError("a registration needs pages and at least two draws per condition")

    def to_json(self) -> str:
        return json.dumps(self.__dict__, sort_keys=True, default=list)

    @property
    def sha(self) -> str:
        return hashlib.sha256(self.to_json().encode()).hexdigest()

    @classmethod
    def from_json(cls, text: str) -> Registration:
        d: dict[str, Any] = {k: tuple(v) if isinstance(v, list) else v
                             for k, v in json.loads(text).items()}
        return cls(**d)


def change_names(base_ref: str, cand_ref: str, tickers: Sequence[str],
                 repo: Path = rp.ROOT) -> set[str]:
    """Every ticker the CHANGE itself names: the subjects and bodies of the commits base..cand and
    the full text of every record they add — the pages a change may have been designed on."""
    def git(*a: str) -> str:
        return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True,
                              check=True).stdout
    text = git("log", "--format=%B", f"{base_ref}..{cand_ref}")
    for rec in git("diff", "--name-only", "--diff-filter=A", f"{base_ref}...{cand_ref}",
                   "--", "docs/records").split():
        text += git("show", f"{cand_ref}:{rec}")
    return {t for t in tickers
            if re.search(rf"(?<![A-Za-z0-9]){re.escape(t)}(?![A-Za-z0-9])", text)}


def register(base_ref: str, cand_ref: str, *, targets: Sequence[str], draws: int = 5,
             transforms: Sequence[str] = (), panel: dict[str, Any] | None = None,
             pages: Sequence[str] | None = None) -> Registration:
    """The registration for a comparison of the frozen panel — or, with ``pages``, of a TARGET
    page outside it (record §6.1: a change whose target never fires on the panel is measured
    where it does, as #921 on NFLX). Every page must be one the frozen file carries inputs for.
    HELD OUT is per change: the pages the change's own commits and records do not name (the
    corpus holds no page that no fix ever named — record R8)."""
    p = panel or rp.load_panel_file()
    chosen = tuple(pages) if pages else tuple(p["panel"])
    unknown = [t for t in chosen if t not in p["pages"]]
    if unknown:
        raise rp.ReplayError(f"{unknown}: no frozen inputs in the panel file for these pages")
    pages = chosen
    named = change_names(base_ref, cand_ref, sorted(p["pages"]))
    return Registration(base_ref=base_ref, cand_ref=cand_ref, transforms=tuple(transforms),
                        pages=pages, draws=draws, targets=tuple(targets),
                        held_out=tuple(t for t in pages if t not in named),
                        scorer=scorer_fingerprint())


def write_registration(reg: Registration, path: Path) -> None:
    rp.refuse_inside_repo(path, "the registration")
    if path.exists():
        raise rp.ReplayError(f"{path} exists: a registration is written once, before any draw")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(reg.to_json(), encoding="utf-8")


def run_compare(c: Captured, *, budget: rp.Budget, out_dir: Path, registration: Registration,
                sdk: Any | None = None) -> None:
    """Step 2, PAID. Page by page, BASE then CAND, so the hours between conditions are bounded by
    one page's ten draws (#920 could not bound them). Draws exactly what ``registration`` says,
    and records its sha256 in the budget ledger before the first draw."""
    refuse_if_unreached(c)
    reg = registration
    pages = tuple(dict.fromkeys(t for t, _ in c.requests))
    if (c.base_ref, c.cand_ref, c.transforms, pages) != (reg.base_ref, reg.cand_ref,
                                                         reg.transforms, reg.pages):
        raise rp.ReplayError("the captured comparison is not the registered one (refs, "
                             "transforms or pages differ) — register it first")
    draws = reg.draws
    rp.refuse_inside_repo(out_dir, "the run folder (requests and draws carry licensed text)")
    if (out_dir / "draws.jsonl").exists():
        raise rp.ReplayError(f"{out_dir} already holds draws: draws append, so a second run here "
                             "would be scored with the first — use a fresh folder")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "registration.json").write_text(reg.to_json(), encoding="utf-8")
    budget.record({"registration": reg.sha, "out_dir": str(out_dir), "usd": 0.0})
    with (out_dir / "requests.jsonl").open("w", encoding="utf-8") as f:
        for (t, cond), req in c.requests.items():
            f.write(json.dumps({"ticker": t, "condition": cond,
                                "ref": c.base_ref if cond == "BASE" else c.cand_ref,
                                "transforms": list(c.transforms), "kwargs": req.kwargs}) + "\n")
    for t in dict.fromkeys(t for t, _ in c.requests):
        for cond in CONDITIONS:
            rp.run_request(c.requests[(t, cond)], draws=draws, budget=budget,
                           label=f"{t}:{cond}", draws_out=out_dir / "draws.jsonl", sdk=sdk)


# ------------------------------------------------------------------------------------- scoring

@dataclass(frozen=True)
class MetricResult:
    metric: str
    base_total: int
    cand_total: int
    p_lower: float
    p_upper: float
    held_out_base: int
    held_out_cand: int


@dataclass(frozen=True)
class Score:
    targets: tuple[str, ...]
    metrics: dict[str, MetricResult]
    leans: dict[str, dict[str, dict[str, int]]]
    proposals: dict[str, dict[str, str | None]]
    failed_draws: dict[str, int]
    echo_new: dict[str, list[str]]
    ships: bool
    reasons: tuple[str, ...]


def holm(p_values: dict[str, float], alpha: float = ALPHA) -> dict[str, bool]:
    """Holm's step-down across the declared targets: the i-th smallest p (0-based) is rejected
    only if every smaller one was and it is <= alpha / (k - i)."""
    k = len(p_values)
    out = dict.fromkeys(p_values, False)
    for i, (m, p) in enumerate(sorted(p_values.items(), key=lambda kv: kv[1])):
        if p > alpha / (k - i):
            break
        out[m] = True
    return out


def usable(row: dict[str, Any]) -> bool:
    """A draw `synthesize` would have kept: the call stopped on its tool (a ``max_tokens`` stop
    is a truncated, partial tool input — production's client raises on it) and the output carries
    every required field but ``evidence_balance`` (production's INCOMPLETE rule)."""
    raw = row.get("raw")
    if not raw or row.get("stop_reason") != "tool_use":
        return False
    required = SYNTHESIS_TOOL["input_schema"]["required"]
    return all(k in raw for k in required if k != "evidence_balance")


def _lean(raw: dict[str, Any]) -> str:
    parts = split_lean(str(_decode_escapes(raw).get("evidence_balance") or ""))
    return parts[0].strip().lower() if parts else ""


_COMMITTED = ("strongly-bullish", "strongly-bearish")


def _modal_set(tally: Counter[str]) -> frozenset[str]:
    """Every lean at the top count — a tie is a set, so draw ORDER never reads as a lean move."""
    if not tally:
        return frozenset()
    top = max(tally.values())
    return frozenset(k for k, v in tally.items() if v == top)


def _proposal(tally: Counter[str], sleeve: str) -> str | None:
    """Production's proposal for a build with this tally: the modal lean, withheld unless the
    draws are unanimous (`verdict.derive_proposal`)."""
    if not tally:
        return None
    modal = max(tally.items(), key=lambda kv: kv[1])[0]
    p = derive_proposal(f"{modal} — x", sleeve=sleeve, draws_unanimous=len(tally) == 1)
    return p.action.value if p.action is not None else None


def _check_run(out_dir: Path, reg: Registration, rows: list[dict[str, Any]]) -> None:
    """The run IS the registered one, scored by the registered scorer, on the registered pages
    and draw counts — anything else is refused, never scored."""
    rec = out_dir / "registration.json"
    if not rec.exists() or Registration.from_json(rec.read_text(encoding="utf-8")).sha != reg.sha:
        raise rp.ReplayError(f"{reg.sha[:12]} is not the registration this run was drawn under "
                             f"({rec}); re-scoring under another needs a new registration and run")
    if (fp := scorer_fingerprint()) != reg.scorer:
        raise rp.ReplayError(f"the scorer here ({fp[:12]}) is not the registered scorer "
                             f"({reg.scorer[:12]}): score from the registered code")
    seen = Counter(r["label"] for r in rows)
    pages = {lab.split(":")[0] for lab in seen}
    if pages != set(reg.pages):
        raise rp.ReplayError(f"the draws cover {sorted(pages)}, not the registered pages "
                             f"{sorted(reg.pages)}")
    for t in reg.pages:
        for cond in CONDITIONS:
            if seen[f"{t}:{cond}"] != reg.draws:
                raise rp.ReplayError(f"{t}:{cond} has {seen[f'{t}:{cond}']} draws; the run "
                                     f"registered {reg.draws} draws per page per condition")


def score_run(out_dir: Path, registration: Registration, *, panel: dict[str, Any] | None = None,
              pages: dict[str, dict[str, Any]] | None = None,
              transcripts: dict[str, str | None] | None = None) -> Score:
    """Step 3, $0 — the registered rule, on the registered run, appended to its score log.
    ``pages``/``transcripts`` override the frozen panel inputs (tests); otherwise they are read
    and checked as the capture read them."""
    reg = registration
    p = panel or rp.load_panel_file()
    rows = [json.loads(x) for x in (out_dir / "draws.jsonl").read_text(encoding="utf-8")
            .splitlines() if x.strip()]
    _check_run(out_dir, reg, rows)
    reqs: dict[tuple[str, str], rp.Request] = {}
    if (out_dir / "requests.jsonl").exists():
        for x in (out_dir / "requests.jsonl").read_text(encoding="utf-8").splitlines():
            if x.strip():
                r = json.loads(x)
                reqs[(r["ticker"], r["condition"])] = rp.Request(r["kwargs"])
    counts: dict[str, dict[str, dict[str, list[int]]]] = {}
    leans: dict[str, dict[str, Counter[str]]] = {}
    failed: Counter[str] = Counter()
    echo: dict[str, dict[str, set[str]]] = {}
    ctxs: dict[str, mt.PageContext] = {}
    indexes: dict[tuple[str, str], mt.EchoIndex] = {}
    for row in rows:
        t, cond = row["label"].split(":")
        if t not in ctxs:
            if pages is not None:
                page, tx = pages[t], (transcripts or {}).get(t)
            else:
                page, tx = rp.panel_inputs(t, panel=p)
            ctxs[t] = mt.PageContext(page=page, mech=pre_synthesis_mech(page), transcript=tx)
        ctx = ctxs[t]
        if not usable(row):
            failed[row["label"]] += 1
            continue
        req = reqs.get((t, cond))
        if req is not None and (t, cond) not in indexes:
            indexes[(t, cond)] = mt.EchoIndex.of(req, ctx)
        sc = mt.score_units(draw_units(row["raw"]), ctx, echo=indexes.get((t, cond)))
        for m, hits in sc.items():
            counts.setdefault(m, {}).setdefault(t, {c: [] for c in CONDITIONS})[cond].append(
                len({h.unit for h in hits}))
        leans.setdefault(t, {c: Counter() for c in CONDITIONS})[cond][_lean(row["raw"])] += 1
        for h in sc.get("M-ECHO", []):
            echo.setdefault(cond, {}).setdefault(h.phrase, set()).add(t)
    reasons: list[str] = []
    for t in reg.pages:
        for cond in CONDITIONS:
            if not sum(leans.get(t, {}).get(cond, Counter()).values()):
                reasons.append(f"{t}: {cond} has no usable draw — the page cannot be compared, "
                               "and a panel is never shrunk silently")
    held = set(reg.held_out)
    results: dict[str, MetricResult] = {}
    for m, by_page in counts.items():
        pd = [sx.PageDraws(t, tuple(v["BASE"]), tuple(v["CAND"]))
              for t, v in sorted(by_page.items()) if v["BASE"] and v["CAND"]]
        if not pd:
            continue
        r = sx.stratified_exact(pd)
        ho = [x for x in pd if x.page in held]
        results[m] = MetricResult(m, r.base_total, r.cand_total, float(r.p_lower),
                                  float(r.p_upper), sum(sum(x.base) for x in ho),
                                  sum(sum(x.cand) for x in ho))
    passed = holm({t: results[t].p_lower for t in reg.targets if t in results}, reg.alpha)
    for t in reg.targets:
        if not passed.get(t):
            got = f"p_lower {results[t].p_lower:.3g}" if t in results else "not scored"
            reasons.append(f"target {t} does not improve beyond noise ({got}; Holm across "
                           f"{len(reg.targets)} target(s))")
    for m, r in results.items():
        if m not in reg.targets and m in mt.GOLD_CLASS and r.p_upper <= reg.alpha:
            reasons.append(f"{m} worsens beyond noise: {r.base_total} → {r.cand_total} "
                           f"(p_upper {r.p_upper:.3g})")
    proposals: dict[str, dict[str, str | None]] = {}
    for t, by in leans.items():
        sleeve = str(ctxs[t].page.get("sleeve"))
        proposals[t] = {c: _proposal(by[c], sleeve) for c in CONDITIONS}
        modal = {c: _modal_set(by[c]) for c in CONDITIONS}
        if modal["BASE"] != modal["CAND"] or proposals[t]["BASE"] != proposals[t]["CAND"]:
            reasons.append(f"{t}: the lean moved ({dict(by['BASE'])} → {dict(by['CAND'])}; "
                           f"proposal {proposals[t]['BASE']} → {proposals[t]['CAND']}) — explain "
                           "it in writing before review")
    committed = [sx.PageDraws(t, *(tuple(int(k in _COMMITTED) for k, v in by[c].items()
                                         for _ in range(v)) for c in CONDITIONS))
                 for t, by in sorted(leans.items()) if by["BASE"] and by["CAND"]]
    if committed:
        cr = sx.stratified_exact(committed)
        two_sided = min(1.0, 2 * float(min(cr.p_lower, cr.p_upper)))
        if two_sided <= reg.alpha:
            reasons.append(f"the panel's committed-lean draws moved {cr.base_total} → "
                           f"{cr.cand_total} (two-sided p {two_sided:.3g}) — explain it in "
                           "writing before review (record §6.3)")
    new_echo = {ph: sorted(ts) for ph, ts in echo.get("CAND", {}).items()
                if ph not in echo.get("BASE", {})}
    score = Score(targets=reg.targets, metrics=results,
                  leans={t: {c: dict(v) for c, v in by.items()} for t, by in leans.items()},
                  proposals=proposals, failed_draws=dict(failed),
                  echo_new={"CAND only": [f"{ph} ({', '.join(ts)})"
                                          for ph, ts in new_echo.items()]},
                  ships=not reasons, reasons=tuple(reasons))
    with (out_dir / "score_log.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            "registration": reg.sha, "scorer": reg.scorer,
                            "ships": score.ships, "reasons": list(score.reasons),
                            "metrics": {m: r.__dict__ for m, r in results.items()}}) + "\n")
    return score


def score_text(s: Score) -> str:
    lines = [f"TARGETS {', '.join(s.targets)}; ships: {s.ships}"]
    for m, r in sorted(s.metrics.items()):
        lines.append(f"  {m:8} BASE {r.base_total:3} → CAND {r.cand_total:3} | p_lower "
                     f"{r.p_lower:.3g} p_upper {r.p_upper:.3g} | held-out {r.held_out_base} → "
                     f"{r.held_out_cand}")
    for t, by in sorted(s.leans.items()):
        lines.append(f"  {t:5} leans BASE {by['BASE']} CAND {by['CAND']} | proposal "
                     f"{s.proposals[t]['BASE']} → {s.proposals[t]['CAND']}")
    if s.failed_draws:
        lines.append(f"  draws with no usable output: {s.failed_draws}")
    lines += [f"  echo, CAND only: {x}" for x in s.echo_new["CAND only"]]
    lines += [f"  BLOCKS: {r}" for r in s.reasons]
    return "\n".join(lines)
