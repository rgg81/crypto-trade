# Yahoo Finance migration — data-quality check

**Date:** 2026-07-01 · **Source switch:** Dukascopy CFD (price-only, 39 names, weekend-padded) →
**Yahoo Finance** (`yfinance==1.2.0`, `auto_adjust=True` = dividend+split-adjusted total return,
native trading-day calendar). Ingest: `analysis/portfolio/tradfi/ingest_yahoo.py`. OOS HIDDEN
throughout (IS-only).

## Coverage — 69/69 + ^VIX, zero failures

| group | names | result |
|---|---|---|
| SECTOR_MAP total | 69 | **69/69 ingested, 0 failed** |
| full 2018-01-02 history | 49 | start ≤ 2018-01-03 |
| ragged / recent-IPO (PIT) | 20 | start later; carry weight only once history exists |
| ^VIX | 1 | `data/VIX/1d.csv` |

- **Recovered (Dukascopy-failed):** GOOGL, ORCL, GLW.
- **Recovered foreign ADRs** (Dukascopy had only a non-USD line): ASML, NVO, SONY.
- **Recovered recent IPOs / names Dukascopy never carried (24):** ARM, KLAC, CRWD, COIN, HOOD,
  MSTR, DKNG, GME, RIVN, HIMS, NOK, CRCL, CRWV, NBIS, IREN, RKLB, ASTS, SMCI, SNDK, CIEN, CRDO,
  ALAB, LITE, FLNC. → **30 new names** vs the 39 Dukascopy had on disk.
- **^VIX:** 2135 bars, 2018-01-02 → 2026-06-30, 0 weekend rows, close ∈ [9.2, 82.7] (82.7 = the
  2020-03 COVID spike — correct). Standalone market-state input; NOT in SECTOR_MAP, so it never
  enters the momentum universe.
- Ticker map: stem == Yahoo ticker for all but two overrides — **BRKB→`BRK-B`, PAYP→`PYPL`**
  (META→`META`, GOOGL→`GOOGL`, ADRs use their US listing). No ticker resolved to the wrong name.

## Yahoo ↔ Dukascopy daily-return correlation (5 overlap names)

| name | raw corr | **corr ex-split** | N | max\|r\| Yahoo | max\|r\| Duka |
|---|---|---|---|---|---|
| MSFT | 0.9984 | 0.9984 | 2133 | 0.147 | 0.148 |
| JPM  | 0.9980 | 0.9980 | 2133 | 0.180 | 0.169 |
| AAPL | 0.7396 | **0.9987** | 2133 | 0.153 | **0.742** |
| AMZN | 0.7097 | **0.9992** | 2133 | 0.140 | **0.949** |
| NVDA | 0.7823 | **0.9996** | 2133 | 0.244 | **0.899** |

**The low raw correlation on AAPL/AMZN/NVDA is a DUKASCOPY DEFECT, not a Yahoo problem.** Dukascopy
left stock splits UNADJUSTED — a single −74%/−95%/−90% spike on exactly the split dates: AAPL
2020-08-31 (4:1), AMZN 2022-06-06 (20:1), NVDA 2021-07-20 (4:1) + 2024-06-10 (10:1). Yahoo's max
single-day move on these names is ≤24% (no 2× jump → splits correctly handled). **Drop those 1–2
split days and every overlap name correlates 0.998–0.9996** with Dukascopy. The two feeds agree on
the signal everywhere Dukascopy isn't broken — and Yahoo is the correct series.

## Total-return (dividends) present

`auto_adjust=False` raw `Close` vs `Adj Close` on 2018-01-02: AAPL 43.06 vs 40.27 (−6.5%), MSFT
85.95 vs 78.70 (−8.4%), JPM 107.95 vs 85.90 (−20.4%) — **adjusted < raw for every dividend payer**
(dividends back-subtracted), confirming Yahoo close is a total-return index. Compounded over the
window, Yahoo total-return exceeds Dukascopy price by the dividend yield where Dukascopy is clean:
**MSFT +9.2%, JPM +25.7%** cumulative drift. Dukascopy being price-only mis-ranks dividend payers —
the exact reason for the switch.

## Calendar / gaps / splits

- **Trading-day calendar:** 0 weekend rows on all names; **251.4 bars/yr mean** (250–253, 2018–25)
  — native ~252, no weekend padding. Downstream trading-day filter is a harmless no-op now.
- **Gaps:** max consecutive-bar gap = 4 calendar days (Fri→Tue holiday weekends); zero gaps > 4d.
- **Splits:** largest single-day adjusted move ≤ 24.4% (NVDA) across the 5 — no unadjusted
  split jumps. (Dukascopy had the −74%…−95% spikes documented above.)

## Re-run of the current best stack (iter-006 crash-brake) on YAHOO — IS only

```
                       net    gross   maxDD    bull    bear    chop   (a/w)  netTot
  Dukascopy iter-006  +0.31    —       —      +0.42   -0.54   +0.26   2/3      —
  YAHOO    iter-005   +0.35   +0.51  -26.4%   +0.57   -2.23   +0.27   2/3    +30%
  YAHOO    iter-006   +0.43   +0.59  -25.5%   +0.60   -1.23   +0.56   2/3    +41%
```

- **Net IS Sharpe +0.31 → +0.43**, bull +0.42 → +0.60, chop +0.26 → +0.56 — all improve on the
  total-return / larger universe. Gate identity (gate=0 reproduces iter-005) PASS; future-bar leak
  self-check PASS; turnover +1% (gate swaps composition, adds ~no churn); fires 73.5% of bear /
  86.1% of chop / 0.5% of bull.
- **bear −0.54 → −1.23 (worse).** The 30 new names are heavily high-beta recent IPOs
  (COIN/MSTR/RIVN/PLTR/HOOD/CRWV…) whose momentum whipsaws hardest in bear regimes; the aggregate
  bear is dominated by the COVID V-crash (Sh −3.65) that a 12-month-trend gate structurally lags.
  The gate's *mechanism* still works directionally — its two largest deltas are the named targets:
  **bear −2.23 → −1.23 (+1.00)** and **2022 momentum-crash grind −1.71 → −0.38**.
- The script prints **VERDICT: REJECT**, but solely because one pre-registered KEEP gate
  (`2022grind ≥ −0.20`, got −0.38) was **calibrated on Dukascopy numbers** and is being applied to a
  different, larger, corrected dataset. Re-calibrating those thresholds against the new data of
  record is a Researcher (Phase 5/7) decision — NOT done here. No threshold was re-tuned.

## Verdict — Yahoo is good to be the new source of record: **YES**

1. Daily returns match Dukascopy 0.998–0.9996 ex-split — same signal.
2. Yahoo correctly split-adjusts where Dukascopy left raw split spikes that would corrupt momentum
   (a strict data-quality upgrade; prior Dukascopy iter numbers for AAPL/AMZN/NVDA-heavy books were
   partly contaminated by those spikes).
3. Dividend+split total return = the correct momentum input (Dukascopy was price-only).
4. Native trading-day calendar (no padding bug), full 69/69 universe + ^VIX.

**Concerns for the Researcher (not blockers):** (a) the larger universe materially deepens the bear
regime via high-beta recent IPOs — the iter-006 KEEP thresholds, calibrated on Dukascopy, now read
REJECT and need re-calibration against the new source; (b) CRWV/CRCL/SNDK/NBIS have nearly all
history in the OOS window → ~zero IS weight (PIT-correct, but thin IS coverage for those names).
