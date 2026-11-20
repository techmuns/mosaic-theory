"""One compact line-set per probed name, straight from out/probe/*.json (no re-interpretation)."""

from __future__ import annotations

import json
import sys

from probe_common import OUT

NS_SHOWN = ("us-gaap", "ifrs-full", "dei")

names = sys.argv[1:] or sorted(p.stem for p in (OUT / "probe").glob("*.json"))
for t in names:
    p = OUT / "probe" / f"{t}.json"
    if not p.exists():
        print(t, "— not probed")
        continue
    d = json.loads(p.read_text())
    if "fatal" in d:
        print(t, "FATAL", d["fatal"])
        continue
    i = d.get("identity", {})
    f = d.get("filings", {})
    cf = d.get("companyfacts", {})
    fy = d.get("fiscal_year") or {}
    sf = d.get("screen_fundamentals", {})
    a = d.get("anchor_gates", {})
    nd = d.get("net_debt", {})
    sh = d.get("shares", {})
    ev = d.get("event_rule", {})
    pr = d.get("price", {})

    def k(x):
        return "ok" if isinstance(x, dict) and x.get("status") == "present" else "UNK"

    print(
        f"=== {t} cik={i.get('cik')} sic={i.get('sic')} {str(i.get('sic_desc'))[:30]} | "
        f"annual={f.get('latest_annual')} 10q={f.get('n_10q_365')} 6k={f.get('n_6k_365')} "
        f"fye={f.get('fye')}"
    )
    if "raised" in i:
        print("   identity RAISED", i)
        continue
    print(
        f"   cf: ns={ {x: y for x, y in (cf.get('namespaces') or {}).items() if x in NS_SHOWN} } "
        f"cur={cf.get('reporting_currency')} {cf.get('raised', '')} "
        f"{str(cf.get('message', ''))[:90]}"
    )
    print(
        f"   fy: end={fy.get('end')} days={fy.get('days')} tag={fy.get('tag')} "
        f"unit={fy.get('unit')} ifrs_end={fy.get('ifrs_end')}"
    )
    if "raised" in sf:
        print("   screen RAISED", sf)
    elif sf:
        print(
            "   screen: "
            + " ".join(f"{x}={k(v)}" for x, v in sf.items())
            + f" | eps={sf.get('eps_diluted_annual', {}).get('value')} "
            f"ebitda={sf.get('ebitda_annual', {}).get('value')}"
        )
        notes = {x: v.get("note") for x, v in sf.items() if v.get("note")}
        if notes:
            print("     notes:", {x: (n or "")[:80] for x, n in list(notes.items())[:4]})
    if "raised" in a:
        print("   anchor RAISED", a)
    elif a:
        print(
            f"   anchor: rev={a.get('revenue_tag')} ({len(a.get('revenue_years', []))}y) "
            f"oi={a.get('opinc_tag')} "
            f"({len(a.get('opinc_years', []))}y) median={a.get('margin_median')} "
            f"n={a.get('margin_years')} "
            f"conflicts={a.get('revenue_conflicts_total')}"
        )
        print(
            f"     gate: {a.get('gate')} | "
            f"D&A={a.get('d_and_a') if isinstance(a.get('d_and_a'), str) else 'ok'} "
            f"| FCF={a.get('fcf') if isinstance(a.get('fcf'), str) else 'ok'}"
        )
    if nd:
        if "raised" in nd:
            print("   net debt RAISED", nd)
        else:
            print(
                f"   net debt: sic_rule={'REFUSED' if nd.get('sic_rule') else 'n/a'} "
                f"builder_refusal={nd.get('builder_refusal')} "
                f"lev=${(nd.get('leverage_usd') or 0) / 1e9:,.2f}bn at {nd.get('at')} "
                f"incl=${(nd.get('lease_inclusive_musd') or 0) / 1e3:,.2f}bn"
            )
    ar = sh.get("ads_ratio", {})
    print(
        f"   shares: edgar_count={sh.get('edgar_count')} "
        f"ads={ar.get('status')}/{ar.get('ordinary_per_ads')} "
        f"{str(sh.get('message', ''))[:80]}"
    )
    print(
        f"   events(365d)={ev.get('events_365')} {ev.get('by_form')} "
        f"median_gap={ev.get('median_gap_days')}d max_gap={ev.get('max_gap_days')}d "
        f"{ev.get('raised', '')}"
    )
    print(
        f"   price: {pr.get('symbol')} close={pr.get('close_2026_11_18')} "
        f"close/eps={pr.get('close_over_edgar_eps')} "
        f"cap=${(pr.get('cap_close_x_edgar_count') or 0) / 1e9:,.1f}bn {pr.get('raised', '')}"
    )
