#!/usr/bin/env python3
"""Retired historical entrypoint after prospective Top40 V3 Amendment 0001."""

import sys

_MESSAGE = (
    "Top40 V3's historical organizer entrypoint is retired; use "
    "scripts/top40_v3_amendment_0001.py"
)


if __name__ == "__main__":
    sys.stderr.write(_MESSAGE + "\n")
    raise SystemExit(2)
