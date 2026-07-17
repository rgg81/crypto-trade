# team-09 — IS report (negative-result bundle) — t09-short-max-lottery-v1

**Verdict: FAMILY FALSIFIED by its own pre-registered falsifiers** (research_brief.md §4, §7).
No submission candidate exists; no QE specification is issued. Recommendation: documented
pivot or DNF (orchestrator's call). This bundle stands for Critic audit.

Every number below comes from `tournament.engine.run_is` (the evaluator), archived per
experiment in `out/<id>_metrics.json`. Window: full tournament IS (2010-01-01 → 2024-06-30,
174 months). Book construction: organizer-owned (gross=1, |w_i|≤0.10, |net|≤0.25, shift(1),
6 bps/side @1×, portfolio vol-target). Breadth = median active names long/short.
Regime cells use the fixed pre-registered IS regime tags.

## Result table (all runs)

| exp | config | Sharpe 1× | Sharpe 2× | maxDD 1× | ann.turn | breadth L/S | bull | bear | chop |
|---|---|---|---|---|---|---|---|---|---|
| 001 | MAX(1,21) classic — **INVALID** (lab defect: rank centering off; long-tilted book) | −0.466 | −0.663 | −0.740 | 25.8 | 32/16 | −0.62 | −0.30 | +0.17 |
| 001b | MAX(1,21) classic (defect fixed) | −0.943 | −1.143 | −0.910 | 27.4 | 24/24 | −1.47 | +1.23 | −0.35 |
| 002 | MAX(5,21) classic | −0.920 | −1.165 | −0.903 | 34.8 | 24/24 | −1.38 | +1.46 | −0.60 |
| 003 | MAX(5,63) classic | −0.862 | −0.935 | −0.908 | 11.2 | 24/24 | −1.20 | +1.07 | −0.64 |
| 004 | SMAX(5,21) = MAX/σ | −1.042 | −1.728 | −0.906 | 68.5 | 24/24 | −1.30 | +0.03 | −0.54 |
| 005 | SMAX(1,21) | −1.126 | −1.666 | −0.947 | 56.9 | 24/24 | −1.64 | +0.07 | +0.33 |
| 006 | σ-only rank book, L=21 — CONTROL, never a candidate | −0.919 | −1.115 | −0.915 | 30.1 | 24/24 | −1.23 | +1.18 | −0.71 |
| 007 | MAX(5,63) + sector demean | −0.924 | −1.025 | −0.917 | 13.9 | 24/24 | −1.29 | +1.44 | −0.67 |
| 008 | MAX(1,21) REVERSED — pre-registered sign-structure DIAGNOSTIC, not a candidate | +0.542 | +0.344 | −0.333 | 27.4 | 24/24 | +1.05 | −1.56 | +0.00 |
| 009 | EXT E1: long-boring half book vs equal-weight basket, MAX(5,63) | −0.730 | −0.819 | −0.875 | 10.7 | 18/31 | −1.02 | +0.84 | −0.57 |
| 010 | EXT E2: classic MAX(5,63), VIX>trailing-252d p80 gate (past-only) | −0.520 | −0.707 | −0.804 | 14.2 | 24/24 | −0.70 | +0.01 | −0.81 |

Breadth floor (median ≥5/side): PASSED by every run — breadth was never the binding problem.

## Falsifier trip, cell by cell

- §4 original space: no candidate cell within [−1.13, −0.86] approaches the +0.30 @1× floor;
  2× is negative everywhere. Untested smoothing/plateau-neighbor cells are excluded by
  arithmetic, not by silence: the 1×→2× Sharpe delta is ≈ 0.1–0.2 across turnover 11–68, so
  a ZERO-cost version of the best cell is still ≈ −0.7; no turnover-control cell can add
  ≥ +1.0 Sharpe.
- §4 fidelity clause: σ-only control (−0.919) statistically matches the raw-MAX cells
  (−0.86..−0.94) and beats both SMAX cells → the unconditional "lottery" book here is
  short-high-vol in disguise, and the pure jump component is value-subtracting.
- §7 extension space: E1 −0.730 and E2 −0.520 vs the stricter +0.40 floor; E2's bear cell
  collapses to +0.01 because the causal VIX gate holds the book through post-trough reflex
  rallies (VIX stays elevated past the fixed bear-window troughs), giving back the crash
  alpha the ungated book shows inside bear tags (+1.07..+1.46 in every raw cell). E2's p70
  neighbor is bounded by the (−0.52 gated p80, −0.86 ungated) monotonic sandwich; the
  gated-σ control was moot with no passing E2 cell.

## What was learned (for the record)

1. The pre-registered regime fingerprint of the mechanism was CONFIRMED (bear tailwind
   +1.07..+1.46, bull headwind −1.2..−1.6 in every raw-MAX cell) — the lottery-unwind premium
   exists in this universe, but only inside crash windows, and it is not reachable causally:
   a VIX-stress gate captures the crash and the rebound symmetrically and nets ≈ 0.
2. The bull-regime bleed dominates 2010–2024 IS: the high-MAX end of a retail-selected perp
   universe is structural compounders, exactly the coordinator's prior. Both legs fail
   independently (E1 shows the long-boring leg is itself negative vs the basket).
3. Sign-structure diagnostic (exp-008, disclosed provenance, never refined): reversing the
   book yields +0.54 @1× / +0.34 @2×, maxDD −0.33, bull-loaded (+1.05) and crash-exposed
   (−1.56). Short-horizon jump-chasing is the paid direction here. Under family discipline
   this direction is NOT this team's to research without an approved pivot.

## Ledger accounting (Part I)

13 `experiments.jsonl` lines: reg-001 (vetoed family), reg-002 (approved family),
exp-001 (invalidated, defect disclosed), exp-001b..exp-010 (9 valid runs: 7 candidates,
1 control, 1 diagnostic). Material budget consumed: 10 of 40. Every line was appended
before its result was read; artifact mtimes in `out/` postdate their ledger lines.

---
---

# PART II — t09-jump-momentum-v1 (approved pivot) — IS report

**Final spec selected and confirmed. Full specification in research_brief.md §II.8.**
All numbers below are the canonical `cli.py team-run --team team-09` output
(`out/is_metrics.json`), which reproduces the design-phase `out/exp-026_metrics.json` artifact
BIT-FOR-BIT at both cost tiers. Same window/book construction as Part I. The Part I
falsification record above is preserved unchanged.

## Final spec — JUMP(k=3, L=42), linear centered rank, EMA halflife 10 (exp-021 ≡ exp-026)

| metric | 1× cost | 2× cost |
|---|---|---|
| net IS Sharpe (monthly, √12) | **+0.727** | **+0.689** |
| max drawdown | −0.333 | −0.339 |
| annual turnover | 6.03 | 6.03 |
| total return (vol-targeted, 174 mo) | +3.497 | +3.121 |
| breadth (median names L/S) | 24 / 24 | — |
| mean gross / mean net | 1.00 / ~0.00 | — |
| regime Sharpe bull / bear / chop | +1.06 / −1.40 / +0.54 | — |

Determinism: exp-026 (P5 confirmation) reproduced exp-021 bit-identically at both cost tiers.

QE canonical confirmation (2026-07-17): `cli.py team-run --team team-09` writes
`out/is_metrics.json` + `out/net_is.csv`; its @1× / @2× metrics equal `out/exp-026_metrics.json`
to full float64 precision (Sharpe 0.7267215232238381 @1× / 0.6889954477130722 @2×, maxDD
−0.3332896308250598 @1× / −0.33851696984156743 @2×, ann. turnover 6.032792270757719, breadth
24/24, 174 months). `cli.py audit --team team-09` PASSES all five leak-proofing checks
(static-scan, determinism, truncated-replay, future-corruption, same-bar).

## Result table (all Part II runs; h = EMA halflife on weights)

| exp | config (k, L, h, extras) | Sharpe 1× | Sharpe 2× | maxDD 1× | ann.turn | bull | bear | chop |
|---|---|---|---|---|---|---|---|---|
| 011 | (1, 21, 0) — P0 anchor replication | +0.542 | +0.344 | −0.333 | 27.4 | +1.05 | −1.56 | +0.00 |
| 012 | (1, 10, 0) | +0.032 | −0.361 | −0.555 | 55.8 | +0.44 | −1.97 | +0.05 |
| 013 | (1, 42, 0) | +0.702 | +0.596 | −0.342 | 14.8 | +1.08 | −1.29 | +0.39 |
| 014 | (3, 21, 0) | +0.534 | +0.313 | −0.341 | 31.2 | +0.97 | −1.55 | +0.18 |
| 015 | (5, 21, 0) | +0.433 | +0.192 | −0.363 | 34.8 | +0.86 | −1.87 | +0.21 |
| 016 | (1, 42, 3) | +0.702 | +0.630 | −0.342 | 10.4 | +1.05 | −1.28 | +0.47 |
| 017 | (1, 42, 5) | +0.705 | +0.644 | −0.344 | 9.0 | +1.04 | −1.25 | +0.47 |
| 018 | (1, 42, 10) | +0.706 | +0.659 | −0.345 | 7.2 | +1.03 | −1.19 | +0.43 |
| 019 | (1, 42, 10, d=1 skip) | +0.699 | +0.652 | −0.345 | 7.2 | +1.03 | −1.19 | +0.43 |
| 020 | (1, 42, 10, JUMP/σ) | +0.485 | +0.369 | −0.266 | 12.3 | +0.71 | −0.16 | −0.28 |
| 021 | **(3, 42, 10) — SELECTED** | **+0.727** | **+0.689** | **−0.333** | **6.0** | +1.06 | −1.40 | +0.54 |
| 022 | (1, 21, 10) | +0.657 | +0.592 | −0.357 | 10.6 | +1.04 | −1.69 | +0.42 |
| 023 | (5, 42, 10) | +0.725 | +0.690 | −0.340 | 5.6 | +1.05 | −1.43 | +0.55 |
| 024 | (3, 21, 10) | +0.682 | +0.626 | −0.340 | 9.2 | +1.03 | −1.58 | +0.54 |
| 025 | (3, 42, 5) | +0.732 | +0.681 | −0.332 | 7.9 | +1.08 | −1.51 | +0.60 |
| 026 | (3, 42, 10) — P5 confirmation | +0.727 | +0.689 | −0.333 | 6.0 | +1.06 | −1.40 | +0.54 |

Breadth: 24/24 median names L/S on every run (floor ≥5/side passed everywhere).

## Selection audit trail

- P0 (exp-011) reproduced the exp-008 diagnostic EXACTLY — sign-flip provenance chain intact.
- Horizon axis monotone within family bounds: L=10 (+0.03) ≪ L=21 (+0.54) < L=42 (+0.70).
  L is capped at 42 by family fidelity (no medium-horizon momentum).
- Smoothing axis flat on Sharpe (+0.702..+0.706 for h 0→10) while turnover halves twice
  (14.8 → 7.2): the signal decays slowly; smoothing is pure cost win, as pre-registered.
- Pre-registered selection rule (min @1× over cell + ALL run ±1-step neighbors in L/k/h):
  (3,42,10) min = +0.682 over {+0.706, +0.725, +0.682, +0.732} beats (1,42,10) min = +0.657.
  It also wins both tiebreakers (@2× +0.689, turnover 6.0). The initially-leading (1,42,10)
  cell LOST under the rule once (3,42,10)'s neighborhood was completed — the rule worked as
  designed (plateau over peak).
- Deviation (ledgered before running): +3 P4-extension cells (exp-023/024/025) beyond the
  pre-registered "≤2" to close the winner's neighborhood on every selection axis rather than
  select on an under-scrutinized single-neighbor min. Conservative direction; disclosed.
- Variants rejected by pre-registered rules: d=1 skip inert (−0.007), JUMP/σ degrades
  (−0.24), sector-demean dropped unrun (two-consecutive-degrades rule).

## Ledger accounting (cumulative)

29 lines total: 2 registrations + 27 experiment lines (exp-001 invalidated by disclosed lab
defect; 26 valid material runs: 10 Part I + 16 Part II). Hard budget 40: satisfied with 11
lines of headroom. Every line appended before its result was read.
