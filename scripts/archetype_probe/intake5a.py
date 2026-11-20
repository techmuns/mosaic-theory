"""5a item 3: what intake does today for each out-of-scope kind — a bank (MTB), a pre-revenue
biotech (PCVX), BRK and an MLP (EPD). MEASURE ONLY.

The paid command's gate sequence, in `cli._cmd_dossier`'s order, run as functions so nothing can
reach a model client: (1) `assemble.load_finalists` (the candidate record or the maintenance route:
follow / committed page / underwrite), (2) `coverage_roster.covered_pages`, (3)
`coverage_roster.require_buildable`. In the CLI the model client is constructed right after (3).

STATE A — main as it is: a scratch COPY of the committed data dir (followed.json, the roster,
watch_defects.json, snapshots, dossiers), nothing added. STATE B — after the operator's two intake
steps (RUNBOOKS §i 1 + 1b): the same copy with a follow entry and an intake line per name. What
the build itself does in state B is build5a.py's run on the same names (the scratch data dir)."""

from __future__ import annotations

import datetime as dt
import json
import shutil
from typing import Any

from probe_common import OUT, SCRATCH, WT, head_sha

from vinci.config import Config

NAMES = {
    "MTB": "bank (SIC 6022)",
    "PCVX": "pre-revenue biotech (SIC 2836)",
    "BRK-B": "insurer-led conglomerate, two classes (SIC 6331)",
    "EPD": "MLP (SIC 4922)",
}
MAIN = SCRATCH / "data_main"


def fresh_copy() -> Config:
    if MAIN.exists():
        shutil.rmtree(MAIN)
    MAIN.mkdir()
    for f in (
        "followed.json",
        "coverage_roster.jsonl",
        "watch_defects.json",
        "graph_coverage.json",
    ):
        shutil.copy2(WT / "data" / f, MAIN / f)
    for d in ("snapshots", "dossiers"):
        shutil.copytree(WT / "data" / d, MAIN / d)
    # bars: the scratch store build5a's refresh filled (a checkout's store is never read here);
    # the SEC cache: the probe's scratch cache, linked so state B's record build reads it
    shutil.copy2(SCRATCH / "data" / "vinci.db", MAIN / "vinci.db")
    (MAIN / "cache").symlink_to(SCRATCH / "data" / "cache")
    return Config(data_dir=MAIN)


def gates(cfg: Config, t: str) -> list[dict[str, Any]]:
    from vinci import coverage_roster as roster
    from vinci.dossier.assemble import load_finalists

    out: list[dict[str, Any]] = []
    try:
        fin = load_finalists(cfg, ticker=t)[0]
        out.append(
            {
                "gate": "load_finalists",
                "result": "PASS",
                "detail": f"sleeve {fin.sleeve}; screen_status {str(fin.screen_status)[:160]}",
            }
        )
    except Exception as exc:  # noqa: BLE001
        out.append(
            {
                "gate": "load_finalists",
                "result": "REFUSED",
                "detail": f"{type(exc).__name__}: {exc}",
            }
        )
        return out
    try:
        roster.covered_pages(cfg.data_dir)
        out.append({"gate": "covered_pages", "result": "PASS", "detail": ""})
    except Exception as exc:  # noqa: BLE001
        out.append(
            {
                "gate": "covered_pages",
                "result": "REFUSED",
                "detail": f"{type(exc).__name__}: {exc}"[:600],
            }
        )
        return out
    try:
        m = roster.require_buildable(cfg.data_dir, t)
        out.append({"gate": "require_buildable", "result": "PASS", "detail": m.cite()})
    except Exception as exc:  # noqa: BLE001
        out.append(
            {
                "gate": "require_buildable",
                "result": "REFUSED",
                "detail": f"{type(exc).__name__}: {exc}",
            }
        )
        return out
    out.append(
        {
            "gate": "next in cli._cmd_dossier",
            "result": "MODEL CLIENT CONSTRUCTED",
            "detail": "AnthropicLlmClient.from_config, then assemble_cohort → assemble_one's paid "
            "phases unless its pre-LLM part refuses (build5a.py measures that part)",
        }
    )
    return out


def main() -> None:
    import vinci
    from vinci import coverage_roster as roster

    print("vinci:", vinci.__file__)
    res: dict[str, Any] = {"main_sha": head_sha(), "state_A": {}, "state_B": {}}
    cfg = fresh_copy()
    for t in NAMES:
        res["state_A"][t] = gates(cfg, t)
    # STATE B: the two intake steps, appended in the files' own forms
    follow = json.loads((MAIN / "followed.json").read_text())
    for t, why in NAMES.items():
        follow[t] = {
            "reason": f"5a intake probe, SCRATCH ONLY: {why}",
            "sleeve": "quality",
            "followed_since": "2026-11-19",
        }
    (MAIN / "followed.json").write_text(json.dumps(follow, indent=2) + "\n")
    last = max(m.date for m in roster.read_moves(MAIN))
    day = max(last, dt.date(2026, 11, 19))
    with roster.roster_path(MAIN).open("a") as fh:
        for t in NAMES:
            fh.write(
                roster.render_line(
                    roster.Move(day, t, "intake", "5a probe, scratch only", "scratch (no PR)", None)
                )
                + "\n"
            )
    for t in NAMES:
        res["state_B"][t] = gates(cfg, t)
    (OUT / "intake5a.json").write_text(json.dumps(res, indent=1))
    for st in ("state_A", "state_B"):
        print(f"== {st}")
        for t, gs in res[st].items():
            print(f"  {t}: " + " → ".join(f"{g['gate']} {g['result']}" for g in gs))
            for g in gs:
                if g["result"] != "PASS":
                    print(f"      {g['detail'][:300]}")
    shutil.rmtree(MAIN)
    print("scratch copy removed:", not MAIN.exists())


if __name__ == "__main__":
    main()
