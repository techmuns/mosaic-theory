"""``python -m vinci.evals <command>`` — the harness's own entry points. $0 except the two marked
PAID, which need ``--paid``, an opened budget ledger (the operator's approval and cap) and a
registration written before the first draw.

    budget-open --budget-ledger FILE --cap USD --approval "<operator's words>"
                                              one ledger per approval; every run shares it
    compare --base main --cand <ref> [--transform NAME ...]       $0: does CAND's request differ?
    register --base main --cand <ref> [--transform NAME ...] --target M-LABEL [--target ...]
             --out FILE                       BEFORE any draw: pages, draws, targets, scorer
    run-compare --registration FILE --budget-ledger FILE --out-dir DIR [--cap USD] --paid
                                              PAID: the registered draws, page by page
    score --out-dir DIR --registration FILE   $0: the registered rule, logged
    capture --ticker T [--code-ref REF] [--transform NAME ...] --out FILE
    prove --ticker T --log FILE [--code-ref REF] [--page-ref REF]
    gold                                      each metric's P/R, DEV and TEST, at the freeze
    panel                                     re-run the panel rule on the frozen rows
    run --ticker T [--code-ref REF] --budget-ledger FILE --draws-out FILE --label L [--cap USD]
        --paid                                PAID: one page, one condition

Requests, saved logs, ledgers, registrations and raw draws hold licensed transcript text or
spend records: they stay OUTSIDE the repository, and every command here refuses a path inside it.
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
    b = sub.add_parser("budget-open")
    b.add_argument("--budget-ledger", required=True, type=Path)
    b.add_argument("--cap", required=True, type=float)
    b.add_argument("--approval", required=True)
    for name in ("compare", "register"):
        c = sub.add_parser(name)
        c.add_argument("--base", required=True)
        c.add_argument("--cand", required=True)
        c.add_argument("--transform", action="append", default=[])
        c.add_argument("--ticker", action="append", help="compare: limit to these panel pages")
        if name == "register":
            c.add_argument("--target", action="append", required=True)
            c.add_argument("--draws", type=int, default=5)
            c.add_argument("--out", required=True, type=Path)
    rc = sub.add_parser("run-compare")
    rc.add_argument("--registration", required=True, type=Path)
    rc.add_argument("--budget-ledger", required=True, type=Path)
    rc.add_argument("--cap", type=float, help="may only LOWER the approved cap")
    rc.add_argument("--out-dir", required=True, type=Path)
    rc.add_argument("--paid", action="store_true")
    s = sub.add_parser("score")
    s.add_argument("--out-dir", required=True, type=Path)
    s.add_argument("--registration", required=True, type=Path)
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
    r.add_argument("--budget-ledger", required=True, type=Path)
    r.add_argument("--cap", type=float, help="may only LOWER the approved cap")
    r.add_argument("--draws-out", required=True, type=Path)
    r.add_argument("--label", required=True)
    r.add_argument("--draws", type=int, default=5)
    r.add_argument("--paid", action="store_true")
    a = ap.parse_args(argv)

    from vinci.evals import replay as rp

    if a.cmd == "budget-open":
        bud = rp.Budget.open(a.budget_ledger, cap_usd=a.cap, approval=a.approval)
        print(f"approved budget ${bud.cap_usd:.2f} opened at {bud.ledger}")
        return 0
    if a.cmd == "register":
        from vinci.evals import compare as cm
        rp.refuse_inside_repo(a.out, "the registration")
        reg = cm.register(a.base, a.cand, targets=a.target, draws=a.draws,
                          transforms=a.transform)
        cm.write_registration(reg, a.out)
        print(f"registered {reg.sha[:16]}: pages {list(reg.pages)}, {reg.draws} draws per "
              f"condition, targets {list(reg.targets)}, held out from this change "
              f"{list(reg.held_out) or 'none'} -> {a.out}")
        return 0
    if a.cmd in ("compare", "run-compare"):
        from vinci.evals import compare as cm
        run: cm.Registration | None = None
        if a.cmd == "run-compare":
            run = cm.Registration.from_json(a.registration.read_text(encoding="utf-8"))
            base, cand, transforms, tickers = (run.base_ref, run.cand_ref, run.transforms,
                                               list(run.pages))
            rp.refuse_inside_repo(a.out_dir, "the run folder")
            budget = rp.Budget.load(a.budget_ledger, cap_usd=a.cap)
        else:
            base, cand, transforms, tickers = a.base, a.cand, tuple(a.transform), a.ticker
        cap = cm.compare_requests(base, cand, tickers=tickers, transforms=transforms)
        for d in cap.diffs:
            delta = {k: d.cand_sizes.get(k, 0) - v for k, v in d.base_sizes.items()
                     if d.cand_sizes.get(k, 0) != v}
            print(f"{d.ticker:5} {'IDENTICAL' if d.identical else 'differs'}; USER diff "
                  f"{d.user_diff_lines} lines; SYSTEM equal {d.system_equal}; size deltas {delta}")
        if not cap.reaches:
            print(f"REFUSED: {cand} reaches no page's request — see RUNBOOKS §n step 2",
                  file=sys.stderr)
            return 1
        if run is None:
            return 0
        if not _paid(a):
            return 2
        cm.run_compare(cap, budget=budget, out_dir=a.out_dir, registration=run)
        print(f"drawn; the approval's spend is now ${budget.spent():.4f} of "
              f"${budget.cap_usd:.2f}; score with `python -m vinci.evals score --out-dir "
              f"{a.out_dir} --registration {a.registration}`")
        return 0
    if a.cmd == "score":
        from vinci.evals import compare as cm
        reg = cm.Registration.from_json(a.registration.read_text(encoding="utf-8"))
        print(cm.score_text(cm.score_run(a.out_dir, reg)))
        return 0
    if a.cmd in ("capture", "prove", "run"):
        if a.cmd == "capture":
            rp.refuse_inside_repo(a.out, "a captured request (it carries the transcripts)")
        if a.cmd == "run":
            rp.refuse_inside_repo(a.draws_out, "raw draws")
            budget = rp.Budget.load(a.budget_ledger, cap_usd=a.cap)
        if a.cmd == "prove" and a.page_ref:
            page = rp.page_at(a.ticker, a.page_ref)
            tx = rp.transcript_for(a.ticker, page=page)
        else:
            page, tx = rp.panel_inputs(a.ticker)
        names: list[str] = list(getattr(a, "transform", []))
        draws = getattr(a, "draws", 5)
        req = (rp.capture_at(a.code_ref, page, tx, draws=draws, transforms=names)
               if a.code_ref else rp.capture(page, tx, draws=draws, transforms=names))
        if a.cmd == "capture":
            a.out.write_text(json.dumps(req.kwargs), encoding="utf-8")
            print(f"{a.ticker}: SYSTEM {len(req.system):,} USER {len(req.user):,} chars -> {a.out}")
            return 0
        if a.cmd == "run":
            if not _paid(a):
                return 2
            raws = rp.run_request(req, draws=draws, budget=budget, label=a.label,
                                  draws_out=a.draws_out)
            print(f"{a.ticker}: {sum(r is not None for r in raws)}/{draws} usable draws; the "
                  f"approval's spend is now ${budget.spent():.4f} of ${budget.cap_usd:.2f}")
            return 0
        proof = rp.prove(req, rp.parse_log(a.log.read_text(encoding="utf-8")))
        for f in proof.fields:
            print(f"{f.name:6} rebuilt {f.rebuilt_chars:>8,} logged {f.logged_chars:>8,} "
                  f"sha256 {f.rebuilt_sha256} {'==' if f.equal else '!='} {f.logged_sha256} "
                  f"diff {f.diff_lines} lines")
        print(f"model equal {proof.model_equal}; max_tokens equal {proof.max_tokens_equal}; "
              f"IDENTICAL {proof.identical} (the log carries no tools, tool_choice or "
              "cache_control: those are compared only between a capture and its paid request)")
        return 0 if proof.identical else 1
    if a.cmd == "gold":
        from vinci.evals.report import gold_report
        print(gold_report())
        return 0
    if a.cmd == "panel":
        from vinci.evals import panel as pn
        frozen = rp.load_panel_file()
        sel = pn.select_panel(pn.rows_from_json(frozen["rows"]), salt=frozen["salt"])
        same = list(sel.panel) == frozen["panel"]
        print(f"panel {list(sel.panel)} from {sel.eligible} eligible, {sel.feasible} of "
              f"{sel.subsets} subsets feasible, {sel.tied_at_best} tied; equals the frozen panel: "
              f"{same}")
        return 0 if same else 1
    return 2  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
