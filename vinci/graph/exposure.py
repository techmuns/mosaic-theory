"""On-demand exposure lookup over the extracted graph — the graph's REAL role: discriminator input.

Test 1 falsified the graph as a standalone trading signal: two clean nulls on the de-confounded
column; supply-chain momentum is a ~17-year-old published, arbitraged (i.e. replicable) anomaly; and
its "hub-down → dependent-down" direction is an un-tradeable short for a long-only small/mid book.

Its non-replicable value is COGNITIVE, not mechanical: when a real event hits a node (a sanction,
export curb, capacity/supply shock, regulatory action), instantly return the full cross-section of
exposed names — including multi-hop downstream small-caps a human wouldn't assemble by hand — as a
candidate list for the *manual* A/B/C discriminator. This gates nothing and runs no statistics; it
widens research. It is validated OPERATIONALLY against a hand-built baseline on live events (is it
faster, broader, surfaces names I'd have missed?), never by a backtest — so it can't be mined.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from vinci.resolver import AmbiguousResolutionError, EntityResolver, UnknownSymbolError
from vinci.resolver.index import normalize_name


@dataclass(frozen=True)
class ExposedName:
    """A name reachable from the query entity, with the provenance chain that connects it."""

    node_id: str
    name: str
    ticker: str | None
    hops: int
    path: list[str]  # human-readable provenance: each "A —rel→ B (evidence)" link in the chain


@dataclass
class ExposureGraph:
    """Undirected reachability over the extracted who-names-whom edges, with per-edge provenance."""

    adj: dict[str, list[tuple[str, str]]] = field(default_factory=dict)  # node->[(neighbor,link)]
    display: dict[str, tuple[str, str | None]] = field(default_factory=dict)  # node->(name,ticker)

    @classmethod
    def from_edges(cls, edges: list[dict[str, Any]]) -> ExposureGraph:
        g = cls()
        for e in edges:
            focal = f"US:{e['focal_cik']}"
            cp = e["node_id"]
            g.display.setdefault(focal, (e["focal_ticker"] or focal, e.get("focal_ticker")))
            g.display.setdefault(cp, (e["counterparty_name"], e.get("counterparty_ticker")))
            link = f"{e['focal_ticker']} —{e['relationship_type']}→ {e['counterparty_name']}"
            ev = (e.get("evidence") or "").strip()
            if ev:
                link += f' ["{ev[:80]}"]'
            g.adj.setdefault(focal, []).append((cp, link))
            g.adj.setdefault(cp, []).append((focal, link))
        return g

    def resolve(self, query: str, resolver: EntityResolver | None = None) -> str | None:
        """Map a ticker / name to a graph node id, or None if the entity isn't in the graph."""
        if query in self.adj:
            return query
        if resolver is not None:
            try:
                nid = f"US:{resolver.resolve_ticker(query).cik}"
                if nid in self.adj:
                    return nid
            except (UnknownSymbolError, AmbiguousResolutionError):
                pass
        nq = normalize_name(query)
        for nid, (name, _t) in self.display.items():
            if normalize_name(name) == nq or nid == f"NAME:{nq}":
                return nid
        return None

    def exposed_within(self, start: str, *, hops: int = 2) -> list[ExposedName]:
        """BFS from ``start`` up to ``hops`` links away → exposed names + provenance chains."""
        seen = {start}
        out: list[ExposedName] = []
        q: deque[tuple[str, int, list[str]]] = deque([(start, 0, [])])
        while q:
            node, dist, path = q.popleft()
            if dist >= hops:
                continue
            for neighbor, link in self.adj.get(node, []):
                if neighbor in seen:
                    continue
                seen.add(neighbor)
                name, ticker = self.display.get(neighbor, (neighbor, None))
                out.append(ExposedName(neighbor, name, ticker, dist + 1, [*path, link]))
                q.append((neighbor, dist + 1, [*path, link]))
        return sorted(out, key=lambda x: (x.hops, x.name))
