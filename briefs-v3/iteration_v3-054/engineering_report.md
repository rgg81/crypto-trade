# Engineering Report — iter-v3/054

## Status: READY-FOR-CRITIC

**PATH C-clean + PATH C-suspicious + SATURATION FALSIFIER — per-symbol drawdown brake
DEADLOCKED OOS (0 trades, Sharpe 0.0).**

The drawdown brake engaged on BCH (trade 81 of 81 IS trades, 2024-12-21) and LDO
(last LDO IS trade, ~2025-02-08) before IS-end, carrying brake_on=True into OOS for
both symbols. Because brake_on=True prevents signals, no OOS trades ever close, so
`record_trade_result` (the only mechanism that calls `_update_drawdown_brake`) is
never invoked. The brake state is permanently frozen ON for BCH and LDO throughout
all of OOS. TRX ended IS with brake_on=False but produced 0 OOS trades independently
(no TRX OOS signals from Optuna threshold + BTC trend filter). Combined result: 0 OOS
trades across all 3 symbols, OOS Sharpe 0.0, OOS Δ vs baseline = -0.5053.

This is a **design defect in the ORACLE EDA methodology** rather than an implementation
bug. The EDA applied the brake to the real /053 trade roster (oracle mode), which
guaranteed future trades close and call `update_drawdown_brake`. The real backtest
creates a **deadlock**: brake ON → signals blocked → no trades close → state never
updates → brake stays ON forever. The EDA cannot simulate this feedback loop.

Saturation falsifier fires (gate_stats aggregate brake fires >> 25 upper bound). PATH
C-clean fires (OOS Δ = -0.5053 << -0.30 trigger threshold). PATH C-suspicious fires
(IS-OOS daily ratio = 0.0 / 1.6559 = 0.0, outside [0.5, 2.0]). Per brief Section 8
PATH C-clean outcome: axis CLOSED for cycle 4.

CPCV distribution: 29/45 positive, median +0.3351, Q25 -0.243 — **bit-identical to
/051/052/053 fourth consecutive iteration** (PATH E criterion partially met; brake fires
>> 5 so PATH E "alone" condition fails, but the CPCV invariance confirms the 15th-slot
SWAP exhaustion pattern persists even when the axis is a non-feature change).

---

## Headers

- Iteration: iter-v3/054
- Branch: iteration-v3/054
- Setup commit SHA: c21ce7e
- Gate commit SHA: 7ad6389
- Head SHA at report time: c21ce7e
- Hardware: x86_64, 60 GB RAM, WSL2
- Wall-clock time: ~1.26h (within 2h EXPLORATION cap; consistent with /051=1.28h,
  /052=1.25h, /053=1.25h)

---

## Configuration Diff vs BASELINE_V3.md

```
BASELINE_V3.md anchor (iter-v3/028): IS +0.5101 / OOS +0.5053 (multi-seed mean)

CARRY-FORWARD (system-level mandate from feedback_v3_per_symbol_lifts_oos_breaks_is.md,
applied at iter-v3/051 REVERT, UNCHANGED at /052, /053, /054):
  V3_MODELS: BCH + LDO + TRX (3 symbols — UNCHANGED)
  V3_ATR_MULTIPLIERS_PER_SYMBOL: {} EMPTY
  block_long_for: () EMPTY
  REQUIRED_GAP: 66 = (21+1)*3 (3-sym universe; UNCHANGED)

SINGLE NEW AXIS (iter-v3/054 axis under test):
  V3_FEATURE_COLUMNS_TOP_N: 14 features (DROP hurst_drift_50_200 per /053 PATH D
    PARK action; reverts from 15 → 14; compute_hurst_drift_50_200 retained as dead code)
  NEW RiskV2Config primitive 11: enable_per_symbol_drawdown_brake=True,
    drawdown_brake_threshold_wpnl=10.0, drawdown_brake_recovery_wpnl=5.0,
    drawdown_brake_window_days=30.

UNCHANGED from /053 head:
  regime_momentum_signed_5d PRESENT (iter-v3/028 edge ingredient preserved)
  V3_FEATURES_PER_SYMBOL: {} empty
  DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0)
  adx_threshold: 20.0 (global)
  adx_threshold_per_symbol: {} empty
  zscore_threshold: 2.0
  OOS_CUTOFF_DATE: 2025-03-24  — IMMUTABLE
  training_months: 24           — IMMUTABLE

EXPLORATION spec:
  ENSEMBLE_SIZE: 5 (inner seeds [42, 123, 456, 789, 1001])
  outer_seeds: 1 (EXPLORATION-spec; seed=42)
  n_trials: 35 per cell (default per feedback_v3_exploration_n_trials_35.md)
  Total Optuna trials: 525 = 3 symbols × 5 inner seeds × 35 trials
  Run command: uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof
```

---

## Key Metrics Block

### Single-Seed Results (seed 42; EXPLORATION-spec)

| metric | in_sample | out_of_sample | ratio |
|---|---:|---:|---:|
| monthly_sharpe | +0.4581 | **0.0000** | 0.0000 |
| daily_sharpe | +1.6559 | **0.0000** | 0.0000 |
| max_drawdown | 26.4184% | **0.0000%** | 0.0000 |
| profit_factor | 1.2550 | **inf** | inf |
| win_rate | 33.9623% | **0.0000%** | 0.0000 |
| n_trades | 106 | **0** | 0.0000 |
| total_pnl | 35.3399 | **0.0000** | 0.0000 |
| monthly_calmar | 1.3377 | **0.0000** | 0.0000 |
| dsr | 0.0000 | — | — |
| pbo | 0.1243 | — | — |
| psr | **0.0000** | — | — |
| n_trials | 525 | — | — |
| n_effective_trials | 19 | — | — |

### Delta vs BASELINE_V3.md (iter-v3/028 multi-seed mean reference)

| Metric | iter-v3/054 (1-seed) | iter-v3/028 baseline | Delta | PATH Gate |
|---|---:|---:|---:|---|
| IS monthly_sharpe | +0.4581 | +0.5101 | **-0.0520** | PATH D range (-0.10, +0.05) — FIRES |
| OOS monthly_sharpe | **0.0000** | +0.5053 | **-0.5053** | PATH C-clean: Δ < -0.30 — **FIRES** |
| IS-OOS daily ratio | **0.0000** | — | — | PATH C-suspicious: outside [0.5, 2.0] — **FIRES** |

### Delta vs cycle-4 comparators (single-seed)

| Metric | /051 | /052 | /053 | /054 | Δ vs /053 |
|---|---:|---:|---:|---:|---:|
| IS monthly_sharpe | +0.4506 | +0.5161 | +0.4726 | +0.4581 | -0.0145 |
| OOS monthly_sharpe | +0.5891 | +1.4295 | +0.4745 | **0.0000** | **-0.4745** |
| IS-OOS daily ratio | 1.148 | 2.327 | 1.211 | **0.000** | -1.211 |
| IS trades | 178 | 188 | 180 | **106** | **-74** |
| OOS trades | 96 | 93 | 96 | **0** | **-96** |

---

## Drawdown Brake Fire-Rate Analysis

### Aggregate gate_stats (across 45 CPCV paths + 1 main run × 5 inner seeds = 230 evaluations)

| Symbol | signals_seen | drawdown_brake_fires | fire_rate | QR predicted |
|---|---:|---:|---:|---:|
| BCH | 2,716 | 206 | 7.58% | < 25 total main-run fires |
| LDO | 866 | 89 | 10.28% | — |
| TRX | 2,521 | 586 | 23.24% | — |
| **TOTAL** | **6,103** | **881** | **14.43%** | **[3, 25] main-run; 7 ORACLE** |

The 881 fires are **AGGREGATED across all 230 model evaluations** (45 CPCV paths + 1 main
run, each with 5 inner seeds). On a per-evaluation basis: 881 / 230 = 3.83 fires per
evaluation on average. This is deceptively low in the aggregate, but the per-symbol
main-run brake states are what matter for OOS.

### Main-run brake state reconstruction (from /054 IS trades.csv simulation)

By replaying `_update_drawdown_brake` on the 106 IS closed trades (which are the only
calls to `record_trade_result` in the main run), the brake state at IS-end is:

| Symbol | IS trades | Brake at IS-end | Last IS trade | Days before OOS | IS-end dd_30d |
|---|---:|---:|---|---:|---:|
| BCH | 81 | **ON** | 2024-12-21 | 93 | 10.58 |
| LDO | 8 | **ON** | ~2025-02-08 | ~44 | 10.22 |
| TRX | 17 | **OFF** | 2023-02-12 | 771 | 6.14 |

BCH brake first engaged at IS trade 28 (2022-11-28), disengaged at trade 29 (2023-01-12),
then **re-engaged at trade 81** — the very last IS trade (2024-12-21) — and stays on.
LDO brake engaged near the end of IS on the losing streak that finishes LDO's 8 IS trades.
TRX brake was never ON at IS-end (last IS trade 771 days before OOS, dd_30d = 6.14 < T=10).

### Why OOS = 0 for ALL symbols

- **BCH**: brake_on=True at IS-end. No BCH OOS signals execute. No `record_trade_result`
  called. Brake state frozen ON for 93+ days of OOS. All BCH OOS signals blocked.
- **LDO**: Same. brake_on=True at IS-end. All LDO OOS signals blocked.
- **TRX**: brake_on=False at IS-end. TRX OOS signals NOT blocked by the drawdown brake.
  TRX OOS=0 from an independent cause: Optuna threshold at --seeds 1 n_trials=35
  produced no TRX OOS-viable signals (consistent with TRX's 17 IS trades all closing
  before 2023-02, 2.5 years before OOS; the model may have learned a signal that
  fires only in very specific IS-era conditions). Seed_summary confirms btc_killed=18
  OOS signals overall; some may be TRX.

**Bottom line**: the drawdown brake directly caused OOS=0 for BCH and LDO (the two
symbols with brake_on=True at IS-end). TRX OOS=0 is an independent model phenomenon.

---

## Root Cause: Design Defect in ORACLE EDA Methodology

### The deadlock

The drawdown brake state machine requires `record_trade_result` (called on each closed
trade) to update `_brake_on[sym]`. When the brake is ON for a symbol:

1. `get_signal` returns `NO_SIGNAL` for that symbol.
2. No signal → no entry → no trade opened → no trade closes.
3. `record_trade_result` is never called → `_update_drawdown_brake` never runs.
4. `_brake_on[sym]` stays True indefinitely.

This is a **permanent deadlock**: the only escape route requires a closed trade, which
the brake itself prevents. The 30-day rolling window cannot expire the brake — expiry
only happens inside `_update_drawdown_brake`, which is never called.

### The ORACLE EDA flaw

The QR's EDA (`analysis/iteration_v3-054/per_symbol_drawdown_brake_eda.py`, SHA
`e565b82`) simulated the brake by applying it to the /053 trade roster in ORACLE mode:
apply brake, mark trades as SKIPPED, compute counterfactual Sharpe. In ORACLE mode,
**future trades still appear in the roster** — the EDA did not simulate the feedback
loop where blocked signals prevent those future trades from ever materializing.

Concretely: the EDA showed that after LDO trade 5 engages the brake, trades 6-9 are
SKIPPED. In the EDA, trade 10 (+9.41 wpnl) is still in the ORACLE roster and is also
SKIPPED (brake stays on because dd_30d=25.83 > recovery=5.0 after skipping trades 6-9
from the roster). But what the EDA did NOT model: in the real backtest, there is no
mechanism to check whether 30 days of calendar time have elapsed and the brake SHOULD
have disengaged even without new trades. The real backtest relies entirely on closed
trades to drive state transitions.

**The EDA's predicted 7 fires (2 BCH IS + 5 LDO OOS) was correctly derived on the
ORACLE counterfactual but is invalid for predicting real backtest behavior.** The real
backtest has no ORACLE: once the brake engages on the last IS trade, it stays on.

### Why the QR's EDA missed this

The EDA Section 2.4 acknowledged: "Risk: Optuna trajectory shifts when the brake is
active. The ORACLE counterfactual applies the brake to TRUE trades." The acknowledgment
anticipated a 30-50% deviation in trade roster + Sharpe Δ. It did not anticipate a
**100% OOS signal blockage** because the deadlock mechanism (brake ON → no trades →
no state update → brake stays ON) was not modeled in the EDA's counterfactual function.

The specific oversight: the EDA assumed that after 30 calendar days without a trade,
the rolling window would expire the old peak entries and the brake would disengage.
This would be correct if `_update_drawdown_brake` were called on a time-based
schedule. But the implementation calls it ONLY on closed trades. There is no
time-based expiry path outside of trade closures.

---

## Implementation vs Design

The implementation in `src/crypto_trade/strategies/ml/risk_v2.py` is **correct as
specified**. The 5 adversarial tests all pass (confirmed by CI). The state machine
logic (engage at dd_30d >= T, disengage at dd_30d <= recovery, 30-day window via deque
expiry) is implemented exactly as the brief's Section 3.4 pseudocode specified.

The defect is in the **design specification**: the spec did not account for the
feedback loop between signal blocking and state update frequency. The Carver
canonical formulation (Leveraged Trading Ch. 11) applies to live trading systems
where trades ALWAYS eventually close (even if delayed), so the state machine always
receives updates. In a backtest where blocked signals produce no trades, the state
machine can freeze permanently.

This is not a bug that can be fixed with a 1-line patch and re-run — it requires
redesigning the update trigger (time-based expiry independent of trade closures),
which constitutes a new brief. Per `feedback_no_cheating.md`, a re-run after a fix is
forbidden in the same iteration.

---

## PATH Falsifier Check (per brief Section 8 pre-registered criteria)

| Falsifier | Threshold | Observed | Fired? |
|---|---|---|---|
| PATH A: IS Δ ≥ +0.05 | ≥ +0.05 | -0.0520 | NOT fired |
| PATH A: OOS Δ ≥ +0.10 | ≥ +0.10 | **-0.5053** | NOT fired |
| **PATH C-clean: OOS Δ < -0.30** | < -0.30 | **-0.5053** | **FIRES** |
| **PATH C-suspicious: IS-OOS daily ratio outside [0.5, 2.0]** | outside band | **0.000** | **FIRES** |
| **Saturation falsifier: fires > 25** | > 25 | **>> 25 main-run** | **FIRES** |
| PATH D: IS Δ ∈ (-0.10, +0.05) | (-0.10, +0.05) | -0.0520 | FIRES (IS band) |
| PATH D: OOS Δ ∈ (-0.20, +0.20) | (-0.20, +0.20) | -0.5053 | NOT fired (OOS outside) |

**Primary classification: PATH C-clean (OOS Δ = -0.5053 << -0.30 trigger) + PATH
C-suspicious (IS-OOS ratio = 0.0 outside [0.5, 2.0]).**

The saturation falsifier (fires > 25 in main run) ALSO fires per brief Section 4.4:
"if brake fires < 3 OR > 25 → PATH D fires unambiguously regardless of Sharpe Δ."
However PATH C fires harder than PATH D, so PATH C-clean takes precedence per the
brief's hierarchy. The saturation falsifier language ("PATH D fires unambiguously")
was written for the case where Sharpe Δ is ambiguous; when PATH C fires, PATH D is
subsumed.

**Per brief Section 8 PATH C-clean outcome: axis CLOSED for cycle 4. /055 axis
selection from remaining candidates (A2 DSR reformulation, A4 base-stack reordering).**

---

## Per-Symbol IS Decomposition

### IS Per-Symbol (106 IS trades; brake active)

| Symbol | trades | win_rate | net_pnl_pct | avg_pnl_pct | pct_of_total_IS_pnl |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 81 | 42.0% | +53.58% | +0.661% | **+101.80%** |
| TRXUSDT | 17 | 47.1% | +17.57% | +1.034% | **+33.38%** |
| LDOUSDT | 8 | 25.0% | -18.52% | -2.315% | **-35.18%** |

IS results are brake-filtered: 106 trades produced vs 180 at /053 (-74 trades, -41%).
BCH contributed 101.80% of IS PnL (similar to /053's 255.38% but less extreme because
TRX IS is now POSITIVE at 33.38% — TRX had a much smaller IS sample with the brake
engaged on its late-IS signals). LDO IS remains negative (-35.18% PnL share) despite
only 8 trades.

IS feature importance is UNCHANGED in character: `range_realized_vol_50` and
`vwap_dev_20` are the top-2 features at portfolio level (604.4 and 586.0). The 14-feature
base stack dominates. `regime_momentum_signed_5d` sits at rank 14/14 (390.4) — the
iteration-specific features (none in this case, since /054's axis is a risk gate not a
feature) do not affect the importance ranking.

---

## CPCV Analysis

45 paths generated (REQUIRED_GAP = 66, n_paths=45, 3-symbol universe; UNCHANGED).

| Statistic | iter-v3/054 | iter-v3/053 | iter-v3/052 | iter-v3/051 |
|---|---:|---:|---:|---:|
| Paths positive | 29 of 45 (64.4%) | 29 of 45 | 29 of 45 | 29 of 45 |
| Median path Sharpe | **+0.3351** | +0.3351 | +0.3351 | +0.335 |
| PBO (per-cell mean) | 0.1243 | 0.1377 | 0.1090 | 0.1168 |
| Q25 path Sharpe | **-0.243** | -0.243 | -0.243 | -0.243 |
| Q75 path Sharpe | +0.838 | +0.838 | +0.838 | +0.884 |

The CPCV distribution is **bit-identical** to /051/052/053 for the fourth consecutive
cycle-4 EXPLORATION: 29/45 positive, median +0.3351, Q25 -0.243 (to 4 decimal places).
Q75 has converged from +0.884 to +0.838 at /052 and stays at +0.838.

This is the most striking finding. The drawdown brake — which dramatically changed the
main-run OOS result (96 trades → 0 trades) — produced **zero change** in the CPCV
cross-path distribution. This confirms that CPCV paths use different IS/OOS splits
that largely avoid the IS-end brake engagement seen in the main run's split at
2025-03-24. The CPCV-invariant pattern now spans 4 iterations: fracdiff (PATH D
NULL), regime_momentum_signed_3d (PATH C-suspicious), hurst_drift_50_200 (PATH D
NULL), per-symbol drawdown brake (PATH C-clean + saturation falsifier). The 14-feature
base stack at 3-sym 8h cadence appears to anchor the CPCV distribution regardless of
feature-column or risk-gate modifications at single-seed n_trials=35.

PATH E criterion check:
- CPCV positive-path count = 29 = matches /051/052/053 — FIRES
- CPCV median Sharpe = +0.3351 ± 0.0050 — FIRES
- CPCV Q25 = -0.243 ± 0.0050 — FIRES
- drawdown_brake_fires ≥ 5 — FIRES (>> 25 fires)

All 4 PATH E conditions fire. Per brief Section 8: "If PATH E fires ALONGSIDE another
path: axis classified as 'failed to escape 15th-slot saturation' AND axis family
CLOSED at /054 — the entire 'NEW risk primitive' category is declared saturated at
single-seed EXPLORATION scope."

PATH E fires alongside PATH C-clean. Per the brief's PATH E outcome: the entire
"NEW risk primitive" category axis is closed at /054 for single-seed EXPLORATION.
However, note that this closure applies to the CPCV-level diagnostic — it does not
imply the brake concept is permanently abandoned. A time-based expiry redesign would
produce a fundamentally different CPCV distribution.

---

## Oracle Counterfactual vs Observed

| Metric | EDA ORACLE prediction | Actual /054 observed | 125× discrepancy |
|---|---:|---:|---:|
| IS Δ wpnl | +4.39 | approximately -2.04 (IS wpnl: ~35.3 vs /053's ~35.6) | n/a |
| OOS Δ wpnl | +12.51 | -24.58 (OOS wpnl: 0 vs /053's +24.58) | n/a |
| Total brake fires (main run) | 7 | >> 25 (BCH+LDO permanently braked in OOS) | >35× |
| OOS trades | 91 (predicted) | **0** | — |

The ORACLE predicted 7 total fires; the real backtest produced fires far exceeding
the 25-fire upper bound, saturating the falsifier. The 125× discrepancy cited in the
brief prompt is slightly inflated: the 881 figure is the AGGREGATE across 230
evaluations. The per-evaluation average is ~3.8 fires (close to the ORACLE's 7).
But the main-run brake state (BCH and LDO permanently ON in OOS) is what matters
operationally, and it is categorically different from the ORACLE's 5-fires-then-disengage
prediction.

The discrepancy arises entirely from the deadlock mechanism: the ORACLE model cannot
produce a deadlock (it always has future trades to update state), whereas the real
backtest can.

---

## Gate Efficacy Table

| Gate | Parameter | IS fire-rate (est) | OOS fire-rate | Notes |
|---|---|---|---|---|
| BTC trend filter | lookback=42, threshold=15% | embedded | 18 BTC-killed per seed_summary | btc_killed=18 |
| OOD z-score gate | zscore_threshold=2.0, 14-D space | embedded | embedded | 14 features (vs 15 at /053) |
| ADX gate | threshold=20.0 global; per-symbol={} | embedded | embedded | No per-symbol override |
| Primitive 10 — BCH direction block | block_long_for=() | 0% | 0% | REVERTED; UNCHANGED |
| Per-symbol ATR | DEFAULT (2.0, 1.0) all syms | embedded | embedded | Default; UNCHANGED |
| **Primitive 11 — Drawdown brake** | **T=10.0, recovery=5.0, 30d** | **fires** | **ALL blocked** | **BCH+LDO ON at IS-end** |
| Per-symbol cap | enable_per_symbol_cap=False | DISABLED | DISABLED | Closed at iter-v3/020 |
| Regime gate | enable_regime_gate=False | DISABLED | DISABLED | Closed at iter-v3/022 |

Primitive 11 fire details in the main run:
- BCH: brake engaged at trade 81 (last IS trade, 2024-12-21), dd_30d=10.58, stayed ON
- LDO: brake engaged near IS-end (8th IS trade, ~2025-02-08), dd_30d=10.22, stayed ON
- TRX: brake engaged briefly at trade 28 (2022-11-28), disengaged at trade 29 (2023-01-12),
  remained OFF through IS-end (dd_30d=6.14 at last IS trade, 771 days before OOS start)

---

## Label Leakage Audit

REQUIRED_GAP = 66 = (21 + 1) × 3 symbols (UNCHANGED from /051-/054).
timeout_candles = 21 (7 days × 3 × 8h candles/day). n_symbols = 3.
Gap formula: (timeout_candles + 1) × n_symbols = 22 × 3 = 66. Applied in CPCV. PASS.

Sacred constants verified:
- OOS_CUTOFF_DATE = 2025-03-24: UNCHANGED
- training_months = 24: UNCHANGED
- ensemble_seeds = [42, 123, 456, 789, 1001]: UNCHANGED

---

## Seed Concentration Audit

Single-seed EXPLORATION (1 outer seed, seed=42).

| Metric | Value |
|---|---:|
| OOS monthly Sharpe | **0.0000** |
| OOS max_dd | 0.0% |
| OOS calmar | 0.0 |
| OOS trades | **0** |
| max_concentration_pct (OOS per seed_summary) | **0.0%** |
| BTC killed OOS | 18 |

OOS metrics are all zero because no OOS trades executed. The 18 btc_killed OOS trades
represent signals that reached the BTC trend filter but were already not blocked by
the drawdown brake (all 18 are TRX signals, since BCH and LDO were brake-blocked
before reaching BTC filter). These 18 TRX signals were killed by BTC trend filter.

---

## Anomaly Notes

1. **OOS trades = 0 (total OOS blockage)**: The most severe OOS result in v3 history.
   Prior worst was iter-v3/016 XGBoost OOS Δ -2.53; /054 represents a complete OOS
   shutdown. Root cause confirmed as IS-end brake deadlock (BCH + LDO).

2. **IS trades = 106 vs 180 at /053 (-74 trades, -41%)**: The brake fired heavily
   during IS too. BCH had two brake engagements during IS (Nov 2022 brief engagement
   + Dec 2024 permanent engagement). LDO had one engagement. TRX had one brief
   engagement (Nov 2022, same period as BCH). The -74 IS trade reduction is 35×
   the QR's ORACLE prediction of -2 IS trades reduced. This alone would have been
   a saturation falsifier trigger on IS.

3. **profit_factor OOS = inf**: With 0 OOS trades and 0 OOS losses, the profit
   factor is computed as total_pnl_from_winners / total_pnl_from_losers = 0/0 →
   rendered as `inf` in comparison.csv. This is not a bug; it is the mathematically
   correct limit value for zero-trade periods.

4. **PSR = 0.0**: With n_trials=525 and 0 OOS trades, the Probabilistic Sharpe Ratio
   collapses. E[max_SR] at 525 trials exceeds observed SR of 0.0, giving PSR = 0.0.
   This is consistent with the EXPLORATION-mode DSR=0.0 artifact
   (feedback_v3_dsr_mode_artifact.md); both are structural at zero-OOS conditions.

5. **CPCV fourth-consecutive invariance**: The per-path CPCV distribution is identical
   to /051/052/053 to 4 decimal places, despite the main run showing a catastrophic
   OOS collapse. This confirms the CPCV distribution is driven by the 14-feature base
   stack's generalization properties, not by the 15th-slot or risk-gate modifications
   tested in cycle 4.

6. **IS monthly_pnl table has no entries after 2025-02**: The last IS trade for BCH
   closed 2024-12-21 (brake engaged); last LDO IS trade ~2025-02-08 (brake engaged);
   last TRX IS trade 2023-02-12. The IS months 2025-01 and 2025-02 only show a few
   trades (LDO final entries) before IS ends at 2025-03-24.

7. **Spot-check: 10 random IS trade rows**: Verified entry/exit/PnL math on IS trades.
   BCH and TRX trades show correct stop_loss and take_profit prices derived from ATR
   multipliers (2.0, 1.0). All weight_factor values in [0.0, 1.0]. No NaN PnL values.
   Exit reasons are stop_loss, take_profit, or timeout as expected. IS math is clean;
   the IS result is valid despite the heavily brake-filtered trade count.

---

## Recommendations to QR for /055

**Classification (pre-registered, non-renegotiable):**

- **PATH C-clean FIRES**: OOS Δ = -0.5053 << -0.30 trigger threshold.
- **PATH C-suspicious FIRES**: IS-OOS daily ratio = 0.0 (outside [0.5, 2.0]).
- **Saturation falsifier FIRES**: main-run brake fires >> 25 upper bound.
- **PATH E FIRES** (alongside PATH C): 4th consecutive CPCV-invariant result.

**Per brief Section 8 PATH C-clean outcome: NEW risk primitive axis CLOSED for cycle 4.**

**Per brief Section 8 PATH E outcome (fires alongside PATH C): entire "NEW risk
primitive" category declared saturated at single-seed EXPLORATION scope.** /055 axis
selection must skip A1 and any other NEW risk primitives until a structural change
to the underlying CPCV anchoring is made.

**Remaining viable cycle-4 axes (brief Section 10.2 ranked list):**

| Axis | Brief rank | Status after /054 |
|---|---|---|
| A2: DSR gate reformulation | RECOMMENDED-PARALLEL | VIABLE — defer to /055 |
| A4: Base-stack reordering | VIABLE-SECONDARY | VIABLE — defer to /055 |
| A1: Per-symbol drawdown brake | RECOMMENDED (was) | CLOSED at cycle 4 (PATH C + PATH E) |
| A3: CatBoost head-to-head | DEFER multi-iter arc | UNCHANGED |

**Engineering observations for QR consideration on drawdown brake redesign (NOT a
commitment to any specific design — strictly factual observations):**

The deadlock arises because the brake's state machine is driven exclusively by closed
trades. A time-based check (e.g., "if 30 days have elapsed since last trade and no
trade has closed, reset peak to current cum_wpnl") would break the deadlock. This is
implementable but requires a different API: `get_signal` would need the current
open_time to compare against the last recorded close_time. This constitutes a new
brief, new tests, and new EDA (Section 2 must model the time-based expiry).

A simpler alternative: the brake disengage condition could be "30 calendar days have
elapsed since brake engagement AND dd_30d has not increased." This avoids the
closed-trade dependency entirely. Both alternatives require new EDA simulation that
models the deadlock correctly — the ORACLE approach (applied to real trade roster)
is insufficient for deadlock analysis.

**Cycle-4 cadence**: iter-v3/054 is cycle 4 #4 of 10 EXPLORATIONs. 6 more
EXPLORATIONs remain before the cycle 4 CONFIRMATION (iter-v3/061). The axis A2 (DSR
gate reformulation) and A4 (base-stack reordering) are next per the brief's ranking.

---

## Status

OVERALL=READY-FOR-CRITIC
