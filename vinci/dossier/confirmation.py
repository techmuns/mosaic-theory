"""C(iv) of the vote rule: a ten-draw confirmation inside `log-verdict`, before the ledger row is
written (`docs/records/2026-11-10-the-proposal-vote-rule-design.md` §5b and §9).

WHY. The page's own proposal is a five-draw one, and under R1 at five its unstable band is today's
(p from 0.631 to 0.979). What the ledger SEALS is what the BUY − AVOID spread's machine baseline is
decomposed against, so at the one moment a verdict is sealed the proposal is decided by R1 at ten
(9 of 10) instead: about $3–4 a logged verdict, against +$1.00–1.50 on every build.

WHAT IT DRAWS. The committed page's mechanical layer as the synthesis received it
(`layer_as_synthesized`) and the page's transcripts, read by production's reader and refused where
they differ from the page's input record (`page_transcripts`), sent through production's
`synthesize` with ten draws. Both readers are the replay harness's own readings
(`evals.capture_child.pre_synthesis_mech`, `evals.replay.transcript_for`) written on the decision
path, which never imports the harness; tests pin them equal on the committed pages. The
input is the committed page, never live data, so the as-of discipline of `_sealed_proposal` holds.
It is THIS code's request on that layer: where the prompt changed since the page was built, it is
not the request the page's own draws used, and the record carries the request's sha256 so the two
can be told apart.

ONE CONFIRMATION PER PAGE VERSION. Each is recorded (`record`) whether or not the verdict is then
logged, keyed by ticker, the page's `assembled_at` AND the sha256 of what the synthesis receives
(`inputs_sha256`: a layer refresh keeps the stamp and moves the layers — Codex round 1); a second
log of the same page REUSES it and draws nothing, so a confirmation cannot be re-run until it
agrees. A page whose input record cannot identify its transcripts (a backfill) is NOT confirmed:
today's files are not the page's inputs (Codex round 1). A dry run's confirmation is
recorded too. Every command prints the confirmation it draws or reuses, so a later log that
REUSES one seals `revealed_pre_verdict`: the human has seen it.
The proposal stays sealed until the verdict is logged, as today.

Nothing here writes the decision ledger; `log-verdict` does, after this returns.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from vinci.dossier.schemas import MechanicalLayer
from vinci.dossier.verdict import GATE_RULE, DrawGate, MachineProposal, derive_proposal, draw_gate
from vinci.graph.llm import LlmClient
from vinci.sleeves import DEFAULT_SLEEVE

#: R1 at ten: the confirmation's draws (9 of 10 to propose).
CONFIRM_DRAWS = 10
#: The record of every confirmation drawn, one JSON row each, under the snapshots folder.
RECORD_NAME = "proposal_confirmations.jsonl"
#: More FAILED draws than this (an API error or an incomplete call, not an unrecognized lean) is an
#: outage, not the model's read: refused and not recorded (review round 0). Up to it, a failed draw
#: is R3's dissent.
MAX_FAILED_DRAWS = 2


class ConfirmationError(RuntimeError):
    """A confirmation that cannot be drawn honestly: the log refuses rather than seal without it."""


@dataclass(frozen=True)
class Confirmation:
    ticker: str
    assembled_at: str | None
    gate: DrawGate
    proposal: MachineProposal
    model: str
    request_sha256: str | None
    drawn_at: str
    dry_run: bool
    reused: bool
    #: True when the transcripts read equal the page's own input record. A fresh confirmation is
    #: never drawn without it (Codex round 1); a row recorded before that rule may carry False.
    transcripts_verified: bool = False
    #: The sha256 of what the synthesis received (`inputs_sha256`), the reuse key's third part.
    inputs_sha256: str | None = None

    def tally(self) -> dict[str, Any]:
        """What the ledger seals beside the proposal (R4): the split as counts, and which draws."""
        return {"draws": self.gate.attempted, "labels": dict(self.gate.labels),
                "lean": self.gate.lean, "modal_count": self.gate.count,
                "required": self.gate.required, "passes": self.gate.passes,
                "state": self.gate.state, "rule": GATE_RULE, "model": self.model,
                "request_sha256": self.request_sha256, "drawn_at": self.drawn_at,
                "assembled_at": self.assembled_at, "revealed_by_dry_run": self.dry_run,
                "transcripts_verified": self.transcripts_verified,
                "inputs_sha256": self.inputs_sha256}


class _Recording(LlmClient):
    """Forwards to the real client and keeps the sha256 of the request it was sent."""

    def __init__(self, inner: LlmClient) -> None:
        self._inner = inner
        self.request_sha256: str | None = None

    @property
    def model(self) -> str:
        return self._inner.model

    @property
    def last_usage(self) -> Any:
        """The inner client's usage of its latest call (`synthesize` reads it for the log)."""
        return getattr(self._inner, "last_usage", None)

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        if self.request_sha256 is None:
            body = json.dumps({"system": system, "user": user, "tool": tool}, sort_keys=True,
                              default=str)
            self.request_sha256 = hashlib.sha256(body.encode()).hexdigest()
        return self._inner.extract(system=system, user=user, tool=tool, cache=cache)


def layer_as_synthesized(page: dict[str, Any]) -> MechanicalLayer:
    """The committed mechanical layer as `synthesize` received it: the gap block and the covenant
    term rows the synthesis never reads are cleared, as the replay harness clears them
    (`evals.capture_child.pre_synthesis_mech`; pinned equal on every committed page)."""
    mech = MechanicalLayer.model_validate(page["mechanical"]).model_copy(update={"ev_gap": None})
    cs = mech.capital_structure
    if cs is not None and cs.covenant_term_rows is not None:
        mech = mech.model_copy(update={
            "capital_structure": cs.model_copy(update={"covenant_term_rows": None})})
    return mech


def inputs_sha256(page: dict[str, Any]) -> str:
    """The sha256 of what the synthesis receives from the committed page: its layer as synthesized,
    its ticker, name and sleeve, and the transcripts its input record names (file and sha256). The
    third part of the reuse key, because `layer_refresh.write_recorded` (ciq-reread,
    financials-backfill, the anchor refresh) moves a page's layers and keeps its `assembled_at`."""
    recorded = sorted((str(c["file"]), str(c["sha256"]))
                      for c in ((page.get("inputs") or {}).get("ciq") or [])
                      if c.get("kind") == "transcript")
    body = json.dumps({"ticker": page.get("ticker"), "name": page.get("name"),
                       "sleeve": str(page.get("sleeve") or DEFAULT_SLEEVE),
                       "layer": json.loads(layer_as_synthesized(page).model_dump_json()),
                       "transcripts": recorded}, sort_keys=True)
    return hashlib.sha256(body.encode()).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def page_transcripts(ticker: str, *, ciq_root: Path,
                     page: dict[str, Any]) -> tuple[str | None, bool]:
    """The transcript text the build fed the synthesis, by production's reader
    (`ciq_sheets.transcript_for_synthesis`), and whether it was VERIFIED against the page's input
    record (names and sha256), refusing where they differ:

    - a BUILD record is COMPLETE (every export the bundle held is listed, `inputs.load_bundle`), so
      it is checked even where it lists no transcript: one on disk now is an input the build never
      read (found by the corpus run of this check: TECX);
    - a BACKFILLED record lists only what the page stamped, and no page stamped a transcript, so
      it is checked only where it lists one; otherwise the read is returned UNVERIFIED, as is a
      page with no record."""
    from vinci.dossier import ciq_sheets
    from vinci.dossier.ciq import CiqBundle
    folder = ciq_root / ticker
    files = sorted(p for p in folder.iterdir() if p.is_file()) if folder.is_dir() else []
    bundle = CiqBundle.from_files(ticker, files)
    got = {w.path.name: _sha256(w.path) for w in bundle.all_workbooks("transcript")}
    inputs = page.get("inputs") or {}
    recorded = {c["file"]: c["sha256"] for c in (inputs.get("ciq") or [])
                if c.get("kind") == "transcript"}
    complete = inputs.get("recorded") == "build" and not any(
        str(u.get("input", "")).startswith("ciq:") for u in (inputs.get("unrecorded") or []))
    if (complete or recorded) and got != recorded:
        raise ConfirmationError(f"{ticker}: transcripts on disk {sorted(got)} differ from the "
                                f"page's input record {sorted(recorded)} (names or sha256)")
    text = ciq_sheets.transcript_for_synthesis(bundle)
    # EVERY CALL ON FILE MUST READ (found by the gate, 2026-11-11). Production's reader drops a call
    # whose read fails and the BUILD flags it (`unparsed_transcript_flag`); LibreOffice fails a
    # conversion while another runs, so GOOGL's OLE-disguised Q3 call can drop under load. The
    # confirmation is drawn once per page version, so a call short would seal a read of other
    # inputs for good: it refuses instead (no committed page carries the build's flag, 2026-11-11)
    present = set(ciq_sheets._SLICE_CALL.findall(text or ""))
    missing = sorted(name for name in got if name not in present)
    if missing:
        raise ConfirmationError(f"{ticker}: {len(missing)} of {len(got)} call(s) on file did not "
                                f"read ({'; '.join(missing)}) — LibreOffice fails a conversion "
                                "while another runs, so re-run alone; if it never reads, re-export "
                                "it and rebuild the page")
    return text, complete or bool(recorded)


def _rows(record: Path) -> list[dict[str, Any]]:
    if not record.exists():
        return []
    return [json.loads(x) for x in record.read_text(encoding="utf-8").splitlines() if x.strip()]


def _from_row(row: dict[str, Any], sleeve: str) -> Confirmation:
    gate = DrawGate.from_record({**row, "attempted": row["draws"]})
    if gate is None:   # every recorded row carries its gate
        raise ConfirmationError(f"{row['ticker']}: a recorded confirmation carries no gate")
    if row.get("lean") is not None:
        # THE LEAN AS DRAWN: the row is written with sorted keys, so a TIED split comes back in
        # name order and `from_record` would name another modal lean than the one recorded
        gate = replace(gate, lean=str(row["lean"]))
    prop = derive_proposal(row.get("evidence_balance"), sleeve=sleeve, gate=gate)
    return Confirmation(ticker=row["ticker"], assembled_at=row.get("assembled_at"), gate=gate,
                        proposal=prop, model=row["model"], request_sha256=row.get("request_sha256"),
                        drawn_at=row["drawn_at"], dry_run=bool(row.get("dry_run")), reused=True,
                        transcripts_verified=bool(row.get("transcripts_verified")),
                        inputs_sha256=row.get("inputs_sha256"))


def confirm(page: dict[str, Any], *, llm: LlmClient, ciq_root: Path, record: Path,
            dry_run: bool = False, draws: int = CONFIRM_DRAWS) -> Confirmation:
    """The page's confirmation: the recorded one if this page version has one, else ten fresh
    draws, recorded before they are returned. PAID when it draws."""
    from vinci.dossier.synthesis import synthesize

    ticker, stamp = str(page["ticker"]), page.get("assembled_at")
    sleeve = str(page.get("sleeve") or DEFAULT_SLEEVE)
    key = inputs_sha256(page)
    prior = [r for r in _rows(record) if r["ticker"] == ticker and r.get("assembled_at") == stamp
             and r.get("inputs_sha256") == key]
    if prior:
        return _from_row(prior[0], sleeve)
    try:
        transcript, verified = page_transcripts(ticker, ciq_root=ciq_root, page=page)
    except (ConfirmationError, OSError) as exc:
        raise ConfirmationError(f"{ticker}: the page's transcripts cannot be read as recorded "
                                f"({exc}); the confirmation refuses rather than draw on other "
                                "inputs") from exc
    if not verified:
        # TODAY'S FILES ARE NOT THE PAGE'S INPUTS (Codex round 1). A backfilled record never lists a
        # transcript, so a call exported after the page was assembled would sway a proposal the
        # ledger seals against the old page; printing UNVERIFIED did not stop it being sealed
        raise ConfirmationError(f"{ticker}: the page's input record cannot identify the "
                                "transcripts its build read (a backfilled record lists none), so "
                                "today's files are not known to be its inputs — re-assemble the "
                                "page, which records them; nothing drawn, nothing recorded")
    mech = layer_as_synthesized(page)
    rec = _Recording(llm)
    synth, flags, _log = synthesize(mech, llm=rec, ticker=ticker, name=str(page["name"]),
                                    transcript=transcript, sleeve=sleeve, draws=draws)
    if synth is None:
        # NOTHING WAS LEARNED, so nothing is recorded: an outage or a missing key must not use up
        # the page's one confirmation (a later log draws again)
        raise ConfirmationError(f"{ticker}: no draw of {draws} returned a usable synthesis "
                                f"({'; '.join(flags) or 'no flag'}); nothing recorded")
    agreement = synth.draw_agreement
    failed = draws - (agreement.completed if agreement is not None else 0)
    if failed > MAX_FAILED_DRAWS:
        # A PARTIAL OUTAGE is not the model's read either: refused and not recorded, and nothing
        # about the drawn leans is printed (review round 0)
        raise ConfirmationError(f"{ticker}: {failed} of {draws} draws failed (more than "
                                f"{MAX_FAILED_DRAWS}): an outage, not a read; nothing recorded")
    gate = (agreement.gate() if agreement is not None else None) or draw_gate([], draws)
    balance = synth.evidence_balance
    prop = derive_proposal(balance, sleeve=sleeve, gate=gate)
    drawn_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    row = {"ticker": ticker, "assembled_at": stamp, "drawn_at": drawn_at, "model": llm.model,
           "draws": gate.attempted, "labels": dict(gate.labels), "lean": gate.lean,
           "modal_count": gate.count, "required": gate.required, "passes": gate.passes,
           "state": gate.state, "rule": GATE_RULE, "evidence_balance": balance,
           "proposal": prop.action.value if prop.action is not None else None,
           "request_sha256": rec.request_sha256, "dry_run": dry_run,
           "transcripts_verified": verified, "inputs_sha256": key,
           "flags": [f for f in flags if "synthesis" in f]}
    record.parent.mkdir(parents=True, exist_ok=True)
    with record.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
    return Confirmation(ticker=ticker, assembled_at=stamp, gate=gate, proposal=prop,
                        model=llm.model, request_sha256=rec.request_sha256, drawn_at=drawn_at,
                        dry_run=dry_run, reused=False, transcripts_verified=verified,
                        inputs_sha256=key)
