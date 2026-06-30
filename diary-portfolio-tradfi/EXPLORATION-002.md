# EXPLORATION-002 — Sector-relative momentum (iter-002)

**Date:** 2026-06-30
**Status:** COMPLETE — **PROMISING-DIRECTIONAL** (mechanism validated; net edge marginal, cost-limited). OOS HIDDEN.
**Cadence:** EXPLORATION (IS-only — `--confirm` NOT passed)
**Commit:** `5534e19f` · builds on iter-001 (NEGATIVE-CONFIRMED, IS −0.18)

---

## Hypothesis (Critic path-forward #1 from iter-001)

iter-001's plain dollar-neutral momentum lost (−0.18) on a ~62%-Semi/Tech-correlated universe where the
cross-sectional spread is dominated by sector-vs-sector drift (noise for momentum). **Demeaning the signal
WITHIN each sector** should isolate the idiosyncratic stock-level momentum (long-best-in-sector /
short-worst-in-sector) and remove the drift.

## Change (one)

Signal: `raw = sector_neutralize( (close.shift(21)/close.shift(252)-1) / rolling_63_rvol , SECTOR_MAP )`
— the iter-001 `mom/rvol` demeaned *within sector* instead of across the whole universe. Each sector nets
zero → dollar-neutral by construction (no separate `dollar_neutralize`). `analysis/portfolio/tradfi/iter_002_sector_rel.py`.
Single-name sectors (Health = LLY alone) are forced to 0 → 38 eligible names.

## IS numbers (trading-day; IS-only < 2025-03-24)

| Metric | iter-002 | iter-001 |
|--------|----------|----------|
| **Net Sharpe** | **+0.08** | −0.18 |
| Gross Sharpe (cost-off) | **+0.26** | −0.04 |
| Cost drag | +0.18 | +0.14 |
| Max Drawdown | −34.7% | −45.2% |
| Net total return | −1% | −26% |
| Turnover | 0.084 /day | 0.086 /day |
| N active | 32.7 / 38 eligible | 34 / 39 |
| Book | gross 1.0, per-sector-neutral to 3e-16 | dollar-neutral |

**Per-regime:** bull **+0.15** · bear **−0.10** · chop **−0.29** (positive in only 1 of 3 — not all-weather yet).
**Negated signal:** **−0.43** → the long form (best-in-sector long) carries the edge; not a sign artifact.

## Leak-check — PASS

New test asserts `build()` is dollar- AND per-sector-neutral on every active row, LLY zeroed, and the
production sector-relative signal is future-bar leak-safe. tradfi suite 18/18 green. (68 pre-existing
v1-runner failures are unrelated, verified by stash.)

## Verdict — PROMISING-DIRECTIONAL

The one change **flipped the sign** (−0.18 → +0.08, a +0.26 swing) and produced a **real +0.26 GROSS edge** —
sector-drift removal worked exactly as theorized, and the negation is worse, so the within-sector momentum
is directionally real. BUT net is only +0.08 (below the +0.30 bar): **turnover cost (+0.18 drag) eats most of
the gross edge**, and it's still bull-only (chop/bear negative). Kept as the new working direction; not promotable.

## Next

The prize is the +0.26 gross edge being half-eaten by cost. **iter-003 = causal hysteresis no-trade band**
(metals iter-011 / crypto iter-020 trick) to cut the ~21.7×/yr turnover and capture more of the gross —
the most direct lever on the +0.18 drag. After cost: revisit the signal (chop/bear weakness) — combine the
within-sector momentum with a second within-sector signal, or a regime/vol gate.
