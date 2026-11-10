"""The Customers view's edges: a list cut short is said, a row with its type blank is a row, and
an empty view is named for what it shows (fix request 2, order 5: audits RBC-D3 and V1-O3; order 6:
RBC-D5; 2026-11-10).

* RBC-D3 — a Customers file cut to 40% of its bytes read as the whole list, PRESENT, no note. All
  72 RTF exports on disk end with CIQ's closing line, '*denotes proprietary relationship'; a view
  without it now says the list may be cut short, and its length is not given as a count.
* V1-O3 — a row naming a party, with its relationship type blank, was dropped with no word. It is
  kept, as "type not stated", when it states any other column.
* RBC-D5 — a header with no rows, a "No Data Available" body and an "Entitlement Needed" body all
  read "could not parse the Business-Relationships table", and a real RTF over 4 KB with few words
  was called "an OLE-disguised Word doc". Each now says what the view shows.

The real-export pins read GOOGL's Customers export, read only, writing any cut or edited copy
under pytest's tmp_path; they skip where the licensed folder is absent, as on CI. The constructed
twins run everywhere.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from vinci.config import get_config
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, CiqParseError, read_text
from vinci.dossier.manual_store import LocalFolderStore
from vinci.dossier.schemas import SourceStatus

_NAME = "Zinnober Fixture Works Inc NasdaqGS ZZFX Customers.rtf"
_HEADER = "Customer Name|Relationship Type|Primary Industry|Source"


def _googl_customers() -> Path:
    files = LocalFolderStore.from_config(get_config()).files("GOOGL")
    hit = next((f for f in files if f.name.endswith("Customers.rtf")), None)
    if hit is None:
        pytest.skip("licensed CIQ bundle for GOOGL unavailable (never committed)")
    return hit


def _rtf(tmp: Path, lines: list[str], *, pad: int = 0) -> Path:
    """A real RTF file whose text is `lines`, one paragraph each; `pad` bytes of an ignored
    destination group make it larger without adding a word."""
    body = "\\par\n".join(ln.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
                         for ln in lines)
    junk = "{\\*\\zzpad " + "x" * pad + "}" if pad else ""
    path = tmp / _NAME
    path.write_text("{\\rtf1\\ansi " + junk + body + "\\par\n}", encoding="latin-1")
    return path


def _roster(path: Path) -> tuple[cs.Sourced[str], int | None]:
    return cs.customer_roster(CiqBundle.from_files("ZZFX", [path]))


# --- RBC-D3: a list cut short is said -------------------------------------------------------------


def test_rbc_d3_a_customers_file_cut_short_says_so_and_gives_no_count(tmp_path: Path) -> None:
    """(+) Before: the cut file read PRESENT, its surviving rows as the whole list, no note."""
    src = _googl_customers()
    whole, n = cs.customer_roster(CiqBundle.from_files("GOOGL", [src]))
    assert whole.status is SourceStatus.PRESENT and n and "closing line" not in (whole.note or "")
    cut = tmp_path / src.name
    data = src.read_bytes()
    cut.write_bytes(data[: int(len(data) * 0.4)])
    got, count = cs.customer_roster(CiqBundle.from_files("GOOGL", [cut]))
    assert got.status is SourceStatus.PRESENT and count is None
    assert "does not end with CIQ's closing line" in (got.note or ""), got.note
    assert str(tmp_path) not in (got.note or ""), "a page note never carries a local path"


def test_rbc_d3_twin_the_closing_line_is_the_views_last_line(tmp_path: Path) -> None:
    rows = [_HEADER, "Acme Corp|Customer|Industrials|10-K"]
    whole, n = _roster(_rtf(tmp_path, [*rows, "*denotes proprietary relationship"]))
    assert whole.status is SourceStatus.PRESENT and n == 1 and whole.note is None
    cut, count = _roster(_rtf(tmp_path, rows))
    assert count is None and "may be cut short: 1 row(s) read" in (cut.note or ""), cut.note


# --- V1-O3: a row with its type blank is a row ----------------------------------------------------


def test_v1_o3_a_row_whose_type_is_blank_is_kept_on_a_real_export(tmp_path: Path) -> None:
    """GOOGL's first row with its relationship type removed from the RTF: the row stays, and the
    count with it. Before: the row dropped and the count fell by one."""
    src = _googl_customers()
    want, n = cs.customer_roster(CiqBundle.from_files("GOOGL", [src]))
    text = read_text(src)
    lines = text.splitlines()
    h = next(i for i, ln in enumerate(lines) if "Customer Name" in ln and "Relationship Type" in ln)
    cols = [c.strip() for c in lines[h].split("|")]
    ti = cols.index("Relationship Type")
    first = next(ln for ln in lines[h + 1:] if ln.split("|")[0].strip() and ln.count("|") >= ti)
    name, rtype = first.split("|")[0].strip(), first.split("|")[ti].strip()
    raw = src.read_bytes().decode("latin-1")
    at = raw.index(rtype, raw.index(name))
    edited = tmp_path / src.name
    edited.write_bytes((raw[:at] + raw[at + len(rtype):]).encode("latin-1"))
    got, count = cs.customer_roster(CiqBundle.from_files("GOOGL", [edited]))
    assert count == n, (count, n)

    def row(value: str | None) -> str:   # the row's own segment ('A ← B — type · …' in 5 columns)
        assert value is not None
        return next(seg for seg in value.split("; ") if seg.startswith(name))
    assert row(got.value).split(" · ")[0].endswith("— type not stated"), row(got.value)
    assert row(want.value).split(" · ")[0].endswith(f"— {rtype}"), row(want.value)


def test_v1_o3_twin_a_blank_type_row_reads_as_type_not_stated() -> None:
    rel = cs._relationships("\n".join([_HEADER, "Acme Corp||Industrials|10-K",
                                       "*denotes proprietary relationship"]))
    assert rel is not None
    assert rel.recent == ["Acme Corp — type not stated · Industrials · src: 10-K"]


def test_v1_o3_twin_a_line_naming_nothing_else_is_not_a_row() -> None:
    """(−) The closing line, a sentence, a name with every other column blank: no row."""
    raw = "\n".join([_HEADER, "Acme Corp|Customer|Industrials|10-K", "*denotes proprietary "
                     "relationship", "Some prose about the view", "Orphan Name|||"])
    rel = cs._relationships(raw)
    assert rel is not None and rel.recent == ["Acme Corp — Customer · Industrials · src: 10-K"]


# --- RBC-D5: an empty view is named for what it shows ---------------------------------------------


@pytest.mark.parametrize(("lines", "said"), [
    ([_HEADER, "*denotes proprietary relationship"], "has its header and no rows"),
    (["Zinnober Fixture Works Inc.", "No Data Available"],
     "reads 'No Data Available' — CIQ returned no rows for this view"),
    (["Zinnober Fixture Works Inc.", "Entitlement Needed"],
     "reads 'Entitlement Needed' — the CIQ account is not entitled to this view"),
])
def test_rbc_d5_twin_an_empty_view_is_never_a_parse_failure(
        tmp_path: Path, lines: list[str], said: str) -> None:
    """(+) Before: each read "could not parse the Business-Relationships table"."""
    got, n = _roster(_rtf(tmp_path, lines))
    assert got.status is SourceStatus.UNKNOWN and n is None
    assert said in (got.note or "") and "could not parse" not in (got.note or ""), got.note


def test_rbc_d5_twin_a_file_with_no_table_is_still_unparsed(tmp_path: Path) -> None:
    """(−) A view showing none of those shapes still reads 'could not parse'."""
    got, _n = _roster(_rtf(tmp_path, ["Zinnober Fixture Works Inc.", "nothing tabular here"]))
    assert "could not parse the Business-Relationships table" in (got.note or ""), got.note


def test_rbc_d3_a_file_cut_before_its_table_says_it_may_be_cut(tmp_path: Path) -> None:
    """(+) A view cut before its header parses nothing; without its closing line it read only
    'could not parse', the cut unsaid. (-) With the closing line, no cut is said."""
    head = ["Zinnober Fixture Works Inc (NasdaqGS:ZZFX) > Business Relationships > Customers"]
    got, n = _roster(_rtf(tmp_path, head))
    assert n is None and "could not parse" in (got.note or ""), got.note
    assert "may be cut short" in (got.note or "") and got.source_ref is not None, got.note
    whole, _n = _roster(_rtf(tmp_path, [*head, "*denotes proprietary relationship"]))
    assert "may be cut short" not in (whole.note or "") and whole.source_ref is None, whole.note


def test_rbc_d5_twin_a_thin_rtf_is_not_called_a_word_document(tmp_path: Path) -> None:
    """(+) Before: "this is an OLE-disguised Word doc, not real RTF" — of a file whose bytes
    `classify` had already read as RTF."""
    path = _rtf(tmp_path, [_HEADER], pad=8000)
    assert path.stat().st_size > 4096
    with pytest.raises(CiqParseError) as err:
        read_text(path)
    assert "OLE-disguised" not in str(err.value) and "whose bytes are RTF" in str(err.value)


# --- review round 0: the shapes at the size a real export has ------------------------------------
# Every relationship export on disk is >= 70 KB (2026-11-11), so an empty view is a THIN RTF: the
# small twins above pass under read_text's 4 KB guard, which a real empty view never does.


@pytest.mark.parametrize(("lines", "said"), [
    ([_HEADER, "*denotes proprietary relationship"], "has its header and no rows"),
    (["Zinnober Fixture Works Inc.", "No Data Available"], "reads 'No Data Available'"),
    (["Zinnober Fixture Works Inc.", "Entitlement Needed"], "reads 'Entitlement Needed'"),
])
def test_rbc_d5_an_empty_view_at_a_real_exports_size_is_named(
        tmp_path: Path, lines: list[str], said: str) -> None:
    """(+) Before: the thin-RTF guard refused each first, so the page read its error, never the
    view's shape. The note makes a claim about the file, so it cites it."""
    path = _rtf(tmp_path, lines, pad=70_000)
    got, n = _roster(path)
    assert got.status is SourceStatus.UNKNOWN and n is None
    assert said in (got.note or "") and "striprtf yielded" not in (got.note or ""), got.note
    assert got.source_ref == f"CIQ Customers&Suppliers {_NAME}"


def test_rbc_d5_a_thin_rtf_showing_no_shape_keeps_the_guards_word(tmp_path: Path) -> None:
    """(-) A thin RTF with neither a table header nor a named sentinel still reads the guard."""
    got, _n = _roster(_rtf(tmp_path, ["Zinnober Fixture Works Inc.", "fragment"], pad=70_000))
    assert "striprtf yielded" in (got.note or "") and got.source_ref is None, got.note


def test_rbc_d5_a_header_with_no_rows_and_no_closing_line_may_be_cut(tmp_path: Path) -> None:
    """(+) A view cut short just after its header is not an empty view."""
    got, _n = _roster(_rtf(tmp_path, [_HEADER], pad=70_000))
    assert "may be cut short" in (got.note or ""), got.note


def test_rbc_d5_a_header_followed_by_content_is_not_called_header_only() -> None:
    """(-) A row this reader cannot read (its customer cell blank) is content, not nothing: the view
    is unparsed, never 'has its header and no rows'."""
    raw = "\n".join([_HEADER, "|Customer|Industrials|10-K", "*denotes proprietary relationship"])
    assert cs._unread_view(raw, _NAME, closing_known=True) is None


def test_rbc_d3_a_prior_list_from_a_cut_file_says_so(tmp_path: Path) -> None:
    """(+) The recent section states none and the prior rows are read from a file with no closing
    line: their count is said to be from a list that may be cut short."""
    lines = ["Recently Disclosed Customers", "There are no recently disclosed customers listed",
             "Prior and Not Recently Disclosed Customers", _HEADER,
             "Acme Corp|Customer|Industrials|10-K"]
    got, n = _roster(_rtf(tmp_path, lines))
    assert n is None and "may be cut short: 1 row(s) read" in (got.note or ""), got.note
    whole, _n = _roster(_rtf(tmp_path, [*lines, "*denotes proprietary relationship"]))
    assert "may be cut short" not in (whole.note or ""), whole.note


def test_rbc_d3_the_count_writer_refuses_a_cut_roster_rather_than_crash(tmp_path: Path) -> None:
    """(+) Before: a PRESENT roster with no count raised RuntimeError, stopping the sweep."""
    import json

    from vinci.dossier import ciq_reread
    from vinci.dossier.schemas import Dossier, dossier_json

    ciq = tmp_path / "ciq" / "AMZN"
    ciq.mkdir(parents=True)
    path = _rtf(ciq, [_HEADER, "Acme Corp|Customer|Industrials|10-K"])
    roster, n = cs.customer_roster(CiqBundle.from_files("AMZN", [path]))
    assert roster.status is SourceStatus.PRESENT and n is None
    root = Path(__file__).resolve().parents[1]
    page = json.loads((root / "data" / "dossiers" / "AMZN" / "dossier.json").read_text())
    page["mechanical"]["concentration"]["customers"] = json.loads(roster.model_dump_json())
    page["mechanical"]["concentration"].pop("customers_listed", None)
    jp = tmp_path / "dossiers" / "AMZN" / "dossier.json"
    jp.parent.mkdir(parents=True)
    jp.write_text(dossier_json(Dossier.model_validate(page)))
    o = ciq_reread.reread(jp, "customers_listed", tmp_path / "ciq")
    assert o.status == "refused" and "may be cut short" in o.detail, o
