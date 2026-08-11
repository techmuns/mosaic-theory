"""The follow list, read as a WHOLE — which followed names belong to which sleeve.

`vinci/dossier/assemble.py` reads this same file one ticker at a time (``_follow_entry``), because
assembly asks a per-name question: is THIS name followed, and why. The passive baseline asks the
complementary one — which names would I have held if I had simply indexed the book — and that needs
the whole list at once.

WHY NOT REUSE THE DOSSIER READER: the scoring package must not import the dossier package (the same
layering the ledger already observes — see `vinci/cli.py` `_followed_identity`, resolved in the CLI
for exactly this reason). And this module cannot live in `vinci/sleeves.py` either: that registry
states out loud that it "must stay importable from anywhere" and imports nothing but `dataclasses`,
so putting file I/O in it would cost the property its own docstring promises.

TWO PARSERS OF ONE FILE IS A BUG CLASS THIS REPO HAS ALREADY PAID FOR, so the divergence is pinned
rather than hoped away: `tests/test_followed_list.py` asserts this reader and the dossier's agree on
the sleeve of every ticker in the COMMITTED `data/followed.json`, and that both refuse the same
malformed shapes. This reader is deliberately the stricter-or-equal of the two — it never skips an
entry it cannot classify, because a name that silently vanishes here does not vanish loudly: it
quietly shrinks the basket the sleeve is measured against, which moves the kill test's answer.
"""

from __future__ import annotations

import json
from pathlib import Path

from vinci.sleeves import require_sleeve


class FollowedListError(ValueError):
    """The follow list exists but cannot be read as a follow list."""


def followed_by_sleeve(path: Path) -> dict[str, tuple[str, ...]]:
    """Map each sleeve key → the tickers followed under it, sorted.

    An ABSENT file is the normal state (nothing is followed yet) → ``{}``. Anything else that
    cannot be read raises: a follow list that half-parses would silently redefine the basket.
    """
    if not path.exists():
        return {}
    try:
        doc = json.loads(path.read_text())
    except ValueError as exc:
        raise FollowedListError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(doc, dict):
        raise FollowedListError(
            f"{path} must be a JSON object mapping TICKER → {{reason, sleeve}}, "
            f"got {type(doc).__name__}")

    by_sleeve: dict[str, list[str]] = {}
    seen: set[str] = set()
    for raw_key, entry in doc.items():
        ticker = str(raw_key).upper()
        # THE SAME CASE-COLLISION REFUSAL THE DOSSIER READER MAKES. Folding `{"uber":…, "UBER":…}`
        # to one key would drop a member of the basket with nothing anywhere saying so.
        if ticker in seen:
            raise FollowedListError(
                f"{path}: {ticker} is listed more than once (keys differing only by case) — one "
                f"entry would be silently discarded. Merge them into a single entry.")
        seen.add(ticker)
        # A BARE STRING IS THE PRE-SLEEVE SHAPE, and it is refused here for the reason it is
        # refused at assembly: an untagged followed name has no sleeve, so it belongs to no
        # basket, and guessing one would put a megacap in whichever book happened to ask first.
        if not isinstance(entry, dict):
            raise FollowedListError(
                f"{path}: {ticker} must be an object with 'reason' and 'sleeve', got "
                f"{type(entry).__name__} — every followed name states which strategy book it is "
                f"judged under.")
        sleeve = require_sleeve(entry.get("sleeve"), where=f"{path}: {ticker}")
        by_sleeve.setdefault(sleeve, []).append(ticker)
    return {k: tuple(sorted(v)) for k, v in sorted(by_sleeve.items())}
