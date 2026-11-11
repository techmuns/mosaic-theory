"""THE CUSTOMER COUNT IS A STRUCTURED FIELD, NEVER THE ROSTER'S PIECES (2026-11-09, audit RBC-D1).

The Customers export's roster is stored as a display string capped at 30 rows plus "…(+N more)"
(`ciq_sheets._roster`). Both renderers counted its ";" pieces, so any list over 30 rows printed
"31 mapped client relationship(s)": eight committed pages (AMZN, EPAM, GOOGL, LLY, NFLX, NKE, UBER,
V) for lists of 34 to 726 rows, and NCNO's 31 was right by coincidence. The count now rides beside
the roster as `Concentration.customers_listed`, every row the export lists, and the renderers print
that — or, on a page built before it, no count at all.

The $0 path onto committed pages is `vinci ciq-reread --field customers_listed`
(`vinci.dossier.ciq_reread`), which writes the count only beside a stored roster that the export on
disk reproduces byte for byte.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tests.fixtures.ciq_synthetic import generate as gen
from vinci.dossier import ciq_sheets as cs
from vinci.dossier import render
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.render import render_markdown
from vinci.dossier.schemas import Dossier, SourceStatus, dossier_json

ROOT = Path(__file__).resolve().parents[1]
PAGES = sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))
_COUNT = re.compile(r"^- \*\*Customers:\*\* (\d+) mapped client relationship")


def _long_customers_rtf(n_extra: int) -> str:
    """SYNTHETIC ON THE REAL TYPE: the synthetic Customers view with ``n_extra`` more invented
    rows, read by the real RTF parser — the shape of a list longer than the 30-row cap."""
    rows = "".join(gen._rtf_table_row([f"Invented Counterparty {i:03d} Ltd", "Customer",
                                       "Industrial Machinery", "Company Filing"])
                   for i in range(n_extra))
    base = gen.customers_rtf()
    assert base.endswith(gen.CLOSING_ROW + "}\n")
    # before CIQ's closing line, which stays the view's last (audit RBC-D3)
    return base[:-len(gen.CLOSING_ROW) - 2] + rows + gen.CLOSING_ROW + "}\n"


def _bundle_with(tmp: Path, rtf: str, ticker: str = gen.TICKER) -> CiqBundle:
    folder = tmp / ticker
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / Path(gen.CUSTOMERS_RTF).name
    path.write_text(rtf)
    return CiqBundle.from_files(ticker, [path])


def test_a_roster_over_thirty_rows_counts_its_rows_not_its_pieces(tmp_path: Path) -> None:
    """(+) 3 + 40 rows: the roster keeps 30 and says "(+13 more)"; the count is 43, and the page's
    line prints 43 — the old ";" count read 31."""
    roster, listed = cs.customer_roster(_bundle_with(tmp_path, _long_customers_rtf(40)))
    assert roster.status is SourceStatus.PRESENT and roster.value is not None
    assert roster.value.endswith("; …(+13 more)")
    assert len(roster.value.split(";")) == 31          # the pieces the old renderer counted
    assert listed == 43
    line = render._fact("Customers", roster, lambda v: render._fmt_customers(v, listed))
    assert line.startswith("- **Customers:** 43 mapped client relationship(s)"), line


def test_a_roster_under_the_cap_is_counted_the_same_way(tmp_path: Path) -> None:
    roster, listed = cs.customer_roster(_bundle_with(tmp_path, gen.customers_rtf()))
    assert roster.status is SourceStatus.PRESENT and listed == 3


def test_an_absent_roster_carries_no_count(tmp_path: Path) -> None:
    """(-) No Customers export, or one that states none: no count, never a 0."""
    (tmp_path / "empty").mkdir()
    roster, listed = cs.customer_roster(CiqBundle.from_files(gen.TICKER, []))
    assert roster.status is SourceStatus.MISSING and listed is None
    prior = gen.HERE / gen.PRIOR_CUSTOMERS_RTF
    roster, listed = cs.customer_roster(CiqBundle.from_files(gen.TICKER, [prior]))
    assert roster.status is SourceStatus.UNKNOWN and listed is None


def test_a_page_without_the_count_prints_no_count_never_the_pieces() -> None:
    """(-) A page built before `customers_listed`: the line says the count is not recorded and
    prints no number — never one read back out of the display string."""
    dump = "; ".join(f"Co {i} — Client Services · src: Banks" for i in range(30)) + \
        "; …(+696 more)"
    out = render._fmt_customers(dump)
    assert out.startswith("mapped client relationships (count not recorded on this page)"), out
    assert not re.search(r"\d", out.split(" — ")[0]), out
    assert render._fmt_customers(dump, 726).startswith("726 mapped client relationship(s)")
    # a value that is not a roster dump passes through verbatim, as before
    assert render._fmt_customers("top customer 28% of revenue") == "top customer 28% of revenue"


@pytest.mark.parametrize("jp", PAGES, ids=[p.parent.name for p in PAGES])
def test_every_committed_page_prints_its_structured_count_or_none(jp: Path) -> None:
    """END TO END on every committed page (TEST-LAYER RULE): real JSON → render → the Customers
    line. A page whose roster is a relationship dump prints exactly `customers_listed` — and, where
    the page carries no count, no number at all. This is what reds on the eight pages that printed
    "31" for a list the page itself stores as 34 to 726 rows."""
    page = json.loads(jp.read_text())
    conc = page["mechanical"]["concentration"]
    roster = conc.get("customers") or {}
    md = render_markdown(Dossier.model_validate(page))
    line = next(ln for ln in md.splitlines() if ln.startswith("- **Customers:**"))
    if roster.get("status") != "present" or "src:" not in str(roster.get("value")):
        assert "mapped client relationship" not in line, line
        return
    m = _COUNT.match(line)
    if conc.get("customers_listed") is None:
        assert m is None and "count not recorded on this page" in line, line
    else:
        assert m is not None and int(m.group(1)) == conc["customers_listed"], line
        # the stored roster shows at most 30 rows; a count is never below what it shows
        assert conc["customers_listed"] >= min(30, len(str(roster["value"]).split("; ")))


def test_the_web_page_prints_the_same_structured_count(tmp_path: Path) -> None:
    """The JS twin (`dossier.js` fmtCustomers) on a committed page carrying the count, through the
    real `renderDossier`: the same number, and never the roster's piece count."""
    if not shutil.which("node"):
        pytest.skip("node not available")
    carrying = [p for p in PAGES
                if json.loads(p.read_text())["mechanical"]["concentration"].get(
                    "customers_listed", 0) > 31]
    if not carrying:
        pytest.skip("no committed page carries a count over 31 yet")
    page = json.loads(carrying[0].read_text())
    want = page["mechanical"]["concentration"]["customers_listed"]
    (tmp_path / "page.json").write_text(json.dumps(page))
    dj = (ROOT / "frontend" / "views" / "shared" / "dossier.js").as_uri()
    driver = tmp_path / "driver.mjs"
    driver.write_text(f"""
import {{ readFileSync }} from "node:fs";
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
const {{ renderDossier }} = await import("{dj}");
const page = JSON.parse(readFileSync({json.dumps(str(tmp_path / "page.json"))}, "utf8"));
const html = renderDossier(page, null);
const at = html.indexOf(">Customers<");
console.log(JSON.stringify({{found: at >= 0, row: html.slice(at, at + 300)}}));
""")
    out = json.loads(subprocess.run(["node", str(driver)], capture_output=True, text=True,
                                    check=True).stdout.strip().splitlines()[-1])
    assert out["found"], "the web page drew no Customers fact"
    assert f"{want} mapped client relationship(s)" in out["row"], out["row"]
    assert "31 mapped client relationship(s)" not in out["row"], out["row"]


# --- the $0 writer -------------------------------------------------------------------------------


def _page_with_roster(tmp: Path, ticker: str, roster: Any) -> Path:
    """A committed page (AMZN's) copied to ``tmp`` with its roster replaced — the REAL page type."""
    page = json.loads((ROOT / "data" / "dossiers" / "AMZN" / "dossier.json").read_text())
    page["mechanical"]["concentration"]["customers"] = json.loads(roster.model_dump_json())
    page["mechanical"]["concentration"].pop("customers_listed", None)
    jp = tmp / "dossiers" / ticker / "dossier.json"
    jp.parent.mkdir(parents=True)
    jp.write_text(dossier_json(Dossier.model_validate(page)))
    return jp


def test_the_writer_states_the_count_beside_the_roster_the_export_reproduces(
        tmp_path: Path) -> None:
    """(+) The export on disk re-reads the stored roster byte for byte: the count is written, the
    roster is not touched, the write is recorded as `ciq-reread`, and the page prints the count."""
    from vinci.dossier import ciq_reread

    ciq = tmp_path / "ciq"
    roster, _n = cs.customer_roster(_bundle_with(ciq, _long_customers_rtf(40), "AMZN"))
    jp = _page_with_roster(tmp_path, "AMZN", roster)
    before = json.loads(jp.read_text())["mechanical"]["concentration"]["customers"]
    o = ciq_reread.reread(jp, "customers_listed", ciq)
    assert o.status == "written", o
    doc = json.loads(jp.read_text())
    assert doc["mechanical"]["concentration"]["customers_listed"] == 43
    assert doc["mechanical"]["concentration"]["customers"] == before
    assert doc["layer_refreshes"][-1]["writer"] == "ciq-reread"
    assert doc["layer_refreshes"][-1]["layers"] == ["mechanical.concentration"]
    md = jp.with_name("dossier.md").read_text()
    assert "- **Customers:** 43 mapped client relationship(s)" in md
    again = ciq_reread.reread(jp, "customers_listed", ciq)
    assert again.status == "unchanged", again


def test_the_writer_refuses_an_export_that_is_not_the_pages_own(tmp_path: Path) -> None:
    """(-) The export on disk lists one more row than the stored roster was built from (a newer
    pull): refused, and the page is byte-identical — no count is written beside a roster it does
    not count."""
    from vinci.dossier import ciq_reread

    ciq = tmp_path / "ciq"
    old, _n = cs.customer_roster(_bundle_with(tmp_path / "old", _long_customers_rtf(40), "AMZN"))
    _bundle_with(ciq, _long_customers_rtf(41), "AMZN")
    jp = _page_with_roster(tmp_path, "AMZN", old)
    raw = jp.read_text()
    o = ciq_reread.reread(jp, "customers_listed", ciq)
    assert o.status == "refused" and "not the one this page was built from" in o.detail, o
    assert jp.read_text() == raw


def test_the_count_is_never_sent_to_the_synthesis() -> None:
    """The count is the roster's display twin: the model reads the roster, and every synthesis
    request stays byte-identical to the one built before the field existed (row 53 measures any
    change to it on the panel first) — on a page carrying a count and on one that does not."""
    from vinci.dossier.synthesis import NOT_SENT

    for t in ("AMZN", "BURL"):
        page = json.loads((ROOT / "data" / "dossiers" / t / "dossier.json").read_text())
        mech = Dossier.model_validate(page).mechanical
        assert "customers_listed" not in mech.model_dump(exclude=NOT_SENT)["concentration"], t
