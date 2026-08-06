"""Orchestrate per-finalist dossier assembly — PARALLEL across the cohort, fail-loud per name.

Parallel assembly is the AI-native leverage: the ~10/week the ranked queue surfaces are independent,
so they assemble concurrently (I/O-bound on EDGAR/LLM). Each name opens its own store + EDGAR
clients (SQLite/HTTP aren't safely shared across threads); the resolver index and graph are shared
read-only. A name whose CIQ export is missing still produces a dossier (CIQ sections MISSING + a
'pull CIQ' flag); any other per-name failure becomes an error and the batch continues — fail-loud.
"""

from __future__ import annotations

import json
import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, TypeVar

from vinci.config import Config, get_config
from vinci.dossier import ciq_sheets, requirements
from vinci.dossier import flags as dossier_flags
from vinci.dossier.anchor import RECIPE_UNKNOWN, Anchor, compute_anchor
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.covenant_extract import (
    covenant_digest,
    extract_covenant_terms,
    extract_maturity_event,
    governing_terms,
)
from vinci.dossier.driver_extract import extract_transcript_drivers
from vinci.dossier.extraction_version import EXTRACTION_VERSION
from vinci.dossier.manual_store import LocalFolderStore, ManualDataStore
from vinci.dossier.mechanical import assemble_mechanical
from vinci.dossier.render import render_markdown
from vinci.dossier.schemas import Dossier, Sourced, SourceStatus
from vinci.dossier.synthesis import (
    contradiction_flags,
    synthesize,
    uncited_material_figures,
)
from vinci.edgar.client import EdgarClient
from vinci.finra import build_finra_http
from vinci.graph.exposure import ExposureGraph
from vinci.graph.llm import LlmClient
from vinci.labels import resolve_label
from vinci.rank import load_candidates_from_snapshot
from vinci.resolver import EntityResolver
from vinci.schemas.candidate import CandidateRecord
from vinci.schemas.data_record import DataRecord
from vinci.sec import build_sec_http
from vinci.store import Store

_S = TypeVar("_S")


class DossierAssemblyError(RuntimeError):
    """A build that cannot honestly be written. Raised per name; ``assemble_cohort`` collects it as
    an ERROR so the CLI's `N done · M error(s)` line counts it — a failure that writes an artifact
    and reports success is the shape this exists to prevent."""


@dataclass(frozen=True)
class Finalist:
    """A ranked-queue finalist: the screen record, its queue rank, the as-of reference date, and
    the ranker's frozen screen-time market cap (USD) — the benchmark-band fallback the dossier uses
    when the CIQ cap is absent, so re-assembly can't silently reselect the index (the MDY→IWM
    drift)."""

    record: CandidateRecord | None
    rank: int | None
    reference_date: date
    market_cap_screen: float | None = None
    #: THE MAINTENANCE PATH. Set when the name has NO current candidate record — a data record
    #: built from the resolver + the price store, never a hand-made `CandidateRecord` (that type
    #: means "screen-admitted", and forging one would put a fabricated screen verdict under a name
    #: about to be underwritten). Exactly one of `record`/`standalone` is set.
    standalone: DataRecord | None = None
    #: Why this name is outside the current candidate set, rendered as a MAIN-BODY caveat. None
    #: for an ordinary screen candidate.
    screen_status: str | None = None

    @property
    def data_record(self) -> DataRecord:
        """The facts assembly reads, whichever route supplied them."""
        if self.record is not None:
            return self.record.data_record
        if self.standalone is None:
            raise DossierAssemblyError(
                "Finalist has neither a candidate record nor a standalone data record — there is "
                "nothing to assemble from")
        return self.standalone


def _ref_of(row: dict[str, Any]) -> date:
    sra = row.get("screen_run_at")
    return date.fromisoformat(str(sra)[:10]) if sra else date.today()


def _cap_of(row: dict[str, Any]) -> float | None:
    """The ranked-queue row's screen-time EOD×XBRL market cap (USD), or None if it isn't a finite
    positive number — a bool (``isinstance(True, int)``), ``inf``/``nan``, or ≤0 is not a real cap
    and must never band a benchmark (fail to the CIQ/IWM path, never fabricate a band from junk)."""
    v = row.get("market_cap")
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return float(v) if math.isfinite(v) and v > 0 else None


def _last_screen_verdict(cfg: Config, ticker: str) -> tuple[str, str] | None:
    """The newest screen run that actually EVALUATED ``ticker`` → (run_id, one-line outcome).

    GROWN OUT AND FAILED MUST NEVER RENDER ALIKE. IT passed all three gates on 2026-07-29 and then
    appreciated past the $10bn ceiling; a page that showed that the way it shows a rejection would
    be the `unstated`-versus-`disagrees` mistake with a position on the other side of it. So this
    reports the LAST REAL VERDICT and its gates — never the mere fact of absence, which is what a
    caller would otherwise be left to infer.

    Runs are scanned newest-first and the first one CARRYING THE TICKER wins: a later run that
    never evaluated the name says nothing about it, and treating its silence as a verdict is the
    same error one level up.
    """
    runs = sorted((cfg.snapshots_dir / "screen_runs").glob("*.jsonl"), reverse=True)
    for path in runs:
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("ticker") != ticker or row.get("grain") != "candidate":
                continue
            gates = row.get("per_gate") or {}
            detail = " · ".join(
                f"{g} {(v or {}).get('outcome')}" for g, v in sorted(gates.items())) or "no gates"
            return str(row.get("run_id")), f"{row.get('outcome')} ({detail})"
    return None


def _maintenance_reason(cfg: Config, ticker: str) -> str | None:
    """Why this name is still MAINTAINED though it is not a current screen candidate — or None.

    THE BAND ANSWERS WHERE WE HUNT, NOT WHAT WE MAY HOLD OR FOLLOW. Screen membership is an ENTRY
    rule; a name we already carry a dossier or an underwrite on must stay refreshable or any
    position that re-rates upward becomes un-maintainable — the defect bites a WINNER first.
    """
    if (cfg.data_dir / "dossiers" / ticker / "dossier.json").exists():
        return "a committed dossier"
    if _read_scenario_card(ticker) is not None:
        return "an open underwrite record"
    return None


def _standalone_record(cfg: Config, ticker: str, reference_date: date) -> DataRecord:
    """Build ``ticker``'s data record from the resolver + the price store, with no screen involved.

    Uses ``build_data_record`` — the SAME constructor the screen's own path composes
    (``build_price_record`` → ``enrich_with_fundamentals``), so a maintained name's facts are
    assembled by one definition, not a second copy that can drift from it.
    """
    from vinci.monitor import BENCHMARK_SMALL
    from vinci.screens import build_data_record
    from vinci.universe import benchmark_identity

    resolver = EntityResolver.from_config(cfg)
    identity = resolver.resolve_ticker(ticker)
    # The SCREEN's own default benchmark, so `rel_ret_vs_market` on this record means what it
    # means on every candidate record. The dossier re-picks its cap-band benchmark downstream;
    # this is the record-level input, not the page's comparison.
    bench = benchmark_identity(BENCHMARK_SMALL)
    with Store(cfg.db_path) as store:
        bars = store.get_price_history(identity.internal_id)
        bench_bars = store.get_price_history(bench.internal_id)
    # TRUNCATE TO THE REFERENCE DATE — `compute_price_features` takes `bars[-1]` as "latest" and
    # never filters; it uses `reference_date` only for staleness and window starts. The screen gets
    # away with passing full history because at screen time the store frontier IS the reference
    # date. Here it is not: IT's record would otherwise carry the 2026-08-04 close ($185.79) under
    # a 2026-07-06 stamp — a record whose own vintage mark contradicts its value. Truncating makes
    # a maintained name's record mean exactly what a candidate record at the same reference date
    # means, which is the only way the two are comparable.
    bars = [b for b in bars if b.bar_date <= reference_date]
    bench_bars = [b for b in bench_bars if b.bar_date <= reference_date]
    if not bars:
        raise DossierAssemblyError(
            f"{ticker}: no price history in the store — a maintained name still needs bars to "
            f"build a data record; refresh EOD before re-assembling")
    return build_data_record(
        identity, price_bars=bars, benchmark_bars=bench_bars,
        edgar=EdgarClient.from_config(cfg), reference_date=reference_date,
        staleness_days=cfg.price_staleness_days)


def _finalist(
    cfg: Config, ticker: str, rec: CandidateRecord | None, row: dict[str, Any] | None
) -> Finalist | None:
    """One Finalist by either route, or None when the name is neither a candidate nor maintained.

    ONE construction for BOTH callers. `--ticker` and the cohort loop reached the same decision by
    two copies, and the first cut of this path only taught the `--ticker` one: `--ticker IT`
    assembled while `--top 20` silently dropped IT at rank 5 — the name the path exists for. A
    half-fix is worse than the symmetric failure it replaced, because it looks like it works.
    """
    ref = _ref_of(row or {})
    rank = int(row["rank"]) if row and row.get("rank") is not None else None
    cap = _cap_of(row) if row else None
    if rec is not None:
        return Finalist(rec, rank, ref, cap)
    # THE MAINTENANCE PATH. Not a candidate today — but the band is an ENTRY rule, and a name we
    # already hold a dossier or an underwrite on has to stay refreshable.
    why = _maintenance_reason(cfg, ticker)
    if why is None:
        return None
    verdict = _last_screen_verdict(cfg, ticker)
    said = (f"last evaluated {verdict[0]}: {verdict[1]}" if verdict
            else "no screen run on file has evaluated it")
    return Finalist(
        None, rank, ref, cap,
        standalone=_standalone_record(cfg, ticker, ref),
        screen_status=(
            f"NOT A CURRENT SCREEN CANDIDATE — assembled because the name carries {why}. The cap "
            f"band decides where the fund HUNTS, not what it may hold or follow, so absence from "
            f"it is not a rejection — read the verdict, not the absence: {said}."))


def load_finalists(
    cfg: Config, *, top: int | None = None, ticker: str | None = None
) -> list[Finalist]:
    """Join the ranked-queue order (top N) to candidate-records facts. ``--ticker`` picks one."""
    snaps = cfg.snapshots_dir
    cands = load_candidates_from_snapshot(snaps / "candidate_records.jsonl")
    by_cid = {c.candidate_id: c for c in cands}
    by_ticker = {c.data_record.identity.ticker: c for c in cands}
    queue_path = snaps / "ranked_queue.jsonl"
    queue: list[dict[str, Any]] = (
        [json.loads(line) for line in queue_path.read_text().splitlines() if line.strip()]
        if queue_path.exists()
        else []
    )
    queue.sort(key=lambda r: int(r.get("rank", 1_000_000)))

    if ticker:
        t = ticker.upper()
        row = next((r for r in queue if r.get("ticker") == t), None)
        rec = by_ticker.get(t) or (by_cid.get(str(row["candidate_id"])) if row else None)
        fin = _finalist(cfg, t, rec, row)
        if fin is None:
            raise LookupError(
                f"{t} not in candidate_records.jsonl and not maintained (no committed dossier, "
                f"no underwrite record) — run screen then rank first")
        return [fin]

    out: list[Finalist] = []
    for r in queue[: top or len(queue)]:
        t = str(r.get("ticker"))
        rec = by_cid.get(str(r.get("candidate_id"))) or by_ticker.get(t)
        fin = _finalist(cfg, t, rec, r)
        if fin is not None:
            out.append(fin)
    return out


def _load_graph(cfg: Config) -> ExposureGraph:
    path = cfg.data_dir / "graph_coverage.json"
    edges = json.loads(path.read_text())["edges"] if path.exists() else []
    return ExposureGraph.from_edges(edges)


def _read_scenario_card(ticker: str) -> Any | None:
    """The committed underwrite record for ``ticker``, or None when the name is not underwritten.

    Imported HERE, not at module scope: ``vinci.scenarios`` imports ``vinci.dossier.midcycle``, so
    a top-level import would cycle. Read-only — the assembler never writes the record, and the
    dossier package still imports no ledger/scoring (the structural no-verdict line is untouched).

    FAIL-LOUD BOUNDARY: an ABSENT record is a normal state (most names are never underwritten) and
    degrades to None. A record that EXISTS but will not parse is not normal — swallowing it would
    ship a dossier.md silently missing its thesis and scenarios, with nothing anywhere saying so.
    That error propagates."""
    from vinci.scenarios import read_record
    try:
        return read_record(ticker)
    except FileNotFoundError:
        return None  # not underwritten — the majority case, not a failure


def _refuse_synthesis_overwrite(dossier: Dossier, folder: Path) -> None:
    """A write that would replace a COMMITTED synthesis with nothing is refused.

    GATED ON THE FILE, NOT THE MODE (operator, 2026-07-30). ``--no-llm`` on a fresh name is a
    legitimate declared mode with its own disclosure, and ``test_the_mechanical_only_mode_cannot_
    reach_the_guard`` exists to keep that working — so the precondition is NOT "an LLM was
    configured". It is **a committed file with a synthesis already exists**, which is the only
    situation where writing ``synthesis: null`` destroys something.

    The 07-22 accepted risk and the 07-30 AORT incident were both the CONFIGURED-client case, closed
    by ``_require_synthesis``. This closes the other door into the same room: the same artifact is
    destroyed just as completely by a mechanical-only re-run over a name that already had prose, and
    nothing stopped that until now. Use ``vinci.dossier.refresh`` to move mechanical numbers under a
    kept synthesis."""
    if dossier.synthesis is not None:
        return
    existing = folder / "dossier.json"
    if not existing.exists():
        return
    try:
        prior = json.loads(existing.read_text()).get("synthesis")
    except (OSError, ValueError):
        return  # an unreadable prior file is not evidence of a synthesis to protect
    if prior is None:
        return
    raise DossierAssemblyError(
        f"{dossier.ticker}: this build has NO synthesis and the committed dossier HAS one — "
        "writing would replace it with null, which is the 2026-07-30 AORT incident reached through "
        "the mechanical-only door instead of the flaky-call one. Re-run WITH a client, or use the "
        "mechanical-only refresh (vinci.dossier.refresh), which moves numbers under a kept "
        "synthesis and refuses per claim when the prose cites one that moved.")


def _write(dossier: Dossier, llm_log: str, out_root: Path) -> Path:
    folder = out_root / dossier.ticker
    _refuse_synthesis_overwrite(dossier, folder)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "dossier.json").write_text(dossier.model_dump_json(indent=2))
    (folder / "dossier.md").write_text(
        render_markdown(dossier, card=_read_scenario_card(dossier.ticker),
                        dossiers_root=folder.parent))
    (folder / "llm_call.log").write_text(llm_log or "(no LLM call — synthesis skipped)")
    return folder




# The brief's static row set is IMPORTED, never re-declared: the guard's satisfying set is
# CORE ∪ MATERIAL, so a drift between this and the renderer's own list would silently narrow what
# counts as "the reader met it". Review found three copies of this set; the repo's rule is that
# where a single import is possible it is used, and a pin is only for the py↔JS leftover.


def _mark_material(mech: Any) -> Any:
    """Flag summary rows over the materiality floor so the BRIEF shows them (P1 brief fix)."""
    from vinci.dossier.materiality import mark_material_rows

    fs = getattr(mech, "financial_summary", None)
    ann = getattr(fs, "annual", None) if fs else None
    tbl = getattr(ann, "value", None) if ann is not None else None
    if tbl is None or fs is None or ann is None:
        return mech
    si = getattr(mech, "stock_info", None)
    mcap = getattr(getattr(si, "market_cap", None), "value", None) if si else None
    marked = mark_material_rows(tbl, market_cap=mcap, revenue=None)
    if marked is tbl:
        return mech
    return mech.model_copy(update={
        "financial_summary": fs.model_copy(update={
            "annual": ann.model_copy(update={"value": marked})})})

def _freshness_check(mech: Any, *, ticker: str, built_at: date) -> None:
    """(item 1) FAIL LOUD on a build whose dated inputs cannot honestly sit on one page: a panel
    older than the ceiling, or a market cap whose share basis disagrees with the price's.

    ``built_at`` IS THE DATE THIS BUILD RAN — the same instant that becomes ``assembled_at``, and
    NOT the screen's ``reference_date``. The first cut used ``reference_date`` and it was wrong in
    a way that defeated the guard: the screen's as-of is weeks behind the build (2026-07-06 against
    a 07-29 run), so the gate measured a 23-day-shorter age than the page it was guarding. CNXC
    passed at 31d and RENDERED "oldest panel 54d old"; NCNO's gate age came out at **−6 days**,
    because its panel postdates the screen. A guard that can return a negative age is not measuring
    anything, and a page stating a number its own guard never applied is the stamp-names-a-different
    -object defect this contract exists to remove.

    The render measures against ``assembled_at`` (a committed artifact reports the age it had when
    built). Passing the same instant here is what makes the two agree BY CONSTRUCTION rather than
    by coincidence.

    Ordinary drift is deliberately NOT fatal — it is a RENDERING obligation (clause (e)), and the
    cap now carries its own vintage on both twins. Failing on drift would fail 11 of 11 committed
    dossiers, which is a freeze wearing a guard's name."""
    from vinci.dossier.freshness import (
        absent_cap_inputs,
        check_freshness,
        panel_age,
        reconcile_cap,
    )

    si = getattr(mech, "stock_info", None)

    def val(k: str) -> float | None:
        v = getattr(getattr(si, k, None), "value", None) if si is not None else None
        return float(v) if isinstance(v, (int, float)) else None

    cap, shares, spot = val("market_cap"), val("shares_out"), val("price")
    recon = reconcile_cap(cap_musd=cap, shares=shares, spot=spot)
    # EXPORT age only (staleness split, 2026-07-30). Consensus staleness is the street's, not ours
    # — no re-export moves it — so it prints and caveats instead of gating. AORT is the live case:
    # its Estimates workbook was re-exported 2026-07-30 and still reads 2026-06-30.
    dumped = mech.model_dump(mode="json")
    check_freshness(panel_age(dumped, built_at, kind="export"), recon,
                    ticker=ticker,
                    absent=absent_cap_inputs(cap_musd=cap, shares=shares, spot=spot))


def _materiality_check(bundle: Any, mech: Any, synthesis: Any, *, ticker: str) -> None:
    """Run the materiality guard on the assembled record (P1). Skips silently ONLY when a
    denominator or the sheet is genuinely unavailable — never when the check merely found nothing,
    which is the distinction between "clean" and "not looked at"."""
    from vinci.dossier import ciq_sheets as _cs
    from vinci.dossier.materiality import (
        MaterialityUnavailableError,
        check_materiality,
    )

    try:
        inc = bundle.sheet("financials", "Income Statement", freq="annual")
    except Exception:
        return                                   # no sheet — its own fail-loud lives upstream
    hdr = _cs._period_header(inc)
    if hdr is None:
        return
    periods = _cs._fin_periods(inc[hdr])
    if not periods:
        return
    ltm = [pp for pp in periods if pp[2]]
    col, label = (ltm[0][0], ltm[0][1]) if ltm else (periods[-1][0], periods[-1][1])
    si = getattr(mech, "stock_info", None)
    mcap = getattr(getattr(si, "market_cap", None), "value", None) if si else None
    fs = getattr(mech, "financial_summary", None)
    ann = getattr(getattr(fs, "annual", None), "value", None) if fs else None
    # (P1 brief fix) The guard's target surface is the BRIEF, not the appendix. `material=True`
    # rows are the ones the brief now shows in addition to its static whitelist, so the satisfying
    # label set is CORE ∪ MATERIAL — an appendix-only row no longer silences the guard.
    from vinci.dossier.render import BRIEF_CORE_ROWS

    rows = list(getattr(ann, "rows", [])) if ann is not None else []
    labels = {r.label for r in rows
              if r.label in BRIEF_CORE_ROWS or getattr(r, "material", False)}
    try:
        check_materiality(
            inc, col, market_cap=mcap, revenue=None, summary_labels=labels,
            synthesis_text=json.dumps(synthesis.model_dump(mode="json")) if synthesis else "",
            ticker=ticker, period=label,
        )
    except MaterialityUnavailableError:
        return                                   # no unusual-items block on this sheet


def _require_synthesis(synthesis: _S | None, *, ticker: str, flags: list[str]) -> _S:
    """REFUSE a build whose configured LLM produced no synthesis. Called from inside the
    ``llm is not None`` branch, so the mechanical-only mode never reaches it.

    Recorded 2026-07-22 as an ACCEPTED RISK (BRBR's synthesis wiped by one flaky call). It fired on
    2026-07-30 and destroyed AORT's: the run printed ``1 done · 0 error(s)`` and wrote
    ``synthesis: null`` over it — the write happened AND was not reported as an error. The only
    signal was the word ``NO-synth`` in a summary line, which is the weakness the 07-22 record
    itself names. Acceptance predated any evidence it fires; it has now fired twice.

    VERIFIED there is no legitimate None: ``synthesize`` returns None on exactly two paths — an
    ``LlmError`` and a truncated/incomplete tool result — both failures. So refusing on None
    cannot break a supported build.

    Keys on the VALUE being absent, never on a flag's wording — the 07-22 guard pinned that a flag
    is emitted and the artifact was destroyed anyway. A named function rather than an inline raise
    so the refusal carries a behavioural pin instead of a source-text assertion."""
    if synthesis is not None:
        return synthesis          # RETURNS the validated value, so callers narrow through it
    raise DossierAssemblyError(
        f"{ticker}: synthesis returned NOTHING from a configured LLM client — refusing to write. "
        "Writing here replaces a committed synthesis with null and reports success; that is how "
        "AORT's synthesis was destroyed on 2026-07-30. Re-run when the model is answering. "
        f"Flags: {'; '.join(flags) or '(none)'}")


def assemble_one(
    fin: Finalist,
    *,
    cfg: Config,
    resolver: EntityResolver,
    graph: ExposureGraph,
    manual: ManualDataStore,
    out_root: Path,
    llm: LlmClient | None,
) -> Dossier:
    """Assemble + persist one finalist's dossier. Opens its own store/edgar (thread-safe)."""
    # THE BUILD'S OWN INSTANT, taken ONCE and used for BOTH the freshness gate and the artifact's
    # ``assembled_at``. Stamping it twice (a second ``datetime.now()`` at write time) would let the
    # guard and the artifact disagree about when the build ran — a small window, but this contract
    # exists so that the number a page reports is the number its own guard applied.
    built_at = datetime.now(UTC)
    rec = fin.data_record
    ticker = rec.identity.ticker
    bundle = CiqBundle.from_files(ticker, manual.files(ticker))
    location = manual.location(ticker)
    # MISSING-manifest: per-module 'pull CIQ' flags from the ONE requirements definition (so this
    # and `vinci dossier requirements` can't drift). Empty/partial folder → what's still owed.
    flags: list[str] = requirements.manifest_flags(bundle, ticker=ticker, location=location)
    with Store(cfg.db_path) as store:
        mech, mech_flags = assemble_mechanical(
            rec, store=store, edgar=EdgarClient.from_config(cfg), http=build_sec_http(cfg),
            finra=build_finra_http(cfg), graph=graph, resolver=resolver, bundle=bundle,
            reference_date=fin.reference_date, screen_cap_usd=fin.market_cap_screen,
            # (item 18) the underwrite record, so a field about to render UNKNOWN can first be
            # checked against what the fund already holds. Read-only, and the SAME reader the
            # renderer already uses — one definition of "the record", not two.
            card=_read_scenario_card(ticker),
        )
    flags += mech_flags
    # (PR-B §3-now) transcript slice computed ONCE here so a fail-loud flag fires whether or not
    # the LLM runs — transcripts on file that don't parse (no LibreOffice) never vanish silently.
    transcript = ciq_sheets.transcript_for_synthesis(bundle)
    unparsed = ciq_sheets.unparsed_transcript_flag(bundle, transcript)
    if unparsed is not None:
        flags.append(unparsed)
    synthesis = None
    logs: list[str] = []
    term_rows = None  # (E5) per-exhibit rows — attached to mech AFTER synthesis (render only)
    if llm is not None:
        # (P1/FIX-0) Tier-2 covenant + maturity extraction runs BEFORE synthesis so the LLM reasons
        # with the ACTUAL governing terms via a term→value digest — never a pointer to unseen data.
        # (P3) the maturity-resolution event is extracted here too and fed to synthesis + the wall.
        if mech.capital_structure is not None:
            http = build_sec_http(cfg)
            cik0 = rec.identity.cik or ""
            term_rows, _sum, cov_flags, cov_log = extract_covenant_terms(
                mech.capital_structure, llm=llm, http=http, cik=cik0, ticker=ticker,
                name=rec.identity.name)
            maturity_event, mat_flags, mat_log = extract_maturity_event(
                mech.capital_structure, llm=llm, http=http, cik=cik0, ticker=ticker,
                name=rec.identity.name)
            flags += cov_flags + mat_flags
            logs += [lg for lg in (cov_log, mat_log) if lg]
            ptrs = mech.capital_structure.covenant_pointer_rows
            gov = (governing_terms(term_rows.value or [], ptrs.value)
                   if term_rows is not None and ptrs is not None and ptrs.value else [])
            # (CC-1) `gov` is non-empty even when every term is UNKNOWN (governing_terms emits one
            # row per (family, term)); base the honest-failure reason on an actually-PRESENT term,
            # so an all-UNKNOWN extraction yields the honest "extraction failed" digest, not a bare
            # header.
            gov_present = any(g.value.status is SourceStatus.PRESENT for g in gov)
            mat_present = (maturity_event is not None
                           and maturity_event.status is SourceStatus.PRESENT)
            fail = (None if (gov_present or mat_present)
                    else "no covenant terms extracted from located exhibits")
            digest = covenant_digest(gov, maturity_event, fail_reason=fail)
            cs_pre = mech.capital_structure.model_copy(update={
                "covenant_terms": Sourced.present(digest, source_ref="fenced Tier-2 digest (P1)"),
                "maturity_event": maturity_event})
            mech = mech.model_copy(update={"capital_structure": cs_pre})
        # (PR-B Tier B) LLM-fenced operating-driver extraction over the transcript slice — runs
        # BEFORE synthesis so the extracted, validated rows are in mech.operating_drivers when the
        # synthesis LLM reads it (each row quote-in-slice + digit-traced or dropped). Merged onto
        # the anchored A1/A2/A3 rows the mechanical layer already built.
        if transcript and mech.operating_drivers is not None:
            tb_rows, tb_flags, tb_log = extract_transcript_drivers(
                transcript, llm=llm, ticker=ticker, name=rec.identity.name)
            flags += tb_flags
            if tb_log:
                logs.append(f"=== TIER-B DRIVER EXTRACT: {ticker} ===\n{tb_log}")
            if tb_rows:
                od = mech.operating_drivers
                merged = od.model_copy(update={"rows": [*od.rows, *tb_rows]})
                mech = mech.model_copy(update={"operating_drivers": merged})
        synthesis, synth_flags, synth_log = synthesize(
            mech, llm=llm, ticker=ticker, name=rec.identity.name, transcript=transcript,
        )
        flags += synth_flags
        logs.append(synth_log)
        # A null synthesis from a CONFIGURED client is a failed build — refuse the write BEFORE
        # `_write` below. Rationale and the 07-22/07-30 incidents: `_require_synthesis`.
        synthesis = _require_synthesis(synthesis, ticker=ticker, flags=synth_flags)
        # (render) attach the structured per-exhibit rows AFTER synthesis (the LLM used the digest).
        if term_rows is not None and mech.capital_structure is not None:
            cs_post = mech.capital_structure.model_copy(update={"covenant_term_rows": term_rows})
            mech = mech.model_copy(update={"capital_structure": cs_post})
        # (P1, IC audit 2026-07-28) MATERIALITY GUARD — a one-off too big to go unmentioned may
        # not reach the reader by no route at all. Runs AFTER synthesis because "mentioned in the
        # synthesis" is one of the two satisfying routes (the other is the financial summary, where
        # material unusual items now surface as data). Fail-loud: SMPL's -$391.9M LTM writedown was
        # 43% of market cap, absent from every tier, while the bear case argued from a figure 5.3x
        # smaller. A warning here would have been read past on exactly the day it mattered.
        mech = _mark_material(mech)          # flag rows over the floor BEFORE the guard reads them
        # (item 19c) A MATERIAL figure the synthesis prose never states — REFUSE, do not flag.
        # SMPL's bear case was right on 07-29 and wrong on 07-30 from identical inputs, so
        # synthesis correctness is STOCHASTIC and a flag would just move the judgement to a human
        # on every run. Refusing means the bad roll FAILS and is re-rolled; the good one ships.
        #
        # MOVED HERE 2026-08-03, AND IT HAD NEVER FIRED BEFORE. It sat ABOVE `_mark_material`, so it
        # read a table on which NO row carried `material=True` — `uncited_material_figures` skips
        # unflagged rows, found nothing to check, and returned `[]` on every build since it shipped.
        # MEASURED, not inferred: at the old position SMPL's table has 0 material rows and the guard
        # returns `[]`; after `_mark_material` it has 1 and returns `Asset Writedown ($M) LTM =
        # -391.9`. Its unit pins passed throughout because they CONSTRUCT rows with `material=True`
        # — the fixture supplied the state production never reached.
        # THIS ALSO CORRECTS #317: SMPL's committed page did not "violate a shipped guard while
        # current code could not reproduce it". Current code reproduces it exactly — the guard was
        # ordered before its own input.
        if (uncited := uncited_material_figures(synthesis, mech)):
            raise DossierAssemblyError(
                f"{ticker}: the synthesis never states {len(uncited)} MATERIAL figure(s) its own "
                f"financial summary shows — {'; '.join(uncited)}. A reader meets the number in the "
                "argument, not the table, so an argument that omits it reads as though the item "
                "did not happen (SMPL 2026-07-30 cited a $249M charge as if it were a $391.9M "
                "writedown). Re-run: synthesis varies between runs.")
        _materiality_check(bundle, mech, synthesis, ticker=ticker)
        _freshness_check(mech, ticker=ticker, built_at=built_at.date())
        # (P2) contradiction lint — flag any synthesis pending-claim about a NOW-present block (the
        # durable guard the FIX-0 incident earns); QA-channel.
        if synthesis is not None:
            flags += contradiction_flags(synthesis, mech)
    else:
        flags.append("LLM synthesis skipped (no ANTHROPIC client) — mechanical layer only")
    # (A2) THE EV GAP — ASSEMBLY MUST PRODUCE IT, or a re-assembly DROPS it.
    #
    # REVIEW OF #324: the first cut PINNED the asymmetry instead of closing it — a test that passes
    # while a fresh assembly writes `ev_gap: null` and reddens only once somebody fixes it. That is
    # a tombstone, not a guard: it offers no protection to the queued SMPL re-assembly, which is
    # the exact event it described.
    #
    # RECOMPUTED, NOT CARRIED FORWARD. Copying the committed value across an assembly would put a
    # gap struck on OLD cap/net-debt/consensus beside NEW ones — the frozen-beside-live defect this
    # repo has already ruled on. THE SAME TRANSFORM the refresh path uses runs here on the FRESH
    # mech, so there is ONE definition and the two write paths cannot disagree by construction —
    # which is what `test_consensus_parity` now asserts as a VALUE comparison.
    from vinci.dossier.refresh import ev_gap_transform
    from vinci.dossier.schemas import MechanicalLayer

    mech = MechanicalLayer.model_validate(
        ev_gap_transform(ticker)(mech.model_dump(mode="json")))
    llm_log = "\n\n".join(lg for lg in logs if lg)
    # split the emitted flags by audience: decision caveats → human PDF/web (re-voiced), machine
    # QA self-checks → dev/JSON only (emission logic is untouched; classification is display-layer).
    caveats, qa_flags = dossier_flags.partition(flags)
    # MAIN BODY, and LEADING. A reader who does not know this name sits outside the current
    # candidate set will read every screen-relative number on the page as current. It leads for the
    # same reason the vintage stamp does: read after the numbers, it no longer changes how they are
    # read. Not a qa_flag — this is decision surface, not audit.
    if fin.screen_status:
        caveats.insert(0, fin.screen_status)
    # (anchor) the persisted R1 anchor — spot-independent, source-bound (vinci.dossier.anchor). Best
    # effort: any own-history gap or EDGAR error yields an INAPPLICABLE anchor with a reason,
    # never a crashed assembly (the dossier stands on its own; the anchor is committed triage
    # context).
    try:
        anchor_facts = EdgarClient.from_config(cfg).companyfacts(rec.identity.cik)
        anchor = compute_anchor(mech.model_dump(mode="json"), facts=anchor_facts,
                                computed_at=datetime.now(UTC))
    except Exception as exc:  # noqa: BLE001 — anchor is best-effort; it never blocks the dossier
        anchor = Anchor(recipe_hint=RECIPE_UNKNOWN, applicable=False, computed_at=datetime.now(UTC),
                        reason=f"anchor computation failed: {type(exc).__name__}")
    dossier = Dossier(
        ticker=ticker, name=rec.identity.name, cik=rec.identity.cik,
        reference_date=fin.reference_date, rank=fin.rank, mechanical=mech, synthesis=synthesis,
        caveats=caveats, qa_flags=qa_flags, anchor=anchor,
        # (teaser/company) SIC-derived sector/sub-industry + exchange + CIQ subject business desc —
        # assemble/inform context for the Brief teaser, never a gate/rank input.
        sector=resolve_label(rec.identity.sic).sector,  # coarse sector — the CIQ-GICS fallback
        industry=ciq_sheets.gics_industry(bundle),  # CIQ GICS Primary Industry Classification
        exchange=rec.identity.exchange,
        business_description=ciq_sheets.business_description(bundle),
        # UTC-aware so the stamp is unambiguous and comparable across machines/timezones — it lets
        # the human tell two same-day re-assemblies apart (rendered with time + "UTC").
        llm_model=(llm.model if llm else None), assembled_at=built_at,
        # (26a) the extractor's declared vintage — the assembly date says WHEN this was built, the
        # version says WITH WHAT. Stored rather than recomputed at render time, so re-rendering an
        # old JSON keeps the version that actually produced it instead of claiming today's.
        extraction_version=EXTRACTION_VERSION,
    )
    _write(dossier, llm_log, out_root)
    return dossier


def assemble_cohort(
    finalists: list[Finalist],
    *,
    cfg: Config | None = None,
    llm: LlmClient | None = None,
    manual: ManualDataStore | None = None,
    max_workers: int = 8,
) -> tuple[list[Dossier], list[str]]:
    """Assemble the cohort in parallel → (dossiers, per-name errors). The batch never crashes."""
    cfg = cfg or get_config()
    cfg.ensure_dirs()
    resolver = EntityResolver.from_config(cfg)
    _ = resolver.index  # preload once so worker threads only do read-only lookups
    graph = _load_graph(cfg)
    manual = manual or LocalFolderStore.from_config(cfg)
    out_root = cfg.data_dir / "dossiers"

    def task(fin: Finalist) -> tuple[Dossier | None, str | None]:
        try:
            return assemble_one(
                fin, cfg=cfg, resolver=resolver, graph=graph, manual=manual,
                out_root=out_root, llm=llm,
            ), None
        except Exception as exc:  # noqa: BLE001 — one bad name must not crash the cohort batch
            return None, f"{fin.data_record.identity.ticker}: {type(exc).__name__}: {exc}"

    dossiers: list[Dossier] = []
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=min(max_workers, max(1, len(finalists)))) as pool:
        for dossier, error in pool.map(task, finalists):
            if dossier is not None:
                dossiers.append(dossier)
            if error is not None:
                errors.append(error)
    return dossiers, errors
