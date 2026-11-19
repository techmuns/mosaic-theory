"""Test support (W73, correction 2; operator 2026-11-19: "Approve with corrections"): the ONE
expected difference between a committed page and what today's code derives from it.

`valuation_basis._r1_current` now dates CIQ's multiple by its own close (W65's
`ev_ebitda_basis.multiple_close`), where LLY's committed page carries the comps TEV's date. So
until LLY is restated, its `valuation_basis.current_multiple.as_of` re-derives 2026-10-30 →
2026-11-02 and nothing else on any page moves. A pin that compares a committed page with its own
re-derivation reads the committed text through :func:`as_derived`: ONLY that leaf, ONLY on LLY,
ONLY to 2026-11-02 — every other byte of every page is compared as before.

NOT AN XFAIL, and temporary: the $0 artifact PR after W73 restates LLY's page and deletes this
module and every call to it. Once LLY carries the new date the function changes nothing.
"""
from __future__ import annotations

_OLD = ('    "current_multiple": {\n      "metric": "EV/EBITDA (TEV/LTM)",\n'
        '      "period": "LTM",\n      "value": 27.9,\n      "as_of": "2026-10-30",')
_NEW = _OLD.replace('"as_of": "2026-10-30",', '"as_of": "2026-11-02",')


def as_derived(ticker: str, text: str) -> str:
    """``text`` (a committed page) with LLY's one expected leaf moved, every other byte kept."""
    if ticker != "LLY" or _NEW in text:
        return text
    assert text.count(_OLD) == 1, (
        "LLY's committed valuation_basis.current_multiple moved: re-cut this allowance or delete "
        "it (the artifact PR restates LLY)")
    return text.replace(_OLD, _NEW)
