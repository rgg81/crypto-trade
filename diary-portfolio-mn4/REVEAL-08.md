# REVEAL-08 — Vol-Targeted Risk-Parity (DIRECTIONAL) — Phase B Holdout

**Token:** MN4-08 (SPT — single-use forever; this was the one authorized look)
**Window:** [2024-07-01, 2026-07-01) — the sealed 2-year holdout
**Construction:** byte-exact Phase-A frozen (NO changes, NO re-gating)
**Model:** Opus 4.8 (Fable rate-limited; user-directed)
**VERDICT:** **FAIL** (2 of 3 frozen gates failed; construction CLOSED)

---

## Construction One-Liner

Long-only equal-weight (BTC/ETH/BNB/XRP/ADA), vol-targeted to 15% ann (14-day
trailing, max_lev=2.0), dd_brake crisis overlay (equity DD ≤ −15% → gross×0.5,
recovery −7.5%), daily rebal (rebal=3 @ 8h), honest 5+2.5bps+funding cost with
10+5bps+funding 2× ground-truth twin. Run on the FULL panel (IS+holdout) with
holdout-period metrics extracted — preserves stateful vol-target/dd_brake
continuity (how the book actually trades live).

## Holdout Headline

| Metric | Holdout 1× | Holdout 2×-GT | IS (Phase A) | Decay |
|--------|-----------|---------------|--------------|-------|
| **Sharpe** | **−0.121** | **−0.222** | +1.193 | **INVERTED** |
| **maxDD** | **−82.8%** | — | −35.4% | **CATASTROPHIC** |
| annReturn | −51.1% | — | +34.2% | inverted |
| realized vol | 24.9% | — | 27.8% | similar (ratio 1.66 vs 1.85) |
| turnover (ann) | 9.07 | — | 9.72 | similar |
| gross mean | 0.434 | — | 0.412 | similar |
| **β_BTC** | **+0.448** | — | +0.353 | higher (more BTC-exposed) |
| cost drop (Sharpe) | — | 0.101 | 0.008 | still cost-robust |

## Per-Half Path (holdout)

| Half | Sharpe | Total Ret | Read |
|------|--------|-----------|------|
| 2024-H2 | +1.30 | +15.9% | Last gasp of the bull — book captured upside |
| 2025-H1 | −0.30 | −5.8% | Chop begins — slow bleed |
| 2025-H2 | +0.10 | −0.5% | Flat — vol-target de-risked but no direction |
| **2026-H1** | **−1.98** | **−18.6%** | **The killer — sustained downtrend destroyed the book** |

The book was positive in 2024-H2 (the tail of the bull), then bled for three
consecutive halves. 2026-H1 alone delivered −18.6% — the sustained downtrend
that the vol-target + dd_brake could NOT protect against.

## Regime Buckets (holdout)

| Regime | n | Sharpe | Total Ret | Gross Mean | IS Comparison |
|--------|---|--------|-----------|------------|---------------|
| CRASH | 269 | −4.53 | −23.8% | 0.331 | IS was −43.8% → **BETTER** (vol-target de-risked) |
| MANIA | 109 | +8.37 | +32.5% | 0.426 | IS was +264.8% → positive but much smaller (fewer mania candles) |
| **CHOP** | **1811** | **−0.21** | **−12.4%** | **0.450** | IS was +74.4% → **INVERTED — the killer** |

**The CHOP regime killed the book.** 83% of holdout candles were CHOP (1811 of
2189), and the book lost −12.4% in choppy sideways/down markets. In IS, CHOP
was positive (+74.4% over 4.5 years — carried by the bull). On the holdout,
CHOP inverted. A long-only book in a prolonged chop/down regime slowly bleeds
regardless of vol-targeting.

## Crisis Overlay Behavior

| Metric | Holdout | IS |
|--------|---------|-----|
| braked rebals | 467 / 730 (64.0%) | 61.2% |
| dd_brake threshold | −15% → gross×0.5 | same |

The dd_brake was chronically engaged (64% of rebals — similar to IS). But it
halved gross from ~0.45 to ~0.22 during drawdowns — NOT flatten. Over 2 years of
compounding, even at half-gross, the losses accumulated to −82.8%. The brake
SLOWED the bleeding but did not PREVENT it.

## Gate-by-Gate Verdict (frozen Phase-A gates, NO re-gating)

| Gate | Threshold | Holdout Value | Verdict |
|------|-----------|---------------|---------|
| Sharpe > 0 | 0.0 | **−0.121** | **FAIL** |
| maxDD > −55% | −0.55 | **−0.828** | **FAIL** |
| MANIA total > 0 | 0.0 | +0.325 | PASS |
| **Overall** | | | **FAIL — CLOSED** |

## HONEST Generalization Read

**The drawdown control did NOT survive. It was substantially bull-regime luck.**

The IS +1.19 Sharpe and −35.4% maxDD were carried by the 2020–2024-H1 bull
market (7/9 IS halves positive, with 2021-H1 at +79.4%). On the 2-year holdout
(2024-H2 mania tail → 2025 stress → 2026-H1 decline), the book **inverted** to
Sharpe −0.121 and maxDD exploded to **−82.8%** — worse than many buy-and-hold
benchmarks.

The mechanism of failure is clear and structural:

1. **CHOP inversion.** The CHOP regime (83% of holdout candles) went from
   +74.4% in IS to −12.4% on the holdout. A long-only book cannot be
   "all-weather" in a sideways/down market — it slowly bleeds. Vol-targeting
   reduces the BLEED RATE (lower gross in high-vol chop), but cannot prevent it.

2. **dd_brake is insufficient.** Halving gross at −15% DD still leaves 50%
   exposure. Over 2 years of compounding losses in adverse regimes, even
   half-gross produces −82.8% drawdowns. A "cut to 50%" overlay is too gentle
   for a book whose entire edge is directional.

3. **Vol-target lag.** Realized vol (24.9%) still exceeded target (15%) by
   1.66×, similar to IS (1.85×). The vol-target reduces gross in high-vol
   periods but LAGS — by the time vol spikes, the book has already lost.

4. **CRASH control WAS genuine.** The one bright spot: CRASH total was −23.8%
   (vs IS's −43.8%) — the vol-target + dd_brake DID protect against sharp
   crashes. But the holdout's damage came from CHOP (slow bleed), not CRASH
   (sharp drop). The crisis overlay is designed for the wrong threat.

**Root cause:** managed-variance (CTA-style vol-targeting) works for
TREND-FOLLOWING books that can go flat or short. A LONG-ONLY book with
vol-targeting is just a de-risked long — it captures upside in bulls and
bleeds (slower, but still bleeds) in everything else. The "winner in every
market" thesis is structurally impossible for a long-only construction without
trend signals that exit downtrends.

The IS edge was real but regime-conditional (bull-market beta de-risked to
lower drawdowns). On a holdout dominated by chop and decline, the book had no
edge — only controlled bleeding that compounded into a catastrophic drawdown.

## What This Means for the Tournament

This construction is CLOSED. No rescue, no second reveal. The FAIL is honest
and instructive:

- **For directional books (IDEA-01, IDEA-09):** the lesson is that long-only
  + vol-target is NOT all-weather. Trend-following signals (go flat/short in
  downtrends) are NECESSARY for directional all-weather claims.
- **For the vol-targeting technique:** it controls SHARP crash drawdowns
  (CRASH −23.8% was genuine) but not PROLONGED chop drawdowns. Future
  constructions should combine vol-targeting with trend/regime signals, not
  use it standalone.
- **For the Critic:** this book had the STRONGEST IS cost-robustness (0.7%
  Sharpe drop at 2×) — and still failed. Cost-survival alone is not
  generalization.

---

*Token MN4-08 spent. One look. Honest numbers. FAIL. The methodology worked.*
