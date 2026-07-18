# team-08 — IS report

Family: `t08-oi-price-confirmation-v3` (registry-approved pivot; original family
`t08-short-horizon-reversal-v2` falsified — record in §6).
Strategy: S1γ0 confirm-only OI-price confirmation — centered-rank of σ-scaled 18-candle
displacement, gated by sign(Δlog OI over 18 candles), count≥10 guard, EMA halflife 2.
Spec: `research_brief.md` §A8, implemented verbatim in `strategy.py` (harness PASS 6/6).

Unless labeled otherwise, every number below is from `out/is_metrics.json` (team-run,
IS window 2020-01-01 → 2024-07-01 exclusive, 54 monthly points).

## 1. Headline (board metrics)

| metric | @1x | @2x-stress |
|---|---|---|
| **net IS Sharpe** | **+0.4596** | **+0.2049** |
| max drawdown | −28.9% | −32.6% |
| total return | +67.2% | +14.4% |
| ann. turnover | 131.9 | 131.9 |
| breadth (median L/S) | 24 / 15 | 24 / 15 |
| total cost (unlevered, cum.) | 0.3604 | 0.7208 |
| total funding P&L (unlevered, cum.) | +0.0848 | +0.0848 |
| mean gross / mean net | 0.993 / +0.163 | 0.993 / +0.163 |

## 2. Full-window vs active-window decomposition (ON THE RECORD)

OI coverage is structurally binary (census, ledger e04): exactly 1 valid name before
Dec-2021, ~40 after. The strategy is therefore flat by construction for the first 24 of 54
IS months, and the board metric carries that dilution in full.

- Full-window (team-run, official): **+0.4596 @1x / +0.2049 @2x**.
- Active-window, lo = 2022-01-01 08:00 UTC (SCRATCH provenance, evaluator-computed, ledger
  e06/e08, `out/scratch/results_e06.json` row ["S1g0","z",18,18,2]): **+0.939 @1x /
  +0.578 @2x**, maxDD −0.289, ann. turnover ≈ 232 over the active period (the full-window
  turnover of 131.9 averages in the flat months).
- **Measured dilution factor ≈ 0.49** (0.4596 / 0.939) — worse than the ~0.7 estimated at
  pivot time; declared here per the orchestrator's on-record requirement.

The Stage-1 board ranks the diluted **+0.460**. That is the honest full-window number and we
stand on it.

## 3. Regime honesty — bull concentration caveat

Full-window regime Sharpe (team-run):

| bucket | @1x | @2x |
|---|---|---|
| bull | +1.053 | +0.974 |
| bear | +0.115 | −0.086 |
| chop | +0.066 | −0.484 |

Active-window (scratch, e06): bull +2.55 / bear +0.75 / chop +0.07.

All three buckets are non-negative at 1x, but the P&L is clearly BULL-LOADED (the ETF-bull
tag dominates; the covered window contains only one bull tag). At 2x-stress the full-window
bear and chop buckets go slightly negative — under doubled costs this strategy is
effectively bull-only. Stated plainly per the pre-registered regime-honesty commitment
(`research_brief.md` §A3). Note also that the pre-2022 tags (COVID crash, 2020-21 bull,
May-2021 crash) are structurally outside OI coverage: their bucket values reflect
near-flat months, not evidence of all-weather robustness.

## 4. V2 integrity disclosure (conditioned-minus-unconditioned)

Pre-registered kill criterion V2 required the OI gate to be load-bearing versus the
price-only analog on the same valid name-candle set (scratch, ledger e08,
`out/scratch/results_e08.json`):

- Selected config (L=18, H=2): **Δ = +0.035 @1x** — formal PASS but noise-level (30 monthly
  active points, Sharpe SE ≈ ±0.4); **Δ = +0.179 @2x**; maxDD −0.289 vs −0.385 (conditioned
  better); chop bucket +0.07 vs −0.29.
- Neighbor (L=18, H=4): Δ @1x −0.044, Δ @2x +0.093.
- Inner-plateau neighbor (L=9, H=4): **Δ @1x +0.320, Δ @2x +0.493** — strongly load-bearing.

Honest characterization: at the selected 6-day displacement horizon the commitment gate's
value shows up primarily in stress-cost robustness, drawdown, and chop behavior rather than
in 1x mean; the gate is strongest for fresh displacement. This disclosure is made for the
Critic exactly as pre-registered.

## 5. Funding thesis — confirmed

The registration expected roughly neutral-to-slightly-positive funding for the
OI-confirmed continuation book. Team-run: **total funding P&L +0.0848** cumulative
unlevered — positive, covering ~24% of the 1x cost load (0.3604). Thesis confirmed in sign
and order of magnitude. (Contrast: the dead reversal family's funding thesis was falsified,
§6.)

## 6. Dead-family record (Part B)

`t08-short-horizon-reversal-v2` (1–3 day cross-sectional overreaction fade) was falsified
under its pre-registered criteria (ledger e01–e03): max gross Sharpe +0.348 < 0.8 across
the full L grid with both rescue axes (σ-normalization, tail kernels) completed and worse;
its funding-alignment thesis also falsified (fade book paid −0.03…−0.11). The 8h–3d top-40
cross-section exhibited robust CONTINUATION instead — the ledgered finding that motivated
this family's displacement leg. Full record: `research_brief.md` PART B.

## 7. Honest expectations for the sealed holdout

Stated as belief bands, not knowledge — the holdout is sealed and nothing here derives
from it.

- The holdout window (2024-07 → 2026-06) has FULL OI coverage from its first candle, so the
  **active-window run-rate (~+0.9 @1x, scratch) is the better holdout prior than the
  diluted board number (+0.460)** — there are no structurally-flat months ahead.
- Against that, the regime table tempers the prior: our edge is bull-loaded, chop is ~0,
  and 24 monthly points carry a Sharpe SE of roughly ±0.8 at this level. Central
  expectation: **+0.4 … +0.9 @1x** depending on the holdout's bull/chop mix.
- Surprise bands: a holdout Sharpe below **−0.5** would indicate the mechanism failed out of
  sample (or a chop/bear-dominated window at stress-level costs); above **+2.0** would
  exceed anything the IS evidence supports and should be read as favorable variance, not
  skill confirmation.

## 8. Provenance of numbers

§1, §3 (full-window), §5, and §6-quoted metrics: `out/is_metrics.json` (team-run).
Active-window and V2 numbers: scratch evaluator runs, ledger ids e04–e08, artifacts in
`out/scratch/results_e0{4..8}.json`, labeled SCRATCH throughout. Experiment budget used:
8/40. Strategy and tests untouched by the QR after QE handoff.
