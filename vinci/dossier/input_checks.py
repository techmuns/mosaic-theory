"""THE INPUT-CHECK GATE — workstream B slice 2: checks on what a page records it was built from.

A build records every CIQ export, HTTP response and price series it read (`vinci.dossier.inputs`,
slice 1, #911). This module runs a REGISTRY of checks on that record and on the page's own export
stamps, and says the result LOUDLY: on the page's first screen (a FLAG block, both surfaces), in
its audit tier, in the build's run record (`run_metrics`, schema 4) and in the $0 pre-spend check
(`prespend`). Design: `docs/records/2026-11-05-every-page-records-what-it-was-built-from.md`
(the registry's shape) and `docs/records/2026-11-18-the-input-check-gate.md` (this slice).

NOTHING IS HARD. Every check starts as FLAG, and FLAG refuses nothing. A check becomes HARD only
by a recorded ruling (`Check.ruled`, test-pinned) — the coordinator's default of 2026-11-12 is a
clean record on all committed pages first (`docs/records/2026-11-12-operator-delegation-and-
defaults.md`). A HARD check that finds something makes the build refuse BEFORE the page is
written (`refusals`, raised by `assemble`), and only the run record keeps the result.

A PURE FUNCTION OF THE PAGE. Each check reads the page's JSON — its ``inputs`` record and its
10-hex export stamps — and nothing else: no clock, no file, no store. So the result is RE-DERIVED
by the one serializer (`schemas.dossier_json`) on every write of a page that carries it, the
`valuation_basis` precedent: a refresh that restamps a block, or a backfill that rewrites the
record, writes a result that describes what it wrote. A page without the block stays without it
(byte-identical), until a build or `vinci dossier input-checks --write` gives it one.

FENCE-CLEAN, ON PURPOSE. `schemas` imports this module (lazily, inside `dossier_json`), and the
monitor imports `schemas`, so nothing here may reach `vinci.store` (`test_outcome_import_fences`).
That is why the page's stamp walker lives HERE and `vinci.dossier.inputs` re-exports it:
`inputs` reaches the price store.

THE CHECKS (each: its condition, and the recorded fields it reads — its supplying layer):

- ``inputs_recorded`` reads ``inputs.recorded``, ``inputs.unrecorded`` and ``inputs.inputs_id``.
  PASS only on a build's complete record. A BACKFILL always FLAGS: it was resolved afterwards from
  the page's own stamps, and its responses, price series and unstamped exports are unrecorded by
  construction. No record at all FLAGS.
- ``one_export_per_kind`` reads the page's stamps (`stamps`) and ``inputs.ciq``. FLAGS a stamp no
  recorded export begins with ("not the page's export"), a stamp two recorded exports begin with,
  one export kind stamped from two exports, and a record listing two exports of one kind read as
  one. `ciq.MULTI_FILE_KINDS` (transcripts, one per call; customers and suppliers) are held as
  several files by design and are exempt from the one-per-kind rule.

DOES THIS SELECT ON FORM? No. Both read the PIPELINE's provenance — which bytes the build read —
never how a filer discloses or what its economics are. Neither ranks, gates or grades a name, and
neither reaches a verdict, a proposal, a rank or the ledger.
"""
from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from vinci.dossier.ciq import MULTI_FILE_KINDS
from vinci.dossier.ciq_balance import stamps_in_text
from vinci.dossier.inputs_schema import CheckResult, InputChecks

#: A page's CIQ export stamp: the first 10 hex of the file's sha256 (`ciq_sheets.file_provenance`).
#: Any other hash a page carries is no export stamp.
STAMP = re.compile(r"[0-9a-f]{10}")
#: The page blocks the stamp walk leaves out: the record itself (full sha256s, never stamps) and
#: this module's own results, whose findings name stamps and must never be read back as one.
NOT_STAMPS = frozenset({"inputs", "input_checks"})


def stamps(doc: Mapping[str, Any]) -> dict[str, list[str]]:
    """``{10-hex stamp: [page sites]}`` for EVERY export stamp a page carries, outside its own
    ``inputs`` and ``input_checks`` blocks, the site a dotted path with list positions dropped:

    - a key ending ``sha256`` whose value is a 10-hex stamp (`STAMP`; any other hash a page
      carries is no export stamp);
    - a stamp written into a string — an anchor input's ``source``, the bridge's claims source —
      read through the ONE shared reader, `ciq_balance.stamps_in_text` (review round 2 of #911:
      four pages' anchors named exports no key stamped, and the backfill never saw them).

    THE ONE PAGE-STAMP WALKER: the input record's backfill (`inputs.stamps`, re-exported) and the
    gate read it."""
    out: dict[str, set[str]] = {}

    def walk(node: Any, path: str) -> None:
        if isinstance(node, Mapping):
            for key, child in node.items():
                here = f"{path}.{key}" if path else str(key)
                if (str(key).endswith("sha256") and isinstance(child, str)
                        and STAMP.fullmatch(child)):
                    out.setdefault(child, set()).add(here)
                else:
                    walk(child, here)
        elif isinstance(node, list):
            for child in node:
                walk(child, path)
        elif isinstance(node, str):
            for stamp in stamps_in_text(node):
                out.setdefault(stamp, set()).add(path)

    walk({k: v for k, v in doc.items() if k not in NOT_STAMPS}, "")
    return {k: sorted(v) for k, v in out.items()}


@dataclass(frozen=True)
class Finding:
    """What one check found on one page: the first screen's line and every finding in full."""

    summary: str
    findings: tuple[str, ...] = ()
    #: False: the check passed (``summary`` says what held)
    found: bool = True


@dataclass(frozen=True)
class Check:
    """One registry entry (the shape the slice-1 record specified, so slices 2–4 agree)."""

    id: str
    #: plain English, one line: what a FLAG means for the page
    what: str
    level: Literal["FLAG", "HARD"]
    #: the record carrying the ruling (quote + date) that made it HARD; None while FLAG
    ruled: str | None
    #: the recorded fields it reads — its supplying layer
    reads: tuple[str, ...]
    run: Callable[[Mapping[str, Any]], Finding]


def _plural(n: int, one: str, many: str | None = None) -> str:
    return f"{n} {one if n == 1 else (many or one + 's')}"


def inputs_recorded(doc: Mapping[str, Any]) -> Finding:
    """Check 1: the page records every input it read (see the module docstring)."""
    rec = doc.get("inputs")
    if not isinstance(rec, Mapping):
        return Finding("the page carries no input record, so nothing says what it was built from",
                       ("no `inputs` block on the page",))
    unrecorded = [u for u in rec.get("unrecorded") or [] if isinstance(u, Mapping)]
    findings = tuple(f"{u.get('input')} — {u.get('why')}" for u in unrecorded)
    names = ", ".join(str(u.get("input")) for u in unrecorded)
    if rec.get("recorded") != "build":
        return Finding(
            f"the record was resolved afterwards from the page's own export stamps "
            f"({rec.get('recorded')}), not recorded by its build: "
            f"{_plural(len(unrecorded), 'input')} unrecorded ({names or 'none named'})",
            findings or ("a backfill's record is partial by construction",))
    if unrecorded:
        return Finding(f"the build did not record {_plural(len(unrecorded), 'input')}: {names}",
                       findings)
    if not rec.get("inputs_id"):
        return Finding("the build's record lists nothing unrecorded and yet carries no id, so it "
                       "cannot be matched to its run record", ("`inputs.inputs_id` is empty",))
    return Finding(f"every input the build read is recorded ({rec.get('inputs_id')})", found=False)


#: Kinds the one-export-per-kind rule does not apply to: those held as several files by design
#: (`ciq.MULTI_FILE_KINDS`), and ``unknown`` — a file the loader could not classify (a backfill's
#: `inputs._classify`), which is no kind at all, so two of them are not two vintages of one.
_NOT_ONE_PER_KIND = MULTI_FILE_KINDS | {"unknown"}


def _kind(export: Mapping[str, Any]) -> str:
    kind = str(export.get("kind") or "unknown")
    return f"{kind}/{export['freq']}" if export.get("freq") else kind


def one_export_per_kind(doc: Mapping[str, Any]) -> Finding:
    """Check 2: every export the page stamps is the record's one export of its kind (see the
    module docstring)."""
    page_stamps = stamps(doc)
    rec = doc.get("inputs")
    if not isinstance(rec, Mapping):
        return Finding(
            f"the page carries no input record, so none of its "
            f"{_plural(len(page_stamps), 'export stamp')} can be resolved to an export",
            tuple(f"stamp {s} at {', '.join(sites)}" for s, sites in sorted(page_stamps.items()))
            or ("no `inputs` block on the page",))
    exports = [e for e in rec.get("ciq") or [] if isinstance(e, Mapping)]
    findings: list[str] = []
    by_kind: dict[str, dict[str, list[str]]] = {}
    for stamp, sites in sorted(page_stamps.items()):
        hits = {str(e.get("sha256")): e for e in exports
                if str(e.get("sha256") or "").startswith(stamp)}
        if not hits:
            findings.append(f"stamp {stamp} at {', '.join(sites)}: no export in the page's record "
                            "begins with it — the block was not built from an export this page "
                            "records")
        elif len(hits) > 1:
            findings.append(f"stamp {stamp} at {', '.join(sites)}: {len(hits)} recorded exports "
                            "begin with it, so it names none of them")
        else:
            e = next(iter(hits.values()))
            if str(e.get("kind")) not in _NOT_ONE_PER_KIND:
                by_kind.setdefault(_kind(e), {})[stamp] = sites
    for kind, held in sorted(by_kind.items()):
        if len(held) > 1:
            findings.append(f"{kind} is stamped from {len(held)} exports on one page — "
                            + "; ".join(f"stamp {s} at {', '.join(sites)}"
                                        for s, sites in sorted(held.items())))
    listed: dict[str, list[str]] = {}
    for e in exports:
        if str(e.get("kind")) not in _NOT_ONE_PER_KIND:
            listed.setdefault(_kind(e), []).append(str(e.get("file")))
    for kind, files in sorted(listed.items()):
        if len(files) > 1:
            findings.append(f"the record lists {len(files)} {kind} exports, a kind read as one: "
                            + ", ".join(sorted(files)))
    if findings:
        return Finding(f"{_plural(len(findings), 'finding')} on the page's "
                       f"{_plural(len(page_stamps), 'export stamp')}: two vintages, or an export "
                       "the record does not name, sit on one page", tuple(findings))
    return Finding(f"each of the page's {_plural(len(page_stamps), 'export stamp')} is the "
                   "record's one export of its kind", found=False)


INPUTS_RECORDED = Check(
    id="inputs_recorded",
    what="The page cannot say everything it was built from, so it cannot be re-checked anywhere "
         "else",
    level="FLAG", ruled=None,
    reads=("inputs.recorded", "inputs.unrecorded", "inputs.inputs_id"),
    run=inputs_recorded)
ONE_EXPORT_PER_KIND = Check(
    id="one_export_per_kind",
    what="A block on the page was not built from the export the page records for its kind",
    level="FLAG", ruled=None,
    reads=("the page's export stamps", "inputs.ciq"),
    run=one_export_per_kind)

#: THE REGISTRY, in the order the page prints it. Every HARD entry names its ruling (pinned).
REGISTRY: tuple[Check, ...] = (INPUTS_RECORDED, ONE_EXPORT_PER_KIND)


def run(doc: Mapping[str, Any], registry: Sequence[Check] | None = None) -> InputChecks:
    """Every check in ``registry`` (default: `REGISTRY`, read at call time) on the page ``doc``
    (its JSON), in order."""
    results = []
    for check in REGISTRY if registry is None else registry:
        f = check.run(doc)
        outcome = ("pass" if not f.found else "refuse" if check.level == "HARD" else "flag")
        results.append(CheckResult(id=check.id, what=check.what, level=check.level,
                                   outcome=outcome, reads=list(check.reads), summary=f.summary,
                                   findings=list(f.findings)))
    return InputChecks(results=results)


def refusals(checks: InputChecks) -> list[CheckResult]:
    """The results that refuse the write: a HARD check that found something."""
    return [r for r in checks.results if r.outcome == "refuse"]


def refusal_message(ticker: str, refused: Sequence[CheckResult]) -> str:
    """The build's refusal, every HARD finding named."""
    return (f"{ticker}: {_plural(len(refused), 'HARD input check')} refused the write — "
            + "; ".join(f"{r.id}: {r.summary}" for r in refused)
            + " — page not written; the run record keeps every result")


def lines(checks: InputChecks) -> list[str]:
    """The pre-spend check's INPUT CHECKS block: every result, a flag's findings in full."""
    out = [f"INPUT CHECKS — the gate the paid build runs before its write, on this $0 build's "
           f"page ({len(checks.flagged)} of {len(checks.results)} flag; a FLAG refuses nothing):"]
    for r in checks.results:
        out.append(f"  {r.id} [{r.level}] {r.outcome.upper()}: {r.summary}")
        out += [f"      {f}" for f in (r.findings if r.outcome != "pass" else [])]
    return out
