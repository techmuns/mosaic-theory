"""THE PRE-SPEND CHECK — the paid build's own readers, run at $0, against the committed page.

``vinci dossier precheck --ticker <T>`` builds ``<T>``'s page the way a paid ``vinci dossier
--ticker <T>`` would, with NO LLM call, into a temporary folder — ``data/dossiers/`` is never
written — and compares it with the committed ``data/dossiers/<T>/dossier.json``. Every Sourced
field (a dict carrying ``value`` + ``status``) that is PRESENT on the committed page and is not in
this build is printed with the note this build gives it, and the process exits non-zero, so an
artifact pass stops for the operator BEFORE the money is spent rather than after.

WHY IT EXISTS (2026-11-04). SMPL's page was re-assembled once (run ``4f30d3a2``, $2.27), and only
afterwards was it found that 12 fields the committed page carried read UNKNOWN and the EV bridge
was gone: the new CIQ Financials export carried an undated "Fiscal Year Change" column, which the
latest-cell reader refuses on purpose. The hand-written checks run before the spend (loader,
period types, currency, press-release columns, dates) all passed, because none of them ran the
page's own readers. This does — every reader, on the exports, store and code the paid build will
use — so any change of export shape shows up as a field regression before anything is spent.

WHAT IT CANNOT SEE. A $0 build makes no LLM call, so:

- the synthesis is LLM prose with no Sourced field in it, so it contributes nothing to compare
  (pinned on the committed corpus by ``test_the_synthesis_carries_no_sourced_field``);
- the three ``capital_structure`` fields the paid build's Tier-2 phase writes (``LLM_WRITTEN``) are
  FORECAST, not read: each phase runs with a client that refuses every call (``_RefusingClient``).
  A phase that returns before calling the model is deterministic, so its result is what the paid
  build will write; a phase that reaches the model is listed as decided by the paid draw and is
  not compared. ``covenant_terms`` is always written (the digest states what the extraction found,
  or why it found nothing). These rules mirror ``assemble.assemble_one``;
  ``test_prespend.py`` pins the SET of fields that block writes against its source, not each rule.

VALUES AND LIST MEMBERS (2026-11-11, TeamNostra fix request 2, RD-D4). The check compared
presence only and skipped every Sourced field inside a list, while its last line said nothing
present on the committed page was lost. It now pairs every outermost Sourced field through the one
value comparator (`vinci.impact.values.sourced_pairs`), list members matched by identity:

- a list member both pages hold whose field reads worse (PRESENT on the committed page, not in this
  build) is a REGRESSION, as an outermost field is, and stops the pass;
- a list member that LEFT its list is listed, not a stop: a list's population moves with the
  calendar (a filing ages out of a window), so its absence is not a reader's failure;
- a field PRESENT on both whose value, source or note differs is listed in full, not a stop:
  measured on SMPL's real pair (its 2026-08-18 page, its 2026-11-04 $0 build), 75 of 112 Sourced
  fields change value across eleven weeks of new prices and exports, so a stop on any change would
  stop every pass and mean nothing.

- the six top-level BLOCKS, compared by presence before, are compared leaf by leaf when both
  pages carry one. The fix log's evidence for RD-D4 sat there: VITL's precheck of 2026-11-09 did
  not see its R1 anchor base go 30.0469 → None, nor UBER's ``valuation_basis.priceable`` go
  True → False. Losing one of `DECISION_LEAVES` — the page's own valuation result — is a
  REGRESSION; every other leaf that moved is listed (a leaf losing its value is not, by itself, a
  loss: measured on the eight real pairs of 2026-11-04 and 2026-11-09, 1 to 14 leaves per page,
  mostly consensus multiples and EV-bridge cells that move with the calendar, do so on every one).

The last line says what was compared and how many moved, never that nothing was lost. The
LLM-written fields (`LLM_WRITTEN`) are never value-compared: the $0 build does not write them.

WHAT IT ATTRIBUTES: nothing. A regression can come from the export, the code (SMPL's covenant rows
went because a guard added since its page refuses both exhibits) or the store (a stale benchmark);
the note says which reader gave up and why, and the boundary block says what moved.

THE REFUSALS THE PAID BUILD MAKES ONLY AFTER IT HAS PAID (2026-11-04, review finding 3 on #893).
``assemble_one`` runs two deterministic checks after its covenant, driver and five synthesis calls
(``POST_SPEND``), so a build they refuse has already been paid for. MNST's first assembly
(2026-11-02, run ``373c8ffc``, $3.33) is the case: ``_freshness_check`` refused a share basis its
2-for-1 split had moved, reading only ``stock_info``. This check runs both, at $0, on the layer the
paid build's checks read (`gate_layer`), and exits 1 on each refusal that needs no synthesis:

- ``_freshness_check``: all three of its refusals (a missing cap input, an export panel past the
  ceiling, a share-basis mismatch) read only the mechanical layer and the build's date;
- ``_materiality_check``: its "cannot look" refusals (``MaterialityUnavailableError``: no annual
  Income Statement, period header, revenue row or unusual-items block) read only the exports. Its
  other refusal (``MaterialityError``, a material unusual item the brief's summary does not show)
  is decided by whether the synthesis states it, so it is listed, never a stop.

- ``_refuse_degraded_drawdown_overwrite`` (``POST_WRITE``): ``_write``, after every LLM phase,
  refuses a drawdown cause degraded over a committed PRESENT one. The $0 build writes into a
  scratch folder and never meets the committed page, so it is run here against the committed one.

These run on a first assembly too: a page that does not exist yet costs the same to refuse. The
synthesis-dependent refusals (``_require_synthesis``, the uncited-material-figure guard) cannot be
decided here.

WHAT IT READ (2026-11-05, `vinci.dossier.inputs`). The check records every input its $0 build
reads — the build's own, and the exhibits the LLM-phase forecast fetches, which the paid build
reads inside its covenant phase — and prints them against the committed page's ``inputs`` record:
per class, which inputs are the page's and which moved. It decides nothing: the exit code is the
regressions' and the refusals' alone. ``--inputs-json`` writes the record in full.

THE DRAWDOWN'S DATED PARTS (2026-11-04, `DrawdownAnchor`). The current window rolls with the
page's date, so a rebuild moves an old gap-down OUT of it; on an anchored name the at-the-anchor
part now carries that event, dated. A current-window field (``MOVABLE``) that leaves the window is
therefore no regression when a dated part of this build carries the SAME dates or the SAME exhibit
— it is listed as moved, with the part that carries it. Anything else stays a regression. The
dated parts are compared by VALUE as well as presence, because they must never change once built:
a date or an exhibit the committed page's part carries and this build's does not is a regression,
and so stops the pass (`dated_part_losses`).
"""

from __future__ import annotations

import datetime as dt
import json
import tempfile
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeGuard

from vinci import provenance
from vinci.config import Config
from vinci.dossier import inputs as page_inputs
from vinci.dossier.freshness import MAX_PANEL_AGE_DAYS, PanelAge, panel_age
from vinci.dossier.schemas import Dossier, MechanicalLayer, SourceStatus, dossier_json
from vinci.graph.llm import LlmClient, LlmError
from vinci.impact.values import VOLATILE, SourcedPair, show, sourced_pairs, value_changes

if TYPE_CHECKING:
    from vinci.dossier.ciq import CiqBundle

#: The top-level blocks a full assembly builds outside ``mechanical``, each compared by presence
#: (none carries a Sourced field on the committed corpus, 2026-11-04 — measured, not assumed).
BLOCKS = ("ev_bridge", "forward_consensus", "forward_multiple_history",
          "historical_forecast_error", "valuation_basis", "anchor")

#: The ``capital_structure`` fields only the paid build's Tier-2 phase writes
#: (``assemble.assemble_one``) — forecast through the phase itself (`forecast_llm_fields`).
LLM_WRITTEN = ("covenant_terms", "maturity_event", "covenant_term_rows")

#: The checks ``assemble.assemble_one`` runs only AFTER its LLM phases, each run here at $0
#: (`post_spend_checks`). ``test_prespend.py`` pins this SET against ``assemble_one``'s source.
POST_SPEND = ("_freshness_check", "_materiality_check")

#: The refusals ``assemble._write`` makes (after every LLM phase) that read the COMMITTED page,
#: which the $0 build's scratch ``_write`` never sees — each run here against it
#: (`post_spend_checks`).
POST_WRITE = ("_refuse_degraded_drawdown_overwrite",)

#: The current drawdown window's fields a dated part can carry once they leave the window
#: (`carried_by`); every other field's loss is a regression.
_DD = "mechanical.drawdown_cause."
MOVABLE = (_DD + "gap_down_dates", _DD + "revised_guidance")

#: The leaves of `BLOCKS` that ARE the page's valuation: one the committed page carries (true, or
#: a number) that this build loses (false, null or absent) is a regression (RD-D4's evidence:
#: VITL's anchor base, UBER's priceable flag).
DECISION_LEAVES = ("anchor.applicable", "anchor.anchor_base_value_per_share",
                   "valuation_basis.priceable")

#: Block-leaf changes printed per block before the cut (every one: ``--changes-json``).
BLOCK_SHOWN = 25

#: The drawdown's dated parts, compared by value (`dated_part_losses`).
DATED_PARTS = ("at_anchor", "since")

#: The status of a field this build does not carry at all (key missing, or written as null).
ABSENT = "absent"
_PRESENT = SourceStatus.PRESENT.value
_CS = "mechanical.capital_structure."


@dataclass(frozen=True)
class Field:
    """One Sourced field's coverage: its status and the note it carries (None when it has none)."""

    status: str
    note: str | None


@dataclass(frozen=True)
class Move:
    """One field or block whose presence changed between the committed page and this build."""

    path: str
    before: str
    after: str
    note: str | None


@dataclass(frozen=True)
class Forecast:
    """What the paid build will write at one LLM-written path. ``status`` None: the phase reaches
    the model, so the paid draw decides and the field is not compared."""

    status: str | None
    why: str


@dataclass(frozen=True)
class ValueMove:
    """A Sourced field PRESENT on both pages whose content differs (RD-D4): listed, not a stop."""

    path: str
    before: str
    after: str
    #: the field's citation on each page (equal when only the value moved)
    source_before: str | None
    source_after: str | None
    #: which of the field's own keys moved (``value``, ``source_ref``, ``note``, …)
    parts: tuple[str, ...]


@dataclass(frozen=True)
class Comparison:
    regressions: tuple[Move, ...]
    gained: tuple[Move, ...]
    undecided: tuple[tuple[str, str], ...]
    #: Sourced fields compared: the union of both pages' outermost fields outside lists, minus the
    #: undecided ones.
    compared: int
    #: Sourced fields inside lists, (committed, this build): each COMPARED with the same member's
    #: field (`sourced_pairs`, matched by identity); one that reads worse is a regression
    in_lists: tuple[int, int]
    #: current-window drawdown fields that left the window and a dated part of this build carries
    #: (`carried_by`): listed, not regressions
    moved: tuple[Move, ...] = ()
    #: PRESENT on both pages, content differs (RD-D4): listed in full, not a stop
    changed: tuple[ValueMove, ...] = ()
    #: PRESENT fields of a list member the committed page holds and this build does not: listed,
    #: not a stop (a list's population moves with the calendar)
    left: tuple[Move, ...] = ()
    #: leaves of a block both pages carry that differ (`DECISION_LEAVES` aside): listed
    in_blocks: tuple[Move, ...] = ()


@dataclass(frozen=True)
class Refusal:
    """One refusal a ``POST_SPEND`` check makes: the check, the error's class and its message."""

    check: str
    error: str
    message: str
    #: False when the synthesis decides it: the paid build refuses only if its prose does not
    #: state what the message names, so it is listed and does not stop the pass
    at_zero: bool = True


@dataclass(frozen=True)
class PostSpend:
    """What the ``POST_SPEND`` checks give on a $0 build."""

    refusals: tuple[Refusal, ...]
    #: refusals the synthesis decides (``Refusal.at_zero`` False)
    undecided: tuple[Refusal, ...]
    #: the oldest export panel's age against this build's date, or None when no export panel is
    #: dated: what the freshness verdict was measured at, since a later build sees older panels
    age: PanelAge | None


def sourced_fields(doc: Mapping[str, Any]) -> tuple[dict[str, Field], int]:
    """Every OUTERMOST Sourced field outside a list, by dotted path, and the count inside lists.

    A Sourced value is not descended into: its status speaks for what it carries."""
    out: dict[str, Field] = {}
    in_lists = 0

    def walk(node: Any, path: str, in_list: bool) -> None:
        nonlocal in_lists
        if isinstance(node, dict):
            if "value" in node and "status" in node:
                if in_list:
                    in_lists += 1
                else:
                    note = node.get("note")
                    out[path] = Field(str(node["status"]), str(note) if note else None)
                return
            for key, child in node.items():
                walk(child, f"{path}.{key}" if path else str(key), in_list)
        elif isinstance(node, list):
            for child in node:
                walk(child, path, True)

    walk(doc, "", False)
    return out, in_lists


def _block_state(doc: Mapping[str, Any], block: str) -> str:
    if doc.get(block) is not None:
        return _PRESENT
    return "null" if block in doc else ABSENT


def compare(committed: Mapping[str, Any], fresh: Mapping[str, Any],
            forecast: Mapping[str, Forecast] | None = None) -> Comparison:
    """Every field and block PRESENT on ``committed`` and not on ``fresh`` (a regression), and every
    one present on ``fresh`` only (gained). ``forecast`` replaces ``fresh``'s status at an
    LLM-written path, and its reason is that path's note; a forecast with no status takes the path
    out of the comparison."""
    before, n_before = sourced_fields(committed)
    after, n_after = sourced_fields(fresh)
    undecided: list[tuple[str, str]] = []
    why: dict[str, str] = {}
    for path, fc in (forecast or {}).items():
        if fc.status is None:
            undecided.append((path, fc.why))
            before.pop(path, None)
            after.pop(path, None)
            continue
        why[path] = fc.why
        if fc.status == ABSENT:
            after.pop(path, None)
        else:
            after[path] = Field(fc.status, fc.why)
    regressions: list[Move] = []
    gained: list[Move] = []
    for block in BLOCKS:
        was, now = _block_state(committed, block), _block_state(fresh, block)
        if (was == _PRESENT) != (now == _PRESENT):
            (regressions if was == _PRESENT else gained).append(Move(block, was, now, None))
    compared = sorted(set(before) | set(after))
    for path in compared:
        old, new = before.get(path), after.get(path)
        was = old.status if old else ABSENT
        now = new.status if new else ABSENT
        if was == _PRESENT and now != _PRESENT:
            regressions.append(Move(path, was, now, why.get(path, new.note if new else None)))
        elif was != _PRESENT and now == _PRESENT:
            gained.append(Move(path, was, now, None))
    moved: list[Move] = []
    kept: list[Move] = []
    for m in regressions:
        carrier = carried_by(m.path, committed, fresh) if m.path in MOVABLE else None
        if carrier is None:
            kept.append(m)
        else:
            moved.append(Move(m.path, m.before, m.after, carrier))
    kept += dated_part_losses(committed, fresh)
    skip = {p for p, _ in undecided} | {_CS + f for f in LLM_WRITTEN}
    changed: list[ValueMove] = []
    left: list[Move] = []
    for pair in sourced_pairs(committed, fresh, ignore=VOLATILE | {"inputs"}):
        if any(pair.path == p or pair.path.startswith(p + ".") for p in skip):
            continue
        was, now = pair.status("base"), pair.status("head")
        if pair.in_list and was == _PRESENT and now != _PRESENT:
            if pair.member_moved:
                left.append(Move(pair.path, was, ABSENT, None))
            else:
                note = pair.head.get("note") if isinstance(pair.head, Mapping) else None
                kept.append(Move(pair.path, was, now, str(note) if note else None))
        elif pair.in_list and was != _PRESENT and now == _PRESENT:
            gained.append(Move(pair.path, was, now, None))
        elif was == _PRESENT and now == _PRESENT and (vm := _value_move(pair)) is not None:
            changed.append(vm)
    in_blocks: list[Move] = []
    for block in BLOCKS:
        if committed.get(block) is None or fresh.get(block) is None:
            continue
        for c in value_changes(committed[block], fresh[block], path=block, ignore=VOLATILE):
            lost = (c.path in DECISION_LEAVES and _carries(c.base) and not _carries(c.head))
            move = Move(c.path, show(c.base), show(c.head),
                        "a decision leaf: the committed page's valuation result, which this "
                        "build no longer carries" if lost else None)
            (kept if lost else in_blocks).append(move)
    # a field already a regression (a dated part that changed, `dated_part_losses`) is not also
    # listed as a mere change
    stopped = {m.path for m in kept}
    changed = [v for v in changed if v.path not in stopped]
    return Comparison(tuple(kept), tuple(gained), tuple(undecided), len(compared),
                      (n_before, n_after), tuple(moved), tuple(changed), tuple(left),
                      tuple(in_blocks))


def _carries(v: Any) -> bool:
    """A decision leaf that says something: true, or a number."""
    return v is True or (isinstance(v, (int, float)) and not isinstance(v, bool))


def _value_move(pair: SourcedPair) -> ValueMove | None:
    """``pair``'s content change, or None when both pages carry the same field."""
    changes = pair.changes(ignore=VOLATILE)
    if not changes:
        return None
    parts = sorted({c.path.removeprefix(pair.path + ".").split(".")[0].split("[")[0]
                    for c in changes})
    b, h = pair.base, pair.head
    return ValueMove(pair.path, show(b.get("value")), show(h.get("value")),
                     b.get("source_ref"), h.get("source_ref"), tuple(parts))


def _dig(doc: Mapping[str, Any], *keys: str) -> Any:
    node: Any = doc
    for key in keys:
        if not isinstance(node, Mapping):
            return None
        node = node.get(key)
    return node


def _present(node: Any) -> TypeGuard[Mapping[str, Any]]:
    return isinstance(node, Mapping) and node.get("status") == _PRESENT


def _dated_parts(doc: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    """The drawdown's dated parts on ``doc``, each named with its window."""
    anchor = _dig(doc, "mechanical", "drawdown_cause", "anchor")
    if not isinstance(anchor, Mapping):
        return []
    return [(f"drawdown_cause.anchor.{part} ({w.get('start')} to {w.get('end')})", w)
            for part in DATED_PARTS if isinstance(w := anchor.get(part), Mapping)]


def carried_by(path: str, committed: Mapping[str, Any], fresh: Mapping[str, Any]) -> str | None:
    """Which dated part of ``fresh`` carries what the current-window field at ``path`` (one of
    ``MOVABLE``) held on ``committed`` — or None, and the loss stays a regression.

    BY VALUE, never by presence: every gap-down date the committed field listed must be in a dated
    part of this build, and a revised outlook must be the same exhibit (its source_ref). A dated
    part that carries some other event carries nothing of this one."""
    key = path.removeprefix(_DD)
    was = _dig(committed, "mechanical", "drawdown_cause", key)
    if not _present(was):
        return None
    parts = _dated_parts(fresh)
    if key == "gap_down_dates":
        want = {str(d) for d in was.get("value") or []}
        have: set[str] = set()
        names: list[str] = []
        for name, w in parts:
            dates = w.get("gap_down_dates")
            held = {str(d) for d in dates.get("value") or []} if _present(dates) else set()
            if want & held:
                names.append(name)
            have |= held
        if not want or not want <= have:
            return None
        return f"carried by {' and '.join(names)}: {', '.join(sorted(want))}"
    for name, w in parts:
        rg = w.get(key)
        if _present(rg) and rg.get("source_ref") == was.get("source_ref"):
            return f"carried by {name}: {was.get('source_ref')}"
    return None


def dated_part_losses(committed: Mapping[str, Any], fresh: Mapping[str, Any]) -> list[Move]:
    """What a dated part of ``committed`` held and the same part of ``fresh`` does not, BY VALUE.

    A part present on both sides is compared on what it holds, because presence alone would let a
    rebuild drop one of two gap-downs, or swap the exhibit, and still read as no change. The
    at-the-anchor part is read at its anchor and cannot change, so its dates, its shape (the
    per-gap causes) and its exhibit must all be the same. The since part grows as the page's date
    moves, so its shape changes by design; only a date it held, or the exhibit it named, can be
    lost. A part that vanished entirely is the presence comparison's to report, not this one's."""
    c_anchor = _dig(committed, "mechanical", "drawdown_cause", "anchor")
    f_anchor = _dig(fresh, "mechanical", "drawdown_cause", "anchor")
    if not isinstance(c_anchor, Mapping) or not isinstance(f_anchor, Mapping):
        return []
    moved_on = ("" if f_anchor.get("on") == c_anchor.get("on") else
                f" — the anchor moved from {c_anchor.get('on')} to {f_anchor.get('on')}")
    out: list[Move] = []
    for part in DATED_PARTS:
        cw, fw = c_anchor.get(part), f_anchor.get(part)
        if not isinstance(cw, Mapping) or not isinstance(fw, Mapping):
            continue
        base = f"{_DD}anchor.{part}."
        c_dates, f_dates = cw.get("gap_down_dates"), fw.get("gap_down_dates")
        if _present(c_dates) and _present(f_dates):
            lost = sorted({str(d) for d in c_dates.get("value") or []}
                          - {str(d) for d in f_dates.get("value") or []})
            if lost:
                out.append(Move(base + "gap_down_dates", _PRESENT, "present, without "
                                + ", ".join(lost), "a dated part keeps every gap-down it "
                                "was built with" + moved_on))
        keys = ("shape", "revised_guidance") if part == "at_anchor" else ("revised_guidance",)
        for key in keys:
            c, f = cw.get(key), fw.get(key)
            if not (_present(c) and _present(f)):
                continue
            same = (c.get("value") == f.get("value") if key == "shape"
                    else c.get("source_ref") == f.get("source_ref"))
            if not same:
                out.append(Move(base + key, _PRESENT, "present, changed",
                                f"was {c.get('value') if key == 'shape' else c.get('source_ref')}"
                                f"; this build: "
                                f"{f.get('value') if key == 'shape' else f.get('source_ref')}"
                                + moved_on))
    return out


class _RefusingClient(LlmClient):
    """An LLM client that sends nothing: every call is recorded and refused (`LlmError`), so a phase
    runs its own entry gates and the record says whether it would have reached the model."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    @property
    def model(self) -> str:
        return "none (pre-spend check)"

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        self.calls.append(str(tool.get("name", "")))
        raise LlmError("pre-spend check: no model is called")


def forecast_llm_fields(doc: Dossier, *, http: Any) -> dict[str, Forecast]:
    """What the paid build's Tier-2 phase writes at each of ``LLM_WRITTEN``, run at $0.

    Mirrors ``assemble.assemble_one``: with a capital structure, ``covenant_terms`` becomes the
    digest (always PRESENT); ``maturity_event`` is whatever ``extract_maturity_event`` returns;
    ``covenant_term_rows`` is set only when ``extract_covenant_terms`` returns rows. No capital
    structure → the phase is skipped and nothing here is forecast."""
    from vinci.dossier.covenant_extract import extract_covenant_terms, extract_maturity_event
    from vinci.netcache import SecRateLimitedError, sec_refusal

    cs = doc.mechanical.capital_structure if doc.mechanical is not None else None
    if cs is None:
        return {}
    who = {"cik": doc.cik or "", "ticker": doc.ticker, "name": doc.name}
    out = {_CS + "covenant_terms": Forecast(
        _PRESENT, "the paid build writes the Tier-2 covenant digest here whatever it extracts")}
    probe = _RefusingClient()
    _rows, _summary, flags, _log = extract_covenant_terms(cs, llm=probe, http=http, **who)
    # Rows exist only after a model call, which this client never completes: with no call, the
    # paid build leaves the field as the mechanical layer has it.
    if probe.calls:
        out[_CS + "covenant_term_rows"] = Forecast(
            None, "the covenant phase sends at least one located exhibit to the model")
    else:
        kept = cs.covenant_term_rows
        why = ("the covenant phase makes no LLM call on this build's pointers, so it writes no "
               "term rows" + (": " + "; ".join(flags) if flags else
                              f" ({cs.covenant_terms.note or 'no located exhibit'})"))
        out[_CS + "covenant_term_rows"] = Forecast(
            kept.status.value if kept is not None else ABSENT, why)
    probe = _RefusingClient()
    event, _flags, _log = extract_maturity_event(cs, llm=probe, http=http, **who)
    if probe.calls:
        out[_CS + "maturity_event"] = Forecast(
            None, "the maturity phase sends its 8-K to the model")
    elif event is None:
        out[_CS + "maturity_event"] = Forecast(ABSENT, "no maturity 8-K to read")
    else:
        out[_CS + "maturity_event"] = Forecast(event.status.value, event.note or "maturity phase")
    # Both phases swallow a failed fetch into "no rows" — so a fetch SEC REFUSED would read here as
    # a deterministic loss. The paid build refuses the whole write after a refusal
    # (`assemble._refuse_after_sec_refusal`); so does this forecast.
    if (refusal := sec_refusal()) is not None:
        raise SecRateLimitedError(
            f"{doc.ticker}: SEC refused this run during the LLM-phase forecast ({refusal}) — a "
            "refused exhibit is not a missing one; re-run once SEC's window has passed"
        ) from refusal
    return out


def mechanical_build(ticker: str, cfg: Config) -> Dossier:
    """``ticker``'s page as a paid build would write it, minus every LLM phase — assembled into a
    temporary folder that is deleted on return, so ``data/dossiers/`` is never touched and no run
    record is written. The committed recipe is applied as ``_write`` applies it, so the anchor and
    the valuation basis are the ones the paid write would carry."""
    from vinci.dossier import assemble
    from vinci.dossier.manual_store import LocalFolderStore
    from vinci.resolver import EntityResolver

    fin = assemble.load_finalists(cfg, ticker=ticker)[0]
    resolver = EntityResolver.from_config(cfg)
    _ = resolver.index
    with tempfile.TemporaryDirectory(prefix="vinci-prespend-") as scratch:
        built = assemble.assemble_one(
            fin, cfg=cfg, resolver=resolver, graph=assemble._load_graph(cfg),
            manual=LocalFolderStore.from_config(cfg), out_root=Path(scratch), llm=None)
    return assemble._keep_committed_recipe(built, cfg.data_dir / "dossiers" / built.ticker)


def gate_layer(built: Dossier) -> MechanicalLayer:
    """The mechanical layer as ``assemble_one``'s ``POST_SPEND`` checks read it, from a $0 build:
    its rows marked material (``_mark_material``), as the paid build marks them before its
    synthesis and a $0 build never does. The materiality check reads the marks.

    The rest differs and is left as it is, because the checks cannot tell: what the LLM phases add
    before the checks (the covenant digest, the maturity event, the transcript drivers, the
    covenant rows) is absent here, and ``ev_gap``, which the paid build writes only after them, is
    present. ``test_prespend.py`` measures, on every committed page (which carries all of it), that
    none of it moves the export age the freshness check gates on."""
    from vinci.dossier.assemble import _mark_material

    marked: MechanicalLayer = _mark_material(built.mechanical)
    return marked


def freshness_refusal(gate: MechanicalLayer, *, ticker: str, built_at: dt.date) -> Refusal | None:
    """``assemble._freshness_check`` on ``gate``, measured at ``built_at``, as a refusal or None."""
    from vinci.dossier.assemble import _freshness_check
    from vinci.dossier.freshness import FreshnessError

    try:
        _freshness_check(gate, ticker=ticker, built_at=built_at)
    except FreshnessError as exc:
        return Refusal("_freshness_check", type(exc).__name__, str(exc))
    return None


def materiality_refusal(gate: MechanicalLayer, bundle: CiqBundle, *,
                        ticker: str) -> Refusal | None:
    """``assemble._materiality_check`` with no synthesis, as a refusal or None. A
    ``MaterialityError`` here names a material item the brief's summary does not show; the paid
    build refuses it only if the synthesis does not state it, so it comes back ``at_zero=False``."""
    from vinci.dossier.assemble import _materiality_check
    from vinci.dossier.materiality import MaterialityError, MaterialityUnavailableError

    try:
        _materiality_check(bundle, gate, None, ticker=ticker)
    except MaterialityUnavailableError as exc:
        return Refusal("_materiality_check", type(exc).__name__, str(exc))
    except MaterialityError as exc:
        return Refusal("_materiality_check", type(exc).__name__, str(exc), at_zero=False)
    return None


def drawdown_refusal(built: Dossier, committed: Path) -> Refusal | None:
    """``assemble._refuse_degraded_drawdown_overwrite`` on ``built`` against the committed page's
    folder ``committed``, as a refusal or None."""
    from vinci.dossier.assemble import DossierAssemblyError, _refuse_degraded_drawdown_overwrite

    try:
        _refuse_degraded_drawdown_overwrite(built, committed)
    except DossierAssemblyError as exc:
        return Refusal("_refuse_degraded_drawdown_overwrite", type(exc).__name__, str(exc))
    return None


def post_spend_checks(built: Dossier, bundle: CiqBundle, *,
                      committed: Path | None = None) -> PostSpend:
    """Both ``POST_SPEND`` checks on ``built``, in the paid build's order, each measured at
    ``built``'s own ``assembled_at``, the instant the paid build's checks use for theirs; then,
    given the committed page's folder ``committed``, the ``POST_WRITE`` refusal ``_write`` makes."""
    gate = gate_layer(built)
    day = built.assembled_at.date()
    found = [r for r in (materiality_refusal(gate, bundle, ticker=built.ticker),
                         freshness_refusal(gate, ticker=built.ticker, built_at=day),
                         drawdown_refusal(built, committed) if committed is not None else None)
             if r is not None]
    return PostSpend(tuple(r for r in found if r.at_zero),
                     tuple(r for r in found if not r.at_zero),
                     panel_age(gate.model_dump(mode="json"), day, kind="export"))


def _stamps(doc: Mapping[str, Any]) -> Counter[str]:
    """Every export sha256 the page stamps (a key ending ``sha256`` whose value is a 10-hex stamp,
    and a stamp written into a string — an anchor input's source — through the one shared reader,
    `ciq_balance.stamps_in_text`), with how often.

    ONLY A 10-HEX VALUE IS AN EXPORT STAMP, the rule `inputs.stamps` already kept. A transcript
    driver row's `locator` carries three full sha256s (the call's file, the quote, the stated
    value; RG-D19), and counting them listed each as an export missing from disk."""
    from vinci.dossier.ciq_balance import stamps_in_text
    from vinci.dossier.inputs import _STAMP

    seen: Counter[str] = Counter()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if str(key).endswith("sha256") and isinstance(child, str):
                    if _STAMP.fullmatch(child):
                        seen[child] += 1
                else:
                    walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)
        elif isinstance(node, str):
            seen.update(stamps_in_text(node))

    # the page's input record names full sha256s of its own; those are no export stamps
    walk({k: v for k, v in doc.items() if k != "inputs"})
    return seen


def _shown(path: str) -> str:
    return path.removeprefix("mechanical.")


def _post_spend_lines(post: PostSpend) -> list[str]:
    """The ``POST_SPEND`` block: each refusal with its message, what the synthesis decides, and
    the date the freshness verdict was measured at."""
    lines = [f"POST-SPEND REFUSALS — the paid build makes these only after its LLM calls; decided "
             f"here at $0 ({len(post.refusals)}):"]
    lines += [f"  {r.check} · {r.error}: {r.message}" for r in post.refusals]
    lines += [f"  decided by the paid draw, not a stop: {r.check} · {r.error}: {r.message} — the "
              "paid build refuses this after spending unless its synthesis states it"
              for r in post.undecided]
    if post.age is None:
        lines.append("  freshness: no dated export panel in this build")
    else:
        due = dt.date.fromisoformat(post.age.oldest) + dt.timedelta(days=MAX_PANEL_AGE_DAYS + 1)
        lines.append(f"  freshness measured at this build's date: {post.age.note()}; a build on "
                     f"or after {due.isoformat()} is refused on it (ceiling {MAX_PANEL_AGE_DAYS}d)")
    return lines


def _verdict(regressions: int | None, refusals: int, result: Comparison | None = None) -> str:
    """The last line. ``regressions`` is None on a first assembly: nothing was compared. It says
    what was compared and what moved (RD-D4) — never that nothing was lost."""
    head = ("no committed page to compare" if regressions is None
            else f"{regressions} regression(s)" if regressions else "0 regressions")
    moved = ("" if result is None else
             f"; {len(result.changed)} field(s) present on both change value, source or note, "
             f"{len(result.in_blocks)} block leaf(ves) change, and {len(result.left)} "
             "list-member field(s) left their list — listed above, not a stop")
    if not (regressions or refusals):
        return (f"=== {head} · 0 post-spend refusals — no field present on the committed page, "
                "outside a list or inside one, reads worse at $0, and no refusal the paid build "
                f"makes after its LLM calls fires{moved} ==="
                if regressions is not None else
                f"=== {head} · 0 post-spend refusals — no refusal the paid build makes after its "
                "LLM calls fires ===")
    why = ("the paid build would pay for its LLM calls and then refuse" if refusals else
           "the paid build would publish the regressions")
    if refusals and regressions:
        why += ", and once the refusal is cleared it would publish the regressions"
    return (f"=== {head} · {refusals} post-spend refusal(s) — STOP: {why}; the operator decides "
            f"before any spend{moved} ===")


def report(ticker: str, committed: Mapping[str, Any] | None, fresh: Mapping[str, Any],
           result: Comparison | None, exports: list[tuple[str, str | None]],
           post: PostSpend) -> list[str]:
    """The printed check: its boundary, then every regression with its note, then every gain, then
    the post-spend refusals. ``committed`` and ``result`` are None on a first assembly."""
    on_disk = {sha for _, sha in exports if sha}
    lines = [
        f"=== pre-spend check · {ticker} · $0: mechanical layer only, nothing written to "
        "data/dossiers ===",
        f"committed page: assembled {committed.get('assembled_at')} · extraction "
        f"{committed.get('extraction_version')} · reference {committed.get('reference_date')}"
        if committed is not None else
        "committed page: none — a first assembly, so no field is compared; the post-spend "
        "refusals still run",
        f"this build:     assembled {fresh.get('assembled_at')} · extraction "
        f"{fresh.get('extraction_version')} · reference {fresh.get('reference_date')}",
        f"exports on disk ({len(exports)}, sha256[:10]): "
        + ("; ".join(f"{kind} {sha or 'UNREADABLE'}" for kind, sha in exports) or "none"),
    ]
    if committed is not None and result is not None:
        stamps = _stamps(committed)
        lines += [
            "the committed page's export stamps: "
            + ("; ".join(f"{sha} ×{n} ({'on disk' if sha in on_disk else 'NOT on disk'})"
                         for sha, n in sorted(stamps.items())) or "none"),
            f"compared: {result.compared} Sourced field(s) outside lists, and every one inside "
            f"a list ({result.in_lists[0]} on the committed page, {result.in_lists[1]} in this "
            f"build), each with the same list member's (matched by identity), by presence AND "
            f"value; + {len(BLOCKS)} block(s) by presence, and leaf by leaf where both pages "
            f"carry one; not compared: "
            f"{len(result.undecided)} the paid draw decides, and the {len(LLM_WRITTEN)} "
            "LLM-written field(s) by value",
        ]
        for path, why in result.undecided:
            lines.append(f"  decided by the paid draw, not compared: {_shown(path)} — {why}")
        lines.append(f"REGRESSIONS — present on the committed page, not in this build "
                     f"({len(result.regressions)}):")
        for m in result.regressions:
            what = "block" if m.path in BLOCKS else "field"
            lines.append(f"  {_shown(m.path)}: {m.before} → {m.after}")
            lines.append(f"      note: {m.note or f'(none — this build carries no such {what})'}")
        lines.append(f"MOVED TO A DATED PART — left the current drawdown window, and a dated "
                     f"part of this build carries the same event ({len(result.moved)}):")
        for m in result.moved:
            lines.append(f"  {_shown(m.path)}: {m.before} → {m.after}")
            lines.append(f"      {m.note}")
        lines.append(f"NEWLY PRESENT — not present on the committed page, present in this build "
                     f"({len(result.gained)}):")
        lines += [f"  {_shown(m.path)}: {m.before} → {m.after}" for m in result.gained]
        lines.append(f"LEFT THEIR LIST — present fields of a list member the committed page holds "
                     f"and this build does not; a list's population moves with the calendar, so "
                     f"listed, not a stop ({len(result.left)}):")
        lines += [f"  {_shown(m.path)}: {m.before} → {m.after}" for m in result.left]
        lines.append(f"CHANGED IN A BLOCK — a leaf of a block both pages carry differs; listed, "
                     f"not a stop ({len(result.in_blocks)}):")
        for block in BLOCKS:
            rows = [m for m in result.in_blocks if m.path.split(".")[0].split("[")[0] == block]
            if not rows:
                continue
            cut = (f" — showing {BLOCK_SHOWN} of {len(rows)}; every one: --changes-json"
                   if len(rows) > BLOCK_SHOWN else "")
            lines.append(f"  {block}: {len(rows)} leaf change(s){cut}")
            lines += [f"    {m.path}: {m.before} → {m.after}" for m in rows[:BLOCK_SHOWN]]
        lines.append(f"CHANGED — present on both, the value, its source or its note differs; "
                     f"listed, not a stop ({len(result.changed)}):")
        for v in result.changed:
            lines.append(f"  {_shown(v.path)} [{', '.join(v.parts)}]: {v.before} → {v.after}")
            if v.source_before != v.source_after:
                lines.append(f"      source: {v.source_before} → {v.source_after}")
    lines += _post_spend_lines(post)
    lines.append(_verdict(len(result.regressions) if result is not None else None,
                          len(post.refusals), result))
    return lines


def write_changes(result: Comparison, path: Path) -> None:
    """Every comparison row as its own JSON file (the precheck's ``--changes-json``) — never a
    page, as `inputs.write_json` is not."""
    path.write_text(json.dumps(asdict(result), indent=1, default=str), encoding="utf-8")


def run(ticker: str, cfg: Config, *, emit: Callable[[str], None] = print,
        inputs_json: Path | None = None, changes_json: Path | None = None) -> int:
    """The check for one name: 0 when nothing present on the committed page is lost and no
    ``POST_SPEND`` refusal fires, else 1. With no committed page only the refusals are checked.
    ``inputs_json``: where to write this build's input record in full (`vinci.dossier.inputs`)."""
    from vinci.dossier.assemble import DossierAssemblyError
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.ciq_sheets import file_provenance
    from vinci.dossier.manual_store import LocalFolderStore
    from vinci.netcache import SecRateLimitedError
    from vinci.sec import build_sec_http

    t = ticker.upper()
    path = cfg.data_dir / "dossiers" / t / "dossier.json"
    committed = json.loads(path.read_text()) if path.exists() else None
    # every read this check makes — the $0 build's (its own recorder is nested in this one) and
    # the forecast's exhibit fetches, which the paid build makes inside its covenant phase
    with provenance.recording() as reads:
        try:
            built = mechanical_build(t, cfg)
            # the forecast feeds only the comparison, so a first assembly does not fetch its
            # exhibits
            forecast = (forecast_llm_fields(built, http=build_sec_http(cfg))
                        if committed is not None else None)
        except (DossierAssemblyError, SecRateLimitedError, LookupError) as exc:
            emit(f"=== pre-spend check · {t}: the $0 build was REFUSED — the paid build stops at "
                 f"the same point — {type(exc).__name__}: {exc} ===")
            return 1
    fresh = json.loads(dossier_json(built))
    bundle = CiqBundle.from_files(t, LocalFolderStore.from_config(cfg).files(t))
    exports = [(wb.kind + (f"/{wb.freq}" if wb.freq else ""), file_provenance(wb.path)[0])
               for wb in bundle.workbooks]
    post = post_spend_checks(built, bundle, committed=path.parent)
    result = compare(committed, fresh, forecast) if committed is not None else None
    present = page_inputs.manifest_for(reads.reads(), db_path=cfg.db_path,
                                       extraction_version=built.extraction_version or "",
                                       facts_base=cfg.data_dir / "facts")
    recorded = (page_inputs.InputManifest.model_validate(committed["inputs"])
                if committed is not None and committed.get("inputs") else None)
    lines = report(t, committed, fresh, result, exports, post)
    # the INPUTS block sits before the verdict, which stays the last line
    for line in [*lines[:-1], *page_inputs.summary_lines(present, recorded), lines[-1]]:
        emit(line)
    if inputs_json is not None:
        page_inputs.write_json(present, inputs_json)
        emit(f"input record written to {inputs_json}")
    if changes_json is not None and result is None:
        emit(f"no committed page, so no comparison: nothing written to {changes_json}")
    elif changes_json is not None and result is not None:
        write_changes(result, changes_json)
        emit(f"every comparison row written to {changes_json}")
    return 1 if post.refusals or (result is not None and result.regressions) else 0
