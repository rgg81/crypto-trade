# Phase 7.5 Critic Review — iter-v1/034 (ETHUSDT) — PURE-DETERMINISTIC trend

OVERALL: **EXPLORATION-PROMISING → CONFIRMATION-MERGE** (the K=20 confirmation iter-035 completed
byte-identical to iter-034 after this review, satisfying the sole outstanding gate element). OOS +0.4148
is LEAK-FREE and REAL; determinism is SOUND; Pareto-dominates iter-027.

## Is the OOS +0.41 leak-free and real? YES.
Traced every data-access path the deterministic entry touches — NO look-ahead, NO new data access vs
iter-027:
- Entry-decision quantities strictly past-only: `_compute_trend_state` + `_compute_trend_strength` use
  `searchsorted(side="right")-1` (candle t-1); SMA/ATR/|dist_atr| built from `.shift(1)`. Future-candle
  inertness test passes.
- Conviction-gate q40 threshold fit on the TRAINING window only (`_tw_mask: >= train_start_ms & <
  train_end_ms`) — never the test month.
- Embargo intact: `walk_forward.py:113` `train_end_ms = test_start_ms - embargo_ms`; grep for the
  unsubtracted form = ZERO matches.
- Entry price = decision-bar CLOSE, decision uses only ≤ t-1 data (a full bar separates them) →
  conservative, no fill leak. Same mechanism as iter-027.
- Costs honest: `net_pnl_pct = pnl_pct - fee_pct - 2×(slippage_bps/100)` (matches trades.csv).
- Lift is mechanistically real: iter-034 catches the +30% July-2025 ETH uptrend that iter-027's model
  SKIPPED (took two losing July trades instead) — exactly the iter-030 thesis (deterministic entry
  catches OOS-generalizing trends the overfit model missed).
- A1/A2/A3 + foundation anti-patterns CLEAN.

## Is the determinism claim sound? YES.
- Model output TRULY unused: `lgbm.py:3143` `if deterministic_entry_only:` sets `_final_signed=100.0`,
  `_ensemble_std=0.0`, skips predict_proba/aggregation/no-consensus. Uniform `confidence=1.0` across all
  34 OOS trades (iter-027 varied 0.05-1.0) — the smoking gun of model bypass. SHORT-vote vs LONG-vote
  mock → identical entries.
- dispersion=0 genuine (specialist_dispersion.csv signed_weight_std=0.0 for all 1842 IS obs;
  basin_diagnostics cross_seed_sharpe_std=0.0).
- R3 OOD fit from training FEATURES (no seed, no predictions) → K/n_trials invariant.
- **iter-035 (K=20) completed BYTE-IDENTICAL** (comparison.csv + IS + OOS trades.csv, zero bytes differ)
  → K-invariance empirically confirmed; the determinism claim holds.

## Per-check: Look-Ahead PASS · Embargo PASS · Multiple-testing INFORMATIONAL (n_trials=1) ·
## Reproducibility PASS (deterministic) · Hypothesis-Implementation PASS · Anti-pattern PASS · Axis PASS.

## Concentration falsifier (quantified)
OOS weighted net +13.79 / 34 trades / 6 positive months. Top-1 ≈ 110% of net, top-2 ≈ 190% → drop-top-2
flips negative. Top-trade-dependent — but the accepted intrinsic let-winners-run exception (same shape as
merged iter-020/027), and MATERIALLY LESS concentrated than iter-027 (top-1 ~1223% of weighted net).
Recorded as a known structural property, not a blocker.

## Merge-worthiness vs iter-027
Generalization-first gate: (1) both-positive ✓ (IS +0.6481/OOS +0.4148); (2) OOS improves, not chased
(deterministic) ✓; (3) no IS regression (+0.6481 ≥ +0.6336) ✓; (4) concentration = intrinsic exception ✓.
Pareto-dominates iter-027. Only outstanding element was K=20 confirmation → iter-035 byte-identical →
**CONFIRMATION-MERGE.**

## Process flags (reconcile, not blocking)
- STALE legacy artifacts in flat `briefs-v1/iteration_v1-034/` (a different pre-redesign basis-zscore
  iteration); redesign artifacts live under `briefs-v1/ETHUSDT/`. No collision; leave legacy as-is.
- Dead duplicate v1-034 dispatch branch at run_baseline_v1.py:6877 (V1_BASELINE_UNIVERSE-guarded;
  disambiguated at runtime). Latent footgun — fold out at next cleanup.

## Path Forward (advisory)
1. Breadth-on-top-of-the-strong-core (2nd deterministic let-winners band / partial-take).
2. Direction-robustness K-invariant screen (trend_state_symbol→BTC / SMA 100-300).
3. PORTABILITY — apply the model-stripped deterministic core to BTC + next coins (possibly the highest-EV
   change across the whole v1 track).
