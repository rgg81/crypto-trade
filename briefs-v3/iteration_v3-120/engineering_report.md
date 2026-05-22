# Engineering Report — iter-v3/120

## Headers

- **Iteration**: iter-v3/120
- **Branch**: `iteration-v3/120`
- **Commit SHA**: `294ac0e` (setup commit — code committed before backtest per discipline)
- **Brief SHA**: `26d99f2`
- **Gate SHA**: `1145c30` (PASS)
- **Hardware**: WSL2 / Linux 6.6.114.1-microsoft-standard-WSL2
- **Wall-clock time**: 3.14h (within 6h hard cap; aligns with /059 CONFIRMATION 3.60h baseline)
- **Runner invocation**: `uv run python run_baseline_v3.py --n-trials 35 --clean-oof`

---

## 1. Setup Verification

### 1.1 Code SHA and brief SHA

| Artifact | SHA | Description |
|---|---|---|
| Setup commit (code) | `294ac0e` | `feat(iter-v3/120): activate CONFIRMATION TWO-COMPONENT bundle state` |
| Research brief | `26d99f2` | `docs(iter-v3/120): research brief — CONFIRMATION TWO-COMPONENT bundle` |
| Phase 5.5 gate | `1145c30` | `docs(iter-v3/120): phase 5.5 gate PASS` |

Gate verdict: OVERALL=PASS (all 9 sections + 7 additional checks verified).

### 1.2 Ruff lint and format

Inherited from setup commit `294ac0e`. No new source files introduced at /120 (runner-only changes). Lint clean per prior iteration chain.

### 1.3 Integration tests

No new feature code was introduced at /120. Component A (`no_confirm` exit) and Component B (`ret5d_signed_tbi`) are unchanged from their EXPLORATION commits and carry their existing unit test coverage. Bundle-state pre-flight assertions (4 assertions verified at runner startup) act as the integration smoke test for this iteration.

---

## 2. Implementation Summary

### 2.1 Bundle state enabled at 3 surfaces

| Surface | File | Change |
|---|---|---|
| Runner config | `run_baseline_v3.py:2037` | `enable_no_confirm_exit=False` → `True` |
| Pre-flight assertion | `run_baseline_v3.py:~2959` | `is False` → `is True` |
| Pre-flight accretion guard | `run_baseline_v3.py:~1150` | expected tuple `(False, 0.50, 4)` → `(True, 0.50, 4)` |

### 2.2 New bundle-state pre-flight block

Four assertions verify BOTH components simultaneously at runner startup:
- `enable_no_confirm_exit is True` (Component A)
- `no_confirm_trigger_atr == 0.50` (Component A parameter)
- `no_confirm_k_candles == 4` (Component A parameter)
- `"ret5d_signed_tbi" in V3_FEATURE_COLUMNS_TOP_N` (Component B)
- `len(V3_FEATURE_COLUMNS_TOP_N) == 15` (Component B feature-count guard)

### 2.3 Component B preserved in V3_FEATURE_COLUMNS_TOP_N

`V3_FEATURE_COLUMNS_TOP_N` remains 15 features (14 anchor + `ret5d_signed_tbi` at index 14), unchanged from /119 head state. `ITERATION_LABEL = "v3-120"` and MODEL_SPECS prefix `"v3-120-..."` set. CPCV n_paths=45, embargo=27, REQUIRED_GAP=66 unchanged. Walk-forward POST-FIX at `e149e9d` carried forward.

### 2.4 Unchanged constants

- `OOS_CUTOFF_DATE = "2025-03-24"` — UNCHANGED
- `training_months = 24` — UNCHANGED
- `ENSEMBLE_SEEDS` 10-tuple — UNCHANGED
- `CONFIRMATION_ENSEMBLE_SIZE = 10` — UNCHANGED
- `n_trials = 35` — UNCHANGED

---

## 3. Key Metrics Table

### 3.1 /120 vs /059 canonical baseline

| Metric | /059 IS | /059 OOS | /059 ratio | /120 IS | /120 OOS | /120 ratio | Δ IS | Δ OOS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| monthly_sharpe | 1.0894 | 0.5791 | 0.5316 | 0.7293 | 1.6946 | 2.3236 | −0.3601 | +1.1155 |
| daily_sharpe | 2.7092 | 1.4359 | 0.5300 | 1.5954 | 4.0750 | 2.5541 | −1.1138 | +2.6391 |
| max_drawdown | 30.97% | 34.53% | 1.115 | 39.81% | 23.73% | 0.596 | +8.84pp | −10.80pp |
| profit_factor | 1.4949 | 1.2107 | 0.810 | 1.2669 | 1.7600 | 1.389 | −0.228 | +0.549 |
| win_rate | 33.33% | 38.30% | 1.149 | 31.46% | 42.71% | 1.358 | −1.87pp | +4.41pp |
| n_trades | 171 | 94 | 0.550 | 178 | 96 | 0.539 | +7 | +2 |
| total_pnl | 78.18 | 22.74 | 0.291 | 46.02 | 64.67 | 1.405 | −32.16 | +41.93 |
| monthly_calmar | 2.5246 | 0.6585 | 0.261 | 1.1560 | 2.7254 | 2.358 | −1.369 | +2.067 |

### 3.2 Methodology metrics

| Metric | /059 | /120 | Gate threshold | /120 result |
|---|---:|---:|---|---|
| PBO (mean per-cell) | 0.1278 | 0.0957 | < 0.40 | PASS |
| PSR | 1.0 | 1.0 | > 0.95 | PASS |
| frac_positive_paths | 0.6444 | 0.6444 | ≥ 0.55 | PASS |
| DSR_relative | 0.1134 | 1.0 | informational | informational |
| OOS/IS Sharpe ratio | 0.5316 | 2.3236 | ≥ 0.5 | PASS |
| n_trials | 1050 | 1050 | — | matches /059 |
| n_effective_trials | 19 | 19 | — | matches /059 |
| OOS trades | 94 | 96 | 130 (informational) | below floor (informational; /059 also below) |

### 3.3 CPCV paths summary (45 paths)

| Stat | Value |
|---|---:|
| frac_positive_paths | 0.6444 (29 of 45) |
| Mean path Sharpe | +0.303 |
| Q25 path Sharpe | −0.243 |
| Q50 path Sharpe | +0.335 |
| Q75 path Sharpe | +0.838 |
| Min path Sharpe | −1.318 |
| Max path Sharpe | +1.880 |

### 3.4 /120 vs component-alone single-seed EXPLORATION reference

| Reference | IS Sharpe | OOS Sharpe | n_trials | Mode |
|---|---:|---:|---:|---|
| /116 (Component A alone) | +0.6246 | +1.1089 | 35 | 3-seed EXPLORATION |
| /119 (Component B alone) | +0.8492 | +0.8420 | 35 | 3-seed EXPLORATION |
| /120 bundle | +0.7293 | +1.6946 | 1050 | 10-seed CONFIRMATION |

Note: these are cross-mode comparisons (3-seed EXPLORATION vs 10-seed CONFIRMATION). The F1 threshold (+1.0089) was pre-calibrated against the single-seed references with a documented multi-seed compression caveat.

---

## 4. Per-Symbol IS Attribution vs /059

IS `net_pnl_pct` comparison (from `in_sample/per_symbol.csv`):

| Symbol | /059 IS net_pnl_pct | /120 IS net_pnl_pct | Delta | Trades /059 | Trades /120 |
|---|---:|---:|---:|---:|---:|
| BCH | +109.23 | +39.92 | **−69.31** | 83 | 89 |
| TRX | +3.95 | +7.27 | **+3.32** | 79 | 79 |
| LDO | +0.89 | +6.40 | **+5.51** | 9 | 10 |

IS summary: BCH net_pnl_pct regressed sharply (−69.31 pct). TRX and LDO modestly improved. The headline IS Sharpe collapse to +0.7293 is attributable almost entirely to BCH IS PnL compression — BCH contributed 95.76% of /059 IS total but only 74.48% at /120 despite a higher trade count (+6 trades). This is the primary IS-regime-cost signature of Component A (no_confirm) operating on the BCH 2022-2023 bear/chop period where the rule early-exits trades that subsequently recover.

---

## 5. Per-Symbol OOS Attribution vs /059

OOS `net_pnl_pct` comparison (from `out_of_sample/per_symbol.csv`):

| Symbol | /059 OOS net_pnl_pct | /120 OOS net_pnl_pct | Delta | Trades /059 | Trades /120 |
|---|---:|---:|---:|---:|---:|
| BCH | +26.58 | +72.03 | **+45.45** | 34 | 30 |
| TRX | +6.47 | +19.06 | **+12.59** | 48 | 52 |
| LDO | −14.46 | +1.28 | **+15.75** | 12 | 14 |

OOS summary: ALL 3 symbols improved vs /059. BCH produced the largest absolute OOS lift (+45.45 pct) despite 4 fewer trades (30 vs 34), indicating higher average PnL per trade. LDO recovered from deeply negative (−14.46) to marginally positive (+1.28), a +15.75 swing. TRX contributed a +12.59 improvement. The OOS improvement is broad-based — anti-single-symbol-carrier pattern.

---

## 6. C6 Feature Importance

### 6.1 Portfolio importance (multi-seed mean)

C6 (`ret5d_signed_tbi`) ranks **15/15** in the portfolio importance table (last position), with importance 128.6 out of 4731.2 total = **2.72% portfolio share**. This is slightly above the /119 single-seed share (2.6% of 5847.67 total), confirming the pattern is stable across seed settings.

`regime_momentum_signed_5d` ranks **14/15** at 171.9, down from the /060 anchor of 506.67 — a 66.1% drop.

### 6.2 Per-symbol importance ranks (multi-seed mean)

| Feature | BCH rank | BCH imp | LDO rank | LDO imp | TRX rank | TRX imp | Portfolio rank | Portfolio imp |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `regime_momentum_signed_5d` | 13/15 | 52.6 | 14/15 | 47.0 | 12/15 | 72.3 | 14/15 | 171.9 |
| `ret5d_signed_tbi` (C6) | 15/15 | 36.4 | 15/15 | 34.7 | 15/15 | 57.5 | 15/15 | 128.6 |

C6 ranks dead-last on every symbol and in the portfolio. Compared to the /119 single-seed EXPLORATION, where C6 ranked 15/15 at 27.8% per-symbol (reported as importance 153 / 5847.67 total), the multi-seed mean confirms C6's allocation remains at the bottom of the stack. TRX shows the highest C6 allocation (57.5) consistent with TRX being the symbol where the taker-buy-imbalance signal most overlaps with the 5-day return sign.

### 6.3 Sister redistribution context

The combined `ret_5d × regime-sign` sister family (regime_momentum_signed_5d + ret5d_signed_tbi) at /120:
- Combined importance: 171.9 + 128.6 = **300.5** (portfolio)
- vs /119 single-seed sister family: 175.67 + 153.0 = 328.67
- vs /060 anchor (no C6): 506.67

The sister family NET continues to compress from the /060 anchor (−40.7%), but is somewhat stabilized at multi-seed relative to /119 single-seed (300.5 vs 328.67). The redistribution toward anchor features is confirmed: `range_realized_vol_50` ranks 1st, `max_dd_window_50` 2nd, `ret_skew_200` 3rd — consistent with the /119 diary §3.5 prediction.

---

## 7. IC Matrix Summary

The IC matrix (`ic_matrix.csv`) confirms the key structural relationships:

- `regime_momentum_signed_5d` × `vwap_dev_20`: IC = **+0.7642** (high, pre-registered algebraic correlation)
- `ret5d_signed_tbi` × `regime_momentum_signed_5d`: IC = **−0.7229** (high inverse, pre-registered algebraic sister)
- `ret5d_signed_tbi` × `vwap_dev_20`: IC = **−0.5668** (expected consequence of IC with regime_momentum)
- `ret5d_signed_tbi` × `ema_spread_atr_20`: IC = **−0.4307** (moderate inverse)

These high pairwise ICs are all pre-registered under the Category-2 composed feature IC carve-out (`feedback_v3_engineered_feature_pivot.md`). The importance-floor gate (≥ 30 threshold per the carve-out) is the applicable gate for C6, and C6 meets it at 36.4 (BCH), 34.7 (LDO), 57.5 (TRX) — all above 30 on a per-symbol basis.

No new unexpected high-IC pairs in the remaining 13 anchor features (max IC among non-C6/non-regime pairs: `sym_vs_btc_ret_7d` × `ema_spread_atr_20` at 0.4856).

---

## 8. ADF Stationarity

ADF test results are present in `adf_test.csv`. January 2020 month shows empty ADF entries (first training month — insufficient lookback for ADF). From February 2020 onward the ADF computes normally. `ret5d_signed_tbi` and `regime_momentum_signed_5d` ADF p-values are consistent with prior iterations — both pass the p < 0.05 stationarity criterion in the later months of the IS window per the /119 EDA records (BCH ADF=−7.753, LDO=−8.128, TRX=−10.295 at IS-end month).

---

## 9. Falsifier Evaluation (BINDING — Central Section)

### F1 — Stacking-linearity

- **Threshold**: bundle multi-seed OOS ≥ max(+1.1089, +0.8420) − 0.10 = **+1.0089**
- **Observed**: bundle OOS = **+1.6946**
- **Result**: **F1 PASS** (+1.6946 ≥ +1.0089; surplus = +0.6857)

The bundle OOS Sharpe clears the stacking-linearity threshold by a wide margin. Relative to the individual component single-seed references: the bundle beats /116 alone by +0.5857 and beats /119 alone by +0.8526. The threshold is explicitly calibrated against single-seed EXPLORATION-mode references with a pre-registered multi-seed compression caveat; F1 PASSES on its own pre-registered terms.

### F2 — TRX-concentration

- **Threshold**: TRX positive-PnL share > 50% → FLAG; > 65% → FULL BLOCK
- **Observed** (from `comparison.csv` per-symbol section): BCH weighted_pnl = 49.6244, LDO = 2.8934, TRX = 12.1515; ALL three symbols are positive.
- **Positive total**: 49.6244 + 2.8934 + 12.1515 = **64.6693**
- **TRX share of positive total**: 12.1515 / 64.6693 = **18.79%**
- **LDO portfolio share**: 2.8934 / 64.6693 = **4.47%** (above −25% flag threshold)
- **Result**: **F2 PASS** (TRX 18.79% << 50% concentration-watch band; no flag triggered)

The multi-seed CONFIRMATION produced remarkably low TRX concentration relative to the /119 single-seed reference (52.05% at /119 single-seed). BCH dominates the positive OOS total at 76.74% — consistent with BCH's historical role as the primary PnL generator in the 3-symbol universe.

### F3 — Sister-redistribution stability (CONJUNCTIVE AND)

- **Condition (a)**: `regime_momentum_signed_5d` multi-seed importance < 253.34 (= 506.67 × 0.50)?
  - Observed: **171.9** (66.1% drop from /060 anchor 506.67)
  - **Leg (a): TRUE** (171.9 < 253.34)
- **Condition (b)**: `ret5d_signed_tbi` (C6) multi-seed importance < 5% of portfolio total?
  - Observed: 128.6 / 4731.2 = **2.72%**
  - **Leg (b): TRUE** (2.72% < 5%)
- **F3 fires if BOTH (a) AND (b)**: both legs hold → **F3 FIRES**
- **Result**: **F3 FIRES** — "allocation cannibal without contribution" at multi-seed. Per brief Section 4 F3 verdict tree: DROP Component B (C6); revert to /116-only.

Critical observation: the single-seed EXPLORATION at /119 produced the same qualitative pattern (regime_momentum importance 175.67 → 65.3% drop; C6 share 2.6% < 5%) — the multi-seed CONFIRMATION did not resolve the pattern; it confirmed it with remarkable numerical stability (multi-seed: 171.9, 66.1%, 2.72% vs single-seed: 175.67, 65.3%, 2.6%). F3 fires cleanly and unambiguously.

### F4 — IS regime-cost floor

- **Threshold**: bundle multi-seed IS monthly Sharpe ≥ **+0.79** (= /059 IS +1.0894 − 0.30)
- **Observed**: IS = **+0.7293**
- **Gap**: +0.7293 − +0.79 = **−0.0607** (misses by 0.0607)
- **Result**: **F4 FAILS by 0.0607**

The regime-cost prediction direction is correct: Component A (no_confirm) produces an IS-cost in the 2022 bear / 2023 chop regimes where the rule exits trades that subsequently recover. The QR's pre-registration correctly identified the looser IS-floor option (−0.50 = +0.59) vs the tighter choice (−0.30 = +0.79) and selected the tighter floor. The observed IS sits 0.06 below the tighter floor — a knife-edge miss. BCH IS net_pnl_pct collapse (−69.31 pct vs /059) is the primary driver: BCH accounted for 95.76% of /059 IS PnL; at /120 BCH IS dropped significantly in absolute PnL terms while trade count actually increased by 6 (+7.2%), confirming the no_confirm channel is cutting BCH trades that would have recovered to full TP.

### F5 — Per-symbol cascade-attribution

- **Threshold**: ≥ 2 of 3 symbols multi-seed OOS weighted_pnl Δ > /059 baseline (BCH > +24.75, LDO > −6.18, TRX > +4.16)
- **Observed** (from `comparison.csv` per-symbol section):
  - BCH: 49.6244 vs baseline 24.7502 → Δ **+24.87** (positive) → condition BCH > +24.75: **PASS**
  - LDO: 2.8934 vs baseline −6.1783 → Δ **+9.07** (positive) → condition LDO > −6.18: **PASS**
  - TRX: 12.1515 vs baseline 4.1639 → Δ **+7.99** (positive) → condition TRX > +4.16: **PASS**
- **Positive delta count**: **3/3** — ALL symbols improved
- **Result**: **F5 PASS** (3/3 ≥ required 2/3)

Full broad-based OOS cascade. This is the strongest per-symbol result in the v3 cycle-6 sequence. All 3 symbols beating the /059 OOS baseline — including LDO which swung from −14.46% OOS net_pnl_pct at /059 to +1.28% at /120, and BCH which produced the largest absolute OOS lift (+45.45 pct despite 4 fewer trades).

### Falsifier summary table

| Falsifier | Threshold | Observed | Result |
|---|---|---|---|
| F1 stacking-linearity | bundle OOS ≥ +1.0089 | +1.6946 | **PASS** |
| F2 TRX-concentration | TRX share ≤ 65% | 18.79% | **PASS** |
| F3 sister-redistribution | NOT BOTH (regime_mom < 253.34 AND C6 share < 5%) | BOTH hold (171.9 < 253.34; 2.72% < 5%) | **FIRES** |
| F4 IS regime-cost floor | IS ≥ +0.79 | +0.7293 | **FAILS by 0.06** |
| F5 per-symbol cascade | ≥ 2/3 symbols positive Δ | 3/3 positive | **PASS** |

---

## 10. CONFIRMATION Verdict Matrix (Section 8 first-match-wins)

Evaluation proceeds in gate order per brief Section 8.

**Step 1 — Hard methodology gates:**
- PBO = 0.0957 < 0.40: PASS
- PSR = 1.0 > 0.95: PASS
- frac_positive_paths = 0.6444 ≥ 0.55: PASS
- OOS/IS ratio = 2.3236 ≥ 0.5: PASS
- OOS trades = 96 < 130: informational flag only (not a hard block per /059 precedent at 94 trades)
- All hard methodology gates: **CLEAR**

**Step 2 — Pre-committed falsifiers:**
- F1 stacking-linearity: PASS
- F2 TRX-concentration: PASS
- F3 sister-redistribution: **FIRES** → per brief Section 8.4 component-DROP fallback tree: DROP Component B (C6); revert to /116-only for MERGE evaluation
- F4 IS regime-cost floor: **FAILS** → IS leg NEGATIVE
- F5 per-symbol cascade: PASS

**Step 3 — BOTH-must-improve gate:**
- IS = +0.7293 < +1.0894: **FAILS** → BASELINE_V3.md does NOT update

**First-match-wins decision:**
F3 FIRES and F4 FAILS. Both are pre-committed binding falsifiers. Per the brief's first-match-wins semantics and Section 8.4 component-DROP fallback tree:
- F3 mandates DROP Component B (C6) → revert to /116-only
- F4 mandates NO-MERGE on the IS-floor leg regardless of OOS performance
- BOTH-must-improve gate independently confirms BASELINE_V3.md does not update

**Mechanical classification**: **CONFIRMATION-NO-MERGE** (F3 component-drop + F4 IS-floor breach; BASELINE_V3.md BLOCKED)

Note: the "revert to /116-only" Component A evaluation — whether /116-alone at 10-seed would satisfy the BOTH-must-improve gate — is not available on disk. A /116-only 10-seed run would be required to determine whether Component A alone merits a cycle-6 PARTIAL-MERGE. This is left to the QR's Phase 8 diary decision on whether to run /116-only at CONFIRMATION-spec.

---

## 11. Mechanism Analysis — Super-additivity at the Bundle Level

### 11.1 What the numbers say

The bundle OOS Sharpe (+1.6946) beats the F1 stacking-linearity threshold (+1.0089) by +0.6857 — nominally "super-additive" relative to the single-seed reference. However, this comparison is cross-mode (3-seed EXPLORATION vs 10-seed CONFIRMATION), which introduces a fundamental confound:

- /116 single-seed EXPLORATION OOS: +1.1089
- /119 single-seed EXPLORATION OOS: +0.8420
- Bundle multi-seed CONFIRMATION OOS: +1.6946

The bundle at +1.6946 is below the naive linear sum of the two single-seed references (1.1089 + 0.8420 = 1.9509), meaning it is **sub-additive relative to the naive single-seed sum** (by −0.2563). This is expected: independent single-seed runs each carry their own Optuna variance upward bias; the 10-seed mean suppresses this variance.

### 11.2 Whether genuine super-additivity can be claimed

A definitive claim of "super-additive stacking" requires comparing bundle OOS to component-alone OOS on the SAME measurement basis (both at 10-seed CONFIRMATION). No /116-alone 10-seed run exists on disk. The pre-registered F1 framework acknowledges this limitation explicitly (brief Section 4 F1 multi-seed compression caveat) and calibrates the threshold against single-seed references with an implicit assumption that the multi-seed bundle beats the single-seed-mode maximum by some margin.

What can be stated with confidence:
1. The bundle produces OOS +1.6946 — the highest multi-seed CONFIRMATION OOS Sharpe in v3 history (prior record: /059 +0.5791)
2. The bundle clears F1 on its pre-registered own terms (> +1.0089)
3. The mechanism interaction (slot-freeing cascade from Component A operating on a loss-surface reorganized by Component B) is plausible as a genuine synergy, but CANNOT be empirically validated without a /116-alone 10-seed control run

### 11.3 Is the super-additive OOS lift real or an artifact?

The most parsimonious explanation is that the OOS lift is primarily attributable to Component A (no_confirm slot-freeing cascade) under 10-seed averaging, and C6 (Component B) contributes marginally via the loss-surface redistribution that elevates `max_dd_window_50` and `ret_kurt_50`. The F3 FIRE confirms C6 operates as a redistribution catalyst rather than a direct edge contributor — C6's 2.72% portfolio importance share is mechanically insufficient to drive a +1.1 OOS Sharpe lift on its own.

The OOS lift is likely real (not an artifact of seed selection — 10-seed unified ensemble averaging confirms it), but the attribution between Component A and Component B cannot be disentangled without a /116-only 10-seed control. The sub-additivity relative to the single-seed sum (−0.2563 vs 1.9509) is consistent with multi-seed variance compression on both components, with the bundle landing at the expected multi-seed level for the Component A slot-freeing mechanism at this universe.

**Key diary finding**: F3 FIRES at multi-seed, meaning the bundle's OOS performance is driven by Component A (no_confirm) acting on a reshaped feature landscape, not by C6 as a direct signal contributor. C6's role is as a redistribution catalyst that was correctly identified as PROMISING-FEATURE-MECHANICAL at /119 — it reorganized importance without contributing direct edge. The fact that F3 fires WHILE the OOS Sharpe hit an all-time v3 record (+1.6946) is the central paradox: the bundle WORKS (OOS evidence) but C6's mechanism (redistribution catalyst) does NOT justify its inclusion by the pre-registered falsifier (F3 FIRES). The honest conclusion is that Component A alone (at 10-seed CONFIRMATION) likely produces the OOS lift observed, with C6 contributing negligible direct signal.

---

## 12. Mechanical Classification

Per the Section 10 verdict matrix:

**CONFIRMATION-NO-MERGE**

Grounds: F3 FIRES (sister-redistribution stability — "allocation cannibal without contribution" confirmed at multi-seed: regime_momentum_signed_5d down 66.1% from anchor, C6 share 2.72% < 5%) + F4 FAILS (IS regime-cost floor: IS +0.7293 < +0.79 threshold, miss of 0.0607) + BOTH-must-improve gate: IS does not beat /059 (+1.0894).

The Critic may override this classification. Specifically, the Critic should evaluate:
1. Whether the extraordinary OOS performance (+1.6946, all-time v3 record, 3/3 symbols positive, F1 and F2 and F5 all PASS) warrants a PARTIAL-MERGE recommendation for Component A alone
2. Whether the F4 knife-edge fail (0.06 below floor) triggers a recommendation for a /116-only 10-seed run to isolate Component A's CONFIRMATION performance
3. Whether the F3 FIRE should be interpreted as "C6 is a net-neutral inclusion" rather than "C6 is actively harmful" — given the OOS performance, the redistribution catalyst hypothesis is not falsified in the OOS direction

**Cycle 6 closes with CONFIRMATION-NO-MERGE. BASELINE_V3.md UNCHANGED.**

---

## Status

OVERALL=READY-FOR-CRITIC
