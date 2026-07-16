#!/usr/bin/env python3
"""Amendment-aware entrypoint for the frozen Top-40 V2 orchestrator."""

from __future__ import annotations

from crypto_trade.tournament.amended_orchestrator_v2 import main

if __name__ == "__main__":
    raise SystemExit(main())
