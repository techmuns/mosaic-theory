# The archetype probe: scripts behind scope pack 1

These scripts produced the evidence for `docs/scope-pack-archetypes-1.md`: the census,
the per-layer probe, the full $0 builds, the D13 audit, each defect's reach on the live pages, and
the source_refs of every CIQ figure the pack quotes. The findings are in
`docs/scope-pack-archetypes-1-findings.md`, and the record is
`docs/records/2026-11-19-archetype-scope-pack-1.md`.

## What a run costs and touches

- **$0.** No script constructs a model client.
- **Fetches:** EDGAR and FINRA go through the repo's own clients, so the SEC user agent is the
  project's default and the machine-wide SEC limiter applies. Polygon is called only by the
  `vinci refresh` step below.
- **Nothing is written into a checkout.** Every cache, the scratch price store and every output
  live under `$ARCHETYPE_PROBE_WORK`, which must be outside the checkout (refused otherwise).
- **CIQ workbooks are read only.** A script copies a pack into
  `$ARCHETYPE_PROBE_WORK/data/manual/ciq/<TICKER>/`, checks each copy's sha256 against its
  original, and deletes the copies when it ends, including on an error.
- **Outputs regenerate, so none is committed.** Some print CIQ cell values for the reader's own use.
  The pack quotes only the cells it cites, each with its source_ref.

## Configuration

Every machine path is an environment variable; none is in the code (`probe_common.py`).

| variable | required by | what |
|---|---|---|
| `ARCHETYPE_PROBE_WORK` | every script | a folder outside the checkout. Data dir `<WORK>/data`, outputs `<WORK>/out` |
| `ARCHETYPE_PROBE_CIQ` | the scripts that read a CIQ pack | the export root in the loader's own layout, `<root>/<TICKER>/<files>` |
| `ARCHETYPE_PROBE_CIQ_PACKS` | `build5a`, `ciq5a`, `ciq_probe` (the 2026-10-28 packs) | the dated-pack layout, `<root>/<TICKER>_<id>/<date>/`; optional elsewhere |
| `ARCHETYPE_PROBE_SEC_CACHE` | `fpi_facts`, `cachecov` (optional) | a read-only SEC cache another checkout holds; absent, reads go through the repo's client |
| `ARCHETYPE_PROBE_DOTENV` | optional | a `.env` to load; default `<checkout>/.env` |

**The checkout is the one the script sits in.** `probe_common.py` puts that checkout's root first
on `sys.path`, imports `vinci` from it, and refuses to run if `vinci` resolves anywhere else. Every
script prints `vinci.__file__` first.

## Running

From the checkout root:

```bash
export ARCHETYPE_PROBE_WORK=/path/outside/the/checkout
python scripts/archetype_probe/<script>.py [args]
```

### Step 3: the census (findings §3)

1. `census_fetch.py`: every universe CIK's submissions, plus the SEC frames. Writes `out/subs_extract.jsonl` and `out/frames/`; it is resumable.
2. `fpi_facts.py`: each 20-F/40-F filer's reporting currency and namespace. Writes `out/fpi_facts.json`.
3. `classify.py`: one census row per company. Writes `out/census.json`.
4. Then the tables:
   - `grid.py`: the archetype table;
   - `crosstab.py`: cross-tabs;
   - `cachecov.py`: cache coverage.

### Step 4: the per-layer probe (findings §5, §6)

1. `probe.py TICKER [TICKER ...]`: each layer per name. Writes `out/probe/<T>.json`; resumable.
2. `ciq_probe.py`: the CIQ layer on the packs on disk.
3. `diag.py`: second looks at anomalies.
4. `score.py`: W/R/X/N per layer. Writes `out/scores.md`.
5. `probe_table.py`: a per-name summary.
6. `stage2.py` and `stage2_summary.py`: stage-2 SEC status. `fts_recheck.py` and `pdf_find.py` are helpers.

### 5a: the full $0 builds (findings §11)

1. `setup5a.py`: the scratch follow list and coverage roster, written under `<WORK>/data` only.
2. Prices, into the scratch store, from the work folder so the CLI's data dir is `<WORK>/data`:

   ```bash
   cd "$ARCHETYPE_PROBE_WORK" && PYTHONPATH=/path/to/checkout python -m vinci refresh PLD AWK RIVN CRWV MORN DVN AQN NBIS SPGI MTB PCVX BRK-B EPD SPY IWM MDY --aggs --start 2024-11-20 --end 2026-11-18
   ```

3. The builds:
   - `build5a.py T` (with its 2026-10-28 pack) or `build5a.py T:nociq` (EDGAR only): the precheck (`prespend.run`), the page, the R4 conditions and the three templates;
   - `ciq5a.py`: the 2026-10-28 packs' consensus inputs.
4. `intake5a.py`: the paid command's gates, before and after the two intake steps.
5. `diff5a.py`: each page against the SPGI control.
6. `d13audit.py`: D13 on the committed pages and candidate records.

### 5a, fresh exports (findings §11f)

- `fresh5a.py [T ...]`: the 2026-11-19 packs, copied, hash-checked, and built.
- `variant5a.py`: the DVN variant without its mislabelled file, plus the refused packs' inputs.
- One script per check:
  - `bs5a.py`: D17's balance-sheet rows;
  - `aqnhc5a.py`: AQN's Historical Capitalization header;
  - `morn5a.py` and `morn5a_ctx.py <accession ...>`: MORN's filings;
  - `rivn5a.py`: D18's filed facts;
  - `mornebitda5b.py`: D20;
  - `xls_headers5b.py TICKER SUFFIX ...`: what a Financials export says it is (DVN).

### 5b: the pack (scope pack §2, §3)

- `pages5b.py`: each defect's reach on the committed pages.
- `cites5b.py`: the source_ref of every CIQ figure quoted.
- `aqnclass5b.py`: SP-D21's proxies.
- `g17pick5b.py`: the substitute G17 name.

## What a re-run can and cannot reproduce

The code is the same, but the inputs move:
- the committed pages and candidate records at a newer main;
- a CIQ pack re-exported on Drive;
- an SEC filing made since.

Each output prints its boundary (main sha, dates, population), so compare boundaries before
comparing numbers. The pack's figures carry theirs.
