#!/usr/bin/env python3
"""Fast Team 12 paper health and performance report.

This command reads the current sealed paper artifacts and process state.  It
deliberately does not launch the multi-year parity replay.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(relative: str) -> int:
    completed = subprocess.run(
        (sys.executable, str(ROOT / relative)),
        cwd=ROOT,
        check=False,
    )
    return completed.returncode


def main() -> int:
    health_status = _run("scripts/team12_paper_healthcheck.py")
    digest_status = _run("scripts/team12_paper_digest.py")
    return health_status or digest_status


if __name__ == "__main__":
    raise SystemExit(main())
