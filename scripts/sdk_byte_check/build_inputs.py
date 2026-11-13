"""Step 2 of the SDK byte check: every committed page built at $0 by `python -m vinci.impact run`,
its synthesis inputs saved by `impact_capture.py`. The only change to the impact check is which
capture module its child loads. Arguments are `vinci.impact`'s own (`capture.py` has the call).
"""
from __future__ import annotations

import sys
from pathlib import Path

from vinci.impact import __main__ as impact
from vinci.impact import run as impact_run

impact_run.CAPTURE_CHILD = Path(__file__).resolve().with_name("impact_capture.py")

if __name__ == "__main__":
    sys.exit(impact.main(sys.argv[1:]))
