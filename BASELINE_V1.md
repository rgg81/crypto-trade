# V1 Baseline — BUNDLE-001 (SPECIALIST + BUNDLE methodology)

Last updated by: **iter-v1/071 FIRST BUNDLE-001 ASSEMBLY on 2026-06-05** under user mandate (`"we merge this, no matter what. This is gonna be our baseline now."`). This iteration establishes the FIRST methodology-trained baseline anchor under the new SPECIALIST + BUNDLE methodology. The prior `v0.v1-baseline-corrected` (corrected walk-forward 5-symbol pooled head) is **SUPERSEDED** — preserved in the "Superseded Baseline" section at the bottom of this file.

OOS cutoff date: 2025-03-24 (fixed, never changes).

Tag: **`v0.v1-071`** (this file's commit).

Reports: `reports-v1/iteration_v1-071/` (bundle) + `reports-v1/iteration_v1-063/` + `reports-v1/iteration_v1-064/` + `reports-v1/iteration_v1-065/` (per-specialist; recovered + committed at /071 setup).

Track: **v1** (refactored; 3-coin specialist bundle).

---

## Baseline = BUNDLE-001 (3 single-coin specialists, pairwise-disjoint universe)

BUNDLE-001 is the symbol-partitioned union of 3 LightGBM specialists, each trained independently under the cycle-6/cycle-7 per-symbol regime-specialist mandate. There are no bundle-level weights; each specialist trades its own coin under its own risk wrapper.

| # | Specialist | Owns | Source iter | Risk wrapper | ATR TP/SL | Inner-ensemble seeds | Outer seed |
|---|---|---|---|---|---|---|---|
| 1 | DOT specialist | `{DOTUSDT}` | iter-v1/063 | R1+R2+R3 | 3.5 / 1.75 | 5 (`[42,123,456,789,1001]`) | 42 |
| 2 | ETH specialist | `{ETHUSDT}` | iter-v1/064 | R3 only (Model A pattern) | 2.9 / 1.45 | 5 | 42 |
| 3 | BTC specialist | `{BTCUSDT}` | iter-v1/065 | R3 only (Model A pattern) | 2.9 / 1.45 | 5 | 42 |

**Pairwise-disjoint universe**: `{DOTUSDT} ∩ {ETHUSDT} = ∅`, `{DOTUSDT} ∩ {BTCUSDT} = ∅`, `{ETHUSDT} ∩ {BTCUSDT} = ∅`. Union = `{BTCUSDT, ETHUSDT, DOTUSDT}` (3 coins). **LINKUSDT and LTCUSDT are NOT in BUNDLE-001** (specialist attempts /066-/070 dropped under 2-strike rule). Per `feedback_v1_bundle_no_coin_overlap.md` Critic Check 16 PASS.

**Bundle decision rule** (per `feedback_v1_backtest_live_parity_hard.md` — Critic Check 15 PASS):

```python
def bundle_signal(symbol, t):
    if symbol == "DOTUSDT":
        return spec_063.get_signal(symbol, t)
    if symbol == "ETHUSDT":
        return spec_064.get_signal(symbol, t)
    if symbol == "BTCUSDT":
        return spec_065.get_signal(symbol, t)
    return None  # not in BUNDLE-001 universe
```

Bit-identical in backtest (post-hoc trades.csv union) and at `live/engine.py:_tick` (specialist dispatch per symbol). No aggregation, no netting, no portfolio-level shared state.

**No bundle-level weights** (per `feedback_v1_bundle_weight_is_only.md` Critic Check 17 N/A): each specialist's per-trade `weight_factor` already encodes vol-targeting + R2 scaling + risk wrapper effects.

---

## BUNDLE-001 Headline Metrics

From `reports-v1/iteration_v1-071/comparison.csv`:

| Metric | In-Sample | Out-of-Sample | OOS/IS ratio |
|---|---:|---:|---:|
| **Monthly Sharpe** | **+0.5463** | **+0.9636** | **1.7639** |
| Monthly Sortino | +0.8729 | +1.5678 | 1.7961 |
| Max Drawdown | 89.03% | 36.51% | 0.4101 |
| Win Rate | 40.60% | 45.22% | 1.1138 |
| Profit Factor | 1.1021 | 1.2158 | 1.1032 |
| Total Trades | 537 | 230 | 0.4283 |
| Total Net PnL | +129.681% | +109.7499% | 0.8463 |
| Calmar Ratio | 0.4482 | 2.2546 | 5.0303 |
| Top-symbol concentration (OOS) | N/A | **37.96% (BTC)** | N/A |

Bundle per-trade Sharpe ratio (OOS/IS) = +0.084 / +0.041 = **2.05** (regime-favorable OOS window).

---

## Per-Specialist Metrics

From each specialist's `reports-v1/iteration_v1-{063,064,065}/comparison.csv`:

| Specialist | Sym | IS Sharpe | OOS Sharpe | IS Trades | OOS Trades | IS PnL% | OOS PnL% | IS MaxDD | OOS MaxDD |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| /063 | DOT | +0.4310 | −0.0709 | 149 | 62 | +23.94 | −1.09 | 17.12% | 16.21% |
| /064 | ETH | +0.2383 | +0.5171 | 198 | 81 | +15.00 | +9.21 | 24.66% | 11.44% |
| /065 | BTC | −0.1763 | +1.1256 | 190 | 87 | −8.33 | +13.75 | 25.86% | 5.48% |

**Regime profile**:
- **DOT** — high-IS, near-flat-OOS (IS-window regime-specialist; R1+R2+R3 retained from Model E lineage).
- **ETH** — balanced, OOS-favored (steady contributor; per-trade Sharpe +0.063 OOS vs +0.049 IS).
- **BTC** — IS-NEGATIVE / OOS-POSITIVE (regime-INVERTING specialist; the single largest OOS contributor at 37.96% of bundle OOS PnL; pending multi-seed disambiguation per `feedback_is_oos_divergence_is_regime_not_overfit.md`).

---

## Per-Symbol OOS PnL Attribution

| Symbol | OOS Trades | OOS PnL% | Share of bundle OOS PnL |
|---|---:|---:|---:|
| BTCUSDT | 87 | +41.66% | **37.96%** |
| DOTUSDT | 62 | +40.18% | **36.61%** |
| ETHUSDT | 81 | +27.91% | **25.43%** |

**Top-symbol concentration**: BTC at **37.96%** > 30% gate. At N=3 the equal-weight concentration ceiling is 33.3% — the standard 30% gate is structurally infeasible. Future BUNDLE-002 must expand to N≥5 to make the 30% gate achievable. The HHI excess over equal-weight is only 2.85% (effectively equal-weighted PnL distribution).

---

## Configuration Inherited Into BUNDLE-001

**Symbols**: `{BTCUSDT, ETHUSDT, DOTUSDT}` (3-coin universe; LINK + LTC excluded under 2-strike rule).

**Excluded universe (v1)**: `V1_EXCLUDED_SYMBOLS = (SOLUSDT, XRPUSDT, DOGEUSDT, NEARUSDT, BCHUSDT, LDOUSDT, TRXUSDT, BNBUSDT)`.

**Risk mitigations active per specialist**:
- DOT specialist (/063): **R1 + R2 + R3** (K=3, C=27 candles ≈ 9 days; R2 trigger=7%, anchor=15%, floor=0.33; R3 cutoff=0.70, 16 SI features). Mirror of historical Model E pattern.
- ETH specialist (/064): **R3 only** (R1/R2 disabled per historical Model A pattern; R3 cutoff=0.70, 16 SI features).
- BTC specialist (/065): **R3 only** (same).

**Feature stack**: `V1_FEATURE_COLUMNS_PRUNED` (48 columns; post-cycle-2/3 prune; same column-pinned passing to LightGBM).

**Ensemble**: 5 inner seeds per specialist (`[42, 123, 456, 789, 1001]`); single outer seed=42 EXPLORATION budget.

**Optuna**: `n_trials = 18` per (symbol, month) cell (EXPLORATION budget; CONFIRMATION budget = 35 trials/cell deferred to /072 multi-seed re-validation).

**Walk-forward**: `train_end_ms = test_start_ms - embargo_ms` (the iter-v3/058 fix at `walk_forward.py:113`; commit `5566a69`).

**Training schedule**: `training_months = 24`, monthly retrain; OOS_CUTOFF_DATE = 2025-03-24.

---

## Hard Merge Gates — Status vs BUNDLE-001 (USER-MANDATE OVERRIDE)

| Gate | Threshold | BUNDLE-001 | Verdict |
|---|---|---:|---|
| IS monthly Sharpe | > 1.0 | +0.5463 | FAIL (informational under user mandate) |
| OOS monthly Sharpe | > 1.0 | +0.9636 | FAIL (informational under user mandate; 0.04 short of floor) |
| OOS / IS Sharpe ratio | ≥ 0.5 | 1.7639 | PASS |
| OOS trades total | ≥ 130 | 230 | PASS |
| Per-specialist OOS trades | ≥ 50 | DOT 62 / ETH 81 / BTC 87 | PASS (3/3) |
| OOS trades/month | ≥ 10 | ~16.4 | PASS |
| IS trades total | ≥ 50 | 537 | PASS |
| Top symbol concentration | ≤ 30% (OOS PnL share) | 37.96% (BTC) | FAIL (structurally infeasible at N=3; informational) |
| **DSR** (CONFIRMATION-grade) | > 0.95 | not computed at bundle layer (per-specialist DSR informational; bundle DSR requires aggregated trial-counting) | FAIL (informational under user mandate) |
| **PSR** (monthly, vs benchmark 1.0) | > 0.95 | not computed at bundle layer | FAIL (informational under user mandate) |
| **PBO** | < 0.40 | not computed at bundle layer (specialist selection PBO non-trivial at 3-of-8) | FAIL (informational under user mandate) |
| Multi-seed re-validation | mean SR > 0 + ≥7/10 profitable | NOT YET RUN (single outer seed=42 EXPLORATION basis) | DEFERRED to /072 |
| Methodology integrity | Look-ahead / embargo / pairwise-disjoint / live-parity | PASS (Critic Phase 7.5 Checks 1, 2, 15, 16, 17) | PASS |

**User mandate is binding for edge-gate evaluation only; methodology-integrity gates (Checks 1, 2, 15, 16, 17) PASS on their own merits and are independent of the mandate.** No methodology violation is overridden — only the standard CONFIRMATION-budget edge thresholds.

**Material work needed to discharge the open gates** (mandatory for /072):
1. Multi-seed re-validation at 7-outer-seed roster `[42, 123, 456, 789, 1001, 2002, 3003]` per specialist.
2. Bundle-layer DSR/PBO/PSR computation (methodology axis; design a CONFIRMATION-grade aggregator that accounts for per-specialist Optuna trial counts and the 3-of-8 specialist selection cost).
3. BUNDLE-002 universe expansion to N≥5 to make the 30% top-symbol concentration gate clearable.

---

## Comparison vs Old (Superseded) Baseline

| Metric | Old `v0.v1-baseline-corrected` | BUNDLE-001 (`v0.v1-071`) | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.2829 | +0.5463 | **+0.2634** |
| OOS monthly Sharpe | +0.6637 | +0.9636 | **+0.2999** |
| OOS/IS Sharpe ratio | 2.346 | 1.764 | −0.582 |
| OOS trades total | 189 | 230 | +41 |
| IS trades total | 621 | 537 | −84 |
| OOS Profit Factor | 1.156 | 1.2158 | +0.060 |
| OOS Win Rate | 40.2% | 45.22% | +5.02pp |
| OOS Max DD | 40.94% | 36.51% | −4.43pp |
| IS Max DD | 73.06% | 89.03% | +15.97pp |
| OOS Calmar | 0.931 | 2.255 | +1.324 |
| Symbol count | 5 (pool) | 3 (specialists) | −2 (LINK+LTC dropped under 2-strike) |

**Pareto result vs old baseline**: PARTIAL. 6 of 9 comparable metrics strictly improve; OOS/IS Sharpe ratio compresses (still ≫ 0.5 floor); IS trade count drops (still ≫ 50 floor); IS MaxDD widens.

---

## Trade-Artifact Persistence — NEW HARD RULE (effective from /072)

Codified at commit `0a19e0682778b98d0523fcc6c70ebe73b10e6fd9`:

> **HARD rule**: At Phase 8 closeout, the QR MUST `git add reports-v1/iteration_v1-NNN/` BEFORE committing the diary. The reports tree (`trades.csv`, `comparison.csv`, `daily_pnl.csv`, `monthly_pnl.csv`, `per_symbol.csv` per IS+OOS) is a load-bearing artifact:
> - Bundle composition (THIS iteration's primary failure mode)
> - Regime attribution
> - Dead-paths verification
> - Trade-level deterministic replay (per `feedback_deterministic_trade_match.md`)
>
> Phase 8 commit messages must include "reports tracked" in the body. Critic Check `REPORTS-TREE-COMMITTED` verifies the reports tree exists in git history before allowing the merge.

iter-v1/063, /064, /065 (and the LINK+LTC dropped specialists /066-/070) are **GRANDFATHERED** — artifacts recovered from `stash@{0}` at commit `ee37f07e` and committed at /071 setup.

---

## Audit Trail

- **2026-04-22** — Historical v0.186 baseline tagged on `main` (R3 OOD gate added; OOS Sharpe +1.735 — later found to be inflated by walk-forward lookahead bias).
- **2026-05-13** — Walk-forward fix `5566a69`; corrected stats captured in `BASELINE.md` (OOS Sharpe +0.827 / 184 trades).
- **2026-05-23** — v1 refactored. `BASELINE_V1.md` created with corrected stats on fresh data — anchor `v0.v1-baseline-corrected` (now SUPERSEDED).
- **2026-05-26** — Cycle-2 CLOSES NO-MERGE at iter-v1/015. Anchor numbers UNCHANGED.
- **2026-06-01** — Cycle-6 CLOSES NO-MERGE at iter-v1/056 CONFIRMATION-BLOCK. Per-symbol regime-specialist mandate continues into cycle-7. Anchor numbers UNCHANGED.
- **2026-06-05** — **iter-v1/071 FIRST BUNDLE-001 ASSEMBLY** under user mandate. Trade-artifact loss incident recovery from `stash@{0}` at `ee37f07e`. New HARD reports-tracking rule codified at `0a19e068`. BASELINE_V1 SUPERSEDED — new anchor is `v0.v1-071` (THIS FILE).

---

## Superseded Baseline — `v0.v1-baseline-corrected` (preserved for history)

The prior baseline (5-symbol pool / 4-model architecture A/C/D/E / 193-col `V1_FEATURE_COLUMNS`) is preserved below verbatim for trace and back-comparison. **Do not cite as the active anchor.** Use `v0.v1-071` BUNDLE-001 for all post-/071 iteration comparisons.

---

## V1 Baseline — Refactored (SUPERSEDED 2026-06-05)

Last updated by: **v1 refactor + fresh-data baseline reproduction on 2026-05-23** — corrected walk-forward stats from re-running v0.186's exact config under the fixed `walk_forward.py:113` (`train_end_ms = test_start_ms - embargo_ms`) and the freshest kline data (2026-05-23 fetch).

OOS cutoff date: 2025-03-24 (fixed, never changes).

Tag: `v0.v1-baseline-corrected` (SUPERSEDED by `v0.v1-071`).

Reports: `reports-v1/iteration_v1-baseline/`.

Track: **v1** (BTC/ETH/LINK/LTC/DOT initial universe; refactored 2026-05-23 to add v3 rigor + LightGBM Master advisor agent + four QR↔Critic dynamic improvements).

---

## 🚨 Origin: Corrected Walk-Forward Baseline

The historical `v0.186` baseline (`OOS Sharpe +1.735`, `Max DD 29.31%`) was produced with an undetected **lookahead bias** at the walk-forward train/test boundary: `walk_forward.py` set `train_end_ms = test_start_ms`, but the triple-barrier labeler's forward scan extends `label_timeout_minutes` (7 days) past each training candle's close. For the last ~22 training candles of every (model, test_month) split, the label was computed using price data from inside the test month — classic peek-into-test contamination.

The bug was identified, fixed, and tested in commit `5566a69` (`fix(walk-forward): purge labeler-horizon from train_end_ms`). The fix landed at `walk_forward.py:113` and shrinks `train_end_ms` by `compute_embargo_candles × interval_ms` so every training candle's forward scan terminates at or before `test_start_ms`. Same helper feeds the CV gap inside Optuna — single source of truth.

Re-running v0.186 with the fix produces the corrected metrics in this file.

**Pre-fix numbers MUST NOT be cited going forward.** They are preserved at the end of this file for historical record only.

**Determinism cross-check (per `feedback_deterministic_trade_match.md`)**: IS metrics on the 2026-05-23 reproduction matched the 2026-05-13 anchor in BASELINE.md **bit-exactly** (IS Sharpe +0.2829 vs +0.283, IS Max DD 73.06% identical, IS trade count 621 identical, IS win rate 39.9% identical). The IS side is fully reproducible across two independent post-fix runs on different dates. OOS metrics differ by exactly 5 trades (189 vs 184), all 5 from the new 2026-05-13 → 2026-05-23 window of fresh data, all 5 net negative — fully explains why OOS Sharpe dropped from +0.827 (2026-05-13 anchor) to +0.6637 (current). **The corrected baseline is honestly reproducible; the OOS Sharpe difference is the cost of trading the last 10 days of unfavorable market conditions.**

---

## Baseline Configuration

**Four independent LightGBM models** — A (BTC+ETH pooled), C (LINK), D (LTC), E (DOT) — each with **5-seed ensemble** + per-symbol vol targeting. Feature selection is explicit (`V1_FEATURE_COLUMNS`, 193 columns; mirrors the historical `BASELINE_FEATURE_COLUMNS`).

**Symbols**: BTC, ETH, LINK, LTC, DOT (5 symbols).

**Universe**: `V1_BASELINE_UNIVERSE = (BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT)`.

**Excluded universe**: `V1_EXCLUDED_SYMBOLS = (SOLUSDT, XRPUSDT, DOGEUSDT, NEARUSDT, BCHUSDT, LDOUSDT, TRXUSDT, BNBUSDT)`.

**Risk mitigations active**:
- **R1 consecutive-SL cool-down** (K=3, C=27 candles ≈ 9 days) — Models C, D, E
- **R2 drawdown-triggered position scaling** (trigger=7%, anchor=15%, floor=0.33) — Model E only
- **R3 OOD Mahalanobis gate** (cutoff=0.70, 16 scale-invariant features) — ALL MODELS (A, C, D, E)
- Model A has R3 only (no R1/R2 — IS analysis showed BTC/ETH have mean-reverting WR at late streaks, so R1 would hurt).

**Ensemble seeds (baseline run, matches historical v186 exactly)**: `[42, 123, 456, 789, 1001]`. 5-seed configuration is preserved for deterministic trade reproduction against the historical anchor.

**Ensemble seeds (for FUTURE iter-v1/NNN per the new skill discipline)**: 3 for EXPLORATION, 10 for CONFIRMATION (selected from the roster `[42, 123, 456, 789, 1001, 2002, 3003, 4004, 5005, 6006]`). The 10-seed CONFIRMATION standard applies to **new iteration work**, NOT to this baseline anchor.

**Training schedule**: `training_months = 24`, monthly retrain; OOS_CUTOFF_DATE = 2025-03-24.

**Optuna**: `n_trials = 50` per (symbol, month, seed) cell.

**Walk-forward**: `train_end_ms = test_start_ms - embargo_ms` (the iter-v3/058 fix; foundation discipline).

**Wall-clock (5-seed ENSEMBLE)**: 7h 0m total — Model A 2h 30m, Model C 1h 30m, Model D 1h 38m, Model E 1h 20m.

---

## Headline Metrics — Corrected Walk-Forward (5-seed)

### Comparison table (from `reports-v1/iteration_v1-baseline/comparison.csv`)

| Metric | In-Sample | Out-of-Sample | OOS/IS ratio |
|---|---|---|---|
| **Monthly Sharpe** | **+0.2829** | **+0.6637** | **2.346** |
| Monthly Sortino | +0.3205 | +0.7697 | 2.401 |
| Max Drawdown | 73.06% | 40.94% | 0.560 |
| Win Rate | 39.9% | 40.2% | 1.007 |
| Profit Factor | 1.060 | 1.156 | 1.091 |
| Total Trades | 621 | 189 | 0.304 |
| Calmar Ratio | 0.740 | 0.931 | 1.259 |
| **DSR** (Deflated Sharpe Ratio) | **−93.80** | **−35.66** | — |
| Total Net PnL | +54.05% | +38.13% | 0.706 |

### Higher-granularity statistics (post-hoc — daily PnL)

| Metric | In-Sample | Out-of-Sample |
|---|---|---|
| Daily Sharpe (annualized √365) | +0.4767 | +1.1913 |
| n_obs (days) | 416 | 131 |
| Skew | — | — |
| **PSR vs 0.0 benchmark (monthly)** | **0.977** | **0.989** |
| **PSR vs 1.0 benchmark (monthly)** | **0.0003** | **0.0789** |
| **PSR vs 0.0 benchmark (daily)** | **1.000** | **1.000** |

Note: PSR formulas computed via `crypto_trade.strategies.ml.validation_v1.psr` using monthly (n=39 IS, n=15 OOS) and daily (n=416 IS, n=131 OOS) granularities. Monthly granularity matches the skill's merge-gate semantics; daily is informational.

---

## Per-Symbol OOS PnL Attribution (`out_of_sample/per_symbol.csv`)

| Symbol | Trades | Wins | Win Rate | Net PnL % | Avg PnL % | % of Total OOS PnL |
|---|---|---|---|---|---|---|
| LINKUSDT | 28 | 14 | 50.0% | +34.23% | +1.22% | 137.66% |
| BTCUSDT | 35 | 16 | 45.7% | +33.17% | +0.95% | 133.38% |
| ETHUSDT | 46 | 18 | 39.1% | +2.75% | +0.06% | 11.08% |
| DOTUSDT | 46 | 18 | 39.1% | +1.96% | +0.04% | 7.88% |
| LTCUSDT | 34 | 10 | 29.4% | −47.25% | −1.39% | −189.99% |

**Top symbol concentration**: LINK at 137.66% of OOS PnL (driven by small denominator — total OOS PnL is only +24.87% absolute, so single-symbol concentration > 100% is achievable). On absolute net_pnl_pct, top contributor is LINK at +34.23%, second is BTC at +33.17%.

**LTC catastrophic OOS**: −47.25% net PnL is the worst contributor. The 5 new OOS trades from 2026-05-13 onwards contained 2 BTC losses (−2.13%, −1.88%), 2 ETH losses (−3.00%, −3.07%), and 1 DOT loss (−1.18%) — these dragged the OOS Sharpe from BASELINE.md's anchored +0.827 to the current +0.6637.

---

## Per-Symbol IS PnL Attribution (`in_sample/per_symbol.csv`)

| Symbol | Trades | Wins | Win Rate | Net PnL % | % of Total IS PnL |
|---|---|---|---|---|---|
| LINKUSDT | 146 | 66 | 45.2% | +72.06% | 141.34% |
| DOTUSDT | 93 | 39 | 41.9% | +26.62% | 52.22% |
| LTCUSDT | 124 | 49 | 39.5% | +3.27% | 6.42% |
| ETHUSDT | 145 | 56 | 38.6% | −13.70% | −26.87% |
| BTCUSDT | 113 | 38 | 33.6% | −37.28% | −73.11% |

**IS concentration**: LINK at 141.34% of IS PnL — heavily concentrated in LINK + DOT. BTC + ETH net negative in IS. (This is BEFORE Model A's pooling; per-symbol shares are independent of model attribution.)

---

## Per-Model Trade Attribution

| Model | Symbols | IS Trades | OOS Trades | Risk Layers |
|---|---|---|---|---|
| **A** (pooled) | BTC + ETH | 258 | 81 | R3 only |
| **C** | LINK | 146 | 28 | R1 + R3 |
| **D** | LTC | 124 | 34 | R1 + R3 |
| **E** | DOT | 93 | 46 | R1 + R2 + R3 |
| **Total** | 5 symbols | **621** | **189** | — |

Wall-clock per model (5-seed): A=2h 30m, C=1h 30m, D=1h 38m, E=1h 20m. Pooled Model A is materially slower than single-symbol models because it trains on combined BTC+ETH data (2× rows).

---

## Exit Reason Distribution

### In-Sample (621 trades)
| Exit Reason | Count | Share |
|---|---|---|
| stop_loss | 334 | 53.8% |
| timeout | 152 | 24.5% |
| take_profit | 135 | 21.7% |

### Out-of-Sample (189 trades)
| Exit Reason | Count | Share |
|---|---|---|
| stop_loss | 101 | 53.4% |
| timeout | 46 | 24.3% |
| take_profit | 40 | 21.2% |
| end_of_data | 2 | 1.1% |

**Regime stability check**: IS/OOS exit-reason distributions match to within 0.4 percentage points across all three exit modes (stop_loss / timeout / take_profit). The strategy's exit-reason mix is regime-stable.

---

## Risk Gate Fire Rates

| Gate | IS Fire Rate | OOS Fire Rate | Notes |
|---|---|---|---|
| **R2 drawdown brake** (weight_factor < 1.0) | 442/621 = 71.2% | 119/189 = 63.0% | Median weight 0.330 (anchor=0.15, floor=0.33). R2 fires aggressively; many trades scaled down. |
| **R1 cool-down** | (manifests as gaps in roster) | (manifests as gaps in roster) | Cannot measure fire count without decision log; future iteration adds tracking. |
| **R3 OOD Mahalanobis gate** | (manifests as gaps in roster) | (manifests as gaps in roster) | Same — needs decision-log instrumentation. |

R2 fires on **71%/63% of trades** indicating the drawdown brake is highly active — the model frequently encounters drawdown conditions during/after R3-gated entries. Future iter-v1/NNN axes may consider tuning R2 trigger / anchor / floor parameters or replacing the proportional scaling with a binary gate.

---

## Monthly PnL Distribution (OOS)

| Month | PnL % | Trades |
|---|---|---|
| 2025-03 | +5.48% | 2 |
| 2025-04 | −5.17% | 12 |
| 2025-05 | **−22.92%** | 22 |
| 2025-06 | +8.68% | 11 |
| 2025-07 | −14.36% | 15 |
| 2025-08 | +22.39% | 13 |
| 2025-09 | +8.74% | 9 |
| 2025-10 | +12.35% | 7 |
| 2025-11 | **+29.61%** | 11 |
| 2025-12 | −6.91% | 10 |
| 2026-01 | −3.34% | 16 |
| 2026-02 | −12.24% | 13 |
| 2026-03 | +25.83% | 17 |
| 2026-04 | −2.09% | 17 |
| 2026-05 (partial) | −7.92% | 14 |

**Monthly volatility**: range −22.92% (May 2025) to +29.61% (Nov 2025). Standard deviation of monthly returns is ~15% — large monthly swings. **Trades/month**: average 12.6, well above the project's ≥10/month floor.

---

## Per-Regime Coverage

| Sample | Regime | Trades | Win Rate | PnL % | Sharpe |
|---|---|---|---|---|---|
| In-Sample | unknown | 621 | 39.9% | +50.98% | 0.012 |
| Out-of-Sample | unknown | 189 | 40.2% | +24.87% | 0.022 |

**All trades fall into "unknown" regime** — the v1 baseline does NOT have a regime labeling layer. Future iter-v1/NNN may add a regime classifier (trend / range / vol-spike per the historical notebooks) to enable regime-conditional analysis. Per-regime breakdown is currently informational only.

---

## New OOS Trades (2026-05-13 → 2026-05-23) — Determinism Boundary

These 5 trades are the diff vs BASELINE.md's 2026-05-13 anchor. All 5 were entered on data freshly fetched on 2026-05-23. All 5 are net negative — that's why the OOS Sharpe dropped from +0.827 (anchor) to +0.6637 (current).

| Open | Close | Symbol | Direction | PnL % | Weighted PnL | Exit |
|---|---|---|---|---|---|---|
| 2026-05-13 23:59 | 2026-05-17 23:59 | BTCUSDT | long | −2.13% | −2.23% | stop_loss |
| 2026-05-15 15:59 | 2026-05-17 23:59 | ETHUSDT | long | −3.00% | −1.02% | stop_loss |
| 2026-05-19 07:59 | 2026-05-22 23:59 | ETHUSDT | long | −3.07% | −1.05% | stop_loss |
| 2026-05-18 23:59 | 2026-05-22 23:59 | BTCUSDT | long | −1.88% | −0.65% | end_of_data |
| 2026-05-16 15:59 | 2026-05-22 23:59 | DOTUSDT | long | −1.18% | −0.42% | end_of_data |

Net weighted PnL from the 5 new trades: **−5.38%**. The model entered long during a recent ~10-day correction phase and got stopped or held into losses.

---

## Hard Merge Floors (inherited from project)

New v1 iterations MERGE only if ALL of the following hold against this baseline:

| Gate | Threshold | Baseline current | Direction |
|---|---|---|---|
| IS monthly Sharpe | > 1.0 | +0.2829 | ▲ improve materially |
| OOS monthly Sharpe | > 1.0 | +0.6637 | ▲ improve materially |
| OOS / IS Sharpe ratio | ≥ 0.5 | 2.346 | ✓ holds |
| OOS trades/month | ≥ 10 | ~12.6 | ✓ holds |
| OOS total trades | ≥ 130 | 189 | ✓ holds |
| Top symbol concentration | ≤ 30% (absolute net_pnl, denominator dependent) | LINK 137.66% of OOS (denominator small) | ⚠ contextual — recompute against per-iteration's OOS PnL |
| **DSR** | > 0.95 | −35.66 (OOS) | ▲ improve dramatically (DSR is heavily negative at current edge level) |
| **PSR (monthly, vs benchmark=1.0)** | > 0.95 | 0.0789 (OOS) | ▲ improve materially |
| 10-seed mean Sharpe (CONF) | > 0 | n/a (baseline is 5-seed; first CONF will produce) | (TBD) |
| 10-seed profitable count (CONF) | ≥ 7/10 | n/a | (TBD) |
| **PBO** | < 0.40 | TBD (requires v1 CPCV — see Outstanding Tasks) | (TBD) |

**Material improvements needed for FIRST CONFIRMATION merge**:
1. **OOS monthly Sharpe (+0.66 → +1.0+)**: roughly +50% lift needed
2. **IS monthly Sharpe (+0.28 → +1.0+)**: roughly +250% lift needed — the IS is essentially noise at the baseline
3. **DSR (−35.66 → +0.95+)**: drastic. The current observed Sharpe is statistically indistinguishable from zero AFTER multi-test correction
4. **PSR (0.08 → 0.95)**: drastic — only 7.9% probability the true OOS Sharpe exceeds 1.0

**Holds without improvement** (but should not regress):
- OOS trades/month (~12.6 vs ≥10 floor)
- OOS total trades (189 vs ≥130 floor)
- IS/OOS Sharpe ratio (2.35 vs ≥0.5 floor — note this is artificially high because IS Sharpe is so low)

---

## Comparison Methodology

For new v1 iterations to claim "beats baseline":

1. **Headline comparison**: re-evaluate the iteration's full backtest under fixed `walk_forward.py:113` AND v1's full report layer (CPCV, DSR, PBO, PSR, ADF, IC, Pareto front for CONFIRMATIONs).
2. **Trade-level deterministic match**: per `feedback_deterministic_trade_match.md`, the iteration's BASELINE-stack trades (same config, same data extent) must match this baseline's trades bit-exactly. Divergence only on the iteration's actual axis change.
3. **Brief Section 2 evidence**: prior-iteration's `comparison.csv` row-level comparison with explicit OOS/IS deltas vs THIS baseline.
4. **Phase 7.5 Critic Check 3**: enforces DSR/PBO/PSR thresholds.
5. **Phase 7.5 Critic Check 6**: enforces Pareto dominance on 10-seed metric vector (CONFIRMATION only).
6. **Phase 7.5 Critic Check 14**: enforces Axis Family declaration matches actual src/ diff (v1 only).

Any single threshold failure = NO-MERGE per skill rules.

---

## Outstanding Tasks Before First v1 Iteration

The following must be in place before iter-v1/001 can launch and produce a CONFIRMATION-spec output:

1. ✅ `src/crypto_trade/run_baseline_v1.py` — v1 runner (DONE 2026-05-23)
2. ✅ `src/crypto_trade/features_v1/__init__.py` — V1_EXCLUDED_SYMBOLS / V1_FEATURE_COLUMNS (DONE 2026-05-23)
3. ✅ `src/crypto_trade/strategies/ml/validation_v1.py` — PSR + DSR + CPCV/PBO public API (DONE 2026-05-23)
4. ✅ Baseline reproduction run committed at `reports-v1/iteration_v1-baseline/` (DONE 2026-05-23 — this file)
5. ✅ `ITERATION_PLAN_8H_V1.md` at repo root (DONE 2026-05-23)
6. ✅ `briefs-v1/exploration_catalog.md` — empty initial ledger (TBD: create on iter-v1/001 startup)

**v1 runner extension work (deferred to iter-v1/001 or a follow-on infra iteration):**
- Wire `validation_v1.combinatorial_purged_cv` and `validation_v1.pbo_from_cpcv` into `run_baseline_v1.py` to produce `cpcv_paths.csv` + populate `pbo` in `comparison.csv` (45-path CPCV mandatory per skill).
- Compute and persist `n_effective_trials` (PCA on trial-return matrix at 95% cumulative variance) to populate `n_effective_trials` in `comparison.csv` and properly compute DSR with the multi-testing correction.
- Persist Optuna trial-level returns matrix to disk for DSR/PSR validation.
- Compute per-feature ADF p-value via `statsmodels.tsa.stattools.adfuller` → `adf_test.csv`.
- Compute pairwise feature-family IC → `ic_matrix.csv`.
- 10-seed × 6-metric Pareto front matrix for CONFIRMATION runs → `pareto_front.csv`.
- Meta-labeling M1 + M2 architecture wiring + fractional Kelly position sizing.

These additions land iteratively. iter-v1/001's first scope may legitimately be "wire the v3-style reporting layer into run_baseline_v1.py" (a methodology axis, not a research axis). Until those land, iterations can only produce the current report set + the post-hoc PSR/DSR computed in this BASELINE_V1.md.

---

## Historical Pre-Fix Numbers (DO NOT CITE)

For the record only:

| Metric | Pre-fix v0.186 (with lookahead, biased) | Post-fix 2026-05-13 anchor (BASELINE.md) | Post-fix 2026-05-23 (THIS FILE) |
|---|---|---|---|
| OOS Sharpe | +1.735 | +0.827 | +0.6637 |
| OOS Trades | 210 | 184 | 189 |
| OOS Win Rate | 43.8% | 42.4% | 40.2% |
| OOS Profit Factor | 1.41 | 1.20 | 1.156 |
| OOS Max Drawdown | 29.31% | 40.94% | 40.94% |
| IS Sharpe | +1.440 | +0.283 | +0.2829 |
| IS Trades | 594 | 621 | 621 |
| IS Profit Factor | n/a | 1.06 | 1.060 |
| IS Max Drawdown | n/a | n/a | 73.06% |

The historical headline (v0.186 = OOS Sharpe +1.735) was inflated by leaked labels. The 2026-05-13 anchor (BASELINE.md) was the first honest reproduction under the WF fix. The 2026-05-23 reproduction (this file) extends the OOS window by ~10 days; those days happened to be net negative for the strategy, pulling OOS Sharpe down from +0.827 to +0.6637.

**New v1 iterations target the 2026-05-23 corrected baseline** (this file, `v0.v1-baseline-corrected`).

---

## Audit Trail

- **2026-04-22** — Historical v0.186 baseline tagged on `main` (R3 OOD gate added; OOS Sharpe +1.735 — later found to be inflated by walk-forward lookahead bias).
- **2026-05-13** — Walk-forward fix `5566a69`: `train_end_ms = test_start_ms - embargo_ms`. Baseline re-ran; corrected stats captured in `BASELINE.md` (OOS Sharpe +0.827 / 184 trades).
- **2026-05-23** — v1 refactored. `BASELINE_V1.md` created (this file) with corrected stats on fresh data. The legacy `BASELINE.md` is kept for backward compatibility but `BASELINE_V1.md` is the canonical anchor for new v1 iterations.
- **2026-05-26** — Cycle-2 CLOSES NO-MERGE at iter-v1/015 CONFIRMATION-NEGATIVE catastrophic (tag `v0.v1-015`). 10 iterations, 1 PROMISING-METHODOLOGY (/008 non-compoundable) + 9 NEGATIVE + 0 merges. Anchor numbers UNCHANGED — see Cycle-2 Outcomes section below.

Future v1 iterations update **this** file (`BASELINE_V1.md`) on CONFIRMATION-MERGE per the skill's git workflow.

---

## Cycle-2 Outcomes (2026-05-23 → 2026-05-26)

**Cycle-2 CLOSES NO-MERGE.** v1 BASELINE_V1.md anchor numbers UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). Cycle-2 iteration ledger and per-iteration verdicts are in `briefs-v1/exploration_catalog.md` and `diary-v1/iteration_v1-*.md`.

**Iteration ledger (cycle-2)**:

| iter | family | verdict |
|---|---|---|
| /006 | universe | EXPLORATION-NEGATIVE (DEGENERATE_PREDICTOR) |
| /007 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) |
| **/008** | **methodology** | **EXPLORATION-PROMISING-METHODOLOGY** (n_eff PCA per-cell median; non-compoundable measurement substrate) |
| /009 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) |
| /010 | risk-primitive | EXPLORATION-NEGATIVE (PROMISING-INERT-with-IS-basin-shift) |
| /011 | risk-primitive | EXPLORATION-NEGATIVE (catastrophic-basin-shift) |
| /012 | methodology-substrate-test | EXPLORATION-NEGATIVE (BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP-PARTIAL) |
| /013 | methodology-substrate-test | EXPLORATION-NEGATIVE (BASIN-LOTTERY-CATASTROPHIC) |
| /014 | labeling | EXPLORATION-NEGATIVE (Cell-5 + PARTIAL-F7 + DURABLE-n_eff-MECHANISM) |
| **/015** | **labeling** (CONFIRMATION) | **CONFIRMATION-NEGATIVE catastrophic** |

**Cycle-2 verdict distribution**: 0 pure PROMISING / 1 PROMISING-METHODOLOGY non-compoundable (/008) / 9 NEGATIVE / 1 CONFIRMATION-NEGATIVE catastrophic / **0 edge ingredients merged**.

### Cycle-2 Structural Contributions (DURABLE — carry forward to cycle-3+)

1. **iter-v1/008 — n_eff PCA per-cell median** (`PROMISING-METHODOLOGY`, non-compoundable). Measurement substrate; informs all v1 brief Section 7 F-AXIS-MECHANISM falsifiers and Section 8 verdict matrices. Not bundled into any CONFIRMATION as an "edge ingredient" — but the substrate that makes F-AXIS-MECHANISM measurable.

2. **iter-v1/015 — n_eff barrier-magnitude curve** (NEW structural finding, codified at `feedback_v1_n_eff_barrier_magnitude_curve.md`). **n_eff is a CURVE in barrier-magnitude space, not a monotone-increasing function.** /014 at 1.70% labels → n_eff = 19; /015 at 7.82% labels → n_eff = 3 collapsed via timeout-fallback dominance. **Optimum likely in 3-5% middle range.** Forward-binding mandate: before any cycle-3+ labeling sub-axis EXPLORATION, run the n_eff calibration sweep at {1.5%, 2.5%, 3.5%, 5.0%, 7.82%} and establish n_eff ≥ 15 preservation band BEFORE selecting CONFIRMATION magnitude. Critic Phase 6.0 verifies the sweep at brief Section 2/7.

### Cycle-2 Methodology Lessons

- **DURABLE-EVIDENCE-OUTWEIGHS-EDA**: at /014 closeout, Critic + LM Master + Phase 6.0 + QR ALL converged on Path 1 (theoretically clean) over Path 2 (preserve durable n_eff=19 signal). Path 1 was empirically wrong; Path 2 was empirically right. **When prior iteration produces DURABLE STRUCTURAL EVIDENCE on a specific implementation, that evidence should OUTWEIGH EDA-prescribed magnitudes.** Future briefs Section 2/3 must explicitly tag durable-evidence claims + dissolution-risk reasoning when re-implementing axes.

- **LM Master mechanism-deterministic predictions earn MEDIUM confidence** (with "mechanism-deterministic" disclaimer). /015 produced FIRST DIRECTIONAL HIT in 13 v1 iterations: 3/3 per-symbol C1-inversion verified (LTC IS+OOS DOWN ✓, ETH IS+OOS UP ✓, BTC IS UP ✓). Mechanism-level track 6/13 PARTIAL+; verdict-class magnitude track remains 0/13 (FLAT priors).

- **HIGH-RISK pre-commit binding mitigation battle-tested**: /014 was the first cycle-2 HIGH-RISK declaration; /015 binding pre-commit fired regardless of /014's catastrophic basin draw — mitigation discipline functioning as designed. Cumulative compute saved across /003-/013 non-firings ≈ 54h; firing at /014→/015 was correct.

### Cycle-2 Closes — v1 Basin-Lock Pattern

v1 cycle-2 mirrors v3 cycle-7 saturation pattern (cf. `feedback_v3_cycle7_terminal_finding.md`): bounded by the prevailing architecture's local-optimum basin at single-axis EXPLORATION+CONFIRMATION resolution. The catalog is dispersed (no axis monoculture across 7 families touched) but each single-axis intervention is either INERT or NEGATIVE within v1's basin. **The basin is the binding constraint, NOT the axis selection.**

Cycle-3 considerations:
1. Multi-axis composition at the CONFIRMATION layer (e.g., universe expansion + sample-weighting bundled)
2. Explicit basin-escape mechanisms (universe denominator expansion; XGBoost depth-wise model swap)
3. NEW UNUSED families (`sample-weighting`) with explicit single-axis isolation first
4. Wall-clock discipline enforced: 2h EXPLORATION / 6h CONFIRMATION caps per skill `4cb8972` (non-negotiable per user directive 2026-05-25); /015 was the last user-authorized exception

### Cycle-2 Dead Paths (do not retry without new evidence)

- Per-leg differentiated Optuna bounds (/005 F2 ρ STRUCTURAL-locked at 0.95 across radically different axis interventions)
- ATR-multiplier per-leg asymmetry (/004 ETH SL-noise-floor death — absolute SL distance < 1.5× NATR_p50 red line)
- σ_t labeling at 7.82% portfolio-median magnitude (/015 n_eff collapse via timeout-fallback dominance)
- Methodology-substrate-test family at single-seed (/012/013 effectively NEGATIVE; basin-substrate properties at single-seed are not the binding lever)
- 7-feature INERT pruning beyond V1_FEATURE_COLUMNS_PRUNED 40-col target (/009 NEGATIVE-NEGATIVE compound)
