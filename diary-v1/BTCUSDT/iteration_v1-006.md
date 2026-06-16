# Diary — iter-v1/006 (BTCUSDT) — EXPLORATION

**Axis:** orthogonal NON-OHLCV feature — `funding_rate_zscore_90` (funding LEVEL z-score, NOT the
/005 spread) added to the 41-col prune (`V1_BTC_PRUNED_ITER002`). R2 OFF. K=5 screen, n_trials=35,
slippage 2 bps/side. FE Phase 4 recommendation (A): the only orthogonal candidate clearing every
IS-only diagnostic (|IS-IC| 0.043 above the 41-col price band max 0.028, orthogonal max|corr| 0.37,
standalone-probe importance rank 8/42, best dual purged-CV OOF lift).

**Result (vs iter-004 prune-only K=20 IS −0.17 / OOS +0.48; iter-005 prune+spread K=5 IS −0.43 / OOS +0.85):**
IS Sharpe **−0.3951** / OOS **−0.4245**, ratio **+1.07 (coherent sign, BOTH negative)**,
dispersion 40.89, 200/87 trades, IS net −18.01, OOS net −5.53. Clean run, 5/5 seeds trained, R5 0%.

**Verdict: NEGATIVE.**
- The profile is sign-coherent (both negative, ratio +1.07) — NOT the inverted artifact of /001/004/005 —
  but it is a **coherently-losing** profile, not an edge. Both windows negative.
- **FE IS-lift prediction (+0.2 to +0.4) FALSIFIED:** IS came in at −0.40, *worse* than prune-only (−0.17).
- **The funding level z-score collapsed OOS:** the inverted configs (/004 +0.48, /005 +0.85) had positive
  OOS riding on negative IS; adding funding z90 dragged OOS to −0.42. That "OOS positivity" was fragile,
  regime-driven, and one orthogonal feature destroyed it.

**Verifiability fix (task #130) — WORKED.** The importance CSV now has all 42 rows (active_feature_columns
sync), and `funding_rate_zscore_90` is visible at **rank 29/42** (gain 557.24) — bottom third. The
standalone-probe rank 8/42 did NOT transfer to the bagged specialist with the 41 prune cols + Optuna.
The feature was genuinely learned but contributed little, and what it contributed hurt generalization.
Orthogonal features are now auditable on importance rank, not just headline. (iter-005's funding column
was invisible only because the writer was keyed on the 193-col canonical list — fixed.)

**Confound (flagged):** iter-006 K=5 vs iter-004 K=20 prune-only; no K=5 prune-only control. But the
verdict does not hinge on it — IS is below the K=20 prune anchor AND OOS went outright negative.

**Funding family status: effectively closed.** Two members tested, both NEGATIVE — the term-structure
spread (/005, |IC| 0.026, rank 16/42) and the level z90 (/006, |IC| 0.043, rank 29/42). The FE flagged
the two funding z-scores as "one factor" (z30/z90 0.78 corr; stacking pointless), so the remaining
member `funding_rate_zscore_30` (|IC| 0.057, the strongest single feature in the search) is expected to
behave like z90 — low information to re-test. The deeper FE finding stands: **BTC's price signal is at
the noise floor (max |IS-IC| 0.028, purged-CV R² −0.095)**, and the strongest orthogonal candidate has
now failed in the live specialist.

**Lessons**
- A univariate IC above the price band + positive purged-CV OOF lift did NOT survive inside the bagged
  specialist. Standalone-probe importance over-promised (rank 8 → actual rank 29). Trust the in-specialist
  importance + headline, not the offline probe rank.
- The inverted-profile OOS positivity is fragile regime exposure, not edge — it inverts to negative the
  moment a feature reshapes the decision boundary.

**Next:** iter-v1/007 — pivot to a NEW orthogonal family (Open Interest: `btc_oi_delta_5_z30`, the best
non-funding candidate by raw dir_acc OOF lift; near-zero univariate IC = a non-linear positioning signal
a tree may capture where linear funding didn't). Completes the orthogonal sweep across funding + OI. If
OI also fails → orthogonal-feature axis decisively closed for BTC → iter-008 pivots axis (label horizon /
regime gate / reconsider whether BTC is the right first symbol given its persistent noise-floor IS).
