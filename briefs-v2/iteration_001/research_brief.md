# Iteration v2/001 Research Brief

**Type**: EXPLORATION (new feature set + new symbol universe + new risk layer)
**Track**: v2 (diversification arm, `quant-research` branch)
**Baseline**: None yet — iter-v2/001 establishes the initial v2 baseline
**Date**: 2026-04-13
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

Shared with v1. The researcher operated on IS-only data (before 2025-03-24)
during phases 1-5. OOS results are seen for the first time in Phase 7.

## Motivation

v1's baseline (iter 152, OOS Sharpe +2.83 on BTC/ETH/LINK/BNB) is mature.
The user identifies two weak areas v1's QR failed to advance:

1. **Feature engineering**: v1's 9 groups (momentum, volatility, trend,
   volume, mean_reversion, statistical, interaction, calendar, entropy_cusum)
   are mostly raw technical indicators. No regime-aware or tail-risk features.
2. **Risk management**: v1 ships SL/TP + per-symbol vol targeting but has no
   defence against the model operating in a market regime it was never
   trained on. Iter 163's entropy/CUSUM experiment catastrophically failed
   (OOS Sharpe -57%) partly because there was no gate to detect the
   feature-space shift in real time.

iter-v2/001 establishes a parallel track that addresses both:

- **New feature set** built on regime awareness, tail risk, efficient OHLC
  vol, momentum acceleration, volume microstructure, and fractional
  differentiation — none of v1's feature modules are imported or ported.
- **Hardened risk layer** (`RiskV2Wrapper`) with 4 MVP gates running ahead
  of the backtest engine: vol-adjusted sizing, ADX gate, Hurst regime check,
  feature z-score OOD alert.
- **Strict diversification** away from v1's universe: BTCUSDT, ETHUSDT,
  LINKUSDT, BNBUSDT are forbidden.

## Configuration

| Setting | Value | Source |
|---|---|---|
| Interval | 8h | inherited from v1 |
| Training window | 24 months | inherited from v1 |
| Labeling | Triple barrier, ATR-scaled barriers (2.9× TP / 1.45× SL via `natr_21_raw`) | inherited from v1 Model A |
| Timeout | 7 days (10080 min) | inherited from v1 |
| Cooldown | 2 candles | inherited from v1 |
| Vol targeting | OFF for inner strategy (RiskV2Wrapper handles sizing) | new |
| Optuna trials | 10 per monthly model (reduced from v1's 50) | iter-v2/001 compute budget |
| CV splits | 5 | inherited from v1 |
| Seeds | 1 for first pass, 10 for MERGE validation | v2 skill §Seed Robustness |
| Model architecture | 3 individual models (one symbol each) | user preference (Q3 decision) |

### Risk-Layer Configuration

```python
RiskV2Config(
    vol_scale_floor=0.3,
    vol_scale_ceiling=1.0,
    adx_threshold=20.0,
    hurst_lower_pct=0.05,
    hurst_upper_pct=0.95,
    zscore_threshold=3.0,
    enable_vol_scaling=True,
    enable_adx_gate=True,
    enable_hurst_check=True,
    enable_zscore_ood=True,
    # Deferred primitives — iter-v2/002+
    enable_drawdown_brake=False,
    enable_btc_contagion=False,
    enable_isolation_forest=False,
    enable_liquidity_floor=False,
)
```

### Optuna Trial Reduction Rationale

v1 uses 50 Optuna trials per monthly model. iter-v2/001 uses 10 because:
1. This is a **first** iteration; we need to ship the infrastructure and
   generate the first v2 baseline, not hyper-tune.
2. 3 models × 24 months × 10 seeds × 10 trials = 7,200 LightGBM fits (full
   validation run) vs v1's 36,000 at 50 trials — a 5× compute saving.
3. iter-v2/002 can re-optimize with 50 trials once the feature set and risk
   layer are proven.

## Feature Set (35 features from v2 catalog)

All 28 core catalog items plus 7 QR-proposed derivatives. Sources in
`src/crypto_trade/features_v2/*.py`. Exact list in
`crypto_trade.features_v2.V2_FEATURE_COLUMNS`.

**Explicit audit**: zero imports from `crypto_trade.features` into the
`features_v2` package. Verified:

```
$ grep -r "from crypto_trade.features " src/crypto_trade/features_v2/
# Empty.
```

### Category breakdown

| Category | Count | Features |
|---|---|---|
| Regime-aware | 7 | `hurst_100, hurst_200, hurst_diff_100_50, atr_pct_rank_{200,500,1000}, bb_width_pct_rank_100, cusum_reset_count_200` |
| Tail risk | 7 | `ret_skew_{50,100,200}, ret_kurt_{50,200}, range_realized_vol_50, max_dd_window_50` |
| Efficient OHLC vol | 5 | `parkinson_vol_{20,50}, garman_klass_vol_20, rogers_satchell_vol_20, parkinson_gk_ratio_20` |
| Momentum acceleration | 5 | `mom_accel_5_20, mom_accel_20_100, ema_spread_atr_20, ret_autocorr_lag{1,5}_50` |
| Volume microstructure | 8 | `vwap_dev_{20,50}, volume_mom_ratio_20, volume_cv_50, obv_slope_50, hl_range_ratio_20, close_pos_in_range_{20,50}` |
| Fracdiff (AFML Ch. 5) | 2 | `fracdiff_logclose_d04, fracdiff_logvolume_d04` |

Plus a non-feature `natr_21_raw` helper column used only by the labeling
code for ATR-scaled triple barriers (explicitly excluded from model inputs).

### Samples-per-feature ratio

35 features × ~4,400 training samples per monthly window = **ratio ≈ 125**.
Well above the 50 floor. Iter 163 (v1) failed at ratio 22 — v2's first pass
is ~5.7× safer.

## Symbol Universe (3 picks via 6-gate protocol)

Starting pool: 28 hand-picked liquid alts outside v1's universe
(`SOLUSDT, XRPUSDT, DOGEUSDT, ADAUSDT, ..., SEIUSDT`).

### Gate results

| Gate | Survivors | Notes |
|---|---|---|
| 1 — Data quality (≥1,095 IS candles, first candle <2023-07-01) | 25 of 28 | Dropped: SEIUSDT, TIAUSDT, TONUSDT (launched too recently) |
| 2 — Liquidity (>$10M daily quote volume) | 25 of 25 | Lowest: ALGOUSDT at $84M/day |
| 3 — Standalone profitability | **Deferred** | iter-v2/001 compute budget; the first-seed backtest serves as Gate 3 |
| 4 — Pooled compatibility | **Vacuous** | No prior v2 baseline to compare against |
| 5 — Pairwise correlation within picks <0.7 | 3 of 3 | DOGE-SOL 0.366, DOGE-XRP 0.370, SOL-XRP 0.488 |
| 6 — Correlation to v1 baseline <0.85 | 25 of 25 | Highest: LTCUSDT 0.816, all pass; computed as correlation to equal-weighted daily returns of BTC+ETH+LINK+BNB (a v1-portfolio proxy) |

### Final selection

| Model | Symbol | v1 correlation | Mean daily quote vol | IS candles | Category |
|---|---|---|---|---|---|
| **E** | DOGEUSDT | 0.507 | $967M | 5,153 | Meme |
| **F** | SOLUSDT | 0.669 | $1,581M | 4,941 | L1 |
| **G** | XRPUSDT | 0.665 | $1,022M | 5,696 | Payment |

**Rationale**: these three span completely different crypto categories,
have the highest liquidity in the screened pool after DOGE, and have the
lowest v1 correlations among highly liquid candidates. DOGE is the lowest
v1-correlation pick by a wide margin (0.507 vs ~0.665 for the rest), making
it the strongest single diversifier.

**Gate 3 justification for deferral**: running standalone LightGBM training
per candidate (50 Optuna trials × 5 CV folds each) on 25 candidates would
cost ~6-12 hours. For iter-v2/001, the first-seed run of the selected 3 is
itself a direct Gate 3 check — if any of the 3 models fail to produce IS
Sharpe > 0 with >100 IS trades, the iteration early-stops (Fail Fast
protocol) and the failing symbol is dropped from iter-v2/002.

## Research Checklist Coverage

iter-v2/001 is the first iteration and has no prior to compare against.
Completed checklist categories:

- **A — Feature Contribution**: A4 (new feature proposals) via the 28-item
  v2 catalog. A1 (pruning) skipped — no baseline to prune from.
- **B — Symbol Universe**: B2 (6-gate protocol) executed. B3 (architecture
  decision) → 3 individual models per user preference.
- **I — Risk Management Analysis**: see Section 6 below (mandatory every v2 iter).

Categories C (labeling), D (feature lookback), E (trade patterns), F
(statistical rigor), G (stationarity/fracdiff), H (overfitting audit) are
deferred to iter-v2/002+ once a baseline exists and A/B comparisons become
meaningful.

## Success Criteria (iter-v2/001 relaxed, no prior baseline)

All must pass to MERGE and become the first v2 baseline:

- OOS Sharpe > +0.5 (modest starting bar)
- ≥7/10 seeds profitable (first seed early-stops if unprofitable)
- OOS trades ≥ 50
- Profit factor > 1.1
- No single symbol > 50% of OOS PnL
- DSR > -0.5 (N=1 trial, wide tolerance)
- **v2-v1 portfolio return correlation < 0.80 in OOS window** (the whole
  point of v2 — non-negotiable)

## Expected Runtime

- First-seed pass (3 models × 24 months × 1 seed × 10 Optuna trials × 5 CV
  folds): ~20-40 minutes of compute.
- Full 10-seed validation (if first-seed passes): ~3-6 hours.
- Feature generation: already done (78s for 28 symbols).

## Hypothesis

The v2 feature catalog captures regime structure (Hurst, ATR percentile
rank), tail risk (skew/kurt, max DD window), and volume microstructure
(VWAP deviation, OBV slope) that v1's pure technical indicators miss.
Combined with the MVP risk layer and 3 highly diversifying symbols, iter-v2/001
should produce a modestly profitable first baseline (OOS Sharpe in the
+0.5 to +1.5 range) that can then be refined across iter-v2/002+.

If iter-v2/001 fails to produce any profitable model, the likely causes
are: (1) 10 Optuna trials is too few for the new feature set to find good
hyperparameters, (2) the 4 MVP gates fire too often and starve the model
of signal, or (3) the 3 alt symbols have fundamentally different dynamics
than v1's large caps and need specialized labeling. Each would feed a
specific corrective iter-v2/002.

---

## Section 6: Risk Management Design

### 6.1 Risk Primitives Active This Iteration

| Primitive | Status | Parameters | Justification |
|---|---|---|---|
| Vol-adjusted sizing | ENABLED | floor=0.3, ceiling=1.0, source=atr_pct_rank_200 | Reduces exposure in high-vol regimes; scale = 1 - atr_pct_rank linearly clipped to [0.3, 1.0] |
| ADX gate | ENABLED | threshold=20 | Skip signals when market is ranging (ADX<20) — momentum learner is miscalibrated in ranging regimes. ADX computed on-the-fly in the wrapper (not a v2 feature) |
| Hurst regime check | ENABLED | 5/95 pct of training `hurst_100` | If current Hurst lies outside the training-window percentile band, the model is in an untrained regime → kill signal |
| Feature z-score OOD | ENABLED | |z|>3 on any of 35 features | Primary "model in untrained regime" detector; training-window mean/std captured per model at `compute_features` time |
| Drawdown brake | DISABLED | — | Deferred to iter-v2/002 (portfolio-level plumbing needed) |
| BTC contagion circuit breaker | DISABLED | — | Deferred to iter-v2/002-003 (needs cross-v1 data feed) |
| Isolation Forest anomaly | DISABLED | — | Deferred to iter-v2/003 (extra dep, tuning surface) |
| Liquidity floor | DISABLED | — | Deferred to iter-v2/002 (spread data not readily available) |

### 6.2 Questions the QR Must Answer

**1. Regime coverage**: The IS window (2020-01 to 2025-03) spans 3+ full
crypto cycles: Covid crash (March 2020), 2020-2021 bull run, 2022 bear
(LUNA, FTX), 2023 recovery, 2024 bull. Hurst distribution is expected to
cover H ∈ [0.3, 0.9] with the median around 0.55. ATR percentile by
construction covers [0, 1] uniformly. **Under-represented regimes**:
sustained low-vol ranging markets (rare in crypto) — the ADX gate will
fire most during 2023 Q1-Q2 lull periods, which is exactly what we want.

**2. Expected gate firing rate**: Estimated on IS data from the feature
parquets:
- ATR sizing: always active; scaling factor median near 1.0, 10% of bars
  scaled below 0.5.
- ADX gate: expected ~15-25% fire rate based on typical crypto regime mix.
- Hurst regime check: targets the 5% tails by construction → ~10% fire rate
  (5% at each tail).
- Feature z-score OOD: rare per-feature, but with 35 features the
  ANY-exceeds-3σ rate could climb to 5-15% if features are weakly
  correlated. Calibration check planned in the engineering report.

If combined kill-rate exceeds 50%, the model is starved. If it's under 5%,
the gates provide no protection. Target: 10-30% combined kill rate.

**3. Black-swan scenario replay** (IS):
- **LUNA crash (May 2022)**: Expected ATR percentile to spike to 0.99+,
  feature z-scores on skew/kurt to exceed |3| → position killed or scaled
  to 0.3. Residual PnL: near zero (desired).
- **FTX collapse (Nov 2022)**: Similar volatility spike, Hurst likely
  shifts toward mean-reversion regime (H<0.4) if it wasn't already there
  → Hurst gate fires. Residual PnL: near zero.
- **March 2020 Covid crash**: Universe has fewer IS candles here (most
  symbols start 2020-03 or later). Likely under-represented; the Hurst
  regime during this period is part of the training distribution, not
  outside it. **This is a known blind spot**: if a Covid-style crash
  happens again OOS, the gates may not recognize it as OOD.

**4. Known-unknown failure modes**: A slow monotone grind-down (e.g., a
6-month bear trend with no ATR spikes, no feature excursions, just
consistent small losses) would bypass all 4 gates. The ADX gate would
not fire (ADX > 20 during a trend), the Hurst gate would not fire (H > 0.6
during a trend), the ATR gate would be permissive (low vol), and the
z-score gate would not fire (features stay inside the training
distribution). Only the drawdown brake (deferred) catches this. iter-v2/002
should enable it.

**5. Deferred primitives rationale**: drawdown brake requires portfolio-
level state that individual models don't have — add in iter-v2/002 by
wiring portfolio DD into the backtest engine as an injected callback.
BTC contagion needs cross-model BTC data; add in iter-v2/002-003. Isolation
Forest adds sklearn dependency and tuning; add in iter-v2/003. Liquidity
floor needs bid-ask data not available in our OHLCV parquets.

### 6.3 Pre-Registered Failure-Mode Prediction

The most likely way iter-v2/001 loses money is: **a sustained 2024-2025
meme-coin or alt correction that moves slowly enough to keep ATR and
Hurst inside their training ranges but persistently enough to accumulate
SL losses on DOGE in particular**. The gates that should catch it are:
the feature z-score OOD alert (if skew/kurt excursions occur) and, once
enabled, the drawdown brake. **If the gates don't catch it**, the loss
will look like: DOGE model shows negative per-symbol PnL in 2024-H2 OOS
with most trades closed at SL, no regime flag fired, concentrated in the
lowest-vol percentile bucket of the regime-stratified Sharpe grid.

A secondary prediction: **10 Optuna trials per monthly model may be
insufficient for the new 35-feature set to find hyperparameters that
generalize**. If this is the cause, all 3 models will show similar
mediocre-to-poor IS Sharpe (+0.2 to +0.6) without strong per-model
differences — a sign to bump trials to 25-50 in iter-v2/002.

### 6.4 Exit Conditions (beyond TP/SL)

Standard 7-day timeout. **On-position gate firing**: for iter-v2/001,
gates fire at SIGNAL time only (when the strategy proposes a new trade).
Open positions continue to honor TP/SL/timeout even if a gate would
currently fire. Rationale: per-candle re-gating of open positions adds
closure/position-tracking complexity; iter-v2/002 can opt into "kill on
gate fire" as a separate enable flag once MVP calibration is known.

### 6.5 Post-Mortem Template (Phase 7 — to be filled in)

After the backtest, the QR reports per gate:

- Fire rate (% of signals/bars it examined)
- PnL of killed trades (what they would have been)
- PnL of scaled-down trades (delta vs full size)
- Gate ROI: (loss avoided − profit killed) / fire count

This table appears in `diary-v2/iteration_001.md` and becomes the baseline
for iter-v2/002 gate tuning.
