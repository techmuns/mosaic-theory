"""Resolver errors — the resolver **fails loud** rather than guessing.

Mis-resolution (joining the wrong company's data) is the system's #1 failure mode, so ambiguity
is an error, never a silent best-guess.
"""

from __future__ import annotations


class ResolutionError(Exception):
    """Base for all resolver failures."""


class UnknownSymbolError(ResolutionError):
    """The input does not match any known US issuer/security (e.g. a renamed/delisted ticker)."""


class AmbiguousResolutionError(ResolutionError):
    """The input matches more than one issuer — resolving would require a guess, so we refuse."""
