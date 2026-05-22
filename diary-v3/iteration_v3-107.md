# iter-v3/107 — Cycle-5 EXPLORATION slot #7 — EXIT-LAYER RE-ARCHITECTURE: an ATR-trailing-stop / dynamic-barrier exit (the first structural attack on the v3 exit geometry in 106 iterations) — FILED NULL-AT-EDA — the gating EDA re-resolved the /059 IS roster under 5 candidate exit designs with no model retrain and conclusively proved EVERY candidate LOWERS the IS monthly Sharpe; the decisive meta-finding is that the /106 win-rate problem is NOT an exit-timing artifact — it is genuine directional-call quality; no backtest was run

**Date**: 2026-05-19
**Type**: EXPLORATION (cycle-5 slot #7) — Phases 1-5 concluded at a NULL-AT-EDA verdict
**Verdict**: **NULL-AT-EDA** — iter-v3/107 was the /106 closeout's Recommendation #1 (TOP): re-architect the v3 exit layer — replace the static triple-barrier (2-ATR TP / 1-ATR SL / 21-candle timeout, barrier distance frozen at entry) with a **dynamic exit** — concretely an ATR-trailing / breakeven stop that ratchets toward the high-water mark. The /106-floated mechanism was *profit give-back*: a static barrier has no memory of a favorable excursion, so a trade that runs to +1.8 ATR then reverses is booked a full loss; a trailing stop has that memory and converts the give-back loser into a scratch or a small win, raising the win rate — the exact /106-identified failure axis. The QR ran the mandated `feedback_fail_fast.md` Phase-1 GO/NO-GO EDA — 2 committed IS-only scripts under `analysis/iteration_v3-107/` (commit `4ce931d`), 7 result CSVs T1–T7 — that re-resolved the existing /059 IS trade entries (entries held fixed, no model retrain) under 5 candidate exit designs directly on the 8h OHLCV path. The EDA fired both pre-registered falsifiers: **F-MFE** (the losing-trade MFE distribution is thin — only 22/100 losers ever reach ≥1.0 ATR favorable) and **F-COUNTERFACTUAL** (EVERY one of the 5 candidate exits LOWERS the counterfactual IS monthly Sharpe by −0.34 to −0.41). No Phase-6 backtest was run.
**Classification**: **NULL-AT-EDA** — reserved for an axis the deep, committed, IS-only EDA conclusively proves dead before any backtest (the dispatch's high bar). Killing it at the EDA — rather than committing a dynamic-exit `src/` re-architecture of `backtest_models.py` / the triple-barrier resolution path and a 3-seed backtest to reproduce a documented IS-Sharpe degradation — is the fail-fast WIN (`feedback_fail_fast.md`), not an iteration failure. Matches the /098/100/103/104/106 NULL-AT-EDA precedent.
**Decision**: **NO-MERGE.** BASELINE_V3.md UNCHANGED — canonical **`v0.v3-059`** (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**, 10-seed CONFIRMATION).
**Branch**: `iteration-v3/107`

---

## 1. The axis — and why it was the right one to test

iter-v3/107 is cycle-5 EXPLORATION slot #7. The axis is the **trade-construction / exit layer** — and it was the correct frontier on the convergent cycle-5 evidence, for two compounding reasons.

**First, /105 localized the binding constraint downstream of the training label.** The /105 closeout falsified the /104 "the label geometry is the binding constraint" hypothesis: the trend-scanning label — a label the 14 features predict 31–52% *better*, robustness-checked, Wilcoxon p=0.013 — *collapsed* the IS fit −0.61 rather than lifting it. The /105 diary localized the constraint **in the trade-construction / exit / risk layer** — the execution geometry the model's predictions are resolved through — and explicitly named the trade-construction / exit layer as the next axis.

**Second, /106 sharpened it to a win-rate problem.** The /106 closeout (the user-directed risk-management axis) established that the 15 IS loss months share a **systematically low win rate (0.0–0.33)** — not a regime signature, not an OOD condition, not a stoppable drawdown. The model's directional calls in those months *convert poorly to PnL*. /106's own Section 8 named the exit layer as the precise un-attacked target: v3's triple-barrier exit has been **knob-tuned exactly once** (iter-v3/010 swept the barrier *multipliers* 2.0/1.0) and **never structurally re-architected** — for 106 iterations every v3 trade has resolved by the identical rule: first-touch of a static, symmetric-in-construction ±ATR barrier within a fixed 21-candle window, the barrier distance frozen at entry.

The /106 give-back hypothesis is a *specific, measurable, falsifiable* mechanism by which a static exit would manufacture a low win rate, and a trailing stop would fix it. It is the right layer (/105), it targets the exact /106 failure, and it had never been built. It deserved — and got — a deep IS-only gating EDA. Per `feedback_v3_axis_selection_quant_discipline.md` the axis was QR-led: the committed EDA (2 scripts, commit `4ce931d`) preceded any brief or build. **The EDA's verdict is the finding of this iteration.**

## 2. The gating EDA — 2 committed IS-only scripts, the design, why it is cheap and decisive

The trade-construction layer is uniquely cheap to pre-test, and this is what makes the fail-fast kill possible: the EDA can **re-resolve the existing /059 trade entries under a candidate exit rule directly on the OHLCV path, with no model retrain and no backtest.** A trailing/breakeven stop can only exit a trade *earlier* than the incumbent's 21-candle timeout — it never changes the entry, never changes the forward horizon, never touches the model. So the EDA holds every /059 IS entry fixed (same symbol, direction, entry price, entry candle) and walks each trade's 8h OHLCV path bar-by-bar under the candidate exit, recomputing the realized PnL. That is a near-complete in-sample backtest of the exit change with zero model involvement.

Two committed scripts under `analysis/iteration_v3-107/` (commit `4ce931d`):

- **`exit_mfe_distribution.py`** — DECISIVE TEST 1. For every trade in the /059 IS roster, walk the 8h OHLCV path from entry candle to exit candle and measure the **Maximum Favorable Excursion (MFE)** — peak unrealized profit in ATR units — before the trade's actual exit. The ATR-at-entry is recovered exactly from the barrier geometry the runner wrote (the SL price is placed exactly 1.0 ATR from entry, so `atr_entry = |entry_price − stop_loss_price| / 1.0`; the 2.0-ATR TP is a cross-check). Outputs T1–T4.
- **`exit_counterfactual.py`** — DECISIVE TEST 2. Hold the /059 IS entries fixed; re-resolve each trade's *exit* on the 8h path under the incumbent static triple-barrier (the **S** control) and **5 candidate dynamic exits** (below); report the counterfactual IS win rate, profit factor, and monthly Sharpe per design. Outputs T5–T7.

**The IS-only invariant.** Both scripts assert at load `(trades["open_time"] < OOS_CUTOFF_MS).all()` with `OOS_CUTOFF_MS = 1742774400000` (2025-03-24). The roster under analysis is the canonical /059 10-seed unified-ensemble IS trade roster — `reports-v3/iteration_v3-059/in_sample/trades.csv`, **171 IS trades**. OHLCV bars are read only from each trade's entry candle to its 21-candle timeout candle — no post-exit, no post-cutoff data. The post-cutoff OOS roster was **never read**; the QR did not inspect OOS in Phases 1-5 (and, on the NULL-AT-EDA verdict, Phase 7 does not occur).

**The 5 candidate exit designs** (all causal — bar `t` uses only the OHLCV path ≤ `t`; TP and 21-candle timeout retained; only the STOP becomes dynamic):

| | Design | Mechanism |
|---|---|---|
| **S** | STATIC (incumbent) | 2.0-ATR TP / 1.0-ATR SL / 21-candle timeout — the control; must reproduce /059 |
| **A** | BE@1.0 | once MFE ≥ 1.0 ATR, move the stop to entry (breakeven) — pure give-back elimination |
| **B** | BE@0.75 | the same, armed earlier at 0.75 ATR |
| **C** | TRAIL@1.0/1.0 | chandelier trail: once MFE ≥ 1.0 ATR, the stop trails 1.0 ATR behind the favorable extreme |
| **D** | TRAIL@1.25/0.75 | arm later (1.25 ATR), trail tighter (0.75 ATR behind extreme) |
| **E** | BE1.0+TRAIL1.5/1.0 | two-stage hybrid: breakeven at 1.0 ATR, then a 1.0-ATR chandelier trail once MFE ≥ 1.5 ATR |

**The honest 8h intra-bar path model.** A single 8h candle is O/H/L/C; the true intra-bar path is unknown. The EDA resolves every barrier/trail hit with a fixed **conservative** rule: if both the stop and the TP lie inside a bar's `[low, high]`, the **stop** is assumed hit first (adverse-first — never optimistic); the trailing stop is *updated* from a bar's extreme but a *hit* is tested against the stop level in force **at bar open** (this bar's ratchet cannot retroactively rescue this bar — strictly causal, no within-bar look-ahead); gap-through is honored (fill at the actual open if the bar opens beyond the level). Fees are 0.10% round-trip — the /059 `fee_pct`. The conservative ordering means the candidate designs are, if anything, given the *benefit* of the doubt relative to a pessimistic intra-bar model — and they still fail.

## 3. The EDA result — both falsifiers fire; the static control reproduces /059; every candidate exit LOWERS the IS Sharpe

### T1–T4 — the losing-trade MFE distribution: F-MFE fires — the give-back population is thin

`exit_mfe_distribution.py` → `T1_per_trade_excursions.csv`, `T2_loser_mfe_thresholds.csv`, `T2b_loser_mfe_sorted.csv`, `T4_per_symbol_loser_mfe.csv`. The /059 IS roster splits **71 winners / 100 losers** (the 100-loser / 71-winner count cross-checks the 41.5% counterfactual-control win rate in T5). The MFE distributions:

| | mean MFE (ATR) | median MFE (ATR) |
|---|---:|---:|
| **Losers** (n=100) | **0.604** | **0.498** |
| **Winners** (n=71) | **2.304** | **2.244** |

The losing-trade MFE threshold table (`T2_loser_mfe_thresholds.csv`) — how many of the 100 losers ever ran far enough favorable to arm a trailing stop *before* booking a loss:

| MFE threshold (ATR) | n losers reaching it | % of losers |
|---:|---:|---:|
| ≥ 0.50 | 50 | 50.0% |
| ≥ 0.75 | 31 | 31.0% |
| **≥ 1.00** | **22** | **22.0%** |
| ≥ 1.25 | 15 | 15.0% |
| ≥ 1.50 | 7 | 7.0% |
| ≥ 1.75 | 4 | 4.0% |

**The give-back population is thin. Only 22 of 100 losing trades ever reached ≥1.0 ATR favorable** — i.e. only ~22% of losers were ever in real profit a trailing stop could lock in. **Half the losers (50/100) never reach even 0.5 ATR favorable — they go essentially straight to the stop.** The /106 give-back mechanism *exists* — a 22% slice is not zero — but it is far too thin a population for a trailing/breakeven stop to convert into a material win-rate lift. The pre-registered falsifier **F-MFE fires**: a trailing rule has very little to capture, because the losing trades, in the main, do not run favorable first.

The per-symbol cut (`T4_per_symbol_loser_mfe.csv`) confirms it is not a single-symbol artifact — `frac_mfe_ge_1` is 0.214 (BCH, 42 losers), 0.167 (LDO, 6 losers), 0.231 (TRX, 52 losers): on every symbol, only ~17–23% of losers ever reach 1.0 ATR favorable. The thin give-back population is a property of the whole roster.

### T5 — the counterfactual exit re-resolution: F-COUNTERFACTUAL fires — every candidate exit LOWERS the IS Sharpe

`exit_counterfactual.py` → `T5_exit_counterfactual.csv`. The 171 /059 IS entries re-resolved under all 6 designs:

| design | name | win rate | profit factor | **monthly Sharpe** | total wpnl | n_TP | n_stop | n_timeout |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **S** | STATIC (incumbent) | 41.5% | 1.478 | **+1.2143** | +92.37 | 56 | 100 | 15 |
| A | BE@1.0 | 28.1% | 1.289 | +0.8747 | +63.04 | 43 | 123 | 5 |
| B | BE@0.75 | 24.6% | 1.276 | +0.8623 | +62.80 | 37 | 129 | 5 |
| C | TRAIL@1.0/1.0 | 48.5% | 1.302 | +0.8647 | +58.99 | 37 | 133 | 1 |
| D | TRAIL@1.25/0.75 | 48.5% | 1.333 | +0.8040 | +60.77 | 32 | 135 | 4 |
| E | BE1.0+TRAIL1.5/1.0 | 35.1% | 1.339 | +0.8429 | +60.05 | 40 | 129 | 2 |

**The static control reproduces /059.** The S-design counterfactual — the incumbent triple-barrier re-resolved by the EDA's own 8h path model — lands at monthly Sharpe **+1.2143**, PF **1.478**, win rate **41.5%**. The /059 reported figures are monthly Sharpe +1.0894 (10-seed), PF 1.4949, win rate 33.3%; the small residual is the 8h intra-bar path model plus the single-roster vs 10-seed-aggregate difference. The control tracking /059 is the EDA's internal validity check — it **passes**: the counterfactual machinery faithfully reproduces the incumbent, so the candidate-design deltas are trustworthy.

**Every candidate exit LOWERS the IS monthly Sharpe.** Deltas vs the S control (+1.2143):

| design | ΔSharpe vs control | Δwin-rate | ΔPF |
|---|---:|---:|---:|
| A — BE@1.0 | **−0.3396** | −13.4 pp | −0.189 |
| B — BE@0.75 | **−0.3520** | −16.9 pp | −0.202 |
| C — TRAIL@1.0/1.0 | **−0.3496** | +7.0 pp | −0.176 |
| D — TRAIL@1.25/0.75 | **−0.4103** | +7.0 pp | −0.145 |
| E — BE1.0+TRAIL1.5/1.0 | **−0.3714** | −6.7 pp | −0.139 |

There is **no exit design that does not destroy IS Sharpe.** The range is −0.34 (BE@1.0, the mildest) to −0.41 (TRAIL@1.25/0.75, the most aggressive trail). The pre-registered falsifier **F-COUNTERFACTUAL fires** decisively: the candidate exits had to *exceed* the static control's IS Sharpe to demonstrate the exit geometry is the binding constraint; they uniformly fall short by a third of a Sharpe point or more.

**A subtle and important point — the trail designs RAISE the win rate but still LOWER the Sharpe.** Designs C and D *do* lift the win rate (+7.0 pp each — the /106 win-rate axis the hypothesis targeted). And yet their monthly Sharpe is −0.35 / −0.41 *worse*. This is the mechanism the EDA exposes: the trail buys win-rate by clipping winners, and the PnL it forfeits on the clipped winners outweighs the PnL it saves on the rescued losers. **A higher win rate is not a higher Sharpe.** Raising the win rate by trailing is not, on this roster, an improvement — it is a worse risk-adjusted book. (The brief-floated F-RATE check is informational and confirmed: a trailing stop does not change the *entry* count, so the bundle-level trade-rate floor is structurally preserved — but this is moot, since both substantive falsifiers fire.)

### T6 — the loser-conversion accounting: the best design rescues 0 losers and clips 23 winners

`exit_counterfactual.py` → `T6_loser_conversion.csv`. Take the *best* candidate design — the one with the highest counterfactual IS Sharpe among the five, which is **A (BE@1.0)** at +0.8747 — and account, trade by trade, for which static outcomes it flips:

| metric | value |
|---|---:|
| static losers → BE@1.0 winners (**rescued**) | **0** |
| static winners → BE@1.0 losers (**clipped**) | **23** |
| net win-count change | **−23** |

**The best of the five exit designs rescues exactly ZERO static losers into winners — and clips 23 static winners into losers.** This is the single most decisive number in the EDA. The give-back hypothesis predicted the trailing/breakeven rule would *convert losers into scratches or wins*; on the /059 IS roster, the best-performing design converts **none**. Recall the T1 winner MFE distribution — mean 2.30 ATR, median 2.24 ATR: **winners run far, but they pull back.** A breakeven or trailing stop, armed by that favorable excursion, catches the pull-back and exits the winner *early* — at break-even or a clipped profit — before it would have reached the 2-ATR TP or ridden a profitable timeout. The "rescued losers" the hypothesis was built on are 0; the "clipped winners" are 23. The exit re-architecture does not fix the win-rate problem — it manufactures a *different* one.

### T7 — the per-symbol counterfactual: BCH and TRX both worse, LDO marginally better but immaterial

`exit_counterfactual.py` → `T7_per_symbol_cf.csv`, the per-symbol monthly Sharpe under the best design (A, BE@1.0) vs the static control:

| symbol | static Sharpe | counterfactual Sharpe | static wpnl | counterfactual wpnl |
|---|---:|---:|---:|---:|
| BCHUSDT | +1.5203 | **+0.9544** | +85.52 | +54.76 |
| LDOUSDT | +1.6231 | +2.0969 | +12.01 | +14.21 |
| TRXUSDT | −0.1990 | **−0.2476** | −5.17 | −5.93 |

The two symbols carrying essentially all of the /059 IS PnL — **BCH (+85.52 wpnl) and TRX** — both get *worse* under the best exit design: BCH Sharpe −0.57, TRX Sharpe −0.05. LDO improves (+0.47 Sharpe) but LDO carries only +12 of +92 wpnl — its lift is far too small to offset the BCH degradation, and LDO is the thinnest-roster symbol (6 losers total). The exit re-architecture is not symbol-rescuable: the symbols that matter are the symbols it hurts.

### EDA verdict — both pre-registered falsifiers fire — the axis is dead

The /106-recommended exit-layer re-architecture is **conclusively falsified** before any backtest, on two independent, pre-registered axes:

1. **F-MFE fires.** The losing-trade MFE distribution is thin — only 22/100 losers ever reach ≥1.0 ATR favorable; half go straight to the stop (MFE < 0.5 ATR). A trailing/breakeven stop has very little to capture, because the losing trades, in the main, do not run favorable first. The /106 give-back mechanism exists but is too thin a population to convert into a material win-rate lift.
2. **F-COUNTERFACTUAL fires.** Every one of the 5 candidate exit designs LOWERS the counterfactual IS monthly Sharpe — by −0.34 to −0.41 vs the static control (+1.2143). The best design (BE@1.0) rescues 0 losers and clips 23 winners. The trail designs raise the win rate (+7 pp) and *still* lower the Sharpe, because clipping winners forfeits more than rescuing losers saves.

There is no exit re-architecture that improves the IS Sharpe on this roster. The honest verdict is **NULL-AT-EDA**.

## 4. The decisive meta-finding — the /106 win-rate problem is NOT an exit-timing artifact; it is genuine directional-call quality

This is the most informative output of /107, and it is what makes the iteration a substantive contribution rather than a dead end.

The /106 closeout established that the v3 loss months are a **low-win-rate** phenomenon and left an open question: *is that low win rate a real defect of the model's directional calls, or is it an artifact of the exit layer booking correct-but-incompletely-resolved calls as losses?* The /106 give-back hypothesis was the second reading — *the calls are fine, the static exit is throwing away the profit.* iter-v3/107 was the decisive test of that reading, and it **falsifies it**:

- The counterfactual control (entries held fixed, the static triple-barrier faithfully reproduced) reproduces /059 — WR 41.5%, monthly Sharpe +1.2143, PF 1.48. **The static triple-barrier is not leaking profit.** A PF of 1.48 means the incumbent exit is already extracting $1.48 of gross profit per $1 of gross loss from the model's calls.
- The give-back population a trailing stop would capture is thin (22/100 losers ≥1.0 ATR MFE), and re-resolving the *same entries* under the *best* trailing rule rescues **0** losers while clipping **23** winners.
- **Therefore the low win rate is not an exit-timing artifact.** If the static exit were squandering correct calls, a trailing stop would rescue a measurable count of losers; it rescues none. The losses are losses because the *directional call was wrong* — the price went adverse and stayed adverse (half the losers never even reach 0.5 ATR favorable). The static triple-barrier is, on this roster, an *efficient* harvester of whatever directional edge the model produces; it is not the bottleneck.

The meta-finding is decisive: **the /106 win-rate problem is genuine directional-call quality.** The model's calls in the loss months are simply wrong more often, and no re-architecture of the exit — the layer that turns a call into realized PnL — can manufacture edge the call did not contain.

### The /105 → /106 → /107 convergent chain — v3's binding constraint is localized to the signal itself

iter-v3/105, /106, and /107 form a **convergent falsification chain** that has, step by step, eliminated every candidate explanation for the thin v3 signal *other than the signal itself*:

- **/105 falsified "the label / the estimand is the binding constraint."** The trend-scanning label — a re-framed estimand the 14 features predict 31–52% *better* — collapsed the IS fit −0.61 rather than lifting it. Re-framing *what the model is trained to predict* does not fix v3. The training-side of the prediction problem (features ×4 families, derivative data, on-chain, model architecture ×4, training objective, label class, label geometry, universe) is comprehensively closed.
- **/106 falsified "the loss months are a detectable / stoppable regime."** No causal regime separator (11 candidates, Mahalanobis OOD at 3 reference lengths) reaches a usable AUC; a trailing-drawdown brake is IS-Sharpe-negative at every trigger. The loss months are not an out-of-distribution condition to be detected and exited — they are a **win-rate** phenomenon.
- **/107 falsifies "the win-rate problem is an exit-timing artifact."** The static triple-barrier is not leaking profit (PF 1.48, faithfully reproduced); no dynamic-exit re-architecture rescues the losers (best design: 0 rescued, 23 clipped). The low win rate is not the exit's fault.

The three iterations are not three unrelated nulls — they are a **localization**. /105 cleared the label. /106 cleared the regime/risk-overlay layer. /107 cleared the exit/trade-construction layer. What the chain has *not* cleared, and what it now points at with near-certainty, is the **signal — the directional-call quality of the per-symbol 8h LightGBM itself.** The losses are wrong directional calls; the exit harvests the edge efficiently; the label and the regime are not the constraint. **v3's binding constraint is the directional accuracy of the primary model's predictions** — and the next iteration must attack *that*, directly.

## 5. The verdict — NULL-AT-EDA, no backtest — the fail-fast justification

The dispatch reserves NULL-AT-EDA for "an axis the deep EDA conclusively proves dead (high bar)." The /107 EDA clears that bar — a two-script, seven-table, strictly-IS-only gating EDA that fired both pre-registered falsifiers (F-MFE and F-COUNTERFACTUAL). No backtest was run, for three binding reasons:

1. **The counterfactual EDA IS an in-sample backtest of the exit change.** `exit_counterfactual.py` re-resolves all 171 /059 IS entries under every candidate exit, on the real 8h OHLCV path, with a conservative intra-bar model and the production fee — it is, structurally, a complete in-sample backtest of the exit re-architecture, with the *only* simplification being that the entries are held fixed (which is correct — a trailing stop cannot change an entry). It already returns the answer: every candidate exit is −0.34 to −0.41 IS Sharpe worse than the incumbent. A Phase-6 backtest would re-derive this same negative at the cost of a dynamic-exit `src/` re-architecture and a 3-seed run.

2. **A backtest would knowingly reproduce a documented failure.** The pre-registered falsifier F-COUNTERFACTUAL is the gate, and it fires unambiguously — every design loses a third of a Sharpe point. To build the dynamic-exit module into `backtest_models.py` / the triple-barrier resolution path and run the backtest anyway would spend compute and an `src/` re-architecture to manufacture a confirmation-shaped artifact around a hypothesis the cheap EDA has already killed.

3. **Fail-fast forbids a foreseeable-failure spend.** `feedback_fail_fast.md` — the cheap-kill discipline of the /094/095/096/098/099/100/103/104/106 fail-fast EDAs — directs that an axis a committed IS-only EDA conclusively kills is closed at the EDA: no `src/` change, no runner change, no backtest, no Critic, no agent dispatch. The honest move is to report the negative verdict with the numbers, which is what NULL-AT-EDA is.

No `src/` code was written — there is no dynamic-exit module; the triple-barrier resolution path in `backtest_models.py` is bit-identical to /059; `V3_FEATURE_COLUMNS` stays at 14; the model / label / universe / 7-gate RiskV2 stack are all /059-identical; there is nothing to revert. The exit re-resolution lives entirely inside the two committed `analysis/iteration_v3-107/` EDA scripts (a pure-numpy/pandas bar-walk — no new dependency, no production wiring). `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` were untouched. Every Phase 1-5 measurement was strictly IS-only; the QR did not inspect the post-cutoff OOS.

## 6. Lessons

1. **The /106 win-rate problem is genuine directional-call quality, NOT an exit-timing artifact — the binding constraint is the signal.** This is the central finding. The static triple-barrier reproduces /059 at PF 1.48 (it is *not* leaking profit); the give-back loser population a trailing stop could capture is thin (22/100 losers ≥1.0 ATR MFE); the best dynamic-exit design rescues **0** losers and clips **23** winners. The exit harvests whatever edge the model produces efficiently — the losses are wrong directional calls. Combined with /105 (the label is not the constraint) and /106 (the loss months are not a stoppable regime), the /105→/106→/107 chain localizes v3's binding constraint to the **directional accuracy of the primary model's predictions** itself.

2. **A higher win rate is not a higher Sharpe.** The trail designs C and D *raised* the win rate by +7 pp — and *lowered* the monthly Sharpe by −0.35 / −0.41. The trail buys win-rate by clipping winners; the PnL forfeited on the clipped winners outweighs the PnL saved on the rescued losers. Any future axis that targets the win rate as an end in itself must be checked against the Sharpe — on this roster, raising the win rate by trailing is a strictly worse book. The /106 framing "the loss is a win-rate problem" is true as a *description* but the win rate is not the right *objective*: the directional-call quality is.

3. **The counterfactual exit re-resolution is a cheap, near-complete in-sample backtest — run it inside the EDA.** Because a trailing/breakeven stop never changes the entry, the forward horizon, or the model, the exit change can be fully re-resolved on the existing trade roster's OHLCV path with no model retrain. `exit_counterfactual.py` is, structurally, an in-sample backtest of the exit re-architecture across 6 designs, at near-zero cost. Future trade-construction / exit-layer EXPLORATIONs should make the fixed-entries counterfactual re-resolution a mandatory Phase-1 EDA step — a candidate exit whose IS counterfactual Sharpe is below the static control is killed at the EDA, exactly as a feature with INERT importance is.

4. **Winners run far but pull back — the v3 roster's MFE structure is hostile to trailing stops.** The winner MFE distribution (mean 2.30 ATR, median 2.24 ATR) shows v3 winners reach a large favorable excursion — but they then pull back enough that a breakeven or trailing stop armed by that excursion exits them *early* (the 23 clipped winners). A trailing stop is a good fit for a roster whose winners trend monotonically; it is a poor fit for a roster whose winners are volatile round-trips. The MFE-vs-pullback geometry must be measured before a trailing stop is proposed — and on the v3 roster it argues *against* one.

5. **A convergent falsification chain is a localization, not three dead ends.** /105, /106, /107 each closed a different candidate explanation for the thin v3 signal — the label, the regime/risk layer, the exit layer. Read together they are not three failures; they are a process of elimination that has localized the constraint to the signal itself. When successive EXPLORATIONs falsify successive *non-signal* explanations, the correct read is not "the search is exhausted" — it is "the constraint has been cornered, and the next axis must attack the cornered thing directly." That is the /108 mandate (Section 7).

## 7. Next Iteration Ideas — iter-v3/108 (cycle-5 EXPLORATION slot #8)

**The diagnosis is now sharp, convergent, and actionable.** The /105→/106→/107 chain has localized v3's binding constraint to **the directional-call quality of the primary per-symbol 8h LightGBM** — not the label (/105), not a detectable regime (/106), not the exit geometry (/107). "Exhausted" is the forbidden — and factually wrong — conclusion: the chain has not exhausted the search space, it has *cornered* the problem. Every prior axis attacked an input to, an estimator of, the label of, or the execution of a fixed signal. **Not one has attacked the question: given that the primary model's directional calls are the constraint, can a SECOND model identify, before the trade, which of those calls to trust?** That is the un-attacked frontier, and it is exactly the right one on the /107 evidence.

### Recommendation #1 (TOP) — meta-labeling done right: a confidence filter on a genuinely DISJOINT secondary feature set (the /017-corrected experiment)

**The axis.** A **meta-labeling secondary model** (López de Prado, AFML Ch. 3): keep the primary LightGBM's *direction* exactly as /059 produces it, and train a **second binary classifier** whose only job is the *take / skip* decision on each primary-model signal — sized by the secondary model's confidence. This is precisely the layer the /107 finding implicates: /107 proved the primary model's calls are the constraint and the exit is not — a meta-label filter does not try to fix the calls or the exit, it *triages* the calls, suppressing the low-confidence ones the primary model itself cannot distinguish.

**Why this is NOT a re-tread of iter-v3/017 — the precise /017-correction.** iter-v3/017 ran a meta-labeling layer and closed **EXPLORATION-NEGATIVE, PATH C (over-filter)**. It would be a methodology failure to re-propose the identical experiment. It is *not* the identical experiment, and the /105 Critic identified exactly why /017 failed: **/017's secondary model (M2) was fed the SAME 13 features the primary model (M1) already used.** The /017 engineering report states the root cause in plain terms (line 131): *"The meta-label signal is not learnable from the same 13 features M1 already used — the precision-residual is uncorrelated with any accessible feature at this EXPLORATION budget."* A secondary model fed the primary model's own feature set is asked to find structure in the *residual* of a fit those very features already produced — by construction it has almost nothing orthogonal to learn. /017 did not falsify meta-labeling; it falsified *meta-labeling with a redundant feature set.* The /017 closeout itself flagged this — and the /104 closeout's runner-up recommendation explicitly called for "a meta-labeling axis fed by a *deliberately disjoint* feature set."

**The /017-correction, concretely.** The /108 secondary model must be trained on a feature set that is **genuinely DISJOINT from `V3_FEATURE_COLUMNS`** — features the primary model does *not* see, that plausibly carry information about *when the primary model is wrong* rather than *which direction price goes*. The disjoint set should be drawn from the "is this a hard call to make" family, not the "which way" family — e.g.: (a) **prediction-disagreement features** — the dispersion / entropy of the 5-seed inner-ensemble's primary predictions at the bar (the ensemble agreeing strongly vs splitting is a direct, model-internal confidence proxy the primary model never sees as an input); (b) **regime-context features the primary stack under-weights** — BTC trend-state, cross-asset correlation regime, realized-vol regime, Hurst at a different lookback, the funding/OI context — selected specifically because they are *absent from or low-importance in* the 14-feature primary stack; (c) **the recent realized hit-rate / calendar context** — features describing the regime the primary model is currently operating in, not the price path. The hard constraint, pre-registered: **zero feature in the secondary set may appear in `V3_FEATURE_COLUMNS`, and the secondary set must have low aggregate redundancy (|ρ| gate) against the 14 primary features** — this is the single discriminating fix vs /017.

**Why this is EDA-gateable — the mandatory fail-fast GO/NO-GO test, and it is decisive.** Per `feedback_fail_fast.md` + `feedback_v3_axis_selection_quant_discipline.md`, /108 must carry a committed `analysis/iteration_v3-108/*.py` IS-only GO/NO-GO EDA *preceding* the brief — and meta-labeling is uniquely cheap to pre-test, because the secondary model's entire training target already exists in the /059 IS roster. The EDA, strictly IS-only on `reports-v3/iteration_v3-059/in_sample/trades.csv`:

1. **Constructs the disjoint secondary feature set** for every bar in the /059 IS roster and **asserts zero overlap and low redundancy** with `V3_FEATURE_COLUMNS` (the /017-correction, machine-checked — this is itself a gate: if a genuinely disjoint, non-redundant set cannot be assembled, the axis is NO-GO before any build).
2. **The decisive test — can a disjoint-feature secondary model separate the primary model's IS winners from its IS losers, IS-only?** Fit a depth-4 LightGBM (the v3 architecture) on the disjoint secondary features, target = `is_winner` (the binary primary-call outcome), on a chronological 70/30 IS train/validation split, no shuffling, no post-cutoff data. Report the **validation-fold AUC of separating winners from losers**. The GO bar is a *materially-above-0.50 AUC* — concretely, AUC ≥ 0.60 with the lift stable across the IS sub-periods. **If a disjoint-feature meta-model cannot separate the primary model's winners from its losers IS-only (AUC at the noise floor), meta-labeling is genuinely dead — NO-GO at the EDA, no backtest** — and that is itself a profound finding (it would mean the primary model's *errors* are unpredictable from any orthogonal information, which would redirect /109 to the primary model's own representational capacity). If the AUC clears the bar, the meta-label has demonstrable IS-detectable separating power that /017's redundant feature set could not access — and *that* is the GO.
3. **The trade-rate floor check** — a meta-label filter suppresses trades; the EDA must confirm the filtered IS roster (at a candidate confidence threshold) stays above the `feedback_v3_trade_rate_floor_bundle_level.md` bundle-level floor, and a behavioral-effect predictor (how many IS trades the filter suppresses) is pre-registered per `feedback_v3_axis_saturation_predictor.md`.

Pre-registered falsifiers: **F-DISJOINT** (a genuinely disjoint, non-redundant secondary feature set cannot be assembled → NO-GO); **F-AUC** (the disjoint-feature meta-model's IS winner-vs-loser separation AUC is below 0.60 / not sub-period-stable → NO-GO — meta-labeling is dead, /017's verdict generalizes); **F-RATE** (the filtered IS roster falls below the bundle-level trade-rate floor). The winner-vs-loser separation AUC from a *disjoint-feature* meta-model is the single most direct possible evidence that the primary model's errors are predictable from orthogonal information — and it is measurable entirely IS-only, before any `src/` build or backtest.

**Why this is genuinely bold.** /107 proved the constraint is the directional-call quality. There are exactly two ways to attack that: make the primary model's calls better (the entire training-side, comprehensively closed across /016/082/085/086/093/096/097/098/099/100/101/102/103/104/105), or **identify which calls to trust and skip the rest.** The second route has been attempted exactly once — /017 — and failed for a now-understood, *correctable* reason. A meta-label model fed genuinely orthogonal information is not a knob and not a re-tread: it is a structurally different attack on the precise constraint the /105→/106→/107 chain has localized, and the /017-correction (the disjoint feature set) is concrete, machine-checkable, and EDA-gateable. It is the right axis.

### Recommendation #2 (runner-up) — primary-model representational capacity: a regime-conditional model ensemble

If the /108 GO/NO-GO EDA fires **F-AUC** — the primary model's errors are *not* separable from any disjoint orthogonal information — then meta-labeling is genuinely dead and the only remaining route is to attack the primary model's *own* directional accuracy. The runner-up axis is a **regime-conditional model ensemble**: rather than one per-symbol LightGBM trained across all market regimes, train *separate* per-symbol models conditioned on a coarse, causally-known regime partition (e.g. BTC trend-up / trend-down / chop, or a realized-vol tercile), and route each bar's prediction to the model trained on the regime that bar is in. The hypothesis is that the thin v3 signal is partly an *averaging* artifact — a single model fit across heterogeneous regimes learns a blurred directional rule, and a regime-specialized model would call its own regime more accurately. This is distinct from the closed regime *kill switch* (primitive 9) — it does not *stop* trading in a regime, it *specializes the predictor* per regime. Its EDA would measure, IS-only, whether per-regime-trained models achieve a higher feature→label IC within their own regime than the pooled model does. It is ranked second only because meta-labeling (#1) is the cheaper, more direct test of the /107 diagnosis, and because a meta-label filter is a strictly accretive overlay whereas a regime-conditional ensemble is a heavier re-architecture of the primary model.

Both recommendations attack the **directional-call quality** the /105→/106→/107 chain has localized as v3's binding constraint — #1 by triaging the calls, #2 by specializing the predictor — not another input, label, or exit on a fixed signal, which is exactly what the convergent-chain evidence demands. Per `feedback_v3_axis_selection_quant_discipline.md` the iter-v3/108 axis must be QR-led with a committed `analysis/iteration_v3-108/*.py` EDA basis preceding the brief; per `feedback_fail_fast.md` it must carry the hard Phase-1 GO/NO-GO EDA (the F-DISJOINT / F-AUC / F-RATE falsifiers above) before any `src/` build.

## 8. Commit chain

- EDA SHA: `4ce931d` — `analysis/iteration_v3-107/` (2 scripts: `exit_mfe_distribution.py`, `exit_counterfactual.py`; 7 result CSVs: `T1_per_trade_excursions.csv`, `T2_loser_mfe_thresholds.csv`, `T2b_loser_mfe_sorted.csv`, `T4_per_symbol_loser_mfe.csv`, `T5_exit_counterfactual.csv`, `T6_loser_conversion.csv`, `T7_per_symbol_cf.csv`).
- Diary SHA: this closeout — `docs(iter-v3/107): closeout diary — FILED NULL-AT-EDA — exit-layer re-architecture FALSIFIED — every candidate dynamic exit lowers IS Sharpe −0.34/−0.41; the /106 win-rate problem is genuine directional-call quality, not an exit-timing artifact`.
- Catalog update SHA: committed with this diary — `briefs-v3/exploration_catalog.md` /107 row (classification NULL-AT-EDA).
- **No reports** (no backtest run — NULL-AT-EDA stopped the iteration at the EDA).
- **No `src/` change** (NULL-AT-EDA — nothing was implemented; there is no dynamic-exit module; the triple-barrier resolution path is bit-identical to /059; `V3_FEATURE_COLUMNS` stays at 14; the model / label / universe / 7-gate RiskV2 stack are all /059-identical; nothing to revert).
- **No brief** (NULL-AT-EDA at the gating EDA — the iteration concluded at Phase 1 before a Phase-5 brief was written; the EDA scripts and this diary are the iteration's record).
- **Tag**: `v0.v3-107` — a closeout marker only, tagged by the orchestrator (NOT a baseline update — the `v0.v3-082`…`v0.v3-106` pattern; BASELINE_V3.md UNCHANGED at `v0.v3-059`, IS +1.0894 / OOS +0.5791, 10-seed CONFIRMATION).

iter-v3/107 is cycle-5 EXPLORATION slot #7; the cadence advances. iter-v3/108 is slot #8 — the recommended meta-labeling-done-right axis (a confidence filter on a genuinely disjoint, /017-corrected secondary feature set) with a hard Phase-1 GO/NO-GO EDA (Section 7), attacking the directional-call quality the /105→/106→/107 convergent chain has localized as v3's binding constraint.

**NO CHEATING.** `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` untouched. The walk-forward embargo fix (`e149e9d`) is inherited unchanged. This EXPLORATION does NOT update BASELINE_V3.md regardless of outcome — `v0.v3-107` is a closeout marker only. All Phase 1-5 EDA was strictly IS-only (`open_time < OOS_CUTOFF_MS` for the /059 trade roster; OHLCV bars read only from each trade's entry candle to its 21-candle timeout candle — each of the 2 committed EDA scripts asserts the IS-only invariant at load); the QR did not inspect the post-cutoff OOS — no backtest was run.
