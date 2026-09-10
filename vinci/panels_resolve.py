"""(phase 3) Resolving the universal seven for one name, against COMMITTED data only.

This is the layer that answers phase 2's FORM question — can the disclosure deliver the number —
and it answers it by READING, never by fetching. Everything here comes from artifacts already on
disk: the per-ticker dossier, the latest monitor snapshot, the scenario record. A panel grid that
fetched would show a mark the repo cannot reproduce, which is the rule `emit_monitor` already
states for the frontend.

THE REFUSAL IS NEVER COMPOSED HERE. A dossier fact is `{value, source_ref, status, note}` — the
assembler already decided whether a figure is present and, when it is not, already wrote down why
(`pe_percentile_5y`: *"a share-basis change (stock split) falls inside the window"*). That `note`
is the upstream refusal phase 2 passes through verbatim. Re-deriving a reason here would be a
divergent parser of a question already answered, which is the class that cost this repo a false
reconcile caveat.

`have` IS SLICED PER PANEL, never shared across the grid — `PanelRegistry.decide` refuses a key
matching no requirement of the panel being decided, and that strictness is deliberate (a panel is
told about its own requirements and no others).
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from vinci.panels import PanelDecision, PanelRegistry, Requirement
from vinci.panels_declare import config_for, declared_for
from vinci.panels_universal import UNIVERSAL_SEVEN, universal_registry

#: A dossier fact is PRESENT only when the assembler says so AND a value survived. Both halves are
#: needed: `status` is the assembler's verdict, and a null value with a "present" status would be a
#: fact that reads as available and renders as nothing.
_PRESENT = "present"


def _fact(mechanical: dict[str, Any], path: str) -> tuple[bool, str]:
    """Resolve a dotted path to `(satisfied, upstream_reason)`.

    The reason is the fact's OWN `note` when it has one. A missing note is not papered over with an
    invented sentence — the panel then refuses with its requirement's `why` alone, which is honest
    about the fact that nobody recorded a cause.
    """
    cur: Any = mechanical
    walked: list[str] = []
    for part in path.split("."):
        walked.append(part)
        if not isinstance(cur, dict) or part not in cur:
            return False, (f"the dossier carries nothing at 'mechanical.{'.'.join(walked)}' — the "
                           f"section is absent from this assembly, which is different from a "
                           f"section present and unresolved")
        cur = cur[part]
    if not isinstance(cur, dict):
        # A bare value with no {value, source_ref} envelope is unsourced, and the fund's
        # source-binding rule makes that unusable rather than merely untidy.
        return False, (f"'mechanical.{path}' holds a bare value with no source_ref envelope, so it "
                       f"cannot be shown source-bound")
    status = cur.get("status")
    note = (cur.get("note") or "").strip()
    if status == _PRESENT and cur.get("value") is not None:
        return True, ""
    if status is None:
        # TWO ENVELOPE SHAPES, and an earlier draft of this function knew only one. A SCALAR fact is
        # `{value, source_ref, status, note}`. A COMPOSITE section — `primary_source.filing`,
        # `dilution_pipeline` — carries its content under its OWN keys (`maturity_wall`,
        # `commitments`, `filings`) with a `source_ref` and no `value` or `status` at all. Requiring
        # `value` refused all 18 names on `sources` while every one of them carried a filing
        # reference: absent-vs-broken, committed by the very phase that exists to separate them, and
        # caught only by running the corpus rather than a fixture.
        if cur.get("value") is not None or cur.get("source_ref"):
            return True, ""
        return False, (f"'mechanical.{path}' is present but carries neither a value nor a "
                       f"source_ref, so there is nothing source-bound to show")
    # A REFUSAL WITH NO REASON IS THE BLANK TILE THIS PHASE EXISTS TO PREVENT, so the absence of a
    # recorded cause is itself stated rather than passed on as silence.
    return False, note or (
        f"'mechanical.{path}' is marked {status!r} and the assembler recorded no note saying why, "
        f"so the cause is genuinely unknown rather than omitted here")


def select_row(rows: list[dict[str, Any]], ticker: str) -> tuple[dict[str, Any] | None, str]:
    """The one decision row "the call" means for a name — or a refusal saying why there isn't one.

    A NAME IS NOT A ROW. The ledger is append-only and a name may carry several decisions: SMPL has
    two in the committed 2026-08-11 snapshot, one closed (entered 2026-07-20) and one open
    (2026-08-04). Keying the snapshot by ticker — `{r["ticker"]: r for r in rows}` — silently keeps
    whichever came last in list order, so the panel would show an entry price and an excess from a
    position the book no longer holds, with nothing anywhere saying it had chosen. This function
    exists because that collapse is invisible at the call site and a dict comprehension is the
    obvious way to write it.

    THE RULE, and it is a rule rather than a preference: the LIVE call is the open row, because a
    closed row's call is already scored and the panel's job is the position the book holds now. With
    no open row the latest closed one is shown — the call is historical but real, and the row's own
    `closed` flag says so. With MORE THAN ONE open row there is no single live call, and choosing
    would pick an entry basis at random, so it refuses by name.
    """
    mine = [r for r in rows if r.get("ticker") == ticker]
    if not mine:
        return None, ""
    live = [r for r in mine if not r.get("closed")]
    if len(live) > 1:
        return None, (
            f"{ticker} carries {len(live)} OPEN decision rows in this snapshot (entered "
            f"{', '.join(str(r.get('entry_date')) for r in live)}), so there is no single live "
            f"call and which entry basis to show would be a guess — the append-only ledger permits "
            f"this and the panel refuses rather than picking one")
    if live:
        return live[0], ""
    return max(mine, key=lambda r: str(r.get("entry_date") or "")), ""


def _resolve_requirement(
    req: Requirement,
    *,
    mechanical: dict[str, Any],
    row: dict[str, Any] | None,
    freshness: dict[str, Any] | None,
    record: dict[str, Any] | None,
) -> tuple[bool, str]:
    if req.kind == "metric_path":
        return _fact(mechanical, req.detail)
    if req.kind == "ledger_row":
        if row is None:
            return False, ("this name has no row in the latest committed monitor snapshot, so "
                           "there is no verdict of record to show — an unrecorded position is "
                           "invisible to the book, which is the state phase 0 exists to fix")
        return (row.get(req.detail) not in (None, "")), (
            f"the snapshot row carries no {req.detail!r}")
    if req.kind == "snapshot_field":
        src = freshness if req.detail in (freshness or {}) else row
        if src is None:
            return False, "this name is in neither the snapshot's rows nor its freshness list"
        return (src.get(req.detail) is not None), (
            f"the snapshot carries no {req.detail!r} for this name")
    if req.kind == "criterion":
        if record is None:
            return False, ("no scenario record on file, so there is no measured criterion to put a "
                           "number beside — the kill text exists only as prose")
        measured = ((record.get("verdict") or {}).get(req.detail)) or []
        return bool(measured), (
            "the record carries kill criteria as PROSE with no measured form, so they can only be "
            "re-printed — which is precisely the gap this phase exists to close")
    raise ValueError(f"no resolver for requirement kind {req.kind!r}")


def resolve_universal(
    *,
    dossier: dict[str, Any] | None,
    row: dict[str, Any] | None,
    freshness: dict[str, Any] | None,
    record: dict[str, Any] | None,
    declared: frozenset[str] | None = None,
    registry: PanelRegistry | None = None,
) -> list[PanelDecision]:
    """Decide all seven for one name, in render order.

    `declared` is SUBSTANCE and defaults to all seven — universal means every followed name has
    every one of these economic questions, which is what the tier *means*. It stays an argument
    rather than an assumption so that a name can be excluded deliberately and visibly.
    """
    reg = registry or universal_registry()
    mechanical = (dossier or {}).get("mechanical") or {}
    want = declared if declared is not None else frozenset(p.key for p in UNIVERSAL_SEVEN)
    out: list[PanelDecision] = []
    for spec in UNIVERSAL_SEVEN:
        have: dict[str, bool] = {}
        because: dict[str, str] = {}
        for req in spec.requires:
            ok, why = _resolve_requirement(
                req, mechanical=mechanical, row=row, freshness=freshness, record=record)
            # KIND-QUALIFIED KEY: `detail` alone collapsed two requirements sharing a detail under
            # different kinds into one probe, so a panel could report READY with a disclosure never
            # probed. `probe_key` is the single place that shape is decided.
            have[req.probe_key] = ok
            if not ok and why:
                because[req.probe_key] = why
        out.append(reg.decide(
            spec.key, declared=spec.key in want, have=have, because=because))
    return out


# --------------------------------------------------------------------------------------------
# (phase 4) COHORT resolution. Same gating rule; one extra moving part — an R-file note's
# presence cannot be known offline.
# --------------------------------------------------------------------------------------------

#: Answers "is this note in this filer's latest filing?" → `(present, upstream_reason)`. INJECTED
#: rather than called directly, because resolving a note means fetching a FilingSummary and this
#: module's contract is that it reads committed artifacts and never fetches. The monitor run owns
#: the network; the gating rule owns the decision; neither reaches into the other.
NoteProbe = Callable[[str], tuple[bool, str]]


def resolve_cohort(
    ticker: str,
    *,
    dossier: dict[str, Any] | None,
    declarations: dict[str, dict[str, dict[str, str]]],
    registry: PanelRegistry,
    note_probe: NoteProbe | None = None,
) -> list[PanelDecision]:
    """Decide this name's DECLARED cohort panels, in registry order.

    Substance comes from the declaration — a name that does not declare a panel gets `not_in_set`
    and renders nothing, which is how LLY and V correctly show no commissioning tile: neither
    publishes a property-named report, so neither runs that panel.

    With no `note_probe` every `rfile_note` requirement REFUSES, naming the absent probe. That is
    deliberate: the alternative is assuming a note exists because a human wrote its name down, and a
    declaration is an intention, not evidence.
    """
    mechanical = (dossier or {}).get("mechanical") or {}
    declared = declared_for(ticker, declarations)
    out: list[PanelDecision] = []
    for key in registry:
        spec = registry.get(key)
        assert spec is not None
        cfg = config_for(ticker, key, declarations)
        have: dict[str, bool] = {}
        because: dict[str, str] = {}
        # SUBSTANCE BEFORE FORM, AT THIS LAYER TOO. `decide` is careful to settle `not_in_set` and
        # the unfilled-config refusal before it ever looks at `have` — but an earlier cut of this
        # loop ran the probes first regardless, so a name that does NOT declare `commissioning`
        # still sent a FilingSummary fetch asking for the DEFAULT note name, which is ALPHABET's,
        # against that filer's accounts. The answer was then thrown away by `decide`. That is both
        # the query this module's docstring says must never be sent and a network round trip for a
        # tile that renders nothing.
        settled = (
            key not in declared
            or any(r.config_key and not (cfg.get(r.config_key) or "").strip()
                   for r in spec.requires))
        if settled:
            out.append(registry.decide(key, declared=key in declared, config=cfg))
            continue
        for req in (r.resolve(cfg) for r in spec.requires):
            if req.kind == "rfile_note":
                if note_probe is None:
                    ok, why = False, (
                        "no filing probe was supplied to this run, so whether the named note is in "
                        "the latest filing is UNKNOWN — a declaration records an intention, not "
                        "evidence, and assuming the note exists is how one filer's note gets read "
                        "as another's")
                else:
                    ok, why = note_probe(req.detail)
            else:
                ok, why = _resolve_requirement(
                    req, mechanical=mechanical, row=None, freshness=None, record=None)
            have[req.probe_key] = ok
            if not ok and why:
                because[req.probe_key] = why
        out.append(registry.decide(
            key, declared=key in declared, have=have, because=because, config=cfg))
    return out
