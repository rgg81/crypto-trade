# Research Brief — iter-v1/008 (BTCUSDT) — Phase 1/2 (IS-ONLY)

**Author:** Quant Research. **Symbol:** BTCUSDT. **Scope:** Phases 1 (EDA) + 2 (labeling),
IS-ONLY. **Mandate:** the orthogonal-feature lever is CLOSED (iter-005/006/007 all NEGATIVE;
diary-v1/007). Investigate the two untouched NON-feature levers — **(1) labeling/horizon** and
**(2) regime gate** — and choose ONE decisive iter-008 axis, or ESCALATE.

All numbers come from three committed, re-runnable, IS-only scripts. Each asserts
`open_time < OOS_CUTOFF_MS = 1742774400000` (2025-03-24) with a leak guard
(`assert df["open_time"].max() < OOS_CUTOFF_MS`); each reads ONLY the BTC 8h parquet; none
touches `src/`, the runner, or OOS:

- `analysis/BTCUSDT/iteration_v1-008/label_horizon_learnability.py` → `label_horizon_learnability.csv`
- `analysis/BTCUSDT/iteration_v1-008/regime_conditional_edge.py` → `regime_conditional_edge.csv`
- `analysis/BTCUSDT/iteration_v1-008/regime_edge_forensic.py` → `regime_edge_forensic.csv`

The label scripts FAITHFULLY reproduce the runner's `label_trades` (ATR triple-barrier first-hit;
fixed_horizon sign rule; trend_scanning OLS-slope rule — verified line-by-line against
`src/crypto_trade/strategies/ml/labeling.py:217-535` and `_trend_scan_label:132-214`), using the
runner's own ATR convention (`ATR = close × vol_natr_21 / 100`, `lgbm.py:758`) and label fee (0.1%).

IS window: 2020-01-01 .. 2025-03-23 16:00 (5727 candles, 8h; ≈62.7 months). Learnability is measured
by purged forward-chaining CV (5 folds, 3-bar embargo) on the frozen 41-col prune
(`V1_BTC_PRUNED_ITER002`) — the exact feature set the specialist trains on.

---

## 0. Headline finding (read this first)

**Neither non-feature lever gives BTC a learnable, coherent edge. Both confirm the FE's noise-floor
diagnosis from the other side: the problem is not the feature set, the label, OR the regime — the
prune model is anti-directional out-of-fold across the entire IS window.**

Two decisive numbers:

1. **No label config lifts BTC off the noise floor.** The CURRENT label (ATR triple-barrier
   2.9/1.45, 7d) has **OOF directional accuracy 0.4886** — *below* a coin flip — and OOF econ
   **−0.24%/candle** (loses money net of fee). The best alternative over 13 label configs reaches
   **dir_acc 0.5116** (`trend_scanning`) and **econ +0.046%/candle** — a fraction of one fee, inside
   noise. Score-IC is ±0.03 everywhere. This is the same 0.5068/−0.095 noise floor the FE found at
   iter-006, now confirmed across every exposed labeling knob.

2. **No regime gate produces model alpha — every "positive-econ" regime is BTC long-drift (beta).**
   The ungated OOF profile is: **model_econ −0.10, always-LONG +0.22, flip-model −0.097**. The model's
   directional signal is *anti-correlated* with realized returns. In every regime bucket that shows
   positive econ (high-vol, uptrend, ADX≥25), **always-LONG beats the model by 2–3×** (e.g. high-vol:
   model +0.18 vs always-long **+0.43**). Gating to those regimes would not flip BTC's edge coherent —
   it would ride BTC's secular uptrend with an anti-directional model bolted on. That is precisely the
   fragile, sign-inverted regime exposure the v1 merge gate was rewritten to reject.

→ **RECOMMENDATION: ESCALATE.** BTC at 8h with this architecture is at the noise floor on the feature
axis (FE, iter-006), the label axis (this brief, §1), and the regime axis (this brief, §2). A clean,
well-evidenced ESCALATE is the honest outcome. Detail + exact alternative below.

---

## 1. Investigation (1) — Label-horizon learnability

Purged 5-fold CV, 3-bar embargo, 41-col prune. `dir_acc` = OOF directional accuracy (model's chosen
sign vs realized sign at the label's own horizon — the metric that drives a directional specialist's
Sharpe). `base_label_econ` = the realized signed return of the LABEL ITSELF (oracle-direction, net
fee) = the bucket's ceiling. `oof_econ` = what the MODEL actually captures out-of-fold.

| label config | n_valid | dir_acc | score_IC | OOF R² | **OOF econ %/cand** | base ceiling % | trades/mo |
|---|---|---|---|---|---|---|---|
| **tb ATR 2.9/1.45, to21 (CURRENT)** | 5726 | **0.4886** | −0.022 | −0.343 | **−0.2398** | +5.12 | 91 |
| tb ATR 2.9/1.45, to42 (14d) | 5726 | 0.4897 | −0.026 | −0.252 | −0.2220 | +5.91 | 91 |
| tb ATR 2.9/1.45, to63 (21d) | 5726 | 0.4950 | +0.003 | −0.256 | −0.1001 | +6.12 | 91 |
| tb ATR 2.0/2.0, to21 (sym) | 5726 | 0.5099 | −0.009 | −0.303 | −0.1550 | +4.65 | 91 |
| tb ATR 2.0/1.0, to21 (tight) | 5726 | 0.4880 | −0.047 | −0.376 | −0.4149 | +4.20 | 91 |
| **tb ATR 4.0/2.0, to42 (wide,14d)** | 5726 | 0.5096 | +0.032 | +0.244 | **+0.0317** | +6.96 | 91 |
| fh N1 (8h) | 5726 | 0.5108 | +0.031 | −0.075 | −0.0708 | +1.12 | 91 |
| fh N3 (1d) | 5724 | 0.4996 | +0.020 | −0.198 | −0.1493 | +2.14 | 91 |
| fh N6 (2d) | 5721 | 0.4866 | +0.007 | −0.266 | −0.0856 | +3.12 | 91 |
| fh N9 (3d) | 5718 | 0.4947 | −0.017 | −0.392 | −0.2509 | +3.97 | 91 |
| **fh N21 (7d)** | 5706 | 0.5015 | −0.027 | +0.008 | **+0.0079** | +6.34 | 91 |
| **ts grid(5,8,13,21)** | 5722 | **0.5116** | −0.005 | +0.046 | **+0.0460** | +6.84 | 91 |
| ts grid(3,6,9) | 5724 | 0.4899 | −0.001 | −0.245 | −0.2535 | +4.27 | 91 |

**Reads:**
- **The CURRENT label is the quantitative root of the negative IS.** Its OOF dir_acc (0.4886) is below
  0.5 and its OOF econ is −0.24%/candle. The specialist is being asked to learn a target it gets wrong
  more often than right out-of-fold. A bagged ensemble of such a model lands at IS Sharpe ≈ 0 to
  negative — exactly the recurring BTC profile (iter-001 −0.28, iter-004 −0.17).
- **The "best" label barely clears the noise floor and only marginally.** The three configs with
  positive OOF econ — `tb 4.0/2.0/14d` (+0.032), `fh N21` (+0.008), `ts(5,8,13,21)` (+0.046) — are all
  a *fraction of one 0.1% fee*. The highest dir_acc anywhere is 0.5116. Score-IC never exceeds 0.032 in
  magnitude. There is no label horizon at which the prune features carry materially more signal.
- **The label ceilings are healthy (+4 to +7% oracle), but the model captures none of it.** The gap
  between `base_label_econ` (+5–7%) and `oof_econ` (≈0) is the whole story: the *labels* are tradeable
  with perfect foresight; the *features* cannot forecast their sign. This is a feature-signal problem
  that no relabeling can fix — relabeling changes the target, not the predictors.
- The FE's hint that funding IC strengthened 1-bar→3-bar does NOT carry over to label learnability:
  longer triple-barrier timeouts (to42/to63) and longer fixed horizons (N6/N9) do not lift dir_acc or
  econ above the to21 baseline in any economically meaningful way.

**Verdict on lever (1): the label is NOT the bottleneck. No label config is a credible iter-008 axis.**
The single least-bad config (`ts grid(5,8,13,21)`, OOF econ +0.046, dir_acc 0.5116) is within CV noise
of the current label and would, mapped through a K=20 bagged specialist net of honest costs, almost
certainly reproduce the noise-floor inversion. Screening it would burn a cadence slot to confirm a null
we can already predict — which the PRIME DIRECTIVE permits skipping ONLY because the experiment's
outcome is already resolved by this IS-only purged-CV evidence (it is a forbidden re-test of a
noise-floor target, not a live axis).

---

## 2. Investigation (2) — Regime-conditional IS edge

Single global purged-OOF prediction (the model the specialist approximates), partitioned by STATELESS,
PAST-ONLY regime variables (SMA-slope sign with `.shift(1)`; NATR/|ret| terciles via rolling-250
past-only quantiles with `.shift(1)`; ADX bands). `econ` = OOF realized PnL/candle in the model's
chosen direction, net fee.

### 2a. Bucket scan (`regime_conditional_edge.py`)

| partition / bucket | n (OOF) | dir_acc | **econ %/cand** | trades/mo |
|---|---|---|---|---|
| **BASE (ungated)** | 4568 | **0.4343** | **−0.1031** | — |
| TREND100 up | 2479 (54%) | 0.4647 | +0.1537 | 49 |
| TREND100 down | 2089 (46%) | 0.3983 | −0.4080 | 42 |
| TREND50 up | 2358 (52%) | 0.4245 | −0.3160 | 47 |
| TREND50 down | 2210 (48%) | 0.4448 | +0.1240 | 44 |
| VOL low | 1761 (39%) | 0.3964 | −0.3929 | 35 |
| VOL mid | 1334 (29%) | 0.4265 | −0.0327 | 27 |
| **VOL high** | 1473 (32%) | 0.4868 | **+0.1795** | 29 |
| ADX chop <20 | 1313 (29%) | 0.4151 | −0.3294 | 26 |
| ADX trend ≥25 | 2352 (52%) | 0.4422 | +0.0655 | 47 |
| \|ret\| calm/normal/turbulent | ~1500 each | ~0.42–0.45 | all negative | ~30 |

At face value four buckets show positive econ with ≥10 trades/mo. **But every bucket has dir_acc < 0.5**
— the model is anti-directional everywhere. A positive econ under dir_acc < 0.5 cannot come from the
model picking direction correctly; it must come from a return-sign asymmetry (drift) in the regime. The
forensic settles it.

### 2b. Forensic — is it model alpha or BTC beta? (`regime_edge_forensic.py`)

| gate bucket | n | dir_acc | **model econ** | **always-LONG** | always-SHORT | flip-model | verdict |
|---|---|---|---|---|---|---|---|
| **ungated** | 4568 | 0.434 | **−0.1031** | **+0.2164** | −0.4164 | −0.0969 | — |
| VOL high | 1473 | 0.487 | +0.1795 | **+0.4260** | −0.626 | −0.380 | beta, not alpha |
| TREND100 up | 2479 | 0.465 | +0.1537 | **+0.4569** | −0.657 | −0.354 | beta, not alpha |
| TREND50 down | 2210 | 0.445 | +0.1240 | **+0.2641** | −0.464 | −0.324 | beta, not alpha |
| ADX ≥25 | 2352 | 0.442 | +0.0655 | **+0.4036** | −0.604 | −0.266 | beta, not alpha |
| VOL high & TREND100 up | 793 | 0.520 | +0.4098 | **+0.7693** | −0.969 | −0.610 | beta, not alpha |

**Reads (decisive):**
- **In EVERY positive-econ regime, always-LONG beats the model — by 2–3×.** The model is not extracting
  a regime edge; it is *destroying* the natural long drift of the regime (it has dir_acc < 0.5, so it
  shorts winners). The "positive econ" is BTC's secular uptrend leaking through despite the model.
- **The ungated profile is the proof at the root:** model_econ −0.10 < flip-model −0.097 < always-LONG
  +0.22. The model's signal is anti-correlated with returns; even flipping it does not rescue it; the
  only thing that makes money is naive long exposure. This is a model with negative directional
  information content, not a regime-locatable edge.
- **Sub-period stability ([3]/[3b] in the script):** always-LONG is positive in essentially every
  chronological third of every bucket — confirming the positive econ is the 2021–2025 BTC uptrend, not
  a stable learned regime. The model's own per-third econ flips sign (e.g. ADX≥25: +0.88 / −0.45 / −0.35
  across thirds = 1/3 positive), i.e. its apparent "edge" is one bull-market third, not a regime
  property.

**Verdict on lever (2): there is NO regime in which the prune model has coherent positive alpha.** A
regime gate built on these buckets would be a long-biased beta filter: it would print a high OOS Sharpe
*iff* the OOS window also drifts up (it does — OOS is 2025-03→2026-06), reproducing the iter-001/004/005
inversion artifact (negative-IS-coherent / positive-OOS-on-drift) that the merge gate explicitly
refuses to reward. Gating to it manufactures the exact fragile profile we have spent seven iterations
learning to distrust. NOT a credible iter-008 axis.

---

## 3. Why this is ESCALATE, not a manufactured LABEL/REGIME pick

The task explicitly warns against manufacturing a weak pick to avoid ESCALATE. Three independent IS-only
axes now converge on the same conclusion:

| axis | best IS-only signal | floor (random) | source |
|---|---|---|---|
| **feature** (orthogonal non-OHLCV) | max \|IS-IC\| 0.057; every added feature bottom-third importance; prune-only OOF R² −0.095 | 0 IC, R²≈0 | FE iter-006 + diary-v1/005-007 (3 families NEGATIVE) |
| **label / horizon** | OOF dir_acc 0.5116, OOF econ +0.046%/cand (fraction of a fee) | 0.50, 0.0 | this brief §1 (13 configs) |
| **regime gate** | every positive-econ bucket = BTC beta; model dir_acc < 0.5 everywhere | always-LONG ≫ model | this brief §2 (5 partitions + forensic) |

The unifying root cause is **the prune model's out-of-fold directional accuracy is below 0.5 across the
entire IS window and across every label/regime cut.** The model has *negative* directional information
content on BTC 8h. You cannot relabel or gate your way out of a predictor that is anti-correlated with
the target — both levers only re-slice a signal that isn't there. This is not pessimism; it is three
orthogonal, purged-CV, IS-only measurements agreeing. Per the PRIME DIRECTIVE, this is a null we EARNED
across seven backtests + three IS analyses — not an axis declared dead to avoid work.

**BTC at 8h may simply be the wrong FIRST symbol.** The v1 redesign chose BTC as "the primary asset,"
but primacy by market cap is not primacy by *learnability*. BTC is the most efficient, most-arbitraged,
most-institutionally-covered crypto — the prior that an 8h OHLCV+funding LightGBM specialist finds
exploitable directional structure in BTC is weak precisely because everyone is already trading it. The
FE flagged this open question at iter-006 (§6 "BTC at max \|IS-IC\| 0.028 may be the wrong first
symbol"); the diary-v1/007 "Next" pre-registered the escalation path. Smaller-cap, higher-retail-flow,
less-efficient alts (the kind v2/v3 found tractable edges on) are a far stronger prior for a directional
specialist.

---

## RECOMMENDATION — ESCALATE (symbol pivot)

**Choice: ESCALATE to the user.** Neither the label lever nor the regime lever shows an IS-only signal
that could plausibly flip BTC to a coherent (both-positive) edge. The evidence is that BTC's prune model
is anti-directional out-of-fold (OOF dir_acc < 0.5 everywhere), so relabeling and regime-gating only
re-slice an absent signal.

**Specific escalation to the user (decision required):**

> The BTC 8h specialist has exhausted the three independent IS levers — feature (FE iter-006), label
> (iter-008 §1), and regime (iter-008 §2). All three confirm the prune model has OOF directional accuracy
> below 0.5 across the full IS window: it has negative directional information content on BTC. The current
> iter-001 baseline (IS −0.28 / OOS +0.64) is a beta-drift inversion, not an edge, and nothing we can do
> within this architecture flips it coherent. **We recommend pivoting the FIRST v1 symbol off BTCUSDT to a
> less-efficient, higher-retail-flow asset where a directional 8h specialist has a stronger prior.**
> Concretely: keep the entire v1 machinery (5-role flow, honest costs, K=5/20 cadence, prune+funding
> feature space, relative merge gate), re-point it at a new symbol, and bootstrap that symbol's baseline
> with a CONFIRMATION exactly as iter-001 did for BTC.

**Pre-screen to make the pivot fast and non-arbitrary (proposed iter-008 work, IS-only, pending user OK):**
Before committing a full CONFIRMATION on a new symbol, run the SAME `label_horizon_learnability.py` +
`regime_conditional_edge.py` + `regime_edge_forensic.py` triplet (parametrized by `SYMBOL`) on a
shortlist of candidate symbols and rank them by **ungated OOF dir_acc** and **model-econ-vs-always-LONG
gap** on the 41-col prune. Pick the symbol whose model has dir_acc clearly > 0.50 AND whose model_econ
beats always-LONG (i.e. genuine directional alpha, not beta) — the exact test BTC just failed. Candidate
shortlist (v1-eligible, NOT in `V1_EXCLUDED_SYMBOLS`; confirm eligibility with the Engineer before
fetching): LTCUSDT, DOTUSDT, LINKUSDT (the legacy v1 single-symbol models that historically carried
their own heads), plus 1-2 higher-flow alts. This converts "BTC is hard" into "here is the symbol with
the highest IS-only directional learnability," which is a data-driven first-symbol choice rather than a
guess.

**Pre-registered falsifier for the ESCALATE itself.** This ESCALATE is WRONG (and a LABEL/REGIME axis
should be reconsidered) if a reviewer shows EITHER:
1. a label config with OOF dir_acc ≥ 0.53 AND OOF econ ≥ +0.20%/candle (a clear, multi-fee, non-noise
   lift over the 0.4886/−0.24 baseline) — none exists in §1 (max 0.5116 / +0.046); OR
2. a stateless regime bucket where **model_econ > always-LONG_econ** (genuine alpha, not beta) with
   ≥10 trades/mo — none exists in §2 (always-LONG beats the model in every positive bucket).
If neither can be produced, ESCALATE stands.

**What I am NOT recommending, and why:** I deliberately did not pick `ts grid(5,8,13,21)` (the least-bad
label) or the `VOL high & TREND100 up` gate (the highest-econ regime) as a token axis. Both are
predictable nulls: the trend-scan label's +0.046 OOF econ is within CV noise of the current label and
would reproduce the inversion at K=20 net of costs; the VOL-high&uptrend gate is a 2× beta bet
(always-LONG +0.77 vs model +0.41) that would print a fragile high-OOS/negative-IS profile — the exact
artifact the merge gate rejects. Screening either would burn a cadence slot to confirm a null this
IS-only evidence already resolves.

---

### Appendix — methodology / OOS-vigilance attestation
- All three scripts hard-filter `open_time < OOS_CUTOFF_MS` and assert `df["open_time"].max() <
  OOS_CUTOFF_MS` before any computation; `df_full` is used ONLY to produce the IS slice. OOS rows
  (open_time ≥ cutoff) are never read.
- Forward labels (TB, fixed-horizon, trend-scan) are built on the IS slice only; the forward reach at the
  IS tail NaN-masks because there is no OOS candle in the frame to index into — no peeking.
- Regime variables are stateless & past-only: SMA-slope sign uses `.shift(1)`; NATR/|ret| tercile
  thresholds use rolling-250 quantiles with `.shift(1)`; ADX/NATR are already past-only indicators.
- Labeling logic verified line-by-line against `src/crypto_trade/strategies/ml/labeling.py` (TB first-hit
  rule, fixed_horizon sign, trend_scanning OLS max-|t|) and the runner's ATR convention
  (`close × vol_natr_21 / 100`, `lgbm.py:758`) + 0.1% label fee. `src/` and the runner are UNMODIFIED.
- Scripts re-runnable; lint clean (`ruff check`, ignoring idiomatic `X` design-matrix naming).
