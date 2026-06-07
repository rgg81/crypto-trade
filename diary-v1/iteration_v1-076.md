# iter-v1/076 — Diary

## Headline

**SPECIALIST-NEGATIVE: AAVE second NEW SYMBOL specialist; IS catastrophic (−0.69), OOS notable (+0.62); IS-first gate excludes merge.**

## Decision: NO MERGE

BUNDLE-001 (DOT/063 + ETH/064 + BTC/065 at v0.v1-071) UNCHANGED. AAVE seat: **1st strike** per the SPECIALIST mining one-attempt-and-eliminate rule (re-attempt possible only with explicit user authorization).

## Results Table

| Metric | IS | OOS | Notes |
|---|---|---|---|
| Sharpe | **−0.6943** | **+0.6234** | F-AXIS #1 NEGATIVE band FIRES (IS < +0.20 by 0.89; PROMISING-VALIDATED +0.50 missed by 1.19). OOS suspicious-divergent. |
| Sortino | −0.6199 | +1.4152 | — |
| Max DD | 55.33% | 24.43% | IS DD second-deepest in v1 catalog. |
| Win rate | 35.4% | 40.5% | Both below specialist-roster median. |
| Profit factor | 0.8026 | 1.1797 | IS sub-unity. |
| Total trades | 158 | 84 | IS ≥ 50 trade-count floor CLEARED. |
| DSR (EXPLORATION-mode, info only) | −33.03 | −47.08 | Informational; not gate-triggering per `feedback_v3_dsr_mode_artifact`. |
| Net PnL % | −43.48% | +16.26% | — |
| Specialist dispersion (mean) | 32.95 | — | **Highest in v1 SPECIALIST roster**; > 30 basin-lottery threshold per `feedback_v1_basin_lottery_vigilance`. |
| Per-direction IS | SHORT 71/−72.15 (WR 31.0%); LONG 87/−19.65 (WR 39.1%) | — | Both directions lose; no single-direction mirage. |
| Per-direction OOS | SHORT 40/+55.50 (WR 47.5%); LONG 44/−6.23 (WR 34.1%) | — | OOS lift concentrated in 14 2026Q1-Q2 shorts (WR 64.3%, +53.26 sum). |
| LM 4.5 prediction | IS +0.20 modal [−0.20, +0.55]; OOS −0.10 modal | actual IS −0.69, OOS +0.62 | **Mechanism-level reversal**, not magnitude miss. Modal IS off by 2.9× lower band; modal OOS off by 2.6× upper band. |

## F-AXIS Verdict (pre-registered Section 4, frozen at brief SHA)

- **F-AXIS #1 (IS Sharpe)**: −0.6943 < +0.20 → **SPECIALIST-NEGATIVE FIRES** (mechanical).
- **F-AXIS #1 trade-count floor**: 158 ≥ 50 → CLEARED.
- **F-AXIS #2 (specialist dispersion / basin-lottery)**: σ_pop proxy `specialist_dispersion_mean = 32.95` > 30 → METHODOLOGY-NEGATIVE basin-lottery fingerprint confirmed; downgrade moot at NEGATIVE.
- **F-AXIS #3 (OOS-dominant lift)**: OOS +0.62 ≥ +0.40 with IS Δ = −1.32 (≫ +0.10) → "Suspicious OOS-dominant lift" band; refers to Phase 7.4 long-bias / regime-coincidence diagnostic.
- **Falsifier #1 per-direction Sharpe balance**: balanced both IS (45/55) and OOS (48/52); F-AXIS #1 verdict stands at face value.
- **Falsifier #2 AAVE/ETH pred-corr + eth_* family rank**: eth_* features at rank 47-48 with 0.0 gain → IDIOSYNCRATIC SPECIALIZATION confirmed; **LM 4.5 Risk Flag 1 (DeFi-cycle leakage HIGH) REFUTED**.
- **Falsifier #3 feature-importance signature**: top-3 = 22.3%, top-10 = 54.9% — broad-based, basin-lottery confirmation.

## What Worked

- Single-bit dispatch discipline preserved (only `SYMBOLS=("AAVEUSDT",)` + `ITERATION_LABEL="v1-076"` + new dispatch branch).
- `feature_columns=list(V1_FEATURE_COLUMNS_PRUNED)` passed explicitly per `feedback_explicit_feature_columns`.
- Phase 5.5 gate PASS confirmed feature-stack hash + NaN coverage.
- Phase 6.0 Critic pre-flight PASS.
- Foundation embargo (walk_forward.py:113) intact; no look-ahead.
- Trade-count floor cleared cleanly (158 IS / 84 OOS).
- Specialist dispersion was correctly captured and flagged (32.95 > 30) — diagnostic infrastructure performed as designed.
- LM 4.5 calibration correctly identified the eligible-set basin-lottery risk and called the IS modal +0.20 with proper confidence (MEDIUM-LOW); the verdict band hit was correct (NEGATIVE-IS-OOS-DIVERGE, assigned 0.18 prior) even though the mechanism prediction was wrong.

## What Failed

- **IS Sharpe is the worst in the v1 catalog (−0.6943)**. The model never learned a clean direction at AAVE — broad-based importance (top-3 = 22.3%) + dispersion 32.95 indicate 50 inner seeds disagreed throughout.
- **Inherited 48-col stack is mis-calibrated to AAVE's micro-structure**. Top-3 importance carriers (`vol_atr_14`, `trend_aroon_osc_50`, `interact_natr_x_adx`) are vol-regime + slow-trend filters that fire indiscriminately on AAVE's high-vol (118%) chop-whipsaw IS regime. `regime_momentum_signed_5d` (load-bearing at DOT/063 / ETH/064 / BTC/065) ranks 29 with 0.59% gain — the DOT-precedent feature stack did not transfer.
- **ATR (2.9, 1.45) pair mechanically mismatched to AAVE's vol cluster (118%)**. SL hit rate 97/158 = 61% IS (vs DOT/063 ~52%) confirms calibration target was 110% vol cluster.
- **Cross-asset features INERT**: `eth_vs_btc_ret_ratio_30` rank 48 with 0.0 gain; `dot_vs_btc_ret_ratio_30` rank 47 with 0.0 gain. LM 4.5 Risk Flag 1 (DeFi-cycle leakage to ETH/064 HIGH) was directionally wrong.
- **LM 4.5 BULL-IS / BEAR-OOS regime mechanism wrong**: actual pattern is chop-IS / trend-OOS, not bull/bear. Both directions lose in IS; shorts win in OOS by regime coincidence (14 trades in 2026Q1-Q2 carry +53.26 sum).
- **OOS +0.62 is regime-accidental, not signal-driven**. The "AAVE as 2025-2026 regime specialist" hypothesis is **not IS-validated**: IS bear quarters (2022Q4 / 2024Q2 / 2025Q1) show shorts flat-to-negative, NOT the same mechanism the OOS shorts express. Per `feedback_v1_oos_inflation_empirically_confirmed`, OOS evidence cannot promote a NEGATIVE-IS iteration to bundle-eligible.

## Lessons

1. **NEW SYMBOL EDA must include per-quarter regime decomposition**. /076 brief Section 2.8 cited "2023 +109% + 2024 +184%" — characterized as "bull-dominant". Quarterly decomposition (2022Q4 −31% / 2023Q1 +44% / 2023Q4 +58% / 2024Q3 +60% / 2024Q4 +88% / 2025Q1 −40%) reveals **chop-whipsaw mean-reversion**, not bull-trend. Annual cumret aggregations hide quarterly regime structure. Future NEW SYMBOL EDA tables (Critic Rec 1 in /076 review) should add quarterly directional regime tagging (TRENDING-UP / TRENDING-DOWN / V-SHAPE / CHOP using `sign(close_t − close_{t−90})`).
2. **Feature-stack adequacy pre-screen before single-bit dispatch on NEW SYMBOL** (Critic Rec 2 in /076 review). Compute per-feature IC vs forward returns on AAVE IS-only and Spearman rank-correlate top-10 vs DOT/063's. If correlation < 0.50, flag feature-stack-mismatched **before** Optuna spend. Cheaper than a full SPECIALIST run.
3. **`specialist_dispersion_mean > 30` should be a pre-registered Section 4 gate, not a post-hoc downgrade** (Critic Rec 3 in /076 review). Matched to DOT/063 ~25 / BTC/065 ~28 baselines.
4. **LM Master mechanism predictions for NEW SYMBOLS at v1 specialist mode are MEDIUM-LOW reliability**. /076: 2 of 5 risk flags directionally wrong, 1 correct, 2 untested. Mechanism predictions are unreliable when the feature stack is inherited rather than co-designed. Per LM 7.4 calibration note: weight broad-based feature-mismatch risk higher than narrow mechanism risks (ETH leakage, regime inversion) in future NEW SYMBOL advisories.
5. **OOS sign-reversal under a HARD methodology lock is regime-coincidence**, not data leakage. Check 1 PASS in Phase 7.5 + foundation `walk_forward.py:113` embargo confirmed intact. The IS-first gate methodology lock holds; LM 7.4's "regime-accidental short-trend pickup" classification is the correct frame.
6. **The "second consecutive NEW SYMBOL specialist NEGATIVE" data point** (/075 ATOM + /076 AAVE) is the **third independent failure mode pattern under the cycle-7 per-symbol regime-specialist mandate**. Per `feedback_v1_cycle6_per_symbol_regime_specialist_mandate`, this does NOT yet trigger a mandate revision (the mandate is at 2 cycles MINIMUM), but autopilot queue prioritization should weight away from un-augmented inherited-stack NEW SYMBOL dispatches and toward methodology-augmented EXPLORATIONs (Critic Rec 2 pre-screen, /077 ICP underway).

## Note on Parallel /077 ICP Backtest

`/077 ICPUSDT specialist backtest currently RUNNING (PID 3619041)`. /077 rotates to a non-DeFi narrative per LM 4.5 Saturation Risk 1 (storage / L1 cluster) and is structurally orthogonal to the AAVE/076 failure mechanism. /077 verdict will be issued at its own Phase 7+8 closeout; it does not retroactively alter the /076 SPECIALIST-NEGATIVE record.

## Path Forward (from Critic)

The /076 SPECIALIST-NEGATIVE stands. AAVE seat: 1st strike per the SPECIALIST one-attempt-and-eliminate rule (cycle-7 per-symbol regime-specialist mandate). Per the autopilot mining queue, **AAVE is dropped after this single attempt unless the user explicitly authorizes a /AAVE-2 second strike**.

Three alternative axes for a hypothetical /AAVE-2 (if user authorizes) or the next non-AAVE rotation queue. Critic and LM Master have aligned on the priority ordering:

### Rec 1 — ATR pair recalibration 2.9/1.45 → 3.5/1.75 [HIGHEST PRIORITY]

- **Axis family**: `risk-primitive` (per-symbol ATR override).
- **What**: AAVE specialist ATR-TP / ATR-SL change 2.9/1.45 → 3.5/1.75, keeping the 2.0× TP/SL ratio intact.
- **Mechanism**: vol-cluster-mismatch is the LM 7.4-confirmed dominant IS failure driver. AAVE IS realized vol 118% vs DOT-calibration target 110% → IS SL hit rate 61% (vs DOT/063 ~52%). Widening to 3.5/1.75 reduces expected SL-hits by ~15% (log-normal SL-distance at AAVE σ vs DOT σ). LONG-side at 22% WR in 2022Q4 = trades getting stopped by intra-quarter volatility before the V-bottom recovery materializes.
- **Why HIGHEST priority**: a **clean single-bit methodology-preserving move**. Mechanism is the dominant IS failure driver, falsifier is sharp (if IS Sharpe ≤ −0.40 AND DD > 60%, the symbol is signal-absent — 2nd strike fires), risk is contained (per-trade max-loss rises ~20% at the wider stop).
- **Risk**: per-trade max-loss rises ~20% (1.75× ATR vs 1.45× ATR). At 84% OOS vol still survivable. IS DD likely widens to 60-65% if signal is genuinely flat — but the widening is the falsifier itself.
- **Falsifier**: /AAVE-2 IS Sharpe ≤ −0.40 AND DD > 60% → signal-absent verdict (2nd strike).

### Rec 2 — OI-family stack augmentation: +3 features (oi_delta_24h_z30 / oi_change_8h_pct / oi_funding_corr_30) [MEDIUM PRIORITY — RISK FLAG]

- **Axis family**: `feature-family` (per-symbol stack augmentation, not methodology change).
- **What**: AAVE specialist run keeps the 48-col stack but adds 3 OI features as a /AAVE-2-only stack expansion.
- **Mechanism**: targets crypto-native idiosyncratic signal. `oi_delta_30_z90` ranks 6/48 with 5.06% gain in /076 → OI family has signal but is under-represented at 1/48. AAVE as a DeFi-lending token has lender-borrower dynamics producing OI bursts ahead of price moves (mechanism distinct from L1s like DOT/ETH/BTC).
- **Critic risk flag**: **breaks the SPECIALIST 48-col locked stack**. Carries /073-precedent dispersion-destabilization risk — at SPECIALIST 50-seed × 30-trial budget, feature-stack changes destabilize cross-seed Optuna trajectory diversity. /076 is already at dispersion 32.95 (basin-lottery floor); stack augmentation may push dispersion higher OR may paradoxically reduce it by giving the model crypto-native focus. The mechanism is real but the SPECIALIST-mode side-effect is empirically demonstrated to be destabilizing.
- **Falsifier**: /AAVE-2 IS Sharpe < +0.10 AND OI features collectively < 15% of gain → signal-absent verdict (2nd strike).

### Rec 3 — Per-symbol R3 OOD cutoff override (0.70 SHARED → 0.55 AAVE-only) [LOWER PRIORITY — STRUCTURAL]

- **Axis family**: `risk-primitive` (per-symbol R3 override).
- **What**: in `run_iteration_AAVE2.py`, override R3 cutoff for AAVE only from 0.70 (SHARED default) to 0.55. Other specialists retain 0.70.
- **Mechanism**: IS/OOS divergence diagnosis shows the model's predictions are direction-noisy in chop (IS) and direction-correct in trend (OOS). A tighter OOD cutoff (0.55 = predictions outside 55th percentile of training distribution get killed) would reject chop-regime predictions that lost in IS while preserving trend-regime predictions that won in OOS.
- **Why LOWER priority**: **breaks cross-specialist comparability** and is a **per-symbol methodology-override which weakens BUNDLE-002 assembly's verdict integrity**. The 0.70 SHARED cutoff is the methodology baseline; deviating breaks the comparability with DOT/063 / ETH/064 / BTC/065 that BUNDLE-001 PROMISING-validation relied on. Mechanism is correct for AAVE specifically but adds methodology-axis risk to the seat-eligibility decision.
- **Falsifier**: /AAVE-2 IS trades < 50 → cutoff too tight, revert or widen.
- **Deploy only if Rec 1 + Rec 2 are both adopted and /AAVE-2 needs a 3rd bit.**

### Axis-rotation note

All three recs are from families the QR has used in the prior 5 SPECIALISTs (/067 LTC `universe`, /073 ETH `feature-family`, /072 BTC `risk-primitive`). **Under the cycle-7 per-symbol regime-specialist mandate (`feedback_v1_cycle6_per_symbol_regime_specialist_mandate`), axis-family rotation is SUSPENDED**, so this constraint is automatically waived.

### Disposition

- **If user authorizes /AAVE-2**: Rec 1 (ATR) is the canonical move — single-bit, methodology-preserving, clean falsifier.
- **If autopilot continues without /AAVE-2 authorization**: AAVE seat dropped; /077 ICPUSDT proceeds (already running, PID 3619041); next NEW SYMBOL candidate from autopilot mine-queue follows /077 verdict.

## Next Iteration Ideas

1. (User-decision) Authorize /AAVE-2 with Rec 1 ATR recalibration, OR drop AAVE seat at 1st strike and continue autopilot rotation.
2. (Pre-/077-Phase-7 prep) When /077 ICP closes out, compare the per-symbol Spearman top-10 IC ranking vs DOT/063 — if /077 outcome is also NEGATIVE with broad-based importance + high dispersion, the "inherited 48-col stack not symbol-portable" hypothesis crystallizes and Critic Rec 2 (feature-stack adequacy pre-screen as gate) becomes the meta-axis for the next autopilot iteration.
3. (Future SPECIALIST briefing) Make per-quarter regime decomposition + quarterly directional tagging mandatory in NEW SYMBOL EDA tables (Critic Rec 1 in /076 review). Add `specialist_dispersion_mean > 30` as a pre-registered Section 4 gate (Critic Rec 3 in /076 review).
4. (Catalog hygiene) Add /076 to `briefs-v1/specialist_catalog.md` as second consecutive NEW SYMBOL universe-extension NEGATIVE (/075 ATOM + /076 AAVE), tracking toward cycle-7 mandate revision threshold.
