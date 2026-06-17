"""``mosaic`` command-line entrypoint.

Grown one subcommand per build step. Today: ``resolve`` (step 1). Later: ``refresh`` (steps 3–4),
``screen`` (step 5), ``log-verdict`` (step 6), ``score`` (step 7).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from mosaic.resolver import EntityResolver, ResolutionError


def _cmd_resolve(args: argparse.Namespace) -> int:
    """Resolve tickers and print the identity table (face-validity eyeballing)."""
    resolver = EntityResolver.from_config()
    header = f"{'INPUT':<10}{'CIK':<12}{'TICKER':<8}{'EXCH':<14}{'EOD':<8}{'SIC':<6}{'NAME'}"
    print(header)
    print("-" * len(header))
    exit_code = 0
    for raw in args.tickers:
        try:
            ident = resolver.resolve_ticker(raw, enrich=args.enrich)
        except ResolutionError as exc:
            print(f"{raw:<10}FAIL-LOUD: {type(exc).__name__}: {exc}")
            exit_code = 0  # fail-loud is correct behaviour, not a CLI error
            continue
        print(
            f"{raw:<10}{ident.cik:<12}{ident.ticker:<8}{ident.exchange:<14}"
            f"{ident.eod_symbol:<8}{ident.sic or '-':<6}{ident.name}"
        )
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mosaic", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_resolve = sub.add_parser("resolve", help="resolve tickers to the canonical identity")
    p_resolve.add_argument("tickers", nargs="+", help="tickers to resolve (e.g. AAPL BRK.B)")
    p_resolve.add_argument(
        "--enrich", action="store_true", help="also fetch SIC sector from EDGAR submissions"
    )
    p_resolve.set_defaults(func=_cmd_resolve)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
