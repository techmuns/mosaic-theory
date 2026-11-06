"""``python -m vinci.evals <command>`` — the harness's own entry points. $0 except ``run``.

    capture --ticker T [--code-ref REF] --out FILE     the request at $0 (panel inputs, frozen)
    prove --ticker T --log FILE [--code-ref REF] [--page-ref REF]
                                                      byte-identity against a saved build log
    gold                                              each metric's precision/recall, DEV and TEST
    panel                                             re-run the panel rule on the frozen rows
    run --ticker T --cap USD --ledger FILE --draws-out FILE --label L --paid
                                                      PAID draws behind the budget guard

A saved log and raw draws hold licensed transcript text: keep them outside the repository (the
guard refuses a ledger or a draws file inside it).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m vinci.evals", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("capture")
    c.add_argument("--ticker", required=True)
    c.add_argument("--code-ref")
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
    r.add_argument("--cap", required=True, type=float)
    r.add_argument("--ledger", required=True, type=Path)
    r.add_argument("--draws-out", required=True, type=Path)
    r.add_argument("--label", required=True)
    r.add_argument("--paid", action="store_true",
                   help="required: this command spends money")
    a = ap.parse_args(argv)

    from vinci.evals import replay as rp

    if a.cmd in ("capture", "prove"):
        if a.cmd == "prove" and a.page_ref:
            page = rp.page_at(a.ticker, a.page_ref)
            tx = rp.transcript_for(a.ticker, page=page)
        else:
            page, tx = rp.panel_inputs(a.ticker)
        req = rp.capture_at(a.code_ref, page, tx) if a.code_ref else rp.capture(page, tx)
        if a.cmd == "capture":
            a.out.write_text(json.dumps(req.kwargs), encoding="utf-8")
            print(f"{a.ticker}: SYSTEM {len(req.system):,} USER {len(req.user):,} chars -> {a.out}")
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
    if a.cmd == "run":
        if not a.paid:
            print("run spends money: pass --paid, with the operator's approval and cap",
                  file=sys.stderr)
            return 2
        from vinci.config import load_local_env
        load_local_env()
        page, tx = rp.panel_inputs(a.ticker)
        budget = rp.Budget(cap_usd=a.cap, ledger=a.ledger)
        synth, flags, _log = rp.run_paid(page, tx, budget=budget, label=a.label,
                                        draws_out=a.draws_out)
        agree = synth.draw_agreement.model_dump() if synth and synth.draw_agreement else None
        print(f"{a.ticker}: agreement {agree}; flags {len(flags)}; spent ${budget.spent():.4f} "
              f"of ${a.cap:.2f}")
        return 0
    return 2  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
