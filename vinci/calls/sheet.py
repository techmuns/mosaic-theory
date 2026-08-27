"""The LOCAL AUDIT WORKBOOK — one row per (tweet, ticker), for verifying tags by hand.

NOT A PRODUCT SURFACE. This is an operator tool: a spreadsheet you sort, filter and bulk-edit, then
feed back with `vinci calls import-sheet`. The dashboard stays read-only and knows nothing about it.

WHY A SHEET AT ALL, when the tape exists. The tape is for reading ONE call against its chart. This
is for the other job — walking 8,185 rows, sorting by what the adoption changed, and correcting in
bulk. Different question, different instrument.

THE LAYOUT IS THE ARGUMENT. Six bands, left to right: what he POSTED, WHERE IT WAS TRADING when he
posted, what it WAS (the original machine labeller), what it is NOW (the adopted second reading,
with the reasoning behind it), what HAPPENED to the price, and the FINAL band you edit.

WHY "WAS" IS STILL HERE. The adoption replaced the machine's tags IN PLACE. Without the before
column the operator is asked to confirm a tag with no way to see the move that produced it — a bare
"changed: YES" and nothing to check it against. It reads `labels.machine.json`, the one-time
pre-adoption snapshot; where none exists WAS equals NOW and every row reads unchanged, rather than
the sheet inventing a comparison.

The final columns are PRE-FILLED WITH WHAT THE CORPUS CARRIES TODAY — the status quo is what you
confirm or override. Changes are coloured so the eye goes there; nothing is hidden.
"""
from __future__ import annotations

import json
from bisect import bisect_right
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from vinci.calls import jsonl_lines
from vinci.calls.accounts import account_dir
from vinci.calls.audit import ACTIONS, BIASES, CLASSES, SPECS, TARGET_TYPES, load_audit
from vinci.calls.bars import load_bars

#: Left band: identity + the post itself. Frozen, so the text stays visible while you scroll right.
COLS_POST = ["tweet_id", "date", "time", "ticker", "text", "url", "media", "likes", "views",
             "n_tickers"]
#: WHERE IT WAS TRADING. The anchor that makes a bare number in the text readable: "$530" is a
#: bullish call above spot and a bearish one below it, and nothing else on the row says which.
COLS_PRICE = ["px_at_post", "px_session", "px_close", "target_gap"]
#: WAS — the upstream machine labeller, as the corpus shipped, from labels.machine.json.
COLS_WAS = ["was_class", "was_bias", "was_action", "was_target", "was_target_type", "was_hlo",
            "was_hhi", "was_spec"]
#: NOW — what the corpus carries today. `src` says which tier wrote it: `hand` is a person, `llm`
#: the adopted second reading, `machine` the original where nothing replaced it.
COLS_NOW = ["src", "now_class", "now_bias", "now_action", "now_target", "now_target_type",
            "now_hlo", "now_hhi", "now_spec", "now_conditional", "now_retrospective",
            "why", "probability", "summary", "changed", "changed_on"]
COLS_SCORE = ["status", "entry", "entry_date", "exit", "exit_date", "horizon_days",
              "horizon_assumed", "ret", "bench_ret", "excess", "mfe", "mae", "target_px",
              "target_status", "target_hit", "direction_correct"]
COLS_FINAL = ["final_bias", "final_action", "final_target", "final_target_type", "final_hlo",
              "final_hhi", "final_spec", "final_class", "final_conditional",
              "final_retrospective", "verified", "notes"]
COLS = (COLS_POST + COLS_PRICE + COLS_WAS + COLS_NOW + COLS_SCORE + ["flags", "priority"]
        + COLS_FINAL)

#: The fields whose MOVEMENT is worth colouring. Bias first: it flips the sign of every return, so
#: a wrong bias is not a tagging nit, it is an inverted result.
COMPARED = [("bias", "was_bias", "now_bias"), ("target", "was_target", "now_target"),
            ("target_type", "was_target_type", "now_target_type"),
            ("spec", "was_spec", "now_spec"), ("class", "was_class", "now_class"),
            ("action", "was_action", "now_action"), ("hlo", "was_hlo", "now_hlo"),
            ("hhi", "was_hhi", "now_hhi")]

#: WHAT TO LOOK AT FIRST. The corpus now carries the adopted reading, so the question is no longer
#: "which reader is right" but "did the adoption get this row right, and is anything still broken".
#: Ranked by what it costs if the tag is wrong.
_DIRECTIONAL = {"bullish", "bearish"}
_BROKEN_TARGET = {"unparseable", "sign_conflict", "implausible"}


def _priority(was_bias: object, now_bias: object, cls: object, changed: list[str],
              target_status: object) -> str:
    a, b = _norm(was_bias), _norm(now_bias)
    if a in _DIRECTIONAL and b in _DIRECTIONAL and a != b:
        return "1 direction flipped"
    if str(target_status) in _BROKEN_TARGET:
        return "2 target unreadable"
    if "bias" in changed and (a in _DIRECTIONAL) != (b in _DIRECTIONAL):
        return "4 not a call" if str(cls) in _NON_SIGNAL else "3 call or not"
    if str(cls) in _NON_SIGNAL:
        return "4 not a call"
    return "5 detail moved" if changed else "6 unchanged"

_NON_SIGNAL = {"flow_spam", "promo", "noise", "engagement"}


def _norm(v: Any) -> str:
    """Compare tags as the operator reads them: blank, none and null are the same absence."""
    if v is None:
        return ""
    s = str(v).strip().lower()
    return "" if s in ("none", "null", "nan") else s


def _flags(cur: dict[str, Any], res: dict[str, Any] | None) -> str:
    """The tape's review reasons, as a sortable column. Same rule set, stated once here for the
    sheet — the tape derives it live and this file cannot import JS."""
    if cur.get("src") == "hand" or cur.get("post_class") in _NON_SIGNAL:
        return ""
    out = []
    ts = (res or {}).get("target_status")
    if ts == "sign_conflict":
        out.append("target-vs-bias")
    if ts == "implausible":
        out.append("target-far-from-price")
    if ts == "counter_directional":
        out.append("level-wrong-side")
    if (res or {}).get("status") == "NO_PRICE_DATA":
        out.append("no-price")
    if cur.get("spec") in ("A", "B"):
        out.append("specific-but-guessed")
    if cur.get("target_type") not in (None, "none") and _norm(cur.get("bias")) in ("", "none"):
        out.append("target-no-direction")
    if cur.get("bias") == "mixed":
        out.append("two-sided")
    return ", ".join(out)



#: US equity regular session close, in exchange-local time. Half-days (13:00 ET) are not modelled:
#: see `_price_context` for why falling back one session there is the safe error.
_ET = ZoneInfo("America/New_York")
_CLOSE_HOUR = 16


def _price_context(bars: list[tuple[date, float, float, float, float, float]],
                   posted_at: str) -> dict[str, Any]:
    """The price the post could see, and how its own session ended.

    `px_at_post` is the last REGULAR-SESSION CLOSE printed before the post went out — the number
    the author had in hand. For an intraday post that is the PRIOR session, never the post-day
    close: that price had not happened yet, and anchoring a reading to it would let the outcome
    colour the reading. `px_close` carries the post-day close separately, where the two differ.

    Half-day sessions close at 13:00 ET and are not modelled. On those few afternoons the anchor
    falls back one session — it is never a price that had not printed, and `px_session` always
    names the session it came from, so the fallback is visible rather than silent.

    Returns {} when the ticker has no bars (8 of the account's symbols are delisted or renamed) or
    the post predates them — a blank cell, never a guessed price.
    """
    if not bars or not posted_at:
        return {}
    try:
        posted = datetime.fromisoformat(posted_at).astimezone(_ET)
    except ValueError:
        return {}
    # the post-day close counts as "seen" only once it has printed
    cutoff = posted.date() if posted.hour >= _CLOSE_HOUR else posted.date() - timedelta(days=1)
    days = [b[0] for b in bars]
    i = bisect_right(days, cutoff) - 1
    if i < 0:
        return {}
    out: dict[str, Any] = {"px_at_post": round(bars[i][4], 4), "px_session": days[i].isoformat()}
    j = bisect_right(days, posted.date()) - 1
    if j > i:                      # the post's own session closed after the post went out
        out["px_close"] = round(bars[j][4], 4)
    return out


def _rows(handle: str) -> list[dict[str, Any]]:
    d = account_dir(handle)
    labels: dict[str, Any] = json.loads((d / "labels.json").read_text())
    was_p = d / "labels.machine.json"
    was_all: dict[str, Any] = json.loads(was_p.read_text()) if was_p.is_file() else {}
    posts: dict[str, dict[str, Any]] = {}
    for f in sorted((d / "posts").glob("*.json")):
        for p in json.loads(f.read_text()):
            posts[str(p["id"])] = p
    res_p = d / "results.jsonl"
    results: dict[tuple[str, str], dict[str, Any]] = {}
    if res_p.is_file():
        for line in jsonl_lines(res_p.read_text()):
            if line.strip():
                r = json.loads(line)
                results[(str(r["tweet_id"]), r["ticker"])] = r
    audit = load_audit(handle)
    bars_of: dict[str, list[tuple[date, float, float, float, float, float]]] = {}

    rows: list[dict[str, Any]] = []
    for key, cur in labels.items():
        tid, _, tkr = key.partition("|")
        post = posts.get(tid)
        if post is None:
            continue
        rd = audit.get(tid)
        llm = next((t for t in rd.tickers if t.ticker.upper() == tkr.upper()), None) if rd else None
        res = results.get((tid, tkr))
        was = was_all.get(key, cur)
        row: dict[str, Any] = {
            "tweet_id": tid, "date": post.get("d"), "time": str(post.get("t"))[11:16],
            "ticker": tkr, "text": post.get("txt") or "", "url": post.get("url"),
            "media": " ".join(m for m, on in (("VIDEO", post.get("v")), ("PHOTO", post.get("p")),
                                              ("QUOTE", post.get("q"))) if on),
            "likes": post.get("lk"), "views": post.get("vw"),
            "n_tickers": len(post.get("tk") or []),
            "was_class": was.get("post_class"), "was_bias": was.get("bias"),
            "was_action": was.get("action"), "was_target": was.get("target"),
            "was_target_type": was.get("target_type"), "was_hlo": was.get("hlo"),
            "was_hhi": was.get("hhi"), "was_spec": was.get("spec"),
            "src": cur.get("src"), "now_class": cur.get("post_class"), "now_bias": cur.get("bias"),
            "now_action": cur.get("action"), "now_target": cur.get("target"),
            "now_target_type": cur.get("target_type"), "now_hlo": cur.get("hlo"),
            "now_hhi": cur.get("hhi"), "now_spec": cur.get("spec"),
            "now_conditional": bool(cur.get("is_conditional")),
            "now_retrospective": bool(cur.get("is_retrospective")),
        }
        if tkr not in bars_of:
            bars_of[tkr] = load_bars(handle, tkr)
        row.update(_price_context(bars_of[tkr], str(post.get("t") or "")))
        if rd is not None and rd.error is None:
            row.update(probability=rd.probability, summary=rd.summary)
        if llm is not None:
            row["why"] = llm.note
        elif rd is not None and rd.error:
            row["why"] = rd.error
        changed = [name for name, a, b in COMPARED if _norm(row.get(a)) != _norm(row.get(b))]
        row["changed_on"] = ", ".join(changed)
        row["changed"] = "YES" if changed else "no"
        if res:
            for col in COLS_SCORE:
                row[col] = res.get(col)
        # SIGNED DISTANCE FROM SPOT — the direction tell, computed once here rather than left for
        # the eye to do against a target three bands away.
        anchor, tgt = row.get("px_at_post"), row.get("target_px")
        if isinstance(anchor, float) and isinstance(tgt, float) and anchor > 0:
            row["target_gap"] = round((tgt - anchor) / anchor, 4)
        row["flags"] = _flags(cur, res)
        row["priority"] = _priority(row.get("was_bias"), row.get("now_bias"),
                                    row.get("now_class"), changed,
                                    (res or {}).get("target_status"))
        # THE FINAL BAND STARTS AT WHAT THE CORPUS CARRIES TODAY.
        row.update(final_bias=cur.get("bias"), final_action=cur.get("action"),
                   final_target=cur.get("target"), final_target_type=cur.get("target_type"),
                   final_hlo=cur.get("hlo"), final_hhi=cur.get("hhi"), final_spec=cur.get("spec"),
                   final_class=cur.get("post_class"),
                   final_conditional="yes" if cur.get("is_conditional") else "",
                   final_retrospective="yes" if cur.get("is_retrospective") else "",
                   verified="", notes="")
        rows.append(row)
    rows.sort(key=lambda r: (str(r["date"]), str(r["time"]), str(r["ticker"])))
    return rows


def build_sheet(handle: str, out: Path) -> int:
    try:
        from openpyxl import Workbook  # type: ignore[import-untyped]
        from openpyxl.formatting.rule import FormulaRule  # type: ignore[import-untyped]
        from openpyxl.styles import Alignment, Font, PatternFill  # type: ignore[import-untyped]
        from openpyxl.utils import get_column_letter  # type: ignore[import-untyped]
        from openpyxl.worksheet.datavalidation import (  # type: ignore[import-untyped]
            DataValidation,
        )
    except ImportError as exc:  # pragma: no cover - dev-only dependency
        raise RuntimeError("the audit sheet needs `openpyxl` (pip install -e '.[dev]')") from exc

    rows = _rows(handle)
    wb = Workbook()
    ws = wb.active
    ws.title = "audit"
    ws.append(COLS)

    bands = [(COLS_POST, "FFF2F2F2"), (COLS_PRICE, "FFEDF4F7"),
             (COLS_WAS, "FFF3EEFA"), (COLS_NOW, "FFEAF1FB"),
             (COLS_SCORE, "FFEFF7EF"), (["flags", "priority"], "FFFDF3E2"),
             (COLS_FINAL, "FFFFF7CC")]
    band_of = {c: fill for cols, fill in bands for c in cols}
    for i, c in enumerate(COLS, start=1):
        cell = ws.cell(row=1, column=i)
        cell.font = Font(bold=True, size=9)
        cell.fill = PatternFill("solid", fgColor=band_of[c])
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

    for r in rows:
        ws.append([r.get(c) for c in COLS])

    idx = {c: i + 1 for i, c in enumerate(COLS)}
    last = len(rows) + 1
    # the text column is the one you actually read — wide and wrapped; everything else stays narrow
    widths = {"text": 90, "priority": 19, "summary": 46, "why": 40, "notes": 28,
              "changed_on": 22, "flags": 26, "url": 12, "tweet_id": 15}
    for c, i in idx.items():
        ws.column_dimensions[get_column_letter(i)].width = widths.get(c, 11.5)
    for row in ws.iter_rows(min_row=2, max_row=last, min_col=idx["text"], max_col=idx["text"]):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    # prices read as prices, and the gap as a signed percentage — a bare 0.0221 is not a tell
    for col, fmt in (("px_at_post", "0.00"), ("px_close", "0.00"), ("entry", "0.00"),
                     ("exit", "0.00"), ("target_px", "0.00"), ("target_gap", "+0.0%;-0.0%")):
        for row in ws.iter_rows(min_row=2, max_row=last, min_col=idx[col], max_col=idx[col]):
            for cell in row:
                cell.number_format = fmt

    ws.freeze_panes = ws.cell(row=2, column=idx["text"] + 1)   # id/date/ticker/text stay on screen
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLS))}{last}"

    # DROPDOWNS, so a hand-typed tag cannot invent a value the importer will silently drop.
    def dv(col: str, values: list[str], allow_blank: bool = True) -> None:
        v = DataValidation(type="list", formula1='"' + ",".join(values) + '"',
                           allow_blank=allow_blank, showDropDown=False)
        v.error = "Pick a listed value — the importer only accepts these."
        ws.add_data_validation(v)
        v.add(f"{get_column_letter(idx[col])}2:{get_column_letter(idx[col])}{last}")

    dv("final_bias", BIASES)
    dv("final_action", ACTIONS)
    dv("final_target_type", TARGET_TYPES)
    dv("final_spec", SPECS)
    dv("final_class", CLASSES)
    for c in ("final_conditional", "final_retrospective", "verified"):
        dv(c, ["yes", "no"])

    # DISAGREEMENT IS THE POINT OF THE SHEET, so it is visible without sorting: the whole row tints
    # where the two readers differ, and the bias pair tints harder because a wrong bias inverts the
    # result rather than merely mislabelling it.
    a_col = get_column_letter(idx["changed"])
    rng = f"A2:{get_column_letter(len(COLS))}{last}"
    ws.conditional_formatting.add(rng, FormulaRule(
        formula=[f'${a_col}2="YES"'], stopIfTrue=False,
        fill=PatternFill("solid", fgColor="FFFDEDED")))
    bias_rng = (f"{get_column_letter(idx['was_bias'])}2:"
                f"{get_column_letter(idx['now_bias'])}{last}")
    d_col = get_column_letter(idx["changed_on"])
    ws.conditional_formatting.add(bias_rng, FormulaRule(
        formula=[f'ISNUMBER(SEARCH("bias",${d_col}2))'],
        stopIfTrue=False, fill=PatternFill("solid", fgColor="FFF8CBAD")))

    # a second sheet the operator never edits: what the bands mean and how to get the work back in
    doc = wb.create_sheet("how to use")
    for line in [
        ["This workbook is a LOCAL audit tool. Nothing reads it until you import it back."],
        [],
        ["Bands, left to right:"],
        ["  what he POSTED", "identity, text, media, engagement"],
        ["  WHERE IT WAS TRADING", "px_at_post — the last close printed BEFORE the post went out"],
        ["  what it WAS", "was_* — the original machine labeller, before the adoption"],
        ["  what it is NOW", "now_* — the adopted second reading; `why` is its reasoning"],
        ["  what HAPPENED", "the scored outcome from `vinci calls score`"],
        ["  what YOU decide", "final_* — pre-filled with NOW; change what is wrong"],
        [],
        ["px_at_post is the anchor that makes a bare number in the text readable: '$530' is a"],
        ["bullish call above it and a bearish one below. px_session names the session that close"],
        ["came from; px_close is the post-day close where the post landed before it."],
        ["target_gap is the signed distance from px_at_post to the target the scorer used."],
        [],
        ["src says who wrote the current tag:"],
        ["  hand", "a person read the post — 83 rows, the only ground truth there is"],
        ["  llm",
         "the adopted second reading — 77% on bias against those 83, vs the machine's ~55%"],
        ["  machine", "the original labeller, where nothing replaced it"],
        [],
        ["changed = YES means the adoption moved this row; changed_on names the fields."],
        ["A moved BIAS inverts the sign of the return, so that pair tints harder."],
        ["flags carries the same review reasons the tape's queue uses."],
        [],
        ["priority ranks rows by what it costs if the tag is wrong — sort by it and work down:"],
        ["  1 direction flipped", "bullish <-> bearish. Inverts the return."],
        ["  2 target unreadable",
         "no target could be read, or it fights the bias. 'Did he hit it' is unanswerable."],
        ["  3 call or not", "a direction was added or removed. Decides whether it is scored."],
        ["  4 not a call", "a flow list / promo / noise. Bulk: verify and move on."],
        ["  5 detail moved", "target, horizon or spec changed; direction intact."],
        ["  6 unchanged", "the machine and the second reading already agreed."],
        [],
        ["Set `verified` to yes on rows you have checked. Then:"],
        ["  vinci calls import-sheet <this file>"],
        ["  vinci calls score"],
        [],
        ["Only rows marked verified=yes are imported, and they land as src=hand."],
        ["Everything else is left exactly as it is."],
    ]:
        doc.append(line)
    doc.column_dimensions["A"].width = 34
    doc.column_dimensions["B"].width = 76

    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return len(rows)


def _q(iso: str) -> str:
    return f"{iso[:4]}Q{(int(iso[5:7]) - 1) // 3 + 1}"


def _int_or_none(v: Any) -> int | None:
    if v is None or str(v).strip() == "":
        return None
    try:
        f = float(str(v).strip())
    except ValueError as exc:
        raise SheetError(f"horizon must be a whole number of trading days, got {v!r}") from exc
    if f != int(f):
        raise SheetError(f"horizon must be a whole number of trading days, got {v!r}")
    return int(f)


class SheetError(RuntimeError):
    """The workbook cannot be read back — raised before anything is merged."""


def read_sheet(path: Path) -> list[dict[str, Any]]:
    """Rows the operator marked `verified`, in gold_labels shape.

    ONLY VERIFIED ROWS COME BACK. The final columns are pre-filled with the current tag, so an
    untouched row would otherwise re-import itself as a HAND label — silently promoting 8,185
    machine guesses to ground truth, which is the worst thing this tool could do. `verified` is the
    operator saying "I read this one".
    """
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - dev-only dependency
        raise SheetError("reading the audit sheet needs `openpyxl`") from exc

    ws = load_workbook(path, data_only=True)["audit"]
    head = [c.value for c in ws[1]]
    missing = [c for c in ("tweet_id", "ticker", "date", "verified", "final_bias") if c not in head]
    if missing:
        raise SheetError(f"{path.name}: not an audit workbook — missing {missing}")
    ix = {name: i for i, name in enumerate(head)}

    out: list[dict[str, Any]] = []
    for n, raw in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        def g(c: str, _r: tuple[Any, ...] = raw) -> Any:
            return _r[ix[c]] if c in ix else None

        if str(g("verified") or "").strip().lower() not in ("yes", "y", "true", "1"):
            continue
        tid, tkr = g("tweet_id"), g("ticker")
        if not tid or not tkr:
            raise SheetError(f"{path.name} row {n}: verified but missing tweet_id/ticker")
        date = str(g("date") or "")[:10]
        try:
            row = {
                "tweet_id": str(tid), "date": date, "quarter": _q(date) if date else None,
                "ticker": str(tkr), "bias": g("final_bias"), "action": g("final_action") or "none",
                "target": g("final_target"), "target_type": g("final_target_type") or "none",
                "horizon_lo_days": _int_or_none(g("final_hlo")),
                "horizon_hi_days": _int_or_none(g("final_hhi")),
                "is_conditional": str(g("final_conditional") or "").lower() == "yes",
                "is_retrospective": str(g("final_retrospective") or "").lower() == "yes",
                "specificity": g("final_spec"), "post_class": g("final_class"),
                "has_video": "VIDEO" in str(g("media") or ""),
                "labeller": "hand", "text": g("text"),
                "note": g("notes") or None,
            }
        except SheetError as exc:
            raise SheetError(f"{path.name} row {n} ({tid}|{tkr}): {exc}") from exc
        if row["bias"] not in (*BIASES, None):
            raise SheetError(f"{path.name} row {n}: bias {row['bias']!r} is not a listed value")
        out.append(row)
    return out
