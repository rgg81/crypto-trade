#!/usr/bin/env python3
"""Current additive entrypoint for the frozen Top-40 V2 tournament."""

from __future__ import annotations

from crypto_trade.tournament.amended_orchestrator_compat_v3 import main

if __name__ == "__main__":
    raise SystemExit(main())
