# EXPLORATION-003 — Engineering Report

## Headers
- Iteration: EXPLORATION-003 (multi-factor rev_3 blend: `0.5·z(vol_low) + 0.5·z(rev_3)` in the EXPLORATION-002 mid-vol shell)
- Track: baseline-blind top-20 L/S portfolio
- Worktree: `quant-portfolio-blind`
- Date: 2026-07-09
- One change: replace the single-factor signal `lowvol_signal(panel)` with an equal-weight cross-sectional z-blend `0.5·z_cs(vol_low) + 0.5·z_cs(rev_3)`. Shell (`weighting="midvol_short"`, long_frac=0.5, short_frac=0.25, gross=1.0, rebal=6, cost 5+2.5bps, funding ON, PIT top-20-$-volume universe) byte-identical to EXPLORATION-002.
- OOS: **SEALED** (`OOS_CUTOFF = 2025-03-24`; panel sliced via `slice_is`; OOS never inspected).

## Test Status

- **23/23 green** (18 pre-existing + 5 new EXPLORATION-003 tests). Existing 18 untouched (regression guard).
- New tests (`tests/test_blind_engine.py`):
  - `test_rev3_signal_past_only` — leak positive-control: corrupt close/open/vol from cutoff forward → `rev3_signal[:cutoff]` bit-identical.
  - `test_cs_zscore_past_only` — `_cs_zscore_2d` uses only same-timestamp cross-section; corrupting arr/univ forward leaves z[:cutoff] bit-identical (with a vacuous-test guard asserting the corruption changed something after cutoff).
  - `test_blended_signal_no_future_leak` — **LOAD-BEARING end-to-end**: corrupt panel forward → `blended_signal` + `run_backtest(midvol_short)` produce bit-identical past weights/turnover/equity.
  - `test_blended_skips_agreement_outlier` — agreement case (z_vol = z_rev = −5): the simulated 100× mooner is skipped (w=0), never shorted. Defensive property holds when both signals agree.
  - `test_blended_crashed_coin_lands_short` — **behavior lock** (not a desirability assertion): a coin with z(vol_low)=−3 AND z(rev_3)=+3 → blended z=0 → SHORT band (w<0). Documents the known disagreement-case risk the brief §2 flagged. Cross-checks that under vol_low-only the same coin is SKIP (w=0), confirming the behavior delta.

## Engine Changes

**NONE.** The blend happens entirely at signal construction; `run_backtest` takes the blended signal as a raw `(T,C)` array and `target_weights_midvol_short`'s internal `rankdata` handles it. No engine code, no builder, no `BacktestResult` field touched.

## Files Touched (all within blinding constraint `blind_*.py` / `tests/test_blind_engine.py` / `diary-portfolio-blind/`)

- `analysis/portfolio/blind_signals.py` — **NEW**: `rev3_signal`, `_cs_zscore_2d`, `blended_signal`; re-exports `lowvol_signal` from `blind_sanity_lowvol` byte-identically.
- `analysis/portfolio/blind_exploration_003.py` — **NEW**: run script (9-run table producer + attribution).
- `tests/test_blind_engine.py` — 5 new tests appended; import of `blind_signals` helpers added.
- `diary-portfolio-blind/EXPLORATION-003-engineering.md` — this report.

Linter: `uv run ruff check` clean on all three files. Formatter: `uv run ruff format` applied.

## 9-Run Table (IS-only, all funding ON, rebal=6, gross=1.0, midvol_short shell unless noted)

| run | signal / weighting | sharpe | ann | maxDD | turn/yr | win% | final | per-year Sharpe |
|---|---|---:|---:|---:|---:|---:|---:|---|
| **1 blended** | `0.5·z(vol_low)+0.5·z(rev_3)` / `midvol_short` | **−0.36** | −12.3% | **−61.3%** | 204x | 51.4 | 0.51 | 2020:−0.19 / 2021:+0.48 / 2022:+0.27 / 2023:−1.10 / 2024:−1.39 / 2025:+0.68 |
| 2 vol_low | `lowvol_signal` raw / `midvol_short` | **+0.09** | −1.3% | −48.5% | 138x | 52.2 | 0.94 | 2020:+0.81 / 2021:−0.38 / 2022:+0.89 / 2023:−0.79 / 2024:−0.34 / 2025:+3.18 |
| 3 rev_3 | `z_cs(rev_3)` / `midvol_short` | **−0.65** | −19.3% | −72.1% | 230x | 48.1 | 0.33 | 2020:−2.10 / 2021:+0.20 / 2022:−1.47 / 2023:−0.28 / 2024:+0.02 / 2025:−0.65 |
| 4 ew_long | `lowvol_signal` / `ew_long` | +0.45 | −0.6% | −88.2% | 31x | 52.4 | 0.97 | 2020:+0.76 / 2021:+1.87 / 2022:−1.53 / 2023:+1.48 / 2024:+0.22 / 2025:−1.68 |
| 5 long-only | `lowvol_signal` / `longonly_tophalf` | +0.51 | +9.8% | −87.0% | 73x | 52.9 | 1.62 | 2020:+0.80 / 2021:+1.54 / 2022:−1.53 / 2023:+1.71 / 2024:+0.53 / 2025:−0.80 |
| 6 b&h BTC | — | +1.07 | +60.4% | — | — | — | — | (benchmark, not through pipeline) |
| 7 blend@2x | blended / `midvol_short` @ 10+5bps | −0.94 | −24.9% | −79.8% | 204x | 50.4 | 0.23 | 2020:−0.88 / 2021:−0.07 / 2022:−0.34 / 2023:−1.68 / 2024:−1.93 / 2025:+0.15 |
| 8 vol@2x | vol_low / `midvol_short` @ 10+5bps | −0.29 | −11.0% | −59.7% | 138x | 51.4 | 0.55 | 2020:+0.37 / 2021:−0.75 / 2022:+0.46 / 2023:−1.13 / 2024:−0.67 / 2025:+2.79 |
| 9 rev@2x | rev_3 / `midvol_short` @ 10+5bps | −1.29 | −32.2% | −88.4% | 231x | 47.3 | 0.13 | 2020:−2.85 / 2021:−0.40 / 2022:−2.08 / 2023:−0.96 / 2024:−0.59 / 2025:−1.19 |

## Alpha-Attribution: rev_3 Marginal Contribution (the core question)

| metric | value |
|---|---:|
| blended Sharpe (run 1) | **−0.363** |
| vol_low Sharpe (run 2) | +0.088 |
| rev_3 Sharpe (run 3) | −0.653 |
| **delta (blended − vol_low-only)** | **−0.451** ← rev_3 marginal alpha net-of-cost |
| delta (blended − rev_3-only) | +0.290 ← vol_low marginal contribution to the blend |

**rev_3 did NOT add alpha. It destroyed it.** The blend (−0.36) is **0.45 Sharpe below** the vol_low-only book (+0.09) — the opposite of the brief's +0.20 G-ALPHA target. rev_3-only is itself deeply negative (−0.65), so the 0.5/0.5 blend inherits rev_3's drag rather than diversifying toward a higher combined IC. The combined-IC math in the brief (`√(0.052²+0.045²)=0.069 → +33% IC lift`) did NOT survive the midvol_short partition net-of-cost: rev_3's 230x turnover (vs vol_low's 138x) eats any gross spread, and the midvol partition apparently does not convert rev_3's raw cross-sectional IC into realizable return-alpha in this shell.

## Funding-by-Year Attribution (bps of equity)

Sign convention: **+ = net drag (longs pay more than shorts receive), − = net income (shorts receive more than longs pay).**

| year | 1 blended | 2 vol_low | 3 rev_3 |
|---|---:|---:|---:|
| 2020 | −80.5 | +124.9 | −119.5 |
| 2021 | **−165.2** | **−240.4** | +100.0 |
| 2022 | +85.2 | +287.8 | −757.1 |
| 2023 | +346.5 | +1184.9 | −943.6 |
| 2024 | +98.9 | −145.4 | +136.8 |
| 2025 | +49.7 | +142.9 | −72.8 |
| **TOTAL** | **+334.6** | +1354.7 | **−1656.2** |

The near-neutrality funding dodge holds for the blended book (2021 = **−165 bps net income**, well within any plausible G-FUND threshold). rev_3-only is actually a larger net funding *earner* over the full IS window (−1656 bps total) because its high turnover rotates more frequently into short positions that receive mania funding — but that funding income is dwarfed by its price-P&L losses.

## Per-Leg Price P&L Attribution — Blended Book (run 1; fraction of equity per year)

Sign convention (matches `_leg_price_pnl_by_year` helper docstring): **long_leg + = longs profited (prices rose); short_leg + = shorts profited (prices fell).**

| year | long_leg | short_leg |
|---|---:|---:|
| 2020 | +0.5063 | −0.4434 |
| 2021 | +1.0904 | −0.8184 |
| 2022 | −0.6744 | **+0.9020** |
| 2023 | +0.4472 | −0.5471 |
| 2024 | +0.1410 | −0.3854 |
| 2025 | −0.1101 | +0.1929 |
| TOTAL | +1.4003 | −1.0995 |

Both legs contribute (long total +1.40, short total −1.10). The long leg is the primary positive driver (2020/2021/2023 bull-capture); the short leg captures the 2022 bear (+0.90 — analog to vol_low's +0.93 in EXPLORATION-002) but loses in mania/rally years. The blend's negative overall Sharpe is not from one leg dominating — it is from the blend's 2023 (−1.10) and 2024 (−1.39) regressions where both signals misfire simultaneously in the midvol partition.

## Orthogonality Diagnostic (DIAGNOSTIC-001 confirmation)

- Avg cross-sectional rank-corr(vol_low, rev_3) over **943 IS rebal steps = −0.0356**.
- DIAGNOSTIC-001 target: **−0.006**. Delta: −0.030. Within the 0.05 tolerance → **ORTHOGONAL (matches DIAGNOSTIC-001)**.

The two signals are genuinely uncorrelated cross-sectionally in production. The combined-IC math failure is therefore NOT an orthogonality breakdown — the signals are orthogonal but their blend does not survive cost/partition. This implicates cause (b) or (c) from the brief's G-ALPHA-failure analysis: either "rev_3's turnover cost eats the spread" or "rev_3's IC doesn't survive the midvol_short partition." Given rev_3-only is −0.65 at 230x turnover, both are operative; cost-fragility (230x) is the larger lever (see cost-robustness below).

## Max Per-Name Weight (|w|; flag if any name > 20%)

| run | max \|w\| | location | flag |
|---|---:|---|---|
| 1 blended | 0.5000 | k=30, col=155 | **\|w\| > 20%** (warmup edge: k=30 < warmup=63) |
| 2 vol_low | 0.5000 | k=30, col=155 | **\|w\| > 20%** (warmup edge) |
| 3 rev_3 | 0.5006 | k=35, col=250 | **\|w\| > 20%** (warmup edge) |
| 4 ew_long | 0.3534 | k=23, col=155 | **\|w\| > 20%** (warmup edge) |
| 5 long-only | 0.5220 | k=23, col=155 | **\|w\| > 20%** (warmup edge) |
| 7 blend@2x | 0.5000 | k=30, col=155 | **\|w\| > 20%** (warmup edge) |
| 8 vol@2x | 0.5000 | k=30, col=155 | **\|w\| > 20%** (warmup edge) |
| 9 rev@2x | 0.5010 | k=35, col=250 | **\|w\| > 20%** (warmup edge) |

All max-|w| excursions occur at k < warmup (63) — same pit_topn_universe lookback-ramp edge effect as EXPLORATION-001/002; excluded from metrics by the warmup mask. Post-warmup per-name long = 0.05 (gross_long=0.5/10), per-name short = 0.10 (gross_short=0.5/5).

## Gross-Leverage Series (target = 1.0; confirm no drift)

| run | mean | max | min_active |
|---|---:|---:|---:|
| 1 blended | 1.0014 | 1.3695 | 0.6551 |
| 2 vol_low | 1.0000 | 1.2744 | 0.5909 |
| 3 rev_3 | 1.0019 | 1.2903 | 0.6560 |
| 7 blend@2x | 1.0021 | 1.3710 | 0.6556 |
| 8 vol@2x | 1.0005 | 1.2750 | 0.5911 |
| 9 rev@2x | 1.0027 | 1.2912 | 0.6566 |

Blended mean gross = 1.0014 (target 1.0; negligible drift). Max excursions during warmup. Post-warmup gross stays tightly near 1.0.

## Dollar-Neutrality Confirmation (at each rebal)

| run | max\|sum(w)\| | mean\|sum(w)\| | n_rebal |
|---|---:|---:|---:|
| 1 blended | **1.11e-16** | 1.15e-17 | 950 |
| 2 vol_low | 2.50e-01 | 4.74e-04 | 950 |
| 3 rev_3 | 1.11e-16 | 1.21e-17 | 950 |

The blended and rev_3 books are dollar-neutral to **machine epsilon** (1e-16) at every rebal step — better than vol_low's 0.25 max (which is the valid_price force-exit artifact documented in EXPLORATION-002). The z-scored signals produce fewer single-name force-exit imbalances. Near-dollar-neutrality is confirmed.

## Cost-Robustness (2x-cost stress; isolates which signal drives cost-fragility)

| signal | base Sharpe | 2x-cost Sharpe | delta |
|---|---:|---:|---:|
| blended | −0.363 | −0.943 | −0.580 |
| vol_low | +0.088 | −0.288 | −0.376 |
| rev_3 | −0.653 | −1.289 | −0.636 |

rev_3 is the more cost-fragile signal (−0.636 Sharpe delta at 2x vs vol_low's −0.376), consistent with its higher turnover (230x vs 138x). The blend inherits roughly the average cost-sensitivity. This directly answers the brief's §3.6 run-8 diagnostic: **rev_3 alone is cost-fragile**, and that fragility propagates into the blend.

## Parity Checks

| run | actual | target | delta | verdict |
|---|---:|---:|---:|---|
| run-2 vol_low-only | +0.088 | +0.09 | −0.002 | **PARITY OK** |
| run-4 ew_long | +0.45 | +0.45 | 0.00 | PARITY OK |
| run-5 long-only | +0.51 | +0.51 | 0.00 | PARITY OK |

EXPLORATION-002's headline (+0.09) and the EXPLORATION-001 benchmarks reproduce bit-identically, confirming the signal-engineering change did not perturb the existing builders or the vol_low signal array.

## Observed Values vs Pre-Registered Thresholds (FACTUAL — gate verdicts are QR's Phase-7 call)

| gate | threshold | observed (blended primary) | factual delta |
|---|---|---:|---|
| G-ALPHA | IS Sharpe ≥ +0.29 | −0.36 | −0.65 below threshold |
| G-EW | IS Sharpe ≥ +0.60 (EW+0.15) | −0.36 | −0.96 below threshold |
| G-DEF-DD | MaxDD ≥ −60% | −61.3% | −1.3pp beyond threshold |
| G-DEF-REGIME | every per-year ≥ −1.0 | 2023:−1.10, 2024:−1.39 | two years below −1.0 |
| G-FUND | 2021 funding ≤ +1500 bps | −165 bps | 1665 bps inside threshold (income) |
| G-COST | 2x-cost Sharpe ≥ 0.5 | −0.94 | −1.44 below threshold |

Reported as raw observed-vs-threshold facts. The G-ALPHA, G-DEF-REGIME, and G-COST deltas are large and co-directional (negative); G-FUND is the only gate with comfortable headroom. The full PASS/FAIL verdict and weighting is the QR's Phase-7 job.

## Anomaly Notes

- **Blended Sharpe −0.36 is well below the brief's Section-5 prediction of +0.30 to +0.60**, and in the opposite direction. This is precisely the brief's §5 "informative null" case (G-ALPHA fails): rev_3's IC +0.045 does not survive realistic cost as a portable alpha source on the PIT-top-20-$-volume universe at 8h in the midvol_short shell. Given vol_low (+0.052) and rev_3 (+0.045) were the TWO STRONGEST orthogonal OHLCV cross-sectional signals DIAGNOSTIC-001 found, the brief's structural interpretation applies: this motivates a scope break (OI-ranked universe or different mechanism family), not a blend-weight tweak.
- **rev_3-only is −0.65, not just weak — deeply negative.** Its 230x turnover at base cost destroys gross alpha entirely. rev_3's raw cross-sectional IC (+0.045) does not convert to return-alpha through the midvol_short partition. This is the load-bearing diagnostic finding.
- **2021 blended Sharpe = +0.48 (improved vs vol_low's −0.38).** rev_3's mean-reversion DID help in 2021 (crashed coins bounced; the long book caught them) — the disagreement-case downside risk the brief flagged did NOT fire in 2021. However, 2023 (−1.10) and 2024 (−1.39) regressed badly below vol_low's (−0.79 / −0.34), dragging the full-IS Sharpe negative. The regression is concentrated in 2023-2024, not the mania-2021 year the brief's G-DEF-REGIME-2021 specifically worried about.
- **MaxDD −61.3% is marginally beyond the −60% G-DEF-DD threshold** (1.3pp over). Close to the line; within any reasonable slack the brief allowed ("some regression from −48.5% as the faster signal raises turnover"). The disagreement-case risk fired mildly but not catastrophically.
- **Dollar-neutrality improved to machine epsilon (1e-16)** for the blended and rev_3 books — better than vol_low's 0.25 max. The z-scored signals produce cleaner long/short balance at force-exit candles.
- **Orthogonality held in production (−0.036 vs −0.006 target)** — the combined-IC failure is NOT an orthogonality breakdown; it is cost/partition conversion failure.
- **Warmup edge effect recurred** (max |w| > 20% at k < 63) — same as EXPLORATION-001/002; expected and warmup-masked.

## Status

OVERALL = READY-FOR-QR-PHASE-7

OOS remains sealed. All G-ALPHA / G-EW / G-DEF-DD / G-DEF-REGIME / G-FUND / G-COST gate verdicts are the QR's call. The factual picture: rev_3 did not add alpha net-of-cost (blended −0.36 vs vol_low-only +0.09, delta −0.45); rev_3-only is itself −0.65 at 230x turnover; the funding dodge (G-FUND) held but the alpha/cost/regime gates present a strongly negative picture. No commits made (user owns the commit decision).
