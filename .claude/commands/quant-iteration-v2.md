---
name: quant-iteration-v2
description: "Quant research/engineering iteration workflow for the crypto-trade LightGBM strategy — v2 TRACK (diversification arm, separate baseline). Use this skill whenever the user mentions: v2 iteration, quant-iteration-v2, iteration-v2, BASELINE_V2, briefs-v2, diary-v2, reports-v2, ITERATION_PLAN_8H_V2, run_baseline_v2, v2 research brief, v2 diary, v2 merge decision, v2 baseline comparison, risk management v2, regime detection v2, Hurst exponent feature, ATR percentile rank, feature z-score OOD, DSR, deflated Sharpe, CPCV, PBO, diversification track, quant-research branch iteration, or 'v2 baseline'. Also trigger when the user says 'start v2 iteration', 'run v2 phase', 'evaluate v2 reports', 'write v2 diary', or 'v2 merge decision'."
---

# Quant Iteration v2 Skill — Diversification Arm

## Mission

v1 (the `quant-iteration` skill, branch `main`, baseline v0.152) has produced
a mature 4-symbol portfolio (BTC+ETH pooled, LINK solo, BNB solo) with
OOS Sharpe +2.83 and MaxDD 21.81% on 8h candles. It is production-ready.

**v2 is different.** v2 exists for one reason: **diversification**. The
combined portfolio we ultimately want to run (v1 + v2) must have lower
correlation, better tail behavior, and higher risk-adjusted returns than
v1 alone. That only happens if v2 is **genuinely different** from v1 — in
symbols, in features, and in risk posture.

If v2 rediscovers v1's universe, v1's features, or v1's risk regime, it has
failed at its only job. Iterations that blur the distinction are a waste of
compute. Every v2 iteration is structurally a diversification iteration.

Three weak areas of v1 this skill specifically addresses:

1. **Feature engineering** — v1's QR rarely proposed genuinely novel features.
   v2's first iteration builds a totally new feature set around regime
   awareness, tail risk, and efficient volatility estimators — no RSI/MACD
   retreads, no reuse of v1's nine feature modules.

2. **Risk management** — v1 ships SL/TP, ATR barriers, cooldown, and per-symbol
   vol targeting. It does NOT ship a defence against the model running in a
   market regime it was never trained on. v2 bakes that defence in from day
   one via a `RiskV2Wrapper` around the strategy — model-agnostic, implemented
   as gates that kill signals when the current market is out-of-distribution
   vs the training window.

3. **Validation rigor** — v1 stopped at 10-seed ensembles + profit thresholds.
   v2 adds Deflated Sharpe Ratio and regime-stratified OOS Sharpe in iter-v2/001,
   and phases in CPCV (iter-v2/002) and PBO (iter-v2/003).

Crypto markets are still the most inefficient markets on earth. Our edge is
still systematic patience on 8h candles. The philosophy of v1 — no p-hacking,
no overfitting, no self-deception — is inherited verbatim. v2 changes what we
look at, not how honestly we look.

---

## Relationship to v1

v2 and v1 are **siblings**, not parent/child. They share infrastructure but
diverge on the things that matter for diversification.

### Shared (inherited from v1, never changes in v2)

| Thing | Shared? | Why |
|---|---|---|
| `OOS_CUTOFF_DATE = 2025-03-24` | Yes, immutable | Researcher-overfitting defence must be global |
| 8h candles | Yes | Same philosophy: slow enough to ignore microstructure |
| Backtest engine (`src/crypto_trade/backtest.py`) | Yes, unchanged | Proven in 163 iterations |
| Labeling (`labeling.py`): triple-barrier + ATR barriers + sample uniqueness | Yes | AFML Ch. 4 foundations |
| Walk-forward (`walk_forward.py`): monthly splits, 24-mo training window | Yes | Same harness |
| `LightGbmStrategy` | Yes, wrapped (not replaced) by `RiskV2Wrapper` | ML code is fine; the gap is the risk layer |
| `TimeSeriesSplit(gap=...)` for label leakage | Yes | Same formula: `gap = (timeout_candles + 1) * n_symbols` |
| NO-CHEATING rules | Yes | Non-negotiable |
| Seed robustness discipline | Single-seed with v1-style 5-seed internal ensemble (outer-seed sweeps are vacuous — see "Seed Robustness Validation" §) | |
| Exploration/Exploitation 70/30 | Yes | |
| QR/QE role split | Yes | |
| 4-commit discipline (code/brief/engineering/diary) | Yes | |

### Diverged (v2 is different by design)

| Axis | v1 | v2 |
|---|---|---|
| Symbol universe | BTC, ETH, LINK, LTC, DOT (v0.186 universe — A pooled BTC+ETH, C=LINK, D=LTC, E=DOT) | Everything ELSE on Binance USDT perps |
| Feature code | `src/crypto_trade/features/*` (9 groups) | `src/crypto_trade/features_v2/*` (6 modules, hard-isolated) |
| Feature parquets | `data/features/` | `data/features_v2/` |
| Feature families | momentum, volatility, trend, volume, mean_reversion, statistical, interaction, calendar, entropy_cusum, cross_asset | regime, tail_risk, price_efficient_vol, momentum_accel, volume_micro, fracdiff |
| Risk layer | SL/TP/ATR/cooldown/vol-targeting + R1 consecutive-SL cooldown + R2 drawdown-triggered position scaling + R3 OOD Mahalanobis (merged from main 2026-04-24) | v1 + `RiskV2Wrapper` (regime gates, feature z-score OOD) |
| Validation | walk-forward, profit thresholds, Sharpe > 1.0 merge floor, Gate-3 evidence rule | v1 + DSR (iter 001), CPCV (iter 002), PBO (iter 003) |
| Git branch | `main` ← `iteration/NNN` | `quant-research` ← `iteration-v2/NNN` |
| Baseline file | `BASELINE.md` | `BASELINE_V2.md` |
| Iteration artifacts | `briefs/`, `diary/`, `reports/` | `briefs-v2/`, `diary-v2/`, `reports-v2/` |
| Tag format | `v0.NNN` | `v0.v2-NNN` |

> **OOD overlap (merged 2026-04-24):** v2's feature z-score gate in
> `RiskV2Wrapper` and v1's R3 Mahalanobis gate inside `LightGbmStrategy`
> target the same failure class ("model running in an untrained regime")
> via different statistics. v2 keeps `ood_enabled=False` on its inner
> `LightGbmStrategy` construction by default. Adopting R3 in v2 (replacing
> or supplementing the z-score gate) is an explicit open iter-v2/072+
> decision — measure before switching.

### The eventual combined portfolio

Once both baselines are stable, a new runner on `main` — `run_portfolio_combined.py` —
will load v1's `LightGbmStrategy` models AND v2's `RiskV2Wrapper`-wrapped
models, concatenate their trades, and report combined Sharpe / MaxDD. The
combined Sharpe is the real metric of interest. That is WHY v2 exists. Every
v2 iteration should ask: "does this advance the combined-portfolio goal, or
does it just add another BTC/ETH lookalike?"

---

## Before You Start

Read these before touching anything:

1. `BASELINE_V2.md` (v2 baseline, NOT `BASELINE.md`)
2. The last diary in `diary-v2/` for "Next Iteration Ideas"
3. `ITERATION_PLAN_8H_V2.md`

### Default Flow: Full Autopilot

When this skill is triggered, **do NOT ask which role to play or whether to
proceed**. Default behavior (same as v1):

1. Read the last v2 diary's "Next Iteration Ideas" and `BASELINE_V2.md`
2. Determine the next v2 iteration number (v2 numbering is independent — v2 starts at 001)
3. Run the full flow: QR Phases 1-5 → QE Phase 6 → QR Phases 7-8
4. **After completing Phase 8 (diary + commit), immediately start the next iteration** —
   go back to step 1 with the new diary's "Next Iteration Ideas"
5. Keep looping iterations until the user intervenes or context runs out
6. Only pause if there's an actual blocker (ambiguous brief, unexpected error,
   decision that genuinely requires user input)

The user can override by specifying a role (e.g., "be the QR") or a phase
(e.g., "run Phase 6"). Otherwise, go.

## NO CHEATING — ABSOLUTE RULES

All of v1's NO-CHEATING rules apply verbatim to v2, plus one extra:

- **NEVER change `start_time`** to skip bad IS months.
- **NEVER cherry-pick date ranges** to make IS or OOS look better.
- **NEVER post-hoc filter trades** from the results to improve metrics.
- **NEVER tune parameters on OOS data** (the researcher sees OOS only in Phase 7).
- **NEVER allow labels to leak across CV fold boundaries.** The `gap` parameter
  in `TimeSeriesSplit` MUST be set correctly: `gap = (timeout_candles + 1) * n_symbols`.
- **NEVER allow labels to leak from live/prediction data to training data.**
- **NEVER import from `crypto_trade.features` in v2 code.** v2's feature
  package is `crypto_trade.features_v2`. The first-iteration hard rule (below)
  forbids any reuse of v1's feature modules. The QE must `grep -r
  "from crypto_trade.features " src/crypto_trade/features_v2/` on every
  v2 commit and reject if non-empty.
- **NEVER trade v1's baseline symbols from v2.** BTC, ETH, LINK, BNB belong
  to v1. v2 runners must assert `set(cfg.symbols).isdisjoint(V2_EXCLUDED_SYMBOLS)`
  at startup.
- **NEVER pass `feature_columns=None` to `LightGbmStrategy`.** Auto-discovery
  reads parquet schema order, and parquet column order depends on how
  `generate_features(df, groups=…)` was invoked (which groups list, what
  insertion order). That means the trained model depends on a parquet layout
  that is effectively an implementation detail — different parquet
  regeneration paths can silently produce differently-ordered parquets and
  therefore different models. See the v1 iter-152 post-mortem
  (`analysis_v1_baseline_battletest.md`) for the concrete failure: +2.83 OOS
  Sharpe became unreproducible because Apr 5 auto-discovery returned a
  column order that today's parquet regeneration cannot recreate. Every v2
  runner MUST pass an explicit, fixed-order `feature_columns=list(V2_FEATURE_COLUMNS)`.

To improve IS Sharpe: improve the STRATEGY (features, model, risk layer) —
not the measurement window.

---

## THE MOST IMPORTANT RULE: IS/OOS Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

**Shared with v1.** The split exists to prevent **researcher overfitting** —
not model leakage. The walk-forward backtest already prevents model-level
leakage by training only on past data each month.

### What the split means:

- The **Quant Researcher** uses ONLY IS data (before 2025-03-24) during
  Phases 1-5 (design). This prevents the researcher from unconsciously tuning
  features, labeling, parameters to fit recent patterns.
- The **walk-forward backtest runs on ALL data** (IS + OOS) as one continuous
  process.
- The **reporting layer** splits trade results at `OOS_CUTOFF_DATE` into
  `in_sample/` and `out_of_sample/` report directories plus a `comparison.csv`
  with OOS/IS ratios.
- The **Quant Researcher** sees OOS results for the FIRST time in Phase 7.

This constant lives in `src/crypto_trade/config.py` and is shared with v1.
DO NOT duplicate it.

## Two Roles

You operate as EITHER the Quant Researcher (QR) OR the Quant Engineer (QE)
for each phase. In autopilot mode (default), you switch roles automatically
between phases — QR for phases 1-5 and 7-8, QE for phase 6.

### Quant Researcher (QR)
- Owns: data analysis, feature design, symbol selection, risk-layer design,
  evaluation, diary
- Produces: research briefs, diary entries, evaluation decisions
- Does NOT: write production code in `src/`. Uses notebooks and analysis
  scripts only
- DATA ACCESS: IS data only during Phases 1-5. Sees OOS reports only in Phase 7

### Quant Engineer (QE)
- Owns: production Python code, feature implementations in `features_v2/`,
  `RiskV2Wrapper` internals, backtest wiring, report generation
- Produces: implementation in `src/crypto_trade/features_v2/`,
  `src/crypto_trade/strategies/ml/risk_v2.py`, `run_baseline_v2.py`,
  engineering reports, backtest reports
- Does NOT: make research decisions. If the research brief is ambiguous, stop
  and ask
- BACKTEST: runs walk-forward on full dataset, then splits reports at
  `OOS_CUTOFF_DATE`

---

## Symbol Exclusion Rules — HARD TABLE

v2 runners MUST exclude the following symbols. They are v1's baseline and
trading them from v2 would double-count exposure in the combined portfolio.

| Symbol | v1 Role | v2 Allowed? |
|---|---|---|
| BTCUSDT | Model A | **No** |
| ETHUSDT | Model A | **No** |
| LINKUSDT | Model C | **No** |
| BNBUSDT | Model D | **No** |

### Enforcement

The canonical constant lives at the top of `run_baseline_v2.py`:

```python
V2_EXCLUDED_SYMBOLS: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "BNBUSDT")
```

Every v2 runner MUST:

```python
symbols = select_symbols(
    features_dir="data/features_v2",
    interval="8h",
    min_is_candles=1095,
    max_start_date="2023-07-01",
    exclude=V2_EXCLUDED_SYMBOLS,
)
assert set(cfg.symbols).isdisjoint(V2_EXCLUDED_SYMBOLS), (
    f"v2 runner cannot trade v1 symbols: "
    f"{set(cfg.symbols) & set(V2_EXCLUDED_SYMBOLS)}"
)
```

Adding ANY symbol from `V2_EXCLUDED_SYMBOLS` to a v2 iteration requires
**explicit user approval** — not a routine decision.

---

## First Iteration Hard Rule — NEW FEATURE SET

**iter-v2/001 MUST construct a completely new feature set.** The following
v1 feature modules are OFF LIMITS — you may NOT import them, copy their math,
rename them, or "port" them to v2:

- `crypto_trade.features.momentum`
- `crypto_trade.features.volatility`
- `crypto_trade.features.trend`
- `crypto_trade.features.volume`
- `crypto_trade.features.mean_reversion`
- `crypto_trade.features.statistical`
- `crypto_trade.features.interaction`
- `crypto_trade.features.calendar`
- `crypto_trade.features.entropy_cusum`
- (plus the ad-hoc `cross_asset` post-processing)

You may borrow the *category* of a signal (e.g., "momentum") only via a new
implementation with different math — v1 ships raw RSI/MACD/ROC; v2 uses
momentum acceleration and Hurst regime. **Concept overlap is fine;
implementation overlap is forbidden.**

**Explicitly forbidden for iter-v2/001**:
- RSI, MACD, Stochastic (standard bounded oscillators)
- Raw SMA, raw EMA (non-normalized moving averages)
- Raw ATR (use the **percentile rank** of ATR instead)
- Raw Bollinger Band levels/position (use the **percentile rank** of BB width instead)
- Raw volume, raw OBV (use **slope** or **ratio** transforms)
- Calendar features (hour_of_day, day_of_week)
- Interaction products in v1's form (RSI×ADX, RSI×NATR)
- Shannon entropy in v1's `entropy_cusum` form
- CUSUM binary break flags in v1's form (v2 uses **reset-count** rate)

The pre-commit audit (manual, but mandatory):

```bash
grep -r "from crypto_trade.features " src/crypto_trade/features_v2/
# Must return empty. If not, reject the commit.
```

### Subsequent v2 iterations

From iter-v2/002 onward, the hard rule relaxes. QR may:
- Add or prune features within `features_v2/`
- Re-examine a v1 concept (e.g., ADX) ONLY if v1's `trend.py` does not already
  ship it AND the QR documents why it belongs in v2's feature set
- NEVER import from `crypto_trade.features` (this rule is permanent)

---

## v2 Feature Catalog — 28 Core Items

Organized by **purpose**, not by v1's group names. iter-v2/001 picks 30-40
features from this list (28 core + up to 12 QR-proposed derivatives).

### A. Regime-aware (module: `features_v2/regime.py`)

1. `hurst_100` — Rolling 100-candle Hurst exponent via rescaled-range (R/S).
   H>0.6 trending, H<0.4 mean-reverting, H≈0.5 random walk. Scale-invariant.
   Stationary by construction. Compute cost: moderate (linear regression per bar).
2. `hurst_200` — Longer-horizon variant. Useful for detecting slower regime shifts.
3. `hurst_diff_100_50` — Difference between 100-bar and 50-bar Hurst. Detects
   regime **transitions**, which are the real alpha signal.
4. `atr_pct_rank_200` — Rolling percentile of current ATR vs last 200 candles.
   0-1 scale. Scale-invariant. Stationary.
5. `atr_pct_rank_500` — Middle horizon (500 × 8h ≈ 166 days).
6. `atr_pct_rank_1000` — Long-horizon context (1000 × 8h ≈ 333 days).
7. `bb_width_pct_rank_100` — Bollinger Band width as a percentile of its own
   history (squeeze detector). Uses BB only as an intermediate; the feature
   is the rank, not the level — so no v1 overlap.
8. `cusum_reset_count_200` — Number of CUSUM structural-break resets in the
   last 200 candles, normalized by window size. **Different from v1**:
   v1's `cusum_break_5` is a binary flag; v2's is a reset-rate count.

### B. Tail risk / black-swan proximity (module: `features_v2/tail_risk.py`)

9. `ret_skew_50` — Rolling 50-candle skewness of log returns. Negative skew =
   more frequent large downside moves. Stationary.
10. `ret_skew_100` — Middle horizon.
11. `ret_skew_200` — Long horizon.
12. `ret_kurt_50` — Rolling 50-candle excess kurtosis. High kurt = fatter
    tails = higher black-swan risk. Stationary.
13. `ret_kurt_200` — Long horizon.
14. `range_realized_vol_50` — Realized vol from rolling high-low range
    (Garman-Klass intermediate). Stationary.
15. `max_dd_window_50` — Rolling 50-candle max drawdown of close, expressed
    as a percentage. Scale-invariant.

### C. Efficient OHLC volatility estimators (module: `features_v2/price_efficient_vol.py`)

16. `parkinson_vol_20` — Parkinson estimator (high/low based). ~5x more
    sample-efficient than close-to-close std dev.
17. `parkinson_vol_50` — Longer horizon.
18. `garman_klass_vol_20` — Garman-Klass estimator (OHLC). Most efficient
    under standard assumptions.
19. `rogers_satchell_vol_20` — Rogers-Satchell estimator, drift-adjusted.
    Useful on trending assets where GK can over/underestimate.
20. `parkinson_gk_ratio_20` — Parkinson / Garman-Klass ratio. Captures
    intrabar vs full-bar vol mismatch — a subtle microstructure signal.

### D. Momentum acceleration / trend structure (module: `features_v2/momentum_accel.py`)

21. `mom_accel_5_20` — `(momentum_5 - momentum_20) / momentum_20`. Momentum
    acceleration vs baseline momentum. Regime-aware trend strength.
22. `mom_accel_20_100` — Longer horizon comparison.
23. `ema_spread_atr_20` — `(EMA_10 - EMA_50) / ATR_20`. Trend strength
    normalized by volatility. Scale-invariant. **Not a v1 overlap** because
    v1's EMA features are raw levels; v2's is a vol-normalized spread.
24. `ret_autocorr_lag1_50` — 50-bar lag-1 autocorrelation of returns.
    Positive = momentum regime; negative = mean-reversion regime. Stationary.
25. `ret_autocorr_lag5_50` — Lag-5 for comparison (medium-frequency structure).

### E. Volume microstructure (module: `features_v2/volume_micro.py`)

26. `vwap_dev_20` — `(close - VWAP_20) / ATR_20`. Distance from fair value
    in volatility units. Scale-invariant.
27. `vwap_dev_50` — Longer horizon.
28. `volume_mom_ratio_20` — `volume_10_mean / volume_50_mean`. Scale-invariant.
29. `volume_cv_50` — `std(volume, 50) / mean(volume, 50)`. Activity consistency.
30. `obv_slope_50` — Linear regression slope of OBV over 50 bars, normalized
    by mean OBV (dimensionless).
31. `hl_range_ratio_20` — `(high - low) / rolling_mean(high - low, 20)`.
    Intrabar dispersion relative to norm. Stationary.
32. `close_pos_in_range_20` — `(close - low_20) / (high_20 - low_20)`. 0=at
    low (bearish), 1=at high (bullish).
33. `close_pos_in_range_50` — Longer horizon.

### F. Fractional differentiation (module: `features_v2/fracdiff_v2.py`)

34. `fracdiff_logclose_d04` — Fractionally differentiated log close (AFML Ch. 5).
    Fixed window=100. `d` chosen per symbol as minimum `d` that gives ADF
    p<0.05 (typically 0.3-0.5 for crypto).
35. `fracdiff_logvolume_d04` — Same for log volume.

### Why these specific features

- **Scale-invariance**: all features are ratios, ranks, or normalized spreads.
  None depend on absolute price levels, so pooling or per-symbol models both
  work.
- **Regime structure**: Hurst + ATR percentile rank + BB width percentile rank
  form a 3-dimensional regime signature that no v1 feature captures.
- **Tail-risk exposure**: rolling skew + kurtosis are the primary early-warning
  signals for regime shifts. v1 had neither.
- **Efficient vol estimators**: Parkinson/GK/RS are 3-5x more statistically
  efficient than close-to-close std dev. Each bar is worth more.
- **Memory preservation**: fracdiff lets the model see long-term price
  structure without being poisoned by non-stationarity. v1 shipped only
  d=1 (returns) and d=0 (raw prices).

### For iter-v2/001 specifically

Target **35 features**: the 28 core items from section A-F plus 7 QR-proposed
derivatives (extra horizons or ratios). Samples-per-feature ≈ 125 with 4,400
training samples. Well above the 50 floor.

---

## Risk Management Layer — 8 Primitives

v2's risk layer lives in `src/crypto_trade/strategies/ml/risk_v2.py` as
`RiskV2Wrapper`, which wraps any strategy (typically `LightGbmStrategy`) and
gates each signal BEFORE it reaches the backtest engine.

The 8 primitives and their status in iter-v2/001:

| # | Primitive | Status | What it does |
|---|---|---|---|
| 1 | **Volatility-adjusted position sizing** | **MVP** | Scale weight inversely with `atr_pct_rank_200`. Floor 0.3, ceiling 1.0. |
| 2 | **ADX gate** | **MVP** | If ADX < 20 (threshold tunable), kill the signal. Ranging regime = untrained territory for a momentum model. |
| 3 | **Hurst regime check** | **MVP** | Compute training-window 5th/95th percentile of `hurst_100`. At inference, if current Hurst is outside that band → kill. |
| 4 | **Feature z-score OOD alert** | **MVP** | Training-window rolling mean/std per feature. At inference, compute z-score per feature. If any `|z| > 3` → kill. Primary "model in untrained regime" detector. |
| 5 | Drawdown brake | Deferred (iter-v2/002) | Portfolio DD > 5% → shrink to 0.5x. > 10% → flatten. |
| 6 | BTC contagion circuit breaker | Deferred (iter-v2/002-003) | BTC 1h < -5% → kill all alt positions. Needs cross-model BTC data feed. |
| 7 | Isolation Forest anomaly | Deferred (iter-v2/003) | Unsupervised OOD on feature vector. Per-bar `isotree.score_samples`. |
| 8 | Liquidity floor | Deferred (iter-v2/002) | Spread > threshold OR volume < 5th pct → zero position. |

### Why these four as MVP

The user's stated #1 risk concern is "model in a market regime it wasn't
trained on." Gates 3 and 4 directly detect that condition. Gate 1 reduces
exposure when vol spikes (the most common precursor). Gate 2 filters the
most common degradation scenario (ranging regime for a momentum learner).

Drawdown brake, BTC contagion, isolation forest, and liquidity floor are all
valuable — but they add more moving parts and depend on cross-model data or
extra deps. Defer until the MVP 4 are tuned and their fire-rate calibrated.

### `RiskV2Wrapper` skeleton (iter-v2/001 will implement)

```python
from crypto_trade.strategies.ml.risk_v2 import RiskV2Wrapper, RiskV2Config

inner = LightGbmStrategy(..., features_dir="data/features_v2", ...)
config = RiskV2Config(
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
)
strategy = RiskV2Wrapper(inner, config)
run_backtest(cfg, strategy)
```

The wrapper delegates `compute_features`, snapshots training-window feature
statistics, then wraps `get_signal` with the gate cascade.

### Calibration

For iter-v2/001, document in the research brief:

- Expected fire rate of each gate on IS data. A gate firing >50% = badly
  calibrated (retune). A gate firing <1% = no protection.
- Gate ROI on IS: (loss avoided) − (profit killed) per fire.
- Coverage: which regimes in the training window fire which gates.

See Section 6 of the research brief schema below for the full template.

---

## Validation Upgrades — Phased Delivery

v2 raises the validation bar over v1 in three steps:

| Iteration | Added | Rationale |
|---|---|---|
| iter-v2/001 | DSR + regime-stratified OOS Sharpe | First iteration: answer "is this edge real?" and "where does it come from?" without blowing compute budget |
| iter-v2/002 | CPCV (N=6, k=2 → 15 paths) | Once DSR shows an edge, CPCV gives a statistically meaningful estimate of OOS variance |
| iter-v2/003 | PBO + ACF-based embargo sizing | PBO uses the CPCV paths; ACF embargo tightens the leakage gap to the actual feature decorrelation |

### Deflated Sharpe Ratio (DSR) — required from iter-v2/001

Formula (López de Prado, AFML Ch. 11):

```
E[max(SR_0)] ≈ sqrt(2·ln(N)) · (1 − γ/(2·ln(N))) + γ/sqrt(2·ln(N))
SE(SR)      = sqrt( (1 − skew·SR + (kurt−1)/4·SR²) / (T − 1) )
DSR         = (SR_observed − E[max(SR_0)]) / SE(SR)
```

where `γ ≈ 0.5772` (Euler-Mascheroni) and `N` = v2 iteration count (NOT
v1's 163 — v2's multiple-testing correction is scoped to its own track). `T`
= OOS trade count. `skew`/`kurt` = OOS return moments.

DSR is reported as a probability (CDF of the z-score). DSR > 0.95 = likely
real edge. DSR < 0.5 = likely overfit.

**Implementation**: `validation_v2.deflated_sharpe_ratio()` (stub scaffolded;
iter-v2/001 implements). Reference: `overfit_detector.py` in the
`walk-forward-validation` skill at `~/.claude/skills/`.

### Regime-stratified OOS Sharpe — required from iter-v2/001

Break OOS Sharpe down by (Hurst bucket × ATR percentile bucket), 3x3 grid.
Report as `reports-v2/iteration_NNN/out_of_sample/per_regime_v2.csv`. A
strategy whose Sharpe collapses outside one quadrant is a deployment risk.

### CPCV — added in iter-v2/002

Partition data into N=6 contiguous groups. For each C(6,2)=15 combination of
2 groups as test set, train on remaining 4 groups. Apply purging (label
horizon) and embargo (3 bars) at each boundary. Report mean OOS Sharpe, std,
and IS-to-OOS rank correlation across 15 paths.

### PBO — added in iter-v2/003

From the 15 CPCV paths, compute the fraction where the in-sample optimal
parameter set underperforms the median out-of-sample rank. PBO > 0.5 = more
likely than not overfit. PBO > 0.5 = **automatic NO-MERGE regardless of Sharpe**.

### ACF-based embargo sizing — added in iter-v2/003

Compute autocorrelation function (ACF) per feature over the training window.
Find first lag where |ACF| < 2/sqrt(N) (significance threshold). That lag =
recommended embargo size. Use `max(feature_embargos)` across all features.

---

## Research Brief — NEW Section 6: Risk Management Design

Every v2 research brief MUST contain this section, filled in before the
backtest runs. It is **mandatory every iteration** (including post-MERGE
iterations where v1 normally lets the QR skip research categories).

```markdown
## Section 6: Risk Management Design

### 6.1 Risk Primitives Active This Iteration

| Primitive | Status | Parameters | Justification |
|-----------|--------|------------|---------------|
| Vol-adjusted sizing | ENABLED | floor=0.3, ceiling=1.0, source=atr_pct_rank_200 | ... |
| ADX gate | ENABLED | threshold=20 | ... |
| Hurst regime check | ENABLED | 5/95 pct of training | ... |
| Feature z-score OOD | ENABLED | |z|>3 threshold | ... |
| Drawdown brake | DISABLED | - | Deferred to iter-v2/002 |
| BTC contagion | DISABLED | - | Deferred to iter-v2/002-003 |
| Isolation Forest | DISABLED | - | Deferred to iter-v2/003 |
| Liquidity floor | DISABLED | - | Deferred to iter-v2/002 |

### 6.2 Questions the QR Must Answer

1. **Regime coverage**: What Hurst distribution and ATR percentile distribution
   does the training window cover? Under-represented regimes (<5% of training)
   are the regimes where OOD gates will fire.

2. **Expected gate firing rate**: For each ENABLED gate, estimate how often it
   fires on IS data. Fire rate > 50% = badly calibrated (retune). Fire rate
   < 1% = no protection.

3. **Black-swan scenarios**: List the 3 worst historical crypto events in the
   IS window (LUNA May 2022, FTX Nov 2022, March 2020 Covid crash). For each,
   state which v2 gates would have triggered and what the residual PnL would
   have been.

4. **Known-unknown failure modes**: What class of market event would bypass
   all active gates? Document at least one. Example: "a slow monotone
   grind-down that never triggers ATR percentile spikes nor feature z-score
   excursions — v2's current gates cannot detect this."

5. **Deferred primitives rationale**: For each DISABLED primitive, why is it
   deferred? Complexity? Data dependency? Phase ordering?

### 6.3 Pre-Registered Failure-Mode Prediction (MANDATORY)

Before running the backtest, the QR writes 1-2 paragraphs:

    The most likely way this iteration loses money is _____. The gates
    that should catch it are _____. If the gates don't catch it, the
    loss will look like _____ in the OOS metrics.

This is a **pre-registered prediction**. The Phase 7 diary compares actual
failure modes to this prediction and updates the risk layer accordingly.

### 6.4 Exit Conditions (beyond TP/SL)

Timeout behavior unchanged (7 days). Additional: if any gate fires on an
OPEN position (not just signal time), does v2 flatten it? Yes/no with
reasoning.

### 6.5 Post-Mortem Template (for Phase 7 eval)

After the backtest, the QR computes per gate:

- Fire rate (% of signals/bars)
- PnL of killed trades (what would have been)
- PnL of scaled-down trades (delta vs full size)
- Gate ROI: (loss avoided − profit killed) / fire count

Each v2 diary reports this table, so gate efficacy is **measurable**.
```

This section is the main mechanism by which v2 forces the weak area (risk
management) into the critical path.

---

## Git Workflow — v2 Only

### Starting a v2 iteration

```bash
# From .worktrees/quant-research (verify with: git rev-parse --show-toplevel)
git checkout quant-research && git pull
git checkout -b iteration-v2/NNN
```

Branch prefix: `iteration-v2/`. Zero-padded NNN. Unique namespace — won't
collide with v1's `iteration/NNN`.

### Commit discipline

Separate documentation from code. NEVER mix them in the same commit.

1. Code commits → `feat(iter-v2/NNN): ...` / `fix(iter-v2/NNN): ...`
2. Research brief → single commit: `docs(iter-v2/NNN): research brief`
3. Engineering report → single commit: `docs(iter-v2/NNN): engineering report`
4. Diary entry → LAST commit on branch: `docs(iter-v2/NNN): diary entry`

Why: failed iterations cherry-pick commits 2, 3, 4 to `quant-research`. If
diary is mixed with code, cherry-pick breaks.

### MERGE (iteration beats v2 baseline)

```bash
git checkout quant-research
git merge iteration-v2/NNN --no-ff -m "merge(iter-v2/NNN): [1-line summary]"
# Update BASELINE_V2.md with new metrics from diary
git add BASELINE_V2.md
git commit -m "baseline-v2: update after iter-v2/NNN"
git tag -a v0.v2-NNN -m "Iter-v2 NNN: OOS Sharpe X.XX, MaxDD Y.Y%"
```

Tag format: `v0.v2-NNN`. `git tag -l 'v0.v2-*'` lists v2 tags only.

### NO-MERGE (iteration is worse)

**PRINCIPLE**: `quant-research` only ever contains **the current baseline's
code + reports + docs**. Failed-iteration code NEVER lands on `quant-research`.
When the iteration's decision is NO-MERGE, the code stays on
`iteration-v2/NNN` forever; only the 3 doc commits cross over.

**FORBIDDEN on NO-MERGE**:

```bash
# NEVER run these when the decision is NO-MERGE. They pull the failed
# code onto quant-research and silently corrupt the baseline:
git merge iteration-v2/NNN                       # FORBIDDEN
git merge iteration-v2/NNN --no-ff               # FORBIDDEN
git merge iteration-v2/NNN -m "merge(iter-v2/NNN): ... NO-MERGE"  # FORBIDDEN — happened iter-v2/061
git rebase iteration-v2/NNN                       # FORBIDDEN
git cherry-pick <any code commit>                 # FORBIDDEN
```

The word "merge" in the commit subject does NOT make a git-merge
into a cherry-pick. iter-v2/061 was labelled "NO-MERGE" in its subject
yet the author ran `git merge --no-ff`, which pulled `feat(iter-v2/061):
swap SOL for DOTUSDT` into `quant-research`. Subsequent baseline runs
unknowingly trained on DOT instead of SOL for 3+ iterations before the
discrepancy was caught. Never again.

**Correct NO-MERGE flow** (docs ONLY):

```bash
git checkout quant-research
git cherry-pick <research-brief-commit>        # briefs-v2/iteration_NNN/
git cherry-pick <engineering-report-commit>    # briefs-v2/iteration_NNN/
git cherry-pick <diary-commit>                 # diary-v2/iteration_NNN.md
# NO git merge. NO cherry-pick of code commits.
# Branch iteration-v2/NNN stays — never delete iteration branches
```

**Post-NO-MERGE audit (MANDATORY)**:

Immediately after the three cherry-picks, confirm no code leaked:

```bash
# Must return empty — if anything shows up, revert before continuing:
git diff HEAD~3 HEAD -- \
    src/crypto_trade/features_v2/ \
    src/crypto_trade/strategies/ml/risk_v2.py \
    src/crypto_trade/strategies/ml/validation_v2.py \
    run_baseline_v2.py
```

If the audit shows any diff, the NO-MERGE was botched. Fix with:

```bash
# Revert the stray code change (keeping the docs):
git revert <stray-code-commit> --no-edit
```

### NO-MERGE hygiene checks (every v2 iteration)

Before opening a new iteration branch, the QE MUST verify
`quant-research` hasn't drifted from its declared baseline:

```bash
# 1. V2_MODELS in run_baseline_v2.py matches BASELINE_V2.md "Symbols" row.
# Each V2_MODELS entry is ("LABEL (SYMBOL)", "SYMBOL") — the 2nd string is
# the canonical symbol.
python -c "
import re
with open('run_baseline_v2.py') as f: runner = f.read()
with open('BASELINE_V2.md') as f: baseline = f.read()
runner_syms = set(re.findall(r',\s*\"([A-Z0-9]+USDT)\"\s*\),', runner))
baseline_line = next(l for l in baseline.splitlines() if l.startswith('| Symbols '))
baseline_syms = set(re.findall(r'[A-Z0-9]+USDT', baseline_line))
assert runner_syms == baseline_syms, f'DRIFT: runner={runner_syms} baseline={baseline_syms}'
print(f'OK: runner and BASELINE_V2.md both declare {sorted(runner_syms)}')
"
```

If drift is detected, stop and revert the runner before starting any new
work.

### First v2 iteration

Since there is no v2 baseline yet, iter-v2/001's merge is special. See
"Baseline Comparison Rules" below for the relaxed success criteria that
apply only to iter-v2/001.

### CRITICAL GUARDRAILS — NEVER CROSS STREAMS

```
NEVER:
  git checkout main                       # from a v2 branch
  git merge iteration-v2/*                # into main
  git push origin iteration-v2/NNN:main   # force-push cross-track

v2 lives on quant-research. main is v1's branch.
Crossing streams destroys v1's baseline by accident.
```

QE pre-flight check at the top of every `run_baseline_v2.py` run:

```python
import subprocess
branch = subprocess.check_output(
    ["git", "branch", "--show-current"], text=True
).strip()
assert branch.startswith("iteration-v2/") or branch == "quant-research", (
    f"v2 runner must run from iteration-v2/* or quant-research, got: {branch}"
)
```

### What Is Tracked (v2)

| Location | Tracked | Merges to quant-research |
|----------|---------|--------------------------|
| `src/crypto_trade/features_v2/`, `src/crypto_trade/strategies/ml/risk_v2.py`, `src/crypto_trade/strategies/ml/validation_v2.py` | Yes | Only on MERGE |
| `run_baseline_v2.py` | Yes | Only on MERGE |
| `diary-v2/` | Yes | Always (cherry-pick or merge) |
| `briefs-v2/` | Yes | Always (cherry-pick or merge) |
| `BASELINE_V2.md` | Yes | Updated only on MERGE |
| `reports-v2/`, `models-v2/`, `analysis-v2/` | No (.gitignore) | Never |
| `data/features_v2/` | No (covered by `data/`) | Never |

### Eventual combined portfolio merge (future)

Out of scope for iter-v2/001-009 but documented here so the end-goal stays visible:

```bash
# Once v2 has a stable baseline (~iter-v2/010+), bring v2 into main for the
# combined-portfolio runner:
git checkout main
git merge quant-research --no-ff -m "merge(v2): import v2 baseline for combined portfolio"
# Then create run_portfolio_combined.py on main that loads both baselines.
```

---

## Phase Quick Reference

| Phase | Role | Data Access | Input | Output |
|-------|------|-------------|-------|--------|
| 1. EDA | QR | IS only | Parquet data in `data/features_v2/` | `briefs-v2/iteration_NNN/research_brief_phase1.md` |
| 2. Labeling | QR | IS only | Phase 1 findings | `briefs-v2/iteration_NNN/research_brief_phase2.md` |
| 3. Symbol Universe | QR | IS only | Phase 1 findings + `V2_EXCLUDED_SYMBOLS` | `briefs-v2/iteration_NNN/research_brief_phase3.md` |
| 4. Data Filtering | QR | IS only | Phase 1 findings | `briefs-v2/iteration_NNN/research_brief_phase4.md` |
| 5. Brief Compilation | QR | IS only | Phases 1-4 + Section 6 Risk Management Design | `briefs-v2/iteration_NNN/research_brief.md` (single commit) |
| 6. Implementation | QE | Walk-forward on ALL data; reports split at cutoff | Research brief | Code, IS reports, OOS reports, comparison.csv, engineering report |
| 7. Evaluation | QR | IS + OOS reports (first time seeing OOS) | Reports + `BASELINE_V2.md` | Merge decision |
| 8. Diary | QR | — | Evaluation | `diary-v2/iteration_NNN.md` (last commit on branch) |

Scope of phases 1-4 for subsequent iterations:
- **After a MERGE**: Phases 1-4 may be partially skipped if only one variable
  changes. QR must still complete **≥2 categories** from the Research Checklist
  (A-H) PLUS Category I (Risk Management Analysis — mandatory in v2 every iter).
- **After 3+ consecutive NO-MERGE**: Phases 1-4 are MANDATORY. QR must complete
  **≥4 of 8 categories** (A-H) PLUS Category I.
- **After EARLY STOP**: Same as 3+ NO-MERGE. Parameter-only changes BANNED.

Phase 5 is always required, Section 0 (Data Split) always included verbatim,
Section 6 (Risk Management Design) always filled in.

---

## Seed Robustness Validation — SUPERSEDED by v1-style 5-seed internal ensemble

**Status**: From iter-v2/035 onward, v2 adopted the v1-style 5-seed INTERNAL
ensemble (`ensemble_seeds=[42, 123, 456, 789, 1001]` baked into every model
call). The ensemble averages predictions across 5 per-seed Optuna runs per
monthly training — that IS the seed-robustness validation for this
architecture.

The old 10-outer-seed rule is therefore **DROPPED** as of iter-v2/069. The
`LightGbmStrategy._train_for_month` code uses `ensemble_seeds or [self.seed]`
(lgbm.py:450), meaning the outer `seed` is IGNORED whenever `ensemble_seeds`
is set (which it always is, post-iter-v2/035). Empirical confirmation from
iter-v2/069's partial 10-seed run: seed 42 and seed 123 produced bit-identical
trade counts (DOGE=58, SOL=77, XRP=78) because the inner ensemble is the same.

### The new rule — single-seed is the measurement

For v2 baselines and MERGE candidates:

1. Run a **single outer seed** (default 42). The inner 5-seed ensemble runs
   5 Optuna studies and averages predictions — this IS the seed robustness.
2. `run_baseline_v2.py --seeds 1` (default) is sufficient.
3. `--seeds N > 1` is DEPRECATED for the v1-style ensemble. It does N × 2.5h
   of work that produces identical trades to `--seeds 1`.

### First-seed early-stop (unchanged)

If the single seed produces OOS Sharpe < 0 or OOS PF < 1.0, the iteration
is immediately a NO-MERGE candidate. No "try more seeds" — the ensemble
has already pooled 5 inner seeds; that's the result.

### If you ever restore true multi-seed validation

Refactor `run_baseline_v2.py::_build_model` to make `ensemble_seeds` a
function of the outer seed, e.g.:
```python
ensemble_seeds=[outer_seed + i * 100 for i in range(5)]
```
Then each outer seed produces a genuinely different 5-seed inner ensemble.
This re-introduces true variance at the cost of 10× compute per MERGE.

### Concentration check (the one that DID matter)

Even without outer-seed variance, the PER-SYMBOL concentration rule stays
fully enforceable on a single seed. See "Seed Concentration Check" below.

---

## Seed Concentration Check — Single-seed per-symbol check

**This is a hard pre-MERGE gate. No baseline merges without passing it.**

(Simplified post-iter-v2/069: since outer-seed sweeps are vacuous under
the v1-style 5-seed internal ensemble, the concentration check runs on
the single merged-baseline seed only. The per-seed-max / mean-max
thresholds in the table below still apply, but for a single measurement.)

### Historical context — why this rule exists

iter-v2/028 had mean OOS monthly Sharpe +1.08 (first breakthrough above
1.0) but primary seed 42 showed XRP = 73.43% concentration. Merging on
headline Sharpe would have deployed a brittle portfolio.

### The rule — n-symbol-aware concentration thresholds

Before MERGE, the QE MUST compute per-symbol OOS PnL share for the
single baseline seed and report it as a table in the engineering report.

**The concentration thresholds scale with the number of symbols in the
portfolio.** A 50% rule is vacuous for n=2 (max is trivially ≥50%) and too
loose for n=10 (an equal-weight target is 10%). The per-n thresholds are:

| n_symbols | Max per seed | Mean max-share | ≤1 seed above |
|-----------|--------------|----------------|---------------|
| 2         | **60%**      | **55%**        | **50%**       |
| 3         | **55%**      | **50%**        | **45%**       |
| 4         | **50%**      | **45%**        | **40%**       |
| 5         | **40%**      | **35%**        | **32%**       |
| 6-7       | **35%**      | **30%**        | **28%**       |
| 8+        | **30%**      | **25%**        | **23%**       |

These are roughly `max = (1/n + 25%)` with a floor of 30% for large n.

An iteration merges ONLY if (single-seed baseline, using the row for its
n_symbols):

1. **Per-seed hard cap (outer)**: No symbol exceeds the "Max per seed"
   threshold for the portfolio's n_symbols. e.g. n=4 → max ≤ 50%.
2. **Per-seed inner cap**: No symbol exceeds the "≤1 seed above"
   threshold. e.g. n=4 → no symbol > 40%. (Stricter than outer; passing
   this is a first-class "clean concentration" signal.)
3. **Mean cap**: Inapplicable under single-seed baselines. Retained in
   the table for reference if ever multi-seed is restored.

### Concentration metric — USE `weighted_pnl`, NOT `net_pnl_pct`

**This was a source of a reporting bug through iter-v2/029.** The
`per_symbol.csv` column `pct_of_total_pnl` is computed from `net_pnl_pct`
(raw trade return percentage). The correct concentration measure is
`weighted_pnl` (= net_pnl_pct × vol-adjusted position weight from
`RiskV2Wrapper`), because concentration is about CAPITAL exposure, not
return percentage.

iter-v2/029 primary seed 42 reported **60.86% XRP concentration** via
`per_symbol.csv` but was really **69.47%** via `weighted_pnl`. The
concentration problem was always worse than visible. Going forward:

- `seed_concentration.json` (added iter-v2/030) uses `weighted_pnl`: this
  is canonical.
- `per_symbol.csv` values are informational only; do not use them to judge
  the Seed Concentration Check rule.

### Distressed-seed handling

When a seed's total OOS `weighted_pnl` is small, near zero, or negative,
the share metric becomes nonsensical (one symbol can show >100% share
because the total is nearly zero). Three iter-v2/030 seeds exhibited this
(seed 1001 showed NEAR = 949% share).

**Rule**: if a seed has **|total_oos_weighted_pnl| < 10.0** OR
**total_oos_weighted_pnl ≤ 0**, flag it as **DISTRESSED** and:

1. Compute the share metric using the **POSITIVE-ONLY total** as the
   denominator: `share[sym] = max(0, sym_wpnl) / sum(max(0, s_wpnl) for s in symbols)`.
   This always produces a number in [0, 1] and has a sensible interpretation
   ("of the positive contributors, how much is from this symbol").
2. Distressed seeds still count as seeds for the overall rule, but the
   dominant-symbol label uses the positive-total interpretation.
3. Report the distressed count in the audit verdict. If >2 of 10 seeds
   are distressed, the strategy is unstable and NO-MERGE regardless of
   other metrics.

### Required reporting template

Every engineering report for a MERGE-candidate iteration must include a
Seed Concentration Audit subsection with TWO things:

1. **The per-seed table** (state its n_symbols, use that row's thresholds):

```
n_symbols = 4, thresholds: max ≤ 50%, mean ≤ 45%, ≤1 seed above 40%

| Seed | Max Share | Symbol    | Pass max | Pass inner | Distressed? |
|------|-----------|-----------|----------|------------|-------------|
| 42   | 69.5%     | XRPUSDT   | FAIL     | FAIL       | —           |
| 123  | 53.8%     | XRPUSDT   | FAIL     | FAIL       | —           |
| 1001 | 72.7%     | XRPUSDT   | FAIL     | FAIL       | DISTRESSED  |
| ...  | ...       | ...       | ...      | ...        | —           |
| Mean | 51.3%     | —         | —        | —          | —           |
```

2. **One-line verdicts** (each threshold from the row above):

- Per-seed max cap (≤ 50%):  X of 10 seeds pass
- Mean ≤ 45%:                PASS / FAIL
- ≤1 seed above 40%:         PASS / FAIL
- Distressed seed count:     Y of 10 (rule: ≤ 2)
- **Overall seed concentration**: PASS / FAIL

**If overall = FAIL, the iteration is NO-MERGE regardless of headline mean
Sharpe**, even if it was the highest OOS mean we've ever seen. The diary
must explicitly state "Seed concentration: PASS" before a MERGE recommendation.

### Why per-seed concentration is its own rule

Seed variance in Optuna hyperparameter search can produce highly-selective
models that lock onto one symbol's sweet spot. The aggregate mean hides this
when other seeds find different sweet spots. The mean can be great while
every individual model is brittle.

Mitigations to try when this rule fails (in priority order):
1. **Reduce Optuna trials** — fewer trials = less selective = better symbol
   distribution (iter-v2/028 → iter-v2/029 path: 25 → 15 trials)
2. **Constrain hyperparameter ranges** (e.g., cap confidence_threshold upper bound)
3. **Per-symbol position cap** at backtest time (hard clip any symbol > X% of capital)
4. **Add/rebalance symbols** — more symbols dilutes concentration mechanically

---

## Symbol Addition Validation — 6 Gates for v2

When iter-v2/001 picks the initial 3 symbols — or any later iteration adds a
new symbol to v2's universe — the QE MUST run the 6-gate protocol.

**Gate 1 — Data quality**: ≥1,095 IS candles (1 year of 8h data), no gaps
> 3 days, first candle before 2023-07-01. Enforced by `universe.py` defaults.

**Gate 2 — Liquidity**: Mean daily volume > $10M (8h candles × 3 per day).

**Gate 3 — Stand-alone profitability**: Train a SEPARATE LightGBM on only
this symbol's IS data (same config: 24mo window, 5 CV folds, 50 Optuna
trials, ATR labeling). Passes only if:
- IS Sharpe > 0.0
- IS WR above break-even
- ≥100 IS trades

**Gate 4 — Pooled / combined compatibility** (applies from iter-v2/002+ when
a v2 baseline exists): Add the symbol to the current v2 portfolio and re-run.
New v2 IS Sharpe must be ≥ v2 baseline IS Sharpe × 0.90. No per-symbol WR
degradation > 2pp.

**Gate 5 — Diversification value** (within v2): Correlation with existing v2
portfolio returns < 0.7.

**Gate 6 — NEW: Diversification from v1**: Correlation of this symbol's
returns with v1's baseline portfolio returns < 0.85. This is the gate that
enforces "v2 must be different from v1" at the symbol-selection level. If a
candidate moves too strongly with BTC/ETH/LINK/BNB, it adds no value to the
combined portfolio.

For iter-v2/001 (no prior v2 baseline), Gate 4 is vacuous and skipped.
Document that fact in the brief.

---

## Feature Normalization Awareness

Same as v1. Tree models (LightGBM) are less sensitive to scale than linear
models, but large absolute values still cause split-point issues. v2's
feature catalog is scale-invariant by construction (all features are ratios,
percentile ranks, or volatility-normalized spreads), so normalization is not
a concern for iter-v2/001. If a future v2 iteration introduces a scale-
dependent feature, it must be flagged in the brief and paired with a
normalization strategy.

---

## Feature Count Discipline

Same as v1:

- Target: **30-50 features** for a new/small model
- Hard ceiling: **200 features**
- Samples-per-feature ratio: **≥ 50**
- **Every added feature must displace a worse one.** Net feature count
  should decrease or stay flat, never balloon.

For iter-v2/001: 35 features × 4,400 samples = ratio 125. Healthy.

**iter 083 (v1) anti-pattern**: added 85 features without pruning → catastrophic.
**iter 163 (v1) anti-pattern**: added 11 entropy/CUSUM features without pruning
→ OOS Sharpe -57%. v2 starts from scratch, so the iter-v2/001 anti-pattern to
watch for is **scope creep** (the 28-item catalog ballooning to 50 before
iter-v2/001 even runs).

---

## Feature Column Pinning — REPRODUCIBILITY GUARANTEE

This section is MANDATORY. Violating it produces silently unreproducible
results. v1 lost its +2.83 baseline exactly this way (see
`analysis_v1_baseline_battletest.md` for the post-mortem).

### The problem

LightGBM's `colsample_bytree < 1.0` samples columns by **position** using the
seeded RNG. Same seed + same features + **different column order** → same
seeded RNG picks **different columns** for each tree → different tree
structure → different probabilities → different trade signals → different
OOS Sharpe.

Empirically proven: on real BNB training data with `colsample_bytree=0.7`
(a typical Optuna-tuned value for v1/v2), shuffling column order produces
6% label flips at 0.5 threshold and ~15–30 signal flips per test month at
the 0.7–0.85 thresholds we actually trade at. Over 12 months this
compounds to hundreds of divergent trades.

LightGBM itself IS deterministic given identical inputs (feature values,
column order, seed). The non-determinism comes from column-position-dependent
sampling — not from the library.

### The rule

Every v2 backtest runner, live engine, notebook, and validation script MUST:

1. Import a single canonical ordered tuple from `src/crypto_trade/features_v2`
   (currently `V2_FEATURE_COLUMNS`; do not fork the name).
2. Pass it to `LightGbmStrategy(..., feature_columns=list(V2_FEATURE_COLUMNS))`.
3. Never pass `feature_columns=None`. Never pass `feature_columns=sorted(...)`.
   Never pass a set, dict-keys view, or any other collection whose iteration
   order is language/implementation-defined.

The LightGbmStrategy class now rejects `feature_columns=None` with a clear
error (enforced by a parallel code session). This skill enforces the same
rule at the workflow/documentation level.

### Changing the feature list

Adding/removing features DOES change the model — that is the whole point of
iteration. But it must be a deliberate, auditable change:

- **Pruning a feature**: Delete the string from `V2_FEATURE_COLUMNS`. Commit.
  OOS Sharpe will change; that is the iteration's measurement.
- **Adding a feature**: Append the string to `V2_FEATURE_COLUMNS` (do NOT
  insert into the middle — that reshuffles positions for every tree already
  using colsample and silently changes every existing prediction even for
  unrelated features).
- **Reordering** is forbidden unless the iteration is explicitly about
  measuring column-order sensitivity.

### Baseline reproducibility audit (QE, every iteration)

Before running a backtest, the QE MUST:

```bash
grep -rn "feature_columns=" run_baseline_v2.py run_iteration_v2_*.py \
    src/crypto_trade/live_v2/  2>/dev/null | \
    grep -v "V2_FEATURE_COLUMNS\|BASELINE_V2_FEATURE_COLUMNS\|list(V2_FEATURE"
```

If this returns any lines, something is passing a non-canonical list.
STOP. Fix it before running.

### The current canonical list

`V2_FEATURE_COLUMNS` in `src/crypto_trade/features_v2/__init__.py`. As of
the iter-v2/059 baseline, it contains the 35 v2 features plus the 5 BTC
cross-asset features (40 total; cross-v2sym features were removed in
iter-v2/044 after IS regression). This tuple is the single source of truth.
Everything else (`run_baseline_v2.py`, future live engines, notebooks) must
import it, never redefine it.

If a future iteration genuinely wants a different feature list (e.g.,
experimenting with a subset), it must:
1. Create a new named tuple (`V2_FEATURE_COLUMNS_EXPERIMENT_047` etc.)
2. Use that named tuple throughout the iteration
3. Either merge it back into `V2_FEATURE_COLUMNS` on MERGE or discard it on
   NO-MERGE. Never let two canonical lists coexist.

---

## Candle Integrity — CLOSED CANDLES ONLY

The v1 baseline lost ~7 days of OOS accuracy because an earlier fetcher wrote
the **currently-forming** kline to the CSV. Binance returns the open/high/low/close
of the candle *as of right now*, so the last row was stale mid-candle values
that never got corrected on subsequent incremental fetches. All 4 v1 baseline
symbols accumulated 3–4 corrupted tail candles; rolling features then
propagated those bad values back through the longest rolling window (~100
candles). This is a second major source of non-reproducibility that sits
BESIDE the column-order bug, not a replacement for it.

### The rule

`fetcher.py::fetch_symbol_interval` MUST drop any kline whose `close_time`
is in the future:

```python
now_ms = int(time.time() * 1000)
closed = [k for k in klines if k.close_time < now_ms]
if not closed:
    return 0
return write_klines(path, closed, append=append)
```

This fix lives on `main` as commit `19a1d3e` (2026-04-13). The
`quant-research` branch inherits fixes to core infrastructure from `main`
via periodic merges — if the branch has drifted and the fix is missing,
STOP, merge `main`, and never run `crypto-trade fetch` from a branch that
doesn't have it.

### QE pre-flight check (mandatory before every iteration)

Before running any `fetch` / `bulk` / feature-regeneration / backtest, the
QE runs this audit:

```bash
# 1. Fetcher has the closed-candle guard
grep -q "k.close_time < now_ms" src/crypto_trade/fetcher.py || \
    { echo "FATAL: fetcher missing closed-candle filter"; exit 1; }

# 2. No CSV tail candle has close_time in the future (proof no corruption)
uv run python -c "
import time, pandas as pd
from pathlib import Path
now_ms = int(time.time() * 1000)
bad = []
for p in Path('data').glob('*/8h.csv'):
    df = pd.read_csv(p)
    if (df['close_time'] >= now_ms).any():
        bad.append(p.name)
if bad:
    raise SystemExit(f'Forming candles present in: {bad}')
print('All CSV tails are closed-candle-only ✓')
"

# 3. Data freshness — kline CSVs for all baseline symbols must be recent.
# A CSV that stopped fetching weeks ago silently truncates the OOS window:
# the backtest will force-close any trade still open at CSV end with
# `exit_reason=end_of_data`, and all trades that would have happened after
# that point simply don't exist in the measurement. iter-v2/059's "OOS
# Sharpe +2.02" was measured on NEAR/SOL/XRP/DOGE CSVs stale to 2026-02-28
# — effectively shortening OOS by 50 days and dropping 3 trades from the
# measurement. Always run this check before measuring a baseline.
uv run python -c "
import sys, time, pandas as pd
from pathlib import Path

BASELINE_SYMBOLS = ['DOGEUSDT', 'SOLUSDT', 'XRPUSDT', 'NEARUSDT', 'BTCUSDT']
MAX_LAG_HOURS = 16   # one 8h candle + one 8h grace
now_ms = int(time.time() * 1000)
stale = []
for sym in BASELINE_SYMBOLS:
    p = Path(f'data/{sym}/8h.csv')
    last_close_ms = int(pd.read_csv(p, usecols=['close_time'])['close_time'].max())
    lag_h = (now_ms - last_close_ms) / 3_600_000
    if lag_h > MAX_LAG_HOURS:
        stale.append((sym, round(lag_h, 1)))
if stale:
    sys.exit(f'STALE DATA (>{MAX_LAG_HOURS}h lag): {stale}. Run crypto-trade fetch.')
print(f'All baseline CSVs fresh (≤{MAX_LAG_HOURS}h lag) ✓')
"

# 4. Runner ↔ BASELINE_V2.md symbol drift (see NO-MERGE hygiene section)
```

All four checks must pass green before Phase 6 starts. If any fails the QE
stops, fixes the underlying issue (re-fetch / revert stray code / cleanup
tail corruption), regenerates features, and re-runs the pre-flight before
proceeding.

### Why this matters for v2

- Rolling feature windows (ATR_14, BB_30, SMA_100, garman_klass_50, etc.)
  propagate a single corrupted candle backward through many downstream
  feature rows.
- Cross-asset features (e.g., `btc_ret_14d`, `sym_vs_btc_ret_7d`) propagate
  BTC corruption into every other symbol's feature row for the same period.
- The vol-targeting layer uses rolling 45-day daily PnL, which consumes
  these features. Corrupted features → wrong vt scale → wrong weighted_pnl
  → wrong Sharpe number — even before we get to colsample_bytree.

Combine this with the column-order bug and you have two independent ways to
silently produce unreproducible baselines. Both must be closed.

---

## Label Leakage Prevention — NON-NEGOTIABLE

Same as v1. The rule:

Labels MUST NOT leak across ANY boundary:
1. CV fold boundaries — training labels cannot see validation-period prices
2. Walk-forward boundaries — training labels cannot see future klines
3. Live prediction — model predicts one step at a time, never trained on future data

### The Fix

```python
gap = (label_timeout_minutes // interval_minutes + 1) * n_symbols
tscv = TimeSeriesSplit(n_splits=cv_splits, gap=gap)
```

**Example**: 8h candles, 7-day timeout, 1 symbol per model (v2's default) →
gap = (10080/480 + 1) × 1 = **22 rows**. Smaller than v1's pooled-BTC+ETH case
because v2 uses individual models.

### Walk-Forward Label Leakage

The walk-forward backtest trains each month's model on a window of past data.
Verify with `assert` checks on date ordering per monthly fold. No change from v1.

---

## Sample Weights: Uniqueness + Time Decay (AFML Ch. 4)

Same as v1 — reused via the shared `labeling.py`. No v2-specific change.

### Final weight formula

```
final_weight(i) = uniqueness(i) × time_decay(i) × abs_pnl_weight(i)
```

v2 inherits this unchanged. The `RiskV2Wrapper` does not touch training
weights — it only gates predictions at inference time.

---

## Fractional Differentiation (AFML Ch. 5)

v1 tested fracdiff in iter 100 and the result was inconclusive due to a
confounding parquet regeneration. v2 treats fracdiff as a **baseline v2
feature**, not an experimental technique. It ships in iter-v2/001's
feature catalog (`fracdiff_logclose_d04`, `fracdiff_logvolume_d04`).

### Why fracdiff belongs in v2

- Tree-based models still benefit from stationary features with long-term
  memory (split points generalize across regimes).
- v2 explores alt symbols with shorter histories (~3 years); every bit of
  retained memory matters.
- The `fracdiff` PyPI package provides FFT-based computation; fixed window=100
  keeps compute cost manageable.

### Implementation

`features_v2/fracdiff_v2.py::add_fracdiff_features()`. For each symbol, find
minimum `d` such that ADF p-value < 0.05. Typical crypto: 0.3-0.5. Apply
windowed fracdiff with fixed window=100 (≈33 days on 8h candles).

---

## Baseline Comparison Rules

Read `BASELINE_V2.md` on `quant-research` before evaluating. An iteration
merges ONLY if:

1. **Primary**: **combined IS+OOS monthly Sharpe** improves vs the current v2
   baseline. Rewards balance, not just OOS dominance. Updated in iter-v2/044
   after iter-044 was unfairly blocked despite beating baseline on combined
   (+2.24 vs +2.16) with better IS (+24%) and better MaxDDs on both sides.
2. **Balance guards** (both must pass — catches overfits disguised as gains):
   - **IS monthly Sharpe ≥ baseline IS × 0.85** — no severe IS regression
   - **OOS monthly Sharpe ≥ baseline OOS × 0.85** — no severe OOS regression
3. **Hard constraints** (all must pass):
   - Max drawdown (OOS) ≤ v2 baseline OOS max drawdown × 1.2
   - Minimum 50 OOS trades
   - Profit factor > 1.0 (OOS)
   - **Seed concentration audit**: PASS (see "Seed Concentration Check" section
     — no single seed > 50% on any symbol, mean seed max-share ≤ 45%, at most
     1 of 10 seeds above 40%)
   - IS/OOS Sharpe ratio > 0.4 (guard against IS<<OOS garbage)
   - **v2-v1 correlation < 0.80** (NEW): correlation of v2 portfolio returns
     vs v1 portfolio returns during OOS window. If too high, v2 is just
     v1-in-disguise and offers no combined-portfolio benefit.

### Why combined IS+OOS as primary

The old rule ("OOS Sharpe > baseline OOS") produced asymmetric incentives:
- A candidate with OOS +1.72, IS +0.82 (ratio 2.10) would beat a candidate
  with OOS +1.40, IS +0.84 (ratio 1.67) even though the second is more
  balanced and has a healthier IS.
- This encouraged OOS-peak-chasing over healthy-portfolio behavior, and
  made every balance-improving iteration NO-MERGE even when the combined
  Sharpe improved.

The combined metric (IS + OOS monthly Sharpe) rewards genuine progress:
- Pure IS gain at OOS expense (iter-039 IS +46% / OOS −51%): combined
  REGRESSES. Correctly NO-MERGE.
- Pure OOS gain at IS expense (iter-037 IS −36%): IS guard FAILS.
  Correctly NO-MERGE.
- Balanced gain with small OOS regression (iter-044 IS +24% / OOS −5%):
  combined IMPROVES, guards pass. Correctly MERGE.

If primary metric improves but a constraint fails → NO-MERGE.

### Special rule for iter-v2/001 (no prior v2 baseline)

Since iter-v2/001 has nothing to compare against, the success criteria are
relaxed:

- OOS Sharpe > **+0.5** (modest starting bar — any profitable edge)
- OOS trades ≥ 50
- Profit factor > 1.1
- **Seed concentration audit**: PASS (see "Seed Concentration Check" section)
- **DSR > -0.5** (wide tolerance — N=1 for v2's trial count)
- **v2-v1 correlation < 0.80** (non-negotiable, the whole point)

If all pass → MERGE: write initial `BASELINE_V2.md`, tag `v0.v2-001`.
If any fail → NO-MERGE: cherry-pick docs, EARLY STOP triggers mandatory
research checklist for iter-v2/002.

### One-time baseline reset: iter-v2/029

**User-directed exception.** iter-v2/029 is merged UNCONDITIONALLY as a
baseline reset, even if its headline metrics are worse than implicit prior
iterations. Reason: after iter-v2/028's breakthrough-but-concentrated result
(mean OOS +1.08 / XRP 73%), the user wants a clean reference point to
continue from, not a continued search in the "maybe MERGE, maybe not" zone.

- iter-v2/029 result → becomes `BASELINE_V2.md` regardless of seed
  concentration, Sharpe, or any other constraint.
- The Seed Concentration Check rule is documented in this skill as of
  iter-v2/029 and is **enforced starting from iter-v2/030 onwards**.
- The iter-v2/029 diary must still REPORT the seed concentration audit
  (the table is mandatory), even though its outcome does not gate the merge.
  This gives iter-v2/030+ a clear reference point for what passed/failed.

### Diversification exception (iter-v2/002+)

Same as v1: if an iteration adds new symbols and OOS Sharpe is within 5% of
the v2 baseline AND OOS MaxDD improves by >10% AND concentration improves
AND all other constraints pass, the QR MAY recommend MERGE even without
strict Sharpe improvement. Requires explicit diary justification.

---

## Overfitting Quantification — DSR, PBO, CPCV

### Deflated Sharpe Ratio (DSR)

`N` = **v2 iteration count** (NOT v1's 163). v2's multiple-testing correction
is scoped to its own track. iter-v2/001 has N=1, so DSR tolerance is wide
(> -0.5 passes). By iter-v2/020, N=20 → E[max(SR_0)] ≈ 2.45. Typical v2 OOS
Sharpe targets at that point should clear E[max(SR_0)] by ≥0.5 std errors.

Implementation: `validation_v2.deflated_sharpe_ratio()` (scaffolded, iter-v2/001
implements). The QR reports DSR in every v2 diary.

### PBO + CPCV (from iter-v2/002-003)

When CPCV is implemented in iter-v2/002:
- N=6 contiguous groups → C(6,2)=15 paths per Optuna configuration
- Purge overlap, embargo 3 bars
- Report mean path Sharpe, std, PBO

PBO > 0.5 → **automatic NO-MERGE** regardless of Sharpe. This is stricter
than v1, which has PBO as an unimplemented idea.

### On 117+ trial multiple testing

v1 at N=117 has E[max(SR_0)] ≈ 3.08. v1's observed OOS Sharpe +2.83 is still
below this, meaning v1's raw Sharpe doesn't clear DSR. v2 starts fresh at
N=1 and compounds its own multiple-testing budget. The combined portfolio
will eventually need a combined multiple-testing correction — **out of scope
for iter-v2/001-009**, flagged for the future combined runner.

---

## Backtest Report Structure — v2

```
reports-v2/iteration_NNN/
├── in_sample/
│   ├── quantstats.html
│   ├── trades.csv
│   ├── daily_pnl.csv
│   ├── monthly_pnl.csv
│   ├── per_regime.csv
│   ├── per_regime_v2.csv          ← NEW: (Hurst bucket × ATR pct bucket)
│   ├── per_symbol.csv
│   └── feature_importance.csv
├── out_of_sample/
│   ├── quantstats.html
│   ├── trades.csv
│   ├── daily_pnl.csv
│   ├── monthly_pnl.csv
│   ├── per_regime.csv
│   ├── per_regime_v2.csv          ← NEW: (Hurst bucket × ATR pct bucket)
│   ├── per_symbol.csv
│   └── gate_efficacy.csv          ← NEW: per-gate fire rate, PnL, ROI
├── comparison.csv
└── dsr.json                        ← NEW: DSR result + inputs for reproducibility
```

`comparison.csv` is the first thing the QR opens in Phase 7. `per_regime_v2.csv`
is opened second — if Sharpe is concentrated in one regime bucket, that's a
deployment risk worth documenting in the diary.

---

## Fail Fast Protocol — Aggressive (inherited from v1)

We are looking for a GOOD model, not an almost-break-even model. Time is the
most valuable resource. Kill bad strategies fast.

### Yearly Checkpoints

### Training window — FIXED at 24 months

**`training_months=24` is locked. Do NOT change it.**

Changing the training window directly changes WHICH months appear in the IS
evaluation period. Shorter window → walk-forward starts later → fewer IS
months to validate. Longer window → same effect (later start due to more
warm-up). Either direction corrupts the IS/OOS comparison because IS itself
changes.

Evidence from iter-v2/037 (18mo) and iter-v2/038 (30mo, aborted): 18mo
improved OOS +9% but IS collapsed −36%. The IS regression was not from
model quality — it was from losing 6 months of IS evaluation data. Any
training-window change conflates model improvement with measurement change.

**To improve IS, change features, labeling, or model architecture — not the
training window.**

### Yearly Checkpoints

Training window is 24 months. First predictions ≈ Jan 2022. Check at end of
each calendar year:

**Year 1 checkpoint**:
- Cumulative PnL negative → **STOP**
- WR < 33% → **STOP**

**Year 2 checkpoint**:
- Cumulative PnL across years 1+2 negative → **STOP**
- Any individual year WR < 30% → **STOP**

**First-seed rule**: Run first seed fully. If OOS Sharpe < 0 or OOS PF < 1.0,
STOP. Don't run the other 9 seeds.

**Don't dismiss positive IS too quickly**: If IS Sharpe > +1.0 but first OOS
seed is weak, run 2-3 more seeds. OOS is heavily seed-dependent.

### When early-stopped

1. QE writes engineering report with partial results and the trigger
2. QR writes diary tagged **`NO-MERGE (EARLY STOP)`** with partial metrics
3. "Next Iteration Ideas" MUST propose **structural changes only** (banned:
   TP/SL tweaks < 2×, Optuna trial count, confidence threshold range, symbol
   count changes < 50%)
4. At least one proposed change must come from the QR Research Checklist

---

## QR Research Methodology — Checklist A-I

Same A-H as v1, plus a **mandatory Category I** specific to v2.

**Minimum completion (v2)**: Category I is required every iteration. Plus:
- After a MERGE: 2 additional categories from A-H
- After 3+ NO-MERGE or EARLY STOP: 4+ additional categories from A-H
- **Category A is mandatory every 5 iterations regardless** (see
  "Mandatory Category A cycle" below)

### Non-negotiable QR output standards

Every brief must satisfy ALL of the following. QE rejects any brief
missing these:

1. **Each claimed category has its own named subsection** in the brief
   (e.g., `## Category A — Feature Contribution Analysis`). No bundled
   bullet points.
2. **Every subsection includes a quantitative output**: a numbered
   finding, a table, a CSV path, or a correlation number. Qualitative
   assertions ("NEAR looks concentrated") are insufficient without a
   number backing them.
3. **Section 6 (risk mgmt) pre-registered failure-mode prediction**
   must be specific enough to be checkable in Phase 7. "Might fail in
   new regime" doesn't qualify; "if BTC 7-day return > 10% and no
   signal killed, fail" does.
4. **"Bold idea" quota**: every 3 iterations, at least 1 must include
   a proposal that adds/changes/removes at least 50 lines of code or
   introduces a new feature family / gate / architecture. Parameter
   tweaks, threshold changes, and single-symbol swaps DO NOT count as
   bold. Track the count in the diary's "Next Iteration Ideas"
   section.

### Mandatory Category A cycle (every 5 iterations)

A complete Category A analysis includes:

1. **Feature correlation matrix** — report every pair with |rho|>0.85
   from the pooled-IS data. Flag for pruning. (Tool:
   `qr_phase1_feature_eda.py`.)
2. **Feature stationarity** — flag features whose mean drifts >0.3σ
   between the first and second halves of the IS period.
3. **Feature-to-forward-return Spearman correlation** — rank all
   features by predictive power. Identify the top-3 and bottom-3.
4. **Feature importance from a trained baseline** — load or compute the
   LightGBM feature importance from a recent MERGE baseline.
5. **A written proposal**: either (a) specific features to drop with
   justification, (b) specific new features to add with math, or (c)
   both.

If iterations since the last Category A exceed 5, the QR MUST run
Category A before proposing any other change. No exceptions. Even a
"quick parameter tweak" iteration must first answer: are we tuning on a
clean feature set?

### Dead-ideas log (BASELINE_V2.md)

`BASELINE_V2.md` carries a "Dead Ideas" section listing what's been
tried and FAILED, grouped by category:

```markdown
## Dead Ideas

### Symbol changes
- AAVEUSDT (iter-v2/063): +Gate-3-skipped, OOS -21 wpnl
- AVAXUSDT (iter-v2/041): IS collapsed
- ATOMUSDT (iter-v2/047): swap for DOGE, failed
- ADAUSDT (iter-v2/036, v2/066): single-seed looks good, ensemble kills signal

### Concentration fixes
- Per-symbol position cap on NEAR (iter-v2/064, /065): data-snooping,
  also trades Sharpe for concentration
- Portfolio drawdown brake (iter-v2/067): INCREASES MaxDD in this strategy

### Gate / filter tunes
- z-score OOD 2.25 (iter-v2/060): OOS trades <50 min
```

QR must consult this list before proposing. Repeating a dead idea
requires explicit justification of WHY conditions have changed enough
to retry.

### A. Feature Contribution Analysis
(Same as v1 A1-A4. For iter-v2/001, A1 pruning is skipped — there's no v2
baseline to prune from — start at A4 "new feature proposals" which for v2
means picking from the 28-item catalog.)

### B. Symbol Universe & Diversification Analysis
(Same as v1 B1-B3. B2 uses the **6-gate** protocol including the new Gate 6:
correlation to v1 baseline portfolio < 0.85. B3 defaults to "per-symbol
individual models" in v2, reflecting the user's model-development preference.)

### C. Labeling Analysis
(Same as v1. For iter-v2/001, inherit v1's ATR labeling parameters (2.9/1.45
for large cap, 3.5/1.75 for mid cap) to isolate the variables under test.
Labeling experimentation deferred to iter-v2/002+.)

### D. Feature Frequency & Lookback Analysis
(Same as v1.)

### E. Trade Pattern Analysis
(Same as v1. Pay extra attention to regime breakdown using `per_regime_v2.csv`.)

### F. Statistical Rigor
(Same as v1.)

### G. Stationarity & Memory Analysis
(UPGRADED from v1. v2 ships fracdiff as a baseline feature, not an optional
experiment. G is relevant when the QR wants to adjust `d` per symbol or
experiment with different series to fractionally differentiate.)

### H. Overfitting Audit
(Same as v1. DSR now mandatory every iter; PBO from iter-v2/003.)

### I. NEW — Risk Management Analysis (MANDATORY EVERY ITERATION)

Every v2 brief answers:

1. Which of the 8 risk primitives are active this iteration? Why are
   disabled ones disabled?
2. What is the expected fire rate of each active gate on IS data?
3. Which training-window regimes are under-represented (<5% of training)?
   These are where the OOD gates will bite.
4. Does the current feature catalog provide enough signal for the risk layer
   (i.e., does it expose Hurst, ATR percentile, etc. as usable inputs)?
5. What is the pre-registered failure-mode prediction? (carries to Section
   6.3 of the brief)

If the QR cannot answer Category I in 2 paragraphs, the brief is incomplete
and Phase 6 cannot start.

---

## Diversification Research Protocol

**In v2, diversification is the entire track's purpose, not a side goal.**
Every v2 iteration is structurally a diversification iteration. The 6-gate
symbol-screening protocol applies to every symbol change.

### Progressive Expansion Roadmap (v2)

**Stage 1 — Initial v2 baseline (iter-v2/001)**:
- 3 individual models (Models E, F, G), 1 symbol each
- Symbols chosen via the 6-gate protocol from the non-v1 universe
- MVP risk layer active
- DSR + regime-stratified Sharpe validation

**Stage 2 — v2 refinement (iter-v2/002-005)**:
- Tune the 4 MVP risk gates (fire-rate calibration)
- Add CPCV validation
- Try a 4th v2 symbol if Gate 6 passes

**Stage 3 — v2 expansion (iter-v2/006-009)**:
- Add PBO + ACF embargo
- Enable 1-2 of the deferred risk primitives (drawdown brake, BTC contagion)
- Target 4-6 v2 symbols

**Stage 4 — Combined portfolio readiness (iter-v2/010+)**:
- Correlation analysis v2 vs v1 at the full-portfolio level
- Prepare for the `main` branch merge that creates `run_portfolio_combined.py`

### Cross-asset feature strategy for v2

v2 does NOT use v1's `xbtc_*` features directly (they live in
`crypto_trade.features.cross_asset` which is forbidden). However, v2 MAY
compute its own BTC-derived features in `features_v2/regime.py` as long as
the implementations are independent. For iter-v2/001, skip cross-asset
features — keep the first iteration clean and focused. Add in iter-v2/002+
if the diary identifies it as the bottleneck.

---

## QR: Deep Analysis & Bold Ideas (Phase 7)

Same as v1. Read the IS quantstats HTML. Analyze trades deeply. Propose bold,
structural changes — not incremental tweaks. Review `lgbm.py` AND
`risk_v2.py` (v2-specific). Reference the Research Checklist + Category I.
Quantify the gap explicitly.

**v2 addition**: always include a **gate-efficacy post-mortem** per Section
6.5 of the brief schema. Compare actual gate fires to the pre-registered
failure-mode prediction.

---

## QE: Trade Execution Verification (Phase 6)

Same as v1, plus v2-specific steps:

1. Sample 10-20 trades from `trades.csv` and verify entry/exit/PnL math.
2. Check exit reasons are consistent (SL ≈ -sl_pct, TP ≈ +tp_pct).
3. Document anomalies in the engineering report.
4. **Label leakage audit** (MANDATORY): `gap = (timeout_candles + 1) × n_symbols`.
5. **v2: Symbol exclusion audit**: `assert set(cfg.symbols).isdisjoint(V2_EXCLUDED_SYMBOLS)`.
6. **v2: Feature isolation audit**: `grep -r "from crypto_trade.features " src/crypto_trade/features_v2/` must be empty.
7. **v2: Risk layer audit**: verify `RiskV2Wrapper` wraps the inner strategy
   and that the 4 MVP gates are actually being consulted on each signal
   (log `get_signal` decisions for 20 random candles).
8. **v2: Feature parquet audit**: verify the run loaded from `data/features_v2/`
   and NOT `data/features/`.

---

## Code Quality (QE) — v2

Same as v1 plus:
- v2 code must NOT import from `crypto_trade.features` (audit on every commit)
- `RiskV2Wrapper` state must be deterministic — seeded `np.random` where used
- `RiskV2Config` is frozen (dataclass frozen=True) to prevent accidental mutation
- Training-window feature stats snapshotted via `compute_features()` and
  never updated mid-backtest

---

## Exploration / Exploitation Protocol — v2

Same 70/30 rule. Every v2 iteration MUST be tagged as **EXPLORATION** or
**EXPLOITATION** in the research brief header.

### v2 definitions

**EXPLOITATION** — improves the current best v2 approach by tuning within
the existing architecture:
- Changing symbol selection within the 6-gate pool
- Adjusting TP/SL by ≤50%, timeout, training window, CV folds, Optuna trials
- Adjusting risk-layer gate thresholds (adx_threshold, zscore_threshold, etc.)
- Turning on a deferred risk primitive (drawdown brake → enabled) — this is
  exploitation of a known technique, not a new approach

**EXPLORATION** — tests a fundamentally different approach:
- Adding a new feature family to `features_v2/`
- Changing model type (classification → regression)
- Adding CPCV/PBO to the validation stack (iter-v2/002 and 003 are explore)
- Switching model architecture from individual to cluster models
- Regime-dependent LightGBM (separate model per Hurst bucket)
- Using v2's risk layer for online retraining (flag regime shift → retrain)

### v2 Exploration Idea Bank — Tier 1 (start empty, will grow)

1. **Isolation Forest anomaly scoring** (deferred risk primitive #7) — unsupervised
   OOD detection on feature vectors. iter-v2/003 or later.
2. **Regime-dependent LightGBM** — separate model per Hurst bucket. Conditional
   on iter-v2/001 showing regime-stratified Sharpe imbalance.
3. **BTC contagion circuit breaker** (deferred risk primitive #6) — cross-v1
   dependency. Requires plumbing to read v1's parquet.
4. **CPCV with PBO** — planned for iter-v2/002-003 already.
5. **Cross-v1 portfolio correlation feature** — compute rolling 30-day
   correlation of the candidate symbol's returns to v1's portfolio returns
   and feed it as a feature. Model learns to reduce exposure when contagion risk is high.
6. **Online feature stat updates** — refresh training-window feature stats
   between walk-forward months (currently snapshotted once per model).
7. **Meta-labeling for v2** (AFML Ch. 3) — train a secondary model on
   "was the primary's signal profitable." Feeds into Kelly sizing.

### Dead ideas (initially empty for v2)

v2 starts with no dead ideas. As iterations fail, populate a table similar
to v1's:

| Idea | Iter(s) | Why it failed |
|------|---------|--------------|
| _(none yet)_ | — | — |

---

## Key Reminders — v2

- The `reports-v2/` directory is in `.gitignore`. The diary captures key
  metrics (IS + OOS) in text form, which is what persists.
- The OOS cutoff date is in `src/crypto_trade/config.py` (shared with v1),
  every v2 research brief (Section 0), every v2 diary, and `BASELINE_V2.md`.
  It is always `2025-03-24`. Always.
- v2 commits go to `quant-research`, NEVER to `main`.
- v2 never imports from `crypto_trade.features`.
- v2 runners never include BTCUSDT, ETHUSDT, LINKUSDT, BNBUSDT unless the
  user explicitly instructs.
- `BASELINE_V2.md` is updated only after a successful MERGE.
- Analysis charts are untracked. Describe findings in text.
- One variable at a time between iterations. Attribution is the point.
- Read the previous diary before starting a new iteration.
- After Phase 8, **keep looping** — this is autopilot.

---

## Quick-start command (for the human user)

```
# User invocation:
/quant-iteration-v2

# The skill then:
# 1. Reads BASELINE_V2.md + diary-v2/iteration_NNN-1.md "Next Iteration Ideas"
# 2. Creates branch iteration-v2/NNN from quant-research
# 3. QR: Phases 1-5 → produce briefs-v2/iteration_NNN/research_brief.md
# 4. QE: Phase 6 → implement, run walk-forward, write engineering_report.md
# 5. QR: Phases 7-8 → evaluate, write diary-v2/iteration_NNN.md with MERGE decision
# 6. Commit + tag + merge per git workflow
# 7. Loop to next iteration unless user intervenes
```
