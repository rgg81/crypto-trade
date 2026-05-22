# iter-v3/110 — Research Brief — Symbol Selection: a signal-screened universe replacement (CRV/AAVE/GRT/ADA)

**Cycle 6, EXPLORATION #1 of 10** (iter-v3/110–119; iter-v3/120 is the mandatory CONFIRMATION).
**Axis:** Symbol selection — a wholesale replacement of the v3 universe.
**Branch:** `iteration-v3/110`

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` — **UNCHANGED, IMMUTABLE.**
- `training_months = 24` — **UNCHANGED, IMMUTABLE.**
- **IS window:** earliest available kline per symbol → 2025-03-24. For the proposed
  universe the IS feature parquets span: CRV 2020-09-01→cutoff (4995 IS candles),
  AAVE 2020-10-16→cutoff (4860), GRT 2020-12-19→cutoff (4653), ADA 2020-01-31→cutoff
  (5636). Every symbol has ≥24 months of IS history — the walk-forward window is
  fully covered.
- **OOS window:** 2025-03-24 → data end (~2026-05-18, ~14 months). The QR did NOT
  inspect any post-cutoff data in Phases 1–5. The EDA loader
  (`analysis/iteration_v3-110/_shared.py`) asserts `close_time < OOS_CUTOFF_MS`
  (`1742774400000`) per symbol before any computation.
- The walk-forward / CPCV backtest runs on ALL data; the reporting layer splits
  at `OOS_CUTOFF_DATE` into `in_sample/` and `out_of_sample/`.

## Section 0.5 — Iteration Type Declaration

**TYPE: EXPLORATION.** Single-axis variation — the ONLY change vs the /059
baseline is the symbol universe `V3_MODELS`. Features (14-feature
`V3_FEATURE_COLUMNS`), labeling (2:1 ATR triple-barrier, 21-candle timeout),
the LightGBM architecture, and the 7-gate RiskV2 stack are all /059-identical.

- **Wall-clock budget: HARD CAP 2h.** Run config: `--exploration --seeds 1
  --n-trials 35`. ENSEMBLE_SIZE forced to 1 by `--exploration`. The /059 unified
  10-seed architecture is a CONFIRMATION-mode concern; EXPLORATION runs single-seed.
- **Type justification:** This is a single structural axis (universe), tested at
  single-seed EXPLORATION budget to position it for the cycle-6 CONFIRMATION
  bundle. It is not a CONFIRMATION — no multi-seed validation, no baseline update.
- This is EXPLORATION #1 of the cycle-6 block (iter-v3/110–119). The 10:1 cadence
  (`feedback_v3_strict_10_to_1_cadence.md`) is respected: iter-v3/120 is the
  mandatory separate CONFIRMATION.

## Section 1 — Hypothesis

**Replacing the saturated BCH/LDO/TRX universe with CRV/AAVE/GRT/ADA — a universe
selected by a per-symbol, walk-forward-faithful feature→label predictive-signal
screen — produces an IS-positive, less-concentrated v3 book, because the /109
permutation null (no IS-detectable directional signal) is specific to the
BCH/LDO/TRX feature→label joint distribution and does not transfer to a universe
the screen shows carries measurably stronger signal.**

## Section 2 — IS-Only Numerical Evidence

All numbers are produced by the committed EDA scripts under
`analysis/iteration_v3-110/` (commit `cfeaf34`): `_shared.py` (the /059-faithful
IS-only triple-barrier labeler, a 21-symbol generalization of /109's `_shared.py`),
`symbol_signal_screen.py`, `universe_construction.py`, `t6_recompute.py`,
`gated_book_2to1.py`, `universe_finalize.py`. Result tables: T1–T10.

### 2.1 The incumbent universe reproduces the /109 null — the screen is trustworthy

The screen runs the EXACT /109 measurement (walk-forward, embargo-purged 22
candles, 5-seed-averaged LightGBM depth-4, on the 14 features against the /059
triple-barrier label) plus a per-symbol permutation null. On the incumbents
(T1, T10):

| symbol | mean fold AUC | perm-null q50 | perm-null q95 | perm p-value | SIGNAL_GO |
|---|---:|---:|---:|---:|:--:|
| BCH | 0.4949 | 0.5007 | 0.5209 | 0.7213 | False |
| LDO | 0.5029 | 0.4990 | 0.5541 | 0.4754 | False |
| TRX | 0.4910 | 0.5001 | 0.5483 | 0.7541 | False |

All three incumbents sit AT or BELOW their permutation q50 with p ≫ 0.10 — an
independent reproduction of the /109 finding (LightGBM real-label feature→label
AUC ≈ 0.50, no signal). The screen faithfully re-derives the known result, so
its verdict on the other 18 symbols is trustworthy.

### 2.2 The incumbent universe's raw IS gated book is NET-NEGATIVE

The 2:1-barrier-faithful gated-tail book (T9 — re-resolves the gated 30% top/bottom
confidence tail of each symbol using the actual `long_pnl`/`short_pnl` from the
/059 labeler, an IS-only standalone-model proxy):

| universe | n_sym | n_trades | win rate | total IS PnL | profit factor | monthly Sharpe proxy | top-symbol PnL share |
|---|---:|---:|---:|---:|---:|---:|---:|
| **incumbent BCH+LDO+TRX** | 3 | 6642 | 0.4118 | **−1294.31** | 0.9300 | **−0.2659** | 140.2% |
| U_A: CRV+AAVE+GRT | 3 | 6834 | 0.4633 | +1275.54 | 1.0401 | +0.1891 | 59.0% |
| **U_B: CRV+AAVE+GRT+ADA** | 4 | 9491 | 0.4774 | **+2196.54** | 1.0501 | **+0.2527** | 41.9% |

The incumbent universe's raw gated 2:1-barrier book is **net-negative** (monthly
Sharpe proxy −0.27). The /059 baseline's reported IS monthly Sharpe of +1.089 is
the product of the production Optuna search + the full 7-gate risk stack
squeezing a thin geometry-carried edge out of this raw signal (consistent with
the /109 reconciliation: /059 trades a barrier-geometry-carried, not a
directional-prediction, edge). The proposed universe U_B flips the raw gated
book POSITIVE (+0.25 monthly Sharpe proxy) before any Optuna search or risk gate
is applied.

### 2.3 The per-symbol signal screen ranks the proposed universe above the incumbents

T1 / T6 — composite ranking (sum of "rank N = best" ranks on mean-fold-AUC,
gated-tail hit-rate, and −permutation-p):

| final rank | symbol | mean fold AUC | perm p-value | gated hit rate | composite score |
|---:|---|---:|---:|---:|---:|
| 1 | GALA | 0.5304 | 0.0820 | 0.5367 | 60.5 |
| 2 | **CRV** | 0.5340 | 0.0656 | 0.5040 | 58.0 |
| 3 | **AAVE** | 0.5234 | 0.1639 | 0.5202 | 56.0 |
| 4 | **GRT** | 0.5176 | 0.2459 | 0.5234 | 54.0 |
| 5 | **ADA** | 0.5193 | 0.0820 | 0.4925 | 48.5 |
| … | | | | | |
| 10 | BCH (incumbent) | 0.4949 | 0.7213 | 0.5133 | 33.5 |
| 15 | LDO (incumbent) | 0.5029 | 0.4754 | 0.4732 | 23.5 |
| 17 | TRX (incumbent) | 0.4910 | 0.7541 | 0.4742 | 17.5 |

All three incumbents land in the bottom half (ranks 10, 15, 17 of 21). CRV, AAVE,
GRT, ADA all beat every incumbent on both the signal AUC and the permutation
p-value.

### 2.4 GALA is excluded — high hit rate, negative 2:1-barrier book

GALA tops the composite (highest hit rate 0.5367, p=0.001) but its 2:1-barrier
gated book is **−803 PnL, PF 0.93** (T7) — its wins are small, its losses large.
This is the /109 lesson directly: a hit rate above the 2:1 breakeven (33.3%) does
NOT guarantee a positive 2:1-barrier book. The T8 leave-one-out is decisive:
**top5_minus_GALA = CRV+AAVE+GRT+ADA = +2197 PnL** (the best aggregate of all six
leave-one-out variants; top5_minus_CRV is only +641). GALA is dropped.

### 2.5 Per-symbol 2:1-barrier gated books of the four proposed symbols (T7)

| symbol | n_trades | win rate | total IS PnL | profit factor |
|---|---:|---:|---:|---:|
| ADA | 2657 | 0.5137 | **+921.00** | 1.0768 |
| CRV | 2354 | 0.5242 | +752.52 | 1.0549 |
| AAVE | 2288 | 0.3632 | +386.88 | 1.0611 |
| GRT | 2192 | 0.5023 | +136.14 | 1.0115 |

All four symbols have an individually POSITIVE raw gated 2:1-barrier book and
PF > 1.0. By contrast the incumbents: BCH −555 (PF 0.82), TRX −1815 (PF 0.81),
LDO +1075 (PF 1.18) — only LDO is positive, and LDO is v3's known thin-roster
lottery symbol.

### 2.6 Diversification — Grinold-Kahn breadth

T5 — mean pairwise PnL-proxy correlation (using the model-free `best_edge`
series, so the correlation reflects intrinsic return co-movement, not a seed
artifact):

- Proposed U_B (CRV+AAVE+GRT+ADA): mean pairwise corr ≈ 0.21.
- Incumbent (BCH+LDO+TRX): mean pairwise corr ≈ 0.04.

The incumbent universe is marginally more decorrelated, but U_B has 4 symbols vs
3 — effective breadth `N·(1+(N−1)ρ)^−1` is ≈ 2.7 (U_B) vs ≈ 2.8 (incumbent), i.e.
comparable. U_B does not sacrifice diversification. Critically, U_B's top-symbol
PnL share is 41.9% vs the incumbent's 140.2% (T9) — U_B directly fixes the
BASELINE_V3 worst structural flaw (BCH carries 95.76% of IS PnL).

### 2.7 Honest statement of signal thinness

The signal is THIN even at the top of the screen. Of the 21 candidates, only CRV
clears the strict 3-criterion GO bar (mean-fold-AUC > permutation q95 AND p < 0.10
AND ≥5/8 folds positive). AAVE/GRT/ADA clear on AUC-margin-over-q50 (T10: CRV
+0.039, AAVE +0.026, ADA +0.017, GRT +0.016 — all positive, vs the incumbents
BCH −0.006, TRX −0.009) and on permutation p-value (CRV 0.066, ADA 0.082, AAVE
0.164, GRT 0.246) but not on the q95 margin. The raw broad-population edge is
small. This brief does NOT claim a large edge — it claims a universe that is
*measurably better than the saturated incumbent* on every IS metric, and lets
the backtest (with the production Optuna search + 7-gate risk stack, which the
EDA does not apply) resolve whether that translates to a merge-grade book. Per
the Prime Directive, a thin EDA result is a cue to sharpen the hypothesis and run
the experiment, not to stop.

## Section 3 — Proposed Changes

**ONE axis: `V3_MODELS` is replaced wholesale.** No feature, label, model, or
risk-gate change.

### 3.1 Universe

| | Before (/059) | After (iter-v3/110) |
|---|---|---|
| `V3_MODELS` | `("A (BCHUSDT)","BCHUSDT")`, `("C (LDOUSDT)","LDOUSDT")`, `("D (TRXUSDT)","TRXUSDT")` | `("A (CRVUSDT)","CRVUSDT")`, `("B (AAVEUSDT)","AAVEUSDT")`, `("C (GRTUSDT)","GRTUSDT")`, `("D (ADAUSDT)","ADAUSDT")` |
| count | 3 | 4 |

**V3_EXCLUDED_SYMBOLS check:** CRV, AAVE, GRT, ADA are NOT in `V3_EXCLUDED_SYMBOLS`
(`BTC/ETH/LINK/LTC/DOT/BNB/SOL/XRP/DOGE/NEAR/MKR`). All four are v3-eligible. The
runner's `_verify_symbols` disjointness assertion passes.

### 3.2 Labeling — UNCHANGED

2:1 ATR triple-barrier (`atr_tp=2.0`, `atr_sl=1.0`), 21-candle (10080-min)
timeout, `natr_21_raw` ATR column, `DEFAULT_ATR_MULTIPLIERS=(2.0,1.0)`,
`V3_ATR_MULTIPLIERS_PER_SYMBOL={}`. All /059-identical.

### 3.3 Features — UNCHANGED

`V3_FEATURE_COLUMNS` stays the 14-feature `V3_FEATURE_COLUMNS_TOP_N` anchor. All
runner ABSENT-bans (adx_14, range_efficiency_50, alpha032, the basis family, the
funding family, etc.) remain in force. `V3_FEATURES_PER_SYMBOL` stays empty —
every new symbol gets the universal 14-feature stack via `features_for_symbol`.

### 3.4 Risk gates — UNCHANGED

The 7-primitive RiskV2 stack is /059-identical: BTC trend kill (±15%, 42-bar),
vol scaling, ADX (threshold 20.0), Hurst regime, feature z-score OOD (2.0),
low-vol filter, hit-rate (disabled). `RiskV2Config` knobs all /059-canonical.

### 3.5 Required `src/` changes (precise instructions for the QE — Phase 6)

The QR does NOT edit `src/`. The QE implements exactly the following. Every change
is mechanical (a universe swap); none alters strategy logic.

1. **`run_baseline_v3.py` `V3_MODELS`** (lines 190–194): replace the 3-tuple with
   the 4-tuple in §3.1. Label strings `"A (CRVUSDT)"` … `"D (ADAUSDT)"`.

2. **`src/crypto_trade/strategies/ml/validation_v3.py` `REQUIRED_GAP`** (line 76):
   `(21+1)*3 = 66` → `(21+1)*4 = 88`. The label-leakage gap formula is
   `(timeout_candles+1) × n_symbols`; n_symbols 3 → 4 ⇒ gap 66 → 88. Update the
   constant AND its inline comment. The runner's `_assert_gap` /
   `verify_no_label_leakage` checks (`run_baseline_v3.py` lines ~1186–1206) read
   `len(V3_MODELS)` and will then assert `88` consistently.

3. **`run_baseline_v3.py` config-accretion guard `_canonical_v059`** (lines
   ~1028–1063): the guard hard-asserts `V3_MODELS symbols == ("BCHUSDT","LDOUSDT",
   "TRXUSDT")` and `REQUIRED_GAP == 66`. Update the two expected values to
   `("CRVUSDT","AAVEUSDT","GRTUSDT","ADAUSDT")` and `88`. The other 9
   `/059-canonical` knobs (ATR multipliers, zscore_threshold, adx_threshold, the
   per-symbol dicts, block lists, drawdown brake) stay UNCHANGED — they are not
   touched by this axis and the guard must still catch drift in them.

4. **`run_baseline_v3.py` hardcoded per-flight model-build checks**: the runner
   builds throwaway `_build_v3_model(symbol=…)` instances for assertion checks at
   lines ~778, ~927, ~951, ~982, ~1021, ~1069 — all hardcoded to
   `BCHUSDT`/`LDOUSDT`/`TRXUSDT`. Repoint each to a symbol in the new universe
   (any one — they only verify the model-build path returns a `RiskV3Wrapper` /
   has the expected attributes; e.g. use `CRVUSDT` uniformly). These are
   non-symbol-specific structural checks; the symbol identity is irrelevant to
   what they assert.

5. **`run_baseline_v3.py` `ITERATION_LABEL`** (line 131): `"v3-105"` → `"v3-110"`.

6. **Feature-column / ABSENT-ban assertions** (`run_baseline_v3.py`
   `_verify_feature_columns`, lines ~360–590): these iterate `for sym in V3_MODELS`
   — they automatically cover the new symbols once `V3_MODELS` is updated. No edit
   needed beyond confirming the 4 new symbols' parquets carry the 14
   `V3_FEATURE_COLUMNS` (they do — verified: `data/features_v3/{CRV,AAVE,GRT,ADA}
   USDT_8h_features.parquet` exist, generated 2026-05-17/18, 24-month span).

7. **Data freshness pre-flight:** the QE's Phase 6 pre-flight must confirm each of
   `data/CRVUSDT/8h.csv`, `data/AAVEUSDT/8h.csv`, `data/GRTUSDT/8h.csv`,
   `data/ADAUSDT/8h.csv` has `close_time` within 16h of run time, and that the
   feature parquets are regenerated if the klines were refreshed. Per
   `feedback_data_staleness_per_worktree.md`, fetch + regenerate features for the
   4 symbols in this worktree before the backtest if the parquets are stale.

8. **CPCV `n_paths`:** `CPCV_N_SPLITS=10`, `CPCV_N_TEST_SPLITS=2` ⇒ 45 paths —
   UNCHANGED (path count does not depend on symbol count). The CPCV embargo (27)
   is UNCHANGED.

No other `src/` file is touched. `features_v3/`, `lgbm.py`, the RiskV2 stack, the
labeling module — all bit-identical to /059.

## Section 4 — Expected OOS Impact

**Predicted OOS monthly Sharpe: +0.3 to +0.9, central estimate +0.55** (vs the
/059 OOS baseline +0.5791). **Predicted IS monthly Sharpe: +0.4 to +1.0, central
estimate +0.7.**

Reasoning:
- The EDA's raw IS gated 2:1-barrier book for U_B is +0.25 monthly Sharpe proxy
  (vs the incumbent's −0.27). The production path adds the Optuna search (35
  trials/cell, single-seed at EXPLORATION) + the 7-gate risk stack, which on the
  incumbent universe lifted a −0.27 raw proxy to a +1.089 reported IS Sharpe. The
  *same* lifting machinery applied to a raw proxy that is already +0.25 (a +0.52
  swing better than the incumbent's starting point) should land the IS Sharpe in
  a comparable-or-better band. **This "lift" must be read honestly, not as a
  guaranteed signal-extraction step.** The /109 `/059`-reconciliation
  (`diary-v3/iteration_v3-109.md` Section 6) established that the −0.27→+1.089
  lift on the incumbent was *not* the machinery extracting directional signal —
  it is largely 2:1-barrier geometry (a coin-flip directional call entered into a
  2:1 ATR barrier mechanically clears the 33.3% breakeven) plus the accumulated
  IS-overfit of 59 iterations of feature/gate/threshold selection (DSR = 0.0 on
  /059's own trial-corrected metric). So the honest claim here is narrower: the
  screened universe gives the production machinery a materially better *raw*
  starting point (+0.25 vs −0.27), and the backtest is what resolves whether that
  better raw input converts to a genuine edge rather than merely producing more
  barrier geometry on top of a better-positioned book. The central +0.7 estimate
  is deliberately conservative — single-seed EXPLORATION variance is high, the
  EDA's gated proxy is not identical to the production gate, and per the /109
  finding a higher reported IS Sharpe is not by itself evidence of extracted
  directional signal.
- OOS: the /109 permutation null does NOT transfer to this universe (it is a
  property of BCH/LDO/TRX's feature→label distribution). The proposed universe's
  IS feature→label AUC is materially above the no-signal floor (CRV/AAVE/GRT/ADA
  margin-over-q50 all positive vs the incumbents' near-zero/negative). A universe
  with genuine IS signal *can* transfer OOS — the question the backtest answers.
  The central OOS +0.55 estimate assumes an OOS/IS retention near the /059 ratio
  (0.53–0.81 across metrics).
- **Concentration:** U_B's IS gated top-symbol share is 41.9% — predicted OOS
  top-symbol concentration meaningfully below the incumbent's. This is the single
  most reliable prediction: 4 symbols each with a positive individual book cannot
  produce a single-symbol-95%-of-PnL roster like /059's.

**Explicit falsifier:** if the backtest produces **IS monthly Sharpe < +0.30 OR
OOS monthly Sharpe < −0.10**, the hypothesis ("a signal-screened universe carries
extractable directional edge") is rejected — it would mean the broad-population
AUC screen does not predict tradeable edge even on a universe it ranks well, and
symbol-selection-by-feature-AUC-screen is closed as an axis for cycle 6.

## Section 5 — Risk Mitigation

This iteration's PRIMARY axis IS a risk mitigation — it directly attacks the
v3 BASELINE's worst structural flaw, the BCH 95.76%-of-IS-PnL concentration,
by moving to a 4-symbol universe whose IS gated top-symbol share is 41.9%.

- **Concentration cap:** No new explicit per-symbol PnL cap is added — the v3
  catalog (`feedback_v3_concentration_is_signal.md`) closed proportional
  per-symbol caps. Instead, concentration is mitigated *structurally* by the
  universe choice: 4 symbols each with a positive individual IS gated book (T7),
  vs the incumbent's single-symbol dominance. The EDA-measured top-symbol share
  drops 140% → 42%.
- **The 7-gate RiskV2 stack is carried UNCHANGED** — BTC trend kill, vol scaling,
  ADX, Hurst regime, z-score OOD, low-vol filter, hit-rate (disabled). The OOD
  z-score gate (|z| > 2.0 on the 14 features) is the relevant defense for a NEW
  universe: the new symbols' feature distributions differ from the incumbents',
  and the OOD gate suppresses trades where the live feature vector is far from
  the training-window covariance. The gate is per-symbol-fitted at training time,
  so it adapts to each new symbol automatically.
- **Per-symbol drawdown brake:** stays DISABLED (`enable_per_symbol_drawdown_brake
  =False`, per /054 STATEFUL-gate finding). Not changed here.
- **Simulated historical effect:** on the IS gated book (T7/T9), the universe
  swap converts the incumbent's −1294 total PnL / 0.93 PF to U_B's +2197 / 1.05.
  The leave-one-out (T8) confirms the U_B book is robust to dropping any single
  member — worst LOO variant (top5_minus_CRV) is still +641 PnL. No single
  symbol carries the book.

## Section 6 — Risk Management Design

The v3 7-primitive risk gate stack — UNCHANGED from /059. Per-symbol fire-rate
predictions for the NEW universe (the gates are per-symbol-fitted, so the
predictions are by gate class):

| # | Primitive | Status | Fire-rate prediction on CRV/AAVE/GRT/ADA |
|---|---|---|---|
| 1 | BTC trend kill (±15%, 42-bar) | Active | ~5–12% of bars killed — BTC-regime-driven, symbol-independent; same as /059 |
| 2 | Vol scaling | Active | Continuous; ADA/CRV/GRT/AAVE are all liquid mid-caps with vol comparable to the incumbents |
| 3 | ADX threshold (20.0) | Active | ~30–45% of bars below threshold; per-symbol ADX distribution differs but the threshold is universal |
| 4 | Hurst regime | Active | Per-symbol-fitted; no symbol-specific tuning |
| 5 | z-score OOD (|z|>2.0, 14 feat) | Active | ~8–15% of bars gated; per-symbol covariance-fitted at training time — adapts to each new symbol |
| 6 | Low-vol filter | Active | Per-symbol-fitted |
| 7 | Hit-rate feedback | **Disabled** | (per iter-v2/045 lesson) |

**Regime coverage:** the 4 proposed symbols span DeFi (CRV, AAVE — lending/DEX),
indexing infrastructure (GRT — The Graph), and a large-cap L1 (ADA). This is a
broader sector mix than the incumbent BCH (L1 fork) / LDO (liquid staking) / TRX
(L1) — the universe is not concentrated in one crypto sub-sector, which the
mean pairwise PnL-proxy correlation of ~0.21 (T5) confirms is genuine
diversification, not nominal.

**No new risk primitive is introduced** — this is a pure universe axis. Adding a
risk primitive simultaneously would violate one-variable-at-a-time. If the
backtest shows a per-symbol failure (e.g. one of the four drags OOS), that is a
finding for iter-v3/111+, not a mid-flight patch.

## Section 7 — Pre-Registered Failure-Mode Prediction

The most plausible way this iteration fails OOS: **the IS feature→label signal
screen ranks symbols on a broad-population AUC that does not survive the
IS→OOS regime shift — the proposed universe's thin IS edge (CRV the only strict
GO; AAVE/GRT/ADA marginal) is real in-sample but the 2025–2026 OOS regime is
different enough that the per-symbol models, fit on a 14-feature stack the /109
chain showed carries near-zero directional information even on a well-screened
universe, produce an OOS book that decays toward or below zero.** In metrics this
looks like: IS monthly Sharpe in the +0.4 to +1.0 band (the screen's IS signal
does lift the IS fit) but OOS monthly Sharpe collapsing toward 0 or negative,
with an OOS/IS ratio well below the 0.5 floor — the classic IS-fit / OOS-decay
signature. The gates that should catch it: the OOS/IS Sharpe ratio (Gate 3), the
DSR/PBO machinery (an overfit universe-selection shows elevated PBO), and the
per-symbol OOS attribution in `comparison.csv` (if 3 of 4 symbols are OOS-negative
the universe is a selection artifact).

A second, distinct failure mode: **the universe swap helps concentration but not
edge** — the book IS less concentrated (top-symbol share drops as predicted) but
the aggregate Sharpe is no better than /059, because spreading a thin edge across
4 symbols neither adds nor removes edge, it just redistributes it. This would
show as IS/OOS Sharpe ≈ /059 levels with top-symbol share materially lower —
a PROMISING-MECHANICAL-class outcome (a concentration improvement without an edge
improvement), valuable but non-compoundable.

A third possibility worth pre-registering: **ADA specifically underperforms** —
ADA has a v2 dead-path note ("5-seed ensemble washes the edge") and a closed v3
/078 single-symbol-swap. If ADA's OOS book is the universe's worst, that
re-confirms the dead-path and iter-v3/111 should test U_A (CRV+AAVE+GRT, the
3-symbol all-novel variant) — the EDA already scoped U_A as the fallback (T9:
U_A IS gated book +1276, PF 1.04, still positive without ADA).

A fourth possibility, at least as likely as the third: **AAVE specifically
underperforms.** AAVE is also a dead-path symbol (the v2 "OOS −35%" note,
disclosed in §10) and its IS evidence is the WEAKEST of the four — its gated 2:1
win rate is 0.3632 (T7), barely above the 33.3% barrier breakeven and far below
CRV/ADA/GRT's 0.50–0.52, so its +386.88 gated book is the most barrier-geometry-
carried and the least directional-signal-carried of the universe; its
permutation p-value is the second-thinnest (0.164, vs CRV 0.066 / ADA 0.082);
and it is the only proposed symbol that fails BOTH the q95-margin and the p<0.10
strict criteria. If AAVE is the universe's OOS-worst symbol, the same fallback
logic applies as for ADA: iter-v3/111 should consider a variant dropping AAVE
(e.g. CRV+GRT+ADA, or the all-novel U_A only if ADA also holds). Because AAVE's
gated book is so barrier-geometry-dominated, an AAVE OOS collapse would be the
*expected* failure tell — the brief pre-registers it as an at-least-equally-
likely per-symbol weak link to ADA, not a surprise.

## Section 8 — Pre-Registered MERGE / NO-MERGE Numerical Criteria

This is an EXPLORATION — it does NOT merge and does NOT update `BASELINE_V3.md`
regardless of outcome (`v0.v3-110` will be a closeout marker only). The criteria
below classify the EXPLORATION verdict; they are LOCKED before the backtest.

**EXPLORATION-PROMISING** (the universe advances to the cycle-6 CONFIRMATION
candidate pool) iff ALL of:
- IS monthly Sharpe **≥ +0.60**, AND
- OOS monthly Sharpe **≥ +0.30**, AND
- OOS / IS monthly Sharpe ratio **≥ 0.40** (EXPLORATION single-seed tolerance,
  below the 0.50 CONFIRMATION floor), AND
- top-symbol OOS PnL share **≤ 70%** (a materially better concentration profile
  than the /059 baseline's 108.86% OOS BCH share — the structural-improvement
  test), AND
- aggregate OOS trades **≥ 130** (the v3 bundle-level trade-rate floor;
  4 symbols × ~14 OOS months should clear this comfortably).

**EXPLORATION-PROMISING-MECHANICAL** (a concentration win without an edge win;
recorded as a structural improvement, non-compoundable) iff: top-symbol OOS PnL
share ≤ 70% AND IS/OOS Sharpe both within ±0.20 of the /059 baseline but not
clearing the PROMISING IS ≥ +0.60 / OOS ≥ +0.30 bars.

**EXPLORATION-NEGATIVE** (the universe-by-signal-screen axis is recorded as
non-advancing) iff: IS monthly Sharpe < +0.30 OR OOS monthly Sharpe < −0.10
(the Section 4 falsifier), OR OOS/IS ratio < 0.40 with OOS < +0.30.

The Critic scores EXPLORATION checks 1, 2, 4, 5, 6, 8 (look-ahead, embargo, IC,
ADF, Pareto, hypothesis-alignment); Check 3 edge thresholds (DSR/PSR) are
informational at EXPLORATION budget per `feedback_v3_dsr_mode_artifact.md`.

## Section 9 — Library Stack Declaration

This iteration adds NO new library. The EDA scripts use only the already-pinned
stack: `lightgbm==4.6.0`, `scikit-learn==1.8.0` (`roc_auc_score`,
`MLPClassifier` not used here), `scipy==1.17.0` (`binomtest`), `numpy==2.2.6`,
`pandas==3.0.0`, `pyarrow==23.0.1`. The Phase 6 backtest uses the existing v3
runner stack — `optuna==4.8.0`, `statsmodels==0.14.6` (ADF), and the in-repo
`validation_v3` (CPCV/PBO/PSR). No `mlfinlab`/`fracdiff`/`pypbo` version change.
No fallback. `pyproject.toml` is UNCHANGED.

## Section 10 — QR Audit Trail

**Axis selection rationale (per `feedback_v3_axis_selection_quant_discipline.md`).**
The cycle-6 axis menu (`project_v3_cycle6_axis_menu.md`) offered four structural
axes; the dispatch recommended opening with symbol selection. The QR confirms
symbol selection as the iter-v3/110 axis, with EDA backing committed *before*
this brief (`analysis/iteration_v3-110/`, commit `cfeaf34`). The choice was not
ad-hoc:

1. **The /109 permutation null is universe-specific.** The terminal /105→/109
   finding (14-feature representation carries no IS-detectable directional
   signal) was explicitly scoped by the /109 diary Section 8.3 and
   `project_v3_cycle5_terminal_finding.md` as a property of the *BCH/LDO/TRX 8h*
   joint distribution — Option A (a different universe) is the listed first
   structural escape, precisely because the null does not transfer. The EDA
   confirms this directly: the screen reproduces the null on the incumbents
   (§2.1) and finds materially stronger signal elsewhere (§2.3).

2. **Symbol selection was never re-opened since cycle 1.** All prior v3 universe
   work (HBAR/AVAX at /021, FIL at /083, GALA/MANA/SAND at /087, ADA-swap at /078)
   was *expansion-by-addition* or *single-symbol-swap* that KEPT the fragile
   BCH-anchored core. None tested a *wholesale replacement* selected by a
   feature→label signal screen. This is a genuinely different axis, not a
   catalogued-dead retry.

3. **Why U_B (CRV+AAVE+GRT+ADA) and not the composite-top-5.** The composite-top
   symbol GALA was dropped on decisive evidence: highest hit rate but a −803
   2:1-barrier gated book (§2.4); the T8 leave-one-out names CRV+AAVE+GRT+ADA the
   best 4-symbol aggregate. U_A (CRV+AAVE+GRT, 3 symbols, all-novel) is the
   pre-registered fallback if ADA underperforms (§7).

**ADA dead-path disclosure.** ADA carries a v2 dead-path note ("ADA — single-seed
strong, 5-seed ensemble washes the edge") and was a closed v3 /078 single-symbol
swap (LDO→ADA, reverted). Including ADA requires explicit new evidence per the
dead-paths rule. The new evidence: this EDA's ADA screen is 5-seed-averaged,
walk-forward-faithful, IS-only, on the v3 14-feature stack — and ADA shows a
positive feature→label AUC (0.5193, permutation p=0.082, margin-over-q50 +0.017)
AND the LARGEST individual 2:1-barrier gated book of the four (+921, PF 1.077,
T7). The v2 note was a v2-universe-context observation; the /078 swap was a
single-symbol substitution into the BCH-anchored core — neither is this
experiment (a 4-symbol signal-screened universe with ADA as one of four positive
contributors). The new quantitative evidence is committed and reproducible. The
brief pre-registers (§7) that if ADA is nonetheless the universe's OOS-worst
symbol, iter-v3/111 falls back to the all-novel U_A.

**AAVE dead-path disclosure.** AAVE is ALSO a dead-path symbol — the QR agent
definition's Dead Paths Catalog lists "AAVE — OOS −35%" under v2 symbol failures.
The dead-paths anti-pattern requires explicit new evidence for EVERY re-proposed
catalogued symbol, so AAVE gets the same disclosure as ADA. The new evidence:
this EDA's AAVE screen is 5-seed-averaged, walk-forward-faithful, IS-only, on the
v3 14-feature stack — and AAVE ranks 3rd of 21 on the composite (T6, score 56.0),
with a mean fold AUC of 0.5234 (margin-over-q50 +0.026, well clear of the
incumbents' near-zero/negative), a permutation p-value of 0.164, and an
individually positive gated 2:1-barrier book of +386.88 (PF 1.06, T7). The v2
"OOS −35%" result was a v2-universe-context observation — a different model
(v2's 34-feature stack and per-symbol ensembling) inside a different universe;
it is not this experiment (the v3 14-feature stack, the 2:1 ATR triple-barrier,
a 4-symbol signal-screened universe with AAVE as one of four contributors). The
same logic applied to ADA applies here: a v2-context failure does not transfer
to v3's distinct feature representation and universe context, and the screen's
verdict is the relevant IS-only evidence. **Honest caveat — AAVE's evidence is
the WEAKEST of the four proposed symbols.** Its gated 2:1 win rate is 0.3632
(T7), barely above the 33.3% 2:1-barrier breakeven and far below the 0.50–0.52
of CRV/GRT/ADA; its +386.88 book is therefore the most barrier-geometry-carried
and the least directional-signal-carried of the four. Its permutation p-value
(0.164) is the second-thinnest, and it is the only proposed symbol failing both
the strict q95-margin and the p<0.10 criteria. AAVE is included because it
nonetheless clears every incumbent on every IS metric and contributes a positive
individual book — but the brief pre-registers (§7) AAVE as an
at-least-equally-likely-to-ADA per-symbol weak link, with a drop-AAVE variant
scoped for iter-v3/111 if it is the universe's OOS-worst symbol.

**Escalation note on excluded liquid majors.** The dispatch invited escalation if
the excluded liquid majors (BTC/ETH/SOL/XRP/etc.) are genuinely needed. They are
NOT needed — the EDA found a positive-signal universe entirely within the
v3-eligible set (CRV/AAVE/GRT/ADA all clear the incumbents on every IS metric).
v3's track mandate is genuine cross-track diversification; `V3_EXCLUDED_SYMBOLS`
is respected with no escalation.

**No orchestrator pick was superseded** — the dispatch recommended symbol
selection and the QR's EDA confirmed it. This audit-trail section is included per
the `feedback_v3_axis_selection_quant_discipline.md` standard, documenting that
the axis and the specific universe are EDA-driven.
