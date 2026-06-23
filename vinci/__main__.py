"""Enable ``python -m vinci`` as the robust entrypoint (run from the repo root).

Note: the ``vinci`` console script (from ``[project.scripts]``) works after a regular
``pip install .`` / a built wheel. Editable installs (``pip install -e .``) rely on a ``.pth``
path injection that is unreliable on some Python 3.14 builds, so for local dev and CI we invoke
``python -m vinci`` from the repo root (pytest manages its own path independently).
"""

from __future__ import annotations

import sys

from vinci.cli import main

if __name__ == "__main__":
    sys.exit(main())
