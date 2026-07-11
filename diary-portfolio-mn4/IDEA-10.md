# IDEA-10 — Born-Diverse Ensemble (diary)

**Track:** MN4 blind tournament · **Idea:** 10 · Born-Diverse Ensemble
**Pair:** QR+QE (Opus 4.8 — Fable rate-limited this session; user-directed. Disclosed per charter §"Model".)
**Date:** 2026-07-11/12 · **Verdict:** IS-gate FAIL → NOT reveal-ready (no token spent)

## Decision: NO-MERGE / NOT reveal-ready

The construction is frozen byte-exact and banked as a **documented finding**, not
a holdout candidate. The IS gate fails on a structural, charter-anchored check
(CRASH-bucket Sharpe -1.005 < -0.5). The 2-year holdout remains pristine.

## Construction (frozen one-liner)

4 orthogonal slow members — `ts_mom90` (BTC-residualized 30d trend) · `carry21`
(−1w funding carry) · `reversal21` (−1w return reversal) · `ownvol90` (own-pctl
vol tilt) — each weekly rank-neutral dollar-neutral at gross 1.0, combined as a
cross-sectional **z-blend at inverse-trailing-vol weights** (`w_i = 1/σ_i`,
90c past-only, NOT IS-Sharpe); composite runs rank-neutral + **HedgeOverlay**
(BTC always + ETH armed) for composite-level β-hedge + **Layer-2 throttle**
(vol-target 20% + dd_brake 15%→0.5×).

## IS headline

| metric | value |
|---|---|
| composite Sharpe 1× | **+0.496** |
| composite Sharpe 2×-GT | **+0.277** (cost-survives) |
| composite maxDD | **-29.7%** (shallower than ALL members: -47% to -89%) |
| median pairwise member corr | **-0.144** (genuinely orthogonal) |
| composite β_BTC post-hedge | **-0.026** |
| CRASH-bucket β_BTC | -0.008 (well-hedged) |
| CRASH-bucket Sharpe | **-1.005** (gate-killer) |

## Did the composite beat the best member?

**No — on Sharpe.** Best member `carry21` = +1.250; composite = +0.496 (trails by
-0.753). Two members (`reversal21` -0.91, `ownvol90` -0.56) are individually
negative, and inverse-vol risk-equalization is return-agnostic, so it cannot
down-weight the losing sleeves (~equal risk budget 0.23-0.27 each).

**Yes — on maxDD.** Composite -29.7% is shallower than every member (best
member -47.3%, worst -89.5%). The DD-diversification claim is CONFIRMED and
measured. The composite is also cost-surviving (2× Sharpe +0.277) and
effectively β-neutral (-0.026).

## What worked

1. **Orthogonalization from birth.** Median pairwise member corr -0.144; the
   `ts_mom90` × `reversal21` pair is -0.521 by design (momentum vs reversal),
   `ts_mom90` × `ownvol90` is -0.627, `carry21` is near-independent of the
   return-based members (+0.10/-0.097/-0.192). The four-mechanism diversity
   (trend / positioning / mean-reversion / vol-regime) delivered genuine
   decorrelation — exactly the directive's premise.
2. **DD-diversification.** Composite maxDD ~40% shallower than the best member.
   This is the robustness axis the charter values most ("very controlled risk").
3. **Composite-level beta hedge.** HedgeOverlay drove post-hedge β_BTC to -0.026
   (members ran raw, unhedged — confirming the directive's warning that
   "member neutrality does NOT automatically compose").
4. **Cost-survival.** Weekly cadence + vol-targeted gross (mean 0.68) → 2×-cost
   Sharpe +0.277. Funding was a net +0.6bp/candle tailwind (shorts earned
   positive funding in mania crowding).

## What failed (honest)

1. **The Sharpe-claim is FALSIFIED.** Born-diverse inverse-vol ensembling does
   NOT beat the best member when 2/4 members are negative-expected-return.
   Inverse-vol is risk-equalization, NOT return-aware. This is the structural
   limitation, not a tuning failure.
2. **Two members structurally negative.** `reversal21` negative in 4/5 IS years;
   `ownvol90` negative in 4/5 years. Crypto-native diagnosis:
   - 21c (weekly) reversal fights the dominant monthly-horizon momentum regime
     in crypto — the real crypto reversal edge is *short*-horizon (1-3d,
     post-liquidation-cascade), not weekly.
   - own-history-vol-tilt (long contracting-vol) is not a well-established edge
     and may pick up stale momentum.
3. **Not all-weather.** CRASH-bucket Sharpe -1.005; per-year 2023:-0.44,
   2024:-1.36. The composite is mania-heavy (2021 +2.28). The throttle (brake
   fired 167/232 rebals) reduced loss magnitude (maxDD proof) but cannot fix the
   Sharpe *sign* in the acute regime.

## The methodological value (the finding)

The directive anticipated two outcomes: (a) members too correlated → mechanism
overlap finding; (b) decorrelation → Sharpe-beating. **This experiment resolved
a THIRD case:** members ARE genuinely orthogonal AND DO diversify the DD
(maxDD -29.7%, β ≈ 0, cost-surviving) — but inverse-vol risk-equalization
cannot produce Sharpe-beating when some members are negative-expected-return,
because it equalizes risk, not return. **Diversification-as-design delivers on
the robustness axis but NOT automatically on the Sharpe axis.** That is a clean,
generalizable structural result.

## Lessons (dead-paths / reusable)

- **Born-diverse inverse-vol ensembling is a risk primitive, not an alpha
  primitive.** It is the right tool for DD-control + neutrality + cost-survival,
  not for Sharpe-boosting over negative members.
- **Member selection matters more than the combination rule.** A return-aware
  blend (e.g. inverse-Sharpe or sign-gating) would help but is IS-mining unless
  pre-registered. A genuinely better path is crypto-native member choice
  (short-horizon cascade reversal, OI-tilt) — but selecting post-IS is mining.
- **Weekly reversal at 21c is the wrong horizon for crypto** (momentum
  dominates monthly); the post-cascade short-horizon reversal is the real edge.
- **The HedgeOverlay composition check is correct**: member neutrality did NOT
  compose (members ran raw; composite β-hedge was needed and delivered β ≈ 0).

## Leak battery (charter mandate — all PASS)

`tests/test_mn4_idea10_signals.py` (9 tests, 1.2s):
- corrupt-future positive control (each member + composite): signal[:t]
  bit-identical under corruption of close/funding from row t onward.
- decision-lag: invol weights consume rets ≤ t; composite consumes weights at [t-1].
- append-invariance: appending a future candle leaves composite[:T] unchanged.
- structural: invol weights non-negative, sum to 1, warmup equal-weight fallback,
  inverse-to-vol ordering (low-vol member outweighs high-vol member).

## Honest cost / engine parity

Every metric runs through `blind_engine.run_backtest` (next-bar open-to-open
fills, 5+2.5bps + funding, 2×-cost GT twin re-run). IS-only via `mn3_split`
guard (cutoff 2024-07-01). ZERO holdout reads. The construction is frozen.

## Next-iteration ideas (banked, not pre-judged)

1. **Member re-derivation from crypto-native principles** (pre-registered, NOT
   IS-Sharpe-selected): replace `reversal21` with a short-horizon
   post-liquidation-cascade reversal (3-5c); replace `ownvol90` with an OI-tilt
   or funding-momentum sleeve. Re-freeze and re-test the ensemble.
2. **Return-aware blend as a SEPARATE pre-registered rule**: e.g. sign-gate
   members (drop sleeves with trailing-negative-Sharpe over a long window) —
   but this must be declared a-priori as the weighting rule, not fitted post-IS.
3. **Drop to 2-strong-member ensemble** (ts_mom90 + carry21) — but this is
   post-IS selection and must NOT be claimed as a generalizable result without a
   pre-registered member-selection rule.

These are candidates for a *different* frozen construction; THIS construction
(IDEA-10) is frozen, failed the IS gate honestly, and is closed.

## Banked-for-reveal?

**NO.** IS gate FAIL (CRASH Sharpe -1.005). No holdout token spent. The
construction is documented as a finding; the holdout stays pristine.

---

*Diary closed. Construction frozen at `analysis/portfolio/mn4_idea10_signals.py`
+ `analysis/portfolio/mn4_idea10_run.py`; scorecard at
`data/mn4_idea10/scorecard.json`. Model: Opus 4.8 (Fable rate-limited; user-directed).*
