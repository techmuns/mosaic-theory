"""THE VALUE COMPARATOR — two JSON documents, compared leaf by leaf, list members included.

ONE comparator for every "what moved" question about a page: the impact check's base-vs-head
pages (`vinci.impact`), and the pre-spend check's committed-vs-fresh page
(`vinci.dossier.prespend`, TeamNostra RD-D4: it compared presence only and skipped every Sourced
field inside a list, while its verdict said nothing present was lost).

WHAT A CHANGE IS. Every leaf (a scalar) that differs, every key present on one side only, and
every list member present on one side only, each with its dotted path and the ``source_ref`` of the
nearest Sourced field (a dict carrying ``value`` + ``status``) that holds it — so a moved number is
printed beside the citation the reader would check. A value is compared EXACTLY: the same code on
the same inputs writes the same float, so a tolerance would only hide a change.

LIST MEMBERS, matched by identity, never by position alone (`_match`):

1. a list of scalars is compared as members: what one side holds and the other does not, and, when
   both hold the same members, whether their ORDER moved (a reordered list is a change);
2. a list of dicts is keyed by the first of `KEY_FIELDS` that every member carries, unique on both
   sides (a row by its ``label``, a filing by its ``accession``) — then each member is compared by
   its key, so inserting one row moves one row, not every row after it;
3. otherwise, members equal on both sides are paired first, and the rest are paired in order.

A list of records whose shared members changed ORDER also carries one ``[order]`` change
(`_order_move`): matching by identity would otherwise hide a reordering.

NOT COMPARED: a key in ``ignore`` (the build's own clock, `VOLATILE`), anywhere in the tree.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

#: The build's own clock: two builds of one page on one input differ here by construction.
VOLATILE = frozenset({"assembled_at", "computed_at"})

#: The build's clock written INTO a string: the assembly log's fetch time
#: (`mechanical.assemble_mechanical`: "… 10-Q parsed (+1.5s fetch)"). Normalised before any
#: comparison, the rest of the string compared as written.
CLOCK_TEXT = ((re.compile(r"\(\+\d+(?:\.\d+)?s fetch\)"), "(+…s fetch)"),
              # the rendered page's own assembly instant ("· assembled 2026-11-11 05:24 UTC")
              (re.compile(r"assembled \d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC"), "assembled <clock>"))


def clock_text(text: str) -> str:
    for pat, to in CLOCK_TEXT:
        text = pat.sub(to, text)
    return text


def _unclock(v: Any) -> Any:
    if isinstance(v, str):
        return clock_text(v)
    if isinstance(v, Mapping):
        return {k: _unclock(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_unclock(x) for x in v]
    return v

#: The fields a list member is identified by, tried in order (`_list_key`).
KEY_FIELDS = ("id", "key", "ticker", "label", "name", "metric", "field", "kind", "term",
              "family", "gap_date", "accession", "period", "fiscal_year", "date", "as_of",
              "filing_date", "bar_date", "file", "source_url", "url", "role", "quote")


class _Absent:
    """The value on the side that does not hold a key or a member."""

    _instance: _Absent | None = None

    def __new__(cls) -> _Absent:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "ABSENT"


ABSENT: Any = _Absent()


@dataclass(frozen=True)
class Change:
    """One leaf, key or list member that differs. ``base``/``head`` are JSON values or `ABSENT`.
    ``source_ref`` is the nearest Sourced field's citation, head's where head holds it."""

    path: str
    base: Any
    head: Any
    source_ref: str | None
    #: the dotted path of the Sourced field holding this leaf, or None outside any
    sourced: str | None = None

    @property
    def kind(self) -> str:
        if self.base is ABSENT:
            return "added"
        if self.head is ABSENT:
            return "removed"
        return "changed"

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "kind": self.kind, "base": _plain(self.base),
                "head": _plain(self.head), "source_ref": self.source_ref,
                "sourced": self.sourced}


def _plain(v: Any) -> Any:
    return "ABSENT" if v is ABSENT else v


def is_sourced(node: Any) -> bool:
    return isinstance(node, Mapping) and "value" in node and "status" in node


def show(v: Any, limit: int = 160) -> str:
    """A value for a report line. A long value says how much it leaves out — never a silent cut."""
    if v is ABSENT:
        return "ABSENT"
    text = v if isinstance(v, str) else json.dumps(v, sort_keys=True, ensure_ascii=False)
    text = text.replace("\n", "\\n")
    if len(text) <= limit:
        return repr(text) if isinstance(v, str) else text
    shown = text[:limit]
    return (repr(shown) if isinstance(v, str) else shown) + f"…(+{len(text) - limit} chars)"


def cut(text: str, limit: int) -> str:
    """``text`` cut at ``limit``, saying how much it leaves out — never a silent cut."""
    return text if len(text) <= limit else text[:limit] + f"…(+{len(text) - limit} chars)"


def _canon(v: Any) -> str:
    return json.dumps(v, sort_keys=True, ensure_ascii=False, default=str)


def _list_key(base: Sequence[Any], head: Sequence[Any]) -> tuple[str, ...] | None:
    """The first of `KEY_FIELDS` every member of both lists carries as a scalar, unique on each
    side; else the first PAIR of them that is (two filings of one accession are told apart by
    their gap dates, never by position); else None."""
    members = [*base, *head]
    if not members or not all(isinstance(m, Mapping) for m in members):
        return None
    carried = [k for k in KEY_FIELDS
               if all(isinstance(m.get(k), (str, int, float)) and not isinstance(m.get(k), bool)
                      for m in members)]

    def unique(keys: tuple[str, ...]) -> bool:
        return all(len({_canon([m[k] for k in keys]) for m in side}) == len(side)
                   for side in (base, head))

    for key in carried:
        if unique((key,)):
            return (key,)
    for i, a in enumerate(carried):
        for b in carried[i + 1:]:
            if unique((a, b)):
                return (a, b)
    return None


def _match(base: Sequence[Any], head: Sequence[Any]
           ) -> list[tuple[str, Any, Any]]:
    """Pairs ``(label, base member or ABSENT, head member or ABSENT)`` — see the module docstring
    for the three rules."""
    keys = _list_key(base, head)
    if keys is not None:
        b = {_canon([m[k] for k in keys]): m for m in base}
        h = {_canon([m[k] for k in keys]): m for m in head}
        order = list(b) + [k for k in h if k not in b]
        return [("[" + ",".join(f"{k}={(b[c] if c in b else h[c])[k]}" for k in keys) + "]",
                 b.get(c, ABSENT), h.get(c, ABSENT)) for c in order]
    # equal members first, then the rest in order
    pairs: list[tuple[str, Any, Any]] = []
    head_left = list(range(len(head)))
    head_canon = [_canon(m) for m in head]
    unmatched_base: list[int] = []
    for i, m in enumerate(base):
        c = _canon(m)
        j = next((j for j in head_left if head_canon[j] == c), None)
        if j is None:
            unmatched_base.append(i)
        else:
            head_left.remove(j)
            pairs.append((f"[#{i}]", m, head[j]))
    for i, j in zip(unmatched_base, head_left, strict=False):
        pairs.append((f"[#{i}]", base[i], head[j]))
    for i in unmatched_base[len(head_left):]:
        pairs.append((f"[#{i}]", base[i], ABSENT))
    for j in head_left[len(unmatched_base):]:
        pairs.append((f"[+#{j}]", ABSENT, head[j]))
    return pairs


def _order_move(base: Sequence[Any], head: Sequence[Any]) -> tuple[list[Any], list[Any]] | None:
    """The members BOTH lists hold, in each side's order, when that order differs — else None.

    Matching by identity (`_match`) pairs a member wherever it sits, so a reordered list of records
    (a ranked list, bull/bear points in their deterministic order) would otherwise read as no
    change. Keyed lists compare their keys (a member joining or leaving is not a reorder); unkeyed
    ones only a pure permutation (the same members, in a different order)."""
    keys = _list_key(base, head)
    if keys is not None:
        kb = [_canon([m[k] for k in keys]) for m in base]
        kh = [_canon([m[k] for k in keys]) for m in head]
        both = set(kb) & set(kh)
        ob, oh = [x for x in kb if x in both], [x for x in kh if x in both]
        if ob == oh:
            return None
        return ([json.loads(x) for x in ob], [json.loads(x) for x in oh])
    cb, ch = [_canon(m) for m in base], [_canon(m) for m in head]
    if cb == ch or Counter(cb) != Counter(ch):
        return None
    return (list(base), list(head))


def _scalar_list(v: Sequence[Any]) -> bool:
    return all(not isinstance(m, (Mapping, list)) for m in v)


def _surplus(members: Sequence[Any], extra: Counter[str]) -> list[Any]:
    """The members of ``members`` that ``extra`` counts, in their own order, each as often as
    counted."""
    left = Counter(extra)
    out: list[Any] = []
    for m in members:
        c = _canon(m)
        if left[c] > 0:
            left[c] -= 1
            out.append(m)
    return out


def value_changes(base: Any, head: Any, *, ignore: Iterable[str] = VOLATILE,
                  path: str = "") -> list[Change]:
    """Every change from ``base`` to ``head`` (see the module docstring), in a stable order: the
    keys of a dict sorted, the members of a list in `_match`'s order."""
    skip = frozenset(ignore)
    out: list[Change] = []

    def ref_of(b: Any, h: Any) -> str | None:
        for node in (h, b):
            if is_sourced(node) and node.get("source_ref") is not None:
                return str(node.get("source_ref"))
        return None

    def walk(b: Any, h: Any, at: str, ref: str | None, sourced: str | None) -> None:
        if is_sourced(b) or is_sourced(h):
            ref, sourced = ref_of(b, h) or ref, at
        if isinstance(b, Mapping) and isinstance(h, Mapping):
            for k in sorted(set(b) | set(h), key=str):
                if k in skip:
                    continue
                walk(b.get(k, ABSENT), h.get(k, ABSENT), f"{at}.{k}" if at else str(k), ref,
                     sourced)
            return
        if isinstance(b, list) and isinstance(h, list):
            if _scalar_list(b) and _scalar_list(h):
                bc, hc = Counter(_canon(m) for m in b), Counter(_canon(m) for m in h)
                if bc == hc:
                    if [_canon(m) for m in b] != [_canon(m) for m in h]:
                        out.append(Change(f"{at}[order]", b, h, ref, sourced))
                    return
                out.extend(Change(f"{at}[-]", m, ABSENT, ref, sourced)
                           for m in _surplus(b, bc - hc))
                out.extend(Change(f"{at}[+]", ABSENT, m, ref, sourced)
                           for m in _surplus(h, hc - bc))
                return
            for label, mb, mh in _match(b, h):
                walk(mb, mh, f"{at}{label}", ref, sourced)
            if (order := _order_move(b, h)) is not None:
                out.append(Change(f"{at}[order]", order[0], order[1], ref, sourced))
            return
        if (b is ABSENT) != (h is ABSENT) or (b is not ABSENT and _canon(b) != _canon(h)):
            out.append(Change(at, b, h, ref_of(b, h) or ref, sourced))

    walk(_unclock(base), _unclock(head), path, None, None)
    return out


@dataclass(frozen=True)
class SourcedPair:
    """One outermost Sourced field (a Sourced value is not descended into: its status speaks for
    what it carries), as each side holds it — the dict, or `ABSENT` where that side has none."""

    path: str
    base: Any
    head: Any
    #: inside a list member (matched by identity, `_match`)
    in_list: bool
    #: one side lacks the WHOLE list member holding this field — the member left (or joined) the
    #: list, as a list's population moves with the calendar; not the field going missing inside a
    #: member both sides hold
    member_moved: bool

    def status(self, side: str) -> str:
        node = self.base if side == "base" else self.head
        if node is ABSENT or node is None:   # an Optional Sourced field written as null
            return "absent"
        return str(node.get("status")) if is_sourced(node) else "not sourced"

    def changes(self, ignore: Iterable[str] = VOLATILE) -> list[Change]:
        return value_changes(self.base, self.head, ignore=ignore, path=self.path)


def sourced_pairs(base: Any, head: Any, *, ignore: Iterable[str] = VOLATILE) -> list[SourcedPair]:
    """Every outermost Sourced field either side holds, paired across the two — list members by
    identity (`_match`), so a field inside a list is compared with the same member's field."""
    skip = frozenset(ignore)
    out: list[SourcedPair] = []

    def walk(b: Any, h: Any, at: str, in_list: bool, moved: bool) -> None:
        if is_sourced(b) or is_sourced(h):
            out.append(SourcedPair(at, b, h, in_list, moved))
            return
        if isinstance(b, Mapping) or isinstance(h, Mapping):
            bm = b if isinstance(b, Mapping) else {}
            hm = h if isinstance(h, Mapping) else {}
            for k in sorted(set(bm) | set(hm), key=str):
                if k not in skip:
                    walk(bm.get(k, ABSENT), hm.get(k, ABSENT), f"{at}.{k}" if at else str(k),
                         in_list, moved)
            return
        if isinstance(b, list) or isinstance(h, list):
            bl = b if isinstance(b, list) else []
            hl = h if isinstance(h, list) else []
            for label, mb, mh in _match(bl, hl):
                walk(mb, mh, f"{at}{label}", True, moved or ((mb is ABSENT) != (mh is ABSENT)))

    walk(base, head, "", False, False)
    return out


_MEMBER = re.compile(r"\[[^\]]*\]")


def family(path: str) -> str:
    """A path with every list member's label collapsed: ``a[label=X].b[#2]`` → ``a[].b[]``."""
    return _MEMBER.sub("[]", path)


def member_families(doc: Any) -> Counter[str]:
    """How many members each list family holds in ``doc`` (``releases[].guidance[]``: every
    guide on the page)."""
    out: Counter[str] = Counter()

    def walk(n: Any, at: str) -> None:
        if isinstance(n, Mapping):
            for k, v in n.items():
                walk(v, f"{at}.{k}" if at else str(k))
        elif isinstance(n, list):
            out[at + "[]"] += len(n)
            for m in n:
                walk(m, at + "[]")

    walk(doc, "")
    return out


def moved_members(paths: Iterable[str]) -> Counter[str]:
    """For change paths, how many DISTINCT members of each list family hold a change."""
    seen: set[tuple[str, str]] = set()
    for p in paths:
        for m in _MEMBER.finditer(p):
            member = p[:m.end()]
            seen.add((family(member), member))
    return Counter(f for f, _ in seen)
