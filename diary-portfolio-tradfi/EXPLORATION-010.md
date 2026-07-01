# EXPLORATION-010 — Regime-conditional beta-neutral overlay (iter-010)

**Date:** 2026-07-01
**Status:** COMPLETE — **REJECT** (chop lift is a beta-premium giveback, not alpha; washes net). OOS HIDDEN.
**Cadence:** EXPLORATION (IS-only, 15-yr data) · **Commit:** `c6b9059` · builds on iter-006 (+0.28)

## Hypothesis
iter-007 found a hard beta-neutral constraint lifted chop (+0.26→+1.05). Since chop is the biggest regime
(+0.51) and the crash-gate/VIX handle bear, a regime-conditional beta-neutral overlay might lift the whole book.

## IS numbers (2010-2025) vs iter-006 (+0.28 / +0.30 / −0.24 / +0.51)
| variant | net | bull | bear | chop | maxDD |
|---------|-----|------|------|------|-------|
| unconditional | +0.16 | +0.15 | −0.78 | **+0.75** | −34.7% |
| conditional (non-bear only) | +0.17 | +0.13 | −0.55 | +0.70 | −32.0% |
| partial 0.5× | +0.23 | +0.24 | −0.44 | +0.63 | −32.3% |

Realized net market-beta 0.118 → 0.000 (projection verified). Leak-safe (50 tests green). OOS hidden.

## Verdict — REJECT (stay iter-006)
The chop lift is REAL but is a **market-beta-premium giveback, not orthogonal alpha** — removing beta helps
chop yet collapses bear and washes net (+0.28→+0.16). Conditioning can't shield the bear (`g` fires only ~40%
of bear bars) and the projection breaks sector-neutrality. No variant beats iter-006.

## Significance
This closes the last strong Sharpe lever. The robust deliverable stands: **iter-006 (15-yr) net +0.28**
(VIX-insured +0.23, bear ~flat) — a validated, leak-free, all-weather-ish market-neutral momentum book at
~0.25 Sharpe. Obvious axes exhausted (reversal ✗, optimizer ✗, weekly ✗, low-vol ✗, residual-mom ✗,
beta-neutral ✗, stop-loss wash). Decision point: CONFIRMATION (re-Critic + OOS reveal) vs continue.
