# portfolio-iteration EXPLORATION-017 — PERP-SPOT BASIS factor (REJECT: orthogonal-to-carry but NO sign-stable, cost-honest edge)

**Axis:** the perp-spot BASIS — `basis = perp_close / spot_close − 1`. A DIFFERENT PRICE SERIES, not a
funding transform (the Critic's constructive next-factor after iter_016 rejected the funding-slope).
Crypto-native hypothesis: when leveraged longs crowd the perp, their aggressive bidding pushes the
perp ABOVE spot (positive basis) = the *realized* leverage premium / over-extension; below = bearish
positioning. Funding is the mechanism that pulls the two back together; the basis is the market's
realized price gap RIGHT NOW — a continuous, intra-settlement positioning gauge funding does not equal.
Code: `analysis/portfolio/iter_017_basis.py`.

**Signal (PAST-ONLY, all inputs known at close[t], trade t+1 via `.shift(1)` on the weight):**
`basis[t] = perp_close[t]/spot_close[t] − 1` → `basis_sm[t] = basis.rolling(9).mean()` → `basis_z` =
cross-sectional z-score of `basis_sm` across the ELIGIBLE PIT top-20 (row-demean/row-std, `axis=1`
same-time only — no time leak). IDENTICAL transform + lag chain to iter_012's `flow_z` / iter_016's
`accel_z`. A DEVIATION form (`basis_sm − basis_sm.rolling(84).mean()`, removing each coin's structural
basis offset) is built as a cross-check. Direction tested BOTH ways; the data picks the **IS-better**
sign, NOT OOS.

## Data hazard found + fixed — flagged artifact (this is the load-bearing part)
The spot files (`data/spot/<SYM>/8h.csv`, 363 files from earlier cash-and-carry work) were read fresh
and nearest-aligned (tolerance 4h, half the 8h grid) to the perp ms index. The **first run HALTED on
the pre-registered alignment sanity gate** (median |basis| 0.06% > my initial 0.05% threshold, max|·|
**19.7%**). Diagnosis: NOT a wholesale bug — 134/150 coins had a clean median |basis| < 0.1%, but a
handful had a **systematic median offset** that can only be a WRONG-ASSET spot file (ticker reuse
across delisting/relisting, a different listing era, or a denomination mismatch):

| coin | median basis | read |
|---|---|---|
| GLMRUSDT | **+94%** | spot file is not the same asset as the GLMR perp |
| RAYUSDT | **−59%** | wrong-era / relisted spot |
| RADUSDT | **+52%** | wrong-era / relisted spot |
| SCUSDT | **+17% (median \|·\|)** | wrong listing |

**Fix (leak-safe, pre-registered semantics):** a PER-COIN ALIGNMENT GUARD drops any coin whose
full-history median |basis| > 2% (a same-asset perp/spot pair *cannot durably diverge* — funding
arbitrages any gap within days, so the median is always a few bp). This is a fixed data-provenance
decision about which spot FILE is the right asset (like the universe `MIN_HISTORY` length filter) —
NOT a return-conditioned or time-varying signal; the same 4 coins (GLMR/RAD/RAY/SC) are dropped
whether scored on IS or OOS. After the guard: **146/206 valid spot, pooled |median| 0.06%, p99 0.34%,
mean −0.017%** → alignment **PASS, perp≈spot confirmed.** Coverage 0.87 of eligible cells, ~17 active
coins/candle (sparse-but-dense — no vol-target degeneracy risk). The remaining max|·| 19.7% is a
genuine single-candle liquidation dislocation on an illiquid alt (z-scored, not an alignment bug).
**Leak check:** signal→weight lag verified = exactly 1 row (past-only); the only forward op is the
standard `fund.shift(-1)` accrual inherited byte-for-byte from the book.

## Orthogonality — DECISIVELY distinct from carry (the headline reject-trigger PASSES)
| metric | value | read |
|---|---|---|
| corr(basis_z, **CARRY**) IS, signal-level | **−0.341** | NOT the funding LEVEL re-skinned — distinct |
| corr(basis_z, trend) IS | −0.047 | orthogonal to trend |
| corr(basis_z, flow) IS | −0.136 | ~orthogonal to flow |
| corr(basis net, **CARRY net**) IS, P&L-level | **+0.16** | P&L stream does NOT co-move with carry |
| corr(basis net, trend net) / (flow net) IS | −0.08 / +0.20 | P&L ~orthogonal to the book |
| carry-only β(basis net ~ carry net), IS | **+0.17** | small carry loading, not a re-skin |

The basis is **NOT carry-redundant** — the brief's primary reject trigger (collinear-with-carry) is
itself rejected. Signal corr −0.34, net corr +0.16, carry-β +0.17: the realized price gap is a
genuinely independent quantity from the funding rate on this universe. So the reject is **NOT** "carry
in disguise." (Signal corr −0.34 is the largest |corr-to-carry| of any factor tested, but still well
inside the 0.50 gate — economically expected, since high basis ⇄ funding pressure to push longs out.)

## Standalone — there is NO sign-stable, cost-honest edge (this is why it rejects)
| direction | IS | OOS | maxDD | netTot | turnover |
|---|---|---|---|---|---|
| MOMENTUM (+basis, long high-basis) 1× | **−1.39** | +0.65 | −98% | −95% | 0.271 |
| MOMENTUM 2× taker | −1.84 | +0.32 | −99% | −98% | 0.271 |
| FADE-LEVERAGE (−basis, short high-basis) 1× | **+0.52** | **−1.25** | −90% | −2% | 0.271 |
| FADE-LEVERAGE 2× taker | +0.09 | −1.51 | −95% | −66% | 0.271 |
| DEVIATION-form 1× (picked dir) | +1.11 | −0.90 | −62% | +297% | 0.310 |

- **The two directions are mirror-opposite and both FAIL.** FADE (the economic prior: short the
  over-leveraged) is **IS +0.52 but OOS −1.25** — a catastrophic sign flip. MOMENTUM is the reverse
  (**IS −1.39 / OOS +0.65**). The data picks FADE by IS, but FADE's OOS is −1.25 → gate [1] FAILS hard.
- **Regime decay (the real story):** the IS-picked FADE direction earned only in the *early, illiquid*
  era and decayed monotonically — per-year net%: **2020 +67, 2021 +146, 2022 −17, 2023 −64, 2024 −10,
  2025 −77, 2026 +1**. The "leverage-premium fade" worked when crypto microstructure was thin and
  basis dislocations were large/persistent; as markets matured (tighter perp-spot arbitrage, deeper
  liquidity) the premium compressed and the edge inverted. The whole OOS window (2025+) is the
  post-decay regime — hence FADE's −1.25 OOS.
- **Cost-fragile:** FADE 2× taker collapses +0.52 IS → +0.09 (and OOS −1.25 → −1.51). Turnover 0.271
  (~baseline 0.296), but the daily-recomputed basis-z whips enough that cost matters — gate [3] FAILS.
- **Window-fragile / sign-unstable:** standalone OOS across the de-noise grid is FADE {win3: +0.37,
  win9: +0.65, win21: +0.83} but with IS {−2.41, −1.39, −1.03} — **no cell is IS+OOS both positive in
  either direction.** Gate [6] FAILS.
- **Residual COLLAPSES:** raw basis IS/OOS +0.48/−1.19 → residual (after trend+carry+flow OLS) −0.00 /
  **−1.87**. There is no positive OOS return for the regression to be additive *with* — gate [5] FAILS.

## Pre-registered falsifier verdict (n=16 OOS months)
| gate | result |
|---|---|
| [1] standalone net-positive IS AND OOS (picked dir) | **FAIL** (FADE IS +0.52 / OOS −1.25 — sign flip) |
| [2] standalone OOS ≥ +0.30 (picked dir) | **FAIL** (−1.25) |
| [3] cost-honest: net-positive at 1× AND 2× taker | **FAIL** (FADE 2× +0.09 IS / −1.51 OOS) |
| [4] DISTINCT from CARRY (\|sig corr\| AND \|net corr\| < 0.50) | **PASS** (sig −0.34, net +0.16) |
| [5] residual-additive vs trend+carry+flow (resid OOS > +0.30) | **FAIL** (resid OOS −1.87) |
| [6] robust across de-noise window (every cell IS+OOS > 0, \|corr-carry\| < 0.50) | **FAIL** (no IS+OOS-positive cell) |

## Read — REJECT for NO-EDGE / COST-FRAGILE / REGIME-DECAYED, NOT for carry-redundancy
The brief asked two separable questions; the data answers them **oppositely** (same pattern as iter_016):
1. **Is the basis distinct from the carry LEVEL? YES, decisively** (sig corr −0.34, net corr +0.16,
   carry-β +0.17). A genuinely orthogonal price series. Had it carried a sign-stable cost-honest edge,
   it would have been a clean orthogonal combiner candidate.
2. **Does it carry a usable standalone edge? NO.** The two directions are mirror-opposite and both fail:
   the IS-picked FADE flips to −1.25 OOS, dies at 2× cost, and its residual collapses to −1.87. The
   edge that *did* exist (FADE IS +0.52) is an **early-illiquid-era artifact** that decayed
   monotonically (2021 +146% → 2025 −77%) — the OOS window is entirely post-decay. This is exactly the
   maturing-microstructure story: the realized leverage premium was harvestable when perp-spot
   arbitrage was loose, and compressed away as the market deepened.

So this is a **clean REJECT-for-no-edge** (specifically: regime-decayed + sign-unstable + cost-fragile),
distinct from a redundancy reject. The honest down-call: the leverage-premium *hypothesis* is sound and
the basis IS a different, orthogonal signal from funding — but the *directional cross-sectional edge*
is not there at 8h on the modern (OOS) regime, at realistic taker cost.

## Verdict: REJECT — perp-spot basis is ORTHOGONAL to carry (and to trend/flow) but carries NO sign-stable, cost-honest, window-robust standalone edge (IS-picked direction flips to −1.25 OOS; the historical edge is an early-illiquid-era artifact that decayed away; residual collapses to −1.87). NOT a combiner candidate. Baseline UNCHANGED (iter_005 WF-λ trend+carry, IS +1.30 / OOS +1.37 / −23%).

## Axis status
- **Perp-spot basis (LEVEL / DEVIATION, cross-sectional z) directional factor: CLOSED at this
  construction.** Orthogonality to carry confirmed (distinct price series — the first non-funding
  microstructure column tested since flow), but no edge: both directions IS-OOS sign-flip, cost-
  fragile, residual collapses, and the historical edge is regime-decayed (early-illiquid only).
- This is the 2nd non-trend/non-carry microstructure column tested. flow (iter_012) carried a real
  orthogonal edge; basis does not — the difference is that taker-flow imbalance persists at 8h while
  the basis premium has been arbitraged down to noise in the mature regime.
- **Data-provenance lesson banked:** 4 of the 150 spot files (GLMR/RAD/RAY/SC) are wrong-asset; any
  future basis/cash-and-carry work on this spot data MUST apply the median-|basis| > 2% per-coin guard.

## Next (candidate axes, not yet run)
- **Basis as a REGIME / gross-exposure gate, not a directional tilt** (cf. the iter_012 / iter_016 Path
  Forward): aggregate (market-wide) basis spiking = system-wide over-leverage building → scale the
  *book's* leverage DOWN (de-risk), attacking the −23% DD lever rather than the Sharpe. A different use
  of the same orthogonal signal that a directional standalone could not bank.
- **Basis-CHANGE / basis-momentum** (the slope of the gap, not the level) — but iter_016 already showed
  funding's *slope* has no edge, and basis tracks funding pressure, so this is lower-priority.
- **Open-interest change** — the last untouched non-price microstructure column. OI rising into a price
  move = positioning confirming; OI falling = unwind. Orthogonal to both basis (a price gap) and flow
  (a volume share). Higher-priority structural family than another basis transform.

## INDEPENDENT CRITIC REVIEW — (pending; pre-registered gates above are all explicit + leak-checked)
Leak test: signal→weight lag verified = 1 row past-only; only forward op is the standard
`fund.shift(-1)` accrual inherited byte-for-byte. Per-coin guard is provenance-based (IS=OOS identical
drop set), not return-conditioned. Reject discards a non-edge: IS-picked direction OOS −1.25, no
IS+OOS-positive cell in either direction or any window, 2×-cost fragile, residual −1.87, year-
concentrated in 2020-2021 then monotone decay. Orthogonality-to-carry (the brief's primary reject
trigger) PASSES — so the reject is correctly attributed to NO-EDGE / REGIME-DECAY, not redundancy.
Baseline iter_005 +1.37 untouched.

## INDEPENDENT CRITIC REVIEW (2026-06-20) — PASS (reject sound, leak-free, guard correct)
Leak test: time-only truncation -> past basis-net bit-identical (the 6e-3 first-glance diff was
cross-sectional universe membership, not time leak); lag chain = 1 (correct). Data-guard leak-safe
(full-history provenance, symmetric IS+OOS; drops the 4 wrong-asset coins GLMR/RAY/RAD/SC; kept coins
p90 |basis| 0.099%, clean separation, no threshold-gaming). Reject honest (FADE regime-decayed +
cost-fragile + residual -1.87; +0.65 momentum is mirror noise). Cosmetic: a docstring states a tighter
band than the executed (looser, correct) gate constants.
DECISIVE RECOMMENDATION: directional search EXHAUSTED (7 rejects, only taker-flow survived). Next =
the POWER-AWARE CONFIRMATION of trend+carry+flow (block-bootstrap CI + DSR deflating for ~14 factors
tried + directional/sign-stability gate + PBO) -> prices in the rejects, decides promotion. DD overlay
comes AFTER confirming the core book. Baseline iter_005 +1.37 untouched.
