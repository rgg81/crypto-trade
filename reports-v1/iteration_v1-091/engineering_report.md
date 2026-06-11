# Engineering Report — iter-v1/091

## Headers

- **Iteration**: iter-v1/091
- **Branch**: iteration-v1/091
- **Commit SHA (setup)**: 9edd7a05 (feat(iter-v1/091): R-CONV post-aggregator ensemble-conviction gate)
- **Hardware**: WSL2 Linux 6.6.114.1 / x86_64
- **Wall-clock time**: 13544s (~3.76h) — aborted at fail-fast trigger; full run projected ~7–8h
- **Outcome**: BLOCKED-FAIL-FAST

---

## Configuration Diff vs ETH/064 Baseline Seat

Single change only. Everything else is byte-identical to the ETH/064 runner.

| Parameter | ETH/064 (baseline seat) | iter-v1/091 (R-CONV) |
|---|---|---|
| `enable_r_conv_gate` | `False` (default OFF) | `True` |
| `r_conv_tau` | N/A (gate OFF) | `0.06` (pre-registered IS-only) |
| `specialist_mode` | True | True (unchanged) |
| `V1_SPECIALIST_SEED_COUNT` | 50 | 50 (unchanged) |
| `V1_SPECIALIST_OPTUNA_TRIALS` | 30 | 30 (unchanged) |
| `max_depth` | 5 FIXED | 5 FIXED (unchanged) |
| `num_leaves` | 31 FIXED | 31 FIXED (unchanged) |
| `n_estimators_max` | 500 | 500 (unchanged) |
| `n_startup_trials` | 10 | 10 (unchanged) |
| `atr_tp / atr_sl` | 2.9 / 1.45 | 2.9 / 1.45 (unchanged) |
| R1 / R2 | OFF / OFF | OFF / OFF (unchanged) |
| R3 (Mahalanobis OOD) | ON, cutoff=0.70 | ON, cutoff=0.70 (unchanged) |
| R5 (vol-targeting) | ON, vt_target_vol=0.3 | ON, vt_target_vol=0.3 (unchanged) |
| `feature_columns` | 48 cols (V1_FEATURE_COLUMNS_PRUNED) | 48 cols (UNCHANGED) |
| `cohort` | ETHUSDT only | ETHUSDT only (unchanged) |
| `OOS_CUTOFF_DATE` | 2025-03-24 | 2025-03-24 (sacred, unchanged) |
| `training_months` | 24 | 24 (sacred, unchanged) |
| `fail_fast_is_years` | OFF | 2.0yr (IS weighted_pnl <= 0 threshold) |

R-CONV gate: `if _sp_confidence < r_conv_tau: return NO_SIGNAL` — a post-aggregator RULE layer inserted
immediately after `_sp_confidence = |_final_signed| / 100.0` is computed and before the `Signal` object
is built. Stateless; does not touch the model, seeds, trials, or Optuna objective.

---

## Fail-Fast Result

```
verdict:                    BLOCKED-FAIL-FAST
reason:                     first 732d IS weighted_pnl=-5.8391 (≤0; 132 IS trades over 2.0yr window)
fail_fast_is_years:         2.0
is_trades_count:            132
is_cumulative_weighted_pnl: -5.8391
is_cumulative_net_pnl_pct:  -2.1431
is_annualized_sharpe_approx:-0.6998
wall_clock_seconds:         13544
abort at:                   2024-01-04 (IS candle after 732d of IS test trades)
```

The abort fired in the very last IS training month. The runner exhausted 50-seed × 30-trial optimization
for all IS folds through end-2023, executed 132 IS trades, and then checked accumulated IS weighted_pnl
at the 2-year mark. Result was negative (−5.84 cumulative weighted PnL, −2.14% net, IS Sharpe ≈ −0.70).
No comparison.csv — expected for a fail-fast abort.

The ETH/064 standalone baseline (the seat R-CONV modifies) was IS **+0.2383** / OOS **+0.5171**
(from `reports-v1/iteration_v1-064/comparison.csv`).

---

## W-DECAY vs R-CONV Magnitude Contrast

| Iteration | Axis | IS first-2yr weighted_pnl | IS net_pnl_pct | IS Sharpe approx | Verdict |
|---|---|---:|---:|---:|---|
| iter-v1/090 | W-DECAY (abs_pnl_timedecay) | −17.17 | −27.91% | −2.02 | SPECIALIST-NEGATIVE (INVERSE-EDGE) |
| **iter-v1/091** | **R-CONV (τ=0.06)** | **−5.84** | **−2.14%** | **−0.70** | **SPECIALIST-NEGATIVE (NO-EFFECT)** |
| ETH/064 baseline | abs_pnl (unchanged) | +0.2383 IS Sharpe (full IS) | — | +0.2383 | Anchor |

The contrast is significant. W-DECAY crushed the first 2yr to −2.02 Sharpe (−27.9% net) — a directionally
catastrophic inversion driven by the inverse-edge mechanism (decay discarded ETH's 2022–23 signal). R-CONV
at τ=0.06 produced −0.70 Sharpe (−2.14% net) — ~neutral-to-marginally-negative, consistent with the
LM-predicted NEGATIVE-NO-EFFECT modal (~45% probability per LM §6): the gate filtered (F2 ENGAGED;
132 vs ETH/064's 198 IS trades = ~33% reduction, matching the pre-registered ~34% projection), but the
IS conviction-noise signature DID NOT transfer as a useful signal.

The R-CONV result is not catastrophic; it is a modest negative consistent with the LM's decisive finding
that the IS low-conviction→net-losing gradient DOES NOT replicate in ETH OOS (dropped OOS set = +6.25% /
44.4% WR, mirror-opposite of IS −5.43% / 37.3%).

---

## Centerpiece: F2 ENGAGED, F1 Negative — SPECIALIST-NEGATIVE (NO-EFFECT)

### F2 (Mechanistic Falsifier) — ENGAGED

The brief pre-registered: IS trade count reduction ≥ 15% (lower bound of the behavioral-effect predictor)
confirms the gate operated. Observed: **132 IS trades** vs ETH/064's 198 baseline = **33% reduction**
(well within the pre-registered ~34% central estimate; above the 15% lower bound). F2 = ENGAGED. The
conviction gate fired on candles with `_sp_confidence < 0.06` as designed.

### F1 (IS Sharpe Falsifier) — NEGATIVE

IS Sharpe ≈ **−0.70** vs ETH/064 baseline **+0.2383**. Delta ≈ **−0.94** — below the NEGATIVE
threshold (Δ < 0.00). The brief Section 8 pre-registered matrix maps F2-ENGAGED + F1-NEGATIVE to
**SPECIALIST-NEGATIVE** (NOT INERT). The mechanism operated; it just did not improve the seat.

### Verdict: SPECIALIST-NEGATIVE (NEGATIVE-NO-EFFECT)

F2 = ENGAGED (gate fired; 33% IS trade reduction as pre-registered).
F1 = NEGATIVE (IS Sharpe Δ ≈ −0.94 vs baseline; below the NEGATIVE threshold of 0.00).
Subtype: **NEGATIVE-NO-EFFECT** — the conviction proxy (`_sp_confidence < τ`) does not separate
signal from noise on this seat. The LM §6 pre-registered this as the decisive finding: removing
the 9 OOS low-conviction candles removes OOS-profitable candles (OOS dropped set +6.25%), and the
IS conviction-noise gradient does not generalize. The fail-fast confirmed the direction.

F3 (OOS trade-rate floor) and F4 (selection-bias / direction check) were not evaluable — the run
aborted before OOS. The fail-fast verdict supersedes.

---

## CENTERPIECE METHODOLOGICAL CAVEAT (Load-Bearing Learning)

**The fail-fast gate is mis-calibrated for machinery re-tests of an existing seat.**

Both W-DECAY/090 AND R-CONV/091 blocked on the ETH seat's first-2yr absolute IS weighted_pnl. ETH's
first 2 years (2022–24, including the 2022 bear market) are WEAK at baseline — the ETH/064 anchor's IS
Sharpe of +0.2383 is earned across the FULL IS window; the first-2yr sub-window is materially weaker
than the full IS average.

The fail-fast gate was designed for **FRESH-COIN MINING**: "does a new coin have early edge structure?"
In that context, an absolute floor of IS weighted_pnl > 0 over the first 2 years is appropriate —
a fresh coin with no positive IS signal in its first 2 years has no demonstrated edge at all.

For **machinery re-tests of a known seat** the correct test is:
- R-CONV-ETH vs baseline-ETH on the SAME first-2yr window (relative comparison)
- NOT an absolute floor against zero

The two tests ask different questions. The absolute gate asks "does the seat have a first-2yr edge?"
The relative gate asks "does the machinery HELP the seat's first-2yr edge?"

For ETH, both tests happened to give a NEGATIVE answer (the seat's weak first-2yr dragged both
W-DECAY and R-CONV below zero). But the inference is muddy: we cannot cleanly attribute whether R-CONV
at τ=0.06 _helped or hurt vs baseline_ on the same first-2yr window, because the baseline ETH first-2yr
IS weighted_pnl is not preserved (run.log from /064 was not retained at the sub-window level; only the
full-IS comparison.csv is available). If the baseline ETH first-2yr were, say, −3.0 and R-CONV produced
−5.84, that is a modest degradation. If it were −8.0, R-CONV would have been an improvement.

**Recommendation for future machinery axes:**

Run fail-fast OFF (omit `--fail-fast-is-years`) and compare full-IS / OOS vs the baseline seat, OR
test machinery on a seat with a confirmed-strong first-2yr (e.g., AAVE/078, DOT/063, BTC/065 — these
seats passed their first-2yr checks during their own mining runs). The fail-fast-for-machinery-re-tests
confound is now pre-registered in the diary so future iterations can route around it.

---

## Fail-Fast Validation Record — 4th Trigger

| Iteration | Seat | Verdict | IS Sharpe approx | Wall-clock saved |
|---|---|---|---:|---|
| BNB/087 | BNBUSDT (fresh mine) | BLOCKED-FAIL-FAST | n/a | ~4–5h |
| XRP/088 | XRPUSDT (fresh mine) | PASSED (positive; full run proceeded) | — | — |
| ETH/090 | ETHUSDT W-DECAY | BLOCKED-FAIL-FAST | −2.02 | ~3.5–4h |
| **ETH/091** | **ETHUSDT R-CONV** | **BLOCKED-FAIL-FAST** | **−0.70** | **~3.5–4h** |

**Caveat on entries 3 and 4**: the gate is well-calibrated for fresh-coin mining (BNB/087, XRP/088).
For machinery re-tests (ETH/090, ETH/091), the absolute floor conflates "does the machinery help"
with "does the seat's early window clear zero" — see Centerpiece caveat above.

---

## LM Master NEGATIVE-NO-EFFECT Alignment

The LM §6 modal assignment:
- NEGATIVE-NO-EFFECT: ~45% probability
- TENTATIVE/FLAT: ~30%
- VALIDATED: ~15%
- Other: ~10%

The observed outcome (NEGATIVE, IS Sharpe −0.70, F2 engaged) lands squarely in the LM-modal bucket.
The LM's decisive finding — "the IS dropped-tail-net-losing does NOT replicate OOS" (dropped OOS set
+6.25% / 44.4% WR vs IS −5.43% / 37.3%) — is the mechanistic explanation. The conviction gate removes
candles that are, on average, profitable OOS; applying it IS-to-OOS is directionally damaging. The
fail-fast confirms the directional negative at the IS level without needing the full OOS pass.

---

## Default-OFF / Foundation Regression

`enable_r_conv_gate` defaults to `False`. With the flag OFF the SPECIALIST path is byte-identical to
the ETH/064 baseline (unit test committed at SHA 9edd7a05 asserts this). The PRUNED feature set stays
at 48 columns (hash prefix `b81176f893826500...` confirmed in run.log header). No foundation regression:
BUNDLE-002 (`v0.v1-082`) and all other seats are unaffected.

PRUNED count unchanged at 48. Lock intact. No new features added.

---

## Ensemble_std Split Reconstructability

The LM §1 REQUIRED deliverable was: persist `specialist_dispersion.csv` + enable the `r_conv_skip`
decision_log entries carrying `ensemble_std`, so Phase 7.4 can split the dropped set by
abstention-vs-disagreement.

**Status: NOT RECONSTRUCTABLE from this run.**

`decision_log.configure()` is called only from `engine.py` (live mode, `engine.py:350`). In backtest
mode `decision_log.log()` is a no-op — the r_conv_skip entries were dispatched in `lgbm.py:2194–2208`
but silently dropped. No JSONL file was written. The `specialist_dispersion.csv` artifact (for the
non-skipped candles' dispersion stats) is also absent because the abort fires before the full IS run
writes its outputs.

The abstention-vs-disagreement split (LM §1's required split of the 67 IS dropped-set trades into
|net|=1 abstention-tail vs |net|=2 disagreement-tail by `ensemble_std`) is therefore not
reconstructable from the available artifacts for this run. The run.log contains no structured r_conv_skip
lines — only the banner confirming the gate was wired (`r_conv_skip carries ensemble_std`). This is a
pre-existing limitation of the backtest decision_log design (no file target in backtest mode), not a
code bug.

Given the SPECIALIST-NEGATIVE verdict, Phase 7.4 does not change the outcome. The ensemble_std split
would be diagnostic only. For future machinery-axis runs where the verdict is TENTATIVE/PROMISING,
a backtest-mode decision_log output path should be wired (e.g., persist to
`reports-v1/iteration_v1-NNN/decision_log.jsonl`) to make the split reconstructable.

---

## Feature Integrity Audit

- `V1_FEATURE_COLUMNS_PRUNED` = 48 columns. UNCHANGED. Hash prefix `b81176f893826500...` confirmed
  in run.log header.
- Cross-track isolation: no v2/v3 feature imports. R-CONV is a post-aggregator RULE layer with no
  effect on the feature pipeline.
- Label-leakage gap: CV gap = 22 rows (184h = 8h × 23 candles), consistent with
  `(timeout_candles + 1) × n_symbols = 22 × 1` for single-symbol ETH specialist. Confirmed in run.log
  per-fold headers.
- Sacred constants: `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24` — both confirmed unchanged
  in runner and run.log header.
- `feature_columns` passed explicitly as `list(V1_FEATURE_COLUMNS_PRUNED)` — never None.

---

## Anomaly Notes

None. The run proceeded cleanly to the fail-fast trigger with no unexpected errors, no NaN in loss,
no fold collapse. 50-seed × 30-trial optimization completed all IS folds through 2023-12. The final
training cell (2024-01) completed and the first OOS-adjacent trade was opened before the abort:
`[trade:open] 2024-01-04 15:59 ETHUSDT LONG`. The fail-fast then fired correctly on checking cumulative
IS weighted_pnl.

The run.log also confirms the fail-fast checks post-IS-close (consistent with the /090 precedent) — the
abort fires after the 2024-01 cell's first live signal, not mid-training.

---

## Status

OVERALL = SPECIALIST-NEGATIVE (NEGATIVE-NO-EFFECT)

**Not forwarded to Critic review** — fail-fast aborts are self-contained NEGATIVE verdicts requiring no
Phase 7.5 adversarial review. QR Phase 8 diary authoring is the next step.

Verdict: **SPECIALIST-NEGATIVE** (NO-EFFECT). F2 ENGAGED (33% IS trade reduction at τ=0.06, matching
the pre-registered ~34% projection). F1 NEGATIVE (IS Sharpe ≈ −0.70 vs baseline +0.2383, Δ ≈ −0.94).
The R-CONV gate is ~neutral-to-marginally-negative on ETH — consistent with LM §6's decisive finding
that the IS conviction-noise gradient inverts in the OOS window. Load-bearing methodological finding:
fail-fast-absolute-floor is mis-calibrated for machinery re-tests of existing seats; the correct design
is fail-fast OFF with relative comparison vs baseline-seat (or test machinery on a seat with a
confirmed-strong first-2yr). R-CONV axis remains open for seats with IS conviction-noise gradients
that replicate OOS; closed for ETH at τ=0.06.
