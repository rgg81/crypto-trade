# Iteration v3-021 — Research Brief

**Type**: EXPLORATION (cadence #3 of 10 in the post-bootstrap cycle; **STRUCTURAL axis (Category 5 — NEW universe; denominator expansion)** — first universe-expansion EXPLORATION in v3 catalog per `feedback_v3_iter019_axis_priorities.md` HIGH-priority axis #2b LOCKED 2026-05-07 + `feedback_v3_concentration_is_signal.md` LOCKED 2026-05-07)
**Track**: v3 (rigor arm) — twenty-first iteration
**Branch**: `iteration-v3/021` (off `iteration-v3/020` head; analysis commit `a360251` shipped before this brief)
**Date**: 2026-05-07
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
n_trials         = 35             # SET BY --exploration default (iter-v3/020 establishment)
colsample_bytree = 1.0            # HARDCODED by --exploration
OOS_CUTOFF_MS    = 1742774400000  # millisecond representation
```

**Sacred constants UNCHANGED.** The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–020 briefs / engineering reports / Critic / diaries; iter-v3/021 EDA `analysis/iteration_v3-021/symbol_candidate_eda.py` outputs (committed at SHA `a360251` BEFORE this brief). The EDA reads ONLY pre-OOS-cutoff IS-window kline data for ranking; OOS-window data is reported informationally only and does NOT enter the composite scoring or top-2 recommendation logic. iter-v3/018 IS trades.csv is also read (for cross-baseline correlation reference) but contaminates nothing — the IS partition is mechanical at `OOS_CUTOFF_MS`.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (cadence #3 of 10 post-bootstrap)
Wall-clock budget: < 30 min target / 2h hard cap
Single-axis variation: NEW universe — V3_MODELS expands 3 → 5 symbols
                       (BCH+LDO+TRX baseline) + (HBAR+AVAX additions)
                       per Critic FINAL Rec #1 of iter-v3/020 (SHA `f913724`) +
                       `feedback_v3_concentration_is_signal.md` LOCKED orthogonal mechanism
Cadence: EXPLORATION #3 of 10 needed before next CONFIRMATION (earliest = iter-v3/029)
Axis category: 5 (NEW universe — denominator expansion; HIGH-priority axis #2b
               per feedback_v3_iter019_axis_priorities.md LOCKED + feedback_v3_concentration_is_signal.md
               LOCKED — orthogonal-mechanism alternative to per-symbol-cap scaling)
ANCHOR: iter-v3/018 BOOTSTRAP baseline (multi-seed mean +0.3788 IS / +0.3869 OOS)
NOT a gate-threshold knob. NOT a feature-pruning variation. NOT a feature-add variation.
NOT a labeling change. NOT a model architecture change. NOT a risk-primitive variation.
This iteration NEVER updates BASELINE_V3.md.
```

**Justification — STRUCTURAL universe-expansion axis (per `feedback_v3_iter019_axis_priorities.md` LOCKED + `feedback_v3_concentration_is_signal.md` LOCKED + `feedback_structural_over_knob_exploration.md` Category 5)**:

After iter-v3/020 EXPLORATION-NEGATIVE (clean / PATH C; Critic FINAL SHA `f913724`, diary commit `5287bd6`):

- The per-symbol PnL share cap mechanism (sub-axis A of HIGH-priority #2 concentration architecture) is **CLOSED at the catalog level**. Cap fired at expected counterfactual rate (BCH 12.8%, LDO 9.4%, TRX 10.4%) but SUBTRACTED edge proportional to model conviction — confirming concentration in the 3-symbol BCH+LDO+TRX universe is **lottery-REWARD source NOT lottery-RISK source**. OOS Sharpe Δ -0.72 vs anchor (way below predicted [+0.45, +0.65] lower bound).
- Per `feedback_v3_concentration_is_signal.md` LOCKED 2026-05-07: future axes touching concentration MUST use orthogonal mechanisms. Permitted alternatives: (i) **universe expansion** (denominator expansion — adds more symbols rather than scaling existing ones); (ii) per-symbol drawdown brake (loss-stop semantics); (iii) vol-target ceiling (exposure ceiling); (iv) regime-conditional kill switch (binary off/on).
- **iter-v3/021 axis = HIGH-priority #2b (universe expansion)**, MANDATED by Critic FINAL Rec #1 of iter-v3/020 + diary `5287bd6` pre-commit + `feedback_v3_concentration_is_signal.md` orthogonal-mechanism prescription.
- Forward priority order from `feedback_v3_iter019_axis_priorities.md`:
  1. ~~HIGH — NEW feature families (iter-v3/019)~~ — closed for cycle (PROMISING-INERT)
  2. ~~HIGH — Concentration architecture sub-axis A (per-symbol cap, iter-v3/020)~~ — CLOSED-mechanism (NEGATIVE clean / PATH C)
  3. **HIGH — Concentration architecture sub-axis B (universe expansion, iter-v3/021 mandate)** — current iteration
  4. MEDIUM — DSR gate reformulation
  5. MEDIUM — TRX/2022-Q4 regime gate
  6. LOW — Knob axes (saturated)

**iter-v3/021 first EXPLORATION axis = HIGH-priority #2b (universe expansion / denominator expansion).** Cannot be renegotiated post-hoc per the LOCKED priority order + LOCKED concentration-mechanism rule.

**Why 2-symbol expansion (HBARUSDT + AVAXUSDT) over 1-symbol expansion (HBARUSDT only)**:

The Critic prior in the dispatch was 1-symbol HBARUSDT (cleanest single-axis attribution; AVAX deferred to iter-v3/022 if HBAR is PROMISING). The QR's call after weighing the trade-rate-floor argument is **2-symbol expansion**, with the following rationale:

- **Trade-rate floor mechanics dominate**: iter-v3/018 BOOTSTRAP OOS bundle = 102 trades (seed 42) — already 28 trades short of the 130 BUNDLE-LEVEL trade-rate floor (per `feedback_trade_rate_floor_bundle_level`). Adding 1 symbol at the EDA's calibrated 2.85 gate-retained/month proxy × 17 OOS months ≈ 48 added OOS trades brings bundle to ~150 — bare PASS with no margin. Adding 2 symbols brings bundle to ~198 — comfortable cushion that won't be wiped out by a single below-proxy month.
- **Single-axis discipline preserved**: "Universe expansion from 3 → 5 symbols" is ONE coherent axis (denominator expansion is the SINGLE structural mechanism the EDA evaluates). The 1-vs-2 distinction is a sizing choice within the axis, NOT a separate axis. Per `feedback_structural_over_knob_exploration.md` counter-rule, single-axis ≠ single-knob; "universe goes from {BCH, LDO, TRX} to {BCH, LDO, TRX, HBAR, AVAX}" is genuinely one axis (additive set membership) AND genuinely structural.
- **Diversification quality**: HBARUSDT has the LOWEST mean |corr| in the entire 7-passing-Gate-1 candidate pool (0.4096 vs ADA 0.496, AVAX 0.498, ATOM 0.531, FIL 0.534, ALGO 0.492, VET 0.558). AVAXUSDT has the SECOND-lowest correlation among large-cap candidates (0.4978) AND the HIGHEST average daily quote volume of any Gate-1-passing candidate ($335M). Picking both gives the strongest concentration-reduction surface in the pool.
- **Falsifier-symmetric**: if 2-symbol underperforms vs the QR's expectation (PATH C scenario), the catalog row will record the negative result and a future iter-v3/022 axis can backstep to HBAR-only via the single-axis discipline. The 2-symbol choice is reversible at axis level.
- **EDA-grounded**: the synthesis explicitly flagged the "2-symbol pre-decision" trade-off; both top-2 candidates were analyzed at parity in the ranking output. Picking both is consistent with the EDA's parity treatment.

**Why HBAR + AVAX over other Gate-1-passing candidates** (re-summarizing the EDA finding for brief audit-trail discipline):

- HBAR > ADA: lower correlation (0.41 vs 0.50) — concentration reduction is the iter-v3/021 OBJECTIVE, not just liquidity addition.
- AVAX > FIL/ALGO/ATOM: similar correlation profile to ADA but largest liquidity (AVAX $335M vs FIL $221M, ATOM $106M, ALGO $61M); highest-liquidity Gate-1-passing candidate.
- HBAR + AVAX BOTH have 100% IS coverage, 0 gap candles, ≥24mo pre-IS history (HBAR exactly 24.48mo — just enough), and pre-existing 8h klines in `data/{SYM}/8h.csv` (no fresh fetch required for the historical extent; only data-freshness top-up).

After iter-v3/021 the catalog will have: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 2 (one drop-MKR retention + one expand-to-5) + gate-adx × 1 (CLOSED) + NEW microstructure feature × 1 (CLOSED-narrow) + NEW model arch × 1 (CLOSED-at-config) + NEW labeling arch × 1 (PATH C) + bootstrap CONFIRMATION × 1 + NEW external-data-source feature × 1 (PROMISING-INERT) + NEW risk primitive (per-symbol cap) × 1 (CLOSED-mechanism) + **NEW universe expansion (3→5 symbols) × 1** = 13 unique axis representations after iter-v3/021, **first universe-expansion-as-orthogonal-mechanism axis in v3 catalog**.

---

## Section 1 — Hypothesis

Adding HBARUSDT + AVAXUSDT to V3_MODELS (universe 3 → 5 symbols; 7-primitive risk gate stack BYTE-IDENTICAL to iter-v3/018 anchor; per-symbol cap DISABLED at first commit per iter-v3/020 PATH C closeout; 13 V3_FEATURE_COLUMNS UNCHANGED) will **dilute single-symbol concentration mechanically without removing edge from any incumbent symbol**, because the universe-expansion mechanism is denominator expansion (adding symbols increases the per-symbol-share denominator without scaling existing positions DOWN — the iter-v3/020 cap mechanism's failure mode). Predicted IS Sharpe band [+0.30, +0.55] median +0.40 (anchor +0.38; bands honestly reflect lottery uncertainty from 2 NEW symbols' Optuna-fit quality); predicted OOS Sharpe band [+0.45, +0.70] median +0.55 (improvement above iter-v3/018 OOS anchor +0.3869 by +0.10 to +0.30 from concentration dilution + new uncorrelated edge from HBAR's 0.41 mean-|corr| diversification surface).

**Mechanism explanation** (why universe expansion should help OOS without destroying IS): in concentrated portfolios with N=3 symbols, OOS Sharpe is dominated by whether the dominant symbol's IS-fitted edge generalizes — iter-v3/018 multi-seed showed TRX 66%/56% concentration as a *structural* feature of the 3-symbol universe (not a tuning artifact, since multi-seed averaging only shifted the dominant symbol LDO → TRX without compressing the share). Expanding to N=5 symbols mechanically expands the denominator: the same TRX positive contribution shrinks to ≤ 40% top-share by arithmetic alone (TRX +19.08% OOS PnL out of new total ≈ +47% under proportional addition would be 41%, but more typically dilutes further because the new symbols add their own non-zero contributions). **Crucially**, the underlying entry signal for BCH, LDO, TRX is UNCHANGED (V3_FEATURE_COLUMNS unchanged; risk gates byte-identical); the new symbols add their own model fits which are independently learned by per-symbol LightGBM heads. This is structurally orthogonal to iter-v3/020's per-symbol-cap (which scaled positions DOWN — removing edge proportional to conviction).

**Why universe expansion may NOT lift OOS** (3 PATH-C-suspect scenarios):
1. **PATH C-1: New symbols underperform across the board.** HBAR or AVAX models can't fit on the 13-feature stack; their per-symbol Sharpe is materially negative (e.g., HBAR -0.50, AVAX -0.40); the dilution effect is dominated by drag, OOS Sharpe falls below anchor. EDA flags this as plausible — neither symbol has prior v3 model-fit evidence.
2. **PATH C-2: New symbols crowd in the same regimes as TRX/BCH/LDO.** Despite low marginal correlation in raw returns, the LightGBM model surfaces the same regime classifiers (e.g., BTC-trend-aligned momentum bursts) for HBAR/AVAX as for incumbents, leading to crowded losses in 2024-08 yen-carry crash, 2025 January correction, etc. Multi-asset crash regimes wipe out diversification.
3. **PATH C-3: Optuna at n_trials=35 splits the search budget across 5 per-symbol heads instead of 3, producing weaker fits per symbol.** With ENSEMBLE_SIZE=1 + --seeds 1, total fits = 5 symbols × 35 trials × 1 ensemble = 175 (vs iter-v3/018 anchor's 3 × 50 × 5 × 2 = 1500). The model-fit budget per symbol drops materially; even the incumbent BCH/LDO/TRX may regress at single-seed EXPLORATION.

The counterfactual evidence (Section 2.5) shows that under static incumbent-model trade rosters, mechanical 5-symbol denominator dilution would compress top-share to ≤ 40%; the empirical question this EXPLORATION answers is whether the NEW per-symbol heads (HBAR, AVAX) at n_trials=35 produce non-trivial trade volume + non-negative Sharpe contribution, AND whether the 7-gate risk stack retains them at the calibrated 30% gate-retention rate.

---

## Section 2 — IS-Only Numerical Evidence + Behavioral-Effect Predictor

**EDA script**: `analysis/iteration_v3-021/symbol_candidate_eda.py` (committed at SHA `a360251` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read** (IS-only window 2023-04-01 → 2025-03-24 plus pre-IS history):
- `data/{symbol}/8h.csv` for 10 candidate symbols and 3 incumbents
- `reports-v3/iteration_v3-018/in_sample/trades.csv` (cross-correlation reference for incumbent universe)

**Outputs** (committed alongside the script at SHA `a360251`):
- `analysis/iteration_v3-021/symbol_candidate_ranking.csv` — composite ranking with all sub-scores
- `analysis/iteration_v3-021/per_candidate_data_quality.csv` — Gate 1 details (24mo pre-IS, IS coverage, gap count)
- `analysis/iteration_v3-021/per_candidate_liquidity.csv` — Gate 2 details (avg/median/p10 daily qvol)
- `analysis/iteration_v3-021/per_candidate_correlations.csv` — full correlation matrix vs BCH/LDO/TRX
- `analysis/iteration_v3-021/per_candidate_volatility.csv` — NATR_21 + trade-rate proxy
- `analysis/iteration_v3-021/synthesis.md` — narrative + top-2 recommendation

### 2.1 Candidate ranking (composite scoring)

Composite score = 0.30 × complementarity (1 − mean_abs_corr_baseline) + 0.30 × data_quality (gate1 × 0.7 + IS_coverage × 0.3) + 0.25 × liquidity (log10(avg daily qvol) / log10(1e9)) + 0.15 × trade_rate_proxy.

| Rank | Symbol | Composite | Gate1 | Gate2 | IS cov% | Avg qvol $M | mean\|corr\| | NATR% | First kline |
|---:|---|---:|---|---|---:|---:|---:|---:|---|
| 1 | **HBARUSDT** | 0.756 | PASS | PASS | 100.0 | 126.4 | 0.410 | 4.27 | 2021-03-17 |
| 2 | **AVAXUSDT** | 0.740 | PASS | PASS | 100.0 | 334.6 | 0.498 | 4.17 | 2020-09-23 |
| 3 | ADAUSDT | 0.738 | PASS | PASS | 100.0 | 390.6 | 0.496 | 3.79 | 2020-01-31 |
| 4 | FILUSDT | 0.724 | PASS | PASS | 100.0 | 220.6 | 0.534 | 4.15 | 2020-10-16 |
| 5 | ALGOUSDT | 0.722 | PASS | PASS | 100.0 | 60.6 | 0.492 | 4.19 | 2020-06-16 |
| 6 | ATOMUSDT | 0.709 | PASS | PASS | 100.0 | 105.8 | 0.531 | 3.54 | 2020-02-07 |
| 7 | VETUSDT | 0.693 | PASS | PASS | 100.0 | 38.3 | 0.558 | 3.97 | 2020-02-14 |
| 8 | OPUSDT | 0.532 | **FAIL** | PASS | 100.0 | 222.5 | 0.500 | 4.74 | 2022-06-01 |
| 9 | ARBUSDT | 0.518 | **FAIL** | PASS | 100.0 | 290.9 | 0.540 | 4.32 | 2023-03-23 |
| 10 | POLUSDT | 0.417 | **FAIL** | PASS | 26.5 | 57.7 | 0.595 | 4.46 | 2024-09-13 |

OPUSDT, ARBUSDT, POLUSDT FAIL Gate 1 — insufficient pre-IS history for the TRAINING_MONTHS=24 walk-forward window. They are EXCLUDED from QR consideration regardless of liquidity profile.

### 2.2 HBARUSDT decision tile

| Property | Value | Threshold | Verdict |
|---|---:|---:|---|
| Composite score | 0.756 | rank-1 of 7 PASSING | TOP |
| mean \|corr\| vs BCH+LDO+TRX | 0.4096 | LOWEST in PASSING pool | TOP |
| max \|corr\| (with LDO) | 0.4749 | < 0.50 IC strict target | PASS |
| IS coverage | 100.0% | ≥ 99% | PASS |
| Pre-IS history | 24.48 months | ≥ 24mo | BARE PASS |
| Gap candles in IS | 0 | ≤ 5 | PASS |
| Avg daily qvol | $126.4M | > $20M | PASS |
| P10 daily qvol | $12.5M | > $5M | PASS |
| Min daily qvol | $5.95M | (informational) | (lowest in pool but above floor) |
| Weekend share | 20.6% | < 30% | PASS |
| NATR_21 IS | 4.27% | (regime indicator) | similar to TRX 3.0% / LDO 6.8% |
| Cap band | MID | (informational) | Hedera; layer-1 altcoin |
| Trade rate proxy | 2.88/month gate-retained | (informational) | (rough heuristic) |

### 2.3 AVAXUSDT decision tile

| Property | Value | Threshold | Verdict |
|---|---:|---:|---|
| Composite score | 0.740 | rank-2 of 7 PASSING | SECOND |
| mean \|corr\| vs BCH+LDO+TRX | 0.4978 | second-lowest in PASSING pool | TOP |
| max \|corr\| (with LDO) | 0.5819 | < 0.70 IC hard gate | PASS |
| IS coverage | 100.0% | ≥ 99% | PASS |
| Pre-IS history | 30.23 months | ≥ 24mo | PASS |
| Gap candles in IS | 0 | ≤ 5 | PASS |
| Avg daily qvol | $334.6M | > $20M | TOP (highest in PASSING pool) |
| P10 daily qvol | $92.9M | > $5M | TOP |
| Min daily qvol | $21.6M | (informational) | well above any candidate |
| Weekend share | 23.3% | < 30% | PASS |
| NATR_21 IS | 4.17% | (regime indicator) | similar to TRX/LDO scale |
| Cap band | LARGE | (informational) | Avalanche; layer-1 smart-contract platform |
| Trade rate proxy | 2.81/month gate-retained | (informational) | (rough heuristic) |

### 2.4 Cross-correlation surface vs BCH/LDO/TRX (incumbent universe)

| Symbol | corr_BCH | corr_LDO | corr_TRX | mean\|corr\| | max\|corr\| |
|---|---:|---:|---:|---:|---:|
| **HBARUSDT** (rank 1) | 0.4517 | 0.4749 | 0.3021 | **0.4096** | 0.4749 |
| **AVAXUSDT** (rank 2) | 0.5489 | 0.5819 | 0.3625 | **0.4978** | 0.5819 |
| ADAUSDT | 0.5523 | 0.5553 | 0.3804 | 0.4960 | 0.5553 |
| FILUSDT | 0.6038 | 0.5843 | 0.4123 | 0.5335 | 0.6038 |
| ALGOUSDT | 0.5558 | 0.5601 | 0.3601 | 0.4920 | 0.5601 |
| ATOMUSDT | 0.5801 | 0.6013 | 0.4100 | 0.5305 | 0.6013 |
| VETUSDT | 0.6035 | 0.5576 | 0.5141 | 0.5584 | 0.6035 |

All 7 PASSING candidates have max |corr| < 0.70 (the IC hard gate); HBAR + AVAX have max < 0.60 (well within IC strict target territory). HBAR's 0.4096 mean |corr| is uniquely lowest — strongest structural-complementarity signal.

### 2.5 Universe-expansion mechanical counterfactual: if iter-v3/018 had been 5-symbol

This is a CRUDE static counterfactual that does NOT model the new per-symbol heads' actual fits — those are the empirical question. The point is to verify the dilution arithmetic.

iter-v3/018 multi-seed mean PnL distribution (from BASELINE_V3.md per-symbol table):

| Symbol | OOS PnL | OOS Conc % (3-symbol) |
|---|---:|---:|
| BCHUSDT | +16.44% | 74.14% |
| LDOUSDT | -13.34% | -60.15% |
| TRXUSDT | +19.08% | 86.01% |
| **Total (3-sym)** | **+22.18%** | (numerator) |

Add 2 hypothetical NEW symbols at OOS PnL contribution ≈ 0% (lottery-symmetric — the most agnostic prior):

| Symbol | OOS PnL | OOS Conc % (5-symbol counterfactual at zero-contribution new symbols) |
|---|---:|---:|
| BCHUSDT | +16.44% | 74.14% (UNCHANGED — denominator unchanged at hypothetical zero-contribution) |
| LDOUSDT | -13.34% | -60.15% |
| TRXUSDT | +19.08% | 86.01% |
| HBARUSDT (hypothetical) | +0.00% | 0.00% |
| AVAXUSDT (hypothetical) | +0.00% | 0.00% |

The counterfactual is **mechanically null** at zero-contribution new symbols — the denominator dilution requires non-zero contributions from new symbols. With the EDA's calibrated trade-rate proxy (2.85/month gate-retained × 17 OOS months = ~48 trades per new symbol over OOS) and a lottery-symmetric ±0.20 PnL per symbol expectation:

| Symbol | OOS PnL (1σ low) | OOS PnL (median) | OOS PnL (1σ high) |
|---|---:|---:|---:|
| HBARUSDT | -10% | 0% | +10% |
| AVAXUSDT | -10% | 0% | +10% |

5-symbol total OOS PnL band: [+2.18%, +22.18%, +42.18%] with new top-share band:

| Scenario | New 5-sym OOS total | TRX share (numerator +19.08%) | Top-share (TRX) |
|---|---:|---:|---:|
| New symbols both -10% | +2.18% | +19.08% | **875%** (numerator/denominator artifact; near-zero denominator) |
| New symbols both 0% | +22.18% | +19.08% | **86%** (UNCHANGED — denominator unchanged) |
| New symbols both +10% | +42.18% | +19.08% | **45%** (closest to gate target) |

**Critical finding from counterfactual**: zero-contribution new symbols do NOT mechanically dilute concentration; non-trivial positive contributions are required. The counterfactual is therefore UNINFORMATIVE at the static incumbent-model level — the empirical question is whether the new per-symbol heads (HBAR, AVAX) at n_trials=35 produce **non-zero positive contribution** (or at worst small negative) such that the denominator expands. A genuine concentration-reduction outcome requires:

- Both new symbols' OOS PnL ≥ 0 (otherwise denominator shrinks AGAIN, inflating top-share)
- At least one new symbol's positive contribution materially exceeds zero (not lottery-zero)
- Combined risk-gate retention rate ≥ 30% (otherwise trade volume too low to register on portfolio metrics)

This is the **stronger** version of PATH C scenario: if new symbols underperform, universe expansion mechanically WORSENS concentration via numerator/denominator artifacts. This is the central risk of the iter-v3/021 axis.

### 2.6 Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md`)

Per the rule (added after iter-v3/012's NULL-RESULT trade-roster bit-identity surprise; extended at iter-v3/015/019/020 for NEW-axis discipline): brief Section 2 must include explicit estimate of how many IS trades will change in the roster. **Anchor**: iter-v3/018 IS trades = 172 (single-seed primary projection from `comparison.csv` — primary anchor for v3 EXPLORATIONs). Universe expansion is NOT directly comparable to anchor because the anchor universe is different — counterfactual:

**New-universe IS trade count counterfactual** (assumes incumbent BCH/LDO/TRX trade volumes UNCHANGED at their iter-v3/018 IS levels per per-symbol architecture; new HBAR/AVAX trade volumes per EDA proxy):

- iter-v3/018 IS BCHUSDT trades: 87 (multi-seed mean) ≈ ~85-95 single-seed band
- iter-v3/018 IS LDOUSDT trades: 10 (multi-seed mean) ≈ ~8-15 single-seed band
- iter-v3/018 IS TRXUSDT trades: 75 (multi-seed mean) ≈ ~70-90 single-seed band
- iter-v3/018 IS portfolio total: 172 (single-seed primary projection from comparison.csv)
- Predicted HBARUSDT IS trades (proxy 2.88/month × 24 IS months): 69 raw, ~21 gate-retained at 30% rate, OR ~50 at 70% retention upper bound
- Predicted AVAXUSDT IS trades (proxy 2.81/month × 24 IS months): 67 raw, ~20 gate-retained at 30% rate, OR ~47 at 70% retention upper bound

| Scenario | Anchor 172 (3-sym) | + HBAR | + AVAX | Total (5-sym) |
|---|---:|---:|---:|---:|
| Lower bound (10% gate retention; rare) | 172 | +7 | +7 | 186 |
| Median (30% gate retention; calibrated to iter-v3/018) | 172 | +21 | +20 | 213 |
| Upper bound (70% gate retention; permissive) | 172 | +50 | +47 | 269 |
| **Anchor counterfactual band ±25% (5-symbol scaling)** | **anchor scaled to (5/3) = 287** | — | — | **[215, 360]** if proportional |

**Saturation falsifier band** (per `feedback_axis_saturation_predictor.md` ±25% rule applied to anchor-scaled-by-symbol-count):

- 3-symbol anchor IS trades = 172
- 5-symbol proportional baseline = 172 × (5/3) ≈ 287
- ±25% band = [0.75 × 287, 1.25 × 287] = **[215, 360]**

But "proportional baseline" is the WRONG anchor for a per-symbol-architecture model — symbol-level Optuna fits don't produce proportional trade volumes. The correct framing is: **bundle-level 3-symbol anchor = 172**; per-symbol predictor (BCH unchanged + LDO unchanged + TRX unchanged + HBAR/AVAX added at proxy + gate retention) = expected band [186, 269]. **Use band [186, 269] as the primary saturation falsifier**; the proportional-scaling band [215, 360] is reported as a secondary informational baseline.

**Predicted IS trade count range: [186, 269]** with median 213.

**Falsifier reading**:
- IS trades < 186: incumbent universe trade volume regressed materially OR new symbols were almost completely killed by the 7-gate risk stack. EITHER scenario indicates the axis behavioral effect is below predicted lower bound — falsifier fires; verdict candidate `EXPLORATION-NEGATIVE-no-effect` (if axis didn't propagate at all) OR `EXPLORATION-NEGATIVE-failed-axis` (if Optuna re-tuning had outsized behavioral effect on incumbents).
- IS trades > 269: Optuna found expansive hyperparams that generated more trades than the gate-retention proxy predicts; either Optuna found over-fit hyperparams OR the gate retention rate calibration is wrong for new symbols. Both are behavioral surprises; flag for review.
- IS trades in [186, 269]: behavioral effect within predicted band — proceed to verdict on Sharpe direction + falsifiers 4-5.

**SECONDARY behavioral-effect verifier (per `feedback_promising_mechanical_subtype.md`)**: trade-roster bit-identity to iter-v3/018 on the 3 INCUMBENT symbols (entry/exit time + symbol + direction byte-equal for BCH/LDO/TRX trades). This is structurally IMPOSSIBLE because the per-symbol architecture means iter-v3/021's 5-symbol universe shares Optuna's `n_trials=35` budget across 5 heads not 3 — the incumbent heads will NOT be byte-identical fits. So this verifier becomes: "incumbent IS trade count for BCH/LDO/TRX combined ≈ iter-v3/018's 172 ± 30 (≈ ±18%)" — i.e., the new-symbol additions don't catastrophically perturb the incumbent fits. If incumbent total drops below 142 (172 - 30), Optuna split has materially weakened incumbent fits — flag for review.

### 2.7 Setup integrity (verified at SHA `a360251`)

```
analysis/iteration_v3-021/symbol_candidate_eda.py operative                       PASS
analysis/iteration_v3-021/symbol_candidate_ranking.csv produced (10 rows)         PASS
analysis/iteration_v3-021/per_candidate_data_quality.csv produced (10 rows)       PASS
analysis/iteration_v3-021/per_candidate_liquidity.csv produced (10 rows)          PASS
analysis/iteration_v3-021/per_candidate_correlations.csv produced (10 rows)       PASS
analysis/iteration_v3-021/per_candidate_volatility.csv produced (10 rows)         PASS
analysis/iteration_v3-021/synthesis.md produced                                   PASS
Top-2 candidates Gate 1 + Gate 2 BOTH PASS                                        PASS (HBAR + AVAX)
mean |corr| top-2 < 0.70 IC hard gate                                             PASS (0.41 / 0.50)
NEW symbols ∩ V3_EXCLUDED_SYMBOLS = ∅                                             PASS (HBAR / AVAX both eligible)
```

---

## Section 3 — Proposed Changes

### 3.1 Symbols — EXPAND 3 → 5 (BCH+LDO+TRX retained; HBAR+AVAX added)

| Symbol | iter-v3/020 status | iter-v3/021 status | Rationale |
|---|---|---|---|
| BCHUSDT | KEEP | UNCHANGED (KEEP) | iter-v3/013 baseline retention; positive OOS contributor multi-seed |
| LDOUSDT | KEEP | UNCHANGED (KEEP) | iter-v3/013 baseline retention; even though OOS-negative drag, drop-LDO would be sub-axis A of axis #5 — separate axis |
| TRXUSDT | KEEP | UNCHANGED (KEEP) | iter-v3/013 baseline retention; strongest OOS contributor in seed 42 (+11.97 weighted_pnl); concentration is REWARD source |
| **HBARUSDT** | (excluded) | **ADD** | EDA rank 1 / composite 0.756 / mean \|corr\| 0.41 LOWEST in pool / Gate 1+2 PASS |
| **AVAXUSDT** | (excluded) | **ADD** | EDA rank 2 / composite 0.740 / mean \|corr\| 0.50 / qvol $335M HIGHEST in pool / Gate 1+2 PASS |

| Symbol | V3_EXCLUDED_SYMBOLS check |
|---|---|
| BCHUSDT | not in excluded set ✓ |
| LDOUSDT | not in excluded set ✓ |
| TRXUSDT | not in excluded set ✓ |
| HBARUSDT | not in excluded set ✓ |
| AVAXUSDT | not in excluded set ✓ |

`set({BCH, LDO, TRX, HBAR, AVAX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓

### 3.2 Labeling — UNCHANGED (iter-v3/010 ATR 2.0/1.0)

| Parameter | iter-v3/020 (current) | iter-v3/021 |
|---|---:|---:|
| `atr_tp_multiplier` | 2.0 | UNCHANGED |
| `atr_sl_multiplier` | 1.0 | UNCHANGED |
| Timeout | 21 candles (7d) | UNCHANGED |
| `use_atr_labeling` | True | UNCHANGED |
| Purge gap | **66 (3-sym)** | **88 (5-sym; mechanical update)** |

The purge gap update is **mechanical** per the formula `REQUIRED_GAP = (timeout_candles + 1) × n_symbols = (21 + 1) × 5 = 110`. Wait — let me re-derive:

- 3-symbol baseline (iter-v3/013-020): `(21 + 1) × 3 = 66` (matches existing constant)
- 5-symbol expansion (iter-v3/021): `(21 + 1) × 5 = 110`

CORRECTION: the 5-symbol REQUIRED_GAP is **110, not 88**. The dispatch's "(was 66 (3 syms); becomes 88 (4 syms) or 110 (5 syms))" was correct only if the 4-sym choice were taken. Since QR chose 2-symbol expansion (5-sym total), REQUIRED_GAP = **110**.

| Parameter | iter-v3/020 | iter-v3/021 |
|---|---:|---:|
| n_symbols | 3 | 5 |
| timeout_candles | 21 | 21 |
| REQUIRED_GAP | 66 = (21+1)×3 | **110 = (21+1)×5** |

### 3.3 Features — UNCHANGED (13 V3_FEATURE_COLUMNS)

iter-v3/020 reverted V3_FEATURE_COLUMNS 14 → 13 (dropped funding_rate_zscore_30 per Critic FINAL Rec 2 of iter-v3/019). iter-v3/021 inherits the 13-feature set BYTE-IDENTICAL.

| Feature column | iter-v3/020 (V3_FEATURE_COLUMNS_TOP_N, 13 cols) | iter-v3/021 |
|---|---|---|
| max_dd_window_50 | KEEP | UNCHANGED |
| ema_spread_atr_20 | KEEP | UNCHANGED |
| ret_kurt_50 | KEEP | UNCHANGED |
| ret_skew_200 | KEEP | UNCHANGED |
| range_realized_vol_50 | KEEP | UNCHANGED |
| hurst_diff_100_50 | KEEP | UNCHANGED |
| ret_kurt_200 | KEEP | UNCHANGED |
| hurst_100 | KEEP | UNCHANGED |
| btc_ret_14d | KEEP | UNCHANGED |
| ret_skew_50 | KEEP | UNCHANGED |
| vwap_dev_20 | KEEP | UNCHANGED |
| ret_autocorr_lag1_50 | KEEP | UNCHANGED |
| sym_vs_btc_ret_7d | KEEP | UNCHANGED |

`len(V3_FEATURE_COLUMNS) == 13` after iter-v3/021. `_verify_feature_columns()` UNCHANGED — still asserts `len == 13` and `'funding_rate_zscore_30' NOT in V3_FEATURE_COLUMNS`. Cross-asset features (`btc_ret_14d`, `sym_vs_btc_ret_7d`) automatically apply to HBAR + AVAX via the existing per-symbol feature regeneration pipeline. **Clean attribution surface** — iter-v3/021's IS/OOS Sharpe deltas are attributable to the universe-expansion axis alone.

### 3.4 Risk gates — REVERT cap to DISABLED; existing 7-primitive stack UNCHANGED

| Parameter | iter-v3/020 (current) | iter-v3/021 |
|---|---:|---:|
| `RiskV2Config.zscore_threshold` | 2.0 | UNCHANGED (iter-v3/011) |
| `BTC_TREND_CONFIG.threshold_pct` | 15.0 | UNCHANGED (iter-v3/012) |
| `BTC_TREND_CONFIG.lookback_bars` | 42 (14d) | UNCHANGED |
| `BTC_TREND_CONFIG.enabled` | True | UNCHANGED |
| Vol scaling | enabled | UNCHANGED |
| `adx_threshold` | 20.0 | UNCHANGED (iter-v3/013 baseline) |
| `adx_period` | 14 (default) | UNCHANGED |
| `enable_adx_gate` | True (default) | UNCHANGED |
| Hurst regime check | (0.05, 0.95) | UNCHANGED |
| Low-vol filter | 0.33 | UNCHANGED |
| Hit-rate feedback | DISABLED | UNCHANGED |
| `max_per_symbol_pnl_share` | 0.40 (iter-v3/020) | **0.40 (still set; but enable_per_symbol_cap=False so no-op)** |
| `max_per_symbol_window_bars` | 90 | UNCHANGED |
| **`enable_per_symbol_cap`** | **True (iter-v3/020)** | **False (REVERT per iter-v3/020 PATH C closeout — diary `5287bd6` pre-commit)** |

The cap mechanism implementation in `RiskV2Wrapper.get_signal()` is RETAINED (zero revert cost; preserves option for fundamentally-different-mechanism future use); only the runner's `enable_per_symbol_cap` flag is set to False. iter-v3/021 effectively returns the risk stack to iter-v3/018's 7-primitive baseline (not the 8-primitive iter-v3/020 stack).

### 3.5 Sub-fix decomposition (7-item, mapped to dispatch's 7 first-commit pre-commits)

| # | Sub-fix | Spec | Verifier |
|---|---|---|---|
| 1 | **ADD HBARUSDT + AVAXUSDT to V3_MODELS** | Append two tuples to `V3_MODELS` in `run_baseline_v3.py`. Tuple labels follow existing convention: `("E (HBARUSDT)", "HBARUSDT")`, `("F (AVAXUSDT)", "AVAXUSDT")`. V3_MODELS goes from 3 → 5 entries. | `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==5; assert ('E (HBARUSDT)', 'HBARUSDT') in m.V3_MODELS; assert ('F (AVAXUSDT)', 'AVAXUSDT') in m.V3_MODELS"` exits 0 |
| 2 | **Update `REQUIRED_GAP` constant** to 110 (was 66 for 3-sym) | Edit `src/crypto_trade/strategies/ml/validation_v3.py` line 45: `REQUIRED_GAP: int = (21 + 1) * 5  # 110` (was `(21 + 1) * 3 # 66`). | `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP == 110"` exits 0 |
| 3 | **Update `_verify_label_leakage_gap()` assertion message** in `run_baseline_v3.py` | Update the print string to reflect 5-symbol universe: `f"Label-leakage gap: (timeout_candles=21+1) * n_symbols=5 = 110 [matches REQUIRED_GAP=110] PASS"`. The assertion logic itself is unchanged (computes from `len(V3_MODELS)` which is now 5). | `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); m._verify_label_leakage_gap()"` exits 0 (re-prints with n=5, gap=110) |
| 4 | **`_verify_feature_columns` UNCHANGED** | iter-v3/020's existing assertion `len(V3_FEATURE_COLUMNS) == 13` and forbidden-list `[tbr_zscore_30, funding_rate_zscore_30, vwap_dev_50]` is correct for iter-v3/021. No change needed. | `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); m._verify_feature_columns()"` exits 0 (still 13-col PASS) |
| 5 | **DISABLE per-symbol cap** in `_build_v3_model` `RiskV2Config` constructor | Edit `run_baseline_v3.py` line ~910: change `enable_per_symbol_cap=True` to `enable_per_symbol_cap=False`. Keep `max_per_symbol_pnl_share=0.40, max_per_symbol_window_bars=90` for documentation but they will be no-op when the flag is False. | `grep -E 'enable_per_symbol_cap=False' run_baseline_v3.py` exits 0 (and no `=True` for this flag) |
| 6 | **Update `ITERATION_LABEL`** from `"v3-020"` to `"v3-021"` | One-line change in `run_baseline_v3.py` line 102. | `grep -E 'ITERATION_LABEL.*=.*"v3-021"' run_baseline_v3.py` exits 0 |
| 7 | **Fetch klines + regenerate features parquets** for new symbols + all symbols | (a) `uv run crypto-trade fetch --symbols HBARUSDT,AVAXUSDT --intervals 8h` (incremental top-up; existing CSVs at 2026-02-28 cover IS+OOS but require freshness top-up to within 16h staleness guard). (b) `uv run crypto-trade features --symbols BCHUSDT,LDOUSDT,TRXUSDT,HBARUSDT,AVAXUSDT --interval 8h --track v3 --format parquet --workers 4` (regenerate v3 parquets for ALL 5 symbols — incumbent BCH/LDO/TRX must be regenerated to ensure feature-extent parity with new symbols). NOTE: the v3 features pipeline includes `cross_asset` group which depends on BTC kline data — verify `data/BTCUSDT/8h.csv` is fresh too (`uv run crypto-trade fetch --symbols BTCUSDT --intervals 8h`). | All 5 symbols have `data/features_v3/{SYM}/8h.parquet` with mtime > brief commit time AND `last_close_time` within 16h of clock time |
| 8 | **Run `--exploration --seeds 1`** on the 5-symbol universe with 13-feature set | Phase 6 invocation: `uv run python run_baseline_v3.py --exploration --seeds 1`. n_trials defaults to 35. Wall-clock target: < 60 min (5 symbols vs 3 = 1.67× scaling from iter-v3/020's 13 min ≈ 22 min, plus 35 trials × 5 symbols × 1 ensemble × 1 outer seed = 175 fits + CPCV with 110-gap ≈ slight overhead), 2h hard cap. | `test -f reports-v3/iteration_v3-021/comparison.csv` |

NO labeling change. NO feature change. NO z-score-gate change. NO BTC-band change. NO ADX change. NO Hurst change. NO low-vol-floor change. NO hit-rate change. NO model architecture change. NO ensemble change. NO outer-seed change. NO n-trials change. The single varied axis vs iter-v3/018 anchor is `+HBAR + +AVAX universe expansion + CAP DISABLED` (sub-fixes 1-5). Sub-fixes 6-8 are MANDATED first-commit pre-commits (label, fetch, regen).

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input) — 15 verifiers

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty cells = Phase 5.5 BLOCK.

| # | Sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | **V3_MODELS has 5 entries** | `run_baseline_v3.py` | `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==5"` exits 0 |
| 2 | **HBARUSDT in V3_MODELS** | `run_baseline_v3.py` | `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); syms = [s for _,s in m.V3_MODELS]; assert 'HBARUSDT' in syms"` exits 0 |
| 3 | **AVAXUSDT in V3_MODELS** | `run_baseline_v3.py` | `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); syms = [s for _,s in m.V3_MODELS]; assert 'AVAXUSDT' in syms"` exits 0 |
| 4 | **REQUIRED_GAP == 110** | `src/crypto_trade/strategies/ml/validation_v3.py` | `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP == 110"` exits 0 |
| 5 | **`_verify_label_leakage_gap()` runs without error and reports gap=110** | `run_baseline_v3.py` | `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); m._verify_label_leakage_gap()"` exits 0 |
| 6 | **`enable_per_symbol_cap=False`** in `_build_v3_model` | `run_baseline_v3.py` | `grep -E 'enable_per_symbol_cap=False' run_baseline_v3.py` exits 0 AND `grep -E 'enable_per_symbol_cap=True' run_baseline_v3.py` exits NON-ZERO (no remaining =True instances in v3 production path) |
| 7 | **V3_FEATURE_COLUMNS unchanged at 13** | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'funding_rate_zscore_30' not in V3_FEATURE_COLUMNS"` exits 0 |
| 8 | **`_verify_feature_columns` PASSES** (asserts len==13 + funding NOT present) | `run_baseline_v3.py` | `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); m._verify_feature_columns()"` exits 0 |
| 9 | **`atr_tp_multiplier=2.0` UNCHANGED (iter-v3/010)** | `run_baseline_v3.py` | `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 |
| 10 | **`atr_sl_multiplier=1.0` UNCHANGED (iter-v3/010)** | `run_baseline_v3.py` | `grep -E 'atr_sl_multiplier=1\.0' run_baseline_v3.py` exits 0 |
| 11 | **`zscore_threshold=2.0` UNCHANGED (iter-v3/011)** | `run_baseline_v3.py` | `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 |
| 12 | **`adx_threshold=20.0` UNCHANGED (iter-v3/013 baseline)** | `run_baseline_v3.py` | `grep -E 'adx_threshold=20\.0' run_baseline_v3.py` exits 0 |
| 13 | **`BTC_TREND_CONFIG.threshold_pct=15.0` UNCHANGED (iter-v3/012)** | `run_baseline_v3.py` | `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 |
| 14 | **`ITERATION_LABEL` updated to `"v3-021"`** | `run_baseline_v3.py` | `grep -E 'ITERATION_LABEL.*=.*"v3-021"' run_baseline_v3.py` exits 0 |
| 15 | **Behavioral-effect verifier (saturation falsifier)** + **per-symbol architecture incumbent fit-stability verifier**: (a) Total IS trades in band [186, 269] per per-symbol predictor (Section 2.6); (b) BCH+LDO+TRX combined IS trade count ≥ 142 (= anchor 172 - 30 incumbent-fit-stability tolerance), to ensure new-symbol additions don't catastrophically perturb incumbent fits; (c) HBAR + AVAX combined IS trade count ≥ 14 (= 7 + 7 lower-bound from 10% gate retention, ensuring new symbols emit non-trivial volume — secondary verifier for axis propagation). | `comparison.csv` + `per_symbol.csv` | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-021/comparison.csv'); n=int(df.loc[df['metric']=='n_trades','in_sample'].iloc[0]); assert 186 <= n <= 269, f'IS trades {n} OUTSIDE saturation band [186, 269]'"` exits 0 AND `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-021/in_sample/per_symbol.csv'); inc=df[df['symbol'].isin(['BCHUSDT','LDOUSDT','TRXUSDT'])]['n_trades'].sum(); assert inc >= 142, f'incumbent IS trades {inc} < 142 stability floor'"` exits 0 AND `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-021/in_sample/per_symbol.csv'); new=df[df['symbol'].isin(['HBARUSDT','AVAXUSDT'])]['n_trades'].sum(); assert new >= 14, f'new IS trades {new} < 14 axis-propagation floor'"` exits 0 |

### 3.7 NO labeling/feature/gate/risk-primitive changes

iter-v3/021 is a single-axis (NEW universe — denominator expansion) EXPLORATION. The labeling, features, model architecture, ATR labeling multipliers, z-score OOD threshold, BTC trend filter band, ADX threshold, low-vol floor, Hurst regime check, hit-rate feedback (disabled), CPCV parameters, and walk-forward window are unchanged from iter-v3/020 (which itself unchanged from iter-v3/018 except for the cap that is now disabled). The only differences vs iter-v3/018 anchor (the active comparison point per iter-v3/021 verdict logic) are:

- **NEW symbols**: HBARUSDT + AVAXUSDT in V3_MODELS (5-symbol universe vs 3-symbol)
- **REQUIRED_GAP**: 66 → 110 (mechanical update from formula `(timeout+1) × n_symbols`)
- **Cap DISABLED**: `enable_per_symbol_cap=False` (revert iter-v3/020's True; per `feedback_v3_concentration_is_signal.md` PATH C closeout)
- `ITERATION_LABEL` (cosmetic)
- Fresh feature parquets for new symbols + regen for all 5

### 3.8 Inheritance from iter-v3/020

The `iteration-v3/021` branch was branched from `iteration-v3/020` head. Inherited commits include all iter-v3/008-020 lineage. Critical inheritance verifiers (run BEFORE any code edits in Phase 6):

- BEFORE iter-v3/021 sub-fix #1 (V3_MODELS expand):
  - `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==3"` exits 0 (still iter-v3/020 state)
- BEFORE iter-v3/021 sub-fix #2 (REQUIRED_GAP):
  - `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP == 66"` exits 0 (still iter-v3/020 state)
- BEFORE iter-v3/021 sub-fix #5 (cap disable):
  - `grep -E 'enable_per_symbol_cap=True' run_baseline_v3.py` exits 0 (still iter-v3/020 state)
- AFTER iter-v3/021 sub-fixes #1-3: 5-symbol universe + 110-gap propagated
- AFTER iter-v3/021 sub-fix #5: cap disabled
- AFTER iter-v3/021 sub-fix #7: features regenerated for 5 symbols
- `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/010 value)
- `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/011 value)
- `grep -E 'adx_threshold=20\.0' run_baseline_v3.py` exits 0 (still iter-v3/013 baseline)
- `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 (still iter-v3/012 value)
- `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13"` exits 0 (still iter-v3/020 state — UNCHANGED for iter-v3/021)
- `uv run pytest tests/strategies/ml/ -v` exits 0 with all tests passing (no Engineer-added tests required for this axis; existing iter-v3/020 cap tests still PASS because the cap implementation is retained and just disabled at config layer)

---

## Section 4 — Expected OOS Impact

### 4.1 EXPLORATION → headline metrics are GUIDANCE not GATES

Per Section 0.5 + skill spec, headline metrics are NOT BLOCK-triggering for the Critic on EXPLORATION iterations. The Critic emits `EXPLORATION-PROMISING`, `EXPLORATION-NEGATIVE`, `EXPLORATION-PROMISING-MECHANICAL`, `EXPLORATION-PROMISING-INERT`, `EXPLORATION-NEGATIVE-no-effect`, or `BLOCK` (process). iter-v3/021 NEVER updates BASELINE_V3.md regardless of verdict.

### 4.2 Predicted IS / OOS Sharpe ranges

Anchor: iter-v3/018 BOOTSTRAP baseline IS Sharpe **+0.3788 (multi-seed mean)** / **+0.4563 (seed 42 single)**; OOS Sharpe **+0.3869 (multi-seed mean)** / **+0.2343 (seed 42 single)**. iter-v3/021 runs at `--seeds 1 --n-trials 35` (EXPLORATION mode), so the closest-comparable single-seed metric is iter-v3/018 seed 42 = +0.4563 IS / +0.2343 OOS. Per the dispatch's anchor-comparison framing, the multi-seed mean is the primary anchor for verdict logic.

| Metric | iter-v3/018 anchor (multi-seed) | iter-v3/018 anchor (seed-42) | iter-v3/021 prediction (5-symbol, 13-feature, no cap) |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.3788 | +0.4563 | **predicted [+0.30, +0.55] median +0.40** = Δ vs multi-seed [-0.08, +0.17]; Δ vs seed-42 [-0.16, +0.09] |
| OOS monthly Sharpe | +0.3869 | +0.2343 | **predicted [+0.45, +0.70] median +0.55** = Δ vs multi-seed [+0.06, +0.31]; Δ vs seed-42 [+0.22, +0.47] |
| Top-symbol concentration IS | 87.36% (BCH multi-seed) / 78.72% (BCH seed-42) | — | **predicted < 60%** (mechanical denominator dilution; not enforced) |
| Top-symbol concentration OOS | 86.01% (TRX multi-seed) / 152.01% (TRX seed-42) | — | **predicted < 60%** (mechanical; depends on new-symbol contribution sign) |
| IS trades | 172 (cumulative) | 172 (seed 42) | **predicted [186, 269]** (per-symbol predictor band) |
| OOS trades | 90.5 (mean) / 102 (seed 42) | 102 (seed 42) | **predicted ~135-170** (anchor 102 + 2 × ~24 OOS trades per new symbol; informational at EXPLORATION) |
| Per-symbol incumbent IS trades | BCH+LDO+TRX = 172 | — | **predicted ≥ 142** (incumbent stability floor) |
| Per-symbol new IS trades | (n/a) | — | **predicted ≥ 14** (new-symbol axis-propagation floor) |
| Phase 6 wall-clock | 4.54h (CONFIRMATION) | — | predicted 25-50 min (5 symbols vs 3 = 1.67× scaling from iter-v3/020's 13 min ≈ 22 min, plus 35 trials × 5 symbols × 1 ensemble × 1 outer seed = 175 fits; CPCV gap=110 vs 66 adds ~5% overhead; feature regen for 5 symbols ~5 min) |

The IS prediction band [+0.30, +0.55] reflects the **mid-prediction** (anchor multi-seed +0.3788 ± Optuna-fit-quality variance from 2 NEW symbols' learnable signal):
- Lower bound +0.30: new symbols' models fit poorly at single-seed n_trials=35; HBAR/AVAX add IS drag of ~-0.08 from the anchor. Counterfactual evidence (Section 2.5) shows zero-contribution new symbols don't dilute concentration; negative-contribution new symbols WORSEN top-share — but at IS where Optuna overfits, both models likely surface SOME positive contribution.
- Upper bound +0.55: best-case where Optuna at n_trials=35 fits HBAR + AVAX heads with non-trivial positive IS contribution; the 5-symbol portfolio benefits from genuine diversification + lower top-share + uncorrelated edge from HBAR's 0.41 mean-|corr| surface.
- Median +0.40: balanced expectation; new-symbol fits add small positive contribution (~+0.02 each); the overall Sharpe stays in the multi-seed anchor's vicinity.

The OOS prediction band [+0.45, +0.70] reflects the **upper-bound aspiration** (Optuna-fit new-symbol heads generalize OOS + concentration discipline materially reduces single-symbol lottery risk):
- Lower bound +0.45: anchor multi-seed +0.3869 + Optuna-discovered diversification gain +0.06 from non-zero new-symbol contributions. Lower-bound is HIGHER than IS lower-bound because the OOS anchor for 3-symbol is dominated by TRX-vs-LDO lottery (single-seed 102 trades / multi-seed 90.5); 5-symbol OOS reduces this lottery risk via denominator expansion alone.
- Upper bound +0.70: anchor + new symbols exhibit OOS-positive contribution that the model didn't pick up at IS. HBAR's low correlation profile (0.41 mean |corr|) is the primary mechanism — the model surfaces uncorrelated edge that doesn't decay OOS. Substantial OOS lift.
- Median +0.55: balanced expectation; new symbols moderately improve OOS by reducing single-symbol concentration AND adding diversifying edge.

**The PATH C scenarios** (Section 1):
- PATH C-1 (HBAR/AVAX both negative OOS): OOS Sharpe < +0.30 (anchor -0.08); concentration WORSENS via numerator/denominator artifact.
- PATH C-2 (crowded crash regimes): OOS Sharpe ≈ anchor; the dilution effect is offset by correlated new-symbol drag in 2024-08 / 2025-01 crashes.
- PATH C-3 (Optuna budget split weakens incumbents): incumbent BCH/LDO/TRX OOS contributions degrade by 10-20% from baseline; new-symbol additions don't compensate. OOS Sharpe < anchor.

The user-mandated bands reflect upper-bound diversification-success outcomes; the QR's primary belief is OUTCOME band [+0.30, +0.55] for IS / [+0.30, +0.55] for OOS (NOT [+0.45, +0.70] as upper-bound aspirational — actual median expectation is closer to anchor). The dispatch's predicted band of [+0.45, +0.70] for OOS is reproduced as the brief's primary band per dispatch instructions, with the QR's annotation that PATH C scenarios are at >30% combined probability.

### 4.3 Falsifiers (locked before backtest)

**Falsifier 1**: IS Sharpe < iter-v3/018 multi-seed anchor (+0.3788) AND OOS Sharpe < anchor +0.2869 (anchor -0.10) → universe expansion is NEGATIVE on both axes. PATH C verdict: EXPLORATION-NEGATIVE (clean) — universe expansion subtracts net edge OR new symbols drag the portfolio; iter-v3/022+ would explore a different concentration mechanism (per-symbol drawdown brake, vol-target ceiling, regime-conditional kill switch — per `feedback_v3_concentration_is_signal.md` permitted alternatives).

**Falsifier 2 (saturation predictor per `feedback_axis_saturation_predictor.md`)**: IS trade count outside [186, 269] (per-symbol predictor band) → axis behavioral effect deviates from prediction. If trades < 186: incumbent fits regressed materially OR new symbols heavily killed by 7-gate stack (≥30% retention proxy missed). If trades > 269: Optuna over-fit OR gate-retention proxy under-calibrated. Verdict path: BLOCK if implementation defect; otherwise EXPLORATION-NEGATIVE-no-effect or NEGATIVE-failed-axis.

**Falsifier 3** (process): Phase 6 wall-clock > 60 min on 5-symbol universe with 13-feature set → unexpected slowdown in feature regen pipeline OR Optuna multi-symbol fit ballooning. Engineer documents the cause. Cap remains 2h hard.

**Falsifier 4 (NEW for NEW-universe-axis discipline)**: incumbent IS trade count for BCH+LDO+TRX combined < 142 (anchor 172 - 30 stability tolerance) → Optuna budget split materially weakened incumbent fits. Verdict: EXPLORATION-NEGATIVE-no-effect (axis didn't isolate cleanly; the 5-symbol expansion perturbed the 3-symbol fits too aggressively). **Mitigation**: this is structurally hard to control at single-seed n_trials=35; if Falsifier 4 fires the catalog row flags "Optuna budget under-provisioned for 5-symbol universe at EXPLORATION mode"; iter-v3/022 may need n_trials raised OR ENSEMBLE_SIZE raised for new-symbol axes.

**Falsifier 5 (NEW — new-symbol axis-propagation gate)**: HBAR + AVAX combined IS trade count < 14 → new symbols were almost completely killed by the 7-gate risk stack (gate retention < 10% combined). Universe-expansion axis didn't propagate. Verdict: EXPLORATION-NEGATIVE-no-effect — analogous to iter-v3/015's INERT pattern adapted to a universe axis; the new symbols emitted near-zero trade volume; the axis is technically applied but mechanically null.

**Falsifier 6 (NEW — new-symbol drag gate)**: HBAR or AVAX individual OOS PnL < -10% (i.e., either new symbol contributes net OOS drag exceeding 10% of total NAV) → new symbol(s) drag the portfolio. PATH C-1 confirmed. Verdict candidate: EXPLORATION-NEGATIVE-clean if portfolio OOS Sharpe Δ < -0.10 (PATH C); else PROMISING-INERT if portfolio OOS Sharpe within ±0.10 anchor (drag offset by other contributions).

**Process falsifier**: pre-flight `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==5"` exits non-zero, OR `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP == 110"` exits non-zero, OR feature parquet for HBAR/AVAX missing/stale → setup drift; Phase 6 must not start.

### 4.4 EXPLORATION outcome interpretation (pre-commit catalog framing)

Per `feedback_promising_mechanical_subtype.md` + `feedback_axis_saturation_predictor.md` + iter-v3/015-020 precedent. §4.4 row 5 NEGATIVE-clean condition follows iter-v3/017's update: "either |Δ trades| ≥ 11 OR per-symbol shift > 5".

| Critic verdict | Conditions | Catalog row | Next iteration |
|---|---|---|---|
| `EXPLORATION-PROMISING` (PATH A) | OOS Sharpe Δ ≥ +0.10 vs iter-v3/018 multi-seed anchor (i.e., OOS ≥ +0.4869) AND top-share OOS < 60% (mechanical concentration reduction) AND IS trades in [186, 269] (Falsifier 2 PASS) AND incumbent IS ≥ 142 (Falsifier 4 PASS) AND new-symbol IS ≥ 14 (Falsifier 5 PASS) AND no new-symbol drag > -10% PnL (Falsifier 6 PASS) AND OOS bundle trades ≥ 130 (BUNDLE-LEVEL trade-rate floor) | "Universe expansion to 5 symbols reduced concentration AND added diversification edge; first orthogonal-mechanism PROMISING result post-iter-v3/020 cap closure" | iter-v3/022 EXPLORATION on a DIFFERENT axis category (MEDIUM-priority #3 DSR gate reformulation OR #4 TRX/2022-Q4 regime gate) — single-axis discipline preserved; universe expansion is a CONFIRMATION-bundle candidate |
| `EXPLORATION-PROMISING-INERT` | OOS Sharpe within ±0.10 of iter-v3/018 multi-seed anchor (i.e., in [+0.2869, +0.4869]) AND IS trades in [186, 269] AND incumbent ≥ 142 AND new-symbol ≥ 14 | "Universe expansion propagated but lift attribution ambiguous; mechanical concentration dilution alone doesn't yield Sharpe lift; new symbols' contribution is roughly net-zero" | iter-v3/022 on a DIFFERENT axis; possibly per-symbol drawdown brake (next concentration-mechanism alternative per `feedback_v3_concentration_is_signal.md`) |
| `EXPLORATION-PROMISING-MECHANICAL` | OOS Sharpe up ≥ +0.10 BUT new-symbol contribution to OOS PnL ≈ 0 (within ±2% NAV; mechanical denominator dilution alone explains the Sharpe lift) | "Universe expansion added denominator without adding edge — mechanical concentration metric improvement; non-compoundable across iterations per `feedback_promising_mechanical_subtype.md`" | similar to iter-v3/013 framing — accountancy lift but not signal lift; flag NON-COMPOUNDABLE |
| `EXPLORATION-NEGATIVE-no-effect` (NULL-RESULT) | (a) Falsifier 4 fires (incumbent IS < 142 — 5-symbol Optuna budget split weakened incumbents) OR (b) Falsifier 5 fires (new-symbol IS < 14 — new symbols killed by gates) | "Universe expansion didn't propagate cleanly OR Optuna budget under-provisioned at single-seed n_trials=35" | iter-v3/022 = re-attempt at MORE n_trials (50+) or ENSEMBLE_SIZE=2 to provide budget margin; this is STILL HIGH-priority #2b axis until cleanly tested |
| `EXPLORATION-NEGATIVE` (clean) (PATH C) | (IS Sharpe Δ < -0.10 vs iter-v3/018 multi-seed anchor AND/OR OOS Sharpe < anchor -0.10 AND concentration didn't reduce mechanically AND non-bit-identical roster: \|Δ trades\| ≥ 11 OR per-symbol shift > 5) AND incumbent ≥ 142 AND new-symbol ≥ 14 (i.e., axis propagated cleanly but produced negative outcome) | "Universe expansion to 5 symbols subtracts net edge; new symbols drag OR Optuna budget split degraded incumbents OR concentration carries genuine signal that dilution removes" | iter-v3/022 on a DIFFERENT axis category — NOT another universe-expansion variant; per-symbol drawdown brake or vol-target ceiling per `feedback_v3_concentration_is_signal.md` permitted alternatives |
| `BLOCK` (process) | Methodology check FAILED, OR Falsifier 2 (saturation, IS trades outside [186, 269]) AND axis didn't propagate, OR Falsifier 3 (wall-clock > 2h) triggered, OR Falsifier 6 fires WITH portfolio Sharpe within band (process anomaly — drag without reflected portfolio impact) | (none) | Diary documents, iter-v3/022 fixes the methodology gap |

---

## Section 5 — Risk Mitigation

### 5.1 Cadence-discipline structural safeguards (4 inherited + 4 methodology-specific + 3 axis-specific = 11 total)

iter-v3/021 inherits the cadence-discipline safeguards from skill SHA `d5c9f21` + the saturation-predictor rule + the structural-axis preference rule + `feedback_v3_iter019_axis_priorities.md` LOCKED + `feedback_v3_concentration_is_signal.md` LOCKED:

1. **2h wall-clock hard cap**: Engineer kills Phase 6 if elapsed > 2h. Wall-clock target < 60 min for 5-symbol + 13-feature `--exploration` mode (~22 min Optuna + ~5 min feature regen + buffer).
2. **Single-axis variation rule** honored (only `+HBAR + +AVAX universe expansion` added; ATR/zscore-OOD/BTC-band/Hurst/low-vol/hit-rate/CPCV byte-for-byte identical to iter-v3/018; no gate threshold tuning; no labeling change; no model architecture change; no new feature). The cap-disable (sub-fix #5) is a MANDATED post-iter-v3/020 closeout pre-commit per `feedback_v3_concentration_is_signal.md` LOCKED, NOT a separate axis — it returns the risk stack to the iter-v3/018 anchor surface for clean attribution. The REQUIRED_GAP update (sub-fix #2) is mechanical from `n_symbols=5` and not a separate axis.
3. **EXPLORATION never updates BASELINE_V3.md** — outcome (PROMISING / PROMISING-INERT / PROMISING-MECHANICAL / NEGATIVE / NEGATIVE-no-effect / BLOCK) records only in `briefs-v3/exploration_catalog.md` and `diary-v3/iteration_v3-021.md`.
4. **Saturation predictor falsifier** (Section 3.6 row 15 + Section 4.3 Falsifier 2, threshold derived from per-symbol predictor band [186, 269] anchored at iter-v3/018 IS trades 172 + 2×proxy increments) actively verifies axis behavioral effect.

### 5.2 Methodology-pipeline safety (inherited from iter-v3/006-020) — 4 safeguards

5. **Adversarial unit tests** — none required for this axis (no new code paths beyond V3_MODELS expansion). Existing iter-v3/020 cap unit tests still PASS because the cap implementation is retained and just disabled at config layer.
6. **File-artifact reconciliation table** (§3.6). 15 verifier commands; empty cells = Phase 5.5 BLOCK.
7. **Pre-flight grep-checks**: V3_MODELS has 5 entries, REQUIRED_GAP = 110, `enable_per_symbol_cap=False`, ITERATION_LABEL=v3-021, V3_FEATURE_COLUMNS unchanged at 13. Catches the case where setup edits were silently lost.
8. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.

### 5.3 NEW-universe-axis-specific risks (3 explicit)

9. **New-symbol underperformance / drag**: HBAR or AVAX models fit poorly at single-seed n_trials=35; their per-symbol Sharpe materially negative (e.g., HBAR -0.50, AVAX -0.40); the dilution effect is dominated by drag, OOS Sharpe falls below anchor (PATH C-1). **Mitigation**: Falsifier 6 explicitly pre-registers per-symbol OOS PnL > -10% threshold; if either new symbol fires the falsifier, the catalog row flags the specific drag symbol and iter-v3/022 may pivot to HBAR-only (de-add AVAX) under new single-axis discipline.
10. **REQUIRED_GAP propagation correctness**: the gap formula `(timeout_candles+1) × n_symbols` must propagate correctly to the CPCV embargo computation. If REQUIRED_GAP = 110 is set but CPCV uses old gap=66 silently, label leakage across train/test boundaries possible. **Mitigation**: sub-fix #2 verifier exits 0 only if `REQUIRED_GAP == 110`; sub-fix #5 verifier (`_verify_label_leakage_gap()`) re-derives the formula from `len(V3_MODELS)` and asserts equality with the constant. Three independent checks: dataclass field, runtime assertion, code-path constant.
11. **Feature parquet regeneration for new symbols + cross-asset feature consistency**: HBAR + AVAX need fresh `data/features_v3/{SYM}/8h.parquet` files. The cross-asset feature group computes `btc_ret_14d` and `sym_vs_btc_ret_7d` which depend on BTCUSDT klines — if BTC klines are stale (>16h), cross-asset features for ALL 5 symbols are corrupted. **Mitigation**: sub-fix #7 explicitly fetches BTCUSDT klines first; data freshness verifier in `_verify_data_freshness()` checks all 5 + BTC. iter-v3/021 sets up + verifies BTC fetch as a pre-flight step.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — REVERTED (cap disabled; v3 returns to iter-v3/018 anchor's 7-primitive stack)

| # | Primitive | Spec | Fire-rate prediction (IS, 5-symbol, 13-feature) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | ADX gate | trade only when ADX ≥ 20 (iter-v3/013 baseline) | ≈ 60% of bars pass per symbol | Trend filter |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass per symbol | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.0 (over 13 features) | ≈ 25–35% killed per symbol | Distributional drift; new symbols may show higher kill rate during cold-start (first ~50 bars) |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass per symbol | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±15% | ≈ 12–13% killed per symbol | Macro flips |
| ~~8~~ | ~~Per-symbol PnL cap (DISABLED iter-v3/021)~~ | ~~scale by `cap / share` if share > 0.40~~ | ~~0% (flag False; implementation retained)~~ | ~~CLOSED-mechanism per `feedback_v3_concentration_is_signal.md`~~ |

Combined kill rate target: **80–90%** per symbol (matches iter-v3/018's range; primitive 8 disabled means iter-v3/021 is identical in risk-stack composition to iter-v3/018).

**Important sub-point**: the universe-expansion axis at iter-v3/021 does NOT modify the risk stack — it ADDS new symbols subject to the SAME 7-primitive stack. The new symbols' gate-retention rates may differ from incumbents (especially primitive 4 z-score OOD during cold-start), which is why the EDA's calibrated trade-rate proxy uses 30% retention (lower than incumbents' empirical ≈ 35-40%). This conservatism flows into Section 2.6's predictor band [186, 269].

**Gate orthogonality**: identical to iter-v3/018. The order of operations in `get_signal` is: signal direction (from inner strategy) → primitive 4 (z-score OOD) → primitive 3 (Hurst) → primitive 2 (ADX) → primitive 5 (low-vol) → primitive 1 (vol scaling, multiplicative) → primitive 7 (BTC trend, post-aggregation) → primitive 6 (hit-rate, disabled).

### 6.2 Regime coverage — MOSTLY UNCHANGED

5-symbol IS data spans 2023-03-24 → 2025-03-23 — same as iter-v3/018. Regime coverage includes 2023 banking crisis, 2024 halving + Trump rally, 2024-08 yen-carry crash, 2025 January correction. New symbols' regime coverage:
- HBARUSDT: pre-IS 24.48 months (2021-03-17 → 2023-03-24) — covers 2021 bull mania, 2022 LUNA/FTX crashes (NOT in IS but in pre-train history per training_months=24 walk-forward)
- AVAXUSDT: pre-IS 30.23 months (2020-09-23 → 2023-03-24) — covers 2020 DeFi summer, 2021 bull, 2022 crashes

Both new symbols' pre-train coverage is sufficient for the walk-forward windows. The only specific concern: HBARUSDT's pre-IS is exactly 24.48mo — if the runner's first walk-forward window starts before 2023-03-24, HBAR cold-start training data may be only 24 months × 90 candles/month = 2160 candles vs incumbents' 2700+ candles. This is BARE PASS for Gate 1 but should be flagged in the engineering report.

### 6.3 Concentration enforcement — denominator expansion mechanism, EXPLORATION-mode informational

iter-v3/018 multi-seed showed TRX 66.08% / 55.83% concentration (gate 7 floor 30% missed); BCH 87.36% IS. iter-v3/021's universe expansion mechanically reduces top-share via denominator expansion — UNLIKE iter-v3/020's per-symbol cap which scaled positions DOWN. The concentration metric (post-expansion top-share) is informational at EXPLORATION:
- If new symbols contribute non-trivially: concentration mechanically dilutes (Section 2.5 counterfactual showed 5-symbol top-share at 45-86% depending on new-symbol contribution sign).
- If new symbols contribute zero: concentration UNCHANGED (denominator unchanged at zero new contributions).
- If new symbols contribute negatively: concentration potentially WORSENS via numerator/denominator artifact (PATH C-1).

The verdict cell is driven by IS Sharpe direction + Falsifiers 4-6 (incumbent stability, new-symbol propagation, new-symbol drag). The concentration metric itself is verified informationally at the catalog row level — it's the AXIS MECHANISM's mechanical metric, not the verdict driver.

---

## Section 7 — Pre-Registered Failure-Mode Prediction (6 predictions calibrated against 12 prior EXPLORATIONs + iter-v3/018 multi-seed evidence + iter-v3/021 EDA evidence)

**Prediction P1 (process, P=10%)**: V3_MODELS expansion silently broken — V3_MODELS has 5 entries but the runner's symbol-subset filter, walk-forward orchestration, or per-symbol report aggregation breaks on 5-symbol input. **Detection signal**: Falsifier 5 (new-symbol IS trades < 14) OR Phase 6 crashes mid-execution. **Mitigation**: §3.6 rows 1-3 verifiers + adversarial smoke check (`uv run python run_baseline_v3.py --exploration --seeds 1 --symbols HBARUSDT --max-walks 1 --debug` — single-symbol single-walk smoke before full run).

**Prediction P2 (process, P=10%)**: REQUIRED_GAP propagation broken — constant set to 110 in validation_v3.py but CPCV embargo silently uses 66 from cached state. **Detection signal**: `_verify_label_leakage_gap()` exits 0 BUT actual CPCV report shows gap=66 in metadata. **Mitigation**: pre-flight verifier blocks Phase 6 launch; engineering report cross-checks CPCV `gap` field in `dsr.json` metadata.

**Prediction P3 (process, P=15%)**: Feature parquet regeneration produces stale or column-misaligned outputs for new symbols. HBAR/AVAX `data/features_v3/{SYM}/8h.parquet` exists but has wrong column count, missing cross-asset features, or stale BTC dependencies. **Detection signal**: backtest fails at `LightGbmStrategy._train_for_month()` with column mismatch error. **Mitigation**: sub-fix #7 explicitly fetches BTCUSDT first; `_verify_data_freshness()` checks all symbols + BTC.

**Prediction P4 (model, P=25%)**: OOS Sharpe lifts to [+0.50, +0.70] (PATH A); universe expansion mechanically reduces single-symbol concentration AND new symbols contribute non-trivial uncorrelated edge. Optuna at n_trials=35 fits HBAR + AVAX heads with positive Sharpe contribution. PROMISING (full PATH A). The EDA's HBAR mean |corr| 0.41 is the mechanism — uncorrelated edge generalizes OOS.

**Prediction P5 (model, P=30%)**: OOS Sharpe stays in iter-v3/018 multi-seed anchor range [+0.2869, +0.4869]; new symbols contribute roughly net-zero (Optuna at single-seed n_trials=35 doesn't fit them well; their OOS PnL is approximately ±10% of anchor). Concentration dilutes mechanically but no edge added. PROMISING-INERT.

**Prediction P6 (model, P=25%)**: OOS Sharpe drops below iter-v3/018 multi-seed anchor (-0.10 → < +0.2869); PATH C-1 (new symbols drag), PATH C-2 (correlated crashes), or PATH C-3 (Optuna budget split weakens incumbents). The 35-trial Optuna budget over 5 symbols is materially less per-symbol than the 50-trial × 3-symbol iter-v3/018 anchor (~7 trials/symbol vs ~17/symbol). NEGATIVE-clean.

**Prediction P7 (model, P=10%)**: OOS Sharpe spikes to > +0.70; both new symbols contribute exceptionally well; HBAR's 0.41 mean-|corr| diversification is verified empirically; LDO drag is offset by HBAR/AVAX contributions; first PROMISING-strong result post-bootstrap. Catalog row flagged as a strong CONFIRMATION-bundle candidate.

**Prediction P8 (process, P=5%)**: Falsifier 4 fires (incumbent IS < 142). Optuna budget split weakened incumbent fits unrecoverably. Verdict: NEGATIVE-no-effect; iter-v3/022 retries at higher n_trials or ENSEMBLE_SIZE=2 to provide budget margin.

P4 + P5 + P6 + P7 + P8 sum to 95% (model-axis outcomes); the remaining 5% is residual PATH C-1/C-2/C-3 attribution overlap with PROMISING-INERT (model band uncertainty). Process predictions P1-P3 sum to 35% (failure-mode hedging, comparable to iter-v3/019/020's 35% reflecting NEW-axis-category complexity — universe expansion is structurally novel for v3).

**Calibration vs prior EXPLORATIONs**:
- The NEW-universe axis category has ZERO prior calibration data points in v3 — iter-v3/021 is the first universe-expansion EXPLORATION (iter-v3/013 was universe REDUCTION, drop-MKR; not symmetric). Predictions are calibrated against:
  - iter-v3/013 (drop-MKR, single-axis universe change): single-seed +1.0088 IS / +2.6970 OOS overshoot, formally falsified at iter-v3/018 multi-seed (62% IS / 86% OOS reduction). Universe-axis lottery suspect remains live.
  - iter-v3/019 (NEW external-data-source feature): PROMISING-INERT — n_trials=35 didn't surface new-feature-family signal at single-seed. The same risk applies to NEW-symbol-family Optuna fits.
  - iter-v3/020 (NEW risk primitive): NEGATIVE-clean (PATH C). Concentration mechanism orthogonal-mechanism prescription is the LOCKED next attempt — iter-v3/021 IS that attempt.
- EDA evidence (HBAR 0.41 mean |corr|, AVAX $335M qvol) supports P4 (PROMISING) at ≥25%; the EDA's diversification surface is genuinely strong.
- Counterfactual evidence (Section 2.5) supports P5 (PROMISING-INERT) at ≥30%: zero-contribution new symbols don't dilute concentration; the EXPLORATION needs non-trivial positive contribution to clear PATH A.
- The user-mandated bands (IS [+0.30, +0.55], OOS [+0.45, +0.70]) reflect upper-bound diversification-success outcomes; the QR's primary belief is OUTCOME band [+0.30, +0.55] for both IS and OOS, with PATH A as moderate-probability upside (P4 = 25%) and PATH C scenarios as combined moderate-probability downside (P6 + P8 = 30%).

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Criteria — 11 EXPLORATION criteria

EXPLORATION never updates BASELINE_V3.md, so traditional MERGE thresholds do not apply. The 11 criteria below pre-register the catalog-row decision and provide unambiguous Critic verdict triggers.

1. **OOS Sharpe ≥ iter-v3/018 multi-seed anchor + 0.10 (i.e., ≥ +0.4869)**: catalog row records PROMISING verdict (PATH A).
2. **OOS Sharpe < iter-v3/018 multi-seed anchor − 0.10 (i.e., < +0.2869)**: Falsifier 1 fires — EXPLORATION-NEGATIVE if non-bit-identical roster (PATH C), or NEGATIVE-no-effect if axis didn't propagate (Falsifier 4 or 5 fires).
3. **OOS Sharpe in [+0.2869, +0.4869] (= anchor ± 0.10)**: PROMISING-INERT (inert verdict) — catalog row records INERT.
4. **n_trades ≥ 50 IS, ≥ 50 OOS bundle-level**: BUNDLE-LEVEL trade-rate floor per `feedback_trade_rate_floor_bundle_level` (informational at EXPLORATION; predicted IS in [186, 269] — well above 50; OOS predicted ~135-170 — comfortably ≥50; single-seed EXPLORATION).
5. **PBO < 0.40 (per-cell mean)** AND `n_high_pbo_cells_99 ≤ 4`: methodology hygiene; both inherited expected-similar from iter-v3/018 multi-seed (mean 0.0892; max 1.0 on TRX/2022-Q4 carry-forward — outstanding constraint flagged in BASELINE_V3.md but NOT iter-v3/021's axis to fix). iter-v3/021 expected near-identical PBO unless 5-symbol expansion has unexpected cell-level effect; new symbols may add new high-PBO cells (e.g., HBAR/2022-LUNA-crash if pre-IS data is in the regime — though IS starts 2023-03-24 so this is not a concern).
6. **IC max abs < 0.70**: per Critic Check 4 — NO new feature added; existing 13-feature IC matrix unchanged from iter-v3/018; new symbols' feature distributions may have IC drift but inter-feature correlations are computed per-symbol. PASS by inheritance for incumbents; new-symbol IC matrix should be reported in engineering report for completeness.
7. **ADF p < 0.05 on 13 V3_FEATURE_COLUMNS for ALL 5 symbols** (or stationarity rationale): the 13 features unchanged; ADF for incumbents inherits PASS from iter-v3/018; new-symbol ADF must be re-run and reported. Expected PASS (features are scale-invariant: returns, z-scores, regime indicators).
8. **Reproducibility verifier**: SHAs stamped in engineering report (analysis `a360251`, runner setup commit, brief commit, Phase 5.5 gate, engineering report).
9. **Pareto dominance**: vacuous under single-seed EXPLORATION (Section 8 criterion 9 waiver inherited from iter-v3/006-020).
10. **Symbol exclusion + feature isolation + track isolation**: `set({BCH, LDO, TRX, HBAR, AVAX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓; no new imports from features modules; the universe expansion uses only existing schema (V3_MODELS tuple). Zero cross-track contamination.
11. **Behavioral-effect verifier (saturation falsifier per `feedback_axis_saturation_predictor.md` ±25% rule applied to per-symbol predictor band)**: IS trades in **[186, 269]** AND incumbent BCH+LDO+TRX combined ≥ 142 (Falsifier 4) AND new HBAR+AVAX combined ≥ 14 (Falsifier 5) AND no individual new symbol OOS PnL drag < -10% (Falsifier 6). Critic uses ALL FOUR signals to disambiguate clean PATH A / PATH C / NULL-RESULT.

**Catalog-axis verdicts** map to §4.4 table. The catalog row records the verdict exactly as Critic FINAL emits it.

---

## Section 9 — Library Stack Declaration

**SAME stack as iter-v3/008-020** — no version updates. iter-v3/020 already pinned sklearn `>=1.8,<1.9`:

```
python = 3.13
lightgbm = 4.6.0
numpy = 2.2.6
pandas = 3.0.0 (or recent compatible)
scikit-learn = 1.8.0  # PINNED EXPLICITLY (iter-v3/020 sub-fix #8) — addresses Critic Check 12 of iter-v3/019
pyarrow = 23.0.1 (for parquet I/O)
mlfinpy = 1.4.0 (CPCV; MIT-licensed fork)
pypbo = 0.10.0 (PBO via CSCV)
fracdiff = 0.10.0 (Numba-accelerated; FracdiffStat + ADF auto-d*)
statsmodels = 0.14.6 (adfuller for ADF stationarity)
optuna = 4.8.0
scipy = 1.17.0
httpx = (already used for kline fetcher; reused for funding-rate fetcher in iter-v3/019)
```

**No new package additions.** The universe expansion uses only existing infrastructure (V3_MODELS tuple in `run_baseline_v3.py`; REQUIRED_GAP constant in `validation_v3.py`; existing feature pipeline). Zero new dependencies.

---

## Section 10 — Adversarial Tests (no new tests required for this axis)

Universe expansion does not add new code paths — V3_MODELS tuple expansion + REQUIRED_GAP constant update + cap-flag toggle. Existing iter-v3/020 cap unit tests (`tests/strategies/ml/test_per_symbol_cap.py`) still PASS because:
- Cap implementation in `RiskV2Wrapper.get_signal()` is RETAINED unchanged
- Cap-disabled-by-default test (`test_per_symbol_cap_disabled_by_default`) verifies that with `enable_per_symbol_cap=False`, weight_factor is unchanged from inner strategy default — exactly iter-v3/021's runtime configuration

If the Engineer wants additional defensive tests, they could be added (NOT mandatory):
- `tests/test_v3_models_expansion.py::test_v3_models_5_symbols` — assert V3_MODELS has 5 entries with HBAR+AVAX present.
- `tests/strategies/ml/test_validation_v3.py::test_required_gap_5_symbol` — assert REQUIRED_GAP == 110 and matches `(timeout_candles+1) × n_symbols` formula.

The mandatory verifier is the Section 3.6 reconciliation table (15 commands), which exercises every code-path change without new test files.

---

## Section 11 — Catalog Row Pre-Commit (audit-trail discipline)

Per iter-v3/006+ catalog discipline, this brief pre-commits a structural template for the iter-v3/021 catalog row before backtest results are known:

```
| iter-v3/021 | 2026-05-07 | NEW universe expansion → V3_MODELS 3 → 5 (+HBAR + +AVAX; concentration architecture sub-axis B; HIGH-priority axis #2b) | IS Sharpe Δ TBD vs iter-v3/018 multi-seed +0.3788 | OOS Sharpe TBD vs anchor +0.3869 | TBD verdict | TBD candidate? |
```

The catalog row will be filled by the Phase 8 diary entry. The verdict cell maps to §4.4 + §8 criteria 1-3 + 11. The "candidate?" cell maps to whether the next CONFIRMATION-bundling QR should consider iter-v3/021 as a stack ingredient.

**Pre-committed disposition** (cannot be renegotiated post-hoc):
- If verdict = `EXPLORATION-PROMISING` (PATH A) AND Falsifier 4-6 ALL PASS: catalog row marked YES candidate (compoundable as a structural ingredient in any future CONFIRMATION bundle; first NEW-universe-expansion ingredient).
- If verdict = `EXPLORATION-PROMISING-INERT`: catalog row marked NO candidate (universe expansion propagated but no material lift — concentration dilution alone doesn't yield Sharpe lift; future concentration axes should test orthogonal mechanisms — per-symbol drawdown brake, vol-target ceiling, regime-conditional kill switch).
- If verdict = `EXPLORATION-PROMISING-MECHANICAL` (UNLIKELY given the per-symbol-architecture means new symbols must emit non-trivial fits; flagged for completeness): catalog row marked YES with NON-COMPOUNDABLE flag.
- If verdict = `EXPLORATION-NEGATIVE` or `EXPLORATION-NEGATIVE-no-effect`: catalog row marked NO; iter-v3/022 explores a DIFFERENT concentration-mechanism alternative (per `feedback_v3_concentration_is_signal.md` permitted alternatives: per-symbol drawdown brake, vol-target ceiling, regime-conditional kill switch) OR a DIFFERENT axis category (MEDIUM-priority #3 DSR gate reformulation OR #4 TRX/2022-Q4 regime gate). NEXT iteration MUST NOT be another universe-expansion variant — single-axis discipline + axis-category-rotation discipline.

**Catalog count after iter-v3/021**: 3 of 10 EXPLORATIONs in the post-bootstrap cycle; **7 more required** before any CONFIRMATION can launch (earliest = iter-v3/029 — bumped from iter-v3/028 because iter-v3/021 + 7 more = iter-v3/028 last EXPLORATION; first CONFIRMATION = iter-v3/029). Axis coverage after iter-v3/021: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 2 (drop-MKR retention + expand-to-5) + gate-adx × 1 (CLOSED) + NEW microstructure feature × 1 (CLOSED-narrow) + NEW model arch × 1 (CLOSED-at-config) + NEW labeling arch × 1 (PATH C) + bootstrap CONFIRMATION × 1 + NEW external-data-source feature × 1 (PROMISING-INERT) + NEW risk primitive (per-symbol cap) × 1 (CLOSED-mechanism) + **NEW universe expansion (3 → 5 symbols) × 1** = 13 unique axis representations after iter-v3/021.

**Forward axis pipeline** (iter-v3/022-028 candidates pre-pre-committed for QR continuity, NOT mandates per `feedback_v3_iter019_axis_priorities.md` LOCKED priority order):
- iter-v3/022 candidates: depending on iter-v3/021 verdict:
  - PATH A (PROMISING): MEDIUM-priority #3 (DSR gate reformulation) OR #4 (TRX/2022-Q4 regime gate) — concentration architecture has its first PROMISING component; bundle-candidates accumulate.
  - PATH C (NEGATIVE) OR INERT: try a different concentration-mechanism alternative — per-symbol drawdown brake (loss-stop semantics; orthogonal to scaling) OR vol-target ceiling (exposure ceiling, not per-symbol share). Per `feedback_v3_concentration_is_signal.md` LOCKED.
- iter-v3/023+ candidates: depend on iter-v3/021 + iter-v3/022 verdicts; further NEW feature families OR NEW model architectures (XGBoost-Sharpe-objective at higher n_trials, drawdown-penalized loss) once 1-2 PROMISING signals have accumulated.

---

## Final Brief-Authoring Checklist (Phase 5.5 self-check)

- [x] §0 sacred constants UNCHANGED, restated.
- [x] §0.5 EXPLORATION declaration with cadence count (3 of 10 in post-bootstrap cycle); STRUCTURAL axis Category 5 declared; explicit "NOT a gate-threshold knob"; references `feedback_v3_iter019_axis_priorities.md` LOCKED axis #2b + `feedback_v3_concentration_is_signal.md` LOCKED + `feedback_structural_over_knob_exploration.md`.
- [x] §1 hypothesis: one sentence, falsifiable; mechanism explanation (denominator expansion dilutes concentration without scaling existing positions; predicted IS [+0.30, +0.55] median +0.40 / OOS [+0.45, +0.70] median +0.55).
- [x] §2 IS-only numerical evidence with COMMITTED EDA SHA `a360251`; full 10-symbol ranking + top-2 decision tiles (HBAR + AVAX) + cross-correlation surface + counterfactual mechanical analysis + behavioral-effect predictor with derived saturation band [186, 269] anchored at iter-v3/018 IS trades 172 + per-symbol increment proxies.
- [x] §3 sub-fixes (8-item) with verifier commands; reconciliation table 15 rows; new V3_MODELS expansion + REQUIRED_GAP update + cap disable + ITERATION_LABEL update + feature regen for all 5 symbols.
- [x] §4 predicted IS Sharpe band [+0.30, +0.55] median +0.40, OOS Sharpe band [+0.45, +0.70] median +0.55; 6 catalog framings + falsifiers 1-6 + process locked; §4.4 row 5 condition `|Δ| ≥ 11 OR per-symbol shift > 5` per iter-v3/017 update; new Falsifier 4 (incumbent stability) + Falsifier 5 (new-symbol propagation) + Falsifier 6 (new-symbol drag).
- [x] §5 risk mitigation (4 cadence + 4 methodology + 3 axis-specific risks: new-symbol underperformance, REQUIRED_GAP propagation, parquet regen for new symbols including BTC dependency).
- [x] §6 7-primitive table — REVERTED (cap disabled; v3 returns to iter-v3/018 anchor's 7-primitive stack); new symbols subject to same 7-primitive stack.
- [x] §7 8 failure-mode predictions calibrated against 12 prior EXPLORATIONs + iter-v3/018 multi-seed evidence + iter-v3/021 EDA evidence (process P1-P3 = 35%; model P4-P8 = 95%; PATH C P6 = 25% reflecting EDA-grounded prior; PATH A P4 = 25% reflecting HBAR's 0.41 mean-|corr| diversification surface).
- [x] §8 11 EXPLORATION criteria; criterion 11 = saturation falsifier with derived band [186, 269] per `feedback_axis_saturation_predictor.md` + Falsifier 4 (incumbent stability) + Falsifier 5 (new-symbol propagation) + Falsifier 6 (new-symbol drag).
- [x] §9 library stack UNCHANGED from iter-v3/020 (sklearn already pinned >=1.8,<1.9); no new dependencies for universe expansion.
- [x] §10 no new adversarial tests required (no new code paths beyond config); existing iter-v3/020 cap tests still PASS.
- [x] §11 catalog row pre-commit + dispositions; forward axis pipeline (iter-v3/022+ candidates per `feedback_v3_iter019_axis_priorities.md` LOCKED priority order + `feedback_v3_concentration_is_signal.md` permitted alternatives).

**Brief authorship complete.** Engineer Phase 5.5 gate is the next step.
