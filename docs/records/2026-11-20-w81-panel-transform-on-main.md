---
id:
status: shipped
date: 2026-11-20
prs: [1147]
supersedes:
superseded-by:
---

# W81's panel transform reaches main ahead of #1147, so its paid panel check can be registered on origin/main's harness (RG-D12); on main it is the identity and no page, request or production file moves ($0, harness + record)

**WHAT.**
- **The change.** `vinci/evals/variants.py` gains `w81_ebitda_names`, the `W81` tuple and its `TRANSFORMS` entry. It is the transform #1147 (W81, SP-D20) wrote for its row-53 panel measurement, unchanged except that both W81 names are read through `getattr`.
- **What it does.** It re-reads the basis, at-price and reconciliation lines with the ref's own code. It writes a line only where the re-read, with W81's words undone, is the committed line.
- **On main it returns the layer untouched.** `ev_ebitda_basis.FOUR_QUARTER` and `at_price_line` do not exist there until #1147 merges. No production file changes.

**WHY.**
- **The rule.** Since RG-D12 (fix request 2, order 8, 2026-11-11), a registration runs on `origin/main`'s harness.
- **What failed.** `register` from a clean checkout of `origin/main` (`cd082d0b`) failed at $0 with "no transform 'w81_ebitda_names'". The transform existed only on #1147, which does not merge before its measurement is scored.
- **The route, checked by coordinator B (2026-11-20).**
  - RUNBOOKS §n's route for a prospective change is `--transform` on the frozen panel. `register --from-impact` and the composite scorer are written for retrospectives.
  - `refuse_if_unreached` names the transform as the route for a change to the mechanical layer's words.
  - The frozen panel keeps the result comparable with the panel's earlier measurements.
  - So the transform comes to main first.

**HOW VERIFIED.**
- **The pins.** `tests/test_evals_w81_identity.py`, 7 pins: the registry entry, and the identity on each of the six frozen panel pages wherever `FOUR_QUARTER` is absent.
  - All 7 fail on `origin/main` `cd082d0b`.
  - The pin removes the name for the test, so it holds on #1147's head too. There, `tests/test_evals_w81_transform.py` pins what the transform writes.
- **On #1147's code** (recorded in `docs/records/2026-11-20-w81-ciq-two-ebitdas-named-apart-and-the-ltm-cause.md`, reaching main with #1147):
  - it reproduces the head builder's three lines on all 25 $0-built pages;
  - its `$0` compare touches only the FACTS span on the six panel pages.
- ruff and `mypy --strict` are clean on main's code, where neither W81 name exists.

**BOUNDARY.** Pages: the six panel pages (BURL, CNXC, LLY, MCK, ROST, SMPL) as frozen at cut `4889ddba`. Base: `origin/main` `cd082d0b`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The protected file was approved by the operator** in #1147's session chat ("Approve it", 2026-11-20) for this same transform, and the commit quotes it.
- **No ask reached the operator at edit time.** The edit was made with the Edit tool, and no ask from `decision_path_guard` reached the operator.
  - The cause is not established. The guard itself asks for that path: B dry-ran it on this file and it returned `ask`.
  - The gate's protected-file check is what bound the approval.
- **Next.** Register from a fresh `origin/main` checkout; the docs-only registration PR; one `run-compare --paid` under the operator's "Yes, cap $35"; score. #1147 then merges main, its `variants.py` made identical to main's.
## Amendments

**2026-11-20 — CARRIED BY #1159.**
- This record's front matter names #1147, the PR whose `3634e29e` first wrote the transform. The PR that carried it to main is **#1159**, merged as `ae5bd872` (the operator: "Merge once green").
- The front matter is left as merged, per the amendment contract.
- **Registered from main.** The registration ran from a clean checkout of `origin/main` at `ae5bd872`, after the import check passed on all 14 modules. It is `e92bfe4da89421c5`: the six panel pages, 5 draws per condition, no target, against #1147's head `4234f9e6`, with this transform.
- Its row reaches main in the docs-only registration PR that carries this amendment, before any draw (RG-D14).
