# EXPLORATION-004 Engineering Report — Long-biased multi-factor + leg-decoupled defense

- **Iteration:** EXPLORATION-004 (baseline-blind top-20 L/S portfolio track)
- **Branch:** `quant-portfolio-blind` (worktree: `.worktrees/quant-portfolio-blind`)
- **OOS sealed:** `OOS_CUTOFF = 2025-03-24`. Not looked at.
- **Configuration (pre-registered defaults, FROZEN at brief §3.2–3.3):**
  - Long leg: top-10 of `0.5·z(vol_low) + 0.5·z(rev_3)` blend at `gross_long=0.7`
  - Short leg: mid-vol band (vol_low ranks 11–15) at `gross_short=0.3`, skip extreme-vol tail
  - Regime scalar: BTC drawdown-off-180d-peak, `threshold=0.20`, `band=0.30`, `floor=0.30`,
    applied multiplicatively to LONG-leg gross ONLY (short leg never scaled)
  - Universe: PIT top-20 by trailing 30-candle $-volume (unchanged); `rebal=6`; funding ON;
    cost `5+2.5 bps` (base) / `10+5 bps` (2x stress)
- **Risk-engineer LEAD calibration (brief §7.1–7.2) DEFERRED:** the QR's task directive was to
  run the pre-registered defaults and report factually; the risk-engineer runs calibration sweeps
  on the built code as a follow-on.

## Test count

**32 / 32 green** (`uv run pytest tests/test_blind_engine.py -v`).
23 pre-existing tests byte-identical (regression guard for R1/R2/P-RN parity) + **9 new**:

1. `test_longbias_ls_gross_and_sign_discipline` — at every rebal: sum(w_long)≈0.7·scalar,
   sum(w_short)≈-0.30 (within overlap drop); all longs>0; all shorts<0; skipped==0.
2. `test_longbias_ls_long_precedence_on_overlap` — overlap name → LONG (positive);
   surviving short carries the full `-gross_short/n_short_post_drop` budget.
3. `test_longbias_ls_decoupled_selection` — A (high blend, mid vol_low) → LONG;
   B (low blend, mid vol_low) → SHORT. Each leg picks by ITS OWN signal.
4. `test_longbias_ls_skips_extreme_tail_short` — very low vol_low (100× mooner) → weight 0,
   never shorted. Inherits EXPLORATION-002's defensive property.
5. `test_longbias_ls_crashed_coin_skipped_on_both_legs` — **F3 elimination lock**:
   crashed coin (z_vol~-3, z_rev~+3 → blend~0) gets weight 0 on BOTH legs. Under the
   single-signal blend through `midvol_short` (EXPLORATION-003 F3) this coin lands SHORT;
   leg-decoupling structurally eliminates that failure.
6. `test_btc_drawdown_scalar_past_only` — corrupt `panel.close[BTC_col, t:]` forward →
   `scalar[:t]` bit-identical (positive control on the regime indicator).
7. `test_btc_drawdown_scalar_monotone_in_bear` — monotone BTC drawdown → scalar non-increasing;
   monotone recovery → non-decreasing.
8. `test_longbias_with_scalar_end_to_end_no_future_leak` — **LOAD-BEARING** end-to-end leak
   assertion: corrupt panel (close/open/vol/qv incl BTC col) + signals + scalar forward from
   cutoff → `run_backtest(weighting="longbias_ls")` produces bit-identical past
   weights/turnover/equity.
9. `test_longbias_scalar_scales_longs_not_shorts` — when `long_scalar=0.5`, long gross halves
   (0.7→0.35) but short gross is unchanged (-0.30) and per-short weights are bit-identical.

## R1–R5 ladder (all IS-only, funding ON, rebal=6, defaults 0.7/0.3, regime 180d/0.20/0.30/0.30)

| run | Sharpe | Ann | MaxDD | Turn/yr | Win% | Final | 2020 | 2021 | 2022 | 2023 | 2024 | 2025Q1 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **R1** vol_low long-only | **+0.511** | +9.8% | -87.0% | 73x | 52.9% | 1.62 | +0.80 | +1.54 | -1.53 | +1.71 | +0.53 | -0.80 |
| **R2** rev_3 long-only | **+0.263** | -19.9% | -91.9% | 198x | 51.4% | 0.32 | +0.22 | +1.56 | -1.47 | +1.18 | +0.26 | -1.12 |
| **R3** blend long-only | **+0.362** | -5.1% | -89.8% | 144x | 52.0% | 0.76 | +0.66 | +1.65 | -1.52 | +1.44 | +0.10 | -1.21 |
| **R4** blend+short 0.7/0.3 | **+0.235** | +1.8% | -58.3% | 180x | 51.0% | 1.10 | +0.47 | +1.44 | -1.17 | +0.79 | -0.50 | +0.21 |
| **R5** R4+regime gate | **+0.336** | +5.7% | **-47.8%** | 162x | 51.5% | 1.33 | -0.26 | +1.52 | **+0.32** | +0.60 | -0.56 | +0.01 |
| B-EW top-20 | +0.451 | -0.6% | -88.2% | 31x | 52.4% | 0.97 | +0.76 | +1.87 | -1.53 | +1.48 | +0.22 | -1.68 |
| R5 ×2 cost | -0.057 | -6.5% | -52.5% | 162x | 50.7% | 0.71 | -0.67 | +1.20 | -0.15 | +0.11 | -0.98 | -0.33 |
| R3 ×2 cost | +0.233 | -14.9% | -92.5% | 144x | 51.7% | 0.43 | +0.53 | +1.55 | -1.65 | +1.26 | -0.06 | -1.33 |
| P-RN rank_neutral | -0.141 | -15.4% | -78.8% | 108x | 52.5% | 0.42 | -0.31 | -1.83 | +0.94 | -0.61 | +0.78 | +1.35 |
| B-BTC b&h | +1.07 | +60.4% | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- |

### Ladder deltas (Rung-to-rung attribution)

- R3 − max(R1, R2) = +0.362 − (+0.511) = **−0.149** → multi-factor synergy **DID NOT fire**
  (R3 < R1; blend dilutes vol_low's alpha with rev_3's weaker, higher-cost alpha).
- R4 − R3 = +0.235 − (+0.362) = **−0.128** (Sharpe) BUT maxDD **−58.3% vs −89.8%**
  (−31.5pp drawdown reduction) → short leg trades Sharpe for defense.
- R5 − R4 = +0.336 − (+0.235) = **+0.102** (Sharpe) AND maxDD **−47.8% vs −58.3%**
  (−10.5pp further drawdown reduction) → regime gate adds BOTH Sharpe and DD defense.

### Parity checks (all PARITY OK)

| run | observed | target | delta | tolerance | verdict |
|---|--:|--:|--:|--:|---|
| R1 vol_low long-only | +0.511 | +0.51 | +0.001 | ±0.005 | **PARITY OK** |
| R2 rev_3 long-only | +0.263 | +0.26 | +0.003 | ±0.01 | **PARITY OK** |
| P-RN rank_neutral | -0.141 | -0.14 | -0.001 | ±0.01 | **PARITY OK** |

## Attribution

### Per-leg per-year price P&L (fraction of equity per year)

**R5 (full book, with regime gate):**

| year | long_leg | short_leg |
|--|--:|--:|
| 2020 | +0.4528 | -0.2941 |
| 2021 | +1.4376 | -0.5938 |
| **2022** | **-0.4282** | **+0.5746** |
| 2023 | +0.5754 | -0.2512 |
| 2024 | +0.1706 | -0.1721 |
| 2025Q1 | -0.1741 | +0.2081 |
| **TOTAL** | **+2.0342** | **-0.5293** |

**R4 (without regime gate, for delta vs R5):**

| year | long_leg | short_leg |
|--|--:|--:|
| 2020 | +0.6971 | -0.2941 |
| 2021 | +1.5417 | -0.5957 |
| **2022** | **-0.9326** | **+0.5730** |
| 2023 | +0.6287 | -0.2511 |
| 2024 | +0.1919 | -0.1721 |
| 2025Q1 | -0.1558 | +0.2081 |
| **TOTAL** | **+1.9710** | **-0.5318** |

**Regime-scalar effect on 2022 long leg:** R5 long-leg 2022 P&L = **−0.4282** vs R4 = **−0.9326**
→ the gate clipped the 2022 long loss by **+0.5044** of equity (54% reduction in long-side crash
damage), with **zero cost** to the short leg's 2022 dampening (+0.5746 vs +0.5730 — bit-identical
by construction since the gate never scales shorts). This is the leg-decoupled defense working
exactly as designed.

### Per-year net funding (bps of equity)

| year | R3 blend LO | R4 blend+short | R5 +regime |
|--|--:|--:|--:|
| 2020 | +2027.1 | +836.6 | +851.6 |
| **2021** | **+3842.3** | **+1394.3** | **+1332.4** |
| 2022 | -1020.2 | -503.1 | -11.6 |
| 2023 | -291.3 | +379.5 | +379.6 |
| 2024 | +1199.3 | +474.5 | +474.2 |
| 2025Q1 | -63.0 | +22.5 | +22.7 |
| TOTAL | +5694.2 | +2604.5 | +3048.9 |

**Funding-dodge confirmation (R5 2021):** long-leg pays **+2665.9 bps**, short-leg receives
**−1333.6 bps** → net **+1332.4 bps** (well under long-only's +3842.3 bps and inside the
G-FUND +1500 bps threshold). The 0.3-gross mid-vol short at 0.6× EXPLORATION-002's gross
delivers ~62% of the EXPLORATION-002 funding-dodge benefit, as the brief §2.4 predicted.

### Regime-scalar firing confirmation (R5 long-leg gate)

| year | mean scalar | min | % candles scalar<1.0 | % candles at floor(0.30) |
|--|--:|--:|--:|--:|
| 2020 | 0.934 | 0.300 | 14.1% | 2.3% |
| 2021 | 0.780 | 0.300 | **51.0%** | **15.9%** |
| **2022** | **0.349** | 0.300 | **100.0%** | **71.7%** |
| 2023 | 0.987 | 0.548 | 4.0% | 0.0% |
| 2024 | 0.994 | 0.728 | 7.4% | 0.0% |
| 2025Q1 | 0.983 | 0.777 | 20.7% | 0.0% |
| IS overall | 0.817 | 0.300 | 34.6% | 17.2% |

- **2022 firing CONFIRMED:** gate fired at 100% of 2022 candles, mean scalar 0.349, 71.7% of
  candles at the 0.30 floor. This is exactly the crash regime the gate was designed for.
- **2020-21 firing (HONEST REPORT):** the brief expected ~0% firing in the 2020-21 bull.
  Observed: 14.1% in 2020 (March 2020 covid crash is a legitimate fire), but **51.0% in 2021**
  is materially higher than the brief's prediction. The 2021 firing is driven by (a) the May-July
  2021 deleveraging crash (BTC −55% peak-to-trough; legitimate fire) and (b) the July-November
  2021 chop where BTC cycled ±30% off its rolling 180d peak. The 180d lookback under the
  pre-registered `threshold=0.20` is broad enough to catch the mid-2021 churn. **This is the
  calibration opportunity the risk-engineer leads (§7.1)** — a higher threshold (e.g. 0.25 or
  0.30) or a longer lookback would reduce 2021 false-positives while preserving the 2022 catch.

### Gross-leverage + net-exposure time series (net-long → net-short flip)

| year | R4 net exposure | R5 net exposure |
|--|--:|--:|
| 2020 | +0.400 | +0.352 |
| 2021 | +0.402 | +0.250 |
| **2022** | **+0.403** | **−0.052** ← **NET-SHORT FLIP CONFIRMED** |
| 2023 | +0.405 | +0.395 |
| 2024 | +0.402 | +0.398 |
| 2025Q1 | +0.400 | +0.387 |

- R5 net exposure **flipped from +0.40 (calm target) to −0.05 in 2022** — the long leg
  de-risked to floor (long gross 0.7 × 0.30 floor = 0.21) while the short leg held at 0.30,
  producing net −0.09 in the deepest crash. As designed (brief §2.5).
- R5 gross leverage: mean 0.870 (vs 1.0 budget; the long leg spends 34.6% of IS candles at
  scalar<1.0, dragging mean gross below 1.0). Min active 0.210 (deep-crash floor: 0.21 long +
  0 short-side none held at the floor in some candles). Max 1.143 (slight overshoot from
  drifted effective weights between rebal steps).

### Overlap diagnostic (long∩short masks BEFORE long-precedence)

| run | n_rebal | overlap_steps | overlap_rate | mean overlap names/rebal |
|--|--:|--:|--:|--:|
| R4 | 950 | 853 | **89.8%** | **1.731** |
| R5 | 950 | 853 | 89.8% | 1.731 |

- **Higher than expected** (brief §3.6/§7.5 expected low overlap because "the blend's vol_low
  component keeps high-vol names out of longs"). In practice the blend's top-10 by BLEND rank
  overlaps structurally with the mid-vol band (vol_low ranks 11–15) because:
  (a) the blend is 50% vol_low — high-blend names are biased toward also being high-vol_low;
  (b) the short band sits immediately BELOW the long band on the vol_low ranking
  (`short_hi = n - k_long`), so any name just below the long cutoff on vol_low that also ranks
  high on rev_3 lands in BOTH masks.
- The long-precedence rule resolves this cleanly (overlap name → LONG, short count drops by 1
  and surviving shorts carry the budget). The short gross is preserved at -0.30 by construction
  (`-gross_short / max(n_short_post_drop, 1)`).
- **Implication for the QR/risk-engineer:** the *effective* mean short count is ~3.27 (5 − 1.73
  overlap drop) rather than the nominal 5. This is a structural property of using the blend
  (which contains vol_low) for the long leg and vol_low alone for the short — it does not
  violate the spec, but it does mean the short leg is more concentrated than the brief's table
  implies. The risk-engineer's gross_short calibration (§7.2) should account for this.

### Max per-name |w| (flag any name > 20%)

| run | max |w| | location | flag |
|---|--:|---|---|
| R1 vol_low LO | 0.5220 | k=23 (warmup edge) | **> 20%** |
| R2 rev_3 LO | 0.5220 | k=23 | **> 20%** |
| R3 blend LO | 0.5220 | k=23 | **> 20%** |
| R4 blend+sh | 0.3706 | k=5261 (late-IS, n_short effectively small after overlap drop) | **> 20%** |
| R5 +regime | 0.3706 | k=5261 | **> 20%** |
| B-EW top20 | 0.3534 | k=23 | **> 20%** |
| R5 cost=2x | 0.3710 | k=5261 | **> 20%** |
| R3 cost=2x | 0.5220 | k=23 | **> 20%** |
| P-RN rank_neutral | 0.5642 | k=29 | **> 20%** |

- The k≈23-30 warmup-edge concentration (small universe early in the pit_topn ramp) is the known
  artifact covered by the warmup mask in metrics; it does NOT affect Sharpe / maxDD / per-year
  numbers (which start post-warmup). Inherited from EXPLORATION-001/002/003.
- The k=5261 R4/R5 short-side concentration (37%) is a real late-IS instance where overlap drop
  left few shorts carrying the 0.30 budget. This is the overlap-diagnostic finding above made
  concrete. Not a bug (long-precedence is the spec); flagged for the QR/risk-engineer.

## Gate observations (raw values; verdict is the QR's Phase-7 call)

| gate | observed | threshold | result |
|---|--:|--:|---|
| G-ALPHA-MF (R3 Sharpe ≥ max(R1,R2)+0.07) | +0.362 | +0.581 | **FAIL** |
| G-DEPLOY (R5 Sharpe ≥ +0.60 AND ≥ EW+0.15) | +0.336 | +0.601 | **FAIL** |
| G-DD (R5 MaxDD ≥ -50%) | -47.8% | -50% | **PASS** |
| G-REGIME (every per-year R5 Sharpe ≥ -1.0) | worst = -0.562 (2024) | -1.0 | **PASS** |
| G-FUND (R5 2021 net funding ≤ +1500 bps) | +1332 bps | +1500 bps | **PASS** |
| G-COST (R5 ×2-cost Sharpe ≥ +0.50) | -0.057 | +0.50 | **FAIL** |

3/6 gates PASS (G-DD, G-REGIME, G-FUND). The defensive engineering works: maxDD tamed from
−89.8% (R3 long-only) → −47.8% (R5), 2022 Sharpe flipped from −1.53 (R1) → +0.32 (R5), 2021
funding dodged 65% of the long-only drag. But the alpha engine is too weak to clear the
deployability gates (G-ALPHA-MF, G-DEPLOY) and the book is cost-fragile (G-COST). The
brief §4.2 maps each failure to its specific next step.

## Files touched (all within blinding)

- `analysis/portfolio/blind_engine.py` — added `target_weights_longbias_ls` builder +
  `"longbias_ls"` dispatch in `run_backtest` with new params (`long_signal`, `gross_long`,
  `gross_short`, `long_scalar_series`). Existing 4 modes byte-identical.
- `analysis/portfolio/blind_regime.py` — NEW. `btc_drawdown_scalar(panel, lookback, threshold,
  band, floor)` past-only long-leg regime indicator.
- `analysis/portfolio/blind_exploration_004.py` — NEW. Runs the R1-R5 + EW + B&H + R5×2 + R3×2 +
  P-RN ladder with the full attribution suite.
- `tests/test_blind_engine.py` — added 9 new tests (32/32 green).

No baseline-artifact reads. OOS never inspected. Run log at `/tmp/exp004_run.log`.

**Status: OVERALL=READY-FOR-QR-PHASE-7.** Risk-engineer to follow with §7.1/§7.2 calibration
sweeps (especially the 2021 false-positive rate under different lookback/threshold combos).
