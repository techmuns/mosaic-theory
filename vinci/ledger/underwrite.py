"""Read the LIVE underwrite record a verdict is logged against (2026-11-13, #1004 item 5).

`log-verdict` seals, beside the verdict, WHICH record priced it: the path, the commit it was read
at and the sha256 of its bytes, plus the record's ratio re-run at the frozen entry price
(`workflow.UnderwriteLink`). Before this nothing wrote `underwrite_ref` or `ratio_at_entry`; the
three committed rows carrying them were hand-authored, and IT's 6.69 was struck on a record that
has since been superseded — the ledger could not say which record a call stood on.

THE BYTES MUST BE THE COMMIT'S. A seal naming a commit whose blob differs from the bytes hashed
points a reader at a record the decision never saw, so an uncommitted or edited record is refused:
commit it, then log. A record that is ABSENT is a different fact — `log_verdict` then requires a
stated reason — and is returned as None.

A RECORD WITHOUT A HORIZON LOADS. It is read, hashed and its recipe re-run exactly as any other;
the refusal for a missing horizon sits in `log_verdict`, at the decision (#762: refusing at load
made `run_recipe` refuse every R1 record once).
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from vinci.ledger.workflow import LedgerError, UnderwriteLink


def _git(root: Path, *args: str) -> bytes:
    done = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)
    if done.returncode != 0:
        raise LedgerError(f"git {' '.join(args)} failed in {root}: "
                          f"{done.stderr.decode(errors='replace').strip()}")
    return done.stdout


def read_underwrite(ticker: str, *, root: Path) -> UnderwriteLink | None:
    """The live ``scenarios/<TICKER>.json`` under ``root`` as an `UnderwriteLink`, or None when
    there is no such record. Refused (`LedgerError`): bytes that differ from HEAD's blob, and a
    record its own recipe cannot re-run."""
    import vinci.scenarios as sc

    rel = f"scenarios/{ticker.upper()}.json"
    path = root / rel
    if not path.exists():
        return None
    raw = path.read_bytes()
    commit = _git(root, "rev-parse", "HEAD").decode().strip()
    shown = subprocess.run(["git", "-C", str(root), "show", f"{commit}:{rel}"],
                           capture_output=True, check=False)
    if shown.returncode != 0 or shown.stdout != raw:
        state = "is not in" if shown.returncode != 0 else "differs from its blob at"
        raise LedgerError(
            f"REFUSED: {rel} {state} the commit it would be sealed at ({commit[:12]}) — the seal "
            f"names a commit and a hash, and they must describe the same bytes. Commit the record, "
            f"then log the verdict.")
    # AN UNREADABLE RECORD REFUSES — never reads as "no record" (the review finding that retired
    # `cli._committed_limit`'s bare except: a guard that turns itself off on a corrupt file)
    try:
        rec = sc.ScenarioRecord.model_validate_json(raw)
    except ValueError as exc:
        raise LedgerError(f"REFUSED: {rel} exists but cannot be read as an underwrite record "
                          f"({exc}) — nothing was logged") from exc
    base = rec.scenarios.get("base")

    def ratio_at(price: float) -> tuple[float | None, str | None]:
        try:
            res = sc.run_recipe(rec.model_copy(update={"spot": price})).result
        except ValueError as exc:
            raise LedgerError(f"{rel}: its recipe cannot be re-run at the entry {price:g} "
                              f"({exc}) — nothing was logged") from exc
        if res is None:
            raise LedgerError(f"{rel}: its recipe returned no result at {price:g}")
        return res.ratio, (res.ratio_undefined or None)

    ratio_at(rec.spot)        # a record its own recipe refuses is refused before any decision
    return UnderwriteLink(ref=rel, commit=commit, sha256=hashlib.sha256(raw).hexdigest(),
                          horizon_years=base.years_to_terminal if base is not None else None,
                          limit=rec.limit, ratio_at=ratio_at)
