# Research Brief — iter-v1/011 (BTCUSDT) — Phase 1/2 (IS-ONLY)

**Author:** Quant Research (crypto-markets). **Symbol:** BTCUSDT. **Interval:** 8h (sacred).
**Scope:** Phases 1 (diagnosis) + 2 (design), IS-ONLY. **Objective: SHARPE (risk-adjusted), NOT
absolute return, NOT beating buy-and-hold.**
**Task:** is the iter-010 long-edge IS→OOS collapse (IS +0.39 / OOS −1.48; longs +33%→−22.7%)
**REDUCIBLE OVERFIT** (fixable by a longer training window / leaner model / different horizon) or
**STRUCTURAL REGIME** (the let-winners-run long edge only exists in an up-trending regime)? Pick the
single highest-leverage gap-reduction lever for iter-011, justified ENTIRELY on IS-internal
stability.

All numbers come from three committed, re-runnable, IS-only scripts under
`analysis/BTCUSDT/iteration_v1-011/`. Each hard-filters `open_time < OOS_CUTOFF_MS = 1742774400000`
(2025-03-24) and asserts `df["open_time"].max() < OOS_CUTOFF_MS` BEFORE any forward quantity. The
walk-forward trains only on candles strictly before each test window minus an embargo ≥ label
horizon (`EMBARGO_C = N+3`); the forward label and let-run trade are computed on the IS slice only
(tail rows NaN-mask — no OOS candle exists in the frame). Regime variables are stateless & past-only
(`.shift(1)` on every rolling stat). Nothing is fit/selected/calibrated against OOS; `src/`, the
runner, and OOS are UNMODIFIED.

- `longedge_stability.py` → `training_window_stability.csv`, `expanding_subperiod_detail.csv`,
  `complexity_stability.csv` (Q1/Q2/Q3 — the three levers, one unifying metric)
- `regime_structural_test.py` → `seed_subperiod_signs.csv`, `longedge_by_regime.csv`,
  `sizing_implication.csv` (structural confirmation: seed-robustness + regime conditioning)
- `regime_gate_subperiod_n9.py` → `regime_gate_subperiod_n9.csv` (does a BULL gate fix the
  dispersion / most-recent-sub-period sign at N=9?)

**Simulation (faithful to iter-010).** The deployed directional specialist is proxied by an IS-only
walk-forward LightGBM (monthly refit, embargo ≥ label horizon, the iter-010 shallow regularized
config) on the exact iter-009/010 **19-col HYBRID** set, predicting the fixed_horizon **N=9 (3d)**
forward return; trade direction = sign(prediction). The **let-winners-run trade** enters at close,
exits at min{SL 1.45 ATR adverse, 9-candle timeout}; TP non-binding (winners run). Net of 0.1%
round-trip fee. **Proxy is DIRECTION-ONLY** per the campaign's thrice-confirmed proxy-overprediction
lesson — magnitudes are relative ranking signals, not backtest forecasts. The **unifying metric** is
the cross-IS-sub-period stability of the let-run **LONG** edge: per ~6-month sub-period LONG Sharpe,
`frac_pos` (fraction of sub-periods positive), dispersion (std of sub-period Sharpe), worst
sub-period, and the **most-recent** sub-period sign (2025 Q1 — the IS slice nearest OOS).

---

## 0. Headline finding (read this first)

**STRUCTURAL, not reducible. The let-winners-run BTC long edge is a trend-persistence (reflexivity)
bet that structurally pays only in an up-trending regime; it is dead in bear/correction regimes. No
IS-selectable lever — not training window (180d→730d→expanding), not model complexity (19/16/8-col,
strong-reg), not a BULL regime gate — moves the cross-sub-period stability: the long edge is positive
in exactly 6/9 IS sub-periods and negative in the SAME 3 (2022-H1, 2022-H2, 2025-Q1) for ALL 5 seeds.
The 3 negative sub-periods are exactly the bear/correction regimes, and crucially the MOST-RECENT IS
sub-period (2025-Q1, nearest OOS) is one of them — that negative sign is the IS-visible fingerprint
that pre-printed the OOS −1.48. The OOS failure is therefore an honest regime artifact (OOS opened in
a hostile correction), NOT a reducible overfit. There is no "fix" to manufacture.**

**Recommendation: NO-GATE → KEEP the iter-010 N=9 (3d) let-winners-run config UNCHANGED, and confirm
it at K=5 with a regime-aware READ (not a gate).** The ungated full book is the single most STABLE
config on every stability axis (lowest dispersion 0.984, best worst-sub-period −0.66, and the
least-negative most-recent sub-period −0.13). Every "fix" lever either leaves stability unchanged or
makes it WORSE — most importantly, a BULL regime gate (the obvious "fix") raises the headline Sharpe
by riding bull beta but DEGRADES the recent-sub-period sign (−0.13 → −0.97), reproducing the iter-010
T3-inversion failure mode at N=9. The honest iter-011 action is to confirm the ungated N=9 config at
K=5 to read its real OOS profile on a multi-seed basis, with the structural limit documented.

This is a clean STRUCTURAL finding earned on IS, per the task's explicit instruction not to
manufacture a fix when the edge is regime-bound in every config.

---

## 1. Q1+Q2 — Training-window sensitivity: longer windows DO NOT stabilize the long edge

`training_window_stability.csv`. 19-col model, seed 42, per-~6-month LONG let-run Sharpe.
Stability = `frac_pos` (sub-periods positive) + `dispersion` (std of sub-period Sharpe) + `worst`.

| training window | full Sₐₙₙ | LONG Sₐₙₙ | LONG WR | sub-periods | **frac_pos** | dispersion | worst |
|---|---:|---:|---:|---:|:--:|---:|---:|
| roll 180d | +1.70 | +2.30 | 0.475 | 10 | **0.600** | 1.685 | −1.90 |
| roll 365d | +1.20 | +1.32 | 0.456 | 9 | **0.667** | 1.269 | −1.90 |
| roll 545d | +1.82 | +1.86 | 0.452 | 8 | **0.625** | 1.419 | −1.70 |
| roll 730d | −0.25 | +0.49 | 0.435 | 7 | **0.571** | 1.251 | −1.36 |
| **expanding** | **+1.87** | **+1.96** | 0.470 | 9 | **0.667** | **1.212** | **−0.95** |

**Reads (crypto-native thesis FALSIFIED on its own terms):**
- The thesis was "a long edge learned on a narrow recent window overfits that regime; a longer window
  spanning bull+bear+chop yields a more stable (lower-dispersion) long edge." **The data says no.**
  `frac_pos` sits at ~0.6–0.67 regardless of window; the longest rolling window (730d) is the WORST
  on `frac_pos` (0.571) and even drives the full-book Sharpe negative (−0.25) — a 730d window is
  dominated by stale bear-regime training data when testing a bull, and vice-versa.
- The **expanding window is the best stability config** (frac_pos 0.667, lowest dispersion 1.212,
  least-bad worst −0.95). This is already what the iter-010 deployed config approximates (Optuna
  searches `training_days` 10–500, and the all-history expanding regime is the diversification-max
  end). **Raising the training_days floor would not help** — the longest fixed windows are strictly
  worse, and the expanding regime is already available to Optuna. TRAIN-WINDOW is ruled out.

### Q1 detail — the expanding-window per-sub-period table (the iter-010 proxy)

`expanding_subperiod_detail.csv`. This is the decisive evidence: the long edge tracks the BTC regime.

| sub-period | start | LONG n | **LONG Sₐₙₙ** | LONG WR | always-LONG Sₐₙₙ | regime |
|---|---|---:|---:|---:|---:|---|
| P0 | 2021-01 | 427 | +0.35 | 0.494 | +0.12 | early bull |
| P1 | 2021-07 | 370 | **+2.14** | 0.543 | +1.01 | **bull peak** |
| P2 | 2022-01 | 301 | **−0.95** | 0.395 | −1.97 | **bear (LUNA/3AC)** |
| P3 | 2022-07 | 293 | **−0.89** | 0.365 | −0.83 | **bear (FTX)** |
| P4 | 2023-01 | 291 | +1.31 | 0.457 | +1.67 | recovery |
| P5 | 2023-07 | 336 | +1.60 | 0.521 | +1.37 | uptrend |
| P6 | 2024-01 | 214 | +1.71 | 0.491 | +0.77 | **bull (ETF)** |
| P7 | 2024-07 | 248 | +0.92 | 0.492 | +1.69 | uptrend |
| P8 | 2025-01 | 69 | **−0.76** | 0.377 | −1.96 | **correction (nearest OOS)** |

The long edge is +0.35..+2.14 in the 6 bull/recovery sub-periods and −0.76..−0.95 in the 3
bear/correction sub-periods. **The WR mirrors it exactly: 49–54% in bull, 36–40% in bear.** The most
recent IS sub-period (P8, 2025-Q1) is negative — and it is the IS slice that most resembles the
post-cutoff OOS regime. **This single row pre-printed the OOS −1.48 collapse.**

---

## 2. Q3 — Model-complexity sensitivity: leaner / more-regularized does NOT stabilize either

`complexity_stability.csv`. Best window (expanding), seed 42.

| complexity config | full Sₐₙₙ | LONG Sₐₙₙ | LONG WR | **frac_pos** | dispersion | worst |
|---|---:|---:|---:|:--:|---:|---:|
| 19-col base (iter-010) | +1.87 | +1.96 | 0.470 | **0.667** | 1.212 | −0.95 |
| 16-col lean (drop 3 near-inert) | +1.82 | +1.89 | 0.466 | **0.667** | 1.183 | −1.04 |
| 8-col top (stable IS gain) | +1.16 | +1.39 | 0.456 | **0.667** | 1.147 | −1.29 |
| 19-col strong-reg | +1.80 | +1.54 | 0.463 | **0.667** | 1.232 | −1.47 |

**Reads:**
- **`frac_pos` is INVARIANT at 0.667 across all four complexity configs.** Dropping the FE-flagged
  near-inert columns (`mom_rsi_9 / vol_cmf_10 / ent_shannon_10`) trims dispersion microscopically
  (1.212→1.183) but does NOT add a positive sub-period and WORSENS the worst sub-period
  (−0.95→−1.04). Heavier regularization is the worst worst-sub-period (−1.47).
- The top-8 stable-gain features (`stat_autocorr_lag1, vol_garman_klass_10, vol_atr_5,
  stat_autocorr_lag5, trend_adx_14, stat_kurtosis_20, btc_funding_spread_30_90, trend_adx_7`) cut the
  feature count 19→8 with the same `frac_pos` and lowest dispersion (1.147) but a lower overall
  Sharpe and worse worst-sub-period. **Complexity is not the binding lever** — the negative
  sub-periods are negative regardless of how lean or regularized the model is. LEANER is ruled out.

---

## 3. Structural confirmation — seed-robust + regime-explained (the kill)

### 3.1 Seed robustness — the sign pattern is seed-DETERMINISTIC, not a basin lottery

`seed_subperiod_signs.csv`. Expanding WF, 19-col, per-sub-period LONG Sₐₙₙ across 5 seeds.

| sub-period | s42 | s123 | s456 | s789 | s1001 | **agreement** |
|---|---:|---:|---:|---:|---:|:--:|
| 2021-01 | +0.34 | +0.39 | +0.30 | +0.34 | +0.27 | **ALL +** |
| 2021-07 | +2.14 | +1.95 | +2.00 | +2.13 | +2.13 | **ALL +** |
| 2022-01 | −0.95 | −1.00 | −1.08 | −0.83 | −0.81 | **ALL −** |
| 2022-07 | −0.89 | −0.68 | −0.81 | −0.77 | −0.78 | **ALL −** |
| 2023-01 | +1.31 | +1.26 | +1.01 | +0.98 | +1.20 | **ALL +** |
| 2023-07 | +1.60 | +1.49 | +1.63 | +1.51 | +1.53 | **ALL +** |
| 2024-01 | +1.71 | +1.49 | +1.52 | +1.42 | +1.40 | **ALL +** |
| 2024-07 | +0.92 | +0.82 | +1.12 | +0.70 | +0.96 | **ALL +** |
| 2025-01 | −0.76 | −0.78 | −1.38 | −0.56 | −0.75 | **ALL −** |

**`frac_pos = 0.667 for ALL 5 seeds, and the SAME 3 sub-periods go negative for ALL 5 seeds.** The
sign of the long edge in each sub-period is seed-deterministic — this is NOT a basin-lottery artifact
(per `feedback_v1_basin_lottery_vigilance`, the per-seed spread on sign is effectively zero). The
regime dependence is a property of the data, not of any particular model draw.

### 3.2 Long edge conditioned on regime — BULL +2.47, BEAR +0.11 (structural directional beta)

`longedge_by_regime.csv`. Stateless past-only regime = 200-candle SMA slope sign. Expanding WF, s42.

| regime | LONG n | trades/mo | **LONG Sₐₙₙ** | LONG WR | always-LONG Sₐₙₙ |
|---|---:|---:|---:|---:|---:|
| ALL (ungated) | 2549 | 40.6 | +1.96 | 0.470 | +0.92 |
| **TREND bull (200SMA up)** | 1425 | 22.7 | **+2.47** | 0.489 | +1.49 |
| **TREND bear (200SMA dn)** | 1124 | 17.9 | **+0.11** | 0.447 | −0.34 |
| VOL high (natr>p67) | 887 | 14.1 | +0.92 | 0.528 | +0.18 |
| VOL low (natr<p33) | 921 | 14.7 | +1.36 | 0.428 | +0.64 |
| BEAR & VOL-high | 412 | 6.6 | −0.35 | 0.500 | −0.66 |

**The long edge is +2.47 in BULL and collapses to +0.11 (≈ dead) in BEAR.** This is the mechanistic
explanation, and it is exactly the crypto-native reading: **a let-winners-run long book is a
trend-persistence bet that structurally requires an up-trending (reflexive) regime to pay.** In a
down-trend the "let winners run" timeout systematically gives back gains and the SL absorbs the
adverse drift — there is no persistent up-move to ride. The model's "long directional skill" is, at
root, trend-following beta that only earns when BTC trends up. (Note the model DOES beat always-LONG
in every regime including bear — it adds directional info — but the bear-regime absolute level is
~zero, so it cannot rescue a bear sub-period.)

### 3.3 Why a BULL regime GATE is NOT the fix (the iter-010 T3-inversion, reproduced at N=9)

`regime_gate_subperiod_n9.csv`. The obvious "fix" is to gate the book to BULL. It fails the unifying
stability metric — exactly as the iter-010 brief found at N=21, now confirmed at N=9.

| book | overall Sₐₙₙ | frac_pos | dispersion | worst | **MOST-RECENT (2025-Q1)** |
|---|---:|:--:|---:|---:|---:|
| **ungated full (iter-010 N9)** | +1.87 | 0.667 | **0.984** | **−0.66** | **−0.13** |
| BULL-restricted full | +2.10 | 0.667 | 1.008 | −0.97 | **−0.97** |
| LONG-only in BULL | +2.47 | 0.667 | 1.640 | −2.91 | −0.54 |
| ungated LONG-only | +1.96 | 0.667 | 1.212 | −0.95 | −0.76 |

**The BULL gate raises the headline Sharpe (+1.87→+2.10) purely by riding bull beta, but it makes
EVERY stability axis WORSE:** dispersion up (0.984→1.008), worst sub-period worse (−0.66→−0.97), and —
decisively — **the most-recent sub-period inverts harder (−0.13 → −0.97).** Gating to BULL throws away
the model's bear-regime trades (which add directional info even when ~flat), concentrating exposure
into precisely the fragile beta the v1 merge gate was rewritten to reject. **A regime gate does not
fix the IS-visible OOS-fragility fingerprint — it amplifies it.** This is the cleanest possible
in-sample confirmation that there is no gate-based fix; the ungated full book is the MOST stable
config available.

---

## 4. RECOMMENDATION — (STRUCTURAL) NO-GATE → confirm the iter-010 N=9 config UNCHANGED at K=5

**Decisive choice: the long-edge collapse is STRUCTURAL (regime-bound), not reducible. There is no
IS-selectable lever that improves cross-sub-period stability. Per the task's explicit guidance — "A
clean STRUCTURAL finding is valuable; don't manufacture a fix" — the honest iter-011 action is to
KEEP the iter-010 N=9 (3d) let-winners-run config EXACTLY as-is (19-col HYBRID, fixed_horizon N=9,
TP non-binding `atr_tp=100`, `atr_sl=1.45`, exec timeout = 9 candles, NO gate) and run a K=5
confirmation to read its true multi-seed OOS profile.** The ungated full book is empirically the
most stable config on every axis tested; no change to features, window, complexity, or regime
conditioning improves it on IS.

**Why each alternative lever is ruled out (all on IS-internal stability, §1–§3):**
- **TRAIN-WINDOW**: `frac_pos` does not rise with longer windows; the longest (730d) is the WORST
  (frac_pos 0.571, full Sharpe −0.25). Expanding is already the best and already in Optuna's reach.
- **LEANER / regularization**: `frac_pos` invariant at 0.667 across 19/16/8-col + strong-reg; the
  negative sub-periods stay negative. Leaner trims dispersion trivially but worsens the worst
  sub-period.
- **HORIZON**: N=9 is already the iter-010 milestone; the structural regime dependence is a property
  of the let-run long book, not the horizon (the same 3 bear/correction sub-periods sink it). A
  different N relocates trades but cannot make a down-trend pay a trend-persistence bet.
- **GATE**: a BULL gate degrades dispersion AND inverts the most-recent sub-period harder (§3.3) —
  the iter-010 finding, reproduced at N=9.

### Exact iter-011 config (BYTE-IDENTICAL to iter-010 — confirm, don't change)
- **Features (19, no regen):** the iter-009/010 HYBRID set verbatim.
- **Label:** `label_mode="fixed_horizon"`, `label_timeout_minutes=4320` (= 9 candles = 3d).
  `use_atr_labeling=False`.
- **Execution:** `atr_tp=100.0` (TP NON-BINDING), `atr_sl=1.45`, exec timeout = 9 candles. R2 OFF.
  No regime gate (the §3.3 evidence rules it out on the Sharpe/stability basis).
- **Cadence/budget:** **K=5 confirmation** (the diary explicitly authorized advancing to a K=5 screen
  once a both-positive-capable config exists; iter-010 produced the FIRST positive-IS config, so the
  K=5 read on the most-stable variant is the correct next compute). n_trials per the v1 SPECIALIST
  default, slippage 2 (honest costs), training_days unchanged (sacred range — and §1 shows the
  expanding/all-history end is already the best, so no floor change).
- **The ONLY change vs iter-010 is the seed count (3→5).** Everything else byte-identical.

### Predicted effect on the IS/OOS gap (DIRECTION-ONLY, per the proxy lesson)
- IS Sharpe predicted to stay **clearly positive** (the milestone holds; the long edge is real in
  bull/recovery sub-periods, which dominate the 2020-2025 IS window).
- **The IS/OOS gap will NOT close** by this confirmation, and I am stating that honestly up front:
  the structural regime dependence means the OOS Sharpe is a function of the post-cutoff regime mix,
  not of any IS-selectable model property. If the OOS window remains net-corrective (as 2025-Q1 was),
  OOS will stay weak; if BTC up-trends through the OOS window, the long edge will pay. **The value of
  the K=5 run is a clean, multi-seed measurement of the structural limit — establishing whether the
  ungated N=9 config is the iter-010 single-seed result reproduced (real milestone) or a single-seed
  draw (basin artifact) — NOT a gap-reduction.** §3.1 (seed-deterministic sub-period signs) predicts
  the IS milestone WILL reproduce across seeds.
- **Forward-looking implication for iter-012+ (NOT this iteration's axis):** the only honest path to
  a smaller OOS gap is a **regime-aware SIZING / long-bias variant** (vol-scaled exposure that
  de-levers in down-trends rather than trying to short them) — NOT a binary gate (§3.3 rules gates
  out) and NOT a model/feature/window change (§1–§2 rule those out). That is a sizing-primitive axis
  for a future iteration, flagged here for the diary's Next-Ideas, not proposed for K=5.

### Risk Mitigation
- **No new state introduced** (no gate, no new feature, no window change) → no new fragility surface
  vs iter-010. The let-run SL at 1.45 ATR is the loss-cut primitive; the 3d timeout caps per-trade
  exposure.
- R3 OOD Mahalanobis gate + confidence-threshold trade filter remain as in the iter-010 wiring
  (unchanged). Concentration N/A (single symbol). Trade-rate ~73/mo full / ~40/mo long ≫ 10/mo floor.
- The structural regime risk is DOCUMENTED, not hidden: this config is expected to bleed in
  sustained down-trends. That is the honest profile, and the K=5 confirmation measures its magnitude.

### Pre-registered both-positive coherence FALSIFIER (NEGATIVE verdict if any holds)
1. **Confirmation IS Sharpe (K=5 multi-seed mean) ≤ 0** — the iter-010 IS milestone fails to
   reproduce (would mean iter-010's +0.39 was a single-seed draw; §3.1 predicts it WILL reproduce, so
   this firing falsifies the seed-determinism claim).
2. **The K=5 per-seed IS Sharpe spread > 0.50 OR sub-period sign Jaccard < 0.40** — basin-lottery
   vigilance: if the sub-period sign pattern is NOT seed-stable in the real backtest (contradicting
   §3.1's offline finding), the structural read is downgraded and a multi-seed re-validation is
   mandated before any conclusion.
3. **Fewer than 3/5 confirmation seeds positive IS** (sign not robust at K=5).
4. **The structural read is contradicted**: if the real backtest's OOS is strongly positive while the
   most-recent IS sub-period is negative, the "most-recent-sub-period sign pre-prints OOS" mechanism
   (§1 Q1 detail, §3.3) is falsified and the regime-bound conclusion must be revisited.

Note this falsifier is deliberately framed around **coherence of the structural read**, not around
forcing OOS-positive — because the structural finding PREDICTS OOS is regime-contingent. A weak OOS
at K=5 that coincides with a corrective OOS regime CONFIRMS the structural finding; it does not
falsify it.

### Kill-switch (mid-flight)
Abort the K=5 run if the exit mix shows TP exits firing (non-binding-TP design broke), or if K=5 mean
IS Sharpe < −0.20 (worse than iter-009 — the milestone evaporated and the whole let-run-long premise
needs re-examination before spending more compute).

---

## Appendix — methodology / OOS-vigilance attestation
- All three scripts hard-filter `open_time < OOS_CUTOFF_MS` and assert `df["open_time"].max() <
  OOS_CUTOFF_MS` BEFORE any forward computation; the IS frame is the ONLY frame; OOS rows
  (open_time ≥ cutoff) are never read. Knowing "iter-010 OOS = −1.48" informed the QUESTION
  (structural vs reducible) but NOTHING was fit/selected/calibrated against OOS.
- The walk-forward trains only on candles strictly before each monthly test window minus an embargo
  `EMBARGO_C = N+3 = 12` candles (≥ the N=9 label horizon) — the forward label of every training
  candle terminates at or before the test-window start (purged). Rolling vs expanding windows differ
  only in the train-window LOWER bound; both respect the embargo upper bound.
- The forward label (N=9 forward return) and the let-run trade are computed on the IS slice only; the
  forward reach at the IS tail NaN-masks (no OOS candle to index) — no peeking.
- Regime variables are stateless & past-only: the 200-SMA slope sign uses `.shift(1)`; NATR terciles
  use rolling-250 quantiles with `.shift(1)`. The let-run trade reproduces the iter-009/010 execution
  (enter at close, exit at min{SL 1.45 ATR, N-candle timeout}, TP non-binding, 0.1% fee; ATR =
  `close × vol_natr_21 / 100`, the runner convention).
- The LightGBM read is a faithful DIRECTION-ONLY proxy of the deployed bagged specialist; magnitudes
  are relative ranking signals, not backtest forecasts (campaign proxy-overprediction lesson).
- Scripts re-runnable; lint clean modulo the idiomatic uppercase design-matrix (`X`/`Xm`) and
  docstring-line-length carve-out consistent with the iter-008/009/010 convention.
