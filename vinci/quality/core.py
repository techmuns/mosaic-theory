"""DATA-QUALITY SCORECARD — the source-agnostic core: one dated answer per data source to "is this
data credible?".

WHY (2026-10-23). Each data source the fund reads has checks, but their results sat where they ran —
CIQ's on 27 pages, each holding its own — with no fleet view and no series over time. The core
counts them; a SOURCE plugs in. A source is ONE module under `vinci.quality.sources` exposing
``SOURCE``: how it loads what it reads, its checks, and its field families. Adding a source is
adding that module — nothing here names one, and a test holds this file to that.

FOUR STATUSES, per UNIT (a quarter, a balance-sheet date, a page — named per check):

* ``confirmed`` — a second figure agrees within the check's OWN tolerance (the producer's constant,
  imported by the source, never re-typed);
* ``differs_stated`` — they differ, and the input carries a reason for THAT unit;
* ``differs_unexplained`` — they differ, and nothing says why;
* ``unchecked`` — the unit exists but has no second figure to compare.

An item where a check never ran is ``not_run`` (its units are unknown), and one it does not apply to
is ``not_applicable``. Neither is folded into ``unchecked``: "no second figure" and "never looked"
are different facts, and summing them would make the second look like the first.

FIVE FAILURE CLASSES — the common frame every source is read in: wrong file, wrong cell, wrong unit,
wrong period or vintage, different definition. Each check DECLARES which it can surface, from what
it compares (face validity, never measured against outcomes); each family then shows which classes
an independent check guards, which only an internal one, and which nothing does.

INDEPENDENCE IS NAMED PER CHECK. ``independent``: the second figure comes from outside the source
(the filings, another provider). ``internal``: from the source's own other output — coherence, never
correctness.

COUNTS AND STATUSES ONLY. The repo is public (2026-10-22): no source's figures enter a snapshot.

A SOURCE DECLARES WHAT ITS SNAPSHOT HOLDS (``Source.committed_rows``, operator ruling C1,
2026-10-29). ``full``: every name for every check. ``exceptions``: every name a check did not
confirm in full, in full; the rest counted and the count stated (`compact`); the full card written
beside the store, git-ignored (`full_rows_path`). The prices source writes every security for every
check, 2-3 MB a day, into a public repo's history that keeps every copy.
"""
from __future__ import annotations

import importlib
import pkgutil
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA = "data_quality/1"
CONFIRMED = "confirmed"
DIFFERS_STATED = "differs_stated"
DIFFERS_UNEXPLAINED = "differs_unexplained"
UNCHECKED = "unchecked"
STATUSES: tuple[str, ...] = (CONFIRMED, DIFFERS_STATED, DIFFERS_UNEXPLAINED, UNCHECKED)
_NOT_CONFIRMED = tuple(s for s in STATUSES if s != CONFIRMED)
STATUS_MEANING: dict[str, str] = {
    CONFIRMED: "a second figure agrees within the check's own tolerance",
    DIFFERS_STATED: "they differ, and the input states a reason for that unit",
    DIFFERS_UNEXPLAINED: "they differ, and nothing says why",
    UNCHECKED: "the unit exists but has no second figure to compare",
}
INDEPENDENT = "independent"
INTERNAL = "internal"
SINGLE_SOURCE = "single_source"
UNVERIFIED = "unchecked"
#: The coverage classes, in the order a reader trusts them.
COVERAGE_MEANING: dict[str, str] = {
    INDEPENDENT: "a figure from outside the source is compared and a verdict stored",
    INTERNAL: "compared only against the source's own other output — coherence, not correctness",
    SINGLE_SOURCE: "no second source exists among this repo's inputs",
    UNVERIFIED: "a second source exists in principle; no structured verdict is stored",
}
#: The five ways a figure goes wrong, in the order they are usually found.
FAILURE_CLASSES: dict[str, str] = {
    "wrong_file": "another company's export, or another pull of it",
    "wrong_cell": "the right file, the wrong row or column",
    "wrong_unit": "the right cell, the wrong scale or currency",
    "wrong_period": "the right figure for another period, or another vintage of it",
    "different_definition": "the same name on a figure built another way",
}
#: What a source's committed snapshot holds (`Source.committed_rows`).
FULL = "full"
EXCEPTIONS = "exceptions"
#: An EXCEPTIONS snapshot's schema: its ``by_name`` is not the population, so a reader of the full
#: form is refused by name rather than reading a missing name as absent.
COMPACT_SCHEMA = f"{SCHEMA}+{EXCEPTIONS}"


@dataclass(frozen=True)
class ItemResult:
    """One check on one item: units by status, or why there are none."""

    counts: dict[str, int] = field(default_factory=dict)
    excluded: int = 0                      # units the check's own rule leaves out (named per check)
    not_run: str | None = None
    not_applicable: str | None = None


def one(status: str) -> ItemResult:
    """A one-unit result — the shape of every per-page check."""
    return ItemResult(counts={status: 1})


@dataclass(frozen=True)
class Check:
    id: str
    title: str
    subject: str                   # the source's figure under test
    second_source: str
    independence: str              # INDEPENDENT | INTERNAL
    unit: str
    tolerance: str
    population: str
    stated_reason: str | None
    excluded_rule: str | None
    catches: tuple[str, ...]       # FAILURE_CLASSES this comparison can surface
    run: Callable[[Any], ItemResult]


@dataclass(frozen=True)
class Family:
    """A field family: where it comes from, what it carries, and how it is verified."""

    id: str
    origin: str                    # the source's own name for where it comes from (a CIQ kind)
    cited_as: tuple[str, ...]      # how the source's records cite it, when they do
    carries: str
    checks: tuple[str, ...] = ()   # scored checks (ids in the source's `checks`)
    fallback: str = UNVERIFIED     # the class when no scored check covers it
    unscored: tuple[str, ...] = ()  # checks that run but leave no structured verdict
    note: str = ""
    # facts COUNTED for the family but not scored (no pass/fail is defined for them)
    counted: Callable[[dict[str, Any]], dict[str, int]] | None = None


@dataclass(frozen=True)
class Corpus:
    """What one run of a source read: its items by name, and the boundary that names them."""

    items: dict[str, Any]
    reads: str                     # what was read, e.g. 'data/dossiers/*/dossier.json'
    item_noun: str                 # 'page'
    sha256: str                    # one hash over exactly what was read
    tracked: tuple[str, ...] = ()  # repo paths read; a working-tree check runs on these


@dataclass(frozen=True)
class Source:
    id: str                        # [a-z0-9_]+ — names the snapshot series
    title: str
    reads_note: str                # one line: what it reads and what it never does
    load: Callable[[Path], Corpus]
    checks: tuple[Check, ...]
    families: tuple[Family, ...]
    committed_rows: str = FULL     # FULL | EXCEPTIONS — what its committed snapshot holds


def validate(src: Source) -> Source:
    """A source that contradicts itself is refused at discovery, never half-scored."""
    if src.committed_rows not in (FULL, EXCEPTIONS):
        raise ValueError(f"{src.id}: committed_rows {src.committed_rows!r}")
    ids = [c.id for c in src.checks]
    if len(set(ids)) != len(ids):
        raise ValueError(f"{src.id}: duplicate check id")
    for c in src.checks:
        if c.independence not in (INDEPENDENT, INTERNAL):
            raise ValueError(f"{src.id}.{c.id}: independence {c.independence!r}")
        if not c.catches or set(c.catches) - set(FAILURE_CLASSES):
            raise ValueError(f"{src.id}.{c.id}: catches {c.catches!r} — name classes from "
                             f"{list(FAILURE_CLASSES)}")
    if len({f.id for f in src.families}) != len(src.families):
        raise ValueError(f"{src.id}: duplicate family id")
    for f in src.families:
        if unknown := sorted(set(f.checks) - set(ids)):
            raise ValueError(f"{src.id}.{f.id}: unknown check(s) {unknown}")
        if f.fallback not in (SINGLE_SOURCE, UNVERIFIED):
            raise ValueError(f"{src.id}.{f.id}: fallback {f.fallback!r}")
    if set(ids) - {cid for f in src.families for cid in f.checks}:
        raise ValueError(f"{src.id}: check(s) on no family "
                         f"{sorted(set(ids) - {cid for f in src.families for cid in f.checks})}")
    return src


def discover(package: str = "vinci.quality.sources") -> dict[str, Source]:
    """Every module under ``package`` exposing ``SOURCE``, validated, by id."""
    pkg = importlib.import_module(package)
    out: dict[str, Source] = {}
    for m in sorted(pkgutil.iter_modules(pkg.__path__), key=lambda m: m.name):
        src = getattr(importlib.import_module(f"{package}.{m.name}"), "SOURCE", None)
        if isinstance(src, Source):
            if src.id in out:
                raise ValueError(f"two sources named {src.id}")
            out[src.id] = validate(src)
    return out


def classify(src: Source, f: Family) -> str:
    """A family's coverage class, DERIVED from its scored checks — never declared beside them."""
    kinds = {c.independence for c in src.checks if c.id in f.checks}
    if INDEPENDENT in kinds:
        return INDEPENDENT
    if INTERNAL in kinds:
        return INTERNAL
    return f.fallback


def failure_guard(src: Source, f: Family) -> dict[str, str]:
    """Per failure class: the strongest guard the family's scored checks give it."""
    out: dict[str, str] = {}
    for fc in FAILURE_CLASSES:
        kinds = {c.independence for c in src.checks if c.id in f.checks and fc in c.catches}
        out[fc] = (INDEPENDENT if INDEPENDENT in kinds else INTERNAL if INTERNAL in kinds
                   else "none")
    return out


def _score_check(c: Check, items: dict[str, Any]) -> dict[str, Any]:
    by_name: dict[str, Any] = {}
    fleet: Counter[str] = Counter()
    excluded = 0
    not_run: dict[str, list[str]] = {}
    not_applicable: dict[str, list[str]] = {}
    for t in sorted(items):
        r = c.run(items[t])
        if r.not_run is not None:
            not_run.setdefault(r.not_run, []).append(t)
            by_name[t] = {"not_run": r.not_run}
            continue
        if r.not_applicable is not None:
            not_applicable.setdefault(r.not_applicable, []).append(t)
            by_name[t] = {"not_applicable": r.not_applicable}
            continue
        row = {s: r.counts.get(s, 0) for s in STATUSES}
        if r.excluded:
            row["excluded"] = r.excluded
        by_name[t] = row
        fleet.update(r.counts)
        excluded += r.excluded
    run = [t for t, v in by_name.items() if "not_run" not in v and "not_applicable" not in v]
    totals = {s: fleet.get(s, 0) for s in STATUSES}
    return {
        "id": c.id, "title": c.title, "subject": c.subject, "second_source": c.second_source,
        "independence": c.independence, "unit": c.unit, "tolerance": c.tolerance,
        "population": c.population, "stated_reason": c.stated_reason,
        "excluded_rule": c.excluded_rule, "catches": list(c.catches),
        "fleet": {"items": len(items), "items_run": len(run), "units": sum(totals.values()),
                  **totals, "excluded": excluded,
                  "items_not_run": sum(len(v) for v in not_run.values()),
                  "items_not_applicable": sum(len(v) for v in not_applicable.values())},
        "not_run": [{"reason": k, "names": v} for k, v in not_run.items()],
        "not_applicable": [{"reason": k, "names": v} for k, v in not_applicable.items()],
        "by_name": by_name,
    }


def scorecard(src: Source, corpus: Corpus, *, measured_on: str, git_head: str | None,
              inputs_match_head: bool | None) -> dict[str, Any]:
    """The scorecard: a pure function of the corpus plus the boundary stamp it is given."""
    checks = [_score_check(c, corpus.items) for c in src.checks]
    by_id = {c["id"]: c for c in checks}
    coverage = []
    for f in src.families:
        entry: dict[str, Any] = {
            "family": f.id, "origin": f.origin, "cited_as": list(f.cited_as),
            "carries": f.carries, "classification": classify(src, f),
            "failure_guard": failure_guard(src, f),
            "checks": [{"id": cid, "independence": by_id[cid]["independence"],
                        "items_run": by_id[cid]["fleet"]["items_run"],
                        "units": by_id[cid]["fleet"]["units"],
                        "confirmed": by_id[cid]["fleet"][CONFIRMED]} for cid in f.checks],
            "unscored": list(f.unscored), "note": f.note or None}
        if f.counted is not None:
            entry["counted"] = f.counted(corpus.items)
        coverage.append(entry)
    guard = {fc: Counter(e["failure_guard"][fc] for e in coverage) for fc in FAILURE_CLASSES}
    # 'none' is split by whether a second source EXISTS for the family — its declared `fallback` —
    # never by its derived class. They agreed while no single-source family carried a check; once
    # one carries a check on ONE class (consensus's stated currency, 2026-10-27), its derived class
    # is internal and the derived split counted its other classes as "a second source exists".
    single = {fc: sum(1 for f, e in zip(src.families, coverage, strict=True)
                      if f.fallback == SINGLE_SOURCE and e["failure_guard"][fc] == "none")
              for fc in FAILURE_CLASSES}
    return {
        "schema": SCHEMA,
        "source": {"id": src.id, "title": src.title},
        "boundary": {
            "measured_on": measured_on, "git_head": git_head,
            "inputs_match_head": inputs_match_head, "reads": corpus.reads,
            "item_noun": corpus.item_noun, "items": len(corpus.items),
            "names": sorted(corpus.items), "inputs_sha256": corpus.sha256,
            "note": src.reads_note},
        "statuses": STATUS_MEANING,
        "coverage_classes": COVERAGE_MEANING,
        "failure_classes": FAILURE_CLASSES,
        "checks": checks,
        "coverage": coverage,
        # 'none' is split: a family with NO second source among the inputs cannot be guarded,
        # which is a different fact from one whose second source exists and goes unused
        "failure_class_summary": {
            fc: {INDEPENDENT: guard[fc].get(INDEPENDENT, 0), INTERNAL: guard[fc].get(INTERNAL, 0),
                 "none": guard[fc].get("none", 0) - single[fc],
                 "none_single_source": single[fc]}
            for fc in FAILURE_CLASSES},
    }


# --- rendering ----------------------------------------------------------------------------------

_SHORT = {CONFIRMED: "confirmed", DIFFERS_STATED: "differs (stated)",
          DIFFERS_UNEXPLAINED: "differs (unexplained)", UNCHECKED: "unchecked"}
_FC_SHORT = {"wrong_file": "file", "wrong_cell": "cell", "wrong_unit": "unit",
             "wrong_period": "period", "different_definition": "definition"}


def _rows(cells: list[str], width: int = 100) -> list[str]:
    """Cells packed into indented lines, never split inside one (a name keeps its counts)."""
    lines: list[str] = []
    for cell in cells:
        if lines and len(lines[-1]) + 2 + len(cell) <= width:
            lines[-1] += "  " + cell
        else:
            lines.append("      " + cell)
    return lines


def render(card: dict[str, Any]) -> str:
    """The scorecard as text. EVERY name is printed — no list here is cut."""
    b, src = card["boundary"], card["source"]
    head = b["git_head"] or "UNKNOWN commit"
    match = {True: "", False: " (WORKING TREE DIFFERS FROM IT — the sha256 names what was read)",
             None: " (whether the working tree matches it is UNKNOWN)"}[b["inputs_match_head"]]
    noun = b["item_noun"]
    out = [f"=== DATA-QUALITY SCORECARD · {src['title']} — {b['measured_on']} · {b['items']} "
           f"{noun}s ({b['reads']}) at {head}{match} ===",
           f"inputs sha256 {b['inputs_sha256']}", f"{b['note']}; counts and statuses only", ""]
    out.append("statuses, per unit:")
    out += [f"  {_SHORT[s]:<22} {m}" for s, m in card["statuses"].items()]
    out.append("")
    for i, c in enumerate(card["checks"], 1):
        f = c["fleet"]
        out.append(f"[{i}] {c['id']} — {c['title']}  ({c['independence'].upper()}; "
                   f"unit: {c['unit']})")
        out.append(f"    subject:       {c['subject']}")
        out.append(f"    second source: {c['second_source']}")
        out.append(f"    tolerance:     {c['tolerance']}")
        out.append(f"    population:    {c['population']}")
        out.append(f"    can surface:   {', '.join(x.replace('_', ' ') for x in c['catches'])}")
        if c["stated_reason"]:
            out.append(f"    stated reason: {c['stated_reason']}")
        out.append(f"    FLEET: {f['units']} {c['unit']}(s) on {f['items_run']} of {f['items']} "
                   f"{noun}s — " + " · ".join(f"{f[s]} {_SHORT[s]}" for s in STATUSES)
                   + (f" · {f['excluded']} excluded ({c['excluded_rule']})"
                      if f["excluded"] else ""))
        for label, groups in (("not run", c["not_run"]), ("not applicable", c["not_applicable"])):
            for g in groups:
                out.append(f"    {label} on {len(g['names'])}: {', '.join(g['names'])} — "
                           f"{g['reason']}")
        run = {t: v for t, v in c["by_name"].items()
               if "not_run" not in v and "not_applicable" not in v}
        cells = [f"{t} {'/'.join(str(v[s]) for s in STATUSES)}" for t, v in run.items()]
        out.append("    by name, confirmed/stated/unexplained/unchecked "
                   f"(all {len(run)} {noun}s run):")
        out += _rows(cells)
        out.append("")
    out.append(f"COVERAGE MAP — how each {src['title']} field family is verified")
    for k, m in card["coverage_classes"].items():
        out.append(f"  {k:<14} {m}")
    out.append("  guards: per failure class, ind = an independent check, int = internal only, "
               "no = nothing")
    out.append("")
    for e in card["coverage"]:
        checks = "; ".join(f"{x['id']} on {x['items_run']}/{b['items']} {noun}s, {x['confirmed']} "
                           f"of {x['units']} confirmed" for x in e["checks"]) or "no scored check"
        mark = {INDEPENDENT: "ind", INTERNAL: "int", "none": "no"}
        guards = " ".join(f"{_FC_SHORT[fc]}:{mark[g]}" for fc, g in e["failure_guard"].items())
        out.append(f"  {e['classification'].upper():<14} {e['family']} — {e['carries']}")
        out.append(f"  {'':<14} {checks}")
        out.append(f"  {'':<14} guards {guards}")
        for u in e["unscored"]:
            out.append(f"  {'':<14} UNSCORED: {u}")
        if "counted" in e:
            out.append(f"  {'':<14} counted: " + ", ".join(f"{k} {v}"
                                                          for k, v in e["counted"].items()))
        if e["note"]:
            out.append(f"  {'':<14} note: {e['note']}")
    totals = Counter(e["classification"] for e in card["coverage"])
    out.append("")
    out.append(f"{len(card['coverage'])} families: " + " · ".join(
        f"{totals.get(k, 0)} {k}" for k in COVERAGE_MEANING))
    out.append("FAILURE CLASSES — families guarded by an independent check / internal only / "
               "nothing though a second source exists / nothing, single-source:")
    for fc, row in card["failure_class_summary"].items():
        out.append(f"  {fc.replace('_', ' '):<21} {row[INDEPENDENT]:>2} / {row[INTERNAL]:>2} / "
                   f"{row['none']:>2} / {row['none_single_source']:>2}   "
                   f"({card['failure_classes'][fc]})")
    return "\n".join(out)


def snapshot_path(root: Path, source_id: str, measured_on: str) -> Path:
    return root / "data" / "snapshots" / "data_quality" / source_id / f"{measured_on}.json"


# --- the exceptions form ------------------------------------------------------------------------


def full_rows_path(root: Path, source_id: str, measured_on: str) -> Path:
    """Where an EXCEPTIONS source's full card goes: under ``data/``, so git-ignored, beside the
    store it was read from — in the checkout that ran it and nowhere else."""
    return root / "data" / "data_quality_full" / source_id / f"{measured_on}.json"


def _listed(row: dict[str, Any]) -> bool:
    """A row the exceptions form lists: the check did not run on the name, judged none of its
    units, left one out by its own rule, or found one not confirmed."""
    if "not_applicable" in row:
        return False
    return ("not_run" in row or row.get("excluded", 0) > 0
            or not sum(row[s] for s in STATUSES) or any(row[s] for s in _NOT_CONFIRMED))


def _listing(c: dict[str, Any], noun: str, ran: int, not_run: int) -> str:
    """A check's own statement of what it lists and what it only counts."""
    f, kept = c["fleet"], c["not_listed"]
    return (f"{ran + not_run:,} of {f['items']:,} {noun}s listed in full: {ran:,} the check ran on "
            f"and did not confirm in full, {not_run:,} it did not run on. Counted, not listed: "
            f"{kept['confirmed_names']:,} {noun}s whose every {c['unit']} is confirmed "
            f"({kept['confirmed_units']:,} {c['unit']}(s)), and "
            f"{sum(g['count'] for g in c['not_applicable']):,} it does not apply to")


def compact(card: dict[str, Any], *, full_path: str, full_sha256: str) -> dict[str, Any]:
    """The EXCEPTIONS form of a full card (operator ruling C1, 2026-10-29). Each check keeps every
    row it did not confirm in full exactly as the full card holds it, and COUNTS the rest — the
    names whose every unit is confirmed and the names it does not apply to — saying so in its
    own ``listing``. The boundary, the fleet counts, the not-run reasons and the coverage map are
    the full card's. ``full_path`` and ``full_sha256`` name the full card as written. Refused
    unless it reconciles (`reconcile`)."""
    noun = card["boundary"]["item_noun"]
    checks = []
    for c in card["checks"]:
        rows = {t: r for t, r in c["by_name"].items() if _listed(r)}
        confirmed = [r for t, r in c["by_name"].items()
                     if t not in rows and "not_applicable" not in r]
        out: dict[str, Any] = {}
        for k, v in c.items():
            if k == "not_applicable":
                out[k] = [{"reason": g["reason"], "count": len(g["names"])} for g in v]
            elif k == "by_name":
                out["not_listed"] = {"confirmed_names": len(confirmed),
                                     "confirmed_units": sum(r[CONFIRMED] for r in confirmed)}
                not_run = sum(1 for r in rows.values() if "not_run" in r)
                out["listing"] = _listing(out, noun, len(rows) - not_run, not_run)
                out[k] = rows
            else:
                out[k] = v
        checks.append(out)
    head = {"schema": COMPACT_SCHEMA, "rows": {
        "form": EXCEPTIONS,
        "statement": (
            f"EXCEPTIONS ONLY (operator ruling C1, 2026-10-29). Each check lists in full every "
            f"{noun} it did not confirm in full — a unit not confirmed, a unit its own rule leaves "
            f"out, or the check not run on it — exactly as the full card holds it. The {noun}s "
            f"whose every unit is confirmed, and those a check does not apply to, are COUNTED, NOT "
            f"LISTED: each check's `listing` and `not_listed` say how many. The boundary, the "
            f"fleet counts and the not-run reasons are the full card's. The full card, every "
            f"{noun} for every check, was written to `full.path`: git-ignored, it exists only in "
            f"the checkout that ran the scorecard, and `full.sha256` is the hash of its bytes."),
        "full": {"path": full_path, "sha256": full_sha256}}}
    out_card = {**head, **{k: (checks if k == "checks" else v) for k, v in card.items()
                           if k != "schema"}}
    reconcile(out_card)
    return out_card


def reconcile(card: dict[str, Any]) -> None:
    """An EXCEPTIONS card against its own rows — raises on the first thing that disagrees.

    Per check: every listed row is an exception (`_listed`) of a name in the boundary; the listed
    names it ran on plus the confirmed names it only counts are the names it ran on; its not-run
    rows are its not-run groups, reason for reason; its not-applicable counts are its
    not-applicable names; every status's units on the listed rows, plus the confirmed units it
    only counts, are the fleet's; and its ``listing`` states exactly those numbers. A dropped row,
    a moved count or a stale statement each fails here, so the form cannot lose what it says it
    counts."""
    rows_block = card.get("rows") or {}
    if card.get("schema") != COMPACT_SCHEMA or rows_block.get("form") != EXCEPTIONS:
        raise ValueError(f"not an exceptions card: schema {card.get('schema')!r}")
    full = rows_block.get("full") or {}
    if not (rows_block.get("statement") and full.get("path") and full.get("sha256")):
        raise ValueError("an exceptions card must state its form and name its full card")
    b = card["boundary"]
    names = set(b["names"])
    if len(names) != b["items"]:
        raise ValueError(f"boundary: {b['items']} items, {len(names)} distinct names")
    for c in card["checks"]:
        where = f"{card['source']['id']}.{c['id']}"
        f, rows, kept = c["fleet"], c["by_name"], c.get("not_listed")
        if kept is None or "listing" not in c:
            raise ValueError(f"{where}: no statement of what it counts and does not list")
        if bad := sorted(t for t, r in rows.items() if t not in names or not _listed(r)):
            raise ValueError(f"{where}: listed rows that are not exceptions in the boundary {bad}")
        ran = [r for r in rows.values() if "not_run" not in r]
        not_run = {t: r["not_run"] for t, r in rows.items() if "not_run" in r}
        if not_run != {t: g["reason"] for g in c["not_run"] for t in g["names"]}:
            raise ValueError(f"{where}: its not-run rows are not its not-run groups")
        got = {"items": f["items_run"] + f["items_not_run"] + f["items_not_applicable"],
               "items_run": len(ran) + kept["confirmed_names"],
               "items_not_run": len(not_run),
               "items_not_applicable": sum(g["count"] for g in c["not_applicable"]),
               "units": sum(f[s] for s in STATUSES),
               CONFIRMED: sum(r[CONFIRMED] for r in ran) + kept["confirmed_units"],
               **{s: sum(r[s] for r in ran) for s in _NOT_CONFIRMED},
               "excluded": sum(r.get("excluded", 0) for r in ran)}
        want = {k: f[k] for k in got} | {"items": b["items"]}
        if got != want or f["items"] != b["items"]:
            raise ValueError(f"{where}: counts do not reconcile — " + "; ".join(
                f"{k} {got[k]} against {want[k]}" for k in got if got[k] != want[k]))
        if c["listing"] != _listing(c, b["item_noun"], len(ran), len(not_run)):
            raise ValueError(f"{where}: its listing does not state its own counts")
