"""The impact report as the PR-body section ``## Cross-setup validation (deterministic)``.

Every list prints in full or says ``showing k of n`` (CLAUDE.md: a truncated output prints its own
truncation); the JSON beside it always holds every row. Every count states its population.
"""
from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from vinci.impact.values import cut as _cut
from vinci.impact.values import show

HEADING = "## Cross-setup validation (deterministic)"
PANEL = ("BURL", "CNXC", "LLY", "MCK", "ROST", "SMPL")


def _cell(v: Any, limit: int = 90) -> str:
    """A value for a table cell. A whole Sourced field (one side holds it, the other does not)
    shows its ``value``, and its status when that is not PRESENT."""
    if isinstance(v, dict) and "value" in v and "status" in v:
        tail = "" if v["status"] == "present" else f" [{v['status']}]"
        return _cell(v["value"], limit) + tail
    text = v if isinstance(v, str) and v in ("ABSENT",) else show(v, limit)
    return text.replace("|", "\\|")


def _some(items: Sequence[Any], k: int) -> tuple[Sequence[Any], str]:
    if len(items) <= k:
        return items, ""
    return items[:k], f" (showing {k} of {len(items)}; every one is in the JSON)"


def _names(items: Sequence[str], k: int = 40) -> str:
    shown, note = _some(list(items), k)
    return (", ".join(shown) or "none") + note


def stamp_lines(r: dict[str, Any], json_name: str) -> list[str]:
    s = r["stamp"]
    ident = s["diff_identity"]
    pid = ident["patch_id"] or "none (no behaviour path changes)"
    lines = [
        f"`python -m vinci.impact run --base {s['base']['ref']} --head {s['head']['ref']}` · $0 "
        f"(no model call) · {s['date']} · wall {r.get('wall_seconds')} s",
        "",
        f"- **Base** `{s['base']['sha']}` (the merge base of `{s['base']['ref']}`"
        + ("" if s["base"].get("tip", s["base"]["sha"]) == s["base"]["sha"] else
           f", whose tip `{str(s['base'].get('tip'))[:10]}` the branch has not merged")
        + f" and head) · **head** `{s['head']['sha']}`",
        f"- **Diff identity:** `patch-id {pid}` over {len(ident['paths'])} behaviour path(s) "
        f"(every path but {', '.join(ident['excluded'])}): {_names(ident['paths'], 30)}",
    ]
    inp = s.get("inputs")
    if inp:
        store = inp["store"]
        content = store.get("content") or {}
        n_ciq = sum(len(v) for v in inp["ciq"].values())
        lines.append(
            f"- **Inputs:** committed data at head `{inp['data_ref'][:10]}` ({len(inp['pages'])} "
            f"pages); CIQ `{inp['ciq_root']}` {n_ciq} export(s) on {len(inp['ciq'])} page(s), "
            f"each by sha256 in the JSON (moved during the run: "
            f"{_names(inp.get('ciq_moved_during_run') or [])}); price store from "
            f"`{store['source']}` (file `{store['file_sha256'][:12]}`, content "
            f"`{str(content.get('content_sha256', '?'))[:12]}` over {content.get('rows', '?')} "
            f"rows, frontier {store['frontier']}; written by a build: "
            f"{_names(store.get('written_by') or [])}); HTTP cache `{inp['cache_root']}` served "
            "FROZEN (every cached response whatever its age; a miss fetched once, named below)")
    lines.append(
        f"- **Valid after a re-sync** while `python -m vinci.impact verify --report {json_name}` "
        "passes: the same patch-id, and main touching none of the PR's own paths since the "
        "stamped base. Otherwise re-run.")
    return lines


def fail_first_lines(ff: dict[str, Any], k: int, code_changed: bool = True) -> list[str]:
    cases = ff.get("cases") or []
    if ff.get("skipped"):
        return ["### 1. Fail first — NOT RUN (`--skip-fail-first`)", "",
                "This run asks what the PR moved, not whether its own tests fail first."]
    if not ff.get("tests"):
        return ["### 1. Fail first — the PR changes no test file", "",
                ("No test to run. A CODE fix without a test that fails first is not done "
                 "(CLAUDE.md)." if code_changed else
                 "No test to run, and the PR changes no code (`vinci/`, or browser-run source "
                 "under `frontend/`).")]
    first = [c for c in cases if c["base"]["outcome"] in ("failed", "error", "absent")
             and c["head"]["outcome"] == "passed"]
    both = [c for c in cases if c["base"]["outcome"] == "passed"
            and c["head"]["outcome"] == "passed"]
    red = [c for c in cases if c["head"]["outcome"] in ("failed", "error")]
    skip = [c for c in cases if "skipped" in (c["base"]["outcome"], c["head"]["outcome"])]
    lines = [f"### 1. Fail first — {len(first)} of {len(cases)} test(s) fail on base code and "
             f"pass on head code", "",
             f"Head's {len(ff['tests'])} changed test file(s), run with base's `vinci/` and with "
             f"head's (both in head's tree, `-m \"not network\"`, no git-ignored data, "
             f"{ff.get('seconds')} s): {_names(ff['tests'])}. Pass at both: {len(both)} (a "
             f"negative pin, or not a fail-first pin); **fail at head: {len(red)}**; skipped: "
             f"{len(skip)}.", ""]
    told = [c for c in cases if c not in both]
    lines += [f"Every node whose outcome is not a pass at both refs ({len(told)}; the {len(both)} "
              "that pass at both are listed in the JSON):", "",
              "| node id | base code | head code |", "|---|---|---|"]
    rows, note = _some(told, k)
    for c in rows:
        b, h = c["base"], c["head"]
        bt = b["outcome"].upper() + (f" at `{b['where']}` — {b['message']}" if b["outcome"]
                                     in ("failed", "error") else
                                     f" — {b['message']}" if b["outcome"] == "skipped" else "")
        ht = h["outcome"].upper() + (f" at `{h['where']}` — {h['message']}" if h["outcome"]
                                     in ("failed", "error") else "")
        lines.append(f"| `{c['node']}` | {bt.replace('|', '/')} | {ht.replace('|', '/')} |")
    if note:
        lines.append(f"\n{note.strip()}")
    return lines


def pages_lines(r: dict[str, Any], k: int) -> list[str]:
    if not r["pages"].get("built", True):
        return ["### 2. Pages — not built: the same by construction", "",
                "No path the PR changes is in the static import closure of the page builder, "
                "its render or its synthesis capture (`run.PAGE_ROOTS`, at either ref), and it "
                "changes no committed input (`data/`, `scenarios/`), the capture child or a "
                "dynamically loaded package. `--no-shortcut` builds them anyway."]
    res = r["pages"]["results"]
    compared = [p for p in res if p["status"] not in ("not compared", "noise")]
    moving = [p for p in compared if p["status"] == "moves"]
    moves = [(p["ticker"], m) for p in moving for m in p["moves"]]
    lines = [f"### 2. Pages — built {len(compared)} of {len(res)}; {len(moving)} of "
             f"{len(compared)} move ({len(moves)} field change(s))", "",
             f"Each committed page built at $0 (`prespend.mechanical_build`, no LLM phase) with "
             f"base's code and with head's, from the same inputs; {r['pages']['workers']} "
             f"workers, {r['pages']['seconds']} s. Compared leaf by leaf, list members matched by "
             "identity (`vinci.impact.values`); the build's clock (`assembled_at`, "
             "`computed_at`) and the input record are not compared."]
    again = [p["ticker"] for p in res if p.get("retried")]
    if again:
        still = [p["ticker"] for p in res if (p.get("retried") or {}).get("still")]
        lines += ["", f"Re-built once after a transcript failed to convert on ONE side (the "
                      f"machine, not the code): {_names(again)}; still one-sided, so set "
                      f"apart as run noise and not counted: {_names(still)}"]
    days = [p for p in res if p.get("realigned")]
    if days:
        still = [p["ticker"] for p in days if p["realigned"]["still"]]
        lines += ["", f"Re-built so both sides were built within one UTC day — a build can "
                      f"stamp its day on the page and in its synthesis request: "
                      f"{_names([p['ticker'] for p in days])}; still on two days, so set apart "
                      f"as run noise and not counted: {_names(still)}"]
    refused = [p for p in res if p["status"] == "not compared"]
    if refused:
        lines += ["", f"**Not built at a side, so not compared ({len(refused)}) — a "
                      f"\"0 move\" says nothing about these:**"]
        for p in refused:
            errs = "; ".join(f"{side}: {e.get('build')}" for side, e in p["errors"].items()
                             if e.get("build"))
            if "no price history in the store" in errs:
                errs += (" — `python -m vinci.impact store` prices every page from the cache "
                         "at $0")
            lines.append(f"- {p['ticker']} — {_cut(errs, 400)}")
    differ = [p for p in res if p.get("inputs_differ")]
    live = sorted({u for p in res for side in ("base", "head") for u in p["live"][side]})
    lines += ["", f"Inputs: {sum(p['reads']['head'] for p in res)} responses read at head; "
                  f"a response read at both refs with different bytes on "
                  f"{len(differ)} page(s): {_names([p['ticker'] for p in differ])}; fetched live "
                  f"(not in the cache): {len(live)}" + (f" — {_names(live, 10)}" if live else "")]
    vm = [(p["ticker"], m) for p in compared for m in p.get("version_moves", [])]
    if vm:
        pairs = sorted({(m["base"], m["head"]) for _, m in vm})
        lines.append(f"Extraction version moves on {len({t for t, _ in vm})} page(s), not "
                     f"counted as a move: " + "; ".join(f"{a} → {b}" for a, b in pairs))
    lines += family_lines(compared, r.get("census") or [], k)
    if moves:
        lines += ["", "| page | field | base → head | source_ref |", "|---|---|---|---|"]
        shown, note = _some(moves, k)
        for t, m in shown:
            lines.append(f"| {t} | `{m['path']}` | {_cell(m['base'])} → {_cell(m['head'])} | "
                         f"{_cell(m['source_ref'] or '—', 70)} |")
        if note:
            lines.append(f"\n{note.strip()}")
    return lines


def family_lines(pages: Sequence[dict[str, Any]], census: Sequence[str], k: int) -> list[str]:
    """Each list family's population over the compared pages, both sides, and its moved members:
    every family with a move, and every family a ``census`` substring names."""
    tot: dict[str, dict[str, Any]] = {}
    for p in pages:
        for f, n in (p.get("families") or {}).items():
            t = tot.setdefault(f, {"base": 0, "head": 0, "moved": 0, "pages": []})
            t["base"] += n["base"]
            t["head"] += n["head"]
            t["moved"] += n["moved"]
            if n["moved"]:
                t["pages"].append(p["ticker"])
    rows = [(f, t) for f, t in sorted(tot.items())
            if t["moved"] or any(c in f for c in census)]
    if not rows:
        return []
    shown, note = _some(rows, k)
    out = ["", f"List families (members on all compared pages; a member moves when any field "
               f"inside it does){note}:", "",
           "| family | members at base | at head | moved | pages |", "|---|---|---|---|---|"]
    out += [f"| `{f}` | {t['base']} | {t['head']} | {t['moved']} | {_names(t['pages'], 12)} |"
            for f, t in shown]
    return out


def requests_lines(r: dict[str, Any]) -> list[str]:
    if not r["pages"].get("built", True):
        return ["### 3. Synthesis requests — the same by construction (part 2)", "",
                "Row-53 panel check: **not owed** — no changed path reaches the synthesis "
                "request (part 2's closure includes `vinci.dossier.synthesis`)."]
    res = r["pages"]["results"]
    reqs = [(p["ticker"], p.get("request") or {}) for p in res]
    compared = [(t, q) for t, q in reqs if q.get("status") == "compared"]
    differ = [(t, q) for t, q in compared if not q["identical"]]
    lines = [f"### 3. Synthesis requests — {len(differ)} of {len(compared)} pages' requests "
             "differ", "",
             "Each side's request captured from its OWN $0 build (the layer marked material as "
             "`assemble_one` marks it; a client that sends nothing; five draws, byte-identical), "
             "compared byte for byte (`replay.wire`), key order included. The covenant digest, "
             "maturity event and transcript drivers the paid build's LLM phases add are absent "
             "on both sides."]
    for t, q in differ:
        u = q.get("user_diff") or {}
        lines.append(f"- **{t}**: sections {', '.join(q.get('sections') or []) or 'none'}; "
                     f"system {'same' if q.get('system_equal') else 'DIFFERS'}; tool schema "
                     f"{'same' if q.get('tools_equal') else 'DIFFERS'}; USER −{u.get('removed')} "
                     f"+{u.get('added')} line(s)"
                     + ("; **KEY ORDER ONLY** — every value is equal and some keys' order "
                        "differs (the tool schema's fields, the top-level arguments or another "
                        "object's): inside a kwarg production sends each side in its own "
                        "order; a reorder of the top-level arguments alone the SDK may send "
                        "alike (`replay.wire` fails safe there)"
                        if q.get("key_order_only") else ""))
    moved = {p["ticker"] for p in res if p["status"] == "moves"}
    unreached = sorted(t for t, q in compared if t in moved and q["identical"])
    if moved:
        lines.append(f"- Pages whose fields move while their request stays byte-identical — "
                     f"their moves reach no synthesis request: {len(unreached)} of "
                     f"{len(moved)} — {_names(unreached)}")
    nc = [(t, q) for t, q in reqs if q.get("status") != "compared"]
    if nc:
        lines.append(f"- not compared ({len(nc)}): {_names([t for t, _ in nc])}")
    pr = r.get("panel_requests") or {}
    if pr.get("status") == "compared":
        dp = [t for t, d in pr["pages"].items() if not d["identical"]]
        lines.append(f"- **Frozen panel** ({', '.join(pr['pages'])}), each page held at its "
                     f"frozen blob and transcripts (`evals compare_requests`): "
                     f"{len(dp)} of {len(pr['pages'])} differ" + (f" — {', '.join(dp)}"
                                                                  if dp else ""))
    else:
        lines.append(f"- **Frozen panel**: NOT COMPARED — {pr.get('why')}")
    panel_built = [t for t, q in differ if t in PANEL]
    panel_frozen = ([t for t, d in pr["pages"].items() if not d["identical"]]
                    if pr.get("status") == "compared" else [])
    owed = sorted(set(panel_built) | set(panel_frozen))
    outside = [t for t, _ in differ if t not in PANEL]
    # a move confined to the FACTS section (the mechanical layer the page is built from), with
    # the system prompt and the tool schema unchanged and the frozen replay identical, is a
    # change in what the page states, not in the prompt: §n names prompt text and the words the
    # layer writes, and whether a value correction needs the panel too is the operator's ruling
    facts_only = (pr.get("status") == "compared" and not panel_frozen and all(
        set(q.get("sections") or []) <= {"facts"} and q.get("system_equal")
        and q.get("tools_equal") and not q.get("other_kwargs") for t, q in differ if t in PANEL))
    if owed and facts_only:
        verdict = (f"**ASK THE OPERATOR** — the request moves on panel page(s) "
                   f"{', '.join(owed)} in its FACTS section only (the values the $0 build "
                   "writes; system prompt, tool schema and digests unchanged; the frozen replay "
                   "identical). RUNBOOKS §n covers prompt text and the layer's words; whether a "
                   "change of values needs the row-53 panel check is a ruling, not a rule")
    elif owed:
        verdict = (f"**OWED** — the request moves on panel page(s) {', '.join(owed)}: a STATE "
                   "row-53 panel check (RUNBOOKS §n) before this ships")
    elif pr.get("status") != "compared":
        verdict = "**UNDECIDED** — the frozen panel could not be replayed (above)"
    else:
        verdict = ("**not owed** — every panel page's request is byte-identical at both refs, "
                   "so the panel check would draw one prompt twice")
        if outside:
            verdict += (f"; the request moves OFF the panel on {', '.join(outside)} — measuring "
                        "it needs target pages (`register --ticker`), the operator's call")
    lines += ["", f"Row-53 panel check: {verdict}."]
    return lines


def rendered_lines(r: dict[str, Any], k: int) -> list[str]:
    res = r["pages"]["results"]
    com = [p for p in res if "committed_md" in p]
    com_moved = [p for p in com if not p["committed_md"]["identical"]]
    blt = [p for p in res if "built_md" in p]
    blt_moved = [p for p in blt if not p["built_md"]["identical"]]
    fe = r["frontend"]
    n_fe = len(fe["differ"]) + len(fe["only_base"]) + len(fe["only_head"])
    lines = [f"### 4. Rendered surface — {len(com_moved)} of {len(com)} committed pages "
             f"re-render differently; {n_fe} frontend file(s) differ", "",
             f"- **Committed JSON re-rendered** by each side's code (`render_markdown`): "
             f"{_names([p['ticker'] for p in com_moved])}",
             f"- **The $0 build's page rendered** by each side's code: "
             f"{len(blt_moved)} of {len(blt)} differ — {_names([p['ticker'] for p in blt_moved])}"
             + (f" (beyond the extraction-version lines, which move on "
                f"{sum(1 for p in blt if p['built_md'].get('version_lines'))} page(s); the "
                "assembly instant is the build's clock)" if blt else ""),
             f"- **`frontend/build.py`** of each side over the data ref with each side's renders "
             f"({fe['files']} files): differ {_names(fe['differ'])}; only at base "
             f"{_names(fe['only_base'])}; only at head {_names(fe['only_head'])}",
             f"- Frontend files the PR edits itself: {_names(fe['pr_edits'])}"]
    src = fe.get("source_edits") or []
    if src:
        lines.append(f"- **Browser-run source the PR changes ({len(src)}): {_names(src)}.** This "
                     "check runs no JavaScript, so what these change on the served page is NOT "
                     "measured here: a browser preview of the committed pages at both refs is "
                     "owed (CLAUDE.md, PREVIEW RULE)")
    stale = [p["ticker"] for p in res if (p.get("committed_md_matches") or {}).get("head")
             is False]
    caused = [p["ticker"] for p in res if (p.get("committed_md_matches") or {}).get("head")
              is False and (p.get("committed_md_matches") or {}).get("base") is True]
    lines.append(f"- Committed `dossier.md` not what head's code renders from its JSON: "
                 f"{len(stale)} — {_names(stale)}; of them, what BASE's code renders "
                 f"(the re-render this PR owes): {_names(caused)}")
    for label, group, key in (("committed JSON", com_moved, "committed_md"),
                              ("$0 build", blt_moved, "built_md")):
        for p in group:
            d = p[key]
            shown, note = _some(d["lines"], k)
            lines += ["", f"<details><summary>{p['ticker']} ({label}): −{d['removed']} "
                          f"+{d['added']} line(s){note}</summary>", "", "```diff",
                      *(_cut(ln, 400) for ln in shown), "```", "</details>"]
    return lines


def downstream_lines(r: dict[str, Any], k: int) -> list[str]:
    d = r["downstream"]
    lines = [f"### 5. Downstream readers — {len(d['changed_modules'])} changed module(s)", ""]
    for m, imp in d["importers"].items():
        lines.append(f"- `{m}`: imported directly by {len(imp['direct'])} — "
                     f"{_names(imp['direct'], k)}; directly or through others by "
                     f"{len(imp['transitive'])} — {_names(imp['transitive'], 30)}")
    lines += ["", "| consumer | reached by (static import closure) | result |", "|---|---|---|"]
    for row in d["consumers"]:
        res = row["result"]
        if res["status"] == "compared":
            pr = res.get("produced", {}).get("head", {})
            made = (f" (exit {res['exit']['head']}; stdout {pr.get('stdout_lines')} line(s); "
                    f"{pr.get('files')} output file(s), {pr.get('bytes')} bytes)")
            if not (pr.get("stdout_lines") or pr.get("files")):
                made += " — PRODUCED NOTHING, so the comparison shows nothing"
            text = ("IDENTICAL at both refs" + made if res["identical"] else
                    f"DIFFERS — exit {res['exit']['base']}→{res['exit']['head']}; stdout "
                    f"−{res['stdout']['removed']} +{res['stdout']['added']}; files: "
                    f"{_names(list(res['files']))}")
        elif res["status"] == "see part 4":
            text = "see part 4"
        else:
            text = res["status"].upper() + (f" — {res['why']}" if res.get("why") else "")
        lines.append(f"| {row['name']} | {_names(row['reached_by'], 8)} | {text} |")
    lines += ["", "A dynamic import is invisible to the static graph (`vinci.impact.graph`)."]
    return lines


#: A local path names the user and the session, and the section is pasted into a PUBLIC PR body.
_LOCAL = re.compile(r"(?:/private)?/(?:tmp|var/folders)/[^\s'\"`)|]+|/Users/[^/\s]+")


def scrub(text: str, run_dir: str | None = None) -> str:
    """Every local path out of ``text``: the run folder as ``<run>``, any other as ``<local>``."""
    if run_dir:
        text = text.replace(run_dir, "<run>")
    return _LOCAL.sub("<local>", text)


def markdown(r: dict[str, Any], *, json_name: str, k: int = 120,
             run_dir: str | None = None) -> str:
    return scrub(_markdown(r, json_name=json_name, k=k), run_dir)


def _markdown(r: dict[str, Any], *, json_name: str, k: int) -> str:
    lines = [HEADING, "", *stamp_lines(r, json_name), ""]
    if r.get("shortcut"):
        lines += [f"**Nothing moves:** {r['shortcut']}.", ""]
        data = [p for p in r["stamp"]["diff_identity"]["paths"]
                if p.startswith(("data/", "scenarios/", "frontend/"))]
        if data:
            lines += [f"The PR changes {len(data)} committed input or artifact path(s) "
                      f"({_names(data, 20)}): one code on one set of inputs cannot differ "
                      "between the sides, so their effect is the PR's own committed diff, not a "
                      "code effect this section measures.", ""]
        lines += [*fail_first_lines(r["fail_first"], k, code_changed=False), ""]
        lines += ["### 2–5. Pages, requests, rendered surface, downstream readers — the same by "
                  "construction (above)"]
        return "\n".join(lines) + "\n"
    for part in (fail_first_lines(r["fail_first"], k), pages_lines(r, k), requests_lines(r),
                 rendered_lines(r, 40), downstream_lines(r, k)):
        lines += [*part, ""]
    return "\n".join(lines)
