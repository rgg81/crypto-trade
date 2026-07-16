#!/usr/bin/env python3
"""Active entrypoint for the amended Top-40 V2 tournament."""

from __future__ import annotations

from crypto_trade.tournament.runner_schema3_compat_v4 import main

if __name__ == "__main__":
    raise SystemExit(main())
