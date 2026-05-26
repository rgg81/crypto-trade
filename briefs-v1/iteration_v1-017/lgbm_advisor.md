# LightGBM Master Advisor — iter-v1/017 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1. Branch `iteration-v1/017`. HEAD `faa4010`. CYCLE-3 EXPLORATION #2 of 10 under STRICT 2h wall-clock.
- **Baseline**: `v0.v1-baseline-corrected` (`f8bc12c`). IS +0.2829 / OOS +0.6637. UNCHANGED through cycle-2 + cycle-3 #1.
- **Anchor**: /016 EXPLORATION-NEGATIVE-catastrophic (OOS Sharpe -1.00; 50 min wall-clock; 75% margin).
- **Track record**: 1/14 verdict-class directional, 6/14 mechanism-level. Modal-NULL prior empirically validated.
- **QR's axis**: +SOL only (6-sym universe), abs_pnl reverted, all other axes pinned. SOL parquet stale — mandatory regen.
- **/016 Phase 7.4 recommendation**: universe expansion at /017 with SOL — **QR adopted exactly as specified.**

## SOL Inclusion Mechanism Call

**SOL IS direction**: NEUTRAL→POSITIVE (60/30/10 positive/null/negative). SOL IS std 3.68% (higher than baseline 3.04-3.24); abs_p95 7.52% leaves headroom for ATR×2.9 TPs. Model F uses Model A's profile (2.9/1.45); tighter SL barrier triggers more on high-vol symbol; IS WR tilts DOWN ~40% baseline but not catastrophically. IS abs PnL share band: **[8%, 25%]**.

**SOL OOS direction**: HIGH-VARIANCE (40/35/25). 0.6164 BTC correlation genuinely diversifying (≥4pp gap below LINK 0.6856), but single-seed=42 EXPLORATION makes OOS regime-conditional. OOS PnL band: **[-35%, +35%]**.

## ETH Dilution vs Regime-Lock Prediction

**Regime-lock probability: 75%. Universe-dilution rescue: 15%. Model-arch recovery: 10%.**

ETH OOS catastrophic spans 3 DISJOINT mechanism layers (label-distribution-shape twice; sample-weight-magnitude once). Adding SOL changes NONE of the three drivers — Model A still trains on BTC+ETH cohort with IDENTICAL labels/weights/features. Only secondary path: SOL trade events shift Optuna per-cell Pareto frontier, re-ranking Model A hparams. Mechanism non-zero but weak.

**Highest-probability outcome**: ETH OOS Scenario A (share > 40% absolute PnL, PnL ≤ -20%). **Forward-bind**: /018 PRIMARY must be ETH-specific kill switch (BTC-trend conditional OR per-symbol drawdown brake), NOT another universe expansion.

## Wall-Clock Recommendation

**KEEP n_trials=18. DO NOT compress to 15.** 60-min linear / 42-min sub-linear → 50-65% margin. n_trials=18 stays above TPE warmup ~10 by 80%; 15 trims buffer to 50% on HIGH-RISK axis. Pre-emptive compression to 15 is false economy.

**CONTINGENCY**: if QE pre-flight at 50% completion projects >72 min, drop to n_trials=15 per brief §3.6.4 — DO NOT pre-emptively compress.

## n_eff_per_cell Prediction

**Predicted band: [11, 17]** (median across cells):
- Label-shape UNCHANGED (no timeout-dominance risk)
- Weight-distribution UNCHANGED (abs_pnl reverted)
- Loss-surface ADDITIVELY ENRICHED (Model F adds ~165 IS rows/month at SOL's volatility profile)

60% lands [11, 17]; 25% lands [10, 13] (insufficient signal-injection); 15% below 10 (Model F noisy enough to homogenize).

## Predicted Verdict-Class

**FLAT 33/33/34** (mild adjustment):
- PROMISING: **30%** (Δ OOS ≥ +0.20). Requires SOL positive AND ETH dilution AND Model A unperturbed — 3 conjunctive at 60-70% each
- NULL: **35%** modal. Universe expands mechanically; no portfolio Sharpe shift
- NEGATIVE: **35%** (incl. 8% catastrophic Δ ≤ -0.55)

**Most likely PROMISING sub-pattern**: PROMISING-MECHANICAL (Cell 2). SOL drives lift via fresh contribution; A/C/D/E rosters near bit-identical. Non-compoundable as signal source.

## Wall-Clock Margin Re-Check for 7-Symbol Option

**RECOMMEND 6-SYMBOL. DO NOT EXPAND TO 7-SYM (+XRP).** Reasons:

1. **Single-axis isolation**: +XRP simultaneously confounds attribution
2. **XRP kurtosis 17.46** (vs SOL 8.41, LINK 5.21) is structural red flag — fat tails drive single-seed=42 lottery effects, contaminating SOL test
3. **Margin compression**: 70-min at 42% margin technically above 20% floor but reduces contingency buffer

**Forward**: /018 alternate A handles +XRP as SECOND universe expansion sequentially.

## Saturation Risks

**Single-seed=42 frozen-baseline pattern (v3 /020-/022 precedent)**: at single-seed EXPLORATION, per-symbol Optuna trajectories deterministic. If /017 PROMISING entirely SOL-driven while A/C/D/E rosters bit-identical to /016, that's PROMISING-MECHANICAL — at multi-seed CONFIRMATION (/027) SOL contribution will DILUTE. Critic should check trade-roster identity for A/C/D/E vs /016.

**HIGH-RISK declaration correct but soft**: universe expansion adds NEW training data via Model F's per-cell Optuna budget. At ENSEMBLE_SIZE=3 single-seed, Model F is lottery-exposed. /015 LESSON forward-mandate (1σ negative across 3 HIGH-RISK accumulates) — /017 is 1st HIGH-RISK cycle-3.

## What I Did NOT Recommend

- Multi-seed at /017 (HIGH-RISK forward-mandate not yet triggered)
- Pin Model F bounds tighter than v1_pruned (axis isolation)
- XGBoost (deferred to /018+ per /016 Phase 7.4)
- ETH-specific feature engineering (multi-axis violation)
- R1/R2 for Model F (R3-only, sister to A; R1 single-symbol could deadlock)

## Closing Note

**MEDIUM confidence in MODAL NULL outcome (35%).** Mechanism well-grounded; QR EDA unusually rigorous. +SOL test discriminates regime-bound vs universe-bound cleanly.

**Three specific calls staked**:
1. ETH regime-lock probability 75% — /018 must pivot to ETH-specific kill
2. KEEP n_trials=18 — pre-emptive compression to 15 false economy
3. 6-symbol over 7-symbol — single-axis isolation preserves attribution

**Critic Phase 7.5 priority check**: F-AXIS-MECHANISM SOL share ∈ [5%, 40%] band has teeth. If <5% Model F under-firing (BLOCK-PENDING-FIX, not NEGATIVE). If >40% single-seed lottery (concentration violation, not edge).
