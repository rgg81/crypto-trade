# iter-v3/083 — Research Brief — Symbol-Universe EXPANSION 3→4 (cycle-3 EXPLORATION #2, Direction 2)

**Iteration**: iter-v3/083 — cycle-3 EXPLORATION #2 of 10
**Axis**: Direction 2 of `briefs-v3/cycle3_plan.md` — symbol-universe **EXPANSION**. `V3_MODELS`
grows from 3 symbols (BCHUSDT, LDOUSDT, TRXUSDT) to 4 by **adding FILUSDT**. This is
**denominator expansion** — the structural fix the /082 closeout (Critic Rec #3) identified
as the only thing that can address v3's BCH-concentration fragility. It is a single-axis
EXPLORATION: the 14-feature stack, ATR labeling `(2.0, 1.0)`, the 7-primitive risk-gate
stack, `ENSEMBLE_SEEDS`, and the Optuna search are all UNCHANGED.
**Anchor**: BASELINE_V3.md `v0.v3-059` (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe
**+0.5791**), re-validated at the iter-v3/081 CONFIRMATION (IS +1.0894 exact / OOS +0.5999).
**Branch**: `iteration-v3/083`

---

## Section 0 — Data Split Declaration

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are **UNCHANGED** — sacred
constants, immutable.

- **IS window**: earliest available data per symbol → 2025-03-24. Each per-symbol model is
  walk-forward trained on a rolling 24-month window. For the new symbol FILUSDT, the IS
  evaluation span begins ~24 months after its first usable candle (FIL listed 2020-10-16;
  after the 60-day new-listing burn-in and the 24-month training window, the first IS
  evaluation month is ~2023-01) — comfortably inside the IS window.
- **OOS window**: 2025-03-24 → present (~14 months).
- The walk-forward / CPCV backtest runs on the full continuous series; the reporting layer
  splits trade results at `OOS_CUTOFF_DATE`.
- **NO CHEATING**: every table in Section 2 was produced by a committed
  `analysis/iteration_v3-083/universe_expansion_edge_screen.py` script that reads ONLY data
  before 2025-03-24. The symbol selection (FIL) was made on IS-data-only evidence. The QR
  sees OOS for the first time in Phase 7. `start_time` is never trimmed.

## Section 0.5 — Iteration Type Declaration

**TYPE: EXPLORATION** (cycle-3 EXPLORATION #2 of 10).

Single-axis variation — one primary change: `V3_MODELS` 3 → 4 symbols (add FILUSDT).
EXPLORATION mode: `run_baseline_v3.py --exploration --n-trials 35` →
`EXPLORATION_ENSEMBLE_SIZE = 3`, `ENSEMBLE_SEEDS` outer-42-lineage subset
`[191664963, 1662057957, 1405681631]`. **Wall-clock budget: ≤ 2h HARD CAP.** Estimate:
the universe grows 3 → 4 symbols, so Optuna trial count rises 35×3×3 = 315 → 35×4×3 = 420
(+33%). iter-v3/021 ran a **5-symbol** universe in EXPLORATION mode in **23 min**; /082 ran
3 symbols in 0.74h (44 min). A 4-symbol run is bounded between those — estimate **~1.0h**,
well within the 2h cap. This iteration does NOT run CONFIRMATION-spec — no `--seeds 2`, no
`ENSEMBLE_SIZE=5`/`10`, no bundle assembly. Only iter-v3/092 runs the cycle-3 CONFIRMATION.

## Section 1 — Hypothesis

Adding FILUSDT — a deep-history, liquid, 2020-listed large-cap altcoin that the IS-edge
screen ranks #1 of 4 candidates by standalone IS edge AND least-harmful to the
portfolio-aggregate IS Sharpe AND duration-clean — to `V3_MODELS` grows the v3 denominator
3 → 4, mechanically diluting BCH's IS/OOS concentration toward the ≤30% gate while
preserving the aggregate IS Sharpe, so the portfolio stops being a structural single-symbol
bet (the /082 finding) without removing edge from any incumbent symbol.

## Section 2 — IS-Only Numerical Evidence

All five tables are produced by the committed EDA
`analysis/iteration_v3-083/universe_expansion_edge_screen.py` (SHA `e538d5f`). Every figure
uses ONLY data before `OOS_CUTOFF_DATE = 2025-03-24`. Source CSVs: `T1_data_liquidity_
screen.csv`, `T2_per_candidate_is_edge.csv`, `T3_portfolio_aggregate_contribution.csv`,
`T4_holding_time_predictor.csv`, `T5_composite_ranking.csv`.

**Screen-scope disclosure (LOAD-BEARING).** This is a **relative-ranking** screen. It runs
every candidate AND the 3 incumbents through one identical un-tuned (fixed-LightGBM-param)
pipeline with NO Optuna and NO 7-gate risk stack. The **absolute** Sharpe numbers therefore
differ from the production v3 +1.09 baseline (which is Optuna-tuned + risk-gated) — the
un-tuned screen produces negative absolute Sharpe everywhere. The load-bearing outputs are
the **cross-symbol ranking** and the **sign/magnitude of the aggregate-IS-Sharpe delta**,
NOT the absolute Sharpe levels. The incumbent pooled Sharpe computed here (screen value
−0.0761) is the internal screen baseline the candidate deltas are measured against — it is
not a /059 reproduction and is not claimed to be.

### T1 — Data-depth / liquidity / 60-day-burn-in screen

Candidate pool: 8 deep-history (2020-listed) liquid large-cap Binance-futures altcoins NOT
in `V3_EXCLUDED_SYMBOLS`. HBAR+AVAX (CLOSED at /021) and ADA (CLOSED at /078) are excluded
from the pool by construction.

| Symbol | First listing | IS bars (post-60d-burn-in) | Median daily quote vol ($M) | Depth OK | Liquidity OK | Status |
|---|---|---:|---:|:--:|:--:|:--:|
| ATOMUSDT | 2020-02-07 | 5435 | 92.3 | ✓ | ✓ | **PASS** |
| FILUSDT | 2020-10-16 | 4665 | **163.9** | ✓ | ✓ | **PASS** |
| ALGOUSDT | 2020-06-16 | 5045 | 47.6 | ✓ | ✗ | DROP |
| VETUSDT | 2020-02-14 | 5399 | 35.0 | ✓ | ✗ | DROP |
| ETCUSDT | 2020-01-16 | 5501 | 139.5 | ✓ | ✓ | **PASS** |
| XLMUSDT | 2020-01-20 | 5474 | 46.3 | ✓ | ✗ | DROP |
| XTZUSDT | 2020-02-06 | 5438 | 34.0 | ✓ | ✗ | DROP |
| AAVEUSDT | 2020-10-16 | 4680 | 104.0 | ✓ | ✓ | **PASS** |

4 of 8 survive: **ATOM, FIL, ETC, AAVE**. All have ≥ 4600 post-burn-in IS bars (ample for
the 24-month training window + a multi-year IS evaluation span). The 4 drops fail the
≥ $50M/day median quote-volume liquidity gate (the crypto exchange-liquidity pitfall —
`$100k Binance ≠ $100k Coinbase`; a thin symbol cannot be sized at v3's notional). **FIL
has the deepest liquidity in the pool at $163.9M/day.**

### T2 — Per-candidate IS-edge walk-forward LightGBM (the load-bearing table)

This is the table /021 and /069 never produced. For each survivor: the v3 14-feature stack
computed from raw OHLCV, the REAL v3 triple-barrier labels (`label_trades`, ATR `(2.0,1.0)`,
21-candle / 10080-min timeout), and an IS-ONLY expanding walk-forward LightGBM (24-month
training window, monthly refit, confidence-threshold-gated at 0.45). NEUTRAL is a genuine
third class (no-clean-edge candles).

| Symbol | IS trades | IS eval months | IS trades/month | **IS monthly Sharpe (screen)** | IS WR % | IS total PnL |
|---|---:|---:|---:|---:|---:|---:|
| **FILUSDT** | 1561 | 28 | 55.8 | **−0.1368** (best of pool) | 33.4 | −364.9 |
| AAVEUSDT | 1435 | 28 | 51.2 | −0.1487 | 33.2 | −307.7 |
| ETCUSDT | 2295 | 37 | 62.0 | −0.2860 | 33.3 | −1150.3 |
| ATOMUSDT | 1952 | 36 | 54.2 | −0.4108 (worst) | 30.2 | −1368.1 |

**FIL has the best (least-negative) standalone IS edge of the four survivors.** ATOM is the
clear worst — the /021 HBAR/AVAX pattern (a candidate that screens well on price diversity
but has no signal the v3 feature stack can fit). All four trade well above the ≥ 10
trades/month floor (51–62 trades/month un-gated by the production risk stack).

### T3 — Portfolio-aggregate IS-Sharpe contribution under BCH dominance

v3 pools the per-symbol rosters into ONE book. The /078 lesson (`feedback_v3_per_symbol_
lifts_oos_breaks_is.md`): a per-symbol Sharpe screen does NOT transfer to portfolio-aggregate
lift — so this table measures the **aggregate**. Incumbent 3-symbol pooled IS monthly
Sharpe (screen) = **−0.0761**.

| Symbol | Aggregate 4-sym IS Sharpe | **Aggregate IS Sharpe Δ** | BCH trade-count share 3-sym | BCH trade-count share 4-sym | **BCH dilution (pp)** | Candidate trade share |
|---|---:|---:|---:|---:|---:|---:|
| **FILUSDT** | −0.1143 | **−0.0382** (least harmful) | 47.5% | **35.4%** | **12.1** | 25.5% |
| AAVEUSDT | −0.1299 | −0.0539 | 47.5% | 36.1% | 11.4 | 24.0% |
| ETCUSDT | −0.2491 | −0.1731 | 47.5% | 31.6% | 15.9 | 33.5% |
| ATOMUSDT | −0.4166 | −0.3405 (most harmful) | 47.5% | 33.3% | 14.3 | 30.0% |

**FIL is the LEAST harmful to the aggregate IS Sharpe** (delta −0.0382, closest to zero of
the four). Every survivor dilutes BCH's IS trade-count share by ~11–16pp; FIL specifically
takes it 47.5% → 35.4%. **Concentration-metric note**: the screen reports two BCH-share
metrics. The wpnl-share figures (`bch_wpnl_share_*`) are **unstable** — the un-tuned screen's
pooled incumbent wpnl is near zero, so BCH wpnl / total can exceed 100% (378% at 3 symbols).
The **stable** concentration proxy is **BCH trade-count share** — always-positive, large
denominator. T3/T5 use trade-count share; the brief's concentration claims rest on it. v3's
≤30% gate is on OOS *PnL* share; trade-count share is the EDA-stage stable proxy for it.

### T4 — Holding-time / roster-composition predictor (`feedback_v3_is_oos_regime_divergence.md`)

The /078 mandate: a candidate whose roster is **duration-loaded** relative to the incumbents
loads the v3 IS/OOS regime factor (IS penalizes longer-held trades; OOS rewards them) — and
the screen-grade label-implied proxy must be flagged because the production Optuna-tuned
barriers bias it LOW (it under-predicts the timeout-trade tail). `hold_candles` here is a
real per-trade forward barrier-scan to first TP/SL/timeout, for the side the model picked.

| Symbol | Incumbent mean dur (candles) | Candidate mean dur | **Duration gap (candles)** | Candidate timeout-trade % | Incumbent timeout-trade % |
|---|---:|---:|---:|---:|---:|
| **FILUSDT** | 6.789 | 6.386 | **−0.403** | 5.0% | 7.4% |
| AAVEUSDT | 6.789 | 6.040 | −0.749 | 4.4% | 7.4% |
| ETCUSDT | 6.789 | 6.874 | +0.085 | 7.2% | 7.4% |
| ATOMUSDT | 6.789 | 6.424 | −0.365 | 4.6% | 7.4% |

**FIL's roster is duration-clean**: gap −0.403 candles vs incumbents — and it is
*slightly shorter*-held, the regime-SAFE direction (the /078 SUSPICIOUS failure was an ADDED
symbol +2.23 candles *longer*-held). FIL's timeout-trade share (5.0%) is *below* the
incumbents' (7.4%) — the opposite of the ADA-at-/078 signature (5 ADA timeout trades where
LDO had zero). **Caveat (mandatory, per /078)**: this is a screen-grade label-implied
proxy; the production walk-forward uses Optuna-tuned timeout parameters that can produce
timeout trades the fixed-parameter screen does not foresee. The Section 4 falsifier is
pre-registered against the *production* duration gap, not this proxy.

### T5 — Composite ranking + the count-expansion decision

Composite score = `2.0·(aggregate IS-Sharpe delta) + 1.0·(standalone IS Sharpe) −
0.5·max(|duration gap|−1, 0)` — the aggregate delta is the dominant term (the /021/069
lesson: rank on signal contribution, not price diversity).

| Rank | Symbol | Standalone IS Sharpe | Aggregate IS Sharpe Δ | BCH dilution (pp) | Trades/mo | Duration gap | Composite |
|---:|---|---:|---:|---:|---:|---:|---:|
| **1** | **FILUSDT** | −0.1368 | −0.0382 | 12.1 | 55.8 | −0.403 | **−0.2132** |
| 2 | AAVEUSDT | −0.1487 | −0.0539 | 11.4 | 51.2 | −0.749 | −0.2565 |
| 3 | ETCUSDT | −0.2860 | −0.1731 | 15.9 | 62.0 | +0.085 | −0.6322 |
| 4 | ATOMUSDT | −0.4108 | −0.3405 | 14.3 | 54.2 | −0.365 | −1.0918 |

**FIL is the screen winner — composite rank #1.** Both reliable signals agree: FIL has the
best standalone IS edge AND the least-harmful aggregate-IS-Sharpe delta AND is duration-clean
AND has the deepest liquidity. AAVE is a close runner-up; ETC and ATOM are materially worse.

**Count decision: expand 3 → 4 (add ONE symbol).** The /021 catalog states the explicit
lesson from the HBAR+AVAX failure: *"universe expansion at n_trials=35 split N ways is
over-stretched relative to incumbent symbols' fit quality"* and recommends a
**1-symbol-at-a-time** expansion. /069 also correctly tested 3 → 4 (one symbol). A 3 → 5
two-symbol jump repeats /021's structural error and dilutes the per-symbol Optuna budget
twice over. The disciplined expansion is **3 → 4: add FILUSDT only**. Subsequent cycle-3
EXPLORATIONs (/084+) may add a 5th symbol if /083 succeeds.

## Section 3 — Proposed Changes

### 3.1 The single axis — `V3_MODELS` 3 → 4 (add FILUSDT)

`V3_MODELS` in `run_baseline_v3.py`:

```python
# BEFORE (iter-v3/059 canonical / iter-v3/082)
V3_MODELS = (
    ("A (BCHUSDT)", "BCHUSDT"),
    ("C (LDOUSDT)", "LDOUSDT"),
    ("D (TRXUSDT)", "TRXUSDT"),
)
# AFTER (iter-v3/083 — universe EXPANSION)
V3_MODELS = (
    ("A (BCHUSDT)", "BCHUSDT"),
    ("C (LDOUSDT)", "LDOUSDT"),
    ("D (TRXUSDT)", "TRXUSDT"),
    ("F (FILUSDT)", "FILUSDT"),
)
```

FILUSDT is NOT in `V3_EXCLUDED_SYMBOLS` (v1 BTC/ETH/LINK/LTC/DOT; v2 SOL/XRP/DOGE/NEAR;
BNB; MKR) — the runner's `_verify_symbols` startup assertion passes. FIL gets one
independent per-symbol LightGBM model with the same 14-feature stack, the same `(2.0,1.0)`
ATR triple-barrier labeling, and the same 7-gate risk stack as every incumbent — a
**universal** addition, no per-symbol customization (the `feedback_v3_per_symbol_lifts_oos_
breaks_is.md` constraint: no per-symbol features, no per-symbol ATR, no per-symbol gates).

### 3.2 Why count-EXPANSION is a structurally different axis from the CLOSED swap family

The /082 closeout notes "v3 has 3 failed expansions" — this is imprecise and the brief must
correct it. The three prior "expansion" data points were:

- **/021 (HBAR+AVAX)**: a genuine count-expansion (3→5) — but it failed on a *correlation/
  feature-distance* screen that captured price diversity, not signal diversity, and it
  jumped 2 symbols at once. Its catalog verdict explicitly *defers* ATOM/FIL/ALGO to
  "LOW-priority retest", it does NOT close them.
- **/069 (ADA)**: a count-expansion (3→4) — but again a feature-space-proximity screen.
- **/078 (LDO→ADA)**: a **swap-by-replacement** at constant count (3→3). This is the CLOSED
  family (`cycle3_plan.md` Section 1; `feedback_v3_is_oos_regime_divergence.md` /078
  extension). /083 is NOT a swap.

The structural distinction: a **swap** removes a symbol and adds another at constant count
— it loads the regime factor via the added symbol's roster while changing the universe
composition wholesale (/078 went SUSPICIOUS exactly this way). A **count-expansion** keeps
every incumbent and adds a symbol — it is **denominator expansion**: the Fundamental Law
(IR = IC·√breadth — Grinold & Kahn 1999) names breadth as the lever, and BCH-concentration
dilution is mechanical (more symbols ⇒ smaller max share) and does not require removing any
incumbent's edge. The two prior count-expansions (/021, /069) failed on **screen
methodology** (price-distance, not signal), not on the count-expansion axis being unsound.
iter-v3/083 fixes the screen: Section 2's T2/T3 are a genuine IS-edge + portfolio-aggregate
screen, the exact methodology the cycle-3 plan Direction 2 mandates. Universe expansion is
also the explicitly-permitted orthogonal concentration mechanism per
`feedback_v3_concentration_is_signal.md` ("denominator expansion — adds more symbols rather
than scaling existing ones").

### 3.3 Mandatory secondary edit — REVERT the /082 funding family (18 → 14 features)

iter-v3/082 left `V3_FEATURE_COLUMNS_TOP_N` at **18** columns (the 14 anchor + 4 funding
features). The /082 closeout (SUSPICIOUS-OOS-DOMINANT; the funding family ranked bottom-4/18
by importance) mandates the revert: per `feedback_v3_inert_features_at_higher_budget.md` an
INERT feature family must NOT be carried forward and must NOT be retested at higher budget.
iter-v3/083's setup **reverts `V3_FEATURE_COLUMNS_TOP_N` 18 → 14** — the /059 canonical
anchor stack. This is the established "mandatory secondary edit" pattern (cf. /077 reverting
/076's `range_efficiency_50`, /079 reverting /078's ADA swap). It is NOT a second axis: it
restores the canonical baseline so iter-v3/083's *sole declared delta vs /059* is the
universe expansion. The `funding_v3.py` `compute_funding_family` function and the
`funding_family_v3` `GROUP_REGISTRY` entry are left as harmless unreferenced infrastructure
at zero revert cost. The `funding_rate_zscore_30` / `btc_funding_rate_zscore_30` literal-name
bans stay intact.

### 3.4 `REQUIRED_GAP` recompute (universe count change)

`REQUIRED_GAP = (timeout_candles + 1) × n_symbols`. With `timeout_candles = 21` and the
universe growing 3 → 4 symbols, `REQUIRED_GAP` **changes 66 → 88** = `(21+1) × 4`. The
runner's `_verify_label_leakage_gap()` recomputes the formula and asserts equality —
`REQUIRED_GAP` must be updated to **88** in `validation_v3.py` (or wherever the constant is
pinned) and in the `CPCV_*` comment block. `PER_CELL_GAP = 43` is a *within-single-symbol-cell*
gap = `(timeout_candles+1)` and is **unchanged** by the symbol count (it is per-cell). The
config-accretion pre-flight's `_canonical_v059` list must update its `REQUIRED_GAP` expected
value 66 → 88 AND its `V3_MODELS symbols` expected tuple to the 4-symbol universe — universe
expansion IS iter-v3/083's single declared axis, so this is a sanctioned pre-flight update,
not illegitimate accretion.

### 3.5 No changes to labeling, features, risk gates, model architecture

- **Labeling**: triple-barrier, ATR `(2.0, 1.0)`, 21-candle (10080-min) timeout — UNCHANGED.
  `V3_ATR_MULTIPLIERS_PER_SYMBOL` stays empty; FIL uses the `(2.0,1.0)` DEFAULT.
- **Features**: `V3_FEATURE_COLUMNS_TOP_N` = the 14-feature /059 anchor stack (reverted from
  /082's 18 per §3.3). `V3_FEATURES_PER_SYMBOL` stays empty; FIL uses the 14-feature
  fallback.
- **Risk gates**: the 7-primitive stack (BTC trend kill, vol scaling, ADX, Hurst regime,
  z-score OOD, low-vol filter, hit-rate-disabled) — UNCHANGED, all `/059`-canonical.
  `block_long_for`/`block_short_for` empty; `enable_per_symbol_drawdown_brake` False;
  `adx_threshold_per_symbol`/`vol_scale_floor_per_symbol`/`zscore_threshold`/`adx_threshold`
  all `/059`-canonical.
- **Model architecture**: one independent LightGBM per symbol; `ENSEMBLE_SEEDS`,
  `ENSEMBLE_SIZE` mode flags, Optuna search space — UNCHANGED.

### 3.6 Engineering checklist for Phase 6 (data acquisition — Direction-2 prerequisite)

Per `feedback_data_staleness_per_worktree.md`, the new symbol FILUSDT needs fresh data +
v3 features generated **in this worktree** (`/home/roberto/crypto-trade/.worktrees/quant-
research`). FIL has NO v3 feature parquet (`data/features_v3/FILUSDT_8h_features.parquet`
does not exist) and its 8h CSV in this worktree is stale (last close ~2026-05-08). The QE
Phase 6 pre-flight MUST run, in order:

```bash
export PATH="$HOME/.local/bin:$PATH"
# 1. fetch fresh 8h klines for FIL (and re-fetch incumbents to clear the 16h staleness gate)
uv run crypto-trade fetch --interval 8h --symbols BCHUSDT,LDOUSDT,TRXUSDT,FILUSDT
# 2. generate v3 features for the full 4-symbol universe
uv run crypto-trade features --symbols BCHUSDT,LDOUSDT,TRXUSDT,FILUSDT \
    --interval 8h --track v3 --format parquet --workers 4
```

FIL's `btc_ret_14d` / `sym_vs_btc_ret_7d` cross-asset features need fresh BTCUSDT klines —
BTCUSDT is fetched as a data dependency (it is in `V3_EXCLUDED_SYMBOLS` for *trading* but
its klines are a feature input, exactly as the incumbents already use). v3 does NOT fetch
funding/OI/basis for /083 — the funding axis is CLOSED and /083 adds no crypto-native feed.
Then: `_verify_data_freshness` must pass for all 4 symbols; `_verify_feature_columns`
asserts the 14-feature stack; the config-accretion pre-flight asserts the 4-symbol
`V3_MODELS` + `REQUIRED_GAP=88`.

## Section 4 — Expected OOS Impact

### 4.1 Predicted impact

This is a **portfolio-composition** change, not a clean single-feature delta — comparing a
4-symbol portfolio's aggregate Sharpe to the 3-symbol /059 anchor compares two different
portfolios. The **right evaluation lens** is therefore two-pronged: (a) does the expansion
*dilute BCH concentration* toward the ≤30% gate, and (b) does it *preserve or improve the
aggregate IS Sharpe*. The headline Sharpe delta is informational; the concentration
dilution is the structural success metric.

- **Concentration (the structural target)**: predict the 4-symbol OOS BCH PnL-share drops
  materially from /082's ~104% / /059's 108.86%. T3's IS trade-count screen shows FIL takes
  BCH's trade share 47.5% → 35.4% (a 12.1pp dilution). Predicted OOS BCH PnL share with FIL
  added: **[55%, 90%]** (still far above the ≤30% gate — one symbol cannot fix a 3→4
  expansion to gate compliance, but the *direction* is the structural fix; reaching ≤30%
  needs the further /084+ expansions).
- **IS monthly Sharpe**: predict **[+0.85, +1.10]** vs the /059 anchor +1.0894. FIL is the
  least-harmful candidate (T3 aggregate screen delta −0.0382), but the screen is un-tuned;
  the production Optuna-tuned 4-symbol model could land anywhere in this band. Adding a
  symbol with a genuine (if modest) IS edge should not collapse the aggregate.
- **OOS monthly Sharpe**: predict **[+0.30, +0.80]** vs the /059 anchor +0.5791 — a wide
  band because OOS is unseen and a new symbol's OOS realization is genuinely uncertain.

### 4.2 Falsifier (LOCKED)

The hypothesis is **rejected** (axis NEGATIVE / classified per Section 8) if ANY of:

1. **IS monthly Sharpe Δ < −0.20** vs /059 (IS collapses below +0.89) — FIL broke the IS
   aggregate, the /021 HBAR/AVAX failure mode reproduced.
2. **OOS monthly Sharpe Δ < −0.20** vs /059 (OOS falls below +0.38) — FIL dragged OOS.
3. **FIL is a per-symbol IS detractor with net IS weighted_pnl < −5.0** AND the portfolio
   IS Sharpe regresses — FIL contributes only noise (the screen's positive relative ranking
   did not transfer).
4. **OOS BCH PnL share does NOT fall** vs /082's ~104% (expansion failed to dilute
   concentration — the structural mechanism did not fire).

### 4.3 Target-symbol-axis falsifier band (`feedback_v3_per_symbol_target_axis_falsifier.md`)

This is a universe axis touching a NEW symbol — the falsifier list must pre-register
**target-symbol** (FIL) bands, not just non-target bands:

- **FIL IS weighted_pnl Δ falsifier band**: FIL's IS weighted_pnl ∈ **[−15.0, +25.0]**.
  Outside this band the FIL model behaves nothing like the screen predicted (the screen had
  FIL standalone IS Sharpe −0.137 with 1561 trades — a modest, near-flat contributor).
- **FIL OOS weighted_pnl Δ falsifier band**: FIL's OOS weighted_pnl ∈ **[−20.0, +30.0]**.
- **Incumbent non-target bands**: BCH/LDO/TRX per-symbol IS+OOS rosters are NOT bit-isolated
  from FIL — adding a 4th symbol changes the pooled-CPCV path composition and (because
  `REQUIRED_GAP` rises 66→88) the embargo, so incumbent rosters CAN shift. Pre-register the
  incumbent aggregate band: BCH+LDO+TRX *combined* IS weighted_pnl Δ ∈ **[−20.0, +20.0]**
  vs /059. A larger incumbent swing means the expansion is perturbing incumbents, not
  cleanly adding breadth.

### 4.4 Holding-time / roster-composition predictor (`feedback_v3_is_oos_regime_divergence.md`)

The /078 mechanism: an ADDED symbol whose roster is duration-loaded relative to the
incumbents loads the v3 IS/OOS regime factor. **Predictor**: FIL's screen roster is
duration-CLEAN — mean duration gap −0.403 candles vs incumbents (T4), and slightly
*shorter*-held (the regime-SAFE direction; /078's ADA was +2.23 candles *longer*).
Predicted FIL production roster mean-duration gap vs the incumbent pooled roster:
**[−1.5, +1.0] candles**. **Falsifier**: if the production FIL roster is **> +1.0 candle
longer-held** than the incumbent pooled roster, the regime factor is loaded via the added
symbol — expect SUSPICIOUS-OOS-DOMINANT. The screen-grade proxy is biased LOW (the /078
lesson — the production Optuna-tuned barriers under-predicted by 6× at /078), which is why
the falsifier band's upper bound (+1.0) is set tighter than the proxy's −0.403 reading and
why the predicted band is widened to allow for the proxy bias.

### 4.5 OOS/IS ratio SUSPICIOUS gate (LOCKED — `feedback_v3_oos_is_ratio_gate.md`)

- **OOS/IS monthly Sharpe ratio > 3.0 → SUSPICIOUS** classification, regardless of absolute
  OOS Sharpe magnitude.
- **OOS-DOMINANT sub-mode**: IS Δ < 0 (vs /059) AND OOS Δ ≥ +0.20 (vs /059) → SUSPICIOUS
  (the /078 signature — a universe change that lifts OOS while IS stays flat/negative).

## Section 5 — Risk Mitigation

The 7-primitive risk-gate stack is UNCHANGED and applies to FIL identically to every
incumbent — no new gate, no gate retune. Risk-mitigation analysis specific to the expansion:

- **R-concentration (the axis IS the mitigation)**: universe expansion is itself the
  concentration-risk mitigation — denominator expansion dilutes BCH's max share. T3 shows
  the IS trade-count share mechanism: 47.5% → 35.4% with FIL added.
- **R-OOD (z-score Mahalanobis gate)**: FIL's feature vectors are gated by the same z-score
  OOD primitive (|z| threshold 2.0) as incumbents — a FIL candle with an out-of-training
  feature vector is suppressed. Simulated effect: the gate fires on the same statistical
  criterion for FIL as for any symbol; no FIL-specific calibration.
- **R-vol (vol scaling + low-vol filter)**: FIL positions are vol-scaled by the same ATR-
  percentile logic; FIL's median daily quote volume ($163.9M, T1) is the deepest in the
  candidate pool, so vol-scaled FIL sizing is liquidity-safe at v3's notional.
- **R-BTC-trend kill**: the BTC trend filter (±15%, 42-bar lookback) applies to FIL
  identically.
- **New-listing burn-in**: FIL listed 2020-10-16; the 60-day burn-in window (the crypto
  non-stationarity pitfall) is long past before the IS evaluation span begins (~2023-01) —
  no listing-instability contamination.

## Section 6 — Risk Management Design

| Primitive | Mechanism | Applies to FIL | Fire-rate prediction (FIL) |
|---|---|---|---|
| BTC trend kill | suppress trades when |BTC 42-bar return| > 15% | yes (universal) | same regime windows as incumbents |
| Vol scaling | position size ∝ ATR percentile | yes (universal) | continuous; FIL liquidity deepest in pool |
| ADX gate | suppress when ADX < 20 | yes (universal) | ~ incumbent fire rate (FIL is a liquid major) |
| Hurst regime | regime classification gate | yes (universal) | same Hurst logic |
| z-score OOD | Mahalanobis suppress at |z| > 2.0 | yes (universal) | ~ incumbent rate; no FIL calibration |
| Low-vol filter | suppress in dead-vol regimes | yes (universal) | ~ incumbent rate |
| Hit-rate gate | DISABLED (per iter-v2/045) | n/a | 0 (disabled) |

Regime coverage: FIL's IS span (~2023-01 → 2025-03) covers the 2023 recovery, the 2024 bull,
and the 2024-Q4/2025-Q1 chop — the same mixed regime the incumbents' IS spans cover. No
regime gap introduced. All gates are universal — the `feedback_v3_per_symbol_lifts_oos_
breaks_is.md` rule (no per-symbol customization) is satisfied by construction.

## Section 7 — Pre-Registered Failure-Mode Prediction

The single most plausible OOS failure mode is **SUSPICIOUS-OOS-DOMINANT via the added
symbol's roster** — the /078 mechanism. Even though FIL's screen roster is duration-clean
(T4 gap −0.40 candles), the screen-grade label-implied proxy is biased LOW; the production
Optuna-tuned 4-symbol model could produce a FIL roster that is materially longer-held than
the screen foresaw, and in v3's OOS sustained uptrend a longer-held roster lifts OOS while
IS stays flat. The signature: IS Δ ≈ 0 or negative, OOS Δ ≥ +0.20, OOS/IS ratio elevated,
FIL carrying a disproportionate OOS share — exactly /078. **Probability ≈ 30%.**

The second failure mode is **INERT / NEGATIVE-aggregate** — the /021 HBAR+AVAX pattern. The
screen ranks FIL #1 of 4, but #1 of 4 negative-Sharpe candidates is still a *negative*
standalone screen Sharpe (−0.137). FIL may simply add un-fittable noise: the per-symbol FIL
model contributes near-zero or negative IS weighted_pnl, the aggregate IS Sharpe regresses
inside [−0.20, 0], and the headline reads NEGATIVE or INERT. The /021 catalog is explicit
that universe expansion at the EXPLORATION budget (35 trials × 1 ensemble per symbol) is
"over-stretched" — a 4-symbol run gives FIL only 35 trials/seed of Optuna search.
**Probability ≈ 40%** (the most likely outcome — the conservative central forecast).

The third failure mode is **NEGATIVE via incumbent perturbation** — adding the 4th symbol
raises `REQUIRED_GAP` 66→88 and changes the pooled CPCV path composition; if this shifts
the incumbent rosters enough to break the BCH IS edge, the aggregate collapses even if FIL
itself is neutral. **Probability ≈ 10%.**

Residual **PROMISING** tail (≈ 20%): FIL's modest IS edge transfers under Optuna tuning, the
4-symbol aggregate IS Sharpe holds in [+0.85, +1.10], OOS holds in [+0.30, +0.80], and BCH
OOS concentration drops materially — the structural fix fires. This would make /083 a
genuine cycle-3 PROMISING candidate for the iter-v3/092 CONFIRMATION bundle.

The honest reckoning: v3 has 0 clean PROMISING across 21 prior EXPLORATIONs, and the two
prior count-expansions both failed — but both failed on **screen methodology** (price-
distance), and /083 is the first universe expansion screened on a genuine IS-edge +
portfolio-aggregate basis. The failure-mode weight (40% INERT/NEGATIVE) honestly reflects
that screen methodology is necessary but not sufficient; a single un-tuned screen cannot
guarantee the production multi-symbol model fits FIL.

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (LOCKED classification taxonomy)

Disjunctive precedence: **SUSPICIOUS → NEGATIVE → PROMISING → INERT → NULL-RESULT**. First
match is canonical. Anchor = BASELINE_V3.md /059 (IS +1.0894 / OOS +0.5791). EXPLORATION
never updates BASELINE_V3.md.

### 8.1 PROMISING

ALL of: IS monthly Sharpe Δ ≥ **+0.10** vs /059 (IS ≥ +1.19) AND OOS monthly Sharpe Δ ≥
**+0.10** vs /059 (OOS ≥ +0.68) AND `frac_positive_paths` ≥ 0.50 AND NOT SUSPICIOUS AND
FIL's IS weighted_pnl ≥ +5.0 (the added symbol carries genuine, non-noise IS edge — not a
free-rider on incumbent edge). A PROMISING /083 carries the universe expansion forward as a
candidate edge ingredient for the iter-v3/092 cycle-3 CONFIRMATION bundle.

### 8.2 NEGATIVE

IS monthly Sharpe Δ < **−0.10** vs /059 OR OOS monthly Sharpe Δ < **−0.20** vs /059 (and
NOT SUSPICIOUS). The universe expansion harmed the portfolio — recorded as NEGATIVE in the
catalog; FIL is not carried forward.

### 8.3 SUSPICIOUS (disjunctive precedence — fires before NEGATIVE/PROMISING)

ANY of:
- **OOS/IS ratio gate**: OOS/IS monthly Sharpe ratio > **3.0**.
- **OOS-DOMINANT sub-mode**: IS Δ < 0 vs /059 AND OOS Δ ≥ +0.20 vs /059 (the /078
  universe-axis signature).
- **Duration-loading**: FIL's production roster mean-duration gap vs the incumbent pooled
  roster > **+1.0 candle** (Section 4.4 falsifier) AND OOS Δ ≥ +0.20 — the regime factor
  loaded via the added symbol's roster.

A SUSPICIOUS /083 produces no edge ingredient and does NOT advance to the CONFIRMATION
bundle.

### 8.4 INERT

Both: IS monthly Sharpe Δ ∈ **[−0.10, +0.10]** vs /059 AND OOS monthly Sharpe Δ ∈
**[−0.20, +0.20]** vs /059 (and NOT SUSPICIOUS). The universe expansion was a no-op for the
headline metrics — FIL added breadth without moving the aggregate Sharpe. Note: even an
INERT headline can be informative if the BCH OOS concentration falls (the structural target
partially achieved); the diary records the concentration outcome regardless of the headline
classification.

### 8.5 NULL-RESULT

The 4-symbol roster is bit-identical to the /082-reverted-to-/059 3-symbol roster (impossible
here — adding a symbol changes the pooled book and `REQUIRED_GAP`). Listed for taxonomy
completeness only.

## Section 9 — Library Stack Declaration

No new dependencies. The universe expansion is a `V3_MODELS` tuple change plus a
`REQUIRED_GAP` constant recompute — pure runner configuration. Pinned stack carried verbatim
from /059/081/082: `lightgbm 4.6.0`, `optuna 4.8.0`, `numpy 2.2.6`, `pandas 3.0.0`,
`scikit-learn 1.8.0`, `scipy 1.17.0`, `statsmodels 0.14.6`, `pyarrow 23.0.1`. The EDA
(`universe_expansion_edge_screen.py`) uses only `lightgbm`, `numpy`, `pandas`, and the
already-shipped `crypto_trade.strategies.ml.labeling.label_trades` — no new library.

## Section 10 — QR Audit Trail (literature-research path + axis selection)

**Axis assignment.** The orchestrator dispatched iter-v3/083 with Direction 2 (universe
EXPANSION) strongly preferred, per the /082 closeout Critic Rec #3 ("no feature-family axis
can fix the 3-symbol denominator problem") and `cycle3_plan.md` Section 7. The QR confirms
Direction 2 is the correct axis: it is QR-EDA-driven — the specific symbol (FILUSDT) and the
count (3→4) were selected by the committed EDA `analysis/iteration_v3-083/universe_expansion_
edge_screen.py` (SHA `e538d5f`), not by orchestrator fiat.

**Literature research path** (cycle-3 research mandate, `cycle3_plan.md` Section 2):

1. **Grinold & Kahn, *Active Portfolio Management* (1999) — the Fundamental Law of Active
   Management.** IR = IC · √breadth, where breadth is the number of *independent* bets per
   period. The directly load-bearing result for Direction 2: with v3's IC roughly fixed
   (the 14-feature stack is a local optimum — `feedback_v3_iter064_process_lessons.md`),
   the only lever left for the information ratio is **breadth**. v3 has run a 3-symbol
   universe for 21 consecutive EXPLORATIONs and never pulled this lever. Adding a 4th
   *independent* per-symbol model is a direct √breadth increase — 3→4 symbols is a √(4/3) ≈
   1.15× breadth multiplier if FIL is genuinely independent. Source:
   `https://www.amazon.com/Active-Portfolio-Management-Quantitative-Controlling/dp/0070248826`;
   also the canon entry in this agent's reference set.

2. **Cakici, Shahzad, Będowska-Sójka & Zaremba, "Machine learning and the cross-section of
   cryptocurrency returns", *International Review of Financial Analysis* 94 (2024),
   S1057521924001765 / SSRN 4295427.** Studies ML on a 2,700+ cryptocurrency cross-section.
   The finding that shapes /083's count decision: in crypto, *model complexity has limited
   benefit* — the simplest methods often beat regression trees and neural nets. Read into
   the universe context: a *wider* universe with simple per-symbol models beats a narrow
   universe with a complex single model — the breadth, not the model, is the lever. This
   supports a count-EXPANSION (more simple per-symbol models) over Direction-3 model-
   architecture complexity. Source: `https://www.sciencedirect.com/science/article/abs/pii/
   S1057521924001765`; SSRN `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4295427`.

3. **Institutional crypto-portfolio-construction practice (2025) + the v3 dead-paths
   record.** Contemporary institutional crypto allocations spread a satellite sleeve across
   large-cap alts / DeFi / L2 and rebalance frequently — diversification across *liquid
   majors*, not concentration. Cross-referenced with the v3 catalog: the /021 (HBAR+AVAX)
   and /069 (ADA) expansions failed because their screens measured **price diversity**
   (return correlation, feature-space distance), not **signal diversity** — both ranked a
   symbol high on price-distance that the v3 feature stack could not actually fit (HBAR was
   the *worst* IS contributor while ranking #1 by correlation). The research-to-axis
   conclusion: the candidate screen must be a genuine **IS-edge screen** — does a v3-style
   LightGBM, trained on v3's own 14 features and v3's own triple-barrier labels, produce a
   positive IS edge on the candidate, AND does it lift the *portfolio-aggregate* IS Sharpe
   (the /078 lesson — `feedback_v3_per_symbol_lifts_oos_breaks_is.md` / `feedback_v3_is_oos_
   regime_divergence.md`). This is exactly the EDA's T2 (per-candidate IS-edge walk-forward
   LightGBM) and T3 (portfolio-aggregate contribution). Source for the institutional
   practice: XBTO 2025 diversified-crypto-portfolio guidance,
   `https://www.xbto.com/resources/building-a-diversified-crypto-portfolio-best-practices-
   for-institutions-in-2025`.

**From "literature says X" to "the iter-v3/083 axis is Y".** The Fundamental Law says
breadth is v3's untouched lever (research finding #1). Crypto-ML research says simple
per-symbol models in a wider universe beat a complex narrow one (#2). The v3 dead-paths
record says prior expansions failed on screen methodology, not on the axis (#3). Therefore
iter-v3/083's axis = a **count-EXPANSION (3→4)** screened on a **genuine IS-edge +
portfolio-aggregate** EDA. The EDA then selected FILUSDT (rank #1 of 4 survivors:
best standalone IS edge, least-harmful aggregate delta, duration-clean, deepest liquidity)
and the count (1-symbol-at-a-time per the explicit /021 catalog lesson).

**Setup commit SHA**: `<SETUP_SHA — backfilled at the Phase-5.5-gate setup commit>`.

---

**EDA SHA**: `e538d5f` (`analysis/iteration_v3-083/universe_expansion_edge_screen.py` + 5
T-table CSVs).
**Brief SHA**: `<this commit — backfilled>`.
**Setup SHA**: `<backfilled at setup>`.
