"""Cap-band universe builder — the start of the real validation clock.

Market cap = latest EOD close × XBRL shares outstanding, filtered to the configured small/mid band
(US exchanges only). It uses the **breadth tools** so it never makes thousands of per-name calls:
one Polygon grouped-daily call (cached) for every close, and a handful of EDGAR ``frames`` calls for
every filer's shares. Membership is snapshotted with an ``as_of`` so future backtests aren't
survivorship-biased.

Market cap uses the issuer's *total* shares against each security's price, EXCEPT where the issuer
lists more than one class: there each line is sized by its own ``share_class_shares_outstanding``,
because the total gave every class the whole company's cap (2026-09-01). A line with no per-class
count is dropped at ``dual_class_unresolved`` rather than sized by the issuer-wide number.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from vinci.config import Config, get_config
from vinci.edgar import EdgarClient
from vinci.edgar.client import SHARES_TAG_WAVG
from vinci.eod import EodClient, PolygonEodClient
from vinci.eod.client import CARRY_DAYS, carry_forward
from vinci.netcache import HttpError
from vinci.resolver import EntityResolver
from vinci.resolver.aliases import detect_renames, load_aliases, write_aliases
from vinci.resolver.instrument import FOREIGN_PRIVATE_ISSUER_FORMS
from vinci.schemas.data_record import Identity
from vinci.schemas.envelope import DataField, SourceTier
from vinci.store import NO_ROW_DROP_TABLES, Store

_QUARTER_ENDS = ((3, 31), (6, 30), (9, 30), (12, 31))
_FILING_LAG_DAYS = 40  # don't ask for a quarter's shares frame until it's plausibly filed


def benchmark_identity(symbol: str) -> Identity:
    """Synthetic identity for a benchmark ETF (not a SEC issuer → not resolver-resolved)."""
    return Identity(
        internal_id=f"IDX-{symbol}", issuer_id="IDX", cik="", ticker=symbol, mic="ARCX",
        exchange="ETF", eod_symbol=symbol, name=f"{symbol} (benchmark)",
    )


def recent_share_periods(reference_date: date, *, n: int = 5) -> list[str]:
    """The ``n`` most recent quarter-instant frame keys (e.g. ``CY2026Q1I``), oldest→newest."""
    keys: list[tuple[date, str]] = []
    for yy in range(reference_date.year - 2, reference_date.year + 2):
        for q, (m, d) in enumerate(_QUARTER_ENDS, start=1):
            qe = date(yy, m, d)
            if qe <= reference_date - timedelta(days=_FILING_LAG_DAYS):
                keys.append((qe, f"CY{yy}Q{q}I"))
    keys.sort()
    return [k for _, k in keys[-n:]]


def latest_close_and_adv(
    eod: EodClient, reference_date: date, *, lookback_days: int = 90
) -> tuple[dict[str, float], dict[str, float]]:
    """({ticker: latest close}, {ticker: 90d avg daily $-volume}) from cached grouped-daily bars."""
    closes: dict[str, float] = {}
    dollar_vol: dict[str, float] = defaultdict(float)
    n_days: dict[str, int] = defaultdict(int)
    d = reference_date
    horizon = reference_date - timedelta(days=lookback_days)
    while d >= horizon:
        for t, b in eod.grouped_daily(d).items():
            closes.setdefault(t, b.close)  # most-recent close wins
            dollar_vol[t] += b.close * b.volume
            n_days[t] += 1
        d -= timedelta(days=1)
    adv = {t: dollar_vol[t] / n_days[t] for t in dollar_vol if n_days[t] > 0}
    return closes, adv


def incumbent_lines(snapshots_dir: Path, table: str,
                    reference_date: date) -> tuple[frozenset[str], date | None]:
    """The lines a band's COMMITTED snapshot admitted — the record the forward return is already
    accumulating against — and the date it was built, or ``(∅, None)`` when there is none to keep.

    Read from the committed file, not the store: the store is git-ignored and starts empty on every
    CI run, while the file is the population that was signed off and screened. Only a snapshot
    dated ON OR BEFORE ``reference_date`` counts — a backdated rebuild must not be steered by a
    population chosen later. A malformed row raises; a guessed incumbent would be worse than none.
    """
    path = snapshots_dir / f"{table}.jsonl"
    if not path.exists():
        return frozenset(), None
    by_date: dict[date, set[str]] = defaultdict(set)
    for line in path.read_text().splitlines():
        if line.strip() and (row := json.loads(line))["in_universe"]:
            by_date[date.fromisoformat(row["as_of"])].add(row["internal_id"])
    usable = [d for d in by_date if d <= reference_date]
    if not usable:
        return frozenset(), None
    return frozenset(by_date[max(usable)]), max(usable)


def admit_security_type(ptype: str | None, allowed: tuple[str, ...]) -> bool:
    """Instrument-type ALLOWLIST test (Axis 2). Admit ONLY listed operating-co equity types.

    Fail-closed: a blank/unknown/missing ``ptype`` (``None``) is never in the allowlist, so it is
    excluded — never silently admitted (the same rule as a blank SIC). An allowlist, not a denylist:
    a structured-product type we have not enumerated defaults to *excluded*.
    """
    return ptype in allowed


# The ONLY snapshot artifacts build_universe writes: upsert_security → issuers + securities,
# record_universe → universe_snapshot. It exports EXACTLY this set so a stale working DB can never
# rewrite candidate_records / decision_ledger via the full dump (the 2026-07-13 ledger-DELETE
# near-miss). Enumerated from the store calls below, not guessed.
BUILD_UNIVERSE_TABLES: tuple[str, ...] = ("issuers", "securities", "universe_snapshot")

#: The same export set for the PARALLEL THEME BAND (operator ruling 2026-08-31): the entity master
#: is SHARED and accumulate-only (a megacap identity is a fact about the world, not about a band),
#: while membership lands in the band's own point-in-time table. Deriving this from the primary
#: tuple keeps the two in step if the export set ever grows.
BUILD_THEME_UNIVERSE_TABLES: tuple[str, ...] = tuple(
    "theme_universe_snapshot" if t == "universe_snapshot" else t for t in BUILD_UNIVERSE_TABLES)

#: band -> (config attribute, store table, stats filename). The BUILDER IS BAND-AGNOSTIC: every
#: gate below reads `band`, so the theme band gets the identical operating-company /
#: tradeability / instrument-type discipline, differing ONLY in the cap bounds it was given.
UNIVERSE_BANDS: dict[str, tuple[str, str, str]] = {
    "primary": ("universe", "universe_snapshot", "universe_stats.json"),
    "theme": ("theme_universe", "theme_universe_snapshot", "theme_universe_stats.json"),
}

#: The subset of :data:`BUILD_UNIVERSE_TABLES` that may never SHRINK, DERIVED from the store's own
#: declaration rather than re-listed here — a hand-copied list is one edit away from silently
#: missing a table the day another accumulate-only one joins the export.
BUILD_UNIVERSE_SEED_TABLES: tuple[str, ...] = tuple(
    t for t in BUILD_UNIVERSE_TABLES if t in NO_ROW_DROP_TABLES)


#: Polygon instrument types whose PRICE is quoted per depositary receipt rather than per ordinary
#: share. The share count used for market cap must be denominated in the same unit as the price.
DEPOSITARY_TYPES: tuple[str, ...] = ("ADRC", "GDR")

#: The instrument types that are a foreign issuer's line by the feed's own record: a depositary
#: receipt, or a foreign ordinary share. See `UniverseConfig.exclude_foreign_private_issuers`.
FOREIGN_LINE_TYPES: tuple[str, ...] = (*DEPOSITARY_TYPES, "OS")

#: EVERY drop this builder can make, in funnel order. Enumerated rather than described, because a
#: stage missing from the thin grain is a stage with no evidence trail — which just MOVES the blind
#: spot instead of closing it. Each is emitted with the one input that decided it.
DROP_STAGES: tuple[str, ...] = (
    "no_price", "no_shares", "ads_count_unresolved", "out_of_band", "below_adv_floor",
    "unknown_sic", "non_operating", "unknown_type", "non_common_equity", "foreign_private_issuer",
    "fpi_status_unread", "duplicate_class",
)


def build_universe(
    config: Config | None = None, *, reference_date: date, share_periods: list[str] | None = None,
    retain_run_id: str | None = None, retain_dir: Path | None = None, band_name: str = "primary",
) -> dict[str, int]:
    """Build + snapshot a cap-band universe as of ``reference_date``. Returns a stats summary.

    ``band_name`` selects WHICH population is built: ``"primary"`` (the forward-validation
    population every decision-path consumer reads) or ``"theme"`` (the parallel larger band read
    only at the theme altitude — operator ruling 2026-08-31). The two never share a table, so a
    theme build cannot add a row to the population the spread is accumulating against.

    RETENTION (thin grain). Every name this builder DROPS gets a row naming the stage, the reason,
    and the single input that decided it. This is the stage nothing has ever measured: a name
    filtered here never reaches the screen, so it has no gate outcomes and would otherwise leave no
    trace at all — and `universe.py`'s market-cap stamp (STATE S3) is exactly a defect at this
    stage. Admitted names are NOT retained here; the screen records them at the candidate grain.
    """
    if (retain_run_id is None) != (retain_dir is None):
        raise ValueError(
            "retain_run_id and retain_dir must be given together — one without the other builds "
            "retention rows and discards them while reporting them as retained")
    cfg = config or get_config()
    cfg.ensure_dirs()
    resolver = EntityResolver.from_config(cfg)
    eod = PolygonEodClient.from_config(cfg)
    edgar = EdgarClient.from_config(cfg)
    if band_name not in UNIVERSE_BANDS:
        raise ValueError(f"unknown universe band {band_name!r} — expected one of "
                         f"{sorted(UNIVERSE_BANDS)}")
    band_attr, band_table, stats_filename = UNIVERSE_BANDS[band_name]
    band = getattr(cfg, band_attr)
    export_tables = (BUILD_UNIVERSE_TABLES if band_name == "primary"
                     else BUILD_THEME_UNIVERSE_TABLES)
    # READ BEFORE THE EXPORT BELOW OVERWRITES IT — the population this build is about to replace
    incumbents, incumbent_as_of = incumbent_lines(cfg.snapshots_dir, band_table, reference_date)

    closes, adv = latest_close_and_adv(eod, reference_date)
    sec_types = eod.security_types()  # instrument-type axis (one cached bulk reference pull)
    # ADS-DENOMINATED COUNTS for depositary receipts (2026-08-31). An ADR's price is per ADS while
    # its XBRL count is per ORDINARY share, and nothing converted between them: TSM computed
    # $10,635B against Polygon's own $2,165B — a ~5x error that pushed it past the theme band's
    # $10T ceiling and out of EVERY band. Fetched only for the ADR/GDR tickers that have a close
    # (~375 on US venues, cached a day), because the details endpoint is per-ticker.
    adr_tickers = sorted(t for t, ty in sec_types.items()
                         if ty in DEPOSITARY_TYPES and t in closes)
    ads_counts = eod.share_class_counts(adr_tickers)
    periods = share_periods or recent_share_periods(reference_date)
    # PERIOD-AVERAGE TIER ON, here only (2026-08-31): the cap band is a COARSE gate, and a filer
    # publishing no instant count was being dropped entirely — 142 operating equities above $100M
    # ADV, 104 recoverable this way (META among them). Every value carries its tag so the row it
    # stamps says which kind of number it is.
    shares, share_tag = edgar.shares_outstanding_with_provenance(
        periods, include_period_average=True)

    # IMPORTED HERE, NOT AT MODULE SCOPE. `vinci.screens.__init__` imports `run`, which imports
    # `vinci.universe` — so a module-scope import of anything under `vinci.screens` makes importing
    # `vinci.universe` FIRST a circular-import crash. It only fires on that import order, which is
    # why the suite stayed green and a real `build_universe` run did not.
    from vinci.screens.retention import StampedInput, UniverseRow, append_rows

    stats: Counter[str] = Counter()
    dropped: list[UniverseRow] = []

    def _drop(ticker: str, stage: str, reason: str, inp: StampedInput) -> None:
        stats[stage] += 1
        if retain_run_id is not None:
            dropped.append(UniverseRow(
                ticker=ticker, run_id=retain_run_id, reference_date=reference_date,
                stage=stage, reason=reason, deciding_input=inp))

    with Store(cfg.db_path) as store:
        # SEED THE ACCUMULATE-ONLY MASTER BEFORE TOUCHING IT (2026-08-24). `data/vinci.db` is
        # git-ignored, so on any fresh checkout — every CI run — this store starts EMPTY. The loop
        # below upserts only what THIS fetch admits, and the export at the end then writes that
        # subset over `issuers.jsonl` / `securities.jsonl`, which are accumulate-only: an identity
        # is never pruned, because the entity master has to resolve a ledgered name after it leaves
        # the universe. The no-row-drop guard therefore REFUSED the write, and the weekly screen
        # failed four consecutive weeks (2026-08-03 through 08-24) with the served queue frozen:
        #
        #   ROW-DROP on issuers.jsonl: writing 1810 row(s) over 2304 on disk
        #   would drop 503 existing row(s) by PK.
        #
        # It passed on a laptop the whole time, because a dev store already holds the accumulation
        # — the "green everywhere except where it matters" shape. `run_weekly` does seed the store,
        # but at its own line AFTER this function has already exported; the seed has to happen
        # HERE, inside the context that writes.
        #
        # SEEDS ONLY THE TABLES THAT MUST NOT SHRINK. `universe_snapshot` is POINT-IN-TIME — the
        # committed file holds exactly one `as_of` — so loading it back would make it accumulate
        # dates it was never meant to keep, turning a fix for one table into a silent semantic
        # change in another.
        store.rebuild_from_snapshots(cfg.snapshots_dir, tables=BUILD_UNIVERSE_SEED_TABLES)
        # FULL replace, THIS BAND ONLY — a rebuild is a clean snapshot, not an accretion
        admitted: list[tuple[Identity, float, str, bool]] = []

        def _one_line_per_issuer(
            rows: list[tuple[Identity, float, str, bool]]
        ) -> list[tuple[Identity, float, str, bool]]:
            """ONE ISSUER, ONE LINE — keep the most TRADEABLE class and drop its siblings.

            WHY. Sizing each class correctly (#546) stopped the caps double-counting, but it did
            not stop the same COMPANY entering the population twice: ZG and Z were two names, so
            one issuer's forward return could enter the BUY-AVOID spread twice and count double in
            the only number that proves this fund works. 12 duplicate lines in the primary band and
            7 in the theme band, on the 2026-08-24 build.

            THE SURVIVOR IS THE HIGHEST-ADV LINE, and that is a face-validity choice measured
            against the alternative, never tuned on returns. Liquidity is the right axis because a
            position can only ever be taken in the line the fund can actually trade, and ADV is
            already a gate here. Against "keep the largest cap" the two rules disagree on 4 of the
            17 issuers, and ADV is right on all four:

                ADAMAS   ADV keeps ADAM (the common); CAP would keep ADAMK — a BOND
                HEICO    ADV keeps HEI  ($177M/day); CAP would keep HEI.A ($79M/day)
                UNDER A. ADV keeps UAA  ($52M/day);  CAP would keep UA    ($19M/day)
                GREIF    ADV keeps GEF  ($19M/day);  CAP would keep GEF.B ($8M/day)

            The ADAMAS case is the one that settles it: a cap rule would have deleted the real
            common and kept the mistyped senior note as the issuer's sole representative.

            Ties break on market cap then ticker, so the choice is deterministic and a re-run can
            never silently swap which line the ledger accumulates against.

            THE INCUMBENT KEEPS THE SLOT WHILE IT CLEARS EVERY GATE (2026-10-27). ADV is a 90-day
            average, so a NEW run could still swap the line — and #549's pre-registered falsifier
            fired: U-Haul entered the population as UHAL on 2026-08-24, and on 2026-09-22 UHAL.B
            fell below the $10B ceiling, entered the band, and took the slot on ADV ($22.1M/day
            against $11.9M) while UHAL still cleared every gate. One company's record then spanned
            two tickers. So the line the committed snapshot admitted ranks first; ADV decides only
            among lines with no record, or once the incumbent has failed a gate and left `rows`.
            """
            by_cik: dict[str, list[tuple[Identity, float, str, bool]]] = defaultdict(list)
            for row in rows:
                by_cik[row[0].cik].append(row)
            kept: list[tuple[Identity, float, str, bool]] = []
            for lines in by_cik.values():
                ranked = sorted(
                    lines,
                    key=lambda r: (r[0].internal_id not in incumbents,
                                   -adv.get(r[0].eod_symbol, 0.0), -r[1], r[0].eod_symbol))
                winner = ranked[0]
                kept.append(winner)
                for loser in ranked[1:]:
                    if (winner[0].internal_id in incumbents
                            and loser[0].internal_id not in incumbents
                            and adv.get(loser[0].eod_symbol, 0.0)
                            > adv.get(winner[0].eod_symbol, 0.0)):
                        # ADV alone would have chosen the loser — say that the record decided
                        _drop(loser[0].eod_symbol, "duplicate_class",
                              f"the incumbent line {winner[0].eod_symbol} — admitted in the "
                              f"{incumbent_as_of} population — keeps its issuer's slot while it "
                              f"clears every gate, though this line trades "
                              f"${adv.get(loser[0].eod_symbol, 0.0) / 1e6:,.1f}M/day against its "
                              f"${adv.get(winner[0].eod_symbol, 0.0) / 1e6:,.1f}M; switching "
                              f"lines would split one issuer's forward record across two tickers",
                              StampedInput(value=winner[0].internal_id, as_of=incumbent_as_of,
                                           source=f"{band_table}.jsonl (the incumbent line)"))
                        continue
                    _drop(loser[0].eod_symbol, "duplicate_class",
                          f"another listed class of the same issuer is more tradeable — "
                          f"{winner[0].eod_symbol} carries "
                          f"${adv.get(winner[0].eod_symbol, 0.0) / 1e6:,.1f}M/day against this "
                          f"line's ${adv.get(loser[0].eod_symbol, 0.0) / 1e6:,.1f}M; one issuer "
                          f"contributes one line so a single company's forward return cannot "
                          f"enter the spread twice",
                          StampedInput(value=adv.get(loser[0].eod_symbol, 0.0),
                                       as_of=reference_date, source="Polygon ADV"))
            return kept

        store.clear_universe(band=band_name)
        # (was clear-only-`reference_date`, which left prior as_of generations on a persistent DB)
        # ONE COUNT PER CLASS, NOT ONE COUNT PER ISSUER (2026-09-01). A filed XBRL count is keyed
        # by CIK, so every listed class of one issuer was sized with the SAME number and each line
        # carried the WHOLE company's cap: Alphabet appeared four times for $9,672B against a real
        # $3,947B, and CENT/CENTA, UA/UAA, LEN/LEN.B, ZG/Z all double-counted the same way. The
        # reference count is per-class (`share_class_shares_outstanding`; GOOGL reports 5,868M
        # against a 12,230M `weighted_shares_outstanding`), so multi-class issuers are sized from
        # it. Materialised because the CIK's OTHER lines have to be known before the first one is
        # sized — a streaming pass cannot tell a second class from a first.
        idents = list(resolver.iter_universe(band.exchanges))
        # A SIBLING ONLY COUNTS IF IT IS ITSELF ADMISSIBLE EQUITY — two gates, both measured.
        # PRICED, because an unpriced sibling is dropped at `no_price` and never competes for the
        # cap. ADMITTED TYPE, because a CIK's other listed lines are usually NOT share classes:
        # the first draft counted any two securities sharing a CIK and swept in every SPAC unit,
        # warrant and note, routing 1,760 lines down this path (935 sized, 825 dropped) against
        # the 46 that are real classes. Those lines still drop — they always did — but at
        # `unknown_type` / `non_common_equity` / `no_shares`, which is what their exclusion is
        # actually about; `dual_class_unresolved` would have claimed 825 of them and made the
        # funnel lie about why. Same gate, same reason as the fallback's in #543.
        def _admissible(i: Identity) -> bool:
            return (i.eod_symbol in closes
                    and admit_security_type(sec_types.get(i.eod_symbol),
                                            band.allowed_security_types))

        multi_class_ciks = {c for c, n in Counter(
            i.cik for i in idents if _admissible(i)).items() if n > 1}
        class_counts = eod.share_class_counts(sorted(
            i.eod_symbol for i in idents if i.cik in multi_class_ciks and _admissible(i)))

        def _per_class_count(i: Identity) -> float | None:
            """This line's OWN share count, or None to leave its sizing exactly as it was.

            STRICTLY NON-REGRESSIVE, and that is a deliberate retreat from a first draft that
            DROPPED a multi-class line whose per-class count would not resolve. Refusing to size a
            name from a number known to be wrong is the right instinct, but the sibling test is a
            heuristic and it misfires: ACGL — Arch Capital, $34.5B of genuine common — publishes no
            `share_class_shares_outstanding`, while ACGLN, a PREFERRED depositary line typed `CS`
            by the same feed, publishes one. The heuristic read that as two classes and excluded
            the common. A name wrongly EXCLUDED from the validation population is as damaging as
            one wrongly admitted, and it is the harder error to notice.

            So a line resolves or it keeps the behaviour it already had. The lines that do not
            resolve are the ones that were never share classes — ADAMK is "Adamas Trust, Inc.
            9.600% Senior Notes", GOOGM/GOOGN are "Alphabet Inc. Depositary Shares" — and they
            stay mis-sized exactly as they are today. Removing them is a real improvement and it
            belongs to instrument typing, on its own evidence: it is not this change's to take as
            a side effect.
            """
            return class_counts.get(i.eod_symbol) if i.cik in multi_class_ciks else None
        for ident in idents:
            stats["considered"] += 1
            close = closes.get(ident.eod_symbol)
            sh = shares.get(ident.cik)
            if close is None:
                _drop(ident.eod_symbol, "no_price", "no latest close in the grouped-daily pull",
                      StampedInput(value=None, source="Polygon grouped-daily"))
                continue
            # THE COUNT MUST BE DENOMINATED IN THE PRICE'S OWN UNIT, and WHICH count that is
            # decides which absence is fatal — so the instrument type is read BEFORE any
            # share-count gate. For a depositary receipt the traded unit is the ADS: the ADS count
            # is the right input, no ratio arithmetic is needed, and THE XBRL COUNT IS NEVER READ.
            # Gating an ADR on the XBRL count first (the first draft of this change) demanded an
            # input it then discarded: measured, EIGHT of the nine names lost at `no_shares` —
            # NVO, SONY, ERIC, TAK, GRAB, JD, SE, BIDU — carry a perfectly good ADS count and were
            # being dropped anyway. Only AZN genuinely has neither.
            is_depositary = sec_types.get(ident.eod_symbol) in DEPOSITARY_TYPES
            if is_depositary:
                # an ADR whose ADS count will not resolve is DROPPED LOUDLY — assuming
                # 1 ADS = 1 ordinary is exactly the silent error this whole change removes
                ads = ads_counts.get(ident.eod_symbol)
                if ads is None:
                    _drop(ident.eod_symbol, "ads_count_unresolved",
                          "depositary receipt with no ADS-denominated share count — refusing to "
                          "assume 1 ADS = 1 ordinary share",
                          StampedInput(value=None, as_of=reference_date,
                                       source="Polygon share_class_shares_outstanding"))
                    continue
                shares_used = ads
                stats["ads_count_used"] += 1
            elif (per_class := _per_class_count(ident)) is not None:
                # BEFORE the `sh is None` test, because the defect is a filed count that IS
                # present and IS wrong for this line — falling through to it is the bug.
                shares_used = per_class
                stats["dual_class_count_used"] += 1
            elif sh is None:
                # FALLBACK, NEVER A REPLACEMENT (2026-09-01). A name with a filed count keeps
                # it — this branch is reached only when EVERY XBRL tier came back empty, so it
                # can add names and can never move an admitted cap.
                #
                # MEASURED before building: of the 1,240 names still lost here after #541, 711
                # are FUND/UNIT/WARRANT types the instrument allowlist rejects anyway, leaving
                # 529 operating equities of which 23 trade above $100M/day. Those 23 are NOT
                # an IFRS problem — the largest are MULTI-CLASS US FILERS (V, BRK.B, STZ, TSN,
                # DUOL, PLNT, SEI, FWONK, ARES, BAM) whose cover-page count is
                # dimension-qualified and so never reaches the XBRL frames. 19 of 22 probed
                # carry a Polygon share count; an `ifrs-full` branch would have reached at
                # most 5 and none of the largest. Fetched ONE ticker at a time and only for
                # allowlisted instrument types, so the call is made only where it can pay.
                fallback: float | None = None
                # the reference is consulted ONLY for instrument types the universe would admit,
                # so the drop reason must say WHICH of the two sources actually ran — a retention
                # row asserting a lookup that never happened is a fabricated evidence trail
                consulted = admit_security_type(sec_types.get(ident.eod_symbol),
                                                band.allowed_security_types)
                if consulted:
                    fallback = eod.share_class_counts([ident.eod_symbol]).get(ident.eod_symbol)
                if fallback is None:
                    reason = ("no share count in any XBRL tier and none from the share-class "
                              "reference either" if consulted else
                              "no share count in any XBRL tier; the share-class reference was NOT "
                              "consulted (instrument type is not admitted, so the name is "
                              "excluded regardless)")
                    _drop(ident.eod_symbol, "no_shares", reason,
                          StampedInput(value=None,
                                       source=("EDGAR share frames (instant tiers + period "
                                               "average) + Polygon share class" if consulted else
                                               "EDGAR share frames (instant tiers + period "
                                               "average)")))
                    continue
                shares_used = fallback
                stats["polygon_count_fallback"] += 1
            else:
                shares_used = sh
            market_cap = close * shares_used
            # WHICH KIND OF SHARE COUNT DECIDED THIS NAME — computed BEFORE the band test, because
            # the drop path needs it too (review 2026-08-31): the period-average tier newly sizes
            # names that then fall OUT of band, and a retention row claiming a filed EDGAR count
            # as its deciding input would misattribute an exclusion the approximation made.
            tag = share_tag.get(ident.cik, "")
            # a multi-class line is sized from the reference, not from any XBRL tier, so the
            # filed tag must not label it — it would count the line as a period-average admission
            # and misattribute an out-of-band drop to an approximation that never ran
            approximate = (not is_depositary and _per_class_count(ident) is None
                           and tag == SHARES_TAG_WAVG)
            if is_depositary:
                shares_source = ("Polygon close x Polygon share_class_shares_outstanding "
                                 "(ADS-denominated)")
            elif _per_class_count(ident) is not None:
                shares_source = ("Polygon close x Polygon share_class_shares_outstanding "
                                 "(PER-CLASS - issuer lists more than one class)")
            elif sh is None:
                shares_source = ("Polygon close x Polygon share_class_shares_outstanding "
                                 "(FALLBACK - no filed count in any XBRL tier)")
            else:
                shares_source = (f"Polygon close x EDGAR {tag}"
                                 + (" (PERIOD AVERAGE - approximate share count)"
                                    if approximate else ""))
            if not (band.market_cap_min_usd <= market_cap <= band.market_cap_max_usd):
                if approximate:
                    stats["out_of_band_period_average"] += 1
                _drop(ident.eod_symbol, "out_of_band",
                      f"market cap {market_cap / 1e6:,.1f}M outside "
                      f"[{band.market_cap_min_usd / 1e6:,.0f}M, "
                      f"{band.market_cap_max_usd / 1e6:,.0f}M]",
                      StampedInput(value=market_cap, as_of=reference_date,
                                   source=shares_source))
                continue
            if (a := adv.get(ident.eod_symbol, 0.0)) < band.adv_floor_usd:
                _drop(ident.eod_symbol, "below_adv_floor",
                      f"ADV ${a / 1e6:,.2f}M below the ${band.adv_floor_usd / 1e6:,.1f}M floor",
                      StampedInput(value=a, as_of=reference_date, source="Polygon ADV"))
                continue  # tradeability gate
            # Operating-companies-only gate — TWO independent structural axes, both fail-CLOSED on a
            # missing value (exclude what we cannot confirm; never silently admit). SIC is fetched
            # only for names that already clear cap+ADV — the would-be-admitted set.
            #
            # Axis 1 — issuer BUSINESS type (EDGAR SIC). A BLANK/unknown SIC is excluded, not
            # admitted: a blank SIC is exactly how a BDC/fund slips a denylist (`None` is never `in`
            # the exclude set — CION, OTF). Then drop the confirmed fund/shell codes.
            sic, sic_desc = resolver.sic_for(ident.cik)
            if sic is None:
                # cannot confirm operating-co → excluded, not admitted
                _drop(ident.eod_symbol, "unknown_sic", "no SIC on the EDGAR issuer record",
                      StampedInput(value=None, source="EDGAR submissions SIC"))
                continue
            if sic in band.excluded_sic_codes:
                # ETF/ETP/fund/blank-check — a basket, not a business
                _drop(ident.eod_symbol, "non_operating", f"SIC {sic} ({sic_desc or '?'}) excluded",
                      StampedInput(value=str(sic), as_of=reference_date,
                                   source="EDGAR submissions SIC"))
                continue
            # Axis 2 — security INSTRUMENT type (Polygon). An ALLOWLIST of operating-company common
            # equity, fail-CLOSED, with the two exclusion reasons counted separately:
            #   • a CONFIRMED non-equity type (ETN/ETF/ETV/ETS/FUND/SP/PFD/RIGHT/WARRANT/UNIT) — a
            #     basket/derivative. This catches an ETN spliced onto its bank issuer (SHNY=ETS →
            #     Bank of Montreal: ticker→CIK is correct, just not common equity).
            #   • a MISSING type — absent from Polygon's current reference, i.e. recently delisted
            #     (these carry stale bars the 90-day price gate still admitted); flagged, excluded.
            ptype = sec_types.get(ident.eod_symbol)
            if not admit_security_type(ptype, band.allowed_security_types):
                stage = "unknown_type" if ptype is None else "non_common_equity"
                _drop(ident.eod_symbol, stage,
                      f"security type {ptype or 'MISSING'} not in the operating-equity allowlist",
                      StampedInput(value=(ptype if ptype else None), as_of=reference_date,
                                   source="Polygon security reference"))
                continue
            # FOREIGN PRIVATE ISSUERS (operator ruling 2026-10-27; the one switch is
            # `exclude_foreign_private_issuers`). The feed's type decides a depositary receipt or a
            # foreign ordinary without a call; otherwise the issuer's latest periodic report — the
            # submissions index `sic_for` has just read — decides.
            if band.exclude_foreign_private_issuers:
                if ptype in FOREIGN_LINE_TYPES:
                    _drop(ident.eod_symbol, "foreign_private_issuer",
                          f"the feed types this line {ptype}, a foreign issuer's line — foreign "
                          f"private issuers are out of the primary population until FPI "
                          f"readiness lands (operator ruling 2026-10-27)",
                          StampedInput(value=ptype, as_of=reference_date,
                                       source="Polygon security reference"))
                    continue
                try:
                    report = resolver.latest_report(ident.cik, reference_date)
                except HttpError as exc:
                    # AN UNREAD INDEX IS NOT A DOMESTIC FILER (#828, round 1): the line is held
                    # out under its own reason and counted, never admitted by default.
                    _drop(ident.eod_symbol, "fpi_status_unread",
                          f"the issuer's filing index could not be read, so whether it files as a "
                          f"foreign private issuer is unknown — held out, never admitted by "
                          f"default ({exc})",
                          StampedInput(value=None, source="SEC submissions index"))
                    continue
                if report is not None and report[0] in FOREIGN_PRIVATE_ISSUER_FORMS:
                    _drop(ident.eod_symbol, "foreign_private_issuer",
                          f"the issuer's latest periodic report is a {report[0]} (filed "
                          f"{report[1].isoformat()}), so it files as a foreign private issuer — "
                          f"out of the primary population until FPI readiness lands (operator "
                          f"ruling 2026-10-27)",
                          StampedInput(value=report[0], as_of=report[1],
                                       source=f"SEC {report[0]} {report[2]} (latest periodic "
                                              f"report)"))
                    continue
            # Axis 3 — what the line IS in the ISSUER'S words (2026-10-27). The feed types some debt
            # and preferred `CS` — ADAMK and TMUSI among 58 debt lines of its 2026-10-17 pull, and
            # MCHPP, a preferred depositary that sat in this population on 2026-08-24 and 09-22 — so
            # Axis 2 admits them. The issuer's latest cover page registers every 12(b) security by
            # symbol and title; a line it registers as debt, or as preferred beside a common traded
            # under another symbol, leaves here, at the same stage as a correctly typed non-equity
            # line (the allowlist already excludes `PFD`). An unread cover, an absent symbol or any
            # other title changes nothing (`EntityResolver.registered_line`). Read for `CS` only,
            # the one type the feed has been seen to mis-assign.
            if (ptype == "CS" and (reg := resolver.registered_line(
                    ident.cik, ident.ticker, reference_date)) is not None
                    and (cls := reg.excluded_class) is not None):
                _drop(ident.eod_symbol, "non_common_equity",
                      f"the issuer's {reg.form} cover page registers {reg.symbol} as "
                      f"\"{reg.title}\" — a {cls} security, though the reference feed types it CS",
                      StampedInput(value=reg.title, as_of=reg.filed,
                                   source=f"SEC {reg.form} {reg.accession} cover page "
                                          f"(dei:Security12bTitle)"))
                continue
            # ADMISSION IS DEFERRED, not decided here — one issuer contributes ONE line, and which
            # line survives cannot be known until every sibling has cleared the same gates.
            # Persist the SIC we ALREADY fetched (above, for the Axis-1 gate) onto the identity so
            # it flows into the committed securities/issuers snapshots — was a dead write (fetched,
            # gated on, then discarded via [0]). The coarse SECTOR is derived downstream
            # (sectors.sector_for_sic); SIC itself is never a screen/rank/verdict input.
            ident = ident.model_copy(update={"sic": sic, "sic_description": sic_desc})
            # UPSERTED HERE, NOT WITH THE WINNERS. `securities`/`issuers` are ACCUMULATE-ONLY and
            # an identity is never pruned — the entity master has to resolve a ledgered name after
            # it leaves the universe. De-duplication decides MEMBERSHIP, not existence, so a class
            # that loses to a more tradeable sibling must still be known to the master (and still
            # carry a refreshed SIC); only its universe row is withheld.
            store.upsert_security(ident, first_seen=reference_date)
            admitted.append((ident, market_cap, shares_source, approximate))

        # A RENAME CONTINUES ITS LINE (2026-10-27). A new ticker mints a new internal id, so HOS
        # entered the 2026-09-22 population with no history while HLX — the same share class —
        # left with all of it, and the screen could not evaluate it. Renames among the admitted
        # lines are confirmed on Polygon's share-class FIGI and recorded in the committed alias
        # table; the new id then (a) inherits the old id's incumbency, so the record is not
        # treated as a new choice, and (b) is given the old id's bars before its listing date.
        # The old id is never re-keyed (`vinci/resolver/aliases.py`).
        aliases = load_aliases(cfg.snapshots_dir)
        def _first_session(line: Identity) -> date | None:
            """The first session the source serves under this line's own ticker."""
            bars = eod.daily_bars(line.eod_symbol,
                                  reference_date - timedelta(days=CARRY_DAYS), reference_date)
            return bars[0][0] if bars else None
        found = detect_renames([row[0] for row in admitted], store.iter_securities(), sec_types,
                               lambda t, on: eod.ticker_details(t, on), _first_session,
                               known=aliases)
        write_aliases(cfg.snapshots_dir, found)
        aliases += found
        incumbents = incumbents | {al.successor_id for al in aliases
                                   if al.predecessor_id in incumbents}
        admitted_ids = {row[0].internal_id for row in admitted}
        for al in aliases:
            if al.successor_id in admitted_ids:
                carry_forward(eod, store, predecessor_id=al.predecessor_id,
                              predecessor_symbol=al.predecessor_symbol,
                              successor_id=al.successor_id, listed=al.listed, end=reference_date)
        for ident, market_cap, cap_source, approximate in _one_line_per_issuer(admitted):
            stats["in_universe"] += 1
            # Stamped on the admitted row and counted in the run's health numbers, so an
            # approximate cap never blends in silently. (`shares_source` was derived above, where
            # the out-of-band drop path needs the same provenance.)
            if approximate:
                stats["shares_period_average"] += 1
            store.record_universe(
                as_of=reference_date,
                internal_id=ident.internal_id,
                in_universe=True,
                market_cap=DataField.present(
                    market_cap, as_of=reference_date, source=cap_source, tier=SourceTier.DERIVED
                ),
                band=band_name,
            )
        store.export_snapshots(cfg.snapshots_dir, tables=export_tables)
    # Persist the fail-closed gate-exclusion counts as a committed health snapshot (the ops
    # dashboard reads these; a wrong count signals a gate bug). Derived counts only — no licensed
    # data. SIC-denylist drops = unknown_sic + non_operating; type-allowlist = unknown_type +
    # non_common_equity.
    stats_out = dict(stats)
    payload = {
        "as_of": reference_date.isoformat(),
        "market_cap_min_usd": band.market_cap_min_usd,
        "market_cap_max_usd": band.market_cap_max_usd,
        "adv_floor_usd": band.adv_floor_usd,
        **stats_out,
    }
    payload["band"] = band_name   # the population this count describes — never inferred
    (cfg.snapshots_dir / stats_filename).write_text(json.dumps(payload, indent=2) + "\n")
    if retain_run_id is not None and retain_dir is not None:
        # THE COUNT MUST MATCH THE ROWS, or the thin grain is quietly incomplete. Every stage that
        # increments a stat also appends a row, so a divergence means a drop path was added without
        # its evidence — the exact way a blind spot re-opens after being closed.
        expected = sum(stats_out.get(k, 0) for k in DROP_STAGES)
        if len(dropped) != expected:
            raise ValueError(
                f"retention emitted {len(dropped)} thin rows against {expected} counted drops — a "
                "drop path is not writing its row")
        stats_out["retained_universe_rows"] = append_rows(
            dropped, run_id=retain_run_id, snapshots_dir=retain_dir)
    return stats_out
