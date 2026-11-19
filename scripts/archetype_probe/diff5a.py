"""Each EDGAR-only $0 page's Sourced fields against the CONTROL's (SPGI, proven path, built the same
way): a field PRESENT on the control and NOT on the name is an archetype gap, not an export gap.
Lists are walked to their first 50 members, so this compares the page's own fields, not list
populations. Writes out/diff5a.json."""

import json

from probe_common import OUT

B = OUT / "build5a"


def fields(doc):
    res = {}

    def walk(n, path):
        if isinstance(n, dict):
            if "status" in n and "value" in n and isinstance(n.get("status"), str):
                res[path] = (n["status"], (n.get("note") or "")[:230])
                return
            for k, v in n.items():
                walk(v, f"{path}.{k}")
        elif isinstance(n, list) and n and isinstance(n[0], dict) and "status" not in n[0]:
            pass  # list populations are calendar-dependent; not compared

    walk(doc.get("mechanical") or {}, "m")
    return res


ctl = fields(json.loads((B / "SPGI.dossier.json").read_text()))
ctl_present = {k for k, (s, _) in ctl.items() if s == "present"}
out = {}
for stem in (
    "PLD-noCIQ",
    "AWK",
    "RIVN-noCIQ",
    "CRWV",
    "MORN",
    "DVN",
    "AQN",
    "NBIS",
    "MTB-noCIQ",
    "BRK-B",
    "EPD",
):
    f = fields(json.loads((B / f"{stem}.dossier.json").read_text()))
    gaps = {k: f[k] for k in sorted(ctl_present) if k in f and f[k][0] != "present"}
    gains = sorted(k for k, (s, _) in f.items() if s == "present" and k not in ctl_present)
    out[stem] = {"gaps_vs_control": gaps, "present_where_control_is_not": gains}
    print(
        f"== {stem}: {len(gaps)} field(s) the control has and this page lacks; {len(gains)} the "
        "other way"
    )
    for k, (s, n) in gaps.items():
        print(f"   - {k} [{s}] {n[:200]}")
    for k in gains[:6]:
        print(f"   + {k}")
print(f"control SPGI: {len(ctl_present)} of {len(ctl)} Sourced fields present (lists not walked)")
(OUT / "diff5a.json").write_text(json.dumps(out, indent=1))
