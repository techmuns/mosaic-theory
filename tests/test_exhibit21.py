"""W86 — the Exhibit 21 reader (`vinci.edgar.exhibit21`) on real filed lists.

Every document is a real EDGAR exhibit (tests/fixtures/exhibit21/README.md). The pins are the
question W86 measures: an own unit ON the list (Google under Alphabet), an own unit OFF a list that
says it holds only significant subsidiaries (Whole Foods under Amazon), a company CIQ files under a
filer that the list does not name (Lyft under Alphabet), and a part-owned company ON a list (Par
Pacific's 40% Yellowstone Pipe Line).
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from bs4 import BeautifulSoup

from vinci.edgar.client import Filing
from vinci.edgar.exhibit21 import (
    Exhibit21Read,
    _is_ex21_type,
    _text_rows,
    bind_exhibit21,
    ex21_documents,
    match_entity,
    name_in_force,
    normalise_name,
    parse_exhibit21,
    read_exhibit21,
)
from vinci.edgar.submissions import FormerName, RegistrantHistory
from vinci.netcache import HttpError

FIX = Path(__file__).parent / "fixtures" / "exhibit21"
CASES: dict[str, Any] = json.loads((FIX / "cases.json").read_text())
EXHIBITS: dict[str, dict[str, Any]] = CASES["exhibits"]
TENK_ACC = "0001652044-26-000018"  # Alphabet's 10-K: types EX-21.01
TENQ_ACC = "0001652044-26-000084"  # Alphabet's 10-Q: files no Exhibit 21


def _read(ticker: str) -> Exhibit21Read:
    """The committed document bound as `read_exhibit21` binds it (no HTTP)."""
    c = EXHIBITS[ticker]
    doc = (FIX / f"{ticker}.htm").read_text()
    return bind_exhibit21(c["cik"], c["accession"], date.fromisoformat(c["filing_date"]),
                          [(c["type"], c["url"], doc)], registrant=c["registrant"],
                          filed_as=c["registrant"])  # none of these filers renamed since


def _names(ticker: str) -> list[str]:
    return [n.name for n in _read(ticker).names]


# --- the question: own on the list, own off it, a non-own name off it, a part-owned name on it --

def test_positive_google_is_alphabets_own_and_listed() -> None:
    read = _read("GOOGL")
    m = match_entity("Google", read)
    assert m.tier == "normalised"
    assert m.listed is not None and m.listed.name == "Google LLC"
    assert TENK_ACC in m.listed.source_ref and "EX-21.01" in m.listed.source_ref
    assert m.listed.source_ref.endswith(EXHIBITS["GOOGL"]["url"])
    assert match_entity("Google LLC", read).tier == "exact"
    assert match_entity("GOOGLE LLC", read).tier == "normalised"  # exact is the name as listed


def test_negative_lyft_is_not_on_alphabets_list() -> None:
    read = _read("GOOGL")
    for entity in ("Lyft", "Lyft, Inc."):
        m = match_entity(entity, read)
        assert m.tier == "not_listed" and m.listed is None
    assert match_entity("Lyft", read).list_states_omission  # Alphabet omits the insignificant


def test_whole_foods_is_amazons_own_and_not_listed_on_a_significant_only_list() -> None:
    """Not listed is NOT "not own": Amazon's list says it holds significant subsidiaries only."""
    read = _read("AMZN")
    assert read.states_omission == "LIST OF SIGNIFICANT SUBSIDIARIES"
    for entity in ("Whole Foods", "Whole Foods Market", "Whole Foods Market, Inc."):
        m = match_entity(entity, read)
        assert m.tier == "not_listed" and m.list_states_omission
    assert match_entity("Kartoon Studios", read).tier == "not_listed"


def test_shipt_is_targets_own_and_not_listed() -> None:
    read = _read("TGT")
    assert read.states_omission is not None and "601(b)(21)(ii)" in read.states_omission
    m = match_entity("Shipt", read)
    assert m.tier == "not_listed" and m.list_states_omission


def test_a_part_owned_company_is_listed_with_its_share() -> None:
    """Par Pacific's list carries an investee: a 40% interest is no subsidiary."""
    m = match_entity("Yellowstone Pipe Line Company", _read("PARR"))
    assert m.tier == "normalised"
    assert m.listed is not None and m.listed.stated_percent == 40.0
    shares = {n.name: n.stated_percent for n in _read("PARR").names}
    assert shares["Laramie Energy, LLC (46.0% interest)"] == 46.0
    assert shares["Hawaii Renewables, LLC"] is None  # a row that states no share has none


def test_the_filer_itself_is_the_registrant_never_not_listed() -> None:
    """The list never names its filer; an entity that IS the filer matches as the registrant."""
    read = _read("GOOGL")
    assert read.registrant == "Alphabet Inc."
    for entity in ("Alphabet", "Alphabet Inc.", "ALPHABET INC"):
        assert match_entity(entity, read).tier == "registrant"
    # a listed subsidiary that shares the filer's first word is no registrant
    assert match_entity("Alphabet Capital US LLC", read).tier == "exact"
    # and the registrant is known even where no list is read
    edgar = _Edgar([], "Alphabet Inc.")
    none = read_exhibit21(edgar, _Http({}), 1652044)  # type: ignore[arg-type]
    assert match_entity("Alphabet", none).tier == "registrant"
    assert match_entity("Google", none).tier == "no_10k"


def test_word_prefix_is_its_own_tier() -> None:
    quest = match_entity("Quest", _read("SMPL"))
    assert quest.tier == "word_prefix"
    assert quest.listed is not None and quest.listed.name == "Quest Nutrition, LLC"
    assert "VMG Quest Blocker, Inc." in _names("SMPL")  # a mid-name hit is never a prefix
    lilly = match_entity("LillyDirect", _read("LLY"))
    assert lilly.tier == "word_prefix"
    assert lilly.listed is not None and lilly.listed.name == "LillyDirect Pharmacy, LLC"
    assert match_entity("Quest Nutrition", _read("SMPL")).tier == "normalised"


def test_affiliates_flag() -> None:
    assert _read("LLY").names_affiliates  # "Exhibit 21 — List of Subsidiaries & Affiliates"
    assert not _read("GOOGL").names_affiliates


def test_no_omission_statement_is_not_a_complete_list() -> None:
    """Uber states no omission and lists 13 names: `states_omission` None says only that."""
    read = _read("UBER")
    assert read.states_omission is None
    assert len(read.names) == 13
    assert match_entity("Uber Eats", read).tier == "not_listed"
    assert not match_entity("Uber Eats", read).list_states_omission


# --- the omission statement ---------------------------------------------------------------------

def test_omission_sentence_is_the_filers_own_words() -> None:
    googl = _read("GOOGL").states_omission
    assert googl is not None and googl.startswith("The following is a list of subsidiaries of "
                                                  "Alphabet Inc., omitting subsidiaries which")
    lly = _read("LLY").states_omission
    assert lly == "Certain subsidiaries have been omitted as they are not significant in the " \
                  "aggregate."
    # a heading set across two text blocks ("List of Significant" / "Subsidiaries of Visa Inc.")
    assert _read("V").states_omission == "List of Significant Subsidiaries of Visa Inc."
    assert _read("SMPL").states_omission is None


# --- the parser's real shapes -------------------------------------------------------------------

def test_table_header_rows_are_not_names() -> None:
    assert _names("GOOGL") == ["Google LLC", "XXVI Holdings Inc.", "Alphabet Capital US LLC"]
    assert "Entity" not in _names("EPAM")
    assert _names("EPAM")[0] == "EPAM Systems Albania SHPK"
    tjx = _names("TJX")
    assert "Operating Subsidiaries" not in tjx and "Leasing Subsidiaries" not in tjx
    assert "NBC Sixth Realty Corp." in tjx
    lly = _names("LLY")
    assert not any("Jurisdiction" in n for n in lly)
    # header vocabulary inside a real name that ends in a corporate form is still a name
    assert "Eli Lilly (Philippines), Incorporated" in lly
    # a form some jurisdictions put first is a name in a text exhibit too (review round 2)
    leading = ["UAB Eli Lilly Lietuva", "LLC IT-PARK UNIVERSITY"]
    assert {r.name for r in _text_rows(leading)} == set(leading)
    assert "LLC IT-PARK UNIVERSITY" in _names("EPAM") and "UAB Eli Lilly Lietuva" in lly


def test_rows_differing_in_form_or_jurisdiction_are_two_companies() -> None:
    """Review round 0: a dedup on the normalised key merged them (EPAM lost 13 rows, CNXC 15)."""
    epam = [(n.name, n.jurisdiction) for n in _read("EPAM").names if n.name == "EPAM Systems LLC"]
    assert epam == [("EPAM Systems LLC", "Armenia"), ("EPAM Systems LLC", "Kyrgyzstan"),
                    ("EPAM Systems LLC", "Ukraine"), ("EPAM Systems LLC", "New Jersey, USA")]
    lly = _names("LLY")
    assert "Aparito Limited" in lly and "Aparito LLC" in lly
    assert match_entity("Aparito LLC", _read("LLY")).tier == "exact"
    tjx = _names("TJX")
    assert "NBC Apparel, Inc." in tjx and "NBC Apparel, LLC" in tjx


def test_only_the_registrant_itself_is_dropped() -> None:
    """Review round 0: a drop on the normalised key removed every subsidiary sharing the filer's
    base name. Lilly (EDGAR: "ELI LILLY & Co") keeps its Limited and S.A.; Target's own heading
    "Target Corporation" ("TARGET CORP") is still dropped."""
    lly = _names("LLY")
    assert "Eli Lilly and Company Limited" in lly and "Eli Lilly S.A." in lly
    assert "Target Corporation" not in _names("TGT")
    assert match_entity("Eli Lilly and Company Limited", _read("LLY")).tier == "exact"


def test_numbered_rows_give_the_name_not_the_number() -> None:
    wern = _read("WERN")
    assert len(wern.names) == 21
    assert wern.names[0].name == "Gra-Gar, LLC" and wern.names[0].jurisdiction == "Delaware"
    assert not any(n.name.rstrip(".").isdigit() for n in wern.names)


def test_percent_cells_are_not_the_jurisdiction() -> None:
    amzn = _read("AMZN")
    assert len(amzn.names) == 9
    assert amzn.names[0].name == "Amazon.com Services LLC"
    assert amzn.names[0].jurisdiction == "Delaware"
    assert amzn.names[0].stated_percent == 100.0


def test_text_list_takes_its_jurisdiction_and_drops_the_registrant() -> None:
    tgt = _read("TGT")
    assert [(n.name, n.jurisdiction) for n in tgt.names] == [
        ("Target Brands, Inc.", "MN"), ("Target Enterprise, Inc.", "MN"),
        ("Target General Merchandise, Inc.", "MN")]
    rows, _ = parse_exhibit21((FIX / "TGT.htm").read_text(), registrant=None)
    assert "Target Corporation" in [r.name for r in rows]  # dropped only as the registrant


def test_a_document_with_no_list_is_no_names_never_empty_listed() -> None:
    """Alphabet's real exhibit with its table taken out: the prose stays, no name is read."""
    soup = BeautifulSoup((FIX / "GOOGL.htm").read_text(), "html.parser")
    for table in soup.find_all("table"):
        table.decompose()
    read = bind_exhibit21("1652044", TENK_ACC, date(2026, 2, 5),
                          [("EX-21.01", EXHIBITS["GOOGL"]["url"], str(soup))],
                          registrant="Alphabet Inc.")
    assert read.status == "no_names" and read.names == ()
    assert read.states_omission is not None  # the statement is still read
    assert match_entity("Google", read).tier == "no_names"


# --- normalisation ------------------------------------------------------------------------------

@pytest.mark.parametrize(("name", "key"), [
    ("Google LLC", "google"),
    ("Amazon.com, Inc.", "amazon com"),
    ("XXVI Holdings Inc.", "xxvi holdings"),  # Holdings tells two companies apart
    ("Eli Lilly and Company", "eli lilly"),
    ("Netflix México S. de R.L. de C.V.", "netflix méxico"),
    ("Yellowstone Pipe Line Company (40.0% interest)", "yellowstone pipe line"),
    ("The Simply Good Foods Company", "simply good foods"),
])
def test_normalise_name(name: str, key: str) -> None:
    assert normalise_name(name) == key


# --- the EDGAR path: the header's TYPE, unreadable and absent ------------------------------------

class _Http:
    """Serves the committed headers and documents by URL; anything else is an HttpError."""

    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages
        self.asked: list[str] = []

    def get_text(self, url: str, *, ttl_seconds: float | None = None) -> str:
        self.asked.append(url)
        if url not in self.pages:
            raise HttpError(f"not served: {url}")
        return self.pages[url]


class _Edgar:
    def __init__(self, filings: list[Filing], registrant: str,
                 former: tuple[FormerName, ...] = ()) -> None:
        self.filings = filings
        self.registrant = registrant
        self.former = former

    def recent_filings(self, cik: int | str, *, forms: tuple[str, ...] = ("8-K",),
                       since: date | None = None) -> list[Filing]:
        self.since = since
        return [f for f in self.filings if f.form in forms
                and (since is None or f.filing_date >= since)]

    def registrant_history(self, cik: int | str) -> RegistrantHistory:
        return RegistrantHistory(current=self.registrant, former=self.former)


def _header_url(acc: str) -> str:
    return CASES["headers"][acc]["url"]


def _googl_pages() -> dict[str, str]:
    return {_header_url(a): (FIX / CASES["headers"][a]["file"]).read_text()
            for a in (TENK_ACC, TENQ_ACC)} | {
        EXHIBITS["GOOGL"]["url"]: (FIX / "GOOGL.htm").read_text()}


def _tenk(acc: str, filed: date) -> Filing:
    return Filing(cik="0001652044", form="10-K", filing_date=filed, accession=acc, items=[],
                  primary_doc=None)


def test_the_exhibit_is_found_by_its_header_type() -> None:
    http = _Http(_googl_pages())
    assert ex21_documents(http, "1652044", TENK_ACC) == [("EX-21.01", EXHIBITS["GOOGL"]["url"])]
    assert ex21_documents(http, "1652044", TENQ_ACC) == []  # read, and it files none
    assert ex21_documents(_Http({}), "1652044", TENK_ACC) is None  # unread is never "none"


def test_read_exhibit21_end_to_end_on_the_real_filing() -> None:
    http = _Http(_googl_pages())
    edgar = _Edgar([_tenk(TENK_ACC, date(2026, 2, 5))], "Alphabet Inc.")
    read = read_exhibit21(edgar, http, 1652044)  # type: ignore[arg-type]
    assert read.status == "listed" and read.accession == TENK_ACC
    assert read == _read("GOOGL")


def test_read_exhibit21_unread_and_no_10k() -> None:
    edgar = _Edgar([_tenk(TENK_ACC, date(2026, 2, 5))], "Alphabet Inc.")
    unread = read_exhibit21(edgar, _Http({}), 1652044)  # type: ignore[arg-type]
    assert unread.status == "unread" and unread.accession == TENK_ACC
    assert match_entity("Google", unread).tier == "unread"
    none = read_exhibit21(_Edgar([], "Alphabet Inc."), _Http({}), 1652044)  # type: ignore[arg-type]
    assert none.status == "no_10k"


def test_through_reads_the_newest_10k_filed_by_then() -> None:
    """A later 10-K the cut has not reached is not read: its header is never asked for."""
    later = "0001652044-27-000001"
    http = _Http(_googl_pages())
    edgar = _Edgar([_tenk(TENK_ACC, date(2026, 2, 5)), _tenk(later, date(2027, 2, 4))],
                   "Alphabet Inc.")
    read = read_exhibit21(edgar, http, 1652044, through=date(2026, 11, 20))  # type: ignore[arg-type]
    assert read.accession == TENK_ACC and read.status == "listed"
    assert not any(later.replace("-", "") in u for u in http.asked)
    # review round 0: a cut in the past reads a window behind it, beyond the recent page
    assert edgar.since is not None and edgar.since <= date(2025, 6, 1)
    newest = read_exhibit21(edgar, _Http(_googl_pages()), 1652044)  # type: ignore[arg-type]
    assert newest.accession == later and newest.status == "unread"


def test_a_past_cut_names_the_registrant_in_force_then() -> None:
    """Codex round 1 on #1152: a read at a past `through` took today's registrant name, a
    look-ahead. Oruka Therapeutics filed as "ARCA biopharma, Inc." until 2024-08-30 (its real
    submissions formerNames), and its 10-K by 2024-06-30 is ARCA's, which files no Exhibit 21."""
    h = CASES["historical"]["ORKA"]
    former = tuple(FormerName.model_validate(f) for f in h["former"])
    tenk = Filing(cik=h["cik"], form="10-K", filing_date=date.fromisoformat(h["filing_date"]),
                  accession=h["accession"], items=[], primary_doc=None)
    http = _Http({h["header_url"]: (FIX / h["header_file"]).read_text()})
    edgar = _Edgar([tenk], h["registrant_current"], former)
    read = read_exhibit21(edgar, http, h["cik"],  # type: ignore[arg-type]
                          through=date.fromisoformat(h["through"]))
    assert read.status == "no_ex21" and read.accession == h["accession"]
    assert read.registrant == "ARCA biopharma, Inc."
    assert match_entity("ARCA biopharma", read).tier == "registrant"
    assert match_entity("Oruka Therapeutics", read).tier == "no_ex21"  # not yet its name
    # with no cut, today's name
    today = read_exhibit21(edgar, http, h["cik"])  # type: ignore[arg-type]
    assert today.registrant == "Oruka Therapeutics, Inc."


# --- review round 2 (coordinator A's independent review of #1152 at 5b8732e1) -------------------

def _tables_removed(ticker: str) -> Exhibit21Read:
    c = EXHIBITS[ticker]
    soup = BeautifulSoup((FIX / f"{ticker}.htm").read_text(), "html.parser")
    for table in soup.find_all("table"):
        table.decompose()
    return bind_exhibit21(c["cik"], c["accession"], date.fromisoformat(c["filing_date"]),
                          [(c["type"], c["url"], str(soup))], registrant=c["registrant"])


@pytest.mark.parametrize("ticker", ["V", "SMPL", "GOOGL"])
def test_text_mode_never_reads_the_heading_as_a_subsidiary(ticker: str) -> None:
    """A1: with its table taken out, Visa's and Simply Good Foods' exhibits read `listed` with
    one name, their own heading ("Subsidiaries of …", ending in "Inc."/"Company")."""
    read = _tables_removed(ticker)
    assert read.status == "no_names", [n.name for n in read.names]


#: Real listed names with no corporate form at all, which text mode cannot tell from prose.
_FORMLESS = {"Visa International Service Association", "TJX UK", "Emakina Branch QFC"}


@pytest.mark.parametrize("ticker", sorted(EXHIBITS))
def test_text_mode_keeps_every_real_name_a_table_lists(ticker: str) -> None:
    """A1: the names each committed exhibit's table lists, laid one per line as a text exhibit
    lays them, are all kept. Text mode dropped every name ending in a form `_SUFFIXES` lacked
    (K.K., s.r.o., S.A.C., Trust, Limited Partnership …)."""
    names = [n.name for n in _read(ticker).names]
    kept = {r.name for r in _text_rows(names)}
    assert [n for n in names if n not in kept and n not in _FORMLESS] == []


def test_text_mode_reads_a_dash_jurisdiction() -> None:
    """A1: Uber's 13 real (name, jurisdiction) pairs laid out "Name - Delaware" keep all 13."""
    pairs = [(n.name, n.jurisdiction) for n in _read("UBER").names]
    rows = _text_rows([f"{name} - {juris}" for name, juris in pairs])
    assert [(r.name, r.jurisdiction) for r in rows] == pairs


def test_an_edgar_state_tag_is_not_part_of_the_registrant_name() -> None:
    """A2: EDGAR names TJX "TJX COMPANIES INC /DE/"; the tag kept the filer from matching itself."""
    assert EXHIBITS["TJX"]["registrant"] == "TJX COMPANIES INC /DE/"
    assert normalise_name("TJX COMPANIES INC /DE/") == "tjx companies"
    assert match_entity("The TJX Companies, Inc.", _read("TJX")).tier == "registrant"
    assert normalise_name("Example Holdings Corp /NEW/") == "example holdings"


def test_only_exact_normalised_and_registrant_confirm_own() -> None:
    """A3: `confirms_own` names the tiers that may promote a row to own. `word_prefix` is a lead,
    never a confirmation ("NBC" leads 28 of TJX's names); a list that names affiliates, or a stated
    minority share, confirms nothing even on an exact match."""
    googl = _read("GOOGL")
    assert match_entity("Google LLC", googl).confirms_own            # exact
    assert match_entity("Google", googl).confirms_own                # normalised
    assert match_entity("Alphabet Inc.", googl).confirms_own         # registrant
    assert not match_entity("Lyft", googl).confirms_own              # not_listed
    nbc = match_entity("NBC", _read("TJX"))
    assert nbc.tier == "word_prefix" and not nbc.confirms_own
    quest = match_entity("Quest", _read("SMPL"))
    assert quest.tier == "word_prefix" and not quest.confirms_own
    lilly = match_entity("LillyDirect Pharmacy, LLC", _read("LLY"))
    assert lilly.tier == "exact" and not lilly.confirms_own          # LLY names affiliates
    yellowstone = match_entity("Yellowstone Pipe Line Company", _read("PARR"))
    assert yellowstone.tier == "normalised" and not yellowstone.confirms_own  # 40.0%
    assert match_entity("Hawaii Renewables, LLC", _read("PARR")).confirms_own  # no share stated


def _orka_history() -> RegistrantHistory:
    h = CASES["historical"]["ORKA"]
    return RegistrantHistory(current=h["registrant_current"],
                             former=tuple(FormerName.model_validate(f) for f in h["former"]))


@pytest.mark.parametrize(("day", "name"), [
    (date(1990, 1, 1), "HYSEQ INC"),           # before the first span: the first name
    (date(2003, 1, 28), "HYSEQ INC"),          # a span's last day is in it
    (date(2003, 2, 1), "NUVELO INC"),          # between two spans: the next name
    (date(2009, 1, 28), "ARCA biopharma, Inc."),
    (date(2024, 8, 30), "ARCA biopharma, Inc."),
    (date(2024, 8, 31), "Oruka Therapeutics, Inc."),
    (None, "Oruka Therapeutics, Inc."),
])
def test_name_in_force_has_no_gap_that_reads_todays_name(day: date | None, name: str) -> None:
    """A4: on ORKA's real formerNames a day between two spans, or before the first, read TODAY's
    name — the look-ahead round 1 fixed, left open in the gaps."""
    assert name_in_force(_orka_history(), day) == name


def test_the_list_drops_the_name_the_filer_filed_under() -> None:
    """A4: the self-drop and the registrant tier read the name in force when the 10-K was FILED as
    well as at `through`. At a 2024-12-31 cut Oruka's newest 10-K is still ARCA's (filed
    2024-02-01): the filer is "Oruka" at the cut and filed as "ARCA biopharma, Inc."."""
    h = CASES["historical"]["ORKA"]
    tenk = Filing(cik=h["cik"], form="10-K", filing_date=date.fromisoformat(h["filing_date"]),
                  accession=h["accession"], items=[], primary_doc=None)
    edgar = _Edgar([tenk], h["registrant_current"], _orka_history().former)
    http = _Http({h["header_url"]: (FIX / h["header_file"]).read_text()})
    read = read_exhibit21(edgar, http, h["cik"], through=date(2024, 12, 31))  # type: ignore[arg-type]
    assert read.registrant == "Oruka Therapeutics, Inc."
    assert read.filed_as == "ARCA biopharma, Inc."
    assert match_entity("ARCA biopharma", read).tier == "registrant"
    assert match_entity("Oruka Therapeutics", read).tier == "registrant"
    # the drop: a list that names the filer under its filing-day name is not read as a subsidiary
    rows, _ = parse_exhibit21("<p>ARCA biopharma, Inc.</p><p>ARCA Operating, LLC</p>",
                              registrant="ARCA biopharma, Inc.")
    assert [r.name for r in rows] == ["ARCA Operating, LLC"]


def test_a_header_page_that_is_not_sgml_is_unread_never_no_ex21() -> None:
    """A5: a header URL that answers with something other than EDGAR's SGML header (here the
    filing's real index.json) is `None` → `unread`; mutated to `[]` it read `no_ex21`."""
    pages = {_header_url(TENK_ACC): (FIX / f"GOOGL_{TENK_ACC}-index.json").read_text()}
    assert ex21_documents(_Http(pages), "1652044", TENK_ACC) is None
    edgar = _Edgar([_tenk(TENK_ACC, date(2026, 2, 5))], "Alphabet Inc.")
    assert read_exhibit21(edgar, _Http(pages), 1652044).status == "unread"  # type: ignore[arg-type]


def test_an_unreadable_exhibit_is_unread_never_no_names() -> None:
    """A5: the header types EX-21.01 and the exhibit itself cannot be fetched: `unread`, naming the
    URL; mutated to skip it, it read `no_names` ("a parse failure")."""
    pages = {_header_url(TENK_ACC): (FIX / CASES["headers"][TENK_ACC]["file"]).read_text()}
    edgar = _Edgar([_tenk(TENK_ACC, date(2026, 2, 5))], "Alphabet Inc.")
    read = read_exhibit21(edgar, _Http(pages), 1652044)  # type: ignore[arg-type]
    assert read.status == "unread" and EXHIBITS["GOOGL"]["url"] in read.note


def test_an_unreadable_submissions_document_is_unread_never_a_crash() -> None:
    """Nit: an HttpError on the filer's submissions document aborted `measure` for every filer;
    the reader returns `unread` for that filer alone."""
    class _Down(_Edgar):
        def recent_filings(self, cik: int | str, *, forms: tuple[str, ...] = ("8-K",),
                           since: date | None = None) -> list[Filing]:
            raise HttpError("submissions unavailable")
    read = read_exhibit21(_Down([], "Alphabet Inc."), _Http({}), 1652044)  # type: ignore[arg-type]
    assert read.status == "unread" and "submissions" in read.note


def test_a_10k_filed_on_the_cut_day_is_read() -> None:
    """Nit: `through` is inclusive: Alphabet's 10-K filed 2026-02-05 is read at that day's cut."""
    edgar = _Edgar([_tenk(TENK_ACC, date(2026, 2, 5))], "Alphabet Inc.")
    read = read_exhibit21(edgar, _Http(_googl_pages()), 1652044,  # type: ignore[arg-type]
                          through=date(2026, 2, 5))
    assert read.accession == TENK_ACC


def test_the_exhibit_type_is_matched_whole() -> None:
    """Nit: EX-21, EX-21.1 and EX-21.01 are the list; EX-210 and EX-2.1 are not."""
    assert all(_is_ex21_type(t) for t in ("EX-21", "EX-21.1", "EX-21.01", "ex-21.1"))
    assert not any(_is_ex21_type(t) for t in ("EX-210", "EX-2.1", "EX-21A", "EX-211"))


@pytest.mark.parametrize(("a", "b"), [
    ("Procter & Gamble Co.", "Procter and Gamble Company"),    # the & rule
    ("Concentrix Legal Services Co., Ltd.", "Concentrix Legal Services"),  # stacked forms
    ("Netflix Pte. Ltd.", "Netflix"),
])
def test_normalise_equates(a: str, b: str) -> None:
    assert normalise_name(a) == normalise_name(b)
