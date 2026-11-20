"""5a item 1 + 2: the $0 end-to-end deterministic build of one name per in-scope archetype, and
the R3/R4 proposal runs where a CIQ consensus block exists.

For each name: (a) `vinci.dossier.prespend.run` — the `vinci dossier precheck --ticker <T>` command
itself, into the SCRATCH data dir (no committed page there, so it checks the refusals only, as on
a first assembly); (b) `prespend.mechanical_build` again for the page it would write, summarised;
(c) the machine's R4 conditions on that page; (d) `propose.build_template` on the page as the
machine tags it, then on the page re-tagged R3 and R4 (a SIMULATED operator tag, re-derived through
`schemas.dossier_json`, the one writer of `valuation_basis`) — the underwrite template each recipe
would hand the analyst, or its refusal.

No LLM client is constructed anywhere (prespend's own `_RefusingClient` refuses every call). CIQ
workbooks are copied from Drive into the scratch manual folder for the run and deleted after."""

from __future__ import annotations

import io
import json
import shutil
import sys
import traceback
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

from probe_common import CFG, OUT, ciq_packs

#: The 2026-10-28 packs, in the dated-pack layout under ARCHETYPE_PROBE_CIQ_PACKS; empty when that
#: is not set. fresh5a.py and variant5a.py replace this map with the loader-layout root.
_PACKS = ciq_packs()
CIQ_SETS: dict[str, Path] = (
    {
        "PLD": _PACKS / "PLD_IQ330123/2026-10-28",
        "RIVN": _PACKS / "RIVN_IQ144746614/2026-10-28",
        "MTB": _PACKS / "MTB_IQ272285/2026-10-28",
        "PCVX": _PACKS / "PCVX_IQ307500026/2026-10-28",
    }
    if _PACKS is not None
    else {}
)
MANUAL = CFG.data_dir / "manual" / "ciq"
DEST = OUT / "build5a"


def copy_ciq(names: list[str]) -> None:
    for t in names:
        if t not in CIQ_SETS:
            continue
        dest = MANUAL / t
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        for p in CIQ_SETS[t].iterdir():
            if p.is_file() and not p.name.startswith("."):
                shutil.copy2(p, dest / p.name)  # Drive read, scratch written


def delete_ciq() -> None:
    if MANUAL.exists():
        shutil.rmtree(MANUAL)


def g(d: Any, *path: Any) -> Any:
    for k in path:
        if isinstance(d, dict):
            d = d.get(k)
        elif isinstance(d, list) and isinstance(k, int) and len(d) > k:
            d = d[k]
        else:
            return None
    return d


def cut(s: Any, n: int = 260) -> Any:
    s = s if isinstance(s, str) else json.dumps(s, default=str)
    return s if len(s) <= n else s[:n] + f" …[{len(s)} chars]"


def sourced(x: Any) -> Any:
    if not isinstance(x, dict):
        return cut(x, 120)
    return {k: cut(x.get(k), 200) for k in ("status", "value", "note") if k in x}


def summarise(doc: dict[str, Any]) -> dict[str, Any]:
    a = doc.get("anchor") or {}
    vb = doc.get("valuation_basis") or {}
    fc = doc.get("forward_consensus") or {}
    m = doc.get("mechanical") or {}
    si = m.get("stock_info") or {}
    out = {
        "reference_date": doc.get("reference_date"),
        "sleeve": doc.get("sleeve"),
        "screen_status": cut(doc.get("screen_status"), 160),
        "anchor": {
            k: cut(a.get(k), 300)
            for k in (
                "recipe_hint",
                "applicable",
                "reason",
                "data_quality",
                "margin",
                "multiple",
                "anchor_base_value_per_share",
                "overall_confidence",
            )
            if k in a
        }
        if a
        else None,
        "anchor_facts": {
            k: sourced(a.get(k))
            for k in ("d_and_a", "net_debt", "diluted_shares", "ltm_revenue")
            if k in a
        }
        if a
        else None,
        "valuation_basis": {
            k: cut(vb.get(k), 300)
            for k in (
                "recipe",
                "priceable",
                "status_reason",
                "conflicts",
                "earnings_basis",
                "current_multiple",
            )
            if k in vb
        }
        if vb
        else None,
        "forward_consensus": (
            {
                "current_multiples": len(fc.get("current_multiples") or []),
                "pe_eps_basis": fc.get("pe_eps_basis"),
            }
            if fc
            else None
        ),
        "stock_info": {
            k: sourced(si.get(k)) for k in ("price", "market_cap", "shares_out") if k in si
        },
        "net_debt": sourced(g(m, "capital_structure", "net_debt")),
        "ev_bridge": cut(doc.get("ev_bridge"), 400),
        "financial_summary": "present" if m.get("financial_summary") else "absent",
        "qa_flags": len(doc.get("qa_flags") or []),
        "caveats": len(doc.get("caveats") or []),
        "qa_flags_list": [cut(f, 220) for f in (doc.get("qa_flags") or [])],
        "caveats_list": [cut(c, 220) for c in (doc.get("caveats") or [])],
    }
    # every Sourced leaf: present vs not, so a page's reach is a count, never an impression
    pres = tot = 0
    unknown: list[str] = []

    def walk(n: Any, path: str) -> None:
        nonlocal pres, tot
        if isinstance(n, dict):
            if "status" in n and "value" in n and isinstance(n.get("status"), str):
                tot += 1
                if n["status"] == "present":
                    pres += 1
                else:
                    unknown.append(path)
                return
            for k, v in n.items():
                walk(v, f"{path}.{k}")
        elif isinstance(n, list):
            for i, v in enumerate(n[:50]):
                walk(v, f"{path}[{i}]")

    walk(m, "mechanical")
    out["sourced_fields"] = {
        "present": pres,
        "total": tot,
        "not_present_first_40": unknown[:40],
        "not_present_count": len(unknown),
    }
    return out


def retag(built: Any, recipe: str) -> dict[str, Any]:
    from vinci.dossier.schemas import dossier_json

    if built.anchor is None:
        raise ValueError("no anchor block on the page to re-tag")
    b2 = built.model_copy(
        update={"anchor": built.anchor.model_copy(update={"recipe_hint": recipe})}
    )
    return json.loads(dossier_json(b2))


def template_run(doc: dict[str, Any]) -> dict[str, Any]:
    from vinci.dossier.propose import ProposalRefusedError, build_template

    try:
        tpl = build_template(doc)
    except ProposalRefusedError as exc:
        return {"result": "REFUSED", "why": cut(str(exc), 600)}
    except Exception as exc:  # noqa: BLE001 — a crash is a finding, reported with its type
        return {"result": "RAISED", "type": type(exc).__name__, "why": cut(str(exc), 600)}
    scen = tpl.get("scenarios") or {}
    cells = {
        leg: {k: v for k, v in c.items() if not k.startswith("_") and not k.endswith("_adjustment")}
        for leg, c in scen.items()
    }
    whys = {
        leg: {k: cut(v, 200) for k, v in c.items() if k.endswith("why_no_anchor")}
        for leg, c in scen.items()
    }
    return {
        "result": "TEMPLATE",
        "recipe_id": tpl.get("recipe_id"),
        "spot": tpl.get("spot"),
        "multiple_basis": tpl.get("multiple_basis"),
        "cells": cells,
        "why_empty": whys,
        "facts": {
            k: {kk: cut(vv, 120) for kk, vv in v.items()}
            for k, v in (tpl.get("facts") or {}).items()
        },
    }


def one(t: str) -> dict[str, Any]:
    from vinci.dossier import prespend, recipe_proposal
    from vinci.dossier.anchor import Anchor
    from vinci.dossier.schemas import dossier_json

    res: dict[str, Any] = {"ticker": t, "ciq_export": t in CIQ_SETS}
    buf = io.StringIO()
    lines: list[str] = []
    try:
        with redirect_stdout(buf):
            code = prespend.run(t, CFG, emit=lines.append, inputs_json=DEST / f"{t}.inputs.json")
        res["precheck_exit"] = code
    except Exception as exc:  # noqa: BLE001
        res["precheck_exit"] = f"RAISED {type(exc).__name__}: {cut(str(exc), 500)}"
        res["precheck_traceback"] = cut(traceback.format_exc(), 1500)
    res["precheck_lines"] = lines
    res["precheck_stdout"] = cut(buf.getvalue(), 2000)
    try:
        built = prespend.mechanical_build(t, CFG)
    except Exception as exc:  # noqa: BLE001
        res["build"] = f"RAISED {type(exc).__name__}: {cut(str(exc), 600)}"
        return res
    doc = json.loads(dossier_json(built))
    (DEST / f"{t}.dossier.json").write_text(json.dumps(doc, indent=1, default=str))
    res["page"] = summarise(doc)
    anc = Anchor.model_validate(doc["anchor"]) if doc.get("anchor") else None
    res["r4_conditions"] = [
        {"name": c.name, "met": c.met, "detail": cut(c.detail, 200)}
        for c in recipe_proposal.r4_conditions(doc, anc)
    ]
    res["template_as_tagged"] = template_run(doc)
    for rid in ("R3_forward_pe", "R4_forward_ev_ebit"):
        try:
            res[f"template_simulated_{rid[:2]}"] = template_run(retag(built, rid))
            vb = retag(built, rid).get("valuation_basis") or {}
            res[f"valuation_basis_simulated_{rid[:2]}"] = {
                k: cut(vb.get(k), 400)
                for k in ("recipe", "priceable", "status_reason", "conflicts")
                if k in vb
            }
        except Exception as exc:  # noqa: BLE001
            res[f"template_simulated_{rid[:2]}"] = {
                "result": "RAISED",
                "type": type(exc).__name__,
                "why": cut(str(exc), 400),
            }
    return res


def main(args: list[str]) -> None:
    """``T`` builds with T's CIQ pack when one is set; ``T:nociq`` builds the same name EDGAR-only
    (its CIQ folder absent), so a name whose export refuses still shows its EDGAR layers."""
    import vinci

    print("vinci:", vinci.__file__, "data_dir:", CFG.data_dir)
    DEST.mkdir(parents=True, exist_ok=True)
    try:
        for a in args:
            t, _, mode = a.partition(":")
            delete_ciq()
            if mode != "nociq":
                copy_ciq([t])
            how = "EDGAR-only" if mode == "nociq" or t not in CIQ_SETS else "with CIQ pack"
            print(f"--- {t} ({how})", flush=True)
            r = one(t)
            r["mode"] = "EDGAR-only" if (mode == "nociq" or t not in CIQ_SETS) else "with CIQ pack"
            stem = f"{t}-noCIQ" if mode == "nociq" else t
            (DEST / f"{stem}.json").write_text(json.dumps(r, indent=1, default=str))
            for f in ("dossier", "inputs"):
                src = DEST / f"{t}.{f}.json"
                if mode == "nociq" and src.exists():
                    src.rename(DEST / f"{stem}.{f}.json")
            print(
                f"    precheck exit {str(r.get('precheck_exit'))[:300]}; build "
                f"{'ok' if 'page' in r else str(r.get('build'))[:300]}",
                flush=True,
            )
    finally:
        delete_ciq()
        print("CIQ scratch copies deleted:", not MANUAL.exists())


if __name__ == "__main__":
    main(sys.argv[1:])
