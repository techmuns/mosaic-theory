"""The registrations index: every registration, and every paid draw under one, as a row of ONE
committed file, `docs/evals/registrations.jsonl` (fix request 2, RG-D14 and RG-D9; operator,
2026-11-11: "Committed index on main").

WHY A COMMITTED INDEX.
- **RG-D14.** "Pre-registered before scoring" could not be checked from main: a registration's
  commit lived on its branch, and the squash merge removed it. Now `register` and `register-run`
  write the registration's row here, the row lands on main in a docs-only PR, and `run-compare`,
  `run`, `score` and `score-run` refuse a registration whose row origin/main does not hold. Main's
  own history then shows the registration before any draw.
- **RG-D9.** "Drawn once" and the judge's "TEST read once" held per approval ledger only, and a
  ledger is one approval's file outside the repository, so a second approval could draw a
  registration again or read the TEST half again. Every draw, and the TEST read, is a row here
  (in the working copy at once, then committed with the run's record); a second one is refused
  whichever approval asks, whether the earlier row is in this checkout or on main.

WHAT A ROW HOLDS: shas, refs, pages, counts, an approval's sha256 and dates — a registration's
design key and its request pins are sha256s too. Never a path, a transcript or a ledger's
contents (the repository is public).

WHAT THE INDEX KNOWS OF A REGISTRATION IS DERIVED FROM IT (#1030 review round 2): `identity`
reads the sha, the design key and the request pins off the registration itself, when its row is
written and again when it is drawn, and a draw whose registration disagrees with its row is
refused. A caller never hands the index a key it then trusts.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from vinci.evals.replay import ROOT, ReplayError

if TYPE_CHECKING:
    from vinci.evals.builds import RunRegistration
    from vinci.evals.compare import Registration

#: The index, relative to the repository root.
INDEX = Path("docs/evals/registrations.jsonl")
#: The ref a registration must be on before it is drawn or scored.
MAIN_REF = "origin/main"


def _parse(text: str) -> list[dict[str, Any]]:
    return [json.loads(x) for x in text.splitlines() if x.strip()]


def working_rows(root: Path = ROOT) -> list[dict[str, Any]]:
    """The index in this checkout, committed or not."""
    path = root / INDEX
    return _parse(path.read_text(encoding="utf-8")) if path.exists() else []


def main_rows(root: Path = ROOT, ref: str = MAIN_REF) -> list[dict[str, Any]]:
    """The index as ``ref`` holds it; a ref that has no index yet holds no row."""
    done = subprocess.run(["git", "-C", str(root), "show", f"{ref}:{INDEX.as_posix()}"],
                          capture_output=True, text=True)
    if done.returncode == 0:
        return _parse(done.stdout)
    known = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", f"{ref}^{{commit}}"],
                           capture_output=True).returncode == 0
    if not known:
        raise ReplayError(f"{ref} is not known in this clone: fetch it, so the index main holds "
                          "can be read (nothing is drawn or scored on a guess)")
    return []


def _append(row: dict[str, Any], root: Path) -> dict[str, Any]:
    path = root / INDEX
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
    return row


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def approval_id(ledger: Path) -> str:
    """An approval's identity: the sha256 of its ledger's first line, where the approval's words,
    cap and opening time are recorded (`replay.Budget.open`)."""
    lines = ledger.read_text(encoding="utf-8").splitlines() if ledger.is_file() else []
    if not lines or not lines[0].strip():
        raise ReplayError(f"{ledger} holds no opened approval (missing or empty): open it with "
                          "`budget-open` first — an approval is its ledger's first line")
    return hashlib.sha256(lines[0].encode()).hexdigest()


def identity(reg: Registration | RunRegistration) -> dict[str, Any]:
    """What the index records of a registration, DERIVED FROM IT (#1030 review round 2, F1): its
    sha, kind, refs, pages and draws; its ``design``, the drawn-once key (`compare.draw_key`,
    `builds.draw_key`); and its request ``pins``, each request's sha256 under the name the
    registration gives it. `record_registered` writes this, and `claim_draw` derives it again from
    the registration about to be drawn. Before round 2 the CLI passed the key in, and a mutant
    that passed the registration's sha as its design survived every test."""
    from vinci.evals import builds as bd
    if isinstance(reg, bd.RunRegistration):
        return {"registration": reg.sha, "kind": "run", "refs": {"code": reg.code_ref},
                "pages": list(reg.pages), "draws": reg.draws, "design": bd.draw_key(reg),
                "pins": dict(reg.requests)}
    from vinci.evals import compare as cm
    return {"registration": reg.sha, "kind": "compare",
            "refs": {"base": reg.base_ref, "cand": reg.cand_ref}, "pages": list(reg.pages),
            "draws": reg.draws, "design": cm.draw_key(reg), "pins": dict(reg.requests)}


def record_registered(reg: Registration | RunRegistration, *, approval: str,
                      root: Path = ROOT) -> dict[str, Any]:
    """The registration's row, appended to this checkout's index: what `identity` derives from
    it, and the approval that may draw it. It is drawn only once the row is on main
    (`require_on_main`); one design, and one set of request bytes, is drawn once across
    approvals, whatever its words (`claim_draw`)."""
    row = identity(reg)
    sha = row["registration"]
    if any(r.get("event") == "registered" and r.get("registration") == sha
           for r in working_rows(root)):
        raise ReplayError(f"registration {sha[:12]} is already in the index")
    # BOUND TO ITS APPROVAL (B's check of order 8, gap 6): the row is on main before any draw,
    # so every checkout reads which approval may draw it — a second approval elsewhere cannot
    return _append({"event": "registered", **row, "approval": approval,
                    "registered_at": _now()}, root)


def require_on_main(sha: str, *, root: Path = ROOT, ref: str = MAIN_REF) -> None:
    """Refuse unless origin/main's index holds the registration's row (RG-D14)."""
    if not any(r.get("event") == "registered" and r.get("registration") == sha
               for r in main_rows(root, ref)):
        raise ReplayError(f"registration {sha[:12]} is not on {ref}: its row in {INDEX} must be "
                          "merged to main (a docs-only PR) before anything is drawn or scored "
                          "under it — so main's own history shows it registered first (RG-D14); "
                          "after the merge, fetch")


def _rows_everywhere(root: Path) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for r in working_rows(root) + main_rows(root):
        key = json.dumps(r, sort_keys=True)
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def _drawn_pins(rows: list[dict[str, Any]], exempt: set[str | None]) -> dict[str, str]:
    """Each request pin drawn under a registration outside ``exempt``, mapped to one that drew
    it: every pin of a drawn comparison (drawn whole), and a build registration's pins of the
    pages it has drawn a build of. A drawn registration whose row records no pins is refused:
    which bytes it drew cannot be read, so no draw can be checked against them."""
    out: dict[str, str] = {}
    for row in rows:
        sha = row.get("registration")
        if row.get("event") != "registered" or sha in exempt:
            continue
        units = [r.get("unit") for r in rows
                 if r.get("event") == "drawn" and r.get("registration") == sha]
        if not units:
            continue
        pins = row.get("pins")
        if not isinstance(pins, dict) or not pins:
            raise ReplayError(f"registration {str(sha)[:12]} was drawn, but its indexed row "
                              "records no request pins: the bytes it drew cannot be read, so no "
                              "draw is checked against them, and none is made")
        if row.get("kind") == "run":
            pages = {str(u).split(":")[0] for u in units if u}
            drew = [str(pins[p]) for p in sorted(pages) if p in pins]
        else:
            drew = [str(p) for p in pins.values()]
        for p in drew:
            out.setdefault(p, str(sha))
    return out


def claim_draw(reg: Registration | RunRegistration, *, approval: str, unit: str | None = None,
               root: Path = ROOT) -> dict[str, Any]:
    """Record a paid draw under ``reg`` BEFORE it is made, refusing a second one (RG-D9).
    ``unit`` is a `register-run` build ("TICKER:k"): each build once, and every build of a
    registration under the approval that drew its first. A `register` comparison is one unit.
    What it is checked by — its sha, its design, its request pins — is derived from ``reg`` here
    (`identity`) and must be what its indexed row records (#1030 review round 2, F1)."""
    me = identity(reg)
    sha = me["registration"]
    rows = _rows_everywhere(root)
    mine = [r for r in rows if r.get("event") == "registered" and r.get("registration") == sha]
    if any(r.get("design") is None for r in mine):
        raise ReplayError(f"registration {sha[:12]}'s indexed row records no design: it cannot "
                          "be checked against the designs drawn under other registrations, so "
                          "it is not drawn")
    # THE ROW IS THE REGISTRATION DRAWN (#1030 review round 2, F1): the claim read the row's key
    # as written, so a key written wrong made a twin a design of its own
    if off := [r for r in mine if (r.get("design"), r.get("pins")) != (me["design"], me["pins"])]:
        raise ReplayError(f"registration {sha[:12]}'s indexed row records design "
                          f"{str(off[0].get('design'))[:12]} and its request pins, but the "
                          f"registration drawn derives design {me['design'][:12]} and its own: "
                          "the index and the registration disagree, so nothing is drawn — "
                          "register it again")
    drawn = [r for r in rows if r.get("event") == "drawn" and r.get("registration") == sha]
    if unit is None and drawn:
        raise ReplayError(f"registration {sha[:12]} was already drawn (at "
                          f"{drawn[0].get('drawn_at')}): a registration is drawn once across "
                          "approvals — a new run needs a new registration (RG-D9)")
    if unit is not None:
        if any(r.get("unit") == unit for r in drawn):
            raise ReplayError(f"build {unit} of registration {sha[:12]} was already drawn: a "
                              "build is drawn once across approvals (RG-D9)")
        others = {r.get("approval") for r in drawn} - {approval}
        if others:
            raise ReplayError(f"registration {sha[:12]}'s builds were drawn under another "
                              "approval: a registration's builds are drawn under one approval, "
                              "the one whose ledger scores them (RG-D9)")
    # ONE DESIGN IS DRAWN ONCE ACROSS APPROVALS (#1030 review round 1, item 1): a new `--note`
    # gives one design a new sha, so keying on the sha let a second approval draw it again
    twins = {r.get("registration") for r in rows if r.get("event") == "registered"
             and r.get("design") == me["design"] and r.get("registration") != sha}
    if prior := [r for r in rows if r.get("event") == "drawn" and r.get("registration") in twins]:
        raise ReplayError(f"registration {sha[:12]}'s design was already drawn, as registration "
                          f"{str(prior[0].get('registration'))[:12]} (at "
                          f"{prior[0].get('drawn_at')}): a design is drawn once across approvals, "
                          "whatever its words — a replication names the run it replicates "
                          "(RG-D9)")
    # ONE SET OF REQUEST BYTES IS DRAWN ONCE ACROSS APPROVALS (#1030 review round 2, F3; operator
    # 2026-11-12: "Refuse by request pins"): the design key carries the scorer's fingerprint and a
    # build's code ref, so a harness commit gave byte-identical requests a new design. The run a
    # replication replicates drew its bytes too, and is the one exemption.
    pins = set(me["pins"].values())
    if not pins:
        raise ReplayError(f"registration {sha[:12]} pins no request bytes: what it would draw "
                          "cannot be checked against what was drawn, so nothing is drawn")
    elsewhere = _drawn_pins(rows, {sha, getattr(reg, "replicates", None)})
    if pins <= set(elsewhere):
        by = sorted({elsewhere[p][:12] for p in pins})
        raise ReplayError(f"every request registration {sha[:12]} pins was already drawn, under "
                          f"registration(s) {by}: one set of request bytes is drawn once across "
                          "approvals, whatever registration, design field or harness commit names "
                          "it — a replication names the run it replicates (RG-D9; operator "
                          "2026-11-12, \"Refuse by request pins\")")
    bound = {r.get("approval") for r in mine}
    if bound != {approval}:
        raise ReplayError(f"registration {sha[:12]} is bound to approval "
                          f"{sorted(map(str, bound)) or 'none'}, not {approval[:12]}: it is drawn "
                          "only under the approval its registered row names (gap 6)")
    return _append({"event": "drawn", "registration": sha, "approval": approval, "unit": unit,
                    "drawn_at": _now()}, root)


def claim_judge_test(*, approval: str, root: Path = ROOT) -> dict[str, Any]:
    """Record the judge's read of the gold's TEST half BEFORE it is made; a read by another
    approval is refused (RG-D9). The approval that holds the read may resume it: `judge.run_half`
    resumes a stopped TEST run into its own folder, and refuses any other folder, per approval."""
    read = [r for r in _rows_everywhere(root) if r.get("event") == "judge_test_read"]
    if read and all(r.get("approval") == approval for r in read):
        return read[0]
    if read:
        raise ReplayError(f"the judge's TEST half was already read (at {read[0].get('read_at')}): "
                          "it is read once across approvals (RG-D9)")
    return _append({"event": "judge_test_read", "approval": approval, "read_at": _now()}, root)
