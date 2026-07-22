"""R1 APPLICABILITY AUDIT — the seven checks, as standing machinery.

R1 re-rates a business to the median multiple of its own trading history on its own reported
median margin. Both halves of that sentence can be false without anything failing: a median margin
means nothing across a regime break, and a band median means nothing if the window never contains
the state being underwritten. IT carried both defects into a recorded BUY, and neither was visible
until an external review forced a re-underwrite.

This module turns the 2026-07-22 hand audit into something that runs on demand. Seven checks:

1. **margin shape** — is there a mid-cycle margin worth reverting to, or does the series straddle
   a regime break?
2. **band regime** — does the multiple window ever VISIT the state a bear leg describes, or is it
   growth-era-only? (The IT signature.)
3. **bear admissibility** — is the bear multiple above where the name trades TODAY, or above its
   own band floor? A bear leg that assumes a re-rating upward is not a downside case.
4. **leverage** — net debt against anchor equity, and one turn of multiple as a share of spot.
   (The CNXC test: at 100% of spot, the multiple choice IS the valuation.)
5. **perimeter** — a completed acquisition or divestiture inside the trailing window, which makes
   the trailing facts describe an entity that no longer exists.
6. **entity** — multi-class stock, non-controlling interests, or a diluted-vs-outstanding gap.
   (The FUBO test: per-share math on the wrong share base.)
7. **data** — band guards, and the vintage of the D&A and free-cash-flow facts.

FLAGS PRINT, THEY NEVER BLOCK — the prose-linter model. The machine surfaces; the human concludes.
A gate that refused to compute would simply be routed around at the moment it mattered most.
"""
from __future__ import annotations

import json
import re
import statistics as st
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# --- RATIFIED THRESHOLDS (2026-07-22) ----------------------------------------------------------
# Face-validity calibrated against the committed book, never against forward returns. Each is the
# line at which the hand audit's judgment flipped, written down so it stops being a judgment.

# A band whose MINIMUM never fell below this fraction of its median has never visited a bear state:
# its floor is a growth-era floor, and using it as a downside multiple imports the regime it is
# supposed to stress. CNXC (0.64) and AORT (0.58) sit above the line; IT (0.32) below it.
GROWTH_ERA_MIN_MEDIAN = 0.55

# A band too short to contain a cycle. MVST (1.3y / 6 closes) and NCNO (2.3y / 10) are the cases:
# both records SAY so in prose, and nothing enforced it.
SHORT_BAND_YEARS = 3.0
SHORT_BAND_CLOSES = 12

# Peak-to-trough spread of completed-FY operating margin beyond which a median is not "mid-cycle"
# but an average across two different businesses.
MARGIN_SPREAD_MAX = 0.08
# A sustained directional shift (mean of last three FYs vs first three) that makes the same point.
MARGIN_RAMP_SHIFT = 0.03

# Leverage lines. At/above these the multiple choice dominates the valuation.
NET_DEBT_TO_EQUITY_MAX = 0.50
ONE_TURN_OF_SPOT_MAX = 0.30

PERIMETER_QUARTERS = 8

_MA = re.compile(r"(acquisi\w+|acquired|divest\w+|merger|business combination|sold (?:its|the)|"
                 r"disposal|carve-?out|take[ -]private)", re.I)
_DATED = re.compile(r"20(?:2[3-9])-\d{2}-\d{2}")


@dataclass
class Flag:
    check: str
    severity: str          # "flag" (loud) | "note"
    message: str


@dataclass
class NameAudit:
    ticker: str
    rows: dict[str, str] = field(default_factory=dict)     # check -> one-line finding
    flags: list[Flag] = field(default_factory=list)
    # the EXISTING machinery's own verdict on this name — an anchor marked inapplicable, or a
    # recipe tag other than R1, means a gate already caught it.
    anchor_applicable: bool = True
    recipe_hint: str | None = None
    guards_tripped: str | None = None

    @property
    def gate_fired(self) -> bool:
        """Did EXISTING machinery already stop this name? Three ways it can have:
        the band guards tripped, the anchor was marked inapplicable, or the recipe tag routed it
        off R1. Any of those means the flags below are a gate working, not a hole."""
        return bool(self.guards_tripped) or not self.anchor_applicable or (
            self.recipe_hint not in (None, "", "R1_midcycle_margin_evebitda"))

    @property
    def disposition(self) -> str:
        """gate fired / NO GATE / clean — the audit's own summary of the name."""
        if not [f for f in self.flags if f.severity == "flag"]:
            return "clean"
        return "gate exists and FIRED" if self.gate_fired else "*** NO GATE — new exposure"


def _fy_margins(dossier: dict[str, Any]) -> list[float]:
    """Completed-FY operating margin series. Estimate and LTM columns excluded — a median that
    includes consensus is a median of somebody's forecast."""
    fs = (((dossier.get("mechanical") or {}).get("financial_summary") or {})
          .get("annual") or {}).get("value") or {}
    cols, rows = fs.get("columns") or [], fs.get("rows") or []
    rev = next((r for r in rows if str(r.get("label", "")).startswith("Revenue ($M)")), None)
    eb = next((r for r in rows if str(r.get("label", "")).startswith("EBIT (")), None)
    if not rev or not eb:
        return []
    out = []
    for i, c in enumerate(cols):
        if c.endswith("E") or c == "LTM":
            continue
        try:
            rv, ev = rev["values"][i], eb["values"][i]
        except (IndexError, KeyError, TypeError):
            continue
        if rv:
            out.append(ev / rv)
    return out


def _band(dossier: dict[str, Any]) -> dict[str, Any] | None:
    oh = (((dossier.get("mechanical") or {}).get("valuation") or {})
          .get("own_history") or {}).get("value") or []
    row = next((r for r in oh if str(r.get("metric", "")).startswith("EV/EBITDA")
                and r.get("series")), None)
    if not row:
        return None
    ser = [(str(a), float(b)) for a, b in row["series"]]
    span = ((int(ser[-1][0][:4]) + int(ser[-1][0][5:7]) / 12)
            - (int(ser[0][0][:4]) + int(ser[0][0][5:7]) / 12))
    return {"n": row.get("n_closes") or len(ser), "start": ser[0][0], "span": span,
            "min": row["low"], "median": row["median"], "current": row["current"]}


def check_margin_shape(a: NameAudit, dossier: dict[str, Any]) -> None:
    mg = _fy_margins(dossier)
    if len(mg) < 4:
        a.rows["margin"] = f"only {len(mg)} completed FYs — too few to shape"
        a.flags.append(Flag("margin", "flag", f"only {len(mg)} completed FYs of margin history"))
        return
    lo, med, hi = min(mg), st.median(mg), max(mg)
    spread = hi - lo
    shift = st.mean(mg[-3:]) - st.mean(mg[:3])
    if shift < -MARGIN_RAMP_SHIFT and mg[-1] <= lo + 0.02:
        shape = "declining"
    elif shift > MARGIN_RAMP_SHIFT:
        shape = "ramp"
    elif spread > 0.12:
        shape = "reset"
    else:
        shape = "stable"
    a.rows["margin"] = (f"{shape}: n={len(mg)} med {med:.1%} spread {spread:.1%} "
                        f"shift {shift:+.1%}")
    if med <= 0:
        a.flags.append(Flag("margin", "flag", f"median FY margin is NEGATIVE ({med:.1%}) — no "
                                              "mid-cycle margin exists to revert to"))
    elif spread > MARGIN_SPREAD_MAX:
        a.flags.append(Flag("margin", "flag", f"FY margin spread {spread:.1%} exceeds "
                            f"{MARGIN_SPREAD_MAX:.0%} — the median averages two regimes"))
    elif shape == "ramp":
        a.flags.append(Flag("margin", "flag", f"sustained ramp ({shift:+.1%}) — a trailing median "
                                              "describes a business the company has left"))
    if 4 <= len(mg) < 5:
        a.flags.append(Flag("margin", "note", f"thin history: {len(mg)} completed FYs"))


def check_band(a: NameAudit, dossier: dict[str, Any]) -> dict[str, Any] | None:
    b = _band(dossier)
    if b is None:
        a.rows["band"] = "NO COMMITTED BAND"
        a.flags.append(Flag("band", "flag", "no committed multiple band — R1 has nothing to "
                                            "revert to"))
        return None
    ratio = b["min"] / b["median"] if b["median"] else float("nan")
    a.rows["band"] = (f"{b['n']}q / {b['span']:.1f}y from {b['start']} · min {b['min']:.2f} "
                      f"med {b['median']:.2f} cur {b['current']:.2f} · min/med {ratio:.2f}")
    if ratio >= GROWTH_ERA_MIN_MEDIAN:
        a.flags.append(Flag("band", "flag", f"GROWTH-ERA-ONLY band: min/median {ratio:.2f} >= "
                            f"{GROWTH_ERA_MIN_MEDIAN} — the window never visits a bear state"))
    if b["span"] < SHORT_BAND_YEARS or b["n"] < SHORT_BAND_CLOSES:
        a.flags.append(Flag("band", "flag", f"SHORT band: {b['span']:.1f}y / {b['n']} closes "
                            f"(floor {SHORT_BAND_YEARS}y / {SHORT_BAND_CLOSES})"))
    return b


def check_bear(a: NameAudit, record: dict[str, Any] | None, b: dict[str, Any] | None) -> None:
    if not record:
        a.rows["bear"] = "no scenario record"
        return
    leg = (record.get("scenarios") or {}).get("bear") or {}
    bx = leg.get("multiple")
    basis = leg.get("bear_basis") or record.get("bear_basis")
    mbasis = leg.get("margin_basis")
    a.rows["bear"] = (f"{bx}x · bear_basis={basis or 'ABSENT'} margin_basis={mbasis or 'ABSENT'}")
    if bx is None or b is None:
        return
    if bx > b["current"]:
        a.flags.append(Flag("bear", "flag", f"BEAR MULTIPLE ABOVE CURRENT: {bx:.2f}x vs "
                            f"{b['current']:.2f}x — the downside case assumes a re-rating UP"))
    if bx > b["min"]:
        a.flags.append(Flag("bear", "note", f"bear multiple {bx:.2f}x above the band minimum "
                                            f"{b['min']:.2f}x"))
    if not basis:
        a.flags.append(Flag("bear", "flag", "bear_basis ABSENT — the multiple's provenance is "
                                            "unstated"))


def check_leverage(a: NameAudit, dossier: dict[str, Any], spot: float | None) -> None:
    anc = dossier.get("anchor") or {}
    nd = (anc.get("net_debt") or {}).get("value")
    sh = (anc.get("diluted_shares") or {}).get("value")
    vps = anc.get("anchor_base_value_per_share")
    if not anc.get("applicable"):
        a.rows["leverage"] = "anchor not applicable — no base value published (guard behaviour)"
        return
    if nd is None or sh is None or not vps:
        a.rows["leverage"] = f"incomplete anchor (net_debt={nd} shares={sh} base={vps})"
        return
    nd, sh, vps = float(nd), float(sh), float(vps)
    eq = vps * sh / 1e6
    rev = (anc.get("ltm_revenue") or {}).get("value")
    mgn = (anc.get("margin") or {}).get("value")
    dna = (anc.get("d_and_a") or {}).get("value")
    ebitda: float | None = None
    if rev is not None and mgn is not None and dna is not None:
        ebitda = float(rev) * float(mgn) + float(dna)
    turn = (ebitda * 1e6 / float(sh)) if ebitda else None
    pct = (turn / float(spot)) if (turn and spot) else None
    a.rows["leverage"] = (f"net debt {nd:,.1f} = {nd / eq:.1%} of anchor equity"
                          + (f" · 1 turn = ${turn:,.2f} = {pct:.1%} of spot" if pct else ""))
    if nd / eq > NET_DEBT_TO_EQUITY_MAX:
        a.flags.append(Flag("leverage", "flag", f"net debt {nd / eq:.0%} of anchor equity exceeds "
                            f"{NET_DEBT_TO_EQUITY_MAX:.0%}"))
    if pct and pct > ONE_TURN_OF_SPOT_MAX:
        a.flags.append(Flag("leverage", "flag", f"ONE TURN of multiple = {pct:.0%} of spot "
                            f"(over {ONE_TURN_OF_SPOT_MAX:.0%}) — the multiple IS the valuation"))


def check_perimeter(a: NameAudit, dossier: dict[str, Any]) -> None:
    """A completed acquisition/divestiture inside the trailing window makes the trailing facts
    describe an entity that no longer exists.

    NOTE THE KNOWN HOLE, printed rather than hidden: the assembler's ``event_impacts`` field is
    EMPTY on every committed release, so this check falls back to a text scan and will MISS a
    perimeter change that no prose happens to mention. FUBO's reverse merger is the live proof.
    """
    hits, empties = [], 0
    rel = ((dossier.get("mechanical") or {}).get("primary_source") or {}).get("releases") or []
    rel = rel if isinstance(rel, list) else (rel.get("value") or [])
    for r in rel:
        if isinstance(r, dict) and not (r.get("event_impacts") or []):
            empties += 1

    def walk(o: Any) -> None:
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
        elif isinstance(o, str) and _MA.search(o) and _DATED.search(o):
            hits.append(o.strip()[:110])

    walk(dossier)
    uniq = list(dict.fromkeys(hits))
    a.rows["perimeter"] = (f"{len(uniq)} dated M&A mention(s); event_impacts empty on "
                           f"{empties}/{len(rel)} releases")
    if uniq:
        a.flags.append(Flag("perimeter", "flag", f"perimeter event detected — check whether "
                            f"trailing facts straddle it: {uniq[0][:80]}"))
    if rel and empties == len(rel):
        a.flags.append(Flag("perimeter", "note", "event_impacts EMPTY on every release — this "
                            "check is running on a text scan, not on structured capture"))


def check_entity(a: NameAudit, dossier: dict[str, Any]) -> None:
    anc = dossier.get("anchor") or {}
    si = ((dossier.get("mechanical") or {}).get("stock_info") or {})
    dil = (anc.get("diluted_shares") or {}).get("value")
    out = (si.get("shares_out") or {}).get("value")
    blob = json.dumps(dossier, ensure_ascii=False)
    classes = sorted(set(re.findall(r"Class [AB]\b", blob)))
    rnci = bool(re.search(r"redeemable non-?controlling", blob, re.I))
    nci = bool(re.search(r"non-?controlling interest", blob, re.I))
    gap = (out / dil) if (dil and out) else None
    a.rows["entity"] = (f"diluted {dil:,.0f} vs outstanding {out:,.0f} · gap "
                        f"{gap:.2f}x" if gap else "share counts incomplete")
    if gap and (gap > 1.5 or gap < 1 / 1.5):
        a.flags.append(Flag("entity", "flag", f"diluted-vs-outstanding gap {gap:.2f}x — per-share "
                            "math may be on the wrong share base"))
    if rnci:
        a.flags.append(Flag("entity", "flag", "REDEEMABLE NCI present — consolidated value is not "
                                              "all the parent's"))
    elif nci:
        a.flags.append(Flag("entity", "note", "non-controlling interest mentioned"))
    if len(classes) > 1:
        a.flags.append(Flag("entity", "note", f"multi-class stock: {', '.join(classes)}"))


def check_data(a: NameAudit, dossier: dict[str, Any]) -> None:
    anc = dossier.get("anchor") or {}
    dq = anc.get("data_quality")
    da = anc.get("d_and_a") or {}
    fc = anc.get("ltm_fcf") or {}
    a.rows["data"] = (f"guards={dq or 'clean'} · d_and_a[{da.get('basis', '?')}] · "
                      f"ltm_fcf[{(fc.get('basis') or 'absent')}]")
    if dq:
        a.flags.append(Flag("data", "flag", f"band guard(s) tripped: {dq}"))
    if fc and "not LTM" in str(fc.get("basis") or ""):
        a.flags.append(Flag("data", "note", f"ltm_fcf is {fc.get('basis')} — not a trailing "
                                            "twelve months"))


def audit_name(ticker: str, dossier: dict[str, Any], record: dict[str, Any] | None,
               spot: float | None) -> NameAudit:
    anc = dossier.get("anchor") or {}
    a = NameAudit(ticker=ticker, anchor_applicable=bool(anc.get("applicable")),
                  recipe_hint=anc.get("recipe_hint"), guards_tripped=anc.get("data_quality"))
    check_margin_shape(a, dossier)
    band = check_band(a, dossier)
    check_bear(a, record, band)
    check_leverage(a, dossier, spot)
    check_perimeter(a, dossier)
    check_entity(a, dossier)
    check_data(a, dossier)
    return a


def load_and_audit(root: Path) -> list[NameAudit]:
    out: list[NameAudit] = []
    ddir = root / "data" / "dossiers"
    for folder in sorted(p for p in ddir.iterdir() if p.is_dir()) if ddir.exists() else []:
        f = folder / "dossier.json"
        if not f.is_file():
            continue
        dossier = json.loads(f.read_text())
        if not (dossier.get("anchor") or {}):
            continue          # no committed anchor — nothing for R1 to be applicable to
        t = folder.name.upper()
        rp = root / "scenarios" / f"{t}.json"
        record = json.loads(rp.read_text()) if rp.exists() else None
        spot = (((dossier.get("mechanical") or {}).get("stock_info") or {}).get("price")
                or {}).get("value") or (record or {}).get("spot")
        out.append(audit_name(t, dossier, record, spot))
    return out


CHECK_ORDER = ("margin", "band", "bear", "leverage", "perimeter", "entity", "data")


def render(audits: list[NameAudit], *, as_of: str) -> str:
    out = [f"# R1 APPLICABILITY AUDIT — {as_of}", "",
         "Read-only. Flags PRINT, never block (the linter model): the machine surfaces, the human "
         "concludes.", "",
         "## Ratified thresholds", "",
         f"- growth-era-only band: `min/median >= {GROWTH_ERA_MIN_MEDIAN}`",
         f"- short band: `span < {SHORT_BAND_YEARS}y` OR `< {SHORT_BAND_CLOSES} closes`",
         f"- margin median unusable: FY spread > {MARGIN_SPREAD_MAX:.0%}, sustained ramp "
         f"> {MARGIN_RAMP_SHIFT:.0%}, or a negative median",
         f"- leverage: net debt > {NET_DEBT_TO_EQUITY_MAX:.0%} of anchor equity; one turn > "
         f"{ONE_TURN_OF_SPOT_MAX:.0%} of spot",
         "- bear admissibility: bear multiple above the CURRENT multiple (loud), or above the "
         "band minimum (note)", "",
         "## Dispositions", ""]
    for a in audits:
        loud = [f for f in a.flags if f.severity == "flag"]
        why = ""
        if a.gate_fired:
            bits = [b for b in (a.guards_tripped,
                                None if a.anchor_applicable else "anchor not applicable",
                                a.recipe_hint if a.recipe_hint not in
                                (None, "", "R1_midcycle_margin_evebitda") else None) if b]
            why = f" — via {', '.join(bits)}" if bits else ""
        out.append(f"- **{a.ticker}** — {a.disposition}{why}"
                 + (f" ({len(loud)} flag{'s' if len(loud) != 1 else ''})" if loud else ""))
    out += ["", "## Matrix", ""]
    for a in audits:
        out += [f"### {a.ticker} — {a.disposition}", ""]
        for c in CHECK_ORDER:
            out.append(f"- `{c}` — {a.rows.get(c, '—')}")
        for f in a.flags:
            out.append(f"  - {'**FLAG**' if f.severity == 'flag' else 'note'}: {f.message}")
        out.append("")
    return "\n".join(out)


__all__ = ["CHECK_ORDER", "GROWTH_ERA_MIN_MEDIAN", "MARGIN_RAMP_SHIFT", "MARGIN_SPREAD_MAX",
           "NET_DEBT_TO_EQUITY_MAX", "ONE_TURN_OF_SPOT_MAX", "PERIMETER_QUARTERS",
           "SHORT_BAND_CLOSES", "SHORT_BAND_YEARS", "Flag", "NameAudit", "audit_name",
           "load_and_audit", "render"]
