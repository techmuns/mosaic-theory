"""``python -m vinci.evals <command>`` — the harness's own entry points. $0 except the two marked
PAID, which need ``--paid``, the operator's approval and a cap.

    compare --base main --cand <ref> [--transform NAME ...]       $0: does CAND's request differ?
    run-compare --base main --cand <ref> [--transform NAME ...] --cap USD --out-dir DIR --paid
                                                                  PAID: 5 draws/page/condition
    score --out-dir DIR --target M-LABEL                          $0: the pre-registered rule
    capture --ticker T [--code-ref REF] [--transform NAME ...] --out FILE
    prove --ticker T --log FILE [--code-ref REF] [--page-ref REF] byte-identity against a log
    gold                                                          each metric's P/R, DEV and TEST
    panel                                                         re-run the panel rule
    run --ticker T [--code-ref REF] --cap USD --ledger FILE --draws-out FILE --label L --paid
                                                                  PAID: one page, one condition

Requests, saved logs and raw draws hold licensed transcript text: they stay OUTSIDE the
repository, and the harness refuses a ledger, draws file or out-dir inside it.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _paid(a: argparse.Namespace) -> bool:
    if not a.paid:
        print("this command spends money: pass --paid, with the operator's approval and cap",
              file=sys.stderr)
        return False
    from vinci.config import load_local_env
    load_local_env()
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m vinci.evals", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("compare", "run-compare"):
        c = sub.add_parser(name)
        c.add_argument("--base", required=True)
        c.add_argument("--cand", required=True)
        c.add_argument("--transform", action="append", default=[])
        c.add_argument("--ticker", action="append", help="limit to these panel pages")
        if name == "run-compare":
            c.add_argument("--cap", required=True, type=float)
            c.add_argument("--out-dir", required=True, type=Path)
            c.add_argument("--draws", type=int, default=5)
            c.add_argument("--paid", action="store_true")
    s = sub.add_parser("score")
    s.add_argument("--out-dir", required=True, type=Path)
    s.add_argument("--target", required=True)
    c = sub.add_parser("capture")
    c.add_argument("--ticker", required=True)
    c.add_argument("--code-ref")
    c.add_argument("--transform", action="append", default=[])
    c.add_argument("--out", required=True, type=Path)
    pr = sub.add_parser("prove")
    pr.add_argument("--ticker", required=True)
    pr.add_argument("--log", required=True, type=Path)
    pr.add_argument("--code-ref")
    pr.add_argument("--page-ref")
    sub.add_parser("gold")
    sub.add_parser("panel")
    r = sub.add_parser("run")
    r.add_argument("--ticker", required=True)
    r.add_argument("--code-ref")
    r.add_argument("--cap", required=True, type=float)
    r.add_argument("--ledger", required=True, type=Path)
    r.add_argument("--draws-out", required=True, type=Path)
    r.add_argument("--label", required=True)
    r.add_argument("--draws", type=int, default=5)
    r.add_argument("--paid", action="store_true")
    a = ap.parse_args(argv)

    from vinci.evals import replay as rp

    if a.cmd in ("compare", "run-compare"):
        from vinci.evals import compare as cm
        cap = cm.compare_requests(a.base, a.cand, tickers=a.ticker, transforms=a.transform)
        for d in cap.diffs:
            delta = {k: d.cand_sizes.get(k, 0) - v for k, v in d.base_sizes.items()
                     if d.cand_sizes.get(k, 0) != v}
            print(f"{d.ticker:5} {'IDENTICAL' if d.identical else 'differs'}; USER diff "
                  f"{d.user_diff_lines} lines; SYSTEM equal {d.system_equal}; size deltas {delta}")
        if not cap.reaches:
            print(f"REFUSED: {a.cand} reaches no page's request — see RUNBOOKS §n step 2",
                  file=sys.stderr)
            return 1
        if a.cmd == "compare":
            return 0
        if not _paid(a):
            return 2
        budget = rp.Budget(cap_usd=a.cap, ledger=a.out_dir / "spend_ledger.jsonl")
        cm.run_compare(cap, budget=budget, out_dir=a.out_dir, draws=a.draws)
        print(f"drawn; spent ${budget.spent():.4f} of ${a.cap:.2f}; score with "
              f"`python -m vinci.evals score --out-dir {a.out_dir} --target <metric>`")
        return 0
    if a.cmd == "score":
        from vinci.evals import compare as cm
        print(cm.score_text(cm.score_run(a.out_dir, target=a.target)))
        return 0
    if a.cmd in ("capture", "prove", "run"):
        if a.cmd == "prove" and a.page_ref:
            page = rp.page_at(a.ticker, a.page_ref)
            tx = rp.transcript_for(a.ticker, page=page)
        else:
            page, tx = rp.panel_inputs(a.ticker)
        transforms = getattr(a, "transform", [])
        draws = getattr(a, "draws", 5)
        req = (rp.capture_at(a.code_ref, page, tx, draws=draws, transforms=transforms)
               if a.code_ref else rp.capture(page, tx, draws=draws, transforms=transforms))
        if a.cmd == "capture":
            a.out.write_text(json.dumps(req.kwargs), encoding="utf-8")
            print(f"{a.ticker}: SYSTEM {len(req.system):,} USER {len(req.user):,} chars -> {a.out}")
            return 0
        if a.cmd == "run":
            if not _paid(a):
                return 2
            budget = rp.Budget(cap_usd=a.cap, ledger=a.ledger)
            raws = rp.run_request(req, draws=draws, budget=budget, label=a.label,
                                  draws_out=a.draws_out)
            print(f"{a.ticker}: {sum(r is not None for r in raws)}/{draws} usable draws; spent "
                  f"${budget.spent():.4f} of ${a.cap:.2f}")
            return 0
        proof = rp.prove(req, rp.parse_log(a.log.read_text(encoding="utf-8")))
        for f in proof.fields:
            print(f"{f.name:6} rebuilt {f.rebuilt_chars:>8,} logged {f.logged_chars:>8,} "
                  f"sha256 {f.rebuilt_sha256} {'==' if f.equal else '!='} {f.logged_sha256} "
                  f"diff {f.diff_lines} lines")
        print(f"model equal {proof.model_equal}; max_tokens equal {proof.max_tokens_equal}; "
              f"IDENTICAL {proof.identical}")
        return 0 if proof.identical else 1
    if a.cmd == "gold":
        from vinci.evals.report import gold_report
        print(gold_report())
        return 0
    if a.cmd == "panel":
        from vinci.evals import panel as pn
        frozen = rp.load_panel_file()
        sel = pn.select_panel(pn.rows_from_json(frozen["rows"]))
        same = list(sel.panel) == frozen["panel"]
        print(f"panel {list(sel.panel)} from {sel.eligible} eligible, {sel.feasible} of "
              f"{sel.subsets} subsets feasible, {sel.tied_at_best} tied; equals the frozen panel: "
              f"{same}")
        return 0 if same else 1
    return 2  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
