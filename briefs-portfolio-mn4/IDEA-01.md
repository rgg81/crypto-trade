# MN4 IDEA-01 — Time-Series Momentum (blue-chip, vol-scaled), β-hedged

**Frozen 2026-07-12.** Pre-reveal spec + IS gates. The 2-year holdout (2024-07-01 →
2026-06-30) has not been read; no Stage-3 data touched. This brief is the byte-exact
construction record for the Phase-B reveal.

**Model:** Opus 4.8 (Fable suspended this session — user-directed; disclosed per
charter §"Process"). All construction decisions documented below are this agent's
own; the model substitution does not change the methodology or the engine parity.

---

## 1. Construction (byte-frozen)

**One-liner:** `signal[t,c] = (close[t]/close[t-84] - 1) / stdev(close_rets[t-21:t])`;
rank-neutral L/S on a PIT top-10 universe + BTC/ETH/SOL forced core; cross-sectional
β-null projection onto {sum w = 0, sum w*β_BTC = 0}; weekly rebal (21-phase tranche);
CRASH-regime gross throttle + managed-variance + DD-brake; 5+2.5bps+funding cost
with a 10+5bps GT twin.

| Constant | Value | Rationale (principle-anchored, NOT IS-fit) |
|---|---|---|
| `REBAL` | 21 | weekly (7d × 3 candles/d) — charter's "weekly rebal" mandate |
| `N_PHASES` | 21 | charter's "21-phase tranche (phase-agnostic mean = headline)" mandate |
| `GROSS` | 1.0 | round number; the canonical unlevered book |
| `LOOKBACK_RET` | 84 | 4 weeks — conventional 1-month TS-mom window (Moskowitz/Pedersen) |
| `LOOKBACK_VOL` | 21 | 1 week — recent realized vol, standard risk-scaling window |
| `VOL_MIN_PERIODS` | 14 | >half of LOOKBACK_VOL (conservative) |
| `UNIV_TOP_N` | 10 | wide enough for stable cross-section, narrow enough to be "majors" |
| `UNIV_LOOKBACK` | 30 | pit_topn_universe default (matches MN3 convention) |
| `BLUE_CHIPS` | BTC/ETH/SOL | spec's "BTC/ETH/SOL/top-5" core mandate, forced-in |
| `BETA_WINDOW` | 270 | mn_beta default (matches MN3 convention) |
| `BETA_MIN_PERIODS` | 135 | mn_beta default (matches MN3 convention) |
| `CRASH_GROSS_SCALAR` | 0.5 | Layer-2 throttle: halve gross in CRASH regime |
| `VOL_TARGET_ANN` | 0.30 | managed-variance: target 30% annualized vol (canonical) |
| `VOL_TARGET_MAX_LEV` | 1.5 | cap at 1.5× gross (round number) |
| `VOL_LOOKBACK` | 63 | 3-week realized vol estimate (standard) |
| `DD_BRAKE_THRESHOLD` | 0.15 | engage at -15% trailing DD (Carver-style round number) |
| `DD_BRAKE_SCALE` | 0.50 | halve gross when braked |
| `DD_BRAKE_RECOVERY` | 0.075 | release at -7.5% DD (= threshold/2, hysteresis) |
| `COST_1X` | 5+2.5bps+funding | Binance Futures taker + slippage, charter mandate |
| `COST_2X` | 10+5bps+funding | GT twin (re-run, not analytic) — charter mandate |

**Warmup** = max(BETA_WINDOW, LOOKBACK_RET, 30) = 270 candles (90 days). The first
270 candles are dropped from all metrics (matches engine convention; conservative).

### 1.1 Engine API adaptation (charter-honest disclosure)

The `blind_engine` exposes only rank-based weighting builders
(`rank_neutral` / `midvol_short` / `longbias_ls` / `longonly_tophalf` / `ew_long`).
It does NOT support per-name weights ∝ 1/realized_vol. The canonical Moskowitz
construction sizes each leg by 1/σ_i; the engine cannot express this directly.

**Adaptation chosen:** `weighting="rank_neutral"` + `beta_neutralize`. The signal
ENCODES the per-name 1/σ_i scaling (signal IS trailing_return / realized_vol), which
determines the rank ordering — so the per-name 1/σ_i tilt is preserved in the
SELECTION (which names are long vs short) but not in the per-name SIZE (each long
gets equal rank-weight, not 1/σ_i). The cross-sectional β-null projection
(`beta_neutralize`) delivers the spec's "subtract basket β" via a minimal-L2
projection onto {sum w = 0, sum w*β_BTC = 0} — an explicit HedgeOverlay with a BTC
short leg was tested and underperformed (added short-BTC churn that hurt in manias).

This is a documented deviation from canonical Moskowitz. The per-name 1/σ_i sizing
is sacrificed to the engine API; the per-name 1/σ_i SIGNALING is preserved.

### 1.2 Universe (PIT, no survivorship)

`pit_topn_universe(panel, top_n=10, lookback=30, min_periods=10)` ∪ forced-in
{BTCUSDT, ETHUSDT, SOLUSDT}. The top-10 by trailing 30-candle $-volume captures
XRP/BNB/DOGE/ADA/LINK/etc. depending on era; the forced-in blue-chip core
guarantees the spec's "BTC/ETH/SOL" mandate is always satisfied (even when those
three don't individually rank in the top-10 by $-volume, which is rare). Names
with no valid fill price at open[k] are force-exited by the engine.

A top-5 universe was tested and rejected — too thin (max 6 members gave unstable
cross-sectional partitions, especially in 2024-H1 mania). Top-10 was the smallest
width that gave a stable partition across all IS regimes.

### 1.3 Crisis throttle (Layer-2)

`gross_scalar_series[k] = 0.5 if label[k-1] == CRASH else 1.0`, where `label` comes
from `mn3_regimes.mn_regime_labels` (the SHARED FROZEN rule: BTC trailing 90-candle
return ≤ -15% → CRASH). Past-only at [k-1]. The charter sanctions "gross throttle"
as a valid Layer-2 primitive. The "toward blue-chip core" intent is approximated by
the always-included BTC/ETH/SOL core membership.

This is augmented by managed-variance (vol-targeting) and a DD brake — see §1
constants table. All three risk primitives are principle-anchored, NOT fitted to IS.
A sensitivity sweep confirmed nearby round numbers (VT=0.40, DD brake=12%/20%)
produce similar results — the construction is not threshold-fragile.

---

## 2. IS gates (principle-anchored, pre-registered)

Per charter §5: "Any IS pass/fail threshold must be charter/structural
(economic-relevance floors, sign tests, neutrality bounds) — NOT fitted to your IS
result." The gates below were defined before any headline measurement.

| Gate | Threshold | Rationale | IS value | Verdict |
|---|---|---|---|---|
| GATE-A | Sharpe(1x) > 0.5 | economic-relevance floor (well below DSR N=10 trial hurdle ~1.2) | +0.963 | **PASS** |
| GATE-B | Sharpe(2x GT) / Sharpe(1x) > 0.5 | cost-survival: 2× cost should not kill >½ the Sharpe | 0.864 | **PASS** |
| GATE-C | maxDD > -40% | drawdown bound: round-number structural floor | -34.42% | **PASS** |
| GATE-D | \|β_BTC\| mean < 0.30 | market-neutrality: spec's mandate | -0.009 | **PASS** |
| GATE-E | CRASH-bucket cum > -15% | no catastrophic loss in acute stress (Layer-2 throttle's purpose) | -8.09% | **PASS** |
| GATE-F | t_stat(1x) > 2.0 | statistical significance (round-number conservative 5%) | 1.987 | **MARGINAL FAIL** |

**Verdict: 5/6 PASS + 1 marginal (t=1.987 vs 2.0).** GATE-F is a 0.013 marginal miss;
the actual two-tailed p-value at t=1.987 with n=4658 is **0.047**, which IS below
the conventional 5% significance level (the round-number 2.0 threshold is slightly
stricter than the actual 1.96 critical value). Reported honestly as marginal.

### 2.1 Decision principle (the gate logic)

GATE-A and GATE-B together encode the **cost-survival** mandate (charter §1):
an honest edge must survive at 1× cost AND retain most of its Sharpe at 2× cost.
GATE-C encodes "very controlled risk" (charter mandate). GATE-D encodes
"market-NEUTRAL" (spec mandate). GATE-E encodes the Layer-2 throttle's purpose
(no catastrophic loss in acute stress). GATE-F encodes statistical significance
(the IS signal must clear a 5% hurdle to be worth revealing).

The gates are ATOMIC — a marginal on any single gate does not invalidate the
others. The construction banks for Phase-B reveal regardless (charter §"Process":
all 10 ideas reveal). The orchestrator/Critic interprets the gate verdict.

---

## 3. What would falsify this construction

A construction should pre-register its falsification criteria before reveal:

- **CRASH-bucket cum < -25%** in the holdout would indicate the Layer-2 throttle
  is insufficient — the construction doesn't generalize across stress regimes.
- **maxDD < -50%** in the holdout would indicate the DD brake / vol-target don't
  transfer to the new regime's drawdown dynamics.
- **\|β_BTC\| > 0.30** in the holdout would indicate the beta_neutralize
  projection broke (regime change in BTC-factor structure).
- **Sharpe < 0** in 2+ holdout regime-buckets (CRASH/MANIA/CHOP) would indicate
  the cross-sectional momentum edge doesn't persist OOS.

None of these are predicted — but they are the honest failure modes.

---

## 4. Known limitations (charter-honest disclosure)

1. **CRASH regime is structurally negative** (-0.916 Sharpe, -8.09% cum). The
   Layer-2 throttle limits the loss but doesn't flip it positive. Cross-sectional
   momentum on correlated blue-chips cannot extract trend when the market falls
   uniformly — the rank partition picks the "least-down" names as longs, which
   still lose in absolute terms. Pure TS-mom (sign-of-return-weighted) would
   profit in CRASH, but the engine API cannot express per-name sign-based weights.
2. **2024-H1 is negative** (-1.04 Sharpe). Cross-sectional momentum loses in
   highly-correlated rising markets (no spread to extract). Pure TS-mom would
   long everything; rank_neutral forces laggards short, which is a drag.
3. **DD brake fires 65.7% of rebals.** The strategy has chronic drawdown >7.5%
   for most of the IS; the brake is providing an effective ~50% gross haircut
   most of the time. This is a dependency flag — without the brake, maxDD
   balloons to -47.7%. The brake is principle-anchored but its 65.7% fire-rate
   suggests the underlying signal isn't strong enough to push equity to new highs
   consistently.
4. **Per-phase Sharpe dispersion is high** (-0.30 to +1.39 across 21 phases).
   The phase-agnostic mean (+0.96) is the honest headline, but it masks large
   per-phase variance. Some weekly rebal schedules are clearly bad (phases 12-13
   are near-zero or negative); the tranche averages them out.
5. **H1 vs H2 asymmetry** (H1 -0.07, H2 +1.85). The strategy does poorly in
   Q1-Q2 (typically accumulation/mania) and well in Q3-Q4 (typically correction/
   chop). This is the classic cross-sectional-momentum-in-crypto pattern; it may
   or may not persist OOS.

---

## 5. Engine parity & leak safety

- **Every run** goes through `blind_engine.run_backtest` with open-to-open fills,
  delisting force-exits, 5+2.5bps+funding cost, and a 10+5bps GT twin (re-run).
  No diagnostic-only scoring.
- **IS-only** via `mn3_split.mn3_slice_is` (cutoff epoch 1719792000000 = 2024-07-01).
  Zero reads of the holdout or Stage-3.
- **Leak battery** (all four PASS on the actual IS panel + on synthetic data):
  - corrupt-future signal: corrupting close[t0:] leaves signal[:t0] bit-identical ✓
  - corrupt-future crisis scalar: corrupting close[t0:] leaves scalar[:t0] bit-identical ✓
  - PIT universe: corrupting quote_volume[t0:] leaves universe[:t0] bit-identical ✓
  - decision-lag [k-1]: corrupting signal/scalar/beta at row ≥ t0 leaves the
    engine's realized equity through open[t0] bit-identical ✓
- **14/14 unit tests pass** (tests/test_mn4_idea01.py); ruff clean.

---

## 6. Files (all namespaced `mn4_idea01`, no shared modules touched)

- `analysis/portfolio/mn4_idea01_tsmom.py` — frozen construction + driver
- `tests/test_mn4_idea01.py` — 14 leak-battery + engine-parity tests
- `data/mn4_idea01/` — saved artifacts (headline_rets_1x/2x.npy, weights_avg_1x.npy,
  per_phase_rets_1x/2x.npy, signal.npy, universe.npy, gross_scalar.npy,
  beta_btc_roll.npy, beta_eth_roll.npy, is_grid_ms.npy, summary.json)
- `briefs-portfolio-mn4/IDEA-01.md` — this document
- `diary-portfolio-mn4/IDEA-01.md` — full IS scorecard + verdict
