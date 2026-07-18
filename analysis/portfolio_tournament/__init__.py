"""crypto-cup-01 — tournament evaluator package (crypto port of the tradfi-cup-01 stack).

Modules mirror the proven tradfi tournament layout:
  constants   — splits, caps, cost model, paths, append-only journal
  universe    — full-pool weekly PIT top-40 mask + membership unions (organizer-only)
  snapshot    — frozen IS snapshot build + SHA-256 manifest + tamper verification
  engine      — organizer-owned scoring (eligibility, caps, lag, cost, slippage, funding, VT)
  protocol    — strategy loading + SHA-bound submission freeze / mutation check
  harness     — 6-check leak harness (scan/determinism/truncation/corruption/same-bar/widening)
  leaderboard — team IS runs, byte-identical reproduction, Stage-1 ranking
  holdout     — sealed Stage-2 evaluator (double-gated, journaled, IS-replay checked)
  teamlib     — the ONLY module team strategies may import (pure metric helpers)
  cli         — single front door for teams and the orchestrator
"""
