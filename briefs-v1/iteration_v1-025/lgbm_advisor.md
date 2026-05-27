# LightGBM Master Advisor — iter-v1/025 — Phase 4.5 (Pre-Design)

## Context Read
- **Track**: v1. Branch `iteration-v1/025`. HEAD `9502ecd`. Cycle-3 EXPLORATION **#10/10 — LAST**. /027 CONFIRMATION follows.
- **Anchor**: BASELINE_V1.md portfolio (IS +0.2829 / OOS +0.6637).
- **/023 outcome**: LEARNED-NEGATIVE (funding gain 5.40% > parity 2.38%; OOS Δ -0.20).
- **/024 outcome**: NEGATIVE-clean (regime-conditional engaged but didn't specialize).
- **EDA reality**: `oi_availability.csv` shows BTC PRESENT (4994 IS rows / 87.2%) BUT **ETH/LINK/LTC/DOT ALL MISSING (oi_n_rows=0)**. Fetch in flight.

## 1. OI vs funding mechanism — LightGBM CAN learn OI more easily

Funding had directional sign-flip at extreme tails (depth 3-5 must compose 2 splits + maintain conditional). OI has Q4 mild-positive single-band concentration (z90 ∈ [+0.29, +0.95], Sharpe-proxy +1.68, +85.30% PnL share) — **a depth-3 tree carves Q4 with one split**.

Q1 (extreme negative) is +0.99 Sharpe-proxy / +54.42% PnL — also positive. Q3 mid is dead. The model learns "Q3 mid dead, everything else alive" — 2-split saddle pattern, depth-3-survivable.

## 2. Verdict-prior recalibration — RECOMMEND 22/8/22/30/12/4/2

| Verdict | QR | LM Master | Rationale |
|---|---|---|---|
| PROMISING-clean | 18% | **22%** | Q4 Sharpe-proxy 1.68 is 2.4× /023's strongest mid-band; single-split learnable |
| PROMISING-INERT-FAV | 8% | **8%** | unchanged |
| INERT | 25% | **22%** | Q4 depth-3-easy; less likely than /023; -3pp |
| LEARNED-NEGATIVE | 30% | **30%** | /023 pattern remains structural prior |
| NEGATIVE-INERT | 13% | **12%** | -1pp |
| NEG-CAT | 4% | **4%** | unchanged |
| AUTO-REJECT (F3) | 2% | **2%** | unchanged |

**Net shift**: PROMISING tail 26% → **30%** (vs /023's 20%).

## 3. F-AXIS #1 DUAL GATE — TIGHTEN with breadth check

Single feature parity = 1/43 = 2.33%; 4.0% = 1.7× parity. Tighten PROMISING-clean: `rank ≤14/43 AND gain ≥4.0% on ≥2 cohorts AND z90 rank ≤20/43 on ≥3 cohorts (breadth check)`. Without breadth check, 2-cohort PROMISING risks being BTC+ETH only while LINK/LTC/DOT NaN-degrade.

## 4. CRITICAL: Pre-launch HARD BLOCK on OI fetch

`oi_availability.csv` shows ETH/LINK/LTC/DOT oi_n_rows=0 status=MISSING. **Phase 6 cannot launch.**

**MANDATE**:
- HARD-RAISE precondition at Phase 6.0: for sym in ETH/LINK/LTC/DOT: `assert data/open_interest/sym/8h.csv exists AND row_count ≥ 1000`. If FAIL → BLOCK-PENDING-FIX.
- **Minimum 3/5 symbols ≥1000 IS OI rows** for DUAL GATE evaluation to have ≥2 cohorts.
- **No silent NaN-feature degradation** (echo of /024 dispatch-defect lesson).
- Brief Section 3.6 commits to FAIL-FAST; LM Master endorses + emit `oi_coverage_check.csv` per-symbol in engineering report Section 7.

## 5. Two implementation risks

**(a) NaN-tolerant LightGBM on partial OI coverage**: 2020-01 → 2020-09 has NO OI for BTC/ETH/LINK/LTC (~700 early IS bars per symbol with `oi_delta_30_z90 = NaN`). LightGBM default-direction split creates `(symbol_dummy × NaN_indicator)` learnable interaction — curve-fit hazard.

**Recommend**: skip-month if OI unavailable (simpler than indicator column; no extra feature). OR add `oi_delta_30_z90_isnull` indicator.

**(b) z90 stationarity hides level non-stationarity**: ADF p≈0 on z90 is true but raw `oi_delta_30` has trend (asymmetric distribution; secular BTC OI growth 2024-2026). z90 normalizes recent 90-bar history but BTC OI building secularly produces different z90 sample than 2020-2022 (post-Luna OI decline). Predict z90 importance will be REGIME-CONDITIONAL across folds. Emit per-fold rank in engineering report.

## 6. /027 CONFIRMATION bundle composition

| /025 verdict | /027 bundle | OOS target |
|---|---|---|
| PROMISING-clean (22%) | LINK + ETH+gate + **OI-aware pool** | **+1.30 to +1.50** under corr drag |
| PROMISING-INERT-FAV (8%) | LINK + ETH+gate (2 components; OI cataloged informational) | +1.10 to +1.30 |
| INERT (22%) | LINK + ETH+gate (2 components) | +1.10 to +1.30 |
| LEARNED-NEGATIVE (30%) | LINK + ETH+gate (2 components; OI as 2nd LEARNED-NEGATIVE catalogued) | +1.10 to +1.30 |
| NEGATIVE-INERT (12%) | LINK + ETH+gate (2 components) | +1.10 to +1.30 |
| NEG-CAT (4%) | LINK + ETH+gate + multi-seed mandate at /026 if HIGH-RISK trips | +1.10 to +1.30 |

**Cross-correlation pre-validation MANDATORY at /027 if /025 PROMISING**: Pearson(monthly_returns_OI-aware-pool, LINK_specialist) < 0.50 AND Pearson(OI-aware-pool, ETH+gate) < 0.50.

## 7. Most important point

**The Q4 mild-positive band (z90 ∈ [+0.29, +0.95], Sharpe-proxy +1.68) is a single-split depth-3-learnable pattern stronger than any single ORACLE band funding ever showed — OI delta has structurally higher PROMISING probability than /023 funding had, BUT the 4-of-5 missing OI data MUST be fetched and verified ≥1000 IS rows per symbol before Phase 6 launches (HARD BLOCK), or the F-AXIS #1 DUAL GATE evaluation degenerates to BTC-only and the verdict is uninterpretable.**

## 8. /026 verdict-conditional staging

- **PROMISING (22%)** → /026 = pre-CONFIRMATION sanity (cross-correlation check). Do NOT stack OI momentum/volatility per SAME-FAMILY rule.
- **PROMISING-INERT-FAV (8%)** → /026 = OI momentum composed feature (Category 2 LR-PF; algebraic identity; Sharpe-Δ primary falsifier).
- **INERT/LEARNED-NEGATIVE/NEGATIVE-INERT** → /026 = methodology pre-CONFIRMATION sanity; no new EXPLORATION axis; proceed to /027.
- **NEG-CAT (4%)** → /026 = methodology only; cycle-3 ≥1σ NEG count reaches 4 → mandatory multi-seed for future HIGH-RISK.

## Critic Phase 7.5 Priority Items

1. **Coverage verification first**: ETH/LINK/LTC/DOT OI exists AND row count ≥1000 AND IS overlap ≥70%. BLOCK if not.
2. F-AXIS #1 DUAL GATE per-cohort with `rank ≤20/43` breadth check on ≥3 cohorts in addition to ≤14/43 on ≥2.
3. Per-fold rank stability of `oi_delta_30_z90` across 24 walk-forward months — if std-of-rank > 8, regime-conditional importance → PROMISING-FEATURE-MECHANICAL.
4. OOS-only IC reconfirmation: `IC(oi_delta_30_z90, funding_rate_zscore_30)` and `IC(oi_delta_30_z90, mom_macd_hist_12_26_9)`.
5. ORACLE Q4 band attribution reconciliation OOS — if Q4 not in OOS trade roster, PROMISING → LEARNED-NEGATIVE (basin relocation).
