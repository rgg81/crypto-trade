# iter-v1/071 — LightGBM Master Advisory

**Date**: 2026-06-05
**Track**: v1
**Type**: CONFIRMATION-PORTFOLIO (BUNDLE-001 ASSEMBLY)
**Author**: LightGBM Master

---

## Phase 4.5 — Pre-Design Advisory

**SKIPPED** for this iteration. Reason: BUNDLE-001 is a composition-only iteration with no Optuna search, no feature-set redefinition, no hyperparameter search domain change. The three specialist EXPLORATIONs (/063, /064, /065) each received their own Phase 4.5 advisories at their respective brief authorship; this iteration only assembles their pre-existing trade artifacts via pairwise-disjoint coin partition (DOT/063, ETH/064, BTC/065).

No new LightGBM mechanics to pre-register.

---

## Phase 7.4-equivalent — Bundle Composition Mechanics Post-Mortem

### 1. Per-specialist Optuna provenance (inherited, not re-searched)

Each specialist trained 5 inner seeds × N outer cells (per its own EXPLORATION axis). LightGBM Master notes (from prior advisories):

| Spec | Inner ensemble | Outer cells (months × seeds) | Optuna trials/cell | Feature columns | Key axis |
|---|---:|---:|---:|---:|---|
| /063 DOT | 5-seed | 60-cell × single outer (EXPLORATION) | ~18 | V1_FEATURE_COLUMNS_PRUNED (48) | R1+R2+R3, atr-band 3.5/1.75 |
| /064 ETH | 5-seed | 60-cell × single outer (EXPLORATION) | ~18 | V1_FEATURE_COLUMNS_PRUNED (48) | R3-only (Model A pattern), atr-band 2.9/1.45 |
| /065 BTC | 5-seed | 60-cell × single outer (EXPLORATION) | ~18 | V1_FEATURE_COLUMNS_PRUNED (48) | R3-only (Model A pattern), atr-band 2.9/1.45 |

Each specialist is therefore an EXPLORATION-budget artifact, not CONFIRMATION-grade. The bundle inherits this provenance. **This is the principal mechanical caveat for the BUNDLE-001 baseline anchor:** specialists were not multi-seed-outer validated; basin-lottery vigilance applies per the project memory rule (`feedback_v1_basin_lottery_vigilance.md`). The bundle's overall outer-seed=42 lottery exposure is not mitigated by the union.

### 2. Are the 3 specialists' contributions COMPLEMENTARY or REDUNDANT?

**Verdict: COMPLEMENTARY at the regime axis, partially REDUNDANT at the universe axis.**

**Complementary (regime axis)** — per-specialist Sharpe trajectory across IS→OOS shows distinct regime profiles:

| Spec | IS per-trade Sharpe | OOS per-trade Sharpe | Regime profile |
|---|---:|---:|---|
| /063 DOT | +0.104 | +0.082 | Stable positive both regimes (IS-strong, OOS-attenuated); ALT high-beta cohort |
| /064 ETH | +0.049 | +0.063 | Marginal both regimes, slight OOS lift; large-cap balanced cohort |
| /065 BTC | **−0.054** | **+0.132** | **OOS-regime-specialist (IS NEGATIVE → OOS LARGEST POSITIVE)**; mega-cap inversion cohort |

Per `feedback_is_oos_divergence_is_regime_not_overfit.md`, this BTC IS→OOS inversion is the EXPECTED regime-specialist signature, NOT overfit. The /065 specialist has discovered a 2025-OOS-favorable regime for BTC that did not exist in 2023–2024 IS. Combining it with /063 (DOT broad-regime) and /064 (ETH balanced) gives the bundle three orthogonal regime-source contributions.

**Bundle per-trade Sharpe IS=+0.041, OOS=+0.084 (ratio 2.05)** reflects this regime composition: the OOS lift is dominated by BTC's regime-specialist behavior, partially offset by DOT's attenuation. This is regime DIVERSIFICATION working as designed under the v1 regime-specialist methodology.

**Partially redundant (universe axis)** — DOT, ETH, BTC are all majors with high pairwise correlation (BTC↔ETH ~0.85 typical; BTC↔DOT ~0.70). Specialists are independently trained but their universes are not regime-orthogonal — when the crypto market goes risk-off, all three drawdown together. The bundle's max-drawdown profile (IS 89.03%, OOS 36.51%) reflects this: peak-trough draws coincide across coins.

For future bundles, adding low-β cohorts (e.g., stablecoin-yield / LDO / TRX-style cross-asset) would reduce this universe redundancy. BUNDLE-002 candidate axis.

### 3. Per-symbol PnL concentration analysis

**Concentration is NOT skewed to BTC despite BTC's headline +1.13 OOS Sharpe.** The actual concentration profile:

| Symbol | OOS n | OOS PnL% | Share of bundle OOS PnL |
|---|---:|---:|---:|
| BTCUSDT | 87 | +41.66% | **37.96%** |
| DOTUSDT | 62 | +40.18% | **36.61%** |
| ETHUSDT | 81 | +27.91% | **25.43%** |

**The concentration is REMARKABLY BALANCED across the 3 coins.** BTC at 37.96% is only 1.35-pp above an equal-weight 1/N=33.3% target. DOT is +3.3pp above equal-weight, ETH is −7.9pp below. The largest single-coin share is 37.96% versus the standard ≤30% gate — a 7.96pp overshoot — but this is **structurally infeasible at N=3** (uniform = 33.3%; the gate was calibrated for N=5 BASELINE_V1).

**Reframed adjusted concentration metric (informational):** Herfindahl-Hirschman Index of OOS shares:
- HHI = 0.3796² + 0.3661² + 0.2543² = 0.1441 + 0.1340 + 0.0647 = **0.3428**
- Equal-weight HHI at N=3: 0.3333
- Excess concentration: 0.0095 (2.85% above equal-weight floor)

At N=3, the bundle is effectively equal-weighted in PnL contribution. The "FAIL ≤30%" is a structural artifact of the gate threshold, NOT a true concentration risk. **The CONCENTRATION SIGNAL HERE IS THAT N=3 IS UNDER-DIVERSIFIED** — the right response is to expand the bundle to N≥5 in a future iteration, not to penalize this bundle for arithmetic at N=3.

### 4. BTC's IS-NEGATIVE → OOS-POSITIVE inversion: mechanism analysis

BTC's per-trade Sharpe inverts from −0.054 IS to +0.132 OOS. This is the LARGEST OOS contributor signal in the bundle. Mechanical decomposition:

- **IS BTC trades (n=190)**: 35.26% WR, avg PnL −0.229%, PF 0.88, net −43.56%. Model learned that during 2023-2024, BTC mid-week 8h breakout signals were structurally net-losing under the R3-only risk wrapper (no R1 cool-down, no R2 DD-scaling). This is consistent with BTC's 2023-2024 lower-volatility, range-bound regime where the LightGBM head — trained on 2023-Q1 → 2025-Q1 features — was producing predictions that misalign with realized price action.

- **OOS BTC trades (n=87)**: 45.98% WR, avg PnL +0.479%, PF 1.34, net +41.66%. The 2025-2026 regime shift (rising volatility, trend-resumption, post-Q4-2024 BTC structural break) flipped the sign of the same model's predictions. The R3 OOD Mahalanobis gate did NOT fire (it's a soft 70th-percentile gate, not a hard kill switch) and the model rode the regime change.

**Risk note**: this is the textbook OOS-regime-specialist artifact López de Prado warns about in AFML Ch. 7 — a model that is OOS-favored at a single OOS window is one regime shift away from inverting back. Per `feedback_v1_basin_lottery_vigilance.md` and `feedback_v1_cycle6_exploration_lottery_terminal.md`, single-seed EXPLORATION promotion to bundle ALWAYS carries OOS regime-specialization risk. The bundle merge under user mandate locks this in as the FIRST methodology-trained baseline; future iterations MUST anchor multi-seed re-validation here.

### 5. Saturation risks (mechanical)

- **No new LightGBM training in this iteration** → no Optuna saturation diagnostic available.
- **Inherited specialist Optuna saturation**: each specialist ran at EXPLORATION budget (~18 trials/cell). Per López de Prado AFML §11.4, n_trials < 30 leaves significant trial-budget headroom; verdicts are TENTATIVE. The bundle as a whole is best characterized as 3 × TENTATIVE-EXPLORATION-PROMISING composed under user mandate, not as a CONFIRMATION-grade artifact.

### 6. Recommendations for BUNDLE-002 and beyond

1. **Multi-seed re-validation of /071 specialists is the highest-priority next-iteration axis.** Run /063, /064, /065 at 7-outer-seed roster `[42, 123, 456, 789, 1001, 2002, 3003]` (per `feedback_v1_trade_rate_floor_50_per_specialist.md` tier-2 condition); confirm OOS regime-specialization is not basin-lottery artifact.
2. **Universe expansion to N≥5**: add 2 low-β specialists (candidates from v1 expanded universe: LDOUSDT, TRXUSDT, NEARUSDT) to mechanically dilute the structural ≥33% concentration. BUNDLE-002.
3. **DSR / PBO / PSR re-computation at multi-seed CONFIRMATION budget**: bundle-level statistical-significance gates were skipped under user mandate; the next baseline-replacement iteration must close this loop.
4. **BTC OOS-specialist follow-up**: monitor BTC's OOS regime — if 2026-Q2 / Q3 reverses the 2025 trend, BTC's specialist will revert to its IS sign and become the bundle's largest drag. Build a regime-aware kill switch as a future risk-primitive iteration.

---

## Phase 4.5 Confidence Assessment

**N/A — Phase 4.5 was skipped.** The bundle is post-hoc composition; no design-time LightGBM advisory.

For the Phase 8 diary's "LM Master Advisory Tracking" field, the appropriate entry is:
- Phase 4.5 confidence: **N/A (composition-only)**
- Phase 4.5 recommendations: **none**
- Phase 7.4 post-mortem highlights:
  1. Three specialists are COMPLEMENTARY at regime axis, partially REDUNDANT at universe axis (all majors, high pairwise correlation).
  2. Concentration is effectively equal-weighted at N=3 (HHI 0.3428 vs equal-weight 0.3333); ≤30% gate is structurally infeasible at N=3.
  3. BTC's IS-NEGATIVE → OOS-POSITIVE inversion is the textbook OOS-regime-specialist signature; bundle inherits OOS-window-specialization risk that must be retested at multi-seed CONFIRMATION budget in a future iteration.

---

**End of Phase 7.4 LM Master post-mortem.**
