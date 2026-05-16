# iter-v3/057 — Candidate Axes Ranking

EDA-driven axis selection per `feedback_v3_axis_selection_quant_discipline.md`.
Mandate from Critic /054/055/056 FINAL recommendations: A4 base-stack reordering
OR NEW feature family.

Cycle 4 status: 6/10 done. 6 consecutive PATH E (CPCV-INVARIANT NULL) firings.

## Candidate axis ranking

### Tier 1 — A4 base-stack SWAP (RECOMMENDED)

| Sub-axis | DROP target | ADD target | Family change | Rationale | Risk |
|---|---|---|---|---|---|
| **1a (LOCKED)** | **ret_skew_50** | **parkinson_gk_ratio_20** | tail_risk → price_efficient_vol | Bottom-3 importance BCH+TRX; new family first-in-category; max |IC|=0.245 | LDO regression (rank 8 ret_skew_50 = MID) |
| 1b | ret_skew_50 | obv_slope_50 | tail_risk → volume_micro | 2nd-ranked Spearman; max |IC|=0.438 (closer to gate) | Stronger correlation with ema_spread_atr_20 |
| 1c | ret_skew_50 | bb_width_pct_rank_100 | tail_risk → regime | 3rd-ranked; max |IC|=0.199 (cleanest); regime family already has 2 | Adds 3rd regime feature; may over-cluster |
| 1d | btc_ret_14d | parkinson_gk_ratio_20 | cross_btc → price_efficient_vol | Bottom-3 BCH+TRX but mid LDO(6); higher load-bearing risk | LDO regression worse than 1a |

**Tier 1a is the LOCKED choice** — strongest combination of:
- Lowest drop-risk (ret_skew_50 has lowest load-bearing across all 3 syms vs btc_ret_14d which is LDO-mid)
- Strongest add-univariate-Spearman (parkinson_gk_ratio_20 p<0.005 all 3 syms)
- Lowest max |IC| with base-14 (0.245 vs 0.438 obv_slope_50 vs 0.440 hurst_200)
- Family first-in-category (price_efficient_vol absent from base-14)

### Tier 2 — NEW feature family at slot 15 (SECONDARY — NOT recommended for /057)

Per Critic /054: "NEW feature families remain UNTESTED". However:
- The 15th-slot SWAP family was closed at "Category 2 composed features" scope.
- A 14 → 15 EXPANSION at single-seed n_trials=35 single-axis adds 1 feature
  WITHOUT removing any; preserves the cycle-4 structural pin even more strongly.
- 14 → 14 SWAP (Tier 1) is structurally weaker than EXPANSION but cleaner because:
  (a) doesn't expand Optuna search space
  (b) doesn't risk lottery effects of higher dimensionality
  (c) explicitly tests whether the new feature beats the dropped one

Tier 2 is deferred to /058 if Tier 1 fails (PATH C).

### Tier 3 — Other axes (NOT for /057)

- **A2 DSR reformulation** — CLOSED at /055 + /056 (mechanically sound but ZERO
  discrimination at single-seed EXPLORATION; revisit at /061 CONFIRMATION).
- **NEW risk primitive (drawdown brake variants)** — CLOSED at /054.
- **NEW labeling architecture** — Mass feature expansion mandated for /062 cycle 5.
- **Universe expansion** — CLOSED-symbols (HBAR/AVAX/ALGO drag); deferred.

## EDA evidence summary (Tier 1a)

### Why ret_skew_50 drop

- Per-symbol rank: BCH 12/14, LDO 8/14, TRX 12/14 (bottom-3 on 2 of 3 syms)
- Portfolio importance: 137.6 (rank 12 of 14)
- NOT load-bearing (regime_momentum_signed_5d was THE per-symbol load-bearing feature
  per /041 falsified-multi-drop lesson)
- Family: tail_risk (already 5 features in V3_BASE_14 — losing 1 keeps 4)

### Why parkinson_gk_ratio_20 add

| Criterion | Value | Verdict |
|---|---:|:---|
| Mean |Spearman| ρ | 0.0514 | Strongest in candidate pool |
| Max |Spearman p-value| | 0.0033 | All 3 syms significant (p<0.005) |
| ADF p (BCH/LDO/TRX) | 1e-19/1e-11/4e-17 | All stationary |
| max |IC| with V3_BASE_14 | 0.245 | Below 0.50 strict gate |
| IC vs proposed drop | 0.09 / 0.05 / 0.11 | Orthogonal signal |
| Skew | 0.66 (BCH) | Well-behaved |
| Kurtosis | 0.69 (BCH) | Well-behaved |
| Family for v3 base | price_efficient_vol — FIRST-IN-CATEGORY | Structural distinction |
| n_valid (all 3 syms) | >2700 | Sufficient data |

### Predicted importance rank

Heuristic mapping from |Spearman| ρ to importance rank (based on /028/056 stack):
- |ρ| ≈ 0.05 typically produces importance 100-300 (rank 8-12 of 14)
- |ρ| ≈ 0.07 typically produces importance 200-400 (rank 6-10 of 14)
- parkinson_gk_ratio_20 |ρ| = 0.039-0.071 → expected rank 8-12, importance 100-400

**Importance threshold for PROMISING**: ≥ 30 in ≥1 symbol. Expected to clear easily.

## Locked decision

iter-v3/057 axis = A4 base-stack SWAP:
- DROP: `ret_skew_50`
- ADD: `parkinson_gk_ratio_20`

The setup commit will:
1. Edit `src/crypto_trade/features_v3/__init__.py`:
   - Replace `"ret_skew_50",` with `"parkinson_gk_ratio_20",` in V3_FEATURE_COLUMNS_TOP_N
   - Update inline comment for the tuple entry
   - Add a comment line explaining iter-v3/057 SWAP rationale
2. Update `run_baseline_v3.py`: ITERATION_LABEL = "v3-057"
3. Add adversarial test (if not already present) for parkinson_gk_ratio_20 past-only discipline

NO other code change. Strategy bit-identical to /056 except for this 1-feature swap.
NO new compute function needed (parkinson_gk_ratio_20 already in parquet via
`add_price_efficient_vol_v3_features`).

Cannot be renegotiated post-hoc per `feedback_v3_axis_selection_quant_discipline.md`.
