# Iteration iter-v3/101 — Diary

## Decision: EXPLORATION-SUSPICIOUS — Falsifier F5 fires (BCH roster-churn duration signature). NO-MERGE; non-advancing.

iter-v3/101 (cycle-5 EXPLORATION slot #1) tested **ONE variable**: the LightGBM
`sample_weight` normalization, switched from magnitude-linear `[1,10]` to
cross-sectional rank-normalized `[1,10]` (`weight_mode="rank_normalized"`). Phase-7.5
Critic OVERALL=MERGE (no methodology BLOCK — all 12 checks pass; the stale-runner fix
verified clean; DSR/PBO/PSR genuinely computed, not the /090/092 placeholder defect).
The PROMISING-vs-NULL classification is the QR's Phase-8 call — and on the corrected
anchor + the F5 roster-diff, the verdict is **EXPLORATION-SUSPICIOUS**: the OOS lift is
a trade-selection roster-churn artifact, not signal. `weight_mode="rank_normalized"`
does **not** carry to a cycle-5 CONFIRMATION; the axis reverts to default `magnitude`.

---

## Section 1 — What Was Done

### The axis (one variable, per the Critic-verified single-axis claim)

`labeling.py` gained a `weight_mode` parameter. `weight_mode="magnitude"` (default)
reproduces /059 byte-for-byte; `weight_mode="rank_normalized"` replaces the final
rescale with `1.0 + pd.Series(weights).rank(pct=True) * 9.0`. The pre-normalization
`|labeled_pnl|` array is unchanged — only the final magnitude→rank-percentile rescale
switches. `lgbm.py` threads `weight_mode` through `LightGbmStrategy.__init__` →
`label_trades`; `run_baseline_v3.py` sets `weight_mode="rank_normalized"` in
`common_kwargs` and `ITERATION_LABEL="v3-101"`. The 14-feature `V3_FEATURE_COLUMNS`,
the BCH/LDO/TRX universe, ATR multipliers (2.0/1.0), the 21-candle timeout, and the
7-gate RiskV2 stack are all bit-identical to /059.

### Backtest

3-seed EXPLORATION mode (`--exploration`, `EXPLORATION_ENSEMBLE_SIZE=3`, n_trials=35),
seeds `ENSEMBLE_SEEDS[0:3]` = (191664963, 1662057957, 1405681631). Wall-clock ~0.72h.
Engineering report committed at `a14fde5`; Critic review at `briefs-v3/iteration_v3-101/review.md`.

### Stale-runner fix (verified clean by the Critic)

`V3_MODELS` was found stale at `(LDO, GALA, ADA)` — leftover from iter-v3/097's setup
commit `e6ed662`, which filed NEGATIVE and never reverted. Fixed to the /059 canonical
`(BCH, LDO, TRX)` in commit `d1ea7d5` BEFORE any backtest ran. The Critic independently
confirmed the backtest ran on BCH/LDO/TRX (per_symbol.csv, per_cell_pbo.csv all
BCH/LDO/TRX; the config-accretion check at `run_baseline_v3.py:1014-1017` hard-raises on
`V3_MODELS` drift and the run reached completion). No backtest was run on the stale
universe.

---

## Section 2 — The Anchor Correction (verdict-determining)

The brief Section 4 / Section 8 anchored the falsifiers and classification taxonomy to
/059's **10-seed CONFIRMATION** numbers (IS +1.0894 / OOS +0.5791). This is
architecturally mismatched. /101 ran **3-seed EXPLORATION mode**; the
architecturally-matched anchor — per `feedback_v3_dsr_mode_artifact.md` and
`feedback_v3_cycle1_axis_pass_criteria.md` — is **/060**, the cycle-1 3-seed
EXPLORATION-mode reference (IS +0.8325 / OOS +0.1403, same `ensemble_size=3`, same
n_trials=35). Per the Phase-7.5 Critic Recommendation 1, /101 is classified against /060.

/060 anchor numbers verified directly from `diary-v3/iteration_v3-060.md` (Section 2
multi-anchor table) and cross-checked against `reports-v3/iteration_v3-060/` (the OOS
roster, per_symbol.csv, monthly_pnl.csv all present and consistent).

| Metric | /101 (3-seed EXPL) | /060 anchor (3-seed EXPL) | Δ vs /060 | /059 (10-seed CONF — caveat) | Δ vs /059 |
|---|---:|---:|---:|---:|---:|
| **IS monthly Sharpe** | **+0.8571** | **+0.8325** | **+0.0246** | +1.0894 | −0.2323 |
| **OOS monthly Sharpe** | **+0.5190** | **+0.1403** | **+0.3787** | +0.5791 | −0.0601 |
| IS daily Sharpe | 1.8577 | 1.7115 | +0.146 | 2.7092 | — |
| OOS daily Sharpe | 1.1703 | 0.3659 | +0.804 | 1.4359 | — |
| OOS/IS monthly ratio | 0.6055 | 0.1685 | +0.437 | 0.5316 | — |
| IS trades | 176 | 159 | +17 | 171 | — |
| OOS trades | 101 | 102 | −1 | 94 | — |
| frac_positive_paths | 0.6444 | 0.6444 | 0.000 (CPCV-invariant) | 0.6444 | — |
| PBO | 0.0968 | 0.1278 | −0.031 | 0.1278 | — |

Against the matched /060 anchor, /101 is **IS Δ +0.0246 / OOS Δ +0.3787** — IS
essentially flat (below the +0.10 cycle-1 IS-PASS gate), OOS up strongly (clears the
+0.20 gate). Against the wrong /059-10-seed anchor it would read as a regression on both
axes — that framing is rejected. The verdict below uses /060.

DSR=0.0 / PSR=1.0 / DSR_relative=0.019 are EXPLORATION-mode artifacts (n_trials=315 vs
CONFIRMATION's 1050) — INFORMATIONAL ONLY per `feedback_v3_dsr_mode_artifact.md`, not
classification inputs.

---

## Section 3 — Per-Symbol OOS Decomposition (vs /060 matched anchor)

| Symbol | /101 OOS wpnl | /060 OOS wpnl | Δ vs /060 | /101 OOS trades | /101 OOS WR |
|---|---:|---:|---:|---:|---:|
| **TRX** | **+18.25** | +23.31 | **−5.06** | 52 | 44.2% |
| **BCH** | **+10.58** | +1.91 | **+8.68** | 37 | 37.8% |
| **LDO** | **−10.41** | −19.72 | **+9.31** | 12 | 33.3% |
| **Portfolio** | **+18.43** | +5.50 | **+12.93** | 101 | 40.6% |

The portfolio OOS lift (+12.93) is carried almost entirely by **BCH (+8.68) and LDO
(+9.31)**, partially offset by TRX (−5.06). The IS side: BCH +78.68 net PnL pct (driver,
172.24% denominator-inflated share), LDO +14.91, TRX −47.91 (drag). TRX's OOS-positive /
IS-negative sign split is the same single-trade-lottery pattern /060 itself exhibited —
not new signal.

---

## Section 4 — Falsifier F5: the verdict-determining finding

**F5 (brief Section 4): "Mechanical-only lift — OOS improves but the per-symbol
added-vs-removed-trade mean-duration gap exceeds +1.0 (the /076 trade-selection
sub-channel signature — the lift is a roster-churn artifact, not signal)."**

The committed analysis script `analysis/iteration_v3-101/f5_roster_diff.py` (output
`T5_f5_roster_diff.csv`) diffs the /101 OOS roster against the architecturally-matched
/060 3-seed OOS roster, keyed on `(symbol, direction, open_time)`, and computes the
per-symbol added-vs-removed mean trade-duration gap in 8h candles. (The `weight_mode`
axis re-weights training samples only — it does not touch features, labels, or the
inference path — so a trade either survives bit-identically or is replaced; entry
timestamp + symbol + side is the natural trade identity.)

**F5 result vs the /060 matched anchor:**

| Symbol | n_kept | n_added | n_removed | added mean dur | removed mean dur | duration gap | F5? |
|---|---:|---:|---:|---:|---:|---:|---|
| **BCH** | 24 | 13 | 13 | **8.000** | **6.385** | **+1.6154** | **FIRES** (> +1.0) |
| LDO | 7 | 5 | 4 | 9.600 | 9.500 | +0.100 | no |
| TRX | 39 | 13 | 15 | 5.308 | 6.267 | −0.959 | no |
| Portfolio (pooled) | 70 | 31 | 32 | 7.129 | 6.719 | +0.410 | no |

**F5 FIRES on BCH** — gap +1.6154 > the pre-registered +1.0 threshold. And BCH is
precisely the symbol with the largest clean OOS lift in the decomposition (+8.68 vs
/060), so the F5-fire is on a symbol with a material lift, not a no-op symbol.

**The corroborating decomposition (why this is a churn artifact, not signal).** Of
BCH's 37 OOS trades, **24 were kept identically from /060** (same entry, side,
timestamp) and **13 were swapped in**. The 24 kept BCH trades net **−1.442 wpnl** — the
trades that survived the re-weight are slightly *negative*. The entire BCH OOS lift
comes from the swap: the 13 removed trades were +3.350 wpnl, the 13 added trades are
+12.026 wpnl. `(kept −1.442 + added 12.026) = +10.584` (/101) vs
`(kept −1.442 + removed 3.350) = +1.908` (/060) → the +8.68 BCH lift IS the
added-minus-removed gap. The model did not get *more accurate* on the trades it shares
with /060; it selected a *different* set of BCH trades, and that different set is
skewed +1.62 candles longer-held. This is the **exact /076 EXPLORATION-SUSPICIOUS-OOS-DOMINANT
signature**: a change with no barrier-extension mechanism still loads a duration factor
through *which trades the model selects*. In an OOS window with directional moves,
longer-held trades score higher — the lift is regime-conditioned roster composition,
not a generalizable edge in the training objective.

(Caveat cross-check against the mismatched /059 10-seed roster, reported for
completeness only: F5 also fires there on LDO gap +1.0 and TRX gap +1.81 — but /059 is
not the architecturally-matched anchor and is not the basis for the verdict. The /060
matched-anchor BCH fire is the binding result.)

**F5 FIRES.** Per the brief Section 8 LOCKED disjunctive precedence
(BLOCKED → NEGATIVE → **SUSPICIOUS** → INERT → PROMISING → NULL-RESULT), F5 firing
places /101 at **SUSPICIOUS** (step 3) — which takes precedence over the PROMISING
candidacy (step 5) the OOS lift would otherwise have suggested.

---

## Section 5 — F1–F5 Falsifier Cross-Audit

Every brief Section-4 pre-registered falsifier, re-evaluated against the committed
artifacts:

| # | Falsifier | Threshold | Observed | Fires? |
|---|---|---|---|---|
| F1 | Headline OOS regression | OOS monthly Sharpe < +0.30 | +0.5190 | **NO** |
| F2 | IS collapse | IS monthly Sharpe < +0.70 | +0.8571 | **NO** |
| F3 | BCH IS-share inversion | BCH IS net-PnL flips negative OR BCH IS share > 99.5% | BCH IS net_pnl +78.68 (positive); share 172.24% is denominator-inflated by TRX IS −104.88%, not a single-symbol monopoly | **NO** |
| F4 | Trade-roster bit-identity | OOS roster bit-identical or <5% change vs anchor | 101 vs /060's 102 = −1.0% (vs /059 +7.4%); the roster is materially *re-composed* even though the count barely moved — 31 added / 32 removed vs /060 | **NO** (behaviorally active) |
| F5 | Mechanical-only lift | OOS improves AND per-symbol added-vs-removed mean-duration gap > +1.0 | BCH gap **+1.6154** vs /060 matched anchor | **FIRES** |

F1, F2, F3, F4 do not fire. **F5 fires.** Note on F4: the OOS *count* moved only −1 vs
/060, but the roster is not saturated — 31 trades added, 32 removed (70 kept of 102).
The `weight_mode` change is behaviorally active; it just expresses that activity as
trade *substitution* rather than count change. This is why F4 (count-based saturation)
does not fire while F5 (composition-based churn) does — and it is exactly why F5 was
pre-registered as a separate, finer falsifier after the /076 lesson.

**SUSPICIOUS sub-check (brief Section 8 step 3, second leg).** The structurally-suspicious
IS/OOS divergence test: IS daily Sharpe 1.8577 / OOS daily Sharpe 1.1703 = ratio
**1.5874**, inside the [0.2, 5] sane band — so the *ratio* leg of SUSPICIOUS does NOT
fire. SUSPICIOUS is reached via the **F5 leg alone**, which is sufficient under the
disjunctive precedence.

---

## Section 6 — Brief Section-7 Pre-Registered Failure-Mode Prediction vs Actual

The brief Section 7 pre-registered **INERT / PROMISING-MECHANICAL as the most-likely
failure mode**: "the rank transform is monotone … the trade roster moves <5% and the
OOS Sharpe lands within noise of /059 … classified PROMISING-MECHANICAL or INERT
(Falsifier F4)." The pre-registered behavioral predictor was "OOS trade count changes
by 5–25% vs /059's 94 OOS trades."

**The prediction partially held and partially missed:**

- **The OOS count predictor missed.** /101 OOS = 101 trades. Against the brief's stated
  /059 reference (94), that is +7.4% — *inside* the predicted 5–25% band, so F4
  (count-saturation) correctly did NOT fire. Against the architecturally-matched /060
  (102), the count moved −1.0% — *below* the 5% floor. The count metric is anchor-sensitive
  and, as Section 5 shows, count is the wrong lens: the roster is materially re-composed
  (31 added / 32 removed vs /060) regardless of the near-zero net count change.
- **The INERT/PROMISING-MECHANICAL "most-likely" call did NOT hold.** The axis was not
  behaviorally inert — it actively re-selected ~30% of the OOS roster. But it also was
  not a clean PROMISING. The actual outcome is the brief's *under-weighted* mode:
  **SUSPICIOUS via F5** — the change is behaviorally active AND its OOS lift is a
  roster-churn artifact. The brief's Section 7 narrative under-weighted F5: it treated
  "monotone transform → small roster move" as the dominant scenario and did not foresee
  that a monotone re-weight can still re-compose the roster toward a duration-biased
  selection without changing the trade count. This is the same calibration miss the /076
  caveat flagged ("the holding-time predictor considered only per-trade barrier mechanics,
  not the roster-composition channel").

**Honest accounting:** the brief got the *direction* right (it did flag F4/F5 and the
roster-churn risk as live, and pre-registered F5 explicitly) but mis-ranked the
probabilities — it called INERT most-likely and SUSPICIOUS ~unlikely, and the actual
outcome is SUSPICIOUS.

---

## Section 7 — Classification: EXPLORATION-SUSPICIOUS

**Anchor used:** /060 (3-seed EXPLORATION-mode, IS +0.8325 / OOS +0.1403) — the
architecturally-matched reference, per the Phase-7.5 Critic Recommendation 1 and
`feedback_v3_dsr_mode_artifact.md` + `feedback_v3_cycle1_axis_pass_criteria.md`.

**Classification:** **EXPLORATION-SUSPICIOUS** — brief Section 8 LOCKED taxonomy step 3
(Falsifier F5 fires). **NO-MERGE; non-advancing.**

**Why SUSPICIOUS and not the neighbors — explicit reasoning:**

- **Not BLOCKED (step 1):** the Phase-7.5 Critic returned OVERALL=MERGE — no methodology
  defect, look-ahead clean, DSR/PBO/PSR genuinely computed. Step 1 does not apply.

- **Not NEGATIVE (step 2):** F1 (OOS < +0.30) and F2 (IS < +0.70) both fail to fire —
  OOS +0.5190, IS +0.8571. The brief's *wrong* /059-10-seed anchor would have made /101
  read as a bilateral regression and tempted a NEGATIVE framing; the Critic explicitly
  warned against letting the wrong anchor "force a NEGATIVE." Against the correct /060
  anchor /101 is IS-flat / OOS-up — not a regression. NEGATIVE is rejected.

- **SUSPICIOUS (step 3) — the match.** F5 fires: the BCH added-vs-removed mean-duration
  gap is +1.6154 > +1.0 against the matched /060 roster. The OOS lift is concentrated in
  BCH (+8.68) and that lift is 100% roster-churn — the 24 kept BCH trades are net −1.44;
  the gain is a swap of 13 short-duration trades for 13 longer-duration trades. This is
  the /076 trade-selection sub-channel signature: a change with no barrier-extension
  mechanism loads a duration factor through trade *selection*, and in a directional OOS
  window longer-held trades score higher. The lift is regime-conditioned roster
  composition, not signal. SUSPICIOUS is the first matching step in the disjunctive
  precedence and therefore the verdict.

- **Not INERT / PROMISING-MECHANICAL (step 4):** unreachable — F5 (step 3) already
  matched. And on the merits, the axis is not behaviorally inert: it re-composed ~30% of
  the OOS roster (31 added / 32 removed vs /060). F4 does not fire. INERT is rejected on
  both the precedence and the substance.

- **Not PROMISING (step 5) — the explicit "do not inflate" call.** The OOS Δ +0.3787
  vs /060 clears the +0.20 cycle-1 OOS-PASS gate, and frac_positive_paths 0.6444 clears
  0.50 — superficially a PROMISING-shaped OOS result. **But two independent reasons
  block PROMISING.** (1) The disjunctive precedence: F5 (step 3) fires, so step 5 is
  never reached — PROMISING requires *none* of F1–F5 to fire. (2) On the merits, even
  setting precedence aside: the IS Δ is **+0.0246**, far below the +0.10 cycle-1 IS-PASS
  gate, so this is at best a PROMISING-on-OOS-only; and the OOS lift itself is the F5
  roster-churn artifact, so the "OOS-only" lift is not a generalizable edge to promote.
  Per the dispatch instruction not to inflate a flat-IS, churn-driven result into a
  clean PROMISING — PROMISING is rejected.

- **Not NULL-RESULT (step 6):** unreachable (step 3 matched), and NULL-RESULT is the
  "fits none of the above cleanly" catch-all — /101 fits SUSPICIOUS cleanly via F5.
  NULL-RESULT is rejected.

The honest one-line read the Critic asked for: **/101 is IS-flat (+0.0246, below the
IS-PASS gate) with an OOS lift (+0.3787) that the F5 roster-diff proves is a BCH
trade-selection duration artifact — it is SUSPICIOUS, neither a clean PROMISING nor a
NEGATIVE.**

---

## Section 8 — Does `weight_mode="rank_normalized"` carry to a CONFIRMATION?

**No. The axis REVERTS to default `weight_mode="magnitude"`.**

A SUSPICIOUS EXPLORATION never advances to CONFIRMATION — this is the same disposition
as /076 and /078 (both EXPLORATION-SUSPICIOUS-OOS-DOMINANT, both non-advancing). The
reasons, specific to /101:

1. **The OOS lift is not signal.** F5 establishes the +8.68 BCH OOS lift is
   roster-churn — a duration-biased trade selection that pays off in a directional OOS
   window. A cycle-5 CONFIRMATION at 10-seed against /059's proper CONFIRMATION baseline
   would not validate an edge; it would re-measure a regime-conditioned composition
   artifact at higher seed count. The /076 caveat is explicit that SUSPICIOUS axes "never
   advance."
2. **The IS side is flat.** IS Δ +0.0246 vs /060 is within noise and below the +0.10
   IS-PASS gate. Per `feedback_v3_strict_both_is_oos_baseline.md`, a CONFIRMATION must
   improve BOTH IS and OOS over the /059 baseline. An axis that is IS-flat at EXPLORATION
   has no IS-improvement thesis to carry into a CONFIRMATION.
3. **The monotone-transform mechanism predicts no robust lift.** `rank_normalized` is a
   monotone transform of the magnitude weight (Spearman ρ = 1.0, per the unit test). It
   preserves the weight *ordering* and only flattens magnitude. LightGBM split selection
   is itself partly rank-based, so the marginal effect on the fitted model is small —
   consistent with the IS-flat result. There is no mechanism by which this produces a
   durable multi-seed edge.

`run_baseline_v3.py` `common_kwargs` reverts to default `weight_mode="magnitude"` (the
parameter and its byte-identical default branch stay in `labeling.py`/`lgbm.py` at zero
revert cost — only the runner's one-line opt-in is removed). The sample-weight
normalization frame is recorded in BASELINE_V3.md Dead Ideas as: **"vol-neutral
rank-normalized sample weighting (`weight_mode='rank_normalized'`) — EXPLORATION-SUSPICIOUS
at iter-v3/101; the OOS lift is a BCH trade-selection duration artifact (F5 fires,
+1.62-candle gap), IS flat (+0.02 vs /060); does not advance."**

Note on the /100 recommendation lineage: the /100 closeout recommended a sample-weighting
axis = AFML-Ch.4 uniqueness weighting + magnitude re-weighting. The /101 EDA already
killed the uniqueness half (ANGLE A/H — uniqueness collapses to ~1/21 ≈ 0.046 with
near-zero dispersion on the 21-candle overlapping label; rank-corr 0.992–0.997 — a
near-no-op). With the magnitude-reweight half now SUSPICIOUS, the **entire
sample-weighting frame is closed** for the v3 per-symbol LightGBM.

---

## Section 9 — BASELINE_V3.md Status: UNCHANGED

Per brief Section 8 and `feedback_v3_baseline_update_policy.md`: an EXPLORATION never
updates `BASELINE_V3.md` regardless of classification. /101 is EXPLORATION-SUSPICIOUS —
NO-MERGE. **BASELINE_V3.md is UNCHANGED**; iter-v3/059 remains the canonical baseline
(IS +1.0894 / OOS +0.5791, 10-seed CONFIRMATION). Tag `v0.v3-101` is a **closeout marker
only** (the `v0.v3-082`…`v0.v3-100` pattern), not a baseline update.

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` were not touched. The
walk-forward embargo fix (`e149e9d`) is inherited unchanged. No cheating: the QR saw OOS
for the first time in Phase 7; all Phase 1–5 EDA was IS-only (Critic-verified `load_is`
filtering in all 4 EDA scripts); the F5 script reads only committed report CSVs.

---

## Section 10 — Lessons

1. **A monotone re-weight can re-compose the roster without changing the trade count.**
   /101's OOS count moved −1 vs /060, yet 31 trades were added and 32 removed (70 of 102
   kept). The brief's Section-7 "monotone transform → <5% roster move → INERT" reasoning
   conflated *count stability* with *roster stability*. F4 (count-based) and F5
   (composition-based) are genuinely distinct falsifiers — and /101 is the case that
   separates them: F4 silent, F5 fires. Future training-objective-axis briefs must lead
   the behavioral predictor with roster *composition* (added/removed sets), not net count.

2. **The /076 trade-selection sub-channel is a recurring v3 failure mode.** /076
   (`range_efficiency_50` feature) and /101 (`rank_normalized` sample weight) are
   mechanism-disjoint changes — one a feature, one a training weight — yet both produced
   an OOS lift that the added-vs-removed duration gap exposes as roster-churn (/076:
   added 7.25 vs removed 6.03; /101 BCH: added 8.00 vs removed 6.38). Any v3 change that
   shifts the fitted model — feature, label, weight, or hyperparameter — can load a
   duration factor through *which* trades it selects, and in a directional OOS window
   that pays off spuriously. The F5 roster-diff (added-vs-removed per-symbol mean
   duration) should be a **standard Phase-7 diagnostic** for every cycle-5 EXPLORATION
   whose OOS roster changes, not a falsifier the QR has to be told to evaluate.

3. **Anchor architecture-matching is verdict-determining.** The brief's /059-10-seed
   anchor would have forced a NEGATIVE framing (IS Δ −0.23 / OOS Δ −0.06); the matched
   /060-3-seed anchor gives IS-flat / OOS-up. The substance (F5 → SUSPICIOUS) is
   anchor-independent because F5's threshold is absolute — but the IS/OOS-delta framing
   is not. Cycle-5 EXPLORATION briefs must anchor Section 4/8 to the 3-seed
   EXPLORATION-mode reference, not the 10-seed CONFIRMATION baseline. (The brief itself
   acknowledged `feedback_v3_dsr_mode_artifact.md` for DSR but did not apply the same
   mode-matching to the Sharpe anchor — a brief-construction defect to fix at the next
   setup.)

4. **The sample-weighting frame is closed for the v3 per-symbol LightGBM.** Uniqueness
   weighting is a near-no-op on the 21-candle overlapping label (/101 ANGLE A/H);
   magnitude-reweighting is SUSPICIOUS (/101 F5). The training-objective layer does not
   carry the binding constraint — the thin per-symbol 8h triple-barrier signal does.
   This is the same conclusion cycle-4 reached for symbols (/097), features (/098),
   model architecture (/093/096), and the label's class structure (/099): the binding
   constraint is the signal, and the lever under test does not lift it.

---

## Section 11 — Next Iteration Ideas (cycle-5 EXPLORATION slot #2 onward)

The training objective is now the sixth attacked-and-closed v3 frame. The structural
priority order from `feedback_v3_structural_over_knob_exploration.md` still holds, but
cycle 4 + /101 have exhausted the cheap structural axes. Candidate axes for the next
EXPLORATION, ranked:

1. **A genuinely new edge *source*, not a new lever on the existing source.** Every
   recent EXPLORATION (symbols, features, model arch, label class, training weight) has
   re-shaped how the model consumes the same per-symbol 8h OHLCV-derived triple-barrier
   signal. The binding-constraint diagnosis across /093–/101 is that this signal is thin.
   The honest next move is a new *information* axis — funding rates and OI were closed
   for v3 (/019/023/024), but cross-exchange basis, liquidation-cascade features, and
   on-chain BTC-regime broadcasts (`references/crypto-edge-deep.md`) are unattacked at
   the per-symbol-book layer. These require a data-fetch + a GO/NO-GO EDA first
   (`feedback_fail_fast.md`).

2. **Universe expansion as denominator expansion** (HIGH-priority per
   `feedback_v3_iter019_axis_priorities.md` #2). The 3-symbol BCH/LDO/TRX book makes
   every per-symbol result a concentration story; F5-style roster-churn artifacts are
   amplified in a thin universe. Expanding the tradable set (subject to
   `V3_EXCLUDED_SYMBOLS`) is an orthogonal mechanism to the closed per-symbol-cap axis.

3. **A regime-switching MODEL** (the /099 closeout's recommendation for /100) — a
   per-symbol two-expert mixture, separate LightGBM models on trending vs
   mean-reverting sub-samples split by a past-only Hurst/ADX gate. Distinct from /093's
   regime size-overlay. Caveat: model-architecture changes have a poor v3 record
   (/016 XGBoost was the worst OOS Δ in v3 at −2.53).

Per `feedback_v3_axis_selection_quant_discipline.md`, the next axis must be QR-led with
a committed `analysis/iteration_v3-NNN/*.py` EDA basis before the brief. Per
`feedback_v3_strict_10_to_1_cadence.md`, cycle 5 runs 10 EXPLORATIONs before a
CONFIRMATION.

---

## Reproducibility

- Iteration: iter-v3/101 — cycle-5 EXPLORATION slot #1
- Branch: `iteration-v3/101`
- Axis: `weight_mode` `magnitude` → `rank_normalized` (one variable)
- Run mode: 3-seed EXPLORATION (`--exploration`, `EXPLORATION_ENSEMBLE_SIZE=3`,
  `--n-trials 35`); seeds `ENSEMBLE_SEEDS[0:3]` = (191664963, 1662057957, 1405681631)
- Anchor for classification: iter-v3/060 (3-seed EXPLORATION-mode; IS +0.8325 / OOS +0.1403)
- Canonical baseline (unchanged): iter-v3/059 (`v0.v3-059`; IS +1.0894 / OOS +0.5791, 10-seed)
- Headline: IS monthly Sharpe +0.8571 / OOS monthly Sharpe +0.5190; 277 trades (176 IS / 101 OOS)
- PBO 0.0968; frac_positive_paths 0.6444; n_eff 18; DSR 0.0 / PSR 1.0 / DSR_relative 0.019014
  / DSR_relative_b4 0.999796 (DSR/PSR EXPLORATION-mode artifacts — informational only)
- Classification: **EXPLORATION-SUSPICIOUS** (Falsifier F5 fires — brief Section 8 step 3); NO-MERGE; non-advancing
- `weight_mode` disposition: REVERTS to default `magnitude`; sample-weighting frame CLOSED
- Brief SHA: `1abeea5`; EDA SHA: `247c4d3`; setup commit `87925c3`; stale-runner fix `d1ea7d5`
- Engineering report SHA: `a14fde5` (`briefs-v3/iteration_v3-101/engineering_report.md` — present, confirmed)
- Phase-7.5 Critic review: `briefs-v3/iteration_v3-101/review.md` (OVERALL=MERGE — no methodology BLOCK)
- F5 roster-diff analysis SHA: `77f7bdf` (`analysis/iteration_v3-101/f5_roster_diff.py` + `T5_f5_roster_diff.csv`)
- Diary SHA: (this commit)
- Catalog update SHA: (next commit — `briefs-v3/exploration_catalog.md` /101 row)
- Tag: `v0.v3-101` — closeout marker only; BASELINE_V3.md UNCHANGED
- Wall-clock: ~0.72h. Hardware: 20-core CPU, 58 GiB RAM (WSL2 / Linux 6.6.114.1)
- Library stack: UNCHANGED from /059 (Python 3.13, lightgbm 4.6.0, optuna 4.8.0, numpy
  2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1)
- Run command: `uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 35`
- NO CHEATING: `OOS_CUTOFF_DATE` / `training_months` untouched; QR saw OOS first in Phase 7;
  all EDA + the F5 script verified IS-only / committed-artifact-only.
