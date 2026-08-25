"""Landing a labelling session back into the corpus — the other half of "Export JSONL".

WHY THIS IS A CLI STEP AND NOT A BUTTON. The dashboard is a read-only static mirror; it has no
write path and must not acquire one (``frontend/lib/snapshots.js``: "there is NO write path"). So
the browser holds a session's edits in ``localStorage`` and exports them; landing them in the repo
is a deliberate, reviewable act taken here, where the change shows up in ``git diff`` like any
other. The friction is the safeguard: hand labels are the ground truth this whole tool exists to
grow, and a silent background write is exactly how ground truth gets corrupted without a trace.

WHAT IT TOUCHES:
  * ``labels.json``     — the merged row becomes ``src: "hand"``; the machine's guess is REPLACED.
  * ``gold_labels.jsonl`` — the hand set, keyed by ``<tweet_id>|<TICKER>``, de-duplicated.
  * ``meta.json``       — the hand / machine counts, so the index cannot drift from the corpus.
  * ``days.json``       — each day's hand-label tally, which is what the calendar's dot reads.

It does NOT re-score. Scoring is a separate, explicit step (``vinci calls score``) because it reads
prices and takes real time; the summary printed here says so rather than leaving the operator to
wonder whether results.jsonl already moved.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vinci.calls.accounts import account_dir

#: The gold-label field -> labels.json field mapping. Anything not here is carried by the post
#: itself (text, date, has_video) and is not stored on the label.
_FIELD_MAP = {
    "bias": "bias", "action": "action", "target": "target", "target_type": "target_type",
    "horizon_lo_days": "hlo", "horizon_hi_days": "hhi", "specificity": "spec",
    "is_conditional": "is_conditional", "is_retrospective": "is_retrospective",
}


class IngestError(RuntimeError):
    """A malformed export — raised rather than partially merging."""


def _refresh_day_labels(d: Path, labels: dict[str, Any]) -> int:
    """Recount ``days.json``'s per-day HAND-label tally from ``labels.json``. Returns days touched.

    WHY IT IS HERE. ``days.json`` carries ``lab`` — the number of hand labels posted that day — and
    it is the ONLY thing the calendar's green dot reads. Nothing in this repo regenerates the file
    (the corpus is produced upstream), so without this an import landed the labels, updated
    ``meta.json``'s totals, and left the calendar still showing the pre-import days: the operator
    browses back looking for the work they just did and the tool says they never did it. The count
    is DERIVED from ``labels.json`` and the post dates, so it cannot drift from what was merged.
    """
    days_p = d / "days.json"
    if not days_p.is_file():
        return 0
    posted: dict[str, str] = {}
    for f in sorted((d / "posts").glob("*.json")):
        for p in json.loads(f.read_text()):
            posted[str(p["id"])] = str(p["d"])[:10]
    per: dict[str, int] = {}
    for key, v in labels.items():
        if not isinstance(v, dict) or v.get("src") != "hand":
            continue
        day = posted.get(key.split("|")[0])
        if day is not None:
            per[day] = per.get(day, 0) + 1
    days = json.loads(days_p.read_text())
    changed = 0
    for iso, rec in days.items():
        n = per.get(iso, 0)
        if rec.get("lab") != n:
            rec["lab"] = n
            changed += 1
    if changed:
        days_p.write_text(json.dumps(days))
    return changed


def _key(row: dict[str, Any]) -> str:
    tid, tkr = row.get("tweet_id"), row.get("ticker")
    if not tid or not tkr:
        raise IngestError(f"row missing tweet_id/ticker: {json.dumps(row)[:120]}")
    return f"{tid}|{tkr}"


def import_labels(handle: str, path: Path, *, dry_run: bool = False) -> dict[str, int]:
    """Merge an exported JSONL into the account's corpus. Returns a counts summary.

    FAIL LOUD BEFORE WRITING ANYTHING: the whole file is parsed and keyed first, so a bad row on
    line 40 cannot leave the corpus half-updated.
    """
    d = account_dir(handle)
    raw = [ln for ln in path.read_text().splitlines() if ln.strip()]
    incoming: dict[str, dict[str, Any]] = {}
    for i, ln in enumerate(raw, 1):
        try:
            row = json.loads(ln)
        except json.JSONDecodeError as exc:
            raise IngestError(f"{path}:{i}: not valid JSON — {exc}") from exc
        if not isinstance(row, dict):
            raise IngestError(f"{path}:{i}: expected an object, got {type(row).__name__}")
        incoming[_key(row)] = row
    if not incoming:
        raise IngestError(f"{path} carries no rows")

    labels: dict[str, Any] = json.loads((d / "labels.json").read_text())
    gold_p = d / "gold_labels.jsonl"
    gold: dict[str, dict[str, Any]] = {}
    if gold_p.is_file():
        for ln in gold_p.read_text().splitlines():
            if ln.strip():
                g = json.loads(ln)
                gold[_key(g)] = g

    new, updated, over_machine = 0, 0, 0
    for key, row in incoming.items():
        prev = labels.get(key)
        if prev is None:
            new += 1
        elif prev.get("src") == "hand":
            updated += 1
        else:
            over_machine += 1
        merged: dict[str, Any] = dict(prev or {})
        for src_f, dst_f in _FIELD_MAP.items():
            if src_f in row:
                merged[dst_f] = row[src_f]
        merged["src"] = "hand"
        merged["needs_review"] = False        # a human has now read it
        labels[key] = merged
        gold[key] = row

    if dry_run:
        return {"rows": len(incoming), "new": new, "updated": updated,
                "replaced_machine": over_machine, "written": 0}

    (d / "labels.json").write_text(json.dumps(labels, separators=(",", ":")))
    gold_p.write_text("".join(json.dumps(g) + "\n" for _, g in sorted(gold.items())))

    meta_p = d / "meta.json"
    meta = json.loads(meta_p.read_text())
    meta["n_hand_labels"] = sum(1 for v in labels.values() if v.get("src") == "hand")
    meta["n_machine_labels"] = sum(1 for v in labels.values() if v.get("src") == "machine")
    meta_p.write_text(json.dumps(meta, indent=2) + "\n")
    days_changed = _refresh_day_labels(d, labels)

    return {"rows": len(incoming), "new": new, "updated": updated,
            "replaced_machine": over_machine, "written": len(incoming),
            "hand_total": meta["n_hand_labels"], "days_recounted": days_changed}
