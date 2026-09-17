"""A name the fund FOLLOWS is assemblable though it never entered the screen band.

WHY. `_maintenance_reason` had two keys — a committed dossier, an open underwrite record — and both
are CONSEQUENCES of work already done, so neither can admit a name the fund has never touched. That
is a bootstrap trap rather than a safeguard, and it closes on itself: `scenario-propose` and
`scenario-create` both require a committed dossier (`cli._dossier_doc`), so the underwrite key
cannot be minted for a fresh name either. A large-cap the operator wants to cover — UBER at ~$150bn
against a $300M–$10B band — was reachable by NO supported route.

THE FIX IS NOT A FORGED ARTIFACT. `_maintenance_reason`'s first key is an `.exists()` check, so an
empty `data/dossiers/<T>/dossier.json` satisfies it and the real build overwrites the stub. That
works, and it is the same fabricated-row move `_finalist` refuses on principle: it forges the very
document a gate reads to decide the name is legitimate, leaves that forgery behind whenever the
build fails, and writes down no reason anywhere.

A REASON IS THE POINT, NOT PAPERWORK. The band answers where the fund HUNTS; following a name is a
judgement that its answer does not apply here. So the judgement is stated in `data/followed.json`
and travels into `screen_status`, printing in the dossier's own main body — the page says out loud
that it did not come through the front door, and why. A bare ticker LIST would admit names silently,
which is the band's own failure mode rebuilt one level up; the blank-reason pins below are what
keep the file from degenerating into one.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any, cast

import pytest

import vinci.dossier.assemble as asm
from vinci.config import Config, get_config
from vinci.sleeves import DEFAULT_SLEEVE, SLEEVES

ROOT = pathlib.Path(__file__).resolve().parents[1]
FOLLOWED = ROOT / "data" / "followed.json"
DOSSIERS = ROOT / "data" / "dossiers"

# A ticker no screen has admitted and no record exists for, so only the follow key can move it.
UNTOUCHED = "ZZZZ"


def _cfg(tmp_path: pathlib.Path) -> Config:
    return Config(data_dir=tmp_path)


def _e(reason: Any, sleeve: str = "quality") -> dict[str, Any]:
    """One follow ENTRY in the committed shape. Every followed name states its reason AND the
    strategy book it is judged under (`vinci/sleeves.py`); the pre-sleeve bare-string form is
    refused outright, which `test_the_pre_sleeve_bare_string_form_is_refused` pins."""
    return {"reason": reason, "sleeve": sleeve}


def _write(tmp_path: pathlib.Path, payload: Any) -> Config:
    """Write ``payload`` as the follow file (raw text passes through unquoted)."""
    body = payload if isinstance(payload, str) else json.dumps(payload)
    (tmp_path / "followed.json").write_text(body)
    return _cfg(tmp_path)


# ---------------------------------------------------------------- the positive case


def test_a_followed_name_is_maintained_and_carries_its_reason(tmp_path: pathlib.Path) -> None:
    """THE POSITIVE CASE. A name with no dossier and no record is admitted by the follow key, and
    the operator's stated reason survives into the maintenance string verbatim."""
    reason = "large-cap comp for the mobility theme"
    cfg = _write(tmp_path, {UNTOUCHED: _e(reason)})

    why = asm._maintenance_reason(cfg, UNTOUCHED)

    assert why is not None, (
        f"{UNTOUCHED} is listed in followed.json but was not admitted — the follow key is the only "
        "route for a name with no prior work, so this is the bootstrap trap still closed")
    assert reason in why, (
        f"the maintenance reason {why!r} dropped the operator's stated reason — the reason is what "
        "makes the admission auditable; without it this is a bare ticker list")


def test_the_reason_reaches_screen_status_where_the_page_prints_it(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PIN THE ARTIFACT, NOT THE HELPER. `_maintenance_reason` returning the reason is worthless if
    `_finalist` drops it on the way to the caveat the human actually reads. The standalone record is
    stubbed because this pins the WIRING (followed.json → screen_status), not the price path."""
    reason = "followed as a read-across on the delivery marketplace"
    cfg = _write(tmp_path, {UNTOUCHED: _e(reason)})
    monkeypatch.setattr(asm, "_standalone_record", lambda *a, **k: object())

    fin = asm._finalist(cfg, UNTOUCHED, None, {"screen_run_at": "2026-07-29"})

    assert fin is not None, "the follow key admitted the name but _finalist refused it"
    assert fin.record is None, (
        "a followed name routed through _finalist carries a CandidateRecord — that type asserts "
        "SCREEN ADMISSION, and this name has none")
    assert reason in (fin.screen_status or ""), (
        f"screen_status {fin.screen_status!r} does not carry the reason — the dossier would print "
        "that the name is out-of-band without ever saying why it is covered")
    assert "NOT A CURRENT SCREEN CANDIDATE" in (fin.screen_status or ""), (
        "the out-of-band disclosure was lost — a followed name must never render as a screen pass")


def test_a_sentence_reason_does_not_double_the_period_in_the_caveat(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """OBSERVED IN THE RENDERED ARTIFACT. `_finalist` composes "…carries {reason}. The cap band…",
    so UBER's first real assembly printed "…outside it.. The cap band…" in its main-body caveat.
    Operators write reasons as sentences; the normalisation belongs here, not in their prose."""
    cfg = _write(tmp_path, {UNTOUCHED: _e("Followed as a large-cap read-across.")})
    monkeypatch.setattr(asm, "_standalone_record", lambda *a, **k: object())

    fin = asm._finalist(cfg, UNTOUCHED, None, {"screen_run_at": "2026-07-29"})

    assert fin is not None
    assert ".." not in (fin.screen_status or ""), (
        f"doubled period in the rendered caveat: {fin.screen_status!r}")
    assert "read-across. The cap band" in (fin.screen_status or "")


def test_the_follow_key_is_case_insensitive(tmp_path: pathlib.Path) -> None:
    """A lowercase key in the file admits the uppercase ticker — the queue and the resolver disagree
    on case often enough that a case-sensitive lookup would silently not-follow a listed name."""
    cfg = _write(tmp_path, {UNTOUCHED.lower(): _e("case should not decide coverage")})
    assert asm._maintenance_reason(cfg, UNTOUCHED) is not None


# ---------------------------------------------------------------- what it must REFUSE


def test_an_absent_file_is_normal_and_admits_nothing(tmp_path: pathlib.Path) -> None:
    """NOT following anything is the majority state, not a failure — it must not raise."""
    assert asm._follow_reason(_cfg(tmp_path), UNTOUCHED) is None
    assert asm._maintenance_reason(_cfg(tmp_path), UNTOUCHED) is None


def test_a_name_absent_from_the_file_is_not_followed(tmp_path: pathlib.Path) -> None:
    cfg = _write(tmp_path, {"AAPL": _e("some other name entirely")})
    assert asm._follow_reason(cfg, UNTOUCHED) is None
    assert asm._maintenance_reason(cfg, UNTOUCHED) is None


@pytest.mark.parametrize("reason", ["", "   ", "\n\t ", "...", " . ", ". . ."])
def test_a_blank_reason_is_refused(tmp_path: pathlib.Path, reason: str) -> None:
    """THE FILE MUST NOT DEGENERATE INTO A BARE TICKER LIST. A blank reason is the shape that would
    silently re-create the band's own failure mode — admission with no stated judgement.

    THE PUNCTUATION-ONLY CASES ARE A REVIEW FINDING, not padding. `"..."` is truthy after
    `.strip()`, so it cleared this guard and `_maintenance_reason`'s `rstrip(' .')` then emptied it
    — the caveat rendered "an operator follow decision — " with no reason after it. The guard has
    to test the value the CONSUMER sees; checking upstream of the normaliser left it reachable."""
    cfg = _write(tmp_path, {UNTOUCHED: _e(reason)})
    with pytest.raises(asm.DossierAssemblyError, match="no stated reason"):
        asm._maintenance_reason(cfg, UNTOUCHED)


@pytest.mark.parametrize("reason", [None, 123, True, ["a list"], {"nested": "object"}])
def test_a_non_string_reason_is_refused(tmp_path: pathlib.Path, reason: Any) -> None:
    """`{"UBER": true}` is the plausible hand-edit — a flag where a sentence belongs. It must not
    read as "followed, reason unknown"."""
    cfg = _write(tmp_path, {UNTOUCHED: _e(reason)})
    with pytest.raises(asm.DossierAssemblyError, match="no stated reason"):
        asm._maintenance_reason(cfg, UNTOUCHED)


def test_malformed_json_raises_rather_than_silently_following_nothing(
    tmp_path: pathlib.Path,
) -> None:
    """A trailing comma must not read as "nothing is followed". Degrading to None would drop EVERY
    followed name at once, and the operator would meet it as an unrelated LookupError later."""
    cfg = _write(tmp_path, '{"UBER": "a reason",}')
    with pytest.raises(asm.DossierAssemblyError, match="not valid JSON"):
        asm._maintenance_reason(cfg, UNTOUCHED)


def test_a_bare_ticker_list_is_refused(tmp_path: pathlib.Path) -> None:
    """The exact shape this design rejects — `["UBER", "SHOP"]` — must fail loud, not be coerced."""
    cfg = _write(tmp_path, ["UBER", "SHOP"])
    with pytest.raises(asm.DossierAssemblyError, match="mapping TICKER"):
        asm._maintenance_reason(cfg, UNTOUCHED)


def test_the_pre_sleeve_bare_string_form_is_refused_and_names_its_rewrite(
    tmp_path: pathlib.Path,
) -> None:
    """THE MIGRATION IS A REFUSAL, NOT A SILENT UPGRADE. Reading a bare string as "reason, sleeve
    unstated" would re-open the exact hole the field closes: an untagged followed name inherits the
    OVERSHOOT framing, so a megacap gets asked what broke when nothing did. Accepting both shapes
    would also leave two parsers of one file — the drift class this repo refuses on principle.

    The refusal QUOTES THE REWRITE because the fix is a hand-edit in another file; a refusal that
    only says "wrong shape" leaves the operator guessing at the key names."""
    cfg = _write(tmp_path, {UNTOUCHED: "a bare reason string"})
    with pytest.raises(asm.DossierAssemblyError, match="pre-sleeve form") as exc:
        asm._maintenance_reason(cfg, UNTOUCHED)
    assert '"sleeve"' in str(exc.value) and '"reason"' in str(exc.value), (
        f"the refusal does not show the shape to write: {exc.value}")


@pytest.mark.parametrize("sleeve", [None, "", "   ", "momentum", "OVERSHOOT", 7, True])
def test_a_missing_or_unlisted_sleeve_is_refused(tmp_path: pathlib.Path, sleeve: Any) -> None:
    """AN UNLISTED STRATEGY IS NOT REVIEWABLE — the `BEAR_BASES` precedent. Includes `"OVERSHOOT"`
    deliberately: the registry is case-SENSITIVE, and quietly upper/lower-casing a key would be the
    same silent coercion the blank-reason guard exists to refuse. The refusal names the admissible
    set so the operator can fix it without reading the source."""
    cfg = _write(tmp_path, {UNTOUCHED: {"reason": "followed for a read-across", "sleeve": sleeve}})
    with pytest.raises(asm.DossierAssemblyError) as exc:
        asm._maintenance_reason(cfg, UNTOUCHED)
    assert "sleeve" in str(exc.value) and "overshoot" in str(exc.value), (
        f"the refusal does not name the admissible set: {exc.value}")


def test_a_screen_candidate_is_overshoot_by_construction(tmp_path: pathlib.Path) -> None:
    """The screen finds overshoot SETUPS by construction (`screens/screen2.py`), so a name that
    came through the front door is tagged by the door it used — not by a default handed out to
    anyone who forgot to state one. Pinned so the two routes cannot silently converge on the same
    fallback if the follow route's refusal is ever weakened."""
    # A SENTINEL, not a forged CandidateRecord: `_finalist` branches on `rec is not None` and this
    # pins the SLEEVE on that branch, so building a real screen record would add setup that the
    # assertion does not depend on — and forging one is the fabricated-screen-verdict move the
    # maintenance path refuses on principle.
    fin = asm._finalist(_cfg(tmp_path), UNTOUCHED, cast(Any, object()),
                        {"screen_run_at": "2026-07-29"})
    assert fin is not None and fin.sleeve == DEFAULT_SLEEVE == "overshoot"


def test_the_followed_sleeve_reaches_the_finalist(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PIN THE ARTIFACT, NOT THE HELPER — the same rule the reason pin above follows. A sleeve that
    `_follow_entry` returns but `_finalist` drops never reaches the dossier, and Phase 2's framing
    would silently fall back to overshoot for exactly the names the tag exists for."""
    cfg = _write(tmp_path, {UNTOUCHED: _e("followed as a compounder read-across", "quality")})
    monkeypatch.setattr(asm, "_standalone_record", lambda *a, **k: object())
    fin = asm._finalist(cfg, UNTOUCHED, None, {"screen_run_at": "2026-07-29"})
    assert fin is not None and fin.sleeve == "quality", (
        f"the stated sleeve did not survive into the Finalist: {fin and fin.sleeve!r}")


def test_two_keys_differing_only_by_case_are_refused(tmp_path: pathlib.Path) -> None:
    """REVIEW FINDING. The case-fold used a dict comprehension, so `{"uber": …, "UBER": …}` kept
    whichever came last and DISCARDED the other stated reason silently — in the one file whose job
    is to record WHY a name is covered. That is the blank-reason class reached by another door: an
    admission whose stated judgement is gone. Plausible as a hand-edit (add a name, miss that it is
    already listed in another case), so it fails loud rather than picking a winner."""
    cfg = _write(tmp_path, {UNTOUCHED.lower(): _e("reason A"), UNTOUCHED: _e("reason B")})
    with pytest.raises(asm.DossierAssemblyError, match="listed more than once"):
        asm._maintenance_reason(cfg, UNTOUCHED)


# ---------------------------------------------------------------- the existing keys still hold


def test_the_prior_two_keys_are_unchanged(tmp_path: pathlib.Path) -> None:
    """REGRESSION. The follow key is additive: a committed dossier still answers when NOTHING is
    followed, and it must keep answering with no follow file present at all."""
    (tmp_path / "dossiers" / UNTOUCHED).mkdir(parents=True)
    (tmp_path / "dossiers" / UNTOUCHED / "dossier.json").write_text("{}")
    assert asm._maintenance_reason(_cfg(tmp_path), UNTOUCHED) == "a committed dossier"


def test_a_follow_entry_outranks_a_committed_dossier(tmp_path: pathlib.Path) -> None:
    """THIS PIN IS THE REVERSE OF WHAT #365 SHIPPED, AND #365 WAS WRONG.

    The dossier key ran first, so a followed name printed its stated reason on the FIRST assembly
    and lost it on every one after: the moment the artifact existed the caveat degraded to
    "assembled because the name carries a committed dossier", which explains nothing — the fund
    covers UBER because the fund has a page on UBER. The operator's judgement about why a $139bn
    name sits outside a $300M–$10B band stopped being printed. Found by re-assembling UBER once.

    The old ordering was defended as stability ("deleting a follow entry never changes the
    maintenance answer"), and that argument does not survive contact: BOTH keys return non-None, so
    the order never decides whether the name is MAINTAINED, only which reason is STATED. The
    stability it claimed is preserved either way — see the test below."""
    cfg = _write(tmp_path, {UNTOUCHED: _e("followed for the mobility read-across")})
    (tmp_path / "dossiers" / UNTOUCHED).mkdir(parents=True)
    (tmp_path / "dossiers" / UNTOUCHED / "dossier.json").write_text("{}")
    why = asm._maintenance_reason(cfg, UNTOUCHED)
    assert why is not None and "followed for the mobility read-across" in why, (
        f"a followed name with a committed dossier reported {why!r} — the stated reason is the "
        "whole point of requiring one, and it must survive the artifact existing")


def test_removing_a_follow_entry_still_leaves_the_name_maintained(tmp_path: pathlib.Path) -> None:
    """THE STABILITY THE OLD ORDERING CLAIMED, kept under the new one. Dropping the follow entry
    falls back to the dossier key — the name never becomes un-maintainable, it only reverts to the
    weaker sentence. That is why reordering costs nothing and buys the informative answer."""
    (tmp_path / "dossiers" / UNTOUCHED).mkdir(parents=True)
    (tmp_path / "dossiers" / UNTOUCHED / "dossier.json").write_text("{}")
    cfg = _write(tmp_path, {UNTOUCHED: _e("followed")})
    assert asm._maintenance_reason(cfg, UNTOUCHED) is not None
    (tmp_path / "followed.json").unlink()                      # operator drops the entry
    assert asm._maintenance_reason(_cfg(tmp_path), UNTOUCHED) == "a committed dossier"


# ---------------------------------------------------------------- the LIVE committed file


def test_the_committed_follow_file_is_well_formed() -> None:
    """CORPUS BEFORE SYNTHETIC. The pins above run on fixtures; this one runs on the file the fund
    actually ships, so a hand-edit that breaks it reddens here instead of at the next assembly."""
    if not FOLLOWED.exists():
        pytest.skip("no committed follow file yet — nothing is followed")
    doc = json.loads(FOLLOWED.read_text())
    assert isinstance(doc, dict), f"{FOLLOWED} must map TICKER → entry, got {type(doc).__name__}"
    assert doc, f"{FOLLOWED} is empty — delete it rather than shipping an empty admission list"
    cfg = get_config()
    for ticker, entry in doc.items():
        assert ticker == ticker.upper(), f"{ticker!r} should be uppercase in {FOLLOWED}"
        assert isinstance(entry, dict), (
            f"{ticker} uses the pre-sleeve bare-string form — every followed name states the "
            f"strategy book it is judged under, or it silently inherits the overshoot framing")
        reason = entry.get("reason")
        assert isinstance(reason, str) and reason.strip(), (
            f"{ticker} carries no stated reason — every followed name says why the band does not "
            f"apply to it")
        assert entry.get("sleeve") in SLEEVES, (
            f"{ticker} carries sleeve {entry.get('sleeve')!r}, not one of {sorted(SLEEVES)}")
        # the real lookup, over the real file, for every real entry
        got = asm._follow_entry(cfg, ticker)
        assert got is not None and got.reason == reason.strip()
        assert got.sleeve == entry["sleeve"]
        assert asm._follow_reason(cfg, ticker) == reason.strip()
        assert asm._maintenance_reason(cfg, ticker) is not None, (
            f"{ticker} is committed as followed but is not maintained — it would refuse assembly")


def test_every_committed_dossier_carries_a_sleeve_matching_its_entry_route() -> None:
    """CORPUS BEFORE SYNTHETIC, on the OTHER artifact the tag rides.

    PIN THE ARTIFACT, NOT THE HELPER: `_follow_entry` returning a sleeve is worthless if it never
    reaches the committed `dossier.json`. The expectation is DERIVED from the follow file rather
    than hardcoded as a roster, so this stays silent when the follow list grows and still reddens
    if a tag and the route that set it ever disagree — a name tagged `quality` whose follow entry
    was deleted, or a screen name that acquired a non-default sleeve from nowhere.

    READ THROUGH THE MODEL, NOT THE RAW KEY. A dossier may legitimately OMIT the field: FUBO's
    record is sealed by `known_wrong.json` and must not be rewritten until a post-combination
    re-assembly exists, so the backfill deliberately skipped it. Absent means `overshoot` — which
    is the truthful answer for it — and asserting on the raw key would fail a record the repo
    forbids touching."""
    if not DOSSIERS.is_dir():
        pytest.skip("no committed dossiers in this worktree")
    cfg = get_config()
    checked = 0
    for path in sorted(DOSSIERS.glob("*/dossier.json")):
        ticker = path.parent.name
        got = json.loads(path.read_text()).get("sleeve", DEFAULT_SLEEVE)
        assert got in SLEEVES, f"{ticker}: sleeve {got!r} is not one of {sorted(SLEEVES)}"
        entry = asm._follow_entry(cfg, ticker)
        expected = entry.sleeve if entry is not None else DEFAULT_SLEEVE
        assert got == expected, (
            f"{ticker}: the dossier says sleeve {got!r} but its entry route says {expected!r} — "
            f"the tag and the route that set it have diverged")
        checked += 1
    assert checked, "no committed dossier was checked — the loop found nothing to assert on"


def test_a_name_that_is_both_followed_and_a_screen_candidate_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """REVIEW FINDING (#377). The screen branch of `_finalist` returns BEFORE the follow file is
    consulted, so a ticker listed in `followed.json` under a non-default book that ALSO appears in
    the ranked candidate set was assembled as `overshoot` — its stated sleeve and its stated reason
    both silently discarded. That is an explicit operator judgement overridden by an implicit one,
    in the one file whose whole job is to record deliberate coverage decisions.

    IT REFUSES RATHER THAN PICKING A WINNER. Either precedence is defensible and both are guesses:
    "the screen wins" throws away a deliberate follow decision, "the follow wins" hides that the
    name now qualifies on its own. Only the operator knows which, so the build stops and names the
    two records that disagree.

    A followed entry on the DEFAULT book is NOT a conflict — it agrees with the screen route, so
    there is nothing to resolve and nothing is discarded."""
    monkey = _write(tmp_path, {UNTOUCHED: _e("followed as a compounder", "quality")})
    with pytest.raises(asm.DossierAssemblyError, match="BOTH a screen candidate and a followed"):
        asm._finalist(monkey, UNTOUCHED, cast(Any, object()), {"screen_run_at": "2026-07-29"})

    agreeing = _write(tmp_path, {UNTOUCHED: _e("followed, same book", DEFAULT_SLEEVE)})
    fin = asm._finalist(agreeing, UNTOUCHED, cast(Any, object()), {"screen_run_at": "2026-07-29"})
    assert fin is not None and fin.sleeve == DEFAULT_SLEEVE, (
        "a follow entry AGREEING with the screen route is not a conflict and must not refuse")


# ---------------------------------------------------------------- the operator's route ruling


def _ruled(reason: str, sleeve: str, ruling: Any) -> dict[str, Any]:
    return {**_e(reason, sleeve), "overrides_screen": ruling}


def test_an_operator_ruling_lets_the_follows_book_govern_a_screen_candidate(
    tmp_path: pathlib.Path,
) -> None:
    """WLK, 2026-09-17: followed under `ultra_short_term` while the screen still ranks it (#183).
    Without a ruling the two routes refuse, and must keep refusing — the pin above. WITH one, the
    follow's book governs, the candidate record stays the data source (the name IS screen-admitted;
    swapping in a standalone record would forge a different history), and the page's main body
    says the name is on BOTH routes, the ruling and the follow reason — "the follow wins" is exactly
    what would otherwise hide that the name also qualifies on its own."""
    cfg = _write(tmp_path, {UNTOUCHED: _ruled(
        "followed as a short-dated trade", "ultra_short_term",
        "operator decision 2026-09-17 — judged as a trade, not an overshoot")})
    rec = cast(Any, object())
    fin = asm._finalist(cfg, UNTOUCHED, rec, {"screen_run_at": "2026-08-24", "rank": 183})
    assert fin is not None
    assert fin.sleeve == "ultra_short_term"
    assert fin.record is rec, "the ruling must not replace the screen's own record"
    status = fin.screen_status or ""
    assert "ALSO A CURRENT SCREEN CANDIDATE at rank 183" in status
    assert "operator decision 2026-09-17 — judged as a trade, not an overshoot" in status
    assert "followed as a short-dated trade" in status


@pytest.mark.parametrize("ruling", ["", "   ", "...", 5, []])
def test_a_ruling_that_states_nothing_is_refused(tmp_path: pathlib.Path, ruling: Any) -> None:
    """A blank ruling would pass `_finalist` as though the operator had decided."""
    cfg = _write(tmp_path, {UNTOUCHED: _ruled("r", "ultra_short_term", ruling)})
    with pytest.raises(asm.DossierAssemblyError, match="states no ruling"):
        asm._follow_entry(cfg, UNTOUCHED)


def test_a_ruling_on_the_default_book_is_refused(tmp_path: pathlib.Path) -> None:
    """Followed under overshoot, the name already agrees with the screen route — a ruling there
    rules on nothing and would read as a decision that was never needed."""
    cfg = _write(tmp_path, {UNTOUCHED: _ruled("r", DEFAULT_SLEEVE, "operator decision")})
    with pytest.raises(asm.DossierAssemblyError, match="no disagreement to rule on"):
        asm._follow_entry(cfg, UNTOUCHED)


def test_every_committed_ruling_on_a_current_candidate_assembles_under_the_follows_book() -> None:
    """CORPUS BEFORE SYNTHETIC — the committed follow file against the committed screen snapshot.
    Derived, not a roster: every entry carrying `overrides_screen` whose ticker the committed queue
    still ranks must come out of the REAL loader under the follow's book, with the ruling printed.
    (A ruled name the screen has since dropped takes the maintenance path instead, which the
    well-formedness pin above already covers.)"""
    if not FOLLOWED.exists():
        pytest.skip("no committed follow file")
    cfg = get_config()
    if not (cfg.snapshots_dir / "candidate_records.jsonl").exists():
        pytest.skip("no committed screen snapshot in this worktree")
    ruled = {t: e for t, e in json.loads(FOLLOWED.read_text()).items() if "overrides_screen" in e}
    checked = 0
    for ticker, entry in sorted(ruled.items()):
        fin = asm.load_finalists(cfg, ticker=ticker)[0]
        if fin.record is None:
            continue
        assert fin.sleeve == entry["sleeve"], f"{ticker}: the ruling did not reach the finalist"
        assert "ALSO A CURRENT SCREEN CANDIDATE" in (fin.screen_status or ""), (
            f"{ticker}: assembled under the follow's book with no main-body note that it is also "
            f"a screen candidate")
        checked += 1
    assert checked or not ruled, "rulings exist but none was checked against the live queue"


def test_a_screen_id_verdict_is_refused_for_a_name_followed_under_another_book(
    tmp_path: pathlib.Path,
) -> None:
    """THE LEDGER TWIN OF THE TWO-ROUTES CHECK. A candidate id seals a screen-origin row with no
    sleeve — overshoot, counted in the PRIMARY spread. For a name followed under another book that
    would put the verdict in the fund's proof metric under a book it is not judged in, append-only.
    The refusal names the ticker route that carries the right book; a DEFAULT-book follow and an
    unfollowed name are not conflicts."""
    from vinci import cli

    other = _write(tmp_path, {UNTOUCHED: _e("r", "ultra_short_term")})
    msg = cli._screen_id_book_conflict(other, UNTOUCHED)
    assert msg is not None
    assert f"log-verdict {UNTOUCHED}" in msg and "'ultra_short_term'" in msg
    assert "primary spread" in msg
    agreeing = _write(tmp_path, {UNTOUCHED: _e("r", DEFAULT_SLEEVE)})
    assert cli._screen_id_book_conflict(agreeing, UNTOUCHED) is None
    assert cli._screen_id_book_conflict(agreeing, "NOTFOLLOWED") is None


def test_the_screen_id_guard_runs_before_the_ledger_write() -> None:
    """STRUCTURAL, like the edge-basis gate's: the ledger is append-only, so the refusal has to come
    before `log_verdict` or not at all."""
    src = (ROOT / "vinci" / "cli.py").read_text()
    body = src[src.index("def _cmd_log_verdict"):]
    body = body[:body.index("\ndef ", 10)]
    assert body.index("_screen_id_book_conflict") < body.index("= log_verdict("), (
        "the screen-id guard runs AFTER the ledger write — an append-only row cannot be recalled")


def test_logging_a_ruled_name_by_its_screen_id_writes_nothing(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """END TO END on a COPY of the committed tree: the real snapshots rebuilt into a store, the
    real follow file, the real parser. Every committed follow entry under a non-default book whose
    ticker the committed screen ranks is logged by its candidate id — each must refuse, print why,
    and leave BOTH the store's ledger and the committed JSONL untouched."""
    import shutil

    from vinci import cli
    from vinci.store import Store

    snaps = ROOT / "data" / "snapshots"
    if not FOLLOWED.exists() or not (snaps / "candidate_records.jsonl").exists():
        pytest.skip("no committed follow file or screen snapshot in this worktree")
    data = tmp_path / "data"
    data.mkdir()
    shutil.copytree(snaps, data / "snapshots")
    shutil.copy(FOLLOWED, data / "followed.json")
    cfg = Config(data_dir=data)
    cfg.ensure_dirs()
    with Store(cfg.db_path) as store:
        store.rebuild_from_snapshots(cfg.snapshots_dir)
    monkeypatch.setattr(cli, "get_config", lambda: cfg)

    queue = [json.loads(ln) for ln in (snaps / "ranked_queue.jsonl").read_text().splitlines()
             if ln.strip()]
    follows = json.loads(FOLLOWED.read_text())
    clashing = [r["candidate_id"] for r in queue
                if follows.get(r["ticker"], {}).get("sleeve", DEFAULT_SLEEVE) != DEFAULT_SLEEVE]
    if not clashing:
        pytest.skip("no committed follow entry is also a current screen candidate")
    jsonl = (data / "snapshots" / "decision_ledger.jsonl").read_text()
    for cid in clashing:
        with Store(cfg.db_path) as store:
            before = len(list(store.iter_ledger()))
        args = cli.build_parser().parse_args([
            "log-verdict", cid, "--verdict", "BUY", "--twin", "t", "--thesis", "th", "--kill", "k",
            "--horizon-days", "10", "--confidence", "medium",
            "--edge-basis", "event-structural", "--edge-note", "a dated event 2026-10-01"])
        assert cli._cmd_log_verdict(args) == 1, f"{cid}: logged under the wrong book"
        assert "is FOLLOWED under" in capsys.readouterr().out
        with Store(cfg.db_path) as store:
            assert len(list(store.iter_ledger())) == before, f"{cid}: a row reached the store"
    assert (data / "snapshots" / "decision_ledger.jsonl").read_text() == jsonl
