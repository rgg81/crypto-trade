# Phase 7.5 Critic Review — iter-v1/088

OVERALL: SPECIALIST-PROMISING

## Iteration Type
SPECIALIST (XRPUSDT single-symbol, universe family, STOCK 48-col stack, fail-fast gate). Checks 1/2/6/8/14 full-enforcement; Check 3 (DSR/PSR/PBO) INFORMATIONAL at SPECIALIST budget; Checks 4/5 INFORMATIONAL per 2026-06-01 EDA revision. Merge floors (IS>1.0 AND OOS>1.0) apply at BUNDLE-003 assembly, NOT this SPECIALIST verdict.

## Per-Check Status
- **Check 1 Look-Ahead: PASS.** `walk_forward.py:113` embargo intact; zero unguarded `train_end_ms=test_start_ms`; 4 regression tests present. ZERO new features. Fresh 48-col regen verified leak-free: the two cohort cross-asset ratios (dot_vs_btc/eth_vs_btc) sit at exactly 0.0 (ranks 47-48) = correct single-symbol signature; a leakage-injecting regen would have shown spurious non-zero importance or hash mismatch (neither). backtest.py byte-unchanged from /087.
- **Check 2 Embargo: PASS.** Single-symbol gap=184h (22 candles) logged; both inner-CV gap + outer embargo applied.
- **Check 3 Multiple-Testing: FAIL (INFORMATIONAL).** IS DSR_corr 0.80 / OOS 0.75 (<0.95); PSR(vs1) 0.18/0.30; pbo null, n_eff=1 (30-trial single-outer-seed — expected; the structural reason this is a SPECIALIST forward-pointer not a merge).
- **Check 4 IC: INFORMATIONAL.** ic_matrix present (feature-level only — the load-bearing TRADE-level correlation is NOT measured here; flagged for the bundle decision).
- **Check 5 ADF: INFORMATIONAL.** adf_test present, spot-checks clear Bonferroni.
- **Check 6 Pareto: N/A** (single outer seed; multi-seed CONFIRMATION permanently dropped). basin V1 std=0.000 DEGENERATE (one observation), NOT robustness. **Single-outer-seed-TENTATIVE, NOT active basin-lottery:** inner-seed dispersion mean ~41.1 (3186/3192 candles std>0 → 50 seeds genuinely disagree) + 54/54 in-fold objectives positive (no TRB-style inversion). The vigilance DOWNGRADE triggers (spread>0.50 / Jaccard<0.40 / ρ<0.50) are unmeasurable at one outer seed → TENTATIVE flag applies, not DOWNGRADE.
- **Check 7 Reproducibility: PASS.** Explicit --pruned-features (48, asserted, hash b81176f8); seeds literal range(42,92); trade-math spot-check on 3 OOS rows clean (LONG/SHORT signs + weight_factor 0.33). Non-defect note: per_symbol/per_regime report UNWEIGHTED net 29.26% vs weighted headline 9.66% (×0.33 weight_factor reconciles) — Sharpe is on the weighted curve, correct.
- **Check 8 Hypothesis-Alignment: PASS.** XRP un-reserved + V1_ITER088_UNIVERSE + thin dispatch wrapper; zero scope creep; fail-fast PASSED (+16.88 IS weighted_pnl, BNB was BLOCKED).
- **Check 13 Anti-Pattern: PASS.** A1-A13 clean; XRP from earliest data (no trim); track isolation clean.
- **Check 14 Axis Family: PASS.** universe family (symbol whitelist), matches src/; rotation SUSPENDED per cycle-7 mandate (declared honestly).

## Independent OOS Adjudication — regime-conditional edge, NOT noise
Reproduced from out_of_sample/monthly_pnl.csv:
- Pre-Nov (2025-03→10, 8mo): **−17.24%**, 1/8 positive (edge OFF).
- 2025-11: +11.75% (inflection).
- Post-Nov (2025-12→2026-06, 7mo): **+15.15%, 6/7 positive, largest +4.05% (broad-based, NOT outlier-driven)** — strongest/most-stable OOS stretch.
**Verdict: regime-conditional edge, not noise.** The engineering "strip Nov → −2.09%" is arithmetically true but decision-misleading (lumps the −17% OFF + +15% ON regimes). Honest residual danger: the regime can turn OFF as abruptly as ON; the degenerate-Optuna tell (8/54 months best_trial=1, 7 in OOS era) means part of "edge on" is a budget-thin generic config. Correct label: **weak-but-real, in-fold-validated, regime-conditional, trial-budget-fragile** = exactly PROMISING (clears +0.30 IS structure threshold + OOS-positive; does NOT clear +1.0 floors, not required at SPECIALIST stage).

## Recommendations to QR
1. **The bundle decision is a TRADE-correlation question; the artifact doesn't exist yet.** IC matrix is feature-level. XRP re-learns the shared trend basis (ADX/Aroon/MACD ranks 2/4/5 cohort-shared; only stat_autocorr_lag5 rank-3 differentiates). The BUNDLE-003 brief MUST pre-register per-symbol trade-level correlation (XRP vs ETH/AAVE/BTC trade returns, overlapping windows) with a pre-committed <0.5 "earned seat" threshold.
2. **Pre-register the cross-track parity/netting audit** — XRP also v2-live; quantify combined v1+v2 XRP notional + parity that v1 bundle XRP decisions are independent of v2.
3. **Pre-register regime-conditionality as a falsifier** — if XRP's incremental bundle OOS Sharpe is itself concentrated in the post-Nov window (contributes nothing in the −17% OFF stretch), the temporal-complementarity claim is unsupported.

## Path Forward
Decisive next step: **BUNDLE-003 assembly backtest including XRP** — the backtest is the proof. (a) Does XRP raise bundle OOS Sharpe; (b) is XRP trade-correlation <0.5 vs ETH/AAVE/BTC. Both → earned seat (temporally-complementary diversifier); flat/down or high-corr → DIVERSIFIER-DEGENERATE, no seat. NO multi-seed CONFIRMATION.
If the bundle trial rejects XRP and a fresh mine is needed, axes from families NOT in the prior 5 (all universe): (1) autocorr-persistence feature-family head (engineer XRP's only orthogonal differentiator); (2) regime-conditional kill primitive (suppress the OFF regime); (3) longer-horizon labeling head (match the lag-5 persistence timescale).

OVERALL=SPECIALIST-PROMISING
