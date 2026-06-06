# LightGBM Master Advisor — iter-v1/074 — Phase 4.5 (Pre-Design)

## Context Read
- Track: v1
- Baseline (this iter's anchor): /064 ETH SPECIALIST — IS Sharpe **+0.2383** / OOS **+0.5171** / 198 IS trades / 81 OOS trades / 48-col `V1_FEATURE_COLUMNS_PRUNED` / atr_tp=2.9 / atr_sl=1.45 / R1=OFF R2=OFF R3=ON-SHARED cutoff=0.70 / 50 seeds × 30 trials × ENSEMBLE_SIZE=1 / max_depth=5 fixed / num_leaves=31 fixed / mean-of-signed-weights aggregator. **/073 is NOT the anchor** — /073 was IMPROVEMENT-FAIL (IS Δ −0.25 vs /064) and was discarded; /064 retains the BUNDLE-001 slot per the closeout.
- Prior iter /073 outcome: ETH-IMPROVED-V2 axis = feature-subset reduction (48 → 25 ETH-top features). IS Δ **−0.25** vs /064 anchor, OOS Δ +0.05. SPECIALIST-NEGATIVE-IMPROVEMENT-FAIL. Mechanism: feature-stack pruning reduced cross-seed HP-trajectory diversity (dispersion 38.61 → 33.44), collapsing the ensemble to a tighter-but-lower-quality consensus. Methodology-specific finding: at SPECIALIST 50-seed×30-trial budget, INERT tail features function as **dimensionality reservoirs** for cross-seed Optuna basin diversity — **structurally inverse** to the v3 INERT-feature finding. AXIS CLOSED: feature-stack pruning at SPECIALIST mode.
- QR's tentative axis (from adversarial 15-pool synthesis at Phase 4): **AXIS-R — Mid-Bull SHORT VETO rule layer**. Skip direction=−1 entries when `ret_270b ∈ [0.20, 0.50]`. Pre-registered band edges, post-prediction filter, no feature/model/label/risk-wrapper change.

## Recommended Axis: AXIS-R — Mid-Bull SHORT VETO rule layer (CONFIRMED)

This is the dominant pick across all four ranking axes (IS-evidence, mechanism strength, implementation tractability, single-bit attribution). Confidence **HIGH**.

### What

Add a single **post-prediction veto** in the runner immediately AFTER the aggregator emits `Signal(direction, weight)` and BEFORE the R3 OOD gate and any risk-wrapper layer:

```python
# AXIS-R: Mid-Bull SHORT VETO (post-prediction rule layer; pre-registered band)
# Computed from the same 270-bar trailing close window the runner already loads.
# ret_270b = (close[t] / close[t - 270]) - 1.0  on 8h candles → 90-day equivalent.
if signal.direction == -1:
    ret_270b = (close_window[-1] / close_window[-271]) - 1.0
    if 0.20 <= ret_270b <= 0.50:
        signal = Signal(direction=0, weight=0)  # VETO short; long/flat untouched
```

Wiring specifics:
- New runner: `run_iteration_074.py`, clone of `run_iteration_064.py`, identical signature down to `FEATURES_BASE_HASH_48COL` and ITERATION_LABEL=`v1-074`.
- New dispatch branch `elif iteration_label == "v1-074"` in `run_baseline_v1.py`, identical to the `v1-064` branch except for one strategy-construction kwarg: `enable_mid_bull_short_veto=True, mid_bull_short_veto_lo=0.20, mid_bull_short_veto_hi=0.50, mid_bull_short_veto_lookback=270`.
- Implementation lives in `LightGbmStrategy.get_signal` (or a thin post-aggregator filter at the call-site in `backtest.py`): after the 50-seed mean-of-signed-weights produces `Signal(direction, weight)`, evaluate the veto on the same close-series the strategy already buffers. Trailing 270 8h bars = 90 calendar days exactly; the buffer is already maintained by R3's Mahalanobis history window.
- Engine parity: the same conditional is wired into `engine.py:_tick` after the LightGBM strategy emits a signal; trailing 270 closes are available from the `klines` table query already used for catch-up. **Zero divergence between backtest and live.**

### Why (EDA-grounded, prescriptive — not descriptive)

The QR's adversarial-synthesis dossier names AXIS-R as **the only proposal in the 15-pool with a quantified effect simulated on the committed /064 IS trade roster**: 32 of 198 trades vetoed (16.2%), +9.73% PnL recovered, +0.186 per-trade Sharpe lift (0.686 → 0.871). Twelve of those 32 carry −30.81% of the 2024-bull short-bleed cohort that /073 §2.6 explicitly identified as the unfixed load-bearing flaw of the /064 architecture. **No other axis in the pool cites a pre-backtest simulated effect on the actual /064 roster** — every other proposal is descriptive EDA.

The mechanism is the missing-regime-feature gap that the model **literally cannot learn** at depth 5:
- The 48-col stack carries `regime_momentum_signed_5d` (5-day) and `eth_vs_btc_ret_ratio_30` (30-day) but **no 90-day structural-regime primitive**.
- The /064 short-bleed cohort 2024-Q1/Q2 (ret_270b ∈ [0.20, 0.50]) is bear-transition / mid-bull-correction territory: short signals fire at WR 16.7% (vs structural-bull shorts at ret_270b > 0.50 which fire at WR 41% and bear-continuation shorts at ret_270b < 0.20 which fire at WR 49%). The regime band is **non-monotone in ret_270b** — a depth-5 tree cannot disambiguate three direction-asymmetric WR bands across a single feature axis when that axis isn't even in the stack.
- Injecting the disambiguation at the **post-prediction inference layer** preserves the IS/OOS training distribution exactly (no label change, no feature change, no model retrain) — the veto is a rule-form patch on a known mechanism gap, not a new edge claim.

This is the v1-analogue of v3's `/116 no_confirm` PROMISING-MECHANICAL pattern (RULE-layer primitive on inference output; structurally accretive without compounding signal claims). Per `feedback_promising_mechanical_subtype.md`, the verdict framework correctly classifies this as a **RULE-form accretive component decision**, not a NEW edge ingredient.

### Pre-registered band edges (anti-tuning hedge — load-bearing)

Per `feedback_v1_basin_lottery_vigilance.md` and the no-cheating mandate, the [0.20, 0.50] band edges MUST be hardwired into the brief Section 4 BEFORE the runner is executed. The brief should state explicitly:

> "Mid-Bull SHORT VETO band: ret_270b ∈ [0.20, 0.50]. Lookback: 270 8h bars = 90 calendar days. Edges pre-registered 2026-06-06 from the /064 IS trade roster. Band edges WILL NOT be re-tuned post-hoc. If observed per-trade Sharpe lift < +0.10, the axis is FALSIFIED — band re-fitting is prohibited."

A secondary falsifier: **no single calendar month may carry > 40% of the realized lift**. This guards against regime-fit / basin-lottery — if 2024-Q1 alone produces 90% of the lift and 2025+ months produce flat or negative, the axis is a regime-coincident artifact not a structural rule.

### Expected effect

Predicted IS Sharpe lift **+0.13 to +0.20** vs /064 anchor (modal **+0.13**, mean +0.15, 90% band [+0.05, +0.25]). This is BELOW the simulator's raw +0.186 per-trade Sharpe lift because:
- (a) The simulator computes per-trade Sharpe on the committed /064 trade roster, holding model identity fixed. The runner re-trains 50 seeds × 30 trials per month — the basin-lottery surface remains. Expect **0.6× to 0.8× simulator scale-down** at single-seed=42 EXPLORATION budget.
- (b) The mean-of-signed-weights aggregator is **non-linear in the veto**: vetoing a Signal(direction=−1, weight=W) at the post-aggregator stage is equivalent to forcing the mean of 50 signed weights to be flipped flat when the aggregated direction is short and ret_270b ∈ band. This is structurally different from per-seed veto (which would re-bias the aggregator distribution). Aggregator-level veto preserves the cross-seed dispersion measurement (F-AXIS #2) — recommended for `/074`. Do NOT veto per-seed.
- (c) OOS expected directionally positive but smaller in magnitude (+0.05 to +0.15) — the OOS window (2025-03-24 onward) is a structural bull (ret_270b > 0.50 frequently), which means few OOS trades fall in the veto band. The veto's OOS impact is **trade-count-bounded** at perhaps 3-8 vetoes of the 81 OOS trades.

### Trade-count floor risk

Vetoing 32 IS trades (16.2%) drops the /064 IS trade count 198 → ~166. This is well above the SPECIALIST 50-trade floor per `feedback_v1_trade_rate_floor_50_per_specialist.md`. **No floor risk at IS**. OOS: 81 baseline − ~5 vetoes = ~76, still well above 50. **No floor risk at OOS**. Safe.

### Risk

- **Pre-registered band rigor (HIGH)**: this is the single most important discipline. If the QR re-fits the band post-hoc to find a stronger lift, the verdict collapses. Brief Section 11 must include an anti-tuning assertion: "ret_270b band edges 0.20 / 0.50 frozen at brief authoring. No post-backtest tuning."
- **Single-bit discipline (HIGH)**: the brief MUST hardwire ATR=2.9/1.45, R-config=(R1=OFF, R2=OFF, R3=ON-SHARED cutoff=0.70), 50 seeds × 30 trials, ENSEMBLE_SIZE=1, max_depth=5, num_leaves=31, n_estimators ≤ 500, n_startup_trials=10, V1_FEATURE_COLUMNS_PRUNED (48 cols, UNCHANGED), mean-of-signed-weights aggregator — **exactly identical to /064**. Only the post-aggregator veto changes. If the brief touches a second axis (e.g., "while we're here, let's try atr_tp=2.8"), the iteration becomes a 2-bit cross-axis confound and the verdict is uninterpretable. /073's failure does NOT license multi-axis compensation.
- **Engine parity (MEDIUM)**: the veto MUST be wired into `engine.py:_tick` at the same call-site as the strategy's signal emission, with the same trailing-270-close computation. Backtest-live parity is HARD per `feedback_v1_backtest_live_parity_hard.md` (Critic Check 15). The QE Phase 5.5 gate should verify this explicitly.
- **Mid-bull regime persistence in OOS (MEDIUM-LOW)**: if 2026+ OOS extends into a new bull/bear transition, the veto may begin firing again. This is expected behavior — the rule is a **regime-state-dependent filter**, not a time-window patch. The verdict at /074 is single-window OOS; cycle-7 multi-seed CONFIRMATION will re-validate at multi-seed.
- **No basin-lottery damage**: the veto is post-aggregator and deterministic given (ret_270b, signal.direction). It does NOT modify the 50-seed inner ensemble distribution, so cross-seed Optuna trajectories remain exactly as in /064. **Mechanism-orthogonal to basin-lottery.**

## Why NOT Critic-A (asymmetric-cutoff HP)

Critic-A proposes per-direction prediction-threshold asymmetry as the mechanism (long/short thresholds split). This is mechanism-adjacent to AXIS-R but at a different layer:
- (a) Critic-A requires a new Optuna search dimension → expands the HP cube at fixed n_trials=30 → INCREASES single-seed basin-lottery exposure.
- (b) Critic-A cannot pre-register an effect estimate on the /064 trade roster — the new HP dimension makes the trade roster non-recoverable without re-running.
- (c) Critic-A and AXIS-R interact: if AXIS-R lands MARGINAL, Critic-A is the natural strike-2 fallback for ETH-IMPROVED-V4. SECONDARY RECOMMENDATION per the QR's synthesis: keep Critic-A as the next-iter axis if /074 lift < +0.10.

## Why NOT QR-F / LM-A1/A2/A5 (new feature axes)

The /073 closeout's load-bearing finding is that the 48-col stack is **mechanically held** at SPECIALIST mode (cross-seed dispersion-reservoir mechanism). Adding OR removing features at 50-seed × 30-trial budget perturbs the cross-seed HP-trajectory diversity in unpredictable directions. Until the methodology graduates to multi-seed CONFIRMATION, feature-axis EXPLORATIONs at SPECIALIST mode are **basin-lottery surfaces** per the /073 evidence. Pivot to a rule-layer axis that doesn't touch the feature stack.

## Why NOT LM-A3 / Critic-C (label changes) or Critic-D (risk-wrapper changes)

Label changes require re-training (changes IS by construction) → not single-bit. Risk-wrapper changes interact with the aggregator non-linearly → multi-bit confound. AXIS-R is the cleanest single-bit deviation from /064 — preserves IS training distribution, preserves cross-seed ensemble, preserves R3 OOD calibration.

## Why NOT QR-U (universe expansion) or QR-L (meta-model)

Universe expansion violates `feedback_v1_bundle_no_coin_overlap.md` for ETH specialist territory. Meta-model adds a model layer (multi-bit). Both out of scope for a 1-bit ETH-IMPROVED iteration.

## Saturation Risks to Flag

1. **ETH-IMPROVED is now 3-of-N**: /064 PROMISING → /073 IMPROVEMENT-FAIL → /074 = third attempt. The pattern across /072 (BTC R1=ON FAIL) and /073 (ETH feature subset FAIL) is that **BUNDLE-001 specialists are HARD to improve incrementally** at SPECIALIST mode. The structural reason is the basin-lottery + dispersion-reservoir mechanisms — both are SPECIALIST-mode artifacts that dissolve at multi-seed CONFIRMATION. If /074 lands MARGINAL/NEGATIVE, the next cycle should pivot ETH-IMPROVED to the next-cycle CONFIRMATION envelope (let the multi-seed test resolve whether /064 itself has a 0.10-0.20 lift surface) rather than continuing single-seed knob-tuning. Flag for QR brief authoring.

2. **AXIS-R generalizes**: if AXIS-R succeeds on ETH, the same rule plausibly applies to BTC's /065 short cohort (BTC has analogous mid-bull short-bleed dynamics). DOT is less clear (DOT's structural regime is more chop-dominant). **Do NOT pre-apply AXIS-R to BTC/DOT at /074** — single-cohort validation first. If /074 PROMISING, the next cycle BTC-IMPROVED-V2 brief can pre-register AXIS-R as the primary axis.

3. **Engine parity surface area**: AXIS-R adds a third inference-layer rule to engine.py (after R3 OOD and R5 vol-target). Each rule adds parity verification surface. The QE's Phase 5.5 gate must explicitly enumerate the inference-layer rule order and verify backtest-live alignment at each. Future iterations should resist accumulating rule-layer primitives without retiring earlier ones.

## What I Did NOT Recommend, and Why

I considered but rejected:
- **(a) Wider band [0.10, 0.60]**: the QR's simulator at [0.20, 0.50] produces +0.186 per-trade lift. Widening the band captures more vetoes but the marginal vetoes outside [0.20, 0.50] are mostly profitable shorts (the WR profile is non-monotone — ret_270b > 0.50 structural-bull shorts WR 41% and ret_270b < 0.20 bear-continuation shorts WR 49%). Widening the band degrades the realized lift. The pre-registered [0.20, 0.50] is at the empirical optimum from the /064 trade roster.
- **(b) Narrower band [0.25, 0.45]**: would over-fit to the /064 IS roster and reduce the trade-count change (32 → ~22 vetoes). The anti-tuning rigor cuts harder against narrower bands than wider — narrow bands have higher post-hoc overfitting risk.
- **(c) Per-month band recalibration**: out of scope (multi-bit) and would defeat the rule-layer simplicity.
- **(d) Long-side veto in opposite regime**: the QR's EDA evidence focuses on short bleed in mid-bull. No equivalent evidence for long bleed in mid-bear. Don't speculate symmetry without IS evidence.

## Closing Note

**HIGH confidence /074 will improve /064 IS Sharpe**, conditional on the pre-registered band edges holding through the brief authoring without re-fitting. The single thing the QR should NOT ignore is the **anti-tuning rigor on the band edges** — the rule's verdict integrity is entirely staked on [0.20, 0.50] being frozen at brief authoring and the falsifier (per-trade Sharpe lift < +0.10 OR any single month > 40% of lift) being hardwired into Section 4. If the runner produces +0.05 IS lift and the QR retrofits [0.18, 0.52] to extract +0.13, the result is methodology-falsified — not validated.

Predicted IS Sharpe: **+0.37** (= /064 anchor +0.2383 + predicted Δ +0.13). 60% modal band: **[+0.29, +0.44]**. 90% band: [+0.19, +0.49]. F-AXIS #1 verdict: SPECIALIST-IMPROVEMENT-PROMISING if IS Δ ≥ +0.10 AND OOS Δ ≥ −0.10 AND no single-month carries > 40% of IS lift.
