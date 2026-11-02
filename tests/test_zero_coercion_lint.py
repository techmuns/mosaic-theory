"""THE ZERO-COERCION LINT (audit RC1, 2026-10-30): no `x or 0` / `x or 0.0` in `vinci/` that a
reviewer has not read and allowed.

THE RULE: a CIQ marker or an absent row is None plus a reason, never 0 (`ciq.read_cell`). `x or 0`
is how a None became a stated zero at eight sites (`tests/test_zero_coercion.py`): the revision
counts, the EV bridge's preferred and minority lines and the R4 basis written from them, the anchor
bridge's lease rows, and the EV gap's D&A ratio; the credit-score sites could not fire but carried
the same shape. Each is fixed, not allowed. Every other `or 0` in the package is LISTED below with
the reason it states no figure — a sort key, a gate a None must fail, a None the line above already
excluded, or accounting where none means none spent.

ON MAIN 08948b5a THIS TEST FAILED, naming the eight real sites (18 `or 0` expressions on 11 lines)
and nothing else: 72 expressions on 62 lines, 54 allowed.

A NEW `or 0` REDS HERE. Read it: if a None can arrive from a CIQ cell, a filing tag or an absent
row, say so instead (None plus a reason); if it truly states no figure, add its line below with the
reason. A line that leaves the package is refused too, so the list cannot rot.

MATCHED BY (file, enclosing function, expression), never a line number, and COUNTED: one function
holding the same expression twice must be listed twice.
"""

from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: The reasons, once each.
SORT_KEY = "a sort or max key: a None sorts low; no figure is stated"
GATE = "a gate a None must FAIL (`… or 0) > 0`, or a filter below a floor): no figure is stated"
NARROWED = ("unreachable: the line above already excluded None (a filter, an `is not None` check "
            "or a PRESENT status) — it narrows the type for mypy")
COST = ("run accounting (LLM tokens, cost, seconds, counts): an absent cost is no spend — not a "
        "CIQ or filing value")
DISPLAY_ZERO = "the value IS zero: `round(v, 1) or 0.0` turns -0.0 into 0.0 after a None check"
SCALE = ("a denominator floor inside max(…, 1.0): an absent total debt leaves |net debt| to scale "
         "the gap; no figure is stated")
#: (2026-10-30, outside Session A's files) read and reasoned here, each REPORTED to the coordinator
#: in the A2 PR body rather than changed: a stated zero is possible, so each wants its owner's look.
REPORTED = "REPORTED in the A2 PR body (outside Session A's files): "

ALLOWED: tuple[tuple[str, str, str, str], ...] = (
    ("vinci/cli.py", "_cmd_screen", "c.data_record.prices.drawdown_from_high.value or 0", SORT_KEY),
    ("vinci/cli.py", "fmt", "b.get('median') or 0",
     REPORTED + "a CLI progress line printing a band's median as 0.0 when it has none; never "
                "stored"),
    ("vinci/dossier/anchor.py", "_band_read", "ev.get('n_closes') or 0",
     "unreachable: `n_closes` is a required field of every own-history band (schemas)"),
    ("vinci/dossier/band_guards.py", "_d_and_a_runs", "revenue or 0.0", GATE),
    ("vinci/dossier/band_guards.py", "_d_and_a_runs", "recorded_d_and_a or 0.0", GATE),
    ("vinci/dossier/capital_allocation.py", "build_peer_capital_intensity",
     "r.market_cap or 0.0", GATE),
    ("vinci/dossier/ciq_sheets.py", "peer_grid", "r.market_cap or 0.0", SORT_KEY),
    ("vinci/dossier/ciq_sheets.py", "_consensus_net_debt_check", "td or 0.0", SCALE),
    ("vinci/dossier/ciq_sheets.py", "pe_eps_basis", "eps.get(k, {}).get(p) or 0", GATE),
    ("vinci/dossier/ebitda_recon.py", "reconcile", "r.filing_ebitda or 0.0", NARROWED),
    ("vinci/dossier/lease_basis.py", "observations",
     "_near(fin_edgar, d, _FINANCE_NEAR_DAYS) or 0.0",
     REPORTED + "a finance-lease tag EDGAR does not carry near the date is added to the ex-lease "
                "bridge as 0 — possibly a stated zero"),
    ("vinci/dossier/mechanical.py", "_split_straddled_trend", "recent[brk].value or 0",
     REPORTED + "picks the word 'rose'/'fell' from two share counts; a None one reads as 0"),
    ("vinci/dossier/mechanical.py", "_split_straddled_trend", "recent[brk - 1].value or 0",
     REPORTED + "picks the word 'rose'/'fell' from two share counts; a None one reads as 0"),
    ("vinci/dossier/mechanical.py", "_share_count_trend", "factor or 0.0", NARROWED),
    ("vinci/dossier/mechanical.py", "_stock_info", "bridged.value or 0", GATE),
    ("vinci/dossier/mechanical.py", "occurrences", "r.usd or 0.0", SORT_KEY),
    ("vinci/dossier/render.py", "_numc", "round(v, 1) or 0.0", DISPLAY_ZERO),
    ("vinci/dossier/render.py", "_multiple_basis_md", "band.implied_ebitda_margin or 0", NARROWED),
    ("vinci/dossier/render.py", "_lease_basis_md", "lb.rent_ebitda or 0", GATE),
    ("vinci/dossier/render.py", "_customer_concentration", "x.pct or 0.0", NARROWED),
    ("vinci/dossier/render.py", "_customer_concentration", "x.pct or 0.0", NARROWED),
    ("vinci/dossier/render.py", "_customer_concentration", "top[0].pct or 0.0", NARROWED),
    ("vinci/dossier/render.py", "_capital_allocation", "x.value or 0.0", NARROWED),
    ("vinci/dossier/synthesis.py", "_cache_misses", "usage.get(k, 0) or 0", COST),
    ("vinci/edgar/net_debt.py", "_unread_debt", "b.current_total or 0.0",
     "inside max(long-term, current): an absent current total leaves the long-term total to "
     "hold; no figure is stated"),
    ("vinci/edgar/primary_source.py", "guide_verification_read", "ciq_high or 0.0",
     REPORTED + "a point guide has no high on either side (0 − 0 matches); one side's high "
                "against the other's none is a mismatch, as it should be"),
    ("vinci/edgar/primary_source.py", "guide_verification_read", "release_high or 0.0",
     REPORTED + "a point guide has no high on either side (0 − 0 matches); one side's high "
                "against the other's none is a mismatch, as it should be"),
    ("vinci/graph/llm.py", "_record_usage", "getattr(u, 'input_tokens', 0) or 0", COST),
    ("vinci/graph/llm.py", "_record_usage", "getattr(u, 'output_tokens', 0) or 0", COST),
    ("vinci/graph/llm.py", "_record_usage", "getattr(u, 'cache_creation_input_tokens', 0) or 0",
     COST),
    ("vinci/graph/llm.py", "_record_usage", "getattr(u, 'cache_read_input_tokens', 0) or 0",
     COST),
    ("vinci/monitor.py", "render_table", "r.excess_price or 0.0",
     REPORTED + "a row's missing excess return prints +0.00 in the monitor table"),
    ("vinci/quality/sources/ciq.py", "_net_debt_vs_implied_bridge", "netted or 0.0", NARROWED),
    ("vinci/quality/sources/ciq.py", "_lease_rows_vs_edgar",
     "_num(o.get('edgar_operating_leases')) or 0.0", GATE),
    ("vinci/quality/sources/release.py", "_revenue_vs_xbrl",
     "_quote_value(value, ('$M',), str(x.get('verbatim') or '')) or 0.0",
     "a tolerance: a quote whose precision is unread gets none, so the comparison is STRICTER"),
    ("vinci/scoring/metrics.py", "to_markdown", "v.vs_basket or 0.0",
     REPORTED + "a missing basket return prints the verdict 'does NOT beat' in the scoring report"),
    ("vinci/theme_intelligence/__main__.py", "cmd_upload", "res.cost_usd or 0", COST),
    ("vinci/theme_intelligence/budget.py", "start_run", "(carried or {}).get('spent_usd') or 0.0",
     COST),
    ("vinci/theme_intelligence/completeness.py", "run_completeness", "c or 0.0", NARROWED),
    ("vinci/theme_intelligence/coverage.py", "_uncarried", "kv[0][0] or 0", SORT_KEY),
    ("vinci/theme_intelligence/desk.py", "gates", "n_counted or 0",
     REPORTED + "a desk line can print '0 exposures' counted where the count was not recorded"),
    ("vinci/theme_intelligence/documents.py", "_read_pdf", "read.pages or 0",
     "a page count bounding a scan for a contents page: an unread count scans none"),
    ("vinci/theme_intelligence/fetch.py", "host_policy", "delay or 0.0",
     "inside max(floor, …): an unstated crawl delay leaves the floor; no figure is stated"),
    ("vinci/theme_intelligence/health.py", "affected_shown", "ma.get('affected_total') or 0",
     "a count in the run-health record: none recorded is none affected"),
    ("vinci/theme_intelligence/ingest.py", "reask_part", "c.cost_usd or 0.0", COST),
    ("vinci/theme_intelligence/pipeline.py", "finish_run", "c.get('seconds') or 0.0", COST),
    ("vinci/theme_intelligence/pipeline.py", "run_scan", "spent_before.get('spent_usd') or 0.0",
     COST),
    ("vinci/theme_intelligence/pipeline.py", "finish_run", "c.get('cost_usd') or 0.0", COST),
    ("vinci/theme_intelligence/pipeline.py", "run_scan", "c.get('cost_usd') or 0.0", COST),
    ("vinci/theme_intelligence/state.py", "pull", "c or 0.0", COST),
    ("vinci/theme_intelligence/upload.py", "_steps", "out.cost_usd or 0", COST),
    ("vinci/themes/forward.py", "baskets_from_mirror", "mirror.get('ratifiedCount', 0) or 0",
     "a count in the radar mirror: an absent count is none ratified"),
    ("vinci/themes/subsidiaries.py", "subsidiaries_of", "str(cik).lstrip('0') or 0",
     "a CIK of all zeros is the integer 0; no figure is stated"),
)


def _zero(node: ast.expr) -> bool:
    return (isinstance(node, ast.Constant) and type(node.value) in (int, float)
            and node.value == 0)


def sites(root: Path = ROOT) -> Counter[tuple[str, str, str]]:
    """Every `x or 0` / `x or 0.0` under `root/vinci/`: (file, enclosing function, expression),
    counted."""
    found: Counter[tuple[str, str, str]] = Counter()
    for py in sorted((root / "vinci").rglob("*.py")):
        tree = ast.parse(py.read_text())
        parent = {c: n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)}
        for node in ast.walk(tree):
            if not (isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or)
                    and _zero(node.values[-1])):
                continue
            fn, p = "<module>", node
            while p in parent:
                p = parent[p]
                if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    fn = p.name
                    break
            found[(py.relative_to(root).as_posix(), fn, ast.unparse(node))] += 1
    return found


def test_every_zero_coercion_in_vinci_is_reviewed() -> None:
    allowed = Counter((f, fn, expr) for f, fn, expr, _why in ALLOWED)
    new = sites() - allowed
    assert not new, (
        "`x or 0` turns a None — a CIQ marker, an absent row, a missing filing tag — into a stated "
        "zero. Say why there is no value instead (`ciq.read_cell`: None plus a reason), or, if "
        "this states no figure, add it to ALLOWED with the reason:\n"
        + "\n".join(f"  {f} [{fn}] {expr}" + (f" ×{n}" if n > 1 else "")
                    for (f, fn, expr), n in sorted(new.items())))


def test_no_allowed_entry_outlives_its_site() -> None:
    allowed = Counter((f, fn, expr) for f, fn, expr, _why in ALLOWED)
    stale = allowed - sites()
    assert not stale, f"ALLOWED lists sites no longer in vinci/ — remove them: {sorted(stale)}"


def test_the_lint_can_fire(tmp_path: Path) -> None:
    """(−) `sites()` itself finds planted sites, so a clean run is a clean package, not a blind
    scan (PR #877 round 2: this read only `_zero`, never the scan)."""
    (tmp_path / "vinci" / "sub").mkdir(parents=True)
    (tmp_path / "vinci" / "sub" / "m.py").write_text(
        "def f(x, y):\n    a = x or 0.0\n    b = y or 0\n    return a + b + (x or False)\n"
        "\ndef g(x):\n    return x or 0.0\n")
    assert sites(tmp_path) == Counter({("vinci/sub/m.py", "f", "x or 0.0"): 1,
                                       ("vinci/sub/m.py", "f", "y or 0"): 1,
                                       ("vinci/sub/m.py", "g", "x or 0.0"): 1})
