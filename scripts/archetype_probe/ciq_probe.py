"""The CIQ layer of the probe: the repo's own CIQ readers on the exports that exist on Drive, read
from a SCRATCH COPY (Drive is never written; the copies are deleted at the end). Licensed workbooks:
nothing from them is printed beyond the reader's own Sourced value/status/note, truncated."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from probe_common import OUT, SCRATCH, ciq_packs, ciq_root

_LIVE = ciq_root()  # ARCHETYPE_PROBE_CIQ: the loader layout, <root>/<TICKER>/
_PACKS = ciq_packs()  # ARCHETYPE_PROBE_CIQ_PACKS: the dated packs, <root>/<TICKER>_<id>/<date>/
SETS = {
    "LLY": _LIVE / "LLY",
    "BRBR": _LIVE / "BRBR",
    **(
        {
            "MTB": _PACKS / "MTB_IQ272285/2026-10-28",
            "PLD": _PACKS / "PLD_IQ330123/2026-10-28",
            "NVO": _PACKS / "NVO_IQ323452/2026-10-28",
            "PCVX": _PACKS / "PCVX_IQ307500026/2026-10-28",
            "RIVN": _PACKS / "RIVN_IQ144746614/2026-10-28",
        }
        if _PACKS is not None
        else {}
    ),
}
TMP = SCRATCH / "ciq_copy"


def cut(s: Any, n: int = 300) -> Any:
    return s[:n] + f" …[truncated, {len(s)} chars]" if isinstance(s, str) and len(s) > n else s


def src(x: Any) -> Any:
    """A Sourced/whatever as a small dict, never the whole object."""
    if x is None:
        return None
    d = {}
    for k in ("status", "note", "source_ref", "as_of"):
        if hasattr(x, k):
            d[k] = cut(str(getattr(x, k)), 240)
    v = getattr(x, "value", x)
    if isinstance(v, list):
        d["value"] = f"list[{len(v)}]"
        if v:
            d["first"] = cut(repr(v[0]), 300)
    elif isinstance(v, (int, float, str)) or v is None:
        d["value"] = cut(v, 200)
    else:
        d["value"] = cut(repr(v), 300)
    return d


def run(t: str, folder: Path) -> dict:
    from vinci.dossier import ciq_sheets as cs
    from vinci.dossier.ciq import CiqBundle

    dest = TMP / t
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for p in folder.iterdir():
        if p.is_file() and not p.name.startswith("."):
            shutil.copy2(p, dest / p.name)  # read from Drive, written only to the scratch copy
    out: dict[str, Any] = {
        "ticker": t,
        "source_folder": str(folder).split("manual/")[-1],
        "files": sorted(p.name.split(" ")[-1] for p in dest.iterdir()),
    }

    def call(name: str, fn, *a, **k):
        try:
            out[name] = src(fn(*a, **k))
        except Exception as exc:  # noqa: BLE001
            out[name] = {"raised": type(exc).__name__, "message": cut(str(exc), 400)}

    try:
        b = CiqBundle.from_files(t, sorted(dest.iterdir()))
    except Exception as exc:  # noqa: BLE001
        out["bundle"] = {"raised": type(exc).__name__, "message": cut(str(exc), 400)}
        return out
    out["bundle"] = {
        "workbooks": [w.kind + (f"/{w.freq}" if w.freq else "") for w in b.workbooks],
        "unrecognised": list(b.unrecognised),
    }
    # the three refusals mechanical runs before anything else
    try:
        cur = cs.stated_currency(b)
        out["stated_currency"] = cut(repr(cur), 300)
        cs.require_usd(cur, t)
        out["require_usd"] = "pass"
    except Exception as exc:  # noqa: BLE001
        out["require_usd"] = {"raised": type(exc).__name__, "message": cut(str(exc), 400)}
    for name in ("require_filed_income_statement", "require_millions"):
        try:
            getattr(cs, name)(b, t)
            out[name] = "pass"
        except Exception as exc:  # noqa: BLE001
            out[name] = {"raised": type(exc).__name__, "message": cut(str(exc), 400)}
    call("own_history_bands", cs.own_history_bands, b)
    call("ev_ebitda_current", cs.ev_ebitda_current, b)
    call("pe_ltm_current", cs.pe_ltm_current, b)
    call("net_debt", cs.net_debt, b)
    call("ltm_ebitda", cs.ltm_ebitda, b)
    call("free_cash_flow", cs.free_cash_flow, b)
    call("financial_summary_annual", cs.financial_summary_annual, b)
    try:
        fc = cs.forward_consensus(b)
        out["forward_consensus"] = (
            None
            if fc is None
            else {
                "current_multiples": [
                    (m.metric, m.period, m.value) for m in (fc.current_multiples or [])
                ][:12],
                "pe_eps_basis": cut(repr(getattr(fc, "pe_eps_basis", None)), 200),
            }
        )
    except Exception as exc:  # noqa: BLE001
        out["forward_consensus"] = {"raised": type(exc).__name__, "message": cut(str(exc), 400)}
    return out


def main() -> None:
    res = []
    try:
        for t, f in SETS.items():
            res.append(run(t, f))
            print(t, "done", flush=True)
    finally:
        shutil.rmtree(TMP, ignore_errors=True)  # licensed copies never outlive the probe
    (OUT / "ciq_probe.json").write_text(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
