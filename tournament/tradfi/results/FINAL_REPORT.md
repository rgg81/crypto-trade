# tradfi-cup-01 — FINAL REPORT

**Winner: team-10 — per-name 12-month sign trend (`t10-ts-trend-v1`).**
Net holdout Sharpe **+2.153** (funding on, 2024-07-01 → 2026-06-30), maxDD −9.4%,
IS-replay bit-identical. Deploys to the second paper desk per charter §12.

## Tournament summary

10 teams (QR=Fable + QE=Opus each), clean-room IS research on a frozen 65-name+VIX snapshot
(2010-01-01 → 2024-06-30, SHA-256 manifest f02c86bc…), sealed 2-year holdout run once per
finalist by the orchestrator. 9 frozen submissions + 1 honorable DNF. Critic (Fable,
read-only): zero integrity failures across the cohort; one orchestrator-side registry gap
fixed as journaled amendment #1.

Four pre-registered falsifiers fired during research (52wk-high direction, low-vol/BAB,
sector-pairs cointegration, plain short-horizon reversal, short-MAX lottery = five family
kills across four teams); two teams pivoted via disclosed sign-flip diagnostics (Critic-
verified provenance chains), one team pivoted to a free family, one took the DNF.

## Stage 1 (net IS Sharpe @1×, critic-gated; all 9 reproduced byte-identically)

| rank | team | family | IS 1× | IS 2× | maxDD | finalist |
|---|---|---|---|---|---|---|
| 1 | team-10 | per-name 12m sign trend | +0.820 | +0.765 | −23.2% | YES |
| 2 | team-06 | VIX-regime books | +0.739 | +0.639 | −23.0% | YES |
| 3 | team-09 | jump momentum (pivot) | +0.727 | +0.689 | −33.3% | YES |
| 4 | team-03 | stress-gated sector reversal | +0.568 | +0.439 | −32.5% | YES |
| 5 | team-04 | 12-1 momentum + hysteresis | +0.525 | +0.471 | −23.3% | |
| 6 | team-02 | anchor-discount contrarian (pivot) | +0.492 | +0.470 | −39.1% | |
| 7 | team-01 | residual momentum | +0.455 | +0.418 | −28.3% | |
| 8 | team-07 | overnight persistence | +0.448 | +0.417 | −35.0% | |
| 9 | team-05 | Amihud illiquidity (pivot) | +0.350 | +0.342 | −42.9% | |
| — | team-08 | short-horizon reversal | DNF (falsified 31/31) | | | |

## Stage 2 — sealed holdout (2024-07-01 → 2026-06-30, perp splice + funding on)

| rank | team | canonical | no-funding | 2× cost | ex-PAYP | maxDD |
|---|---|---|---|---|---|---|
| 1 | **team-10** | **+2.153** | +2.164 | +2.101 | +2.078 | −9.4% |
| 2 | team-09 | +2.095 | +2.100 | +2.081 | +2.069 | −9.3% |
| 3 | team-06 | +1.721 | +1.731 | +1.627 | +1.689 | −8.3% |
| 4 | team-03 | −0.662 | −0.644 | −0.856 | −0.613 | −20.7% |

All four IS-replays bit-identical (causality cross-check passed). Funding drag was small
(canonical vs no-funding ≤ 0.011 Sharpe) — perps only existed for the 2026 tail.

## Honest caveats (read before celebrating)

1. **Noise floor.** 24 monthly points ⇒ holdout Sharpe SE ≈ 0.77. team-10 vs team-09
   (Δ = 0.058) is deep inside noise — the locked rule (best canonical Sharpe) decides, but
   statistically ranks 1–2 are a tie, and even rank 3 is within ~0.6 SE.
2. **Regime concentration.** The holdout window was a strong trend regime for this universe;
   holdout Sharpes 1.7–2.2 vastly exceed the IS levels (0.45–0.82). Expect paper-trading
   performance closer to (or below) IS levels; team-10's own brief predicted holdout below
   its IS point estimate.
3. **Selection-on-IS at the top of the board** (Critic systemic note): team-03 and team-06
   embed state-conditioning found after unconditional books failed; team-09's family
   direction was chosen after observing an IS diagnostic. team-03's holdout collapse
   (−0.66) is this risk realized. team-10's book is the plainest construction of the four
   finalists — a point in its favor beyond the headline.
4. **team-10 book shape.** Long-heavy (median 37L/11S, mean net +0.195 within the 0.25 cap),
   bear-regime IS Sharpe −1.13: this book will bleed in a sharp bear. The paper desk should
   be watched with that expectation, not surprise.

## Critic verdicts

8 PASS, team-06 PASS after amendment #1, team-08 PASS-as-DNF. Zero DQs. Full report:
`tournament/tradfi/critic/PHASE3-COHORT-REPORT.md`.

## Deployment

Winner deploys via `run_tradfi_tournament_paper.py` — a second `TradfiPaperEngine` instance
(own DB `data/tradfi_tournament_paper.db`, equity CSV `data/tradfi_tournament_equity.csv`,
refresh staggered vs the incumbent desk), weight source = team-10's frozen
`build_raw_weights` through the tournament engine's caps, on the frozen-IS-canon spliced
panel (same data path as Stage 2). The incumbent iter-016 desk is untouched.
