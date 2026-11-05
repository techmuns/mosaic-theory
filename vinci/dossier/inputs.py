"""THE INPUT MANIFEST — what a page was built from, by content hash (workstream B, slice 1).

A build records one :class:`InputManifest`: the full sha256 of every CIQ export its bundle held,
of every HTTP response it read (SEC, Polygon, FINRA), and the identity of every price series it
read from the store. Design and its boundaries:
`docs/records/2026-11-05-every-page-records-what-it-was-built-from.md`.

TWO HOMES, ONE RECORD. The assembly-run record carries it IN FULL, so a build that was REFUSED
still says what it read. The page carries it with the response list cut to the fact layer's
sources (:func:`for_page`): GOOGL's $0 build on 2026-11-05 read 1,080 responses (1,050 of them
EDGAR filing documents and indexes) — 357 KB of record against a 635 KB page. Every CIQ export and
price series stays listed; the cut responses are counted and hashed (``responses_digest``), and
the page's ``inputs_id`` is the full record's, so the run record carrying the same id is the list.

ONE IDENTITY PER LAYER, REUSED — never a parallel scheme:

- a CIQ export: the sha256 of the file's bytes — the rule every page stamp already takes
  (`ciq_sheets.file_provenance`), untruncated; the fact layer's slice 4 keys CIQ facts on it too;
- a response: the fact layer's ``response_sha256`` — sha256 of the cached text, UTF-8 — under
  the same ``source_url`` and ``fetched_at`` its snapshot manifests use. A response that a
  committed fact-layer snapshot sealed names that snapshot (``sealed_by``), so the page input and
  the store's entity are one identity: when the page later reads the store instead (fact layer
  slice 6) the record names the snapshot id it read, and nothing else changes;
- a price series: its rows, bar_date ascending, through its newest bar
  (:func:`series_rows_sha256`) — re-hashable later on another store holding more bars;
- the manifest itself: ``inputs-<16 hex>`` over those identities only, the shape of the fact
  layer's ``<source>-<16 hex>`` snapshot id — two builds from identical inputs carry one id. It
  is set only on a COMPLETE record (nothing ``unrecorded``): a partial record has no identity.

NOTHING IS GUESSED. An input that could not be hashed is listed in ``unrecorded`` with its reason,
never given a hash. A page built before this field existed is BACKFILLED only from what it
stamped itself (:func:`backfill`): a 10-hex stamp is resolved to a full sha256 only when a file on
this machine hashes to it; everything else says "unrecorded", and why.

WHAT IT DOES NOT COVER (``covers`` says so on every record): the committed repository files a
build reads — `data/graph_coverage.json`, `scenarios/<T>.json`, `data/followed.json`, the screen
snapshots and the committed page itself. They are versioned by the commit the page lands in.

JSON-ONLY (2026-11-05): the block is not rendered. Its readers are machines — the precheck, and
the gate and the elsewhere-check of the later slices. DESIGN RULE v2 places it in the JSON tier.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

from vinci import provenance
from vinci.dossier.inputs_schema import (
    CiqExport,
    InputManifest,
    PriceSeries,
    Response,
    ResponsesDigest,
    Unrecorded,
)

__all__ = ["CiqExport", "InputManifest", "PriceSeries", "Response", "ResponsesDigest",
           "Unrecorded"]

if TYPE_CHECKING:
    from vinci.dossier.ciq import CiqBundle
    from vinci.schemas.market import PriceBar
    from vinci.store.store import Store

SCHEMA_VERSION = 1
#: The input classes this schema version records. Anything a build reads outside them is named in
#: the module docstring, never silently implied to be covered.
COVERS = ("ciq", "responses", "prices")
_ID_PREFIX = "inputs-"
#: A page's CIQ export stamp: the first 10 hex of the file's sha256 (`ciq_sheets.file_provenance`).
#: Any other hash a page carries is no export stamp.
_STAMP = re.compile(r"[0-9a-f]{10}")


# --- recording -------------------------------------------------------------------------------


def note_bundle(bundle: CiqBundle) -> None:
    """Record every export ``bundle`` holds as read (`provenance.note_file`). The bundle is the
    one door the page's CIQ readers read through, so its workbooks ARE the CIQ inputs."""
    for wb in bundle.workbooks:
        provenance.note_file("ciq", wb.path, kind=wb.kind, freq=wb.freq)


def note_files(paths: Iterable[Path]) -> None:
    """Record CIQ files the loader read but refused to build a bundle from, kind unread."""
    for p in paths:
        if not p.name.startswith((".", "~$")):
            provenance.note_file("ciq", p)


def series_rows_sha256(bars: Sequence[PriceBar]) -> str:
    """THE ONE RULE for a series' identity: sha256 over one canonical JSON line per bar
    (``[date, open, high, low, close, volume, source]``), oldest first. A store that later holds
    more bars re-hashes the rows through the recorded newest bar and compares."""
    digest = hashlib.sha256()
    for b in sorted(bars, key=lambda b: b.bar_date):
        row = [b.bar_date.isoformat(), b.open, b.high, b.low, b.close, b.volume, b.source]
        digest.update(json.dumps(row, separators=(",", ":")).encode("utf-8") + b"\n")
    return digest.hexdigest()


def _iso(ts: float | None) -> str | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@lru_cache(maxsize=4)
def _sealed_index(manifests_dir: str, stamp: tuple[tuple[str, float], ...]
                  ) -> dict[str, tuple[str, ...]]:
    """``{response_sha256: snapshot ids}`` over every committed fact-layer manifest. ``stamp``
    (name, mtime) keys the cache, so a manifest added mid-process is read."""
    out: dict[str, set[str]] = {}
    for name, _ in stamp:
        body = json.loads((Path(manifests_dir) / name).read_text())
        sid = str(body.get("snapshot_id"))
        for ent in body.get("entities") or []:
            if sha := ent.get("response_sha256"):
                out.setdefault(str(sha), set()).add(sid)
    return {k: tuple(sorted(v)) for k, v in out.items()}


def sealed_index(facts_base: Path | None = None) -> Mapping[str, tuple[str, ...]]:
    """The fact layer's own manifests directory (`vinci.facts.store.manifests_dir`: under
    ``facts_base``, else the working directory's ``data/facts``, as `Config.data_dir` resolves)."""
    from vinci.facts.store import manifests_dir as facts_manifests

    manifests_dir = facts_manifests(facts_base)
    if not manifests_dir.is_dir():
        return {}
    stamp = tuple(sorted((p.name, p.stat().st_mtime) for p in manifests_dir.glob("*.json")))
    return _sealed_index(str(manifests_dir), stamp)


def _responses(reads: Iterable[provenance.HttpRead],
               sealed: Mapping[str, tuple[str, ...]]) -> list[Response]:
    return sorted(
        (Response(namespace=r.namespace, source_url=r.url, fetched_at=_iso(r.fetched_at),
                  response_sha256=r.sha256, bytes=r.bytes,
                  sealed_by=list(sealed[r.sha256]) if r.sha256 in sealed else None)
         for r in reads),
        key=lambda r: (r.namespace, r.source_url, r.fetched_at or "", r.response_sha256))


def _ciq(files: Iterable[provenance.FileRead]) -> tuple[list[CiqExport], list[Unrecorded]]:
    exports: dict[tuple[str, str | None, str, str], CiqExport] = {}
    missing: list[Unrecorded] = []
    for f in files:
        if f.role != "ciq":
            continue
        name = Path(f.path).name
        if f.sha256 is None or f.bytes is None:
            missing.append(Unrecorded(input=f"ciq:{name}",
                                      why=f"the export could not be hashed ({f.error})"))
            continue
        kind = f.kind or "unknown"
        exports[(kind, f.freq, name, f.sha256)] = CiqExport(
            kind=kind, freq=f.freq, file=name, sha256=f.sha256, bytes=f.bytes)
    return sorted(exports.values(), key=lambda e: (e.kind, e.freq or "", e.file)), missing


def price_series(store: Store, internal_ids: Iterable[str]
                 ) -> tuple[list[PriceSeries], list[Unrecorded]]:
    """Each series' identity as the store holds it now — read right after the build, from the
    store it read (no build writes the price store)."""
    out: list[PriceSeries] = []
    missing: list[Unrecorded] = []
    for iid in sorted(set(internal_ids)):
        try:
            bars = store.get_price_history(iid)
            sec = store.get_security(iid)
        except Exception as exc:  # noqa: BLE001 — an unreadable series is recorded as such
            missing.append(Unrecorded(input=f"prices:{iid}",
                                      why=f"the store could not be read ({type(exc).__name__})"))
            continue
        out.append(PriceSeries(
            internal_id=iid, ticker=sec.ticker if sec is not None else None, bars=len(bars),
            first_bar=bars[0].bar_date if bars else None,
            newest_bar=bars[-1].bar_date if bars else None,
            rows_sha256=series_rows_sha256(bars) if bars else None))
    return out, missing


#: The responses the fact layer stores (`vinci.facts.edgar_ingest`): EDGAR companyfacts. A page
#: lists these one by one, so it can later be pointed at the snapshot that sealed each.
FACT_SOURCE = "/api/xbrl/companyfacts/"


def is_fact_source(r: Response) -> bool:
    return r.namespace == "sec" and FACT_SOURCE in r.source_url


def responses_digest(responses: Sequence[Response]) -> ResponsesDigest:
    lines = sorted(f"{r.namespace} {r.source_url} {r.response_sha256}" for r in responses)
    counts: dict[str, int] = {}
    for r in responses:
        counts[r.namespace] = counts.get(r.namespace, 0) + 1
    return ResponsesDigest(
        count=len(responses), by_namespace=dict(sorted(counts.items())),
        sha256=hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest())


def for_page(full: InputManifest) -> InputManifest:
    """The record as the page carries it: the response list cut to the fact layer's sources, the
    digest and the id kept from the full record (`responses_digest`, `inputs_id_for`)."""
    if full.responses_listed != "all":
        return full
    return full.model_copy(update={
        "responses_listed": "fact_layer_sources",
        "responses": [r for r in full.responses if is_fact_source(r)]})


def inputs_id_for(ciq: Sequence[CiqExport], responses: Sequence[Response],
                  prices: Sequence[PriceSeries]) -> str:
    """``inputs-<16 hex>`` over the identities only — never names, times or counts."""
    body = {"ciq": sorted([e.kind, e.freq, e.sha256] for e in ciq),
            "responses": sorted([r.namespace, r.source_url, r.response_sha256]
                                for r in responses),
            "prices": sorted([p.internal_id, p.newest_bar.isoformat() if p.newest_bar else None,
                              p.rows_sha256] for p in prices)}
    canon = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    return _ID_PREFIX + hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16]


def from_reads(reads: provenance.Reads, *, store: Store | None, extraction_version: str,
               facts_base: Path | None = None) -> InputManifest:
    """The build's manifest from what its recorder saw. ``store`` None (it could not be opened):
    every series it read is ``unrecorded``."""
    ciq, missing = _ciq(reads.files)
    # BUILT AFTER EVERY PAID PHASE, so a lookup that cannot read the fact layer's manifests is
    # said in the record, never a refused build
    try:
        sealed = sealed_index(facts_base)
    except (OSError, ValueError) as exc:
        sealed = {}
        missing.append(Unrecorded(
            input="responses:sealed_by",
            why=f"the fact layer's snapshot manifests could not be read ({type(exc).__name__}), "
                "so no response names the snapshot that sealed it"))
    responses = _responses(reads.http, sealed)
    if store is None:
        prices: list[PriceSeries] = []
        missing += [Unrecorded(input=f"prices:{iid}", why="the price store could not be opened")
                    for iid in sorted(reads.series)]
    else:
        prices, gone = price_series(store, reads.series)
        missing += gone
    return InputManifest(
        recorded="build", extraction_version=extraction_version, covers=list(COVERS),
        inputs_id=None if missing else inputs_id_for(ciq, responses, prices),
        ciq=ciq, responses=responses, responses_digest=responses_digest(responses),
        prices=prices, unrecorded=missing)


def manifest_for(reads: provenance.Reads, *, db_path: Path, extraction_version: str,
                 facts_base: Path | None = None) -> InputManifest:
    """`from_reads` with the store opened here and closed again; an unopenable store makes the
    series unrecorded rather than failing the build. ``facts_base``: the build's
    ``<data_dir>/facts``, where the fact layer's manifests are read from."""
    from vinci.store.store import Store

    try:
        store = Store(db_path)
    except Exception:  # noqa: BLE001 — named in the record, never a guessed series
        return from_reads(reads, store=None, extraction_version=extraction_version,
                          facts_base=facts_base)
    with store:
        return from_reads(reads, store=store, extraction_version=extraction_version,
                          facts_base=facts_base)


def write_json(manifest: InputManifest, path: Path) -> None:
    """One record as its own JSON file (the precheck's ``--inputs-json``) — never a page."""
    path.write_text(manifest.model_dump_json(indent=2) + "\n")


# --- the backfill ------------------------------------------------------------------------------

#: Why a page built before 2026-11-05 cannot say which responses or series it read.
UNRECORDED_RESPONSES = (
    "no build before 2026-11-05 recorded which SEC, Polygon or FINRA responses it read, and the "
    "cache rewrites an entry in place, so the copy there now is no evidence of the copy read")
UNRECORDED_UNSTAMPED_CIQ = (
    "a page built before 2026-11-05 stamps an export only where a block records a 10-hex prefix "
    "of its sha256; any other export it read (comps, transcripts, capital structure, credit "
    "health …) was never recorded")


def stamps(doc: Mapping[str, Any]) -> dict[str, list[str]]:
    """``{10-hex stamp: [page sites]}`` for every key ending ``sha256`` whose value is a 10-hex
    stamp (`_STAMP`; any other hash a page carries is no export stamp), outside the page's own
    ``inputs`` block, the site a dotted path with list positions dropped."""
    out: dict[str, set[str]] = {}

    def walk(node: Any, path: str) -> None:
        if isinstance(node, Mapping):
            for key, child in node.items():
                here = f"{path}.{key}" if path else str(key)
                if (str(key).endswith("sha256") and isinstance(child, str)
                        and _STAMP.fullmatch(child)):
                    out.setdefault(child, set()).add(here)
                else:
                    walk(child, here)
        elif isinstance(node, list):
            for child in node:
                walk(child, path)

    walk({k: v for k, v in doc.items() if k != "inputs"}, "")
    return {k: sorted(v) for k, v in out.items()}


@dataclass(frozen=True)
class Candidate:
    """A file on this machine that may be one of a page's exports."""

    path: Path
    sha256: str
    bytes: int


def candidates(ticker: str, roots: Iterable[Path]) -> list[Candidate]:
    """Every file under a folder named ``ticker`` beneath each root (a live CIQ folder, or an
    archive holding ``replaced-<date>/<TICKER>/``), hashed. Links are followed: the identity is
    the bytes, wherever they sit. Sync droppings are skipped as the loader skips them."""
    seen: dict[Path, Candidate] = {}
    for root in roots:
        if not root.is_dir():
            continue
        dirs = [root / ticker] if (root / ticker).is_dir() else []
        dirs += [d for d in root.rglob(ticker) if d.is_dir() and d not in dirs]
        for d in dirs:
            for p in sorted(d.iterdir()):
                if not p.is_file() or p.name.startswith((".", "~$")):
                    continue
                real = p.resolve()
                if real in seen:
                    continue
                try:
                    sha, size = provenance.file_sha256(p)
                except OSError:
                    continue
                seen[real] = Candidate(p, sha, size)
    return list(seen.values())


def _classify(ticker: str, path: Path) -> tuple[str, str | None]:
    """The export's kind and period type by the loader's OWN rule (`CiqBundle.from_files`)."""
    from vinci.dossier.ciq import CiqBundle

    try:
        wbs = CiqBundle.from_files(ticker, [path]).workbooks
    except Exception:  # noqa: BLE001 — a file the loader refuses is still these bytes
        return "unknown", None
    return (wbs[0].kind, wbs[0].freq) if wbs else ("unknown", None)


def backfill(doc: Mapping[str, Any], *, ticker: str, roots: Sequence[Path],
             extraction_version: str) -> InputManifest:
    """The record a page built before this field can carry, from its OWN stamps only.

    Each 10-hex stamp becomes a full sha256 only when exactly one distinct file on this machine
    hashes to it (a chance match is 1 in 16^10 per file); a stamp no file matches, and every
    class the page never stamped, is ``unrecorded`` with its reason. DETERMINISTIC: the same
    page and the same files give the same record, byte for byte (no clock is read)."""
    found = candidates(ticker, roots)
    ciq: list[CiqExport] = []
    missing: list[Unrecorded] = []
    for stamp, sites in sorted(stamps(doc).items()):
        hits = {c.sha256: c for c in found if c.sha256.startswith(stamp)}
        if len(hits) == 1:
            c = next(iter(hits.values()))
            kind, freq = _classify(ticker, c.path)
            ciq.append(CiqExport(kind=kind, freq=freq, file=c.path.name, sha256=c.sha256,
                                 bytes=c.bytes, stamped_by=sites))
        elif not hits:
            missing.append(Unrecorded(
                input=f"ciq:{stamp}",
                why=(f"stamped at {', '.join(sites)}; no file on this machine hashes to it "
                     f"({len(found)} file(s) under {len(roots)} root(s) searched)")))
        else:
            missing.append(Unrecorded(
                input=f"ciq:{stamp}",
                why=f"stamped at {', '.join(sites)}; {len(hits)} different files begin with "
                    "it, so the stamp names none of them"))
    missing.append(Unrecorded(input="ciq:unstamped", why=UNRECORDED_UNSTAMPED_CIQ))
    missing.append(Unrecorded(input="responses", why=UNRECORDED_RESPONSES))
    frontier = (doc.get("price_store") or {}).get("frontier")
    missing.append(Unrecorded(
        input="prices",
        why=("the page records only the store's newest bar across every name "
             f"(price_store.frontier = {frontier}), not which series it read"
             if frontier else "the page records no price store")))
    return InputManifest(
        recorded="backfill", extraction_version=extraction_version, covers=list(COVERS),
        inputs_id=None, ciq=sorted(ciq, key=lambda e: (e.kind, e.freq or "", e.file)),
        unrecorded=missing)


# --- recorded against present ------------------------------------------------------------------


@dataclass(frozen=True)
class ClassDiff:
    """One input class, the page's record against what is present here."""

    name: str
    same: int
    changed: tuple[str, ...]
    only_recorded: tuple[str, ...]
    only_present: tuple[str, ...]

    @property
    def moved(self) -> bool:
        return bool(self.changed or self.only_recorded or self.only_present)


def _diff(name: str, recorded: Mapping[str, str], present: Mapping[str, str]) -> ClassDiff:
    keys = set(recorded) | set(present)
    return ClassDiff(
        name=name,
        same=sum(1 for k in keys if k in recorded and recorded.get(k) == present.get(k)),
        changed=tuple(sorted(k for k in keys if k in recorded and k in present
                             and recorded[k] != present[k])),
        only_recorded=tuple(sorted(k for k in recorded if k not in present)),
        only_present=tuple(sorted(k for k in present if k not in recorded)))


def compare(recorded: InputManifest, present: InputManifest) -> list[ClassDiff]:
    """Per class, which inputs the page's record and this build's agree on. CIQ exports are keyed
    by kind and period type (a kind read as several files — transcripts — by their set), a
    response by namespace and URL, a series by internal id. Where either side lists only the fact
    layer's sources, the responses compared are those."""
    def ciq(m: InputManifest) -> dict[str, str]:
        out: dict[str, set[str]] = {}
        for e in m.ciq:
            out.setdefault(f"{e.kind}/{e.freq}" if e.freq else e.kind, set()).add(e.sha256)
        return {k: ",".join(sorted(v)) for k, v in out.items()}

    cut = "fact_layer_sources" in (recorded.responses_listed, present.responses_listed)

    def resp(m: InputManifest) -> dict[str, str]:
        out: dict[str, set[str]] = {}
        for r in m.responses:
            if not cut or is_fact_source(r):
                out.setdefault(f"{r.namespace} {r.source_url}", set()).add(r.response_sha256)
        return {k: ",".join(sorted(v)) for k, v in out.items()}

    def px(m: InputManifest) -> dict[str, str]:
        return {p.internal_id: f"{p.newest_bar}:{p.rows_sha256}" for p in m.prices}

    return [_diff("ciq", ciq(recorded), ciq(present)),
            _diff("responses", resp(recorded), resp(present)),
            _diff("prices", px(recorded), px(present))]


def _first(items: Sequence[str], n: int) -> str:
    shown = ", ".join(items[:n])
    return shown + (f" … (showing {n} of {len(items)})" if len(items) > n else "")


def summary_lines(present: InputManifest, recorded: InputManifest | None, *,
                  show: int = 5) -> list[str]:
    """The precheck's INPUTS block: what this build read, then the page's record against it."""
    lines = [f"INPUTS — this build read {len(present.ciq)} CIQ export(s), "
             f"{len(present.responses)} response(s) "
             f"({', '.join(f'{ns} {n}' for ns, n in _by_namespace(present)) or 'none'}), "
             f"{len(present.prices)} price series · "
             + (present.inputs_id or f"no id: {len(present.unrecorded)} unrecorded")]
    lines += [f"  unrecorded here: {u.input} — {u.why}" for u in present.unrecorded]
    if recorded is None:
        lines.append("  the committed page records no inputs — nothing to compare")
        return lines
    lines.append(f"  the committed page's record: {recorded.recorded}, "
                 + (recorded.inputs_id or f"{len(recorded.unrecorded)} input class(es) "
                    "unrecorded"))
    if recorded.inputs_id is not None and recorded.inputs_id == present.inputs_id:
        lines.append("  every recorded input is the one present here")
        return lines
    rd, pd = recorded.responses_digest, present.responses_digest
    if rd is not None and pd is not None:
        same = "the same" if rd.sha256 == pd.sha256 else "MOVED"
        lines.append(f"  responses, all of them: {same} — the page's {rd.count}, here "
                     f"{pd.count} (digest)")
    for d in compare(recorded, present):
        unrec = [u.input for u in recorded.unrecorded
                 if u.input == d.name or u.input.startswith(d.name + ":")]
        if unrec and not d.same and not d.changed and not d.only_recorded:
            lines.append(f"  {d.name}: the page did not record it ({', '.join(unrec)})")
            continue
        lines.append(f"  {d.name}: {d.same} same, {len(d.changed)} changed, "
                     f"{len(d.only_recorded)} only on the page, {len(d.only_present)} only here")
        if d.changed:
            lines.append(f"      changed: {_first(d.changed, show)}")
        if d.only_recorded:
            lines.append(f"      only on the page: {_first(d.only_recorded, show)}")
    return lines


def _by_namespace(m: InputManifest) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for r in m.responses:
        counts[r.namespace] = counts.get(r.namespace, 0) + 1
    return sorted(counts.items())
