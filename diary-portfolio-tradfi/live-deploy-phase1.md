# Live-Deploy Phase 1 — parity bridge + reconciliation (iter-016)

**Goal.** Prove the live desk can reproduce the confirmed baseline (iter-016 BEAR-GATED TSMOM)
DEPLOYED weight book BIT-FOR-BIT from on-disk history, BEFORE building the paper engine. Mirror the
metals track's proven `live_weights.py` / `reconcile_metals.py` / `deployed_from_raw` pattern.

Baseline chain: `iter_016` → `iter_013` (combined+VIX) → `iter_011` (mom+0.5·LTR) → `iter_006`
(EW-252d bear gate) → `iter_005`/`iter_002` → `core_tradfi` (`net_from_raw` / `vol_target`). Book:
`(1−0.25·(1−g))·[mom+0.5·LTR] + 0.25·(1−g)·TSMOM`, g = EW-252d bear-state; band δ=0.010 daily;
portfolio vol-target 15%/yr (cap 5×); iter-008 VIX brake (base=20 / floor=0.50). 69 Yahoo names + VIX.

## What shipped (3 files + this diary + a test)
1. **`iter_016_bear_gated_tsmom.deployed_weights(pn, s_vix=None, data_dir=None) -> (net, deployed_w)`**
   — Task-1 extractor. Mirrors metals `universe_metals.deployed_from_raw`: decomposes the DEPLOYED
   position book the desk HOLDS from the SAME arithmetic as the backtest net (no two-stream drift):
   `deployed_w[t] = w_banded[t] · vol_target_scale[t] · s_vix[t]`, with
   `net[t] = Σ deployed_w[t]·ret_fwd[t] − scale[t]·s_vix[t]·cost[t]`. `net` reproduces the backtest's
   `deployed_metrics` d1x (VIX-ON 1x) bit-for-bit (max|Δ| = 0.0, Sharpe +0.7276). ADDED function only
   — no signal touched.
2. **`live_weights_tradfi.py`** — Task-2 parity bridge. `deployed_target_weights(as_of, data_dir)`
   recomputes-from-full-history sliced to `≤ as_of` and returns the deployed book row (dict) the desk
   should hold as of `as_of`. Parity BY CONSTRUCTION — it calls `iter_016.deployed_weights`, never a
   reimplementation.
3. **`reconcile_tradfi.py`** — Task-3 reconcile. Truncates history to each `as_of`, recomputes, and
   asserts the last row == the full-backtest `deployed_w.loc[as_of]` BIT-EXACT (tol 1e-10) at
   phase-diverse dates + a dense recent sweep. Part (2) quantifies the live forming-bar proxy gap.
4. Two tests appended to `tests/test_portfolio_tradfi_foundation.py` (skip when data absent).

## The one real bug this surfaced (ragged-panel / forming-bar)
Metals `deployed_from_raw` does `net0 = (pnl−cost).dropna()` THEN `vol_target_scale(net0)`, and
reindexes the scale onto `w.index` with `.fillna(0.0)`. On the LATEST bar the forward return is NaN
(no next open), so `net0` loses that index, the scale reindex fills 0, and the last deployed row
collapses to **all-zeros** — i.e. "the book to hold now" would be empty. The extractor computes the
vol-target scale on the **NON-`dropna`** `net0`: because `vol_target_scale` reads `net0` only through
`t−1` (its own `.shift(1)`), `scale[as_of]` stays VALID and causal even though `net0[as_of]` is NaN.
Result: the latest bar (2026-06-30) carries a real 69-name book (gross 0.69) that reconciles
bit-exact. `net` is then `.dropna`-ed so it still matches the backtest d1x on the valid bars exactly.

## Results
Deployed-weights extractor gives the REAL held book (not the pre-scale unit gross):
- mean gross Σ|w| = **1.75** (vol-target-scaled leverage, ≤ 5× cap; median 1.80, max 5.0) — NOT unit
  gross. `gross == scale·s_vix` to 0.0 (banded book is unit-gross by construction).
- net-long fraction Σw/Σ|w| = **+0.160** (matches iter-016 `nlong` +0.161) — the small bear-gated
  TSMOM β-tilt; ~sector/dollar-neutral otherwise (0.75 neutral engine + 0.25 gated TSMOM).
- bit-consistency `net == Σ deployed·ret_fwd − scaled cost`: max|Δ| = 1.4e-17.

Reconcile — live == backtest deployed weights **BIT-EXACT** (tol 1e-10):

| as_of | phase | gross | max|Δw| recompute | max|Δw| public API |
|---|---|---|---|---|
| 2018-05-15 | mid-history | 1.86 | 8.3e-17 | 8.3e-17 |
| 2018-05-02 | month boundary | 1.66 | 2.8e-17 | 2.8e-17 |
| 2026-06-30 | latest bar (forming-adjacent) | 0.69 | 0.0 | 0.0 |
| 2022-11-23 | **bear-gate firing** (lam_eff=0) | 1.61 | 2.8e-17 | 2.8e-17 |
| 2022-03-02 | **band hold** (no re-snap) | 0.57 | 2.1e-17 | 2.1e-17 |
| last 40 bars | dense sweep | — | 0.0 | — |

Worst overall = **8.3e-17** (machine eps), ≪ 1e-10. Live forming-bar proxy gap (open ≈ prior close,
informational) = 8.75e-04 ≪ 5e-2 — the expected next-open approximation only.

## Leak-safety
`as_of` slicing is past-only; every input is causal (`close.shift` / `rolling` / `.shift(1)` lag, the
EW-252d bear gate, past-only vol-target + VIX scalars), so the truncated recompute's `as_of` row is
provably identical to the full-history book — the reconcile is the empirical proof at 6 phase-diverse
dates + a 40-bar sweep.

## Phase-2 DEPLOYMENT TODO (documented, NOT solved here)
**PERP-VS-UNDERLYING BASIS.** Backtest is priced on Yahoo UNDERLYING total-return daily bars; live
fills on Binance single-stock TradFi PERPS. The target WEIGHTS are identical (same signal, same book)
— but the fill-price basis differs (perp mark vs underlying close, funding, overnight/weekend gaps).
Phase 2 maps each `<STEM>` → `<STEM>USDT` perp, sizes in perp notional, and accounts for basis +
funding drag. Flagged in the `live_weights_tradfi` header + the CLI note.

## Suite
Portfolio-tradfi track fully GREEN: `test_portfolio_tradfi_foundation.py` 68 passed (2 skipped =
crypto-parity needing 8h data), including the 2 new reconcile tests. The 266 crypto v1/v2/v3 failures
in the full run are pre-existing worktree drift (stale `run_baseline_v1` symbol renames + seed-rule
changes) — outside this track, none import the tradfi modules, none touched by this change.

**Read:** the parity foundation is SOLID. The live path reuses the backtest deployed-weights code and
reproduces it bit-for-bit at every tested phase incl. the two hard cases (bear-gate firing + latest
forming-adjacent bar). Safe to build the paper engine on top.
