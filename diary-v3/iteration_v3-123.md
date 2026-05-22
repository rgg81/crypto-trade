# iter-v3/123 — Cycle-7 slot 2 — EXPLORATION-NEGATIVE-catastrophic / cross-asset OHLCV axis CLOSED at 6th failure

**Date**: 2026-05-20
**Type**: EXPLORATION (cycle-7 slot 2 of 10; single-axis: replace `eth_ret_3d` with `eth_vs_sym_rv_50` as 15th feature; cross-asset OHLCV-derived sub-axis B1)
**Axis**: NEW cross-asset volatility-regime ratio feature `eth_vs_sym_rv_50 = eth_realized_vol_50 / range_realized_vol_50` (50-bar past-only rolling)
**Verdict**: EXPLORATION-NEGATIVE-catastrophic per Critic FINAL `9c35833`
**Classification**: NEGATIVE — IS Sharpe Δ −1.73 vs /121 multi-seed (threshold < −0.40); F5 C6-DISSOCIATION-PATTERN-RECURRENT secondary fire (LDO EDA rank 1/15 → production rank 11/15)
**BASELINE_V3.md**: UNCHANGED (/121 canonical at `v0.v3-121`)

## 1. What was done

QR-led EDA at `dbc2993` selected sub-axis B1 = `eth_realized_vol_50 / sym_realized_vol_50` per /122 Critic Rec 2 (continue cycle-7 axis-1 cross-asset menu with structurally different sub-axis after `eth_ret_3d` NEGATIVE-INERT at /122). Hypothesis: cross-asset volatility-regime divergence as a directional signal — structurally orthogonal to the directional momentum signal /122 found INERT, with predicted pairwise |IC| with vwap_dev_20 ≤ 0.25 and with regime_momentum_signed_5d ≤ 0.30 (both clear the new < 0.40 gate established at /122 Critic Rec 1).

Commit chain: EDA `dbc2993` → brief `aa0b29a` → setup `32306c3` (replace `eth_ret_3d` with `eth_vs_sym_rv_50` in `V3_FEATURE_COLUMNS_TOP_N`, count stays 15) → engineering `89a1acf` → Critic FINAL `9c35833`. Wall-clock 0.69h (within 2h EXPLORATION cap).

Files changed: `src/crypto_trade/features_v3/cross_btc_v3.py` (compute `eth_vs_sym_rv_50` per symbol from past-only 50-bar rolling std of ETH/sym log returns); `src/crypto_trade/features_v3/__init__.py` (`"eth_ret_3d"` → `"eth_vs_sym_rv_50"`); `run_baseline_v3.py` (ITERATION_LABEL "v3-123", pre-flight inverted: ABSENT `eth_ret_3d`, PRESENT `eth_vs_sym_rv_50`); tests `test_eth_vs_sym_rv_50_past_only` + `test_eth_vs_sym_rv_50_integration` added.

No labeling, risk-gate, walk-forward, or ensemble changes. /116 no_confirm STAYS ENABLED; /119 C6 STAYS BANNED.

## 2. Results

| Metric | /121 BASELINE (multi-seed) | /123 (single-seed EXPLORATION) | Δ vs /121 |
|---|---:|---:|---:|
| IS monthly Sharpe | +1.3108 | **−0.4155** | **−1.73** |
| OOS monthly Sharpe | +0.9682 | **+1.7536** | **+0.79** |
| IS MaxDD | 26.38% | 56.32% | +29.94pp |
| OOS MaxDD | 25.70% | 19.21% | −6.49pp |
| IS trades | (multi-seed) | 181 | — |
| OOS trades | (multi-seed) | 91 | — |
| OOS PF | (multi-seed) | 1.574 | — |

vs /120 all-time bundle record (+1.6946 OOS): /123 OOS Sharpe +1.7536 EXCEEDS by +0.0590 — nominally the highest OOS monthly Sharpe in v3 history, achieved while IS is the lowest in v3 history at −0.4155. The Critic engineering report Section 11 explicit it's regime-classifier artifact, NOT signal.

Per-symbol IS attribution (all 3 symbols IS-negative — UNIVERSAL collapse, not isolated to EDA-predicted carrier LDO):
- BCHUSDT: 89 IS trades, 34.8% WR, net_pnl −1.06 (Δ vs /121: −120.22)
- LDOUSDT: 9 IS trades, 22.2% WR, net_pnl −21.53 (Δ vs /121: −31.06)
- TRXUSDT: 83 IS trades, 30.1% WR, net_pnl −15.52 (Δ vs /121: −22.83)

Per-symbol OOS attribution:
- BCHUSDT: 35 OOS trades, 54.3% WR, weighted_pnl +56.67 (108.32% concentration — single OOS carrier)
- LDOUSDT: 14 OOS trades, 28.6% WR, weighted_pnl −5.70
- TRXUSDT: 42 OOS trades, 33.3% WR, weighted_pnl +1.34

## 3. Mechanism: cross-asset OHLCV dissociation — 6th consecutive failure

The cross-asset OHLCV-derived axis closure is now mechanically explained across SIX iterations spanning THREE feature classes:

| # | Iter | Feature | Class | Failure mode |
|---|------|---------|-------|-------------|
| 1 | /082 | funding_rate_zscore_30 | crypto-native sentiment | INERT-by-importance + OOS-spike artifact |
| 2 | /085 | funding_rate_zscore_30 (higher Optuna budget retry) | crypto-native sentiment | Same as #1 — failure mechanism robust to budget |
| 3 | /086 | basis_zscore_30 (cross-exchange) | crypto-native sentiment | INERT-by-importance + OOS-spike artifact |
| 4 | /119 C6 | ret_5d × sign(taker_buy_imbalance_20) | engineered Category-2 composed | PROMISING-FEATURE-MECHANICAL (sister-cannibalization; F3-DROP at /120) |
| 5 | /122 | eth_ret_3d | OFF-THE-SHELF cross-asset primitive | NEGATIVE-INERT (rank 14-15/15; suspicious-OOS-dominant) |
| 6 | **/123** | **eth_vs_sym_rv_50** | **OFF-THE-SHELF cross-asset volatility-regime ratio** | **NEGATIVE-catastrophic — sign-flipped IS/OOS dissociation** |

**The pattern, formalized**: in the BCH/LDO/TRX 8h universe with /121's 14-feature stack, cross-asset OHLCV-derived primitives either become INERT (rank 14-15/15 — the model can't separate them from the 14 anchor features) OR become harmful regime classifiers with diverging IS/OOS PnL distributions (suspicious-OOS-dominant pattern). Either failure mode is structural, not budget-dependent (/082→/085 retest at higher budget reproduced).

**Why this iteration's IS collapse is universal, not LDO-localized**: /123 is the first cross-asset axis where the IS collapse cascaded across ALL THREE symbols (BCH −1.06, LDO −21.53, TRX −15.52). At /122 the failure was IS-aggregate-NEGATIVE but BCH IS PnL was only −64.62 (single-symbol carrier with TRX +32.45 partially offsetting); at /123 the ratio feature broadcasts the cross-asset regime signal symmetrically into all 3 symbols' label distribution, simultaneously degrading the model's per-symbol predictions. The OOS +1.75 lift is a regime-classifier artifact — the OOS window happens to align with a vol-ratio regime that produces a tradeable directional bias by chance, NOT a structurally exploitable signal.

**The cycle-7 cross-asset OHLCV-derived axis is now exhausted**. Six iterations, three feature classes, two failure modes — all NEGATIVE or PROMISING-FEATURE-MECHANICAL (which itself F3-DROPs at multi-seed). Cross-asset axes at /124+ MUST use structurally different primitive classes: on-chain (Glassnode), liquidations data, non-Binance basis. Pure OHLCV-derived ETH/BTC primitives at any window or transform are CONSIDERED EXHAUSTED.

## 4. Critic verdict summary

OVERALL = **EXPLORATION-NEGATIVE-catastrophic**. Zero clarifications raised (catastrophic verdict unambiguous). Eight checks PASS:

- **Check 1 (look-ahead)**: PASS. `cross_btc_v3.py:57-88` past-only by construction; canonical `rolling(50, min_periods=50).std()` on 1-bar ETH log returns; merge `on="open_time", how="left"`. OOS BCH WR 60% spike is vol-regime classification artifact, NOT look-ahead.
- **Check 2 (embargo)**: PASS. REQUIRED_GAP=66 unchanged. Walk-forward POST-FIX `e149e9d` intact.
- **Check 3 (multiple-testing)**: INFORMATIONAL at EXPLORATION. PBO=0.1042 PASS, PSR=1.0 PASS, frac_pos=0.6444 PASS. DSR=0.0 degenerate because IS Sharpe negative (mathematically correct, not defect).
- **Check 4 (IC)**: PASS. Production IC matrix CONFIRMS /122 Critic Rec 1 strict pairwise gate: B1 vs vwap_dev_20 = 0.0567 (7.1× safety margin); B1 vs regime_momentum_signed_5d = −0.0177 (22.6× margin). Joint R²=0.39 < 0.70. B1 vs range_realized_vol_50 = −0.5353 is structural by denominator-sharing (carve-out adjudicated in brief Section 2.2).
- **Check 5 (ADF)**: PASS. All p<0.05 at final IS month.
- **Check 6 (Pareto)**: N/A (single-seed EXPLORATION).
- **Check 7 (reproducibility)**: PASS. ITERATION_LABEL=v3-123 verified; explicit `feature_columns=_feature_columns`; pre-flight assertions PASS; 2 OOS trade-level spot checks reproduce math.
- **Check 8 (alignment)**: PASS. Brief Section 3.5 5-file manifest exactly implemented. No scope creep.

## 5. PATH classification

**NEGATIVE-catastrophic** per Section 8 first-match. The IS Sharpe Δ −1.73 vs /121 multi-seed deeply violates the < −0.40 catastrophic-IS-collapse threshold; combined with the F5 C6-DISSOCIATION-PATTERN-RECURRENT secondary fire (LDO EDA rank 1/15 → production rank 11/15 — the EDA importance predicted prediction completely inverted at production), the verdict is mechanically unambiguous.

The OOS +1.75 nominal lift does NOT promote this to PROMISING-SUSPICIOUS — the IS catastrophic collapse (lowest IS in v3 history) is the dominant signal. Critic engineering report Section 11 explicit: regime-classifier artifact, not exploitable edge.

**The PROMISING-FEATURE-MECHANICAL classification is NOT applicable here** because diagnostic condition (c) FAILS at the per-symbol IS PnL Δ leg (all 3 symbols IS-negative — broad-based COLLAPSE, not broad-based POSITIVE Δ). Per `feedback_v3_promising_feature_mechanical.md` RECURRENCE NOTE classification boundary, "broad-based-IS-collapse" is the structural antonym of "broad-based-positive-IS-Δ".

## 6. Hypothesis check

Brief Section 4 NEGATIVE-band predictions were calibrated against /122's pattern, NOT against an even-more-catastrophic outcome. The /123 IS Δ −1.73 exceeded any pre-registered envelope. Future cross-asset axes (if any) should pre-register IS Δ band [−2.00, +0.50] given the demonstrated tail risk in this feature class.

## 7. BASELINE_V3.md status

UNCHANGED — /121 stays canonical at `v0.v3-121` (IS +1.3108 / OOS +0.9682).

## 8. Critic Recommendations carried forward

1. **Cycle-7 cross-asset OHLCV axis CLOSED at 6th failure** (per Critic Rec 1). Next cross-asset axis MUST use structurally different primitive class — on-chain (Glassnode/CryptoQuant — Exchange Whale Ratio, MVRV-Z, NUPL/SOPR, CDD/Dormancy, active addresses), liquidations data, non-Binance basis — with external-feed access decision adjudicated upfront. Pure OHLCV-derived ETH/BTC primitives EXHAUSTED.

2. **EDA single-window importance NOT reliable for cross-asset** (per Critic Rec 2). For future cross-asset axes, EDA Section 2 MUST include rolling-window T5 importance test across ≥ 3 IS endpoint slices (e.g., 2023-Q1, 2024-Q1, 2025-Q1) and report rank stability range. Feature predicted top-1 at one window and bottom-third at another must trigger F-falsifier on rank instability.

3. **Pivot /124 axis AWAY from cross-asset entirely** (per Critic Rec 3). /124 should select from:
   - **Longer-cadence labels axis-3** (1d or 3d horizon-extended triple-barrier — currently 21-bar 8h ≈ 7-day horizon; doubling to 14d most-deferred high-priority axis in cycle 7) — given /068's NEGATIVE-catastrophic 42-candle timeout precedent, axis design must learn from /068.
   - OR creative out-of-box (per-symbol drawdown brake at closed-loop simulator layer with deadlock-impossibility proof per `feedback_v3_oracle_eda_validity.md`).

The OOS +1.75 headline should NOT seduce QR into cross-asset retry.

## 9. Next Iteration Ideas — cycle-7 progress

Cycle-7 progress: 2/10 EXPLORATIONs done.

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /122 | cross-asset axis-1 sub-axis A4 (eth_ret_3d) | NEGATIVE-INERT |
| **#2** | **/123** | **cross-asset axis-1 sub-axis B1 (eth_vs_sym_rv_50)** | **NEGATIVE-catastrophic — cross-asset OHLCV AXIS CLOSED at 6th failure** |
| #3 | /124 | TBD per Critic Rec 3 — longer-cadence labels OR creative out-of-box | TBD |
| #4-#10 | /125-/131 | TBD | TBD |
| CONFIRMATION | /132 | Anchors against /121 multi-seed baseline | TBD |

**iter-v3/124 axis candidates** (per Critic Rec 3 + cycle-7 structural-reorientation mandate):

- **Longer-cadence labels axis-3 (RECOMMENDED)**: pivot to NON-FEATURE TRAIN-TIME axis. Sub-options:
  - 42-candle timeout — **REJECTED a priori**: /068's NEGATIVE-catastrophic precedent. Same axis at same scale.
  - 63-candle timeout (~21-day, 3× current) — open candidate. Embargo cost: REQUIRED_GAP = (63+1)*3 = 192 (vs current 66, vs /068's 129). Sample-uniqueness loss likely worse than /068's. Must carry coherent +2/−1 ATR multiplier scaling AND falsifier on training-sample loss.
  - 84-candle timeout (~28-day, 4× current) — open candidate. REQUIRED_GAP = (84+1)*3 = 255. Most extreme sample-uniqueness loss.
- **Creative out-of-box (alternative)**: per-symbol drawdown brake at closed-loop simulator layer with deadlock-impossibility proof per `feedback_v3_oracle_eda_validity.md`.
- **Forbidden**: any cross-asset OHLCV-derived axis (6 failures, exhausted); per-symbol customizations (closed at /039 NEGATIVE); knob-tuning of saturated axes (ADX, z-score, BTC band); 42-candle timeout retry (/068 precedent).
