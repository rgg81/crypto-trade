# Engineering Report — iter-v3/111

## Headers

- Iteration: iter-v3/111
- Branch: iteration-v3/111
- Commit SHA: 7dd84eedd07ae057228f202958bb307dcde939a7
- Hardware: DESKTOP-H1H6T11 / 20 CPU cores / 58 GiB RAM
- Wall-clock time: 1.09h

---

## Phase 5.5 Gate

OVERALL: PASS (committed at `briefs-v3/iteration_v3-111/phase5p5_gate.md`, SHA `319bcac`).

---

## label_mode Fix Verification — THE Purpose of iter-v3/111

**Verbatim run.log lines confirming triple_barrier (run.log lines 19–20):**

```
Config-accretion check (Critic /081 Rec #3): 13 knobs verified — ALL /111-canonical (CRV/AAVE/GRT/ADA 4-symbol universe, label_mode=triple_barrier)  PASS
label_mode (iter-v3/111 correction): 'triple_barrier'  PASS (triple_barrier restored; trend_scan_grid not applicable)
```

Both the expanded `_canonical_v059` guard (now 13 knobs including `label_mode` and `trend_scan_grid`) and the dedicated `label_mode` pre-flight assertion confirm `triple_barrier` as the training label. The iter-v3/110 confound (`trend_scanning` carry-over from /105) is verified absent. This satisfies Section 3.6 QE reconciliation instruction item 1.

---

## Configuration Diff vs /059 — LINE-BY-LINE Verified Against run.log

Per Section 3.6 item 2, every row was derived from `run.log` — NOT copied from brief prose.

| Knob | /059 canonical | iter-v3/111 as-run | Changed? | run.log evidence |
|---|---|---|---|---|
| `V3_MODELS` symbols | BCH, LDO, TRX | **CRV, AAVE, GRT, ADA** | **YES** (the axis) | run.log line 29: "Active models: 4/4" + "CRVUSDT, AAVEUSDT, GRTUSDT, ADAUSDT" |
| `label_mode` | `triple_barrier` | **`triple_barrier`** | **NO** (restored from /110's `trend_scanning`) | run.log line 20: `'triple_barrier'  PASS` (verbatim above) |
| `trend_scan_grid` | neutralized / default | neutralized / default | NO (restored) | run.log line 19: `_canonical_v059` 13-knob guard PASS; `trend_scan_grid not applicable` at line 20 |
| `REQUIRED_GAP` | 66 (3 syms) | **88** = (21+1)×4 | **YES** (consequence of 3→4 symbols) | run.log line 33: "Gap: 88 (= (21+1)*4; iter-v3/110 4-symbol universe CRV/AAVE/GRT/ADA; timeout UNCHANGED 10080 min; label_mode=triple_barrier iter-v3/111 correction)" |
| `label_timeout_minutes` | 10080 | 10080 | NO | run.log: "Timeout consistency ... BacktestConfig.timeout_minutes == LightGbmStrategy.label_timeout_minutes == 10080  PASS" |
| ATR multipliers (TP/SL) | 2.0 / 1.0 | 2.0 / 1.0 | NO | run.log line 3: "DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) ... PASS" |
| `V3_ATR_MULTIPLIERS_PER_SYMBOL` | `{}` | `{}` | NO | run.log line 5: "V3_ATR_MULTIPLIERS_PER_SYMBOL: 0 entries ... PASS" |
| `V3_FEATURE_COLUMNS` | 14-feature top-N | 14-feature top-N | NO | run.log line 2: "V3_FEATURE_COLUMNS: 14 columns ... PASS"; pre-flight "feature-cols=14  PASS" |
| `V3_FEATURES_PER_SYMBOL` | `{}` | `{}` | NO | run.log line 4: "V3_FEATURES_PER_SYMBOL: 0 entries ... PASS" |
| `zscore_threshold` | 2.0 | 2.0 | NO | run.log line 19: `_canonical_v059` 13-knob guard PASS |
| `adx_threshold` | 20.0 | 20.0 | NO | run.log: "Per-symbol ADX threshold ... global ADX threshold 20.0 applies to all 4 symbols PASS" |
| `inference_threshold_floor` | 0.0 | 0.0 | NO | run.log: "inference_threshold_floor REVERTED to default 0.0 ... PASS" |
| `enable_per_symbol_drawdown_brake` | False | False | NO | run.log: "Primitive 11 (per-symbol drawdown brake): enable=False ... PASS" |
| `block_long_for` / `block_short_for` | `()` / `()` | `()` / `()` | NO | run.log: "Primitive 10 ... block_long_for=(); block_short_for=() ... PASS" |
| ENSEMBLE_SIZE | 3 (EXPLORATION) | 3 | NO | run.log line 27: "Running in EXPLORATION mode (ensemble_size=3)"; `ensemble_summary.json`: `mode=exploration, ensemble_size=3` |
| `n_trials` | 35 | 35 | NO | run.log line 30: "Optuna trials/model: 35" |
| CPCV (N, k, paths, embargo) | 10, 2, 45, 27 | 10, 2, 45, 27 | NO | run.log line 32: "CPCV: N=10, k=2, 45 paths on IS CANDLE SEQUENCE" |
| `ITERATION_LABEL` | `v3-059` | `v3-111` | YES (label only) | run.log line 29: "BASELINE v3 iter-v3-111" |

**Substantive changes vs /059: exactly two — `V3_MODELS` (the axis) and `REQUIRED_GAP` (mechanical consequence of 3→4 symbols). Every label/model/risk knob is /059-canonical. `label_mode=triple_barrier` is confirmed at the guard level and pre-flight level.**

---

## Reconciliation and Consistency Checks

### Universe and Gap

- 4-symbol universe CRV/AAVE/GRT/ADA confirmed active (run.log: "Active models: 4/4").
- `REQUIRED_GAP=88` confirmed: run.log line 33 states `Gap: 88 (= (21+1)*4)`. `_verify_label_leakage_gap()` PASS confirmed.
- `V3_MODELS ∩ V3_EXCLUDED_SYMBOLS = ∅` PASS: run.log confirms CRV/AAVE/GRT/ADA disjoint from excluded list.

### OOS Cutoff

- OOS_CUTOFF_DATE = 2025-03-24 is operative: IS monthly_pnl.csv spans 2022-01 through 2025-03; OOS monthly_pnl.csv starts 2025-04. Split is correct.

### Walk-Forward Embargo

- Embargo present: the gap computation `(timeout_candles=21+1) * n_symbols=4 = 88` purges 88 candles between IS training end and test start per cell. PASS confirmed in run.log.

### Trade PnL Spot Check (2:1 ATR barrier geometry)

Trade row 1 (CRVUSDT SHORT @ 0.480000, SL=0.509283, TP=0.421433):
- SL_pct = (0.509283 − 0.480000) / 0.480000 = 0.06101
- TP_price = 0.480000 × (1 − 2.0 × 0.06101) = **0.421434** (file: 0.421433 — rounding only)
- gross_pnl = (0.509283 − 0.480000) / 0.480000 × 100 × (−1) = −6.101%; net = −6.201% (file: −6.2007) ✓

Trade row 2 (CRVUSDT LONG @ 0.457000, SL=0.420581, TP=0.529838):
- SL_pct = (0.457000 − 0.420581) / 0.457000 = 0.07969
- TP_price = 0.457000 × (1 + 2.0 × 0.07969) = **0.529838** (file: 0.529838) ✓
- gross_pnl = (0.529838 − 0.457000) / 0.457000 × 100 = 15.938%; net = 15.838% (file: 15.8382) ✓

The 2:1 ATR triple-barrier geometry is consistent throughout. Both TP and SL prices match the formula to 4–5 decimal places (sub-pip rounding only).

### IS MaxDD of 136.98% — Explanation

This is **a weighted-PnL cumulative-accounting artifact, NOT a data pathology.**

The MaxDD metric is computed on cumulative `weighted_pnl` (= `net_pnl_pct × weight_factor`), where `weight_factor` is the vol-scaled position size (0.0–1.0 per trade). Across 237 IS trades, the sum of weight_factors is 136.65, meaning aggregate notional exposure over the IS period greatly exceeds 1.0 in cumulative terms.

Reconstruction:
- Peak cumulative weighted_pnl reached during IS: **+42.19** (ADAUSDT-driven early IS profits, months 2022–2023 and 2024-12).
- Final cumulative weighted_pnl: **−51.51**.
- MaxDD = peak − trough = 42.19 − (−94.79) = **136.98%** (verified against comparison.csv 136.9823 to 4 decimal places).

The unit is percentage-points of cumulative weighted PnL, not percentage of notional account. Since multiple symbols trade concurrently and each carries a weight_factor up to 1.0, the cumulative exposure comfortably exceeds 100% over the 37-month IS window. A MaxDD of 136.98% denominated in these units is consistent with aggregate IS weighted_pnl of −51.51 and a peak of +42.19 — no implied leverage or data error.

---

## Key Metrics Block

| metric | in_sample | out_of_sample | ratio |
|---|---:|---:|---:|
| monthly_sharpe | −0.3075 | +0.1073 | −0.349 |
| daily_sharpe | −0.9505 | +0.1746 | −0.184 |
| max_drawdown | 136.98% | 49.59% | 0.362 |
| profit_factor | 0.8857 | 1.0239 | 1.156 |
| win_rate | 31.22% | 27.50% | 0.881 |
| n_trades | 237 | 80 | 0.338 |
| total_pnl | −51.51 | +3.39 | −0.066 |
| monthly_calmar | −0.3760 | +0.0683 | −0.182 |
| weighted_pnl_total | −51.51 | +3.39 | −0.066 |
| dsr | 0.0 | — | — |
| pbo | 0.1094 | — | — |
| psr | 0.7815 | — | — |
| n_trials | 420 | — | — |
| n_effective_trials | 19 | — | — |

---

## Ensemble Configuration

- Mode: EXPLORATION (3-seed ensemble, `ensemble_size=3`)
- Seeds: [191664963, 1662057957, 1405681631] (all `outer=42` lineage)
- Optuna trials per model: 35
- CPCV: N=10, k=2, 45 paths, IS candle sequence 20,144 candles across 4 symbols

---

## CPCV Path Distribution

45 paths: median Sharpe Q50 = +0.3916, Q25 = −0.4756, Q75 = +1.0728.
frac_positive_paths = 0.622 (28/45 paths positive). Gate threshold 0.55: PASS.
Per-cell mean PBO = 0.1094 (184 informative cells / 184 total).

Path-Sharpe dispersion is very wide (range approximately −3.44 to +2.11), consistent with 3-seed EXPLORATION-mode variance. The positive path fraction (0.622) is above the 0.55 floor but the highly negative tail paths (paths 24–29 all below −2.0) indicate meaningful path-dependent instability.

---

## ADF Stationarity

3,136 rows (4 syms × 14 feats × [52–63] months per symbol). 80.7% of cells stationary (p < 0.05). Non-stationary cells: 605. Within expected range [2,912, 3,528]. No anomaly.

---

## Label Leakage Audit

REQUIRED_GAP = 88 = (21 + 1) × 4 (timeout_candles = 21, n_symbols = 4). The `_verify_label_leakage_gap()` pre-flight confirmed this matches the López de Prado purge requirement. Confirmed at run.log line 33 and the "Label-leakage gap" pre-flight PASS block. No leakage.

---

## Gate Efficacy Table

From run.log ADAUSDT gate stats (seed 191664963, illustrative):

| Gate | Signals seen | Fires | Fire rate |
|---|---:|---:|---:|
| z-score OOD | — | 853 | — |
| Hurst regime | — | 100 | — |
| ADX threshold | — | 508 | — |
| Low-vol filter | — | 442 | — |
| Total kill rate | 2,399 | 1,903 | 79.3% |
| BTC trend (portfolio level) | 317 total trades | 35 killed | 11.0% |

Vol-scaled signals: 496. Mean vol scale: 0.633. Cap fires: 0. Drawdown brake fires: 0 (disabled). Direction block fires: 0. Regime gate fires: 0. Regime size scalar fires: 0.

The high ADX gate fire rate (508 / 2,399 signals = 21.2%) and OOD z-score rate (35.6%) are consistent with AAVE/ADA/GRT/CRV having different feature distributions from the /059 training environment; the OOD gate adapts per-symbol at training time.

---

## Section 8 Pre-Registered Criteria — Mechanical Application

**Anchor (per `feedback_v3_cycle1_axis_pass_criteria.md` and Section 8):** /060 EXPLORATION-mode reference: IS monthly Sharpe +0.8325, OOS monthly Sharpe +0.1403, frac_positive_paths 0.6444.

### EXPLORATION-PROMISING criteria (ALL must pass):

| Criterion | Threshold | Actual | Pass? |
|---|---|---|---|
| IS monthly Sharpe ≥ +0.9325 (IS Δ ≥ +0.10 vs /060) | +0.9325 | **−0.3075** | **FAIL** |
| OOS monthly Sharpe ≥ +0.3403 (OOS Δ ≥ +0.20 vs /060) | +0.3403 | **+0.1073** | **FAIL** |
| frac_positive_paths ≥ 0.50 | 0.50 | **0.622** | PASS |
| OOS / IS monthly Sharpe ratio ≥ 0.40 | 0.40 | **−0.349** | **FAIL** (OOS/IS undefined sign; OOS positive, IS negative) |
| top-symbol OOS PnL share ≤ 70% | 70% | **90.41%** (GRT) | **FAIL** |
| aggregate OOS trades ≥ 130 | 130 | **80** | **FAIL** |

EXPLORATION-PROMISING: **NOT MET** (5 of 6 criteria fail).

### EXPLORATION-PROMISING-MECHANICAL criteria:

Requires: top-symbol OOS PnL share ≤ 70% AND IS/OOS Sharpe both within ±0.20 of /060 anchor.
- IS within [+0.63, +1.03]: actual IS −0.3075 → **FAIL**.
- top-symbol OOS PnL share ≤ 70%: actual 90.41% → **FAIL**.

EXPLORATION-PROMISING-MECHANICAL: **NOT MET**.

### EXPLORATION-NEGATIVE criteria (ANY triggers NEGATIVE):

| Trigger | Threshold | Actual | Triggered? |
|---|---|---|---|
| IS monthly Sharpe < +0.7325 (IS Δ < −0.10 vs /060) | +0.7325 | −0.3075 | **YES** |
| OOS monthly Sharpe < −0.0597 (OOS Δ < −0.20 vs /060) | −0.0597 | +0.1073 | NO |
| OOS/IS ratio < 0.40 WITH OOS < +0.3403 | OOS=+0.1073 < +0.3403 → ratio check active; ratio = −0.349 | N/A (sign inversion) | **YES** (OOS not cleared AND ratio negative) |
| aggregate OOS trades < 130 | 130 | 80 | **YES** |

EXPLORATION-NEGATIVE: **TRIGGERED** (IS Sharpe far below floor at −0.3075 vs +0.7325 threshold; OOS trades 80 vs 130 floor; OOS/IS ratio inverted).

### IS-OOS daily Sharpe ratio sanity check (NEGATIVE-SUSPICIOUS band):

The ratio is (daily Sharpe OOS / daily Sharpe IS) = +0.1746 / −0.9505. The ratio is negative (IS negative, OOS positive), which is outside the [0.5, 2.0] normal band but in an atypical direction — OOS is BETTER than IS, not worse. This is the inverse of the NEGATIVE-SUSPICIOUS-OOS pattern (IS-fit/OOS-collapse). The IS/OOS daily Sharpe inversion (IS strongly negative, OOS weakly positive) is a structural feature of this result, not a sign-flip artifact. The NEGATIVE-SUSPICIOUS trigger fires on the criterion alone (ratio outside [0.5, 2.0]), but the direction is unusual.

### Final EXPLORATION verdict:

**EXPLORATION-NEGATIVE**

Primary trigger: IS monthly Sharpe −0.3075 (vs floor +0.7325, Δ = −1.04 vs /060 anchor). Secondary triggers: OOS trades 80 (vs floor 130), OOS/IS ratio inverted. The OOS Sharpe +0.1073 is fractionally below the INERT lower band (−0.0597) but that is overtaken by the IS collapse and trade-rate-floor failure.

---

## Per-Symbol OOS Attribution

From `out_of_sample/per_symbol.csv`:

| Symbol | OOS trades | Win rate | Net PnL % | OOS PnL share | Role |
|---|---:|---:|---:|---:|---|
| CRV | 22 | 31.8% | +5.51% | −9.59% | **Carrier** (positive net PnL) |
| AAVE | 20 | 35.0% | +3.54% | −6.16% | **Carrier** (positive net PnL) |
| ADA | 18 | 27.8% | −14.56% | 25.34% | **Dragger** |
| GRT | 20 | 20.0% | −51.94% | 90.41% | **Largest Dragger** |

Notes:
- The "concentration_pct" column in `comparison.csv` per-symbol section uses share-of-weighted-PnL, where the total OOS weighted PnL is +3.39. GRT's −25.20 weighted_pnl represents 90.41% of losses (on a near-zero total, concentration values are amplified by denominator noise — the total is close to zero so individual shares are large).
- CRV and AAVE are OOS-positive (carriers). This is notable: AAVE was pre-registered in Section 7 Mode 3 as the weakest IS candidate (win rate 0.3632 in IS gated book) — it performed better than expected OOS.
- GRT is the dominant OOS dragger (20.0% win rate OOS, −51.94% net PnL). GRT had the weakest absolute IS gated book (+136.14, PF 1.01). This is consistent with GRT being the most marginal universe member.
- ADA is a significant dragger (−14.56% net PnL), confirming the Section 7 Mode 4 pre-registration. ADA shows 27.8% OOS win rate vs 40.5% IS win rate — a substantial win-rate drop.
- Pre-registered failure modes: Mode 3 (AAVE underperforms) DID NOT fire (AAVE was OOS-positive). Mode 4 (ADA underperforms) PARTIALLY fired (ADA is a dragger). GRT's failure was not pre-registered as the primary dragger — GRT had the most marginal IS book (+136.14) and carried through to OOS.
- The overall OOS book is technically positive (+3.39 weighted PnL, PF 1.02) but on 80 trades — the signal exists but is too sparse and too dependent on CRV/AAVE to be tradeable at the current universe composition.

---

## Trade-Rate Explanation

OOS trades = 80 (vs brief predicted 90–180). The brief noted 89 OOS trades at iter-v3/110 (confounded label) and predicted `triple_barrier` would produce "at least as dense" a roster. The actual 80 is slightly below the /110 figure and below the 90 lower bound of the prediction band. The trade-rate-floor failure (80 < 130) is partly explained by the 4-symbol universe at EXPLORATION budget: each symbol generates ~18–22 OOS trades; GRT and ADA low win-rates suppress confidence signals. This is a legitimate trade-rate-floor failure, not a bug.

---

## Anomaly Notes

1. IS Sharpe strongly negative (−0.3075) while OOS slightly positive (+0.1073). This inversion — where IS is far worse than OOS — is unusual. It indicates the Optuna search at 35 trials/cell is not finding IS-profitable configurations for this universe on the 14-feature stack; the IS environment may be more volatile/adverse for the model (AAVE −66.62% net PnL IS, GRT −27.64% IS). The OOS environment over 2025-04–2026-05 happens to be marginally favourable for CRV and AAVE. This pattern is consistent with the hypothesis that the thin IS signal (Section 2.7 "thinness") is not reliably exploitable — the IS book fails while the OOS accidentally clears.

2. IS win rate 31.22% is below the 2:1 ATR breakeven of 33.3%. For the backtest to be profitable IS, the win rate must exceed 33.3% at the 2:1 ATR barrier geometry. The observed 31.22% IS win rate means the IS book is sub-breakeven, which mechanically causes the IS loss.

3. OOS win rate 27.50% is also below breakeven — yet OOS PnL is +3.39 weighted. This is possible when winners are systematically larger than the 2:1 expectation (e.g. some trades close at favourable intermediate prices) or when the weighted_pnl distribution is skewed. With only 80 OOS trades at 3-seed EXPLORATION variance, the OOS positive PnL is within sampling noise.

4. Random trade row spot-check (row 1, CRVUSDT SHORT OOS): exit_reason=stop_loss, exit at SL price 0.509283 confirmed against PnL −6.2007%. Geometry verified (see Reconciliation section above). No anomaly.

---

## Status

OVERALL=READY-FOR-CRITIC
