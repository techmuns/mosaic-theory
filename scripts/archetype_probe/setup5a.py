"""5a scratch inputs: the follow list and the coverage roster an operator's intake would write
(RUNBOOKS §i steps 1 and 1b), written ONLY under the scratch data dir. Nothing in a checkout.

BUILD names get a follow entry + an intake line (so the $0 build admits them by the maintenance
route, as a followed name). INTAKE names (MTB, PCVX, BRK-B, EPD) are left OUT of both files here:
intake5a.py measures them in their state today, then in a second scratch dir after the two steps."""

from __future__ import annotations

import datetime as dt
import json

from probe_common import CFG

BUILD = {
    "PLD": "REIT (SIC 6798), co-registrant operating partnership",
    "AWK": "regulated water utility",
    "RIVN": "loss-making automaker",
    "CRWV": "loss-making, capex/lease-heavy, IPO 2025",
    "MORN": "asset manager / data (SIC 6282)",
    "DVN": "reserve-based (E&P)",
    "AQN": "FPI 40-F, US GAAP USD, utility",
    "NBIS": "FPI 20-F, US GAAP USD, transformed 2024",
    "SPGI": "CONTROL: proven path, built EDGAR-only like the rest",
    # intake names (out of scope), STATE B: after the operator's two intake steps
    "MTB": "bank (SIC 6022)",
    "PCVX": "pre-revenue biotech (SIC 2836)",
    "BRK-B": "insurer-led conglomerate, two classes (SIC 6331)",
    "EPD": "MLP (SIC 4922)",
}


def main() -> None:
    from vinci import coverage_roster as roster

    d = CFG.data_dir
    follow = {
        t: {
            "reason": f"5a archetype probe, SCRATCH ONLY: {why} — a $0 deterministic build",
            "sleeve": "quality",
            "followed_since": "2026-11-19",
        }
        for t, why in BUILD.items()
    }
    (d / "followed.json").write_text(json.dumps(follow, indent=2) + "\n")
    lines = [
        roster.render_line(
            roster.Move(
                dt.date(2026, 11, 19),
                t,
                "intake",
                "5a probe, scratch only",
                "scratch (no PR)",
                None,
            )
        )
        for t in BUILD
    ]
    roster.roster_path(d).write_text("\n".join(lines) + "\n")
    print(f"followed.json: {len(follow)} names; roster: {len(lines)} intake lines → {d}")
    print("roster reads back:", {t: m.status for t, m in roster.current(d).items()})


if __name__ == "__main__":
    main()
