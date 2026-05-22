# QR Response to Critic — iter-v3/114

**Round 2 of the two-round Phase 7.5 protocol.** No new evidence is introduced —
every artifact cited below is committed under EDA SHA `d8a9725`
(`analysis/iteration_v3-114/`), the brief (`research_brief.md`), the engineering
report, or the `reports-v3/iteration_v3-114/` outputs. No new analysis script,
no new backtest.

This response answers the Critic's three clarifications. The Critic's source
traces are correct on every point I was able to check. I have re-read the EDA
scripts, the result tables, and the brief myself, and I confirm the Critic's
findings rather than contest them.

---

## Clarification 1 — Threshold-0.30 provenance

**This is a research-integrity question governed by `feedback_no_cheating.md`. I
am answering it with total honesty.**

### 1(a) — There is no committed EDA table or code path that produced 0.30 as an optimization output. 0.30 was hand-chosen.

I traced this myself. The Critic is correct:

- **`trigger_selection_synthesis.py:323`** — `chosen_thr = 0.30  # IS-calibrated;
  13% surgical panel fire-rate`. This is a literal hardcoded constant inside
  `main()`. It is not read from any table, not returned by any sweep, not the
  output of any optimization.
- **The S3 sweep does not select it.** `s3_chosen_gate_counterfactual` builds its
  grid as `np.linspace(np.nanmin(v), np.nanmax(v), 21)` — for `abs_ldo_vz` that
  natural grid is `[0.2694, 0.3331, 0.3967, ...]` (visible in
  `S3_chosen_gate_counterfactual.csv`: the first two rows after 0.30 are 0.3331
  and 0.3967). 0.30 is **not** a grid point. It enters the S3 table only because
  `main()` passes `extra_thr=0.30`, and the function's own docstring
  (lines 132–133) states `extra_thr` is appended "so the honest-classification
  lookup lands on it exactly." S3's own band-selection logic
  (`n_suppressed in [2,7]`, lines 162–169) would have picked a *different*
  threshold (the band starts at 0.3331, `n_suppressed=2`); 0.30 is force-injected
  past that selector.
- **T3 does not produce 0.30.** `t3_threshold_sweep` (`ldo_killswitch_eda.py`
  lines 192–250) sweeps `abs_ldo_vz` at percentiles `[75,80,82,85,88,90,92,95]`
  with **kill_HIGH** polarity (`fire = v2 > thr`, line 221). The committed
  `T3_threshold_sweep.csv` `abs_ldo_vz` rows carry thresholds **1.1221 → 1.7540**.
  The value 0.30 appears nowhere in T3. The kill_HIGH polarity is the *opposite*
  of the production kill_LOW gate. **The brief's stated provenance — Section 2.4
  "IS LDO candle-panel threshold sweep (T3 / panel-fire diagnostic)", the
  `risk_v2.py:269` comment `# IS-calibrated (EDA SHA d8a9725, T3)`, and Section 5
  R-PRIMITIVE "fixed by the T3 IS-only panel-fire sweep" — is false. T3 did not
  produce 0.30. I withdraw that provenance claim. The brief is wrong on this
  point and I am not defending it.**
- **The T3-driven `main()` auto-selection picked 1.6621**, not 0.30. The
  `ldo_killswitch_eda.py::main()` threshold logic (lines 688–712) selects on T3's
  `fire_rate ∈ [0.08, 0.30]` band and lands on 1.6621 (the 92nd percentile). At
  1.6621 the EDA's own downstream tables are damning: `T4_oracle_aggregate.csv`
  records `n_suppressed=0`, `counterfactual_wpnl_delta=-0.0`;
  `T9_oos_coverage_annex.csv` records `n_oos_trigger_fires=0`,
  `gate_dead_on_arrival_oos=True`. The EDA's own automated pipeline produced a
  dead-on-arrival gate. 0.30 was substituted by hand in
  `trigger_selection_synthesis.py` to rescue a non-dead gate.

**Plain statement: `ldo_realvol_zscore_floor=0.30` was hand-chosen by the QR. It
is not an EDA optimization output. The brief's "T3 IS-only sweep" provenance is
false and I withdraw it.**

### 1(b) — What information was used to place it at 0.30, and whether that information was IS-only

I must answer the harder question the Critic posed: was 0.30 placed on IS-only
information, and can I demonstrate that from the committed artifacts?

**What I can demonstrate from IS-only artifacts:** The 9 IS LDO roster trigger
values are committed in `T4_oracle_roster_counterfactual.csv` — `abs_ldo_vz`
values `[0.2694, 0.3126, 0.5752, 0.6640, 0.7221, 0.9138, 1.0657, 1.1829,
1.5422]`. These 9 values are the IS roster (`load_059_ldo_roster("in_sample")`),
strictly `close_time < OOS_CUTOFF_MS`. 0.30 sits in the gap `(0.2694, 0.3126)`.
Any threshold in that 2.5%-wide gap suppresses, under the kill_LOW rule
(`v < thr`), exactly the single trade at 0.2694 — the **2024-10-07,
−5.0184% stop-loss loser** — and no other trade. That much is an IS-only fact,
and it is the fact the brief leaned on: "suppress the one IS LDO loser that sits
in the lowest-realized-vol bucket."

**What I cannot demonstrate, and must concede.** The Critic asks me to
demonstrate, from the EDA's IS-only outputs *alone*, that no OOS-window
information informed the choice of 0.30 over (say) 0.32 or 0.40. **I cannot
demonstrate that, and here is the honest accounting of why:**

1. **The OOS-roster trigger values were computed in the same EDA session, in the
   same committed scripts.** `s1_consolidated_ranking` calls
   `load_059_ldo_roster("out_of_sample")` and attaches all 6 triggers to the OOS
   roster; `t9_oos_coverage_annex` loads the OOS roster; the A2 annex
   (`roster_loss_separation_annex.py`) loads it. All three are in commit
   `d8a9725` — the *same atomic commit* as `trigger_selection_synthesis.py` where
   0.30 is hardcoded. The committed history gives me **no evidence of temporal
   ordering** — I cannot point to an artifact proving I fixed 0.30 *before*
   running the OOS-roster scripts. The brief's defense (Section 0: "the threshold
   is fixed IS-only by the T3 sweep before the annex runs") is doubly broken: T3
   does not produce 0.30, and there is no committed ordering that places the
   hardcoding before the annex.

2. **The choice of 0.30 specifically — over 0.32 or 0.40 — is not pinned by any
   IS-only selection rule.** On IS-only information alone, any threshold in the
   wide interval `[0.3126, 0.5752)` is *strictly better than 0.30* by the EDA's
   own stated IS criterion: `S3_chosen_gate_counterfactual.csv` shows thresholds
   0.3331 / 0.3967 / 0.4604 / 0.5240 each suppress **2** IS trades, both losers
   (`loser_hit_rate=1.0`), `cf_wpnl_delta=+4.8694` — versus 0.30's **1** trade,
   `cf_wpnl_delta=+2.3586`. If I had been optimizing the threshold on IS roster
   loss-avoidance alone, I would have picked something in `[0.3331, 0.5240]`
   (more IS loss removed, still 100% loser-hit). I picked the *lower* edge of the
   one-trade gap instead. The brief rationalizes that as "surgicality" (a 13%
   fire-rate claim — see Clarification 2, which is itself unsupported). But
   "place the threshold at the bottom of the narrowest gap that clips exactly one
   IS trade" is not an IS-optimal rule; it is a rule that minimizes the gate's
   footprint while still firing. **I cannot rule out — and the committed
   artifacts do not let me rule out — that the appeal of the narrow one-trade
   placement was informed by having seen, in the same session, that wider
   thresholds fire heavily on the OOS roster** (`T9` / A2 ran on the OOS roster;
   `S1` computed the OOS `std_gap` of `+0.388`, a sign-flip the brief Section 2.6
   itself reports — which means the OOS roster trigger distribution *was* looked
   at).

3. **The honest conclusion.** I cannot demonstrate, from the committed IS-only
   artifacts, that the placement of 0.30 was made on IS-only information. The
   brief asserts an IS-only provenance ("T3 sweep") that is factually false. The
   OOS LDO roster trigger values and the OOS coverage figures were computed in
   the same EDA session and the same commit, with no committed ordering that
   fences the threshold choice from them. Under `feedback_no_cheating.md` — "verify
   EDA code is IS-only, don't trust the brief's prose" — the brief's prose claimed
   IS-only, the code does not bear it out, and I will not defend the prose. **I
   concede Check 1: the threshold-0.30 calibration cannot be confirmed as IS-only
   from the artifacts. Check 1 should stand as a FAIL (or, at the Critic's
   discretion, an unresolved CONCERN — but I am not arguing it down to PASS,
   because I cannot produce the IS-only proof that would justify PASS).**

This is a process failure I own. The correct construction would have been: (i) a
committed IS-only threshold-selection rule with an explicit objective, run and
committed *before* any script touches the OOS roster; (ii) the OOS coverage annex
in a *separate later commit*, so the temporal fence is auditable; (iii) the brief
citing the actual selecting table, not T3. None of those three held. I am
recording this for the dead-paths / process record.

---

## Clarification 2 — The "13% panel fire-rate" claim

**The 13% figure is not computed in any committed table. I cannot substantiate
it.**

The brief (Section 2.4, Section 6, `S4_surgicality_override.csv`) presents
"13.0% IS-panel fire-rate at threshold 0.30" as the surgicality justification —
the stated reason `ldo_realvol_zscore` was chosen over `ldo_vs_btc_30d` (which the
S4 screen disqualifies for a 46–79% fire-rate). I traced every committed table
for the number 13.0% / 0.130 at threshold 0.30:

- **`T3_threshold_sweep.csv`** — the only table with a `fire_rate` column. Its
  `abs_ldo_vz` rows are kill_HIGH at thresholds 1.12–1.75; the row nearest a 13%
  fire-rate is threshold **1.4763** (88th pctile, `fire_rate=0.1202`) — a
  kill_HIGH gate at 1.48, **not** a kill_LOW gate at 0.30. No T3 row has
  threshold 0.30.
- **`S3_chosen_gate_counterfactual.csv`** — has a row at threshold 0.30, but it
  is a *9-trade roster* counterfactual: `n_suppressed=1, n_losers=1,
  loser_hit_rate=1.0, cf_wpnl_delta=2.3586`. It has **no `fire_rate` column and
  no panel percentage**. 1/9 = 11.1%, not 13.0% — and that is a roster ratio, not
  a panel rate.
- **`T5_behavioural_predictor.csv`** — the `LDO_panel_candles` row reports
  `predicted_count=219, denominator=2728, predicted_pct=8.03`. That 8.03% is
  computed at threshold **1.6621** (the T3-`main()` auto-selected value `main()`
  passed into `t5_behavioural_predictor`), not 0.30. The brief's Channel A
  prediction "13.0% of IS LDO candidate candles suppressed" does not match T5's
  committed 8.03% either — Channel A in Section 4 is internally inconsistent with
  the EDA table it cites.
- **`S2_honest_classification.csv`** — the verdict string literally contains the
  phrase "surgical 13% IS-panel fire-rate", but S2 computes nothing — it is a
  prose field assembled by `s2_honest_classification`, repeating the same
  unsupported number.

**There is no committed cell, in any of the 19 tables, that computes a 13.0%
panel fire-rate at threshold 0.30.** The number 13.0% has no committed
derivation. I cannot tell the Critic which candle population it was computed over
because it was not computed — it appears only as a hardcoded comment string
(`trigger_selection_synthesis.py:323`, `:344`; `S4` row literal "0.13 (thr=0.30)")
and as prose in the brief. I withdraw the 13% claim.

**Reconciliation against the ~59% production figure.** The engineering report's
Gate Fire-Rate Reconciliation establishes the production gate fired 842 times on
LDO with `signals_seen=595`, i.e. it suppressed `842 / (842 + ≥595) ≈ 59%` of the
LDO candidate-candle space. The production gate fires the kill_LOW rule on the
**full walk-forward LDO candle sequence**. The closest thing to an honest IS
panel rate the EDA *can* offer is a kill_LOW recomputation of T3's logic — but no
such table was committed; T3 only swept kill_HIGH. So I cannot even produce a
clean IS-panel kill_LOW number to set beside the 59%. What I can say definitively:
the 13% was never a measured panel fire-rate, and the production gate at ~59% is
squarely in the 46–79% "near-constant off-switch" regime the brief's own S4
screen used to **disqualify** `ldo_vs_btc_30d`.

**Confirming the Critic's Check 8 finding.** Yes — the brief's surgicality
argument (the stated reason `ldo_realvol_zscore` was chosen over
`ldo_vs_btc_30d`) was made on a base that does not exist. The S4 screen
disqualified `ldo_vs_btc_30d` for a 46–79% panel fire-rate and admitted
`ldo_realvol_zscore` for a "13%" panel fire-rate that was never computed. The
production kill_LOW gate fires ~59% — inside the very regime S4 used to reject
the alternative. The registered design property was "surgical, fire-rate well
below a constant-off"; the delivered gate is broad. **The hypothesis as
registered (a surgical ~13% low-vol-chop regime gate) is not the mechanism that
ran (a ~59% broad LDO suppressor). I confirm the Check 8 FAIL.**

---

## Clarification 3 — OOS-lift attribution and the per-symbol metric

### Single stable per-symbol metric for the Phase-8 diary

I will use **`concentration_pct` from `comparison.csv`** as the single per-symbol
attribution metric in the Phase-8 diary, and I will use it consistently.

Rationale: `pct_of_total_pnl` from `per_symbol.csv` divides a per-symbol PnL by
the *portfolio total* PnL. When the portfolio total is small (the OOS book is a
thin 3-symbol roster with two negative symbols and one positive), the denominator
is near-zero and the column is numerically unstable — it is the column that
produced the engineering report's TRX OOS = **+189.64%**. `concentration_pct`
(TRX OOS = **+95.61%**) is the bounded, stable column. The engineering report
citing both numbers ~94pp apart, both as authoritative, is a defect in the
report; the Phase-8 diary will cite only `concentration_pct` and will explicitly
note that `pct_of_total_pnl` is the known-unstable near-zero-denominator column
and is not used.

### Position on the +0.66 OOS lift attribution

**I agree with the Critic. The +0.66 OOS Sharpe delta is a thin-roster
aggregate-arithmetic artifact, not an attributable LDO-kill-switch edge.** The
committed evidence forces this conclusion:

1. **The TRX OOS book is bit-identical to /060.** The engineering report's
   non-contamination check confirms 54 of 55 /114 TRX OOS trades are bit-identical
   to /060's TRX OOS trades (the 55th, open_time 2026-05-16, post-dates /060's
   data extent by 12 candles — a pure data-extent artifact). TRX is /114's OOS
   carrier at `concentration_pct` +95.61%. The symbol that carries the OOS book
   did not change. This is the `feedback_v3_single_seed_frozen_baseline.md`
   frozen-baseline pattern: at single-lineage EXPLORATION the non-target symbols'
   rosters are deterministic and identical regardless of the LDO axis.

2. **The surviving LDO OOS book is still net-negative.** `comparison.csv` /
   `per_symbol.csv` show the 5 surviving LDO OOS trades net **−7.39%**
   (`concentration_pct` −2.95% of the OOS book; the engineering report's
   per-symbol table shows LDO OOS WR 20.0%). The gate did not turn LDO
   profitable. It removed LDO trades — including a winner (LDO OOS went 11→5
   trades; the engineering report notes the gate suppressed predominantly LDO
   *winners* in OOS) — and the residual is still a loss.

3. **Therefore the mechanism of the lift is arithmetic, not signal.** Removing 6
   LDO trades (a net drag, but a drag with a winner in it) from a 3-symbol
   monthly-return series mechanically re-weights the aggregate monthly-return
   mean and standard deviation, which mechanically moves the aggregate monthly
   Sharpe from /060's +0.14 to /114's +0.80. The TRX book — which actually
   produced the OOS PnL — is unchanged. The LDO kill-switch did not *discover* a
   transferable low-vol-chop edge; it *deleted* part of a thin negative book and
   the aggregate ratio moved. That is a thin-roster arithmetic effect. It is
   fragile (it would not survive a multi-seed CONFIRMATION dissolving the frozen
   baseline) and it is not robust.

4. **The prediction-miss corroborates this.** The brief Section 4 pre-registered
   OOS +0.18, 80% interval [−0.10, +0.45]; the EDA's own
   `S2_honest_classification.csv` predicted an OOS effect in [−0.05, +0.25]. The
   realized OOS is +0.7991 — 3× the top of the EDA's own caveated band, a hard
   upside interval violation. A result 3× above the EDA's own prediction, on a
   5-trade OOS LDO residual, where the lift traces to aggregate re-weighting
   rather than the gate's named mechanism, is the signature of a fragile artifact,
   not a transferable edge. The brief's Section 7 modal outcome
   ("INERT-to-mildly-negative") was the honest call; the +0.80 headline is not
   the "clean PROMISING" outcome it superficially resembles.

I do **not** claim the +0.66 as an LDO-kill-switch edge in the Phase-8 diary. The
diary will classify the OOS headline as a thin-roster aggregate artifact and will
state that the LDO kill-switch's own attributable OOS contribution is negligible
(the surviving LDO OOS book is still net-negative).

---

## Position

**STAND BY VERDICT.**

I accept the Critic's preliminary heading to **EXPLORATION-NEGATIVE**. I have no
artifact-grounded counter-argument, and a false defense would be a far worse
violation than an admitted error.

Specifically:

- **Check 8 FAIL — confirmed.** The brief registered a surgical ~13% low-vol-chop
  regime gate; the production gate fired ~59% of the LDO signal space. The "13%"
  has no committed derivation. The implementation tested a materially different
  mechanism (broad LDO suppression) than the registered hypothesis. The gate also
  did not fix LDO — the residual LDO OOS book is net-negative. I do not contest
  this.
- **Check 1 — concede as FAIL.** The brief's stated provenance for
  `ldo_realvol_zscore_floor=0.30` ("the T3 IS-only sweep") is false: T3 sweeps a
  different polarity at thresholds 1.12–1.75 and does not produce 0.30. 0.30 is
  hardcoded at `trigger_selection_synthesis.py:323` and force-injected. I cannot
  demonstrate from the committed IS-only artifacts that 0.30 was placed on
  IS-only information — the OOS-roster trigger values were computed in the same
  EDA session and the same commit, with no auditable temporal fence. Per
  `feedback_no_cheating.md` I will not argue Check 1 down to PASS without the
  IS-only proof, and I cannot produce it.
- **The +0.80 OOS headline is a thin-roster aggregate artifact**, not an
  attributable edge — TRX OOS bit-identical to /060, the surviving LDO OOS book
  still net-negative.

iter-v3/114 should be filed **EXPLORATION-NEGATIVE**. The LDO-realvol kill_LOW
gate does NOT advance to the iter-v3/120 CONFIRMATION bundle.

**For the dead-paths record (Phase-8 diary will carry these):**
1. The threshold-0.30 hand-placement with a false "T3 sweep" provenance is a
   process failure. Future risk-axis EDAs that select a scalar threshold MUST
   commit the IS-only selection rule and its selecting table in a commit that
   precedes any script touching an OOS-window file, so the IS-only fence is
   auditable. A hardcoded constant with a comment is not a calibration.
2. The "13%" surgicality figure was never computed. Brief claims that gate a
   trigger choice on a fire-rate MUST cite the committed table and column that
   computed it; an uncomputed number in a comment string is not evidence.
3. The single-lineage EXPLORATION frozen-baseline pattern means a per-symbol
   gate's aggregate OOS Sharpe delta is dominated by the unchanged non-target
   symbols' arithmetic. A per-symbol risk axis must be attributed on the
   target symbol's own roster, not on the portfolio aggregate Sharpe.
4. RiskV3 primitive 9 is now NEGATIVE/INERT across three data points
   (iter-v3/022 TRX, iter-v3/074 TRX, iter-v3/114 LDO). The kill-switch primitive
   should be treated as a closed path absent genuinely new, properly-fenced
   IS-only counterfactual evidence.
