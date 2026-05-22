# iter-v3/106 — Cycle-5 EXPLORATION slot #6 — RISK-MANAGEMENT OVERLAY (USER-DIRECTED): IS loss-month / "unseen-regime" detection — FILED NULL-AT-EDA — the deep IS-only EDA tested the user's hypothesis and conclusively FALSIFIED it; the IS loss months are a low-win-rate, regime-agnostic, MEAN-REVERTING drag, NOT a detectable or stoppable condition; no backtest was run

**Date**: 2026-05-19
**Type**: EXPLORATION (cycle-5 slot #6) — Phases 1-5 concluded at a NULL-AT-EDA verdict
**Verdict**: **NULL-AT-EDA** — iter-v3/106 was a **USER-DIRECTED** axis with a specific, falsifiable hypothesis: *the IS calendar months in which the v3 book loses money are months the model has not seen before (a novel / out-of-distribution regime), and a detector that recognizes that condition and stops trading would lift the Sharpe.* The QR ran a deep, multi-angle, strictly IS-only EDA — 4 committed scripts under `analysis/iteration_v3-106/` (commit `7b55698`), 9 result tables T1–T9 — that operationalized the hypothesis and **conclusively falsified it on three independent axes**. No causal regime separator reaches a usable bar; the Mahalanobis OOD distance the hypothesis literally points at does not separate the loss months; and a trailing-equity drawdown brake — the cleanest "stop when losing" mechanism — ACTIVELY HURTS the IS Sharpe at every trigger because the book's drawdowns mean-revert. No Phase-6 backtest was run.
**Classification**: **NULL-AT-EDA** — reserved for an axis the deep, committed, IS-only EDA conclusively proves dead before any backtest (the dispatch's high bar). Killing it at the EDA — rather than committing a `RiskV2` Mahalanobis-gate `src/` module and a 3-seed backtest to reproduce a documented failure mode (the gate removes *profitable* trades; the drawdown brake is IS-negative) — is the fail-fast WIN (`feedback_fail_fast.md`), not an iteration failure. Matches the /098/100/103/104 NULL-AT-EDA precedent. **For a user-directed hypothesis, the honest falsification is the rigor arm working as designed** (Section 6).
**Decision**: **NO-MERGE.** BASELINE_V3.md UNCHANGED — canonical **`v0.v3-059`** (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**, 10-seed CONFIRMATION).
**Branch**: `iteration-v3/106`

---

## 1. The axis — and why it was directed

iter-v3/106 is cycle-5 EXPLORATION slot #6. Unlike the QR-selected axes of /101–/105, **this axis was directed by the user** (2026-05-19, verbatim in Section 2). The /105 closeout had just falsified the /104 "the label geometry is the binding constraint" hypothesis and localized the constraint **downstream of the training label, in the trade-construction / exit / risk layer**; the /105 diary Section 9 pre-registered iter-v3/106 as the user-directed risk-management axis and noted the /105 finding directly supports working the execution-and-risk layer.

The user's directive was specific: focus the QR on **risk management** — analyze the IS months where the model underperforms, on the premise that those are months the model "hasn't seen before" and "needs to stop," and use that to lift the Sharpe. This is a **risk-management overlay** axis: it touches neither features, the label, the model, nor the training objective; it works only the execution-and-risk layer — exactly where /105 localized the binding constraint.

Per `feedback_v3_axis_selection_quant_discipline.md` the axis was still QR-led: the QR's job on a directed axis is to *operationalize the hypothesis into a falsifiable claim and test it with a committed IS-only EDA before any brief or build.* That is what happened. The committed EDA (4 scripts, commit `7b55698`) preceded the brief (`81fd62b`). And the EDA's verdict is the finding of this iteration.

## 2. The user's hypothesis — operationalized into a falsifiable claim

**The user-directed hypothesis (verbatim, 2026-05-19):** *"make the QR focus more on risk management, analyse in IS the months where model didn't perform. Those months most likely the model hasn't seen before it needs to stop. Focus on that part to improve sharp. It's not linked directly to machine learning eda, but for sure we can improve during the months when we lost more."*

The QR operationalized this into a single falsifiable claim, so the EDA could decisively pass or kill it:

> **The IS calendar months in which the /059 book lost money share a common, IS-detectable, CAUSAL signature — specifically that the market state in those months is novel relative to the model's training distribution (out-of-distribution) — and a risk gate that detects that condition at bar `t` (using only data ≤ `t`) and stops or reduces trading would remove the loss months while preserving the profitable months, lifting the IS Sharpe.**

The claim has three testable parts, and the EDA was built to interrogate each:
1. **Do the loss months share a signature at all?** (T1 — characterize them.)
2. **Is that signature an "unseen-regime" / OOD condition, and is it CAUSAL — detectable at the start of the month / the entry of the trade using only past data?** (T2/T3/T4/T7/T8 — measure every plausible causal regime separator.)
3. **Would "stopping when losing" actually lift the Sharpe?** (T9 — the drawdown-brake counterfactual.)

The EDA falsified all three. The honest verdict is NULL-AT-EDA.

## 3. The deep IS-only EDA — 4 committed scripts, 9 tables, the falsification

Four committed IS-only scripts under `analysis/iteration_v3-106/` (commit `7b55698`): `loss_month_diagnostic.py`, `loss_month_separators.py`, `loss_month_deep.py`, `regime_final_check.py` — 9 result CSVs (T1, T1b, T2–T9). Every script asserts the IS-only invariant at load: every trade entering any computation has `open_time < OOS_CUTOFF_MS = 1742774400000`; every feature row entering any reference/test window has `close_time < OOS_CUTOFF_MS`. The post-cutoff OOS roster and post-cutoff feature data were **never read** — the QR did not inspect OOS in Phases 1-5 (and, on the NULL-AT-EDA verdict, Phase 7 does not occur).

The roster under analysis is the canonical /059 10-seed unified-ensemble IS trade roster — `reports-v3/iteration_v3-059/in_sample/trades.csv`, **171 IS trades, 36 active calendar months** (not /101/102/105, which carried rejected axes).

### T1 — the IS loss-month diagnostic: the loss months share a LOW WIN RATE, not a regime signature

`loss_month_diagnostic.py` → `T1_per_month_is_pnl.csv`, `T1b_worst10_is_months.csv`. The /059 IS roster split by calendar month:

| | months | weighted_pnl sum |
|---|---:|---:|
| All IS active months | 36 | +78.18 |
| **Loss months (`wpnl < 0`)** | **15 (42%)** | **−50.49** |
| Profit months (`wpnl ≥ 0`) | 21 | +128.67 |

The 10 worst IS months (`T1b`):

| month | n_trades | win_rate | weighted_pnl | bch_wpnl | trx_wpnl | ldo_wpnl |
|---|---:|---:|---:|---:|---:|---:|
| 2023-09 | 4 | **0.000** | −6.51 | −5.54 | −0.97 | 0.00 |
| 2024-02 | 7 | **0.143** | −5.75 | −1.32 | −4.43 | 0.00 |
| 2023-12 | 9 | 0.333 | −5.39 | −4.76 | −0.62 | 0.00 |
| 2023-11 | 6 | **0.167** | −5.31 | −2.42 | −2.88 | 0.00 |
| 2022-02 | 6 | 0.333 | −5.08 | −0.30 | −4.78 | 0.00 |
| 2024-09 | 3 | **0.000** | −3.73 | 0.00 | −1.22 | −2.51 |
| 2022-07 | 3 | 0.333 | −3.59 | −3.59 | 0.00 | 0.00 |
| 2023-02 | 10 | 0.300 | −3.38 | −0.57 | −2.81 | 0.00 |
| 2023-01 | 9 | 0.222 | −2.41 | −0.67 | −1.74 | 0.00 |
| 2024-10 | 10 | 0.300 | −2.19 | +0.71 | −0.54 | −2.36 |

Two things the loss months **do** share — **neither of which is an "unseen-regime" signature**:
1. **A systematically LOW WIN RATE — 0.0 to 0.33.** The loss-vs-profit distinction is fundamentally a *hit-rate* effect: the model's directional calls in those months convert poorly to PnL. This is not a magnitude effect (the per-trade losses are normal-sized ATR-stop losses) — it is that the calls are simply wrong more often.
2. **2023 clustering** — 6 of 15 loss months fall in calendar 2023 (the year-long crypto bear/chop). But (T7) calendar 2023 is *not* an OOD year by the model's feature distribution, and "trade less in 2023" is hindsight, not a causal detector.

The prize, **if** a clean causal detector existed, would be material: removing the worst 5 months lifts IS wpnl +28.03 (to +106.21); the worst 8, +38.73. That is precisely why the hypothesis deserved — and got — a deep multi-angle EDA. The detector does not exist.

### T2/T3 — the Mahalanobis OOD distance: the literal "unseen-regime" statistic does NOT separate the loss months

`loss_month_separators.py` → `T2_loss_month_separators.csv`, `T3_separation_power.csv`. The genuinely-new mechanism the user's "unseen-regime" framing points at is a **trailing-window Mahalanobis OOD distance**: at month `M`, fit `mu, Sigma` on the trailing `training_months = 24` of per-symbol 14-`V3_FEATURE_COLUMNS` rows (the exact window the LightGBM for month `M`'s first cell trains on), then score month `M`'s own feature rows — `D(M) = mean_t sqrt((x_t − mu)ᵀ Σ⁻¹ (x_t − mu))`. `D(M)` large ⇔ month `M`'s joint feature distribution is far from what the model was trained on ⇔ exactly the user's "regime the model hasn't seen."

A usable detector needs AUC ≥ 0.70 (AUC = P(a loss month ranks higher on the separator than a profit month)). The result:

| separator | mean(loss) | mean(profit) | AUC | Cohen's d |
|---|---:|---:|---:|---:|
| **maha_ood** (trailing 24-month) | 4.776 | 4.478 | **0.559** | 0.153 |
| atr_pct_rank_200 | 0.385 | 0.486 | 0.362 | −0.403 |
| hurst_100 | 1.004 | 1.008 | 0.486 | −0.104 |
| range_realized_vol_50 | 0.023 | 0.025 | 0.413 | −0.158 |
| btc_dd_30d (primitive-9 signal) | 9.072 | 7.985 | 0.483 | 0.129 |
| btc_vol_z_30d (primitive-9 signal) | 0.136 | −0.291 | 0.590 | 0.366 |

**The Mahalanobis OOD distance scores AUC 0.559 — barely above the 0.50 no-separation line.** The per-month ranking is decisive: the single highest-OOD month (2023-01, `maha` 11.90) does lose — but the 2nd/3rd/6th highest-OOD months (2024-12, 2023-06, 2022-05) are all *profit* months, and the **largest winner of the entire IS** (2024-04, +25.24 wpnl) sits *below the median* OOD distance. High OOD does not imply a loss; low OOD does not imply a win. The OOD axis carries no loss-vs-profit information.

Every other separator also fails: ATR percentile AUC 0.362 (loss months are if anything *lower*-vol — the inverse of an "unseen-regime" intuition); BTC drawdown AUC 0.483 (no separation — consistent with primitive 9 being CLOSED at /022/074); BTC vol-z AUC 0.590 (the strongest of this set, still far below 0.70).

### T4 — trade-level OOD: a losing TRADE does not have a higher entry-bar OOD

`loss_month_deep.py` → `T4_trade_ood_quartiles.csv`. Month aggregation can mask a clean trade-level separator, so the same Mahalanobis OOD was computed **per trade** at the trade's entry bar (causal — the trade `open_time` equals the entry candle's `close_time`; reference = the trailing 24-month window of bars closing strictly before entry):

| | mean entry-OOD | n |
|---|---:|---:|
| Losing trades | **3.395** | 100 |
| Winning trades | **3.383** | 71 |

**AUC (loser ranks higher) = 0.504 — no separation whatsoever.** The loser and winner mean entry-OOD are *identical to 2 decimal places.* The entry-OOD quartile split confirms it: the most-OOD quartile (Q4_high) carries wpnl **+25.63** at a 41.9% win rate — the most out-of-distribution trades are *fine*; the worst quartile by PnL is **Q2** (−6.25 wpnl), a *middle* OOD bucket. The user's "unseen-regime" hypothesis fails at both the month level (T2/T3) and the trade level (T4).

### T5/T6 — per-(symbol, direction) drag and trailing hit-rate state

`loss_month_deep.py` → `T5_symbol_direction_cells.csv`, `T6_trade_level_state.csv`.

**T5** — the only genuine structural drag is **TRX, net-negative on BOTH directions** (short −5.34 / 13.0% net, long −2.01). But this is a *symbol* problem, not a *regime/unseen-distribution* problem — and it is already-known (TRX is why /049 raised TRX's ADX threshold, /061 raised TRX's vol-scale floor, /074 targeted TRX with the regime kill switch, /075 scoped the BTC-trend de-rate to TRX). A symbol-asymmetric drag is not the /106 axis, and the regime-conditional kill switch keyed on it (primitive 9) is CLOSED at the catalog level.

**T6** — for each trade, the win-rate of the last `K` closed trades of the same symbol (causal). Does a cold streak predict the next trade losing? AUC 0.499 (K=3), 0.511 (K=5), 0.534 (K=8). **No** — a trailing cold streak carries essentially no information about the next trade's outcome. Trade outcomes on this roster are close to serially independent in sign.

### T7/T8 — the wide causal separator sweep: the last-chance check

`regime_final_check.py` → `T7_wide_regime_separators.csv`, `T8_separator_ranking.csv`. To rule out that the EDA simply used the wrong variable or the wrong reference-window length, a wider battery of **11 causal separators** was swept at month level — BTC trailing return at 30/60/90d, BTC trailing realized vol at 30/60d, BTC absolute 60d return (direction-agnostic regime intensity), symbol trailing return and ATR percentile, and the Mahalanobis OOD at **three** reference lengths (12 / 18 / 24 months):

| separator | AUC | \|AUC − 0.5\| |
|---|---:|---:|
| **btc_abs_ret_60d** (strongest of 11) | **0.641** | **0.141** |
| sym_atr_pct | 0.362 | 0.138 |
| sym_ret_30d | 0.387 | 0.113 |
| btc_vol_30d | 0.422 | 0.078 |
| btc_vol_60d | 0.429 | 0.071 |
| maha_ood_24m | 0.559 | 0.059 |
| btc_ret_90d | 0.448 | 0.052 |
| btc_ret_30d | 0.451 | 0.049 |
| maha_ood_18m | 0.537 | 0.037 |
| maha_ood_12m | 0.533 | 0.033 |
| btc_ret_60d | 0.470 | 0.030 |

**The strongest separator out of 11 candidates is `btc_abs_ret_60d` at AUC 0.641 — below the AUC ≥ 0.70 bar for a usable causal detector.** The Mahalanobis OOD is essentially flat across all three reference lengths (12m 0.533 / 18m 0.537 / 24m 0.559) — the 24-month length was not "the wrong reference"; the OOD axis simply carries no loss-vs-profit signal at any reference length. **No causal regime variable cleanly separates the IS loss months.** This is the conclusive negative for parts 1–2 of the hypothesis.

### T9 — the drawdown-brake counterfactual: "stop when losing" ACTIVELY HURTS

`regime_final_check.py` → `T9_drawdown_brake_counterfactual.csv`. The user's "the model needs to stop" intuition, taken at face value, is a **trailing-equity drawdown brake**: kill every trade entered while the portfolio's trailing-equity drawdown (known from prior *closed* trades — strictly past-only) exceeds a trigger. The full IS counterfactual over a trigger grid (/059 IS baseline: weighted_pnl +78.18, monthly Sharpe +1.0658):

| trigger (wpnl) | trades killed | kept wpnl | kept monthly Sharpe | Δ Sharpe |
|---:|---:|---:|---:|---:|
| 3.0 | 165 | −3.25 | −46.82 | **−47.89** |
| 5.0 | 164 | −6.79 | −4.93 | **−6.00** |
| 8.0 | 163 | −8.71 | −5.33 | **−6.40** |
| 10.0 | 162 | −11.53 | −7.17 | **−8.24** |
| 12.0 | 162 | −11.53 | −7.17 | **−8.24** |
| 15.0 | 99 | +17.09 | +0.52 | **−0.55** |

**Every trigger produces a NEGATIVE Δ Sharpe. There is no threshold at which stopping during a drawdown improves the IS Sharpe.** Two mechanisms, both fatal to part 3 of the hypothesis:

1. **Drawdowns mean-revert.** The EDA measured this directly: trades entered while the portfolio trailing-DD ≥ 3 / 5 / 8 wpnl have *positive* cumulative wpnl. The brake stops exactly the trades that recover the book. This is the **iter-v3/054 per-symbol drawdown-brake failure mode** (closed at /054) reproduced at the portfolio level.
2. **Early-arm deadlock.** The /059 IS book opens with losing months (2022-01/02). At low triggers the brake arms in the first months and — because the kill removes the very trades that would have generated the recovery PnL — it can never see the equity recover to disarm: 165 of 171 trades killed at trigger 3.0. This is the `feedback_v3_oracle_eda_validity.md` STATEFUL-gate deadlock the /054 closeout flagged. A trailing-drawdown brake is structurally incapable of helping on this roster.

### EDA verdict — the hypothesis is falsified on three independent axes

The user's hypothesis — *the IS loss months are an out-of-distribution / unseen regime the model should detect and stop in* — is **conclusively falsified**:

1. **No OOD signature.** The Mahalanobis OOD distance — the literal "unseen-distribution" statistic — does not separate loss months: month AUC 0.559, trade AUC 0.504 (loser entry-OOD 3.395 ≈ winner 3.383, identical), flat across 12/18/24-month reference windows.
2. **No causal regime separator at all.** The strongest of 11 causal regime separators is AUC 0.641 — below the 0.70 usable bar. There is no clean, causal, IS-detectable condition the loss months share and the profit months do not.
3. **"Stop when losing" actively hurts.** A trailing-drawdown brake — the cleanest "stop" mechanism — yields a NEGATIVE IS Sharpe delta at every trigger, because drawdowns mean-revert: stopping kills the recovery. The /054 brake failure mode, confirmed at portfolio level.

There is no genuine signature to build a gate on. The honest verdict is **NULL-AT-EDA**.

## 4. The verdict — NULL-AT-EDA, no backtest — the fail-fast justification

The dispatch reserves NULL-AT-EDA for "an axis the deep EDA conclusively proves dead (high bar)." The /106 EDA clears that bar — a four-script, nine-table, strictly-IS-only screen that operationalized a user-directed hypothesis and falsified it on three independent axes. No backtest was run, for three binding reasons:

1. **A backtest would knowingly reproduce a documented failure mode.** The brief Section 3 specifies a complete, gate-able implementation of the designated detector — a trailing-window Mahalanobis OOD kill gate (primitive 13). The EDA (T4) already shows what that gate does: at the IS-90th-percentile cutoff it kills the Q4_high OOD quartile, which carries **+25.63 wpnl at a 41.9% win rate** — the gate removes *profitable* trades. The pre-registered falsifier F1 (IS Sharpe non-improvement) is predicted to fire. Running the backtest would spend compute and a `RiskV2` `src/` build to confirm a negative the EDA has already established.

2. **Fail-fast forbids a foreseeable-failure spend.** `feedback_fail_fast.md` — the cheap-kill discipline the /094/095/096/098/099/100/103/104 fail-fast EDAs established — directs that an axis a committed IS-only EDA conclusively kills is closed at the EDA: no `src/` change, no runner change, no backtest, no Critic, no agent dispatch. The honest move is to report the negative verdict with the numbers, which is what NULL-AT-EDA is.

3. **The drawdown-brake counterfactual (T9) is itself a complete in-sample backtest of the user's "stop" intuition** — and it is IS-negative at every trigger. The cheapest possible test of "stop when losing" has already been run, inside the EDA, and it failed. There is no second mechanism to try that the EDA has not already covered (OOD gate — T4; drawdown brake — T9; regime kill switch — T2/T8; cold-streak gate — T6).

No `src/` code was written — `V3_FEATURE_COLUMNS` stays at 14, the model / label / universe / 7-gate RiskV2 stack are bit-identical to /059; there is nothing to revert. The Mahalanobis computation lives entirely inside the committed `analysis/iteration_v3-106/` EDA scripts (closed-form `numpy.linalg.inv` + an `einsum` quadratic form — no new dependency, no production wiring). `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` were untouched. Every Phase 1-5 measurement was strictly IS-only; the QR did not inspect the post-cutoff OOS.

## 5. The honest risk-management conclusion — what /106 establishes about v3 risk posture

iter-v3/106 **is itself** a risk-management iteration — its entire subject is whether a risk gate would mitigate the IS loss-month drag. The EDA's role was to verify, before any build, that the proposed gate would actually mitigate risk. It established the opposite, and that is a substantive, useful finding for the v3 risk posture:

- **The IS loss months are not a *detectable* condition.** No causal regime variable (11 candidates, OOD at 3 reference lengths) separates them at a usable AUC.
- **The IS loss months are not a *stoppable* condition.** They are a **low-win-rate, regime-agnostic, MEAN-REVERTING drag** distributed across regimes; the book *recovers* from its drawdowns (T9). A stop that arms during a drawdown interrupts the recovery and lowers the Sharpe at every trigger.
- **The correct risk posture is therefore to NOT add a stop that would interrupt the recovery** — which is exactly what NULL-AT-EDA delivers: zero change to the standing /059 risk stack. The incumbent RiskV2 gates (R1/R2/R3/R4/R5 — BTC-trend kill, vol scaling, ADX, Hurst regime, low-vol filter, z-score OOD) stay /059-identical. The univariate z-score OOD gate (R3) is re-validated *as a tail-safety gate, not a loss-month detector* — T2/T4 show its multivariate Mahalanobis cousin carries no loss-month signal, consistent with R3's correct role.

The generalizable risk-management lesson: **a portfolio whose drawdowns mean-revert must not be fitted with a trailing-drawdown stop.** The /054 closeout established this at the per-symbol level; /106 confirms it at the portfolio level with a full IS counterfactual. The v3 book's losses are a hit-rate phenomenon to be fixed *upstream* (better trade construction — Section 7), not a regime to be detected and exited.

## 6. The directed-hypothesis framing — the honest falsification IS the rigor arm working

This iteration tested a hypothesis the **user** specified. The result is a clean falsification. It is important to frame that correctly.

The crypto-trade v3 process has two arms: an *exploration* arm that generates and tests bold axes, and a *rigor* arm that holds every result to the 5-rung evidence ladder and reports honestly — including null and negative results — with the same discipline as positive ones (`feedback_no_cheating.md`, `feedback_always_document.md`). A directed hypothesis is run through *both* arms exactly as a QR-selected one is. The user's intuition — that the loss months are an unseen regime the model should stop in — was a genuinely reasonable prior; it is the kind of hypothesis a careful practitioner would form. The QR's job was not to confirm it but to *operationalize it into a falsifiable claim and test it without flinching.* That is what happened: the claim was made precise (Section 2), a deep multi-angle IS-only EDA was built to interrogate all three of its testable parts, and the evidence falsified all three.

**A directed hypothesis that the evidence falsifies is not a failure of the iteration — it is the rigor arm doing precisely what it exists to do.** The alternative — running a backtest of a Mahalanobis gate the EDA has already shown removes profitable trades, so the iteration produces a "result" that nominally honors the directive — would be the failure mode: it would spend compute to manufacture a confirmation-shaped artifact around a hypothesis the cheap evidence has already killed. NULL-AT-EDA on a directed axis is the *more* disciplined outcome, not the less. The finding is delivered cleanly, with the numbers, and it is genuinely informative: it tells v3 that the loss months are a low-win-rate mean-reverting drag, redirects the next iteration to the layer that *can* move them (trade construction — Section 7), and adds a portfolio-level confirmation of the /054 "don't fit a drawdown stop to a mean-reverting book" lesson. The user's directive to "focus on risk management" was honored — by establishing rigorously what the correct risk posture *is*.

## 7. Lessons

1. **The IS loss months are a low-win-rate, regime-agnostic, MEAN-REVERTING drag — not a detectable or stoppable condition.** This is the central finding. 15 of 36 IS months lose (−50.49 wpnl); they share a low win rate (0.0–0.33), not a regime signature. No causal separator (11 candidates, Mahalanobis OOD at 3 reference lengths) reaches AUC 0.70; the OOD distance the "unseen-regime" hypothesis points at is flat at AUC 0.559 month / 0.504 trade. And a trailing-drawdown brake is IS-Sharpe-negative at every trigger because the book's drawdowns mean-revert. The loss is a *hit-rate* phenomenon, to be fixed upstream — not a regime to be exited.

2. **A trailing-drawdown stop must not be fitted to a portfolio whose drawdowns mean-revert.** T9 ran the full IS counterfactual of the user's "stop when losing" intuition: every trigger lowers the Sharpe, because the brake stops exactly the trades that recover the book, and at low triggers it deadlocks (165/171 trades killed — it arms early and the kill removes the PnL that would let it disarm). This is the /054 per-symbol drawdown-brake failure mode reproduced at the portfolio level. Generalizable: before proposing any stateful loss-stop gate, the brief must measure whether the book's drawdowns mean-revert or trend — and if they mean-revert, the gate is structurally counterproductive.

3. **The Mahalanobis OOD distance is a tail-safety statistic, not a loss-month predictor.** The economically intuitive prior — that the model loses in regimes far from its training distribution — did not survive contact with the data: losing and winning trades have *identical* mean entry-OOD (3.395 vs 3.383), and the most-OOD trade quartile is the second-most *profitable*. An OOD gate detects feature-space novelty; it does not detect when the directional call will be wrong. The two are different things, and on this roster they are uncorrelated. (This also re-validates that the incumbent R3 z-score OOD gate is correctly scoped as tail safety, not loss avoidance.)

4. **A directed hypothesis is run through the rigor arm exactly as a QR-selected one — and an honest falsification is the disciplined outcome.** The user directed this axis with a specific, reasonable prior. The QR operationalized it into a falsifiable claim and tested all three of its parts with a committed IS-only EDA. The evidence falsified it. The honest move — a clean NULL-AT-EDA with the numbers, no backtest manufactured to nominally honor the directive — is the rigor arm working as designed (`feedback_no_cheating.md`). The directive to "focus on risk management" was honored by establishing rigorously what the correct risk posture is: do not add a stop that interrupts the recovery.

5. **The drawdown-brake counterfactual is itself a cheap, complete IS backtest of a risk gate — run it inside the EDA.** T9 is a full in-sample replay of the proposed "stop" mechanism over a trigger grid, with no `src/` build. It is the cheapest possible test of a loss-stop gate, and it is decisive. Future risk-overlay EXPLORATIONs should make the in-sample counterfactual replay a mandatory Phase-1 EDA step — a stateful risk gate whose IS counterfactual is negative at every trigger is killed at the EDA, exactly as a feature with INERT importance is.

## 8. Next Iteration Ideas — iter-v3/107 (cycle-5 EXPLORATION slot #7)

**The diagnosis is now sharp and convergent.** The /105 closeout localized the binding constraint **downstream of the training label, in the trade-construction / exit / risk layer.** The /105 Critic flagged the **trade-construction / exit layer** as the next axis. The /106 finding is fully consistent and *sharpens* it: the loss months are a **low-win-rate** phenomenon — *the model's directional calls convert poorly to PnL.* That is not a signal problem (the training side is comprehensively closed across /016/082/085/086/093/096/097/098/099/100/101/102/103/104/105) and it is not a detectable-regime problem (/106). **It is a trade-construction problem: the layer that turns a directional score into a realized P&L — the entry, the exits, the sizing — is converting good calls into mediocre money.**

And there is a precise, un-attacked target. v3's exit logic — the triple-barrier **2-ATR take-profit / 1-ATR stop-loss / 21-candle timeout** — has only ever been **knob-tuned** (iter-v3/010 swept the barrier *multipliers*). It has **never been re-architected.** Every v3 trade, for 106 iterations, has resolved by the identical rule: first-touch of a *static, symmetric-in-construction* ±ATR barrier within a *fixed* 21-candle window, with the barrier distance frozen at entry. "Exhausted" is the forbidden conclusion — and it is also factually wrong: the exit *geometry* is an entire axis class that has had exactly one knob-tune and zero structural attacks.

### Recommendation #1 (TOP) — re-architect the exit: an ATR-trailing-stop / dynamic-barrier exit

**The axis.** Replace the static triple-barrier exit with a **dynamic exit** — concretely, an **ATR-trailing stop**: the stop-loss is no longer frozen at entry−1·ATR; it *ratchets* — once the trade moves favorably, the stop trails the high-water mark at a fixed ATR distance, locking in open profit while still cutting losers at the original 1-ATR risk. The take-profit either remains the 2-ATR barrier or is removed entirely (let the trailing stop define the exit), and the 21-candle timeout is retained as a backstop.

**Why this directly attacks the /106 finding — the quantitative rationale.** The /106 loss months are a *win-rate* problem: many trades the model directionally calls correctly still close as losers or as thin wins. There is a specific, measurable mechanism a static barrier creates and a trailing stop fixes — **profit give-back**: under a static 2-ATR TP, a trade that runs to +1.8 ATR and then reverses to −1 ATR is booked as a *full loss*, despite the model's call having been correct for most of the trade's life. A static barrier has no memory of the favorable excursion; it converts a correct-but-incompletely-resolved call into a maximal loss. A trailing stop has exactly that memory: the same trade closes at roughly break-even or a small profit. This converts a slice of the loss-month losers into wins or scratches — it raises the *win rate*, which is precisely the /106-identified failure axis. The mechanism is concrete, it is the right layer (downstream of the label, per /105), and it has never been built in v3.

**The fail-fast gating EDA — and why it is cheap and decisive.** Per `feedback_fail_fast.md` + `feedback_v3_axis_selection_quant_discipline.md` the axis must carry a committed `analysis/iteration_v3-107/*.py` IS-only GO/NO-GO EDA preceding the brief — and the trade-construction layer is uniquely cheap to pre-test, because the EDA can **re-resolve the existing /059 trade entries under the candidate exit rule directly on the OHLCV path**, with no model retrain and no backtest. The EDA computes, strictly IS-only: (a) the **Maximum Favorable Excursion (MFE)** distribution of every /059 IS trade — how far each trade ran in its favor before its actual exit; if a material fraction of the *losing* trades have an MFE ≥ 1 ATR (they were *in profit* at some point), the give-back mechanism is real and the trailing stop has something to capture — this is the GO bar; (b) a **counterfactual re-resolution** of all 171 IS trades under the ATR-trailing rule (for each trade, walk its OHLCV path bar-by-bar, ratchet the stop, record the trailing-rule exit), reporting the counterfactual IS win rate, weighted_pnl, and monthly Sharpe vs the /059 actuals — a near-complete IS backtest of the exit change, with zero model involvement; (c) the trade-rate check — a trailing stop does not change the *entry* count, so the bundle-level trade-rate floor is structurally preserved (a point the brief must state). Pre-registered falsifiers: F-MFE (if losing trades' MFE is degenerately small — they go straight to the stop — the trailing rule has nothing to capture → NO-GO at EDA), F-COUNTERFACTUAL (if the counterfactual IS Sharpe does not exceed the /059 IS Sharpe → no structural lift → NO-GO), F-RATE (entry count unchanged — informational). A higher counterfactual IS win rate and Sharpe from re-resolving the *same* entries under a trailing exit is the single most direct possible evidence that the exit geometry — not the signal — is the binding constraint, and it is measurable entirely IS-only before any `src/` build or backtest.

**Why this is genuinely bold, not a re-tread.** iter-v3/010 tuned the barrier *multipliers* — it asked "is 2.0/1.0 the right *distance*" while keeping the barrier *static and frozen at entry*. An ATR-trailing stop changes the **structure** of the exit: the stop becomes path-dependent and time-evolving. This is to /010 what the trend-scanning label (/105) was to the barrier-multiplier knob — a different *kind* of object, not a different value of the same knob. It is the first structural attack on the v3 exit layer in 106 iterations, it targets the exact /106-identified failure (win rate / profit give-back), and it sits in the exact layer /105 localized as binding.

### Recommendation #2 (runner-up) — scaled / partial exits with a time-decayed barrier

If the /107 QR judges the MFE EDA's give-back evidence thin (the F-MFE kill — losing trades go straight to the stop, leaving a trailing rule nothing to capture), the next exit-layer axis is a **scaled exit with a time-decayed barrier**: rather than a single all-or-nothing first-touch resolution, take partial profit at an intermediate level (e.g. close half the position at +1 ATR, let the rest run to 2 ATR or a trailing stop), and *decay the take-profit barrier toward the entry as the timeout approaches* — so a trade that has not resolved by candle 15 of 21 is exited at a barrier that has tightened to capture whatever favorable excursion exists rather than dying at the timeout for a near-zero or negative P&L. This attacks a *different* slice of the /106 win-rate problem — the *thin-win and timeout-scratch* trades rather than the profit-give-back losers — and is the natural second structural exit axis. It is ranked second only because the ATR-trailing stop (#1) is the cleaner single-variable change and its MFE/counterfactual EDA is the more direct test of the /106 diagnosis. Both recommendations are **structural re-architectures of the trade-construction / exit layer** — the layer /105 localized and /106 sharpened — not another knob on a fixed exit, which is exactly what the closed-axis record demands.

Per `feedback_v3_axis_selection_quant_discipline.md` the iter-v3/107 axis must be QR-led with a committed `analysis/iteration_v3-107/*.py` EDA basis preceding the brief; per `feedback_fail_fast.md` it must carry the hard Phase-1 GO/NO-GO EDA (the F-MFE / F-COUNTERFACTUAL / F-RATE falsifiers above) before any `src/` build.

## 9. Commit chain

- EDA SHA: `7b55698` — `analysis/iteration_v3-106/` (4 scripts: `loss_month_diagnostic.py`, `loss_month_separators.py`, `loss_month_deep.py`, `regime_final_check.py`; 9 result CSVs: `T1_per_month_is_pnl.csv`, `T1b_worst10_is_months.csv`, `T2_loss_month_separators.csv`, `T3_separation_power.csv`, `T4_trade_ood_quartiles.csv`, `T5_symbol_direction_cells.csv`, `T6_trade_level_state.csv`, `T7_wide_regime_separators.csv`, `T8_separator_ranking.csv`, `T9_drawdown_brake_counterfactual.csv`).
- Brief SHA: `81fd62b` — `briefs-v3/iteration_v3-106/research_brief.md` (the full 10-section brief; Section 4 carries the NULL-AT-EDA recommendation; Section 3 documents the designated would-be Mahalanobis OOD gate with a complete implementation spec for an override-to-backtest). Setup SHA backfilled into Section 10 at `05e2a46`.
- Diary SHA: this closeout — `docs(iter-v3/106): closeout diary — FILED NULL-AT-EDA / user-directed risk-management hypothesis FALSIFIED — IS loss months are a low-win-rate, regime-agnostic, mean-reverting drag, not a detectable or stoppable condition`.
- Catalog update SHA: committed with this diary — `briefs-v3/exploration_catalog.md` /106 row (classification NULL-AT-EDA).
- **No reports** (no backtest run — NULL-AT-EDA stopped the iteration at the EDA).
- **No `src/` change** (NULL-AT-EDA — nothing was implemented; `V3_FEATURE_COLUMNS` stays at 14, bit-identical to /059; the model / label / universe / 7-gate RiskV2 stack are all /059-identical; nothing to revert).
- **Tag**: `v0.v3-106` — a closeout marker only, tagged by the orchestrator (NOT a baseline update — the `v0.v3-082`…`v0.v3-105` pattern; BASELINE_V3.md UNCHANGED at `v0.v3-059`, IS +1.0894 / OOS +0.5791, 10-seed CONFIRMATION).

iter-v3/106 is cycle-5 EXPLORATION slot #6; the cadence advances. iter-v3/107 is slot #7 — the recommended EXIT-LAYER re-architecture (an ATR-trailing-stop / dynamic-barrier exit) with a hard Phase-1 GO/NO-GO EDA (Section 8) — the first structural attack on the v3 exit geometry in 106 iterations, targeting the /106-identified win-rate / profit-give-back failure in the trade-construction layer /105 localized as binding.

**NO CHEATING.** `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` untouched. The walk-forward embargo fix (`e149e9d`) is inherited unchanged. This EXPLORATION does NOT update BASELINE_V3.md regardless of outcome — `v0.v3-106` is a closeout marker only. All Phase 1-5 EDA was strictly IS-only (`open_time < OOS_CUTOFF_MS` for trades; `close_time < OOS_CUTOFF_MS` for the feature reference/test windows — each of the 4 committed EDA scripts asserts the invariant at load); the QR did not inspect the post-cutoff OOS — no backtest was run.
