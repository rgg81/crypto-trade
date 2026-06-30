# EXPLORATION-001 — Dollar-neutral XS-momentum anchor (iter-001)

**Date:** 2026-06-30
**Status:** COMPLETE — **NEGATIVE-CONFIRMED** (real, leak-free reject of the bare-momentum anchor). OOS HIDDEN.
**Cadence:** EXPLORATION (IS-only — `--confirm` NOT passed; OOS never revealed)

---

## Hypothesis

Dollar-neutral cross-sectional 12-1 month momentum (continuously weight each name by its risk-adjusted
12m-1m return — long above-average, short below-average), vol-targeted ~15%, should net a positive IS
Sharpe across ~2018→2025-03 (covering 2020 COVID + 2022 bear) without beta/sector neutralization, because
12-1 is a slow, persistent equity anomaly and the native-short perp removes the borrow cost that eats
cash-equity momentum. Establishes the anchor every later EXPLORATION beats.

**Pre-registered IS bar (QR brief):** promotable-direction ≥ +0.30 (healthy +0.50); REJECT ≤ +0.10/negative;
**> +1.0 = assume-leak, not a win**; all-weather (positive in ≥2 of 3 regimes, no catastrophic regime).

---

## Change

**From:** no baseline (track inception). **To:** dollar-neutral cross-sectional momentum portfolio.

- Universe: `universe_tradfi.py` — Binance `TRADIFI_PERPETUAL` single-company stocks, PIT. **39 of 42**
  sourceable from Dukascopy (GOOGL/ORCL/GLW failed fetch; 27 others dropped at the map stage — recent
  IPOs absent from Dukascopy + non-USD foreign ADRs).
- Signal: continuous `dollar_neutralize( (close.shift(21)/close.shift(252) - 1) / rolling_63_realized_vol )`
  — 12-1m momentum, inverse-vol scaled, cross-sectionally demeaned. NOT terciles (continuous magnitude).
- Execution: signal on CLOSE[t-1] → fill OPEN[t] → earn to OPEN[t+1]; taker ≈ 6 bps/side on |Δw|; no funding;
  portfolio vol-target 15%/yr ≤5× lev. `analysis/portfolio/tradfi/iter_001_xsmom.py`.

### Mid-iteration DATA-BUG fix (load-bearing — commit `eef9b524`)
The first run used **calendar-daily** Dukascopy bars (3102/name, ~28.7% zero-return weekend padding), so
`shift(252)` spanned ~8.3 *trading* months, not 12, and realized-vol was diluted by flat weekend rows —
**the canonical 12-1m spec was never actually tested.** Fixed `resample_daily` to emit **trading-day**
bars (drop weekday≥5 + flat `high==low` holiday bars): AAPL 3102→2133 rows, **~251.7 bars/yr**. Signal
unchanged — only the data grain corrected. This moved the headline −0.30 → −0.18 and flipped 2/3 regime
signs, confirming how badly the padding had corrupted the first read. All numbers below are trading-day.

---

## IS numbers (trading-day; IS-only < 2025-03-24)

| Metric | IS (~2019-01 → 2025-03-23) |
|--------|----------------------------|
| **Net Sharpe** | **−0.18** |
| Gross Sharpe (cost-off) | −0.04 → cost drag +0.14 → **loss is SIGNAL-driven, not cost-driven** |
| Max Drawdown | −45.2% |
| Net total return | −26% |
| Turnover | 0.086 /day (~21.7× one-way/yr) |
| Avg longs / shorts | 16.1 / 17.6 |
| Book sanity | gross Σ\|w\|=1.000, dollar-neutral to 1e-16, max name 24.3% (<25%) — **not degenerate** |
| Breadth | median 31 active names/month; first ≥20 in 2019-01; healthy |

**Per-regime (the all-weather check):** bull **−0.20** · bear **+0.36** · chop **−0.62** → fails all-weather
(positive in only 1 of 3 regimes; loss concentrated in chop).

**Per-year:** 2019 −0.90 · 2020 −0.30 · 2021 −0.91 · 2022 **+1.64** · 2023 −0.92 · 2024 +0.37 · 2025 +1.35.
Broad-based negative (loses in 4 of 7 years across both bull and chop) — **not a single-regime artifact**.

**Sign / lookback robustness (diagnostic, anchor unchanged):** anchor −0.18 · **negated −0.10** · 6-1m −0.13 ·
3-1m −0.04. The *entire* momentum neighborhood — and its negation — is IS-negative.

**Exposures:** realized net market-β **−0.003**; largest net sector tilt ConsDisc **−0.05** → the book is
already ~beta- and ~sector-neutral, so the planned iter-002/003 neutrality overlays **cannot rescue a
signal-level negative** (they remove exposure that is already ≈0).

---

## Leak-check result — **PASS (all three axes)**

| Check | Method | Result |
|-------|--------|--------|
| Future-bar | corrupt inputs after a cutoff; past net+weights bit-identical | **PASS** (`test_*future_bar*`, on the real `xsmom_raw`) |
| Same-bar | corrupt only close[t]; net ≤ t bit-identical | **PASS** (`test_production_xsmom_same_bar_close_no_leak`) |
| Trading-day filter | new weekend/flat-bar drop is per-bar, calendar-only, no forward scan | **PASS** (verified in on-disk data, `ingest_dukascopy_stocks.py:148-150`) |

The production signal (`dollar_neutralize(mom/rvol)`, op-order differs from the test proxy) is now directly
guarded — the one pre-flight gap (proxy-only leak tests) is CLOSED (commit `dd3597cd`). 16/16 foundation
tests green. `net_from_raw` lags weights `.shift(1)` before `ret_fwd`; OOS gate verified.

---

## Critic verdict — BLOCK-PENDING-FIX → **NEGATIVE-CONFIRMED**

The quant-critic PASSED leak (all three axes) and methodology (signal unchanged, no OOS peek, no tuning),
but issued **BLOCK-PENDING-FIX**: the BUG-vs-REAL forensics (negate-test, gross-vs-net, regime decomposition)
were stale **calendar-day** output, and 2/3 regime signs had flipped under the grain fix — so the decisive
negate-test for the −0.18 number did not yet exist. Critic pre-registered the decision rule: *if trading-day
−anchor ≈0/negative → NEGATIVE-CONFIRMED; if materially positive → the finding is "reversal edge," pivot.*

**Fix applied:** re-ran the read-only `iter_001_diag.py` on trading-day data. Result: **−anchor = −0.10**
(negative), **gross = −0.04** (negative → signal-driven), broad-based across years. By the Critic's own
pre-registered rule → **NEGATIVE-CONFIRMED**: bare 12-1m XS-momentum has no exploitable edge on this
universe — momentum *and* its negation both lose, net of cost. Not a sign bug, not a masked reversal edge,
not cost-driven, not a single-regime artifact, leak-free, well-formed book.

**Verdict:** NEGATIVE-CONFIRMED. No baseline established (fails the +0.30 promotable bar decisively). A
trustworthy reject that narrows the search.

---

## Next — Path Forward (Critic, constructive; one change per iteration)

Bare momentum is a signal-level negative whose exposure diagnostics rule out a neutrality-overlay rescue,
on a ~62%-Semi+Tech correlated universe. The leverage is at **signal construction**, not the neutrality
overlay. Candidate iter-002 axes (one each):

1. **Sector-RELATIVE momentum (highest leverage)** — demean the *signal* within each sector bucket
   (`sector_neutralize` applied to `mom/rvol` *before* `dollar_neutralize`), so the book is long-best-Semi /
   short-worst-Semi rather than Semi-vs-Comm. Isolates idiosyncratic stock momentum from sector drift in a
   correlated cross-section. Distinct from the (inert) iter-003 weight overlay.
2. **Short-term reversal leg** — long recent losers / short recent winners (~21d), the 1-month reversal the
   12-1 skip deliberately removes; frequently stronger than slow trend in liquid large-caps. (Negate-test was
   −0.10, so reversal is not a free win, but a *focused* near-term reversal is a different signal worth testing.)
3. **Re-fetch GOOGL/ORCL/GLW + trading-day robustness sweep** — repair the fetch gap, run the brief's
   lookback/skip/vol neighborhood in trading-day units to confirm the negative is a true plateau (supporting).

**NOTE:** the previously-planned iter-002 beta-neutral / iter-003 sector-neutral *weight* overlays are
DEMOTED — the exposure numbers (β≈0, sector tilt ≈0.05) show they are inert on the average-case loss. The
neutrality primitives in `neutralize.py` are repurposed: `sector_neutralize` now feeds axis (1) at the
SIGNAL layer.
