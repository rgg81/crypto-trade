# EXPLORATION-005 — Second non-price axis scout → FRONTIER VERDICT (no 5th sleeve)

**Track:** metals portfolio. **Date:** 2026-06-25. User directive: bold, non-obvious, search internet.
**Verdict:** ⛔ **FRONTIER / NEGATIVE** (Critic CONCURS) — no candidate robustly beats the 4-sleeve
book net-of-cost. **No sleeve added.** OOS hidden.

## The question
iter-004 (COT positioning) was the breakthrough — slow, weekly, NON-PRICE, contrarian. Does a SECOND,
DIFFERENT non-price information TYPE add orthogonal value beyond it, or is positioning the only edge?

## What was scouted (all NEGATIVE, IS-only, net 6bps/side, leak-safe)
| Candidate | Mechanism | Standalone IS SR | corr to book | Best combined lift | Why it failed |
|---|---|---|---|---|---|
| **ETF physical-demand flow (GLD)** | physical investment demand (Δholdings) | −0.22..+0.23 | ≈0 | **+0.000** | orthogonal but NO lift — gold-only (no cross-section; SLV/PPLT/PALL holdings not freely/leak-safely sourceable), and ETF demand CHASES price → echo of the trend anchor |
| **GVZ gold-VIX / vol-risk-premium** | options-implied vol regime | −0.11..−0.71 | ±0.3 | −0.002 | all negative; vol chases price down; VRP turnover 0.15/candle = cost-lethal; gold-only |
| **COT-flow (Δ MM-net/OI) contrarian** | positioning FLOW extremity | +0.09 | +0.28 to MM sleeve | +0.07 agg BUT **falsifier FAILS** | 0/9 cells both-halves-positive (H1 −0.08..−0.21 / H2 +0.16..+0.43 = recent-half artifact); same info-type as iter-004; ~4× turnover — the OOS-inflation TRAP |
| **Commercial (producer) follow** | hedger "smart money" | +0.19 | +0.47 to MM sleeve | +0.015 | redundant — producer net is the OI-mirror of MM net (−0.6..−0.96 corr) |

Data hard-stops found: `yfinance.get_shares_full()` is a stale 2016-2021 snapshot, empty for PPLT/PALL;
iShares SLV holdings endpoint is an HTML consent wall. Only GLD has a clean free leak-safe daily
holdings feed (SPDR `historical-archive`). So an ETF-flow cross-section can't be built right now.

## Durable lessons (Critic-endorsed — the value of this iteration)
1. **Orthogonality ≠ lift.** A corr≈0 return stream with HIGHER raw IC than the incumbent COT sleeve
   (GLD +0.006–0.014 vs COT +0.0037) still added **+0.000** — because the long-gold trend anchor
   already expresses the gold-demand exposure. Decorrelation is necessary, not sufficient; incremental
   information *net of the existing book* is the real test.
2. **The non-price-POSITIONING axis is exhausted at COT.** MM-level (iter-004, merged) is the surviving
   form; MM-flow inverts across IS halves; commercials are the OI-mirror (redundant); ETF demand
   echoes price; vol/VRP is cost-lethal. No further single-name positioning sleeve is worth scouting.
3. **The half-split falsifier is working consistently** — it gated iter-003 pt/pd to PROMOTABLE=False
   and now COT-flow. That consistency is the evidence the rejects aren't ad hoc.

## Critic note (CONCUR — frontier verdict sound)
Verified the scout harness is parity-correct (single net_from_raw, gross-norm, leak-safe — not an
artifact hiding edges). COT-flow reject correct on TWO independent grounds (half-split inversion +
redundancy). GLD null is a real subsumption finding. GVZ leak-clean + genuinely cost-lethal.
**One caveat recorded:** cross-sectional COT-*flow* dispersion (demean weekly ΔMM-z across the 4
metals) is **law-compliant but UNTESTED — deferred, not dispositive**. iter-004's "V5" only ruled out
the *level* cross-sectional form; the *flow* cross-sectional form is technically untested but
LOW-PRIOR (inherits both the 4-name thinness that killed V5 and the flow half-split instability). Not
worth blocking on.

## Path forward — the strategic fork (Critic-ranked)
The data/signal axis within the **4-metal, 8h, taker-cost** regime is near-saturated: the edges are
trend + cross-sectional dispersion + COT positioning. Further gains need a STRUCTURAL change:
1. **CONFIRMATION of the 4-sleeve iter-004 book** (the disciplined call) — multi-seed validate + reveal
   OOS under the same single-net_from_raw engine, no re-tuning. iter-004 is deep-history, leak-clean,
   falsifier-PASSING. **NOTE: user reserved the OOS reveal for "the end" — their call.**
2. **Copper-as-tradeable universe expansion (4→5 names)** — the Critic's highest-leverage structural
   move: copper is the missing cyclical-industrial leg; widening the cross-section directly attacks the
   4-name thinness behind every cross-sectional signal's failure. Copper COT already ingested
   (`ingest_cot.py:42`). **CAVEAT: copper is NOT on Binance (delisted) — this breaks the live-parity /
   "4 precious perps" universe the user chose; the copper leg would be backtest/research-only or need a
   non-Binance venue. Needs user sign-off.**
3. **ML synthesis of the already-discovered signals** — a shallow, regularized, walk-forward model over
   the existing leak-safe sleeve features (trend state, MM-level z, dispersion, pt/pd ratio), IS-only
   with embargo, testing whether a NONLINEAR combination beats the fixed-weight linear sum. No new data
   axis, no new leak surface, reuses the audited engine. In-bounds.

## Files
- No code change (frontier verdict). Scout harness lived in scratch (not committed). Diary only.
