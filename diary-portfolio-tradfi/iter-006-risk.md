# iter-006 RISK NOTE — Momentum-crash brake (fast-sleeve crash gate)

**Date:** 2026-07-01 · **Track:** portfolio-tradfi · **Role:** Risk Engineer
**Cadence:** EXPLORATION (IS-only, `< OOS_CUTOFF 2025-03-24`; **OOS HIDDEN** — no `--confirm`)
**Working best entering iter-006:** iter-005 multi-horizon (net **+0.20** / gross +0.40 / maxDD −31% / bull +0.38 / **bear −0.90** / chop +0.26, 2/3).
**Source of truth (every number below):** `analysis/portfolio/tradfi/iter_006_crashbrake.py` (IS-only). Reproduce: `uv run python analysis/portfolio/tradfi/iter_006_crashbrake.py`.

---

## 1. The ONE change — a leak-safe, theory-pinned crash gate

In a past-only **market bear state**, collapse the iter-005 blend to the bear-robust 12-1m sleeve:

```
mkt[t] = cumprod(mean cross-sectional close.pct_change)        # EW-universe index, past-only
g[t]   = 1 if mkt[t]/mkt[t-252]-1 < 0  else 0                  # market 12m return < 0 (bear state)
raw[t] = (1 - g[t]) * EW{3-1,6-1,12-1}[t]  +  g[t] * sleeve(252)[t]
net,w  = i3.banded_net(raw, ret_fwd, delta=0.005)             # iter-003 band + core vol-target UNCHANGED
```

The three sleeves, the band (δ=0.005), `net_from_raw`'s 63d vol-target / taker-cost model and the
OOS-hidden accounting are all UNCHANGED. Only the per-bar **blend** becomes state-dependent.

## 2. Why a composition gate and NOT a vol/drawdown overlay (empirical rejection, IS-only)

iter-005's net0 is **already 63d vol-targeted**, so its realised vol barely differs by regime
(bull ~15% / bear ~17% / chop ~14% ann). The two textbook crash brakes therefore FAIL here:

| candidate (IS-calibrated) | effect on net | effect on bear |
|---|---|---|
| **Barroso constant-vol** k=min(1, σ_tgt/rv_W.shift1), W∈{21,30,42}, q∈{.5,.6,.7} | +0.20 → +0.13..+0.18 (washes) | −0.90 → **−0.94..−1.10 (worse)** |
| **Drawdown brake** (metals iter-007 hysteresis, worst-quintile D_trip) | +0.20 → +0.11..+0.21 | −0.90 → **−1.04..−1.12 (worse)** |

Both scale all three sleeves **uniformly**, so they cannot exploit the one fixable fact — the SLOW
sleeve **survives** the bear (standalone IS bear: 12-1m **−0.08**, 6-1m −0.80, 3-1m −1.23). The bear
is a **composition** problem (too much fast sleeve), not an exposure-level one. (Metals' lesson —
uniform scaling washes / level-taper pins the bull — is exactly why these fail.)

## 3. Pre-registered thresholds (IS-calibrated; NOTHING curve-fit)

- **Gate horizon = 252 d (12 months).** PINNED to the 12-1m sleeve's own long leg AND to the crash
  book `sleeve(252)` — one theory-fixed horizon, no free window. "12m trailing return < 0" is the
  canonical TSMOM / Daniel-Moskowitz bear-state (Moskowitz-Ooi-Pedersen 2012). Threshold = sign(0).
- **Crash book = `sleeve(252)` (12-1m only)** — the bear-robust horizon (faster momentum crashes
  harder; the slow sleeve is the bear survivor).
- **δ = 0.005** inherited from iter-003, NOT re-tuned.
- **Anti-overfit:** ret252 is the **most conservative** of four candidate gates (lowest net). I did
  NOT pick the max-net cell.

  | gate (12-1m crash book) | net | bull | bear | chop |
  |---|---|---|---|---|
  | **ret252<0 (CHOSEN, pinned)** | **+0.31** | +0.42 | −0.54 | +0.26 |
  | ret200<0 | +0.45 | +0.54 | −0.44 | +0.50 |
  | ret126<0 | +0.42 | +0.52 | −0.53 | +0.47 |
  | price<MA200 | +0.46 | +0.55 | −0.37 | +0.38 |

  All four IS-positive and 2/3 → broad basin, not knife-edge.

## 4. Simulated historical effect — BEAR specifically

| metric | iter-005 | **iter-006** | Δ |
|---|---|---|---|
| net Sharpe | +0.20 | **+0.31** | +0.11 (clears +0.30) |
| gross Sharpe | +0.40 | **+0.51** | +0.11 |
| maxDD (IS) | −31.4% | **−29.9%** | better |
| bull / **bear** / chop | +0.38 / **−0.90** / +0.26 | +0.42 / **−0.54** / +0.26 | bear +0.36, bull+chop preserved |
| turnover/day | 0.1144 | 0.1089 | **−5%** (swaps composition, no churn) |
| regimes positive | 2/3 | 2/3 | held |

**Gate firing (IS): bull 1.2% · bear 79.2% · chop 90.5%** — surgical: the bull book is essentially
untouched, the gate engages in the bear/post-bear-chop.

**Bear sub-window decomposition** (the honest picture):
- **2022 grind (the NAMED target, 10mo):** Sh **−0.73/−11% → −0.01/−1%** — the momentum crash is fixed.
- **COVID V-crash (2mo):** Sh −1.94/−4% → **−5.85/−6% (WORSE)** — a 12m-trend gate lags a 2-month
  V-crash and fires near the bottom, concentrating into the slow sleeve right as the market
  V-reverses. This is the **pre-registered cost**: the brake targets the SUSTAINED momentum crash,
  not V-crashes. The aggregate-bear residual (−0.54, not ~−0.3) is entirely this COVID drag.

## 5. Leak safety (HARD rule)

- `g[t]` is the freshest bear-state at close[t], aligned with the close[t]-decided sleeves; `banded_net`
  applies the single `.shift(1)` execution lag. `net[t]` reads only `held[t-1]` → independent of
  `close[t]` (same-bar safe) and of any future bar.
- **Future-bar leak self-check PASS** (corrupt panel+returns after a cutoff → braked net + lagged book
  bit-identical pre-cut). 6 new tests green (identity g=0→iter-005, g=1→12-1m sleeve, future-bar
  no-leak, gate past-only, sector-neutral). Suite **36 passed, 2 skipped**.
- **OOS HIDDEN**: 0 `OOS_Sharpe` in default output; `--confirm` never passed.

## 6. Verdict & handoff

**KEEP** by the task's literal test — fixes the 2022 momentum crash (−0.73→−0.01), preserves bull
(+0.42) and chop (+0.26), lifts net past +0.30 (+0.31), improves maxDD, adds no churn. Did NOT kill
bull or wash net (the metals failure mode). **Clears the +0.30 promote bar** — a candidate baseline.

**For Quant Research:** the one open cost is the COVID V-crash worsening, which a trend gate cannot
help. If the COVID 2-month tail matters for the merge, a natural future-iter complement is a *fast*
V-crash overlay (e.g. a short-window reactive de-lever) orthogonal to this *slow* trend gate — NOT a
re-tune of the 252 window (which is pinned). QR may adopt ret252 (pinned/conservative) or, if the
COVID cost is acceptable, note that ret200/ret126/MA200 score higher net but are less theory-anchored.
Recommend QR validate across seeds at CONFIRMATION (the gate is deterministic, so seed-stable).
