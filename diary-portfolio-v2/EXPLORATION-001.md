# portfolio-iteration-v2 EXPLORATION-001 — ANCHOR (port v1 stack to rank 21–40, honest universe + slippage)

**Type:** foundation iteration (NO new factor). Establishes the v2 baseline + the de-inflated v1
benchmark on the corrected universe, with the parity/leak/survivorship gates green.

## What was built
- `analysis/portfolio_v2/engine_v2.py` — consolidated, parametrized port of the v1 stack
  (trend+carry → walk-forward λ → hysteresis band → eligibility-exit → renorm → vol-target).
  Parametrized by rank band `(lo,hi]`, PIT seasoning, and liquidity-scaled slippage.
- `analysis/portfolio_v2/universe_v2.py` — `load_pool_pit()` (survivorship-safe), `load_pool_v1compat()`,
  `eligibility(rank_lo, rank_hi, season)`, `candidate_count_per_year`.
- `analysis/portfolio_v2/parity_check.py` — **PARITY PASS** max|Δ|=1.04e-16 vs iter_021 K=2.
- `tests/test_portfolio_v2.py` — 8/8 pass (rank-band, seasoning, PIT-delisting, slippage zero-reduces
  -to-taker + monotone, future-perturbation leak, dollar-neutrality, past-only eligibility).

## Gates (all green)
- **Parity:** engine_v2(v1-compat) == iter_021 K=2 bit-for-bit (IS +1.2178 / OOS +1.5923).
- **Leak:** future-perturbation test — pre-cutoff target_w + net bit-identical after corrupting all
  inputs ≥ cutoff.
- **Survivorship fix works:** PIT pool = 542 coins (vs 227 survivor). Mean seasoned-ranked candidates
  per year GROWS toward 2026 under PIT (2020:21 → 2024:217 → 2026:504) vs the v1 survivor-snapshot
  which PLATEAUS (2024:213 → 2025:220 → 2026:219) — the snapshot-bias signature, now removed.

## Results (OOS_CUTOFF=2025-03-24)
| config | IS | OOS | maxDD | oosDD | netTot | avgPos | turn |
|---|---|---|---|---|---|---|---|
| v1 INFLATED (top20, survivor, no-slip) | +1.22 | +1.59 | −23% | −20% | +500% | 18.5 | 0.288 |
| v1 HONEST (top20, PIT, slip) | +1.24 | +1.49 | −26% | −25% | +559% | 19.0 | 0.278 |
| **v2 ANCHOR (21–40, PIT, slip)** | **+1.53** | **+0.01** | −30% | −30% | +319% | 18.8 | 0.297 |

v2-anchor per-year net%: `{2020:-10, 2021:+51, 2022:+46, 2023:+59, 2024:+18, 2025:+18, 2026:-1}`.
Slippage/cost sensitivity (anchor): no-slip IS+1.58/OOS+0.13 · 1×slip IS+1.53/OOS+0.01 ·
2×slip IS+1.10/OOS−0.12 · 2×taker IS+0.82/OOS−0.38.

## Honest reading
1. **v1's top-20 headline was only mildly inflated.** De-inflating (PIT universe + slippage) moves the
   top-20 from IS+1.22/OOS+1.59 → IS+1.24/OOS+1.49 — survivorship barely touches the mega-caps (they
   survive anyway); the −0.10 OOS is mostly slippage. v1's top-20 numbers are roughly robust.
2. **The rank-21–40 cohort has RICH in-sample structure** — IS +1.53, *stronger* than the top-20
   (+1.24). The mid-cap dispersion the cohort was chosen for is clearly there in-sample.
3. **…but the naive trend+carry port does NOT generalize OOS** — OOS +0.01 (vs top-20 +1.49). The
   recent window (2025-03-24→) is flat. This is the honest v2 starting point: a strong-IS / dead-OOS
   port, exactly the IS/OOS divergence the iteration process exists to attack.
4. **The cohort is more cost-sensitive** than the top-20 (2×-taker → IS +0.82), validating the
   mandatory slippage upgrade.
5. **Early-period thinness:** 2020 has only ~21 seasoned candidates, so the 21–40 band is near-empty
   then (2020 net −10%). A later universe start (≥40 seasoned, ~2022) is a candidate refinement.

## Critic review — PASS-WITH-CONCERNS (honest baseline; not an edge)
Adversarial `quant-critic` pass: the two HIGH leak fixes are genuine (PIT pool + seasoning + slippage);
parity holds at 1.04e-16; leak discipline intact. Concerns raised + how they were resolved:
1. **Leak test #6 too weak** (only `fixed_lambda_book`; net assertion vacuous at scale=0 on short
   panels) → **FIXED**: added test #9, a `run_book`-level future-perturbation test on a 26-month panel
   that exercises the walk-forward stitch + band/eligexit overlay. 9/9 green.
2. **IS +1.53 = thin-denominator artifact?** → **MEASURED & REFUTED** (see characterization below).
3. **Slippage optimistic in the thin tail** → **MEASURED**: pessimistic preset (cap=25bp, B=40) gives
   anchor IS +1.10 / OOS **−0.12**. The +0.01 headline travels with this caveat.
4. **Residual survivorship** → **MEASURED**: census below.
5. **Disclose de-inflated v1 barely moved** → done (point 1 of Honest reading).

## Post-critic characterization (diag_v2_001.py)
**The IS +1.53 is regime-concentrated, NOT a thin-denominator/concentration artifact.**
- Band is FULL: `band names/yr = {2020:14.8, 2021:20, 2022:20, 2023:20, 2024:20, 2025:20, 2026:20}`;
  `avgPos/yr ≈ 15→20`. The strong 2021–23 years run on a complete 20-name book, not a handful.
- Per-year Sharpe: `{2020:−0.68, 2021:+1.93, 2022:+2.45, 2023:+2.13, 2024:+0.71, 2025:+0.80, 2026:−0.11}`
  — genuine alt-season strength 2021–23, FADING 2024→26. This is regime non-stationarity, not overfit
  (walk-forward λ verified honest) and not concentration (band full).
- OOS sub-windows: 2025-03..12 Sharpe +0.08 (n=849), 2026 −0.11 (n=518) — recent regime is flat.
- Regime split vs top-20: v1-honest stays positive OOS (2025 +1.02, 2026 +2.06) — mega-cap trend kept
  working while mid-cap trend died. Mid-caps are in a harder recent regime for directional trend.
- λ-picks lean to carry (0.25) in 2024–26 yet still flat → carry tilt isn't rescuing it either.

**PIT-pool census (residual survivorship):** 542 coins; only 24 delisted-tagged (collection floor —
many historical Binance delistings were never downloaded → an unmeasured residual survivorship I cannot
fully close without re-pulling delisted history via `bulk --all`). Internal gaps: 90 candle-cells over
49 coins (negligible; band=20.0 confirms no material band-thinning from the `==season` rule).

## Verdict
ANCHOR ESTABLISHED — honest, leak-clean, survivorship-safe baseline; gates green (parity 1.04e-16,
9/9 tests, future-perturbation at run_book level). **NOT a profitable strategy:** pure trend+carry on
rank 21–40 is strong IS but regime-faded to OOS ≈ 0 (−0.12 under pessimistic slip). The bar for v2 is
to beat OOS +0.01 (default slip) / clear ~0 under pessimistic slip on the de-inflated comparison.
**Next (iter-v2-002): cross-sectional momentum** — a DIFFERENT signal class (dollar-neutral XS rank)
on the full 20-name mid-cap cross-section, the factor v1 rejected on the efficient top-20. Per critic:
gate the book off when the band has <N names, judge on the 2×/pessimistic-slip OOS (XS-mom turns over
more), and split results by era — an edge that only lives in 2021–23 alt-season is the same regime
effect in a new costume.
