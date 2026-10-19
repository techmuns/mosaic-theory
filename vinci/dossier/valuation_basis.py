"""THE ACTIVE RECIPE'S VALUATION BASIS, AND THE PAGE'S DATES, NAMED (2026-10-09).

THE OPERATOR'S SCHEMA CORRECTION. AMZN's page is tagged `R4_forward_ev_ebit`, yet the block that
carries the tag — `anchor` — holds R1's screen arithmetic: an EV/EBITDA multiple, EDGAR net debt, a
weighted-average diluted share count. A consumer reading the page (the underwriting prompts) could
take an R1 field for the active recipe's. Ruled 2026-10-09: the anchor stays R1's screen, its value
fields carry their eligibility (`Anchor.scenario_eligibility`), and the ACTIVE recipe's basis is
stated in one block beside it — `valuation_basis`, built here.

ONE FUNCTION OF THE PAGE. Every value is read from a layer already on the page, and the layer is
named beside it; nothing is estimated and no judgment is added. `schemas.dossier_json` re-derives
both blocks on every write, so they describe the page that was written.

GENERIC BY RECIPE FAMILY, never by ticker: R1 (any tag starting "R1"), R3, R4. Any other tag —
`R2_NEEDED`, `unknown` — is NOT PRICEABLE here and says why; no basis is invented for it.

THE GATE. Each input the active recipe requires that is missing or disagrees is a CONFLICT, listed
on the block and written to `qa_flags` as VALUATION_RECIPE_BASIS_CONFLICT — and the field it names
stays empty. A conflict is never repaired by substituting another basis's figure: an R4 page
without a CIQ bridge does NOT fall back to the anchor's EDGAR net debt.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from vinci.dossier.anchor import NET_DEBT_EX_LEASE, r1_multiple_band
from vinci.dossier.ciq_sheets import EV_BRIDGE_CIQ_TOL
from vinci.dossier.midcycle import R1_FORMULA
from vinci.dossier.schemas import DateSemantics, Dossier, ValuationBasis

#: Recipe ids and formulas, mirrored from `vinci.scenarios` (pinned equal in the tests): this
#: module sits on the dossier side, which must not import the scenario engine.
RECIPE_R1 = "R1_midcycle_margin_evebitda"
RECIPE_R3 = "R3_forward_pe"
RECIPE_R4 = "R4_forward_ev_ebit"
BASIS_PE = "P/E"
BASIS_EV_NTM_EBIT = "EV/NTM EBIT"
R3_FORMULA: tuple[str, ...] = ("value/share = EPS × forward P/E multiple",)
R4_FORMULA: tuple[str, ...] = (
    "EV = NTM EBIT at exit × EV/NTM EBIT multiple",
    "equity = EV − net debt at exit (CIQ basis)",
    "value/share = equity ÷ diluted shares",
)

CONFLICT_FLAG = "VALUATION_RECIPE_BASIS_CONFLICT"

#: The exit-claims methods, named for a reader rather than for the bridge's own two-word
#: vocabulary (`ExitClaims.method`), which is unchanged.
_EXIT_METHOD = {"held": ("HOLD_CURRENT_SAME_BASIS", "assumption"),
                "consensus": ("SAME_BASIS_CONSENSUS", "forecast")}

_SHARES_BASIS = ("BASIC shares outstanding at the EDGAR cover date (point-in-time) — it EXCLUDES "
                 "the dilutive increment (options, RSUs, convertibles)")
_SHARES_OVERRIDE = ("replace with the point-in-time DILUTED count — this basic count plus the "
                    "dilutive increment stated from the filing (options and RSUs by the "
                    "treasury-stock method, convertibles if-converted) — or with a reliable, "
                    "explicit forward share-count forecast on that basis; never the diluted "
                    "weighted average, which is a period average")

#: Non-operating assets on an ENTERPRISE recipe whose multiple is a vendor-TEV series — the
#: operator's 2026-10-08 R4 ruling ("non-operating investments stay inside the multiple, for now"),
#: made the generic default by the 2026-10-09 schema correction. No amount is carried: the policy is
#: a rule, not a figure.
_NON_OP_VENDOR_TEV: dict[str, Any] = {
    "primary_treatment": "included_in_vendor_tev",
    "carve_out": False,
    "reason": ("the primary current and historical EV multiple series use the vendor's TEV "
               "definition, which carries non-operating investments inside enterprise value; "
               "carving them out of the bridge alone would value a different enterprise than the "
               "one the multiple was struck on"),
    "adjusted_operating_ev_allowed": True,
    "adjustment_condition": ("only if BOTH the current and the historical valuation series are "
                             "rebuilt consistently on the adjusted operating-EV basis — a "
                             "separate, consistently rebased framework, never a carve-out in "
                             "the bridge alone"),
}


def _get(d: Any, *path: str) -> Any:
    for k in path:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def _num(x: Any) -> float | None:
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None


#: How close FY multiple × that year's consensus must come to the snapshot TEV for the multiple to
#: be called struck at it. Face validity, not fitted: on 2026-10-09 the 20 pages whose exports are
#: one pull agreed to 0.005% (rounding); the three that did not were off by 1.0%–8.3%.
SNAPSHOT_TOL = 0.001


def _with_snapshot(d: dict[str, Any], cur: dict[str, Any]) -> dict[str, Any]:
    """The snapshot today's multiple is struck at, tested; and the multiple at the page's price."""
    si = _get(d, "mechanical", "stock_info") or {}
    fc = d.get("forward_consensus") or {}
    mc, price = _num(_get(si, "market_cap", "value")), _num(_get(si, "price", "value"))
    shares = _num(_get(si, "shares_out", "value"))
    snap_day, price_day = _day(si.get("market_cap_as_of")), _day(si.get("as_of"))
    out = dict(cur, snapshot_as_of=si.get("market_cap_as_of"), snapshot_market_cap=mc,
               page_price=price, page_price_as_of=si.get("as_of"),
               days_price_after_snapshot=((price_day - snap_day).days
                                          if price_day and snap_day else None))
    if cur["metric"] == "TEV/EBIT":
        claims = _num(_get(d, "ev_bridge", "ciq_tev_claims"))
        if mc is None or claims is None:
            return out
        tev = out["snapshot_tev"] = mc + claims
        means = {s.get("period"): _num(s.get("mean")) for s in fc.get("spreads") or []
                 if isinstance(s, dict) and s.get("metric") == "EBIT"}
        fy = [(v, e) for m in fc.get("current_multiples") or []
              if m.get("metric") == "TEV/EBIT" and str(m.get("period")).startswith("FY")
              and (v := _num(m.get("value"))) and (e := means.get(m["period"]))]
        if fy:
            out["snapshot_reconciles"] = all(
                abs(v * e - tev) / tev <= SNAPSHOT_TOL for v, e in fy)
        if out.get("snapshot_reconciles") and price and shares:
            ev_at_price = price * shares / 1e6 + claims
            out["value_at_page_price"] = round(cur["value"] * ev_at_price / tev, 6)
            out["value_at_page_price_basis"] = (
                "(page price × point-in-time shares outstanding + CIQ claims) ÷ (snapshot TEV ÷ "
                "the multiple) — the entry multiple an R4 record at the page's price carries")
    elif cur["metric"] == "Price/Earnings":
        eps = {round(e, 6) for f in _get(fc, "pe_eps_basis", "fits") or []
               if isinstance(e := _num(f.get("ntm_implied_eps")), float)}
        if price and len(eps) == 1:
            out["value_at_page_price"] = round(price / eps.pop(), 6)
            out["value_at_page_price_basis"] = ("page price ÷ the NTM EPS CIQ's NTM P/E implies "
                                                "(forward_consensus.pe_eps_basis)")
    return out


def _current_multiple(d: dict[str, Any], metric: str) -> dict[str, Any] | None:
    """TODAY'S NTM multiple from CIQ Estimates (`forward_consensus.current_multiples`), with the
    snapshot it is struck at."""
    fc = d.get("forward_consensus") or {}
    for m in fc.get("current_multiples") or []:
        if isinstance(m, dict) and m.get("metric") == metric and m.get("period") == "NTM":
            v = _num(m.get("value"))
            if v is None:
                return None
            return _with_snapshot(d, {
                "metric": metric, "period": "NTM", "value": v, "as_of": fc.get("as_of"),
                "source": "forward_consensus.current_multiples (CIQ Estimates→Multiples)"})
    return None


def _share_count(d: dict[str, Any]) -> dict[str, Any]:
    """The per-share denominator policy: the point-in-time count, held; the EPS count apart."""
    so = _get(d, "mechanical", "stock_info", "shares_out") or {}
    ds = _get(d, "anchor", "diluted_shares") or {}
    return {
        "default_method": "HOLD_CURRENT_SHARES_OUTSTANDING",
        "current_value": _num(so.get("value")),
        "unit": "shares",
        "current_source": (f"mechanical.stock_info.shares_out ({so.get('source_ref')})"
                           if so else None),
        "count_basis": _SHARES_BASIS,
        "includes_dilutive_increment": False,
        "forecast_status": "assumption",
        "override_allowed": True,
        "override_rule": _SHARES_OVERRIDE,
        "diluted_weighted_average": ({
            "value": _num(ds.get("value")), "unit": ds.get("unit") or "shares",
            "source": f"anchor.diluted_shares ({ds.get('basis')}; {ds.get('source')})",
            "eligible_as_point_in_time_denominator": False} if ds else None),
    }


def _shares_conflict(d: dict[str, Any], conflicts: list[str]) -> None:
    """THE TEMPLATE'S OWN SHARE GUARD (`propose.resolve_shares`), applied here so `priceable`
    never says yes where `scenario-propose` refuses (2026-10-10). It refuses an absent
    point-in-time count, and one more than 2% from the diluted weighted average — a conversion, a
    raise or a split, not the buyback pace. IT (5.43%) and LLY (5.06%), both R1, were first called
    priceable here; the
    diluted weighted average is never substituted for the missing or disputed count."""
    from vinci.dossier.propose import ProposalRefusedError, resolve_shares

    try:
        resolve_shares(d)
    except ProposalRefusedError as exc:
        conflicts.append(str(exc))


def _anchor_net_debt_label(d: dict[str, Any]) -> str:
    """What the anchor's net debt IS, named from its own basis field — ex-lease on a lease-material
    name since 2026-10-19, lease-inclusive everywhere else."""
    if (_get(d, "anchor", "net_debt", "basis") or "") == NET_DEBT_EX_LEASE:
        return "EDGAR net debt excluding operating leases (the anchor's)"
    return "EDGAR lease-inclusive net debt (the anchor's)"


def _r4_bridge(eb: dict[str, Any], anchor_label: str) -> dict[str, Any]:
    ciq = _num(eb.get("ciq_tev_claims"))
    claims = _num(eb.get("claims"))
    return {
        "primary_basis": "CIQ TEV-compatible",
        "current_claims": claims,
        "current_claims_source": (
            "ev_bridge.claims — CIQ Net Debt + preferred + minority interest at the "
            f"{eb.get('balance_sheet_date')} balance sheet ({eb.get('source_file')}, "
            f"sha {eb.get('source_sha256')})"),
        "balance_sheet_date": eb.get("balance_sheet_date"),
        "components": [{"label": ln.get("label"), "sign": ln.get("sign"),
                        "value": _num(ln.get("value"))} for ln in eb.get("lines") or []],
        "ciq_tev_less_market_cap": ciq,
        "reconciles_to_ciq_tev": (abs(claims - ciq) <= EV_BRIDGE_CIQ_TOL
                                  if claims is not None and ciq is not None else None),
        "cross_check": {
            "basis": anchor_label,
            "value": _num(eb.get("edgar_net_debt")), "source": eb.get("edgar_source"),
            "eligible_for_primary_bridge": False,
            "reason": ("a different capital-structure and asset-classification basis from the "
                       "vendor TEV the EV/NTM EBIT multiple is struck on — a cross-check, never "
                       "substituted into the bridge")},
    }


def _r4_exit_claims(eb: dict[str, Any]) -> dict[str, Any]:
    years = [{"fiscal_year": x.get("fiscal_year"), "value": _num(x.get("value")),
              "method": _EXIT_METHOD[x["method"]][0],
              "forecast_status": _EXIT_METHOD[x["method"]][1]}
             for x in eb.get("exit_claims") or [] if x.get("method") in _EXIT_METHOD]
    methods = {y["method"] for y in years}
    statuses = {y["forecast_status"] for y in years}
    return {
        "method": methods.pop() if len(methods) == 1 else "PER_YEAR",
        "forecast_status": statuses.pop() if len(statuses) == 1 else "mixed",
        "current_claims": _num(eb.get("claims")),
        "by_year": years,
        "fcf_rollforward_used": False,
        "rule": eb.get("rule") or "",
        "reason": eb.get("note"),
    }


def _r4(d: dict[str, Any], conflicts: list[str]) -> dict[str, Any]:
    cur = _current_multiple(d, "TEV/EBIT")
    if cur is None:
        conflicts.append("no CIQ Estimates NTM TEV/EBIT on the page "
                         "(forward_consensus.current_multiples) — R4's multiple has no current")
    elif cur["value"] <= 0:
        conflicts.append(f"CIQ's NTM TEV/EBIT is not positive ({cur['value']}) — R4 prices a "
                         "positive forward operating profit")
    if cur is not None and cur.get("snapshot_reconciles") is False:
        conflicts.append(
            "the NTM TEV/EBIT is not struck at the page's CIQ snapshot: FY TEV/EBIT × EBIT "
            f"consensus differs from market cap + CIQ claims by more than {SNAPSHOT_TOL:.1%} — the "
            "Estimates and comps exports are different pulls")
    eb = d.get("ev_bridge")
    out: dict[str, Any] = {
        "earnings_basis": "NTM EBIT", "multiple_basis": BASIS_EV_NTM_EBIT,
        "current_multiple": cur,
        "history_series": "forward_multiple_history.series[metric='EV/NTM EBIT']",
        "ev_bridge_basis": "CIQ TEV-compatible",
        "scenario_formula": "(exit_ntm_ebit * exit_ev_ntm_ebit) - exit_tev_claims",
        "per_share_formula": "exit_equity_value / exit_share_count",
        "formula_steps": list(R4_FORMULA),
        "non_operating_assets": _NON_OP_VENDOR_TEV,
        "exit_share_count": _share_count(d),
    }
    _shares_conflict(d, conflicts)
    if not isinstance(eb, dict):
        conflicts.append("no CIQ TEV bridge on the page (ev_bridge) — the anchor's EDGAR net debt "
                         "is NOT substituted for it")
        return out
    bridge = _r4_bridge(eb, _anchor_net_debt_label(d))
    out["ev_bridge"], out["exit_claims"] = bridge, _r4_exit_claims(eb)
    if bridge["ciq_tev_less_market_cap"] is None:
        conflicts.append("the bridge is unchecked: no CIQ TEV less market cap to test it against")
    elif bridge["reconciles_to_ciq_tev"] is False:
        conflicts.append(f"the bridge ({bridge['current_claims']}) disagrees with CIQ's TEV less "
                         f"market cap ({bridge['ciq_tev_less_market_cap']}) by more than "
                         f"{EV_BRIDGE_CIQ_TOL} ($M)")
    fc_sha = _get(d, "forward_consensus", "source_sha256")
    if eb.get("estimates_sha256") and fc_sha and eb["estimates_sha256"] != fc_sha:
        conflicts.append(f"the bridge and the multiple come from two Estimates pulls "
                         f"({eb['estimates_sha256']} vs {fc_sha})")
    if not out["exit_claims"]["by_year"]:
        conflicts.append("the bridge carries no exit claims")
    return out


def _r1(d: dict[str, Any], conflicts: list[str]) -> dict[str, Any]:
    a = d.get("anchor") or {}
    nd = a.get("net_debt") or {}
    raw = d.get("ev_bridge")
    eb: dict[str, Any] = raw if isinstance(raw, dict) else {}
    # THE ANCHOR SAYS WHICH HISTORY AND WHICH BRIDGE IT PRICED ON (2026-10-19): ex-lease on a
    # lease-material name, CIQ's own otherwise. Read from its fields, never re-decided here.
    mult_ex = str(_get(a, "multiple", "source") or "").startswith("valuation.lease_basis")
    nd_label = _anchor_net_debt_label(d)
    out: dict[str, Any] = {
        "earnings_basis": "EBITDA at exit (revenue × operating margin + D&A)",
        "multiple_basis": a.get("multiple_basis"),
        "current_multiple": None,
        "history_series": (
            "mechanical.valuation.lease_basis.ex_lease_band (trailing EV/EBITDA ex-lease: TEV "
            "less operating leases / LTM EBITDA)" if mult_ex
            else "mechanical.valuation.own_history (trailing EV/EBITDA, TEV/LTM)"),
        "ev_bridge_basis": nd_label,
        "scenario_formula": ("((exit_revenue * exit_operating_margin) + d_and_a) * exit_ev_ebitda "
                             "- net_debt"),
        "per_share_formula": "exit_equity_value / exit_share_count",
        "formula_steps": list(R1_FORMULA),
        "non_operating_assets": _NON_OP_VENDOR_TEV,
        "exit_share_count": _share_count(d),
        "ev_bridge": {
            "primary_basis": nd_label,
            "current_claims": _num(nd.get("value")),
            "current_claims_source": f"anchor.net_debt ({nd.get('source')})",
            "ciq_tev_less_market_cap": _num(eb.get("ciq_tev_claims")),
            "reconciles_to_ciq_tev": None,
            "cross_check": ({
                "basis": "CIQ TEV claims (ev_bridge)", "value": _num(eb.get("claims")),
                "source": "ev_bridge.claims", "eligible_for_primary_bridge": False,
                "reason": ("R1's record subtracts the anchor's EDGAR net debt by its own rule; "
                           "CIQ's claims are shown beside it, never substituted")} if eb else None),
        },
        "exit_claims": {
            "method": "HOLD_CURRENT_SAME_BASIS", "forecast_status": "assumption",
            "current_claims": _num(nd.get("value")), "by_year": [], "fcf_rollforward_used": False,
            "rule": "R1's record subtracts the anchor's net debt as given — today's figure, held",
            "reason": None},
    }
    if a.get("applicable"):
        for key in ("multiple", "d_and_a", "net_debt"):
            if _num(_get(a, key, "value")) is None:
                conflicts.append(f"R1 needs anchor.{key} and the page carries none")
        # ONE LEASE BASIS ACROSS THE PAIR, and the page's: an ex-lease multiple against a
        # lease-inclusive bridge (or the reverse) misprices by the whole lease book, and an anchor
        # derived before the page's lease basis landed is on the wrong one (2026-10-19)
        nd_ex = nd.get("basis") == NET_DEBT_EX_LEASE
        if mult_ex != nd_ex:
            conflicts.append(
                f"R1's multiple ({'ex-lease' if mult_ex else 'lease-inclusive'}) and net debt "
                f"({'ex-lease' if nd_ex else 'lease-inclusive'}) are on different lease bases")
        sel = r1_multiple_band(d.get("mechanical") or {})
        if sel.ex_lease != mult_ex:
            conflicts.append(
                "the anchor's multiple is not on the page's lease basis "
                f"({'ex-lease' if sel.ex_lease else 'CIQ'} history; {sel.materiality}) — "
                "re-derive the anchor (anchor-backfill)")
        _shares_conflict(d, conflicts)
    return out


def _r3(d: dict[str, Any], conflicts: list[str]) -> dict[str, Any]:
    cur = _current_multiple(d, "Price/Earnings")
    basis = _get(d, "forward_consensus", "pe_eps_basis", "ntm")
    if cur is None:
        conflicts.append("no CIQ Estimates NTM P/E on the page "
                         "(forward_consensus.current_multiples)")
    if basis is None:
        conflicts.append("the NTM P/E's EPS line is not measured "
                         "(forward_consensus.pe_eps_basis absent)")
    return {
        "earnings_basis": f"NTM EPS — the {basis} line CIQ's NTM P/E is struck on" if basis
        else "NTM EPS — line not measured",
        "multiple_basis": BASIS_PE, "current_multiple": cur,
        "history_series": ("forward_multiple_history.series[metric='P/NTM EPS'] "
                           "(context only — BASIS MATCH: LIMITED)"),
        "ev_bridge_basis": None,
        "scenario_formula": "exit_ntm_eps * exit_pe",
        "per_share_formula": "the value is per share already (EPS × P/E)",
        "formula_steps": list(R3_FORMULA),
    }


def derive(d: dict[str, Any]) -> ValuationBasis:
    """The active recipe's basis, read off the page (a dossier as JSON)."""
    a = d.get("anchor") or {}
    hint = a.get("recipe_hint") or "unknown"
    applicable = bool(a.get("applicable"))
    anchor_ok = hint.startswith("R1") and applicable
    conflicts: list[str] = []
    if hint == RECIPE_R4:
        body, accepted = _r4(d, conflicts), True
        why = "R4: priced as NTM EBIT × EV/NTM EBIT, bridged on CIQ's TEV basis"
    elif hint.startswith("R1"):
        body, accepted = _r1(d, conflicts), applicable
        why = (f"R1-family ({hint}): priced from the anchor's R1 inputs" if applicable else
               f"tagged {hint}, but R1's anchor declines (applicable=False) — the scenario gate "
               "refuses an R1 record on this page")
    elif hint == RECIPE_R3:
        body, accepted = _r3(d, conflicts), True
        why = "R3: priced as NTM EPS × forward P/E — an equity multiple, so no bridge"
    else:
        body, accepted = {}, False
        why = (f"no machine-priceable recipe is tagged ({hint}) — no valuation basis is derived "
               "for it here; a record on this name states its own basis")
    if conflicts:
        why += f" — {len(conflicts)} conflict(s), see `conflicts`"
    return ValuationBasis.model_validate({
        "recipe": hint, "priceable": accepted and not conflicts, "status_reason": why, **body,
        "anchor_fields_eligible": anchor_ok, "conflicts": conflicts})


def _day(s: Any) -> date | None:
    """The calendar day a page date names; a `≥` floor counts at its floor."""
    if not isinstance(s, str):
        return None
    try:
        return date.fromisoformat(s.lstrip("≥").strip()[:10])
    except ValueError:
        return None


def date_semantics(d: dict[str, Any]) -> DateSemantics:
    """Every date the page's inputs carry, named — read, never inferred."""
    m = d.get("mechanical") or {}
    named = {
        "price_as_of": _get(m, "stock_info", "as_of"),
        "market_cap_as_of": _get(m, "stock_info", "market_cap_as_of"),
        "tev_as_of": _get(m, "valuation", "implied_expectations", "tev_as_of"),
        "consensus_as_of": _get(d, "forward_consensus", "as_of"),
        "balance_sheet_date": _get(d, "ev_bridge", "balance_sheet_date"),
        "historical_multiple_latest_observation": _get(d, "forward_multiple_history", "as_of"),
    }
    days = [x for x in map(_day, named.values()) if x is not None]
    return DateSemantics.model_validate({
        "screen_reference_date": str(d.get("reference_date"))[:10],
        "reference_date_semantics": (
            "the screening/reference date the page was assembled against — NOT the freshness "
            "date of its inputs; each input's own date is named in this block"),
        "analysis_as_of": max(days).isoformat() if days else None,
        "analysis_as_of_rule": (
            "the latest of price_as_of, market_cap_as_of, tev_as_of, consensus_as_of (a '≥' date "
            "counts at its floor), balance_sheet_date and historical_multiple_latest_observation"),
        **named,
        "historical_multiple_history_through": _get(d, "forward_multiple_history",
                                                    "history_through"),
        "stock_performance_as_of": _get(m, "stock_performance", "as_of"),
        "assembled_at": d.get("assembled_at"),
        "valuation_snapshot_as_of": named["market_cap_as_of"],
        "price_days_after_valuation_snapshot": (
            (p - s).days if (p := _day(named["price_as_of"]))
            and (s := _day(named["market_cap_as_of"])) else None),
    })


def with_derived(doc: Dossier) -> Dossier:
    """`doc` with both blocks re-derived and its VALUATION_RECIPE_BASIS_CONFLICT flags in step."""
    d = doc.model_dump(mode="json")
    vb = derive(d)
    flags = [f for f in doc.qa_flags if not f.startswith(CONFLICT_FLAG)]
    flags += [f"{CONFLICT_FLAG}: {c}" for c in vb.conflicts]
    return doc.model_copy(update={"valuation_basis": vb, "date_semantics": date_semantics(d),
                                  "qa_flags": flags})
