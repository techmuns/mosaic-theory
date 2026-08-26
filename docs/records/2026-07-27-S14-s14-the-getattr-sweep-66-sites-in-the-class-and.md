---
id: S14
status: shipped
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**S14. THE `getattr` SWEEP — 66 SITES IN THE CLASS, AND THE RULE'S OWN LIMIT FOUND. NOTHING FIXED.**
(2026-08-01; D15 says run the check where the class recurs, so it was run.)

AST sweep of `vinci/`: **82 defaulting `getattr(obj, name, default)` calls**, of which **75 name a
constant attribute** (7 are genuinely dynamic — f-string or loop-variable names). Each of the 75 was
mechanically rewritten to direct attribute access in a scratch copy and the whole package
type-checked ONCE:

| outcome of rewriting to `obj.attr` | sites |
|---|---|
| **mypy-clean — the object is typed and the attribute exists** | **66** |
| mypy errors (`attr-defined` / `union-attr`) — NOT the class | 9 |

The 9 that error are the legitimate uses, and they are legitimate for three different reasons:
`themes/exposure.py:584` (`BaseException.status_code` — genuinely dynamic on an HTTP exception
subclass); `screens/run.py:246,257` (`rec: object` — an untyped boundary, exactly as #305 recorded);
`render.py:585,2053,2072` (`X | None` — the getattr is standing in for a None-guard, which is a
RESTRUCTURE, not a swap).

The 66 by file: render.py 21 · assemble.py 16 · synthesis.py 9 · cli.py 7 · materiality.py 6 ·
mechanical.py 4 · freshness.py 1 · graph/llm.py 1 · themes/classify.py 1.
By default: 40 `None` · 9 `[]` · 8 `False` · 4 `''` · 2 `True` · 1 each `'assemble'`, `'$M'`,
`'EV/EBITDA'`.

**NOTHING WAS FIXED, AND THIS IS WHY — the sweep falsified its own screening test.**
"Rewrites mypy-clean" looked like a proof that the default is dead code. It is not. Measured:

    a: argparse.Namespace
    mypy --strict on `a.show_proposal`  ->  Success: no issues found
    runtime `ns.show_proposal`          ->  AttributeError: 'Namespace' object has no attribute …

typeshed gives `argparse.Namespace` a `__getattr__(self, name: str) -> Any`, so **mypy accepts ANY
attribute on it** — and `cli.py`'s 7 sites are all `getattr(args, …)`, where the default is doing
REAL work because different subparsers set different attributes. Swapping those ships an
`AttributeError` into the CLI.

**SO THE RULE FROM #305 NARROWS.** *A defaulting `getattr` on a typed model is an un-typing
operation* — TRUE, and it still holds for models that DECLARE their fields. It does NOT hold for
types with a permissive `__getattr__`, where mypy's silence means nothing. **The sound test is not
mypy: it is whether the attribute is a declared field on the object's model** (`model_fields` for a
pydantic model), which is verifiable at runtime rather than inferred. Establishing that per-site
across 66 sites is real work with real crash risk in the renderer, and it is not a mechanical
sweep — so it is REPORTED, not attempted, and the count above is the worklist.

**INVARIANT: none shipped.** No guard was added, because the sound discriminator (declared-field
membership) is not yet expressible as a lint without the per-site type resolution this entry defers.
Recorded as accepted risk with its worklist rather than closed with a check that would repeat the
mypy mistake one level up.
