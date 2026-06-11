
## Phase 7.4 — LightGBM Master Post-Mortem (iter-v1/088)

**Outcome:** IS Sharpe +0.3783 (219 trades, PF 1.13, DSR_corr 0.80, PSR_vs1 0.18); OOS +0.4966 (84 trades, PF 1.14, DSR_corr 0.75, PSR_vs1 0.30). FIRST non-negative fresh mine (0/7 before); fail-fast PASSED (first-2yr IS +16.88).

### 1. IS +0.38 robust or basin artifact?
**NOT the /086 TRB inversion failure.** Parsed 54 per-month best Optuna objectives from run.log: **54/54 positive** (range [+0.0145,+0.3015], mean +0.176). No in-fold/realized inversion (the realized walk-forward sign is consistent). Inner-seed dispersion mean 41.14 (3186/3192 candles >0) → 50 seeds genuinely disagree → aggregation meaningful, not collapsed → NOT basin-lottery. **Counterweight (degenerate-Optuna tell):** 8/54 months have best_trial=1 (random startup never beaten by 29 TPE trials), all the identical conservative config (training_days=320, lr=0.006, conf=0.832), **7 of 8 in the OOS era** → recent signal thin enough that a generic config dominates. IS ex-top-3 months = −13.06% (leans on 3 best), but genuine positive skew (PF 1.13 @ 42.5% WR). **Verdict: weak-but-real, in-fold-validated, trial-budget-fragile.**

### 2. Feature read — coherent
Top-6: vol_atr_14(1), trend_adx_14(2), stat_autocorr_lag5(3), trend_aroon_osc_50(4), mom_macd_line(5), interact_natr_x_adx(6) = coherent trend/autocorr/vol edge (XRP exhibits positive return autocorr/persistence; model monetizes it). Diverse (gain decay 9531→3359 = gentle 2.8×, no single-feature spike). **Orthogonality (vs TRB DIVERSIFIER-DEGENERATE):** stat_autocorr_lag5 rank-3 is the ONLY structural differentiator; ADX/Aroon/MACD at 2/4/5 mean XRP LARGELY RE-LEARNS THE SHARED TREND BASIS (lighter than TRB but not strongly orthogonal). Trade-correlation vs cohort is the load-bearing unchecked quantity.

### 3. OOS single-month concentration — corrected read
The engineering "strip Nov→−2.09%" is correct but INCOMPLETE. Breakdown: 2025-03→10 (8mo) net **−17.24%** (1/8 pos, edge OFF); 2025-11 +11.75% (inflection); **2025-12→2026-06 (7mo) net +15.15%, 6/7 pos, largest +4.05% (NOT outlier-driven).** This is a REGIME TRANSITION at 2025-11, not a one-off jackpot — the most recent 7 months are the strongest/most-stable OOS stretch. The trend/autocorr edge "turned ON" in late 2025. Danger (Sharpe is regime-dependent, could turn off) is real, but "noise that got lucky once" is the WRONG characterization. (Caveat: 7/8 degenerate best_trial=1 months are this recent window → "edge on" partly served by the robust conservative config.)

### 4. Bundle-fit
XRP IS +0.38 is the TOP of the bundle standalone-IS cohort (ETH +0.24, AAVE +0.34, BTC +0.07; none clears +1.0). Per the cycle-7 regime-diverse-bundle mandate, **legitimate BUNDLE-003 candidate.** OOS regime profile (OFF early-2025, ON late-2025/2026) is potentially temporally-complementary. **2 hard caveats:** (1) trade-correlation must be CHECKED not assumed (if >0.5 vs ETH/AAVE/BTC trades → concentration not diversification → DIVERSIFIER-DEGENERATE); (2) cross-track v2 overlap = deployment-parity / netting audit (not a v1-bundle-assembly violation).

### 5. Verdict recommendation (advisory)
**SPECIALIST-PROMISING (single-outer-seed-TENTATIVE) — worth a BUNDLE-003 seat trial. NOT too-marginal.** Strongest fresh-mine result of the campaign (first to clear fail-fast, first non-negative, in-fold uniformly positive, coherent mechanism, post-Nov OOS consistency). Does not clear +1.0 standalone — but the mandate does not require it for bundle members. Robustness framed WITHOUT multi-seed (permanently dropped): single-outer-seed-TENTATIVE flag (NOT basin-lottery — inner dispersion healthy + in-fold never inverts). **What settles it = the BUNDLE backtest itself (per "the backtest is the proof"): drop XRP into a candidate BUNDLE-003 and read bundle OOS Sharpe + per-symbol trade-correlation. If XRP raises bundle OOS AND trade-corr <0.5 → earned its seat (temporally-complementary diversifier). If flat/down or high corr → DIVERSIFIER-DEGENERATE, no seat.** Next step = BUNDLE-003 assembly backtest including XRP, NOT a standalone re-run.

### Notes for Critic (7.5)
1. OOS is better characterized as a regime transition at 2025-11 (post-Nov +15.15%/6-of-7-pos) than a single lucky month — weigh both framings.
2. Degenerate-Optuna tell: 8/54 months best_trial=1 (7 in OOS era) caps trial-budget-effective edge.
3. Bundle orthogonality: stat_autocorr_lag5 rank-3 is the only differentiator; trade-level co-movement vs cohort is the load-bearing unchecked quantity (IC-matrix is feature-level only).
