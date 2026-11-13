"""$0: the vote-rule design's independence measurement, scored by the rule it pre-registered.

`docs/records/2026-11-10-the-proposal-vote-rule-design.md` §7 fixes the test before any draw:
four production-shaped ten-draw builds of each panel page's one request (`builds.RunRegistration`,
drawn by `builds.run_build`), and ONE falsifier:

- **Pearson's dispersion test on per-build counts.** Per page, p̂ is the share of its draws that
  carry the page's pooled modal label, x_k that label's count in build k:
  X² = Σ_k (x_k − n·p̂)² / (n·p̂·(1 − p̂)), summed over the pages with 0 < p̂ < 1, referred to χ²
  with (builds − 1) degrees of freedom per such page. **Independence is falsified when X² exceeds
  the χ² upper 5% point** (p ≤ 0.05); VIF = X²/df is the measured variance inflation.

Reported beside it, decided on by nothing: the first draws of the builds that opened uncached
(the ledger's `first_draw_cache_read` is 0) against the rest (an exact test, stratified by page),
a runs test within builds (`runs_test`, pooled over builds), failed / unparsed / unrecognized
draws (more than 4 of 240 STOP the design, record §7), and what each option does on each
build — A (R1 at five draws, on each build's first five), B (R1 at ten), C(i) (five, then five
more on a committed 3/2 or 4/1) and
C(iii)'s three outcomes — with how often two builds of one page disagree under each. A run where
every page is unanimous over its draws has no degree of freedom: NOT TESTABLE, and it STOPS.

The labels are read as production reads them: a draw `extract` raises on (truncated at
max_tokens) or `synthesize` drops (a structural field missing) is no draw; a literal ``\\uXXXX`` is
decoded (`synthesis._decode_escapes`); then `verdict.split_lean`, then the mapping's own key
(whitespace collapsed to hyphens, `verdict.py:140`), so two spellings of one lean are one label. A
draw that failed, did not parse or carries no recognized lean is DISSENT (R3): it counts toward
no lean.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Any

from vinci.dossier.synthesis import SYNTHESIS_TOOL, _decode_escapes
from vinci.dossier.verdict import split_lean
from vinci.evals import builds as bd
from vinci.evals import replay as rp

COMMITTED = ("strongly-bullish", "strongly-bearish")
KNOWN = (*COMMITTED, "mixed")
#: What a draw that is no lean reads as: failed (no tool output), unparsed, or unrecognized.
DISSENT = "dissent"
ALPHA = 0.05
#: Record §7's STOP: more failed, unparsed or unrecognized draws than this, of 240.
MAX_DISSENT_DRAWS = 4
#: The fields without which `synthesize` drops a draw as INCOMPLETE (as it computes them).
_STRUCTURAL = tuple(k for k in SYNTHESIS_TOOL["input_schema"]["required"]
                    if k != "evidence_balance")


# ------------------------------------------------------------------- the two distributions

def binom_tail(n: int, k: int, p: float) -> float:
    """P(X ≥ k) for X ~ Binomial(n, p)."""
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(max(k, 0), n + 1))


def r1_k(n: int, alpha: float = ALPHA) -> int:
    """R1's bar at n attempted draws: the least x with P(X ≥ x | n, ½) ≤ alpha (5 of 5, 9 of 10)."""
    return next(x for x in range(n + 2) if x > n or binom_tail(n, x, 0.5) <= alpha)


def chi2_sf(x: float, df: int) -> float:
    """P(χ²_df ≥ x): the regularized upper incomplete gamma Q(df/2, x/2), by its series below the
    mean and its continued fraction above it (Numerical Recipes §6.2). Exact to ~1e-12."""
    if df <= 0:
        raise ValueError("a χ² test needs at least one degree of freedom")
    if x <= 0:
        return 1.0
    a, z = df / 2.0, x / 2.0
    gln = math.lgamma(a)
    if z < a + 1:                      # P by the series; Q = 1 − P
        term = total = 1.0 / a
        ap = a
        for _ in range(10_000):
            ap += 1
            term *= z / ap
            total += term
            if abs(term) < abs(total) * 1e-15:
                break
        return max(0.0, 1.0 - total * math.exp(-z + a * math.log(z) - gln))
    b = z + 1 - a                      # Q by the continued fraction (modified Lentz)
    c, d = 1.0 / 1e-300, 1.0 / b
    h = d
    for i in range(1, 10_000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1e-300 if abs(d) < 1e-300 else d
        c = b + an / c
        c = 1e-300 if abs(c) < 1e-300 else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-15:
            break
    return min(1.0, math.exp(-z + a * math.log(z) - gln) * h)


# ------------------------------------------------------------------- reading the run

def lean_of(raw: dict[str, Any] | None, *, stop_reason: str | None = None) -> str:
    """One draw's lean, as production reads it, or DISSENT. The guard writes a truncated
    response's PARTIAL tool input to the draws file, but `extract` raises on it (a failed draw),
    and `synthesize` drops a draw missing a structural field: neither is a vote."""
    if not raw or stop_reason == "max_tokens" or any(k not in raw for k in _STRUCTURAL):
        return DISSENT
    parts = split_lean(str(_decode_escapes(raw.get("evidence_balance")) or ""))
    if parts is None:
        return DISSENT
    key = re.sub(r"\s+", "-", parts[0].strip().lower())
    return key if key in KNOWN else DISSENT


def modal(labels: Sequence[str]) -> tuple[str, int]:
    """The modal lean of a sequence of draws and its count — ties to the label that appears
    first, as `synthesis.synthesize` breaks them. DISSENT is never a lean."""
    tally = Counter(x for x in labels if x != DISSENT)
    if not tally:
        return DISSENT, 0
    top = max(tally.values())
    first = next(x for x in labels if x != DISSENT and tally[x] == top)
    return first, top


def run_labels(reg: bd.RunRegistration, budget: rp.Budget,
               draws_out: Path) -> dict[str, list[list[str]]]:
    """Every registered build's draws as labels, in draw order: page → build → draws. Refuses a run
    that is not the registered one, complete: a build missing, stopped, or of the wrong length."""
    starts = {(r["ticker"], r["build"]) for r in bd._build_rows(budget, reg.sha, "build_start")}
    ends = {(r["ticker"], r["build"]): r for r in bd._build_rows(budget, reg.sha, "build_end")}
    want = {(t, k) for t in reg.pages for k in range(1, reg.builds + 1)}
    if starts != want or set(ends) != want:
        missing = sorted(want - (starts & set(ends)))
        raise rp.ReplayError(f"the run is not complete under {reg.sha[:12]}: builds {missing} "
                             "have no start or end in the ledger — score a complete run only")
    stopped = sorted(k for k, e in ends.items() if e.get("stopped"))
    if stopped:
        raise rp.ReplayError(f"builds {stopped} stopped: the run is not the registered one")
    rows = [json.loads(x) for x in draws_out.read_text(encoding="utf-8").splitlines() if x.strip()]
    out: dict[str, list[list[str]]] = {}
    used: list[dict[str, Any]] = []
    for t in reg.pages:
        out[t] = []
        for k in range(1, reg.builds + 1):
            label = f"{reg.sha[:12]}:{t}:build{k}"
            mine = sorted((r for r in rows if r.get("label") == label), key=lambda r: r["draw"])
            if [r["draw"] for r in mine] != list(range(1, reg.draws + 1)):
                raise rp.ReplayError(f"{t} build {k}: draws {[r['draw'] for r in mine]} on file, "
                                     f"not 1..{reg.draws}")
            out[t].append([lean_of(r.get("raw"), stop_reason=r.get("stop_reason")) for r in mine])
            used += mine
    # every build of one registration on one SDK: a re-sync between builds would read as
    # between-build dispersion (review of #1049, round 1)
    rp.one_sdk(used, f"registration {reg.sha[:12]}")
    return out


# ------------------------------------------------------------------- the rules on one build

def r1(labels: Sequence[str]) -> tuple[str | None, str]:
    """R1 + C(iii) on one build's attempted draws: (the proposed lean or None, the state)."""
    lean, x = modal(labels)
    n = len(labels)
    if lean in COMMITTED and x >= r1_k(n):
        return lean, "proposed"
    if lean in COMMITTED and 2 * x > n:
        return None, "borderline"
    return None, "none"


def c_i(labels: Sequence[str]) -> tuple[str | None, str, int]:
    """C(i) on a ten-draw build: decide on the first five; a committed 3/2 or 4/1 continues and is
    decided by R1 at ten on the SAME lean. Returns (lean or None, state, draws it used)."""
    first = labels[:5]
    lean, x = modal(first)
    if lean in COMMITTED and x == 5:
        return lean, "proposed", 5
    if lean in COMMITTED and x in (3, 4):
        same = sum(1 for y in labels if y == lean)
        if same >= r1_k(len(labels)):
            return lean, "proposed", len(labels)
        return None, ("borderline" if 2 * same > len(labels) else "none"), len(labels)
    return None, "none", 5


# ------------------------------------------------------------------- the score

@dataclass(frozen=True)
class PageDispersion:
    ticker: str
    modal: str
    counts: tuple[int, ...]
    p_hat: float
    x2: float | None   # None: p̂ is 0 or 1, the page carries no degree of freedom


@dataclass(frozen=True)
class IndependenceScore:
    registration: str
    pages: tuple[PageDispersion, ...]
    x2: float
    df: int
    p: float
    vif: float
    falsified: bool
    dissent_draws: int
    stop_dissent: bool
    first_vs_cached_p: float
    first_modal: int
    first_n: int
    outcomes: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    disagree: dict[str, tuple[int, int]] = field(default_factory=dict)
    expected_draws_c: float = 0.0
    #: False when no page has 0 < p̂ < 1: the dispersion test has no degree of freedom.
    testable: bool = True
    #: The reported runs test, pooled over builds (record §7): z and its two-sided normal p.
    runs_z: float = 0.0
    runs_p: float = 1.0
    #: Builds whose first draw read 0 tokens from the cache (`build_end.first_draw_cache_read`).
    uncached_openings: int = 0

    @property
    def decision(self) -> str:
        if self.stop_dissent:
            return (f"STOP: {self.dissent_draws} draws failed, did not parse or carried no lean "
                    f"(more than {MAX_DISSENT_DRAWS}) — the operator rules")
        if not self.testable:
            return ("STOP: NOT TESTABLE — every page is unanimous over its draws (p̂ 0 or 1), so "
                    "the dispersion test has no degree of freedom; the operator rules")
        if self.falsified:
            return (f"STOP: independence FALSIFIED (X² {self.x2:.2f} on {self.df} df, p "
                    f"{self.p:.4f} ≤ {ALPHA}; VIF {self.vif:.2f}) — the binomial tables are "
                    "optimistic; the implementing PR waits for the operator")
        return (f"independence NOT falsified (X² {self.x2:.2f} on {self.df} df, p {self.p:.4f}; "
                f"VIF {self.vif:.2f}): the design's tables stand")


def _first_vs_cached(labels: dict[str, list[list[str]]], modals: dict[str, str],
                     uncached: dict[str, list[bool]]) -> tuple[float, int, int]:
    """Exact, stratified by page: given each page's draws carrying its pooled modal label, the
    number among the first draws of its builds that OPENED UNCACHED (the ledger's
    `first_draw_cache_read` is 0) is hypergeometric; the pages' sum is their convolution. Two-sided
    p: every total no more likely than the one observed."""
    dist = {0: 1.0}
    observed = n_first = 0
    for t, builds in labels.items():
        allx = [y for b in builds for y in b]
        opened = [b for b, cold in zip(builds, uncached[t], strict=True) if cold]
        m, total, firsts = sum(y == modals[t] for y in allx), len(allx), len(opened)
        observed += sum(b[0] == modals[t] for b in opened)
        n_first += firsts
        page = {j: math.comb(m, j) * math.comb(total - m, firsts - j) / math.comb(total, firsts)
                for j in range(0, min(m, firsts) + 1) if firsts - j <= total - m}
        new: dict[int, float] = {}
        for a, pa in dist.items():
            for j, pj in page.items():
                new[a + j] = new.get(a + j, 0.0) + pa * pj
        dist = new
    p_obs = dist.get(observed, 0.0)
    return min(1.0, sum(p for p in dist.values() if p <= p_obs * (1 + 1e-9))), observed, n_first


def runs_test(labels: dict[str, list[list[str]]], modals: dict[str, str]) -> tuple[float, float]:
    """Wald–Wolfowitz runs within each build, the draws read as carrying the page's pooled modal
    label or not, pooled over builds: z = Σ(R − E) / √ΣVar over the builds holding both symbols,
    E = 1 + 2·n₁n₀/n and Var = 2·n₁n₀(2·n₁n₀ − n) / (n²(n − 1)); two-sided normal p. Too few runs
    (z < 0) is clumping inside a build. Reported, never decided on (record §7)."""
    dev = var = 0.0
    for t, builds in labels.items():
        for b in builds:
            xs = [y == modals[t] for y in b]
            n1, n = sum(xs), len(xs)
            n0 = n - n1
            if n1 == 0 or n0 == 0:
                continue
            runs = 1 + sum(1 for u, v in zip(xs, xs[1:], strict=False) if u != v)
            dev += runs - (1 + 2 * n1 * n0 / n)
            var += 2 * n1 * n0 * (2 * n1 * n0 - n) / (n * n * (n - 1))
    if var <= 0:
        return 0.0, 1.0
    z = dev / math.sqrt(var)
    return z, math.erfc(abs(z) / math.sqrt(2))


def score(reg: bd.RunRegistration, budget: rp.Budget, draws_out: Path) -> IndependenceScore:
    """$0: the registered rule on the registered run (`run_labels` refuses any other)."""
    labels = run_labels(reg, budget, draws_out)
    pages: list[PageDispersion] = []
    x2 = 0.0
    df = 0
    modals: dict[str, str] = {}
    for t, builds in labels.items():
        lean, _ = modal([y for b in builds for y in b])
        modals[t] = lean
        counts = tuple(sum(y == lean for y in b) for b in builds)
        n = reg.draws
        p_hat = sum(counts) / (n * len(builds))
        page_x2: float | None = None
        if 0 < p_hat < 1:
            page_x2 = sum((x - n * p_hat) ** 2 for x in counts) / (n * p_hat * (1 - p_hat))
            x2 += page_x2
            df += len(builds) - 1
        pages.append(PageDispersion(t, lean, counts, p_hat, page_x2))
    testable = df > 0
    p = chi2_sf(x2, df) if testable else 1.0
    dissent = sum(y == DISSENT for bs in labels.values() for b in bs for y in b)
    ends = {(r["ticker"], r["build"]): r for r in bd._build_rows(budget, reg.sha, "build_end")}
    uncached = {t: [ends[(t, k)].get("first_draw_cache_read") == 0
                    for k in range(1, reg.builds + 1)] for t in labels}
    first_p, first_modal, first_n = _first_vs_cached(labels, modals, uncached)
    runs_z, runs_p = runs_test(labels, modals)
    outcomes: dict[str, dict[str, list[str]]] = {"A": {}, "B": {}, "C(i)": {}}
    disagree: dict[str, tuple[int, int]] = {}
    used: list[int] = []
    for t, builds in labels.items():
        a = [r1(b[:5]) for b in builds]
        b10 = [r1(b) for b in builds]
        c = [c_i(b) for b in builds]
        used += [u for _, _, u in c]
        outcomes["A"][t] = [f"{lean or '-'} ({state})" for lean, state in a]
        outcomes["B"][t] = [f"{lean or '-'} ({state})" for lean, state in b10]
        outcomes["C(i)"][t] = [f"{lean or '-'} ({state})" for lean, state, _ in c]
        for rule, got in (("A", [x for x, _ in a]), ("B", [x for x, _ in b10]),
                          ("C(i)", [x for x, _, _ in c])):
            d, n_pairs = disagree.get(rule, (0, 0))
            pairs = list(combinations(got, 2))
            disagree[rule] = (d + sum(1 for u, v in pairs if u != v), n_pairs + len(pairs))
    return IndependenceScore(
        registration=reg.sha, pages=tuple(pages), x2=x2, df=df, p=p,
        vif=x2 / df if testable else 0.0, falsified=testable and p <= ALPHA,
        dissent_draws=dissent, stop_dissent=dissent > MAX_DISSENT_DRAWS,
        first_vs_cached_p=first_p, first_modal=first_modal, first_n=first_n,
        outcomes=outcomes, disagree=disagree,
        expected_draws_c=sum(used) / len(used) if used else 0.0, testable=testable,
        runs_z=runs_z, runs_p=runs_p,
        uncached_openings=sum(sum(v) for v in uncached.values()))


def score_text(s: IndependenceScore) -> str:
    lines = [s.decision, f"  registration {s.registration[:16]}"]
    for pg in s.pages:
        x2 = "n/a (p̂ 0 or 1)" if pg.x2 is None else f"{pg.x2:.2f}"
        lines.append(f"  {pg.ticker:5} modal {pg.modal:16} counts {list(pg.counts)} "
                     f"p̂ {pg.p_hat:.3f} X² {x2}")
    lines.append(f"  dissent draws {s.dissent_draws} (STOP above {MAX_DISSENT_DRAWS})")
    lines.append(f"  builds that opened uncached {s.uncached_openings}; their first draws carrying "
                 f"the page's modal label {s.first_modal} of {s.first_n}; exact stratified p "
                 f"{s.first_vs_cached_p:.4f} (reported)")
    lines.append(f"  runs test within builds, pooled: z {s.runs_z:+.2f}, two-sided p "
                 f"{s.runs_p:.4f} (reported)")
    for rule, (d, n) in s.disagree.items():
        lines.append(f"  {rule}: builds of one page disagree in {d} of {n} pairs (reported)")
    lines.append(f"  C(i) draws a build, observed mean {s.expected_draws_c:.2f}")
    for rule, by_page in s.outcomes.items():
        for t, got in by_page.items():
            lines.append(f"  {rule:5} {t:5} {got}")
    return "\n".join(lines)
