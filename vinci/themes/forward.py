"""Stage-4 forward-validation harness — the append-only ratification LEDGER + the forward
MEASUREMENT layer implementing ``docs/theme_forward_validation.md`` (the revised protocol).

It LOGS the analyst's ratified/passed dispositions and MEASURES their forward performance vs the
controls: the RATIFIED-PASSED spread (§3a, "did the human sort the tier") and the
RATIFIED-NAIVE(equal-weight) spread (§3b-i, "did selecting beat holding the whole tier"), both
POOLED AND broken out BY CHAIN LAYER (§4 — pooling masks the thin-layer signal). It surfaces the §3c
PARTIAL-KILL state first-class and enforces the §4 power label on every spread.

DEAD-SIGNAL FIREWALL (§6): NO code path here selects, ranks, scores, or promotes a grade to a hold.
The machine ASSEMBLES + MEASURES; the human DECIDES. Forward-only — no backtest, no tuning on
returns; spreads accrue over calendar time. Append-only — a correction is a NEW row, never a
mutation.

CAVEAT recorded (an honest property of §3b-i, not a bug): the equal-weight-all baseline is
mathematically a *scaled* RATIFIED-PASSED — RATIFIED-NAIVE = (n_passed / N) * (RATIFIED-PASSED) — so
it shares that spread's sign and is a WEAK control (it tests "did selecting beat not-selecting",
correlated with §3a). A strict PARTIAL-KILL (RATIFIED-NAIVE <= 0 while RATIFIED-PASSED > 0) is thus
UNREACHABLE with §3b-i when both legs are present; ``apparatus_fraction`` (= n_passed/N in scope)
surfaces the "~0" case for the human to judge. The INDEPENDENT replicable control
(keyword/co-movement, §3b-ii) — where the partial-kill test truly bites — is the SECOND-PHASE build
(needs Component A
live-forward), recorded as a deferred control, not built here.
"""
from __future__ import annotations

import csv
from collections.abc import Callable
from datetime import date, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from vinci.eod.client import EodClient

# --------------------------------------------------------------------------------------------------
# Schemas (§1) — the ratification record + the frozen baskets + the measurement report
# --------------------------------------------------------------------------------------------------


class Disposition(StrEnum):
    RATIFIED = "ratified"       # the BUY leg
    PASSED = "passed"           # the AVOID leg (§3a) — first-class control data, NOT a discard
    DIG_DEEPER = "dig-deeper"   # temporary — MUST resolve before a basket freezes


class RatificationRecord(BaseModel):
    """One append-only ledger row (§1). The machine fields are the INPUT the human judged;
    disposition + rationale + ratification_date are the HUMAN's. ``comovement_onset_date`` is logged
    FORWARD (§5). ``substructure_tag`` + ``grade`` are theme-AGNOSTIC (a value-chain layer for a
    chain driver, a parallel capability category for a demand-shaped one). BACK-COMPAT: the reader
    ALSO accepts the legacy names ``chain_layer`` / ``machine_grade`` so ledgers frozen before the
    rename still load without re-freezing; new writes use the neutral names."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    ticker: str
    cik: str
    driver: str
    substructure_tag: str = Field(validation_alias=AliasChoices("substructure_tag", "chain_layer"))
    grade: str = Field(validation_alias=AliasChoices("grade", "machine_grade"))
    driver_tie: str
    grade_fact: str
    source_ref: str
    disposition: Disposition
    rationale: str
    ratification_date: date
    first_disclosure_date: date | None = None
    theme_confirmation_date: date | None = None
    comovement_onset_date: date | None = None


class FrozenBaskets(BaseModel, frozen=True):
    """The immutable frozen references (§3). Entry = each name's ratification date (§2).

    EMPTY-BUY reality (all committed PASSED, zero RATIFIED): ``ratified`` freezes as ``()`` and
    does NOT error; every RATIFIED-dependent spread is then UNDEFINED (see ``measure_hold_none``).
    ``watchlist`` + ``watchlist_triggers`` carry the re-underwrite cohort; ``real_tier`` is the
    OPTIONAL looser secondary (build-2 REAL tier)."""

    driver: str
    freeze_timestamp: str
    ratified: tuple[str, ...]
    passed: tuple[str, ...]
    all_committed: tuple[str, ...]
    entry_dates: dict[str, str]
    layer_of: dict[str, str]
    watchlist: tuple[str, ...] = ()  # genuine-exposure re-underwrite cohort
    # ticker -> verbatim trigger text
    watchlist_triggers: dict[str, str] = Field(default_factory=dict)
    real_tier: tuple[str, ...] = ()  # OPTIONAL looser secondary (build-2 REAL-7)
    # labeled control cohort WITHIN the AVOID leg — the highest-value near-misses (best of PASSED);
    # tracks whether the human's PASS on the strongest almost-buys held up forward. NOT the
    # watchlist (those are genuine-exposure re-underwrite candidates); these are near-miss controls.
    avoid_controls: tuple[str, ...] = ()
    #: WHERE THIS FILE CAME FROM, in one sentence. A basket written by the freeze and a basket
    #: RECONSTRUCTED from the frontend mirror hold the same names, but they are not the same
    #: evidence: the freeze read the analyst's dispositioned worksheet, the reconstruction read a
    #: published summary of it. Committing both without saying which is which would make the
    #: durable record unauditable at exactly the point it starts being trusted.
    provenance: str = ""
    deferred_controls: tuple[str, ...] = (
        "keyword/co-movement naive baseline (§3b-ii) — SECOND-PHASE: needs Component A "
        "live-forward; the INDEPENDENT replicable control (isolates the classifier's contribution "
        "vs the human's selection) that the equal-weight baseline is not. Build it so this can be "
        "ADDED later.",
    )


# power floor (§4) — a-priori face-validity constants; NEVER tuned on returns
MIN_THEME_QUARTERS = 8
MIN_DRIVERS = 4


class PowerLabel(BaseModel, frozen=True):
    theme_quarters: int
    drivers: int
    sign_consistent: bool
    label: str   # "UNPOWERED" | "POWERED-DIRECTIONAL" — NEVER "significant"
    note: str


class LayerSpread(BaseModel, frozen=True):
    scope: str   # "POOLED" or a chain-layer name
    n_ratified: int
    n_passed: int
    n_all: int
    ratified_minus_passed: float | None   # §3a
    ratified_minus_naive: float | None    # §3b-i (equal-weight-all)
    apparatus_fraction: float | None    # RATIFIED−NAIVE / RATIFIED−PASSED — surfaces "~0" (§3c)
    mean_ratified: float | None
    state: str   # EDGE-DIRECTIONAL | PARTIAL-KILL | NO-SELECTION | INSUFFICIENT


class SpreadReport(BaseModel, frozen=True):
    driver: str
    as_of: str
    horizon_days: int
    power: PowerLabel
    pooled: LayerSpread
    by_layer: tuple[LayerSpread, ...]
    partial_kill_scopes: tuple[str, ...]   # §3c — surfaced first-class, never buried


# --------------------------------------------------------------------------------------------------
# Component 1 — the append-only ratification ledger (§1)
# --------------------------------------------------------------------------------------------------
def append_record(ledger_path: Path, rec: RatificationRecord) -> None:
    """Append ONE JSONL row. Append-only: a correction is a new row, never a mutation."""
    with open(ledger_path, "a") as fh:
        fh.write(rec.model_dump_json() + "\n")


def load_ledger(ledger_path: Path) -> list[RatificationRecord]:
    if not ledger_path.exists():
        return []
    return [RatificationRecord.model_validate_json(ln)
            for ln in ledger_path.read_text().splitlines() if ln.strip()]


def current_dispositions(records: list[RatificationRecord]) -> dict[str, RatificationRecord]:
    """Append-only READ: the LATEST row per ticker wins (a later correction supersedes; the file is
    never mutated)."""
    out: dict[str, RatificationRecord] = {}
    for r in records:  # file order == append order → last wins
        out[r.ticker] = r
    return out


_DISPOSITION_ALIASES = {
    "ratified": Disposition.RATIFIED, "ratify": Disposition.RATIFIED,
    "passed": Disposition.PASSED, "pass": Disposition.PASSED,
    "dig-deeper": Disposition.DIG_DEEPER, "dig deeper": Disposition.DIG_DEEPER,
    "dig_deeper": Disposition.DIG_DEEPER,
}


def records_from_worksheet(
    csv_path: Path, *, driver: str, ratification_date: date,
) -> tuple[list[RatificationRecord], int]:
    """Build records from the analyst's dispositioned worksheet
    (``committed_review_worksheet.csv``). Rows with an EMPTY disposition are NOT logged (pending the
    analyst) — returns ``(records, n_pending)``. NEVER fabricates a disposition."""
    records: list[RatificationRecord] = []
    pending = 0
    with open(csv_path) as fh:
        for row in csv.DictReader(fh):
            raw = (row.get("DISPOSITION") or "").strip().lower()
            if not raw:
                pending += 1
                continue
            disp = _DISPOSITION_ALIASES.get(raw)
            if disp is None:
                raise ValueError(f"{row.get('ticker')}: unrecognized DISPOSITION {raw!r}")
            records.append(RatificationRecord(
                ticker=row["ticker"], cik=row["cik"], driver=driver,
                # schema-flexible CSV read: the AI-datacenter worksheet columns are chain_layer /
                # machine_grade / grade_driver_tie; a demand-shaped worksheet (e.g. defense) uses
                # category / grade_concreteness / driver_tie for the SAME three fields. These fill
                # the neutral record fields substructure_tag / grade / driver_tie.
                substructure_tag=row.get("chain_layer") or row.get("category", ""),
                grade=row.get("machine_grade") or row.get("grade_concreteness", ""),
                driver_tie=row.get("grade_driver_tie") or row.get("driver_tie", ""),
                grade_fact=row.get("grade_fact", ""),
                source_ref=row.get("grade_accession", ""), disposition=disp,
                rationale=(row.get("RATIONALE") or "").strip(),
                ratification_date=ratification_date))
    return records, pending


# --------------------------------------------------------------------------------------------------
# Component 2 — the frozen baskets (§3): BUY leg, AVOID leg, equal-weight naive baseline
# --------------------------------------------------------------------------------------------------
def freeze_baskets(
    records: list[RatificationRecord], all_committed: list[str], *,
    driver: str, freeze_timestamp: str, layer_of: dict[str, str],
    watchlist: list[str] | None = None, watchlist_triggers: dict[str, str] | None = None,
    real_tier: list[str] | None = None, avoid_controls: list[str] | None = None,
) -> FrozenBaskets:
    """Freeze the immutable baskets. GUARD (§1): every committed name must be RATIFIED or PASSED —
    a DIG-DEEPER or a missing disposition means the tier is NOT ready; raise (cannot freeze). An
    EMPTY BUY leg (zero RATIFIED — all PASSED) is VALID and does NOT error: ``ratified`` freezes as
    ``()``. The optional ``watchlist`` (re-underwrite cohort, must be ⊆ committed) + verbatim
    ``watchlist_triggers``, the ``real_tier`` (a separate build-2 cohort), and the
    ``avoid_controls`` (labeled near-miss control cohort, must be ⊆ the PASSED leg) freeze
    alongside."""
    disp = current_dispositions(records)
    missing = [t for t in all_committed if t not in disp]
    unresolved = [t for t in all_committed
                  if t in disp and disp[t].disposition is Disposition.DIG_DEEPER]
    if missing or unresolved:
        raise ValueError(
            f"cannot freeze baskets: {len(missing)} un-dispositioned {missing[:6]} + "
            f"{len(unresolved)} DIG-DEEPER {unresolved[:6]} — every name must be "
            "RATIFIED/PASSED first")
    ratified = tuple(t for t in all_committed if disp[t].disposition is Disposition.RATIFIED)
    passed = tuple(t for t in all_committed if disp[t].disposition is Disposition.PASSED)
    entry_dates = {t: disp[t].ratification_date.isoformat() for t in all_committed}
    wl = tuple(watchlist or ())
    unknown = [t for t in wl if t not in all_committed]
    if unknown:  # a watchlist name must be a committed-tier name — fail loud, never silently drop
        raise ValueError(f"watchlist names not in the committed tier: {unknown}")
    ac = tuple(avoid_controls or ())
    bad_ac = [t for t in ac if t not in passed]
    if bad_ac:  # an avoid-control is a PASSED near-miss (the AVOID leg) — fail loud, never RATIFIED
        raise ValueError(f"avoid_controls must be PASSED names (the AVOID leg): {bad_ac}")
    return FrozenBaskets(
        driver=driver, freeze_timestamp=freeze_timestamp, ratified=ratified, passed=passed,
        all_committed=tuple(all_committed), entry_dates=entry_dates, layer_of=layer_of,
        watchlist=wl, watchlist_triggers=dict(watchlist_triggers or {}),
        real_tier=tuple(real_tier or ()), avoid_controls=ac)


#: The COMMITTED home for a frozen basket, one file per driver. Operator decision 2026-08-12,
#: reversing the standing `.gitignore` rule that these were local-only. The reason the rule changed:
#: the Stage-4 measurement's whole product is a number that accrues over CALENDAR TIME, and its
#: input existed on exactly one machine — so on any other checkout the accrual could not be computed
#: at all, and the reconstruction path that closed that gap works ONLY for hold-none freezes. The
#: first RATIFIED theme would have had no durable record of its BUY leg's entry dates anywhere.
#: The ratification LEDGER stays git-ignored: it is the analyst's raw dispositioned worksheet output
#: and that was not what was decided here.
BASKETS_SUBDIR = "themes/baskets"

#: The COMMITTED home for a driver's ratification ledger — operator decision 2026-08-12, extending
#: the basket decision to the record the basket is DERIVED FROM. The basket says which names are in
#: which cohort; the ledger says WHY, in the analyst's own words, one appended row at a time. Losing
#: it loses the judgment and keeps only its conclusion.
#:
#: THE THREE JULY 2026 LEDGERS ARE GONE and are NOT reconstructed here. A ledger is an APPEND-ONLY
#: record whose value is that it records what was appended and when; a rebuild from the published
#: mirror would carry one synthetic timestamp for every row and no correction history, and
#: committing that as "the ledger" would misrepresent the artifact at the moment it starts being
#: trusted. Their dispositions survive in the mirrors (`rationale`, `gradeFact`, `accession` per
#: name) — that is the honest surviving record, and it is named as such rather than dressed up.
LEDGER_SUBDIR = "themes/ledgers"


def ledger_path(driver: str, *, data_dir: Path) -> Path:
    """The committed ratification ledger for one driver."""
    return data_dir / LEDGER_SUBDIR / f"{driver}.jsonl"


def baskets_path(driver: str, *, data_dir: Path) -> Path:
    """The committed basket for one driver, under the configured DATA DIR.

    Keyed on ``data_dir`` rather than the process's cwd, and that is not a detail: the first cut
    resolved it from `Path.cwd()`, so an existing CLI test that freezes a tmp worksheet wrote its
    four synthetic names straight over the real committed baskets in the repo. Every other durable
    artifact here is located through config; this one is too."""
    return data_dir / BASKETS_SUBDIR / f"{driver}.json"


def write_baskets(
    baskets: FrozenBaskets, *, data_dir: Path, supersede: bool = False,
) -> Path:
    """Write one driver's frozen basket to its committed home. Returns the path.

    REFUSES TO OVERWRITE AN EXISTING BASKET (operator review P1 on #422). These are the
    IMMUTABLE frozen references, and their per-name entry dates are the input to a calendar-time
    accrual — but every later `themes-forward --worksheet …` for the same driver wrote a newly
    frozen object to the same filename. Measured: re-freezing defense moved `entry_dates` from
    {2026-07-03} to {2026-08-12}, shifting the forward window's start by 40 days with nothing said.
    The append-only ledger does not protect this artifact, and committing it made the silent
    rewrite worse, not better — it now looks authoritative.

    THE SAME CLASS AS THE MONITOR SNAPSHOT OVERWRITE (#418), and this file did not learn from it.

    ``supersede=True`` is the deliberate re-freeze: the existing basket is ARCHIVED under
    ``baskets/archive/<driver>-<its own freeze date>.json`` before the new one lands, so a
    supersession never destroys the window it replaces. Archiving rather than refusing outright is
    what makes the flow usable — a re-freeze is legitimate when the analyst re-dispositions a tier;
    losing the prior basket is not.
    """
    p = baskets_path(baskets.driver, data_dir=data_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        prior = load_baskets(p)
        if not supersede:
            raise FileExistsError(
                f"{p} already exists (frozen {prior.freeze_timestamp[:10]}) — re-freezing would "
                f"replace the entry dates the forward accrual is measured from. Pass "
                f"supersede=True to archive it and re-freeze deliberately.")
        # THE ARCHIVE NAME IS DATE-KEYED and the freeze timestamp is date-only, so two
        # supersessions on the SAME DAY would collide and the second would overwrite the first
        # archive — losing exactly what archiving exists to keep. Disambiguated rather than
        # trusted to be rare: re-dispositioning a tier twice in a session is a normal thing to do.
        base = p.parent / "archive" / f"{baskets.driver}-{prior.freeze_timestamp[:10]}"
        base.parent.mkdir(parents=True, exist_ok=True)
        archive = base.with_suffix(".json")
        n = 2
        while archive.exists():
            archive = base.with_name(f"{base.name}-{n}").with_suffix(".json")
            n += 1
        archive.write_text(p.read_text())
    p.write_text(baskets.model_dump_json(indent=1) + "\n")
    return p


def load_baskets(path: Path) -> FrozenBaskets:
    """Read a committed frozen basket — the durable input the forward measurement was missing."""
    return FrozenBaskets.model_validate_json(path.read_text())


def baskets_from_mirror(
    mirror: dict[str, object], *, driver: str | None = None,
) -> FrozenBaskets:
    """Rebuild the frozen baskets from a COMMITTED ``frontend/themes/<slug>.json`` mirror.

    WHY THIS EXISTS. The ratification ledger and the frozen baskets are git-ignored by an explicit
    standing decision (`.gitignore`: "derived, LOCAL-only … never committed"), so the only durable
    record of a freeze is the frontend mirror. When the local files are gone — a different machine,
    a fresh clone, a cleaned worktree — the Stage-4 forward measurement has NO input, and the whole
    point of Stage 4 is a number that accrues over CALENDAR TIME. Three themes froze in July 2026;
    two passed their 30-day horizon in early August with their diagnostics still reading
    ``0 days forward from freeze``, because nothing could recompute them. This closes that gap
    WITHOUT committing the ledger, which stays the operator's call.

    REFUSES A NON-EMPTY BUY LEG. The mirror carries no per-name ratification date, and for a
    RATIFIED name the entry date IS the ratification date — dating the BUY leg from the freeze
    instead would silently measure a window the analyst never held. An all-PASSED (hold-none)
    freeze has no such problem: every name entered at the freeze, which is exactly what
    ``_cohort_fwd_mean`` already defaults to, so nothing is invented. Rebuild the BUY leg from the
    local ledger, or re-freeze from the worksheet.
    """
    # ONE DRIVER IDENTITY PER REPORT. The mirror's own `driver` field is a HUMAN LABEL, not the
    # registry key — ai-datacenter's reads "AI-datacenter value chain" while its key is
    # "ai-datacenter" — so taking it as identity made the header (CLI key) and the confound strings
    # (`f"{baskets.driver}-BETA-CONFOUNDED"`) name two different drivers in one report. The caller's
    # registry key wins when given; the mirror's label is provenance, echoed by the CLI so loading
    # the wrong file is visible on the first line rather than inferred from the name count.
    # NOTE (recorded in STATE.md): mirrors carry NO registry key at all — not `driver`, not `slug`
    # ("defense" vs the key "defense-demand-shift") — so nothing here can VERIFY that this mirror
    # belongs to `driver`. That binding is operator care, not a machine check, until the mirror
    # carries its key.
    driver = driver or str(mirror["driver"])
    n_ratified = int(str(mirror.get("ratifiedCount", 0) or 0))
    if n_ratified:
        raise ValueError(
            f"{driver}: the mirror reports {n_ratified} RATIFIED name(s) and carries no "
            f"ratification dates — a BUY leg dated from the freeze would measure a window the "
            f"analyst never held. Rebuild from the local ledger, or re-freeze from the worksheet.")
    raw = mirror["names"]
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{driver}: mirror carries no committed names")
    names: list[dict[str, object]] = [n for n in raw if isinstance(n, dict)]
    if len(names) != len(raw):
        raise ValueError(f"{driver}: {len(raw) - len(names)} malformed entries in `names`")
    freeze_ts = str(mirror["freezeTimestamp"])

    def field(n: dict[str, object], key: str) -> str:
        return str(n.get(key, "") or "")

    def cohort(tag: str) -> list[str]:
        out: list[str] = []
        for n in names:
            tags = n.get("cohorts")
            if isinstance(tags, list) and tag in tags:
                out.append(field(n, "ticker"))
        return out

    all_committed = [field(n, "ticker") for n in names]
    return freeze_baskets(
        # Every name PASSED, dispositioned at the freeze. Reconstructed rather than read, and legal
        # ONLY because the no-BUY-leg case above is the only one this function accepts.
        [RatificationRecord(
            ticker=field(n, "ticker"), cik="", driver=driver,
            substructure_tag=field(n, "substructureTag"), grade=field(n, "grade"),
            driver_tie=field(n, "driverTie"), grade_fact=field(n, "gradeFact"),
            source_ref=field(n, "accession"), disposition=Disposition.PASSED,
            rationale=field(n, "rationale"),
            ratification_date=date.fromisoformat(freeze_ts[:10]))
         for n in names],
        all_committed, driver=driver, freeze_timestamp=freeze_ts,
        layer_of={field(n, "ticker"): field(n, "substructureTag") for n in names},
        watchlist=cohort("watchlist") or None,
        avoid_controls=cohort("avoid-control") or None,
        real_tier=cohort("real") or None,
    ).model_copy(update={"provenance": (
        f"RECONSTRUCTED from the committed frontend mirror, not written by the freeze. The "
        f"ratification ledger and the freeze-time basket were git-ignored local-only files and "
        f"were gone; this recovers the names, cohorts and freeze timestamp from the published "
        f"summary. Every name is PASSED with entry = the freeze date, which is the only reading a "
        f"hold-none mirror supports and what `_cohort_fwd_mean` already defaults to — a BUY leg "
        f"cannot be reconstructed this way and is refused. Driver key supplied by the caller; the "
        f"mirror's own `driver` field read {str(mirror.get('driver'))!r}.")})


# --------------------------------------------------------------------------------------------------
# Component 3 — the forward measurement (§4): LAYER-AWARE + §3c partial-kill + §4 power
# --------------------------------------------------------------------------------------------------
PriceFn = Callable[[str, date], float | None]  # (ticker, date) -> close, or None if no bar


def _fwd_return(price_fn: PriceFn, ticker: str, entry: date, checkpoint: date) -> float | None:
    p0 = price_fn(ticker, entry)
    p1 = price_fn(ticker, checkpoint)
    if p0 is None or p1 is None or p0 <= 0:
        return None
    return p1 / p0 - 1.0


def _adj_return(price_fn: PriceFn, benchmark: str, ticker: str, entry: date,
                checkpoint: date) -> float | None:
    """Benchmark-adjusted forward return (§4): name return minus benchmark over the SAME window."""
    r = _fwd_return(price_fn, ticker, entry, checkpoint)
    b = _fwd_return(price_fn, benchmark, entry, checkpoint)
    return None if r is None or b is None else r - b


def _mean(xs: list[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None


def classify_state(rmp: float | None, rmn: float | None, n_ratified: int) -> str:
    """§3c states from the two co-primary spreads — SIGN-based, NO return-tuned threshold. EDGE
    requires BOTH positive; PARTIAL-KILL = selection works (rmp>0) but the apparatus does not beat
    naive (rmn<=0); NO-SELECTION = the human did not sort the tier (rmp<=0)."""
    if n_ratified == 0 or rmp is None:
        return "INSUFFICIENT"
    if rmp <= 0:
        return "NO-SELECTION"
    if rmn is None:
        return "INSUFFICIENT"
    if rmn <= 0:
        return "PARTIAL-KILL"
    return "EDGE-DIRECTIONAL"


def _spread(scope: str, scope_tickers: set[str], baskets: FrozenBaskets,
            adj: dict[str, float]) -> LayerSpread:
    rat = [adj[t] for t in baskets.ratified if t in scope_tickers and t in adj]
    pas = [adj[t] for t in baskets.passed if t in scope_tickers and t in adj]
    allc = [adj[t] for t in baskets.all_committed if t in scope_tickers and t in adj]
    mr, mp, ma = _mean(rat), _mean(pas), _mean(allc)
    rmp = None if mr is None or mp is None else mr - mp
    rmn = None if mr is None or ma is None else mr - ma
    frac = (rmn / rmp) if (rmp is not None and rmp > 0 and rmn is not None) else None
    return LayerSpread(
        scope=scope, n_ratified=len(rat), n_passed=len(pas), n_all=len(allc),
        ratified_minus_passed=rmp, ratified_minus_naive=rmn, apparatus_fraction=frac,
        mean_ratified=mr, state=classify_state(rmp, rmn, len(rat)))


def _quarter_index(d: date) -> int:
    return d.year * 4 + (d.month - 1) // 3


def power_label(*, theme_quarters: int, drivers: int, sign_consistent: bool) -> PowerLabel:
    """§4 power — effective sample = THEME-QUARTERS (names within a theme co-move → ~1 obs per
    theme-quarter). Below the a-priori floor the spread is UNPOWERED / DIRECTIONAL, never
    significant."""
    powered = theme_quarters >= MIN_THEME_QUARTERS and drivers >= MIN_DRIVERS and sign_consistent
    if powered:
        return PowerLabel(
            theme_quarters=theme_quarters, drivers=drivers, sign_consistent=True,
            label="POWERED-DIRECTIONAL",
            note=(f"{theme_quarters} theme-quarters across {drivers} drivers, sign-consistent "
                  "— meets the a-priori floor; still a FORWARD-directional read, never a "
                  "significance test"))
    reasons = []
    if theme_quarters < MIN_THEME_QUARTERS:
        reasons.append(f"theme-quarters {theme_quarters}<{MIN_THEME_QUARTERS}")
    if drivers < MIN_DRIVERS:
        reasons.append(f"drivers {drivers}<{MIN_DRIVERS}")
    if not sign_consistent:
        reasons.append("sign not consistent across drivers")
    return PowerLabel(
        theme_quarters=theme_quarters, drivers=drivers, sign_consistent=sign_consistent,
        label="UNPOWERED",
        note=("DIRECTIONAL / ANECDOTAL — do NOT read as validation or kill ("
              + "; ".join(reasons) + ")"))


def measure_horizon(
    baskets: FrozenBaskets, *, price_fn: PriceFn, horizon_days: int, as_of: date,
    benchmark: str = "IWM", drivers: int = 1, sign_consistent: bool = True,
) -> SpreadReport:
    """One horizon's spreads (§4): POOLED + BY-LAYER (§4 — pooling masks the thin-layer signal),
    each with the §3c state + apparatus_fraction, plus the first-class partial-kill scope list and
    the §4 power label. Per name checkpoint = entry + horizon; names whose checkpoint is beyond
    ``as_of``
    (horizon not yet reached) are dropped from that horizon."""
    adj: dict[str, float] = {}
    for t in baskets.all_committed:
        entry = date.fromisoformat(baskets.entry_dates[t])
        checkpoint = entry + timedelta(days=horizon_days)
        if checkpoint > as_of:
            continue
        a = _adj_return(price_fn, benchmark, t, entry, checkpoint)
        if a is not None:
            adj[t] = a
    pooled = _spread("POOLED", set(baskets.all_committed), baskets, adj)
    layers = sorted({baskets.layer_of[t] for t in baskets.all_committed})
    by_layer = tuple(
        _spread(lyr, {t for t in baskets.all_committed if baskets.layer_of[t] == lyr}, baskets, adj)
        for lyr in layers)
    partial_kill = tuple(ls.scope for ls in (pooled, *by_layer) if ls.state == "PARTIAL-KILL")
    theme_quarters = (_quarter_index(as_of)
                      - _quarter_index(date.fromisoformat(baskets.freeze_timestamp[:10])) + 1)
    power = power_label(theme_quarters=max(0, theme_quarters), drivers=drivers,
                        sign_consistent=sign_consistent)
    return SpreadReport(
        driver=baskets.driver, as_of=as_of.isoformat(), horizon_days=horizon_days, power=power,
        pooled=pooled, by_layer=by_layer, partial_kill_scopes=partial_kill)


def measure(
    baskets: FrozenBaskets, *, price_fn: PriceFn, horizons_days: list[int], as_of: date,
    benchmark: str = "IWM", drivers: int = 1, sign_consistent: bool = True,
) -> list[SpreadReport]:
    """The full forward measurement — one SpreadReport per horizon reached."""
    return [measure_horizon(baskets, price_fn=price_fn, horizon_days=h, as_of=as_of,
                            benchmark=benchmark, drivers=drivers, sign_consistent=sign_consistent)
            for h in horizons_days]


# --------------------------------------------------------------------------------------------------
# Component 3 (EMPTY-BUY) — the zero-RATIFIED / hold-none measurement. RATIFIED-dependent
# spreads are UNDEFINED (never 0.0); the two VALID beta-confounded diagnostics + the layer-aware
# split accrue FORWARD-ONLY from the freeze date. NEVER an edge verdict.
# --------------------------------------------------------------------------------------------------
# thin-layer = where semantic-primary uniquely contributed; obvious-layer = a keyword screen
# finds it
THIN_LAYERS = ("HBM/memory", "packaging", "thermal/cooling", "optical/interconnect")
OBVIOUS_LAYERS = ("chips/GPU", "power/electrical", "colocation/operator", "AI-cloud")

HOLD_NONE_HONESTY = (
    "No BUY leg exists (zero RATIFIED) -> the core edge-measure (RATIFIED-PASSED) and all "
    "RATIFIED-dependent spreads are UNDEFINED and NOT computed. The outputs below are "
    "AVOID-discipline and exposure-carry DIAGNOSTICS, beta-confounded, and are NOT a validation "
    "of the semantic-primary edge."
)


class Diagnostic(BaseModel, frozen=True):
    """One beta-confounded forward diagnostic (NOT an edge verdict). ``value`` is None until the
    horizon is reached forward from the freeze date."""

    name: str            # "avoid-discipline" | "exposure-carry"
    horizon_days: int
    value: float | None
    n: int
    confound: str        # the explicit beta-confound label — always carried
    detail: str


class LayerSplit(BaseModel, frozen=True):
    """NAIVE-56 forward return split thin- vs obvious-layer (§4 layer-aware) — NOT pooled. This
    split is AI-datacenter-SPECIFIC (thin = where semantic-primary uniquely contributed); a
    demand-shaped driver with no thin/obvious tiering uses ``naive_by_layer`` (per-category)."""

    horizon_days: int
    thin_return: float | None
    obvious_return: float | None
    n_thin: int
    n_obvious: int


class LayerReturn(BaseModel, frozen=True):
    """One layer/category's slice of the NAIVE forward return (§4 layer-aware, driver-AGNOSTIC): the
    equal-weight forward return of the committed names carrying that ``layer_of`` value — a
    value-chain layer for a chain driver, a parallel capability category for a demand-shaped one."""

    layer: str
    mean_return: float | None
    n: int


class HoldNoneReport(BaseModel, frozen=True):
    """The empty-BUY (zero-RATIFIED) report: the UNDEFINED RATIFIED-dependent measures (never
    computed), the two valid diagnostics, the (AI-datacenter) thin/obvious layer split, the
    driver-agnostic per-category ``naive_by_layer`` breakdown, the watchlist onset baselines, and
    the honesty label."""

    driver: str
    as_of: str
    freeze_timestamp: str
    horizon_days: int
    undefined_measures: tuple[tuple[str, str], ...]   # (measure, reason) — RATIFIED-dependent
    avoid_discipline: Diagnostic
    exposure_carry: Diagnostic
    layer_split: LayerSplit
    naive_by_layer: tuple[LayerReturn, ...] = ()      # per-category (driver-agnostic) NAIVE split
    onset_baselines: dict[str, str | None]            # watchlist ticker -> onset iso, or None
    honesty_label: str


def undefined_ratified_measures(baskets: FrozenBaskets) -> tuple[tuple[str, str], ...]:
    """When the BUY leg is empty (zero RATIFIED), EVERY RATIFIED-dependent spread is UNDEFINED —
    return each with its reason. NEVER computed, NEVER 0.0 (fail-loud, never fabricate). () if a
    BUY leg exists."""
    if baskets.ratified:
        return ()
    reason = "no BUY leg — zero RATIFIED; requires a ratified cohort that does not exist"
    return tuple((m, reason) for m in (
        "RATIFIED-PASSED (§3a, the core edge-measure)",
        "RATIFIED-NAIVE(equal-weight) (§3b-i)",
        "RATIFIED vs keyword/co-movement screen (§3b-ii, deferred)",
    ))


def _cohort_fwd_mean(
    tickers: tuple[str, ...] | list[str], baskets: FrozenBaskets, price_fn: PriceFn, *,
    horizon_days: int, as_of: date, adjust: bool, benchmark: str,
) -> tuple[float | None, int]:
    """Mean forward return over a cohort, FORWARD-ONLY from the freeze date: entry = each name's
    entry_date (= freeze for a hold-none posture); a name whose entry precedes the freeze is SKIPPED
    (never a trailing/pre-freeze return); a name whose checkpoint (entry + horizon) is beyond
    ``as_of`` is SKIPPED (horizon not yet reached). ``adjust`` subtracts the benchmark per name."""
    freeze = date.fromisoformat(baskets.freeze_timestamp[:10])
    vals: list[float] = []
    for t in tickers:
        entry = date.fromisoformat(baskets.entry_dates.get(t, baskets.freeze_timestamp[:10]))
        if entry < freeze:
            continue  # forward-only: never measure from before the freeze (anti-hindsight)
        checkpoint = entry + timedelta(days=horizon_days)
        if checkpoint > as_of:
            continue  # horizon not yet reached — no forward data
        v = (_adj_return(price_fn, benchmark, t, entry, checkpoint) if adjust
             else _fwd_return(price_fn, t, entry, checkpoint))
        if v is not None:
            vals.append(v)
    return _mean(vals), len(vals)


def diagnostic_avoid_discipline(
    baskets: FrozenBaskets, price_fn: PriceFn, *, horizon_days: int, as_of: date,
    benchmark: str = "IWM",
) -> Diagnostic:
    """DIAGNOSTIC 1 — did declining to buy the committed tier cost or vindicate? The NAIVE
    (equal-weight-all) forward return vs hold-none (cash). Positive = costly (the tier rose),
    negative = vindicated. BETA-CONFOUNDED: largely a driver-beta / regime bet, NOT a test of
    selection skill."""
    raw, n = _cohort_fwd_mean(baskets.all_committed, baskets, price_fn, horizon_days=horizon_days,
                              as_of=as_of, adjust=False, benchmark=benchmark)
    adj, _ = _cohort_fwd_mean(baskets.all_committed, baskets, price_fn, horizon_days=horizon_days,
                              as_of=as_of, adjust=True, benchmark=benchmark)
    return Diagnostic(
        name="avoid-discipline", horizon_days=horizon_days, value=raw, n=n,
        confound=(f"{baskets.driver}-BETA-CONFOUNDED + regime-dependent — tests whether declining "
                  f"to buy the committed tier was costly or vindicated in THIS window, largely a "
                  f"{baskets.driver}-beta bet, NOT selection skill"),
        detail=(f"NAIVE-{len(baskets.all_committed)} equal-weight forward return raw(vs cash)="
                f"{'pending' if raw is None else f'{raw:+.1%}'}, vs {benchmark}="
                f"{'pending' if adj is None else f'{adj:+.1%}'}"))


def diagnostic_exposure_carry(
    baskets: FrozenBaskets, exposure_names: list[str], price_fn: PriceFn, *,
    horizon_days: int, as_of: date, benchmark: str = "IWM",
) -> Diagnostic:
    """DIAGNOSTIC 2 (the more informative) — does the machine's exposure GRADE carry forward info?
    The genuine-exposure names vs the other PASSED names, benchmark-adjusted forward-return
    DIVERGENCE. Both cohorts are AI-labelled, so the common AI-beta largely cancels — PARTIALLY
    beta-controlled. Positive divergence = the real-vs-not exposure read carries forward info. NOT
    an edge verdict."""
    exp = set(exposure_names)
    e_names = tuple(t for t in baskets.all_committed if t in exp)
    o_names = tuple(t for t in baskets.all_committed if t not in exp)
    me, ne = _cohort_fwd_mean(e_names, baskets, price_fn, horizon_days=horizon_days, as_of=as_of,
                              adjust=True, benchmark=benchmark)
    mo, no = _cohort_fwd_mean(o_names, baskets, price_fn, horizon_days=horizon_days, as_of=as_of,
                              adjust=True, benchmark=benchmark)
    div = None if me is None or mo is None else me - mo
    return Diagnostic(
        name="exposure-carry", horizon_days=horizon_days, value=div, n=ne + no,
        confound=(f"PARTIALLY beta-controlled — both cohorts are {baskets.driver}-labelled so the "
                  f"common {baskets.driver}-beta largely cancels in the divergence; isolates "
                  "whether the exposure GRADE (real vs not) carries forward info. The more "
                  "informative of the two — still NOT an edge verdict"),
        detail=(f"{len(e_names)} genuine-exposure {list(e_names)} adj="
                f"{'pending' if me is None else f'{me:+.1%}'} (n={ne}) "
                f"vs {len(o_names)} other-PASSED "
                f"adj={'pending' if mo is None else f'{mo:+.1%}'} (n={no}); divergence="
                f"{'pending' if div is None else f'{div:+.1%}'}"))


def layer_split_naive(
    baskets: FrozenBaskets, price_fn: PriceFn, *, horizon_days: int, as_of: date,
    benchmark: str = "IWM",
) -> LayerSplit:
    """The §4 layer-aware split of NAIVE-56 forward return: thin-layer
    (thermal/packaging/optical/HBM, where semantic-primary uniquely contributed) vs obvious-layer
    (chips/power/colo). NOT pooled — pooling would mask the thin-layer slice."""
    thin = tuple(t for t in baskets.all_committed if baskets.layer_of.get(t, "") in THIN_LAYERS)
    obvious = tuple(
        t for t in baskets.all_committed if baskets.layer_of.get(t, "") in OBVIOUS_LAYERS)
    mt, nt = _cohort_fwd_mean(thin, baskets, price_fn, horizon_days=horizon_days, as_of=as_of,
                              adjust=True, benchmark=benchmark)
    mo, no = _cohort_fwd_mean(obvious, baskets, price_fn, horizon_days=horizon_days, as_of=as_of,
                              adjust=True, benchmark=benchmark)
    return LayerSplit(horizon_days=horizon_days, thin_return=mt, obvious_return=mo,
                      n_thin=nt, n_obvious=no)


def naive_by_layer(
    baskets: FrozenBaskets, price_fn: PriceFn, *, horizon_days: int, as_of: date,
    benchmark: str = "IWM",
) -> tuple[LayerReturn, ...]:
    """Driver-AGNOSTIC §4 layer-aware split: the NAIVE (equal-weight) benchmark-adjusted forward
    return broken out by EACH distinct ``layer_of`` value — a value-chain layer for a chain driver,
    a parallel capability CATEGORY for a demand-shaped one (defense: attritable-air,
    defense-autonomy …). Forward-only from the freeze date; NOT pooled (pooling masks the
    per-category slice). The generic complement to the thin/obvious ``layer_split_naive``."""
    layers = sorted({baskets.layer_of.get(t, "unspecified") for t in baskets.all_committed})
    out: list[LayerReturn] = []
    for lyr in layers:
        names = [t for t in baskets.all_committed if baskets.layer_of.get(t, "unspecified") == lyr]
        m, n = _cohort_fwd_mean(names, baskets, price_fn, horizon_days=horizon_days, as_of=as_of,
                                adjust=True, benchmark=benchmark)
        out.append(LayerReturn(layer=lyr, mean_return=m, n=n))
    return tuple(out)


def measure_hold_none(
    baskets: FrozenBaskets, *, exposure_names: list[str], price_fn: PriceFn, horizon_days: int,
    as_of: date, benchmark: str = "IWM", onset_baselines: dict[str, str | None] | None = None,
) -> HoldNoneReport:
    """The EMPTY-BUY (zero-RATIFIED) measurement. Emits the RATIFIED-dependent spreads as UNDEFINED
    (never 0.0), plus the two VALID beta-confounded diagnostics + the layer-aware split (both the
    AI-datacenter thin/obvious view and the driver-agnostic per-category ``naive_by_layer``), all
    FORWARD-ONLY from the freeze date. Carries HOLD_NONE_HONESTY — NEVER an edge verdict."""
    return HoldNoneReport(
        driver=baskets.driver, as_of=as_of.isoformat(), freeze_timestamp=baskets.freeze_timestamp,
        horizon_days=horizon_days, undefined_measures=undefined_ratified_measures(baskets),
        avoid_discipline=diagnostic_avoid_discipline(baskets, price_fn, horizon_days=horizon_days,
                                                     as_of=as_of, benchmark=benchmark),
        exposure_carry=diagnostic_exposure_carry(baskets, exposure_names, price_fn,
                                                 horizon_days=horizon_days, as_of=as_of,
                                                 benchmark=benchmark),
        layer_split=layer_split_naive(baskets, price_fn, horizon_days=horizon_days, as_of=as_of,
                                      benchmark=benchmark),
        naive_by_layer=naive_by_layer(baskets, price_fn, horizon_days=horizon_days, as_of=as_of,
                                      benchmark=benchmark),
        onset_baselines=dict(onset_baselines or {}), honesty_label=HOLD_NONE_HONESTY)


# --------------------------------------------------------------------------------------------------
# Component 4 — the early-detection test (§5): forward-log co-movement onset; early vs late
# --------------------------------------------------------------------------------------------------
MembershipFn = Callable[[str, date], bool]  # (ticker, as_of) -> in Component A's theme cluster?


def update_onsets(
    records: list[RatificationRecord], ledger_path: Path, membership_fn: MembershipFn, *,
    as_of: date,
) -> list[RatificationRecord]:
    """For each RATIFIED record with null onset, check Component A membership as of ``as_of``
    (read-only); if now in the cluster, APPEND a new ledger row stamping ``comovement_onset_date``
    (append-only). A name that never co-moves keeps null — a logged null, NOT an error. Returns the
    new rows."""
    new: list[RatificationRecord] = []
    for r in current_dispositions(records).values():
        if (r.disposition is Disposition.RATIFIED and r.comovement_onset_date is None
                and membership_fn(r.ticker, as_of)):
            updated = r.model_copy(update={"comovement_onset_date": as_of})
            append_record(ledger_path, updated)
            new.append(updated)
    return new


def early_vs_late(
    record: RatificationRecord, *, price_fn: PriceFn, benchmark: str, forward_asof: date,
) -> dict[str, object]:
    """Benchmark-adjusted return ratification→onset (EARLY) vs onset→forward (LATE) for a ratified
    enabler (§5). Onset null (never co-moved) → early spans ratification→forward, late is None (a
    logged null). The semantic-primary thesis test: did EARLY entry beat entry once OBVIOUS."""
    entry = record.ratification_date
    if record.comovement_onset_date is None:
        return {"ticker": record.ticker, "onset": None,
                "early_adj": _adj_return(price_fn, benchmark, record.ticker, entry, forward_asof),
                "late_adj": None, "note": "never co-moved (logged null)"}
    onset = record.comovement_onset_date
    return {"ticker": record.ticker, "onset": onset.isoformat(),
            "early_adj": _adj_return(price_fn, benchmark, record.ticker, entry, onset),
            "late_adj": _adj_return(price_fn, benchmark, record.ticker, onset, forward_asof),
            "note": ""}


def watchlist_onset_baselines(
    watchlist: tuple[str, ...] | list[str], membership_fn: MembershipFn, *,
    as_of: date,
) -> dict[str, str | None]:
    """Component-4 baseline for the re-underwrite cohort (§5, read-only): for each watchlist name,
    the co-movement onset baseline = ``as_of`` if it is ALREADY in Component A's cluster (the
    market has caught it), else None — not-yet-co-moving, the EXPECTED state for an early enabler
    and the anchor against which future earliness is measured when its trigger fires. No spread,
    just the anchor."""
    return {t: (as_of.isoformat() if membership_fn(t, as_of) else None) for t in watchlist}


# --------------------------------------------------------------------------------------------------
# Live adapters — thin READ-ONLY wrappers over the committed pipeline (used once dispositions land)
# --------------------------------------------------------------------------------------------------
def eod_close_fn(eod: EodClient, *, backstep_days: int = 5) -> PriceFn:
    """A PriceFn over the committed grouped-daily EOD (read-only). On a non-trading ``day`` it steps
    back up to ``backstep_days`` to the nearest prior trading close. Returns None if no bar
    (fail-soft — the name is dropped from that checkpoint, never fabricated)."""
    def close_on(ticker: str, day: date) -> float | None:
        for i in range(backstep_days + 1):
            b = eod.grouped_daily(day - timedelta(days=i)).get(ticker)
            if b is not None and b.close > 0:
                return b.close
        return None
    return close_on


class _HasMembers(Protocol):
    members: list[str]


def component_a_membership_fn(detect: Callable[[date], list[_HasMembers]]) -> MembershipFn:
    """Wrap Component A (read-only): ``membership(ticker, as_of)`` = is the ticker in ANY admitted
    theme's members when detection is run as of that date. ``detect(as_of)`` calls the committed
    ``detect_themes`` — this harness NEVER modifies detection."""
    def member(ticker: str, as_of: date) -> bool:
        return any(ticker in th.members for th in detect(as_of))
    return member
