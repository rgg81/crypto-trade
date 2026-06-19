# Carry-iteration EXPLORATION — short-leg-squeeze enhancements (IS-ONLY)

**Date:** 2026-06-19 · **Track:** market-neutral funding carry · **Engine:** realistic
(`analysis/pair_engine.py` — next-bar-open fills, real 8h funding, 0.07%/side cost, leak-tested).
**Baseline:** walk-forward funding carry, net OOS +0.96 / DD −37% (the bias-free
`analysis/carry_walkforward.py`); the deployable fixed-param point used as the IS anchor here is the
most-picked walk-forward combo **M=9, FRAC=0.25, min_history=1095** (≈1y point-in-time listing age).

> **Gauntlet status of everything below: IS-ONLY.** Selection/ranking used only data before
> `OOS_CUTOFF = 2025-03-24`. **No OOS number was looked at to choose any enhancement.** OOS is
> revealed only at a separate CONFIRMATION. Every number here is reproduced by a committed script.

---

## 0. Scripts (every claim is backed by one of these)

| File | What it does |
|---|---|
| `analysis/carry_enh_common.py` | Shared harness: a strict superset of `broad_carry.build_book` with pluggable per-row **rank signal** + **short-leg guard / re-rank**, plus a **long-leg vs short-leg price+funding decomposition**. Verified to reproduce the baseline EXACTLY (IS Sharpe +1.3785, IS total +256.77%, identical row count, leg-decomp residual 5.6e-17). |
| `analysis/carry_enh_squeeze.py` | Axis 1 — name-level short-leg squeeze avoidance (funding-z rank, funding-persistence rank, momentum guard, taker-flow guard, soft momentum re-rank). → `carry_enh_squeeze_results.csv` |
| `analysis/carry_enh_beta.py` | Axis 2 — book-level beta controls (asymmetric legs, short inverse-vol, static long-index hedge). → `carry_enh_beta_results.csv` |
| `analysis/carry_enh_regime.py` | Axis 3 — past-only alt-rally **breadth brake** on the short leg + a **random-brake null control**. → `carry_enh_regime_results.csv` |

Run: `uv run python analysis/carry_enh_squeeze.py` (and `_beta.py`, `_regime.py`). Lint-clean
(`uv run ruff check analysis/carry_enh_*.py`). Foundation tests stay green (10 passed).

---

## 1. The diagnosis that drove the design (IS-only, the load-bearing finding)

The harness's leg decomposition splits the IS net into long-leg and short-leg, price and funding:

| Leg | IS price PnL | IS funding PnL |
|---|---|---|
| **LONG** (lowest-funding / crowded-shorts) | **+309%** | +32% |
| **SHORT** (highest-funding / crowded-longs) | **−54%** | **+94%** |

Two facts reframe the whole problem:

1. **The long leg is the price hero (+309%), not just a hedge.** Longing the most-negative-funding
   coins (crowded shorts) grinds *up* — that is where the price alpha lives. **Leave it untouched.**
2. **The short leg is the drag (−54% price), but its funding income is the single biggest
   component (+94%).** The short leg's price loss and its funding income are **two sides of the same
   crowded-long position**: the coins paying the most funding are exactly the ones that squeeze.

A concentration probe (`/tmp` diagnostic, reproduced in the squeeze-script comments) shows the
short-price loss is **diffuse, not a thin tail**: the worst 1% of candles = only 12% of the negative
short PnL; short price is *positive in 65% of months*; the worst single days cluster in **broad
alt-rally windows** (May-2021, Jan-2021, May-2022 bounce). → the short-leg drag is a **market/alt
beta exposure**, not a few avoidable names. This prediction is what each axis tests.

---

## 2. Axis 1 — name-level squeeze avoidance (`carry_enh_squeeze.py`) — NEGATIVE

IS-only ranking (baseline first; everything compared to IS net Sharpe **+1.38**, short price **−54%**):

| enhancement | IS net Sh | IS net % | IS maxDD | IS short price | fund t |
|---|---|---|---|---|---|
| **BASELINE (rank=raw funding)** | **+1.38** | +257 | −22% | **−54%** | +10.83 |
| D. taker-buy guard (drop top-q taker-dominance from short) | +1.38 | +257 | −22% | −54% | +10.83 |
| B. funding-**persistence** rank | +1.37 | +255 | −23% | −85% | +10.88 |
| C. momentum guard (drop top-q recent up-movers from short) | +1.05 | +150 | −22% | −86% | +10.93 |
| E. momentum soft re-rank (keep safest 75%) | +0.89 | +144 | −33% | −111% | +10.98 |
| A. funding-**z** rank | +0.25 | +36 | −58% | −108% | +9.87 |

**Findings.**
- **Funding-z ranking (A) is the worst idea (−0.25 IS net).** Ranking the short leg by an *acute*
  funding spike shorts coins that are already spiking — they squeeze harder (short price −108%). The
  squeeze precursor is NOT "elevated vs own history."
- **Momentum guards (C, E) make the short leg WORSE, not better** (−86% / −111% vs −54%). "Don't
  short a coin mid-squeeze" backfires: dropping the running-up names forces the short onto
  less-crowded coins that pay less funding while squeezing just as much. The intuition is wrong.
- **Taker-flow guard (D) is completely INERT** (bit-identical to baseline). Taker-buy dominance
  never coincides with the highest-funding names in a way that changes the short selection — taker
  flow does not separate squeeze-prone shorts at the cross-section.
- **Funding-persistence (B) is the one near-neutral idea:** IS Sharpe +1.37 (vs +1.38) at **lower
  turnover (0.26 vs 0.31)** and slightly higher funding t (+10.88). It rewards *durable* crowding,
  so the book thrashes less — equal IS Sharpe, ~16% less turnover, identical funding income. Its raw
  short price is worse on paper but the net is unchanged. **Only candidate worth an OOS look from
  this axis, and ONLY for the turnover/cost-realizability angle, not for Sharpe lift.**

**Verdict: name-picking cannot decouple the squeeze from the income.** Confirms the diagnosis.

---

## 3. Axis 2 — book-level beta controls (`carry_enh_beta.py`) — MARGINAL / NEGATIVE

| enhancement | IS net Sh | IS net % | IS maxDD | IS short px | IS long px |
|---|---|---|---|---|---|
| H. beta-hedge h=0.05 (long-index overlay) | **+1.39** | +263 | −24% | −53% | +313 |
| H. beta-hedge h=0.10 | **+1.39** | +269 | −27% | −52% | +316 |
| **BASELINE (sym legs, eq-weight)** | **+1.38** | +257 | −22% | −54% | +309 |
| H. beta-hedge h=0.15 | +1.37 | +275 | −29% | −51% | +320 |
| H. beta-hedge h=0.20 | +1.35 | +281 | −32% | −50% | +324 |
| F. asym long=0.20 short=0.35 | +1.28 | +274 | −24% | −81% | +330 |
| F. asym long=0.25 short=0.35 | +1.24 | +221 | −20% | −99% | +309 |
| F. asym long=0.25 short=0.40 | +1.06 | +187 | −27% | −137% | +309 |
| G. short inverse-vol win=30 | +0.94 | +218 | −63% | −98% | +314 |
| G. short inverse-vol win=60 | +0.92 | +229 | −65% | −95% | +309 |

**Findings.**
- **Widening the short leg (F) hurts** (short price −81% → −137% as short FRAC grows). More short
  names = shorting *less-crowded* coins whose funding income is lower but whose squeeze is no better.
- **Short inverse-vol weighting (G) is catastrophic for DD** (−63%/−65%). Down-weighting high-vol
  shorts concentrates notional into fewer names and *amplifies* drawdown. The squeeze is not a vol
  story you can size away.
- **Static long-index hedge (H) is the only thing that nudges Sharpe up** (h=0.05–0.10: +1.39 vs
  +1.38; total return +263–269% vs +257%). But it barely moves short price (−53% vs −54%) and the
  gain is within noise — confirming the short drag is **alpha-side beta** (the hot alts the longs are
  *not* in), not pure market beta a passive index long can cancel. Larger h *increases* DD.

**Verdict: the book-level beta levers give at most a hair of Sharpe (H) and one (G) is a DD trap.**

---

## 4. Axis 3 — alt-rally breadth brake on the short leg (`carry_enh_regime.py`) — NEGATIVE for Sharpe

Past-only breadth = fraction of eligible coins with positive trailing return; brake scales the short
leg down in hot-breadth regimes (threshold from IS distribution only). **Includes a null control K.**

| enhancement | IS net Sh | IS net % | IS maxDD | IS short px | IS fund Sh |
|---|---|---|---|---|---|
| **BASELINE (no brake)** | **+1.38** | +257 | −22% | −54% | +4.73 |
| J. brake win=21 q70 scale=0.5 | +1.37 | **+331** | −26% | **+49%** | +4.10 |
| J. brake win=21 q70 scale=0.0 | +1.24 | **+405** | −33% | +151% | +2.31 |
| **K. NULL random brake (matched 24% duty)** | **+1.18** | +271 | −34% | +19% | +4.65 |

**Findings.**
- The brake **does fix the short *price*** (−54% → +49%, or +151% if you fully cut the short in
  rallies) and **raises total return** (+257% → +331%/+405%) — the alt-rally diagnosis is correct
  about *price*.
- **But it trades the funding income away** (fund Sharpe +4.73 → +4.10 → +2.31): shutting the short
  in rallies stops collecting the *huge* funding crowded longs pay precisely when funding is highest.
- **It is NOT a Sharpe edge.** Best brake net Sharpe +1.37 ≈ baseline +1.38, and it only modestly
  beats its own **random-brake null (+1.18)** — i.e. most of the apparent "help" is just *less short
  exposure on average*, not regime-timing skill. Net is a **return/risk rebalance, not alpha**.

**Verdict: regime-timing the short raises total return at flat-or-worse Sharpe and is partly a coin
flip.** Relevant only if the deployment objective ever switches from Sharpe to absolute return.

---

## 5. Ranked recommendations

1. **NO Sharpe-improving short-leg enhancement was found — and that is the high-value result.**
   The short-leg squeeze (−54% IS price) and the short-leg funding income (+94% IS) are mechanically
   inseparable: every attempt to cut the squeeze (z-rank, momentum guard, wider short, inverse-vol,
   regime brake) cuts the income by at least as much. **The baseline is already near the efficient
   point of this trade-off.** This should close the "improve short-leg *selection*" axis for the
   carry track — it is now empirically exhausted across 5 mechanisms × the gauntlet.

2. **Take ONE thing to CONFIRMATION: funding-persistence ranking (B), for cost-realizability, not
   Sharpe.** IS Sharpe is identical (+1.37 vs +1.38) but turnover is **~16% lower (0.26 vs 0.31)**
   with identical funding income. Lower turnover directly improves the *realizable* (cost-stressed)
   Sharpe — the number the skill says to deploy on. Reveal OOS + run the 1×/2×/4× cost stress; only
   promote if OOS is non-inferior to baseline AND the cost-stressed Sharpe is strictly better.

3. **Optional, return-target only: the static long-index hedge (H, h≈0.05–0.10).** A hair of IS
   Sharpe (+1.39) and meaningfully more total return (+263–269%) at small DD cost. Worth an OOS look
   *only* if the objective is total return; on Sharpe it is within noise — do not over-fit h.

4. **Pivot the next EXPLORATION OFF the short leg.** The decomposition says the **long leg is the
   price engine (+309%)** and has had **zero** enhancement attention. Orthogonal, un-explored,
   crypto-native axes that the gauntlet has NOT yet closed:
   - **Long-leg concentration / depth** — does longing the bottom-FRAC vs an even deeper
     bottom-decile of negative-funding coins (the most-crowded shorts) raise the +309% further?
   - **Funding *acceleration* on the LONG leg** — rank longs by funding becoming *more* negative
     (shorts piling in / about to be squeezed up), a long-side momentum-of-crowding signal.
   - **Capacity-realizable carry** — re-run with the `min_liquidity` floor (already in
     `broad_carry`) + position-vs-trailing-volume capacity to produce the discounted deployable
     Sharpe the skill requires before any engine integration.

**Bottom line:** the funding income edge is real and large; the short leg cannot be cheaply
de-squeezed without surrendering that income; the carry's next real lift is on the **long leg** and
in **cost/capacity realizability**, not in short-leg name-picking. Recommend CONFIRMATION of (B) on
cost-realizability grounds and an EXPLORATION pivot to the long leg.
