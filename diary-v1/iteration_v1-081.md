# iter-v1/081 — Diary

## Headline

**SPECIALIST-NEGATIVE-IMPROVEMENT-FAIL — CF-kill mechanism falsified; /078 anchor retained.**

The pre-registered F1 falsifier fired mechanically (Δ IS Sharpe = −0.15 vs the +0.20 lift required over the /078 AAVE anchor). The CF-kill-inside-Optuna-fitness mechanism at `confidence_floor=0.20` is **falsified** as a /078 → /081 improvement axis for AAVE specialist. The /078 anchor is **untouched** (parallel-substrate attempt, not a modification). AAVE BUNDLE-002 seat retained at /078 PROMISING-TENTATIVE; 4-component BUNDLE-002 assembly remains viable.

## Decision: NO MERGE

- /081 itself: SPECIALIST-NEGATIVE-IMPROVEMENT-FAIL.
- /078 anchor: PROMISING-TENTATIVE seat status **unchanged**.
- BUNDLE-002 4-component option (DOT/063 + ETH/064 + BTC/065 + AAVE/078): **viable**, gated on user authorization for the TENTATIVE AAVE component.

## Results vs /078 Anchor

| Metric | /078 (anchor) | /081 | Δ vs anchor | Pre-registered floor |
|---|---|---|---|---|
| IS Sharpe | +0.34 | **+0.1865** | **−0.15** | Δ ≥ +0.20 → **F1 FIRED** |
| OOS Sharpe | +0.16 | +0.1193 | −0.04 | — |
| IS trades | — | 135 | — | ≥ 50 cleared |
| OOS trades | — | 71 | — | ≥ 45 cleared (F2 not fired) |
| Max DD IS | — | 21.12% | — | — |
| Max DD OOS | — | 38.07% | — | — |
| Win rate IS | — | 39.3% | — | — |
| Win rate OOS | — | 40.8% | — | — |
| Profit factor IS | — | 1.0658 | — | — |
| Profit factor OOS | — | 1.0368 | — | — |
| Specialist dispersion (mean) | — | **47.23** | — | basin-lottery zone (> 30) |
| DSR_IS / DSR_OOS (EXPLORATION-mode, info only) | — | −78.27 / −56.45 | — | not gate-triggering |
| PSR_monthly_vs_0 IS / OOS | — | 0.615 / 0.549 | — | INFORMATIONAL |
| Net PnL % IS / OOS | — | +70.42% / +20.54% | — | — |

Per-symbol attribution (AAVE-only scope):
- IS: 135 trades / 53 wins (WR 39.3%) / +70.42% / +0.5216% mean.
- OOS: 71 trades / 29 wins (WR 40.8%) / +20.54% / +0.2893% mean.

## Falsifier Outcomes (pre-registered Section 4, frozen at brief SHA)

| Falsifier | Threshold | Observed | Outcome |
|---|---|---|---|
| **F1 (insufficient IS lift)** | Δ IS Sharpe ≥ +0.20 vs /078 anchor | Δ IS = **−0.15** (0.1865 vs 0.34) | **FIRED** |
| F2 (trade-rate floor) | OOS trades ≥ 45 | OOS trades = 71 | NOT FIRED |
| F3 (cross-contamination) | Non-AAVE symbols regress | AAVE-only scope; N/A | N/A |

**F1 fire is dispositive.** Verdict: SPECIALIST-NEGATIVE-IMPROVEMENT-FAIL. The mechanism was honestly pre-committed and falsified by the empirical result — this is a methodologically clean negative, not a post-hoc renegotiation candidate.

## What Worked

- Pre-registration discipline preserved: F1 / F2 / F3 authored before the run; F1 fired mechanically with no retroactive band-shifting.
- Phase 6.0 Critic pre-flight PASS (commit `12a0097`).
- Foundation embargo (walk_forward.py canonical line) intact at Check 1; no look-ahead introduced by the CF-kill change.
- AAVE-only single-bit dispatch discipline preserved.
- Trade-count floors cleared on both sides (135 IS ≥ 50; 71 OOS ≥ 45).
- LM 7.4 forensic attribution depth was excellent — per-trade kill-rate (38.9% IS / 48.9% OOS), saved PnL (+56.67), new-trade PnL (−75.02), new-trade mean confidence (0.43 / median 0.36) all reconstructed cleanly from `trades.csv` differencing. Repro confirmed at Check 7.
- Critic / LM 7.4 mechanism-falsification narrative aligned and adopted.

## What Failed

- **CF-kill-inside-Optuna-fitness reorganizes the loss surface.** Embedding the `confidence_floor=0.20` hard-kill inside the per-(symbol, month) fitness function shifted the hyperparameter optima away from the /078 substrate's local basin. The Optuna search at the modified substrate pulled in **57 new IS trades** (sum −75.02, mean −1.32, WR 26.3%) that did not exist on the /078 substrate. Net IS PnL Δ = −18.35 (saved +56.67 from killed low-conf trades vs introduced −75.02 from substrate-shift new trades). Same shape OOS.
- **CF-kill calibration on /078 was valid in isolation** — low-confidence trades genuinely lose (IS 32.8% WR / −0.55 mean; OOS 29.5% WR / −1.82 mean). The bug was the assumption that adding the kill inside the fitness loop would preserve the substrate. It did not.
- **NEW-trade mean confidence (0.43, median 0.36)** lands in the moderate band [0.30, 0.50] — an anti-calibration zone the /078 substrate never visited but the modified substrate exposes.
- **Specialist dispersion mean = 47.23**, the highest in the v1 SPECIALIST roster (cycle-7 basin-lottery floor 30; /076 AAVE was 32.95). The modified loss surface induced broad-based 50-inner-seed disagreement — the model never found a confident direction at AAVE on the new substrate.
- **OOS Sharpe +0.1193 ≈ IS Sharpe +0.1865**: the substrate-shift is symmetric (same shape IS and OOS); no OOS-divergent illusion to chase.

## Lessons

1. **Substrate coupling matters for risk primitives.** A risk-primitive change embedded *inside* the Optuna fitness loop (CF-IN-FITNESS) is a fundamentally different axis than the same change applied *after* Optuna (CF-AT-INFERENCE). The catalog must distinguish them; conflating would corrupt the LEARNED-NEG ledger. /081 falsifies CF-IN-FITNESS at threshold 0.20 for AAVE specialist — it does NOT falsify CF-AT-INFERENCE, soft attenuation, or lower thresholds, nor the broader confidence-aware-gating axis class.
2. **Calibration validity ≠ deployment improvement.** Even when a kill threshold is correctly calibrated on the anchor substrate's bad trades (which it was at /078), embedding the kill in the search loop can paradoxically reduce IS Sharpe by exposing the model to new anti-calibration zones. The kill-on-anchor analysis is a NECESSARY but NOT SUFFICIENT pre-flight check for substrate-coupled risk primitives.
3. **Instrumentation gap.** The forensic depth in LM 7.4 required reconstructing kill-rates from `trades.csv` differencing. Emitting `kind=cf_kill` decision-log events at the lgbm signal-application site would make per-cell R3-overlap audits cheap for the NEXT confidence-gating axis attempt (any variant).
4. **Single-seed EXPLORATION verdicts on substrate-shifting axes carry hidden multi-seed risk.** /081 cannot be elevated above TENTATIVE under any circumstances per the methodology lock. Dispersion 47.23 is itself basin-lottery evidence; even a hypothetical IS lift at single-seed would still need multi-seed validation before bundle eligibility.
5. **Empirical axis base-rate now informs Path Forward priors.** Feature-family axis class is **4-of-4 PROMISING** at /063/064/065/078. Risk-primitive axis class on AAVE is **0-of-1** after /081 (CF-kill-in-fitness LEARNED-NEG). The Bayesian update strongly favors feature-engineering on the next AAVE attempt over additional risk-primitive variants.

## BUNDLE-002 Status

**4-component option is VIABLE.** /081 did not modify /078; the /078 PROMISING-TENTATIVE seat is intact.

| Seat | Iteration | Status |
|---|---|---|
| DOT | /063 | PROMISING-VALIDATED |
| ETH | /064 | PROMISING-VALIDATED |
| BTC | /065 | PROMISING-VALIDATED |
| AAVE | /078 | PROMISING-TENTATIVE (single-seed under methodology lock) |

Assembly preconditions:
- No-coin-overlap (`feedback_v1_bundle_no_coin_overlap`): satisfied trivially.
- IS-only weight calibration (`feedback_v1_bundle_weight_is_only`): required, would run via `analysis/iteration_v1-NNN/weight_calibration.py` reading only IS data.
- Backtest-live parity (`feedback_v1_backtest_live_parity_hard`): required.
- **User authorization required** for the TENTATIVE AAVE component (per the v1 verdict set, TENTATIVE components shift the BUNDLE's verdict surface and require explicit user sign-off).

## Path Forward (from Critic / LM 7.4, concurrence)

Three options ranked by EV. The Critic concurs with LM 7.4 that the confidence-aware-gating axis class is NOT closed — only the hard-kill-inside-Optuna-fitness variant at threshold 0.20 is falsified for AAVE specialist. Post-Optuna eval-time gating and soft attenuation remain untested but are deferred behind Options A and B.

### Option A — Assemble BUNDLE-002 (HIGHEST EV)
- **Family**: BUNDLE-assembly (meta-axis).
- **Composition**: DOT/063 + ETH/064 + BTC/065 + AAVE/078.
- **What**: bundle-weight calibration (IS-only), no-coin-overlap assertion, backtest-live parity statement; AAVE/078 enters at TENTATIVE.
- **Why HIGHEST**: converts work-in-progress roster into a baseline candidate. Three of four components VALIDATED; AAVE seat is the only TENTATIVE element.
- **Constraint**: **requires explicit user authorization** for the TENTATIVE AAVE component.
- **Risk**: TENTATIVE component shifts BUNDLE-002's verdict surface; user owns the trade-off.

### Option B — Try /082 on AAVE with a feature-engineering axis (NEXT-BEST)
- **Family**: `feature-family` (Category-2 composed feature).
- **Candidate**: `excess_ret_x_funding = excess_ret_5d_vs_majors_z90 × sign(btc_funding_spread_30_90)` (next-ranked per LM 7.4 PIVOT; ranked 3rd in /081 importance).
- **Why**: empirical base rate strongly favors this axis — feature-family is **4-of-4 PROMISING** (/063 /064 /065 /078) vs risk-primitive **0-of-1** after /081.
- **Constraints honored**: `feedback_v1_cycle6_per_symbol_regime_specialist_mandate` permits re-trying AAVE any number of times under the per-symbol regime-specialist mandate; axis-family rotation is suspended.
- **Risk**: lower EV than Option A (does not directly convert the BUNDLE-002 roster), but highest per-iteration lift among non-bundle moves.

### Option C — Pivot to LINK or LTC under fixed-code re-evaluation
- **Family**: `universe` (single-symbol cohort expansion).
- **Why LOWER**: /078 EDA prior weakly favored AAVE over LINK / LTC at the fixed /078 substrate.
- **Use only if**: Options A and B are both blocked (user declines BUNDLE-002 authorization AND feature-engineering axis is explicitly de-prioritized).
- **Disposition**: exploratory rather than improvement-targeted.

## Catalog Entry

```
iter-v1/081 | AAVE | risk-primitive (CF-kill in-fitness, threshold=0.20)
            | SPECIALIST-NEGATIVE-IMPROVEMENT-FAIL
            | IS +0.1865 / OOS +0.1193 vs /078 anchor (IS +0.34 / OOS +0.16)
            | F1 fired (Δ IS = −0.15 < +0.20)
            | dispersion 47.23 (basin-lottery zone)
            | LEARNED-NEG: hard-CF-kill inside Optuna fitness at 0.20
            | Open variants: post-Optuna eval-time CF gate; soft attenuation;
              lower threshold (0.10) on either substrate-coupling mode
```

## Next Iteration Ideas

1. **(USER DECISION REQUIRED)** Authorize BUNDLE-002 assembly with AAVE/078 at TENTATIVE, OR proceed to /082.
2. **(If /082 proceeds)** Feature-engineering axis: `excess_ret_x_funding` Category-2 composed feature on AAVE per LM 7.4 PIVOT. Pre-flight: feature-stack adequacy IC check vs /078 anchor substrate; pre-register F1/F2/F3 with the same +0.20 IS lift threshold.
3. **(Instrumentation tech-debt)** Land `kind=cf_kill` decision-log emission at the lgbm signal-application site before any future confidence-gating axis attempt.
4. **(Catalog hygiene)** Add /081 to `briefs-v1/specialist_catalog.md`. Distinguish CF-IN-FITNESS (falsified) vs CF-AT-INFERENCE (untested) in the LEARNED-NEG ledger so the broader axis class is not prematurely closed.
5. **(Methodology note for future briefs)** When proposing a substrate-coupled risk primitive, brief Section 2 must declare the substrate-coupling mode (IN-FITNESS vs AT-INFERENCE vs HYBRID) and pre-commit a basin-stability proxy (e.g., dispersion-mean falsifier band) so the LEARNED-NEG ledger remains taxonomically clean.
