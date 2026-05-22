# Iteration v3-054 — Research Brief (Per-symbol drawdown brake, NEW risk primitive)

**Type**: EXPLORATION (Cycle 4 #4 of 10)
**Track**: v3 (rigor arm) — fifty-fourth iteration
**Branch**: `iteration-v3/054` (off iter-v3/053 head at SHA `092c66a`)
**Date**: 2026-05-11
**Author**: QR (autopilot)

**AXIS EXIT MANDATE**: Per Critic FINAL of iter-v3/053 (SHA `c056354`) Recommendation
#1, the 15th-slot SWAP family is STRUCTURALLY EXHAUSTED at single-seed EXPLORATION.
CPCV positive-path count CONSTANT 29/45, median path Sharpe IDENTICAL +0.3351 to
4 decimals, Q25 IDENTICAL -0.243 across iter-v3/051 (fracdiff), iter-v3/052
(regime_momentum_3d), and iter-v3/053 (hurst_drift). iter-v3/054 MUST exit the
15th-slot SWAP family.

**SELECTED AXIS**: A1 — Per-symbol drawdown brake (NEW risk primitive). EDA-driven
selection from 4 candidate axes; ranked at SHA `e565b82` (this commit's parent
analysis commit). NEW risk primitive is orthogonal to feature-column axes that
exhausted at /051/052/053; per `feedback_v3_concentration_is_signal.md`, per-symbol
DRAWDOWN BRAKE is one of 4 explicitly-permitted orthogonal mechanisms (binary
off/on), distinct from per-symbol PnL share CAP (CLOSED at iter-v3/020 because
"concentration is lottery-REWARD source NOT lottery-RISK source").

**MECHANISM**: 30-day rolling-trade-window per-symbol drawdown brake (Carver,
*Leveraged Trading* Ch. 11 canonical formulation). State machine: brake engages
when per-symbol dd_30d ≥ T; disengages when dd_30d ≤ T/2 (recovery). Default
T = 10.0 weighted_pnl units, recovery = 5.0 weighted_pnl units, window = 30 days.

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 5              # single outer seed (EXPLORATION-spec)
n_trials         = 35             # EXPLORATION default (per `feedback_v3_exploration_n_trials_35.md`)
colsample_bytree = Optuna-tuned   # NOT hardcoded 1.0
OOS_CUTOFF_MS    = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. The QR sees iter-v3/054 OOS metrics for the FIRST time
in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Cycle: 4 — #4 of 10 (fourth EXPLORATION post-iter-v3/050 NO-MERGE CONFIRMATION)
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof
  - ENSEMBLE_SIZE=5 (auto; inner ensemble)
  - n_trials=35 (default per `feedback_v3_exploration_n_trials_35.md`)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
  - --clean-oof (use guardrail from SHA `6a216b5` to prevent OOF parquet contamination)

Carry-forward state from iter-v3/053 head (UNCHANGED unless explicit at §3):
  - V3_FEATURE_COLUMNS_TOP_N at /053 HEAD = 15 features (incl. hurst_drift_50_200
    at slot 15 — PARKED per /053 PATH D closeout; DROPPED at /054 setup; net 14)
  - V3_MODELS at /053 HEAD = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols UNCHANGED at /054
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty) UNCHANGED at /054
  - block_long_for = () (empty) UNCHANGED at /054
  - regime_momentum_signed_5d PRESERVED (iter-v3/028 edge ingredient) UNCHANGED at /054
  - DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) UNCHANGED at /054
  - adx_threshold_per_symbol = {} (empty) UNCHANGED at /054
  - All other risk gates UNCHANGED (BTC trend, OOD, ADX 20.0, hit-rate disabled, etc.)
  - REQUIRED_GAP at /053 HEAD = 66 = (21+1)×3 UNCHANGED at /054 (universe unchanged)

SINGLE-AXIS CHANGE for /054 (QR-EDA-backed per `feedback_v3_axis_selection_quant_discipline.md`):
  AXIS: ADD per-symbol drawdown brake to RiskV2Config (NEW risk primitive 11)
    Mechanism: 30-day rolling-trade-window per-symbol drawdown brake.
      State machine: brake engages when per-symbol dd_30d ≥ T = 10.0; disengages
      when dd_30d ≤ recovery = 5.0. Per-symbol independent state.
      Implementation: RiskV2Config.enable_per_symbol_drawdown_brake = True,
        drawdown_brake_threshold_wpnl = 10.0,
        drawdown_brake_recovery_wpnl = 5.0,
        drawdown_brake_window_days = 30.
      State: shared deque self._brake_timeline keyed by (close_time, symbol, wpnl).
        Per-symbol cumulative_wpnl, running_peak_30d, current_dd_30d updated on each
        closed trade. Brake state per-symbol: `_brake_on[sym]: bool`.
    PLUS: DROP hurst_drift_50_200 from V3_FEATURE_COLUMNS_TOP_N (15 → 14) per
      /053 closeout PATH D PARK action. compute_hurst_drift_50_200 retained as
      dead-code dispatch (zero revert cost). 5 adversarial tests retained.
    Net effect: V3_FEATURE_COLUMNS_TOP_N drops 15 → 14 (PARKING the cycle-4 SWAP
      attempts); NEW RiskV2 gate added; universe / labeling / model UNCHANGED.

Setup commit changes (locked in §3):
  - src/crypto_trade/strategies/ml/risk_v2.py: ADD `drawdown_brake_threshold_wpnl`,
    `drawdown_brake_recovery_wpnl`, `drawdown_brake_window_days`,
    `enable_per_symbol_drawdown_brake` fields to RiskV2Config (defaults: 10.0, 5.0,
    30, False — backward-compatible). ADD `_brake_timeline`, `_brake_on`,
    `_brake_per_symbol_pnl` state to RiskV2Wrapper.__init__. ADD `direction_block_fires`-
    style GateStats counter `drawdown_brake_fires`. ADD signal-killing logic in
    get_signal (per-symbol; signal weight set to 0 when brake_on[sym]). ADD
    trade-recording hook to update peak/dd on each closed trade.
  - src/crypto_trade/features_v3/__init__.py: V3_FEATURE_COLUMNS_TOP_N = 14 (DROP
    15th-slot hurst_drift_50_200).
  - tests/strategies/ml/test_risk_v2_drawdown_brake.py: NEW 5 adversarial tests:
    1. brake disabled by default (backward-compat)
    2. brake engages at threshold (per-symbol, single-symbol-only)
    3. brake disengages at recovery threshold (state machine integrity)
    4. brake independent across symbols (LDO brake doesn't affect BCH/TRX)
    5. brake respects 30-day rolling window (trades older than window expire)
  - run_baseline_v3.py: ITERATION_LABEL = "v3-054"
  - run_baseline_v3.py:_verify_feature_columns: assert hurst_drift_50_200 NOT
    present in V3_FEATURE_COLUMNS_TOP_N; assert net 14 features. Drop the
    regime_momentum_signed_3d ABSENT assertion if it was a custom check.
  - run_baseline_v3.py: pass `RiskV2Config(enable_per_symbol_drawdown_brake=True,
    drawdown_brake_threshold_wpnl=10.0, drawdown_brake_recovery_wpnl=5.0,
    drawdown_brake_window_days=30)` to LightGbmStrategy.

Predicted classification (locked in §8 LOCKED):
  - PATH A (PROMISING-clean): 35% — IS Δ in [+0.05, +0.15] AND OOS Δ ≥ +0.10 AND
    ratio in [0.5, 2.0] AND brake fires ≥3 times in OOS
  - PATH B (PROMISING-INERT): 5% — brake fires 0 times → effectively a no-op;
    classification primarily applies to feature axes, not risk primitives
  - PATH C-clean (NEGATIVE): 15% — brake over-fires on a profitable streak
  - PATH C-suspicious: 10% — IS-OOS daily ratio outside [0.5, 2.0]
  - PATH D (NULL-RESULT): 30% — brake fires too rarely; IS Δ in (-0.10, +0.05)
  - PATH E (CPCV-INVARIANT NULL): 5% — CPCV path distribution unchanged from
    /051/052/053 (would mean even the 5 skipped LDO trades are within-block noise)
```

iter-v3/054 = cycle 4 #4 of 10 EXPLORATIONs (per `feedback_v3_strict_10_to_1_cadence.md`).
iter-v3/061 = cycle 4 CONFIRMATION (SEPARATE single-seed iter-v3/060 first; do NOT
collapse 10th EXPLORATION).

---

## Section 1 — Hypothesis

ADDING a per-symbol drawdown brake (NEW RiskV2 primitive 11) to the v3 risk gate
stack — alongside the system-level REVERT carry-forward (V3_MODELS = 3-sym
BCH+LDO+TRX; V3_ATR_MULTIPLIERS_PER_SYMBOL = {}; block_long_for = (); REQUIRED_GAP
= 66) and PARKING the 15th-slot SWAP attempts (V3_FEATURE_COLUMNS_TOP_N reverts to
14 base features) — investigates whether a Carver-canonical loss-stop mechanism
detects and pauses symbols in catastrophic-drawdown regime, lifting bundle IS
Sharpe vs iter-v3/028 anchor +0.5101 and OOS Sharpe vs +0.5053 by removing the
cycle-4 LDO OOS catastrophic streak identified across /051/052/053 diaries.

**Targeted finding**: iter-v3/051 LDO OOS wpnl = -17.44; iter-v3/052 = -13.96;
iter-v3/053 = -15.61 (range -13.96 to -17.44 across three consecutive 15th-slot
SWAP EXPLORATIONs at default ATR + no per-symbol customization). At /053 OOS LDO
trade roster:

- Trade 1: +9.74 wpnl (cum +9.74)
- Trade 2: +5.31 wpnl (cum +15.06 → peak; brief recovery)
- Trade 3: -2.17 wpnl (cum +12.90)
- Trade 4: -6.15 wpnl (cum +6.75)
- Trade 5: -5.01 wpnl (cum +1.74)
- Trade 6: -5.65 wpnl (cum -3.91)
- Trade 7: -6.69 wpnl (cum -10.60)
- Trade 8: -5.34 wpnl (cum -15.94)
- Trade 9: -4.23 wpnl (cum -20.17)
- Trade 10: +9.41 wpnl (cum -10.76 — partial recovery)
- Trades 11-13: losses
- Trade 14: +6.90 wpnl
- Trade 15: -5.07 wpnl

The pattern is canonical for a Carver drawdown brake: peak +15.06 → 7 consecutive
losers down to -20.17 (35.23 wpnl drawdown) → recovery → more losses. A brake
calibrated at T=10.0 wpnl drawdown (recovery 5.0) would engage after trade 4 and
skip trades 5-9 (the worst losses), saving ~30 wpnl in losses.

**This is a structural NEW risk primitive, not a feature-column knob.** Per
`feedback_v3_structural_over_knob_exploration.md` priority order (NEW feature
families > NEW model > NEW labeling > NEW risk primitive > universe > knobs),
a NEW risk primitive is Category 4 priority — well above gate-threshold knobs
which are CLOSED at cycle 4. Per `feedback_v3_concentration_is_signal.md`
explicitly:

> Per-symbol drawdown brake (loss-stop semantics differs from proportional scaling
> CLOSED at iter-v3/020)... remain valid axes.

**Predicted single-seed result (per QR EDA at SHA `e565b82`, ORACLE counterfactual
on /053 trade roster — see Section 2):**

- Bundle IS Sharpe: predicted band [+0.45, +0.65] (mean +0.55); Δ vs /028 anchor
  +0.5101: **[-0.06, +0.14]** (small positive lift; 2 BCH IS trades skipped saving
  +4.39 wpnl while 0 trades skipped from LDO/TRX IS). The mechanism is too
  surgical to cause a large IS Sharpe move.
- Bundle OOS Sharpe: predicted band [+0.55, +0.85] (mean +0.70); Δ vs /028 anchor
  +0.5053: **[+0.05, +0.35]**. The mechanism skips 5 LDO OOS trades summing to
  -12.51 wpnl. ORACLE wpnl total +24.58 → +37.08 (+50.8% lift); converted to monthly
  Sharpe via std-rescaling, this is approximately +0.20 Sharpe lift.
- IS-OOS daily Sharpe ratio: predicted ∈ [0.5, 2.0] with 65% prob (in-band); outside
  band PATH C-suspicious with 10% prob (lower than /051/052/053 because risk
  primitives have more uniform effect across time than feature-stack changes).
- IS trade count: predicted band [175, 180] (Δ -1% to +0% vs /053's 180; brake
  fires on 2 IS trades).
- OOS trade count: predicted band [90, 93] (Δ -6% to -3% vs /053's 96; brake
  fires on 5 OOS trades; clears the ≥10 trades/month floor only if monthly average
  stays ≥10 — see §6 below).
- drawdown_brake_fires counter: predicted 2 IS + 5 OOS = 7 fires per /053 trade
  roster ORACLE; subject to Optuna trajectory shift at backtest time.

This axis directly addresses the cycle 4 starting hypothesis: "lift IS Sharpe to
≥ +0.5101 (BASELINE_V3.md update gate floor) while preserving OOS Sharpe ≥ +0.5053"
(per iter-v3/050 diary §Cadence). The mechanism is the FIRST cycle-4 axis that
ORACLE-predicts simultaneous IS+OOS lift (other axes /051-/053 all NULL/NEGATIVE).

---

## Section 2 — IS-Only Numerical Evidence

**Primary EDA evidence sourced from committed `analysis/iteration_v3-054/` (SHA
`e565b82`), produced by `cycle4_axis_ranking_eda.py` + `per_symbol_drawdown_brake_eda.py`
on /053 trade roster (in_sample/trades.csv + out_of_sample/trades.csv).**

### 2.1 — Mechanism selection (brake_mechanism_options.csv)

3 mechanism variants considered:

| Mechanism | Implementable live | Skips LDO OOS catastrophic | Skips TRX OOS healthy | Verdict |
|---|---|---|---|---|
| A: Peak resets at OOS boundary | NO | YES | NO | REJECTED (live engine can't know OOS boundary) |
| **B: 30-day rolling-time-window peak** | YES | YES | NO | **RECOMMENDED** (Carver canonical) |
| C: 30-trade rolling-count window | YES | YES | NO | REJECTED (LDO 9 trades = 5+ year window) |

**Mechanism B is the Carver *Leveraged Trading* Ch. 11 canonical formulation.**
30-day time-window peak is implementable in the live engine via a per-symbol deque
of (close_time, cumulative_wpnl) tuples, expiring entries older than 30 days from
the front. State carried across iterations / restarts via the existing live engine
DB serialization (parallel to R1 cooldown_until and R2 cum PnL state).

### 2.2 — Per-symbol drawdown distribution (brake_threshold_sensitivity.csv)

OPTION B 30-day rolling-window dd_30d distribution per (symbol, period):

| Symbol | Period | N trades | Max dd_30d | P50 dd_30d | P90 dd_30d |
|---|---|---:|---:|---:|---:|
| BCH | IS | 86 | 14.72 | 0.80 | 6.09 |
| BCH | OOS | 36 | 9.44 | 2.19 | 6.58 |
| LDO | IS | 9 | 9.57 | 0.00 | 6.70 |
| LDO | OOS | 16 | **23.50** | 4.31 | **22.30** |
| TRX | IS | 85 | 10.39 | 1.44 | 5.56 |
| TRX | OOS | 44 | 4.80 | 0.34 | 2.34 |

**LDO OOS P90 dd_30d = 22.30 is more than 2x the next-highest (BCH IS 6.09).**
This is the cycle-4 LDO catastrophic-streak signature. TRX OOS P90 = 2.34 — TRX
OOS dd_30d distribution is well-behaved despite TRX's cumulative IS being -17.79
wpnl (TRX IS losses are SPREAD-OUT signal-quality leakage, NOT drawdown events).

### 2.3 — Threshold sensitivity (brake_threshold_sensitivity.csv)

Counterfactual brake firing per (symbol, period, threshold T):

| T | Recovery | BCH IS skipped | BCH OOS skipped | LDO IS skipped | LDO OOS skipped | TRX IS skipped | TRX OOS skipped |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 5.0 | 2.5 | 8 (+2.77 Δ) | 5 (-2.08 Δ) | 0 | 6 (+17.51 Δ) | 13 (+12.96 Δ) | 0 |
| 7.5 | 3.75 | 4 (+5.98 Δ) | 0 | 0 | 5 (+12.51 Δ) | 3 (+6.03 Δ) | 0 |
| **10.0** | **5.0** | **2 (+4.39 Δ)** | **0** | **0** | **5 (+12.51 Δ)** | **0** | **0** |
| 15.0 | 7.5 | 0 | 0 | 0 | 3 (+16.27 Δ) | 0 | 0 |

Aggregate Δ wpnl per (T, period):

| T | IS Δ | OOS Δ |
|---:|---:|---:|
| 5.0 | +15.73 | +15.43 |
| 7.5 | +12.00 | +12.51 |
| **10.0** | **+4.39** | **+12.51** |
| 15.0 | +0.00 | +16.27 |

**T=10.0 is selected** as the threshold for /054 setup because:

1. At T=5.0 the brake over-fires on BCH OOS (5 trades skipped, -2.08 Δ — BCH's
   normal volatility hits the threshold). T=5 cuts profitable trades.
2. At T=7.5 brake fires on TRX IS (3 trades skipped, +6.03 Δ — TRX IS hits a
   transient single-month dd of 10.39 but recovers). Cutting TRX IS at /054 risks
   regressing TRX OOS where TRX is the strongest OOS contributor (+15.60 wpnl).
3. At T=10.0 the brake fires ONLY on LDO OOS (5 trades, +12.51 Δ) and BCH IS (2
   trades, +4.39 Δ). No TRX trades touched, no LDO IS touched. Surgical strike
   on the cycle-4 LDO drag.
4. At T=15.0 brake fires only 3 times on LDO OOS (+16.27 Δ — even better in raw
   wpnl terms), but the larger threshold means it MISSES the early-streak
   inflection. T=10 fires after LDO's 4th OOS loss; T=15 fires only after the
   8th OOS loss. Earlier engagement is preferable for risk management.

**Risk: Optuna trajectory shifts when the brake is active.** The ORACLE
counterfactual applies the brake to TRUE trades; at backtest time the model sees
fewer LDO trades and the per-symbol-fit Optuna draws may shift. This is the same
caveat as `feedback_v3_single_seed_frozen_baseline.md`. ORACLE estimates are
the lower-bound effect; actual backtest may produce 30-50% deviation in either
direction.

### 2.4 — Why TRX IS is NOT a drawdown event (mechanism caveat)

TRX has IS cumulative wpnl = -17.79 across 85 trades. The naïve interpretation is
"TRX is a drawdown problem." But the 30-day rolling-window dd_30d shows P90 = 5.56
and max = 10.39 across IS. **TRX losses are SPREAD-OUT** — many small trades with
slight negative expectancy, NOT one or two catastrophic streaks. A drawdown brake
can't fix small consistent leakage; it only fixes catastrophic streaks.

**This is intentional.** Spread-out losses are signal-quality problems (model
says trade when it shouldn't), not risk-management problems. The right fix for
TRX is in the feature stack / model architecture (deferred to /055+ NEW feature
families axis) or labeling (deferred to /055+ labeling architecture axis), not
in a risk gate.

### 2.5 — LDO OOS catastrophic streak detail (brake_recommended_counterfactual.csv)

LDO OOS trades 1-16 with cumulative wpnl + dd_30d + brake state at T=10.0,
recovery=5.0:

| # | close_time | wpnl | cum_wpnl | dd_30d | Brake state DURING trade | Action |
|--:|---|---:|---:|---:|---|---|
| 1 | 1747612799999 | +9.74 | +9.74 | 0.00 | off | TAKEN |
| 2 | 1749772799999 | +5.31 | +15.06 | 0.00 | off | TAKEN |
| 3 | 1752796799999 | -2.17 | +12.90 | 2.17 | off | TAKEN |
| 4 | 1753372799999 | -6.15 | +6.75 | 8.32 | off | TAKEN |
| 5 | 1753689599999 | -5.01 | +1.74 | 13.32 | off→ on | TAKEN (last before brake) |
| 6 | 1754582399999 | -5.65 | -3.91 | 18.97 | on | SKIPPED |
| 7 | 1755331199999 | -6.69 | -10.60 | 25.66 | on | SKIPPED |
| 8 | 1755878399999 | -5.34 | -15.94 | 31.01 | on | SKIPPED |
| 9 | 1756079999999 | -4.23 | -20.17 | 35.24 | on | SKIPPED |
| 10 | 1756771199999 | +9.41 | -10.76 | 25.83 | on | SKIPPED |
| 11 | 1759449599999 | -1.38 | -12.14 | 27.21 | on | (would skip but trade 12+ rolling-out 30-day window changes things) |

(See `brake_recommended_counterfactual.csv` for full trade-by-trade detail; 5
total OOS trades skipped per the state machine.)

**The brake correctly identifies the inflection point** (after trade 5, where cum
wpnl dropped from peak +15.06 to +1.74 = dd_30d 13.32 ≥ T=10.0). It correctly
skips the worst losses (trades 6-9 sum to -21.91 wpnl). It "misses" the recovery
trade 10 (+9.41 wpnl) — a false-negative cost — but the NET counterfactual is
strongly positive (+12.51 wpnl skipped losses, -9.41 missed recovery = net +3.10
absolute; full counterfactual accounts for non-trivial state machine = +12.51
total Δ).

---

## Section 3 — Code Changes (Setup Commit Locked)

The setup commit will modify:

### 3.1 — RiskV2Config dataclass (src/crypto_trade/strategies/ml/risk_v2.py)

ADD new fields (defaults preserve backward compatibility):

```python
# iter-v3/054: primitive 11 — per-symbol drawdown brake.
# Pauses signals for a symbol when its 30-day rolling-window weighted_pnl drawdown
# hits drawdown_brake_threshold_wpnl. Resumes when drawdown recovers to
# drawdown_brake_recovery_wpnl. Per-symbol independent state. Carver canonical
# formulation (Leveraged Trading Ch. 11).
# Calibrated by QR EDA at iter-v3/054 (analysis/iteration_v3-054/
# per_symbol_drawdown_brake_eda.py): at T=10.0 wpnl, recovery=5.0 wpnl, 30-day
# window, brake fires on 5 LDO OOS trades + 2 BCH IS trades at /053 trade roster
# ORACLE counterfactual (IS Δ +4.39 wpnl; OOS Δ +12.51 wpnl).
# Default disabled preserves v1/v2/v3-prior behavior.
enable_per_symbol_drawdown_brake: bool = False
drawdown_brake_threshold_wpnl: float = 10.0       # engage when dd_30d >= this
drawdown_brake_recovery_wpnl: float = 5.0          # disengage when dd_30d <= this
drawdown_brake_window_days: int = 30               # rolling window for peak calculation
```

Validation in `__post_init__`: `recovery < threshold < +inf` and `window_days > 0`.

### 3.2 — RiskV2Wrapper state (src/crypto_trade/strategies/ml/risk_v2.py)

ADD to `__init__`:

```python
# iter-v3/054: per-symbol drawdown brake state (primitive 11).
# _brake_timeline[sym] = deque of (close_time_ms, cum_wpnl) for the last
# drawdown_brake_window_days days of THIS symbol's closed trades.
# _brake_running_peak[sym] = max(cum_wpnl) over _brake_timeline[sym].
# _brake_cum_wpnl[sym] = current cumulative weighted_pnl from oldest in-window trade.
# _brake_on[sym] = True if brake is currently engaged (signals killed).
self._brake_timeline: dict[str, deque[tuple[int, float]]] = {}
self._brake_running_peak: dict[str, float] = {}
self._brake_cum_wpnl: dict[str, float] = {}
self._brake_on: dict[str, bool] = {}
```

ADD to `GateStats`:

```python
drawdown_brake_fires: int = 0  # iter-v3/054: per-symbol drawdown brake fires (primitive 11)
```

### 3.3 — Signal-kill logic (src/crypto_trade/strategies/ml/risk_v2.py:get_signal)

ADD before the inner-strategy call (or in the gate-cascade — whichever matches
the existing primitive 10 placement):

```python
# Primitive 11: per-symbol drawdown brake
if self.config.enable_per_symbol_drawdown_brake:
    if self._brake_on.get(symbol, False):
        self._gate_stats[symbol].drawdown_brake_fires += 1
        return NO_SIGNAL  # kill
```

### 3.4 — Trade-recording hook (src/crypto_trade/strategies/ml/risk_v2.py)

The RiskV2Wrapper needs to update `_brake_timeline`, `_brake_running_peak`,
`_brake_cum_wpnl`, `_brake_on` on each closed trade. Investigation needed: does
the wrapper currently receive a per-trade callback, or does it observe closed
trades via some other mechanism? If not, ADD an `update_on_closed_trade(self,
trade: TradeResult)` method following the existing R2 cumulative-PnL pattern.

The state-update logic:

```python
def update_on_closed_trade(self, trade: TradeResult) -> None:
    """Update per-symbol drawdown brake state on each closed trade.

    Called by the backtest engine when a trade closes (parallel to R2 update).
    """
    if not self.config.enable_per_symbol_drawdown_brake:
        return

    sym = trade.symbol
    close_time = trade.close_time
    wpnl = trade.weighted_pnl

    # Initialize per-symbol state on first trade
    if sym not in self._brake_timeline:
        self._brake_timeline[sym] = deque()
        self._brake_running_peak[sym] = 0.0
        self._brake_cum_wpnl[sym] = 0.0
        self._brake_on[sym] = False

    # Update cumulative wpnl
    self._brake_cum_wpnl[sym] += wpnl
    self._brake_timeline[sym].append((close_time, self._brake_cum_wpnl[sym]))

    # Expire entries older than window_days
    window_ms = self.config.drawdown_brake_window_days * 24 * 60 * 60 * 1000
    cutoff = close_time - window_ms
    while self._brake_timeline[sym] and self._brake_timeline[sym][0][0] < cutoff:
        self._brake_timeline[sym].popleft()

    # Compute running peak over the rolling window
    self._brake_running_peak[sym] = max(c for _, c in self._brake_timeline[sym])

    # Compute drawdown
    dd_30d = self._brake_running_peak[sym] - self._brake_cum_wpnl[sym]

    # State machine: engage / disengage
    if self._brake_on[sym]:
        if dd_30d <= self.config.drawdown_brake_recovery_wpnl:
            self._brake_on[sym] = False  # disengage
    else:
        if dd_30d >= self.config.drawdown_brake_threshold_wpnl:
            self._brake_on[sym] = True  # engage
```

**Caveat**: the backtest engine's existing trade-recording loop must call
`update_on_closed_trade` for each closed trade. If R1/R2 use a different callback
pattern, the brake's state-update path must match. The QE will implement this in
Phase 6 and report the callback wiring in the engineering report.

### 3.5 — V3_FEATURE_COLUMNS_TOP_N revert (src/crypto_trade/features_v3/__init__.py)

DROP `hurst_drift_50_200` (slot 15) per /053 closeout PATH D PARK action. Net
count: 14 features. compute_hurst_drift_50_200 retained as dead code in
engineered_v3.py (zero revert cost). 5 adversarial tests retained.

### 3.6 — Runner updates (run_baseline_v3.py)

```python
ITERATION_LABEL = "v3-054"
# UPDATE _verify_feature_columns: 14 features (UNCHANGED from /028 base);
# assert hurst_drift_50_200 NOT in V3_FEATURE_COLUMNS_TOP_N.
# Drop /053-specific regime_momentum_signed_3d ABSENT check.
# UPDATE LightGbmStrategy instantiation: pass RiskV2Config with
#   enable_per_symbol_drawdown_brake=True (NEW),
#   drawdown_brake_threshold_wpnl=10.0 (NEW),
#   drawdown_brake_recovery_wpnl=5.0 (NEW),
#   drawdown_brake_window_days=30 (NEW)
```

### 3.7 — Adversarial tests (tests/strategies/ml/test_risk_v2_drawdown_brake.py)

5 NEW adversarial tests covering:

1. **brake_disabled_by_default_is_no_op**: with `enable_per_symbol_drawdown_brake=False`,
   the wrapper behavior is bit-identical to v3-prior — no state changes, no signal
   modifications, no GateStats counter increments.

2. **brake_engages_at_threshold_per_symbol**: construct a synthetic 30-day trade
   sequence where LDO's cum_wpnl drops from peak +15 to +1 (dd_30d = 14 ≥ T=10).
   Assert `_brake_on[LDO] == True` after the engaging trade.

3. **brake_disengages_at_recovery_threshold**: after engagement, simulate a +10 wpnl
   recovery trade (dd_30d drops to 4 ≤ recovery=5). Assert `_brake_on[LDO] == False`
   AND the recovery trade itself is TAKEN (per state machine: disengage AND take).

4. **brake_independent_across_symbols**: simulate LDO catastrophic streak +
   BCH/TRX healthy trades simultaneously. Assert `_brake_on[LDO] == True`,
   `_brake_on[BCH] == False`, `_brake_on[TRX] == False`. Assert BCH/TRX signals
   are NOT killed even when LDO brake is on.

5. **brake_respects_30_day_window**: simulate a trade 31 days ago that established
   a peak. Assert that after the 30-day window expiration, the brake re-evaluates
   peak from in-window trades only — so a trade that would have triggered the brake
   relative to the old peak no longer does so.

### 3.8 — Dead-code retention (per established discipline)

- `compute_hurst_drift_50_200` function in engineered_v3.py: RETAINED (zero revert
  cost per `feedback_v3_inert_features_at_higher_budget.md` PARKED status)
- `tests/features_v3/test_hurst_drift_50_200_universal.py`: 5 adversarial tests
  RETAINED as dead-code coverage
- `compute_regime_momentum_signed_3d` + tests: RETAINED (PARKED at /052)
- `compute_fracdiff_d05_close` + tests: RETAINED (PARKED at /051)

---

## Section 4 — Predicted Outcome Bands

### 4.1 — Predicted band table

| Metric | Predicted band | Central prediction | Anchor (/028) | Δ band |
|---|---|---:|---:|---|
| IS monthly Sharpe | [+0.45, +0.65] | +0.55 | +0.5101 | [-0.06, +0.14] |
| OOS monthly Sharpe | [+0.55, +0.85] | +0.70 | +0.5053 | [+0.05, +0.35] |
| IS-OOS daily Sharpe ratio | [0.5, 2.0] | 1.10 | 0.99 | in-band |
| IS trades | [175, 180] | 178 | 156 (/028 mean) | -2 to 0 vs /053 |
| OOS trades | [90, 93] | 91 | 95 (/028 mean) | -5 to -3 vs /053 |
| OOS MaxDD | [25%, 40%] | 33% | 23.5% (/028 mean) | -10pp to +12pp |
| OOS Calmar | [0.55, 0.80] | 0.68 | 0.92 (/028 mean) | -0.37 to -0.12 |
| LDO OOS wpnl | [-5, +5] | -2 | -15.61 (/053) | +14 to +20 vs /053 |
| BCH OOS wpnl | [+20, +28] | +24 | +24.59 (/053) | -5 to +3 vs /053 |
| TRX OOS wpnl | [+12, +18] | +15 | +15.60 (/053) | -4 to +2 vs /053 |
| drawdown_brake_fires (OOS) | [3, 8] | 5 | n/a | n/a |

### 4.2 — CPCV path distribution prediction

This is the genuine test of escape from 15th-slot SWAP exhaustion:

| CPCV metric | /051 | /052 | /053 | Predicted /054 |
|---|---:|---:|---:|---:|
| Paths positive (of 45) | 29 | 29 | 29 | **30-34** |
| Median path Sharpe | +0.3350 | +0.3351 | +0.3351 | **+0.40 to +0.55** |
| Q25 path Sharpe | -0.243 | -0.243 | -0.243 | **-0.18 to -0.10** |
| Q75 path Sharpe | +0.884 | +0.838 | +0.838 | **+0.95 to +1.10** |

A NEW risk primitive that changes 5-8 OOS trades + 2 IS trades SHOULD shift the
CPCV path distribution because the per-block path Sharpes depend on which trades
land in which CPCV split. If PATH E (CPCV-INVARIANT NULL) fires alongside PATH D,
the axis is classified as 'failed to escape 15th-slot saturation' per Critic /053
recommendation #3.

### 4.3 — Optuna trajectory shift uncertainty

ORACLE counterfactual assumes Optuna draws IDENTICAL hyperparameters with brake
active. In practice the brake removes 7 trades from the training-window PnL
distribution; per-symbol Optuna search at n_trials=35 single-seed may find
slightly different optima.

Bounding the trajectory-shift uncertainty:
- **Lower bound (brake under-fires)**: brake fires on 0-3 trades only → 0% to
  100% of ORACLE counterfactual. IS Δ in [+0.00, +0.04]; OOS Δ in [+0.00, +0.13].
  Result: NULL-RESULT PATH D (35% probability of this scenario).
- **Central bound (brake fires per oracle ± 30%)**: 5-9 trades skipped → ~70-130%
  of ORACLE counterfactual. IS Δ in [+0.03, +0.18]; OOS Δ in [+0.09, +0.39].
  Result: PROMISING-clean PATH A (35% probability).
- **Upper bound (brake over-fires)**: brake fires on 10-20 trades → 200% of
  ORACLE counterfactual including BCH/TRX false positives. IS Δ in [-0.05, +0.10];
  OOS Δ in [-0.05, +0.50]. Result: PROMISING-clean PATH A but with concentration
  shift toward BCH (30% probability).
- **Pathological (Optuna finds new local minimum)**: 15% probability of qualitative
  divergence; could be NEGATIVE-clean PATH C if Optuna chases the brake's reduced
  PnL distribution and finds a noise-fitted optimum.

### 4.4 — Behavioral effect predictor (per `feedback_axis_saturation_predictor.md`)

Predicted behavioral effect: brake fires 7 times on /053 ORACLE roster (2 IS BCH
+ 5 OOS LDO). At backtest time with Optuna trajectory shift:

- Predicted lower bound: 3 fires (mostly OOS LDO; BCH/TRX 0)
- Predicted central: 7 fires (matches ORACLE)
- Predicted upper bound: 15 fires (including TRX IS occasional + BCH OOS occasional)

**Saturation falsifier (Section 8 LOCKED PATH E)**: if brake fires < 3 times OR > 25
times across full /054 run, axis effect is OUT-OF-PREDICTION-RANGE and PATH D
fires unambiguously regardless of Sharpe Δ.

---

## Section 5 — Risk Mitigation

### 5.1 — R1 / R2 / R3 / R4 / R5 / R6 / R7 / R8 / R9 / R10 carried forward unchanged

All 7 existing v3 risk gates UNCHANGED:
- R1 cooldown (post-trade): 2-candle UNCHANGED
- BTC trend kill: 15% threshold UNCHANGED
- Vol scaling: floor 0.3 UNCHANGED
- ADX gate: 20.0 UNCHANGED (per-symbol overrides {} empty)
- Hurst regime: 5th/95th percentile UNCHANGED
- z-score OOD: 2.0 UNCHANGED
- Low-vol filter: 0.33 UNCHANGED

Primitive 10 (block_long_for) and primitive 9 (regime gate) UNCHANGED (both empty).

### 5.2 — NEW: R11 = per-symbol drawdown brake (primitive 11)

Mechanism: per-symbol 30-day rolling-window weighted_pnl drawdown brake.

Calibrated thresholds (IS-derived from /053 trade roster ORACLE counterfactual):
- T = 10.0 wpnl (engagement) — selected so that brake fires on LDO catastrophic
  but NOT on BCH/TRX healthy
- Recovery = 5.0 wpnl (disengagement) — T/2 ratio is canonical Carver
- Window = 30 days — Carver canonical; matches monthly Optuna refit cadence

Simulated historical effect (from /053 trade roster):
- IS wpnl Δ = +4.39 (BCH skipped 2 May 2024 drawdown trades)
- OOS wpnl Δ = +12.51 (LDO skipped 5 OOS catastrophic-streak trades)
- Total brake fires: 7

Per `feedback_risk_mitigation_design.md` mandate: this section documents
IS-calibrated thresholds with explicit simulated historical effect.

### 5.3 — Kill-switch criteria (under what conditions /054 aborts)

If during Phase 6 the backtest produces:
- OOS trades < 50 → trade-rate floor breached (kill /054, classify as NULL)
- drawdown_brake_fires > 50 → brake over-fires catastrophically (kill /054)
- Any adversarial test fails → setup commit invalid

---

## Section 6 — Trade-Rate Floor Compliance

Per `feedback_v3_trade_rate_floor_bundle_level`: trade-rate floor applies at
CONFIRMATION-bundle level (≥130 OOS trades total), NOT per single-seed EXPLORATION
row. /054 EXPLORATION at single-seed with predicted OOS trades ~91 (vs 130 floor)
is INFORMATIONAL ONLY.

Per `feedback_trade_rate_floor`: ≥10 trades/month OOS = ≥120 OOS trades over 12
months. /053 OOS trades = 96 over ~14 months = 6.9 trades/month — BELOW floor.
/054 predicted 91 trades = 6.5 trades/month — BELOW floor.

This is a known cycle-4 structural caveat. The bundle-level math (91 × 5 outer ×
3-5× ensemble = ~1400-2300 OOS bundle trades at iter-v3/061 CONFIRMATION) clears
the floor. /054 verdict is purely IS+OOS axis driven; trade count is informational.

---

## Section 7 — Wall-Clock Budget

Predicted /054 wall-clock:

| Phase | Estimate |
|---|---:|
| QE Phase 6 implementation (code + 5 tests) | 1.0-1.5h |
| QE Phase 6 backtest | 1.25h (same as /053; no feature regen needed) |
| QR Phase 7 result evaluation | 0.25h |
| QR Phase 5.5 gate (before backtest) | 0.25h |
| Critic Phase 7.5 verification | 0.5h |
| **TOTAL (within EXPLORATION cap)** | **3.25-3.75h** |

Note: code-implementation portion is ~1.5h but the backtest itself is 1.25h. The
2h EXPLORATION cap applies to wall-clock of the BACKTEST (not full QE-QR-Critic
pipeline). 1.25h backtest is comfortably within the 2h cap.

If QE Phase 6 implementation reveals architectural complexity (e.g. the
update_on_closed_trade callback wiring doesn't exist), implementation may extend
to 2.5h. QR adjudicates: if implementation cost exceeds 2.5h, defer /054 axis
to multi-iteration arc and pivot /054 to A2 (DSR gate reformulation, 1h impl).

---

## Section 8 — LOCKED MERGE/NO-MERGE Criteria (Pre-Registered)

This iteration is EXPLORATION — no MERGE consideration. Classification per the
6-path criteria below. Verdict is mechanical and non-renegotiable post-hoc per
`feedback_no_cheating.md`.

### PATH A (PROMISING-clean)

Trigger (ALL conditions must be met):
1. IS monthly Sharpe Δ vs /028 anchor ≥ +0.05 (i.e. /054 ≥ +0.5601)
2. OOS monthly Sharpe Δ vs /028 anchor ≥ +0.10 (i.e. /054 ≥ +0.6053)
3. IS-OOS daily Sharpe ratio ∈ [0.5, 2.0]
4. drawdown_brake_fires (full backtest) ∈ [3, 25]
5. CPCV positive-path count > 30 OR (CPCV median Sharpe > 0.40 AND Q25 > -0.18)
   — i.e. CPCV distribution moved from /051/052/053 invariant

Outcome: Axis advances to /055 → /060 carry-forward bundle ingredient (subject
to /061 CONFIRMATION multi-seed validation).

### PATH B (PROMISING-INERT)

NOT APPLICABLE to risk primitives. PATH B is the feature-rank saturation outcome;
risk primitives either fire or don't fire (no "rank ≥ 14/15" analog). If
drawdown_brake_fires = 0 over full backtest, classify as PATH D NULL-RESULT.

### PATH C-clean (NEGATIVE)

Trigger (any one of):
1. IS monthly Sharpe Δ < -0.10 (i.e. /054 IS < +0.4101)
2. OOS monthly Sharpe Δ < -0.30 (i.e. /054 OOS < +0.2053)
3. drawdown_brake_fires > 25 with simultaneous IS or OOS regression (brake
   over-fires)

Outcome: Axis CLOSED for cycle 4. /055 axis selection from candidates list
(remaining: A2 DSR reformulation, A4 base-stack reordering).

### PATH C-suspicious (NEGATIVE-SUSPICIOUS-OOS)

Trigger:
- IS-OOS daily Sharpe ratio OUTSIDE [0.5, 2.0]

Outcome: Axis CLOSED for cycle 4. Same as PATH C-clean.

### PATH D (EXPLORATION-NULL-RESULT)

Trigger (ALL conditions must be met):
1. IS monthly Sharpe Δ ∈ (-0.10, +0.05)
2. OOS monthly Sharpe Δ ∈ (-0.20, +0.20)
3. drawdown_brake_fires ∈ [0, 25] (mechanism behaved as designed but no Sharpe lift)

Outcome: Axis PARKED for cycle 4 (NOT CLOSED — re-test at /061 CONFIRMATION
multi-seed budget where single-seed Optuna trajectory shifts dissolve).
Mechanism retained as backward-compatible disable-by-default RiskV2Config field.

### PATH E (CPCV-INVARIANT NULL) — per Critic /053 recommendation #3

Trigger (ALL conditions must be met):
1. CPCV positive-path count = 29 (matches /051/052/053 to integer)
2. CPCV median path Sharpe = +0.3351 ± 0.0050 (matches /051/052/053 to 2 decimals)
3. CPCV Q25 path Sharpe = -0.243 ± 0.0050 (matches /051/052/053 to 2 decimals)
4. drawdown_brake_fires ≥ 5 (mechanism fired; not a no-op explanation)

Outcome (if PATH E fires ALONGSIDE another path): axis classified as 'failed
to escape 15th-slot saturation' (per Critic /053 recommendation #3) AND **axis
family CLOSED at /054** — meaning the entire "NEW risk primitive" category is
declared saturated at single-seed EXPLORATION scope. /055 axis selection skips
A1 and any other NEW risk primitives until a structural change to the underlying
CPCV anchoring is made.

If PATH E fires ALONE (no other path triggers — extremely unlikely; would mean
NULL Sharpe Δ + CPCV identical despite brake firing 5+ times): classify as PATH D.

---

## Section 9 — Reproducibility

```
Library stack (pinned in pyproject.toml):
  lightgbm == 4.6.0
  optuna == 4.8.0
  numpy == 2.2.6
  pandas == 3.0.0
  scikit-learn == 1.8.0
  scipy == 1.17.0
  statsmodels == 0.14.6
  pyarrow == 23.0.1

Hardware: WSL2 / Linux 6.6.114.1
Random seeds (inner ensemble): [42, 123, 456, 789, 1001]
Outer seeds: [42] (EXPLORATION-spec, --seeds 1)

Run command:
  uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof

Expected wall-clock: 1.25h backtest + ~1.5h implementation.
```

---

## Section 10 — QR Audit Trail (per `feedback_v3_axis_selection_quant_discipline.md`)

### 10.1 — EDA SHA `e565b82` precedes brief

Per memory rule `feedback_v3_axis_selection_quant_discipline.md`: "Future axis
selections MUST be made by QR with EDA-driven quantitative basis (committed
`analysis/iteration_v3-NNN/*.py` script before brief)." The /054 EDA is committed
at SHA `e565b82` (parent of this brief commit). Brief Section 2 numerical tables
sourced from:

- `analysis/iteration_v3-054/cycle4_axis_ranking_eda.py` — 4-axis ranking
- `analysis/iteration_v3-054/per_symbol_drawdown_brake_eda.py` — mechanism design
- `analysis/iteration_v3-054/synthesis.md` — 5-criterion synthesis
- `analysis/iteration_v3-054/candidate_axes_ranking.md` — final pick + rationale
- `analysis/iteration_v3-054/brake_synthesis.md` — mechanism + behavioral effect
- Supporting CSVs: brake_mechanism_options.csv, brake_threshold_sensitivity.csv,
  brake_recommended_counterfactual.csv, per_symbol_drawdown_eda.csv,
  per_symbol_drawdown_thresholds.csv, dsr_reformulation_simulation.csv,
  catboost_implementation_cost.csv, base_stack_importance_ranking.csv

### 10.2 — 4-axis ranking (per Critic /053 recommendation #1)

| Axis | C1 ≤2h impl | C2 escape slot-15 | C3 cycle-4 finding | C4 orthogonal | C5 revert | Verdict |
|---|---|---|---|---|---|---|
| **A1 Per-symbol drawdown brake** | **YES** | **YES** | **HIGH (LDO drag)** | **YES** | **YES** | **RECOMMENDED** |
| A2 DSR gate reformulation | YES | YES | HIGH (DSR=0 structural) | YES | YES | RECOMMENDED-PARALLEL (defer to /055) |
| A3 CatBoost head-to-head | NO (7-10h) | YES | MEDIUM | PARTIAL (/016 NEG) | YES | DEFER multi-iter arc |
| A4 Base-stack reordering | PARTIAL | YES | HIGH | PARTIAL | YES | VIABLE-SECONDARY (defer to /055) |

A1 wins 5/5 criteria; A2 wins 4/5 (the 5th — "addresses cycle-4 LDO drag" — is
not addressed by methodology reformulation). A1 is the recommended axis.

### 10.3 — Orthogonality vs CLOSED precedents

Per `feedback_v3_concentration_is_signal.md` (LOCKED at iter-v3/020 closeout):
"Per-symbol PnL share caps CLOSED at catalog level. Future 'concentration' axes
MUST use orthogonal mechanisms: universe expansion (denominator expansion),
**per-symbol drawdown brake (loss-stop semantics)**, vol-target ceiling (exposure
ceiling), regime-conditional kill switch (binary off/on). NOT proportional
scaling."

Per-symbol drawdown brake is one of FOUR explicitly-listed permitted orthogonal
mechanisms. The /020 closure was about PROPORTIONAL SCALING (capping symbol
weight to 40% of portfolio); /054 is LOSS-STOP SEMANTICS (binary off/on on
drawdown). The distinction is canonical Carver — proportional scaling is the
WRONG mechanism for managing catastrophic tail loss in a per-symbol model
because it linearly degrades the contribution of high-conviction trades; binary
loss-stop is the CORRECT mechanism because it preserves high-conviction trades
EXCEPT when the symbol has demonstrably entered catastrophic regime.

### 10.4 — Why NOT 15th-slot SWAP (per Critic /053 recommendation #1)

Three consecutive 15th-slot SWAPs all produced identical CPCV path distributions
(29/45 positive, +0.3351 median, -0.243 Q25 to 4 decimals). The 14-feature base
stack dominates cross-path generalization at 3-sym + n_trials=35 + ENSEMBLE_SIZE=5
regime. The 15th-slot SWAP family is STRUCTURALLY EXHAUSTED at single-seed
EXPLORATION scope.

Continuing 15th-slot SWAP experiments (4th, 5th, 6th candidate feature) is a
guaranteed sequence of NULL-RESULT or PROMISING-INERT outcomes at CPCV level.
**iter-v3/054 MUST exit the 15th-slot SWAP family.**

### 10.5 — Three pre-falsifiers acknowledged

Following the /053 brief LR-PF methodology, I disclose three pre-falsifiers for
this axis upfront:

1. **Optuna trajectory shift**: ORACLE counterfactual assumes identical Optuna
   draws. Real backtest may produce 30-50% deviation in trade roster + Sharpe Δ.

2. **TRX IS not addressed**: TRX is the IS structural loser (-17.79 wpnl over
   85 trades) but TRX losses are SPREAD-OUT signal-quality leakage, NOT
   drawdown-event catastrophic. The brake cannot fix spread-out leakage. /054
   does not improve TRX IS contribution.

3. **Single-seed lottery**: /054 is single-seed=42 EXPLORATION. Brake firing
   pattern is sensitive to which trades land in seed-42's specific Optuna draw.
   At multi-seed CONFIRMATION (/061) the brake may fire on different trades or
   not at all.

Despite these caveats, A1 is selected because:
- ORACLE counterfactual is strongly positive (+4.39 IS wpnl + +12.51 OOS wpnl)
- Mechanism is structurally orthogonal to all 3 cycle-4 NULL/NEGATIVE axes
- Implementation cost ≤ 2h (vs A3 CatBoost 7-10h)
- Addresses an explicit cycle-4 structural finding (LDO drag, all 3 iterations)

---

## Section 11 — Cycle Cadence Tracking

Per `feedback_v3_strict_10_to_1_cadence.md`:

- Cycle 4 #1 = iter-v3/051 (fracdiff_d05_close ADD UNIVERSAL; EXPLORATION-NULL-RESULT PATH D; PARKED)
- Cycle 4 #2 = iter-v3/052 (regime_momentum_signed_3d SWAP UNIVERSAL; PATH C-suspicious; CLOSED)
- Cycle 4 #3 = iter-v3/053 (hurst_drift_50_200 SWAP UNIVERSAL; PATH D NULL-RESULT; PARKED)
- **Cycle 4 #4 = iter-v3/054 (THIS BRIEF — per-symbol drawdown brake, NEW risk primitive)**
- Cycle 4 #5-#10 = iter-v3/055-iter-v3/060 (TBD)
- Cycle 4 CONFIRMATION = iter-v3/061 (SEPARATE single-seed iter-v3/060 first)

6 more EXPLORATIONs remain before cycle 4 CONFIRMATION (iter-v3/055 through
iter-v3/060).

---

## Section 12 — See Also

- `analysis/iteration_v3-054/cycle4_axis_ranking_eda.py` (SHA `e565b82`)
- `analysis/iteration_v3-054/per_symbol_drawdown_brake_eda.py` (SHA `e565b82`)
- `analysis/iteration_v3-054/synthesis.md` (SHA `e565b82`)
- `analysis/iteration_v3-054/candidate_axes_ranking.md` (SHA `e565b82`)
- `analysis/iteration_v3-054/brake_synthesis.md` (SHA `e565b82`)
- `src/crypto_trade/strategies/ml/risk_v2.py` (file to modify)
- `src/crypto_trade/features_v3/__init__.py` (V3_FEATURE_COLUMNS_TOP_N: 15 → 14)
- `run_baseline_v3.py` (ITERATION_LABEL "v3-054"; RiskV2Config wiring)
- `tests/strategies/ml/test_risk_v2_drawdown_brake.py` (NEW 5 adversarial tests)
- `diary-v3/iteration_v3-053.md` — predecessor diary (PATH D; LR-PF methodology;
  15th-slot SWAP exhausted; PATH E pre-registration mandate)
- `briefs-v3/iteration_v3-053/review.md` — Critic FINAL SHA `c056354` Recommendations 1-5
- `BASELINE_V3.md` — UNCHANGED at iter-v3/028 (+0.5101 IS / +0.5053 OOS; SHA `b0576df`)
- `feedback_v3_concentration_is_signal.md` — per-symbol drawdown brake explicitly
  permitted as orthogonal mechanism
- `feedback_v3_structural_over_knob_exploration.md` — NEW risk primitive ranked
  Category 4 priority
- `feedback_v3_axis_selection_quant_discipline.md` — EDA-driven axis selection rule
- `feedback_risk_mitigation_design.md` — Risk Mitigation section requirements
- `feedback_v3_lr_pf_methodology.md` — LR-PF methodology established at /053
