# iter-v1/029 — Research Brief (Phase 5)

**Authored**: 2026-05-28
**Branch**: `iteration-v1/029`
**Cycle**: 4, EXPLORATION 2/10
**Anchor**: BASELINE_V1.md `v0.v1-baseline-corrected` (`f8bc12c`) — Portfolio IS Sharpe +0.2829 / OOS Sharpe +0.6637
**Per-cohort anchor**: DOT-in-pool IS per-trade Sharpe +0.0398 / OOS per-trade Sharpe +0.0053 (DOT IS net +26.62% / OOS net +1.96%)
**LM Master verdict** (`briefs-v1/iteration_v1-029/lgbm_advisor.md`, `c4a4d14`): DOT HYBRID class `FRAGILE-POSITIVE-WITH-LONG-COUNTER-TREND-DRAG`; Path C BINDING recommendation (mirror ETH /019 symmetric BTC-trend gate ±8%).

---

## Section 0 — Hypothesis Statement

**H1 (primary)**: DOT-only single-cohort training (Model E semantics: R1 ON + R3 ON, atr_tp=3.5, atr_sl=1.75, baseline V1_FEATURE_COLUMNS_PRUNED 43 columns) **paired with a stateless direction-aware BTC-trend regime gate at ±8% on BTC 14d return (post-hoc trade-stream filter via `risk_v2.apply_btc_trend_filter`)** will lift DOT OOS per-trade Sharpe Δ into the **[+0.05, +0.55] band centered modal +0.30** by removing the OOS LONG-in-weak-up-BTC catastrophe (−8.47% / 7 tr / WR 28.6%) and the OOS SHORT-in-strong-down-BTC sample-zero void identified in `analysis/iteration_v1-029/dot_btc_trend_bucket.csv`. The mechanism mirrors ETH /019 (PROMISING +0.50 OOS Δ single-seed) which targeted the same counter-trend fingerprint at the same ±8% threshold + 42-bar lookback. Modal verdict cell: **PROMISING-INERT** (OOS Δ ~+0.30); HIGH-tail PROMISING (Δ ≥ +0.20).

### 0.1 Cycle position

Cycle-4 EXPLORATION **2 of 10** (cycle-4 started at /028 post-/027 technical-failure closeout). /028 (LTC single-cohort + atr_sl=1.0 LABEL-shift) returned PROMISING at +0.598 OOS Δ — first cycle-4 PROMISING precedent. /029 is the **LAST untested single-cohort in v1 baseline universe** (LINK /018 ✓, ETH /019 ✓, BTC /020 ✗-NEG-CAT, LTC /022 ✗-NEG-CAT then /028 ✓-PROMISING, DOT /029 = ?). Regardless of /029 verdict, cycle-4 pivots to **NEW feature families** at /030 (LM Master §7 PRE-COMMIT; funding-rate v2 or open-interest v2 or basis primitives — feature-family axis to avoid 4 consecutive per-cohort EXPLORATIONs).

### 0.2 LM Master Phase 4.5 coordination slot

LM Master adjudicated DOT as **HYBRID class FRAGILE-POSITIVE-WITH-LONG-COUNTER-TREND-DRAG** (NOT pure POSITIVE_EVERYWHERE as the Phase 4 classifier headline suggested) and recommended Path C (symmetric BTC-trend gate ±8% mirror /019) with 30% modal probability and OOS Δ band [+0.05, +0.55]. Path A (pure isolation, QR's tentative) carries 35% probability with wider bimodal risk band [−0.20, +0.35]. The QR has read `lgbm_advisor.md` end-to-end and **ADOPTS Path C** per the mechanistic evidence (DOT's OOS LONG-in-weak-up-BTC bucket −8.47% / WR 28.6% is the ETH /019 fingerprint). See Section 3.4 for the full LM Master response map.

### 0.3 DOT prior class (Phase 1 numerical evidence)

From `analysis/iteration_v1-029/dot_classification.csv` (committed at `bbab148`):

| Metric | DOT IS | DOT OOS |
|---|---|---|
| Net PnL | **+26.62%** | **+1.96%** |
| Trades | 93 | 46 |
| Win rate | 41.9% | 39.1% |
| Per-trade Sharpe | +0.0398 | +0.0053 |
| OOS/IS Sharpe ratio | — | **+0.1332** (FAIL the ≥ 0.5 floor — edge-erosion) |
| Avg PnL z-score | +0.384 | +0.036 |

**Classification headline**: POSITIVE_EVERYWHERE (sign-of-net-PnL both samples positive). **LM Master HYBRID re-classification**: structurally closer to ETH /019 than LINK /018 because of three drag fingerprints (see Section 1).

### 0.4 Cycle-4 cadence ledger summary

Cycle-4 EXPLORATIONs to date:
1. /028 — per-cohort-specialization-LTC-v2 (atr_sl=1.0 LABEL-shift) → **PROMISING** +0.598 OOS Δ (vs LTC-in-pool anchor)
2. /029 = THIS — per-cohort-specialization-DOT-v2 (symmetric BTC gate ±8%, mirror /019)

8 EXPLORATIONs remaining; CONFIRMATION earliest at /039 (after 10 EXPLORATION precedents accumulate from /028 forward).

### 0.5 LM Master tail re-weighting

LM Master adopted priors over 5 mechanism paths (§4):
- Path A (pure isolation): 35% probability, modal INERT, band [−0.20, +0.35] centered +0.05
- **Path C (symmetric BTC gate ±8%): 30% probability, modal PROMISING-INERT, band [+0.05, +0.55] centered +0.30** ← RECOMMENDED
- Path B (atr_sl=1.0): 15%, modal INERT-FAV, band [−0.30, +0.55] centered +0.10
- Path D (asymmetric long-suppress): 5%, NEGATIVE-CAT high tail
- Path E (COMBINED atr_sl=1.0 + BTC gate): 15%, HIGH-RISK 2-axis confound, modal wide band

LM Master directional track entering /029: 3/9 = 33%; methodology 7/7 perfect. Tail recalibrations consistently directionally correct on non-POSITIVE_EVERYWHERE cohorts. **QR ADOPTS Path C** with LM Master priors.

### 0.6 Axis Family Declaration + Rotation Discipline (v1 mandatory)

**This iter's family**: `per-cohort-specialization-DOT-v2` (NEW; **differentiates from /020 BTC pure isolation** by adding the orthogonal mechanism class of symmetric BTC-trend regime gate; **differentiates from /019 ETH mirror** by COHORT and underlying class designation HYBRID-FRAGILE-POSITIVE rather than /019's COUNTER-TREND class).

**Prior 5 EXPLORATIONs** (excluding /026 sanity slot and /027 CONFIRMATION-technical-failure which are exempt from Axis Rotation Discipline per skill Rule 4):

| iter | axis family | verdict |
|---|---|---|
| /022 | per-cohort-specialization-LTC (asymmetric long-suppress BTC gate) | NEG-CAT |
| /023 | feature-family (funding-rate z-score 30/90) | LEARNED-NEG clean |
| /024 | model-arch (regime-conditional sub-models) | NEG-clean |
| /025 | feature-family (OI delta z-score) | LEARNED-NEG-CAT |
| /028 | per-cohort-specialization-LTC-v2 (atr_sl=1.0 LABEL-shift) | PROMISING +0.598 |

**Rotation status**: **VALID**. The prior 5 disperse across **3 distinct families** (per-cohort/2, feature-family/2, model-arch/1). NOT same-family-5-of-5 monoculture; rotation discipline is honored.

**Rotation rationale**: `per-cohort-specialization-DOT-v2` is a NEW family designation (DOT cohort + post-Optuna BTC-trend gate as orthogonal mechanism class). Distinct from /022 LTC pure-asymmetric-gate (DIFFERENT cohort + DIFFERENT gate symmetry); distinct from /020 BTC pure-isolation (DIFFERENT cohort + NEW mechanism class — gate); distinct from /028 LTC-v2 (DIFFERENT cohort + DIFFERENT mechanism — label-shift vs post-Optuna gate). Family novelty justified per `feedback_v1_per_cohort_saturation_asymmetric_rotation.md` (mechanism class distinguishes families).

---

## Section 1 — DOT EDA (IS-only numerical evidence)

All numbers cite committed CSVs at `analysis/iteration_v1-029/`. Script: `dot_cohort_classification.py` (committed `bbab148`).

### 1.1 Direction-split attribution (`dot_direction_split.csv`)

| Sample | Direction | Trades | Win Rate | Net PnL | Per-trade Sharpe |
|---|---|---|---|---|---|
| IS LONG | +1 | 56 | 42.9% | **+25.39%** | +0.0636 |
| IS SHORT | −1 | 37 | 40.5% | +1.24% | +0.0045 |
| OOS LONG | +1 | 20 | 35.0% | **−1.60%** | −0.0093 |
| OOS SHORT | −1 | 26 | 42.3% | +3.56% | +0.0180 |

**Three diagnostic facts**:
1. **IS LONG carries 95% of IS net PnL** (+25.39% of +26.62%). Model E learned a LONG-biased basin.
2. **OOS direction signs FLIP**: LONG goes net-negative; SHORT carries the +1.96% OOS net. |Δ| = 5.17pp — right at the 5pp asymmetry threshold for COUNTER-TREND_OOS_DRAG classification.
3. The OOS SHORT-carried regime + IS LONG-biased basin is **exactly the ETH /019 signature** (ETH had IS LONG-dominant / OOS SHORT-dominant under the same gated mechanism).

### 1.2 OOS LONG counter-trend BTC bucket signature (`dot_btc_trend_bucket.csv`)

The LOAD-BEARING evidence supporting Path C is in the per-direction × BTC-trend-bucket attribution. Cell-level numbers:

| Sample | Direction | BTC trend bucket | Trades | Win Rate | Net PnL | Per-trade Sharpe |
|---|---|---|---|---|---|---|
| OOS | LONG | strong_down (< −8%) | 5 | 40.0% | −5.80% | −0.123 |
| OOS | LONG | weak_down (−8 → 0) | 6 | 33.3% | +14.07% | +0.209 |
| **OOS** | **LONG** | **weak_up (0 → +8)** | **7** | **28.6%** | **−8.47%** | **−0.162** |
| OOS | LONG | strong_up (≥ +8) | 2 | 50.0% | −1.41% | −0.122 |
| OOS | SHORT | strong_down (< −8%) | **0** | 0.0% | 0.00% | 0.00 |
| OOS | SHORT | weak_down (−8 → 0) | 11 | 45.5% | +0.88% | +0.011 |
| OOS | SHORT | weak_up (0 → +8) | 8 | 37.5% | −2.91% | −0.051 |
| OOS | SHORT | strong_up (≥ +8) | 7 | 42.9% | +5.59% | +0.080 |

**Key reading**:
- The **OOS LONG weak-up-BTC bucket** (BTC 14d return ∈ [0, +8%]) is the dominant OOS LONG drag: −8.47% from 7 trades at WR 28.6%. **A symmetric ±8% BTC-trend gate kills this bucket** (BTC trend within [−8, +8] permits trades; the gate strictly *opens* at extreme BTC trends in the symmetric framing). **CORRECTION**: the gate as wired in /019 KILLS counter-trend trades — kill LONG when BTC trend < −8% (strong-down dump), kill SHORT when BTC trend > +8% (strong-up rally). See Section 3.3 for the exact gate semantics.
- The OOS LONG strong-down bucket (BTC < −8%) at −5.80% from 5 trades is also counter-trend (DOT longing into a BTC dump) — killed by /019 gate semantics.
- The OOS SHORT strong-up bucket (BTC > +8%) at +5.59% from 7 trades is the **counter-trend SHORT that worked** — but at /019 gate semantics, a SHORT into a strong-up BTC IS counter-trend and gets killed. This creates the verdict-determining tension: does the gate's removal of the +5.59% strong-up SHORT wins offset its removal of the −5.80% / −8.47% LONG losses?
- **Net mechanism arithmetic** (rough): kill OOS LONG strong-down (−5.80%) + kill OOS LONG weak-up-BTC at threshold (−8.47%) − kill OOS SHORT strong-up (+5.59%). NET +8.68% recovery if symmetric gate kills both counter-trend buckets.

### 1.3 IS H1/H2 regime instability (`dot_monthly_pnl.csv`)

DOT had a catastrophic-then-recovery IS regime shift:
- **IS H1 (months 1-15: 2022-08 to 2023-12)**: **−18.19% net / 59 trades** (WR ~37%; catastrophic)
- **IS H2 (months 16-30: 2024-01 to 2025-02)**: **+44.82% net / 34 trades** (WR ~50%; massive recovery)

The +26.62% IS net is dominated by H2. If DOT-only training lands in an H1-similar OOS regime (large drawdown phase), pure isolation has no defense. The BTC-trend gate (Path C) addresses this indirectly by killing trades when BTC is in extreme regimes — historically (per `dot_btc_trend_bucket.csv` IS rows) IS LONG strong-down at +23.42% (positive in IS) and IS SHORT strong-up at −38.00% (catastrophic in IS) are the gate-fire candidates; the symmetric gate kills both. IS gate effect computed at fire-rate band §F-AXIS #3.

### 1.4 OOS exit-reason distribution (`dot_exit_reasons.csv`)

| Sample | Exit reason | Count | Share |
|---|---|---|---|
| IS | stop_loss | 47 | 50.5% |
| IS | timeout | 26 | 28.0% |
| IS | take_profit | 20 | 21.5% |
| OOS | stop_loss | 26 | 56.5% |
| OOS | timeout | 11 | 23.9% |
| OOS | take_profit | 8 | 17.4% |
| OOS | end_of_data | 1 | 2.2% |

OOS TP-exit count is **8** in baseline DOT-in-pool — well above the F-AXIS #5 LOAD-BEARING threshold of ≥ 2 transferred from /028. The gate will compress trade count by ~15% (predicted fire-rate; see §F-AXIS #3) → expected /029 OOS TP-exit count ≈ 7 (well within safe band).

### 1.5 LM Master HYBRID classification (recap)

LM Master adjudicated DOT as **NEW HYBRID sub-class `FRAGILE-POSITIVE-WITH-LONG-COUNTER-TREND-DRAG`**:
- **Fragile**: OOS/IS Sharpe ratio +0.13 (well below 0.5 generalization floor)
- **Positive**: sign-of-net-PnL both samples positive (POSITIVE_EVERYWHERE classifier headline)
- **Long-counter-trend-drag**: OOS LONG weak-up-BTC bucket −8.47% / WR 28.6% (ETH /019 fingerprint)
- **+ H1/H2 IS regime instability** (LTC /028 fingerprint)

QR ADOPTS HYBRID re-classification verbatim.

---

## Section 2 — ORACLE EDA + Falsifier pre-registration

All falsifier bands are LM Master §5 verbatim; QR ADOPTS all 5 F-AXIS items.

### F-AXIS #1 — Dispatch correctness (binary)

`df['symbol'].unique() == ['DOTUSDT']` for both `in_sample/trades.csv` and `out_of_sample/trades.csv`. **PASS criterion**: 100% DOTUSDT in both rosters. **FAIL criterion**: any non-DOTUSDT row.

### F-AXIS #2 — Trade-count band

- **IS predicted [62, 130] modal 90**. DOT-in-pool 93 IS trades → DOT-only retrain ±30% → effective IS [50, 105] post-gate; pre-gate [62, 130].
- **OOS predicted [22, 55] modal 38**. DOT-in-pool 46 OOS trades → gate kill ~15% → effective OOS [18, 47]; pre-gate [25, 55].
- **FAIL trigger**: OOS < 22 → UNDER-FIRE NEGATIVE-INERT-no-trades; IS > 130 → over-permissive baseline drift (unlikely).

### F-AXIS #3 — Gate fire-rate band [PATH C; LOAD-BEARING]

Per LM Master §5 + /019 ETH precedent (IS fire-rate 19.50%, OOS fire-rate 14.29% both PASS):

- **IS band [10%, 30%] modal 18%** (mirror /019 ETH IS 19.50%; DOT weak-up-BTC concentration narrower)
- **OOS band [5%, 30%] modal 15%** (mirror /019 ETH OOS 14.29%)

**LOAD-BEARING THRESHOLDS**:
- OOS fire-rate < 5% → UNDER-FIRE → INERT-NO-EFFECT (verdict CAPPED at INERT regardless of F1 magnitude)
- OOS fire-rate > 35% → OVER-KILL → NEGATIVE-INERT-no-trades or NEGATIVE-INTRINSIC

### F-AXIS #4 — n_eff_per_cell band

- **Band [3, 8] modal 5**. DOT IS labels ~93 + ENSEMBLE_SIZE=10 + n_trials=35 → predict 5.
- **Informational only on verdict-positive outcome**. If n_eff=2 AND verdict NEGATIVE → flag as ENSEMBLE COLLAPSE (vs single-instance anomaly at /028).

### F-AXIS #5 — OOS TP-exit count ≥ 2 [LOAD-BEARING; transferred from /028]

- **Predicted /029 OOS TP exits ≥ 5** retains mechanism upside (consistent with baseline DOT-in-pool OOS TP=8 minus ~15% gate kill).
- **F-AXIS #5 binary**: OOS TP-exit count < 2 → mechanism degenerates to loss-clipping-only → verdict **CAPPED at PROMISING-INERT regardless of F1 magnitude**. This is the /028 §6 lesson transferred verbatim.
- **Path-C-specific check**: gate should preserve TP share at ~17-20%; if gate destroys high-TP trades preferentially (TP share drops below 10%), gate is destroying value not adding it (informational diagnostic).

### F-AXIS-MECHANISM compound (5 sub-checks)

1. **F-AXIS-M #1 (binary dispatch)** = F-AXIS #1 above
2. **F-AXIS-M #2 (trade-count)** = F-AXIS #2 above
3. **F-AXIS-M #3 (gate fire-rate LOAD-BEARING)** = F-AXIS #3 above
4. **F-AXIS-M #4 (n_eff_per_cell)** = F-AXIS #4 above
5. **F-AXIS-M #5 (TP-exit LOAD-BEARING)** = F-AXIS #5 above

All sub-checks PASS criteria pre-registered. F-AXIS-M #3 and #5 are verdict-capping.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1 mandatory)

**Declaration**: **NORMAL-RISK**.

**Reason**: Path C (symmetric BTC-trend gate ±8%) is a **post-Optuna stateless trade-stream filter** applied via `risk_v2.apply_btc_trend_filter`. It does **NOT** change Optuna's training-objective domain (label distribution, feature set, training universe, or risk-primitive). Per `feedback_v1_high_risk_declaration_discipline.md`, only training-objective-domain changes (label-mode, universe substitution, feature-set replacement, bar-interval change) qualify as HIGH-RISK. The gate is identical to /019 ETH gate spec where /019 was declared HIGH-RISK because of the *combined* 2-axis change (cohort + gate). /029 cohort variation (DOT-only) is the primary axis; gate is the orthogonal post-Optuna mechanism. Single-axis EXPLORATION at single-seed=42 is permitted per `feedback_axis_saturation_predictor.md`.

**Note on /019 precedent**: /019 was declared HIGH-RISK (3rd cycle-3 HIGH-RISK) primarily because of ETH's 4/4 NEGATIVE structural prior. DOT's prior class is FRAGILE-POSITIVE (sign-positive both samples) — less structural risk than ETH's 4/4 negative pattern. NORMAL-RISK declaration calibrated.

**Mitigation (informational)**: Optional pre-commit-to-CONFIRMATION tripwire NOT armed at NORMAL-RISK (would require PROMISING gate hit + cycle 4 wall-clock budget reservation). If /029 returns PROMISING (Δ ≥ +0.20), the /027-style bundle composition is enriched at /029 closeout — informational impact only, no compute commitment.

---

## Section 2.6 — ORACLE EDA trade-attribution requirement

Per `feedback_v1_oracle_eda_trade_attribution.md`, all feature-family briefs must include BOTH distribution-level Sharpe-proxy AND realized-trade attribution. /029 is **per-cohort-specialization** (NOT feature-family), but the rule's spirit applies to the BTC-trend bucket signal.

**Distribution-level**: The /029 brief Section 1.2 dot_btc_trend_bucket.csv table IS the realized-trade attribution at cell level. Per-direction × per-BTC-trend bucket × IS/OOS = 16 cells. Both win-rate AND net-PnL × per-trade-Sharpe reported.

**Sharpe-proxy distribution** (forward-return regression on BTC trend bucket): not separately required because the realized-trade attribution is already published and is the direct mechanism evidence. The /025 OI-delta Q1 sign-flip basin-relocation lesson does not apply at /029 because the BTC-trend gate has NO basin-relocation risk on labels (it is a post-Optuna trade-stream filter; labels are computed identically to baseline DOT-in-pool).

**Mandate satisfied**. CSV: `analysis/iteration_v1-029/dot_btc_trend_bucket.csv` (16 cells; committed `bbab148`).

---

## Section 3 — Implementation Spec

### 3.1 Universe + features

- **`V1_ITER029_UNIVERSE = ("DOTUSDT",)`** — NEW constant in `src/crypto_trade/features_v1/__init__.py`
- **Feature set**: `V1_FEATURE_COLUMNS_PRUNED` (43 cols) — **FROZEN UNCHANGED** from /028
- **Cross-asset features**: BTC klines still required for cross-asset feature generation (DOTUSDT klines drive trade roster; BTC klines drive cross-features + BTC-trend gate input)

### 3.2 Labels

- **Triple-barrier σ_t EWMA 14d** (cycle-2 baseline UNCHANGED)
- **`atr_tp_multiplier = 3.5`** UNCHANGED (Model E baseline; same as /018 LINK + /019 ETH)
- **`atr_sl_multiplier = 1.75`** UNCHANGED (Model E baseline; baseline pure-isolation mandate per LM Master Path C — gate is the only orthogonal axis change)
- **`label_timeout = 21 bars`** UNCHANGED (7 days at 8h)
- **Embargo at walk-forward boundary**: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` UNCHANGED — verified at /058 cycle-2 FIX and load-bearing for all post-/058 v1 iterations

### 3.3 Mechanism (Path C — BTC-trend gate ±8% mirror /019)

**Gate spec** (mirrors /019 ETH exactly):
- **Module**: `src/crypto_trade/strategies/ml/risk_v2.py` — uses `BtcTrendFilterConfig` + `apply_btc_trend_filter` helper (cross-track helper-layer import permitted under documented v1 track-isolation rule per /019 precedent)
- **Lookback**: 42 bars (14 days at 8h candles) — UNCHANGED from /019
- **Threshold**: ±8% on BTC 14d return — UNCHANGED from /019
- **Direction-aware semantics**:
  - Kill LONG when BTC 14d return < −8% (strong-down BTC dump; counter-trend long)
  - Kill SHORT when BTC 14d return > +8% (strong-up BTC rally; counter-trend short)
  - Trades within BTC 14d return ∈ [−8%, +8%] (mild regime) → PASS
  - Trades aligned with BTC trend (LONG in strong-up; SHORT in strong-down) → PASS
- **Application point**: post-hoc trade-stream filter (after Model E LightGBM signal generation; before live trade execution / backtest matching)
- **Constants** (frozen for /029):
  - `V1_ITER029_BTC_GATE_LOOKBACK_BARS = 42`
  - `V1_ITER029_BTC_GATE_THRESHOLD_PCT = 8.0`
  - `V1_ITER029_BTC_GATE_ENABLED = True`

**Past-only verification**: Gate computes `btc_14d_return` from BTC kline series indexed to candle close_time (read via `np.searchsorted right−1`) with warmup floor of 42 bars. The gate input at signal-time t uses only BTC kline data with close_time < t. PASS by construction (mirrors /019 verified at /019 walk-forward audit).

**Risk layer config** (mirror /019 + /028 Model E semantics):
- **R1**: ON (15-day cooldown after 2 consecutive stop-losses; Model E baseline)
- **R2**: OFF (drawdown brake; standard Path C constraint — deviation from Model E baseline is documented and mirrors LINK /018 + ETH /019 single-cohort precedents)
- **R3**: ON (OOD Mahalanobis; always-on project-wide)

### 3.4 LM Master Phase 4.5 Responses (MANDATORY — explicit ADOPTED / MODIFIED / REJECTED per §1-§7)

#### §1 HYBRID classification

- **ADOPTED**. DOT re-classified as **FRAGILE-POSITIVE-WITH-LONG-COUNTER-TREND-DRAG** in brief Section 1.5 verbatim. The Phase 4 sign-of-net-PnL classifier headline (POSITIVE_EVERYWHERE) is preserved as the *classifier output* but LM Master HYBRID is the **operational class** that drives Path C selection. This adoption changes the modal verdict expectation from /018-LINK analog (modal PROMISING +0.80 single-seed) to /019-ETH analog (modal PROMISING +0.30 single-seed, narrower band).

#### §2 Hyperparameter region recommendations + §2.5 ESCALATE n_trials and ENSEMBLE_SIZE

- **ADOPTED**. n_trials ESCALATED 18 → **35** (mirror /028 LTC config). ENSEMBLE_SIZE ESCALATED 3 → **10** (mirror /028 LTC config). LM Master §2.5 rationale accepted: /028 vindicated n_trials=35 + ENSEMBLE_SIZE=10 at EXPLORATION budget (~30 min wall-clock); DOT cohort is structurally HARDER than LTC at /028 (FRAGILE-POSITIVE + IS H1/H2 regime instability + LONG-counter-trend drag) and deserves equal variance budget. Wall-clock prediction 30-45 min, INSIDE 2h cap.
- **Sub-recommendations** (informational; default LightGBM bounds from `v1_pruned` profile retained):
  - num_leaves upper bound default (LM recommended cap 47 — **DEFER**, default v1_pruned upper is already 47 from /002 prune)
  - min_data_in_leaf lower bound default (LM recommended ≥60 — **DEFER**, default v1_pruned is 30)
  - learning_rate upper default (LM recommended cap 0.08 — **DEFER**, default v1_pruned is 0.1)
  - lambda_l1 lower bound default (LM recommended ≥0.1 — **DEFER**)
  - bagging_fraction lower bound default (LM recommended ≥0.6 — **DEFER**)
  - **Rationale for DEFER**: LM Master §2 sub-recommendations are informational; the n_trials=35 + ENSEMBLE_SIZE=10 elevation is the binding change. Bounds tightening is a SECONDARY axis variation that would confound Path C attribution (gate + bounds tightening = 2 changes) under single-seed EXPLORATION. Per /014's "no bundled axes" lesson, single-axis isolation is preserved.

#### §3 Feature rank predictions

- **ADOPTED INFORMATIONAL** (post-hoc validation at Phase 7.4). LM Master predicts: ret_5d / atr_pct_50 / vwap_dev_20 / rsi_14_smooth_5 in top-3-rank; btc_ret_42 in rank 5-10; small-window RSI variants rank 30+/43 (DEAD WEIGHT). These are post-hoc check items — no pre-commit action. The /027-retry feature_importance audit will produce per-cohort feature_importance.csv automatically (carry-forward from /021 infrastructure).

#### §4 Path C BINDING recommendation

- **ADOPTED** (the load-bearing decision). Path C (symmetric BTC-trend gate ±8% mirror /019) is the brief's primary mechanism. **REJECTION of Path A** (pure isolation) is explicit: LM Master §4 "Why NOT Path A" rationale (LINK /018 pure isolation worked for direction-balanced edge; DOT has 95% LONG IS basin + LONG-counter-trend OOS DRAG → pure isolation bimodal risk band [−0.20, +0.35] vs Path C [+0.05, +0.55]) is accepted. **REJECTION of Path B** (atr_sl=1.0): per-cohort SATURATION rule (post-/028) — atr_sl=1.0 is for ASYMMETRIC_ROTATION cohorts (/028 LTC). DOT is FRAGILE-POSITIVE, not ASYMMETRIC_ROTATION. **REJECTION of Path D** (asymmetric long-suppress): /022 FAILED precedent at single-axis asymmetric gate. **REJECTION of Path E** (COMBINED atr_sl=1.0 + BTC gate): HIGH-RISK 2-axis perturbation; confounds attribution at single-seed EXPLORATION; DEFER to /030+ retry stack only if /029 Path C lands INERT.

#### §5 Falsifier pre-registration (5 F-AXIS items)

- **ADOPTED VERBATIM**. All 5 F-AXIS items (#1 dispatch, #2 trade-count, #3 gate fire-rate LOAD-BEARING, #4 n_eff_per_cell, #5 TP-exit LOAD-BEARING) carried into brief Section 2 verbatim. Bands per LM Master §5 numbers. F-AXIS #3 and #5 are verdict-capping.

#### §6 Track-record commentary on calibration

- **ACKNOWLEDGED**. LM Master /028 calibration: modal +0.30 to +0.60 OOS Δ; observed +0.598 → upper edge of modal band. Magnitude predictions slightly conservative on atr_sl-style label-shift on ASYMMETRIC_ROTATION cohorts. For /029 Path C, LM Master predicts modal +0.30 centered, band [+0.05, +0.55] — this is the brief's PROMISING-INERT modal expectation. Confidence MEDIUM (higher than /020 BTC pure isolation 60% INERT NEG-CAT; lower than /028 post-LTC-class understanding).

#### §7 Routing recommendation for /030

- **ADOPTED PRE-COMMIT**. Regardless of /029 verdict (PROMISING / INERT / NEGATIVE), /030 axis = **NEW feature family** (funding-rate v2 or open-interest v2 — both UNUSED at EXPLORATION budget with v2 designation since /023 funding LEARNED-NEG-clean and /025 OI-delta LEARNED-NEG-CAT). Cohort-coverage axis CLOSES at /029 regardless of outcome (DOT is the LAST untested single-cohort). /030 PRE-COMMIT to feature-family avoids 4 consecutive per-cohort EXPLORATIONs (/020 BTC, /022 LTC, /028 LTC-v2, /029 DOT-v2). Verdict-conditional fine-grained routing:
  - /029 PROMISING (Δ ≥ +0.20) → /030 NEW-feature-family + concurrent /027-retry bundle composition planning (4-specialist: LINK /018 + ETH+gate /019 + LTC+atr_sl /028 + DOT+gate /029)
  - /029 INERT (|Δ| < 0.20) → /030 NEW-feature-family (DOT-specialist NOT bundled; /027-retry stays 3-specialist)
  - /029 NEGATIVE (Δ < −0.20) → /030 NEW-feature-family (cohort-isolation axis CLOSED PERMANENTLY for v1 at 3 NEG-CAT across /020 + /022 + /029)

### 3.5 Configuration

- **n_trials**: 35 (LM Master §2.5 ADOPTED; mirror /028)
- **ENSEMBLE_SIZE**: 10 (LM Master §2.5 ADOPTED; mirror /028; single-pass inner — v1 runner has no `--seeds` flag, ensemble_seeds is the LightGBM strategy's internal ensemble)
- **Outer seed**: single-seed=42 (EXPLORATION budget; v1 runner is single-seed by default)
- **Sample weighting**: `abs_pnl` (baseline; cycle-3 /016 finding — uniform sample weighting NEG-CAT)
- **Bar interval**: 8h (UNCHANGED)
- **Bounds profile**: `v1_pruned` (UNCHANGED from /028 — Path C sub-recommendations DEFERRED)
- **Risk layers**: R1 ON (Model E baseline), R2 OFF (Path C constraint), R3 ON (always-on)
- **Wall-clock HARD CAP**: 2h (EXPLORATION cadence; LM Master prediction 30-45 min)

### 3.6 Wall-Clock Estimate (Phase 5.5 BLOCK if missing or > 1.6h)

- **LM Master prediction**: 30-45 min Optuna (similar to /028 LTC at same n_trials=35 + ENSEMBLE_SIZE=10)
- **Pre-flight + post-flight**: ~5-10 min (artifact emission + engineering_report.md)
- **TOTAL**: 35-55 min (BUDGET 1.6h-equivalent target satisfied with margin)
- **Kill-switch**: > 1.6h total → wall-clock breach; same as /028 protocol
- **Cumulative wall-clock budget tracking**: cycle-4 to date = /028 ~30 min + /029 ~45 min projected = ~75 min over 2 EXPLORATIONs (well inside 10-EXPLORATION budget)

### 3.7 Code changes (single src/ file: `run_baseline_v1.py`)

Mirror /019's exact pattern. NEW constants at top:
```python
V1_ITER029_UNIVERSE = ("DOTUSDT",)
V1_ITER029_BTC_GATE_LOOKBACK_BARS = 42
V1_ITER029_BTC_GATE_THRESHOLD_PCT = 8.0
V1_ITER029_BTC_GATE_ENABLED = True
```

NEW elif branch in `run_baseline_v1.py` main dispatch (mirror /019 structure):
```python
elif set(symbols) == set(V1_ITER029_UNIVERSE):
    # Model E semantics: R1 ON + R3 ON, atr_tp=3.5, atr_sl=1.75
    # Path C: symmetric BTC-trend gate ±8% (post-hoc trade-stream filter)
    btc_gate_config = BtcTrendFilterConfig(
        lookback_bars=V1_ITER029_BTC_GATE_LOOKBACK_BARS,
        threshold_pct=V1_ITER029_BTC_GATE_THRESHOLD_PCT,
        enabled=V1_ITER029_BTC_GATE_ENABLED,
    )
    # ... build Model E strategy with btc_gate_config wired through
```

A/C/D/F/G dispatch branches dropped via `set(symbols)==set(V1_ITER029_UNIVERSE)` guard. **No methodology, no report-file ordering, no race-condition surfaces** (mirror /019 structural-incapable-of-look-ahead).

### 3.8 Axis Family Declaration (Critic Check 14 verification path)

- **Axis family**: `per-cohort-specialization-DOT-v2` (NEW family)
- **Justification for NEW family vs reuse of /020's literal `per-cohort-specialization-BTC` or /022's `per-cohort-specialization-LTC` or /028's `per-cohort-specialization-LTC-v2`**:
  - DIFFERENT cohort (DOT) from /020 BTC, /022 LTC, /028 LTC-v2
  - DIFFERENT mechanism class from /020 (BTC pure isolation; no orthogonal mechanism layer)
  - DIFFERENT mechanism class from /022 (asymmetric long-suppress gate; one-sided)
  - DIFFERENT mechanism class from /028 (atr_sl=1.0 LABEL-shift; pre-Optuna)
  - SAME mechanism class as /019 (symmetric BTC-trend gate ±8%; post-Optuna trade-stream filter) but DIFFERENT cohort and HYBRID-FRAGILE-POSITIVE class designation
  - Per `feedback_v1_per_cohort_saturation_asymmetric_rotation.md`, mechanism class distinguishes families
- **Rotation status**: VALID (prior 5 disperse across 3 distinct families; not monoculture)

---

## Section 4 — Verdict Matrix (F1 OOS Δ band per LM Master §5)

| OOS Δ band | Verdict cell | Mechanism interpretation |
|---|---|---|
| Δ ≥ +0.55 | **PROMISING-CLEAN** (very tail; prior 8%) | Gate over-performs ETH /019 single-seed benchmark — informational; likely lottery |
| Δ ∈ [+0.20, +0.55) | **PROMISING** (modal; prior 25%) | Path C mechanism delivers as predicted; bundle into /027-retry |
| Δ ∈ [+0.05, +0.20) | **PROMISING-INERT** (modal sub-band; prior 25%) | Gate works but lift small; informational on bundle composition |
| Δ ∈ [−0.20, +0.05) | **INERT** (prior 25%) | Gate has no effect OR labels untouched and baseline DOT-only matches DOT-in-pool |
| Δ ∈ [−0.55, −0.20) | **NEGATIVE-CLEAN** (prior 12%) | Gate kills value (kills high-TP trades) OR Path C fails on DOT class |
| Δ < −0.55 | **NEGATIVE-CATASTROPHIC** (prior 5%) | DOT FRAGILE-POSITIVE class collapses under cohort isolation alone (gate has no defense against H1-regime drag) |

**F-AXIS overrides** (verdict-capping per LM Master §5):
- F-AXIS #3 OOS fire-rate < 5% → verdict CAPPED at INERT-NO-EFFECT (regardless of F1)
- F-AXIS #3 OOS fire-rate > 35% → verdict CAPPED at NEGATIVE-INERT or NEGATIVE-INTRINSIC
- F-AXIS #5 OOS TP-exit count < 2 → verdict CAPPED at PROMISING-INERT (regardless of F1)

**LM Master modal prediction**: PROMISING-INERT (Δ ~+0.30; prior 25% on Path C; ~10% conditional on Path adopted).

**Pre-committed CONFIRMATION composition implications**:
- If verdict ≥ PROMISING → /029 DOT+gate joins /027-retry 4-specialist bundle (LINK + ETH+gate + LTC+atr_sl + DOT+gate); nominal sum +1.90, correlation-adjusted target +1.10 to +1.40 OOS Sharpe at multi-seed
- If verdict INERT → bundle stays 3-specialist
- If verdict NEGATIVE → cycle-4 cohort-isolation axis is at 3 NEG-CAT (/020 BTC + /022 LTC + /029 DOT); axis CLOSED PERMANENTLY for v1

---

## Section 5 — Risk Mitigation (per `feedback_risk_mitigation_design.md`)

### R1 (consecutive-SL cooldown) — ON

- Model E baseline: 15-day cooldown after 2 consecutive stop-losses
- IS-calibrated effect on DOT-in-pool: ~5-8 IS trade reduction from cooldown trips
- Simulated /029 effect: similar magnitude (~5 IS / ~2 OOS trade reduction)
- Mechanism: prevents cascade of stop-losses in catastrophic regime; complementary to BTC-trend gate (gate handles extreme regimes; R1 handles micro-streaks)

### R2 (drawdown brake) — OFF

- Standard Path C constraint per LM Master §2 + mirror /019 ETH + /018 LINK single-cohort precedents
- Deviation from Model E baseline (which has R2 ON with DD trigger=7%, anchor=15%, floor=0.33)
- Rationale: pure-isolation cohort experiments need axis isolation; R2 is a secondary axis that would confound gate attribution. DEFER R2 reactivation to /027-retry CONFIRMATION (multi-seed budget can attribute R2 separately).
- Risk: if DOT IS H1-style catastrophic regime materializes in /029 OOS, no drawdown-triggered defense → exposure to monthly catastrophic loss. **Mitigation**: BTC-trend gate addresses extreme BTC regimes which are the primary correlate of DOT H1-catastrophic months (per `dot_btc_trend_bucket.csv` IS rows showing IS LONG strong-down at +23.42% IS positive but OOS LONG strong-down at −5.80% — gate kills this counter-trend channel).

### R3 (OOD Mahalanobis) — ON

- Project-wide always-on
- IS-calibrated cutoff: 70th percentile of feature-vector Mahalanobis distance against training-window covariance (16 scale-invariant features)
- /029 effect: standard OOD blocking; ~2-5% trade-skip rate expected (informational)

### F-AXIS #3 LOAD-BEARING monitoring

- OOS gate fire-rate band [5%, 30%] modal 15% (LM Master §5)
- < 5% → UNDER-FIRE → INERT-NO-EFFECT verdict cap
- > 35% → OVER-KILL → NEGATIVE verdict cap
- Forensic logs at `data/v1_iter_v1-029_optuna_best_params.parquet` (carry-forward from /021 infrastructure; required for Phase 7.4 mechanism attribution)

### F-AXIS #5 TP-exit LOAD-BEARING monitoring (transferred from /028)

- OOS TP-exit count ≥ 2 floor
- < 2 → mechanism degenerates to loss-clipping-only → verdict CAPPED at PROMISING-INERT regardless of F1 magnitude
- Predicted /029 OOS TP-exits ~7 (baseline 8 minus ~15% gate kill); WELL above floor

### Wall-clock kill-switch

- Hard cap 2h per cycle-4 EXPLORATION cadence discipline
- LM Master predicts 30-45 min Optuna + 5-10 min wrap-up = ~45 min total
- If wall-clock > 1.6h → kill-switch (mirror /028 protocol)

---

## Section 6 — Symbol Exclusion

**`V1_EXCLUDED_SYMBOLS` unchanged.** No symbols added or removed from the v1 baseline universe (`V1_BASELINE_UNIVERSE = (BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT)`). /029 narrows to `V1_ITER029_UNIVERSE = (DOTUSDT,)` only for the iter-v1/029 dispatch branch — baseline universe constant is untouched.

---

## Section 7 — Reproducibility

- **HEAD commit (post-Phase 5.5)**: TBD (orchestrator will dispatch QE Phase 6 to commit src/ changes; Phase 5.5 gate verifies brief readiness BEFORE Phase 6)
- **Seed**: 42 (single outer seed)
- **ENSEMBLE_SIZE**: 10 (inner ensemble seeds — LightGBM strategy internal)
- **n_trials**: 35 (Optuna budget)
- **Bounds profile**: `v1_pruned` (UNCHANGED)
- **Feature columns**: `list(V1_FEATURE_COLUMNS_PRUNED)` (43 cols; explicit per `feedback_explicit_feature_columns.md`)
- **Universe**: `V1_ITER029_UNIVERSE = ("DOTUSDT",)`
- **Gate constants**: lookback_bars=42, threshold_pct=8.0, enabled=True (mirror /019 verbatim)
- **OOS_CUTOFF_DATE = 2025-03-24** (UNCHANGED; sacred constant)
- **training_months = 24** (UNCHANGED; sacred constant)
- **Embargo**: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` (post-/058 FIX UNCHANGED)
- **`oof_persist_path`**: `data/v1_iter_v1-029_oof.parquet`
- **`params_persist_path`**: `data/v1_iter_v1-029_optuna_best_params.parquet` (carry-forward /021 infrastructure)
- **`feature_importance_path`**: `feature_importance_E_DOTUSDT.csv` (carry-forward /021 + /023 _post_dispatch_fi_strategies refactor)
- **Reports directory**: `reports-v1/iteration_v1-029/`

---

## Section 8 — Verdict Cell Determination Table

Pre-commit to verdict cells (mirror /028 format; 8 rows):

| Row | Condition | Verdict cell |
|---|---|---|
| 1 | F-AXIS #1 dispatch FAIL (non-DOT trades) | **TECHNICAL-FAILURE** (no verdict; redispatch) |
| 2 | F-AXIS #3 OOS fire-rate < 5% (UNDER-FIRE) | **INERT-NO-EFFECT** (verdict cap; F1 magnitude irrelevant) |
| 3 | F-AXIS #3 OOS fire-rate > 35% (OVER-KILL) AND F1 Δ < −0.20 | **NEGATIVE-INERT** (gate destroys value) |
| 4 | F-AXIS #5 OOS TP-exit count < 2 | **PROMISING-INERT** (verdict cap; F1 magnitude irrelevant) |
| 5 | F1 Δ ≥ +0.20 AND F-AXIS #3 ∈ [5%, 35%] AND F-AXIS #5 ≥ 2 AND F-AXIS #2 OOS ∈ [22, 55] | **PROMISING** (modal Path C outcome; bundle into /027-retry) |
| 6 | F1 Δ ∈ [+0.05, +0.20) AND F-AXIS #3 ∈ [5%, 35%] AND F-AXIS #5 ≥ 2 | **PROMISING-INERT** (mild lift; informational) |
| 7 | F1 Δ ∈ [−0.20, +0.05) | **INERT** (gate or cohort isolation no effect) |
| 8 | F1 Δ < −0.20 AND F-AXIS #3 ∈ [5%, 35%] | **NEGATIVE-CLEAN or NEGATIVE-CATASTROPHIC** (DOT FRAGILE-POSITIVE class collapses) |

**Modal expectation per LM Master**: Row 5 or Row 6 (PROMISING / PROMISING-INERT) at 50% combined probability.

---

## Section 9 — Test Suite Mandate (per `feedback_v1_defensive_check_must_be_tested.md`)

For QE Phase 6 implementation:

### 9.1 Required regression tests at `tests/test_lookahead_embargo.py` (4 mandated)

- Line 120: walk-forward train_end_ms < test_start_ms invariant
- Line 163: embargo_ms positive and applied to BOTH leading and trailing test boundary
- Line 232: triple-barrier σ_t uses past-only EWMA (no labeling-window contamination)
- Line 261: BTC-trend gate input uses BTC kline data with close_time < signal-time t (past-only via np.searchsorted right−1)

### 9.2 New tests at `tests/test_iteration_v1_029.py` (6+ required)

- `test_v1_iter029_universe_constant`: `V1_ITER029_UNIVERSE == ("DOTUSDT",)`
- `test_v1_iter029_dispatch_branch_pass`: `set(symbols) == set(V1_ITER029_UNIVERSE)` triggers Model E + gate path
- `test_v1_iter029_dispatch_branch_no_match`: full 5-symbol universe falls through to baseline dispatch (no /029 cross-contamination)
- `test_v1_iter029_btc_gate_constants`: lookback_bars=42, threshold_pct=8.0, enabled=True
- `test_v1_iter029_btc_gate_fire_at_threshold`: gate kills LONG when BTC 14d return < −8% (sample-instance unit test per /027 lesson — defensive checks MUST be tested with real instance, not just static code pattern)
- `test_v1_iter029_btc_gate_fire_at_positive_threshold`: gate kills SHORT when BTC 14d return > +8% (sample-instance unit test)
- `test_v1_iter029_btc_gate_pass_mild_regime`: gate passes trades when BTC 14d return ∈ [−8%, +8%]

### 9.3 ANY new hard-assert MUST include sample-instance unit test (the /027 lesson)

The /027 CONFIRMATION crashed at a hard-assert with `AttributeError: 'TradeResult' object has no attribute 'model_name'` — the defensive runtime check was itself defective. **Mandate**: every hard-assert added in /029 src/ MUST have a corresponding test that instantiates the real object and verifies the assert path. This includes any AssertionError or ValueError raise inside the dispatch logic.

---

## Path Forward (LM Master + Critic + QR convergence)

Cycle-4 EXPLORATION 2/10 — 8 EXPLORATIONs remain after /029. Pre-committed /030 axis = NEW feature family (regardless of /029 verdict) per LM Master §7 + cycle-4 cohort-isolation saturation.

If /029 PROMISING → /027-retry bundle composition expands to 4 specialists at CONFIRMATION (LINK + ETH+gate + LTC+atr_sl + DOT+gate); target OOS Sharpe +1.10 to +1.40 multi-seed mean.

If /029 INERT or NEGATIVE → /027-retry bundle stays 3 specialists; cycle-4 pivots to feature-family axis exclusively at /030+.

If /029 NEGATIVE-CATASTROPHIC → cohort-isolation axis CLOSED PERMANENTLY for v1 (3 NEG-CAT across /020 BTC + /022 LTC + /029 DOT); /030+ must pivot AWAY from per-cohort axes.

---

## Brief authoring complete.

**Authoring sign-off**: Quant Researcher; Phase 5 brief authored 2026-05-28; ready for Phase 5.5 gate dispatch.
