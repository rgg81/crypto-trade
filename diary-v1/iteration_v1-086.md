# iter-v1/086 — Phase 8 Diary (TRBUSDT SPECIALIST)

**Date**: 2026-06-10
**Track**: v1 (refactored)
**Branch**: `iteration-v1/086`
**TYPE**: SPECIALIST — single-coin cohort `("TRBUSDT",)`; bundle-diversification mine (lowest-correlation eligible seat vs BUNDLE-002); STOCK 48-col stack, NO new features; FIRST fresh candidate to CLEAR the GATE-2 probe since the /085 hard-reject reform.
**Cycle**: 7, fresh-alt mining (bundle-diversification axis)
**Author**: QR (autopilot)
**Tag**: `v0.v1-086`

---

## Headline

**SPECIALIST-NEGATIVE — subtype NEGATIVE-PROBE-INCONSISTENT. IS Sharpe −0.3044 / OOS −0.5967. The +0.49 GATE-2 probe did NOT reproduce at full budget — and the Critic found WHY: the probe→full gap is THREE confounds, not one.**

TRB was the first fresh candidate to clear GATE-2 (probe +0.4930 ≥ +0.30) since the reform, picked as the lowest-bundle-correlation eligible seat (0.548 vs DOT/ETH/BTC/AAVE). The full 50-inner-seed / n_trials=30 specialist came in at IS −0.3044 — a Δ−0.80 collapse from the probe. This is the **second** consecutive probe→full degradation (UNI/085 was Δ−0.46), exposing that the **n_trials=10 GATE-2 probe systematically OVERSTATES the full specialist**. The Critic's load-bearing correction: the degradation is NOT n_trials alone — the probe also ran `ood_enabled=False` + `bounds_profile="v1_pruned"` while the full runs OOD ON + `v1_specialist` bounds. THREE confounds.

This is the IDEAL adversarial outcome: the hypothesis was tested cleanly (no leak, faithful implementation, global PRUNED stayed 48, zero new features, Critic Checks 1/7/8/13/14 all PASS) and DECISIVELY FALSIFIED — and it produced a high-value methodology finding that fixes the screening gate.

---

## Results

| Metric | IS | OOS |
|---|---:|---:|
| Sharpe (monthly) | **−0.3044** | −0.5967 |
| Trades | 157 | 90 |
| Win rate | 35.7% | 35.6% |
| Profit factor | 0.90 | 0.86 |
| Max drawdown | 72.95% | 34.47% |
| OOS/IS ratio | — | 1.96 (both negative) |

GATE-2 probe (n_trials=10, seed=42): IS **+0.4930**. Full (n_trials=30, 50 inner seeds): **−0.3044**. **Δ−0.80.**

---

## Falsifier outcomes

- **F2 FALSIFIED → NEGATIVE-PROBE-INCONSISTENT.** Realized 50-seed IS Sharpe −0.30 collapsed below +0.00; the +0.49 single-seed n_trials=10 probe did not survive the full budget.
- **F4 FALSIFIED → NEGATIVE-MOMENTUM-DOMINATED.** IS −0.30 < 0 (and below trivial −0.179).
- **F3 NEGATIVE** (IS < +0.20).
- **F5 (diversification-conditionality) MOOT** — negative standalone, no bundle seat. (For the record, F5a DIVERSIFIER-DEGENERATE *would* have fired: 5 of top-10 features are shared bundle anchors — vol_atr_14 r1, btc_funding_spread r2, funding_zscore r7/8, oi_delta r10 — with TRB's MACD tier only at rank 5. TRB re-learned the shared basis.)

---

## Key findings

1. **The probe→full collapse is THREE confounds, not n_trials alone (Critic correction).** The LM 7.4 + QE attributed it to n_trials 10→30; the Critic traced the code and found the probe also ran `ood_enabled=False` + `bounds_profile="v1_pruned"` vs the full's OOD-ON + `v1_specialist`. So the corrected GATE-2 probe must be the **exact full-specialist config at single-inner-seed** (n_trials=30 + OOD ON + v1_specialist bounds), not merely n_trials=30.

2. **The overfit mechanism (LM 7.4): training_days collapsed SHORT.** At n_trials=30 the deeper search found short training windows (median 95d, 26/46 folds <120d) that maximize the in-fold Optuna objective (mean +0.179, 46/46 folds positive) but don't generalize one month forward (realized −0.30) — a ~0.48 in-fold/walk-forward optimism gap. The LM's own Phase 4.5 `training_days<120d` red flag FIRED.

3. **`cross_seed_sharpe_std=0.000` is DEGENERATE** (single OUTER seed via `--seeds 1`), NOT robustness. The 50-INNER-seed ensemble DID execute (specialist_mode hardwires it). This also tempers the same "robust negative" claim in the /085 diary — basin-lottery dispersion is unmeasured at single-outer-seed.

4. **R5 cold-start fired again.** TRB's 2022-09 listing month = −38.43% (15.7% of |IS PnL|); dropping it flips cumulative IS PnL −25.24% → +13.19% (but NOT Sharpe — the negativity is the all-folds short-window overfit, not one month). R5 fire rate 0.000 IS. Confirms R5 needs a listing-window guard.

---

## Decision: SPECIALIST-NEGATIVE — NO MERGE

**Verdict** (Phase 7.5 Critic review, commit `a22d571b`): `SPECIALIST-NEGATIVE`, subtype `NEGATIVE-PROBE-INCONSISTENT`. Methodology INTACT (not a code/config defect).

- TRB DROPPED from the bundle candidate roster.
- **BUNDLE-002 (`v0.v1-082`; DOT+ETH+BTC+AAVE; IS +0.72 / OOS +1.00) UNCHANGED.** No BUNDLE-003.
- Campaign now **0/6 fresh-alt mines** (ATOM/075, ICP/077, FIL/083, CRV/084, UNI/085, TRB/086).

---

## Methodological reform: GATE-2 PRIMARY must be CONFIG-MATCHED

The /085 GATE-2 reject-side is 2/2 (CRV, UNI correctly rejected). The PASS-side is now INVALIDATED: TRB is the only pass-side test and it false-passed by Δ−0.80. The corrected gate (Critic + LM 7.4):
- **GATE-2 PRIMARY = the full-specialist config probe at single-inner-seed=42** (n_trials=30 + `ood_enabled=True` + `bounds_profile="v1_specialist"`), threshold stays ≥ +0.30. Closes ALL THREE confounds. Cost ~single-digit minutes (~1% of the 6h full run).
- Keep the n_trials=10 probe as an advisory seconds-long pre-pre-screen ONLY (never a PASS gate).
- **GATE-2 SECONDARY (new): in-fold/walk-forward optimism gap** — mean per-fold best in-fold objective − realized walk-forward IS > ~0.3 → flag noise-dominated surface (would have caught UNI + TRB).
- **training_days ≥ 120d floor** for single-symbol stock-stack mines.
Codified to `feedback_v1_negative_trivial_baseline_selector` memory.

---

## Next Iteration Ideas (Critic Path Forward + standing directives)

The bottleneck is the screening gate + the noisy single-symbol surface, NOT the symbol. Per "alternate machinery with coins" + the BNB/XRP universe directive:

1. **GATE-INV probe-calibration diagnostic** (cheap, do FIRST) — batch-run the config-matched n_trials=30 probe AND the n_trials=10 probe across the failed roster (FIL/CRV/UNI/TRB) to convert the 2-point probe→full bias (Δ−0.46, Δ−0.80) into a calibrated curve and verify the config-matched probe eliminates the gap. De-risks the whole queue in <1h.
2. **R5 listing-window-guard primitive (R5-LWG)** — risk-primitive family; skip-or-0.5×-weight first 45 candles post-listing; testable on the existing failed roster (isolates cold-start drag vs no-edge).
3. **W-DECAY time-decay sample weighting** — removes the short-window noise-exploitation channel at the labeling layer (keeps the full 24-month window).
4. **BNB + XRP universe-expansion mines** (user-directed) — MUST gate on the AMENDED config-matched probe, NOT the retired n_trials=10 probe. XRP carries the cross-track double-exposure flag.

---

## Catalog

iter-v1/086 → `per-cohort-specialization-TRB` | SPECIALIST-NEGATIVE | NEGATIVE-PROBE-INCONSISTENT | IS −0.3044 / OOS −0.5967 | GATE-2 pass-side INVALIDATED (probe +0.49 → full −0.30, Δ−0.80, 3 confounds); GATE-2 now config-matched | campaign 0/6 fresh mines | non-roster.
