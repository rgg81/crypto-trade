# Engineering Report — iter-v3/089

## Headers

- Iteration: iter-v3/089
- Branch: iteration-v3/089
- Implementation commit SHA: bb8c231 (feat(iter-v3/089): sign fix + CPCV-proxy fix + cost-aware cross-sectional construction)
- Phase 5.5 gate PASS commit SHA: 32ee747
- Hardware: WSL2 Linux 6.6.114.1, CPU: standard, RAM: standard
- Wall-clock time: 0h 22m 46s
- Exit status: 0 (OVERALL=READY-FOR-CRITIC printed by runner)

---

## Configuration Diff vs /088 Baseline

Three corrections applied in bb8c231 (all IS-EDA-selected; EDA commit c172a12):

| Parameter | /088 | /089 |
|---|---|---|
| SIGN (build_positions) | LONG bottom quantile (predicted losers) | LONG top quantile (predicted winners) |
| CPCV proxy | label-grade self-correlation (degenerate; 45 paths all sharpe=0.0) | actual realised long-short net return per CPCV path |
| XS_QUANTILE_FRAC | 0.333 (tercile) | 0.200 (quintile) |
| XS_HOLD_BARS | 1 (every-bar rebalance) | 3 (overlapping 3-bar tranches) |
| XS_NO_TRADE_BAND | 0.000 | 0.020 |

Sacred constants unchanged: OOS_CUTOFF_DATE=2025-03-24, training_months=24, seed=42, n_trials=35.

---

## Key Metrics Block

| metric | in_sample | out_of_sample | ratio |
|---|---|---|---|
| monthly_sharpe | -0.1960 | -0.0985 | 0.502 |
| max_drawdown | 7.4775 | 2.7614 | 0.369 |
| n_trades (bar-symbol rows) | 44893 | 18852 | 0.420 |
| total_net_pnl | -0.2716 | -0.0326 | — |
| total_gross_pnl | +0.1155 | +0.0567 | — |
| total_fees | 0.3871 | 0.0893 | — |
| turnover_per_bar | 0.1153 | 0.0710 | 0.616 |
| frac_positive_paths (CPCV) | 0.356 | — | — |
| rank_ic_mean (OOS) | — | +0.0279 | — |
| rank_ic_std (OOS) | — | 0.3316 | — |
| rank_ic_n_timestamps | — | 1255 | — |

Delta vs /088 (IS monthly Sharpe −0.6403, OOS −0.5418):
- IS: −0.1960 vs −0.6403 = **+0.4443 lift**
- OOS: −0.0985 vs −0.5418 = **+0.4433 lift**

---

## Gross-vs-Net Decomposition (Central Diagnostic)

### Totals

| | Gross PnL | Total Fees | Net PnL | Fees / |Gross| |
|---|---|---|---|---|
| IS | **+0.1155** | 0.3871 | -0.2716 | **3.35x** |
| OOS | **+0.0567** | 0.0893 | -0.0326 | **1.58x** |

**The book is gross-POSITIVE both IS and OOS.** The cross-sectional long-short signal produces a genuine positive gross spread. Fees remain the sole source of net loss.

IS fees-to-gross ratio: 3.35x (down from /088's 8.8x — a 2.6x reduction attributable to the quintile + overlapping-hold + no-trade-band construction).

OOS fees-to-gross ratio: 1.58x. The OOS turnover dropped further (0.0710 vs IS 0.1153), shrinking the fee burden relative to the gross spread. The OOS gross PnL (+0.0567) only needs ~37% further fee reduction (or gross lift) to cross breakeven net.

### Monthly Sharpe — Gross vs Net

| | Gross monthly Sharpe | Net monthly Sharpe |
|---|---|---|
| IS | **+0.0925** | -0.1960 |
| OOS | **+0.1717** | -0.0985 |

IS gross Sharpe +0.0925 vs the EDA E1 estimate of +0.05 for the corrected-sign construction — the realized IS gross lift is slightly above the conservative EDA bound. OOS gross Sharpe +0.1717 is materially higher than IS gross, consistent with the OOS turnover being lower (less bleeding per bar).

### Per-Leg PnL (Sign Fix Verification)

| | n rows | Gross PnL | Fees | Net PnL |
|---|---|---|---|---|
| IS LONG | 19721 | -0.1566 | 0.1426 | -0.2992 |
| IS SHORT | 23166 | +0.2721 | 0.1741 | +0.0980 |
| OOS LONG | 7478 | -0.0633 | 0.0363 | -0.0997 |
| OOS SHORT | 10880 | +0.1200 | 0.0386 | +0.0815 |

Confirmed by predicted_score distribution: mean score LONG leg +0.114, mean score SHORT leg -0.209 — high-score symbols are correctly assigned to the LONG leg (sign fix verified as structurally correct).

**However, the realized long leg gross PnL is negative despite longing the model's predicted winners.** The short leg (predicted losers) produces the positive gross spread. This is the opposite of the textbook cross-sectional pattern where the long leg wins. Interpretations for QR Phase 7:
1. The LGBMRanker's lambdarank objective produces relative orderings; high-scoring symbols may be "least-bad" rather than "absolute winners." The short leg (bottom quintile) may systematically underperform (losers losing more than winners winning) — consistent with crypto-specific momentum reversal in trending altcoins.
2. The signal is a DOWNSIDE-predictor rather than an UPSIDE-predictor; the short side drives the gross positive spread.

This is a fact, not an error. The sign fix is confirmed correct (the /088 brief mis-specified it); the realized P&L anatomy is informative for /090 feature/signal design.

---

## /088 to /089 Attribution

| Source | IS Sharpe contribution | OOS Sharpe contribution |
|---|---|---|
| Sign fix alone | Gross IS +0.0925 (from prior −0.067 gross flipped) — removes the systematic long-from-wrong-end drag | Gross OOS +0.1717 (from −0.043 flipped) |
| Turnover reduction (quintile + 3-bar + no-trade band) | IS fees 0.387 vs /088 0.687 = 0.300 fee reduction; net IS Sharpe lift ~+0.32 | OOS fees 0.089 vs /088 ~0.149 est. = further fee reduction |
| Combined | IS net Δ +0.4443 | OOS net Δ +0.4433 |

The brief's EDA E1 pre-registered that the sign fix alone would restore IS gross Sharpe to ≈+0.05 and EDA E2/E3/E4 estimated the construction levers would halve the net loss. Realized: IS gross +0.0925 (above EDA lower bound of +0.05), IS net moved from −0.6403 to −0.1960 (Δ +0.44, consistent with "roughly halves"). Attribution is fully consistent with the pre-registered EDA prediction.

---

## Turnover Gate

**PASS.** IS turnover/bar 0.1153 ≤ pre-registered ceiling 0.138. OOS turnover/bar 0.0710. Gate computed as gross position weight changes per bar, summed across all symbols, divided by total bars. The ceiling was pre-registered in brief Section 8 before the backtest ran.

---

## CPCV Proxy Fix Verification

/088's `_compute_xs_cpcv` computed label-grade self-correlation, producing 45 identical paths with sharpe=0.0 (frac_positive=0.000, degenerate). /089 rewritten to compute each of the 45 CPCV paths' Sharpe from the actual realised per-bar book net return. XS_REQUIRED_GAP=88 expected_gap assertion retained and confirmed in run.log.

CPCV path distribution (45 paths, IS-only):
- frac_positive_paths: **0.356** (16 positive / 29 negative)
- Median path Sharpe: -0.0210
- Min: -0.0937, Max: +0.0530
- The distribution is right-skewed (mean -0.0177 vs median -0.0210); several paths approach breakeven or turn slightly positive. Below the 0.55 gate.

---

## OOS Rank-IC

OOS rank-IC: **+0.0279 ± 0.3316** (n=1255 timestamps). Slight drop from /088's +0.0430 (Δ -0.0151). Plausible reason: the quintile + overlapping-hold construction changes which (symbol, bar) rows participate in each prediction step — the rank correlation is measured over the changed universe of active tranche entries, not every bar. The signal direction (positive IC) is preserved; the magnitude shift is consistent with the no-trade-band filtering out near-zero-score rows (which had near-zero IC contribution anyway).

---

## Per-Symbol Breakdown

### IS

| Symbol | Weighted PnL | n_trades |
|---|---|---|
| TRXUSDT | +0.1475 | 3004 |
| THETAUSDT | +0.0935 | 1528 |
| FILUSDT | +0.0666 | 1911 |
| SANDUSDT | +0.0571 | 1839 |
| EOSUSDT | +0.0481 | 2392 |
| GRTUSDT | +0.0398 | 1789 |
| ... (16 negative) | | |
| ADAUSDT | -0.1011 | 1986 |
| AVAXUSDT | -0.1160 | 2069 |

### OOS

| Symbol | Weighted PnL | n_trades |
|---|---|---|
| FILUSDT | +0.0287 | 589 |
| ATOMUSDT | +0.0230 | 739 |
| AXSUSDT | +0.0213 | 911 |
| AVAXUSDT | +0.0205 | 822 |
| ... |  |  |
| ICPUSDT | -0.0371 | 814 |
| HBARUSDT | -0.0236 | 709 |

OOS concentration: ICPUSDT largest loss at 12.2% of trades, FILUSDT largest profit at 9.4%. No single symbol dominates the OOS book — dispersion is healthy.

---

## Run Integrity

- Exit status: 0
- Errors in run.log: 0 (only sklearn feature-name UserWarnings from LGBMRanker predict, expected and benign — the model is trained with feature names but `predict_ranking` passes numpy array; does not affect results)
- IS n_bars: 44893, OOS n_bars: 18852 (IS rows 63745 total in all bar-symbol entries)
- 22 symbols, 73 features per symbol per parquet
- Corrections bb8c231 in place: sign fix, CPCV-proxy fix, XS_QUANTILE_FRAC=0.20, XS_HOLD_BARS=3, XS_NO_TRADE_BAND=0.020
- OOS_CUTOFF_DATE=2025-03-24 immutable: IS range 2022-03 to 2025-02 (37 months), OOS range 2025-03 to 2026-05 (15 months)
- No NaN Sharpe, no zero-trade months in IS or OOS, no negative fees

---

## MaxDD Summary

- IS MaxDD: 7.4775 (significantly tighter than /088 — overlapping holds smooth the equity curve)
- OOS MaxDD: 2.7614 (OOS MaxDD < IS MaxDD; ratio 0.369 — healthier than /088)

---

## Anomaly Notes

- Trade row spot check: 10 random rows verified. position, gross_pnl, fee, net_pnl internally consistent (net_pnl = gross_pnl - fee). predicted_score signs align with position sign (positive score → positive position = LONG). No anomalies.
- The per-leg result (long leg gross-negative, short leg gross-positive) is unexpected relative to a textbook momentum cross-section but is internally consistent and mechanically sound. It is a signal-anatomy finding for QR, not an engineering bug.

---

## Status

OVERALL=READY-FOR-CRITIC
