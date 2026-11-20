"""Shared setup for the archetype probe (`scripts/archetype_probe/`; how to run: README.md
beside it).

EVERY MACHINE PATH IS AN INPUT, never a literal in the code:

- ``ARCHETYPE_PROBE_WORK`` (required): a folder OUTSIDE any checkout. The probe's data dir is
  ``<WORK>/data`` (its SEC, Polygon and FINRA caches, its scratch price store, follow list and
  coverage roster) and every output lands in ``<WORK>/out``. Nothing is written into a checkout.
- ``ARCHETYPE_PROBE_CIQ``: the CIQ export root in the loader's own layout,
``<root>/<TICKER>/<files>``.
  Read only: a script copies a pack into ``<WORK>/data/manual/ciq/<TICKER>/``, checks each copy's
  sha256 against its original, and deletes the copies when it ends.
- ``ARCHETYPE_PROBE_CIQ_PACKS`` (optional): the dated-pack layout ``<root>/<TICKER>_<id>/<date>/``
  that the 2026-10-28 packs used (``build5a``, ``ciq5a``, ``ciq_probe``).
- ``ARCHETYPE_PROBE_SEC_CACHE`` (optional): a READ-ONLY SEC cache folder another checkout already
  holds (``fpi_facts``, ``cachecov``). Absent, those reads go through the repo's client into
  ``<WORK>/data/cache``.
- ``ARCHETYPE_PROBE_DOTENV`` (optional): a ``.env`` file to load; default ``<checkout>/.env``. Only
the
  ``vinci refresh`` step reads a key (Polygon), and no script prints one.

THE CHECKOUT is the one this file sits in. Its root goes first on ``sys.path``, so ``vinci`` is
imported from it and from nowhere else, and that is asserted. Every script prints ``vinci.__file__``
first. ($0: no script constructs a model client.)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import vinci  # noqa: E402

if not Path(vinci.__file__).resolve().is_relative_to(REPO):
    raise SystemExit(f"vinci was imported from {vinci.__file__}, not from this checkout ({REPO})")
print("vinci:", vinci.__file__, flush=True)  # first, from every script that imports this

from vinci.config import Config, load_local_env  # noqa: E402


def _env_dir(name: str, *, required: bool) -> Path | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        if required:
            raise SystemExit(f"set {name} (see scripts/archetype_probe/README.md)")
        return None
    path = Path(raw).expanduser().resolve()
    if path.is_relative_to(REPO):
        raise SystemExit(f"{name} must be OUTSIDE the checkout ({REPO}); got {path}")
    return path


WORK = _env_dir("ARCHETYPE_PROBE_WORK", required=True)
assert WORK is not None
OUT = WORK / "out"  # every output
DATA = WORK / "data"  # Config.data_dir for the probe: caches land in DATA/cache/
SNAP = REPO / "data" / "snapshots"  # committed snapshots, READ only
OUT.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)
#: The names the scripts were written against: the checkout and the scratch folder.
WT = REPO
SCRATCH = WORK

load_local_env(Path(os.environ.get("ARCHETYPE_PROBE_DOTENV") or REPO / ".env"))
CFG = Config(data_dir=DATA)


#: THE ARCHETYPE RULE, ONCE (grid.py, pages5b.py, aqnclass5b.py and g17pick5b.py read it).
#: Precedence, first match wins: no annual report → FPI IFRS → FPI US GAAP non-USD → FPI US GAAP
#: USD (then by form) → statement form → economic model.
def grid_arch(x: dict[str, Any]) -> str:
    r, f, m = x["regime"], x["form"], x["model"]
    if r.startswith("no annual") or r.startswith("UNREAD"):
        return "G20 no annual report on file (new registrant / successor)"
    if r.startswith("FPI"):
        if "IFRS" in r:
            return "G19 FPI · IFRS (any form)"
        if "US GAAP, USD" not in r:
            return "G18 FPI · US GAAP non-USD (or unread)"
        return (
            "G17 FPI · US GAAP USD · operating"
            if f == "operating company"
            else "G17b FPI · US GAAP USD · financial/other form"
        )
    forms = {
        "bank": "G06 bank",
        "lender / specialty finance": "G07 lender / specialty finance",
        "insurer (underwriting)": "G08 insurer",
        "managed care (SIC 6324)": "G09 managed care",
        "broker-dealer / investment bank": "G10 broker-dealer / IB",
        "asset manager / exchange": "G11 asset manager / exchange",
        "insurance broker": "G12 insurance broker",
        "REIT": "G13 REIT (SIC 6798)",
        "real-estate operator / developer": (
            "G13b real-estate operator (65xx; INVH-type REITs inside)"
        ),
        "regulated utility": "G14 regulated utility",
        "partnership / MLP": "G15 partnership / MLP",
        "royalty / patent owner": "G16 royalty / patent owner",
        "holding / investment office": "G16b holding / investment office",
    }
    if f in forms:
        return forms[f]
    return {
        "operating, positive operating income in a recent year": (
            "G01 PROVEN PATH · 10-K operating, positive OI"
        ),
        "profitable-or-unknown, OperatingIncomeLoss untagged": "G02 10-K operating · OI untagged",
        "pre-profit (operating loss CY2024 and CY2025)": "G03 10-K operating · pre-profit",
        "pre-revenue (< $10M revenue CY2024 and CY2025)": "G04 10-K operating · pre-revenue",
        "reserve-based (mining / E&P)": "G05 10-K operating · reserve-based",
        "no CY2024/25 us-gaap USD frame data": (
            "G05b 10-K operating · no USD frame data (non-USD 10-K / short history)"
        ),
    }.get(m or "", f"G?? {f} / {m}")


def grid_code(x: dict[str, Any]) -> str:
    """The archetype's code alone (``G13b``), from :func:`grid_arch`'s label."""
    return grid_arch(x).split()[0]


def ciq_root() -> Path:
    """The CIQ export root (``<root>/<TICKER>/<files>``), for the scripts that read a pack."""
    path = _env_dir("ARCHETYPE_PROBE_CIQ", required=True)
    assert path is not None
    return path


def ciq_packs() -> Path | None:
    """The dated-pack root (``<root>/<TICKER>_<id>/<date>/``), or None when it is not set."""
    return _env_dir("ARCHETYPE_PROBE_CIQ_PACKS", required=False)


def sec_cache_readonly() -> Path | None:
    """A read-only SEC cache another checkout holds, or None."""
    return _env_dir("ARCHETYPE_PROBE_SEC_CACHE", required=False)


def head_sha() -> str:
    """The checkout's HEAD, short, for the boundary every output states."""
    return subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def edgar() -> Any:
    from vinci.edgar.client import EdgarClient

    return EdgarClient.from_config(CFG)


def sec_http() -> Any:
    from vinci.sec import build_sec_http

    return build_sec_http(CFG)


def universe_rows() -> list[dict[str, Any]]:
    """Both committed universes joined to securities + issuers. One row per (band, security)."""
    sec = {}
    for line in (SNAP / "securities.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            sec[r["internal_id"]] = r
    iss = {}
    for line in (SNAP / "issuers.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            iss[r["issuer_id"]] = r
    rows = []
    for band, f in (
        ("primary", "universe_snapshot.jsonl"),
        ("theme", "theme_universe_snapshot.jsonl"),
    ):
        for line in (SNAP / f).read_text().splitlines():
            if not line.strip():
                continue
            u = json.loads(line)
            s = sec.get(u["internal_id"], {})
            i = iss.get(s.get("issuer_id", ""), {})
            rows.append(
                {
                    "band": band,
                    "as_of": u["as_of"],
                    "internal_id": u["internal_id"],
                    "cik": u["internal_id"].split("-")[1],
                    "ticker": s.get("ticker"),
                    "name": s.get("name"),
                    "exchange": s.get("exchange"),
                    "share_class": s.get("share_class"),
                    "sic": s.get("sic") or i.get("sic"),
                    "country": i.get("country"),
                    "market_cap": u.get("market_cap"),
                    "cap_source": u.get("source"),
                }
            )
    return rows
