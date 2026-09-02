"""Guard pins for `EdgarClient`'s per-instance submissions memo (`_submissions`).

WHY THESE PINS. `CachedHttp` caches on DISK only, so one dossier assembly's ~13 reads of one CIK's
submissions document each cost a disk read plus TWO json parses — and, on a degraded feed, each
re-runs the full retry storm because `_write_cache` runs only on success. The memo pays both once
per CIK per client.

The dangerous failure is NOT a slow run: it is a memo that answers a remembered FAILURE with `None`
or `{}`. Nearly every submissions consumer treats "no filings" as a legitimate empty answer, so that
would silently blank the 8-K / Form 4 / catalyst blocks across a degraded run WITH THE SUITE GREEN.
`test_a_remembered_failure_re_raises_and_never_answers_empty` is the pin that must never be relaxed.

The payload shape here is copied from a real cached document
(`data/cache/sec` → `https://data.sec.gov/submissions/CIK0002002473.json`): the same top-level keys
the consumers read, `formerNames` rows carrying the real `...T05:00:00.000Z` stamps, and a
`filings.recent` block of PARALLEL ARRAYS — the shape `recent_filings` indexes into.
"""

from __future__ import annotations

from typing import Any

import pytest

from vinci.edgar.client import _SUBMISSIONS_MEMO_MAX, EdgarClient
from vinci.netcache import HttpError


def _submissions_doc(*, cik10: str, name: str, former: str) -> dict[str, Any]:
    """One realistically-shaped submissions payload. Built from the REAL document's key set, not
    from the minimum this test could get away with — a fixture trimmed to the assertion would stop
    exercising the `.get(...)` fallbacks `recent_filings` relies on."""
    return {
        "cik": cik10.lstrip("0"),
        "name": name,
        "sic": "3841",
        "sicDescription": "Surgical & Medical Instruments",
        "tickers": ["ZZZZ"],
        "exchanges": ["NYSE"],
        "formerNames": [
            {"name": former, "from": "2023-12-21T05:00:00.000Z", "to": "2024-02-05T05:00:00.000Z"}
        ],
        "filings": {
            "recent": {
                "accessionNumber": ["0002002473-26-000017", "0002002473-26-000018"],
                "form": ["8-K", "10-Q"],
                "filingDate": ["2026-08-05", "2026-08-12"],
                "items": ["2.02,9.01", ""],
                "primaryDocument": ["bow-20260805.htm", "bow-20260812.htm"],
                "reportDate": ["2026-08-05", "2026-06-30"],
            }
        },
    }


class _CountingHttp:
    """Duck-typed `CachedHttp` double: serves one document per CIK and COUNTS every upstream read.

    It re-serialises on each call so a caller receives a FRESH object exactly as the real
    `get_json` does (which re-parses the payload every time). A double that handed back one shared
    object would make the isolation and mutation pins pass vacuously.
    """

    def __init__(
        self, docs: dict[str, dict[str, Any]], *, fail_with: Exception | None = None
    ) -> None:
        self._docs = docs
        self.fail_with = fail_with
        self.urls: list[str] = []

    def get_json(
        self,
        url: str,
        *,
        ttl_seconds: float | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        self.urls.append(url)
        if self.fail_with is not None:
            raise self.fail_with
        cik10 = url.rsplit("CIK", 1)[1].removesuffix(".json")
        import copy

        return copy.deepcopy(self._docs[cik10])


_CIK_A = "0002002473"
_CIK_B = "0000320193"


def _client(
    docs: dict[str, dict[str, Any]] | None = None, *, fail_with: Exception | None = None
) -> tuple[EdgarClient, _CountingHttp]:
    docs = docs if docs is not None else {
        _CIK_A: _submissions_doc(cik10=_CIK_A, name="Bowhead Specialty", former="Bowhead Holdings"),
        _CIK_B: _submissions_doc(cik10=_CIK_B, name="Apple Inc.", former="Apple Computer, Inc."),
    }
    http = _CountingHttp(docs, fail_with=fail_with)
    return EdgarClient(http=http), http  # type: ignore[arg-type]


# --- the parse-count pin (verify gate 2) -------------------------------------------------------


def test_one_cik_is_read_from_upstream_once_however_many_consumers_ask() -> None:
    """THE POINT OF THE CHANGE. `recent_filings` and `registrant_history` are the two consumers of
    `_submissions`; one assembly calls them ~13 times for one CIK. Upstream must see ONE read."""
    edgar, http = _client()

    for _ in range(6):
        edgar.recent_filings(_CIK_A, forms=("8-K",))
    edgar.registrant_history(_CIK_A)
    edgar.recent_filings(int(_CIK_A), forms=("10-Q",))  # an UNPADDED int must hit the same memo

    assert http.urls == [f"https://data.sec.gov/submissions/CIK{_CIK_A}.json"]


def test_the_answers_are_unchanged_by_memoisation() -> None:
    """A memo that returned something different from the un-memoized read would be a data bug, not
    a speed-up. Pin the second answer against the first, through both consumers."""
    edgar, _ = _client()

    first = edgar.recent_filings(_CIK_A, forms=("8-K",))
    second = edgar.recent_filings(_CIK_A, forms=("8-K",))
    assert first == second
    assert [f.accession for f in first] == ["0002002473-26-000017"]
    assert first[0].items == ["2.02", "9.01"]

    hist_a, hist_b = edgar.registrant_history(_CIK_A), edgar.registrant_history(_CIK_A)
    assert hist_a == hist_b
    assert hist_a.current == "Bowhead Specialty"
    assert [f.name for f in hist_a.former] == ["Bowhead Holdings"]


# --- the mutation pin ---------------------------------------------------------------------------


def test_the_memoized_document_is_not_mutated_by_its_consumers() -> None:
    """THE REFERENCE-RETURN PIN. `_submissions` hands back the memoized dict BY REFERENCE, because
    copying it costs 4.4x the parse it replaces (deepcopy 1.86 ms vs json.loads 0.42 ms on the
    corpus-median document) and would make the change a net pessimization.

    That is only safe while no consumer mutates. This asserts the production consumers leave the
    document untouched after a full round-trip. Its FALSIFIER is a future consumer that writes to
    the document — at which point this pin reddens and the copy-vs-reference decision is re-opened.
    """
    edgar, _ = _client()
    pristine = _submissions_doc(cik10=_CIK_A, name="Bowhead Specialty", former="Bowhead Holdings")

    edgar.recent_filings(_CIK_A, forms=("8-K", "10-Q"))
    edgar.registrant_history(_CIK_A)

    assert edgar._submissions(_CIK_A) == pristine


def test_the_memo_returns_by_reference_so_the_mutation_pin_is_load_bearing() -> None:
    """THE NEGATIVE HALF of the pin above. If `_submissions` returned a copy, the no-mutation pin
    would pass vacuously and stop guarding anything. This proves the memo really does share one
    object — so the pin above is testing a real property, not a tautology."""
    edgar, http = _client()

    first, second = edgar._submissions(_CIK_A), edgar._submissions(_CIK_A)
    # IDENTITY, not equality. Equality holds for a copy too, so an `==` assertion here would let a
    # `copy.deepcopy` on the memo-hit path through — and that copy is precisely the 4.4x
    # pessimization this design rejects. (Found by mutation-testing this file: an earlier version
    # of this pin asserted a sentinel write survived, which a copy ALSO satisfies, because the
    # first read returns the memoized object itself either way.)
    assert first is second
    first["__sentinel__"] = "written by a caller"
    assert edgar._submissions(_CIK_A)["__sentinel__"] == "written by a caller"
    assert len(http.urls) == 1  # and still no second upstream read


# --- the isolation pin --------------------------------------------------------------------------


def test_two_ciks_do_not_collide() -> None:
    edgar, http = _client()

    a = edgar.registrant_history(_CIK_A)
    b = edgar.registrant_history(_CIK_B)

    assert a.current == "Bowhead Specialty"
    assert b.current == "Apple Inc."
    assert a != b
    assert len(http.urls) == 2  # one read each — neither served the other's document


def test_the_second_cik_is_never_served_the_first_ciks_document() -> None:
    """The negative pin: read A, then ask for B, and B must NOT come back as A. A memo keyed on
    anything coarser than the CIK (a bare flag, the URL template) passes the test above and fails
    this one."""
    edgar, _ = _client()

    edgar.recent_filings(_CIK_A, forms=("8-K",))
    assert edgar._submissions(_CIK_B)["name"] == "Apple Inc."
    assert edgar._submissions(_CIK_A)["name"] == "Bowhead Specialty"


# --- the failure pin (verify gate 3) ------------------------------------------------------------


def test_a_remembered_failure_re_raises_and_never_answers_empty() -> None:
    """THE HIGHEST-RISK FAILURE MODE, pinned. On a degraded feed the memo must remember the FAILURE
    and re-raise an equivalent `HttpError` — never `None`, never `{}`. Consumers read an empty
    submissions document as "this issuer has no filings", so answering empty here would blank the
    8-K / Form 4 / catalyst blocks on every dossier in a degraded run with the suite green."""
    boom = HttpError("Exhausted retries for https://data.sec.gov/submissions/CIK.json")
    edgar, http = _client(fail_with=boom)

    with pytest.raises(HttpError) as first:
        edgar._submissions(_CIK_A)
    with pytest.raises(HttpError) as second:
        edgar._submissions(_CIK_A)

    # the storm is paid ONCE — this is payoff (b), the reason the change exists
    assert len(http.urls) == 1
    # and the second caller sees an EQUIVALENT error, so every `except HttpError` still fires
    assert str(second.value) == str(first.value)
    assert type(second.value) is type(first.value)


def test_a_remembered_failure_still_raises_through_the_real_consumers() -> None:
    """The pin above calls the private helper directly. This one goes through the two PUBLIC
    consumers, because those are what the ~13 call sites actually use: neither may convert a
    remembered failure into an empty list or an empty history."""
    edgar, http = _client(fail_with=HttpError("503 from data.sec.gov"))

    with pytest.raises(HttpError):
        edgar.recent_filings(_CIK_A, forms=("8-K",))
    with pytest.raises(HttpError):
        edgar.registrant_history(_CIK_A)

    assert len(http.urls) == 1


def test_a_failure_for_one_cik_does_not_poison_another() -> None:
    """A remembered failure is keyed like a success. CIK B must still be fetchable after A failed,
    and must not inherit A's error."""
    docs = {
        _CIK_B: _submissions_doc(cik10=_CIK_B, name="Apple Inc.", former="Apple Computer, Inc.")
    }
    http = _CountingHttp(docs)
    edgar = EdgarClient(http=http)  # type: ignore[arg-type]

    http.fail_with = HttpError("503 from data.sec.gov")
    with pytest.raises(HttpError):
        edgar._submissions(_CIK_A)

    http.fail_with = None
    assert edgar._submissions(_CIK_B)["name"] == "Apple Inc."
    with pytest.raises(HttpError):
        edgar._submissions(_CIK_A)  # A stays remembered-failed, from the memo, without a refetch
    assert http.urls.count(f"https://data.sec.gov/submissions/CIK{_CIK_B}.json") == 1


def test_only_http_errors_are_remembered() -> None:
    """DELIBERATE NARROWNESS. Only `HttpError` — the retry-storm case — is memoized. Anything else
    (a malformed payload, a programming error) propagates UNremembered, so it cannot become sticky
    for the life of the client and is re-attempted like it is today."""
    edgar, http = _client(fail_with=ValueError("malformed payload"))

    with pytest.raises(ValueError):
        edgar._submissions(_CIK_A)
    with pytest.raises(ValueError):
        edgar._submissions(_CIK_A)

    assert len(http.urls) == 2  # re-attempted, NOT remembered
    assert edgar._submissions_memo == {}


# --- the bound pin ------------------------------------------------------------------------------


def test_the_memo_is_bounded_across_a_many_cik_sweep() -> None:
    """`vinci/cli.py`'s monitor loop and the theme scans hold ONE client across MANY CIKs and read
    each exactly once, so an unbounded memo there would retain every document for no reuse
    (~1.0 GB over a 2,000-name sweep at the corpus median). The bound must hold."""
    docs = {
        f"{n:010d}": _submissions_doc(cik10=f"{n:010d}", name=f"Issuer {n}", former=f"Old {n}")
        for n in range(1, 41)
    }
    http = _CountingHttp(docs)
    edgar = EdgarClient(http=http)  # type: ignore[arg-type]

    for cik10 in docs:
        edgar.registrant_history(cik10)

    assert len(edgar._submissions_memo) <= _SUBMISSIONS_MEMO_MAX
    assert len(http.urls) == 40  # each read once — the sweep is not slowed by the bound


def test_the_bound_keeps_the_most_recent_cik_which_is_the_one_being_assembled() -> None:
    """Eviction is oldest-first, so the CIK currently being assembled — the one with ~13 reads
    ahead of it — is the one retained."""
    docs = {
        f"{n:010d}": _submissions_doc(cik10=f"{n:010d}", name=f"Issuer {n}", former=f"Old {n}")
        for n in range(1, 6)
    }
    http = _CountingHttp(docs)
    edgar = EdgarClient(http=http)  # type: ignore[arg-type]

    for cik10 in docs:
        edgar.registrant_history(cik10)
    before = len(http.urls)
    edgar.registrant_history("0000000005")  # the most recent CIK is still remembered

    assert len(http.urls) == before


# --- the lifetime pin ---------------------------------------------------------------------------


def test_the_memo_does_not_outlive_the_client() -> None:
    """"For the life of one run" is enforced by the memo living on the INSTANCE. A fresh client
    must go back upstream — which is what keeps the disk cache's TTL the authority on staleness
    rather than a memo that could serve a day-old document to a new invocation."""
    docs = {_CIK_A: _submissions_doc(cik10=_CIK_A, name="Bowhead Specialty", former="Bowhead")}
    http = _CountingHttp(docs)

    first = EdgarClient(http=http)  # type: ignore[arg-type]
    first.registrant_history(_CIK_A)
    first.registrant_history(_CIK_A)
    assert len(http.urls) == 1

    second = EdgarClient(http=http)  # type: ignore[arg-type]
    second.registrant_history(_CIK_A)
    assert len(http.urls) == 2  # a NEW client re-reads; the memo did not survive it
    assert first._submissions_memo is not second._submissions_memo


def test_each_client_memoizes_into_its_own_dict() -> None:
    """`assemble_cohort` runs 8 worker threads and each `assemble_one` builds its own `EdgarClient`,
    so the memo must be per-instance state, never shared or class-level. A class attribute would
    make this fail — and would silently share documents across concurrently-assembled names."""
    a, _ = _client()
    b, _ = _client()

    a.registrant_history(_CIK_A)

    assert a._submissions_memo != {}
    assert b._submissions_memo == {}


def test_a_non_object_payload_fails_loud_instead_of_memoizing_none() -> None:
    """A JSON `null` (or list) body must NOT be stored. `None` would be indistinguishable from a
    memo MISS on every later read — re-fetching 13 times silently while still occupying a bounded
    slot — and would then AttributeError inside `recent_filings`' `data.get(...)`. Fail loud as an
    HttpError, which every consumer already degrades on."""
    for payload in (None, [], "not a document"):
        http = _CountingHttp({})
        http.get_json = (  # type: ignore[method-assign]
            lambda *a, _p=payload, **k: _p  # bind now, not at call time (ruff B023)
        )
        edgar = EdgarClient(http=http)  # type: ignore[arg-type]

        with pytest.raises(HttpError) as exc:
            edgar._submissions(_CIK_A)
        assert "not a JSON object" in str(exc.value)
        assert None not in edgar._submissions_memo.values()


def test_the_hot_cik_survives_eviction_because_a_hit_refreshes_it() -> None:
    """TRUE LRU, not insertion-FIFO. A plain dict evicts by FIRST INSERTION and does not reorder on
    re-assignment, so the CIK currently being assembled — the one with ~13 reads still ahead of it —
    was the first to be dropped once two other CIKs were read. `_recall_submissions` now
    `move_to_end`s on a hit. The earlier pin could not see this: its fixture inserted the hot CIK
    last, so it passed identically under FIFO and LRU."""
    docs = {
        f"{n:010d}": _submissions_doc(cik10=f"{n:010d}", name=f"Issuer {n}", former=f"Old {n}")
        for n in (1, 2, 3)
    }
    http = _CountingHttp(docs)
    edgar = EdgarClient(http=http)  # type: ignore[arg-type]

    edgar._submissions("0000000001")          # the hot one, inserted FIRST
    edgar._submissions("0000000002")
    edgar._submissions("0000000001")          # ...but read again — under LRU this refreshes it
    edgar._submissions("0000000003")          # evicts the LEAST-recently-used, which is #2

    assert "0000000001" in edgar._submissions_memo, "the hot CIK was evicted — eviction is FIFO"
    assert "0000000002" not in edgar._submissions_memo
    assert len(http.urls) == 3, "the hot CIK was re-fetched despite being in the memo"


def test_the_memo_survives_concurrent_use_of_one_client() -> None:
    """`_submissions_memo` is the first mutable state on `EdgarClient`, and ONE client is shared
    across a `ThreadPoolExecutor` by `vinci/themes/exposure.py::scan_driver_exposure`
    (built at `vinci/cli.py`). The original `pop(next(iter(...)))` read the mapping while mutating
    it: reproduced as `RuntimeError: dictionary changed size during iteration` and `KeyError` under
    8 threads. Those land in the scan's per-name `except Exception` and drop a name from the
    exposure population, blaming EDGAR for a local race."""
    import threading

    docs = {
        f"{n:010d}": _submissions_doc(cik10=f"{n:010d}", name=f"Issuer {n}", former=f"Old {n}")
        for n in range(1, 25)
    }
    http = _CountingHttp(docs)
    edgar = EdgarClient(http=http)  # type: ignore[arg-type]
    errors: list[BaseException] = []

    def hammer() -> None:
        try:
            for _ in range(300):
                for cik10 in docs:
                    edgar._submissions(cik10)
        except BaseException as exc:  # noqa: BLE001 — the point is that NOTHING escapes
            errors.append(exc)

    threads = [threading.Thread(target=hammer) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"the memo raced under 8 threads: {errors[:3]}"
    assert len(edgar._submissions_memo) <= _SUBMISSIONS_MEMO_MAX
