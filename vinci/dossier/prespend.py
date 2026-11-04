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
"""

from __future__ import annotations

import datetime as dt
import json
import tempfile
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from vinci.config import Config
from vinci.dossier.freshness import MAX_PANEL_AGE_DAYS, PanelAge, panel_age
from vinci.dossier.schemas import Dossier, MechanicalLayer, SourceStatus, dossier_json
from vinci.graph.llm import LlmClient, LlmError

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
class Comparison:
    regressions: tuple[Move, ...]
    gained: tuple[Move, ...]
    undecided: tuple[tuple[str, str], ...]
    #: Sourced fields compared: the union of both pages' outermost fields outside lists, minus the
    #: undecided ones.
    compared: int
    #: Sourced fields inside lists, (committed, this build): NOT compared — a list's population
    #: moves with the calendar, so position is not identity.
    in_lists: tuple[int, int]


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
    return Comparison(tuple(regressions), tuple(gained), tuple(undecided), len(compared),
                      (n_before, n_after))


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
    """Every export sha256 the page stamps (any key ending ``sha256``), with how often."""
    seen: Counter[str] = Counter()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if str(key).endswith("sha256") and isinstance(child, str):
                    seen[child] += 1
                else:
                    walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(doc)
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


def _verdict(regressions: int | None, refusals: int) -> str:
    """The last line. ``regressions`` is None on a first assembly: nothing was compared."""
    head = ("no committed page to compare" if regressions is None
            else f"{regressions} regression(s)" if regressions else "0 regressions")
    if not (regressions or refusals):
        return (f"=== {head} · 0 post-spend refusals — nothing present on the committed page is "
                "lost at $0, and no refusal the paid build makes after its LLM calls fires ==="
                if regressions is not None else
                f"=== {head} · 0 post-spend refusals — no refusal the paid build makes after its "
                "LLM calls fires ===")
    why = ("the paid build would pay for its LLM calls and then refuse" if refusals else
           "the paid build would publish the regressions")
    if refusals and regressions:
        why += ", and once the refusal is cleared it would publish the regressions"
    return (f"=== {head} · {refusals} post-spend refusal(s) — STOP: {why}; the operator decides "
            "before any spend ===")


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
            f"compared: {result.compared} Sourced field(s) (outermost, outside lists) + "
            f"{len(BLOCKS)} block(s); not compared: {result.in_lists[0]} on the committed "
            f"page and {result.in_lists[1]} in this build inside lists, and "
            f"{len(result.undecided)} the paid draw decides",
        ]
        for path, why in result.undecided:
            lines.append(f"  decided by the paid draw, not compared: {_shown(path)} — {why}")
        lines.append(f"REGRESSIONS — present on the committed page, not in this build "
                     f"({len(result.regressions)}):")
        for m in result.regressions:
            what = "block" if m.path in BLOCKS else "field"
            lines.append(f"  {_shown(m.path)}: {m.before} → {m.after}")
            lines.append(f"      note: {m.note or f'(none — this build carries no such {what})'}")
        lines.append(f"NEWLY PRESENT — not present on the committed page, present in this build "
                     f"({len(result.gained)}):")
        lines += [f"  {_shown(m.path)}: {m.before} → {m.after}" for m in result.gained]
    lines += _post_spend_lines(post)
    lines.append(_verdict(len(result.regressions) if result is not None else None,
                          len(post.refusals)))
    return lines


def run(ticker: str, cfg: Config, *, emit: Callable[[str], None] = print) -> int:
    """The check for one name: 0 when nothing present on the committed page is lost and no
    ``POST_SPEND`` refusal fires, else 1. With no committed page only the refusals are checked."""
    from vinci.dossier.assemble import DossierAssemblyError
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.ciq_sheets import file_provenance
    from vinci.dossier.manual_store import LocalFolderStore
    from vinci.netcache import SecRateLimitedError
    from vinci.sec import build_sec_http

    t = ticker.upper()
    path = cfg.data_dir / "dossiers" / t / "dossier.json"
    committed = json.loads(path.read_text()) if path.exists() else None
    try:
        built = mechanical_build(t, cfg)
        # the forecast feeds only the comparison, so a first assembly does not fetch its exhibits
        forecast = (forecast_llm_fields(built, http=build_sec_http(cfg))
                    if committed is not None else None)
    except (DossierAssemblyError, SecRateLimitedError, LookupError) as exc:
        emit(f"=== pre-spend check · {t}: the $0 build was REFUSED — the paid build stops at the "
             f"same point — {type(exc).__name__}: {exc} ===")
        return 1
    fresh = json.loads(dossier_json(built))
    bundle = CiqBundle.from_files(t, LocalFolderStore.from_config(cfg).files(t))
    exports = [(wb.kind + (f"/{wb.freq}" if wb.freq else ""), file_provenance(wb.path)[0])
               for wb in bundle.workbooks]
    post = post_spend_checks(built, bundle, committed=path.parent)
    result = compare(committed, fresh, forecast) if committed is not None else None
    for line in report(t, committed, fresh, result, exports, post):
        emit(line)
    return 1 if post.refusals or (result is not None and result.regressions) else 0
