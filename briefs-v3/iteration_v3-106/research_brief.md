# iter-v3/106 — Research Brief — Cycle-5 EXPLORATION slot #6: a risk-management overlay — IS loss-month / "unseen-regime" detection (USER-DIRECTED)

> **QR RECOMMENDATION: NULL-AT-EDA.** The deep, multi-angle IS-only EDA
> (4 committed scripts, commit `7b55698`; 9 result tables T1–T9) tested the
> user's hypothesis — *the IS loss months are months the model has not seen
> before (a novel / out-of-distribution regime), and a detector that recognizes
> that condition and stops trading would lift the Sharpe* — and **conclusively
> falsified it on the /059 10-seed baseline roster.** No causal regime variable
> separates the 15 IS loss months from the 21 profit months at a usable bar
> (strongest of 11 candidates: AUC 0.641, below the 0.70 threshold; the
> Mahalanobis OOD composite the hypothesis literally points at scores AUC 0.559
> at month level and 0.504 at trade level). And the cleanest "stop when losing"
> mechanism — a trailing-equity drawdown brake — produces a **NEGATIVE** IS
> Sharpe delta at *every* trigger threshold (drawdowns mean-revert on this
> roster; the brake kills the recovery — the /054 per-symbol-brake failure mode
> reproduced at portfolio level). There is no clean, IS-detectable, causal
> "unseen-regime" signature to build a gate on. No Phase-6 backtest is
> recommended. Sections 2–4 carry the full numerical basis; Section 3 documents
> a designated would-be detector with a complete implementation spec and
> Section 4 carries pre-registered falsifiers, so an override-to-backtest has a
> gate-able artifact.

---

## Section 0 — Data-Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` (`OOS_CUTOFF_MS = 1742774400000`) — IMMUTABLE. Untouched.
- `training_months = 24` — IMMUTABLE. Untouched. Used as the trailing reference-window length for the Mahalanobis OOD detector (the detector the user's hypothesis points at).
- Every Phase 1–5 measurement in this brief is **strictly IS-only**: every trade entering any computation has `open_time < OOS_CUTOFF_MS`; every feature row entering any reference/test window has `close_time < OOS_CUTOFF_MS` (loss-month identification, separator measurement, drawdown-brake counterfactual). The post-cutoff OOS roster and post-cutoff feature data are **never read** — the QR sees OOS for the first time in Phase 7 (which, on the NULL-AT-EDA recommendation, does not occur).
- The detector and its threshold are calibrated **only** on the IS loss months identified by EDA 1. There is no OOS-month identification anywhere.
- The /059 baseline IS trade roster is `reports-v3/iteration_v3-059/in_sample/trades.csv` — the canonical 10-seed unified-ensemble single trade roster (NOT /101/102/105, which carried rejected axes). 171 IS trades, 36 active calendar months.

## Section 1 — Hypothesis

**The user-directed hypothesis (verbatim, 2026-05-19):** *"make the QR focus more on risk management, analyse in IS the months where model didn't perform. Those months most likely the model hasn't seen before it needs to stop. Focus on that part to improve sharp. It's not linked directly to machine learning eda, but for sure we can improve during the months when we lost more."*

Operationalized as a falsifiable claim: **the IS calendar months in which the /059 book lost money share a common, IS-detectable, CAUSAL signature — specifically that the market state in those months is novel relative to the model's training distribution (out-of-distribution) — and a risk gate that detects that condition at bar `t` (using only data ≤ `t`) and stops or reduces trading would remove the loss months while preserving the profitable months, lifting the IS Sharpe.**

This is a **risk-management overlay** axis, not a feature/label/model axis. It is downstream of the training label — exactly where the /105 closeout localized the binding constraint (the /104 "the label is the constraint" hypothesis was falsified at /105; the /105 diary Section 6 explicitly directed /106 to "work the execution and risk layer"). The model, the 14 `V3_FEATURE_COLUMNS`, the triple-barrier label (ATR 2.0/1.0, 21-candle timeout), and the BCH/LDO/TRX universe stay **bit-identical to /059**. The single clean variable is one NEW risk gate (or a materially-modified RiskV2 gate).

**The test of the hypothesis is the EDA itself.** If the loss months carry a clean causal "unseen-regime" signature, the axis proceeds to a gate design + a backtest. If the deep EDA conclusively shows no such signature exists, the honest verdict is NULL-AT-EDA. **The EDA falsified the hypothesis** (Section 2). The recommendation is NULL-AT-EDA.

## Section 2 — IS-Only Numerical Evidence

Four committed IS-only EDA scripts under `analysis/iteration_v3-106/` (commit `7b55698`), 9 result tables. Every row entering any computation satisfies the IS-only invariant declared in Section 0 (each script asserts it at load time).

### T1 — the IS loss-month diagnostic (`loss_month_diagnostic.py`; `T1_per_month_is_pnl.csv`, `T1b_worst10_is_months.csv`)

The /059 IS roster (171 trades) split by calendar month:

| | months | weighted_pnl sum |
|---|---:|---:|
| All IS active months | 36 | +78.18 |
| Loss months (`wpnl < 0`) | **15 (42%)** | **−50.49** |
| Profit months (`wpnl ≥ 0`) | 21 | +128.67 |

**The 10 worst IS months:**

| month | n_trades | win_rate | weighted_pnl | bch_wpnl | trx_wpnl | ldo_wpnl |
|---|---:|---:|---:|---:|---:|---:|
| 2023-09 | 4 | 0.000 | −6.51 | −5.54 | −0.97 | 0.00 |
| 2024-02 | 7 | 0.143 | −5.75 | −1.32 | −4.43 | 0.00 |
| 2023-12 | 9 | 0.333 | −5.39 | −4.76 | −0.62 | 0.00 |
| 2023-11 | 6 | 0.167 | −5.31 | −2.42 | −2.88 | 0.00 |
| 2022-02 | 6 | 0.333 | −5.08 | −0.30 | −4.78 | 0.00 |
| 2024-09 | 3 | 0.000 | −3.73 | 0.00 | −1.22 | −2.51 |
| 2022-07 | 3 | 0.333 | −3.59 | −3.59 | 0.00 | 0.00 |
| 2023-02 | 10 | 0.300 | −3.38 | −0.57 | −2.81 | 0.00 |
| 2023-01 | 9 | 0.222 | −2.41 | −0.67 | −1.74 | 0.00 |
| 2024-10 | 10 | 0.300 | −2.19 | +0.71 | −0.54 | −2.36 |

Two observations the loss months **do** share — neither of which is an "unseen-regime" signature:
1. **Low win rate.** The loss months systematically have win rates of 0.0–0.33; the loss-vs-profit signal is fundamentally a *hit-rate* effect, not a *PnL-magnitude* effect.
2. **2023 clustering.** 6 of the 15 loss months fall in calendar 2023 (the year-long crypto bear/chop). But — see T7 — calendar 2023 is *not* an OOD year by the model's feature distribution, and a "2023" calendar gate is not a causal detector (it is hindsight).

Loss concentration: removing the worst 5 months would lift IS wpnl by +28.03 (to +106.21); the worst 8, by +38.73. **If** a clean detector existed, the prize would be material — which is why the hypothesis deserved the deep EDA it got. It does not exist (T2–T9).

### T2/T3 — month-level regime separators: does ANY variable split loss from profit? (`loss_month_separators.py`; `T2_loss_month_separators.csv`, `T3_separation_power.csv`)

For each of the 36 IS months, a battery of **causal** separators measured at the month's start (every value a function only of data closing before the month begins). The headline candidate — and the genuinely-NEW mechanism the user's "unseen-regime" framing points at — is a **trailing-window Mahalanobis OOD distance**: at month `M`, fit `mu, Sigma` on the trailing `training_months = 24` of per-symbol 14-feature rows (the window the LightGBM for month `M`'s first cell is trained on), then score month `M`'s own feature rows: `D(M) = mean_t sqrt((x_t − mu)ᵀ Σ⁻¹ (x_t − mu))`. `D(M)` large ⇔ month `M`'s joint feature distribution is far from what the model was trained on ⇔ the user's "regime the model hasn't seen".

Separation power, AUC = P(a loss month ranks **higher** on the separator than a profit month); a usable "unseen-regime" detector needs AUC ≥ 0.70:

| separator | mean(loss) | mean(profit) | AUC | Cohen's d |
|---|---:|---:|---:|---:|
| **maha_ood** (trailing 24-month) | 4.776 | 4.478 | **0.559** | 0.153 |
| atr_pct_rank_200 | 0.385 | 0.486 | 0.362 | −0.403 |
| hurst_100 | 1.004 | 1.008 | 0.486 | −0.104 |
| range_realized_vol_50 | 0.023 | 0.025 | 0.413 | −0.158 |
| btc_dd_30d (primitive-9 signal) | 9.072 | 7.985 | 0.483 | 0.129 |
| btc_vol_z_30d (primitive-9 signal) | 0.136 | −0.291 | 0.590 | 0.366 |

**The Mahalanobis OOD distance does not separate the loss months (AUC 0.559 — barely above the 0.50 no-separation line).** The per-month ranking is decisive: the single highest-OOD month (2023-01, `maha` 11.90) loses — but the 2nd, 3rd, and 6th highest-OOD months (2024-12, 2023-06, 2022-05) are all *profit* months, and the **largest winner of the entire IS** (2024-04, +25.24 wpnl) sits *below the median* OOD distance. High OOD does not imply a loss; low OOD does not imply a win.

Every other separator also fails: ATR percentile AUC 0.362 (loss months are if anything *lower*-vol — the inverse of an "unseen-regime" intuition); BTC drawdown AUC 0.483 (no separation — consistent with primitive 9 being CLOSED); BTC vol-z AUC 0.590 (weak, the strongest of this set but far below 0.70).

### T4 — trade-level OOD: does a losing TRADE have a higher entry-bar OOD? (`loss_month_deep.py`; `T4_trade_ood_quartiles.csv`)

Month aggregation can mask a clean trade-level separator, so the same Mahalanobis OOD was computed **per trade** at the trade's entry bar (the trade `open_time` equals the entry candle's `close_time` — causal; reference = trailing 24-month window of bars closing strictly before entry).

| | mean entry-OOD | n |
|---|---:|---:|
| Losing trades | 3.395 | 100 |
| Winning trades | 3.383 | 71 |

**AUC (loser ranks higher) = 0.504 — no separation whatsoever.** Confirmed by the entry-OOD quartile split: the most-OOD quartile (Q4_high) has wpnl **+25.63** and 41.9% win rate — the most out-of-distribution trades are *fine*; the worst quartile by PnL is Q2 (−6.25 wpnl), a *middle* OOD bucket. The user's "unseen-regime" hypothesis fails at both the month level (T2/T3) and the trade level (T4).

### T5 — per-(symbol, direction) loss concentration (`loss_month_deep.py`; `T5_symbol_direction_cells.csv`)

| symbol | direction | n | weighted_pnl | win_rate |
|---|---:|---:|---:|---:|
| BCHUSDT | short | 47 | +44.83 | 0.426 |
| BCHUSDT | long | 36 | +31.78 | 0.583 |
| TRXUSDT | short | 43 | **−5.34** | 0.302 |
| TRXUSDT | long | 36 | **−2.01** | 0.389 |
| LDOUSDT | short | 6 | +2.33 | 0.333 |
| LDOUSDT | long | 3 | +6.60 | 0.333 |

The only genuine structural drag is **TRX, net-negative on BOTH directions**. But this is already-known (TRX is why iter-v3/049 raised TRX's ADX threshold, /061 raised TRX's vol-scale floor, /074 targeted TRX with the regime kill switch, /075 scoped the BTC-trend de-rate to TRX) — and it is a *symbol* problem, not a *regime/unseen-distribution* problem. A symbol-asymmetric drag is not what the /106 axis is about; the regime-conditional kill switch keyed on it (primitive 9) is CLOSED at the catalog level (/022, /074 — "no signal").

### T6/Q3b — trailing per-symbol hit-rate state (`loss_month_deep.py`)

For each trade, the win-rate of the last `K` closed trades of the same symbol (causal — only trades closing before the entry). Does a cold streak predict the next trade losing?

| K | AUC (low trailing hit-rate ranks next-loser high) |
|---|---:|
| 3 | 0.499 |
| 5 | 0.511 |
| 8 | 0.534 |

**No.** AUC 0.499–0.534. A trailing cold streak carries essentially no information about the next trade's outcome — trade outcomes on this roster are close to serially independent in sign.

### T7/T8 — the wide causal separator sweep — the last-chance check (`regime_final_check.py`; `T7_wide_regime_separators.csv`, `T8_separator_ranking.csv`)

To rule out that EDA 2 simply used the wrong variable or the wrong reference-window length, a wider battery of 11 causal separators was swept at month level — including BTC trailing return at 30/60/90d (directional bull/bear state), BTC trailing realized vol at 30/60d, BTC absolute 60d return (direction-agnostic regime intensity), symbol trailing return and ATR percentile, and the Mahalanobis OOD at **three** reference-window lengths (12 / 18 / 24 months):

| separator | AUC | \|AUC − 0.5\| |
|---|---:|---:|
| **btc_abs_ret_60d** (strongest) | **0.641** | **0.141** |
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

**The strongest separator out of 11 candidates is `btc_abs_ret_60d` at AUC 0.641 — below the AUC ≥ 0.70 bar for a usable causal detector.** The Mahalanobis OOD is essentially flat across all three reference lengths (12m: 0.533, 18m: 0.537, 24m: 0.559) — the 24-month length was not "the wrong reference"; the OOD axis simply carries no loss-vs-profit signal. **No causal regime variable cleanly separates the IS loss months.** This is the conclusive negative.

### T9 — the drawdown-brake counterfactual — does "stop when losing" help at all? (`regime_final_check.py`; `T9_drawdown_brake_counterfactual.csv`)

The user's "the model needs to stop" intuition, taken at face value, is a **trailing-equity drawdown brake**: kill every trade entered while the portfolio's trailing-equity drawdown (known from prior *closed* trades — past-only) exceeds a trigger. Full IS counterfactual over a trigger grid (/059 IS baseline: weighted_pnl +78.18, monthly Sharpe +1.0658):

| trigger (wpnl) | trades killed | kept wpnl | kept monthly Sharpe | Δ Sharpe |
|---:|---:|---:|---:|---:|
| 3.0 | 165 | −3.25 | −46.82 | **−47.89** |
| 5.0 | 164 | −6.79 | −4.93 | **−6.00** |
| 8.0 | 163 | −8.71 | −5.33 | **−6.40** |
| 10.0 | 162 | −11.53 | −7.17 | **−8.24** |
| 12.0 | 162 | −11.53 | −7.17 | **−8.24** |
| 15.0 | 99 | +17.09 | +0.52 | **−0.55** |

**Every trigger produces a NEGATIVE Δ Sharpe.** There is no threshold at which stopping during a drawdown improves the IS Sharpe. Two mechanisms, both fatal to the hypothesis:
1. **Drawdowns mean-revert.** EDA 3 Q2 measured it directly: trades entered while the portfolio trailing-DD ≥ 3 / 5 / 8 wpnl have *positive* cumulative wpnl (+50.5 / +53.2 / +42.5). The brake stops exactly the trades that recover the book. This is the **iter-v3/054 per-symbol drawdown-brake failure mode** (closed at /054) reproduced at the portfolio level.
2. **Early-arm deadlock.** The /059 IS book opens with losing months (2022-01/02). At low triggers the brake arms in the first months and — because the kill removes the trades that would have generated the recovery PnL — it can never see the equity recover to disarm. 165 of 171 trades killed at trigger 3.0. This is the `feedback_v3_oracle_eda_validity.md` STATEFUL-gate deadlock the /054 closeout flagged. A trailing-drawdown brake is structurally incapable of helping here.

### EDA verdict

The user's hypothesis — *the IS loss months are an out-of-distribution / unseen regime the model should detect and stop in* — is **falsified on three independent axes**:
1. **No OOD signature.** Mahalanobis OOD (the literal "unseen-distribution" statistic) does not separate loss months: month AUC 0.559, trade AUC 0.504, flat across 12/18/24-month reference windows.
2. **No regime separator at all.** The strongest of 11 causal regime separators is AUC 0.641 — below the 0.70 usable bar. There is no clean, causal, IS-detectable condition that the loss months share and the profit months do not.
3. **"Stop when losing" actively hurts.** A trailing-drawdown brake — the cleanest "stop" mechanism — yields a negative IS Sharpe delta at every trigger, because drawdowns mean-revert (stopping kills the recovery). The /054 brake failure mode, confirmed at portfolio level.

There is no genuine signature to build a gate on. The honest verdict is **NULL-AT-EDA**.

## Section 3 — Proposed Changes (the designated would-be detector — implementation spec, for an override-to-backtest only)

**Per the QR recommendation (NULL-AT-EDA), no `src/` change is proposed and no backtest is run.** This section exists so that, if the Phase-5.5 gate or the orchestrator overrides the recommendation, a complete and gate-able implementation spec exists. The EDA does **not** support running it.

**Designated would-be detector: a trailing-window Mahalanobis OOD kill gate (primitive 13).** This is the construction the user's hypothesis points at, and it is genuinely NEW vs every incumbent RiskV2 gate (Section 6 distinguishes it from the incumbents). Spec:

- **New `RiskV2Config` field** `enable_mahalanobis_ood_gate: bool = False` (default off — preserves all prior behavior), plus `maha_ood_ref_months: int = 24`, `maha_ood_cutoff: float` (the IS-calibrated threshold), `maha_ood_ridge: float = 1e-6`.
- **At `compute_features`-time** (snapshot discipline, like the incumbent z-score gate): for each symbol and each walk-forward month `M`, fit `mu_M, Sigma_M` on the trailing `maha_ood_ref_months` of that symbol's 14-`V3_FEATURE_COLUMNS` rows (the same window the LightGBM cell for month `M` trains on); store `Sigma_M⁻¹` (ridge-regularized: `Sigma += ridge · mean(diag(Sigma)) · I`).
- **At `get_signal(symbol, t)`**: compute `D = sqrt((x_t − mu_M)ᵀ Σ_M⁻¹ (x_t − mu_M))` for the entry bar `t`'s feature vector `x_t` (causal — `x_t` is a completed candle; `mu_M, Σ_M` use only data ≤ month `M`'s training-window end). If `D > maha_ood_cutoff`, return `NO_SIGNAL`.
- **Threshold calibration:** `maha_ood_cutoff` would be set to the IS distribution's 90th percentile of per-trade `D` (an a-priori percentile, not OOS-fitted). EDA T4 already computed the per-trade `D` distribution — the IS 90th percentile is ≈ 5.3 (Q4_high quartile lower edge).
- **One clean variable.** Model, features, label, universe stay /059-identical. No other RiskV2 gate is changed.

This spec is complete and would pass a Phase-5.5 gate on completeness. **It would not pass on merit** — the EDA (T4) shows the gate would kill the Q4_high OOD quartile, which carries +25.63 wpnl at a 41.9% win rate; the gate removes *profitable* trades. The pre-registered falsifiers in Section 4 would fire.

## Section 4 — Expected OOS Impact + Pre-Registered Numerical Falsifiers

### The QR recommendation — NULL-AT-EDA

No OOS impact is predicted because **no backtest is recommended.** The EDA conclusively shows there is no clean causal "unseen-regime" detector to build, and the cleanest "stop" mechanism (drawdown brake) is IS-negative at every trigger. Running a backtest of the designated Mahalanobis gate would spend compute to reproduce a documented failure mode (the gate removes the profitable Q4_high OOD quartile). Per `feedback_fail_fast.md` — the cheap-kill discipline established by the /094/095/096/098/099/100/103 fail-fast EDAs — an axis a committed IS-only EDA conclusively kills is closed at the EDA: no `fetch`, no runner change, no backtest, no Critic, no agent dispatch.

### Pre-registered numerical falsifiers (GATES — used only if a backtest is run despite the NULL-AT-EDA recommendation)

If the Phase-5.5 gate or orchestrator overrides and the designated Mahalanobis OOD gate (Section 3) is backtested, these falsifiers are pre-registered and evaluated at Phase 7 against the /059 anchor (IS monthly Sharpe +1.0894 / OOS +0.5791):

- **F1 — IS Sharpe non-improvement.** Fires if the gated IS monthly Sharpe ≤ +1.0894 (the /059 IS anchor). The EDA predicts this fires: the Mahalanobis gate removes the +25.63-wpnl Q4_high OOD quartile (T4), which *lowers* IS PnL.
- **F2 — OOS regression.** Fires if the gated OOS monthly Sharpe < +0.5791 (the /059 OOS anchor).
- **F3 — behavioral-effect miss.** The gate at the IS-90th-percentile cutoff is predicted to kill ≈ 10% of IS signals (≈ 17 of 171 IS trades) and a comparable OOS fraction. Fires if the observed kill count is < 8 or > 35 IS trades (the gate is mis-calibrated — too inert or too aggressive).
- **F4 — trade-rate floor.** Fires if bundle-level OOS trade count after gating < 60 (the gate over-kills below the trade-rate floor).
- **F5 — IS/OOS divergence (SUSPICIOUS).** Fires if the IS/OOS daily-Sharpe ratio falls outside [0.2, 5].

**Pre-registered prediction: F1 fires.** A backtest of the designated gate is predicted to close EXPLORATION-NEGATIVE by IS non-improvement — which is precisely why the QR recommendation is to not run it.

## Section 5 — Risk Mitigation (R1–R5, IS-calibrated, simulated effect)

The /106 axis **is itself** a risk-management iteration — its entire subject is a risk gate. The EDA's role is to verify, before any build, that the proposed risk gate would actually mitigate risk. It established the opposite: the candidate gates (Mahalanobis OOD kill, trailing-drawdown brake) do **not** mitigate the IS loss-month risk — the OOD gate removes profitable trades (T4) and the drawdown brake is IS-negative at every trigger (T9).

For the standing /059 risk stack that **remains in force unchanged** under the NULL-AT-EDA verdict:
- **R3 — feature z-score OOD gate** (`enable_zscore_ood=True`, `zscore_threshold=2.0`): the incumbent univariate OOD gate stays active. Note that EDA T2/T4 effectively also re-validate that an OOD construction (the *multivariate* Mahalanobis cousin of R3) carries no loss-month signal — consistent with R3 itself being a tail-safety gate, not a loss-month detector.
- **R1/R2/R4/R5** — all incumbent RiskV2 gates (BTC-trend kill, vol scaling, ADX, Hurst regime, low-vol filter) stay /059-identical. No gate is added, removed, or re-tuned.
- **The honest risk-management conclusion of /106:** the IS loss months are not a *detectable-and-stoppable* risk. They are a low-win-rate, mean-reverting drag distributed across regimes; the book *recovers* from its drawdowns (T9 Q2). The correct risk posture is to *not* add a stop that would interrupt the recovery — which is what NULL-AT-EDA delivers (zero change to the risk stack).

## Section 6 — Risk-Management Design (how the designated detector differs from the incumbent RiskV2 gates)

The brief was mandated to distinguish any /106 detector from the incumbent RiskV2 gates and to confirm it does not re-tread a closed gate. The designated Mahalanobis OOD gate (Section 3) **is** genuinely distinct — and the EDA's value is precisely that it tested this distinct, non-closed mechanism rigorously and found it carries no signal:

| Incumbent gate | Mechanism | Why the designated Mahalanobis gate is DIFFERENT |
|---|---|---|
| **R3 — feature z-score OOD** (`_zscore_ood`) | UNIVARIATE: fires if **any single** feature's \|z\| exceeds the threshold, against the **full static IS** window | The Mahalanobis gate is MULTIVARIATE (uses `Σ⁻¹`, the full covariance) — it detects OOD in the *joint / correlation* structure (a month OOD in the *combination* of features while every marginal sits at \|z\|<2). And it re-fits the reference to each month's **trailing 24-month training window**, not the static full IS — it measures drift relative to *what the current model actually saw*. A different statistic on a different reference set. |
| **Primitive 9 — regime-conditional kill switch** (`enable_regime_gate`) — **CLOSED at /022, /074** | BINARY kill keyed on **BTC** `drawdown_30d` / `vol_z` — hand-picked BTC scalars | The Mahalanobis gate keys on the **symbol's own 14-feature input vector** — the model's own input-space novelty, not a BTC scalar. EDA T2 confirms `btc_dd_30d` (AUC 0.483) and `btc_vol_z_30d` (AUC 0.590) separately fail — re-confirming primitive 9 is correctly closed, and that the Mahalanobis construction is a genuinely different signal (not a re-tread). |
| **Primitive 11 — per-symbol drawdown brake** (`enable_per_symbol_drawdown_brake`) — **CLOSED at /054 (deadlock)** | STATEFUL: pauses a symbol when its trailing-window weighted-PnL drawdown exceeds a threshold | The Mahalanobis gate is STATELESS at decision time (`D` is a pure function of the bar's features + the snapshot `mu/Σ`) — no closed-loop state, no deadlock surface. EDA T9 separately re-confirms the drawdown-brake mechanism is IS-negative — so the Mahalanobis gate is correctly *not* a drawdown brake. |
| **Primitive 12 — BTC-trend-regime size de-rate** (`enable_regime_size_scalar`) | Position-SIZE de-rate keyed on a BTC SMA-270 bull/bear classifier | The Mahalanobis gate is a binary KILL keyed on the symbol's feature-space OOD distance — a different signal and a different action (kill vs size de-rate). |

The designated detector is therefore a legitimate, non-closed, genuinely-NEW mechanism — which is exactly why it warranted the rigorous EDA it received. **The EDA's finding is that this genuinely-new mechanism, correctly distinguished from every incumbent, nonetheless carries no loss-vs-profit signal (AUC 0.559 / 0.504).** That is a NULL-AT-EDA on a properly-scoped, non-redundant axis — not a process gap.

## Section 7 — Pre-Registered Failure-Mode Prediction

In probability order:

1. **MODAL (predicted) — NULL-AT-EDA.** The deep IS-only EDA conclusively shows the IS loss months carry no clean causal "unseen-regime" signature (strongest of 11 separators AUC 0.641 < 0.70; Mahalanobis OOD AUC 0.559 month / 0.504 trade) and the cleanest "stop" mechanism (drawdown brake) is IS-negative at every trigger. No backtest is run. **This is the outcome** — see Section 8.
2. **If the orchestrator overrides and backtests the designated Mahalanobis gate — EXPLORATION-NEGATIVE by IS non-improvement (F1 fires).** The gate removes the profitable Q4_high OOD quartile (T4: +25.63 wpnl, 41.9% WR); the gated IS Sharpe is predicted to fall, not rise.
3. **Tail — a multi-seed Optuna interaction surprises.** Low-probability: the gate is a pure post-model overlay (it does not change the training objective or feature space), so it does not widen the Optuna search space — the /102/105 IS-collapse mechanism is structurally absent. But a kill gate does change the *trade roster* the per-symbol fits' walk-forward sees, so a small IS shift is possible. Still predicted to be a *negative* shift (F1).

**The honest meta-prediction.** The most informative reading of /106 is structural: the user's intuition that the loss months are a *detectable, stoppable* condition is, on this specific roster, empirically wrong — the loss months are a low-win-rate, regime-agnostic, *mean-reverting* drag. The book recovers from its drawdowns. The correct response is not a better detector; it is to recognize that a stop interrupts the recovery. NULL-AT-EDA is that recognition.

## Section 8 — Classification Taxonomy (LOCKED, disjunctive precedence)

Evaluated in precedence order; first match wins.

1. **BLOCKED** — Critic OVERALL=BLOCK. Not reached — no backtest, no Critic review (NULL-AT-EDA stops the iteration at the EDA).
2. **NULL-AT-EDA** — the deep, committed, IS-only EDA conclusively proves the axis dead before any backtest (the high bar reserved for a conclusive at-EDA kill). ✅ **MATCH.** Four committed scripts, 9 result tables: no causal regime separator reaches the AUC ≥ 0.70 usable bar (strongest 0.641); the Mahalanobis OOD the hypothesis literally points at scores AUC 0.559 (month) / 0.504 (trade), flat across 12/18/24-month references; the trailing-drawdown brake is IS-Sharpe-negative at every trigger. The hypothesis is falsified on three independent axes.
3. **NEGATIVE / SUSPICIOUS / INERT / PROMISING** — all require a backtest to evaluate. Not reached.

**Classification: NULL-AT-EDA.** No baseline change. `BASELINE_V3.md` stays canonical at `v0.v3-059` (IS monthly Sharpe +1.0894 / OOS +0.5791, 10-seed CONFIRMATION). No `src/` code is written — the model, features (`V3_FEATURE_COLUMNS` stays at 14), label, universe, and the RiskV2 stack are all bit-identical to /059; there is nothing to revert. `v0.v3-106` is a closeout marker only.

## Section 9 — Library Stack + Integration-Test Mandate

**No library stack and no integration test** — NULL-AT-EDA writes no `src/` code. The EDA scripts use only the already-pinned stack: `numpy 2.2.6`, `pandas 3.0.0`, `pyarrow 23.0.1`, plus `crypto_trade.config.OOS_CUTOFF_MS` and `crypto_trade.features_v3.V3_FEATURE_COLUMNS`. No new dependency. The Mahalanobis distance is a closed-form linear-algebra computation (`numpy.linalg.inv` + an `einsum` quadratic form) — no `mlfinlab` / `pypbo` / `fracdiff` involvement.

Were the designated gate (Section 3) ever built under an override, the integration-test mandate (`feedback_v3_methodology_axis_integration_test.md`) would apply: an end-to-end smoke test that the `RiskV2Wrapper` Mahalanobis snapshot is computed at the correct walk-forward boundary and a per-trade past-only causality test (the entry bar's `D` is bit-identical whether or not future bars are appended to the frame). Not applicable under the NULL-AT-EDA recommendation.

## Section 10 — QR Audit Trail

- **Axis origin:** USER-DIRECTED (2026-05-19, verbatim in Section 1). The /105 closeout Section 9 pre-registered iter-v3/106 as the user-directed risk-management axis and the /105 finding (binding constraint is downstream of the label, in the trade-construction / risk layer) directly motivated it. Per `feedback_v3_axis_selection_quant_discipline.md` the axis is QR-led with a committed `analysis/iteration_v3-106/*.py` EDA basis preceding this brief.
- **EDA commit:** `7b55698` — `analysis/iteration_v3-106/` (4 scripts: `loss_month_diagnostic.py`, `loss_month_separators.py`, `loss_month_deep.py`, `regime_final_check.py`; 9 result CSVs `T1`–`T9`, `T1b`).
- **Brief setup commit:** `81fd62b` — `briefs-v3/iteration_v3-106/research_brief.md` (the full 10-section brief; Section 4 carries the NULL-AT-EDA recommendation; Section 3 documents the designated would-be detector with a complete spec for an override-to-backtest). Setup SHA backfilled into this Section 10 at the immediately-following commit.
- **Designated would-be axis (for an override only):** the trailing-window Mahalanobis OOD kill gate (primitive 13) — full implementation spec in Section 3, pre-registered falsifiers in Section 4. The EDA does not support running it.
- **NO CHEATING:** `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` untouched. All Phase 1–5 EDA strictly IS-only (`open_time < OOS_CUTOFF_MS` for trades; `close_time < OOS_CUTOFF_MS` for the feature reference/test windows — each script asserts the invariant at load). The OOS roster and post-cutoff feature data were never read. The detector and threshold were calibrated only on the IS loss months. `V3_EXCLUDED_SYMBOLS` untouched. No `src/` code written.
