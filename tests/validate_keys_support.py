"""The `validate-keys` script and workflow, for the tests that pin them — one loader, so a key
check's pins never depend on another feature's test module."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / ".github" / "scripts" / "validate_keys.py"
VALIDATE_WORKFLOW = ROOT / ".github" / "workflows" / "validate-keys.yml"


def validator() -> Any:
    """The `validate-keys` script, loaded as a module (it is not a package)."""
    spec = importlib.util.spec_from_file_location("validate_keys", VALIDATOR)
    assert spec is not None and spec.loader is not None
    vk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vk)
    return vk
