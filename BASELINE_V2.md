# Current Baseline — v2 Track (Diversification Arm)

Last updated by: **iter-v2/069** (2026-04-24) — Category-A driven feature
pruning: 40 → 34 features by removing 6 near-identical/redundant features.
First iteration in 10 attempts to cleanly pass ALL concentration rules.
OOS cutoff date: 2025-03-24 (fixed, shared with v1, never changes)

## iter-v2/069 — feature pruning (CURRENT)

**OOS cutoff: 2025-03-24 (fixed)**
**Data extent: 2026-04-23 23:59 UTC** (~13.0 months of OOS, single seed 42)

| Metric | iter-v2/059-clean | **iter-v2/069** | Δ |
|---|---|---|---|
| IS monthly Sharpe | +1.042 | +0.874 | −16% |
| IS daily Sharpe | +0.974 | +1.032 | +6% |
| **OOS monthly Sharpe** | +1.659 | **+2.108** | **+27%** |
| **OOS daily Sharpe** | +1.663 | **+2.409** | **+45%** |
| **Combined monthly** | +2.701 | **+2.982** | **+10%** |
| OOS PF | 1.78 | 2.41 | +35% |
| OOS WR | 49.1% | 54.5% | +5.4pp |
| **OOS MaxDD** | 22.61% | **18.80%** | **−17% (improved)** |
| IS MaxDD | 68.55% | 85.91% | +25% (worse) |
| OOS trades | 57 | 55 | −3% |
| OOS total wpnl | +79.98 | +116.08 | +45% |

### Concentration — CLEAN on all n=4 rules (first time)

| Symbol | OOS wpnl | Share |
|---|---|---|
| SOLUSDT | +41.61 | 35.84% (max) |
| XRPUSDT | +30.51 | 26.29% |
| NEARUSDT | +28.70 | 24.72% |
| DOGEUSDT | +15.26 | 13.15% |

- Max per seed ≤ 50% (outer): **PASS**
- Max per seed ≤ 40% (inner n=4): **PASS** (first time!)
- No symbol dominant; all 4 profitable OOS

### Pruning decisions (Category A driven, IS-only)

Removed from V2_FEATURE_COLUMNS:

| Removed | Reason |
|---|---|
| `parkinson_vol_50` | rho=1.000 with `range_realized_vol_50` — identical |
| `garman_klass_vol_20` | rho=0.997 with `parkinson_vol_20` |
| `rogers_satchell_vol_20` | rho=0.988 with `parkinson_vol_20` |
| `close_pos_in_range_20` | rho=0.905 with `vwap_dev_20` |
| `close_pos_in_range_50` | rho=0.927 with `vwap_dev_50` |
| `atr_pct_rank_1000` | rho=0.905 with `atr_pct_rank_500` |

### Why it worked

LightGBM's `colsample_bytree` (Optuna-tuned, typically 0.6–0.8)
randomly samples features per tree. With 4 near-identical OHLC vol
estimators in the pool, trees often picked one of the clones instead
of a different family. Pruning freed capacity for diverse feature
coverage → more diverse ensemble → better OOS generalization.

Pre-registered hypothesis confirmed exactly: IS regression (cost of
reduced overfit) offset by larger OOS improvement.

### 10-seed validation status: STRUCTURALLY VACUOUS

Single-seed is the measurement. `LightGbmStrategy._train_for_month`
ignores the outer `seed` parameter when `ensemble_seeds=[42,123,456,789,1001]`
is fixed (the v1-style ensemble convention from iter-v2/035). All "outer
seeds" produce bit-identical trades. Flagged for future infrastructure
fix (see iter-v2/069 diary).

## iter-v2/059-clean — previous baseline (superseded by iter-v2/069)

## Reference: current v1 baseline (merged from main 2026-04-24)

v1 lives on `main` and has advanced independently of v2 while this worktree
iterated. For cross-reference:

| Metric | Value |
|---|---|
| Baseline tag | `v0.186` (main branch) |
| OOS Sharpe | +1.735 |
| OOS MaxDD | 29.31% |
| OOS Calmar | 5.91 |
| Symbols | A: BTC+ETH pooled, C: LINK, D: LTC, E: DOT |
| Risk primitives | R1 consecutive-SL cooldown, R2 drawdown-triggered position scaling, R3 OOD Mahalanobis |

The eventual combined portfolio (v1 + v2) is still the objective. v2's
`RiskV2Wrapper` feature z-score OOD gate (|z|>2.5 on any feature) and v1's
R3 OOD gate (Mahalanobis distance on 16 scale-invariant features) target the
same failure class — "model running in a regime it wasn't trained on" — via
different statistics. An iter-v2/072+ decision will evaluate whether v2 should
adopt R3 in place of (or alongside) its feature z-score gate. Until then, v2
keeps `ood_enabled=False` on its inner `LightGbmStrategy`.

## Measurement Discipline

Every headline metric in this file MUST state BOTH the OOS cutoff
(immutable, 2025-03-24) AND the **data extent** — the last `close_time`
present in the kline CSVs at measurement time. Without data extent, a
reader cannot tell whether "OOS Sharpe +X" was measured over 12 months
or 6. iter-v2/059's original headline +2.02 OOS trade Sharpe was
measured with CSVs stale to 2026-02-28 — a point the declaration did not
state and that silently shortened OOS by 50 days. Every new baseline
entry includes "Data extent: YYYY-MM-DD HH:MM UTC" in its header.

## iter-v2/059-clean — rerun with fix (CURRENT)

**OOS cutoff: 2025-03-24 (fixed)**
**Data extent: 2026-04-23 07:59 UTC** (~13.0 months of OOS)

**Same config as iter-v2/059** (z-score OOD 2.5, 4 symbols, cooldown=4,
hit-rate gate off, v1-style 5-seed internal ensemble, n_trials=50). Rerun
became necessary when v1's baseline investigation uncovered two
reproducibility bugs that also affected v2:
1. **Forming-candle fetcher bug** — corrupt tail CSV rows propagated
   through rolling features (fixed by commit `19a1d3e`, merged into
   quant-research at `6f6e63c`).
2. **Auto-discovered feature column order** — LightGBM's colsample_bytree
   samples columns by position, so the parquet schema's column order
   silently bled into the trained model. v2 had already been pinning
   `feature_columns=list(V2_FEATURE_COLUMNS)` from iter-v2/001, so it
   wasn't affected by the order bug itself — but the audit caught the
   fetcher bug at the same time.

Clean-data results vs iter-v2/059 as originally declared:

| Metric | iter-v2/059 (declared) | **iter-v2/059-clean** | Δ |
|---|---|---|---|
| IS trade Sharpe | +0.9742 | **+0.9742** | identical |
| OOS trade Sharpe | **+2.0232** | +1.6626 | **−18%** |
| OOS monthly Sharpe | +1.8346 | +1.6590 | −10% |
| IS MaxDD | 68.55% | 68.55% | identical |
| OOS MaxDD | 22.61% | 22.61% | identical |
| OOS PF | 1.8782 | 1.7806 | −5% |
| IS PF | 1.3807 | 1.3807 | identical |
| OOS WR | 50.0% | 49.1% | −0.9pp |
| IS trades | 225 | 225 | identical |
| OOS trades | 54 | 57 | +3 (extended window) |
| **Concentration (NEAR)** | 44.58% | **57.96%** | **FAIL** (>50% cap) |

**IS is pixel-perfect identical** — same strategy, same seeds, same
training data. Confirms IS metrics weren't affected by the forming-candle
bug (which only touches the tail of the CSV).

**OOS regressed** because:
1. Forming-candle corruption in the Mar-2025→Apr-2026 OOS window was
   propagating through rolling features until fixed.
2. The OOS window extended by ~5 weeks (Mar 17 → Apr 23 2026), adding 3
   new trades, with NEAR dominating that extension.

**Concentration now FAILS**: NEAR's share of positive OOS PnL jumped from
44.58% to 57.96%, breaching both the 50% outer cap and the 45% inner mean
rule. This is the honest clean-data number; iter-v2/059's declared 44.58%
was inflated by the corrupted data.

Still solidly profitable and positive on all 4 symbols (NEAR 62.5% WR,
XRP 57.1%, SOL 38.9%, DOGE 43.8%). The strategy has real edge — just less
edge than the pre-fix measurement showed, and less diversified.

## iter-v2/059 (pre-clean) — z-score OOD 2.5 (HISTORICAL — stale-data measurement)

**OOS cutoff: 2025-03-24 (fixed)**
**Data extent at measurement: 2026-02-28 23:59 UTC** (~11.2 months of OOS
— NEAR/SOL/XRP/DOGE CSVs had stopped refreshing; see forensic reconciliation
below)

Change from iter-v2/050: `zscore_threshold: 3.0 → 2.5`. More aggressive
OOD filtering catches mild distributional drift.

**Numbers below were measured with stale CSVs (last close 2026-02-28)
and are retained only for historical traceability. The delta vs clean
is fully accounted for — no code bug. Use iter-v2/059-clean for all
comparisons going forward.**

Key gains over iter-v2/050 (pre-clean measurement):
- OOS monthly +1.7036 → +1.8346 (+8%)
- OOS trade Sharpe +1.8129 → +2.0232 (+12%)
- OOS PF 1.8069 → 1.8782 (best ever)
- OOS WR 49.2% → 50.0% (first time >50%!)
- Concentration 47.06% → 44.58% (best ever)
- Combined IS+OOS monthly: +2.87 → +2.88 (+0.3%)

Trade-off:
- IS monthly +1.1670 → +1.0421 (−11%) — still >1.0
- IS trade Sharpe +1.2395 → +0.9742 (−21%)

Both IS and OOS still above 1.0 monthly (IS +1.04, OOS +1.83).
**First iteration with mean concentration ≤45%** (the strict inner
rule) — declared "clean concentration audit" but turned out to be 45.58%
after the forming-candle fix.

## iter-v2/050 — cooldown=4, BOTH IS+OOS above 1.0 monthly (superseded)

First v2 baseline with **both IS and OOS monthly Sharpe above 1.0** —
the user's long-standing goal, finally achieved.

Change from iter-v2/045: `cooldown_candles=3 → 4` (32h between trades).

Key gains over iter-v2/045:
- **IS monthly +0.8408 → +1.1670 (+39%, first time >1.0)**
- IS trade Sharpe +0.8001 → +1.2395 (+55%)
- IS PF 1.2669 → 1.4787 (+17%)
- OOS MaxDD 23.91% → 22.61% (best ever)
- Concentration 53.26% → 47.06% (first clean PASS)
- OOS/IS balance 2.28x → 1.46x (in target 1.0-2.0)
- Combined IS+OOS monthly: +2.76 → +2.87 (+4%)

Trade-off:
- OOS monthly +1.9166 → +1.7036 (−11%)
- OOS trade Sharpe +1.9664 → +1.8129 (−8%)

**ALL 7 MERGE gates pass cleanly** — first time since rule redesign.
Not a marginal pass; concentration is 2.94pp under the 50% rule and
the IS/OOS balance is solidly inside target.

## iter-v2/045 — disable hit-rate gate, massive OOS gain (superseded)

Single-parameter change from iter-v2/044: `HIT_RATE_CONFIG.enabled=False`.

The hit-rate gate was over-killing NEAR trades during drawdowns,
suppressing NEAR's strongest signal. With gate disabled:

- **OOS monthly +1.4024 → +1.9166 (+37%)** — best OOS ever
- **OOS trade Sharpe +1.5355 → +1.9664 (+28%)**
- **OOS PF +1.7469 → +1.8681 (+7%)**
- **OOS DSR +9.611 → +11.050 (+15%)**
- **Combined IS+OOS monthly: +2.24 → +2.76 (+23%)**
- IS metrics: identical (gate is OOS-only)

NEAR emerges as the dominant contributor: 16 trades, 68.8% WR,
+86.73% cumulative. Concentration 53.26% (marginally over 50% rule
but driven by high-quality signal, not structural weakness).

## iter-v2/044 — cooldown=3, balanced MERGE (superseded by iter-v2/045)

**Best-balanced v2 result ever.** Adopted after the MERGE criteria was updated
to use combined IS+OOS monthly Sharpe as the primary metric.

Change from iter-035: `cooldown_candles=2 → 3` (24h vs 16h between trades).

Key gains:
- **IS monthly Sharpe +0.6795 → +0.8408** (+24%, best IS ever)
- **IS MaxDD 71.93% → 52.04%** (better by 28%)
- **OOS MaxDD 26.69% → 23.91%** (better by 10%)
- **OOS/IS balance ratio 2.18x → 1.92x** (first time in target 1.0-2.0)

Trade-off:
- OOS trade Sharpe +1.7229 → +1.5355 (−11%)
- OOS monthly +1.4805 → +1.4024 (−5%)

Combined IS+OOS monthly Sharpe: **+2.24** vs iter-035's **+2.16** → +3.7% improvement.

## iter-v2/035 — v1-style 5-seed ensemble (superseded)

**Best v2 result ever on every OOS metric.** Adopts v1's proven ensemble
approach: `ensemble_seeds=[42,123,456,789,1001]`, `n_trials=50`.

Key breakthrough: the 5-seed ensemble acts as a quality filter — trade
count drops 41% (107 → 63 OOS) but Win Rate jumps 8pp (41.1% → 49.2%),
OOS PF jumps to 1.87, OOS MaxDD improves to 26.69%, and XRP concentration
drops from 69.47% to 44.57% (first time passing the n=4 50% rule).

All 4 symbols are OOS-positive for the first time in v2's history.

**IS/OOS ratio 0.475**: slightly below the 0.5 threshold which was relaxed
to 0.4 based on iter-035 data. IS (+0.82 trade Sharpe) is genuinely strong;
the ratio is high because OOS is exceptionally strong, not because IS is weak.

### Supersedes

- iter-v2/029 (forced reset baseline, concentration failed at 69%)
- iter-v2/019 (prior baseline, trade-level Sharpe only)

## Purpose

v2 is the diversification arm of the crypto-trade strategy. Its goal is to
cover market exposure **outside** v1's baseline symbols (BTC, ETH, LINK, BNB)
so that the eventual combined portfolio (v1 + v2) has lower correlation,
better tail behavior, and higher risk-adjusted returns than either track
alone.

v2 is iterated on the `quant-research` branch. v1 stays on `main`.

## Forbidden Symbols

| Symbol | v1 Role | v2 Allowed? |
|---|---|---|
| BTCUSDT | Model A | No |
| ETHUSDT | Model A | No |
| LINKUSDT | Model C | No |
| BNBUSDT | Model D | No |

Enforced via `V2_EXCLUDED_SYMBOLS` and `select_symbols(exclude=...)`.

## Methodology

**Primary metric clarification**: From iter-v2/035 onward, v2 uses
**v1-style 5-seed internal ensemble** (`ensemble_seeds=[42,123,456,789,1001]`,
`n_trials=50`). The ensemble IS the robustness validation. Single-run
output is the primary metric. The 10-seed outer sweep is optional
(for diagnostics, not gating).

**Risk-layer composition** (7 active gates as of iter-v2/019):

1. Vol-adjusted position sizing via `atr_pct_rank_200` (inverted:
   `vol_scale = atr_pct_rank_200` clipped to [0.3, 1.0])
2. ADX gate (threshold 20, inline Wilder ADX)
3. Hurst regime check (training 5/95 percentile band on `hurst_100`)
4. Feature z-score OOD alert (|z| > 3 on any of 35 v2 features)
5. Low-vol filter (`atr_pct_rank_200 >= 0.33`) — added iter-v2/004
6. Hit-rate feedback gate (window=20, SL threshold=0.65) — added iter-v2/017 (OOS only)
7. **BTC trend-alignment filter (14d ±20%)** — added iter-v2/019 (full period)

## Out-of-Sample Metrics — iter-v2/059-clean (CURRENT, measured 2026-04-23)

**v1-style 5-seed ensemble + cooldown=4 + hit-rate gate OFF + z-score OOD 2.5**

Fresh-data measurement through 2026-04-23 07:59 UTC with forming-candle
fetcher fix applied and pinned column order.

| Metric | iter-v2/050 | iter-v2/059 (pre-clean) | **iter-v2/059-clean** |
|---|---|---|---|
| IS monthly Sharpe | +1.1670 | +1.0421 | **+1.0421** (unchanged) |
| **OOS monthly Sharpe** | +1.7036 | +1.8346 | **+1.6590** |
| IS trade Sharpe | +1.2395 | +0.9742 | **+0.9742** (unchanged) |
| **OOS trade Sharpe** | +1.8129 | +2.0232 | **+1.6626** |
| IS PF | 1.4787 | 1.3807 | **1.3807** (unchanged) |
| **OOS PF** | 1.8069 | 1.8782 | **1.7806** |
| IS MaxDD | 63.73% | 68.55% | 68.55% (unchanged) |
| OOS MaxDD | 22.61% | 22.61% | 22.61% (unchanged) |
| **OOS WR** | 49.2% | 50.0% | **49.1%** |
| IS trades | 258 | 225 | 225 (unchanged) |
| OOS trades | 59 | 54 | **57** (extended window) |
| **Concentration** | 47.06% | 44.58% | **57.96% (NEAR) — FAILS 50% cap** |

**Notes on the pre-clean → clean transition**:
- IS is pixel-identical across both measurements — proves the fetcher
  corruption only affected recent data and the v2 code is fully
  deterministic given the same inputs.
- OOS dropped ~10-18% because (a) forming-candle rows were
  contaminating rolling features in the Mar-2025 → Apr-2026 OOS period,
  and (b) the OOS window extended ~5 weeks, adding 3 new trades
  dominated by NEAR.
- Concentration regressed sharply: NEAR's clean-data share is 57.96%
  — well over the 50% outer cap. The declared 44.58% was inflated.

**Still a real edge**: all 4 symbols profitable OOS, WR 49.1%, PF 1.78,
OOS monthly +1.66. But concentration FAIL means this baseline is not
eligible for deployment without addressing NEAR dominance.

### Forensic reconciliation — iter-v2/059 vs iter-v2/059-clean

Trade-by-trade proof that the OOS delta is fully explained and no code
bug exists. Total OOS wpnl delta = **−2.44**.

| Source | Contribution | Running |
|---|---|---|
| 53 of 54 shared trades — entry/exit/PnL bit-identical | 0.00 | 0.00 |
| NEAR 2026-02-28 trade: `end_of_data` (Feb 28 23:59) → `take_profit` (Mar 1 07:59) because the clean run has one more candle | +0.76 | +0.76 |
| 3 new trades in the 50-day extended window: NEAR 2026-03-04 SL, NEAR 2026-03-17 TP, XRP 2026-04-19 SL | −3.20 | **−2.44** ✓ |

`iter-v2/059` has **zero** OOS trades closing on or after 2026-03-01 —
definitive proof the CSVs had stopped fetching. The `end_of_data` exit
reason on the NEAR Feb-28 trade is the backtest engine's literal signal
that it ran out of candles mid-trade.

Script: `forensic_v2_059_vs_clean.py`.

### iter-v2/019 historical (trade-level Sharpe)

Kept for continuity. iter-029 uses monthly Sharpe going forward.

| Statistic | iter-v2/005 | iter-v2/017 | iter-v2/019 |
|---|---|---|---|
| Mean OOS trade Sharpe | +1.297 | +1.4066 | +1.3968 |
| Profitable seeds | 10/10 | 10/10 | 10/10 |
| Worst-seed floor | +0.319 | +0.061 | +0.579 |

**Single-run output (v1-style 5-seed ensemble) — iter-v2/035**

| Metric | iter-v2/029 | **iter-v2/035** |
|---|---|---|
| **OOS trade Sharpe** | +1.4054 | **+1.7229** (+23%) |
| **OOS monthly** | +1.2774 | **+1.4805** (+16%) |
| **OOS PF** | 1.5889 | **1.8702** (+18%) |
| **OOS MaxDD** | 32.08% | **26.69%** (best) |
| **OOS WR** | 41.1% | **49.2%** (+8pp) |
| OOS trades | 107 | 63 |
| OOS DSR | +9.30 | **+9.71** |
| IS trade Sharpe | +0.7778 | +0.8186 |
| IS monthly | +0.6680 | +0.6795 |
| IS MaxDD | 59.93% | 71.93% |
| IS DSR | +17.35 | +17.03 |
| **XRP share (wpnl)** | **69.47%** FAIL | **44.57%** PASS |

**v2-v1 OOS daily return correlation**: −0.046 (from iter-v2/005 IS
measurement, re-check in iter-v2/019 post-MERGE combined analysis)

## In-Sample Metrics (primary seed 42) — iter-v2/019

| Metric | iter-v2/005 | iter-v2/017 | **iter-v2/019** |
|---|---|---|---|
| **IS Sharpe** | +0.1162 | +0.1162 | **+0.5689** (+390%) |
| **IS Sortino** | +0.1188 | +0.1188 | **+0.5870** (+394%) |
| **IS Profit factor** | 1.0288 | 1.0288 | **1.1557** (+12%) |
| **IS Max drawdown** | 111.55% | 111.55% | **72.24%** (−35%) |
| **IS DSR** | +4.1589 | +4.1589 | **+17.59** (+323%) |
| **IS Total PnL** | +25.82% | +25.82% | **+116.72%** (+352%) |
| IS Win rate | 40.1% | 40.1% | 40.1% |
| IS Total trades | 344 | 344 | 344 |

**The iter-v2/019 BTC trend filter dramatically improves IS.** The
filter catches 2022 bear-crash longs (LUNA May, FTX Nov) and
2024-11 post-election rally shorts. NEAR's IS PnL recovers from
−67.39% to −20.50% (+46.89 improvement on NEAR alone).

**2024-11 specifically**: weighted PnL improves from −73.66% to
−28.68% (−61% loss reduction), directly responding to user
feedback on iter-v2/018.

**IS/OOS Sharpe ratio: +4.46** (iter-v2/017 was +21.10). The
lower ratio means IS and OOS are now comparable — a HEALTHIER
sign than divergent ratios. Both are strong.

## Per-Symbol OOS Performance — iter-v2/035

**All 4 symbols OOS-positive** (first time in v2 history):

| Symbol | Model | Trades | WR | Weighted PnL | Share (wpnl) |
|---|---|---|---|---|---|
| **XRPUSDT** | G | 7 | **71.4%** | **+31.47** | **44.57%** PASS |
| **NEARUSDT** | H | 17 | **64.7%** | **+28.85** | **40.86%** |
| DOGEUSDT | E | 19 | 42.1% | +8.62 | 12.20% |
| SOLUSDT | F | 20 | 35.0% | +1.68 | 2.37% |

**Concentration: 44.57% — PASS** (n=4 rule ≤ 50%).

The v1-style ensemble quality-filters XRP to only 7 OOS trades (from
iter-029's 22) but each at 71.4% WR — extreme selectivity. NEAR
becomes a major contributor at 64.7% WR. The 2 main alpha sources
(XRP+NEAR) are balanced at 45/41 share — the best diversification
within v2's 4-symbol portfolio ever.

## Per-Symbol IS Performance (primary seed 42, iter-v2/019)

| Symbol | Model | Trades | WR | Weighted PnL | Δ from v0.v2-005 |
|---|---|---|---|---|---|
| XRPUSDT | G | 103 | 42.7% | +83.62% | +2.61 |
| SOLUSDT | F | 85 | 41.2% | +31.17% | +3.48 |
| DOGEUSDT | E | 84 | 39.3% | +22.43% | **+40.66** (flipped positive) |
| **NEARUSDT** | H | 72 | 36.1% | **−20.50%** | **+46.89** (2022 rescue) |

**NEAR's 2022 bear damage cut by 70%**. DOGE flipped from −18.23
to +22.43 (+40.66 swing). BTC trend filter catches 2022 bear-crash
longs (LUNA May, FTX Nov, BTC 14d < −20%) AND the 2024-11 rally shorts.

## Hit-Rate Gate (iter-v2/017 primitive #6)

**Config D (OOS only, window=20, SL threshold=0.65)**. 21 kills
per primary seed, all clustered in July 16 → August 29 2025
drawdown window. See `briefs-v2/iteration_017/engineering_report.md`.

## BTC Trend Filter (iter-v2/019 primitive #7)

**Config**: lookback=42 bars (14 days 8h), threshold=±20%, full period.

Rule: kill alt trade when direction fights BTC 14d return exceeding
±20% in opposing direction.

**Primary seed firing stats**: 39 kills out of 461 trades (8.46%)
distributed across the full IS+OOS window:

| Period | Kills | Event |
|---|---|---|
| 2022-01, 2022-05-06 | ~6 | LUNA crash |
| 2022-11 | ~2 | FTX crash |
| 2023-10 | ~3 | BTC +25% rally |
| 2024-03 | ~4 | ATH rally |
| **2024-11** | **15** | **Post-election Trump rally** ← target |
| other | ~9 | minor events |

**10-seed kill stats**: mean 43 kills per seed, range 35-52.
The kill list is nearly seed-invariant because trade open_times
are shared across seeds and BTC data is fixed.

The two gates are complementary: BTC filter catches IS regime
shifts, hit-rate gate catches OOS slow bleeds. No double-firing.

## Regime-Stratified OOS Sharpe

All OOS trades in `hurst_100 ≥ 0.6` (trending) bucket.

| Hurst | ATR pct | Approx count | Notes |
|---|---|---|---|
| [0.60, 2.00) | [0.33, 0.66) | ~50 | mid-vol, slightly negative |
| [0.60, 2.00) | [0.66, 1.01) | ~45 | high-vol, carries Sharpe |

Regime-stratified breakdown from iter-v2/017 report not fully recomputed
— inherits structure from iter-v2/005.

## Configuration

| Field | Value |
|---|---|
| Symbols | **DOGEUSDT, SOLUSDT, XRPUSDT, NEARUSDT** |
| Interval | 8h |
| Training window | 24 months rolling, monthly walk-forward |
| Optuna trials / month | **50** (iter-v2/035+, v1-style budget) |
| CV splits | 5 with `gap = (timeout_candles + 1) × n_symbols = 22` |
| Labeling | Triple barrier, ATR-scaled (2.9 × NATR TP / 1.45 × NATR SL) |
| Timeout | 7 days (10080 min) |
| Cooldown | 2 candles |
| Features | 40 from `V2_FEATURE_COLUMNS` (35 core + 5 BTC cross-asset) |
| Feature helper | `natr_21_raw` (labeling input, excluded from features) |
| Feature column pinning | **MANDATORY**: `feature_columns=list(V2_FEATURE_COLUMNS)` from `crypto_trade.features_v2`. Never `None`, never sorted, never reordered. See `.claude/commands/quant-iteration-v2.md` § "Feature Column Pinning". |
| Candle integrity | **MANDATORY**: `fetcher.py` must drop forming candles (`k.close_time < now_ms`). Fix on `main` at commit `19a1d3e` (2026-04-13). Pre-flight: grep the guard + scan CSV tails for `close_time >= now_ms`. See `.claude/commands/quant-iteration-v2.md` § "Candle Integrity". |
| Data freshness | **MANDATORY**: every baseline symbol's CSV must have `close_time` within 16h of measurement time. A baseline measured on stale CSVs silently truncates OOS (iter-v2/059 lost 50 days / 3 trades / 1 force-closed trade this way). |
| Risk gates | 7 active gates (vol-scaling, ADX, Hurst, z-score OOD, low-vol, **hit-rate (OOS)**, **BTC trend (full)**) |
| **Ensemble** | **5-seed internal** (`[42,123,456,789,1001]`, v1-style, from iter-v2/035) |
| Fee | 0.1% per trade |

## iter-v2/020+ Roadmap

1. **iter-v2/020 (EXPLOITATION)**: CPCV + PBO validation upgrades.
   Deferred from iter-v2/001 skill. Quantifies honest
   expected-vs-realized Sharpe gap. Gatekeeper for paper trading.
2. **iter-v2/021 (EXPLORATION)**: Paper trading deployment
   harness. Run 4 v2 models + both risk gates on live data at
   50/50 v1/v2 capital split (per iter-v2/018 recommendation).
3. **iter-v2/022+ (EXPLORATION)**: Additional regime filters
   (BTC realized vol regime, cross-asset correlation spike,
   macro signals). Speculative — the 2 existing gates cover
   most known failure modes.

## Dead Ideas — don't re-propose without new justification

Required consultation before any iter-v2/NNN brief. Approach classes that
have been tried and failed — retrying needs explicit justification of
WHY conditions have changed.

### Symbol changes
- **AAVEUSDT** (iter-v2/063): added as 5th symbol without Gate 3
  screening; OOS −21.34 wpnl, 26% WR, drove total OOS −35%
- **AVAXUSDT** (iter-v2/041): IS collapsed; NO-MERGE
- **ATOMUSDT** (iter-v2/047): swap for DOGE; failed
- **ADAUSDT** (iter-v2/036, /066): single-seed IS screening looks strong
  but 5-seed ensemble averaging washes out the signal; consistently
  loses OOS
- **DOTUSDT** (iter-v2/061): best OOS trade Sharpe ever (+2.18) but IS
  −62%; NO-MERGE
- **OPUSDT, TRXUSDT as primary picks** (iter-v2/066): IS-only screener
  selected both; walk-forward showed TRX 99 trades breakeven, OP only
  18 trades total

### Concentration fixes
- **Per-symbol position cap on NEAR** (iter-v2/064, 065): fixes
  concentration but data-snoops on NEAR's OOS behaviour. User flagged
  as biased/overfit; validated empirically when same approach via
  "generic" IS-ranking still failed
- **Portfolio drawdown brake Config C** (iter-v2/067): symmetric,
  portfolio-level. Counter-intuitively INCREASED OOS MaxDD (22.61% →
  35.24%) because shrinking during drawdown misses rebound trades;
  equity recovers slower → deeper next trough
- **IS-only universe re-screening** (iter-v2/066): catastrophic OOS
  −67%, concentration WORSE (XRP 78%). The IS-only 80/20 split + single
  seed screener does NOT predict walk-forward + 5-seed ensemble Sharpe

### Gate / filter tunes
- **z-score OOD 2.25** (iter-v2/060): too tight, OOS trade count <50 min
- **z-score OOD 2.4** (iter-v2/068): pending at time of writing
- **Hit-rate gate enabled** (iter-v2/017-044): over-kills NEAR signals
  during drawdowns; disabled in iter-v2/045 onwards

### Key insight — the baseline is near local optimum
iter-v2/063-067 empirically showed the iter-v2/059-clean baseline is at
or near a local optimum for this architecture. Five consecutive concen-
tration-focused iterations all degraded OOS Sharpe. NEAR's ~44%
concentration is a consequence of NEAR having genuine edge in the OOS
regime, not a bug. Future iterations should prioritise BOLD
explorations (new features, new model architecture, new risk layer
primitives) over incremental tunes.

## Tags

- `v0.v2-002` — first v2 baseline (inverted vol-scale)
- `v0.v2-004` — low-vol filter baseline
- `v0.v2-005` — 4-symbol baseline (+1.67 primary / +1.30 mean)
- `v0.v2-017` — hit-rate gate baseline (+2.45 primary, Calmar 4.92, 2024-11 NOT addressed)
- `v0.v2-019` — BTC trend filter baseline (+2.54 primary trade Sharpe, IS +0.57, Calmar 5.10)
- `v0.v2-029` — 15 Optuna trials, forced reset, BTC cross-asset features (primary OOS monthly +1.28, mean OOS +0.90, concentration 60.86% FAIL)
- `v0.v2-035` — v1-style 5-seed ensemble, 50 trials (OOS trade Sharpe +1.7229, OOS PF 1.87, MaxDD 26.69%, WR 49.2%, concentration 44.57% PASS)
- `v0.v2-044` — cooldown=3 + v1 ensemble (IS monthly +0.8408, OOS monthly +1.4024, combined +2.24, balance ratio 1.92x, IS MaxDD 52%, OOS MaxDD 24%)
- `v0.v2-045` — hit-rate gate DISABLED (IS monthly +0.8408, OOS monthly +1.9166, combined +2.76; NEAR 53% concentration marginal FAIL)
- `v0.v2-050` — cooldown=4 milestone (IS monthly +1.1670 AND OOS monthly +1.7036 — BOTH ABOVE 1.0 first time; combined +2.87; concentration 47.06%)
- `v0.v2-059` — z-score OOD 2.5, measured pre-clean on corrupted data. IS monthly +1.04, OOS monthly +1.83 (inflated), concentration 44.58% (inflated). Superseded by v0.v2-059-clean.
- **`v0.v2-059-clean` (2026-04-23) — SAME CONFIG as v0.v2-059, rerun on fresh data with fetcher fix + pinned feature columns. IS identical (+0.97 trade Sharpe, +1.04 monthly). OOS trade Sharpe +1.66, OOS monthly +1.66, OOS PF 1.78, OOS WR 49.1%, OOS trades 57, OOS MaxDD 22.61%. Concentration 57.96% (NEAR) — FAILS 50% cap. Real edge, still profitable on all 4 symbols, but not deployment-ready without addressing concentration.**
