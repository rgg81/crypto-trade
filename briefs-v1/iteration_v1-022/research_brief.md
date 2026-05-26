# iter-v1/022 — Research Brief (Phases 2-5)

**Branch**: `iteration-v1/022` from `iteration-v1/021` HEAD `c4f6ac1` (tag `v0.v1-021`).

**Anchor**: `v0.v1-baseline-corrected` (`BASELINE_V1.md` commit `f8bc12c`). Portfolio IS Sharpe **+0.2829** / OOS Sharpe **+0.6637** / OOS trades 189 / 5-sym universe / 4 models (A, C, D, E).

**Per-cohort anchor** (this iter's verdict baseline): LTC-in-pool IS per-trade Sharpe **+0.0038** (124 trades, +3.27% net, WR 39.5%; from `analysis/iteration_v1-022/ltc_prior_class.csv`) / OOS per-trade Sharpe **−0.2670** (34 trades, −47.25% net, WR 29.4%). LTC is the WORST OOS contributor in baseline (−189.99% of total OOS PnL share).

**Track**: v1 (refactored 2026-05-23). 13 phases. LightGBM Master + Critic.

**Iteration type**: EXPLORATION (cycle-3 #7 of 10).

---

## Section 0 — Position in cycle / pivot context

### 0.1 Cycle-3 cadence position

- Cycle-3 EXPLORATION #7 of 10 (CONFIRMATION earliest at /027).
- Prior cycle-3 EXPLORATIONs: /016 sample-weighting NEGATIVE-catastrophic; /017 universe NEGATIVE-anti-direction-INERT; /018 per-cohort-LINK PROMISING-INERT-favorable; /019 per-cohort-ETH+gate PROMISING; /020 per-cohort-BTC NEGATIVE-CATASTROPHIC; /021 methodology-pivot PROMISING-METHODOLOGY non-compoundable.
- Cycle-3 ledger thus far: 2 PROMISING (/018 LINK, /019 ETH+gate) + 1 PROMISING-METHODOLOGY (/021) + 2 NEGATIVE clean (/016/017) + 1 NEGATIVE-CATASTROPHIC (/020) + 0 merges.

### 0.2 Per-cohort methodology — fourth cohort

User strategic pivot 2026-05-26 codified at `feedback_v1_per_cohort_exploration_strategy.md`. /018 LINK (POSITIVE_EVERYWHERE prior) validated PROMISING-INERT-favorable under pure isolation. /019 ETH (ASYMMETRIC_ROTATION, IS-NEG/OOS-POS) validated PROMISING under cohort + direction-aware BTC-trend gate. /020 BTC (ASYMMETRIC_ROTATION, IS-NEG/OOS-POS) NEGATIVE-CATASTROPHIC under pure isolation — confirmed /021 H2 REFUTATION basin-relocation mechanism (ρ=0.9448 feature signatures). /022 advances to the **WORST OOS-contributor cohort** (LTC) with the **strongest directionally asymmetric OOS prior** in v1.

### 0.3 LTC prior class classification (CRITICAL — Critic /021 Rec #1 PASS gate)

Computed in `analysis/iteration_v1-022/ltc_prior_class.py` (committed `4eb091d`). Anchor: BASELINE_V1.md.

| Metric | LTC IS | LTC OOS |
|---|---|---|
| Trades | 124 | 34 |
| Win Rate | 39.5% | 29.4% (worst in v1 portfolio) |
| Net PnL % | **+3.27%** (noise — avg z-score +0.043) | **−47.25%** (avg z-score −1.557) |
| Per-trade avg | +0.0264% | −1.3897% |
| Per-trade Sharpe | +0.0038 | **−0.2670** |
| Per-trade std | 6.8953% | 5.2045% |
| n_months | 37 | 13 |
| n_pos_months | 18 (48.6%) | 4 (30.8%) |
| Max neg streak | **7 months** | **4 months** |

**Direction-asymmetric attribution (LOAD-BEARING for mechanism story)**:

| Sample × Direction | n | WR | Net PnL % | Per-trade avg |
|---|---|---|---|---|
| IS shorts (dir=-1) | 50 | 44.0% | **+14.10%** | +0.282% |
| IS longs (dir=+1) | 74 | 36.5% | −10.82% | −0.146% |
| OOS shorts (dir=-1) | 15 | 33.3% | −1.81% (noise) | −0.120% |
| OOS longs (dir=+1) | 19 | 26.3% | **−45.44%** | **−2.392%** |

**89% of LTC's OOS catastrophic loss is concentrated in LONG direction.** OOS shorts are roughly neutral (−1.81% across 15 trades). This is the strongest directional asymmetry of any v1 cohort.

**IS half-split sign reversal**: IS H1 (months 0-18) +14.76% (69 trades); IS H2 (months 19-36) **−11.49%** (55 trades). LTC's IS is regime-bound positive in H1 and regime-bound negative in H2 — IS itself is not stationary. LTC IS-marginal positive is half-split artifact, not a stable prior.

**OOS regime concentration**: 2025-12 (−13.29% / 4 tr) + 2026-01 (−17.01% / 6 tr) = **−30.30% across 10 trades in 2 months** = 64% of OOS catastrophe. These months coincide with BTC's late-2025/early-2026 correction phase (motivates BTC-trend mechanism hypothesis).

**Verdict per `_classify_ltc()`**: `ASYMMETRIC_ROTATION-INVERSE_IS-MARGINAL_OOS-CAT`.

**Class definition** (mirroring /021 diary §6 framework + /020 retrospective):
- **POSITIVE_EVERYWHERE**: like LINK — both halves positive; pure isolation sufficient.
- **ASYMMETRIC_ROTATION_IS-NEG_OOS-POS**: like BTC (/020) — pool-conferred OOS positive rotation; pure isolation DISSOLVES the OOS positive into basin-relocation NEGATIVE.
- **ASYMMETRIC_ROTATION-INVERSE_IS-MARGINAL_OOS-CAT**: like LTC (THIS iter) — IS noise-positive masks a directionally-asymmetric OOS catastrophic prior. Pure isolation likely amplifies the OOS catastrophe by exposing the directional asymmetry without intervention. **Orthogonal mechanism REQUIRED** per /021 H2 REFUTATION + /020 retrospective.
- **NEGATIVE_EVERYWHERE**: like ETH (/019 pre-gate) — both halves negative; orthogonal mechanism required and the mechanism must FLIP cohort exposure.

**Per /021 Critic Rec #1 PASS gate**: pre-classification COMPLETE. LTC = ASYMMETRIC_ROTATION-INVERSE_IS-MARGINAL_OOS-CAT. Mechanism selection at Section 0.4 is gated by this classification.

### 0.4 Orthogonal-mechanism selection (Critic /021 Rec #1 + LM Master forward-binding)

Per LTC = ASYMMETRIC_ROTATION-INVERSE_IS-MARGINAL_OOS-CAT, /022 MUST add orthogonal mechanism on top of cohort isolation (per /020 BTC retrospective + /019 ETH+gate empirical validation). Candidate mechanisms tested in `analysis/iteration_v1-022/ltc_directional_btc_trend_analysis.py` (committed `4eb091d`) via ORACLE EDA on baseline LTC trade roster (post-hoc trade-stream filter; STATELESS — VALID per `feedback_v3_oracle_eda_validity.md` STATELESS gate carve-out, NO deadlock risk).

| Mechanism | OOS Δ vs anchor | OOS Sharpe Δ | IS Δ | Notes |
|---|---|---|---|---|
| anchor (no mechanism) | +0.0 | +0.0 | +0.0 | LTC = ASYMMETRIC_ROTATION-INVERSE prior. |
| **shorts_only_total** (kill all longs) | **+45.44%** | **+0.243** | **+10.82%** | Highest empirical lift; but structural prior (HIGH-RISK pure direction-binary). |
| symmetric_btc_trend@4% (/019 pattern, tighter) | +27.97% | +0.105 | −0.81% | Strong OOS, IS slightly negative; symmetric kills OOS shorts unnecessarily. |
| symmetric_btc_trend@6% (/019 pattern, tighter) | +25.09% | +0.086 | +6.04% | OOS great, IS positive; symmetric still over-kills. |
| symmetric_btc_trend@8% (literal /019) | +20.63% | +0.056 | **−23.98%** | /019 nominal threshold catastrophic IS at LTC. |
| **longsuppress_btc_trend@4%** | **+12.45%** | **+0.036** | **+10.79%** | **Both halves positive**; kills only LTC longs in BTC bear regime. |
| longsuppress_btc_trend@6% | +12.45% | +0.036 | −3.50% | OOS gain, IS slight drag. |
| longsuppress_btc_trend@8% | +7.98% | +0.013 | −12.50% | Threshold too loose for LTC. |

**Mechanism selected for /022**: **`longsuppress_btc_trend_gate@4%`** (asymmetric one-sided variant of /019's primitive).

**Rationale**:
1. **Both halves positive** (IS Δ +10.79%, OOS Δ +12.45% on raw PnL roster ORACLE) — only mechanism with this property.
2. **Causal mechanism story at parameter-basin level** (per /021 H2 REFUTATION mandatory): LTC longs in BTC bear regime have catastrophic per-trade economics (89% of OOS loss in longs); Optuna under LTC-isolated joint loss CANNOT escape this without an external direction-asymmetric filter. The mechanism does NOT claim "different features for LTC" (forbidden); it claims directional regime-conditional drag and adds a stateless filter to remove the drag-class.
3. **Threshold tighter than /019** (4% vs 8%): LTC's direction-asymmetric drag is more sensitive to mild BTC weakness than ETH's. EDA confirms 4% threshold loses kill rate ~15% IS (smaller than /019's 17% IS kill rate at 8%) but lifts both halves.
4. **Asymmetric design (long-only suppression) DOMINATES symmetric** at low thresholds for LTC: symmetric@4% kills OOS shorts unnecessarily (OOS shorts are neutral; killing them yields no benefit and costs IS).
5. **NOT a regression to v2/019 SAME-pattern**: this is a NEW asymmetric variant of the v1/019 primitive; LM Master may flag PROMISING-MECHANICAL adjacency (Section 6.7).

**Rejected candidates**:
- **shorts_only_total** (kill all longs): empirically dominant on ORACLE EDA but methodologically risky as a HIGH-RISK pure structural prior — no falsifier path if it works (cannot distinguish regime-specific from intrinsic). Also, completely removes 60% of cohort exposure, so basin lottery widens disproportionately.
- **symmetric_btc_trend@8%** (literal /019 threshold): IS Δ −23.98% catastrophic at LTC scale; /019 threshold is calibrated for ETH not LTC.
- **direction-asymmetric ATR**: not testable as ORACLE EDA (changes Optuna's training-objective domain via different SL distances per direction); would require multi-EXPLORATION sequence.

**Caveat — ORACLE EDA limitations**: Numbers above are POST-HOC on baseline Model D LTC roster. /020 BTC catastrophic showed Jaccard 0.084 vs pool under pure cohort isolation — basin relocates materially. Actual /022 trade roster from Model H'-LTC-only at single-seed=42 n_trials=18 may differ substantially. The MECHANISM is causal (direction-asymmetric BTC bear-regime exposure) not roster-specific — the gate operates on whatever roster the basin produces.

### 0.5 Cadence ledger summary

Cycle-3 #7 of 10 needed for /027 CONFIRMATION. After this iteration: 7 of 10 done. 3 more EXPLORATIONs needed before /027.

### 0.6 Axis Rotation Discipline + Family Declaration (v1 mandatory)

- **This iter's axis family**: `per-cohort-specialization-LTC` (NEW 14th family — FIRST usage; convergent recommendation from /021 closeout Critic + LM Master + diary §6).
- **Cohort identifier**: LTC (single-symbol cohort).
- **Specialization dimension**: stateless direction-asymmetric BTC-trend regime gate (long-suppression-only at BTC ret_42 < −4%).
- **Prior 5 EXPLORATION families** (verified against `briefs-v1/exploration_catalog.md` HEAD `c4f6ac1`):
  - /017: `universe`
  - /018: `per-cohort-specialization-LINK`
  - /019: `per-cohort-specialization-ETH`
  - /020: `per-cohort-specialization-BTC`
  - /021: `methodology-pivot` (REUSE family `methodology`)
- **Rotation status**: **VALID** — `per-cohort-specialization-LTC` is in NONE of the prior 5 families. Per /018-/020 closeouts (codified rule), per-cohort specialization is the active cycle-3 methodology; LTC is a different COHORT from LINK/ETH/BTC (rotation by cohort, not by family literal-name).
- **One-sentence rationale**: LTC has the strongest **directionally asymmetric** OOS prior in v1 catalog (89% of OOS loss in longs / OOS shorts neutral); a long-suppression BTC-trend gate at 4% threshold targets the mechanism (LTC longs in BTC bear regime) confirmed by IS ORACLE EDA (both halves positive).

**NEW family declaration check (Critic Phase 7.5 Check 14 PASS requires Critic + LM Master + QR convergence on orthogonality)**: cohort-specialization-LTC is orthogonal to /018 LINK + /019 ETH + /020 BTC because (a) different COHORT, (b) different SPECIALIZATION (asymmetric one-sided gate vs symmetric /019 vs no gate /018+/020), (c) test of NEW prior class (ASYMMETRIC_ROTATION-INVERSE_IS-MARGINAL_OOS-CAT — the first IS-marginal cohort in v1). Justified per /021 closeout pre-committed Path Forward + LM Master /022 forward-binding.

### 0.7 LM Master Phase 4.5 coordination slot

LM Master Phase 4.5 fires AFTER this brief. Section 3.4 below RESERVES a placeholder for LM Master responses; integration is a Phase 5.5 BLOCK condition if LM Master fires after brief but brief doesn't echo each recommendation.

---

## Section 1 — Hypothesis

**Primary hypothesis (H1)**: A LightGBM model trained on **LTC-only data** (single-symbol cohort) at Model D's existing per-symbol config (`atr_tp=3.5, atr_sl=1.75, apply_r1=True`) with a **stateless long-suppression BTC-trend regime gate** (kill LTC long when BTC 14d return < −4%; LTC shorts UNRESTRICTED) applied as a post-hoc trade-stream filter will **flip LTC's catastrophic OOS prior** (−47.25%/−0.27 per-trade Sharpe) toward neutral-or-positive, producing per-trade OOS Sharpe ≥ −0.05 (i.e., Δ ≥ +0.21 vs LTC-in-pool OOS anchor −0.27 per-trade) AND avoiding /020 BTC's catastrophic basin-relocation pattern.

**Secondary hypothesis (H2 — INFORMATIONAL only; does NOT determine verdict)**: LTC's IS marginal-positive (+3.27%) is a half-split artifact (H1 +14.76% / H2 −11.49%), NOT a stable IS edge. Cohort isolation may amplify the H2 negative half (basin lands in the regime LTC OOS lives in), absent the gate. Gate intervention should produce IS+OOS sign agreement at positive (if /019 ETH+gate pattern generalizes).

**Falsification logic**:
- If gated LTC-only OOS per-trade Sharpe ≤ −0.40 (worse than anchor by ≥0.13) → gate insufficient to flip directional drag → NEGATIVE-INTRINSIC.
- If gated LTC-only OOS per-trade Sharpe ∈ (−0.40, −0.10] → gate works but small effect → INERT.
- If gated LTC-only OOS per-trade Sharpe ∈ (−0.10, +0.10] → gate flips drag toward neutral → PROMISING-INERT.
- If gated LTC-only OOS per-trade Sharpe ≥ +0.10 → gate flips drag toward positive → PROMISING.
- If gated LTC-only OOS per-trade Sharpe ≤ −0.55 → catastrophic basin-relocation (mirror /020 BTC pattern) → NEGATIVE-CATASTROPHIC.

**Critical interpretation note**: LTC OOS per-trade Sharpe anchor (−0.2670) is the only NEGATIVE per-trade anchor in v1 cycle-3 catalog (LINK +1.22%/trade, ETH +0.06%/trade, BTC +0.95%/trade, LTC −1.39%/trade). This is a **drag-removal experiment**: the verdict is "did the gate remove enough drag to clear NEGATIVE-INERT threshold." PROMISING bar is +0.10 absolute (Δ +0.37 from anchor) — high empirical bar.

**Per /021 H2 REFUTATION binding**: this hypothesis is framed at **parameter-basin level NOT feature level**. The mechanism story is "Optuna under LTC-isolated joint loss cannot escape direction-asymmetric BTC bear-regime drag without external orthogonal directional filter." NOT "LTC needs different features." The same 40 V1_FEATURE_COLUMNS_PRUNED features remain; the BTC-trend gate operates orthogonally on the trade stream.

---

## Section 2 — IS-Only Evidence (EDA results)

### 2.1 LTC prior class numerical evidence (Section 0.3 condensed)

All numbers from `analysis/iteration_v1-022/ltc_prior_class.py` output committed at `4eb091d`. Anchor: BASELINE_V1.md reports-v1/iteration_v1-baseline.

Headline: IS net PnL +3.27% (124 tr, WR 39.5%, avg z=+0.043); OOS net PnL **−47.25%** (34 tr, WR 29.4%, avg z=−1.557).

### 2.2 Direction asymmetry table

| Sample × Direction | n | net PnL % | avg PnL % | per-trade Sharpe |
|---|---|---|---|---|
| IS shorts | 50 | +14.10% | +0.282% | +0.040 |
| IS longs | 74 | −10.82% | −0.146% | −0.021 |
| OOS shorts | 15 | −1.81% | −0.120% | −0.024 |
| OOS longs | 19 | **−45.44%** | **−2.392%** | **−0.456** |

**Mechanism finding**: 89% of LTC OOS PnL loss is concentrated in LONG direction. OOS shorts are roughly neutral. This is **the strongest single-cohort directional asymmetry in v1 catalog**.

### 2.3 OOS monthly distribution (regime concentration check)

| Month | n trades | Net PnL % | Cumulative % |
|---|---|---|---|
| 2025-03 | 1 | −5.30% | −5.30% |
| 2025-04 | 3 | −1.08% | −6.38% |
| 2025-05 | 2 | −6.39% | −12.77% |
| 2025-07 | 1 | −4.81% | −17.58% |
| 2025-08 | 1 | **+10.55%** | −7.03% |
| 2025-09 | 1 | **+6.74%** | −0.29% |
| 2025-10 | 2 | +1.18% | +0.89% |
| 2025-11 | 2 | −8.43% | −7.54% |
| **2025-12** | **4** | **−13.29%** | −20.83% |
| **2026-01** | **6** | **−17.01%** | **−37.84%** |
| 2026-03 | 5 | +5.92% | −31.92% |
| 2026-04 | 4 | −9.45% | −41.37% |
| 2026-05 | 2 | −5.89% | −47.25% (final) |

**Regime concentration**: 2025-12 + 2026-01 = **−30.30% across 10 trades in 2 months** = 64% of OOS catastrophe. These months coincide with BTC's late-2025/early-2026 correction phase (BTC 14d return reached −15-20% in those windows). Motivates BTC-trend mechanism hypothesis.

### 2.4 IS-half stability

IS H1 (months 1-18) +14.76% over 69 trades. IS H2 (months 19-37) **−11.49%** over 55 trades. **IS itself is regime-bound, not stationary** — confirms IS marginal-positive is half-split artifact, not a stable IS edge.

This is structurally different from LINK (POSITIVE_EVERYWHERE — IS H1 and IS H2 both positive at large magnitude). LTC's IS marginal-positive is a 2-regime average, not a true positive prior.

### 2.5 Exit reason mix

| Sample | stop_loss | timeout | take_profit | total |
|---|---|---|---|---|
| IS | 70 (56.5%) | 23 (18.5%) | 31 (25.0%) | 124 |
| OOS | 19 (55.9%) | 11 (32.4%) | 4 (11.8%) | 34 |

**OOS take_profit collapse**: 25.0% IS → 11.8% OOS. OOS timeout rate spikes 18.5% → 32.4%. Pattern consistent with directional-asymmetry hypothesis: longs in BTC bear regime time out or hit SL more frequently in OOS than IS.

### 2.6 Gate ORACLE EDA — pre-registered fire rates

`analysis/iteration_v1-022/ltc_btc_trend_alignment.csv` (n=158 LTC trades total, with BTC ret_42 attached):

| Mechanism | IS kill rate (124 trades) | OOS kill rate (34 trades) |
|---|---|---|
| longsuppress_btc_trend@4% (selected) | 25.81% (32/124) | 14.71% (5/34) |

**F-AXIS-MECHANISM #3 pre-registered band** for /022 gate fire rate:
- IS: [15%, 40%] (mid 28%) — ORACLE EDA observed 25.81%; tighter than /019's [10%, 30%] band because LTC has more BTC bear-regime trades than ETH did.
- OOS: [5%, 30%] (mid 18%) — ORACLE EDA observed 14.71%; wider than IS because basin-relocation may shift OOS trade timing.

**Mechanism integrity check**: if observed IS fire rate < 15% → gate under-fires (4% threshold too loose for LTC). If observed IS fire rate > 40% → gate over-kills. If observed OOS fire rate < 5% → cohort exposure dominates; mechanism off; near-certain NEGATIVE.

### 2.7 Multi-mechanism comparison summary (Section 0.4 quantitative anchor)

Re-quoted from `analysis/iteration_v1-022/mechanism_candidates.csv` for verdict matrix at Section 8:

Mechanism = `longsuppress_btc_trend_gate@4%` projected IS Δ +10.79% / OOS Δ +12.45% PnL (raw ORACLE).

**EDA prediction (informational; mechanism story basis)**: gate applied to baseline LTC IS trades:
- IS kept: 92 trades / kept net PnL +14.07% (vs anchor +3.27%, Δ +10.80%)
- IS killed: 32 trades / killed net PnL −10.80% (gate kills net-negative LTC longs in BTC bear)
- OOS kept: 29 trades / kept net PnL −34.80% (vs anchor −47.25%, Δ +12.45%)
- OOS killed: 5 trades / killed net PnL −12.45% (small but high-impact-per-trade subset)

**Per-trade Sharpe Δ projection**: anchor LTC IS +0.0038 / OOS −0.2670. After gate (ORACLE): IS per-trade Sharpe ≈ +0.05 (Δ +0.05); OOS per-trade Sharpe ≈ −0.23 (Δ +0.04). Small OOS Sharpe shift — BUT raw PnL shift large +12.45pp. Discrepancy is because the 5 killed OOS trades had very large negative PnL (−2.49% per trade average) — kill rate is small but per-trade-impact is large.

**Predicted verdict cell BEFORE actual backtest** (mechanism remains causal but basin may relocate): see Section 5 priors.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1 mandatory)

**Declaration: HIGH-RISK.**

**Reason (one sentence)**: dropping Models A/C/D/E from the dispatch is a structural change to Optuna's training-objective domain (universe goes from 5 symbols to 1) AND adding a post-hoc gate alters the realized trade stream — both modifications change the OOS measurement substrate vs the baseline; LTC ASYMMETRIC_ROTATION-INVERSE prior with IS half-split sign reversal means cohort isolation alone is near-certainly catastrophic (mirror /020 BTC) absent the gate intervention.

**Mitigation (opt-in)**: NONE — single-seed-style EXPLORATION at ENSEMBLE_SIZE=3 inner seeds (fixed cycle-3 default per `feedback_v1_wall_clock_discipline_enforced.md`). Multi-seed validation deferred to /027 CONFIRMATION.

**HIGH-RISK cumulative tracker (cycle-3)**:
- /016: HIGH-RISK declared / NEGATIVE-catastrophic / >1σ OOS Δ
- /017: HIGH-RISK declared / NEGATIVE-anti-direction-INERT / OOS Δ within band
- /018: HIGH-RISK declared / PROMISING-INERT favorable / OOS Δ +0.16
- /019: HIGH-RISK declared / PROMISING / OOS Δ +0.65
- /020: HIGH-RISK declared / **NEGATIVE-CATASTROPHIC** / OOS Δ −0.86
- /021: HIGH-RISK declared / PROMISING-METHODOLOGY (methodology iter)
- **/022** (this iter): HIGH-RISK declared / outcome TBD

**Multi-seed binding check**: per `feedback_v1_n_eff_barrier_magnitude_curve.md` forward-binding mandate, 3 consecutive ≥1σ HIGH-RISK negatives triggers MANDATORY multi-seed. Current trajectory: /020 (>1σ neg) is the only ≥1σ neg in cycle-3 HIGH-RISK runs; /016 catastrophic and /017 anti-direction not counted (different axis families). NOT yet at 3-consecutive threshold; single-seed for /022 remains valid.

---

## Section 3 — Implementation Spec

### 3.1 Code change (single src/ file: `run_baseline_v1.py`)

```python
# After V1_ITER020_UNIVERSE definition (~line 171), add:
V1_ITER022_UNIVERSE: tuple[str, ...] = ("LTCUSDT",)
"""iter-v1/022 cohort: LTC-only with stateless long-suppression BTC-trend gate.

USER STRATEGIC PIVOT 2026-05-26 cycle-3 #7 EXPLORATION:
per-cohort-specialization-LTC (NEW 14th family). LTC is the WORST OOS contributor
in baseline (-47.25% / -0.27 per-trade Sharpe). LTC has the strongest directional
asymmetry of any v1 cohort: 89% of OOS loss in LONG direction; OOS shorts neutral.

Long-suppression BTC-trend gate at -4% on 14d BTC return kills LTC long entries
when BTC is in bear regime; LTC shorts UNRESTRICTED. IS ORACLE EDA shows
+10.79% IS / +12.45% OOS lift (both halves positive).

LOCAL to runner. assert_v1_universe() accepts {LTCUSDT}.
"""

#: Gate configuration constants (frozen for /022; tunable at /023+ verdict-conditional).
V1_ITER022_BTC_GATE_LOOKBACK_BARS: int = 42  # 14 days at 8h (matches /019)
V1_ITER022_BTC_GATE_THRESHOLD_PCT: float = 4.0  # -4% BTC 14d return (TIGHTER than /019's 8%)
V1_ITER022_BTC_GATE_ENABLED: bool = True
V1_ITER022_BTC_GATE_LONG_ONLY: bool = True  # NEW asymmetric mode (long-suppression only)
```

```python
# Add elif branch after V1_ITER021_UNIVERSE branch (~line 1738):
elif set(symbols) == set(V1_ITER022_UNIVERSE):
    # iter-v1/022: LTC-only single-cohort EXPLORATION + stateless long-suppression
    # BTC-trend gate (cycle-3 #7 of 10; per-cohort-specialization-LTC; NEW 14th family).
    # USER STRATEGIC PIVOT 2026-05-26: per-cohort specialization axis.
    #
    # Dispatch — ONLY Model D' (LTC-only; mirrors Model D semantics with apply_r1=True
    # which baseline Model D uses; ATR 3.5/1.75 matches Model D's per-symbol config).
    # Models A (BTC+ETH pooled), C (LINK), D (LTC pooled... wait, D is LTC-pooled
    # already; the rename is "Model D' = LTC-only at single-cohort dispatch"),
    # E (DOT) DROPPED — single-axis isolation.
    #
    # Single-axis isolation: SYMBOL DIMENSION (5 sym -> 1 sym + drop A/C/E)
    # AND post-hoc direction-asymmetric BTC-trend gate as the specialization.
    # The gate is STATELESS post-hoc trade-stream filter (no model retrain; mirrors
    # /019 BtcTrendFilterConfig pattern but asymmetric long-only mode).
    #
    # F-AXIS-MECHANISM #1: trades.csv must contain ONLY LTCUSDT rows.
    # F-AXIS-MECHANISM #2: LTC IS [80, 180] / OOS [20, 60] trade band.
    # F-AXIS-MECHANISM #3: gate fire rate IS in [15%, 40%] / OOS in [5%, 30%].
    assert set(symbols) == {"LTCUSDT"}, (
        f"iter-v1/022 guard: expected {{LTCUSDT}}, got {set(symbols)}"
    )
    results_dprime, faxm_dprime, _strat_dprime = run_model(
        "D' (LTC-only + R1 + R3 + BTC-trend long-suppress gate)",
        ("LTCUSDT",),
        atr_tp=3.5,
        atr_sl=1.75,
        apply_r1=True,  # NOTE: baseline Model D has R1; preserved
        n_trials=n_trials,
        ensemble_size=ensemble_size,
        oof_persist_path=OOF_PARQUET_PATH,
        feature_columns=active_feature_columns,
        bounds_profile=bounds_profile,
        **_r5_kwargs,
    )
    # Apply stateless long-suppression BTC-trend gate as post-hoc filter.
    # ASYMMETRIC: kills only LTC longs (dir=+1) when BTC ret_42 < -4%; LTC shorts UNRESTRICTED.
    btc_open_times, btc_closes = load_btc_klines_for_filter()
    gate_cfg = BtcTrendFilterConfig(
        lookback_bars=V1_ITER022_BTC_GATE_LOOKBACK_BARS,
        threshold_pct=V1_ITER022_BTC_GATE_THRESHOLD_PCT,
        enabled=V1_ITER022_BTC_GATE_ENABLED,
        long_only_mode=V1_ITER022_BTC_GATE_LONG_ONLY,  # NEW kwarg
    )
    results_dprime, gate_stats = apply_btc_trend_filter(
        results_dprime, btc_open_times, btc_closes, gate_cfg,
    )
    gate_stats_dict = gate_stats.as_dict()
    print(
        f"[iter-v1/022 BTC-trend long-suppress gate] "
        f"normal={gate_stats_dict['n_normal']} "
        f"warmup={gate_stats_dict['n_warmup']} "
        f"killed={gate_stats_dict['n_killed']}/{gate_stats_dict['n_total']} "
        f"fire_rate={gate_stats_dict['fire_rate']:.2%} "
        f"long_only={V1_ITER022_BTC_GATE_LONG_ONLY}"
    )
    _all_faxm_logs = faxm_dprime
    all_results = results_dprime
    _r5_model_results = [results_dprime]
```

**File 2 — `crypto_trade/strategies/ml/risk_v2.py`**: add `long_only_mode: bool = False` kwarg to `BtcTrendFilterConfig` and corresponding asymmetric branch in `apply_btc_trend_filter`:

```python
# In BtcTrendFilterConfig dataclass (~line 1346 of risk_v2.py):
@dataclass(frozen=True)
class BtcTrendFilterConfig:
    lookback_bars: int = 42
    threshold_pct: float = 8.0
    enabled: bool = True
    long_only_mode: bool = False  # NEW: when True, only kills longs in bear regime
                                  # (BTC ret < -threshold); shorts in bull regime
                                  # UNRESTRICTED. Symmetric (False) preserves /019 behavior.
```

```python
# In apply_btc_trend_filter (~line 1400):
# After computing btc_ret per-trade, modify the kill condition:
if cfg.long_only_mode:
    kill_long = (direction == 1) & (btc_ret < -cfg.threshold_pct)
    # No kill for shorts in long_only_mode
    kill_mask = kill_long
else:
    # Existing symmetric behavior:
    kill_long = (direction == 1) & (btc_ret < -cfg.threshold_pct)
    kill_short = (direction == -1) & (btc_ret > cfg.threshold_pct)
    kill_mask = kill_long | kill_short
```

**Backward compatibility**: default `long_only_mode=False` preserves bit-identical behavior for /019's `BtcTrendFilterConfig` call site. The /019 elif branch does not pass `long_only_mode` so the default applies.

**Diff scope** (2 src/ files):
- `run_baseline_v1.py`: ~80 lines added (constants + elif branch).
- `crypto_trade/strategies/ml/risk_v2.py`: ~10 lines added (1 dataclass kwarg + 1 conditional branch).

Zero changes to:
- `src/crypto_trade/features_v1/`
- `src/crypto_trade/strategies/ml/lgbm.py`
- `src/crypto_trade/strategies/ml/optimization.py`
- `src/crypto_trade/strategies/ml/walk_forward.py`
- `src/crypto_trade/labeling.py`
- v1 risk gate code (R1/R3 unchanged at Model D' which inherits Model D's R1+R3)

**Foundation guardrail**: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` UNCHANGED. No regression.

**Cross-track import note**: `risk_v2.py` is a STRATEGY HELPER module not a FEATURE module — v1 already imports it at /019 (HEAD `c4f6ac1` line ~258). Adding a backward-compatible kwarg to `BtcTrendFilterConfig` does not introduce new cross-track coupling. If Phase 6.0 Critic BLOCKs, fallback is vendor-copy as `risk_v1_gates.py` (deferred until BLOCKed).

### 3.2 CLI invocation

```bash
uv run python run_baseline_v1.py \
  --symbols LTCUSDT \
  --pruned-features \
  --ensemble-size 3 \
  --n-trials 18 \
  --iteration-label "v1-022" \
  --reports-dir reports-v1
```

(`--symbols LTCUSDT` triggers the new elif branch via `set(symbols) == set(V1_ITER022_UNIVERSE)`. `--pruned-features` activates V1_FEATURE_COLUMNS_PRUNED + bounds_profile=v1_pruned. `--ensemble-size 3` + `--n-trials 18` matches cycle-3 EXPLORATION budget. **No `--no-engineering-report`** per Critic /017/019/020/021 Rec #2/#1.)

### 3.3 Pinned values

- `feature_columns = list(V1_FEATURE_COLUMNS_PRUNED)` — 40 cols, passed explicitly (per `feedback_explicit_feature_columns.md`).
- `bounds_profile = "v1_pruned"` — same as baseline.
- `ENSEMBLE_SEEDS[0:3] = [42, 123, 456]` — same as baseline 3-seed EXPLORATION default.
- `r5_vol_target_enabled = False` (cycle-3+ default).
- `r5_kill_low_natr_enabled = False` (cycle-3+ default).
- `sample_weight_mode = "abs_pnl"` (baseline default).
- `sigma_source = "natr"` (baseline default).
- `apply_r1 = True` (mirrors Model D's baseline semantics; LTC trained in pool D with R1).
- `apply_r2 = False` (Model E only; LTC is not Model E).
- **GATE: `lookback_bars=42, threshold_pct=4.0, enabled=True, long_only_mode=True`** (frozen for /022).

### 3.4 LM Master Phase 4.5 Responses

LM Master advisory committed at `briefs-v1/iteration_v1-022/lgbm_advisor.md` (HEAD `79fd7fa`, 90 lines). Below: line-by-line QR responses with adopted/modified/rejected labels. Per `quant-iteration-v1.md` Phase 5.5 gate: brief MUST address each LM Master recommendation; failure to address triggers Phase 5.5 BLOCK.

**Track record entering /022** (LM Master §Context): H1 directional 0.5/4, methodology 2/2, alternative-branch utility 1/1 — confirms MEDIUM-HIGH confidence in calibrated recommendations.

#### 3.4.1 LM Master §1 — H2 REFUTATION binding compliance (BASIN-VECTOR evidence mandate)

**LM Master**: PASS framing check, but Phase 7.4 verdict assignment MUST cite **Optuna best_params shifts (basin vector evidence) via params_persist_path infrastructure from /021**, NOT feature_importance rank-shift evidence. Without this discipline, /021 H2 REFUTATION binding is at risk of soft-rebinding through linguistic slippage.

**QR**: **ADOPTED**. Updated Section 10 closeout protocol — Phase 7.4 LM Master post-mortem mandate added: any verdict assignment that cites mechanism MUST reference `optuna_studies/iter-v1-022_*.params.json` (basin-vector / best_params shift) as the primary evidence channel. Feature_importance rank-shifts are INFORMATIONAL ONLY at this iter (single-cohort Model D'-LTC-only feature_importance is well-defined — no pool-aggregation defect like /021 — but does NOT constitute basin-vector evidence). Critic Phase 7.5 watch list (Section 10.6) includes this check.

#### 3.4.2 LM Master §2 — ORACLE EDA validity confirmed but DO NOT cite Δ as predicted /022 outcome

**LM Master**: STATELESS carve-out applies for `longsuppress_btc_trend_gate@4%` (no deadlock risk; valid ORACLE EDA basis). BUT IS Δ +10.79% / OOS Δ +12.45% are post-hoc projections on baseline Model D LTC roster (pool-trained, 124 IS / 34 OOS); /022 retrains in single-cohort isolation so actual roster differs. Per /019 §3 empirical: gate efficacy compressed at retraining (EDA projected +0.30 OOS Sharpe; observed +0.6990 — actually MORE; Jaccard 0.04 = mechanism NOT roster-locked). For LTC, basin-relocation risk is real and BIDIRECTIONAL. QR should NOT cite ORACLE EDA Δ as predicted /022 outcome — only as mechanism validation evidence.

**QR**: **ADOPTED**. Section 1 hypothesis framing tightened — H1 falsification logic at Section 1 remains anchored on PER-TRADE Sharpe (F1) bands, NOT on raw PnL ORACLE EDA projections. Section 2.7 already explicitly carries the "EDA prediction is informational; mechanism story basis" caveat. F1 prediction band (Section 5 priors) does NOT cite ORACLE EDA Δ as anchor; instead anchors on basin-relocation-aware modal-INERT framework. Section 4 F1 cell already states "EDA prediction (informational)" — preserved. No further numerical edits needed; framing is already QR-LM aligned.

#### 3.4.3 LM Master §3 — Recalibrated verdict priors 8/12/40/20/10/10

**LM Master**: QR's 15/10/45/12/8/10 underweights negative tail. Reasons: (a) ASYMMETRIC threshold tuning IS harder than symmetric (LTC longs-only @ -4% narrower band than /019 ETH @ ±8%), (b) /020 ASYMMETRIC_ROTATION cohort went catastrophic — basin-relocation applies to LTC equally, (c) PROMISING tail at 25% needs basin to land favorably AND gate efficacy to exceed EDA upper bound ~10× — that's 8-15% not 25%. Recalibrated: PROMISING 8% / PROMISING-INERT 12% / INERT 40% (still modal) / NEGATIVE 20% / NEGATIVE-INTRINSIC 10% / NEGATIVE-CATASTROPHIC 10%.

**QR**: **ADOPTED**. Section 5 priors updated 15/10/45/12/8/10 → **8/12/40/20/10/10** with full LM Master rationale embedded. PROMISING+PROMISING-INERT favorable tail: 25% → **20%**. NEGATIVE total (clean+intrinsic+catastrophic): 30% → **40%**. INERT modal: 45% → **40%** (LM Master correctly notes gate is causally targeted, so pure null less likely than /020 BTC NEGATIVE-CATASTROPHIC at 60% INERT prior).

#### 3.4.4 LM Master §4 F-AXIS #2 — trade band tighter sub-band [70, 160] IS / [18, 50] OOS

**LM Master**: QR's [80, 180] / [20, 60] wider on lower bound. LM tighter: IS [70, 160] modal 100; OOS [18, 50] modal 28. Phase 7.4 measures exact roster.

**QR**: **ADOPTED as informational sub-band annotation; QR blocking band KEPT.** Section 4 F-AXIS #2 row updated with LM Master tighter informational sub-band [70, 160] IS / [18, 50] OOS modal 100/28 annotated separately. QR's [80, 180] / [20, 60] remains the F8 BREACH thresholds (blocking band) because: (a) LM tighter is informational projection, (b) QR's wider band is safer for verdict-call discrimination at single-seed lottery variance, (c) Phase 7.4 post-mortem will report exact roster against BOTH bands. Two-band reporting is dual-band annotation pattern from /019 §F-AXIS-MECHANISM precedent.

#### 3.4.5 LM Master §4 F-AXIS #3 — fire-rate band [15%, 40%] IS / [5%, 30%] OOS LOAD-BEARING; NEGATIVE-UNDER-FIRE if OOS <5%

**LM Master**: Predicted band [15%, 40%] IS / [5%, 30%] OOS LOAD-BEARING. NEGATIVE-UNDER-FIRE classification if OOS <5% (cohort-isolation already removed BTC-bear regime trades → gate effectively off).

**QR**: **ADOPTED.** Section 4 F-AXIS #3 row already has LOAD-BEARING marker (carried from QR Section 2.6 + LM /019 Rec § 9 forward-binding). Falsifier explicit: OOS fire rate < 5% → NEGATIVE-UNDER-FIRE verdict cell (Section 8 hierarchy preserved). Section 4 F-AXIS #3 LOAD-BEARING rationale tightened to cite LM Master §4 reasoning: "F1 anchor at extreme negative end of v1 cohorts (−0.27 per-trade), so F1 OOS Sharpe Δ has reduced diagnostic power around INERT/NEGATIVE boundary; F-AXIS #3 is mechanism-level, pre-registered, binary — strongest verdict-disambiguator." Critic Phase 7.5 watch list (Section 10.6) flags F-AXIS #3 fire-rate as priority diagnostic.

#### 3.4.6 LM Master §5 — n_eff_per_cell band [6, 10]

**LM Master**: Predicted n_eff_per_cell point estimate 8, band [6, 10]. QR's 7-modal / [4, 9] too pessimistic on lower bound. ACCEPT QR's 7-modal but widen upper to 10.

**QR**: **ADOPTED.** Section 4 F-AXIS-MECHANISM #4 band updated: QR point 7 / band [4, 9] → QR point 7 (preserved) / **band [4, 10]** (upper widened per LM). Section 5 + Section 13.7 pre-registered prediction priors echo this update. n_eff_per_cell is INFORMATIONAL only (per /017 closeout demotion); but band-band coverage matters for Phase 7.4 calibration tracking.

#### 3.4.7 LM Master §6 — Jaccard band narrowed to [0.03, 0.20] modal 0.06

**LM Master**: Per /018 LINK 0.04 / /019 ETH 0.04 / /020 BTC 0.084 empirical history — single-cohort retraining produces ~95% NEW roster regardless of cohort prior class at single-seed=42 n_trials=18 ENSEMBLE_SIZE=3 budget. Predicted LTC /022 vs baseline LTC-in-pool Jaccard: 0.04-0.10, modal 0.06. PROMISING-MECHANICAL classification (Jaccard ≥ 0.80) is NEAR-ZERO. QR's [0.05, 0.35] correct lower but wider than empirical — recommend narrow to [0.03, 0.20].

**QR**: **ADOPTED.** Section 7 Jaccard pre-registered band updated: QR [0.05, 0.35] → **LM Master [0.03, 0.20] modal 0.06** (LM empirical narrowing). PROMISING-MECHANICAL adjacency (Jaccard ≥ 0.80) classification in Section 6.7 + Section 8 verdict matrix retained — it is a structural classification rule, not a prediction. Modal 0.06 is the central prediction. Phase 7.4 LM Master post-mortem computes Jaccard.

#### 3.4.8 LM Master §7 — /023+ verdict-conditional pre-staging

**LM Master**: PROMISING (8%) → /023 DOT-only (LAST single-cohort untested). PROMISING-INERT (12%) → /023 DOT-only (cohort-coverage closure scientific value). INERT (40% modal) → /023 DOT-only. NEGATIVE (20%) or NEGATIVE-INTRINSIC (10%) → /023 NEW-family axis (funding-rate or per-cohort drawdown brake). NEGATIVE-CATASTROPHIC (10%) → /023 NEW-family axis (NOT closeout + jump to /027). DO NOT collapse cadence.

**QR**: **ADOPTED.** Section 11.7 (renumbered as Section 11.1 — verdict-conditional /023 routing matrix) updated with LM Master /023 staging matrix. Note: Section 11.1 already exists with verdict-conditional routing aligned with LM Master logic; LM Master §7 confirms QR /023 routing matrix EXCEPT QR's PROMISING-MECHANICAL cell was "NEW family (funding-rate)" — LM Master logic implies INERT-mapping at PROMISING-MECHANICAL ⇒ /023 = DOT-only. Updated Section 11.1 PROMISING-MECHANICAL row to **/023 = DOT-only** (alignment with LM Master closure logic — PROMISING-MECHANICAL is non-compoundable; cohort coverage closure is the scientific play). LM Master cadence-discipline mandate (NO closeout-jump-to-/027 on NEGATIVE-CATASTROPHIC) carried forward as binding constraint.

#### 3.4.9 LM Master §8 — Most important point (F-AXIS #3 LOAD-BEARING supersedes F1 magnitude at extreme negative anchor)

**LM Master**: /022's verdict is dominated by basin-relocation × gate fire-rate interaction. F-AXIS #3 fire-rate empirical observation is the LOAD-BEARING diagnostic, NOT F1 magnitude alone. F1 anchor at extreme negative reduces F1 diagnostic power around INERT/NEGATIVE boundary.

**QR**: **ADOPTED.** Section 4 F1 introduction updated with LM Master Section 8 hierarchy clarification: F-AXIS #3 supersedes F1 magnitude at extreme negative anchor. Section 8 verdict matrix hierarchy preserves: F-AXIS #3 (under-fire/over-kill cells) ranks above F1 magnitude (NEGATIVE-INTRINSIC/CATASTROPHIC). Section 8 entry rule strict adherence to thresholds — LM Master logic is structurally embedded.

#### 3.4.10 LM Master §9 — /027 3-specialist bundle (LINK + ETH+gate + LTC+gate) at LTC PROMISING

**LM Master**: If LTC PROMISING (8%) or PROMISING-INERT (12%): 3-specialist bundle on FULL POOL preserved (Option β extended). LINK-only specialist (+0.80 anchor at multi-seed) + ETH-only + symmetric gate (+0.50 anchor) + **LTC-only + asymmetric long-suppress gate (NEW; +0.30 anchor at multi-seed)**. Nominal Σ_independent +2.26. Realistic with correlation drag: **+1.20 to +1.50 OOS Sharpe** (raises ceiling vs 2-specialist /021 §7 estimate of +1.10-1.30). Multi-seed CONFIRMATION mandatory cross-correlation pre-validation: LTC+gate paths vs LINK paths AND vs ETH+gate paths — both < 0.40 required.

**QR**: **ADOPTED.** Section 11.6 bundle composition table updated with 3-specialist projection. Section 11.4 /027 target Δ updated: prior estimate +1.10-1.30 OOS Sharpe (2-specialist /021 §7) → **+1.20-1.50 OOS Sharpe** (3-specialist if LTC PROMISING or PROMISING-INERT). Cross-correlation pre-validation constraint < 0.40 between (LTC+gate, LINK) AND (LTC+gate, ETH+gate) seed paths carried as Phase 7.4 LM Master post-mortem mandate (already in /027 spec at Section 11.4).

#### 3.4.11 LM Master Closing — Critic Phase 7.5 priority items

**LM Master**: 4 priority items: (1) F-AXIS #3 fire-rate against pre-registered [15%, 40%] IS / [5%, 30%] OOS — LOAD-BEARING. (2) Layer C single-cohort feature_importance defect check. (3) Basin relocation evidence (Optuna best_params shift) — BASIN-VECTOR not feature-importance. (4) Jaccard against baseline LTC-in-pool — empirical [0.03, 0.20].

**QR**: **ADOPTED.** Section 10.6 (NEW — Critic Phase 7.5 Watch List) created with these 4 priority items as the binding Critic dispatch surface. Each item maps to a specific brief section: (1) → §4 F-AXIS #3 + §10 closeout protocol; (2) → §10.3 step 7 + §6.5 stateless gate sanity; (3) → §3.4.1 basin-vector mandate + §10.6; (4) → §7 Jaccard pre-registered band.

#### 3.4.12 Summary of edits made for LM Master ADOPTION

| LM § | Action | Brief location edited |
|---|---|---|
| §1 BASIN-VECTOR | ADOPT | §10.6 (NEW Critic Phase 7.5 watch list); §3.4.1 |
| §2 ORACLE EDA caveat | ADOPT | §1 framing (preserved); §2.7 (already explicit) |
| §3 priors 8/12/40/20/10/10 | ADOPT | §5 (replace numerics) |
| §4 F-AXIS #2 sub-band | ADOPT informational | §4 F-AXIS #2 row |
| §4 F-AXIS #3 LOAD-BEARING | ADOPT | §4 F-AXIS #3 row (preserved); §10.6 |
| §5 n_eff band [4, 10] | ADOPT | §4 F-AXIS-MECHANISM #4; §13.7 |
| §6 Jaccard [0.03, 0.20] modal 0.06 | ADOPT | §7 Jaccard row |
| §7 /023 staging | ADOPT | §11.1 routing matrix |
| §8 F-AXIS #3 supersedes F1 hierarchy | ADOPT | §4 F1 intro; §8 hierarchy (already aligned) |
| §9 /027 3-specialist +1.20-1.50 | ADOPT | §11.6 bundle composition table; §11.4 target Δ |
| Closing Critic 4 items | ADOPT | §10.6 (NEW) |

**No rejections. No partial modifications beyond §4 F-AXIS #2 dual-band annotation pattern (informational + blocking).** Track-record-warranted MEDIUM-HIGH confidence in LM Master calibration justifies full adoption of numerical recalibrations.

### 3.5 Axis Family Declaration (v1 mandatory)

- **Axis family**: `per-cohort-specialization-LTC` (NEW 14th family declaration; FIRST usage; convergent recommendation from /021 closeout Critic + LM Master + diary §6).
- **Cohort + Specialization pairing**: cohort=LTC, specialization=stateless long-suppression BTC-trend gate (lookback=42 bars, threshold=−4%, asymmetric one-sided, post-hoc filter).
- **Single-axis isolation verified**: ONLY SYMBOL DIMENSION + GATE changes — per `feedback_v1_per_cohort_exploration_strategy.md` per-cohort methodology, COHORT + ONE SPECIALIZATION is the single-axis unit. All other knobs frozen at baseline Model D config.
- **Phase 7.5 Critic Check 14 PASS requires**: NEW family declaration is structurally orthogonal to /018 LINK + /019 ETH + /020 BTC because (a) different COHORT, (b) different SPECIALIZATION (asymmetric long-only gate, NOT symmetric /019 gate, NOT no-gate /018+/020), (c) NEW prior class tested (ASYMMETRIC_ROTATION-INVERSE_IS-MARGINAL_OOS-CAT — first IS-marginal cohort).

### 3.6 Wall-Clock Estimate (CRITICAL — Phase 5.5 BLOCK if missing or > 1.6h)

**Predicted wall-clock: 26 minutes total.**

Decomposition:
- Anchor: /018/019/020 single-cohort at ENSEMBLE_SIZE=3 + n_trials=18 + V1_FEATURE_COLUMNS_PRUNED ran 25 min total per their diaries.
- LTC-only (1 sym, identical scale config) projected: **25 min** (linear).
- BTC-trend gate (long-only mode) post-hoc filter overhead: **~1 min** (numpy boolean mask on ~150 IS + ~40 OOS trades + 1 BTC kline CSV load; identical to /019 overhead).
- Methodology + reporting overhead: ~3 min (post-hoc PSR, DSR on 1-model trade roster).
- **Total projected: 26 minutes.**

**Margin vs 2h cap = 1h:34min (78% margin).**
**Margin vs 1.6h Phase 5.5 BLOCK threshold = 70+ minutes of buffer.**
**45-minute internal kill-switch (per Section 10.5) provides 1.7× projected wall-clock buffer.**

---

## Section 4 — Falsifiers (F1-F8 + F-AXIS-MECHANISM)

Per `feedback_v1_per_cohort_exploration_strategy.md`: per-cohort EXPLORATION. F1 + F8 thresholds adapt to LTC-only cohort scale, NOT portfolio-level. Per `feedback_v3_promising_mechanical_subtype.md` + /019 closeout LESSON #3 + LM Master /022 §8 hierarchy: F-AXIS-MECHANISM #3 (fire-rate band) is LOAD-BEARING for verdict disambiguation.

**Falsifier hierarchy at /022 (LM Master §8 ADOPTED, Section 3.4.9)**: F-AXIS-MECHANISM #3 fire-rate SUPERSEDES F1 magnitude at extreme negative anchor. F1 anchor (LTC OOS per-trade Sharpe −0.27) is at the negative extreme of v1 cohorts, so F1 OOS Sharpe Δ has reduced diagnostic power around the INERT/NEGATIVE boundary. F-AXIS #3 is mechanism-level, pre-registered, binary — it is the strongest single verdict-disambiguator. Critic Phase 7.5 should evaluate F-AXIS #3 BEFORE F1 magnitude when assigning verdict cell.

### F1 — LTC-only OOS per-trade Sharpe Δ vs LTC-in-pool OOS per-trade Sharpe anchor

**Anchor**: LTC-in-pool OOS per-trade Sharpe = **−0.2670** (from `ltc_prior_class.csv`).

(Note: brief uses per-trade Sharpe instead of /019's monthly Sharpe proxy because per-trade is what `comparison.csv` "sharpe" field actually reports at single-cohort scale; this anchor is the literal `sharpe_per_trade` column at OOS_DIR for LTC. Anchor frame consistency is enforced by post-Phase-7 engineering_report.md.)

(LM Master §8 hierarchy note: F1 magnitude has reduced diagnostic power at extreme negative anchor; F-AXIS #3 fire-rate is the LOAD-BEARING verdict-disambiguator for /022.)

| Verdict cell | F1 OOS per-trade Sharpe Δ band | Absolute OOS per-trade Sharpe |
|---|---|---|
| **PROMISING** | Δ ≥ +0.37 | ≥ +0.10 |
| **PROMISING-INERT** | Δ ∈ [+0.17, +0.37) | ∈ [−0.10, +0.10) |
| INERT | Δ ∈ [−0.13, +0.17) | ∈ [−0.40, −0.10) |
| **NEGATIVE** | Δ ≤ −0.13 | ≤ −0.40 |
| Catastrophic-NEGATIVE | Δ ≤ −0.28 | ≤ −0.55 |

**Calibration**: PROMISING bar (Δ ≥ +0.37 absolute) is HIGH — anchor is the worst per-trade Sharpe of any v1 cohort. Gate must remove drag substantially. ORACLE EDA projects modest per-trade Sharpe Δ +0.04 — well below PROMISING band; PROMISING-INERT (Δ ∈ [+0.17, +0.37)) is the realistic high-end if mechanism works as intended.

### F3 — LTC-only IS per-trade Sharpe Δ vs LTC-in-pool IS per-trade Sharpe anchor

**Anchor**: LTC-in-pool IS per-trade Sharpe = **+0.0038**.

| Verdict cell | F3 IS per-trade Sharpe Δ band | Absolute IS per-trade Sharpe |
|---|---|---|
| **PROMISING** | Δ ≥ +0.20 | ≥ +0.20 |
| INERT | Δ ∈ [−0.20, +0.20] | ∈ [−0.20, +0.20] |
| **NEGATIVE** | Δ ≤ −0.20 | ≤ −0.20 |
| Catastrophic-NEGATIVE | Δ ≤ −0.30 | ≤ −0.30 |

**EDA prediction (informational)**: ORACLE EDA projects IS per-trade Sharpe rises from +0.0038 to ~+0.05 (Δ +0.05) under gate. /020 BTC catastrophic showed actual basin-relocation produced IS Sharpe Δ −0.47 from a +0.30 anchor (1σ negative regardless of EDA). PROMISING (Δ ≥ +0.20) is plausible IS but not guaranteed; INERT is the realistic modal IS outcome.

### F2 — Embargo/look-ahead PASS (structural; automatic)

`walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` UNCHANGED. BTC gate is past-only (np.searchsorted right-1 with 42-bar warmup floor). PASS by construction.

### F4 — Feature ADF stationarity (informational; no new features)

40 V1_FEATURE_COLUMNS_PRUNED unchanged. Per /021 H2 REFUTATION, feature stack is appropriate regardless of cohort. INFORMATIONAL.

### F5 — PSR_monthly_vs_0 OOS (basin-health signal)

LTC-only OOS PSR_monthly_vs_0:
- Baseline anchor (5-sym OOS portfolio) PSR_monthly_vs_0 = 0.989.
- LTC-only OOS at 13 OOS months single-symbol distribution; predicted band **[0.10, 0.50]** for LTC-only OOS PSR after gate intervention. Wider band than ETH/LINK because LTC's structural prior is catastrophic-negative.

**Catastrophic if** PSR_monthly_vs_0 < 0.05 → indicates LTC OOS still mostly negative after gate (gate failed to flip drag).

### F6 — Per-symbol IS direction (vacuous — only 1 symbol)

LTC-only model has only LTC trades. F6 PASS by construction.

### F7 — Per-symbol IS/OOS sign agreement (LTC only)

LTC IS and OOS PnL same-sign positive for INERT-or-better verdict.

**LTC-specific note**: anchor (LTC-in-pool) has IS +3.27% / OOS −47.25% — **already in IS-OOS sign disagreement** (LTC's structural pattern). F7 PASS at gated /022 requires gate flipping OOS to positive OR at minimum to ≥ −5% net PnL. F7 PASS condition is **the strongest single mechanism check** for /022 — does the gate flip LTC's directional asymmetric drag?

### F8 — LTC-only trade count band (cohort + gate scale)

**Anchor**: LTC-in-pool trade counts in baseline = 124 IS / 34 OOS.

LTC-only at ENSEMBLE_SIZE=3 (not 5) at gate fire rate 15-40% IS: predicted trade band:

| F8 cell | IS trade band | OOS trade band |
|---|---|---|
| PASS | IS ∈ [80, 180] | OOS ∈ [20, 60] |
| **F8 BREACH-low** | IS < 80 OR OOS < 20 | (cohort under-fires or gate over-kills) |
| **F8 BREACH-high** | IS > 180 OR OOS > 60 | (gate under-fires or Model D' over-trades) |

OOS lower bound 20 = baseline LTC OOS 34 - gate kill ~15% - margin; OOS upper bound 60 = baseline LTC OOS 34 × ~2× ensemble factor margin.

### F-AXIS-MECHANISM (compound 4-sub-check)

The single-axis isolation is the SYMBOL DIMENSION + STATELESS GATE.

- **F-AXIS #1 — Dispatch correctness**: ONLY Model D' runs; trades.csv contains only LTCUSDT rows (zero rows for BTC/ETH/LINK/DOT/SOL). PASS criterion: `df['symbol'].unique() == ['LTCUSDT']`.
- **F-AXIS #2 — LTC trade-count and PnL within band** (DUAL-BAND ANNOTATION per LM Master §4 ADOPTED, Section 3.4.4):
  - **QR blocking band (F8 BREACH thresholds; preserved)**: LTC IS trades ∈ [80, 180], LTC OOS trades ∈ [20, 60].
  - **LM Master informational sub-band (annotation only)**: LTC IS [70, 160] modal 100; LTC OOS [18, 50] modal 28.
  - LTC OOS net PnL > −20% preferred (flips ASYMMETRIC_ROTATION-INVERSE prior). LOAD-BEARING per /020 Lesson — basin relocation can shift trade roster materially; trade count outside QR blocking band indicates F8 BREACH (verdict cells NEGATIVE-OVER-KILL / NEGATIVE-UNDER-FIRE candidates). Phase 7.4 LM Master post-mortem reports observed count against BOTH bands.
- **F-AXIS #3 — Gate fire-rate within pre-registered band** **[LOAD-BEARING per LM Master /019 Rec § 9 carry-forward + LM /022 §4-§8 reaffirmation, Section 3.4.5 + 3.4.9 ADOPTED]**: IS gate fire rate ∈ [15%, 40%], OOS gate fire rate ∈ [5%, 30%] per Section 2.6 ORACLE EDA. Failure indicates gate threshold or BTC indicator computation broken.
  - **LOAD-BEARING rationale (LM /022 §8)**: F1 anchor at extreme negative end (−0.27 per-trade) → F1 OOS Sharpe Δ has reduced diagnostic power around INERT/NEGATIVE boundary; F-AXIS #3 is mechanism-level, pre-registered, binary — strongest single verdict-disambiguator. Critic Phase 7.5 evaluates F-AXIS #3 BEFORE F1 magnitude.
  - **NEGATIVE-UNDER-FIRE classification (LM /022 §4 + §8)**: if observed OOS fire rate < 5% → cohort-isolation has already removed BTC-bear regime trades; gate effectively OFF; basin produced LTC-only roster without bear-regime exposure → mechanism cannot fire → NEGATIVE-UNDER-FIRE verdict cell (Section 8 hierarchy).
- **F-AXIS-MECHANISM #4 — n_eff_per_cell band [4, 10]** **[INFORMATIONAL per /017 closeout demotion; LM Master §5 ADOPTED, Section 3.4.6 — upper widened 9 → 10]**: LTC-only cohort + 25% gate fire rate IS → LTC IS trades post-gate ~93 (vs LINK-only /018 ~154; ETH-only /019 ~120). Smaller training rows + post-hoc gate roster trim → narrower Optuna trial diversity. /018 hit n_eff=9, /019 hit n_eff=9 (LM /019 prediction nominal), /020 hit n_eff=9 (exact match). QR prediction for /022: n_eff_per_cell point estimate 7 (LTC's lower IS trade volume + 25% kill rate); **band [4, 10]** (LM widened upper from 9 to 10; LM modal 8). INFORMATIONAL only.

### F-PORTFOLIO (informational; cannot determine verdict)

Portfolio-level Sharpe (LTC-only = 1 model = portfolio) compared to v1 baseline portfolio +0.6637. INFORMATIONAL ONLY per per-cohort methodology.

---

## Section 5 — Predicted Verdict Distribution (FLAT priors per cycle-3 lessons)

Per /016/017/018/019/020/021 closeouts: cycle-3 LM Master + QR mechanism-level predictions track FLAT priors at EXPLORATION single-seed level. /020 BTC priors (INERT 60% modal) catastrophically REFUTED by actual NEGATIVE-CATASTROPHIC outcome.

**Verdict priors UPDATED 2026-05-26 per LM Master §3 recalibration** (Section 3.4.3 ADOPTED): QR initial 15/10/45/12/8/10 → **LM Master 8/12/40/20/10/10**. LM Master rationale: (a) ASYMMETRIC threshold tuning IS harder than symmetric — LTC longs-only @ -4% targets narrower band than /019 ETH @ ±8%, (b) /020 BTC ASYMMETRIC_ROTATION precedent went catastrophic — basin-relocation mechanism applies to LTC equally, (c) PROMISING tail at 25% (QR initial) requires basin to land favorably AND gate efficacy to exceed ORACLE EDA upper bound by ~10× — that's 8-15%, not 25%.

**Verdict prior 20/40/40** (modal INERT 40%; favorable tail tightened 25%→20%; negative tail widened 30%→40%):

- **PROMISING (Δ ≥ +0.37 per-trade Sharpe)**: **8%** (QR initial 15% → LM 8%) — gate flips both halves to positive at single-seed=42 Optuna trajectory; matches /019 ETH+gate pattern. ORACLE EDA projects modest Δ (~+0.04); large Δ requires basin to land favorably AND gate efficacy to be at upper EDA estimate.
- **PROMISING-INERT (Δ ∈ [+0.17, +0.37))**: **12%** (QR initial 10% → LM 12%) — gate reduces drag enough to clear OOS Sharpe to ≥ −0.10 absolute but not into positive territory.
- **INERT (Δ ∈ [−0.13, +0.17))**: **40%** (QR initial 45% → LM 40%) — modal cell per per-cohort methodology; basin relocation absorbs some gate lift; single-seed lottery wide. LM correctly notes: gate is causally targeted, so pure null less likely than /020 BTC NEGATIVE-CATASTROPHIC at 60% INERT prior.
- **NEGATIVE clean (Δ ≤ −0.13)**: **20%** (QR initial 12% → LM 20%) — basin relocates to worse OOS subset (mirror /020 pattern at LTC scale); gate fire rate within band but absolute OOS still ≤ −0.40.
- **NEGATIVE-INTRINSIC (Δ ≤ −0.28 + F-AXIS #3 PASS)**: **10%** (QR initial 8% → LM 10%) — gate works mechanically but LTC drag isn't BTC-trend-conditional in OOS regime.
- **NEGATIVE-CATASTROPHIC (Δ ≤ −0.28; mirror /020 catastrophic)**: **10%** (preserved) — mirror /020 BTC outcome; ASYMMETRIC_ROTATION cohort × pure isolation pathway.

**Predicted modal cell**: INERT 40%. Predicted favorable tail (PROMISING + PROMISING-INERT) = **20%** (LM tighter than QR 25%). Predicted negative tail (NEGATIVE + NEGATIVE-INTRINSIC + NEGATIVE-CATASTROPHIC) = **40%** (LM wider than QR 30%). **NOTE**: distribution weighted toward NEGATIVE relative to /019's modal-INERT priors because LTC's anchor is the worst-in-portfolio AND /020 confirmed basin-relocation catastrophic for asymmetric-rotation cohorts AND LM Master MEDIUM-HIGH calibration confidence track record (post-/021 H1 0.5/1 directional credit) warrants full prior adoption.

Two specific mechanism predictions (informational):

1. **Gate fire rate at observation**: predicted IS 25.8%, OOS 14.7% (per ORACLE EDA; /019 had predicted-observed gap ~0pp). If IS observed < 15% or > 40%, gate threshold or computation broken (F-AXIS #3 falsifier). LM Master §5 widens F-AXIS-MECHANISM #4 n_eff band: QR point 7 / band [4, 9] → **point 7 / band [4, 10]** (upper widened from 9 to 10).
2. **F-AXIS #2 trade band**: at OOS predicted ~30 trades after gate (cf. baseline 34 OOS LTC trades pre-gate; 3-seed ensemble factor ~1.0x at single-cohort + 14.7% gate kill ~ -5 trades). LM Master tighter sub-band annotation: IS [70, 160] modal 100; OOS [18, 50] modal 28 (informational only; QR F8 BREACH band [80, 180] / [20, 60] is blocking).

---

## Section 6 — Failure Modes

### 6.1 Single-cohort basin lottery at single-seed=42 EXPLORATION (per /020 lesson)

LTC-only at ENSEMBLE_SIZE=3 + n_trials=18 + single-seed=42 = potentially basin-locked. LTC has ASYMMETRIC_ROTATION-INVERSE prior with the **worst** OOS contribution in v1 — basin lottery downside band is theoretically widest of any cohort. /020 BTC precedent shows ASYMMETRIC_ROTATION cohorts can land in structurally adverse OOS subsets under pure isolation. The gate is the mitigation hypothesis.

**Mitigation**: gate intervention is mechanically tied to a documented IS pattern (direction asymmetry: 89% OOS loss in longs) AND cross-year-stable in ORACLE EDA (both IS and OOS halves positive at 4% threshold). /027 multi-seed will dissolve basin-lottery uncertainty.

### 6.2 Gate over-kills OOS

If observed OOS gate fire rate > 30% (above pre-registered F-AXIS #3 upper band), gate is over-killing OOS. Possible cause: OOS regime has higher BTC volatility than IS, triggering more crosses of −4%. Result: F8 OOS trade count breaches low; verdict cell NEGATIVE-OVER-KILL.

### 6.3 Gate under-fires OOS

If observed OOS gate fire rate < 5%, gate is effectively off. LTC-only cohort isolation alone (without gate intervention) at ASYMMETRIC_ROTATION-INVERSE prior → high probability NEGATIVE-CATASTROPHIC (mirror /020 BTC). Verdict: NEGATIVE-COHORT-EXPOSURE / NEGATIVE-UNDER-FIRE.

### 6.4 LTC drag is not BTC-trend-conditional

If gated LTC OOS per-trade Sharpe ≤ −0.40 (NEGATIVE-INTRINSIC) AND F-AXIS #3 PASS (gate fires within band), the hypothesis that LTC drag is BTC-trend-conditional is FALSIFIED. LTC drag would then be LTC-intrinsic (e.g., LTC liquidity regime, LTC-specific bear-cycle pattern) — load-bearing finding for /023+ axis selection (e.g., LTC-specific volatility-regime gate, LTC-on-chain features deferred to feature-family axis cycle-4).

### 6.5 Stateless gate deadlock risk (per Critic /019/020 Rec + A8 anti-pattern)

The gate is **stateless by design**:
- Decision at each signal time uses only past BTC data (np.searchsorted right-1 with 42-bar warmup floor).
- No persistent state. No drawdown-conditional ON/OFF. No cumulative counter.
- Asymmetric mode (long-only) is a stateless modification of the kill condition — no state added.
- The v2 `apply_btc_trend_filter` is a post-hoc trade-stream pass; deadlock-impossible by construction.

Verified at code-review time (Phase 6.0 will re-check).

### 6.6 Wall-clock breach (low probability)

26 min predicted with 78% margin. Even worst-case 2× linear scaling stays under 1h. Kill-switch at 45 min provides additional safety. No realistic path to 2h breach.

### 6.7 PROMISING-MECHANICAL adjacency risk (LM Master /019 Rec + Critic Check 14 watch)

The gate is a **NEW asymmetric variant** of v2/019 + v1/019 primitive, applied post-hoc to a retrained trade stream. **If the verdict is PROMISING but the kept-trade roster preserves >80% of the EDA baseline kept-trade roster (trade_id Jaccard)**, classify the iteration as PROMISING-MECHANICAL — a non-compoundable signal source. Phase 7.4 LM Master post-mortem will verify via trade_id Jaccard between baseline LTC roster (filtered for gate-applied) and /022 backtest kept set. This adjacency does NOT change the Phase 5 brief design; it informs Phase 7.4 + Phase 7.5 classification and /027 bundle treatment.

Note: /020 BTC showed Jaccard 0.084 (basin relocates), so PROMISING-MECHANICAL is LESS LIKELY than PROMISING-NEW-EDGE at single-cohort isolation — but the gate primitive is RE-USE, so adjacency must be checked.

### 6.8 Cross-track import contamination risk (per /019 Phase 5.5 carry-forward)

Adding `long_only_mode` kwarg to `BtcTrendFilterConfig` in `risk_v2.py` is a BACKWARD-COMPATIBLE addition (default False = bit-identical /019 behavior). Per /019 Phase 5.5 PASS, v1's import of `crypto_trade.strategies.ml.risk_v2.{...}` was accepted because `risk_v2.py` is a STRATEGY HELPER NOT a feature module. Phase 6.0 Critic re-verifies; if BLOCKed, fallback is vendor-copy `risk_v1_gates.py` (deferred until BLOCKed). Code-quality cost of vendor-copy ≈ 60 lines; trade-off vs cross-track import already approved at /019.

---

## Section 7 — Optional / informational metrics

- LTC-only DSR: expected LOWER than baseline portfolio DSR (single-symbol = lower n_obs). INFORMATIONAL per EXPLORATION rule + `feedback_v3_dsr_mode_artifact.md` (EXPLORATION-mode DSR is regime-specific artifact).
- LTC-only PBO via CSCV: deferred (single-cohort = limited n_obs).
- LTC-only PSR_monthly_vs_1: expected to be very low (anchor is −0.27 per-trade; matching +1.0 unlikely at single-symbol EXPLORATION). INFORMATIONAL.
- Pareto front: N/A (single-seed EXPLORATION).
- Gate stats JSON: `gate_stats_dict` written to engineering_report.md per /017/019/020/021 Rec.
- LTC Jaccard vs baseline LTC roster (combined IS+OOS): **pre-registered band [0.03, 0.20] modal 0.06 per LM Master §6 ADOPTED (Section 3.4.7)** — narrowed from QR initial [0.05, 0.35]. LM rationale: empirical history /018 LINK 0.04 / /019 ETH 0.04 / /020 BTC 0.084 shows single-cohort retraining produces ~95% NEW roster regardless of cohort prior class at single-seed=42 n_trials=18 ENSEMBLE_SIZE=3 budget; PROMISING-MECHANICAL classification (Jaccard ≥ 0.80) is NEAR-ZERO probability. Phase 7.4 LM Master computes this.

---

## Section 8 — Verdict Matrix (per-cohort + asymmetric gate variant)

| Verdict cell | F1 (LTC OOS per-trade Δ) | F3 (LTC IS Δ) | F-AXIS-MECHANISM | F7 sign | Action |
|---|---|---|---|---|---|
| **PROMISING** | Δ ≥ +0.37 | any | #1+#2+#3 PASS | IS+OOS positive | LTC-only specialist + asymmetric gate CARRIED to /027 substrate |
| **PROMISING-INERT** | Δ ∈ [+0.17, +0.37) | any | #1+#2+#3 PASS | IS+OOS sign-mixed favorable | CONDITIONALLY CARRIED to /027; re-evaluate multi-seed |
| **PROMISING-INERT-no-effect** | |Δ| < 0.05 | any | #3 fire rate within band BUT directional Δ not realized | mixed signs | gate had no measurable effect; document; deprioritize at /027 |
| **PROMISING-MECHANICAL** | Δ ≥ +0.17 BUT Jaccard ≥ 0.80 | any | #1+#2+#3 PASS | aligned | Non-compoundable signal; /027 substrate decision deferred (`feedback_promising_mechanical_subtype.md`) |
| **NEGATIVE-INERT** | Δ ∈ (−0.28, −0.13] | any | #1+#2 PASS | mixed | LTC-only specialist + gate DROPPED for /027 |
| **NEGATIVE-INTRINSIC** | Δ ≤ −0.28 + F-AXIS #3 PASS | any | #1 PASS | OOS negative | LTC drag NOT BTC-trend-conditional; load-bearing finding for /023+ |
| **NEGATIVE-CATASTROPHIC** | Δ ≤ −0.28 + magnitude | any | #1 PASS | OOS negative | LTC structural prior dominates; gate insufficient (mirror /020 BTC) |
| **NEGATIVE-OVER-KILL** | any | any | #3 fire rate > 30% OOS | starved | gate over-aggressive; redesign threshold at /023 |
| **NEGATIVE-UNDER-FIRE** | any | any | #3 fire rate < 5% OOS | cohort exposure dominates | gate effectively off; cohort-alone NEGATIVE confirmed |
| **NEGATIVE-IS-COLLAPSE** | Δ_OOS any | Δ_IS ≤ −0.30 | #1 PASS | IS catastrophic | IS basin inversion at LTC-only (H2-half dominates) |
| **NEGATIVE-DISPATCH** | any | any | #1 FAIL | n/a | Implementation defect; BLOCK-PENDING-FIX candidate |

**Section 8 entry rule**: must select EXACTLY ONE cell. Strict adherence to thresholds. Hierarchy when multiple cells could apply: NEGATIVE-DISPATCH > NEGATIVE-OVER-KILL/UNDER-FIRE > NEGATIVE-IS-COLLAPSE > NEGATIVE-INTRINSIC > NEGATIVE-CATASTROPHIC > NEGATIVE-INERT > PROMISING-MECHANICAL > PROMISING-INERT-no-effect > PROMISING-INERT > PROMISING.

**Anchor frame integrity**: F1 and F3 read `comparison.csv` "sharpe" field as **per-trade Sharpe** (the underlying daily/monthly Sharpe granularity at single-cohort is mathematically equivalent if measurement window is fixed). Anchor LTC-in-pool per-trade Sharpe (IS +0.0038 / OOS −0.2670) is pre-computed at `ltc_prior_class.csv`. Per `feedback_v1_anchor_frame_integrity.md` (cycle-2 carry-forward from /020 Lesson #5), no mixed-frame Δ rule applies; all comparisons use per-trade Sharpe at this single-cohort scale.

---

## Section 9 — Library Stack

No changes to library versions. Inheriting cycle-3 baseline:
- `mlfinlab==1.4` (CPCV / meta-labeling utilities)
- `pypbo` (PBO via CSCV)
- `fracdiff>=0.10` (FracdiffStat)
- `statsmodels` (ADF testing)
- `lightgbm>=4.0` (LightGBM regression)
- `optuna>=3.0` (Bayesian hyperparameter search)
- `crypto_trade.strategies.ml.risk_v2.{apply_btc_trend_filter, BtcTrendFilterConfig, load_btc_klines_for_filter}` — RE-used as post-hoc filter (no new dependency; one new kwarg `long_only_mode`).

---

## Section 10 — Implementation Spec (CRITICAL detail)

### 10.1 No `--no-engineering-report` flag at launch (Critic /017/019/020/021 Rec)

Engineer Phase 6 MUST generate `reports-v1/iteration_v1-022/engineering_report.md`. Run command excludes `--no-engineering-report` flag. **Engineering report BLOCKING per Critic /020/021 Rec #1**: no Phase 7.5 Critic dispatch without engineering_report.md present (3rd consecutive cycle-3 ENGINEERING-REPORT contract enforced).

### 10.2 Reports artifacts expected

After backtest completion:

```
reports-v1/iteration_v1-022/
├── comparison.csv              # IS/OOS metrics (sharpe, dsr, psr, n_eff rows, etc.)
├── engineering_report.md       # Engineer Phase 6 summary + gate fire stats + Jaccard prep
├── f_axis_mechanism.csv        # F-AXIS-MECHANISM #1+#2+#3 rows
├── in_sample/
│   ├── trades.csv              # ONLY LTCUSDT rows (verify F-AXIS #1)
│   ├── per_symbol.csv          # ONLY LTCUSDT row
│   ├── monthly_pnl.csv
│   ├── daily_pnl.csv
│   ├── per_regime.csv
│   ├── dsr.json
│   ├── adf_test.csv
│   ├── ic_matrix.csv
│   ├── feature_importance_*.csv (NEW per /021 per-month accumulator)
│   └── quantstats.html
└── out_of_sample/
    └── (same structure)
```

Engineer also writes gate stats (n_killed / n_total / fire_rate / long_only=True) to engineering_report.md.

### 10.3 Pre-flight verification (Engineer in Phase 6 setup)

Before launching backtest:
1. Verify `LTCUSDT_8h_features.parquet` exists in `data/features/` (or `data/features_v1/`) and is fresh.
2. Verify `data/BTCUSDT/8h.csv` has close_time within 16h of measurement time (gate reads BTC closes; stale BTC data corrupts gate).
3. Verify `data/LTCUSDT/8h.csv` close_time within 16h.
4. Verify branch is `iteration-v1/022` and HEAD is post-brief commit.
5. Verify `run_baseline_v1.py` HEAD has V1_ITER022_UNIVERSE + import for risk_v2 BTC filter + elif branch.
6. Verify `risk_v2.py` HEAD has `long_only_mode` kwarg in BtcTrendFilterConfig + asymmetric branch in apply_btc_trend_filter.
7. Smoke test: invoke `apply_btc_trend_filter` on 5 mock LTC long trades with BTC ret_42 < −4% and 5 mock LTC short trades with BTC ret_42 > +4%; verify only the 5 LTC longs are killed (long_only_mode=True semantics).

### 10.4 Engineer launch protocol — ENGINEERING REPORT BLOCKING (per Critic /020/021 Rec)

Per skill `4cb8972` split-engineer dispatch:
1. Engineer does setup (code change in 2 src/ files, smoke test, gate sanity check on 10 mock trades).
2. Orchestrator launches `uv run python run_baseline_v1.py ...` as detached bash (run_in_background=true).
3. Engineer monitors via Monitor tool until completion.
4. Engineer **writes engineering_report.md BEFORE handoff to Phase 7.4/7.5**. **CONTRACT**: no Phase 7.5 Critic dispatch without engineering_report.md present (Critic /020/021 Rec #1 BINDING).
5. Engineer reports HEAD SHA at handoff to Phase 7.4 LM Master + Phase 7.5 Critic.

**Failure mode**: if engineering_report.md is MISSING at Phase 7.5 dispatch, Critic emits BLOCK-PENDING-FIX (per /020/021 precedent — 3rd consecutive incident permits NO retrospective forgiveness; Phase 7.5 holds for the report).

### 10.5 Wall-clock kill-switch

Engineer kills the backtest if wall-clock exceeds **45 minutes** (1.7× projected 26 min). Per `feedback_v1_wall_clock_discipline_enforced.md`, 2h is the cycle-3 EXPLORATION HARD CAP; 45 min internal kill-switch is well below cap.

### 10.6 Critic Phase 7.5 Watch List (LM Master Closing ADOPTED, Section 3.4.11)

Per LM Master closing recommendations 4 priority items, Critic Phase 7.5 dispatch surface includes:

1. **F-AXIS #3 fire-rate against pre-registered band [15%, 40%] IS / [5%, 30%] OOS — LOAD-BEARING**: Critic evaluates this BEFORE F1 magnitude per LM §8 hierarchy. NEGATIVE-UNDER-FIRE classification mandatory if observed OOS fire rate < 5% (cohort-isolation has already removed BTC-bear regime trades; gate effectively off).
2. **Layer C single-cohort feature_importance defect check**: /021 pool aggregation defect (all-zeros feature_importance) was Model D pooled artifact; single-symbol Model D'-LTC-only feature_importance is well-defined by construction at /022 — but Critic verifies actual non-zero importance values across all 13 walk-forward months in `reports-v1/iteration_v1-022/in_sample/feature_importance_*.csv`. Defect recurrence would be implementation issue not basin-level.
3. **Basin relocation evidence (Optuna best_params shift) — BASIN-VECTOR not feature-importance** (LM §1 binding compliance + Section 3.4.1): /021 H2 REFUTATION binding requires Phase 7.4 verdict assignment cite Optuna best_params shifts from `optuna_studies/iter-v1-022_*.params.json` as primary basin-vector evidence channel. Feature_importance rank-shifts are INFORMATIONAL ONLY at this iter. Critic flags any verdict text that uses feature_importance as mechanism evidence (rebinding-by-slippage risk).
4. **Jaccard against baseline LTC-in-pool — empirical [0.03, 0.20] modal 0.06** (LM §6 narrowed band, Section 3.4.7): Phase 7.4 LM Master post-mortem computes trade_id Jaccard between `reports-v1/iteration_v1-baseline/in_sample/trades.csv` (LTC rows; pool roster) and `reports-v1/iteration_v1-022/in_sample/trades.csv` (gate-applied /022 roster). PROMISING-MECHANICAL classification (Jaccard ≥ 0.80) is NEAR-ZERO probability; modal 0.06 prediction.

---

## Section 11 — Alternates for /023+ (cycle-3 eighth EXPLORATION onwards)

### 11.1 Verdict-conditional /023 routing (LM Master §7 ADOPTED, Section 3.4.8)

LM Master /022 §7 staging matrix integrated. Key changes from QR initial: (a) PROMISING-MECHANICAL row moved to DOT-only (LM closure logic — PROMISING-MECHANICAL is non-compoundable, cohort coverage closure is the scientific play, NOT NEW family pivot); (b) NEGATIVE-CATASTROPHIC explicit cadence-discipline binding (DO NOT collapse cadence by jumping to /027); (c) INERT modal cell explicitly routed to DOT-only (last single-cohort untested).

| /022 verdict | LM Master Prior | /023 primary axis | /023 rationale |
|---|---|---|---|
| **PROMISING** | 8% | DOT-only + orthogonal mechanism | Cohort coverage complete (LINK/ETH/BTC/LTC → DOT next, LAST single-cohort untested); DOT IS +96.07% at /017 suggests ASYMMETRIC_ROTATION; needs orthogonal mechanism |
| **PROMISING-INERT** | 12% | DOT-only + orthogonal mechanism | LM Master §7: cohort-coverage closure has scientific value; proceed with cohort coverage |
| **PROMISING-MECHANICAL** | NEAR-ZERO (per Jaccard prior [0.03, 0.20]) | DOT-only (LM §7 ADOPTED — was: NEW family) | LM closure logic: PROMISING-MECHANICAL is non-compoundable; cohort coverage closure DOT-only is the scientific play |
| **INERT** | 40% (modal) | DOT-only (LM §7 explicit) | Last single-cohort untested; cohort-coverage closure scientific value |
| **NEGATIVE clean** | 20% | NEW-family axis (funding-rate OR per-cohort drawdown brake) | LM §7: structural axis pivot; LM Master cadence-discipline NO closeout-jump |
| **NEGATIVE-INTRINSIC** | 10% | NEW-family axis (funding-rate OR per-cohort drawdown brake) | LM §7 + QR: LTC drag NOT BTC-trend-conditional; LTC-specific alt mechanism considered but feature-family pivot dominant per LM cohort-saturation logic |
| **NEGATIVE-CATASTROPHIC** | 10% | **NEW-family axis (NOT closeout-jump-to-/027)** | LM §7 CADENCE BINDING: DO NOT collapse cadence; structural pivot to NEW family (funding-rate per Critic /020 Path Forward #2 OR per-cohort drawdown brake) |
| **NEGATIVE-OVER-KILL** | (sub-cell of NEGATIVE-clean) | LTC-only + WIDER gate threshold (5% or 6%) | Gate threshold retune; one EXPLORATION before pivoting |
| **NEGATIVE-UNDER-FIRE** | (sub-cell of NEGATIVE-clean) | LTC-only + TIGHTER gate threshold (3%) + symmetric mode | LM §4 + §8 LOAD-BEARING falsifier; gate threshold + mode retune |
| **NEGATIVE-IS-COLLAPSE** | (catastrophic sub-cell) | LTC + sample-weighting OR feature-family axis | IS basin inversion requires substrate-level intervention |

### 11.2 /024-/025 = methodology + bundle composition work (FLEXIBLE)

Possible families (cycle-3 deficit: feature-family + funding-rate + risk-primitive UNUSED in cycle-3):
- **NEW feature family — funding-rate z-score or open-interest delta** (Critic /020 Path Forward #2 + /019 Critic Rec #3 carry-forward); family: `feature-family`; NOT touched in cycle-3 to date; falsifier: importance rank ≥ 30% on ≥2 cohorts at IS using per-month FI accumulator from /021.
- **Risk-primitive — per-cohort drawdown brake** (Critic /020 Path Forward #3); family: `risk-primitive`; binary off/on at −25% per-cohort cumulative loss; pre-commit deadlock-impossibility proof per A8 catalog + iter-v3/054 lesson.
- **Bundle composition stress-test** — partial /027 multi-seed at single-seed surrogate to pre-validate cross-correlation < 0.40 between LINK and ETH+gate (and LTC+gate if /022 PROMISING).

### 11.3 /026 = pre-CONFIRMATION sanity (FINAL EXPLORATION)

Layer B determinism re-verification at /027 multi-seed config; final brief Section 11.7 routing matrix verification; engineering report contract re-confirmation.

### 11.4 /027 = first cycle-3 CONFIRMATION (Option β PRE-COMMITTED per /021 §7)

Per /021 §7 + LM Master Phase 4.5 /021 ADOPTED:

Bundle architecture: FULL POOL (5 symbols unchanged — A/C/D/E baseline) + alpha-enhancement specialists. Components:
- Pool baseline (5 symbols, A/C/D/E unchanged) — anchor
- LINK-only specialist (Model C) — /018 PROMISING-INERT-FAVORABLE
- ETH-only + BTC-trend symmetric gate (Model G) — /019 PROMISING
- BTC in pool (Model A) — /020 retrospective: BTC stays in pool, NOT excluded
- **LTC-only + BTC-trend long-suppress gate (Model D')** — **/022 candidate (THIS iter)** if PROMISING or PROMISING-INERT
- DOT specialist or DOT-in-pool — TBD /023

**/027 Target Δ at multi-seed**:
- **2-specialist bundle (LINK + ETH+gate; if /022 INERT/NEGATIVE)**: realistic +1.10 to +1.30 OOS Sharpe (per /021 §7).
- **3-specialist bundle (LINK + ETH+gate + LTC+gate; if /022 PROMISING or PROMISING-INERT) — LM Master §9 ADOPTED**: nominal +2.26 (Σ_independent: LINK +0.80 + ETH+gate +0.50 + LTC+gate +0.30); realistic with correlation drag + multi-seed variance reduction: **+1.20 to +1.50 OOS Sharpe** (LM §9 RAISES ceiling vs 2-specialist /021 §7 estimate by +0.10-0.20).

Required gates at /027: IS Sharpe > 1.0 + OOS Sharpe > 1.0 multi-seed mean + OOS/IS ≥ 0.5 + Top-symbol ≤ 30% OOS PnL + 10-seed validation (mean SR > 0, ≥7/10 profitable) + Cross-correlation < 0.40 between specialist Sharpe paths (LM §9 mandate: BOTH (LTC+gate, LINK) AND (LTC+gate, ETH+gate) at 3-specialist) + Pre-computed BTC-in-pool annualized-daily-Sharpe (NO proxy).

### 11.5 Lessons forward-binding (codified at this brief)

Per /021 closeout:
1. **/022 brief Section 0.4 — pre-classify LTC prior class** ✓ DONE (Section 0.3 ASYMMETRIC_ROTATION-INVERSE)
2. **/022 brief Section 4 — frame H2 REFUTED as substantive prior; mechanism stories at parameter-basin level** ✓ DONE (Section 1 explicitly cites basin-level framing)
3. **Per-month FI accumulation now on trunk** — methodologically superior to v3 last-month-snapshot; carries forward to /022 reports automatically
4. **Engineering report timing contract** — codified at Section 10.4

### 11.6 /022 forward-binding mandates for /023+ + /027 3-specialist bundle composition (LM Master §9 ADOPTED, Section 3.4.10)

**/027 bundle composition table — LM Master §9 3-specialist projection** (CONDITIONAL on /022 PROMISING or PROMISING-INERT):

| Component | Multi-seed Sharpe anchor | Source iter | Notes |
|---|---|---|---|
| Pool baseline (5 sym, A/C/D/E unchanged) | +0.6637 (OOS portfolio per BASELINE_V1.md) | baseline | ANCHOR |
| LINK-only specialist (Model C) | **+0.80** | /018 PROMISING-INERT-FAVORABLE | LM /019 multi-seed anchor |
| ETH-only + symmetric BTC-trend gate (Model G) | **+0.50** | /019 PROMISING | LM /019 multi-seed anchor |
| **LTC-only + asymmetric long-suppress gate (Model D') — NEW** | **+0.30** (multi-seed target) | **/022 candidate** | LM §9 target if /022 PROMISING |
| Σ_independent nominal | **+2.26** | (3-specialist) | nominal sum if specialists uncorrelated |
| **Σ_realistic with correlation drag** | **+1.20 to +1.50 OOS Sharpe** | LM §9 ADOPTED | RAISES ceiling vs 2-specialist /021 §7 estimate (+1.10-1.30) |

**LM Master cross-correlation pre-validation mandate (Section 3.4.10 ADOPTED, Phase 7.4 LM Master post-mortem at /027 CONFIRMATION)**:
- ρ(LTC+gate seed paths, LINK seed paths) < 0.40 required
- ρ(LTC+gate seed paths, ETH+gate seed paths) < 0.40 required
- If either correlation ≥ 0.40 → specialist drops or bundle re-architected

**/023+ forward-binding** (LM Master §7 staging carried forward):

If /022 PROMISING / PROMISING-INERT:
- /023 = DOT-only with orthogonal mechanism (LM §7: cohort coverage complete; pre-classify DOT prior class per /021 Rec #1)
- /027 substrate gains LTC+gate specialist (alongside LINK + ETH+gate); target +1.20-1.50 OOS Sharpe at multi-seed
- Multi-seed CONFIRMATION cross-correlation pre-validation MANDATORY (LM Master §9 ADOPTED)

If /022 INERT (LM Master 40% modal):
- /023 = DOT-only (LM §7: cohort-coverage closure scientific value)
- /027 substrate does NOT gain LTC specialist; LTC stays in pool D
- Bundle composition remains 2-specialist (LINK + ETH+gate) at /027 target +1.10-1.30 (per /021 §7)

If /022 NEGATIVE-INTRINSIC:
- /023 = NEW-family axis (funding-rate per Critic /020 Path Forward #2 OR per-cohort drawdown brake) per LM §7
- LTC drag is not BTC-trend-conditional — load-bearing finding for /023+ axis selection
- /027 substrate does NOT gain LTC specialist; LTC stays in pool D

If /022 NEGATIVE-CATASTROPHIC:
- /023 = NEW-family axis (funding-rate OR per-cohort drawdown brake) — **LM §7 CADENCE BINDING: NOT closeout-jump-to-/027**
- LTC ASYMMETRIC_ROTATION-INVERSE prior is structurally unbreakable at single-axis EXPLORATION budget; mirror /020 → /021 methodology pivot pattern
- /027 substrate does NOT gain LTC specialist
- Cadence discipline binding: 3 more EXPLORATIONs at /024-/026 before /027 CONFIRMATION

### 11.7 LTC threshold sensitivity matrix (deferred to /023 if /022 borderline)

If /022 verdict is NEGATIVE-OVER-KILL or NEGATIVE-UNDER-FIRE:

| Threshold | IS kill | OOS kill | IS Δ | OOS Δ | Notes |
|---|---|---|---|---|---|
| 3% | ~30% | ~18% | TBD | TBD | tighter — kills more longs |
| 4% (THIS iter) | 25.8% | 14.7% | +10.79% ORACLE | +12.45% ORACLE | nominal |
| 5% | ~22% | ~13% | TBD | TBD | borderline |
| 6% | 20.2% | 14.7% | −3.50% ORACLE | +12.45% ORACLE | IS regression |
| 8% (/019 literal) | 16.1% | 11.8% | −12.50% ORACLE | +7.98% ORACLE | wrong primary anchor |

---

## Section 12 — Catalog Closeout Plan (Phase 8)

Per `briefs-v1/exploration_catalog.md` row format + /016-/021 precedent:

Phase 8 diary writes:
1. Decision (MERGE / NO-MERGE) + verdict cell from Section 8
2. Headline numbers (LTC IS/OOS per-trade Sharpe + Δ vs anchor; F-AXIS-MECHANISM #1-4 PASS/FAIL; F7 sign agreement)
3. Mechanism narrative (gate efficacy + Jaccard + basin-relocation analysis)
4. Substrate-level findings (binding for /023+)
5. /027 bundle composition update
6. /023 staging (per Section 11.1 verdict-conditional routing)
7. Path Forward (from Critic — Phase 7.5 FINAL recommendations)
8. Cycle-3 cadence status (after /022)
9. Axis Rotation Status
10. Track Record Update (LM Master directional + methodology + Critic mechanism-level + verdict-class directional)
11. Files & Commits on Branch
12. Tag application (`v0.v1-022`)

Catalog entry format:

```
| iter-v1/022 | 2026-05-26 | LTC-only single-cohort EXPLORATION + stateless long-suppression BTC-trend gate at threshold -4% (cycle-3 #7/10; per-cohort-specialization-LTC NEW 14th family; LTC = ASYMMETRIC_ROTATION-INVERSE_IS-MARGINAL_OOS-CAT prior class; asymmetric one-sided variant of /019 primitive) | per-cohort-specialization-LTC | <F3 result> | <F1 result> | <verdict cell> | <next-iter routing> |
```

---

## Section 13 — Phase 5.5 self-check (QR pre-handoff)

Per `feedback_v1_phase5_self_check.md` + /021 Section 13 Addendum precedent:

### 13.1 Brief completeness (11 v1 mandatory sections)

- [x] Section 0 (Position in cycle / pivot context) — sub-sections 0.1-0.7 present
- [x] Section 0.6 (Axis Rotation Discipline + Family Declaration) — VALID rotation
- [x] Section 1 (Hypothesis) — H1 primary + H2 informational
- [x] Section 2 (IS-Only Evidence) — numerical tables from `analysis/iteration_v1-022/`
- [x] Section 2.5 (HIGH-RISK Axis Declaration) — HIGH-RISK declared
- [x] Section 3 (Implementation Spec) — code change + CLI + pinned values + LM Master placeholder
- [x] Section 3.4 (LM Master Phase 4.5 Responses) — POPULATED with 11 adopted recommendations (Section 3.4.1-3.4.12) post-Phase-4.5 amendment commit
- [x] Section 3.5 (Axis Family Declaration) — explicit
- [x] Section 3.6 (Wall-Clock Estimate) — 26 min
- [x] Section 4 (Falsifiers F1-F8 + F-AXIS-MECHANISM) — all 4 sub-checks + LOAD-BEARING markings
- [x] Section 5 (Predicted Verdict Distribution) — priors 25/45/30
- [x] Section 6 (Failure Modes) — 8 sub-modes
- [x] Section 7 (Optional / informational metrics) — DSR/PBO/Jaccard
- [x] Section 8 (Verdict Matrix) — 11-cell matrix + hierarchy + anchor frame integrity
- [x] Section 9 (Library Stack) — no changes
- [x] Section 10 (Implementation Spec critical detail) — engineering report BLOCKING + smoke test
- [x] Section 11 (Alternates for /023+) — verdict-conditional routing matrix
- [x] Section 12 (Catalog Closeout Plan) — Phase 8 diary structure
- [x] Section 13 (Phase 5.5 self-check) — this section

### 13.2 Per-cohort methodology compliance

- [x] LTC prior class pre-classified (Section 0.3) ✓ Critic /021 Rec #1 PASS
- [x] Mechanism story at parameter-basin level NOT feature level (Section 1) ✓ /021 H2 REFUTATION binding
- [x] Single-cohort + ONE specialization isolation (Section 3.5)
- [x] Direction-asymmetry attribution (Section 2.2) — load-bearing data
- [x] Anchor frame integrity — per-trade Sharpe at single-cohort (Section 8)

### 13.3 Foundation guardrails

- [x] `walk_forward.py:113` UNCHANGED (`train_end_ms = test_start_ms - embargo_ms`)
- [x] `OOS_CUTOFF_DATE = 2025-03-24` UNCHANGED
- [x] `training_months = 24` UNCHANGED
- [x] No v2/v3 symbol in LTCUSDT universe (`assert_v1_universe({"LTCUSDT"})` PASS)
- [x] No `features_v2` / `features_v3` imports added
- [x] `risk_v2.py` modification is backward-compatible (default `long_only_mode=False`)

### 13.4 Cycle-3 cadence

- [x] EXPLORATION #7 of 10 — VALID position (3 more before /027 CONFIRMATION)
- [x] EXPLORATION wall-clock estimate ≤ 2h cap — 26 min predicted
- [x] CONFIRMATION precedent count: NA for EXPLORATION

### 13.5 ORACLE EDA caveats explicit

- [x] Section 0.4 + 2.7 — ORACLE EDA limitations explicit (post-hoc on baseline roster; basin relocation can shift roster; mechanism is causal NOT roster-specific)
- [x] /020 precedent cited (Jaccard 0.084 catastrophic; mechanism story matters more than EDA numbers)

### 13.6 Engineering report contract

- [x] Section 10.4 — BLOCKING per Critic /020/021 Rec #1
- [x] Smoke test specified (Section 10.3 step 7 — 10 mock trades with long_only_mode semantics)

### 13.7 Pre-registered prediction priors (for Phase 7+8 calibration tracking)

LM Master /022 Phase 4.5 ADOPTED in full (Section 3.4):

- **Verdict priors 8/12/40/20/10/10** (PROMISING / PROMISING-INERT / INERT / NEGATIVE clean / NEGATIVE-INTRINSIC / NEGATIVE-CATASTROPHIC) — LM Master §3 (was QR initial 15/10/45/12/8/10).
- **Modal cell**: INERT 40% (was QR initial 45%).
- **Favorable tail**: 20% PROMISING + PROMISING-INERT (was QR initial 25%).
- **Negative tail**: 40% NEGATIVE + NEGATIVE-INTRINSIC + NEGATIVE-CATASTROPHIC (was QR initial 30%).
- F-AXIS #3 fire rate predictions: IS 25.8%, OOS 14.7%. NEGATIVE-UNDER-FIRE if OOS < 5% (LM §4 LOAD-BEARING falsifier).
- F-AXIS #2 OOS trade count: QR blocking band [20, 60] (preserved) + LM Master informational sub-band [18, 50] modal 28 (LM §4 ADOPTED).
- F-AXIS #2 IS trade count: QR blocking band [80, 180] (preserved) + LM Master informational sub-band [70, 160] modal 100 (LM §4 ADOPTED).
- F-AXIS-MECHANISM #4 n_eff_per_cell: point 7 (preserved) / **band [4, 10]** (LM §5 widened upper from 9 to 10; LM modal 8).
- **Jaccard band**: [0.03, 0.20] modal 0.06 (LM §6; was QR initial [0.05, 0.35]).
- **/027 3-specialist target Δ**: +1.20 to +1.50 OOS Sharpe (LM §9 ADOPTED) if LTC PROMISING; +1.10 to +1.30 (preserved /021 §7) if LTC INERT/NEGATIVE.

---

## Section 13 — Phase 7+8 Self-check Addendum (post-closeout calibration)

Added at /022 Phase 8 closeout (2026-05-26). Tracks how the pre-registered Section 13 checks held up against actual Phase 7+8 outcomes.

### Verdict-cell calibration

- **Pre-registered (Section 5)**: LM Master priors 8/12/40/20/10/10. Modal cell INERT 40%; NEG total 40% (NEG clean 20% + NEG-INTRINSIC 10% + NEG-CAT 10%); PROMISING tail 20%.
- **Observed**: **EXPLORATION-NEGATIVE-CATASTROPHIC** (Section 8 Row 6 — F1 OOS Sharpe Δ −1.17 ≤ −0.55 threshold). The 10% NEG-CAT tail materialized — modal INERT 40% REFUTED.
- **Per LM Master Phase 4.5 §8 closing point**: "F-AXIS #3 LOAD-BEARING disambiguator, not F1 magnitude — anchor at extreme negative reduces F1 diagnostic power around INERT/NEGATIVE boundary." This pre-registration was VINDICATED at /022 — ALL 4 F-AXIS-MECHANISM checks PASSED yet F1 catastrophic. **Mechanism ≠ outcome.**
- **Calibration synthesis**: LM Master priors were materially better-calibrated than QR's initial 15/10/45/12/8/10. The LM Master 10pp shift from PROMISING/INERT tails into NEGATIVE tails captured the observed tail outcome; QR's initial 30% NEG total + 8% NEG-CAT was systematically too tight.

### F-AXIS-MECHANISM 4/4 PASS calibration (Section 4)

- **Pre-registered F-AXIS #1 dispatch**: `df['symbol'].unique() == ['LTCUSDT']`. **PASS** (117 IS + 48 OOS all LTCUSDT).
- **Pre-registered F-AXIS #2 trade count**:
  - QR blocking band IS [80, 180] / OOS [20, 60]. **PASS** both (117 / 48).
  - LM Master informational sub-band IS [70, 160] modal 100 / OOS [18, 50] modal 28. **PASS** both bands (above modal but inside band).
- **Pre-registered F-AXIS #3 gate fire rate (LOAD-BEARING)**:
  - IS [15%, 40%]: **PASS** at 17.95% (21/117).
  - OOS [5%, 30%]: **PASS** at 29.17% (14/48) — near top of band.
  - Neither NEGATIVE-OVER-KILL (>30% OOS) nor NEGATIVE-UNDER-FIRE (<5% OOS) triggered. The gate operated nominally per design.
- **Pre-registered F-AXIS #4 n_eff_per_cell**: LM Master modal 8 / band [6, 10]. **PASS EXACT** (observed 8).

**Methodology calibration accurate**: 6/6 mechanism-level micro-mechanics HIT. LM Master methodology track 4/4 = 100% perfect.

### Jaccard calibration (Section 3.4.7 + 7)

- **Pre-registered (LM Master §6 ADOPTED, Section 3.4.7)**: [0.03, 0.20] modal 0.06.
- **Observed**: IS 0.1005 (22/219) / OOS 0.0933 (7/75). **PASS** both inside band, above modal.
- **Interpretation**: ~90% NEW roster on both windows confirms basin relocation per /020 BTC precedent (Jaccard 0.084 OOS). The retrained basin produced fundamentally different roster where the targeted phenomenon (89% long-direction drag) dissolved.

### Anchor-frame ambiguity discovered (Section 8 + Critic Check 8)

- **Pre-registered (Section 8 anchor frame integrity)**: F1 and F3 read `comparison.csv` "sharpe" field; brief Section 1 anchor stated as LTC-in-pool per-trade Sharpe (IS +0.0038 / OOS −0.2670).
- **Critic Check 8 finding (review.md)**: `comparison.csv` "sharpe" field is daily-annualized (per `iteration_report.py:69`), NOT per-trade. The two frames produce divergent verdicts:
  - Daily-annualized (binding): Δ = −1.17 → NEGATIVE-CATASTROPHIC.
  - Per-trade (informational): Δ ≈ +0.148 → borderline PROMISING-INERT.
- **Resolution**: Section 8 pre-registration binds to daily-annualized via comparison.csv anchor. **Verdict ROBUST under binding frame.**
- **Carry-forward action**: ELEVATED to BINDING for /023 — pre-compute per-cohort daily-annualized Sharpe directly on baseline roster; lock F1 frame to comparison.csv "sharpe" semantics. CARRY-FORWARD from /020 Rec #2 → /022 Rec #3 BINDING.

### Engineering report contract calibration (Section 10.4)

- **Pre-registered (Section 10.4)**: engineering_report.md BLOCKING per Critic /020/021 Rec #1; no Phase 7.5 Critic dispatch without engineering_report.md present.
- **Observed**: engineering_report.md MISSING at Phase 7.5 dispatch on `374bf39`. Critic emitted BLOCK-PENDING-FIX at `53dffd4`. **4th cycle-3 engineering_report contract incident — RE-VIOLATION post-/021 resolution.**
- **Resolution**: retrospective fix `d6afb68` per BLOCK-PENDING-FIX protocol (287-line engineering_report.md from existing CSVs, zero backtest re-run, 37 tests still PASS). Defect axis (report content completeness) PASS at re-evaluation.
- **Carry-forward action (NOT QR scope)**: Critic Phase 7.5 FINAL Recommendation #1 — codify NON-RETROSPECTIVE-FORGIVENESS at orchestrator dispatch level. Brief-level contracts cannot enforce; SKILL-LAYER fix required. 4 incidents across 4 iterations (/019/020/021 initial/022) confirms.

### LM Master Phase 4.5 prediction calibration

| Phase 4.5 prediction | Observed | Hit/Miss |
|---|---|---|
| Verdict-class modal INERT 40% | NEG-CAT (10% tail) | **MISS modal; HIT tail (LM Master tighter than QR)** |
| F-AXIS #2 IS [70, 160] modal 100 | 117 | **HIT inside band, above modal** |
| F-AXIS #2 OOS [18, 50] modal 28 | 48 | **HIT inside band, above modal** |
| F-AXIS #3 IS [15%, 40%] LOAD-BEARING | 17.95% | **HIT** |
| F-AXIS #3 OOS [5%, 30%] LOAD-BEARING | 29.17% | **HIT (near top)** |
| F-AXIS #4 n_eff_per_cell point 8 band [6, 10] | 8 | **HIT EXACT** |
| Jaccard [0.03, 0.20] modal 0.06 | IS 0.10 / OOS 0.093 | **HIT band both windows** |
| LM §8 closing: F-AXIS #3 LOAD-BEARING not F1 magnitude | F-AXIS #3 PASS yet F1 catastrophic | **VINDICATED (diagnostic scenario pre-registered exactly)** |

### Track record contributions

- **LM Master directional**: 1.5/6 post-/022 → 25% directional accuracy (modal misses continue at single-seed EXPLORATION on non-POSITIVE_EVERYWHERE cohorts).
- **LM Master methodology**: 4/4 post-/022 = 100% perfect (mechanism-level prediction 6/6 micro-mechanics hit; F-AXIS #3 LOAD-BEARING designation VINDICATED).
- **LM Master tail upweighting reliability at non-POSITIVE_EVERYWHERE cohorts (n=2)**: /020 LM raised NEG total + tail materialized; /022 LM raised NEG tail 30→40% + 10% NEG-CAT tail materialized. Pattern: at single-seed EXPLORATION on non-POSITIVE_EVERYWHERE cohort priors, LM Master's negative-tail upweighting is reliably directionally correct, even when modal misses.

### Cycle-3 cadence

- **Pre-registered (Section 0.5)**: cycle-3 EXPLORATION #7 of 10; CONFIRMATION earliest at /027.
- **Observed**: CONFIRMED. Cadence preserved at 7/10 (NOT accelerated /022=/027 per NEG-CAT). 3 more EXPLORATIONs (/023-/025) + sanity (/026) before /027.

### Carry-forward bindings for /023+

1. **Per-cohort isolation axis SATURATED for ASYMMETRIC_ROTATION cohorts at n=2** (NEW memory `feedback_v1_per_cohort_saturation_asymmetric_rotation.md`). Future v1 single-cohort EXPLORATIONs require POSITIVE_EVERYWHERE or counter-trend-symmetric cohort class with pre-classification.
2. **Anchor-frame ambiguity ELEVATED to BINDING for /023** — pre-compute daily-annualized Sharpe; lock to comparison.csv "sharpe" semantics.
3. **/027 bundle composition LOCKED**: 2 specialists (LINK +0.80 + ETH+gate +0.50) + FULL POOL preserved (BTC + LTC + DOT in pool).
4. **/023 routing 3-WAY CONVERGENT**: funding-rate z-score (PRIMARY) > per-cohort drawdown brake (STATEFUL deadlock proof MANDATORY) > meta-labeling (v3/017 NEG PATH C risk).
5. **DOT pre-classification MANDATORY** before any further per-cohort consideration — if DOT class = ASYMMETRIC_ROTATION, predict NEG-CAT a third time.
6. **Engineering report contract orchestrator-layer fix REQUIRED** (NOT QR scope) — NON-RETROSPECTIVE-FORGIVENESS at dispatch level.
7. **Basin-vector + feature_importance gaps DEFERRED to /023** — wire params_persist_path in /023 elif branch; refactor _post_dispatch_fi_strategies generic list.
8. **LM Master priors over QR initial pass** at single-seed EXPLORATIONs on non-POSITIVE_EVERYWHERE cohort priors — tail upweighting reliably directionally correct.

---

**END OF BRIEF.** Phase 4.5 LM Master dispatch is the next step.
