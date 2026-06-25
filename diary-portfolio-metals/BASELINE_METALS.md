# BASELINE_METALS — metals portfolio baseline (BOOTSTRAP)

**Established:** 2026-06-25 (first metals baseline). **Verdict:** CONFIRMATION-**BOOTSTRAP** (Critic).
**Branch:** `portfolio-metals`. **Engine:** the audited `universe_metals.net_from_raw`
(gross-norm → `.shift(1)` lag → 6bps/side taker cost → ~15% annual vol-target, ≤5× leverage).

## The baseline book — L2 = anchor + dispersion
```
raw = gn(iter_001_trend.build_raw(coins))            # long-biased trend anchor
    + 0.5 · gn(iter_002_mn_overlay.mn_dispersion_raw(close))   # dollar-neutral gold-defensive dispersion
→ ONE net_from_raw
```
- **anchor:** EMA(84)/EMA(189) crossover with FLOOR=0.5 — long-biased, NEVER shorts (the naive
  symmetric trend's short leg scores −0.71 IS; metals carry secular long drift).
- **dispersion:** long gold / short an inverse-vol basket of the other present metals, demeaned to
  exact dollar-neutral; ALPHA=0.5, vol_win=84.
- Universe: XAUUSDT, XAGUSDT, XPTUSDT, XPDUSDT (Binance precious perps). Gold/silver 2015+,
  platinum/palladium 2022+ (ragged, point-in-time).

## Numbers (IS = data start → 2025-03-24; OOS = 2025-03-24 → 2026-06, ~16 months)
| | IS Sharpe | OOS Sharpe | IS maxDD | OOS maxDD | turnover/candle |
|---|---|---|---|---|---|
| **L2 baseline** | **+0.51** | **+1.71** | −26% | −18% | 0.007 |
| benchmark: buy-hold gold (VT 15%) | +0.74 | +1.45 | — | — | — |
| benchmark: equal-weight 4-metal basket (VT 15%) | +0.34 | +1.58 | — | — | — |
- L2 **beats both benchmarks OOS** (1.71 > 1.58 > 1.45), at the lowest turnover of any layer.
- **Cost-stress:** OOS Sharpe 1× = 1.71, 2× (12bps/side) = 1.70 (Δ−0.012) — highly cost-robust.
- Leak re-audit PASS (IS book bit-identical with vs without OOS data on disk). DSR clears
  E[max|null]≈+1.23. Deterministic book (no RNG) → multi-seed N/A; robustness is structural.

## REGIME CAVEAT (load-bearing — do not over-claim)
The OOS window (2025–2026) is a **single benign metals BULL** (L2 2025 OOS net +61%; gold melt-up).
OOS Sharpe ~3× IS Sharpe is **regime, NOT confirmed multi-regime alpha** — vol-targeted buy-and-hold
gold (1.45) and the equal-weight basket (1.58) reached the same neighbourhood in that window, so the
book's edge **over buy-and-hold is THIN** and is ~entirely the directional anchor riding the melt-up.
Of the market-neutral overlays, **only dispersion confirms OOS** (+0.010 marginal); it is the one
overlay kept in the baseline.

## Sleeves NOT in the baseline (tested, dispositioned honestly)
- **COT managed-money contrarian (iter-004):** CONFIRMED **GOLD/SILVER-ONLY** (OOS GS-only marginal
  lift +0.044). The **full-4-metal** COT sleeve OOS marginal lift = **−0.137 (FALSIFIED)** — dragged
  by the thin pt/pd-COT legs — so it is NOT promoted as wired. The strongest IS sleeve (IS +0.10 lift)
  did not generalise OOS at the full-universe center config; its durable claim survives only on the
  deep-history gold/silver legs, exactly as pre-registered (EXPLORATION-004). **`L2 + GS-only-COT` is
  the prime candidate for the NEXT confirmation** — it was inferred from a marginal-lift cell here, not
  run as a first-class OOS layer.
- **pt/pd reversion (iter-003):** `PROMOTABLE=False` (thin-n 2022+, era-split falsifier tripped IS).
  The full 4-sleeve book (L4) beats both benchmarks OOS (1.63) but that beat **leans on this
  non-promotable sleeve** → not baselined.

## Outstanding constraints (must clear before a FULL CONFIRMATION-PASS / multi-regime alpha claim)
1. **A metals-BEAR OOS window.** The binding open question: does a long-biased anchor + dollar-neutral
   dispersion survive a metals DOWNTURN? The anchor's long-bias is the obvious vulnerability (IS bad
   years 2015/2018/2021/2023). Until a post-2026 bear (or a pre-registered bear sub-window stress),
   the OOS Sharpe is regime-conditional.
2. **A second non-overlapping OOS regime** confirming the overlays' lift.
3. **`L2 + GS-only-COT` run as an explicit headline OOS layer** (not an inferred cell).
4. **Live-parity reconcile harness** before any capital (reproduce the COT weekly-release alignment +
   `vol_target` `.shift(1)` scalar bit-identically live; analogous to `scripts/reconcile_full_oos.py`).

## Provenance
Foundation + iter-001..006 + CONFIRMATION, all Critic-reviewed, on branch `portfolio-metals`.
Data: Dukascopy 8h (gold/silver 2015+, pt/pd 2022+); CFTC COT 2015+ (`data/cot/`). Diaries
`EXPLORATION-00{1..6}.md`; gauntlet `analysis/portfolio/metals/confirm_metals.py`.
The in-scope signal frontier is CLOSED (iter-005/006, two independent confirmations + a fair ML null).
