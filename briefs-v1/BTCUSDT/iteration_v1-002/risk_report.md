# Risk Report — iter-v1/002 EXPLORATION (BTCUSDT)

**Role:** Risk Engineer (Phase 4.7). **Mode:** EXPLORATION (bagging K=3).
**Symbol:** BTCUSDT (single-symbol v1). **Anchor baseline:** iter-v1/001
`BASELINE_V1_BTCUSDT` — IS Sharpe **−0.2793** / OOS **+0.6401**, 201/95 trades,
IS MaxDD **22.14%** / OOS 13.57%, WR 39.3%/44.2%, net of fees+slippage.

All numbers below are **IS-only** — derived strictly from trades with
`close_time < OOS_CUTOFF_MS` (2025-03-24), via the committed script
`analysis/BTCUSDT/iteration_v1-002/risk_is_analysis.py`. No OOS data was read.
Everything here is **pre-registered before the Phase-6 backtest runs.**

> **Positioning (read first).** The iteration's PRIMARY axis is the Feature
> Engineer's pruned feature set. This risk config is a **SUPPORTING,
> conservatively-calibrated single brake** applied alongside it. It is chosen
> specifically to be *state-discontinuous, explainable, and minimally
> confounding* to the feature read (it scales position size in deep-drawdown
> pockets; it does **not** suppress entries, so it cannot mask a feature effect
> by changing which candles trade). I deliberately reject the louder knobs
> (R1 cooldown, NATR kill) below — the IS data does not support them and they
> would confound the read.

---

## 1. Risk-primitive settings + IS justification + simulated effect

### 1.1 Where the IS losses live (the diagnosis)

IS roster = 200 closed trades, 2022-01-01 .. 2025-02-24. IS net PnL −29.27%
(unweighted) / −16.12% (weighted). The loss is **entirely a stop-loss story**:

| exit_reason | trades | net PnL % | avg % | win rate |
|---|---|---|---|---|
| stop_loss | 109 (54.5%) | **−361.72** | −3.32 | 0% |
| take_profit | 46 | +273.02 | +5.94 | 100% |
| timeout | 45 | +59.43 | +1.32 | 71% |

SLs alone subtract 361.7 points; TPs+timeouts add back 332.5. The edge is thin
and the loss control is the lever.

**Drawdown is a slow grind, not a single catastrophe.** Running cumulative
weighted PnL bottoms at **−22.14** (matches the headline IS MaxDD) late-2024.
Decomposing trades by the drawdown depth at entry:

| DD-at-entry band | trades | net PnL % |
|---|---|---|
| [0, 5%) — shallow | 72 | **+53.91** |
| [5, 10%) — bleed | 72 | **−51.41** |
| [10, 15%) | 6 | −17.90 |
| [15%+, deep tail] | 50 | −13.86 |

The profit is concentrated in shallow-drawdown trades; the bleed concentrates
in the 5–10% drawdown band and the deep tail. **A drawdown-conditioned brake
that scales DOWN exposure once we are >~8% below peak targets exactly the
loss-bearing region while leaving the profitable shallow region least affected.**

**Vol structure is bimodal (this rules out a NATR kill — see §1.3).** Splitting
IS entries by `vol_natr_14` (past-only, known at signal time) into terciles:

| NATR bucket | trades | net PnL % | avg % | win rate | SL rate |
|---|---|---|---|---|---|
| low (≤1.88) | 67 | −16.84 | −0.25 | 34.3% | **62.7%** |
| mid (≤2.35) | 66 | **+10.84** | +0.16 | 39.4% | 50.0% |
| high (>2.35) | 67 | **−23.27** | −0.35 | 43.3% | 50.7% |

Losses sit in BOTH the low-NATR (highest SL rate) and high-NATR (worst PnL)
tails; only the mid bucket is profitable. There is **no clean NATR threshold**
that isolates the losers.

**Consecutive-SL streaks exist but the post-streak bounce is POSITIVE** (this
rules out an R1 cooldown — see §1.2). SL-run-length histogram: runs of 6 (×2)
and 7 (×1) exist; longest streak = 7. But trades **entered after ≥3 consecutive
prior SLs** number 23 with net PnL **+10.96** (WR 43.5%) — the recovery window
is where winners cluster, not where the bleed continues.

### 1.2 REJECTED: R1 consecutive-SL cooldown

The runner pre-wires `risk_consecutive_sl_limit=3 / _cooldown_candles=27`. I
**reject** it for BTC. Replaying the IS roster, R1(K=3, C=18) would arm a
cooldown after each 3-SL streak and suppress entries in the recovery window.
Of the 16 entries it suppresses: **8 are take-profits (+46.0), only 5 are SLs
(−17.5)** → it removes a *net +28.5* of IS PnL. R1(3,27) is the same picture
(8 TP / 9 SL suppressed, removes +15.3 net). The post-3-SL bounce on BTC IS is
profitable; a streak cooldown amputates it. **R1 stays OFF.**

### 1.3 REJECTED: R5 NATR binary kill / vol-target tuning

The NATR kill (`risk_r5_kill_low_natr_enabled`) skips entries below a NATR
floor. The IS shows the low-NATR bucket has the worst SL rate (62.7%) BUT also
near-zero net contribution, and the *worst PnL* bucket is high-NATR — losses are
**bimodal in vol**, so no single NATR floor cleanly removes the losers without
also removing the mid-bucket winners. A NATR kill would also *change which
candles trade*, directly confounding the feature read. **R5 NATR kill stays
OFF; R5 vol-target stays at the baseline (enabled, vt_target_vol 0.3) — no
change**, so the feature axis is read against the same R5/VT context as /001.

### 1.4 PROPOSED (the one brake): R2 drawdown-triggered position scaling

State-discontinuous, explainable, **does not suppress entries** (trade count
unchanged → minimal confound of the feature read). Mechanics (`backtest.py`
L406–411, scaling in the vt pipeline): when cumulative weighted PnL sits more
than `trigger_pct` below its running peak, scale new-trade `weight_factor`
linearly from 1.0 (at the trigger) down to `floor` (at `anchor_pct` DD).

**Pre-registered setting (primary):**

```
risk_drawdown_scale_enabled  = True
risk_drawdown_trigger_pct    = 8.0
risk_drawdown_scale_floor    = 0.5
risk_drawdown_scale_anchor_pct = 18.0
```

**Simulated IS effect** (within-roster size scaling; trade count = 200,
unchanged):

| config | IS MaxDD (wPnL) | Δ MaxDD | IS net wPnL | trades scaled | mean scale |
|---|---|---|---|---|---|
| baseline /001 (R2 off) | −22.14 | — | −16.12 | 0 | 1.00 |
| **R2 (8 / 0.5 / 18)** | **−17.63** | **−20% (≈4.5 pts)** | −19.58 | 188 | 0.73 |
| R2 (10 / 0.5 / 20) — gentler alt | −17.44 | −21% | −20.23 | 172 | 0.69 |
| R2 (10 / 0.5 / 25) — gentlest alt | −20.85 | −6% | −19.82 | 118 | 0.89 |
| R2 (5 / 0.33 / 12) — aggressive | −12.74 | −42% | −15.51 | 198 | 0.39 |

**Expected effect, stated honestly:**
- **IS MaxDD: −20% (≈4.5 points), the primary objective.** This is the loss
  control the negative-IS baseline needs.
- **IS net PnL: roughly flat-to-slightly-worse magnitude.** Because BTC's IS
  cumulative PnL is in drawdown nearly the whole window, de-risking shrinks the
  small recoveries as well as the bleed — so on a net-*negative* IS series the
  PnL magnitude barely moves while the path gets smoother. This is expected and
  acceptable: the deliverable is **MaxDD/Sharpe-stability**, not IS PnL, and the
  real prize (the FE pruned features) is what should move IS PnL.
- **IS Sharpe:** directionally up (smoother equity path, lower DD); magnitude is
  for the Phase-6 backtest to confirm.
- **OOS:** untouched and untuned. On the /001 OOS (MaxDD already a benign 13.6%,
  positive Sharpe) an 8%-trigger brake fires rarely, so OOS should be ~unchanged
  — exactly what a supporting brake should do (protect the bad tail, stay out of
  the way otherwise).

**Why floor=0.5 (not 0.33):** 0.5 keeps the strategy meaningfully invested
during drawdown so the profitable post-drawdown recoveries (the bounce winners
identified in §1.1/§1.2) are not over-suppressed; 0.33 over-de-risks a thin edge.

> **Sequential-cascade caveat (NO-CHEATING rule).** These are *directional*
> within-roster estimates. R2 scales size, not entry timing, so it cascades far
> less than an entry filter — but it still alters the cumulative-PnL trajectory,
> which feeds back into the trigger. **Only the Phase-6 backtest is the verdict.**
> I am NOT projecting a Sharpe number; I am pre-registering a brake whose
> *direction* (lower MaxDD, ~flat trade count) is robust.

**Fallback for QR:** if the feature read is the overriding concern and even a
size-scaling brake feels confounding, the gentlest variant **R2 (10 / 0.5 / 25)**
(only 118/200 scaled, mean 0.89) is the minimum-footprint option; it still
removes ~6% of MaxDD. I default to the (8/0.5/18) primary because the −20%
MaxDD reduction is the point.

---

## 2. Fractional-Kelly sizing note

From the IS roster (net of costs):

| quantity | IS value |
|---|---|
| win rate p | 0.390 |
| avg win (net %) | +4.42 |
| avg loss (net %, abs) | 3.07 |
| payoff ratio b | 1.442 |
| per-trade mean μ | **−0.146** |
| per-trade variance | 16.95 |
| per-trade std | 4.12 |
| classic Kelly f\* = (bp−q)/b | **−0.033** |
| continuous Kelly μ/σ² | **−0.009** |

**The IS edge is NEGATIVE (μ < 0), so full Kelly is ≤ 0.** Any fractional Kelly
(¼ or ½) of a non-positive f\* is ≤ 0 → the IS-honest sizing recommendation is
**do not lever up; size at or below the current baseline.**

Concretely: **keep `weight_factor`/`max_amount_usd` at baseline** — do NOT raise
them. The current VT/R5 pipeline already scales most trades to ~0.33
(`weight_factor` 0.33 on 187/201 /001 trades); that is consistent with a
sub-unity Kelly posture and should be preserved. The proposed R2 brake only
ever *reduces* size in drawdown — fully consistent with a conservative,
sub-Kelly stance. **No sizing-up. Pre-registered: `max_amount_usd=1000`,
`vt_*` unchanged from /001.** (Kelly is computed on the /001 IS edge; once the
FE features lift the IS edge positive, a future iteration can revisit a true
¼–½ Kelly target — but not on a negative-edge IS window.)

---

## 3. Stress matrix (proposed config, IS-only)

Rows = scenarios; cols = the IS quantities that matter for a loss brake. All
figures are IS-only and describe the **proposed R2 (8/0.5/18)** config's posture
versus the /001 baseline.

| Scenario | Definition (IS) | trades | net PnL % | WR | SL rate | R2 posture |
|---|---|---|---|---|---|---|
| **Vol-spike replay** | top-20% NATR entries (NATR ≥ 2.75) | 40 | −10.87 | 47.5% | 45.0% | R2 brakes here only if also in DD; mean scale on high-NATR ≈ 0.80 (incidental, not targeted) |
| **Calm replay** | bottom-80% NATR entries | 160 | −18.40 | 36.9% | 56.9% | majority of the bleed is here; R2 brakes the DD-pocket subset |
| **Regime: low-NATR tercile** | NATR ≤ 1.88 | 67 | −16.84 | 34.3% | **62.7%** | not killed (NATR-kill rejected); braked only via DD |
| **Regime: mid-NATR tercile** | 1.88–2.35 | 66 | **+10.84** | 39.4% | 50.0% | the only profitable regime — preserved (floor 0.5 keeps it invested) |
| **Regime: high-NATR tercile** | NATR > 2.35 | 67 | −23.27 | 43.3% | 50.7% | worst PnL; braked when it coincides with DD |
| **Tail-loss: worst trade** | min single net_pnl_pct | 1 | **−10.15** (SL, long, 2022-06-18) | — | — | gap-through-stop; R2 caps size, does NOT cap per-trade loss depth — see note |
| **Tail-loss: worst day** | min daily PnL | — | **−4.63** (2022-01-10) | — | — | clustered in 2022-Q1; R2 reduces size as the streak deepens |
| **Tail percentiles** | p5 / p1 per-trade net | — | −4.79 / −5.68 | — | — | bounded by SL except gap-throughs |

**Worst-month clustering (IS):** the six worst IS months sum to −67.6 (vs total
−29.3): 2024-02 (−14.1), 2022-01 (−13.1), 2023-01 (−12.5), 2022-07 (−10.8),
2024-10 (−8.7), 2024-06 (−8.5). These are exactly the deep-drawdown pockets R2
is designed to de-risk into.

**Tail-loss note:** the worst single IS trade is −10.15% even though the ATR-SL
sits at ~1.45×ATR — this is a **gap-through-stop** (entry candle gapped past the
stop, filled at a worse price). R2 bounds the *aggregate* drawdown by shrinking
size, but it cannot bound a single-trade gap below the stop. That residual is
inherent to a stop-based system on 8h candles and is the same in /001; it is not
made worse by R2. If a future iteration wants per-trade tail control, that is a
separate axis (e.g. max-position-loss cap), not this brake.

---

## 4. OOD flags

R3 (OOD Mahalanobis) is **not a `BacktestConfig` field** — it is recomputed at
training time from each per-month model's training-window stats (cutoff
`OOS_CUTOFF` is respected by the walk-forward train_end). It stays **ON at the
baseline `ood_cutoff_pct=0.70`, unchanged.** I do not modify it (no IS tuning of
an OOD knob this iteration). On the IS roster I checked PnL is **not** concentrated
in a single vol pocket — the bleed is spread across both the low- and high-NATR
tails and across six different calendar months, so there is no single OOD pocket
carrying the result. No OOD red flag for this config.

---

## 5. Pre-registered slippage cost-stress assumption

**The candidate is pre-registered to be judged at `--slippage-bps 2`** (2.0
bps/side, 0.04% round-trip — the v1 default and backtest-live parity setting).

**Cost-stress sweep (pre-registered, the Engineer runs these in Phase 6):**
re-run the candidate at `--slippage-bps` ∈ {**1, 2, 4**} (i.e. 1× / 2× / 4× the
round-trip drag) and report IS+OOS Sharpe / MaxDD / trade-count at each. Edge
decay acceptance: the IS MaxDD reduction from R2 should **persist (monotone, no
sign flip) across all three** — a loss brake that only helps at one slippage
level is not robust. The merge will be judged at the **2 bps** assumption; the
{1×, 4×} runs are robustness context, not the merge bar.

Per-trade arithmetic for intuition: at 4 bps/side the round-trip slippage is
0.08% vs 0.04% at 2 bps — an extra ~0.04% drag on each of ~200 IS trades ≈ −8
points of gross IS PnL added on top of the existing −29.3. The edge is thin, so
the 4× run is the real cost-robustness test; R2 (which cuts losers' size in DD)
should *help* relatively more as costs rise.

---

## 6. Exact proposed `BacktestConfig` risk kwargs (handoff to QR)

```python
# iter-v1/002 — Risk Engineer pre-registered (IS-only, BTCUSDT, EXPLORATION K=3)
# SINGLE brake: R2 drawdown-triggered position scaling. Everything else = /001 baseline.

risk_drawdown_scale_enabled    = True    # CHANGED from baseline (was False)
risk_drawdown_trigger_pct      = 8.0     # brake once >8% below peak (preserves shallow-DD profit zone)
risk_drawdown_scale_floor      = 0.5     # min size in deep DD (keeps thin edge invested for the bounce)
risk_drawdown_scale_anchor_pct = 18.0    # floor reached at 18% DD

# UNCHANGED from /001 baseline (do NOT touch — keep the feature read clean):
risk_consecutive_sl_limit              = None   # R1 OFF  (post-streak bounce is +; cooldown amputates it)
risk_consecutive_sl_cooldown_candles   = 0
risk_r5_vol_target_enabled             = True   # R5 vol-target ON, vt_target_vol 0.3 (baseline)
risk_r5_kill_low_natr_enabled          = False  # NATR kill OFF (losses bimodal in vol; no clean floor)
vol_targeting                          = True   # vt_* unchanged: target_vol 0.3, lookback 45, min 0.33, max 2.0
vol_ceiling_enabled                    = False  # unchanged
max_amount_usd                         = 1000.0 # unchanged (negative IS edge → Kelly ≤ 0 → no sizing-up)
# R3 OOD: ON at ood_cutoff_pct=0.70 (training-time, not a BacktestConfig field) — unchanged.
```

**QR fallback option (documented):** if minimizing confound of the feature read
is paramount, substitute the gentlest variant
`trigger=10.0 / floor=0.5 / anchor=25.0` (118/200 scaled, mean 0.89, ~6% MaxDD
cut). QR may adopt, modify, or reject — rationale above.

---

### Provenance
- Script: `analysis/BTCUSDT/iteration_v1-002/risk_is_analysis.py` (IS-only;
  merges `vol_natr_14` via trade `open_time` = signal-candle `close_time`).
- Inputs: `reports-v1/BTCUSDT/iteration_v1-001/in_sample/{trades.csv,daily_pnl.csv}`,
  `data/features/BTCUSDT_8h_features.parquet`.
- Constants: `OOS_CUTOFF_MS=1742774400000` (2025-03-24), 8h cadence (3 candles/day).
