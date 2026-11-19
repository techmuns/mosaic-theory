"""5a item 2, where the page itself was refused: the consensus block each CIQ pack yields through
the
page's own reader (`ciq_sheets.forward_consensus`), and the two R4 conditions it decides alone
(1: NTM TEV/EBIT > 0; 3's half: the FY P/E's EPS basis), plus whether R1's own-history band exists
(`ciq_sheets.own_history_bands`). INPUTS ONLY — never a proposal: a proposal runs on a page, and
these pages were refused. Scratch copies of the workbooks, deleted at the end."""

from __future__ import annotations

import json
from typing import Any

from build5a import CIQ_SETS, MANUAL, copy_ciq, cut, delete_ciq
from probe_common import OUT


def one(t: str) -> dict[str, Any]:
    from vinci.dossier import ciq_sheets as cs
    from vinci.dossier.ciq import CiqBundle

    files = sorted(p for p in (MANUAL / t).iterdir() if p.is_file())
    b = CiqBundle.from_files(t, files)
    out: dict[str, Any] = {"ticker": t}
    try:
        fc = cs.forward_consensus(b)
        mults = (
            fc.get("current_multiples")
            if isinstance(fc, dict)
            else getattr(fc, "current_multiples", None)
        ) or []
        rows = [m if isinstance(m, dict) else m.model_dump() for m in mults]
        pick = {
            f"{r.get('metric')} {r.get('period')}": r.get("value")
            for r in rows
            if r.get("period") in ("NTM", "FY1", "FY2026", "FY2027")
            or str(r.get("period", "")).startswith("FY")
        }
        basis = (
            fc.get("pe_eps_basis") if isinstance(fc, dict) else getattr(fc, "pe_eps_basis", None)
        )
        basis = basis if isinstance(basis, dict) or basis is None else basis.model_dump()
        ntm_ebit = next(
            (
                r.get("value")
                for r in rows
                if r.get("metric") == "TEV/EBIT" and r.get("period") == "NTM"
            ),
            None,
        )
        ntm_pe = next(
            (r.get("value") for r in rows if r.get("metric") == "P/E" and r.get("period") == "NTM"),
            None,
        )
        out.update(
            {
                "current_multiples": len(rows),
                "ntm_tev_ebit": ntm_ebit,
                "ntm_pe": ntm_pe,
                "pe_eps_basis_fy": (basis or {}).get("fiscal_years"),
                "pe_eps_basis_ntm": (basis or {}).get("ntm"),
                "multiples_seen": cut(json.dumps(dict(list(pick.items())[:14]), default=str), 700),
                "as_of": cut(
                    str(fc.get("as_of") if isinstance(fc, dict) else getattr(fc, "as_of", None)), 60
                ),
            }
        )
    except Exception as exc:  # noqa: BLE001
        out["forward_consensus"] = f"RAISED {type(exc).__name__}: {cut(str(exc), 300)}"
    try:
        bands = cs.own_history_bands(b)
        out["own_history_bands"] = cut(repr(bands), 400)
    except Exception as exc:  # noqa: BLE001
        out["own_history_bands"] = f"RAISED {type(exc).__name__}: {cut(str(exc), 300)}"
    return out


def main() -> None:
    import vinci

    print("vinci:", vinci.__file__)
    res = []
    try:
        for t in CIQ_SETS:
            delete_ciq()
            copy_ciq([t])
            r = one(t)
            res.append(r)
            print(json.dumps(r, default=str)[:1600])
    finally:
        delete_ciq()
        print("CIQ scratch copies deleted:", not MANUAL.exists())
    (OUT / "ciq5a.json").write_text(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
