"""The LOCAL AUDIT WORKBOOK — one row per (tweet, ticker), for verifying tags by hand.

NOT A PRODUCT SURFACE. This is an operator tool: a spreadsheet you sort, filter and bulk-edit, then
feed back with `vinci calls import-sheet`. The dashboard stays read-only and knows nothing about it.

WHY A SHEET AT ALL, when the tape exists. The tape is for reading ONE call against its chart. This
is for the other job — walking 8,185 rows, sorting by where two readers disagree, and correcting in
bulk. Different question, different instrument.

THE LAYOUT IS THE ARGUMENT. Four bands, left to right: what he POSTED, what the corpus currently
TAGS it, what a second reader (the LLM) READ, and what actually HAPPENED to the price. Then the
FINAL band you edit. The final columns are PRE-FILLED WITH THE CURRENT TAG, not with the LLM's
reading — the status quo is what you are confirming or overriding, and pre-filling the machine's
second opinion would quietly make it the default answer. Disagreements are coloured so the eye goes
there; nothing is hidden or pre-decided.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vinci.calls.accounts import account_dir
from vinci.calls.audit import ACTIONS, BIASES, CLASSES, SPECS, TARGET_TYPES, load_audit

#: Left band: identity + the post itself. Frozen, so the text stays visible while you scroll right.
COLS_POST = ["tweet_id", "date", "time", "ticker", "text", "url", "media", "likes", "views",
             "n_tickers"]
COLS_CUR = ["src", "cur_class", "cur_bias", "cur_action", "cur_target", "cur_target_type",
            "cur_hlo", "cur_hhi", "cur_spec", "cur_needs_review"]
COLS_LLM = ["llm_class", "llm_bias", "llm_action", "llm_target", "llm_target_type", "llm_hlo",
            "llm_hhi", "llm_spec", "llm_conditional", "llm_retrospective", "llm_probability",
            "llm_summary", "llm_note", "agree", "differs_on"]
COLS_SCORE = ["status", "entry", "entry_date", "exit", "exit_date", "horizon_days",
              "horizon_assumed", "ret", "bench_ret", "excess", "mfe", "mae", "target_px",
              "target_status", "target_hit", "direction_correct"]
COLS_FINAL = ["final_bias", "final_action", "final_target", "final_target_type", "final_hlo",
              "final_hhi", "final_spec", "final_class", "final_conditional",
              "final_retrospective", "verified", "notes"]
COLS = (COLS_POST + COLS_CUR + COLS_LLM + COLS_SCORE + ["flags", "priority"]
        + COLS_FINAL)

#: The fields whose disagreement is worth colouring. Bias first: it is the one that flips the sign
#: of every return, so a wrong bias is not a tagging nit, it is an inverted result.
COMPARED = [("bias", "cur_bias", "llm_bias"), ("target", "cur_target", "llm_target"),
            ("target_type", "cur_target_type", "llm_target_type"), ("spec", "cur_spec", "llm_spec"),
            ("class", "cur_class", "llm_class"), ("action", "cur_action", "llm_action"),
            ("hlo", "cur_hlo", "llm_hlo"), ("hhi", "cur_hhi", "llm_hhi")]

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


#: WHAT TO LOOK AT FIRST. 8,185 rows is not a queue, it is a wall. This ranks each row by how much
#: its disagreement COSTS if the current tag is wrong, so the sheet can be sorted into a day's work:
#:   1 — the two readers give OPPOSITE directions. A wrong bias does not mislabel the row, it
#:       INVERTS the sign of its return, so these are worth more than every other class combined.
#:   2 — one reader sees a call and the other sees none, on a post that could carry one. Decides
#:       whether the row is scored at all.
#:   3 — the post is not a call by both readings (a flow list, promo, noise). A bulk dismissal:
#:       set bias to none, mark verified, move on.
#:   4 — same direction, different target/horizon/spec. Changes whether the target was HIT, not
#:       whether the call was right.
#:   5 — the two readers agree; nothing to decide unless you disagree with both.
_DIRECTIONAL = {"bullish", "bearish"}


def _priority(cur_bias: Any, llm_bias: Any, cls: Any, differs: list[str]) -> str:
    a, b = _norm(cur_bias), _norm(llm_bias)
    if not differs:
        return "5 agree"
    if a in _DIRECTIONAL and b in _DIRECTIONAL and a != b:
        return "1 opposite direction"
    if "bias" in differs and (a in _DIRECTIONAL) != (b in _DIRECTIONAL):
        return "3 not a call" if str(cls) in _NON_SIGNAL else "2 call or not"
    if str(cls) in _NON_SIGNAL:
        return "3 not a call"
    return "4 detail only"


def _rows(handle: str) -> list[dict[str, Any]]:
    d = account_dir(handle)
    labels: dict[str, Any] = json.loads((d / "labels.json").read_text())
    posts: dict[str, dict[str, Any]] = {}
    for f in sorted((d / "posts").glob("*.json")):
        for p in json.loads(f.read_text()):
            posts[str(p["id"])] = p
    res_p = d / "results.jsonl"
    results: dict[tuple[str, str], dict[str, Any]] = {}
    if res_p.is_file():
        for line in res_p.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                results[(str(r["tweet_id"]), r["ticker"])] = r
    audit = load_audit(handle)

    rows: list[dict[str, Any]] = []
    for key, cur in labels.items():
        tid, _, tkr = key.partition("|")
        post = posts.get(tid)
        if post is None:
            continue
        rd = audit.get(tid)
        llm = next((t for t in rd.tickers if t.ticker.upper() == tkr.upper()), None) if rd else None
        res = results.get((tid, tkr))
        row: dict[str, Any] = {
            "tweet_id": tid, "date": post.get("d"), "time": str(post.get("t"))[11:16],
            "ticker": tkr, "text": post.get("txt") or "", "url": post.get("url"),
            "media": " ".join(m for m, on in (("VIDEO", post.get("v")), ("PHOTO", post.get("p")),
                                              ("QUOTE", post.get("q"))) if on),
            "likes": post.get("lk"), "views": post.get("vw"),
            "n_tickers": len(post.get("tk") or []),
            "src": cur.get("src"), "cur_class": cur.get("post_class"), "cur_bias": cur.get("bias"),
            "cur_action": cur.get("action"), "cur_target": cur.get("target"),
            "cur_target_type": cur.get("target_type"), "cur_hlo": cur.get("hlo"),
            "cur_hhi": cur.get("hhi"), "cur_spec": cur.get("spec"),
            "cur_needs_review": bool(cur.get("needs_review")),
        }
        if rd is not None and rd.error is None:
            row.update(llm_class=rd.post_class, llm_conditional=rd.is_conditional,
                       llm_retrospective=rd.is_retrospective, llm_probability=rd.probability,
                       llm_summary=rd.summary)
        if llm is not None:
            row.update(llm_bias=llm.bias, llm_action=llm.action, llm_target=llm.target,
                       llm_target_type=llm.target_type, llm_hlo=llm.horizon_lo_days,
                       llm_hhi=llm.horizon_hi_days, llm_spec=llm.spec, llm_note=llm.note)
            diffs = [name for name, a, b in COMPARED if _norm(row.get(a)) != _norm(row.get(b))]
            row["differs_on"] = ", ".join(diffs)
            row["agree"] = "NO" if diffs else "yes"
            row["priority"] = _priority(row.get("cur_bias"), row.get("llm_bias"),
                                        row.get("cur_class"), diffs)
        elif rd is not None and rd.error:
            row["agree"] = "ERR"
            row["llm_note"] = rd.error
            # unread by the second reader — a human has to make this one alone
            row["priority"] = "2 call or not"
        else:
            row["agree"] = ""            # not audited (yet)
        if res:
            for col in COLS_SCORE:
                row[col] = res.get(col)
        row["flags"] = _flags(cur, res)
        # THE FINAL BAND STARTS AS THE STATUS QUO, never as the LLM's reading.
        row.update(final_bias=cur.get("bias"), final_action=cur.get("action"),
                   final_target=cur.get("target"), final_target_type=cur.get("target_type"),
                   final_hlo=cur.get("hlo"), final_hhi=cur.get("hhi"), final_spec=cur.get("spec"),
                   final_class=cur.get("post_class"), final_conditional="", final_retrospective="",
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

    bands = [(COLS_POST, "FFF2F2F2"), (COLS_CUR, "FFEAF1FB"), (COLS_LLM, "FFF3EEFA"),
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
    widths = {"text": 90, "priority": 19, "llm_summary": 46, "llm_note": 40, "notes": 28,
              "differs_on": 22, "flags": 26, "url": 12, "tweet_id": 15}
    for c, i in idx.items():
        ws.column_dimensions[get_column_letter(i)].width = widths.get(c, 11.5)
    for row in ws.iter_rows(min_row=2, max_row=last, min_col=idx["text"], max_col=idx["text"]):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

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
    a_col = get_column_letter(idx["agree"])
    rng = f"A2:{get_column_letter(len(COLS))}{last}"
    ws.conditional_formatting.add(rng, FormulaRule(
        formula=[f'${a_col}2="NO"'], stopIfTrue=False,
        fill=PatternFill("solid", fgColor="FFFDEDED")))
    bias_rng = (f"{get_column_letter(idx['cur_bias'])}2:"
                f"{get_column_letter(idx['llm_bias'])}{last}")
    d_col = get_column_letter(idx["differs_on"])
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
        ["  what it is TAGGED now", "cur_* — machine unless src says hand"],
        ["  what a SECOND READER read",
         "llm_* — an LLM reading of the same post; PROPOSED, never applied"],
        ["  what HAPPENED", "the scored outcome from `vinci calls score`"],
        ["  what YOU decide", "final_* — pre-filled with the CURRENT tag; change what is wrong"],
        [],
        ["agree = NO means the two readers differ; differs_on names the fields. Rows tint red."],
        ["A wrong BIAS inverts the sign of the return, so that pair tints harder."],
        ["flags carries the same review reasons the tape's queue uses."],
        ["priority ranks rows by what the disagreement COSTS — sort by it and work down:"],
        ["  1 opposite direction",
         "they disagree on the SIGN. A wrong bias inverts the return."],
        ["  2 call or not",
         "one sees a call, the other none. Decides whether the row is scored at all."],
        ["  3 not a call", "a flow list / promo / noise. Bulk: set bias none, verify, move on."],
        ["  4 detail only",
         "same direction, different target or horizon. Changes hit, not right."],
        ["  5 agree", "nothing to decide unless you disagree with both."],
        [],
        ["Set `verified` to yes on rows you have checked. Then:"],
        ["  vinci calls import-sheet <this file>"],
        ["  vinci calls score"],
        [],
        ["Only rows marked verified=yes are imported. Everything else is left exactly as it was."],
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
