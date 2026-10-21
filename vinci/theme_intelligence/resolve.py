"""A REVIEWER's disposition of one card-review finding — dismissed, or reopened — kept append-only
beside the finding, never in place of it (follow-up B of the research desk record, 2026-10-13).

    python -m vinci.theme_intelligence review list [--thesis TH-…] [--history]
    python -m vinci.theme_intelligence review dismiss --finding F-… --reviewer NAME --reason "…"
    python -m vinci.theme_intelligence review reopen --finding F-… --reviewer NAME --reason "…"

WHAT A DISMISSAL IS: a named reviewer read the finding and the line, and records why the line may
stand as printed. The finding stops counting as OPEN on the card, the desk's Review screen and the
weekly report, and is shown as history with who, when and why.

WHAT IT IS NOT: a verification. Accepting a warning never makes unsupported evidence valid —
  * the line keeps the label the finding capped (at most SOURCE OPINION, cards.shown_label);
  * a WITHHELD line is never dismissible: it closes by an analyst correction that passes the card
    checks (`reassess --corrections`) or by a re-review;
  * a line whose words or cited evidence changed since the review (NOT RE-REVIEWED) is never
    dismissible: nobody has read it as it stands;
  * no research-action rule reads the record (test_theme_intelligence_isolation).

Each finding has a KEY (`report.finding_key`) bound to the review that made it and to the line as
it reads now: the same finding read onto a later unreviewed version keeps its dismissal; a changed
line, or a NEW review's finding on a later version, is open again. Every row stays; a finding's
state is the row no later row SUPERSEDES (each names the state its reviewer saw), never the latest
of two machines' clocks — and a dismissal and a reopening made apart read OPEN until a new
resolution supersedes both (`report.resolution_state`).

Every write is a run of mode "review" — $0, no fetch, no model call — so `state pull` sees it and
carries it (state.py), and `qa` re-checks it.
"""

from __future__ import annotations

import hashlib
import traceback
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Literal

from vinci.theme_intelligence.report import (
    LineFinding,
    resolution_heads,
    resolution_state,
    review_findings,
)
from vinci.theme_intelligence.schemas import (
    ReviewResolution,
    RunStatus,
    Thesis,
    ThesisStatus,
    ThesisVersion,
    WeeklyRun,
)
from vinci.theme_intelligence.store import Store

if TYPE_CHECKING:
    from vinci.theme_intelligence.pipeline import Pipeline

Action = Literal["dismissed", "reopened"]


class ResolutionError(ValueError):
    """A resolution refused — the message says why; nothing was written."""


@dataclass(frozen=True)
class Located:
    """One open card-review finding on a thesis's CURRENT version, with its resolutions."""
    thesis: Thesis
    version: ThesisVersion
    finding: LineFinding
    #: its state (`report.resolution_state`; None: never resolved, or a conflict)
    state: ReviewResolution | None
    #: the resolutions no other supersedes — a new one supersedes them all
    heads: tuple[ReviewResolution, ...] = ()

    @property
    def conflict(self) -> bool:
        """A dismissal and a reopening made apart, neither superseding the other."""
        return len({h.action for h in self.heads}) > 1

    @property
    def dismissed(self) -> bool:
        return self.finding.dismissible and self.state is not None \
            and self.state.action == "dismissed"


def current_findings(store: Store, thesis_ids: tuple[str, ...] = (), *,
                     archived: bool = False) -> list[Located]:
    """Every open card-review finding on the current version of the named theses — by default,
    of every thesis not archived (an archived thesis's findings are history on the desk)."""
    out: list[Located] = []
    for t in store.theses():
        if thesis_ids and t.thesis_id not in thesis_ids:
            continue
        if not thesis_ids and not archived and t.status is ThesisStatus.ARCHIVED:
            continue
        v = store.thesis_version(t.thesis_id, t.current_version)
        if v is None:
            continue
        by_key: dict[str, list[ReviewResolution]] = {}
        for r in store.review_resolutions(t.thesis_id):
            by_key.setdefault(r.finding_key, []).append(r)
        out += [Located(t, v, lf, resolution_state(rows := by_key.get(lf.key, [])),
                        tuple(resolution_heads(rows)))
                for lf in review_findings(store, t.thesis_id, v)]
    return out


def finding_state(x: Located) -> str:
    """DISMISSED, OPEN (dismissible), WITHHELD or NOT RE-REVIEWED — read from the finding's
    structured fields, as `not_dismissible` is."""
    lf = x.finding
    return ("DISMISSED" if x.dismissed else "OPEN" if lf.dismissible
            else "NOT RE-REVIEWED" if lf.finding.changed and not lf.withheld else "WITHHELD")


def not_dismissible(lf: LineFinding) -> str:
    """Why a finding cannot be dismissed, in words ("" when it can)."""
    if lf.dismissible:
        return ""
    if lf.finding.changed and not lf.withheld:
        return ("the line's words or cited evidence changed since the review made it (NOT "
                "RE-REVIEWED) — nobody has read the line as it stands: a review must run first")
    return ("the line is WITHHELD (failed source verification) — a withheld line closes by an "
            "analyst correction that passes the card checks (`reassess --corrections`) or by a "
            "re-review, never by a dismissal")


def resolve(pipe: Pipeline, key: str, action: Action, *, reviewer: str, reason: str,
            as_of: date) -> tuple[WeeklyRun, ReviewResolution]:
    """Record a reviewer's `action` on finding `key` as a run of its own. Refused, with nothing
    written, when the reviewer or the reason is blank, the key names no open finding on a current
    version, the finding may not be dismissed, it is already dismissed, or (reopen) it is not."""
    reviewer, reason = reviewer.strip(), reason.strip()
    if not reviewer or not reason:
        raise ResolutionError("a resolution names its reviewer and its reason — both are required")
    hit = [x for x in current_findings(pipe.store, archived=True) if x.finding.key == key]
    if not hit:
        raise ResolutionError(
            f"no open card-review finding {key} on any thesis's current version — `review list` "
            f"shows the keys (a changed line, or a finding a new review raised, has a new key)")
    if len(hit) > 1:  # a key names a thesis, a review and a line: never two findings
        raise ResolutionError(f"{key} names {len(hit)} findings — refusing to guess which")
    (x,) = hit
    lf = x.finding
    if action == "dismissed":
        if not lf.dismissible:
            raise ResolutionError(f"{key} cannot be dismissed: {not_dismissible(lf)}")
        if x.dismissed and x.state is not None:
            raise ResolutionError(f"{key} is already dismissed ({x.state.reviewer}, "
                                  f"{x.state.created_at.date().isoformat()}: {x.state.reason})")
    elif not x.dismissed:
        raise ResolutionError(f"{key} is not dismissed — there is nothing to reopen")
    run = pipe.start_run("review", as_of=as_of, window_from=as_of, window_to=as_of)
    try:
        now = datetime.now(tz=UTC)
        rid = "RR-" + hashlib.sha256(
            f"{key}|{action}|{reviewer}|{reason}|{now.isoformat()}".encode()).hexdigest()[:12]
        r = ReviewResolution(
            resolution_id=rid, run_id=run.run_id, thesis_id=lf.thesis_id, version=lf.version,
            sentence_id=lf.sentence_id, finding_key=key, finding_code=lf.finding.code,
            finding_version=lf.finding.origin_version, finding_detail=lf.finding.detail,
            line_text=lf.text, claim_ids=lf.claim_ids, action=action, reviewer=reviewer,
            reason=reason, created_at=now,
            supersedes=tuple(sorted(h.resolution_id for h in x.heads)))
        with pipe.store.tx():
            pipe.store.add_review_resolution(r)
        pipe._count(f"findings_{action}")  # noqa: SLF001 — the run's own counter
    except Exception as exc:
        pipe.finish_run(RunStatus.FAILED, error=f"{type(exc).__name__}: {exc}\n"
                                                f"{traceback.format_exc()[-1500:]}")
        raise
    return pipe.finish_run(RunStatus.SUCCEEDED), r


def check_run(store: Store, run_id: str) -> list[str]:
    """QA: what is wrong with the resolutions a run wrote — each must name a finding that was on
    the version it records, with that finding's words and that line's words and evidence, and a
    dismissal one that may be dismissed. [] when every one holds."""
    bad: list[str] = []
    for r in store.review_resolutions(run_id=run_id):
        known = {x.resolution_id for x in store.review_resolutions(r.thesis_id)
                 if x.finding_key == r.finding_key and x.resolution_id != r.resolution_id}
        if set(r.supersedes) - known:
            bad.append(f"{r.resolution_id}: supersedes {sorted(set(r.supersedes) - known)}, "
                       f"no resolution of {r.finding_key}")
        v = store.thesis_version(r.thesis_id, r.version)
        lf = next((x for x in review_findings(store, r.thesis_id, v) if x.key == r.finding_key),
                  None) if v is not None else None
        if lf is None:
            bad.append(f"{r.resolution_id}: {r.finding_key} is no finding of {r.thesis_id} "
                       f"version {r.version}")
        elif (lf.sentence_id, lf.text, lf.claim_ids, lf.finding.code, lf.finding.detail,
              lf.finding.origin_version) != (r.sentence_id, r.line_text, r.claim_ids,
                                             r.finding_code, r.finding_detail,
                                             r.finding_version):
            bad.append(f"{r.resolution_id}: its record of {r.finding_key} does not match the "
                       f"finding")
        elif r.action == "dismissed" and not lf.dismissible:
            bad.append(f"{r.resolution_id}: dismissed {r.finding_key}, which may not be "
                       f"dismissed: {not_dismissible(lf)}")
    return bad
