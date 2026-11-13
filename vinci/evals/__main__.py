"""``python -m vinci.evals <command>`` — the harness's own entry points. $0 except the two marked
PAID, which need ``--paid``, an opened budget ledger (the operator's approval and cap) and a
registration written before the first draw.

    budget-open --budget-ledger FILE --cap USD --approval "<operator's words>"
                                              one ledger per approval; every run shares it
    compare --base main --cand <ref> [--transform NAME ...]       $0: does CAND's request differ?
    register --base main --cand <ref> [--transform NAME ...] (--target M-LABEL [--target ...] |
             --no-worsening) [--ticker T ...] [--ciq-root DIR] [--ship-alpha A | --single-run]
             [--replicates FIRST.json] --budget-ledger FILE --out FILE
                                              BEFORE any draw, $0: pages, draws, targets, scorer,
                                              and every request's bytes (captured here); a target
                                              is under the replication rule at ship alpha 0.01
                                              BY DEFAULT, and --single-run opts out, stated
    run-compare --registration FILE --budget-ledger FILE --out-dir DIR [--cap USD] --paid
                                              PAID: the registered draws, page by page, ONCE
    score --out-dir DIR --registration FILE --budget-ledger FILE
                                              $0: the registered rule, logged, with every run
                                              the ledger records under the registration
    capture --ticker T [--code-ref REF] [--transform NAME ...] --out FILE
    prove --ticker T --log FILE [--code-ref REF] [--page-ref REF]
    judge --half dev|test --budget-ledger FILE --out-dir DIR --paid
                                              PAID: the judge on one gold half, calibrated
    gold                                      each metric's P/R, DEV and TEST, at the freeze
    panel                                     re-run the panel rule on the frozen rows
    register-run [--code-ref REF] [--transform NAME ...] [--ticker T ...] [--draws N] [--builds K]
                 [--min-gap-s S] [--ciq-root DIR] [--note TEXT] --out FILE
                                              BEFORE any draw, $0: one condition drawn as separate
                                              builds; every page's request bytes pinned (`builds`)
    run --registration FILE --ticker T --build K --budget-ledger FILE --draws-out FILE
        [--ciq-root DIR] [--transform NAME ...] [--cap USD] --paid
                                              PAID: one build of one page, under its registration;
                                              without --paid, every check at $0 and no draw
    score-run --registration FILE --budget-ledger FILE --draws-out FILE
                                              $0: the independence measurement's registered rule
                                              on its complete run (`independence`)

Requests, saved logs, ledgers, registrations and raw draws hold licensed transcript text or
spend records: they stay OUTSIDE the repository, and every command here refuses a path inside it.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vinci.evals.compare import Registration


def _paid(a: argparse.Namespace) -> bool:
    if not a.paid:
        print("this command spends money: pass --paid, with the operator's approval and cap",
              file=sys.stderr)
        return False
    from vinci.config import load_local_env
    load_local_env()
    return True


def _rule_line(reg: Registration) -> str:
    """The rule a `register` registration is decided by, as printed: the replication rule is the
    default for a target (coordinator default 3, 2026-11-12), so a single run says it opted out.
    A gated metric's families are printed too: the no-worsening check reads only those."""
    gates = "".join(f"; {m}'s no-worsening check counts only {fams}"
                    for m, fams in sorted(reg.no_worsening_families.items()))
    return _rule_body(reg) + gates


def _rule_body(reg: Registration) -> str:
    if reg.no_worsening:
        return f"no-worsening only (no target): no class metric worsens at p_upper <= {reg.alpha}"
    if reg.replicates is not None:
        return (f"a REPLICATION of {reg.replicates[:16]} under the replication rule: its "
                f"target(s) must reach p_lower <= {reg.alpha}")
    if reg.ship_alpha is not None:
        return (f"the replication rule (the default): ships at p_lower <= {reg.ship_alpha}; in "
                f"({reg.ship_alpha}, {reg.alpha}] a fresh registered replication (`register "
                f"--replicates`) must reach p_lower <= {reg.alpha}; above {reg.alpha} it does "
                "not ship")
    if reg.single_run:
        return (f"SINGLE RUN (--single-run, stated in the registration): ships at p_lower <= "
                f"{reg.alpha} on one run, with no replication — it opts out of the replication "
                "rule, the default")
    return reg.rule


def _run(a: argparse.Namespace) -> int:
    """`run`: one build of one page, under its `register-run` registration. Every flag that would
    change what is drawn is the registration's; given here, it is only checked against it."""
    from vinci.evals import builds as bd
    from vinci.evals import replay as rp
    if a.registration is None:
        raise rp.ReplayError("`run` needs --registration: paid draws only on a registration "
                             "written before them (`register-run`; RUNBOOKS §n step 4)")
    reg = bd.RunRegistration.from_json(a.registration.read_text(encoding="utf-8"))
    if a.build is None:
        raise rp.ReplayError("`run` needs --build: which of the page's registered builds")
    if a.transform and tuple(a.transform) != reg.transforms:
        raise rp.ReplayError(f"--transform {a.transform}: the registration's transforms are "
                             f"{list(reg.transforms)}")
    if a.code_ref and bd._resolve(a.code_ref) != reg.code_ref:
        raise rp.ReplayError(f"--code-ref {a.code_ref}: the registration's commit is "
                             f"{reg.code_ref[:12]}")
    if a.draws is not None and a.draws != reg.draws:
        raise rp.ReplayError(f"--draws {a.draws}: the registration draws {reg.draws} a build")
    if a.label is not None:
        raise rp.ReplayError("--label: a registered build's label is derived from it")
    rp.refuse_inside_repo(a.draws_out, "raw draws")
    budget = rp.Budget.load(a.budget_ledger, cap_usd=a.cap)
    # read where the registration was captured unless told otherwise (the pin checks either way);
    # a registration always records its root, so there is no default to fall back to
    ciq_root = a.ciq_root or Path(reg.inputs["ciq_root"])
    if not a.paid:   # $0: every refusal and the pinned capture, then the usual refusal to spend
        pb = bd.prepare_build(reg, a.ticker, a.build, budget=budget, ciq_root=ciq_root)
        gap = "first build" if pb.gap_s is None else f"{pb.gap_s:.0f}s after the last"
        print(f"{a.ticker} build {a.build}: every check passed ({gap}); nothing drawn",
              file=sys.stderr)
        _paid(a)     # prints the refusal to spend
        return 2
    _paid(a)         # loads the key from the local env
    from vinci.evals import registry
    registry.require_on_main(reg.sha)   # RG-D14: drawn only once main holds the registration
    approval = registry.approval_id(a.budget_ledger)

    def claim() -> object:   # RG-D9: called by run_build after its $0 checks, under its lock
        return registry.claim_draw(reg, approval=approval, unit=f"{a.ticker}:{a.build}")
    raws = bd.run_build(reg, a.ticker, a.build, budget=budget, draws_out=a.draws_out,
                        ciq_root=ciq_root, claim=claim)
    start, end = (bd.build_row(budget, reg, k, a.ticker, a.build)
                  for k in ("build_start", "build_end"))
    gap = "first build" if start["gap_s"] is None else f"{start['gap_s']:.0f}s after the last"
    print(f"{a.ticker} build {a.build}: {sum(r is not None for r in raws)}/{reg.draws} usable "
          f"draws ({gap}; first draw read {end['first_draw_cache_read']} tokens from cache); the "
          f"approval's spend is now ${budget.spent():.4f} of ${budget.cap_usd:.2f}")
    return 0


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
        # register --from-impact reads its two commits from the export (both may be omitted)
        c.add_argument("--base", required=name == "compare")
        c.add_argument("--cand", required=name == "compare")
        c.add_argument("--transform", action="append", default=[])
        c.add_argument("--ciq-root", type=Path,
                       help="the CIQ folders transcripts and comps exports are read from "
                            "(default: the assembler's copy)")
        c.add_argument("--ticker", action="append",
                       help="limit to these pages (register: target pages OUTSIDE the panel; "
                            "the panel is registered whole)")
        if name == "register":
            c.add_argument("--target", action="append", default=[])
            c.add_argument("--no-worsening", action="store_true",
                           help="no target: only that no class metric worsens (§6.1)")
            rule = c.add_mutually_exclusive_group()
            rule.add_argument("--ship-alpha", type=float,
                              help="the replication rule, THE DEFAULT for a target at 0.01: ship "
                                   "at p_lower <= this; up to alpha, a fresh registered "
                                   "replication must reach alpha")
            rule.add_argument("--single-run", action="store_true",
                              help="opt a target OUT of the replication rule: one run, decided "
                                   "at alpha — stated in the registration and printed")
            c.add_argument("--replicates", type=Path,
                           help="register a REPLICATION of this registration (same design)")
            c.add_argument("--no-worsening-families", action="append", default=[],
                           metavar="METRIC=FAMILY,FAMILY",
                           help="gate METRIC's no-worsening check on these families only; the "
                                "rest are reported, never gated")
            c.add_argument("--note", help="what the registration states before the draw (in "
                                          "its sha): what the target covers and does not")
            c.add_argument("--budget-ledger", type=Path,
                           help="required: the approval that may draw this registration (with "
                                "--replicates, the ledger that records the first run and its "
                                "ledger-backed score)")
            c.add_argument("--draws", type=int, default=5)
            c.add_argument("--from-impact", type=Path, metavar="EXPORT",
                           help="register an impact run's captured requests and layers (fresh "
                                "builds at each arm's code), never a replay of the frozen page")
            c.add_argument("--out", required=True, type=Path)
    rc = sub.add_parser("run-compare")
    rc.add_argument("--registration", required=True, type=Path)
    rc.add_argument("--budget-ledger", required=True, type=Path)
    rc.add_argument("--cap", type=float, help="may only LOWER the approved cap")
    rc.add_argument("--out-dir", required=True, type=Path)
    rc.add_argument("--ciq-root", type=Path)
    rc.add_argument("--paid", action="store_true")
    s = sub.add_parser("score")
    s.add_argument("--out-dir", required=True, type=Path)
    s.add_argument("--registration", required=True, type=Path)
    s.add_argument("--budget-ledger", required=True, type=Path)
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
    jd = sub.add_parser("judge")
    jd.add_argument("--half", required=True, choices=("dev", "test"))
    jd.add_argument("--budget-ledger", required=True, type=Path)
    jd.add_argument("--cap", type=float, help="may only LOWER the approved cap")
    jd.add_argument("--out-dir", required=True, type=Path)
    jd.add_argument("--ticker", action="append", help="limit to these pages of the half")
    jd.add_argument("--paid", action="store_true")
    sub.add_parser("gold")
    sub.add_parser("panel")
    rr = sub.add_parser("register-run")
    rr.add_argument("--code-ref", default="HEAD")
    rr.add_argument("--transform", action="append", default=[])
    rr.add_argument("--ticker", action="append",
                    help="target pages OUTSIDE the panel; none given: the panel whole")
    rr.add_argument("--draws", type=int, default=10, help="draws a build")
    rr.add_argument("--builds", type=int, default=4, help="builds a page")
    rr.add_argument("--min-gap-s", type=float, default=300.0,
                    help="least seconds between two builds of one page (the cache lifetime)")
    rr.add_argument("--ciq-root", type=Path,
                    help="the CIQ folders transcripts and comps exports are read from "
                         "(default: the assembler's copy)")
    rr.add_argument("--note")
    rr.add_argument("--budget-ledger", required=True, type=Path,
                    help="the approval that may draw this registration (bound in the index)")
    rr.add_argument("--out", required=True, type=Path)
    sr = sub.add_parser("score-run")
    sr.add_argument("--registration", required=True, type=Path)
    sr.add_argument("--budget-ledger", required=True, type=Path)
    sr.add_argument("--draws-out", required=True, type=Path)
    r = sub.add_parser("run")
    r.add_argument("--registration", type=Path,
                   help="a `register-run` registration; required (no paid draw is unregistered)")
    r.add_argument("--build", type=int, help="which of the page's registered builds, from 1")
    r.add_argument("--ticker", required=True)
    r.add_argument("--code-ref", help="a cross-check: must be the registration's commit")
    r.add_argument("--transform", action="append", default=[],
                   help="a cross-check: given, they must be the registration's, in order")
    r.add_argument("--ciq-root", type=Path,
                   help="the CIQ folders transcripts and comps exports are read from "
                        "(default: the registration's)")
    r.add_argument("--budget-ledger", required=True, type=Path)
    r.add_argument("--cap", type=float, help="may only LOWER the approved cap")
    r.add_argument("--draws-out", required=True, type=Path)
    r.add_argument("--label", help="refused: a registered build's label is derived")
    r.add_argument("--draws", type=int, help="a cross-check: must be the registration's")
    r.add_argument("--paid", action="store_true")
    a = ap.parse_args(argv)

    from vinci.evals import replay as rp

    if a.cmd == "budget-open":
        bud = rp.Budget.open(a.budget_ledger, cap_usd=a.cap, approval=a.approval)
        print(f"approved budget ${bud.cap_usd:.2f} opened at {bud.ledger}")
        return 0
    if a.cmd == "register":
        from vinci.evals import compare as cm
        from vinci.evals import registry
        rp.refuse_inside_repo(a.out, "the registration")
        if a.out.exists():
            raise rp.ReplayError(f"{a.out} exists: a registration is written once")
        # THE APPROVAL FIRST (#1030 review round 1, item 7): refused after the file was written,
        # the file left behind blocked the retry
        if a.budget_ledger is None:
            raise rp.ReplayError("register needs --budget-ledger: a registration is bound to the "
                                 "approval that may draw it (open it first: budget-open)")
        approval = registry.approval_id(a.budget_ledger)
        from vinci.evals.builds import _resolve
        if a.from_impact is not None:   # the impact run's fresh captures, read as captured
            if a.transform:
                raise rp.ReplayError("--transform: an impact export's requests were built by "
                                     "each arm's own code; there is nothing to transform")
            if a.ticker:
                raise rp.ReplayError("--ticker: an impact export is registered with the pages "
                                     "it captured; none is chosen or dropped")
            cap = cm.captured_from_impact(a.from_impact)
            for given, got in ((a.base, cap.base_ref), (a.cand, cap.cand_ref)):
                if given is not None and _resolve(given) != got:
                    raise rp.ReplayError(f"{given}: the export's commits are {cap.base_ref[:12]}"
                                         f" and {cap.cand_ref[:12]}")
            a.base, a.cand = cap.base_ref, cap.cand_ref
            p = rp.load_panel_file()
            pages_of = [t for t, cond in cap.requests if cond == "BASE"]
            a.ticker = None if set(pages_of) == set(p["panel"]) else pages_of
        elif a.base is None or a.cand is None:
            raise rp.ReplayError("register needs --base and --cand, or --from-impact")
        else:
            # PINNED TO COMMITS (review round 0): RG-D14's own merge moves main between
            # registering and drawing, so a ref recorded as given would be read at a moved main
            a.base, a.cand = _resolve(a.base), _resolve(a.cand)
        scorer, scorer_ref = cm.fixed_scorer(a.base)   # RG-D12: BASE production, main harness
        if a.from_impact is None:
            pages = cm.registered_pages(a.ticker)
            cap = cm.compare_requests(a.base, a.cand, tickers=pages, transforms=a.transform,
                                      ciq_root=a.ciq_root or rp.DEFAULT_CIQ_ROOT)
        cm.refuse_if_unreached(cap)
        first = (cm.Registration.from_json(a.replicates.read_text(encoding="utf-8"))
                 if a.replicates else None)
        reg = cm.register(a.base, a.cand, targets=a.target, draws=a.draws,
                          transforms=a.transform, pages=a.ticker, captured=cap,
                          no_worsening=a.no_worsening, ship_alpha=a.ship_alpha,
                          single_run=a.single_run,
                          replicates=first, ledger=a.budget_ledger, note=a.note,
                          no_worsening_families={
                              m: f.split(",") for m, _, f in
                              (x.partition("=") for x in a.no_worsening_families)})
        if reg.scorer != scorer:
            raise rp.ReplayError(f"the scorer registered ({reg.scorer[:12]}) is not the fixed "
                                 f"scorer ({scorer[:12]}) at {scorer_ref[:12]}")
        import dataclasses
        reg = dataclasses.replace(reg, scorer_ref=scorer_ref)
        cm.write_registration(reg, a.out)
        registry.record_registered(reg, approval=approval)   # its key derived from it (round 2)
        print(f"indexed in {registry.INDEX}: merge that row to main in a docs-only PR before "
              "any draw (RG-D14)")
        print(f"registered {reg.sha[:16]}: pages {list(reg.pages)}, {reg.draws} draws per "
              f"condition, targets {list(reg.targets)}, held out from this change "
              f"{list(reg.held_out) or 'none'} -> {a.out}")
        print(f"rule: {_rule_line(reg)}")
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
        imp = run.inputs.get("impact") if run is not None else None
        if imp:   # an impact registration: the exported bytes, checked, never a replay
            cap = cm.captured_from_impact(Path(imp["dir"]))   # its manifest: run_compare's check
        else:
            cap = cm.compare_requests(base, cand, tickers=tickers, transforms=transforms,
                                      ciq_root=a.ciq_root or rp.DEFAULT_CIQ_ROOT)
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
        cm.refuse_unless_registered_scorer(run)   # RG-D12: the fixed scorer, never the candidate's
        from vinci.evals import registry
        registry.require_on_main(run.sha)   # RG-D14: drawn only once main holds the registration
        approval = registry.approval_id(a.budget_ledger)

        def claim() -> object:   # RG-D9: called by run_compare after its $0 refusals
            return registry.claim_draw(run, approval=approval)
        cm.run_compare(cap, budget=budget, out_dir=a.out_dir, registration=run, claim=claim)
        print(f"drawn; the approval's spend is now ${budget.spent():.4f} of "
              f"${budget.cap_usd:.2f}; score with `python -m vinci.evals score --out-dir "
              f"{a.out_dir} --registration {a.registration} --budget-ledger {a.budget_ledger}`")
        return 0
    if a.cmd == "register-run":
        from vinci.evals import builds as bd
        from vinci.evals import compare as cm
        rp.refuse_inside_repo(a.out, "the registration")
        if a.out.exists():
            raise rp.ReplayError(f"{a.out} exists: a registration is written once")
        from vinci.evals import registry
        approval = registry.approval_id(a.budget_ledger)   # the approval first (round 1, item 7)
        breg = bd.register_run(code_ref=a.code_ref, pages=cm.registered_pages(a.ticker),
                               transforms=a.transform, draws=a.draws, builds=a.builds,
                               min_gap_s=a.min_gap_s, ciq_root=a.ciq_root or rp.DEFAULT_CIQ_ROOT,
                               note=a.note)
        bd.write_registration(breg, a.out)
        registry.record_registered(breg, approval=approval)   # its key derived from it (round 2)
        print(f"indexed in {registry.INDEX}: merge that row to main in a docs-only PR before "
              "any draw (RG-D14)")
        print(f"registered {breg.sha[:16]}: pages {list(breg.pages)}, {breg.builds} builds of "
              f"{breg.draws} draws a page, at least {breg.min_gap_s:.0f}s between a page's "
              f"builds, code {breg.code_ref[:12]}, transforms {list(breg.transforms)} -> {a.out}")
        return 0
    if a.cmd == "run":
        return _run(a)
    if a.cmd == "score-run":
        from vinci.evals import builds as bd
        from vinci.evals import independence as ind
        breg = bd.RunRegistration.from_json(a.registration.read_text(encoding="utf-8"))
        from vinci.evals import registry
        registry.require_on_main(breg.sha)   # RG-D14: scored only as main holds it registered
        res = ind.score(breg, rp.Budget.load(a.budget_ledger), a.draws_out)
        print(ind.score_text(res))
        # every STOP exits 1, NOT TESTABLE included (Codex round 1, #978), so no gate reads past it
        return 1 if (res.falsified or res.stop_dissent or not res.testable) else 0
    if a.cmd == "score":
        from vinci.evals import compare as cm
        reg = cm.Registration.from_json(a.registration.read_text(encoding="utf-8"))
        cm.refuse_unless_registered_scorer(reg)   # RG-D12: the fixed scorer, never the candidate's
        from vinci.evals import registry
        registry.require_on_main(reg.sha)   # RG-D14: scored only as main holds it registered
        print(cm.score_text(cm.score_run(a.out_dir, reg, ledger=a.budget_ledger)))
        return 0
    if a.cmd in ("capture", "prove"):
        if a.cmd == "capture":
            rp.refuse_inside_repo(a.out, "a captured request (it carries the transcripts)")
        if a.cmd == "prove" and a.page_ref:
            page = rp.page_at(a.ticker, a.page_ref)
            tx = rp.transcript_for(a.ticker, page=page)
        else:
            page, tx = rp.panel_inputs(a.ticker)
        names: list[str] = list(getattr(a, "transform", []))
        req = (rp.capture_at(a.code_ref, page, tx, transforms=names)
               if a.code_ref else rp.capture(page, tx, transforms=names))
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
              f"IDENTICAL {proof.identical} (the log carries no tools, tool_choice or "
              "cache_control: those are compared only between a capture and its paid request)")
        return 0 if proof.identical else 1
    if a.cmd == "judge":
        from vinci.evals import gold as gd
        from vinci.evals import judge as jg
        rp.refuse_inside_repo(a.out_dir, "the judge's run folder")
        budget = rp.Budget.load(a.budget_ledger, cap_usd=a.cap)
        if not _paid(a):
            return 2
        gold = gd.load_gold()
        # RG-D9's TEST-once across approvals is claimed by run_half itself (#1030 round 2, F5)
        judged = jg.run_half(a.half, budget=budget, out_dir=a.out_dir, gold=gold,
                             tickers=a.ticker)
        print(jg.calibration_text(jg.calibrate(judged, gold, a.half, tickers=a.ticker)))
        print(f"the approval's spend is now ${budget.spent():.4f} of ${budget.cap_usd:.2f}")
        return 0
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
