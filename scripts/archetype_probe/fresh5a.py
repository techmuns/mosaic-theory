"""5a, last part: the six FRESH CIQ packs the operator exported 2026-11-19 (Drive `manual/ciq/<T>/`,
landed ~16:49Z) in place of no export (AWK, MORN, DVN, AQN) or the stale 2026-10-28 pack (PLD,
RIVN).

Per name: (1) copy every file from Drive into the scratch manual folder, READ-ONLY on Drive, and
hash-check each copy against its Drive original (sha256, both sides); (2) the loader's view of the
folder — each file's workbook kind / format / period, and the files it recognises as no kind;
(3) the currency every money panel STATES (`ciq_sheets.stated_currency`, the assembler's own read)
and whether `require_usd` refuses it; (4) `build5a.one` — `prespend.run` (the `vinci dossier
precheck` command itself), the page `mechanical_build` writes, the R4 conditions, the R3/R4
templates as tagged and re-tagged. Copies deleted after every name and again at the end."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import build5a
from probe_common import CFG, OUT, ciq_root

FRESH = ciq_root()  # ARCHETYPE_PROBE_CIQ: <root>/<TICKER>/<files>, read only
NAMES = ["PLD", "AWK", "RIVN", "MORN", "DVN", "AQN"]
DEST = OUT / "build5a_fresh"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_hashed(t: str) -> list[dict[str, Any]]:
    src, dest = FRESH / t, build5a.MANUAL / t
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    rows = []
    for p in sorted(src.iterdir()):
        if not p.is_file() or p.name.startswith("."):
            continue
        shutil.copy2(p, dest / p.name)  # Drive read, scratch written
        a, b = sha(p), sha(dest / p.name)
        if a != b:
            raise SystemExit(f"HASH MISMATCH {t}/{p.name}: drive {a[:12]} copy {b[:12]}")
        rows.append(
            {
                "file": p.name,
                "bytes": p.stat().st_size,
                "sha256": a,
                "mtime_utc": dt.datetime.fromtimestamp(p.stat().st_mtime, dt.UTC).isoformat()[:19],
            }
        )
    return rows


def loader_view(t: str) -> dict[str, Any]:
    from vinci.dossier import ciq_sheets as cs
    from vinci.dossier.ciq import CiqBundle

    files = sorted(p for p in (build5a.MANUAL / t).iterdir() if p.is_file())
    out: dict[str, Any] = {}
    try:
        b = CiqBundle.from_files(t, files)
    except Exception as exc:  # noqa: BLE001 — a loader refusal is the finding
        out["bundle"] = f"RAISED {type(exc).__name__}: {build5a.cut(str(exc), 900)}"
        return out
    out["workbooks"] = [
        {"file": w.path.name, "kind": w.kind, "fmt": str(w.fmt), "freq": w.freq}
        for w in b.workbooks
    ]
    out["unrecognised"] = list(b.unrecognised)
    try:
        cur = cs.stated_currency(b)
        out["currency_panels"] = (
            [{"panel": p.panel, "stated": p.stated, "check": str(p.check)} for p in cur.panels]
            if cur
            else None
        )
        out["currency_page_check"] = str(cur.check) if cur else None
        try:
            cs.require_usd(cur, t)
            out["require_usd"] = "PASS"
        except cs.CiqCurrencyError as exc:
            out["require_usd"] = f"REFUSED: {build5a.cut(str(exc), 900)}"
    except Exception as exc:  # noqa: BLE001
        out["currency_panels"] = f"RAISED {type(exc).__name__}: {build5a.cut(str(exc), 600)}"
    try:
        cs.require_millions(b, t)
        out["require_millions"] = "PASS"
    except Exception as exc:  # noqa: BLE001
        out["require_millions"] = f"REFUSED {type(exc).__name__}: {build5a.cut(str(exc), 600)}"
    return out


def main(args: list[str]) -> None:
    import vinci

    print("vinci:", vinci.__file__, "data_dir:", CFG.data_dir, flush=True)
    DEST.mkdir(parents=True, exist_ok=True)
    build5a.DEST = DEST  # build5a.one writes its inputs/page JSON here
    build5a.CIQ_SETS = {t: FRESH / t for t in NAMES}
    names = args or NAMES
    try:
        for t in names:
            build5a.delete_ciq()
            res: dict[str, Any] = {"ticker": t}
            res["files"] = copy_hashed(t)
            print(f"--- {t}: {len(res['files'])} files copied, all hash-equal to Drive", flush=True)
            for f in res["files"]:
                print(f"    {f['sha256'][:12]}  {f['bytes']:>9}  {f['file']}")
            res["loader"] = loader_view(t)
            print(f"    loader: {json.dumps(res['loader'], default=str)[:1500]}", flush=True)
            res.update(build5a.one(t))
            (DEST / f"{t}.json").write_text(json.dumps(res, indent=1, default=str))
            print(
                f"    precheck exit {str(res.get('precheck_exit'))[:300]}; build "
                f"{'ok' if 'page' in res else str(res.get('build'))[:400]}",
                flush=True,
            )
            for line in res.get("precheck_lines") or []:
                print(f"      | {line[:400]}")
    finally:
        build5a.delete_ciq()
        print("CIQ scratch copies deleted:", not build5a.MANUAL.exists())


if __name__ == "__main__":
    main(sys.argv[1:])
