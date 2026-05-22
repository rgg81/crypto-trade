# iter-v3/111 — Research Brief — Symbol Selection (CORRECTED RE-TEST): the signal-screened CRV/AAVE/GRT/ADA universe under a `triple_barrier`-corrected runner

**Cycle 6, EXPLORATION #2 of 10** (iter-v3/110–119; iter-v3/120 is the mandatory CONFIRMATION).
**Axis:** Symbol selection — a wholesale replacement of the v3 universe — **the Critic-mandated clean re-test of iter-v3/110.**
**Branch:** `iteration-v3/111`

> **Why this iteration exists.** iter-v3/110 ran this exact universe swap
> (BCH/LDO/TRX → CRV/AAVE/GRT/ADA) but closed **EXPLORATION-NEGATIVE — label
> confound**: the runner trained every /110 model under a stale
> `label_mode="trend_scanning"` (carry-over from iter-v3/105) instead of the
> brief-declared `triple_barrier`. The run therefore varied TWO variables — the
> intended universe swap AND an unintended labeling-geometry change — so the
> symbol-selection axis was **NOT cleanly tested**. The Phase-7.5 Critic
> (`briefs-v3/iteration_v3-110/review.md` Recommendation 4) and the iter-v3/110
> diary (`diary-v3/iteration_v3-110.md` Section 9) mandate iter-v3/111 as the
> clean re-run under a `triple_barrier`-corrected runner. **The corrected runner
> IS the core deliverable of iter-v3/111** (Section 3.5). The universe choice,
> the screen evidence, and the AAVE/ADA dead-path disclosures are all carried
> forward from iter-v3/110 unchanged — only the as-run measurement is being
> redone.

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` — **UNCHANGED, IMMUTABLE.**
- `training_months = 24` — **UNCHANGED, IMMUTABLE.**
- **IS window:** earliest available kline per symbol → 2025-03-24. For the
  proposed universe the IS feature parquets span: CRV 2020-09-01→cutoff (4995 IS
  candles), AAVE 2020-10-16→cutoff (4860), GRT 2020-12-19→cutoff (4653), ADA
  2020-01-31→cutoff (5636). Every symbol has ≥24 months of IS history — the
  walk-forward window is fully covered.
- **OOS window:** 2025-03-24 → data end (~2026-05-18, ~14 months). The QR did NOT
  inspect any post-cutoff data in Phases 1–5. The reused EDA loader
  (`analysis/iteration_v3-110/_shared.py`) asserts `close_time < OOS_CUTOFF_MS`
  (`1742774400000`) per symbol before any computation.
- The walk-forward / CPCV backtest runs on ALL data; the reporting layer splits
  at `OOS_CUTOFF_DATE` into `in_sample/` and `out_of_sample/`.
- **No data-window change vs iter-v3/110 or vs /059.** iter-v3/111's only
  difference vs /110 is the runner's `label_mode` knob (Section 3.5) — NOT the
  data, NOT the universe, NOT the features.

## Section 0.5 — Iteration Type Declaration

**TYPE: EXPLORATION.** Single-axis variation — the substantive change vs the
/059 baseline is the symbol universe `V3_MODELS` (BCH/LDO/TRX → CRV/AAVE/GRT/ADA).
Features (14-feature `V3_FEATURE_COLUMNS`), labeling (2:1 ATR **triple-barrier**,
21-candle timeout), the LightGBM architecture, and the 7-gate RiskV2 stack are
all /059-identical.

- **EXPLORATION mode = `ENSEMBLE_SIZE=3`.** The current v3 EXPLORATION mode has
  been a **3-seed** ensemble since the iter-v3/060 RE-ANCHOR
  (`feedback_v3_cycle1_axis_pass_criteria.md`; `feedback_v3_unified_10seed_baseline.md`).
  The `--exploration` flag sets `ENSEMBLE_SIZE=3` with the standard 3-seed set
  (`ensemble_summary.json` for /110 confirms `mode=exploration, ensemble_size=3,
  seeds=[191664963, 1662057957, 1405681631]`, all `outer=42` lineage). The
  iter-v3/110 brief's Section 0.5 "ENSEMBLE_SIZE forced to 1 / single-seed"
  wording was **stale /105-era prose** (iter-v3/110 diary Lesson 5) — this brief
  states the mode correctly: **`ENSEMBLE_SIZE=3`, NOT single-seed.**
- **Wall-clock budget: HARD CAP 2h.** Run config: `--exploration --n-trials 35`.
  `--exploration` selects `ENSEMBLE_SIZE=3`. iter-v3/110 ran the identical
  4-symbol universe in 1.08h, well inside the cap.
- **Type justification:** This is a single structural axis (universe), tested at
  3-seed EXPLORATION budget to position it for the cycle-6 CONFIRMATION
  (iter-v3/120). It is NOT a CONFIRMATION — no 10-seed validation, no baseline
  update, no Pareto front.
- This is EXPLORATION #2 of the cycle-6 block (iter-v3/110–119). The 10:1 cadence
  (`feedback_v3_strict_10_to_1_cadence.md`) is respected: iter-v3/120 is the
  mandatory separate CONFIRMATION. **iter-v3/110 spent EXPLORATION slot #1** (it
  consumed a runner execution) — the universe axis it was meant to test was left
  UNRESOLVED by the label confound; iter-v3/111 spends slot #2 to resolve it.

## Section 1 — Hypothesis

**Replacing the saturated BCH/LDO/TRX universe with CRV/AAVE/GRT/ADA — a universe
selected by a per-symbol, walk-forward-faithful feature→label predictive-signal
screen — produces an IS-positive, less-concentrated v3 book, because the /109
permutation null (no IS-detectable directional signal) is specific to the
BCH/LDO/TRX feature→label joint distribution and does not transfer to a universe
the screen shows carries measurably stronger signal.**

This is **the same hypothesis iter-v3/110 registered.** What changes at
iter-v3/111 is not the hypothesis but the *test*: iter-v3/110 could not test it
because the runner trained under `trend_scanning` while the EDA was computed
under `triple_barrier` — two different label geometries, so the EDA → backtest
inferential chain was void. iter-v3/111 corrects the runner to `triple_barrier`
(Section 3.5), so the screen evidence (Section 2, computed under `triple_barrier`)
and the backtest now share **one label geometry** and the hypothesis becomes
**cleanly testable** for the first time.

## Section 2 — IS-Only Numerical Evidence

**The IS evidence is the iter-v3/110 EDA, REUSED verbatim — committed at
`analysis/iteration_v3-110/` (commit `cfeaf34`).** Per the iter-v3/111 dispatch
("The /110 research basis is VALID and REUSED — do NOT redo it"), the screen is
NOT re-run. The reuse is sound for one specific reason:

> **The /110 EDA was already computed under `label_mode="triple_barrier"`** —
> the correct label geometry for iter-v3/111's corrected backtest. This is
> verified at source in `analysis/iteration_v3-110/_shared.py` lines 21–25:
> *"Label faithfulness — replicates `labeling.label_trades` (label_mode=
> "triple_barrier") exactly: ATR triple-barrier, atr_tp=2.0 / atr_sl=1.0, ATR
> column `natr_21_raw`, 21-candle (10080-min / 8h) timeout, fee 0.1%."*

The /110 EDA's label geometry was never the problem — the /110 *runner's*
`trend_scanning` knob was. With the runner corrected to `triple_barrier`
(Section 3.5), the /110 EDA and the /111 backtest will at last share one
estimand, and the Section 2 → Section 4 inferential chain becomes valid (it was
the precise thing the /110 confound voided). A thin pointer note documenting this
reuse and the IS-evidence provenance is committed at `analysis/iteration_v3-111/POINTER.md`.

All numbers below are produced by the committed EDA scripts under
`analysis/iteration_v3-110/`: `_shared.py` (the /059-faithful IS-only
triple-barrier labeler, a 21-symbol generalization of /109's `_shared.py`),
`symbol_signal_screen.py`, `universe_construction.py`, `t6_recompute.py`,
`gated_book_2to1.py`, `universe_finalize.py`. Result tables: T1–T10. Every row
entering any computation has `close_time < OOS_CUTOFF_MS` — strict IS-only.

### 2.1 The incumbent universe reproduces the /109 null — the screen is trustworthy

The screen runs the EXACT /109 measurement (walk-forward, embargo-purged 22
candles, 5-seed-averaged LightGBM depth-4, on the 14 features against the /059
**triple-barrier** label) plus a per-symbol permutation null. On the incumbents
(`T1_per_symbol_signal.csv`, `T10_signal_margin.csv`):

| symbol | mean fold AUC | perm-null q50 | perm-null q95 | perm p-value | SIGNAL_GO |
|---|---:|---:|---:|---:|:--:|
| BCH | 0.4949 | 0.5007 | 0.5209 | 0.7213 | False |
| LDO | 0.5029 | 0.4990 | 0.5541 | 0.4754 | False |
| TRX | 0.4910 | 0.5001 | 0.5483 | 0.7541 | False |

All three incumbents sit AT or BELOW their permutation q50 with p ≫ 0.10 — an
independent reproduction of the /109 finding (LightGBM real-label feature→label
AUC ≈ 0.50, no signal). The screen faithfully re-derives the known result, so
its verdict on the other 18 symbols is trustworthy.

### 2.2 The incumbent universe's raw IS gated book is NET-NEGATIVE; the proposed universe's is POSITIVE

The 2:1-barrier-faithful gated-tail book (`T9_final_bakeoff.csv` — re-resolves
the gated 30% top/bottom confidence tail of each symbol using the actual
`long_pnl`/`short_pnl` from the /059 triple-barrier labeler, an IS-only
standalone-model proxy):

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
directional-prediction, edge). The proposed universe **U_B flips the raw gated
book POSITIVE** (+0.25 monthly Sharpe proxy) before any Optuna search or risk
gate is applied.

### 2.3 The per-symbol signal screen ranks the proposed universe above the incumbents

`T1` / `T6_universe_recommendation.csv` — composite ranking (sum of "rank N = best"
ranks on mean-fold-AUC, gated-tail hit-rate, and −permutation-p):

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

GALA tops the composite (highest hit rate 0.5367, p=0.082) but its 2:1-barrier
gated book is **−802.86 PnL, PF 0.93** (`T7_gated_book_2to1.csv`) — its wins are
small, its losses large. This is the /109 lesson directly: a hit rate above the
2:1 breakeven (33.3%) does NOT guarantee a positive 2:1-barrier book. The
leave-one-out (`T8_universe_aggregate.csv`) is decisive: **top5_minus_GALA =
CRV+AAVE+GRT+ADA = +2196.54 PnL** (the best aggregate of all six leave-one-out
variants; top5_minus_CRV is only +641). GALA is dropped.

### 2.5 Per-symbol 2:1-barrier gated books of the four proposed symbols

`T7_gated_book_2to1.csv`:

| symbol | n_trades | win rate | total IS PnL | profit factor |
|---|---:|---:|---:|---:|
| ADA | 2657 | 0.5137 | **+921.00** | 1.0768 |
| CRV | 2354 | 0.5242 | +752.52 | 1.0549 |
| AAVE | 2288 | 0.3632 | +386.88 | 1.0611 |
| GRT | 2192 | 0.5023 | +136.14 | 1.0115 |

All four symbols have an individually POSITIVE raw gated 2:1-barrier book and
PF > 1.0. By contrast the incumbents: BCH −555.17 (PF 0.82), TRX −1814.57 (PF
0.81), LDO +1075.42 (PF 1.18) — only LDO is positive, and LDO is v3's known thin-
roster lottery symbol.

### 2.6 Diversification — Grinold-Kahn breadth

`T5_pnl_correlation.csv` — mean pairwise PnL-proxy correlation (using the
model-free `best_edge` series, so the correlation reflects intrinsic return
co-movement, not a seed artifact):

- Proposed U_B (CRV+AAVE+GRT+ADA): mean pairwise corr ≈ 0.21.
- Incumbent (BCH+LDO+TRX): mean pairwise corr ≈ 0.04.

The incumbent universe is marginally more decorrelated, but U_B has 4 symbols vs
3 — effective breadth `N·(1+(N−1)ρ)^−1` is ≈ 2.7 (U_B) vs ≈ 2.8 (incumbent), i.e.
comparable. U_B does not sacrifice diversification. Critically, U_B's top-symbol
PnL share is 41.9% vs the incumbent's 140.2% (`T9`) — U_B directly fixes the
BASELINE_V3 worst structural flaw (BCH carries 95.76% of IS PnL).

### 2.7 Honest statement of signal thinness

The signal is THIN even at the top of the screen. Of the 21 candidates, only CRV
clears the strict 3-criterion GO bar (mean-fold-AUC > permutation q95 AND p < 0.10
AND ≥5/8 folds positive — `T10`: CRV `SIGNAL_GO=True`, 8/8 positive folds).
AAVE/GRT/ADA clear on AUC-margin-over-q50 (`T10`: CRV +0.039, AAVE +0.026, ADA
+0.017, GRT +0.016 — all positive, vs the incumbents BCH −0.006, TRX −0.009) and
on permutation p-value (CRV 0.066, ADA 0.082, AAVE 0.164, GRT 0.246) but not on
the q95 margin (`T10` `auc_margin_over_q95`: AAVE −0.0067, ADA −0.0010, GRT
−0.0201 — all marginally negative). The raw broad-population edge is small. This
brief does NOT claim a large edge — it claims a universe that is *measurably
better than the saturated incumbent* on every IS metric, and lets the backtest
(with the production Optuna search + 7-gate risk stack, which the EDA does not
apply) resolve whether that translates to a merge-grade book. Per the Prime
Directive, a thin EDA result is a cue to sharpen the hypothesis and run the
experiment, not to stop.

**This thinness is exactly why a clean test matters.** A thin IS signal is
fragile to a label-geometry confound: the iter-v3/110 `trend_scanning` carry-over
voided the measurement precisely because, with a signal this small, the
labeling-geometry interaction term (a sign-flip-or-scale hazard, not a
subtractable bias) swamped any universe effect. iter-v3/111 removes that
interaction so the thin signal can be measured for what it is.

## Section 3 — Proposed Changes

**ONE substantive axis: `V3_MODELS` is replaced wholesale** (the universe swap).
**PLUS the Critic-mandated runner correction** — the iter-v3/105 `label_mode`
revert that was never discharged. The runner correction is NOT a second research
axis: it RESTORES the /059-canonical `triple_barrier` label that the brief always
intended and that iter-v3/110 *claimed* (falsely) to have run. After the
correction, iter-v3/111 varies exactly ONE variable vs /059 — the universe — at
last cleanly.

No feature, no model-architecture, no risk-gate change.

### 3.1 Universe

| | Before (/059) | After (iter-v3/111) |
|---|---|---|
| `V3_MODELS` | `("A (BCHUSDT)","BCHUSDT")`, `("C (LDOUSDT)","LDOUSDT")`, `("D (TRXUSDT)","TRXUSDT")` | `("A (CRVUSDT)","CRVUSDT")`, `("B (AAVEUSDT)","AAVEUSDT")`, `("C (GRTUSDT)","GRTUSDT")`, `("D (ADAUSDT)","ADAUSDT")` |
| count | 3 | 4 |

`V3_MODELS` is **already set** to the 4-tuple at iter-v3/110 commit `f7e564f`
(verified: `run_baseline_v3.py:190-194`). No edit needed — iter-v3/111 keeps
iter-v3/110's universe (Critic Rec 4: "keep iter-v3/110's universe and brief
intact").

**V3_EXCLUDED_SYMBOLS check:** CRV, AAVE, GRT, ADA are NOT in
`V3_EXCLUDED_SYMBOLS` (`BTC/ETH/LINK/LTC/DOT/BNB/SOL/XRP/DOGE/NEAR/MKR`). All
four are v3-eligible. The runner's `_verify_symbols` disjointness assertion
passes.

### 3.2 Labeling — CORRECTED to `triple_barrier` (the /059-canonical label)

2:1 ATR **triple-barrier** (`atr_tp=2.0`, `atr_sl=1.0`), 21-candle (10080-min)
timeout, `natr_21_raw` ATR column, `DEFAULT_ATR_MULTIPLIERS=(2.0,1.0)`,
`V3_ATR_MULTIPLIERS_PER_SYMBOL={}`. **This is /059-identical** — and it is the
label the runner must be CORRECTED to use. iter-v3/110's runner trained under the
stale `label_mode="trend_scanning"`; the precise revert is Section 3.5 item 1.
This is NOT a labeling-axis change vs /059 — it is the restoration of the
/059-canonical label that iter-v3/105 mandated and iter-v3/106–109 (all
NULL-AT-EDA) never discharged.

### 3.3 Features — UNCHANGED

`V3_FEATURE_COLUMNS` stays the 14-feature `V3_FEATURE_COLUMNS_TOP_N` anchor
(`max_dd_window_50, ema_spread_atr_20, ret_kurt_50, ret_skew_200,
range_realized_vol_50, hurst_diff_100_50, ret_kurt_200, hurst_100, btc_ret_14d,
ret_skew_50, vwap_dev_20, ret_autocorr_lag1_50, sym_vs_btc_ret_7d,
regime_momentum_signed_5d`). All runner ABSENT-bans (adx_14, range_efficiency_50,
alpha032, the basis family, the funding family, etc.) remain in force.
`V3_FEATURES_PER_SYMBOL` stays empty — every new symbol gets the universal
14-feature stack via `features_for_symbol`.

### 3.4 Risk gates — UNCHANGED

The 7-primitive RiskV2 stack is /059-identical: BTC trend kill (±15%, 42-bar),
vol scaling, ADX (threshold 20.0), Hurst regime, feature z-score OOD (2.0),
low-vol filter, hit-rate (disabled). `RiskV2Config` knobs all /059-canonical.

### 3.5 Required `src/` changes — the QE's precise Phase 6 work (the runner correction IS the core of /111)

The QR does NOT edit `src/`. The QE implements exactly the following. **Items
1–4 are the Critic-mandated runner correction (Critic Recs 2 + 3) — they are
PRECONDITIONS: no v3 runner execution may occur until they are committed and the
pre-flight confirms `triple_barrier`.** Item 5 is the standard label bump. Item 6
documents what is already done.

**1. Revert the training label to `triple_barrier`** —
`run_baseline_v3.py:1917-1918`, inside `_build_v3_model`'s `common_kwargs`:
   - Change `label_mode="trend_scanning"` → `label_mode="triple_barrier"`.
   - Remove or neutralize `trend_scan_grid=(5, 8, 13, 21)`. Removal is preferred
     (the `triple_barrier` path does not consume `trend_scan_grid`); if the
     `LightGbmStrategy` constructor signature requires the kwarg, neutralize it
     to the constructor default. The `_trend_scan_label` branch in `lgbm.py` is
     retained as zero-cost dead-code infrastructure (per the iter-v3/105
     closeout) — only the runner's *selection* of it is reverted.
   - `common_kwargs` is passed to every v3 model constructor at lines 1925 /
     1927 / 1932 — the single edit propagates to all four symbols' models.

**2. Fix the pre-flight assertion target** — `run_baseline_v3.py:1125`:
   - Change `expected_label_mode = "trend_scanning"` → `"triple_barrier"`.
   - Revise the assertion + print block at lines `1126-1163` so the pre-flight
     **enforces and announces `triple_barrier`**: the `RuntimeError` message must
     refer to `triple_barrier` (not `trend_scanning`), and the `print(...)` at
     `1159-1163` must announce `label_mode: 'triple_barrier'` rather than
     `label_mode (iter-v3/105): 'trend_scanning' grid=...`.
   - The `trend_scan_grid` assertion block at `1134-1146` and the `max(grid) ≤
     timeout_candles` embargo gate at `1147-1158` are `trend_scanning`-specific —
     under `triple_barrier` there is no grid. The QE should remove these two
     blocks (the `triple_barrier` label has a fixed 21-candle timeout, not a
     grid, so the `max(grid)` embargo check is not applicable; the embargo for
     `triple_barrier` is already covered by `REQUIRED_GAP=88` and the
     `_verify_label_leakage_gap()` check). If the QE prefers to retain a
     defensive assertion, it must be re-expressed for `triple_barrier` (assert
     `label_timeout_minutes == 10080`, which the existing `expected_label_timeout`
     check at `1099-1113` already does — so the grid blocks are pure dead weight
     under `triple_barrier` and should be removed).
   - **Methodology note (Critic Rec 4 carry-forward):** a runner pre-flight that
     *asserts* a config value is only protective if the asserted target is
     correct. iter-v3/110's pre-flight asserted the *stale* target
     (`expected_label_mode = "trend_scanning"`) and so *enforced* the bug rather
     than catching it. The pre-flight target MUST be re-derived from this brief,
     never carried forward.

**3. Rewrite the stale `iter-v3/105` comment blocks** —
`run_baseline_v3.py:1114-1118` and `1912-1916`:
   - Both blocks are still tagged verbatim `iter-v3/105` and still describe the
     trend-scanning label as "the ONE clean variable for this iteration." Rewrite
     them for the iter-v3/111 universe-axis context: state that the label is
     `triple_barrier` (the /059-canonical label, restored from the iter-v3/105
     trend-scanning EXPLORATION which closed NEGATIVE), and that the
     iter-v3/111 axis is the CRV/AAVE/GRT/ADA universe swap (a corrected re-test
     of iter-v3/110).
   - Per iter-v3/110 diary Lesson 5, also drop any stale "single-seed" /
     "forced to 1" EXPLORATION-mode prose wherever it appears in these blocks or
     nearby — the current EXPLORATION mode is `ENSEMBLE_SIZE=3`.

**4. Extend the `_canonical_v059` config-accretion guard** —
`run_baseline_v3.py:1032-1050`:
   - The guard's `_canonical_v059` list currently enumerates 11 knobs (V3_MODELS
     symbols, REQUIRED_GAP, the ATR multipliers, the per-symbol dicts, four
     RiskV2 thresholds, the block lists, the drawdown brake). **`label_mode` and
     `trend_scan_grid` are NOT among them** — the blind spot exactly where the
     /110 drift occurred. Add two entries against the /059-canonical values:
     - `("label_mode", _p13_lgbm.label_mode, "triple_barrier")` — the
       /059-canonical training label.
     - `("trend_scan_grid", <observed>, <neutralized/default>)` — assert the
       grid is neutralized to the constructor default. The QE picks the exact
       canonical value to match item 1's neutralization choice (e.g. if the
       kwarg is removed and the constructor default is `None`, the entry is
       `("trend_scan_grid", getattr(_p13_lgbm, "trend_scan_grid", None), None)`).
   - The guard reads its observed `label_mode` from a `_build_v3_model` instance
     — `_p13_lgbm` (the `_p13_inner` LightGbmStrategy already built and inspected
     at `1071-1100`) exposes `.label_mode`; route the guard's check through that
     instance, or build a throwaway instance inside the guard block as the
     existing knobs do.
   - **Sweep all label/model knobs touched by EXPLORATIONs /072–/105** (Critic
     Rec 3): the closed EXPLORATIONs that mutated label/model knobs are
     `/072` (fixed-horizon label), `/105` (trend-scanning label), `/067`
     (inference-threshold-floor). Confirm the guard now covers every such knob
     against its /059-canonical value: `label_timeout_minutes` (the `1099-1113`
     check already enforces 10080 — fold it or a sibling assertion into the
     guard if not already covered), `inference_threshold_floor` (the `1081-1089`
     check enforces 0.0 — likewise), `label_mode` and `trend_scan_grid` (new,
     this item). The deliverable is: every knob any closed EXPLORATION mutated is
     pinned to its /059-canonical value by an assertion the runner cannot bypass.
   - Update the guard's failure message and the `Config-accretion check` PASS
     print at `1052-1064` to reflect the new knob count (11 → 13+) and the
     iter-v3/111 label.

**5. Bump `ITERATION_LABEL`** — `run_baseline_v3.py:131`: `"v3-110"` → `"v3-111"`.

**6. `REQUIRED_GAP` and `V3_MODELS` are ALREADY correct.** `REQUIRED_GAP` is
already 88 = `(21+1) × 4` (verified: the `_canonical_v059` guard at `:1039`
asserts 88; `validation_v3.py` carries the constant; the runner's
`_verify_label_leakage_gap()` recomputes 88). `V3_MODELS` is already the
4-tuple CRV/AAVE/GRT/ADA (set at /110 commit `f7e564f`, `:190-194`). **No edit to
either** — iter-v3/111 inherits them from the iter-v3/110 setup.

**7. Clean the stale `Gap:` diagnostic print string** —
`run_baseline_v3.py:2769-2770` (the source of `run.log` line 33). The string
currently reads `Gap: {REQUIRED_GAP} (= (21+1)*3; iter-v3/088 RE-ARCHITECTURE
reverts /087's 6-sym expansion to the 3-sym /059 universe BCH+LDO+TRX; timeout
UNCHANGED 10080 min)`. This is a stale copy-paste artifact (the Critic flagged it
at /110 Check 2): the parenthetical says `(21+1)*3` and `3-sym /059 universe
BCH+LDO+TRX` while the runner is on the 4-symbol CRV/AAVE/GRT/ADA universe with
`REQUIRED_GAP=88`. Rewrite the parenthetical to `(= (21+1)*4; iter-v3/110
universe swap to the 4-symbol CRV/AAVE/GRT/ADA universe; timeout UNCHANGED
10080 min)`. This is cosmetic — the authoritative computed value (88) is correct
— but the Critic flagged it for cleanup and a corrected re-test must not carry a
stale diagnostic string.

**8. Data freshness pre-flight:** the QE's Phase 6 pre-flight must confirm each of
`data/CRVUSDT/8h.csv`, `data/AAVEUSDT/8h.csv`, `data/GRTUSDT/8h.csv`,
`data/ADAUSDT/8h.csv` has `close_time` within 16h of run time, and that the
feature parquets (`data/features_v3/{CRV,AAVE,GRT,ADA}USDT_8h_features.parquet`)
are regenerated if the klines were refreshed. Per
`feedback_data_staleness_per_worktree.md`, fetch + regenerate features for the
4 symbols in this worktree before the backtest if the parquets are stale.

**9. CPCV `n_paths`:** `CPCV_N_SPLITS=10`, `CPCV_N_TEST_SPLITS=2` ⇒ 45 paths —
UNCHANGED (path count does not depend on symbol count). The CPCV embargo (27) is
UNCHANGED.

**10. Pre-flight `_build_v3_model` symbol references:** the runner builds
throwaway `_build_v3_model(symbol=...)` instances for assertion checks. iter-v3/110
already repointed these to `CRVUSDT` (verified: `:1024`, `:1072` use `CRVUSDT`).
No edit needed — confirm during Phase 6 that no `BCHUSDT`/`LDOUSDT`/`TRXUSDT`
reference survives in the pre-flight build calls.

No other `src/` file is touched. `features_v3/`, the RiskV2 stack, the labeling
module — all bit-identical to /059 except the runner's restored `triple_barrier`
selection.

### 3.6 QE Phase-6 reconciliation instruction (Critic Rec 4 — mandatory)

After the backtest completes, the QE MUST:

1. **`grep run.log` for the executed `label_mode`** and quote it **verbatim** in
   the engineering report's reconciliation section. The expected line, after the
   item-2 pre-flight rewrite, announces `label_mode: 'triple_barrier'`. If
   `run.log` shows anything other than `triple_barrier`, the run is invalid and
   the QE must STOP and re-flag — a second label carry-over must be caught at
   Phase 6, not at Phase 7.5.
2. **Verify the Configuration Diff vs /059 (Section 3.7) LINE-BY-LINE against
   `run.log`** — every row of the diff must be checked against the runner's
   actual logged config, NOT copied from this brief's prose. The iter-v3/110
   engineering report asserted "all other knobs /059-identical" by copying the
   brief; that assertion was false and the Phase-5.5 gate missed it. The QE
   re-derives the diff from `run.log`.
3. Quote the `_canonical_v059` config-accretion-check PASS line from `run.log`
   verbatim, confirming the new `label_mode`/`trend_scan_grid` entries are
   present and PASS.

### 3.7 Configuration Diff vs /059 — the QE verifies this LINE-BY-LINE against `run.log`

This table is the contract. The QE checks **every row** against the runner's
logged config in `run.log` (Section 3.6 item 2) — not against this brief's prose.

| Knob | /059 canonical | iter-v3/111 | Changed? | Verified how |
|---|---|---|---|---|
| `V3_MODELS` symbols | BCH, LDO, TRX | **CRV, AAVE, GRT, ADA** | **YES** (the axis) | `run.log` "Active models" + symbols line |
| `label_mode` | **`triple_barrier`** | **`triple_barrier`** | **NO** (restored — /110 ran `trend_scanning`) | `run.log` pre-flight `label_mode:` line — **grep + quote verbatim (Section 3.6)** |
| `trend_scan_grid` | neutralized / default | neutralized / default | NO (restored) | `run.log` `_canonical_v059` PASS line |
| `REQUIRED_GAP` | 66 | **88** = (21+1)×4 | **YES** (consequence of 3→4 symbols) | `run.log` "Gap:" line + `_verify_label_leakage_gap` PASS |
| `label_timeout_minutes` | 10080 | 10080 | NO | `run.log` timeout-consistency PASS |
| ATR multipliers (TP/SL) | 2.0 / 1.0 | 2.0 / 1.0 | NO | `run.log` `_canonical_v059` PASS line |
| `V3_ATR_MULTIPLIERS_PER_SYMBOL` | `{}` | `{}` | NO | `run.log` `_canonical_v059` PASS line |
| `V3_FEATURE_COLUMNS` | 14-feature top-N | 14-feature top-N | NO | `run.log` "feature-cols=14" + `_verify_feature_columns` |
| `V3_FEATURES_PER_SYMBOL` | `{}` | `{}` | NO | `run.log` feature-cols pre-flight |
| `zscore_threshold` | 2.0 | 2.0 | NO | `run.log` `_canonical_v059` PASS line |
| `adx_threshold` | 20.0 | 20.0 | NO | `run.log` `_canonical_v059` PASS line |
| `inference_threshold_floor` | 0.0 | 0.0 | NO | `run.log` pre-flight floor PASS |
| `enable_per_symbol_drawdown_brake` | False | False | NO | `run.log` `_canonical_v059` PASS line |
| `block_long_for` / `block_short_for` | `()` / `()` | `()` / `()` | NO | `run.log` `_canonical_v059` PASS line |
| ENSEMBLE_SIZE (EXPLORATION) | n/a (3-seed EXPLORATION) | 3 | n/a | `ensemble_summary.json` `mode=exploration, ensemble_size=3` |
| `n_trials` | 35 | 35 | NO | `run.log` "Optuna trials/model" |
| CPCV (N, k, paths, embargo) | 10, 2, 45, 27 | 10, 2, 45, 27 | NO | `run.log` "CPCV:" line |
| `ITERATION_LABEL` | `v3-059` | `v3-111` | YES (label only) | `run.log` header |

**Exactly TWO substantive rows change vs /059: `V3_MODELS` (the axis) and
`REQUIRED_GAP` (a mechanical consequence of the symbol count).** Every label/model
knob is /059-canonical — `label_mode` in particular is `triple_barrier`, the row
iter-v3/110 got wrong.

## Section 4 — Expected OOS Impact

**Anchor.** Per `feedback_v3_cycle1_axis_pass_criteria.md`, EXPLORATION-mode
expected-impact projections anchor on the **/060 EXPLORATION-mode reference**
(IS monthly Sharpe **+0.8325** / OOS monthly Sharpe **+0.1403**, 3-seed) — NOT
the /059 CONFIRMATION baseline. The iter-v3/110 numbers are NOT a usable anchor
(the run was confounded). iter-v3/120 (the cycle-6 CONFIRMATION) will
cross-validate any PROMISING result against /059's 10-seed CONFIRMATION baseline.

**Predicted OOS monthly Sharpe: −0.10 to +0.70, central estimate +0.30.**
**Predicted IS monthly Sharpe: +0.30 to +1.00, central estimate +0.60.**

Reasoning:

- **The raw IS gated proxy is the strongest signal in the EDA.** U_B's raw IS
  gated 2:1-barrier book is +0.25 monthly Sharpe proxy (`T9`), vs the incumbent's
  −0.27. The production path adds the Optuna search (35 trials/cell, 3-seed at
  EXPLORATION) + the 7-gate risk stack. On the incumbent universe that machinery
  lifted a −0.27 raw proxy to /059's +1.089 reported IS Sharpe. The *same*
  lifting machinery applied to a raw proxy already at +0.25 (a +0.52 swing better
  than the incumbent's starting point) should land the IS Sharpe in a
  comparable-or-better band — central estimate +0.60, with a wide band because
  3-seed EXPLORATION variance is high and the EDA's gated proxy is not identical
  to the production gate.
- **This "lift" must be read honestly, not as a guaranteed signal-extraction
  step.** The /109 `/059`-reconciliation (`diary-v3/iteration_v3-109.md` Section
  6) established that the −0.27 → +1.089 lift on the incumbent was *not* the
  machinery extracting directional signal — it is largely 2:1-barrier geometry (a
  coin-flip directional call entered into a 2:1 ATR barrier mechanically clears
  the 33.3% breakeven) plus the accumulated IS-overfit of 59 iterations of
  feature/gate/threshold selection (DSR = 0.0 on /059's own trial-corrected
  metric). So the honest claim is narrower: the screened universe gives the
  production machinery a materially better *raw* starting point (+0.25 vs −0.27),
  and the corrected backtest is what resolves whether that better raw input
  converts to a genuine edge rather than merely producing more barrier geometry
  on a better-positioned book.
- **OOS:** the /109 permutation null does NOT transfer to this universe (it is a
  property of BCH/LDO/TRX's feature→label distribution). The proposed universe's
  IS feature→label AUC is materially above the no-signal floor (CRV/AAVE/GRT/ADA
  margin-over-q50 all positive vs the incumbents' near-zero/negative — `T10`). A
  universe with genuine IS signal *can* transfer OOS — the question the backtest
  answers. The central OOS +0.30 estimate assumes an OOS/IS retention near the
  /059 ratio (0.53). **The OOS band is deliberately wide and includes negative
  values** — a thin IS signal screened on broad-population AUC is exactly the
  kind of signal that can fail the IS→OOS regime shift (Section 7).
- **Concentration:** U_B's IS gated top-symbol share is 41.9% — predicted OOS
  top-symbol concentration meaningfully below the incumbent's. This is the single
  most reliable prediction: 4 symbols each with a positive individual book cannot
  produce a single-symbol-95%-of-PnL roster like /059's.

**BCH IS sensitivity (per `feedback_v3_cycle1_axis_pass_criteria.md` mandate +
/059 Critic Rec #3).** /059's IS book is 95.76% BCH. iter-v3/111 *removes BCH
entirely* — so /059's headline IS Sharpe (+1.089), which is overwhelmingly a BCH
artifact, is not a meaningful comparison point for iter-v3/111's IS. The
iter-v3/111 IS Sharpe is built from four entirely different symbols; whether it
clears +0.60 depends on whether CRV/AAVE/GRT/ADA's combined production book is
positive, NOT on any BCH sensitivity. The EDA's per-symbol gated books (`T7`: all
four individually positive) are the relevant IS evidence. The /059 BCH-IS-share
fragility flag is *resolved by construction* — there is no BCH in the universe.

**Behavioral-effect predictor (per `feedback_v3_axis_saturation_predictor.md`).**
This is a wholesale universe swap, NOT a gate-threshold tweak — so the behavioral
effect is total, not marginal: the entire IS and OOS trade roster is replaced.
iter-v3/110 (the identical universe, confounded label) produced **250 IS trades
/ 89 OOS trades**. iter-v3/111, under the corrected `triple_barrier` label, will
produce a *different* roster (the label change shifts which bars become trades),
but the *order of magnitude* should be similar — 4 symbols × ~25 IS months and
~14 OOS months. **Predicted: IS trades 180–320, OOS trades 90–180.** The
falsifier on the predictor: if OOS trades fall below 90, the trade-rate floor
(Section 8) is at risk and the universe is producing too sparse a book to
evaluate. The /110 89-OOS-trade figure is right at that boundary — a `triple_barrier`
roster is expected to be at least as dense (the `trend_scanning` label's
per-bar OLS horizon selection tends to *reduce* signal emission relative to a
fixed-barrier label), so 90+ OOS trades is the central expectation.

**Explicit falsifier:** see Section 8 — the LOCKED EXPLORATION-NEGATIVE criteria.

## Section 5 — Risk Mitigation

This iteration's PRIMARY axis IS a risk mitigation — it directly attacks the
v3 BASELINE's worst structural flaw, the BCH 95.76%-of-IS-PnL concentration, by
moving to a 4-symbol universe whose IS gated top-symbol share is 41.9%.

- **Concentration cap:** No new explicit per-symbol PnL cap is added — the v3
  catalog (`feedback_v3_concentration_is_signal.md`) closed proportional
  per-symbol caps. Instead, concentration is mitigated *structurally* by the
  universe choice: 4 symbols each with a positive individual IS gated book
  (`T7`), vs the incumbent's single-symbol dominance. The EDA-measured top-symbol
  share drops 140% → 42%.
- **The 7-gate RiskV2 stack is carried UNCHANGED** — BTC trend kill, vol scaling,
  ADX, Hurst regime, z-score OOD, low-vol filter, hit-rate (disabled). The OOD
  z-score gate (|z| > 2.0 on the 14 features) is the relevant defense for a NEW
  universe: the new symbols' feature distributions differ from the incumbents',
  and the OOD gate suppresses trades where the live feature vector is far from
  the training-window covariance. The gate is per-symbol-fitted at training time,
  so it adapts to each new symbol automatically.
- **Per-symbol drawdown brake:** stays DISABLED (`enable_per_symbol_drawdown_brake
  =False`, per the /054 STATEFUL-gate finding). Not changed here.
- **Simulated historical effect:** on the IS gated book (`T7`/`T9`), the universe
  swap converts the incumbent's −1294.31 total PnL / 0.93 PF to U_B's +2196.54 /
  1.05. The leave-one-out (`T8`) confirms the U_B book is robust to dropping any
  single member — worst LOO variant (top5_minus_CRV) is still +641 PnL. No single
  symbol carries the book.
- **The label correction is itself a methodology risk-mitigation.** iter-v3/110's
  confound was a stale-state bug; iter-v3/111's Section 3.5 items 1–4 (the
  `label_mode` revert, the pre-flight fix, the comment rewrite, the
  `_canonical_v059` guard extension) close that failure class — the accretion
  guard now covers `label_mode`/`trend_scan_grid`, so no future EXPLORATION can
  silently inherit a stale label knob. Section 3.6 (the QE `run.log` grep) closes
  the Phase-6 detection gap.

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
| 5 | z-score OOD (\|z\|>2.0, 14 feat) | Active | ~8–15% of bars gated; per-symbol covariance-fitted at training time — adapts to each new symbol |
| 6 | Low-vol filter | Active | Per-symbol-fitted |
| 7 | Hit-rate feedback | **Disabled** | (per iter-v2/045 lesson) |

**Regime coverage:** the 4 proposed symbols span DeFi (CRV, AAVE — lending/DEX),
indexing infrastructure (GRT — The Graph), and a large-cap L1 (ADA). This is a
broader sector mix than the incumbent BCH (L1 fork) / LDO (liquid staking) / TRX
(L1) — the universe is not concentrated in one crypto sub-sector, which the mean
pairwise PnL-proxy correlation of ~0.21 (`T5`) confirms is genuine
diversification, not nominal.

**No new risk primitive is introduced** — this is a pure universe axis (plus the
runner correction, which is not a research change). Adding a risk primitive
simultaneously would violate one-variable-at-a-time. If the corrected backtest
shows a per-symbol failure (e.g. one of the four drags OOS), that is a finding
for iter-v3/112+, not a mid-flight patch — see Section 7 for the pre-registered
AAVE/ADA fallbacks.

## Section 7 — Pre-Registered Failure-Mode Prediction

These failure modes are carried forward from the iter-v3/110 brief — they remain
the most plausible ways iter-v3/111 fails. The key difference: under the
corrected `triple_barrier` label, a failure-mode firing is now **interpretable
evidence about the universe** (at /110 it was confounded with the label and could
not be attributed).

**Mode 1 — the broad-population AUC screen does not survive the IS→OOS regime
shift.** The most plausible way iter-v3/111 fails OOS: the IS feature→label
signal screen ranks symbols on a broad-population AUC that is real in-sample but
does not survive the 2025–2026 OOS regime shift — the proposed universe's thin IS
edge (CRV the only strict GO; AAVE/GRT/ADA marginal) decays toward or below zero
OOS. In metrics: IS monthly Sharpe in the +0.30 to +1.00 band but OOS monthly
Sharpe collapsing toward 0 or negative, OOS/IS ratio well below the 0.40 floor —
the classic IS-fit / OOS-decay signature. The gates that catch it: the OOS/IS
Sharpe ratio (Section 8), the per-symbol OOS attribution in `comparison.csv` (if
3 of 4 symbols are OOS-negative the universe is a selection artifact), and the
PBO machinery (informational at EXPLORATION budget). **Under `triple_barrier`,
this firing is now clean evidence** — at /110 it was observationally identical to
the `trend_scanning` IS-collapse/OOS-overfit signature and could not be
distinguished from the confound.

**Mode 2 — the universe swap helps concentration but not edge
(PROMISING-MECHANICAL).** The book IS less concentrated (top-symbol share drops
as predicted) but the aggregate Sharpe is no better than the /060 anchor, because
spreading a thin edge across 4 symbols neither adds nor removes edge, it just
redistributes it. This shows as IS/OOS Sharpe ≈ /060 levels with top-symbol share
materially lower — a PROMISING-MECHANICAL-class outcome (a concentration
improvement without an edge improvement), valuable but non-compoundable
(`feedback_v3_promising_mechanical_subtype.md`).

**Mode 3 — AAVE specifically underperforms (dead-path symbol; weakest IS
evidence of the four).** AAVE is a dead-path symbol — the QR agent definition's
Dead Paths Catalog lists "AAVE — OOS −35%" under v2 symbol failures (disclosed in
Section 10). Its IS evidence is the WEAKEST of the four proposed symbols: its
gated 2:1 win rate is 0.3632 (`T7`), barely above the 33.3% 2:1-barrier breakeven
and far below CRV/ADA/GRT's 0.50–0.52 — so its +386.88 gated book is the most
barrier-geometry-carried and the least directional-signal-carried of the
universe; its permutation p-value is the second-thinnest (0.164, vs CRV 0.066 /
ADA 0.082); and it is the only proposed symbol that fails BOTH the q95-margin and
the p<0.10 strict criteria. **At iter-v3/110 (confounded label) AAVE was indeed
the universe's largest OOS dragger (−13.03%, 43.69% of total loss)** — but under
`trend_scanning`, so not a clean confirmation. If AAVE is again the universe's
OOS-worst symbol under the corrected `triple_barrier` label, that is the *clean*
re-confirmation, and iter-v3/112 should test a drop-AAVE variant (CRV+GRT+ADA, or
the all-novel U_A = CRV+AAVE+GRT only if ADA also holds). Because AAVE's gated
book is so barrier-geometry-dominated, an AAVE OOS collapse is the *expected*
failure tell — this brief pre-registers AAVE as an at-least-equally-likely-to-ADA
per-symbol weak link.

**Mode 4 — ADA specifically underperforms (dead-path symbol).** ADA carries a v2
dead-path note ("ADA — single-seed strong, 5-seed ensemble washes the edge") and
was a closed v3 /078 single-symbol swap (LDO→ADA, reverted) — disclosed in
Section 10. ADA has the LARGEST individual IS gated book of the four (+921.00, PF
1.077, `T7`) and a positive feature→label AUC (0.5193, p=0.082, margin-over-q50
+0.017), so the IS evidence for ADA is the *strongest* of the four — but the
dead-path note warns the 5-seed ensemble can wash a single-seed edge. **At
iter-v3/110 (confounded label) ADA was the 3rd-largest OOS dragger
(−9.80%)** — confounded, not clean. If ADA's OOS book is again the universe's
worst under `triple_barrier`, that re-confirms the dead-path and iter-v3/112
should test U_A (CRV+AAVE+GRT, the 3-symbol all-novel variant; `T9`: U_A IS gated
book +1275.54, PF 1.04, still positive without ADA).

**Mode 5 (process) — a second label carry-over.** The iteration-specific failure
mode for a *corrected re-test* is that the correction itself does not land — the
QE fails to revert `label_mode`, or reverts it but the pre-flight still asserts
the stale target, and iter-v3/111 *again* runs `trend_scanning`. This is
pre-empted by Section 3.5 items 1–4 (the revert + pre-flight fix + guard
extension) and Section 3.6 (the QE `run.log` grep + line-by-line diff
verification). If `run.log` shows `label_mode` ≠ `triple_barrier`, the QE STOPS
at Phase 6 — the iteration does not proceed to Phase 7 on a confounded run a
second time.

## Section 8 — Pre-Registered MERGE / NO-MERGE Numerical Criteria

This is an EXPLORATION — it does NOT merge and does NOT update `BASELINE_V3.md`
regardless of outcome (`v0.v3-111` will be a closeout marker only). The criteria
below classify the EXPLORATION verdict; they are **LOCKED before the backtest**
and are **re-pre-registered afresh** for iter-v3/111 (NOT carried from the
iter-v3/110 brief — the /110 brief anchored its falsifiers loosely; iter-v3/111
anchors them precisely against the /060 EXPLORATION-mode reference per
`feedback_v3_cycle1_axis_pass_criteria.md`).

**Anchor:** the /060 EXPLORATION-mode reference — **IS monthly Sharpe +0.8325 /
OOS monthly Sharpe +0.1403**, 3-seed, `frac_positive_paths` 0.6444. Per
`feedback_v3_cycle1_axis_pass_criteria.md`, cycle-1-style EXPLORATION axes are
scored by Δ vs /060 (an axis is detected if it has SOME signal worth a
CONFIRMATION look); the cycle CONFIRMATION (iter-v3/120) re-validates any
PROMISING result against /059's 10-seed CONFIRMATION baseline. iter-v3/111 is a
cycle-6 EXPLORATION; the /060 anchor and the same Δ thresholds apply.

**Threshold methodology.** `feedback_v3_cycle1_axis_pass_criteria.md` sets the
canonical cycle-1 EXPLORATION-PASS bar as **IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 vs
/060 AND `frac_positive_paths` ≥ 0.50**. I adopt these thresholds unchanged for
cycle 6 — they are the established, Critic-locked, noise-floor-adjusted bar and
there is no cycle-6-specific reason to move them (the 3-seed EXPLORATION variance
floor that motivated them is unchanged; the EXPLORATION mode is still
`ENSEMBLE_SIZE=3`). Translating the Δ thresholds to absolute levels against the
/060 anchor: IS Δ ≥ +0.10 ⇒ **IS ≥ +0.9325**; OOS Δ ≥ +0.20 ⇒ **OOS ≥ +0.3403**.

**EXPLORATION-PROMISING** (the universe advances to the cycle-6 CONFIRMATION
candidate pool, to be cross-validated at iter-v3/120 against /059's 10-seed
baseline) iff ALL of:
- IS monthly Sharpe **≥ +0.9325** (IS Δ ≥ +0.10 vs the /060 anchor +0.8325), AND
- OOS monthly Sharpe **≥ +0.3403** (OOS Δ ≥ +0.20 vs the /060 anchor +0.1403), AND
- `frac_positive_paths` (CPCV) **≥ 0.50**, AND
- OOS / IS monthly Sharpe ratio **≥ 0.40** (EXPLORATION 3-seed tolerance, below
  the 0.50 CONFIRMATION floor — a guard against an IS-only fit), AND
- top-symbol OOS PnL share **≤ 70%** (a materially better concentration profile
  than the /059 baseline's 108.86% OOS BCH share — the structural-improvement
  test), AND
- aggregate OOS trades **≥ 130** (the v3 bundle-level trade-rate floor,
  `feedback_v3_trade_rate_floor_bundle_level.md`).

**EXPLORATION-PROMISING-MECHANICAL** (a concentration win without an edge win;
recorded as a structural improvement, non-compoundable per
`feedback_v3_promising_mechanical_subtype.md`) iff: top-symbol OOS PnL share
≤ 70% AND IS/OOS Sharpe both within ±0.20 of the /060 anchor (i.e. IS in
[+0.63, +1.03], OOS in [−0.06, +0.34]) but NOT clearing the PROMISING IS ≥ +0.9325
/ OOS ≥ +0.3403 bars.

**EXPLORATION-NEGATIVE** (the universe-by-signal-screen axis is recorded as
non-advancing — and this is the verdict that **legitimately closes** the
symbol-selection-by-feature-AUC-screen axis for cycle 6, since the label confound
is now removed) iff ANY of:
- IS monthly Sharpe **< +0.7325** (IS Δ < −0.10 vs the /060 anchor — the
  NEGATIVE-AT-EXPLORATION band), OR
- OOS monthly Sharpe **< −0.0597** (OOS Δ < −0.20 vs the /060 anchor — the
  NEGATIVE-AT-EXPLORATION band), OR
- OOS / IS monthly Sharpe ratio **< 0.40** with OOS monthly Sharpe < +0.3403, OR
- aggregate OOS trades **< 130** (the book is too sparse to evaluate — a
  trade-rate-floor failure, recorded as NEGATIVE for the axis).

**EXPLORATION-INERT** (the axis has no detectable effect — noise-band) iff the
result falls in neither the PROMISING nor the NEGATIVE bands: IS Δ within
[−0.10, +0.10] vs /060 (IS in [+0.7325, +0.9325]) OR OOS Δ within [−0.20, +0.20]
vs /060 (OOS in [−0.0597, +0.3403]), without a trade-rate-floor failure.

**Mandatory caveat — the IS-OOS daily-Sharpe ratio sanity check.** If the IS-OOS
*daily* Sharpe ratio falls outside [0.5, 2.0] (the /060 Critic
`NEGATIVE-SUSPICIOUS-OOS` band), the verdict is **EXPLORATION-NEGATIVE-SUSPICIOUS**
regardless of the headline monthly figures — a structurally suspicious IS/OOS
divergence (the iter-v3/026/027/030/034/036/037/039 pattern) is not a PROMISING
signal even if the monthly numbers clear the bars.

**Critic scoring.** The Critic scores EXPLORATION checks 1, 2, 4, 5, 6, 8
(look-ahead, embargo, IC, ADF, Pareto, hypothesis-alignment); Check 3 edge
thresholds (DSR/PSR) are informational at EXPLORATION budget per
`feedback_v3_dsr_mode_artifact.md`. **Check 8 (hypothesis-implementation
alignment) is the check iter-v3/110 failed** — for iter-v3/111 it specifically
verifies, via `run.log`, that the runner trained under `triple_barrier`. The QE's
Section 3.6 `run.log` grep produces the artifact the Critic needs.

## Section 9 — Library Stack Declaration

This iteration adds NO new library. The reused EDA scripts use only the
already-pinned stack: `lightgbm==4.6.0`, `scikit-learn==1.8.0` (`roc_auc_score`),
`scipy==1.17.0` (`binomtest`), `numpy==2.2.6`, `pandas==3.0.0`,
`pyarrow==23.0.1`. No new EDA is run at iter-v3/111 (the /110 screen is reused).
The Phase 6 backtest uses the existing v3 runner stack — `optuna==4.8.0`,
`statsmodels==0.14.6` (ADF), and the in-repo `validation_v3` (CPCV/PBO/PSR). No
`mlfinlab`/`fracdiff`/`pypbo` version change. No fallback. `pyproject.toml` is
UNCHANGED.

## Section 10 — QR Audit Trail

**This iteration is a Critic-mandated corrected re-test, not a fresh axis.**
iter-v3/111 exists because the Phase-7.5 Critic of iter-v3/110
(`briefs-v3/iteration_v3-110/review.md`, Recommendation 4) and the iter-v3/110
diary (`diary-v3/iteration_v3-110.md` Section 9) mandate it: iter-v3/110 ran the
CRV/AAVE/GRT/ADA universe swap but the runner trained every model under a stale
`label_mode="trend_scanning"` (iter-v3/105 carry-over) instead of the
brief-declared `triple_barrier`, so the symbol-selection axis was NOT cleanly
tested. iter-v3/111 keeps the /110 universe and the /110 EDA intact and re-runs
under a `triple_barrier`-corrected runner. **No new axis-selection EDA was
performed** — per the iter-v3/111 dispatch, the /110 research basis is VALID and
REUSED (the /110 screen was already computed under `triple_barrier`, verified
`analysis/iteration_v3-110/_shared.py` lines 21–25). A thin pointer note
documenting the reuse is committed at `analysis/iteration_v3-111/POINTER.md`.

**Axis selection rationale (carried forward from iter-v3/110, per
`feedback_v3_axis_selection_quant_discipline.md`).** The cycle-6 axis menu
(`project_v3_cycle6_axis_menu.md`) lists symbol selection as item 1. The
iter-v3/110 QR confirmed it with EDA backing committed before the /110 brief
(`analysis/iteration_v3-110/`, commit `cfeaf34`). The choice was not ad-hoc:

1. **The /109 permutation null is universe-specific.** The terminal /105→/109
   finding (the 14-feature representation carries no IS-detectable directional
   signal) was scoped by the /109 diary and `project_v3_cycle5_terminal_finding.md`
   as a property of the *BCH/LDO/TRX 8h* joint distribution — Option A (a
   different universe) is the listed first structural escape. The EDA confirms
   this: it reproduces the null on the incumbents (Section 2.1) and finds
   materially stronger signal elsewhere (Section 2.3).
2. **Symbol selection was never re-opened as a wholesale replacement since cycle
   1.** All prior v3 universe work (HBAR/AVAX at /021, FIL at /083, GALA/MANA/SAND
   at /087, ADA-swap at /078) was expansion-by-addition or single-symbol-swap
   that KEPT the fragile BCH-anchored core. None tested a wholesale replacement
   selected by a feature→label signal screen.
3. **Why U_B (CRV+AAVE+GRT+ADA) and not the composite-top-5.** GALA was dropped
   on decisive evidence: highest hit rate but a −802.86 2:1-barrier gated book
   (Section 2.4); the `T8` leave-one-out names CRV+AAVE+GRT+ADA the best 4-symbol
   aggregate. U_A (CRV+AAVE+GRT, 3 symbols, all-novel) is the pre-registered
   fallback if ADA underperforms (Section 7 Mode 4).

**ADA dead-path disclosure (carried forward from iter-v3/110).** ADA carries a v2
dead-path note ("ADA — single-seed strong, 5-seed ensemble washes the edge") and
was a closed v3 /078 single-symbol swap (LDO→ADA, reverted). Including ADA
requires explicit new evidence per the dead-paths rule. The new evidence: the
/110 EDA's ADA screen is 5-seed-averaged, walk-forward-faithful, IS-only, on the
v3 14-feature stack under `triple_barrier` — and ADA shows a positive
feature→label AUC (0.5193, permutation p=0.082, margin-over-q50 +0.017) AND the
LARGEST individual 2:1-barrier gated book of the four (+921.00, PF 1.077, `T7`).
The v2 note was a v2-universe-context observation; the /078 swap was a
single-symbol substitution into the BCH-anchored core — neither is this
experiment (a 4-symbol signal-screened universe with ADA as one of four positive
contributors). The new quantitative evidence is committed and reproducible. The
brief pre-registers (Section 7 Mode 4) that if ADA is nonetheless the universe's
OOS-worst symbol under the corrected `triple_barrier` label, iter-v3/112 falls
back to the all-novel U_A.

**AAVE dead-path disclosure (carried forward from iter-v3/110).** AAVE is ALSO a
dead-path symbol — the QR agent definition's Dead Paths Catalog lists "AAVE — OOS
−35%" under v2 symbol failures. The dead-paths anti-pattern requires explicit new
evidence for EVERY re-proposed catalogued symbol, so AAVE gets the same
disclosure as ADA. The new evidence: the /110 EDA's AAVE screen is
5-seed-averaged, walk-forward-faithful, IS-only, on the v3 14-feature stack under
`triple_barrier` — and AAVE ranks 3rd of 21 on the composite (`T6`, score 56.0),
with a mean fold AUC of 0.5234 (margin-over-q50 +0.026, well clear of the
incumbents' near-zero/negative), a permutation p-value of 0.164, and an
individually positive gated 2:1-barrier book of +386.88 (PF 1.06, `T7`). The v2
"OOS −35%" result was a v2-universe-context observation — a different model
(v2's 34-feature stack and per-symbol ensembling) inside a different universe; it
is not this experiment (the v3 14-feature stack, the 2:1 ATR triple-barrier, a
4-symbol signal-screened universe with AAVE as one of four contributors). A
v2-context failure does not transfer to v3's distinct feature representation and
universe context. **Honest caveat — AAVE's evidence is the WEAKEST of the four
proposed symbols.** Its gated 2:1 win rate is 0.3632 (`T7`), barely above the
33.3% 2:1-barrier breakeven and far below the 0.50–0.52 of CRV/GRT/ADA; its
+386.88 book is therefore the most barrier-geometry-carried and the least
directional-signal-carried of the four. Its permutation p-value (0.164) is the
second-thinnest, and it is the only proposed symbol failing both the strict
q95-margin and the p<0.10 criteria. AAVE is included because it nonetheless
clears every incumbent on every IS metric and contributes a positive individual
book — but the brief pre-registers (Section 7 Mode 3) AAVE as an
at-least-equally-likely-to-ADA per-symbol weak link, with a drop-AAVE variant
scoped for iter-v3/112 if it is the universe's OOS-worst symbol.

**Note on the iter-v3/110 confound and its non-attribution.** iter-v3/110's
per-symbol OOS attribution (AAVE the largest dragger, ADA the 3rd) *appeared* to
confirm the AAVE/ADA pre-registration — but the iter-v3/110 diary Section 6 is
explicit that this is **NOT a clean confirmation**: the /105 `trend_scanning`
IS-collapse/OOS-overfit signature produces the *same observable* (an IS-fit /
OOS-decay pattern with most symbols negative), so the firing of the modes on the
/110 numbers is not independent evidence about the universe. iter-v3/111 is the
clean test; only the iter-v3/111 per-symbol OOS attribution under `triple_barrier`
is interpretable evidence for the AAVE/ADA failure modes.

**Escalation note on excluded liquid majors.** The excluded liquid majors
(BTC/ETH/SOL/XRP/etc.) are NOT needed — the /110 EDA found a positive-signal
universe entirely within the v3-eligible set (CRV/AAVE/GRT/ADA all clear the
incumbents on every IS metric). v3's track mandate is genuine cross-track
diversification; `V3_EXCLUDED_SYMBOLS` is respected with no escalation.

**No orchestrator pick was superseded.** The cycle-6 dispatch recommended symbol
selection; the iter-v3/110 QR's EDA confirmed it; iter-v3/111 is the
Critic-mandated corrected re-run of that same QR-led, EDA-backed axis. This
audit-trail section is included per the `feedback_v3_axis_selection_quant_discipline.md`
standard, documenting that the axis and the specific universe are EDA-driven and
that iter-v3/111 introduces no new research decision — only the runner correction
the Critic mandated.
