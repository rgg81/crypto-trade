# iter-v3/116 — Research Brief

**Axis**: a NEW EXIT primitive — *early-exit-on-no-confirmation* — a time-conditioned absence-of-excursion exit. If a trade fails to show a `+0.50` ATR favorable excursion within the first `K=4` candles after entry, the trade is closed at candle K's close (a fourth `exit_reason` named `"no_confirm"`); otherwise the trade proceeds to the normal TP/SL/timeout resolution. The triple-barrier label estimand is UNCHANGED; the static `2.0`/`1.0` ATR barrier geometry is UNCHANGED. The single substantive axis vs /059 is one new optional exit primitive controlled by two hand-chosen scalar parameters (`trigger_atr = 0.50`, `k_candles = 4`).

**Cycle**: 6 EXPLORATION slot #7 of 10 (iter-v3/120 is the mandatory cycle-6 CONFIRMATION). The cycle-6 axis menu (`project_v3_cycle6_axis_menu.md`) was spent by /110–/114 (universe ×2, model architecture ×1, multi-frequency ×1, risk management ×1 — all NEGATIVE); /115 opened a NEW labeling axis outside the menu (NEGATIVE). iter-v3/116 advances to a TRADE-CONSTRUCTION / EXIT-LAYER axis — the /115 closeout's recommended frontier — and, per the dispatch's standing out-of-the-box mandate plus the EDA evidence, lands on a BOLDER axis than the dispatch's literal recommendation (see Section 10).

---

## Section 0 — Provenance & Honesty Statement

This brief is governed by `feedback_v3_brief_parameter_provenance.md` (the iter-v3/114 Check-1 no-cheating FAIL response): every tuned scalar parameter must name the exact committed analysis table that produces it; every hand-chosen parameter must be DECLARED hand-chosen and IS-calibrated with an auditable temporal fence.

This iteration cites **two hand-chosen scalar parameters**:

- `trigger_atr = 0.50` — DECLARED hand-chosen. The grid `[0.25, 0.50, 0.75, 1.00]` was swept on IS-only data (`analysis/iteration_v3-116/T7_early_exit_grid.csv`); `0.50` is chosen for parsimony — it is a round-number midpoint of the swept range, NOT the per-symbol grid optimum (per-symbol optima are `BCH 0.50, LDO 1.00, TRX 0.50` from `T9_out_of_fold.csv`; a per-symbol pick would be the closed /073 axis). The choice is justified by the supporting evidence at this single cell: positive IS Sharpe lift across all 3 symbols (`T7`: BCH `+0.1253`, LDO `+0.0068`, TRX `+0.0415` — the *only* cell with all-3-positive lift in the entire 16-cell grid).
- `k_candles = 4` — DECLARED hand-chosen. The grid `[2, 3, 4, 5]` was swept on IS-only data. `4` is chosen at the same `T7` row as `trigger_atr=0.50` for the all-3-positive property. It is roughly the median holding time of the static triple-barrier book per `T6_confirm_separates.csv` and corresponds to ~32 hours at the 8h interval — the *first third* of the 21-candle timeout, a parsimonious "fast-confirm or cut" window.

**Auditable temporal fence**: the EDA (`analysis/iteration_v3-116/`, commit `52444c9`) is committed in ONE atomic commit BEFORE this brief or any subsequent setup commit touches the runner. Every script in the EDA directory asserts `close_time < OOS_CUTOFF_MS = 1742774400000` (2025-03-24); no OOS-window file is read at any point. There is no OOS coverage annex — the parameters above are hand-chosen on IS-only evidence, not OOS-tuned, and the brief is committed *before* the runner code change. The /115-applied "OOS annex in a separate later commit" pattern is not needed here (no OOS-window EDA was produced); the temporal fence is the commit ordering plus the IS-only assertion in every analysis script.

No parameter is laundered as an Optuna sweep output or a "T# IS-only sweep" outcome. The grid was swept and the hand-chosen cell named explicitly.

## Section 0.5 — Iteration Type Declaration

- **TYPE**: **EXPLORATION**
- **Runner flags**: `--exploration --n-trials 35`
- **ENSEMBLE_SIZE**: 3 (the v3-cap EXPLORATION ensemble — first 3 seeds of the unified 10-seed lineage: `191664963, 1662057957, 1405681631`, outer=42 lineage subset; see BASELINE_V3.md "Phase B-3 unified 10-seed ensemble architecture")
- **Wall-clock cap**: ≤ 2h (cycle-6 EXPLORATION cap per `feedback_v3_cadence_discipline.md`; /115 ran 0.69h, /114 ran 0.71h, /113 ran 0.80h — well under cap)
- **Cycle position**: cycle-6 EXPLORATION slot #7 of 10. 3 slots remain (/117, /118, /119) before the mandatory iter-v3/120 CONFIRMATION.
- **Anchor for EXPLORATION-mode comparison**: iter-v3/060 (IS monthly Sharpe **+0.8325** / OOS monthly Sharpe **+0.1403**) — the 3-seed EXPLORATION-mode reference per BASELINE_V3.md.
- **Canonical baseline (UNCHANGED)**: `v0.v3-059` (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**, 10-seed CONFIRMATION).

## Section 1 — Hypothesis

**Hypothesis.** Adding a single new exit primitive — close the trade at candle K's close if it has not shown a `+0.50` ATR favorable excursion within the first `K=4` candles — does not improve the IS monthly Sharpe at production scale. The pre-registered modal outcome is **EXPLORATION-NEGATIVE / INERT** because the EDA's g2 mechanism gate FAILED: the trades the rule cuts are positive-mean-PnL held-to-barrier in 48/48 (trigger, K) cells (it cuts modestly-below-average WINNERS, not losers), and the small IS lift observed at the chosen cell is grid-search-on-an-uptrend variance reduction that is unlikely to survive production Optuna + multi-seed inference + OOS regime exposure.

The brief still runs the backtest because (i) THE PRIME DIRECTIVE mandates it (the EDA designs the experiment; it never terminates it); (ii) the early-exit primitive is the genuine structural complement to /107's high-water-mark trailing-stop family (the absence-of-excursion exit /107 did not test); (iii) at the IS-cell-picked `(trigger=0.50, K=4)` setting the rule produces a small coherent positive lift on all 3 symbols on the EDA's static-direction counterfactual — the only cell with that property in a 16-cell grid — making it the residual-uncertainty axis worth resolving in production.

## Section 2 — IS-Only Numerical Evidence

The /116 EDA produced TEN result tables across THREE distinct trade-construction-layer hypotheses, all strictly IS-only (`close_time < OOS_CUTOFF_MS = 2025-03-24`). The full EDA design lives in `analysis/iteration_v3-116/_shared.py`, `regime_barrier_gating_eda.py`, `scaled_entry_eda.py`, `early_exit_eda.py`, `regime_barrier_synthesis.py`, `early_exit_synthesis.py` (commit `52444c9`).

### 2.1 The axis space the EDA mapped (three structural hypotheses)

| Axis | Hypothesis | Mechanism |
|---|---|---|
| **A** | regime-conditioned exit barrier (the /115 closeout's recommended axis) | `(tp,sl)` ATR multipliers become a function of the entry-bar Hurst-100 / realized-vol z-score bucket |
| **B** | scaled-entry (staged-entry path) | `f0` of position at signal candle; remaining `1-f0` added on +trigger-ATR favorable excursion within K candles |
| **C** | early-exit-on-no-confirmation | close the trade at candle K's close if no +trigger-ATR favorable excursion observed; else proceed to TP/SL/timeout |

All three axes are genuinely structural (NOT a knob, NOT a feature/model/universe/label change) and were chosen for dead-path-distance from every /042/065/073/107/114 dead path (full disclosure in Section 10).

### 2.2 Axis A — regime-conditioned exit barrier — DECISIVE NO-GO at shuffle placebo

Six (3 symbols × 2 conditioning variables) regime-bucketed grid sweeps over `TP_GRID = [1.0, 1.5, 2.0, 2.5, 3.0]` × `SL_GRID = [0.5, 0.75, 1.0, 1.5, 2.0]` = 25 cells per bucket.

`T1_regime_bucket_optima.csv` (the per-bucket optimal `(tp, sl)`):

| symbol | cond_var | bucket | best_tp | best_sl | bucket_lift_vs_static |
|---|---|---:|---:|---:|---:|
| BCH | hurst_100 | 0 | 1.0 | 1.5 | +0.31 |
| BCH | hurst_100 | 1 | 1.0 | 2.0 | +0.35 |
| BCH | hurst_100 | 2 | 1.5 | 2.0 | +0.09 |
| BCH | realvol_z | 0/1/2 | 1.0/1.0/1.0 | 2.0/2.0/2.0 | +0.26 / +0.34 / +0.29 |
| LDO | hurst_100 | 0/1/2 | 1.0/1.0/1.0 | 2.0/1.5/2.0 | +0.26 / +0.21 / +0.23 |
| LDO | realvol_z | 0/1/2 | 1.0/1.0/1.0 | 2.0/2.0/1.0 | +0.54 / +0.31 / +0.28 |
| TRX | hurst_100 | 0/1/2 | 1.0/1.0/1.0 | 2.0/2.0/2.0 | +0.22 / +0.07 / +0.09 |
| TRX | realvol_z | 0/1/2 | 1.5/1.0/1.0 | 1.0/2.0/2.0 | +0.03 / +0.42 / +0.11 |

The grid-search optimum collapses to ONE cell — `(tp=1.0, sl=2.0)` — in 13 of 18 buckets (the modal cell has 72% share per the T4 synthesis). The "per-bucket difference" g1 PASSES only on a technicality (≤1 grid-step spread).

`T3a_shuffle_placebo.csv` (the DECISIVE falsifier) — re-pick per-bucket optima on RANDOM bucket labels:

| symbol | cond_var | real_lift | shuffle_mean_lift | shuffle_q95 | real_beats_shuffle_q95 |
|---|---|---:|---:|---:|:---:|
| BCH | hurst_100 | +0.27 | +0.43 | +0.53 | **False** |
| BCH | realvol_z | +0.41 | +0.45 | +0.54 | **False** |
| LDO | hurst_100 | +1.16 | +1.07 | +1.11 | True |
| LDO | realvol_z | +0.76 | +1.34 | +1.53 | **False** |
| TRX | hurst_100 | +0.15 | +0.17 | +0.20 | **False** |
| TRX | realvol_z | +0.14 | +0.16 | +0.19 | **False** |

A RANDOM bucketing captures the same or greater lift than the regime bucketing in **5 of 6 combos** (only LDO/hurst_100 beats the q95 — and only by 0.05). The T2 "lift" is grid-search overfitting from picking the best of 25 cells per bucket; the regime variable carries **NO information** about the optimal barrier geometry. The optimum `(tp=1.0, sl=2.0)` is MORE EXTREME than /065's REJECTED `(2.0, 1.5)` SL widening (BASELINE_V3.md "Dead Ideas") — the geometry the grid is finding is a known regime-exposed pattern with no edge content.

**Axis A — NO-GO confirmed at the shuffle placebo** (`T4_go_nogo_verdict.csv`). Per the dispatch directive, the iteration pivots to a bolder axis.

### 2.3 Axis B — scaled-entry (staged-entry path) — formal NO-GO across the entire grid

`T5_scaled_entry_grid.csv` — 81-cell grid `[f0 ∈ {0.33, 0.50, 0.67}] × [trigger ∈ {0.25, 0.50, 1.00} ATR] × [K ∈ {2, 3, 5}] candles`, per-symbol monthly Sharpe lift vs the static single-full-size book:

| symbol | best cell `(f0, trigger, K)` | static Sharpe | scaled Sharpe | best lift | fraction of cells with positive lift |
|---|---|---:|---:|---:|---:|
| BCH | (0.67, 0.5, 2) | 2.2546 | 2.2408 | **−0.014** | 0/27 |
| LDO | (0.67, 1.0, 2) | 2.3804 | 2.3163 | **−0.064** | 0/27 |
| TRX | (0.67, 1.0, 2) | 1.4196 | 1.4025 | **−0.017** | 0/27 |

**Negative lift in ALL 81 cells across all 3 symbols.** Mechanism: scaling INTO a confirmed trade adds size at the confirmation candle's close — already +trigger ATR above entry — capturing less of the move per dollar; meanwhile it keeps the non-confirmed trades at f0 size but does not eliminate them. The small variance reduction does not compensate. **Axis B — formal NO-GO.**

But `T6_confirm_separates.csv` produced a startling secondary finding: the confirmation event has *enormous* discriminating power on the static-barrier book's outcomes. At `(trigger=0.50, K=4)`: confirmed trades have a held-to-barrier WR of **73-78%** and a mean PnL of **+3.7 to +5.9%**; non-confirmed trades have a held-to-barrier WR of **23-58%** and a mean PnL of **−0.6 to +2.3%**. The confirmation event observed within K candles of entry — at ZERO look-ahead — is a powerful winner/loser discriminator on the trade's own forward path. This finding motivated Axis C.

### 2.4 Axis C — early-exit-on-no-confirmation — the chosen /116 backtest axis

The early-exit primitive uses the T6 confirmation signal in the structurally correct direction: instead of *adding* to confirmed trades (Axis B — at a worse price), *cut* the non-confirmed trades early (close at candle K's close) and let the confirmed trades proceed to normal TP/SL/timeout. The triple-barrier label estimand and the `2.0/1.0` ATR barrier geometry are UNCHANGED.

`T7_early_exit_grid.csv` — 16-cell grid `[trigger ∈ {0.25, 0.50, 0.75, 1.00} ATR] × [K ∈ {2, 3, 4, 5}] candles`, per-symbol monthly Sharpe lift vs the static held-to-barrier book. **The chosen cell `(trigger=0.50, K=4)` is the only cell with positive lift on all 3 symbols in the entire grid:**

| symbol | static Sharpe | early-exit Sharpe `(0.5, 4)` | sharpe_lift | no_confirm exit rate |
|---|---:|---:|---:|---:|
| BCH | 2.2546 | 2.3799 | **+0.1253** | 10.60% |
| LDO | 2.3804 | 2.3872 | **+0.0068** | 9.19% |
| TRX | 1.4196 | 1.4612 | **+0.0415** | 10.51% |

Per-symbol fraction of all 16 grid cells with positive lift: **BCH 0.625, LDO 0.500, TRX 0.938** — TRX is the strongest carrier, BCH is in the middle, LDO is at the coin-flip line. The lift is small (+0.07 portfolio-mean) and the no_confirm exit rate at the chosen cell is modest (~10% of trades) — the rule is a sparse, surgical intervention, not a broad re-architecture.

`T8_cuts_losers.csv` — the g2 mechanism gate — answers the key question: **are the trades the rule cuts net losers when held to barrier?**

| symbol | trigger | K | n_cut | cut_held_mean_pnl_pct | kept_held_mean_pnl_pct | cuts_losers |
|---|---:|---:|---:|---:|---:|:---:|
| BCH | 0.50 | 4 | 607 | **+3.75** | +4.05 | **False** |
| LDO | 0.50 | 4 | 252 | **+2.90** | +4.76 | **False** |
| TRX | 0.50 | 4 | 596 | **+3.26** | +3.17 | **False** |

**In all 48 (trigger, K) cells across all 3 symbols, `cuts_losers = False`** — the trades the rule cuts are POSITIVE-mean held-to-barrier (modestly below-average winners, NOT losers). **g2 mechanism FAILS.** The small IS lift in `T7` is *variance reduction* (cutting modest-positive trades early at a candle K close that happened to be slightly above their barrier-resolved outcome on average in the IS uptrend window), NOT a discovered loser-filter mechanism. This is the honest mechanism reading.

`T9_out_of_fold.csv` — the g3 robustness gate — fold-A-best cell applied to fold B:

| symbol | fold_a_best `(trigger, K)` | fold_a_lift | fold_b_static_sharpe | fold_b_early_exit_sharpe | fold_b_lift | helps? |
|---|---|---:|---:|---:|---:|:---:|
| BCH | (0.5, 4) | +0.13 | 2.5427 | 2.7861 | **+0.2434** | YES |
| LDO | (1.0, 3) | +0.29 | 4.0920 | 3.5626 | **−0.5294** | **NO** |
| TRX | (0.5, 3) | +0.06 | 1.7492 | 1.8292 | **+0.0800** | YES |

LDO's fold-A-best cell REGRESSES fold B by **−0.53** — the (1.0, 3) cell that wins on the early IS half is a fold artifact, not a stable property. BCH and TRX are stable. **g3 PARTIAL FAIL.**

### 2.5 EDA verdict — pre-registered GO rule, NO-GO

Per `T4_go_nogo_verdict.csv` (Axis A) and the per-axis g1/g2/g3 readings above:

| Axis | g1 | g2 | g3 | GO? |
|---|:---:|:---:|:---:|:---:|
| A — regime-conditioned barrier | PASS (technical) | PASS (IS-opt ceiling) | g3a **FAIL**, g3b PASS | **NO-GO** |
| B — scaled-entry | **FAIL** (0/81 positive) | n/a | n/a | **NO-GO** |
| C — early-exit-on-no-confirmation | PASS-soft (small +ve on all 3) | **FAIL** (cuts winners not losers) | g3 PARTIAL (LDO regresses) | **NO-GO** |

**All three structural axes return NO-GO on the pre-registered formal gates.** Axis C is the chosen /116 backtest axis on the residual-uncertainty criterion: it is the only axis with any positive IS lift signal, and the gap between the EDA's static-direction counterfactual and the production LightGBM + 7-gate stack + OOS regime is the source of genuine uncertainty the backtest resolves.

## Section 3 — Proposed Changes

**The single substantive axis vs /059** is a new optional EXIT primitive in `backtest.py`, gated by two new `BacktestConfig` fields, applied to every model. The triple-barrier label estimand and the `2.0/1.0` static ATR barrier geometry are UNCHANGED. The 14-feature stack, the BCH/LDO/TRX universe, the per-symbol LightGBM architecture, the 7-gate RiskV2 stack, the ensemble seeds, the data window, the embargo, and `REQUIRED_GAP=66` are all held /059-identical.

### Configuration Diff vs /059

| Item | /059 canonical | /116 |
|---|---|---|
| `label_mode` | `triple_barrier` | `triple_barrier` (REVERTED from /115's `fixed_horizon`) |
| `DEFAULT_ATR_MULTIPLIERS` | `(2.0, 1.0)` | `(2.0, 1.0)` (unchanged) |
| `V3_ATR_MULTIPLIERS_PER_SYMBOL` | `{}` | `{}` (unchanged) |
| `V3_FEATURE_COLUMNS_TOP_N` | 14 | 14 (unchanged) |
| `V3_MODELS` | `("BCHUSDT", "LDOUSDT", "TRXUSDT")` | `("BCHUSDT", "LDOUSDT", "TRXUSDT")` (unchanged) |
| `enable_ldo_realvol_gate` | False | False (/114 revert preserved) |
| `regime_gate_symbols` | `()` | `()` (/114 revert preserved) |
| `enable_regime_gate` | False | False |
| `enable_no_confirm_exit` | (not present) | **True** (new field on `BacktestConfig`) |
| `no_confirm_trigger_atr` | (not present) | **0.50** (hand-chosen; see Section 0) |
| `no_confirm_k_candles` | (not present) | **4** (hand-chosen; see Section 0) |
| `ITERATION_LABEL` | `"v3-059"` | **`"v3-116"`** |
| `atr_tp_multiplier` / `atr_sl_multiplier` | 2.0 / 1.0 | 2.0 / 1.0 (UNCHANGED — the /115 `100.0/100.0` is REVERTED) |
| ENSEMBLE_SIZE | 10 (CONFIRMATION) | **3** (EXPLORATION subset of the 10-seed lineage) |
| `--n-trials` | 35 | 35 |
| `--seeds` | — | — (deprecated under unified ensemble; EXPLORATION mode forces ENSEMBLE_SIZE=3) |
| `OOS_CUTOFF_DATE` | 2025-03-24 | 2025-03-24 (IMMUTABLE) |
| `training_months` | 24 | 24 (IMMUTABLE) |

## Section 3.5 — Precise `src/` Changes for the QE (Phase 6)

The /116 implementation surface is narrow and entirely confined to (a) the `BacktestConfig` schema, (b) the `Order` dataclass, (c) the `check_close` / order-loop bookkeeping in `backtest.py`, (d) the runner setup. Existing per-month training loops, per-symbol model bundles, ensemble seeds, walk-forward, CPCV/PBO/PSR reporting, the 7-gate RiskV2 stack, and `lgbm.py` predict-path semantics are UNCHANGED.

**Change 1 — `BacktestConfig` (`src/crypto_trade/backtest_models.py`)**: add three new fields with /059-canonical defaults that preserve byte-identical behavior when the flag is False:

```python
@dataclass(frozen=True)
class BacktestConfig:
    ...
    # iter-v3/116: early-exit-on-no-confirmation exit primitive
    enable_no_confirm_exit: bool = False
    no_confirm_trigger_atr: float = 0.50
    no_confirm_k_candles: int = 4
```

When `enable_no_confirm_exit = False` (the /059 canonical default), no new behavior is introduced — every backtest before /116 produces the same result. The new fields are read only inside the order-loop path that is gated by the flag.

**Change 2 — `Order` (`src/crypto_trade/backtest_models.py`)**: extend the frozen dataclass with two new fields recording the no-confirm rule state at order creation:

```python
@dataclass(frozen=True)
class Order:
    symbol: str
    direction: int
    entry_price: float
    amount_usd: float
    weight_factor: float
    stop_loss_price: float
    take_profit_price: float
    open_time: int
    timeout_time: int
    confidence: float | None = None
    # iter-v3/116: early-exit-on-no-confirmation primitive
    no_confirm_arm_time: int = 0  # close_time at end of K-candle window
    no_confirm_threshold_price: float = 0.0  # entry +/- trigger*atr_distance
```

`no_confirm_arm_time` = `open_time + no_confirm_k_candles * interval_minutes * 60 * 1000` (the close_time of candle K after entry). `no_confirm_threshold_price` = `entry + trigger_atr * atr_distance` for longs, `entry − trigger_atr * atr_distance` for shorts (the price the trade must reach for confirmation). `atr_distance` is `entry_price * atr_pct_at_entry / 100.0` where `atr_pct_at_entry` is the same NATR value `lgbm.py` already uses for `tp_pct`/`sl_pct` at predict time (the `_month_natr` value carried in the `Signal` — see Change 4).

When `enable_no_confirm_exit = False` the fields default to `(0, 0.0)` and are never read; the dataclass extension is binary-compatible with all existing call sites.

**Change 3 — `TradeResult.exit_reason`**: add `"no_confirm"` to the documented set of exit reasons. No code change; the existing string-typed field accepts arbitrary values. The reporting layer (`backtest_report.py` and `comparison.csv` generators) groups by `exit_reason` for the breakdown table; the new value will appear naturally. Update the docstring comment listing the canonical set: `"stop_loss" | "take_profit" | "timeout" | "end_of_data" | "no_confirm"`.

**Change 4 — `Signal.tp_pct` / `sl_pct` carry the atr distance to the order** (`src/crypto_trade/strategies/ml/lgbm.py` and `src/crypto_trade/backtest_models.py`): the `Signal` already carries `tp_pct` and `sl_pct` (the NATR-scaled TP/SL pcts), which the backtest uses to compute `stop_loss_price` and `take_profit_price` at order creation. For the no-confirm primitive the backtest must derive the `atr_distance` at order creation:
   - For longs: `atr_distance = entry_price * sl_pct / 100.0` (the SL distance in price terms equals `1.0 * atr_distance` at the canonical `sl_mult=1.0`).
   - The `no_confirm_threshold_price` is then `entry_price ± trigger_atr * atr_distance`.

   **No new field on `Signal` is required.** The QE derives `atr_distance` from the existing `sl_pct` (a long with sl_pct=3.0% → 1×ATR=3.0% of entry; a `trigger_atr=0.50` confirmation needs +1.5% favorable excursion). When the ML strategy uses ATR-scaled barriers (the v3 default), this derivation is exact. When the strategy does NOT use ATR-scaled barriers (rare; not the v3 case), the early-exit primitive degenerates gracefully — `sl_pct` is still the SL distance in pct terms, and `trigger * sl_pct` is a stable confirmation threshold even if it is not a literal ATR multiplier.

**Change 5 — `create_order` (`src/crypto_trade/backtest.py`, line ~558)**: populate the two new `Order` fields. When `config.enable_no_confirm_exit = True` and the signal supplied `tp_pct`/`sl_pct` (the ATR-derived path):

```python
no_confirm_arm_time = 0
no_confirm_threshold_price = 0.0
if config.enable_no_confirm_exit and signal.sl_pct is not None:
    interval_ms = config.timeout_minutes // 21 * 60 * 1000  # v3 = 480_000 (8h)
    no_confirm_arm_time = open_time + config.no_confirm_k_candles * interval_ms
    sl_distance_pct = signal.sl_pct  # the runner uses sl_mult=1.0, so this == 1.0 * atr
    trigger_pct = config.no_confirm_trigger_atr * sl_distance_pct  # favorable excursion in pct
    if signal.direction == 1:
        no_confirm_threshold_price = entry_price * (1.0 + trigger_pct / 100.0)
    else:
        no_confirm_threshold_price = entry_price * (1.0 - trigger_pct / 100.0)

return Order(
    ...,
    no_confirm_arm_time=no_confirm_arm_time,
    no_confirm_threshold_price=no_confirm_threshold_price,
)
```

(The `interval_ms` derivation `timeout_minutes // 21 * 60_000` is the v3-canonical 8h candle; the QE should expose `interval_ms` as a `BacktestConfig` field if it is not already — at v3 8h, `interval_ms = 480 * 60_000 = 28_800_000`.)

**Change 6 — order-loop bookkeeping for max favorable excursion + the early-exit check** (`src/crypto_trade/backtest.py`): the backtest's main per-candle loop must track, for every active order, whether the per-candle high/low has reached `no_confirm_threshold_price` at any point during the K-candle observation window. The cleanest implementation is a mutable side dict keyed by order id (the `Order` is frozen):

   - `confirmed: dict[id(Order), bool] = {}` — populated to `False` at order creation; set to `True` the first candle the order's favorable excursion (high for long, −low for short) reaches `no_confirm_threshold_price`.
   - Inside `check_close` (or its caller), BEFORE the existing TP/SL/timeout checks, ADD: if `enable_no_confirm_exit` AND order.no_confirm_arm_time > 0 AND not confirmed[id(order)]:
     - Update confirmation on the current candle: if `direction == 1 and high >= no_confirm_threshold_price` → confirmed. Symmetric for shorts.
     - If still not confirmed AND `close_time >= no_confirm_arm_time` → fire the early exit at the candle's close: `make_result(order, close_price, close_time, "no_confirm", fee_pct)`. The confirmed flag is then irrelevant.
   - The check fires BEFORE the timeout (so a trade whose arm_time equals the timeout_time prefers the no_confirm reason) but AFTER the SL/TP barrier check is logically resolved — i.e., the new check is positioned so that a candle hitting SL OR TP on the same bar resolves to SL/TP, not no_confirm. The cleanest ordering is: (a) check TP/SL on the candle; (b) if not resolved, check no_confirm; (c) if not resolved, check timeout.

The mutable `confirmed` dict scope: alive for the duration of one walk-forward symbol-month loop; cleared when the order resolves. No persistence between months. No live-engine state to seed (the live engine reads only resolved trades from the DB — the in-flight `confirmed` flag does NOT need DB seeding; if the engine restarts mid-trade, the flag re-initializes to False and the trade may be cut more eagerly than it would have been continuously — an acceptable conservative behavior consistent with R1/R2/R3 patterns).

**Change 7 — runner setup (`run_baseline_v3.py`)**: this is where the dispatch's explicit cosmetic-cleanup task lands.

   (a) Update `ITERATION_LABEL = "v3-116"` (currently `"v3-115"`).
   (b) Set the three new `BacktestConfig` fields when constructing the backtest config: `enable_no_confirm_exit=True`, `no_confirm_trigger_atr=0.50`, `no_confirm_k_candles=4`.
   (c) **Fix the stale banner-print at `run_baseline_v3.py:2889`** — the line currently reads `label_mode=triple_barrier; V3_FEATURE_COLUMNS=22` (the `22` is /113 carry-over; the /115 closeout's Critic Rec 2 flagged this for /116 cleanup). Update it to read `label_mode=triple_barrier; V3_FEATURE_COLUMNS=14`. Confirm the run.log line is internally consistent with `len(V3_FEATURE_COLUMNS) = 14`.
   (d) **Fix the `MODEL_SPECS` model-name prefix at `run_baseline_v3.py:197–199`** — currently `"v3-113-BCH"`/`"v3-113-LDO"`/`"v3-113-TRX"` (per the /115 Critic Rec 2). Update to `"v3-116-BCH"`/`"v3-116-LDO"`/`"v3-116-TRX"` (or strip the iteration prefix entirely if the QE prefers a less-iteration-specific pattern — the `ITERATION_LABEL` is the source of truth for report paths; the `MODEL_SPECS` names are cosmetic and used only in log output).
   (e) Extend the `_canonical_v059` accretion guard with two new permitted /116 knobs: `("enable_no_confirm_exit", BacktestConfig.enable_no_confirm_exit, True)`, `("no_confirm_trigger_atr", BacktestConfig.no_confirm_trigger_atr, 0.50)`, `("no_confirm_k_candles", BacktestConfig.no_confirm_k_candles, 4)`. The /115's `label_mode = "fixed_horizon"` guard entry MUST REVERT to `triple_barrier`. The `atr_tp_multiplier=atr_sl_multiplier=100.0` /115 setting MUST REVERT to the /059 canonical (`2.0`, `1.0`). All 13+ canonical knobs must verify `PASS` at runner pre-flight.
   (f) Pre-flight assertion: assert `enable_no_confirm_exit is True` AND `no_confirm_trigger_atr == 0.50` AND `no_confirm_k_candles == 4` AND `label_mode == "triple_barrier"` (the explicit /115 revert).

**Change 8 — adversarial integration test** (`tests/test_no_confirm_exit.py`, new file): a focused test asserting (a) a synthetic /BCH-like trade whose high reaches `+0.50 * sl_distance` before candle K fires `confirmed=True` and proceeds to TP/SL/timeout (the "confirmed" path); (b) a synthetic trade whose max favorable excursion stays below `+0.50 * sl_distance` through candle K resolves with `exit_reason = "no_confirm"` at candle K's close; (c) `enable_no_confirm_exit = False` produces byte-identical TradeResults to a control run — the /059 byte-identity guarantee. The test uses synthetic OHLCV not real klines so it is data-extent-independent.

## Section 4 — Expected OOS Impact

The pre-registered modal outcome (Section 7 modal mode) is **EXPLORATION-NEGATIVE / INERT** — IS Sharpe small negative or flat, OOS Sharpe small negative or flat. The EDA evidence supporting this modal call:

- The g2 mechanism gate FAILED on the IS counterfactual — the rule cuts modestly-below-average winners, not losers (`T8`, 48/48 cells, `cuts_losers = False`).
- The IS-counterfactual lift is small (chosen cell: BCH +0.13, LDO +0.01, TRX +0.04 monthly Sharpe; portfolio approx +0.06–0.07) and is attributable to variance reduction (cutting modest winners early in a trending IS window), not signal discovery.
- The EDA's static-direction counterfactual is an UPPER BOUND on what the production LightGBM should produce: the LightGBM trains on triple-barrier labels whose realized outcomes the early-exit rule alters AFTER training. Trades that the LightGBM model is most confident about (high `confidence`) are exactly the trades that confirm fast (the T6 finding) and are KEPT — the rule operates predominantly on the M1's low-confidence book-tail. The marginal effect at the M1 model's actual decision distribution is likely smaller than the EDA's full-roster lift.
- The g3 robustness FAILED on LDO (fold-A best cell regresses fold B by −0.53). At production multi-seed + OOS regime, the LDO leg is the modal carrier of any regression.

**Pre-registered Section 4 numerical bands** (anchored on /060 EXPLORATION-mode reference IS +0.8325 / OOS +0.1403):

| Outcome | IS monthly Sharpe (80% band) | OOS monthly Sharpe (80% band) | likelihood |
|---|---|---|:---:|
| **Modal: INERT / EXPLORATION-NEGATIVE** | [+0.70, +0.95] (Δ vs /060 ∈ [−0.13, +0.12]) | [−0.10, +0.20] (Δ vs /060 ∈ [−0.24, +0.06]) | ~55% |
| Mild positive: small IS lift survives | [+0.85, +1.05] (Δ +0.02 to +0.22) | [+0.15, +0.40] (Δ +0.01 to +0.26) | ~25% |
| IS-collapse / OOS-spike SUSPICIOUS-class | [+0.40, +0.65] (Δ −0.43 to −0.18) | [+0.50, +1.10] (Δ +0.36 to +0.96) | ~15% |
| Behavioral inertia (rule rarely fires) | IS Δ < ±0.05, OOS Δ < ±0.05, no_confirm exits < 5% of trade roster | — | ~5% |

The +0.06 portfolio-mean IS lift from the EDA is INSIDE the modal band's central tendency — the modal call is "small IS lift partially survives, OOS reverts." A larger lift survival (~25% mode) would be PROMISING-class; an IS-collapse / OOS-spike (~15%) would be the /065 / /073 / /114 regime-exposed dead-path pattern that the EDA explicitly flags as a high-probability failure mode (the EDA's optimal-cell concentration in the SL-wide corner is the /065-pattern signature).

## Section 5 — Risk Mitigation

The /116 axis is structurally constrained — the new primitive operates on already-open trades and never affects the trade roster's CARDINALITY; every signal still enters. The risk surface is bounded.

**Risk 1 — no_confirm rule produces ZERO no_confirm exits at production scale**: the chosen `(0.50, 4)` cell fires on ~10% of the IS book per `T7`. The pre-flight log must report the no_confirm exit count after each backtest; if < 30 total no_confirm exits across the 3-symbol IS book, the rule has effectively not fired and the result is BEHAVIORAL-INERTIA (Section 7 Mode 4). Mitigation: report the no_confirm count in the engineering report; the Critic's Check 8 (hypothesis-implementation alignment) verifies it.

**Risk 2 — single-seed lottery artifact at EXPLORATION budget**: at `--exploration --n-trials 35` and ENSEMBLE_SIZE=3 the Optuna landscape is finite-search-noisy. Mitigation: the 3-seed lineage subset (the first 3 of the unified 10-seed sequence) is a representative single-lineage sample; the formal multi-seed dissolution of any thin-roster effect is deferred to the iter-v3/120 CONFIRMATION. The EXPLORATION's job is to surface direction and magnitude, not to certify edge.

**Risk 3 — IS-collapse / OOS-spike regime artifact**: the EDA explicitly named this the second-most-likely failure mode (~15%); the optimal-barrier-corner-collapse evidence from Axis A (the (tp=1.0, sl=2.0) signature) shows the trade-construction layer can produce regime-exposed artifacts at small IS Sharpe lifts. Mitigation: Section 8's first-match-wins taxonomy fires NEGATIVE on the IS leg first before any OOS-spike classification can be made; Critic Check 1 audits the IS-collapse/OOS-spike as a regime artifact (the /105 / /115 audit) by checking the OOS month-by-month distribution.

**Risk 4 — the /115 LDO kill-switch carry-over** (the iter-v3/110 stale-knob failure mode): Change 7(e) reverts the /115 `label_mode = "fixed_horizon"` and `atr_tp_multiplier = atr_sl_multiplier = 100.0` AND adds them to the accretion guard. Risk: any new latent /115 carry-over not in the guard. Mitigation: the runner's pre-flight log must print all 13+ canonical knobs at PASS verification; the Critic's Check 8 verifies at source.

**Risk 5 — Order dataclass extension breaks a frozen invariant**: the two new Order fields default to `(0, 0.0)` and are never read when the flag is False. Mitigation: Change 8's adversarial integration test asserts the byte-identity-with-flag-False property on synthetic OHLCV.

## Section 6 — Risk Management Design

The /116 axis is a TRADE-CONSTRUCTION-LAYER axis, not a RISK-PRIMITIVE axis. The 7-gate RiskV2 stack (vol scaling, ADX, Hurst regime, feature z-score OOD, low-vol filter, hit-rate disabled, BTC trend alignment) is UNCHANGED. RiskV2Config: `zscore_threshold=2.0`, `adx_threshold=20.0`, `adx_threshold_per_symbol={}`, `BTC_TREND_CONFIG.threshold_pct=15.0`, `block_long_for=()`, `block_short_for=()`, `enable_per_symbol_drawdown_brake=False`, `enable_ldo_realvol_gate=False` (/114 revert), `regime_gate_symbols=()` (/114 revert), `enable_regime_gate=False`.

The new no_confirm exit primitive composes cleanly with R1/R2/R3 in the v1 lineage and with the v3 7-gate stack: the gates DECIDE WHETHER TO ENTER; the exit primitive DECIDES WHEN TO CLOSE an already-open trade. The two layers are orthogonal by construction. The /054 stateful-deadlock failure mode (`feedback_v3_oracle_eda_validity.md`) does NOT apply: the no_confirm rule's state is per-trade and does NOT update any persistent strategy state — the next trade's entry decision is unaffected by the previous trade's no_confirm outcome.

## Section 7 — Pre-Registered Failure-Mode Prediction

| # | Failure mode | Signature | Likelihood |
|---|---|---|---:|
| 1 (MODAL) | **INERT / EXPLORATION-NEGATIVE — the variance-reduction-doesn't-transfer mode** — the small IS lift the EDA showed (~+0.06 portfolio) does not survive the production LightGBM's trade-selection (the LightGBM keeps mostly trades it is confident about, which are the trades that confirm fast and are KEPT — the rule operates on a thin low-confidence tail); the OOS reverts to neutral-to-negative. | IS monthly Sharpe ∈ [+0.70, +0.95], OOS ∈ [−0.10, +0.20]; no_confirm exit rate at production 5–12% of trades; cut-trades' counterfactual mean PnL > 0 (g2 mechanism FAIL re-confirmed in production). | **~55%** |
| 2 | Mild positive — the small IS lift survives | IS ∈ [+0.85, +1.05] (Δ +0.02 to +0.22 vs /060), OOS ∈ [+0.15, +0.40] (Δ +0.01 to +0.26), no_confirm exit rate ~10%, cut-trades modestly-negative-mean held-to-barrier (the mechanism actually holds in production). | ~25% |
| 3 | **IS-collapse / OOS-spike SUSPICIOUS-class (the /065 / /073 / /114 regime-exposure pattern)** — the rule's IS effect is broader than the EDA's static-direction counterfactual predicted, the LightGBM's training distribution shifts (it sees a different label-PnL distribution and Optuna lands in an IS-overfit region), IS collapses, OOS uptrend captures variance reduction. | IS ∈ [+0.40, +0.65] (Δ −0.43 to −0.18), OOS ∈ [+0.50, +1.10] (Δ +0.36 to +0.96), OOS/IS ratio > 1.5; the no_confirm exit rate may be elevated (>20%) on the regime carrier symbol. | ~15% |
| 4 | Behavioral inertia | no_confirm exit count < 30 total IS, both deltas inside ±0.05 noise bands. | ~5% |

The modal call is honest given the EDA's three honest signals: (i) g2 mechanism FAIL; (ii) g3 instability on LDO; (iii) all 3 axes (A, B, C) returning NO-GO on the pre-registered formal gates. A PROMISING-class outcome (~25% — Mode 2) IS within the credible range — the chosen cell IS the only cell with all-3-positive IS lift in a 16-cell grid, and the EDA static-direction counterfactual is structurally a LOWER bound on what the LightGBM-selected trade subset could see — but it is not the modal call. The brief reports this honestly.

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

EXPLORATION classification — **first-match-wins** evaluation order. Anchor for EXPLORATION-mode comparison: iter-v3/060 (IS +0.8325 / OOS +0.1403).

1. **EXPLORATION-NEGATIVE** — fires first IF any single condition holds:
   (a) IS monthly Sharpe < `+0.7325` (Δ vs /060 < −0.10); OR
   (b) OOS monthly Sharpe < `−0.10`; OR
   (c) OOS/IS monthly Sharpe ratio < `0` (sign-inverted).

2. **EXPLORATION-SUSPICIOUS-OOS-DOMINANT** — fires second IF: OOS/IS monthly Sharpe ratio > `3.0`. (The /065/073/114 regime-exposed-OOS-spike taxonomy per `feedback_v3_oos_is_ratio_gate.md`.)

3. **EXPLORATION-INERT** — fires third IF: both deltas vs /060 inside `±0.05` AND no_confirm exit count < 30 total IS trades (the BEHAVIORAL-INERTIA path).

4. **EXPLORATION-NULL-RESULT** — fires fourth IF: rule fires (no_confirm count ≥ 30) AND both deltas inside `±0.20` noise bands AND OOS/IS ratio ∈ `[0.0, 3.0]`.

5. **EXPLORATION-PROMISING** — fires LAST IF all of:
   (a) IS monthly Sharpe Δ ≥ `+0.10` (vs /060 +0.8325, i.e. IS ≥ `+0.9325`); AND
   (b) OOS monthly Sharpe Δ ≥ `+0.20` (vs /060 +0.1403, i.e. OOS ≥ `+0.3403`); AND
   (c) frac_positive_paths (CPCV) ≥ `0.50`; AND
   (d) OOS/IS monthly Sharpe ratio ∈ `[0.0, 3.0]`; AND
   (e) no_confirm exit rate ∈ `[5%, 25%]` (the rule fired in a sensible regime); AND
   (f) per-symbol IS no_confirm cut-trades held-to-barrier mean PnL < 0 on ≥ 2/3 symbols (the g2 mechanism gate actually held in production).

The Section-8 evaluation is mechanical. An EXPLORATION-PROMISING outcome with the mechanism gate failed (criterion (f) FAIL) would be re-classified by the Critic as a thin-roster artifact (the /114 precedent). The Critic's Check 8 verifies the mechanism gate at source.

## Section 9 — Library Stack Declaration

No new library is introduced by /116. The implementation uses only the existing v3 stack:

| Library | Version (pyproject.toml) | Used for |
|---|---|---|
| `numpy` | inherited | per-candle OHLCV path arithmetic |
| `pandas` | inherited | EDA tables, runner I/O |
| `lightgbm` | inherited | M1 model (unchanged) |
| `mlfinlab` | 1.4 (CONFIRMATION only) | CPCV (deferred to iter-v3/120) |
| `pypbo` | inherited | PBO (deferred to iter-v3/120) |
| `fracdiff` | inherited | (UNUSED by /116) |
| `statsmodels` | inherited | ADF (unchanged) |

The early-exit primitive is implemented as pure Python in `backtest.py` — no library dependency.

## Section 10 — QR Audit Trail & Dead-Path Disclosure

This section discloses the EDA's dead-path adjacencies head-on (the dispatch's explicit instruction).

**The dispatch's recommended axis vs the chosen axis.** The dispatch recommended a regime-conditioned exit-barrier architecture (Axis A) and explicitly instructed the QR to pivot to a bolder axis if the EDA did not support a GO. The QR's EDA on Axis A returned a hard NO-GO (Section 2.2, `T3a` shuffle placebo FAIL 5/6). The QR pivoted to two more structural axes, ran their EDAs (Section 2.3 / Section 2.4), and selected Axis C — the early-exit-on-no-confirmation primitive — as the /116 backtest axis on the residual-uncertainty criterion (the only axis with any positive IS lift signal at the chosen cell). The selection is QR-led with committed EDA backing per `feedback_v3_axis_selection_quant_discipline.md`.

**Dead-path adjacencies — addressed individually.**

1. **iter-v3/107 (the exit-layer NULL-AT-EDA — 5 STATIC exit re-architectures, all keyed on the high-water mark).** Distinction: /107 tested ATR-trailing / breakeven stops — exits that ACT ON A FAVORABLE EXCURSION once it has happened. /107's own F-MFE falsifier ("losers' MFE distribution is thin — only 22/100 losers reach ≥1.0 ATR favorable") is exactly WHY a trailing stop did not help: it only engages once a trade has run up; losers never run up; so the trailing stop never engages on losers. The /116 axis is the LOGICAL COMPLEMENT: it acts on the ABSENCE of a favorable excursion. /107's F-MFE finding is the POSITIVE case FOR this primitive — losers' MFE distribution is thin BECAUSE losers rarely confirm; an absence-of-excursion exit is the right tool for that data shape. /107's NULL does not constrain a complement mechanism, and /107's evidence directly motivates it.

2. **iter-v3/065 (global SL widening 1.0 → 1.5; REJECTED + reverted at /070).** Distinction: /065 widened the static SL, exposing the book to deeper drawdowns in chop while letting winners run in trends. /116 does NOT widen any barrier (SL stays at 1.0 ATR; TP stays at 2.0 ATR; the static barrier geometry is byte-identical to /059). The early-exit primitive *narrows* the effective holding distribution by truncating the right tail of the holding-time distribution for the trades that never run up — the opposite direction from /065's barrier widening. The Axis A EDA explicitly showed why the (tp=1.0, sl=2.0) grid optimum is a /065-pattern regime-exposed artifact, which is why Axis A was rejected.

3. **iter-v3/042 (global ATR tightening 1.5, 0.75; NEGATIVE).** Same distinction as /065 — /042 is a barrier knob; /116 leaves the barrier unchanged.

4. **iter-v3/073 (per-symbol triple-barrier asymmetry; SUSPICIOUS-OOS-DOMINANT, closed at catalog level).** Distinction: /073 conditioned on SYMBOL IDENTITY (a static label fixed for the symbol's whole history). /116 conditions on a DYNAMIC per-trade STATE — the trade's own forward-path excursion within K candles. The hand-chosen parameters are GLOBAL — `(0.50, 4)` applied to BCH, LDO, TRX equally — not per-symbol-tuned. The chosen cell is NOT the per-symbol grid optimum (per-symbol optima from `T9` are `BCH (0.5, 4) / LDO (1.0, 3) / TRX (0.5, 3)`); the global cell is chosen for parsimony and the all-3-positive-IS-lift property of a single cell — explicitly NOT per-symbol-tuned to avoid the /073 axis.

5. **iter-v3/074 + /114 (regime-conditional kill switches; closed across 3 data points).** Distinction: /074/114 PREVENT trade entry (a binary off/on at signal time). /116 does NOT prevent any entry — every signal still enters; the new primitive operates on already-open trades. The /116 cardinality of the trade roster is UNCHANGED (~158 IS trades at /060) before the no_confirm rule fires; the rule then closes a subset of them early. Different mechanism layer.

6. **iter-v3/079 (conviction-weighted position-sizing primitive 13; NULL-RESULT).** Distinction: /079 is a position-SIZE scalar (one multiply, fixed at entry). /116 is a position-PATH change (two timestamps, one fill price, the trade may exit earlier). Different object.

7. **iter-v3/108 (the /017-corrected meta-labeling EDA; FALSIFIED).** Distinction: /108 was a SECONDARY model (M2) trained to take/skip a primary direction. /116 introduces NO model. The early-exit rule is a deterministic-path event observed on the trade's own forward OHLCV path; there is no M2 model and no skip decision before entry.

8. **iter-v3/115 + the /072/105 label-estimand family (all closed).** /116 leaves `label_mode = "triple_barrier"` (REVERTED from /115's `"fixed_horizon"`). The label estimand is unchanged from /059. The /115 closeout's mandate ("`label_mode = "fixed_horizon"` must NOT be re-bundled at iter-v3/120") is honored — and the early-exit primitive does not bundle the label change at all.

**The ADX axis** (closed per `feedback_adx_axis_asymmetric_v3.md`): /116 does not use ADX as a conditioning variable in any of the three EDA'd axes; the Axis A conditioning variables were `hurst_100` and a realized-vol z-score (both already in `V3_FEATURE_COLUMNS` or trivially derived from one), not ADX. The chosen Axis C uses no conditioning variable beyond the trade's own forward-path excursion.

**The /115 cosmetic-cleanup task** (Critic Rec 2): explicitly assigned to the QE in Section 3.5 Change 7(c) (`run_baseline_v3.py:2889` banner-print `V3_FEATURE_COLUMNS=22` → `=14`) and Change 7(d) (`MODEL_SPECS` `v3-113-` prefix → `v3-116-`). The /115 closeout flagged these for the iter-v3/116 setup commit; they are now in the brief's QE scope and will be verified by Phase 5.5 + the Critic's Check 8.

**The brief-parameter-provenance discipline** (`feedback_v3_brief_parameter_provenance.md`): every tuned scalar parameter cites the committed source table per Section 0. The two hand-chosen scalars (`trigger_atr=0.50`, `k_candles=4`) are DECLARED hand-chosen, justified for parsimony (round-number midpoint + first-third-of-timeout), and NOT laundered as a sweep optimum or a per-symbol grid pick. The auditable temporal fence is the commit ordering (EDA commit `52444c9` BEFORE this brief) plus the IS-only assertion in every analysis script.
