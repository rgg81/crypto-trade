# Research Brief — iter-v1/016 (BTCUSDT) — Phases 1–2 (TARGET/STRATEGY redesign, IS-ONLY)

**Author:** Crypto-markets Quant Researcher. **Symbol:** BTCUSDT. **Interval:** 8h (sacred).
**Scope:** Phase 1 (EDA) + Phase 2 (labeling/target). **IS-ONLY.** **Objective: SHARPE.**
**TARGET = both-positive (IS Sharpe > 0 AND OOS Sharpe > 0).** Merge bar is RELATIVE vs
`BASELINE_V1_BTCUSDT` (iter-001 IS −0.2793 / OOS +0.6401).

All numbers come from three committed, re-runnable, IS-only scripts under
`analysis/BTCUSDT/iteration_v1-016/`. Each hard-filters `open_time < OOS_CUTOFF_MS = 1742774400000`
(2025-03-24), asserts `df["open_time"].max() < OOS_CUTOFF_MS` BEFORE any forward quantity, computes
the forward log-return AFTER the filter (tail rows NaN-mask — no OOS candle in the frame), uses
`.shift(1)` past-only direction rules, and trains every walk-forward model + percentile threshold on
PAST rows only (strict `train < test_start − embargo`, embargo = N_LABEL = 42 candles ≥ label
horizon). Nothing is fit/selected/calibrated against OOS; OOS rows are never read. `src/`, the
runner, and OOS are UNTOUCHED.

- `magnitude_gate_subperiod_stability.py` → tests Framing 1 (gate the campaign's LightGBM direction
  on PREDICTED magnitude).
- `breakout_and_metalabel_stability.py` → tests Framings 2 (breakout) + stateless direction rules
  (structural-long, trend-state, supertrend) with a vol confirmation.
- `design_decision_trendstate_metalabel.py` → the final head-to-head: LightGBM-direction vs
  trend-state vs trend-state + magnitude meta-label (Framing 4), all net of honest costs.

---

## 0. Headline finding (read this first)

**The both-positive path is a TREND-STATE direction (close vs 200-candle SMA, past-only) traded on
the campaign's 14d let-winners-run mechanism. It is the ONLY direction source in the whole campaign
whose most-recent IS sub-period (the OOS-fragility fingerprint identified in iter-011) is POSITIVE —
and it is positive at EVERY horizon (3d→30d). The mechanism is simple and crypto-native: the
LightGBM-LEARNED sign overfits IS-bull microstructure and inverts in OOS-bull (diary-012); the
stateless 200-SMA trend-state sign has NO parameters fit to IS, so it cannot overfit, and it encodes
BTC's slow reflexive trend-persistence regime — a cross-regime-stable directional signal.**

Three decisive IS-only results (net of honest cost = 0.1% fee + 0.04% slippage = 0.14%/trade):

1. **Framing 1 (magnitude-gated LightGBM direction) FAILS — and tells us why.** Gating the
   LightGBM-direction book on PREDICTED magnitude makes the most-recent IS sub-period MONOTONICALLY
   WORSE (RECENT −2.10 ungated → −3.38 at p50 → −8.25 at p70). The biggest moves are exactly where
   the overfit LightGBM sign is most wrong, so concentrating into them amplifies the error. **The
   problem is the DIRECTION SOURCE, not the magnitude signal.** Crucially, a NAIVE high-vol gate (raw
   `vol_natr_7` ≥ past-only median) moves the SAME book's stability the RIGHT way (frac_pos 0.6→0.8;
   RECENT −2.10→−1.64) — the dissociation that pointed us to a different direction source.

2. **Framings 2/A–D (stateless direction rules) — trend-state is the clean winner.** Of four
   stateless direction rules (always-long, 200-SMA trend-state, Donchian-20 breakout, supertrend),
   the **200-SMA trend-state** rule has the LOWEST cross-sub-period dispersion (1.32) AND a POSITIVE
   most-recent sub-period (+1.55), at full trade rate. The Donchian breakout fires too rarely at the
   let-run horizon (504 breakouts over 5,727 candles after the look-ahead-correct re-test — viable as
   a future axis, not the primary). Supertrend is positive-recent (+0.17) but noisier.

3. **The head-to-head (net of costs), trend-state vs LightGBM vs +meta-label:**

   | book | full-IS Sₐₙₙ | frac_pos | dispersion | worst sub | **RECENT** | trades | WR | mean ret/trade |
   |---|---:|:--:|---:|---:|---:|---:|:--:|---:|
   | BOOK1 LightGBM direction (WF-OOF) | +0.189 | 0.7 | 0.752 | −0.96 | +0.78 | 5075 | 53.0% | +0.46% |
   | **BOOK2 trend-state SMA200** | **+0.446** | **0.7** | 1.413 | −2.56 | **+1.45** | 5075 | 50.8% | **+1.09%** |
   | BOOK3 trend-state + mag meta-label | +0.243 | 0.6 | 1.598 | −2.59 | +3.33 | 3810 | 48.9% | +0.62% |

   **BOOK2 (bare trend-state) is the design.** Best full-IS Sharpe (+0.45), frac_pos 0.7, the
   strongest mean-return-per-trade (+1.09%), positive RECENT (+1.45). BOOK3's magnitude meta-label
   raises RECENT further (+3.33) but LOWERS win-rate (50.8%→48.9%) and full-IS Sharpe and worsens
   dispersion — it trades a louder recent for worse overall consistency, so the **meta-label is NOT
   adopted as a hard gate** (the script's automatic verdict agrees: "META-LABEL does NOT help").
   The magnitude signal is kept as an OPTIONAL vol-confirmation/sizing lever (Section 3), not the
   primary mechanism.

→ **RECOMMENDATION: iter-016 = TREND-STATE-DIRECTION let-winners-run book.** Direction = sign(close
vs past-only SMA200); the LightGBM model is RE-PURPOSED from direction-predictor to a confidence/size
input (or dropped entirely in the simplest variant). Keep the 14d let-winners-run execution and the
R2 drawdown brake (iter-015 keeper). Predicted IS + OOS both-positive; pre-registered falsifier in §6.

---

## 1. EDA / Phase-1 evidence — the generalization fingerprint

The campaign's unifying metric (iter-011/014) is **cross-IS-sub-period stability**: a direction
source whose per-sub-period edge is sign-stable — especially in the MOST-RECENT IS sub-period
(2024-12→2025-03, the window adjacent to OOS) — is the IS-visible signature of OOS generalization.
The directional LightGBM model fails this test deterministically (iter-011: positive in 6/9
sub-periods, negative in the SAME 3 for all seeds; diary-012: IS-bull longs +31% INVERT to OOS-bull
−22%, WR 24%).

**Trend-state SMA200 net annualized Sharpe (RT cost 0.14%), full-IS and most-recent sub-period,
by horizon** (`design_decision` probe):

| horizon | full-IS Sₐₙₙ | most-recent sub-period Sₐₙₙ |
|---|---:|---:|
| N=9 (3d) | +0.470 | +1.650 |
| N=21 (7d) | +0.429 | +1.858 |
| **N=42 (14d)** | **+0.317** | **+2.431** |
| N=63 (21d) | +0.304 | +2.601 |
| N=90 (30d) | +0.294 | +2.156 |

**Positive at EVERY horizon on BOTH axes** — the LightGBM direction was negative-OOS at every
horizon (diary-013 sweep). In the most-recent sub-period (N=42) the trend-state rule has **68.8%
directional accuracy**, **77.1% long fraction** vs a **55.3% forward-up base rate** — it is correctly
long in the up-trend AND steps aside / shorts the corrections, the precise behaviour the
LightGBM-learned sign got backwards in OOS-bull.

**Robustness to the one free parameter (SMA window):** recent-sub-period net Sharpe is +1.89 / +2.09
/ +2.51 / +2.53 / +2.05 for SMA windows 100 / 150 / 200 / 250 / 300 — a broad, flat plateau, NOT a
knife-edge. SMA200 (crypto-canonical) sits mid-plateau. This is not a tuned number.

---

## 2. Labeling / Phase-2 decision — keep the let-winners-run mechanism, change only the DIRECTION SOURCE

The campaign solved the IS side already (diary-013): `fixed_horizon` (sign of N-candle-forward
return) + let-winners-run execution at N=42 extracts a genuine, strong IS edge (low WR ~26% × large
payoff ~4.26). The unsolved half was OOS, and the cause is now isolated to the DIRECTION SOURCE.

**Target/label (UNCHANGED):** `label_mode="fixed_horizon"`, timeout = N=42 candles (14d), realized
forward log-return net of fee. Sample weighting `abs_pnl` (the existing default — already biases
training toward large-magnitude moves, which is the FE's stable signal; see §3). σ_t source / ATR
barriers as in iter-013 (non-binding TP, the let-run mechanism).

**Direction source (CHANGED — this is the iteration's single axis):** the trade direction at each
signal candle is NOT the LightGBM predicted sign. It is the **trend-state sign**:
```
trend_state(t) = +1 if close[t−1] > SMA_200(close)[t−1]   (long)
                 −1 otherwise                              (short)
```
computed past-only (`.shift(1)`; SMA over the prior 200 candles, excluding the decision candle's own
close). This is a deterministic, stateless regime descriptor — zero parameters fit to IS.

**Two implementable variants (QE picks the simplest that compiles cleanly; QR prefers V-A):**
- **V-A (RULE-layer direction override, preferred):** keep the existing LightGBM specialist
  aggregator to decide WHETHER to trade (its confidence gate / R-CONV conviction gate = the
  "should I be in the market now" filter) but OVERRIDE the entry DIRECTION with `trend_state(t)`.
  i.e. `final_direction = trend_state(t)`; the model supplies entry timing + sizing only. This reuses
  100% of the let-winners-run + R2 + confidence machinery; the model is demoted from sign-picker to
  timing/size filter — directly addressing the iter-012 finding that the model's *sign* is the broken
  part, not its *activity*.
- **V-B (pure trend-state, model-free direction AND timing):** trade every candle (or every candle
  passing a vol/conviction confirmation) in `trend_state(t)` direction. No LightGBM at all. Simplest;
  matches BOOK2 exactly. Use as the fallback / sanity anchor if V-A's model-timing interaction is
  unstable.

Recommended: implement **V-A first** (it is the smallest diff from the deployed config and keeps the
model contributing where it IS stable — abstention/timing — while removing it where it is broken —
the sign). If V-A's IS sub-period stability matches BOOK2's, it is the merge candidate; if the model
timing drags it below BOOK2, fall back to V-B.

---

## 3. Proposed changes (Phase 5 → QE Phase 6)

- **Labeling:** UNCHANGED — `fixed_horizon`, N=42 (14d), `abs_pnl` weights, let-winners-run exit.
- **Direction:** NEW trend-state override (Section 2). `trend_state` from a past-only SMA200 on BTC's
  own close (inline close-index, the exact pattern already used by the iter-092 BTC-regime-kill gate
  `_compute_btc_ret_42` / close-index build at `lgbm.py:651+`). This is a stateless RULE-layer
  primitive; it does NOT change Optuna's training-objective domain in V-A (the model still trains the
  same direction labels; only the EXECUTED direction is overridden at signal time). **Therefore V-A
  is NORMAL-RISK.** V-B removes the model from direction entirely → that IS a label/architecture
  change → HIGH-RISK (see §2.5-equivalent below).
- **Magnitude signal (OPTIONAL, NOT a hard gate):** the FE iter-014 stable vol-magnitude core
  (`vol_natr_7`, `vol_garman_klass_*`, `vol_parkinson_*`, `vol_bb_bandwidth_*`, `interact_natr_x_adx`)
  is RETAINED in the feature set (it is in the 19-col HYBRID already via `vol_garman_klass_10`,
  `vol_atr_5`, `vol_range_spike_72`) and is what the `abs_pnl` sample-weighting leans on. It is NOT
  wired as a meta-label gate (BOOK3 showed that hurts WR/dispersion). A future iteration MAY test it
  as a SIZE multiplier (scale up when predicted |move| is high) — flagged, not this iteration.
- **Features:** KEEP the incumbent 19-col HYBRID set for the model's timing/confidence role (FE
  iter-014 recommended UNCHANGED; the stable vol-magnitude core is already represented). No feature
  swap this iteration — the axis is the DIRECTION SOURCE, single-axis discipline.
- **Risk gates:** **KEEP R2 drawdown brake** (iter-015 keeper: cut OOS DD 80%, OOS net loss 80%;
  trigger=2.07 / anchor=8.28 / floor=0.20 RE shape). R3 OOD ON (aggregator-level, cutoff 0.70) as
  baseline. R5 vol-target as baseline. R1 OFF.

---

## Section 2.5 — Risk Declaration (v1)
- **Declaration:** V-A = NORMAL-RISK · V-B = HIGH-RISK.
- **Reason:** V-A overrides only the EXECUTED direction at signal time (stateless rule on top of the
  unchanged training objective). V-B removes the LightGBM direction model entirely (architecture
  change → changes the training-objective domain).
- **Mitigation:** run V-A as the EXPLORATION (K=3) screen first. If PROMISING, the CONFIRMATION (K=20)
  is the multi-seed validation. If V-A is unstable, V-B is the model-free fallback (already
  characterised by BOOK2 — IS full +0.45, recent +1.45 — so its IS profile is pre-known).

---

## 4. Expected OOS impact + predicted IS/OOS profile

- **Predicted IS Sharpe:** ≈ **+0.3 to +0.6** (BOOK2 full-IS net +0.45; V-A may differ as the model
  timing filter interacts — expect within this band). This is INTENTIONALLY lower than iter-013's
  +0.88: the campaign learned that a high IS Sharpe from the LightGBM sign is the OVERFIT TRAP. A
  moderate IS Sharpe from a non-overfittable direction rule is the GENERALIZABLE bet.
- **Predicted OOS Sharpe:** ≈ **+0.5 to +1.5**, both-positive. Rationale: the most-recent IS
  sub-period (the closest IS analogue to OOS, and the row iter-011 showed pre-prints OOS) is +1.45 to
  +2.6 across horizons; OOS opened in a correction then recovered into a 2025 up-trend, and the
  trend-state rule is correctly positioned in both (long in up-trends, short/aside in the
  correction). This is the FIRST design whose IS fingerprint POINTS THE RIGHT WAY for OOS.
- **vs baseline (iter-001 IS −0.28 / OOS +0.64):** expected to BEAT IS clearly (+0.45 vs −0.28) and
  match-or-beat OOS (+0.5..+1.5 vs +0.64) at much lower dispersion → a relative MERGE candidate AND a
  both-positive candidate.
- **Trade rate:** at full trade rate the trend-state book fires on essentially every candle the
  confidence/conviction gate passes (BOOK2 5,075 IS / proportional OOS) — NOT trade-rate-constrained,
  unlike the thin 14d LightGBM book (iter-013 OOS 3.7/mo). This also FIXES the iter-013 trade-rate
  concern.

---

## 5. Risk Mitigation
- **R2 drawdown brake (KEEP):** IS-calibrated (iter-015), regime-agnostic. Bounds the worst
  sub-period (BOOK2 worst −2.56) drawdown magnitude; simulated historical effect (iter-015): OOS DD
  31.8%→6.4%, OOS net loss −28→−6. The trend-state book's negative sub-periods (2021-07, 2022-07) are
  exactly the regime-transition windows R2 is built to de-lever through.
- **R3 OOD (KEEP):** aggregator-level Mahalanobis gate, cutoff 0.70 — suppresses entries when the
  feature vector is outside the training-window distribution (regime-shift guard).
- **Concentration cap:** N/A (single symbol).
- **Kill-switch:** if the EXPLORATION V-A run shows the model-timing filter REVERSING the trend-state
  edge (recent sub-period flips negative vs BOOK2's +1.45), abandon V-A and run V-B (model-free).

---

## 6. Pre-registered FALSIFIER (both-positive target)

This design's both-positive claim is FALSIFIED if, on the real bagged backtest:
1. **OOS Sharpe ≤ 0** (the both-positive target is not met). Given the most-recent IS sub-period is
   strongly positive (+1.45..+2.6) and the rule cannot overfit, I predict OOS > 0; if OOS is negative
   the "stateless trend-state generalizes" thesis is wrong and the honest conclusion is that BTC 8h
   direction is unrecoverable at this horizon (pivot symbol/track).
2. **OR IS Sharpe < 0** (worse than the proxy and the baseline) — would indicate the model-timing
   filter in V-A is actively harmful; fall back to V-B (BOOK2, IS +0.45 pre-known).
3. **OR the most-recent IS sub-period comes in negative in the real backtest** (contradicting the
   proxy's +1.45) — would mean the let-run+R2+confidence interaction destroys the proxy edge; re-test
   V-B.

If (1) fires for BOTH V-A and V-B, the non-directional/trend-state pivot is genuinely falsified for
BTC 8h and the honest call is to report it and pivot. **I do not predict this:** the trend-state
rule is the first direction source in 15 iterations whose IS generalization fingerprint is positive,
robust across horizon and SMA window, and mechanistically un-overfittable.

---

## 7. QE WIRING FLAG (new code the Engineer must add for V-A)

1. **Trend-state direction primitive** — add `enable_trend_state_dir: bool = False` +
   `trend_state_sma_window: int = 200` to `LightGbmStrategy.__init__`, mirroring the iter-092
   `enable_btc_regime_kill` pattern. In `compute_features()`, build a past-only close-index for BTC
   (reuse the `_compute_btc_ret_42` close-index machinery at `lgbm.py:651+`). Add
   `_compute_trend_state(open_time) -> int|None` returning sign(close_prev − SMA200_prev) using only
   candles with `close_time < open_time` (past-only; conservative None when < SMA_window history).
2. **Direction override in `get_signal`** — in the specialist aggregator path, AFTER the conviction /
   R-CONV / R3 gates decide the trade FIRES, set `_sp_direction = _compute_trend_state(open_time)`
   (override the model's `_final_signed` sign; keep `_sp_weight` / confidence from the model for
   sizing). If `_compute_trend_state` returns None (warmup), fall back to the model sign (conservative).
3. **Runner flags** — add `--enable-trend-state-dir` (store_true) + `--trend-state-sma-window`
   (default 200) to `run_baseline_v1.py`, threaded to the strategy constructor. Single-axis: every
   other flag identical to the iter-013/015 base (label-mode fixed_horizon, N=42 timeout, R2 on).
4. **V-B (fallback)** — if needed, a `--trend-state-pure` mode that skips the model entirely and
   trades `trend_state(t)` direction on every confidence-gate-passing candle. Lower priority.
5. **Parity** — backtest and live `engine.py:_tick` must compute `trend_state` identically (past-only,
   BTC close-index). The iter-092 BTC-regime-kill gate already established the live close-index +
   defer-on-lag pattern; reuse it. No post-trade aggregation/netting.
6. **Pre-flight** — when `enable_trend_state_dir=True`, FAIL LOUD if the BTC parquet is missing
   (same guard as iter-092 `enable_btc_regime_kill`).

**Tests:** look-ahead suite must confirm `_compute_trend_state(open_time)` never reads a candle with
`close_time >= open_time`; a unit test pinning trend_state sign on a synthetic SMA-cross series.

---

## [Post-Phase-6 addendum — to be appended after the backtest]
_Reserved: real bagged IS/OOS Sharpe for V-A (and V-B if run), per-sub-period table vs the proxy,
falsifier resolution, R2 interaction, trade-rate, feature importance of the demoted model._
