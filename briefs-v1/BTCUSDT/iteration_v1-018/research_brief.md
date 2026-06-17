# Research Brief — iter-v1/018 (BTCUSDT) — Phases 1–2 (ASYMMETRY investigation, IS-ONLY)

**Author:** Crypto-markets Quant Researcher. **Symbol:** BTCUSDT. **Interval:** 8h (sacred).
**Scope:** Phase 1 (EDA) + Phase 2 (labeling/target). **IS-ONLY.** **Objective: SHARPE.**
**TARGET = both-positive (IS Sharpe > 0 AND OOS Sharpe > 0).** Merge bar RELATIVE vs
`BASELINE_V1_BTCUSDT` (iter-001 IS −0.2793 / OOS +0.6401).

All numbers come from four committed, re-runnable, IS-only scripts under
`analysis/BTCUSDT/iteration_v1-018/`. Each hard-filters `open_time < OOS_CUTOFF_MS = 1742774400000`
(2025-03-24), asserts `df["open_time"].max() < OOS_CUTOFF_MS` BEFORE any forward quantity, computes
the forward log-return AFTER the filter, builds every primitive (SMA200, ATR14, distance) with
`.shift(1)` past-only, and selects every threshold/quantile on PAST rows only (purged by N_LABEL=42).
**Nothing is fit/selected/calibrated against OOS; OOS rows are never read.** A leak-probe
(`shift(1)` vs no-shift) confirms the past-only construction is load-bearing (143/5527 rows flip
direction-sign without it). `src/`, the runner, and OOS are UNTOUCHED.

- `asymmetry_subperiod_decomposition.py` → decomposes the iter-016 trend-state book by SIDE across
  the 11 IS sub-periods.
- `asymmetric_design_candidates.py` → tests the 4 task candidates (asym-threshold, short-and-flat,
  long-and-flat mirror control, trend-strength gate).
- `strength_gate_by_side.py` → tests whether the trend-strength gate's benefit is asymmetric by side.
- `strength_quantile_robustness.py` → sweeps the strength knob (no knife-edge) + trade-rate estimate.

---

## 0. Headline finding (read this first)

**The OOS asymmetry from diary-017 ("shorts generalize, longs don't") is NOT an IS-sub-period-stable
edge — it is the OPPOSITE of what the IS data says, and is concentrated in a single recent window.
A short-favoring design would be pure curve-fit to the OOS observation. HOWEVER, the IS sub-period
decomposition surfaced a DIFFERENT, genuinely IS-stable asymmetry: a crypto-native trend-CONVICTION
filter (distance from the SMA200 in ATR units) creates a stable, sub-period-robust edge on the LONG
side and an unstable one on the SHORT side. The clean, single-axis merge candidate is the SYMMETRIC
trend-strength conviction gate — trade the trend-state direction ONLY when the trend is convincing
(|close − SMA200| ≥ past-only median, in ATR units); skip weak-trend chop. This is the first design
in the campaign whose IS full-period Sharpe is STRONG (+1.21) AND whose sub-period fingerprint is
stable (frac_pos 0.70, recent3 +2.09) at the same time.**

### 0.1 — The asymmetry is the OPPOSITE of the OOS observation (IS-only)

`asymmetry_subperiod_decomposition.py`, trend-state book split by side, net of 0.14% RT cost:

| leg | full-IS Sₐₙₙ | frac_pos | dispersion | RECENT (most-recent IS sub-period) | WR | mret%/trade |
|---|---:|:--:|---:|---:|:--:|---:|
| FULL symmetric (iter-016 BOOK2) | +0.32 | 0.64 | 1.35 | +1.45 | 49.4% | +0.78% |
| **LONG leg only** | **+0.98** | **0.73** | 3.50 | −0.74 | 54.3% | **+2.39%** |
| **SHORT leg only** | **−0.58** | **0.27** | 2.83 | +3.16 | 42.8% | **−1.39%** |

On IS, the **LONG leg is the money-maker** (full +0.98, positive in 8/11 sub-periods, +2.39%/trade)
and the **SHORT leg is a net loser** (full −0.58, positive in only 3/11 sub-periods, −1.39%/trade).
The short leg's apparent strength lives entirely in the SINGLE most-recent IS window (2024-12, +3.16).
**This is exactly the OOS observation inverted** — diary-017 saw OOS shorts +6.5% / OOS longs −14%,
but that is an OOS-regime fact, not an IS-stable property. Designing a short-favoring rule on it would
be the curve-fit the task explicitly warns against.

### 0.2 — short-and-flat vs long-and-flat: the mirror control settles it (IS-only)

`asymmetric_design_candidates.py`, the decisive contrast:

| candidate | full-IS Sₐₙₙ | frac_pos | recent3 (avg last-3 sub-periods) | WR | mret%/trade |
|---|---:|:--:|---:|:--:|---:|
| C0 symmetric (anchor) | +0.32 | 0.64 | +0.61 | 49.4% | +0.78% |
| Cb **short-and-flat** | **−0.58** | **0.27** | **−0.70** | 42.8% | −1.39% |
| Cc **long-and-flat** (mirror) | **+0.98** | **0.73** | **+0.50** | 54.3% | +2.39% |
| Ca asym-threshold (band 0.06) | +0.28 | 0.55 | +0.63 | 49.2% | +0.68% |

**Short-and-flat (Cb) — the literal "trade shorts, skip longs" reading of the OOS observation — is
the WORST candidate on IS** (negative full, frac_pos 0.27, negative recent3). Its mirror, long-and-flat
(Cc), dominates. **The IS-honest asymmetry is LONG-favoring, not short-favoring.** The
asymmetric-entry-threshold candidate (Ca) does not beat the symmetric anchor at any band. So candidates
(a) and (b) from the task are both falsified on IS — and crucially, candidate (b) in its OOS-suggested
direction (short-and-flat) is an OOS artifact.

### 0.3 — the genuine IS-stable mechanism: a crypto-native trend-CONVICTION gate

`asymmetric_design_candidates.py` Cd + `strength_gate_by_side.py`. Trade the trend-state direction
ONLY in **strong-trend** rows (signed distance from SMA200 measured in ATR units, |dist| ≥ past-only
median); skip weak-trend chop. Net of cost, IS-only:

| book | full-IS Sₐₙₙ | frac_pos | dispersion | recent3 | npos/scored | WR | mret%/trade | trades |
|---|---:|:--:|---:|---:|:--:|:--:|---:|---:|
| Cd strong BOTH (symmetric gate) | **+1.21** | **0.70** | 2.33 | **+2.09** | 7/10 | 56.4% | +2.90% | 2328 |
| Cd strong LONG | +1.79 | 0.75 | 8.45 | +2.87 | 6/8 | 61.8% | +4.16% | 1531 |
| Cd strong SHORT | +0.20 | 0.29 | 6.90 | **−9.74** | 2/7 | 45.9% | +0.49% | 797 |
| weak BOTH (the chop we skip) | −0.22 | 0.30 | 1.16 | −0.11 | 3/10 | 45.8% | −0.54% | 2809 |

The conviction filter's benefit is **strongly asymmetric by side**: strong-LONG is a clean stable edge
(frac_pos 0.75, recent3 +2.87, WR 62%); strong-SHORT is blowup-driven and unstable (recent3 −9.74,
positive in only 2/7). And the rows the gate SKIPS (weak-trend chop) are net-negative (full −0.22) —
the gate removes the loss-making chop, not signal. **The symmetric gate (Cd strong BOTH) captures the
stable long edge AND the genuinely-positive strong-short windows while cutting the chop, at the best
combination of full Sharpe (+1.21), frac_pos (0.70), low dispersion (2.33), and recent3 (+2.09).**

### 0.4 — no knife-edge; broad plateau (IS-only)

`strength_quantile_robustness.py`, symmetric gate across the strength quantile q:

| q | full-IS Sₐₙₙ | frac_pos | recent3 | WR | mret%/trade | est. OOS firing rows |
|---:|---:|:--:|---:|:--:|---:|---:|
| 0.30 | +0.77 | 0.70 | +1.35 | 52.6% | +1.83% | 800 |
| 0.40 | +1.00 | 0.70 | +1.86 | 54.7% | +2.39% | 676 |
| **0.50** | **+1.21** | **0.70** | **+2.09** | **56.4%** | **+2.90%** | **571** |
| 0.60 | +1.37 | 0.67 | +2.60 | 56.7% | +3.35% | 476 |
| 0.70 | +1.44 | 0.67 | +2.57 | 56.2% | +3.55% | 372 |

Monotone, flat-rising plateau — full Sharpe climbs with q while frac_pos stays 0.67–0.70. q=0.50 is
the crypto-canonical mid-plateau choice (median = "above-average trend strength"), matching the
un-tuned SMA200 philosophy. This is NOT a tuned number. (Higher q raises Sharpe but thins trades; we
pick the median, not the Sharpe-max, to stay off the trade-rate floor.)

→ **RECOMMENDATION: iter-018 = TREND-STATE direction + SYMMETRIC trend-CONVICTION gate.** Direction =
sign(close_prev − SMA200_prev) (iter-016 keeper); ADD an entry filter: only fire when the trend is
convincing (|close_prev − SMA200_prev| / ATR14_prev ≥ past-only-median). Keep the 14d let-run
execution + R2 brake. Single axis vs iter-016: the conviction gate.

---

## 1. Why this is the right answer to the task's question

The task asked: does BTC's long and short edge have DIFFERENT generalization properties that an
IS-only analysis reveals? **Yes — but not the difference the OOS observation suggested.** The IS-stable
asymmetry is that the long side carries the edge and the short side is unstable; AND the conviction
filter sharpens precisely that long-side stability while the same filter does NOT stabilize the short
side (strong-SHORT recent3 −9.74). The honest, non-cheating conclusion is twofold:

1. **NULL on the short-favoring framing** (task candidates a + b in their OOS direction): the
   "shorts generalize" pattern is an OOS-regime artifact with NO IS-sub-period support — short-and-flat
   is the worst IS candidate. We refuse to fit it. (This prevents a curve-fit; valuable in itself.)
2. **POSITIVE on a different, IS-justified mechanism** (task candidate c, generalized): a trend-strength
   conviction gate is the most IS-sub-period-stable design found, and its mechanism is crypto-native —
   strong-trend rows are where BTC's reflexive trend-persistence is real; weak-trend rows (price hugging
   the SMA200) are chop where the 14d directional bet is a coin-flip net of cost.

This is a single-axis, low-parameter, mechanism-driven change — not knob-tuning.

---

## 2. Labeling / Phase-2 decision — UNCHANGED; the axis is an ENTRY FILTER

**Target/label UNCHANGED:** `label_mode="fixed_horizon"`, timeout N=42 (14d), let-winners-run exit,
`abs_pnl` weights, ATR barriers as iter-015/016. **Direction UNCHANGED:** stateless trend-state
sign = sign(close_prev − SMA200_prev), past-only.

**NEW (the single axis): a trend-CONVICTION entry gate.** At each signal candle compute, past-only:
```
dist_atr(t) = (close[t−1] − SMA200(close)[t−1]) / ATR14(t−1)        # signed trend strength
fire(t)     = |dist_atr(t)| ≥ q_thr(t)                              # q_thr = past-only median of |dist_atr|
```
where `q_thr(t)` is the **median of |dist_atr| over candles strictly before t's training cut** (the
existing walk-forward past-only convention; conservative: if < 50 past rows, do not gate). The trade
fires ONLY when `fire(t)` is True; otherwise the candle is skipped (no trade — flat). Direction, when
it fires, is the unchanged trend-state sign.

---

## 3. Proposed changes (Phase 5 → QE Phase 6)

- **Labeling:** UNCHANGED.
- **Direction:** UNCHANGED (iter-016 trend-state override, `enable_trend_state_dir=True`,
  `trend_state_sma_window=200`).
- **NEW conviction gate:** `enable_trend_strength_gate: bool=False`, `trend_strength_atr_window: int=14`,
  `trend_strength_quantile: float=0.50`. In `compute_features()` build `dist_atr` from the SAME
  past-only close-index machinery already used for the trend-state SMA (reuse the
  `_compute_trend_state` close-index at `lgbm.py:651+`); add `_compute_trend_strength(open_time) ->
  float|None` returning `(close_prev − SMA200_prev)/ATR14_prev`. Maintain a rolling past-only median of
  `|dist_atr|` (or compute it from the training window at month-train time, mirroring the R3 OOD
  training-window-stat pattern). At signal time, if `enable_trend_strength_gate` and the model+R-gates
  decide to fire, ALSO require `|dist_atr(t)| ≥ q_thr` else SKIP (return no-trade). If
  `_compute_trend_strength` returns None (warmup), do NOT gate (conservative — fire).
- **Features:** KEEP the 19-col HYBRID set (unchanged; the gate is a RULE-layer primitive, not a
  feature). Single-axis discipline.
- **Risk gates:** KEEP R2 drawdown brake, R3 OOD (0.70), R5 vol-target. R1 OFF. Unchanged from iter-016.

### Section 2.5 — Risk Declaration (v1)
- **Declaration:** NORMAL-RISK.
- **Reason:** the conviction gate is a stateless RULE-layer entry filter on top of the unchanged
  training objective and unchanged direction rule — it does NOT change Optuna's training-objective
  domain (the model still trains the same direction labels; only WHETHER a candle trades is gated).
- **Mitigation:** the gate only REMOVES trades (the weak-trend chop, IS full −0.22); it cannot add a
  position the baseline wouldn't take. Worst case it thins the book — caught by the trade-rate floor.

---

## 4. Expected OOS impact + predicted IS/OOS profile

- **Predicted IS Sharpe:** ≈ **+0.9 to +1.3** (Cd strong BOTH full +1.21 at q=0.50; the let-run + R2 +
  model-timing interaction may shift it within this band). HIGHER than iter-016's BOOK2 (+0.45) because
  the gate removes the net-negative chop.
- **Predicted OOS Sharpe:** ≈ **+0.3 to +1.0**, both-positive TARGET. Rationale: the recent3 IS
  fingerprint (the closest IS analogue to OOS) is +2.09 and frac_pos is 0.70 — the most stable
  fingerprint of any design in the campaign. The mechanism (skip weak-trend chop, trade convincing
  trends) is regime-agnostic. CAVEAT: this is a directional 14d book and the campaign's OOS-long
  fragility is real; the gate's protection is that it skips the LOW-conviction longs (price hugging the
  SMA200) that are the coin-flips — but a deep OOS-bull-correction could still hurt the strong-LONG leg.
  Honest CI is wide.
- **vs baseline (iter-001 IS −0.28 / OOS +0.64):** expected to BEAT IS clearly (+1.21 vs −0.28); OOS
  is the open question — a both-positive at OOS > 0 BEATS the baseline on the coherence/generalization
  gate even if raw OOS is below +0.64, per the codified Sharpe-first directive.
- **Trade rate:** est. ~571 OOS firing rows at q=0.50 (proportional scaling); but the let-run book holds
  ~42 candles so the INDEPENDENT OOS trade count is much lower. **This is the primary risk** — the v1
  specialist floor is ≥50 OOS trades. Must be verified on the REAL backtest. If the K=20 run comes in
  < 50 OOS trades, drop q to 0.40 (est. firing 676) or 0.30 (800) — both still IS-stable (full +1.00 /
  +0.77, frac_pos 0.70).

---

## 5. Risk Mitigation

- **R2 drawdown brake (KEEP):** IS-calibrated (iter-015), bounds the worst sub-period (Cd strong BOTH
  worst −4.41) drawdown. Simulated historical effect (iter-015): OOS DD 31.8%→6.4%.
- **R3 OOD (KEEP):** Mahalanobis gate cutoff 0.70 — regime-shift guard, complementary to the
  conviction gate (R3 gates on feature-distribution OOD; the conviction gate on trend strength).
- **Conviction gate IS the new risk primitive:** it removes the IS-net-negative weak-trend chop
  (full −0.22, the bulk of losing trades). Simulated IS effect: full Sharpe +0.32 (ungated) → +1.21
  (gated q50); the skipped rows are 2809 IS chop rows with −0.54%/trade mean.
- **Concentration cap:** N/A (single symbol).
- **Kill-switch:** if the EXPLORATION (K=3) run shows the gate REVERSING the long-leg edge (recent
  sub-period flips negative vs Cd's +2.09) OR the OOS trade count < 30, abandon q=0.50 and re-test at
  q=0.30 (the trade-rate-preserving variant) — pre-registered, IS-pre-known profile.

---

## 6. Pre-registered FALSIFIER (both-positive target)

This design's both-positive claim is FALSIFIED if, on the real bagged K=20 backtest:
1. **OOS Sharpe ≤ 0** — the conviction-gate-generalizes thesis is wrong; the honest conclusion is that
   even high-conviction BTC 14d directional bets do not generalize to the 2025-26 OOS, and the campaign
   should pivot off directional BTC entirely (symbol/track pivot).
2. **OR IS Sharpe < +0.45** (worse than the ungated iter-016 BOOK2) — would mean the let-run + model
   timing interaction destroys the gate's IS edge; fall back to the bare iter-016 trend-state book.
3. **OR the most-recent IS sub-period comes in negative on the real backtest** (contradicting the
   proxy's +2.09 recent3) — would mean the gate's stability is a proxy artifact; re-test bare BOOK2.
4. **OR OOS trades < 50** AND the q=0.40/q=0.30 fallbacks also miss the floor — the design is too thin
   at this horizon to validate; report and pivot the horizon (shorter N) to lift trade count.

**MANDATORY K=20 confirmation:** the iter-016 K=5 both-positive was a proven basin-lottery (iter-017).
ANY K=5 EXPLORATION screen of this design MUST be K=20-confirmed before any merge claim. The
direction + gate are deterministic (zero seed variance), but the model-timing/sizing layer is the
basin-lottery surface — so the K=20 average is the only honest read.

---

## 7. QE WIRING FLAG (new code the Engineer must add)

1. **Trend-strength primitive** — add `enable_trend_strength_gate: bool=False`,
   `trend_strength_atr_window: int=14`, `trend_strength_quantile: float=0.50` to
   `LightGbmStrategy.__init__`, mirroring the iter-092 `enable_btc_regime_kill` / iter-016
   `enable_trend_state_dir` patterns. Reuse the trend-state close-index build at `lgbm.py:651+`.
2. **`_compute_trend_strength(open_time) -> float|None`** — returns `(close_prev − SMA200_prev) /
   ATR14_prev` using ONLY candles with `close_time < open_time` (past-only). None during warmup
   (< SMA200 or < ATR14 history) → do NOT gate (conservative fire).
3. **Past-only strength threshold** — at month-train time compute `q_thr = quantile(|dist_atr| over the
   training window, trend_strength_quantile)`, stored per model (mirror the R3 OOD training-window-stat
   pattern). Do NOT recompute on test rows.
4. **Gate in `get_signal`** — AFTER the conviction/R-CONV/R3 gates AND the trend-state direction
   override decide the trade FIRES, additionally require `abs(_compute_trend_strength(open_time)) ≥
   q_thr` else return no-trade (skip). If `_compute_trend_strength` is None, fire (conservative).
5. **Runner flags** — `--enable-trend-strength-gate` (store_true), `--trend-strength-atr-window`,
   `--trend-strength-quantile`.

**Cadence:** EXPLORATION K=3 screen first → if PROMISING (IS>0 AND OOS>0, beats baseline on coherence)
→ MANDATORY K=20 CONFIRMATION (the basin-lottery is live). Only the K=20 read can support a merge.
