# iter-013 OOS FORENSIC — is OOS Sharpe +3.39 genuine or an artifact?

**Date:** 2026-07-01 · **Track:** portfolio-tradfi · **Role:** Quant Engineer (forensic)
**Trigger:** CONFIRMATION revealed OOS Sharpe **+3.39** on an IS of only **+0.61** — the OOS is **5.5× the in-sample** and **5× the pre-registered ">+1.0 = assume-leak/investigate" red-flag line**. Reveal must be proven before it is trusted.
**Source of truth (every number below):** `analysis/portfolio/tradfi/oos_forensic.py` (imports iter-013's EXACT deployed build — lam=0.25, VIX ON, 1x cost — via the same `combined_raw → i3.banded_net → *s_vix` path the reveal used, and only DECOMPOSES the already-revealed OOS net; strategy + `data/` untouched). Reproduce: `uv run python analysis/portfolio/tradfi/oos_forensic.py`.
**Deployed config of record:** lam=0.25, VIX brake ON, 1x cost. **OOS window:** 2025-03-24 → 2026-06-30 (~15 months, n=16 monthly obs).
**Headline reveal:** IS +0.61 · OOS **+3.39** · OOS maxDD **−8%** · OOS netTot **+65%** · OOS realized vol **15%/yr** (= vol-target working; +65% ≈ 3.39 Sharpe × 15% vol × 1.27 yr — **no hidden leverage**).
**Decomposition ties out exactly:** official reveal net == reconstructed net (atol 1e-12); per-name-sum + cost == net (atol 1e-12).

---

## Check 1 — Per-MONTH: consistent, NOT 1-2 months

| period | net% | | period | net% |
|--------|-----:|-|--------|-----:|
| 2025-03 | +0.52 | | 2025-11 | −0.44 |
| 2025-04 | +1.15 | | 2025-12 | +2.03 |
| 2025-05 | +1.22 | | 2026-01 | +8.48 |
| 2025-06 | −1.25 | | 2026-02 | +4.83 |
| 2025-07 | +0.77 | | 2026-03 | −0.73 |
| 2025-08 | +4.73 | | 2026-04 | +3.94 |
| 2025-09 | +8.03 | | 2026-05 | +4.43 |
| 2025-10 | +8.60 | | 2026-06 | +5.42 |

- **13/16 positive months.** Best month 2025-10 (+8.60%) is only **17% of the OOS sum**.
- **Sharpe EX-BEST-MONTH = +3.23** (drops just 0.16 from +3.39). **NOT a 1-2-month spike.**
- **Regime signature though:** the strength is second-half loaded — the first ~5 months (Mar–Jul 2025) are modest/mixed (+0.5 to +1.2, one −1.3); the big +4-to-+8% months cluster Aug 2025 → Jun 2026. That is a *favorable-regime run*, but a broad one.

## Check 2 — Per-NAME: thematic AI/memory cluster, but broad enough (ex-top-name barely moves)

| rank | name | OOS contrib% | share of ΣPnL |
|-----:|------|------------:|-------------:|
| 1 | LITE (optical) | +7.83 | 15% |
| 2 | SNDK (storage) | +7.47 | 14% |
| 3 | WDC (storage) | +6.81 | 13% |
| 4 | CIEN | +4.91 | 9% |
| 5 | MSTR | +4.86 | 9% |
| 6 | PLTR | +4.82 | 9% |
| … worst | FLNC | −4.81 | −9% |

- **Top-3 = LITE/SNDK/WDC = 42% of ΣPnL** — a single macro theme (AI hardware / optical / NAND-memory momentum), the exact cohort a momentum + net-long book is built to ride. Moderately concentrated, not a lone meme runner.
- **42/69 names positive.** **OOS Sharpe EX-TOP-NAME (additive) = +3.07** (drops just 0.32). **NOT a 1-2-name artifact** — but the edge is a *thematic* concentration that could reverse with the AI/memory cycle.

## Check 3 — Benchmark-relative: ~65% market-neutral alpha, ~35% beta on a monster tape

- **EW-69 PIT market OOS return = +133% compound** (the tradeable universe is mega-cap AI/growth — it *ripped*). EW-broad-500 S&P proxy (survivorship-biased, overstates) = only **+34%** → the EW-69 "market" is itself an AI-momentum-loaded cohort.
- **Book OOS realized beta on EW-69 = +0.19** (IS beta +0.12; risk-note +0.12 — the tilt ran a touch hotter OOS).
- **Beta-TILT contribution (β × market) = +19% compound = 35% of OOS ΣPnL.**
- **RESIDUAL market-neutral alpha = +39% compound = 65% of OOS ΣPnL, residual monthly Sharpe +2.21.**
- Verdict: the +65% is **NOT mostly captured beta** — the majority is residual market-neutral alpha and even the residual carries a +2.2 Sharpe. But a **non-trivial ~35% is beta riding an extraordinary +133% tape** — remove the favorable tape and a third of the return disappears.

## Check 4 — Directional-tilt split: the OOS strength is the NEUTRAL momentum CORE, not the TSMOM tilt

| book | IS Sharpe | OOS Sharpe | OOS tot |
|------|----------:|-----------:|--------:|
| NEUTRAL lam=0.00 + VIX (mom+LTR, no TSMOM) | +0.30 | **+2.95** | +55% |
| DEPLOYED lam=0.25 + VIX (with TSMOM tilt) | +0.61 | **+3.39** | +65% |

- **The directional TSMOM tilt adds only +0.44 OOS Sharpe.** The +3.39 is **overwhelmingly the market-neutral cross-sectional momentum core** (λ=0 already OOS +2.95).
- **This is the single most important — and most suspicious — number:** the neutral core went **IS +0.30 → OOS +2.95 (~10×)**. It is NOT a leak (Check 6). It is a **pure favorable-regime effect**: the IS window (2010-25) is dragged down by the low-dispersion melt-ups where cross-sectional momentum earns ~0 (2017 −1.11, 2019 −0.96); the OOS window (2025-26) landed squarely in momentum's *best* regime — a high-dispersion, strongly-trending AI/semis tape. The tilt the iteration was *designed around* (win the melt-ups) contributed almost nothing to the reveal; the reveal is the base engine catching a great momentum year.

## Check 5 — Small-sample honesty: point estimate is barely distinguishable from +1.0

- n = **16 monthly obs**. Lo-2002 iid Sharpe SE ≈ **1.05** (annualised). **95% CI = [+1.33, +5.46].**
- Distinguishable from +1.0? z = (3.39−1.0)/1.05 = **2.27 → YES, but only marginally** (+1.0 sits just below the CI floor of +1.33).
- **The CI is enormous.** The true Sharpe could plausibly be anywhere from ~+1.3 to ~+5.5; **+3.39 is a point estimate with no precision.** A defensible lower bound is ≈+1.3, not +3.4.

## Check 6 — Leak re-confirm: CLEAN

- **OOS uses the SAME past-only `net_from_raw`/`banded_net` path, sliced by date — no OOS-specific code branch** (revealed +3.39 == `msharpe(dep, OOS, HI1)` on the exact reveal path: CONFIRMED).
- **Committed future-bar signal leak self-check (lam=0.25, combined+VIX): PASS** (corrupt post-cutoff close+ret_fwd → IS net bit-identical). TSMOM reads `close.shift(252)` + trailing-63 rvol (pure past); the blend feeds the strictly-causal iter-003 band; VIX is ffill-then-`.shift(1)`.
- Decomposition ties out to the official reveal net (recon + split both exact). The 58-test tradfi suite is green.

---

## VERDICT

**GENUINE but FAVORABLE-REGIME — real and leak-free, but the MAGNITUDE is regime-inflated and small-sample-fragile; do NOT extrapolate +3.39.**

The +3.39 survives every artifact test: it is **not a leak** (same past-only path, self-check PASS, decomposition exact), **not a 1-2-month spike** (ex-best-month +3.23, 13/16 months up), **not a 1-2-name artifact** (ex-top-name +3.07, 42/69 names up), and **not mostly beta** (~65% is residual market-neutral alpha, residual Sharpe +2.2). But it is a **favorable-regime realization of the market-neutral MOMENTUM CORE, not of the directional tilt the iteration was designed around** — the neutral λ=0 book alone is OOS +2.95 (an ~10× jump off its IS +0.30), because the OOS window was an exceptional high-dispersion AI/memory momentum tape (EW-69 +133%) that is precisely cross-sectional momentum's best regime and precisely the regime the 2010-25 IS is *dragged down* by. The name concentration is thematic (AI hardware/memory, 42% top-3) and cycle-dependent, the beta tilt (~35% of PnL) rode a once-in-a-cycle +133% cohort, and the 95% CI [+1.33, +5.46] shows the point estimate has no precision.

**Honest read for merge/deploy:** treat +3.39 as a *direction-confirming* OOS (positive, broad, leak-free) but expect a through-cycle forward Sharpe far below it — the IS +0.61 is the honest through-cycle anchor and +1.3 (the 95% CI floor) is the defensible optimistic lower bound. The reveal validates that the book is real and correctly signed; it does **not** validate a +3.4 edge, and the deployed config already failed the 2×-cost bar (IS +0.42) and the 16/16-year bar (13/16) at EXPLORATION — those constraints stand.
