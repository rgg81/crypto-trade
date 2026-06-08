# iter-v1/081 — OOS Evaluation Memo

## TL;DR

**SPECIALIST-NEGATIVE-IMPROVEMENT-FAIL.** The pre-registered F1 falsifier fired
mechanically (Δ IS Sharpe = −0.15 vs the +0.20 required improvement over the
/078 AAVE anchor). The CF-kill-inside-Optuna-fitness mechanism is **falsified**
as a /078 → /081 improvement axis. The /078 anchor (IS +0.34 / OOS +0.16) is
untouched — /081 is a parallel attempt on a separate substrate, not a
modification of /078. The AAVE BUNDLE-002 seat is retained at /078
**PROMISING-TENTATIVE**.

## 1. Anchor Reference (/078)

The /078 anchor stands as the AAVE specialist baseline candidate:

| Metric | /078 (anchor) | /081 (this iteration) | Δ vs anchor |
|---|---|---|---|
| IS Sharpe | +0.34 | +0.1865 | **−0.15** (F1 fires; required ≥ +0.20) |
| OOS Sharpe | +0.16 | +0.1193 | −0.04 |
| OOS trades | — | 71 | F2 not fired (≥ 45 required) |
| IS trades | — | 135 | ≥ 50 floor cleared |

The anchor seat is **not modified** by /081 — /081 ran on a freshly-seeded
Optuna substrate with the CF-kill (`confidence_floor=0.20`) embedded inside
the per-(symbol, month) fitness loop. The /078 substrate's hyperparameter
optima were not replicated; the modified loss surface relocated them.

## 2. Falsifier Outcomes (Pre-Registered Section 4)

| Falsifier | Threshold | Observed | Outcome |
|---|---|---|---|
| **F1 (insufficient IS lift)** | Δ IS Sharpe ≥ +0.20 vs /078 anchor | Δ IS = **−0.15** | **FIRED** |
| F2 (trade-rate floor) | OOS trades ≥ 45 | OOS trades = 71 | NOT FIRED |
| F3 (cross-contamination) | Non-AAVE symbols regress | AAVE-only scope; N/A | N/A |

**F1 fire is dispositive.** Verdict at Phase 7.5 from Critic:
**SPECIALIST-NEGATIVE-IMPROVEMENT-FAIL**. The mechanism (CF-kill inside Optuna
fitness) did not produce the pre-committed IS lift, and the falsifier was
honestly authored — this is a methodologically clean negative, not a
re-litigation candidate.

## 3. Raw /081 Headline Metrics (from `reports-v1/iteration_v1-081/comparison.csv`)

| Metric | IS | OOS | IS/OOS Ratio |
|---|---|---|---|
| Sharpe | 0.1865 | 0.1193 | 0.6397 |
| Sortino | 0.1641 | 0.1347 | 0.8205 |
| Max Drawdown | 21.12% | 38.07% | 1.8024 |
| Win Rate | 39.3% | 40.8% | 1.0404 |
| Profit Factor | 1.0658 | 1.0368 | 0.9728 |
| Total Trades | 135 | 71 | 0.5259 |
| Calmar Ratio | 0.5550 | 0.0856 | 0.1543 |
| DSR (EXPLORATION-mode, info only) | −78.27 | −56.45 | 0.72 |
| PSR_monthly_vs_0 | 0.6153 | 0.5491 | 0.8925 |
| Net PnL % | +70.42% | +20.54% | 0.29 |
| Specialist dispersion (mean) | 47.23 | — | **basin-lottery zone** |

Per-symbol attribution (AAVE-only scope; both IS and OOS):
- IS: 135 trades / 53 wins (WR 39.3%) / +70.42% net PnL / +0.5216% mean.
- OOS: 71 trades / 29 wins (WR 40.8%) / +20.54% net PnL / +0.2893% mean.

Trade-count floor (≥ 50 IS, ≥ 45 OOS) cleared comfortably.

## 4. Basin-Lottery Diagnostics

From `reports-v1/iteration_v1-081/basin_diagnostics/basin_diagnostics.json`:

- v1 cross-seed Sharpe std = 0.0 (degenerate at single-seed mode) → PASS
- v2 per-cell Spearman ρ = NaN → BORDERLINE (single-cell pathology)
- v3 OOS trade-roster Jaccard = NaN → SKIPPED
- Global verdict: **BORDERLINE**

`specialist_dispersion_mean` = **47.23** (highest in the v1 SPECIALIST roster;
the cycle-7 basin-lottery floor is 30). This corroborates the inherited
LM 7.4 finding that the CF-kill-modified loss surface induces broad-based
disagreement across the 50 inner seeds — the model never found a confident
direction at AAVE.

Per the methodology lock, single-seed=42 EXPLORATION mode means a
multi-seed Pareto front is not available; the verdict remains TENTATIVE at
best regardless of outcome.

## 5. Mechanism Falsification — CF-Kill-in-Optuna-Loss

The Critic's Phase 7.5 review adopts the LM 7.4 forensic attribution as the
canonical narrative:

- **CF-kill calibration on /078 was VALID.** Low-confidence trades in the /078
  substrate were genuinely worse (IS 32.8% WR / −0.55 mean PnL; OOS 29.5% WR
  / −1.82 mean PnL).
- **The failure mode is substrate REORGANIZATION.** Embedding the CF-kill
  inside the per-cell Optuna fitness function changes the loss surface,
  shifts the hyperparameter optima, and pulls in **57 new IS trades**
  (sum −75.02 PnL, mean −1.32, WR 26.3%) that did not exist on the /078
  substrate.
- Net IS PnL Δ = −18.35 (saved +56.67 vs introduced −75.02). The same shape
  appears OOS.
- The NEW-trade mean confidence (0.43, median 0.36) lands in the moderate
  band [0.30, 0.50] — an **anti-calibration zone** that the /078 substrate
  did not visit but the CF-kill-modified substrate exposes.

### What is falsified
- Hard CF-kill **inside Optuna fitness** at threshold 0.20 for AAVE
  specialist (this exact mechanism, on this substrate, at this threshold).

### What is NOT falsified
- Post-Optuna **eval-time** CF gate (decouples substrate from gate).
- Soft probability attenuation (does not push trades to zero, only scales).
- Lower threshold (e.g., 0.10) variants on either substrate-coupling mode.
- The broader **confidence-aware gating axis class**.

Critic and LM 7.4 concur: the broader axis class is NOT closed; only the
in-loss-loop hard-kill variant is dead.

## 6. BUNDLE-002 Seat Status

/078 remains the AAVE BUNDLE-002 candidate at **PROMISING-TENTATIVE**
(IS +0.34 / OOS +0.16). /081 did NOT degrade /078 — they ran on independent
substrates. The seat is untouched.

BUNDLE-002 4-component candidate roster:

| Seat | Iteration | Status |
|---|---|---|
| DOT | /063 | PROMISING-VALIDATED |
| ETH | /064 | PROMISING-VALIDATED |
| BTC | /065 | PROMISING-VALIDATED |
| AAVE | /078 | **PROMISING-TENTATIVE** (single-seed under methodology lock) |

The 4-component option is **viable** for bundle assembly under user
authorization for the TENTATIVE component.

## 7. Path Forward (ranked by EV / risk)

Critic Phase 7.5 and LM 7.4 are aligned on this ordering.

### Option A — Assemble BUNDLE-002 (HIGHEST EV)
Family: BUNDLE-assembly (meta-axis, not feature/risk/universe).

- Composition: DOT/063 + ETH/064 + BTC/065 + AAVE/078.
- AAVE/078 enters at TENTATIVE; bundle weight calibration IS-only per
  `feedback_v1_bundle_weight_is_only`; no-coin-overlap per
  `feedback_v1_bundle_no_coin_overlap` satisfied trivially (single seat per
  coin).
- **Requires explicit user authorization** for the TENTATIVE AAVE component.
- Converts work-in-progress roster into a baseline candidate. Highest EV
  path because three of four components are VALIDATED and the AAVE seat is
  the only TENTATIVE element.

### Option B — Try /082 on AAVE with a feature-engineering axis
Family: `feature-family` (next-ranked candidate per LM 7.4 PIVOT
recommendation).

- Candidate feature: `excess_ret_x_funding =
  excess_ret_5d_vs_majors_z90 × sign(btc_funding_spread_30_90)`
  (Category-2 composed; ranked 3rd in /081 feature importance).
- Empirical base-rate prior: feature-family axis class is **4-of-4
  PROMISING** at /063/064/065/078; risk-primitive axis class is now
  **0-of-1** with /081 falsifying CF-kill-in-fitness.
- Under `feedback_v1_cycle6_per_symbol_regime_specialist_mandate`, AAVE may
  be re-tried any number of times. Axis-family rotation is suspended; the
  feature-family base rate strongly favors this axis.
- Lower EV than Option A (does not directly convert the roster), but
  highest expected per-iteration lift among non-bundle moves.

### Option C — Pivot to LINK or LTC under fixed-code re-evaluation
Family: `universe` (single-symbol cohort expansion).

- Lower EV per the /078 EDA prior; LINK / LTC show weaker per-symbol signal
  in the fixed /078 substrate.
- Use only if Options A and B are both blocked (user declines BUNDLE-002
  authorization AND the feature-engineering axis is explicitly de-prioritized).
- Treat as exploratory rather than improvement-targeted.

### Critic / LM 7.4 concurrence note

The confidence-aware-gating axis class is **NOT closed**. Only the
hard-kill-inside-Optuna-fitness variant is falsified. Post-Optuna eval-time
gating and soft attenuation remain **untested**, but are deferred behind
Options A and B given the EV ordering and the BUNDLE-002 4-component roster
proximity.

## 8. Recommendations to Future QR

1. **Instrumentation gap.** Emit `kind=cf_kill` decision-log events at the
   lgbm signal-application site so the NEXT confidence-gating axis attempt
   (any variant) can be audited per-cell empirically with R3 overlap. LM 7.4's
   forensic depth on /081 required reconstructing kill-rate from
   `trades.csv` differencing — instrumentation would make this cheap.
2. **Axis-class taxonomy hygiene.** Distinguish CF-IN-FITNESS (falsified)
   from CF-AT-INFERENCE (untested) in catalog rows. Future briefs proposing
   confidence-aware gating must declare which substrate-coupling mode they
   sit in; conflating the two would corrupt the LEARNED-NEG ledger.
3. **Pre-registration discipline preserved.** F1 / F2 / F3 were honestly
   pre-committed and F1 fired cleanly. Log this iteration as a clean
   methodological negative in the SPECIALIST roster. Do not re-litigate the
   threshold post-hoc.

## 9. Catalog Entry (for `briefs-v1/specialist_catalog.md`)

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
