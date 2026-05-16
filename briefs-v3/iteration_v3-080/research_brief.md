# iter-v3/080 — Research Brief

**Cycle 2 EXPLORATION #10 of 10 — the FINAL cycle-2 EXPLORATION. Axis: PASSIVE-DIAGNOSTIC — persist the per-trade M1 `confidence` scalar to `trades.csv` + emit `confidence_distribution.csv` (bit-identical trade roster).**

---

## Section 0 — Data Split Declaration

The sacred constants are **UNCHANGED**:

```
OOS_CUTOFF_DATE = 2025-03-24       # IMMUTABLE
training_months = 24                # IMMUTABLE
```

- **IS window**: earliest available data per symbol → 2025-03-24. The QR uses ONLY IS data in Phases 1–5.
- **OOS window**: 2025-03-24 → data extent (~2026-05). The QR sees OOS results for the first time in Phase 7.
- **Walk-forward**: `generate_monthly_splits` applies `compute_embargo_candles(10080, 480) = 22` candles; `train_end_ms = test_start_ms − embargo_ms`. POST-FIX state (`e149e9d`) — the lookahead bug is FIXED in this worktree (confirmed by the /074–/079 Critics; `feedback_v3_walkforward_lookahead_bug.md` corrected at the /079 closeout).
- **Universe**: BCH, LDO, TRX (`V3_MODELS` unchanged; `REQUIRED_GAP = 66 = (21+1) × 3`).
- **No `start_time` change.** The backtest runs from the earliest available data.

### RE-ANCHORING (Critic /077 Rec #1 — adopted at the /077 closeout; re-stated for /080)

The frozen iter-v3/060 EXPLORATION-MODE anchor (IS +0.8325 / OOS +0.1403) is **STALE**. iter-v3/077 — the first iteration since /060 to run the exact /060 14-feature config with no axis — established that it does not reproduce on current code + current data. **iter-v3/080 anchors against the current-code /060-config baseline: IS +0.8236 / OOS +0.2078.** All /080 IS/OOS deltas in this brief are computed against IS +0.8236 / OOS +0.2078, NOT the frozen /060 values.

The anchor gap decomposes exactly and additively (established by /077; carried by /078, /079):

- **IS code-drift: −0.0089** — entirely the iter-v3/061 TRX `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` (introduced 16 iterations after /060; a permanent, deterministic offset that floors 13 IS TRX `weight_factor` values).
- **OOS data-extent: +0.0675** — the 2026-05 OOS month that post-dates /060's data fetch (monotonic with calendar time).

This is a methodology correction — a stale reference value replaced by the freshest reproducible no-axis run of the canonical config — **not** a measurement-window change. The OOS-cutoff and start dates are untouched. The /059 CONFIRMATION baseline (tag `v0.v3-059`, IS +1.0894 / OOS +0.5791) is the canonical baseline and is **NOT** the EXPLORATION anchor; it is unchanged and unaffected.

**V3_MODELS confirmation.** `V3_MODELS` stays **BCH/LDO/TRX** — the /060 anchor universe. /078's universe-revision axis (BCH/ADA/TRX) was SUSPICIOUS-OOS-DOMINANT and CLOSED; LDO was already restored to `V3_MODELS` at /079's setup. /080 makes no universe change.

---

## Section 0.5 — Iteration Type Declaration

**TYPE: EXPLORATION — cycle 2 EXPLORATION #10 of 10 (the FINAL cycle-2 EXPLORATION).** Per `feedback_v3_strict_10_to_1_cadence.md`, cycle 2 runs 10 SEPARATE EXPLORATIONs (/071–/080) followed by 1 SEPARATE CONFIRMATION (/081 or later) — the 10th EXPLORATION is NOT collapsed into the CONFIRMATION.

- **Axis category**: **PASSIVE-DIAGNOSTIC** — an instrumentation/report-emission axis. The single primary axis persists the per-trade M1 `confidence` scalar (already computed inside `lgbm.get_signal`, currently discarded) into `trades.csv` as a new `confidence` column, and emits a new report CSV `confidence_distribution.csv` (per-symbol / per-IS-month M1-confidence histograms with the realized Optuna `confidence_threshold` per cell overlaid). The trade roster is provably **bit-identical to /060** (Section 4.1). This is the iter-v3/079 Critic Recommendation #1 instrument.
- **Mandatory secondary edit (a baseline-restore, NOT a second varied axis)**: revert /079's conviction-derate primitive — restore the hardcoded `weight = 100` in `lgbm.get_signal`, returning the strategy to the /060-config flat-weight state. /079 was NULL-RESULT (PARKED) and does not advance; restoring the /060 anchor is the mandated post-/079 setup state, exactly the established "mandatory secondary edit" pattern (cf. /077 reverting /076's feature, /079 reverting /078's universe).
- **Run mode**: `--exploration` → `EXPLORATION_ENSEMBLE_SIZE = 3` (`ENSEMBLE_SEEDS` outer-42 lineage subset `[191664963, 1662057957, 1405681631]`), `--n-trials 35`. 3-symbol universe (BCH/LDO/TRX). `REQUIRED_GAP = 66`, embargo 22. Total 315 Optuna trials.
- **Run command**: `uv run python run_baseline_v3.py --exploration --clean-oof`
- **Wall-clock target**: bit-identical to /060's run plus one report-column write and one O(trades) report CSV. **Estimated wall-clock ≈ /060 ≈ 1.0–1.3h** — well within the 2h EXPLORATION cap.
- **Type justification (1–2 sentences)**: Cycle 2 is 9/10 done with 0 clean PROMISING; on current evidence the /081 CONFIRMATION is a /059-baseline multi-seed re-validation regardless of /080's outcome, so the question is what the final EXPLORATION slot should *deliver* — and the EDA (Section 2) shows the highest-EV deliverable is the persisted-`confidence` instrument the /079 Critic Rec #1 mandated, because the alternative (a vol-adjusted barrier "fresh axis") is a knob on the SATURATED holding-time-extension family that is structurally predicted to reproduce SUSPICIOUS-OOS-DOMINANT. A PASSIVE-DIAGNOSTIC iteration is the only candidate whose SUSPICIOUS probability is a *provable* near-zero (bit-identical roster — Section 4.5) AND it produces the instrument a clean cycle-3 conviction-derate re-attempt requires.

---

## Section 1 — Hypothesis

This is a **diagnostic hypothesis**, not a performance hypothesis. The deliverable is the persisted-`confidence` instrument, NOT an IS/OOS Sharpe lift; the expected and intended classification is **NULL-RESULT** (Section 7).

> Persisting the per-trade M1 directional `confidence` scalar — `max(P(long), P(short))`, already computed inside `lgbm.get_signal` and currently discarded after the confidence-threshold gate — into `trades.csv` and emitting a per-symbol / per-IS-month `confidence_distribution.csv` (with the realized Optuna `confidence_threshold` per cell overlaid) produces the empirical M1-confidence distribution that the iter-v3/079 conviction-derate axis lacked; this lets a cycle-3 conviction-derate re-attempt place its reference constant `C_REF` empirically in the *populated* region of the confidence distribution rather than by an a-priori guess (the /079 root cause), while the trade roster stays provably bit-identical to /060 — `confidence` is a passive metadata field threaded `Signal → Order → TradeResult` that no decision, barrier, gate, or model input ever consults — so the iteration cannot itself produce a SUSPICIOUS outcome.

---

## Section 2 — IS-Only Numerical Evidence

EDA committed at SHA `0029155` (`analysis/iteration_v3-080/axis_selection_eda.py` + 6 output CSVs). All tables are computed IS-data-only on the committed `/060` and `/079` trade rosters; the OOS rosters are read ONLY to print OOS trade counts for the bit-identity / degeneracy proofs (TEST A, D, E) — no OOS quantity feeds any sort / filter / argmax / threshold. The EDA carries a `_grep_no_oos_tuning()` AST self-audit (flags any OOS-metric token used as a live `Name` / `Attribute` / `Subscript`-key identifier); it returns **PASS**.

### Section 2.1 — TEST A: the instrumentation gap is real and unrecoverable without a backtest

`reports-v3/iteration_v3-060/in_sample/trades.csv` (the canonical roster artifact) has exactly **15 columns** — `symbol, direction, entry_price, exit_price, weight_factor, open_time, close_time, exit_reason, pnl_pct, fee_pct, net_pnl_pct, weighted_pnl, stop_loss_price, take_profit_price, timeout_time`. **`confidence` is not one of them.**

| Fact | Value | Note |
|---|---|---|
| `trades.csv` column count | 15 | `confidence` absent |
| `confidence` column present in `trades.csv` | **False** | the M1 directional margin is NOT persisted in any report artifact |
| `weight_factor` semantics | `vt_scale × (signal.weight/100)` | `weight_factor` is the vol-target scale × the signal weight — at /079 `signal.weight` is the conviction-derate output. It is **not** the M1 confidence scalar; `confidence` is *upstream* of `weight`. |
| `C_REF` empirical placement possible today | **False** | `confidence` is computed inside `lgbm.get_signal` (`directional_conf = max(proba[0], proba[2])`, `lgbm.py:672`) and discarded after the `if confidence < threshold` gate; recovering its distribution requires a backtest (re-train every walk-forward month) — exactly the /079 root cause |

**This is the iter-v3/079 Critic Recommendation #1 finding restated as verified fact.** /079's conviction-derate (primitive 13) classified NULL-RESULT (behavioral saturation): the de-rate engaged only 7.5% of IS trades (12/159) vs a predicted ≥25%, because its a-priori reference constant `C_REF = 0.65` landed at the Optuna-tuned `confidence_threshold` pile-up rather than in the populated region of the M1-confidence distribution. The /079 Critic ruled: a fair re-attempt is permissible ONLY after the per-trade M1 `confidence` is persisted to a report artifact, so a re-attempt's `C_REF` can be placed empirically. **That artifact does not exist. iter-v3/080 builds it.**

### Section 2.2 — TEST B: the "fresh structural axis" alternative is a knob on a closed axis

The /079 diary Section 11 floated, as candidate #2 for /080, "a fresh structural labeling axis — a trend-scanning label or a vol-adjusted past-only-realized-vol barrier." The EDA documents — a-priori, over the cycle-2 record — that this is **not a genuinely fresh axis**:

| Cycle-2 labeling attempt | Verdict | Mechanism |
|---|---|---|
| iter-v3/071 meta-labeling (M2 take/skip) | SUSPICIOUS-OOS-DOMINANT | M2 veto removes early stop-outs → holding-time extension |
| iter-v3/072 fixed-horizon-21 label | NEGATIVE | label DEFINITION change; no edge |
| iter-v3/073 per-symbol triple-barrier asymmetry | SUSPICIOUS-OOS-DOMINANT (OOS/IS ratio 6.85) | per-symbol barrier rebalanced toward TP → holding-time extension |
| **candidate: vol-adjusted past-only-realized-vol barrier** | **PREDICTED SUSPICIOUS-OOS-DOMINANT — SKIP** | replacing the global ATR multiplier with a per-symbol realized-vol barrier RE-SCALES the per-trade TP/SL distances → changes per-trade duration → SATURATED holding-time-extension family (`feedback_v3_is_oos_regime_divergence.md`: /065 SL widening, /071, /073). A barrier knob is NOT a category-1/2 structural axis; it is a knob on a closed axis. |

Cycle 2 has already tested labeling **three** ways. A vol-adjusted barrier is a barrier-REBALANCING change — it re-scales per-trade barrier distances, which changes per-trade duration, which loads the v3 IS/OOS regime factor (`feedback_v3_is_oos_regime_divergence.md`: v3's IS window penalizes longer-held trades, the OOS window rewards them; /065, /071, /073 all loaded this factor and went SUSPICIOUS-OOS-DOMINANT). Spending the final cycle-2 slot on a structurally-predicted-SUSPICIOUS knob delivers another regime-luck data point, not an edge ingredient or an instrument. Per `feedback_v3_axis_saturation_predictor.md` (skip a saturated axis) and `feedback_v3_structural_over_knob_exploration.md` (a knob on a closed axis is not a structural axis), the alt candidate is **SKIPPED**.

### Section 2.3 — TEST C: the conviction hypothesis has weak-but-real residual support

A cycle-3 conviction-derate re-attempt is only worth instrumenting for if /079's directional hypothesis ("M1 confidence carries per-trade edge that flat sizing wastes") has real support. The EDA quantifies it from the committed `/079` IS roster. `confidence` itself is not recoverable here (TEST A) — but /079's derate de-rated exactly when conviction was below `C_REF`, and a de-rate is detectable in the /079 roster as a `weight_factor` strictly lower than the SAME-key `/060` trade's `weight_factor` (the conviction-derate is the only `/060 → /079` change; the roster keys and the vol-target scale are bit-identical, per the /079 diary):

| Group | n IS trades | mean `net_pnl_pct` | win rate |
|---|---:|---:|---:|
| de-rated (low-conviction; /079 `weight_factor` < /060) | 11 | **−0.1816%** | **27.3%** |
| non-de-rated | 148 | **+0.3173%** | **31.8%** |
| de-rate incidence (IS) | 11/159 = **6.9%** | — | — |

The de-rated (low-conviction) IS trades **underperformed** the non-de-rated group on both mean PnL and win rate. The directional hypothesis is **weakly confirmed** on the available sample — low conviction *did* mean lower realized edge. (The EDA's weight-factor-diff method identifies 11 de-rated trades vs the /079 engineering report's 12 — one BCH de-rate is masked by a `weight_factor` rounding tie at the 0.5 vol-target floor; the directional finding is robust to the off-by-one.) /079's problem was not that the hypothesis is dead — it is that the de-rate engaged too few trades (6.9–7.5%) to move the aggregate. **Persisting `confidence` is the precondition for a cycle-3 re-attempt that places `C_REF` in the populated band where it can actually engage a material trade population.**

### Section 2.4 — TEST D: the PASSIVE-DIAGNOSTIC roster is bit-identical to /060 (the SUSPICIOUS proof)

| Split | n /060 | n /079 | keys added /079 vs /060 | keys removed /079 vs /060 |
|---|---:|---:|---:|---:|
| in_sample | 159 | 159 | **0** | **0** |
| out_of_sample | 102 | 103 | 1 | 0 |

The IS `(symbol, open_time)` key roster is **bit-identical** /060 ↔ /079 (159 = 159, 0/0) — /079's conviction-derate only re-weighted trades; it added/removed none. The OOS +1-key is the known data-extent artifact (the 2026-05 OOS month post-dating /060's data fetch — certified benign by the /074/075/077/079 Critics).

**The proof.** iter-v3/080 = the /060-config exactly, plus three changes: (a) flat `weight = 100` restored (the /079-derate revert — a revert TO the anchor, so it makes /080 *more* identical to /060, not less); (b) a `confidence` column added to `trades.csv`; (c) a `confidence_distribution.csv` report CSV. Changes (b) and (c) are **pure report emission with zero behavioral effect** — `confidence` is a passive metadata field that no decision consults (Section 3.1). Therefore the /080 trade roster is bit-identical to /060 on keys AND `weight_factor` ⇒ the OOS/IS monthly Sharpe ratio is a *mechanical identity*, not an estimate ⇒ the SUSPICIOUS ratio gate and the SUSPICIOUS-OOS-DOMINANT sub-mode are mechanically near-impossible (Section 4.5). This is the conditional-orthogonality-equivalent PROOF the Critic /076 Rec #3 demands as the prerequisite for flooring SUSPICIOUS below the cycle-2 base rate (Section 7) — the /077 PASSIVE-DIAGNOSTIC precedent exactly.

### Section 2.5 — TEST E: holding-time-effect predictor (mechanical identity)

| Split | n trades (/060) | mean duration (candles, /060) | predicted full-roster duration Δ | predicted trades added | predicted trades removed |
|---|---:|---:|---:|---:|---:|
| in_sample | 159 | 6.3145 | **0.0000** | **0** | **0** |
| out_of_sample | 102 | 6.4608 | **0.0000** | **0** | **0** |

Both holding-time channels (`feedback_v3_is_oos_regime_divergence.md` + Critic /076 Rec #2) are mechanical identities — see Section 4.4. The byte-identical /060-config labeling + model + seeds produce identical per-trade barriers; a passive metadata column touches no barrier; the added set and the removed set are BOTH empty (degenerate sub-channel).

---

## Section 3 — Proposed Changes

Exactly **TWO** changes. ONE is the single primary axis; the other is a mandatory baseline-restore (NOT a second varied axis).

### 3.1 — PRIMARY AXIS: persist the per-trade M1 `confidence` + emit `confidence_distribution.csv`

The M1 LightGBM ensemble computes a per-trade directional `confidence` inside `LightGbmStrategy.get_signal` — `directional_conf = max(float(proba[0]), float(proba[2]))` at `lgbm.py:672` (the `proba` vector is the inner-ensemble mean `predict_proba`). It is used as a binary gate (`if confidence < self._confidence_threshold: return NO_SIGNAL`, `lgbm.py:678`) and then **discarded** — no downstream artifact records it.

The axis persists it. Two sub-changes:

**(1) A `confidence` field threaded `Signal → Order → TradeResult` and written to `trades.csv`.**

- `Signal` (`backtest_models.py:30`) gains an optional field `confidence: float | None = None` (a passive metadata field; no default-behavior change).
- `LightGbmStrategy.get_signal` populates it: `return Signal(direction=direction, weight=weight, tp_pct=tp_pct, sl_pct=sl_pct, confidence=confidence)` — `confidence` is already in scope at the return site.
- `Order` (`backtest_models.py:76`) gains `confidence: float | None = None`; `backtest.py`'s order-construction (`make_order`, ~`backtest.py:599`) copies `signal.confidence` into the `Order`.
- `TradeResult` (`backtest_models.py:89`) gains `confidence: float | None = None`; `make_result` (`backtest.py:623`) copies `order.confidence` into the `TradeResult`.
- `iteration_report.py:_write_trades_csv` (`fields` list at line 98) appends `"confidence"` to the column list and writes `f"{t.confidence:.6f}"` if non-None else `""`.

**This field is PASSIVE.** It is metadata carried alongside the trade. **No decision, barrier, gate, position size, model input, label, or Optuna objective ever reads `Signal.confidence` / `Order.confidence` / `TradeResult.confidence`.** The QE must verify (Section 6, Section 8.6) that the only consumers of the new field are: the constructors that copy it forward, and `_write_trades_csv`. Adding a passive metadata field to the three frozen dataclasses with a `None` default does not change the value of any existing field on any path → the trade roster is bit-identical to /060.

**(2) A new report function `_write_confidence_distribution(...)` emitting `reports-v3/iteration_v3-080/confidence_distribution.csv`.**

Called immediately after `_write_conditional_orthogonality` (the existing post-backtest report call site, `run_baseline_v3.py:2849`). It reads the IS trade roster (which now carries `confidence`) plus the realized per-`(symbol, month)` Optuna `confidence_threshold` (the trained strategies' `_confidence_thresholds` lists, available on the `model_pairs` objects the runner already passes to the report writers — `lgbm.py:530` appends them; if the report stage holds only the last-month strategy state per the lazy-monthly-training pattern, the function emits the realized last-month `confidence_threshold` and labels it `last_month`, exactly the documented `_write_conditional_orthogonality` PART A degeneracy — the Engineer states which in the engineering report). It writes a per-symbol / per-IS-month histogram of trade `confidence` over the a-priori uniform bin grid `CONF_BIN_EDGES` (edges every 0.025 on `[0.50, 1.00]`), with the realized Optuna `confidence_threshold` per cell as an overlaid column.

`confidence_distribution.csv` schema (one row per `(symbol, IS-month, confidence_bin)`):
```
symbol, is_month, conf_bin_lo, conf_bin_hi, n_trades, realized_optuna_conf_threshold
```
Plus a pooled `symbol=PORTFOLIO` block and an `is_month=ALL_IS` block per symbol.

**This is the cycle-3 instrument.** It answers, empirically, the question /079's `C_REF = 0.65` guessed blind: *where does the surviving-trade M1-confidence mass actually sit, relative to the Optuna threshold?* A cycle-3 conviction-derate brief places `C_REF` in the populated region this CSV reveals.

### 3.2 — MANDATORY BASELINE-RESTORE: revert /079's conviction-derate

`lgbm.get_signal` line 754 (`weight = conviction_derate(confidence)`) reverts to the hardcoded **`weight = 100`** — the /060-config flat-weight state. The `conviction_derate` helper function (`lgbm.py:114-137`) may remain defined (it is unreferenced once line 754 is reverted, and a future cycle-3 re-attempt will re-wire it) OR be removed — the Engineer's call, but the call site MUST revert and the `run_baseline_v3.py` import + the 3-point pre-flight assertion on `conviction_derate` must be removed (since /080 ships flat weight, asserting the derate map's shape is no longer a /080 pre-flight invariant).

This is a **baseline-restore, NOT a second varied axis**. /079's conviction-derate was NULL-RESULT (PARKED — `diary-v3/iteration_v3-079.md` Section 5); a NULL-RESULT axis does not advance, and restoring the /060 anchor is the mandated post-/079 setup state. It is the identical "mandatory secondary edit" pattern as /077 (reverting /076's `range_efficiency_50`) and /079 (reverting /078's universe). It returns the strategy to the state every cycle-2 EXPLORATION /071–/078 ran on.

`ITERATION_LABEL` → `"v3-080"`.

### 3.3 — Single-axis discipline

The brief declares exactly TWO changes: (1) the persist-`confidence` instrumentation — the single primary axis — comprising the passive metadata field + the `confidence_distribution.csv` report function; (2) the mandatory revert of /079's conviction-derate — a baseline-restore to the /060 flat-weight state, NOT a second varied axis. No feature is added. No labeling change. No risk-gate change. No model-architecture change. No universe change. The 14-feature stack, the ATR labeling `(2.0, 1.0)`, the `ENSEMBLE_SEEDS`, the Optuna search, and the 7-primitive risk-gate stack are ALL unchanged at their /060 configuration.

---

## Section 4 — Expected OOS Impact

### 4.1 — Predicted IS / OOS deltas (mechanical identities)

The PASSIVE-DIAGNOSTIC axis adds a passive metadata field (zero behavioral effect — Section 3.1) and reverts /079's conviction-derate back to the /060 flat-weight state. The Phase-6 backtest therefore runs the **byte-identical /060 configuration** — same 14-feature stack, same flat `weight = 100`, same labeling, same risk gates, same `ENSEMBLE_SEEDS`, same Optuna search. The trained models are deterministically identical to /060's; the trade roster is **bit-identical to /060**.

| Metric | Predicted /080 | vs /060-config anchor | Basis |
|---|---:|---:|---|
| IS monthly Sharpe | +0.8236 | **Δ 0.0000** | bit-identical roster → identical `comparison.csv` |
| OOS monthly Sharpe | +0.2078 | **Δ 0.0000** (± a small data-extent drift) | bit-identical roster |
| OOS/IS monthly Sharpe ratio | 0.2523 | identical (± drift) | mechanical identity |
| IS n_trades | 159 | 0 | deterministic models, flat weight |
| OOS n_trades | 102–103 | 0 to +1 | deterministic models; +1 admitted for the data-extent artifact (Section 2.4) |

**Honest precision on the "bit-identical" claim** (the lesson from the /077 Critic Rec #2 — do not over-claim "algebraic identity" without git-verifying the config frozen). The /080 roster is bit-identical to **the current-code /060-config** (the re-anchored IS +0.8236 / OOS +0.2078), NOT to the frozen /060 CSV — the iter-v3/061 TRX `vol_scale_floor` is already in the current code (it floors 13 IS TRX `weight_factor` values; the −0.0089 IS code-drift component). /080 carries that same /061 floor, so /080 reproduces the *re-anchored* baseline, not the frozen one. The bit-identity claim is therefore "/080 == the current-code /060-config", and it is verifiable by the QE diffing `reports-v3/iteration_v3-080/` against `reports-v3/iteration_v3-079/` — /079's roster, with the conviction-derate reverted out, IS the current-code /060-config roster. A small OOS data-extent drift (≤ +1 OOS trade, an `end_of_data` trade resolving differently as the data extent grows by days) is admitted and is NOT a falsifier.

### 4.2 — Falsifier (LOCKED)

**The diagnostic hypothesis is falsified if the /080 trade roster is NOT bit-identical (on `(symbol, open_time)` keys AND `weight_factor`) to /079's roster with the conviction-derate reverted** — i.e. if the IS roster differs from /079's IS roster on any key or any `weight_factor`, or the OOS roster differs by more than the ≤ +1 data-extent trade. Such a divergence would NOT be a strategy result — it would be a Phase-6 wiring defect (the passive metadata field unintentionally altering a decision path, or the conviction-derate revert being incomplete). It is a falsifier of the iteration's PASSIVE-DIAGNOSTIC framing, to be diagnosed and fixed, not interpreted as signal.

**Secondary deliverable falsifier**: if `confidence_distribution.csv` is emitted but is degenerate (e.g. only the `last_month` overlay is recoverable AND the per-IS-month histogram cannot be built from the roster), the diagnostic value is reduced — but the `confidence` column on `trades.csv` is itself the primary, sufficient deliverable for a cycle-3 re-attempt (a cycle-3 EDA can build any histogram it needs directly from the persisted column). The CSV is the convenience surface; the column is the load-bearing instrument.

### 4.3 — Behavioral-effect predictor (mandated by `feedback_v3_axis_saturation_predictor.md`)

The behavioral-effect prediction is a **mechanical identity**: the axis changes **0 IS trades and 0 OOS trades** — the added trade set and the removed trade set are both EMPTY, and **0 `weight_factor` values change** (a passive metadata field re-weights nothing; the conviction-derate revert restores the /060 flat weight that every /071–/078 EXPLORATION already ran on). Falsifier: any non-zero roster delta (keys or `weight_factor`) beyond the ≤ +1 OOS data-extent trade → Phase-6 wiring defect (Section 4.2).

This is **not a "saturated axis"** in the `feedback_v3_axis_saturation_predictor.md` sense (an axis whose tunable parameter sits outside the data sensitivity band). It is a **deliberately zero-behavioral-effect axis** — a PASSIVE-DIAGNOSTIC. The diagnostic VALUE is the persisted `confidence` column + `confidence_distribution.csv`, not a roster change. This is the legitimate exception the rule contemplates: the predictor says the axis is zero-effect *by design*, and the instrument it delivers IS the axis output. The /079 behavioral-saturation pathology (an a-priori threshold-coupled constant landing on the Optuna pile-up) **cannot recur here** — /080 ships NO conviction constant; it ships the *measurement* that lets cycle 3 place that constant non-blind.

### 4.4 — Holding-time-effect predictor + added-vs-removed sub-channel (mandated by `feedback_v3_is_oos_regime_divergence.md` + Critic /076 Rec #2)

Both holding-time channels are **mechanical identities** (EDA TEST E):

| Channel | Predicted | Falsifier |
|---|---|---|
| Full-roster mean/median trade-duration delta vs the current-code /060-config | **0.000 candles** (byte-identical labeling + flat weight + deterministic model → identical per-trade barriers) | > +1.0-candle full-roster shift → Phase-6 wiring defect |
| Added-vs-removed roster-composition mean-duration gap (Critic /076 Rec #2 sub-channel) | **UNDEFINED — DEGENERATE** — the added set and the removed set are BOTH EMPTY (0 trades added, 0 removed) | any non-empty added/removed set (beyond the ≤ +1 OOS data-extent trade) → Phase-6 wiring defect |

All THREE known v3 regime-loading vectors are **structurally inaccessible** to a passive metadata column: (a) holding-time EXTENSION — the labeling and barriers are byte-identical, per-trade duration delta is 0.000; (b) trade SELECTION — the model feature set, seeds, and Optuna search are byte-identical → the models are deterministically identical → no trade is re-selected; (c) universe SWAP — `V3_MODELS` is unchanged. A passive metadata field that no decision reads cannot load the IS/OOS regime factor through any channel. Both the > +1.0-candle full-roster falsifier AND the added-vs-removed sub-channel falsifier are pre-registered and both are trivially satisfied; a non-zero observed value is a wiring-defect signal, not a regime-loading signal.

### 4.5 — OOS/IS ratio SUSPICIOUS pre-registration (mandated by `feedback_v3_oos_is_ratio_gate.md`)

Pre-registered, LOCKED, using the canonical within-iteration `comparison.csv` `monthly_sharpe` ratio column:

- **OOS/IS monthly Sharpe ratio > 3.0 → SUSPICIOUS classification** — fires regardless of absolute OOS Sharpe magnitude.
- **OOS-DOMINANT sub-mode → SUSPICIOUS classification**: IS shift < 0 (vs +0.8236) AND OOS shift ≥ +0.20 (vs +0.2078).

**Predicted /080 OOS/IS ratio = 0.2523** — mechanically equal to the current-code /060-config (bit-identical roster → identical `comparison.csv`). 0.2523 ≪ 3.0. The SUSPICIOUS ratio gate is **mechanically near-impossible to trip**: the ratio is an algebraic copy of the /060-config's 0.2523. The SUSPICIOUS-OOS-DOMINANT sub-mode is likewise mechanically near-impossible — it requires OOS shift ≥ +0.20 against a predicted OOS shift of 0.000 (± ≤ a few-hundredths data-extent drift on one `end_of_data` trade, far below +0.20). This is the PROOF (per Critic /076 Rec #3) that justifies a sub-base-rate SUSPICIOUS weight in Section 7: a bit-identical roster makes the OOS/IS ratio a mechanical identity, not a probability estimate — exactly the /077 PASSIVE-DIAGNOSTIC precedent.

---

## Section 5 — Risk Mitigation

iter-v3/080 ships **no strategy change** — the trade roster, the risk-gate stack, the labeling, the model, and the position sizing are byte-identical to the current-code /060-config (flat `weight = 100` restored). There is therefore no new risk surface to mitigate at the strategy level. The risk-gate stack is the established 7-primitive stack at its /060 configuration (BTC trend kill, vol scaling, ADX, Hurst regime, feature z-score OOD, low-vol filter, hit-rate DISABLED — `RiskV2Config` unchanged).

The only iteration-level risks are engineering risks, both detected by pre-registered falsifiers:

1. **A Phase-6 wiring defect** — the passive `confidence` metadata field unintentionally altering a decision path (e.g. a constructor positional-argument shift, or `confidence` being read by something other than the forward-copy constructors and `_write_trades_csv`), or the /079 conviction-derate revert being incomplete. Mitigation: the Section 4.2 roster-bit-identity falsifier is the explicit detector; the QE's Phase-6 pre-flight verifies `ITERATION_LABEL`, the 14-feature stack, the reverted flat `weight = 100`, and the unchanged `RiskV2Config`; the Critic Check 8 (hypothesis-implementation alignment) independently audits that the only code deltas are the passive field + the report function + the conviction-derate revert.
2. **A look-ahead via the new field** — structurally impossible: `confidence` is computed from the same past-only `proba` vector the existing direction/weight already use (`lgbm.py:664-672`), and the production model is trained only on the embargoed past walk-forward window. The new field carries a value that was *already* look-ahead-clean; persisting it introduces zero new data dependency. The QE verifies (Section 8.6) that `confidence` is sourced only from the in-scope `proba`-derived scalar.

Reverting /079's conviction-derate is itself a risk *reduction*: it returns the strategy to the proven /060 flat-weight state, removing the NULL-RESULT primitive 13.

---

## Section 6 — Risk Management Design

The 7-primitive v3 risk gate stack is UNCHANGED at its /060 configuration. No primitive is added, removed, re-scoped, or re-thresholded. /079's conviction-derate (primitive 13) is REMOVED (reverted to flat `weight = 100`).

| # | Primitive | /080 state | Fire-rate prediction |
|---|---|---|---|
| 1 | BTC trend kill | /060 config (`threshold_pct = 15.0`) | identical to /060-config |
| 2 | Vol scaling | /060 config | identical to /060-config |
| 3 | ADX threshold | /060 config (`adx_threshold = 20.0`) | identical to /060-config |
| 4 | Hurst regime | /060 config | identical to /060-config |
| 5 | Feature z-score OOD | /060 config (`zscore_threshold = 2.0`) | identical to /060-config |
| 6 | Low-vol filter | /060 config | identical to /060-config |
| 7 | Hit-rate | DISABLED (as /060) | n/a |
| — | Conviction-derate (primitive 13, /079) | **REMOVED** — reverted to flat `weight = 100` | not fired |
| — | Regime-conditional kill switch (primitive 9) | DISABLED (CLOSED axis) | not fired |
| — | BTC-trend position-SIZE de-rate (primitive 12) | DISABLED (reverted at /076) | not fired |
| — | Per-symbol PnL cap / drawdown brake | DISABLED (CLOSED axes) | not fired |

Regime coverage: identical to the /060-config — the diagnostic instrumentation is post-decision metadata + a post-backtest report CSV and does not touch the gate stack. Every gate fires exactly as it did at /060.

The QE's Phase-6 implementation includes an adversarial test asserting: (a) `Signal` / `Order` / `TradeResult` each carry a `confidence` field defaulting to `None`, and constructing any of them WITHOUT `confidence` produces the identical object on every pre-existing field; (b) no module other than the forward-copy constructors (`make_order`, `make_result`, `get_signal`) and `_write_trades_csv` reads the `confidence` attribute (a static grep); (c) the `lgbm.get_signal` weight is the literal `100` (the conviction-derate revert); (d) the trade roster `(symbol, open_time)` key set + `weight_factor` values are bit-identical to /079's roster with the conviction-derate reverted; (e) `confidence` is read look-ahead-clean (it is the `proba`-derived scalar already in scope, computed from past-only features).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

The expected and **intended** classification is **NULL-RESULT** (probability ≈ 93%). iter-v3/080 is a PASSIVE-DIAGNOSTIC iteration: it adds a passive `confidence` metadata field (zero behavioral effect — Section 3.1), emits `confidence_distribution.csv`, and reverts /079's conviction-derate to the /060 flat-weight state. The Phase-6 backtest reproduces the current-code /060-config exactly — the trade roster is bit-identical, IS Δ = 0.000, OOS Δ = 0.000 (± a small data-extent drift). Per the Section 8 disjunctive classifier, a roster bit-identical to the /060-config with shifts inside the noise band is **NULL-RESULT**. NULL-RESULT here is not a failure — it is the designed outcome: a diagnostic iteration's deliverable is the persisted-`confidence` instrument (the `confidence` column on `trades.csv` + `confidence_distribution.csv`), not a Sharpe lift.

**SUSPICIOUS is mechanically ruled out** (probability ≈ 2%, residual). All three SUSPICIOUS grounds are *structurally* excluded — (a) the labeling is byte-identical to the /060-config so per-trade duration delta is 0.000 (no holding-time extension); (b) there is no macro classifier and no feature change (the gate stack and the 14-feature stack are byte-identical so there is no trade re-selection); (c) `V3_MODELS` is unchanged (no universe swap). The OOS/IS ratio is an algebraic copy of the /060-config's 0.2523, far below the 3.0 gate, and the SUSPICIOUS-OOS-DOMINANT sub-mode requires OOS shift ≥ +0.20 against a predicted ~0.000. **This residual ≈2% SUSPICIOUS weight — deviating below the running cycle-2 base rate of 4/9 ≈ 44% — is justified by the bit-identity PROOF of Section 2.4 / Section 4.5**: a bit-identical roster makes the OOS/IS ratio a mechanical identity, not a probability estimate. This is exactly the proof standard the Critic /076 Rec #3 requires for a sub-base-rate weight, and exactly the /077 PASSIVE-DIAGNOSTIC precedent (the /079 calibration assessment in `diary-v3/iteration_v3-079.md` Section 8 explicitly confirms: "a CSV-only PASSIVE-DIAGNOSTIC IS such a proof"). The residual ≈2% is **not** a regime-loading allowance — it is the probability of a Phase-6 wiring defect (a config drift or an incomplete conviction-derate revert breaking the bit-identity), which the Section 4.2 falsifier and the Critic Check 8 are designed to catch, and which would be diagnosed as an engineering bug, not interpreted as signal.

The remaining ≈5% covers a benign roster perturbation from an unforeseen non-determinism source (a floating-point reduction-order change, or a slightly wider OOS data-extent drift) landing the shifts inside the noise band with the roster NOT bit-identical → that outcome would be classified INERT-AT-EXPLORATION (Section 8.3), still not SUSPICIOUS.

The genuine *diagnostic* risk — distinct from a classification failure — is that `confidence_distribution.csv` proves partly degenerate: if the report stage holds only the last walk-forward month's strategy state (the lazy-monthly-training pattern that made `_write_conditional_orthogonality` PART A a single-point map), the per-IS-month `realized_optuna_conf_threshold` overlay collapses to a `last_month` value. This is a reporting-completeness risk, not a strategy risk, and it is fully mitigated: the **`confidence` column on `trades.csv` is the load-bearing deliverable** (Section 4.2) — a cycle-3 EDA builds any histogram it needs directly from the persisted per-trade column, independent of the report-stage CSV. The CSV is the convenience surface; the column is the instrument.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (LOCKED)

The /080 classification is the per-brief disjunctive taxonomy, evaluated in this DISJUNCTIVE ORDER (**SUSPICIOUS → NULL-RESULT → NEGATIVE → PROMISING → INERT** — first match is canonical). All thresholds are LOCKED before the backtest. Anchor = the re-anchored current-code /060-config baseline **IS +0.8236 / OOS +0.2078**. "IS shift" / "OOS shift" = /080 minus the anchor monthly Sharpe. "OOS/IS ratio" = the within-iteration `comparison.csv` `monthly_sharpe` ratio column.

**8.1 — PROMISING-AT-EXPLORATION**: IS shift ≥ **+0.10** AND OOS shift ≥ **+0.20** AND `frac_positive_paths` (CPCV) ≥ 0.50 AND not SUSPICIOUS. *(Mechanically impossible here — a PASSIVE-DIAGNOSTIC has no edge mechanism; predicted shifts are 0.000.)*

**8.2 — NEGATIVE-AT-EXPLORATION** (disjunctive OR): IS shift < **−0.10** OR OOS shift < **−0.20**, AND not SUSPICIOUS. *(Mechanically impossible here — predicted shifts are 0.000.)*

**8.3 — INERT-AT-EXPLORATION**: both shifts within **[−0.10, +0.10]** IS and **[−0.20, +0.20]** OOS (the noise bands), AND the roster is NOT bit-identical to the current-code /060-config (≥1 trade key or `weight_factor` differs, beyond the ≤ +1 OOS data-extent trade), AND not SUSPICIOUS. *(This fires only if a benign non-determinism perturbs the roster without moving the metrics — Section 7's ≈5% tail.)*

**8.4 — SUSPICIOUS** (disjunctive — fires on EITHER ground; SUSPICIOUS takes precedence over NEGATIVE/INERT/NULL-RESULT with no magnitude qualifier):
- **Ratio gate**: OOS/IS monthly Sharpe ratio > **3.0**.
- **SUSPICIOUS-OOS-DOMINANT sub-mode**: IS shift < 0 AND OOS shift ≥ +0.20.
*(Both mechanically near-impossible here — Section 4.5. If SUSPICIOUS fires, it is a Phase-6 wiring defect and the iteration is NO-MERGE pending root-cause.)*

**8.5 — NULL-RESULT** (the expected/intended outcome): the /080 trade roster is **bit-identical** (on `(symbol, open_time)` keys AND `weight_factor`) to /079's roster with the conviction-derate reverted (= the current-code /060-config) — IS n_trades = 159, OOS n_trades = 102–103, every IS trade matches on key and `weight_factor`, the OOS roster differs by at most the ≤ +1 data-extent trade — AND IS shift = OOS shift = 0.000 (± data-extent drift). The diagnostic deliverable (the `confidence` column on `trades.csv` + `confidence_distribution.csv`) is produced.

**Evaluation order**: SUSPICIOUS (8.4) → NULL-RESULT (8.5) → NEGATIVE (8.2) → PROMISING (8.1) → INERT (8.3). First match is canonical.

**MERGE / NO-MERGE**: This is an EXPLORATION — it does NOT update `BASELINE_V3.md` regardless of classification (only a CONFIRMATION-MERGE updates the baseline). "MERGE" at the EXPLORATION level (the Critic verdict `EXPLORATION-MERGE` / `OVERALL=MERGE`) means the Critic certifies the classification clean and the instrumentation lands on the branch as accretive diagnostic infrastructure — a strictly-accretive, non-compoundable methodology component per `feedback_v3_promising_mechanical_subtype.md` (the persisted-`confidence` instrument is tooling, not an edge ingredient). A NULL-RESULT diagnostic iteration with the deliverable produced and the bit-identity verified is the intended success. **/080 does NOT advance to the cycle-2 CONFIRMATION (iter-v3/081) bundle as an edge ingredient** — a PASSIVE-DIAGNOSTIC has no edge to bundle; its output is the instrument that seeds a clean cycle-3 conviction-derate re-attempt.

An INERT classification (Section 7's ≈5% benign-perturbation tail) still lands the instrumentation cleanly. A NEGATIVE / SUSPICIOUS classification would each indicate a Phase-6 wiring defect breaking the bit-identity — to be diagnosed and fixed, not interpreted as a genuine strategy result, not bundled.

---

## Section 9 — Library Stack Declaration

Unchanged from the /079 stack (pinned in `pyproject.toml` / `uv.lock`):

- lightgbm 4.6.0
- optuna 4.8.0
- numpy 2.2.6
- pandas 3.0.0
- scikit-learn 1.8.0
- scipy 1.17.0
- statsmodels 0.14.6
- pyarrow 23.0.1

No new library is added. The `confidence` metadata field is a plain `float | None`; `_write_confidence_distribution` uses only stdlib `csv` + numpy (already in the stack — the same dependencies `_write_conditional_orthogonality` uses). SHAP is **not** added. CPCV/PBO/PSR/DSR per `validation_v3.py` unchanged.

---

## Section 10 — QR Audit Trail

### 10.1 — Axis selection provenance (per `feedback_v3_axis_selection_quant_discipline.md`)

- **EDA SHA**: `0029155` — `analysis/iteration_v3-080/axis_selection_eda.py` + 6 output CSVs. Committed BEFORE this brief.
- **Orchestrator-seeded candidates** (`/079` diary Section 11, non-binding): (1) a PASSIVE-DIAGNOSTIC that builds the persisted per-trade M1 `confidence` instrumentation (the /079-diary RECOMMENDED option, discharging Critic /079 Rec #1); (2) a fresh structural axis — a NEW model architecture or NEW labeling architecture (a trend-scanning label or a vol-adjusted past-only-realized-vol barrier).
- **QR axis decision**: candidate **#1 — the PASSIVE-DIAGNOSTIC** (persist `confidence` + emit `confidence_distribution.csv`). The QR weighed both candidates via the committed EDA:
  - The EDA TEST A confirmed the instrumentation gap is real and unrecoverable without a backtest — `confidence` is absent from every report artifact, so a cycle-3 conviction-derate `C_REF` cannot be placed empirically today (the exact /079 root cause).
  - The EDA TEST B established that candidate #2's concrete instance — a vol-adjusted past-only-realized-vol barrier — is **not a genuinely fresh structural axis**: it is a barrier-rebalancing change in the SATURATED holding-time-extension family (`feedback_v3_is_oos_regime_divergence.md`: /065, /071, /073 all loaded the IS/OOS regime factor and went SUSPICIOUS-OOS-DOMINANT), and per `feedback_v3_structural_over_knob_exploration.md` a knob on a closed axis is not a category-1/2 structural axis. The other candidate-#2 instance — a trend-scanning / first-significant-move label — is variable-horizon and changes per-trade duration, loading the same regime factor at the brief stage (the /073 precedent + Critic /078). Cycle 2 has already tested labeling three ways (/071 meta-labeling, /072 fixed-horizon, /073 per-symbol-barrier); there is no genuinely-untested, holding-time-orthogonal labeling axis.
  - The EDA TEST C confirmed the conviction hypothesis has weak-but-real IS residual support (de-rated /079 IS trades underperformed: mean `net_pnl_pct` −0.18% vs +0.32%, WR 27.3% vs 31.8%) — so the instrument /080 builds genuinely seeds a worthwhile cycle-3 re-attempt.
  - **The decisive reasoning**: cycle 2 is 9/10 done with 0 clean PROMISING; the /081 CONFIRMATION is a /059-baseline re-validation regardless of /080's outcome (a PASSIVE-DIAGNOSTIC by design is not PROMISING). The final slot's value is therefore what it *delivers*. Candidate #1 converts the standing /079 Critic Rec #1 methodology debt into a committed deliverable and seeds a clean cycle-3 conviction-derate re-attempt; candidate #2 spends the slot on a knob whose outcome is structurally predicted (SUSPICIOUS-OOS-DOMINANT). The higher-EV use of the final cycle-2 slot is candidate #1. This is the /077 PASSIVE-DIAGNOSTIC precedent (a slot spent building the conditional-orthogonality map, certified clean INERT-AT-EXPLORATION).
- No orchestrator setup commit was made ad-hoc; the QR EDA backs the axis and this brief is the first design artifact. The setup commit follows this brief.

### 10.2 — Per-parameter IS-only / a-priori selection-function disclosure (mandated by Critic /075 Rec #2)

Every design parameter of the selected axis is selected by a function whose inputs are demonstrably IS-only or a-priori. The EDA module docstring carries the same disclosure verbatim; it is reproduced here:

| Parameter | Selection function | Input columns | IS-only / a-priori |
|---|---|---|---|
| PARAMETER 1 — the AXIS (PASSIVE-DIAGNOSTIC: persist `confidence` + emit `confidence_distribution.csv`) | `_pick_axis()` — returns a fixed string constant; not a sort/filter/argmax over any metric | NONE (data-free) | **a-priori** |
| PARAMETER 2 — the BTC monthly regime label that BINS the `confidence_distribution.csv` per-IS-month histogram rows | `build_btc_monthly_regime()` — a month is BULL if ≥50% of its BTC 8h bars have `close[t-1] > SMA_270[t-1]` (`.shift(1)` before the rolling SMA — past-only) | BTCUSDT 8h `open_time`, `close` ONLY (a calendar/price label, NOT an OOS performance metric) | **a-priori** |
| PARAMETER 3 — the histogram bin edges for `confidence_distribution.csv` | a-priori uniform grid on the intrinsic `[0.50, 1.00]` confidence scale, edges every 0.025 (`CONF_BIN_EDGES`) | NONE | **a-priori** |
| PARAMETER 4 — the EDA per-month training window (used only by TEST B's labeling-family reasoning; no model trained in the EDA) | a-priori — `training_months = 24`, the SACRED CONSTANT | NONE | **a-priori (sacred)** |

The conviction-derate constants `C_FLOOR` / `C_REF` / `W_MIN_FRAC` are **NOT design parameters of iter-v3/080** — /080 REVERTS /079's conviction-derate (Section 3.2) and ships flat `weight = 100`. /080 selects NO conviction constant. The empirical placement of a future `C_REF` is explicitly DEFERRED to cycle 3, to be done from the `confidence_distribution.csv` / the `trades.csv` `confidence` column this iteration builds.

The EDA computes **no** per-candidate OOS counterfactual. The only OOS-window quantities anywhere are the OOS trade *counts* in TEST A / D / E (used for the bit-identity / degeneracy proofs) — clearly count-only, feeding no `sort`, `filter`, `argmax`, or threshold. The EDA carries a `_grep_no_oos_tuning()` AST self-audit (flags any OOS-metric token used as a live `Name` / `Attribute` / `Subscript`-key identifier — the concrete iter-v3/075 cheating signature `row["oos_delta"]`); it returns **PASS**. **No design parameter was selected on OOS data.**

### 10.3 — Setup commit SHA

- EDA commit SHA: `0029155` (`analysis/iteration_v3-080/` — committed before the brief)
- Brief commit SHA: `6df3d04`
- Setup commit SHA: `dec440e` (`run_baseline_v3.py` — `ITERATION_LABEL` "v3-080", `conviction_derate` import + 3-point pre-flight assertion removed; the `lgbm.py` call-site revert + the passive-`confidence` `src/` instrumentation are QE Phase-6 scope per Section 3.1/3.2)
- This SHA-backfill commit: `<backfill_sha>`
- Phase 5.5 gate SHA: `<filled by the Phase 5.5 gate>`
