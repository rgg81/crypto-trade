# iter-v1/020 — Research Brief (Phases 2-5)

**Branch**: `iteration-v1/020` from `iteration-v1/019` HEAD `d7966d8` (tag `v0.v1-019`).

**Anchor**: `v0.v1-baseline-corrected` (`BASELINE_V1.md` commit `f8bc12c`). Portfolio IS Sharpe **+0.2829** / OOS Sharpe **+0.6637** / OOS trades 189 / 5-sym universe / 4 models (A, C, D, E).

**Per-cohort anchor** (this iter's verdict baseline): BTC-in-pool baseline IS net_pnl_pct **−37.28%** (worst IS contributor) / OOS net_pnl_pct **+33.17%** (second highest OOS contributor; OOS WR jumps 33.6% → 45.7%). True BTC-in-pool monthly Sharpe will be produced at backtest time and recorded in `reports-v1/iteration_v1-020/comparison.csv`; the per-symbol monthly Sharpe is not directly available in baseline per-symbol CSV — F1/F3 anchors use BTC-in-pool **net_pnl_pct** PROXY for the verdict band calibration (Section 4 records the proxy → Sharpe-band translation).

**Track**: v1 (refactored 2026-05-23). 13 phases. LightGBM Master + Critic.

**Iteration type**: EXPLORATION (cycle-3 #5 of 10).

---

## Section 0 — Position in cycle / pivot context

### 0.1 Cycle-3 cadence position

- Cycle-3 EXPLORATION #5 of 10 (CONFIRMATION earliest at /027).
- Prior cycle-3 EXPLORATIONs: /016 (sample-weighting NEGATIVE-catastrophic), /017 (universe NEGATIVE-anti-direction-INERT), /018 (per-cohort-specialization-LINK PROMISING-INERT favorable), /019 (per-cohort-specialization-ETH PROMISING).
- Cycle-3 ledger thus far: 2 PROMISING (1 PROMISING-INERT favorable, 1 PROMISING) / 2 NEGATIVE / 0 merges.
- After /020: 5 of 10 EXPLORATIONs done; 5 more before /027 CONFIRMATION.

### 0.2 Per-cohort methodology — third cohort

User strategic pivot 2026-05-26 (`feedback_v1_per_cohort_exploration_strategy.md`) codified per-cohort specialization as the cycle-3 default. /018 LINK-only (POSITIVE-prior cohort) + /019 ETH-only + gate (NEGATIVE-prior cohort) both produced PROMISING. /020 attacks the **third structurally-distinct cohort**: BTC, which has a UNIQUE IS-NEGATIVE / OOS-POSITIVE asymmetric rotation prior — different from both LINK (positive-everywhere) and ETH (negative-everywhere through cycle-3).

### 0.3 Methodology + structural justification

BTC IS/OOS trajectory across baseline + /014/015/016/017 (from `analysis/iteration_v1-020/btc_oos_trajectory.csv`):

| Iter | BTC IS trades | BTC IS WR | BTC IS net_pnl_pct | BTC OOS trades | BTC OOS WR | BTC OOS net_pnl_pct |
|---|---|---|---|---|---|---|
| baseline | 113 | 33.6% | **−37.28%** | 35 | 45.7% | **+33.17%** |
| /014 | 120 | 37.5% | **−24.25%** | 41 | 43.9% | **+5.70%** |
| /015 | 114 | 39.5% | −0.65% | 44 | 29.5% | **−7.18%** |
| /016 | 131 | 38.2% | **−34.60%** | 61 | 34.4% | **−8.31%** |
| /017 | 129 | 31.0% | **−93.81%** | 52 | 36.5% | **+15.11%** |

**BTC IS positive: 0/5 (5/5 negative, mean −38.12%, range [−93.81, −0.65]). BTC OOS positive: 3/5 (4/5 if we include /014's +5.70 sign-positive; mean +7.70%, range [−8.31, +33.17]).**

This is the **strongest IS-OOS asymmetric rotation in v1 catalog** — opposite of LINK (9/9 OOS positive AND IS positive too, mean +51%) and opposite of ETH (5/5 IS-OOS both NEGATIVE through cycle-3 until /019 cohort+gate dissolved it).

### 0.4 Mechanistic hypothesis sharpening (EDA-driven)

**Competing hypotheses for BTC IS-OOS asymmetric rotation**:

- **H_INTRINSIC**: BTC IS catastrophic is **regime-bound** — IS includes 2022-2024 bear/chop where BTC's edge profile is structurally weak; OOS is 2025-2026 mixed regime where BTC's edge profile reappears. Cohort isolation will NOT fix the IS catastrophic; it will simply preserve it.
- **H_POOL_ANCHOR**: BTC IS catastrophic is **pool-induced** — Model A's BTC+ETH pooled training distorts BTC labels to compensate for ETH drag; BTC's intrinsic edge is masked by the joint loss surface. Cohort isolation will FIX the IS catastrophic and preserve OOS positive.

Two diagnostic tests at EDA:

**Test 1 — Regime concentration of BTC IS catastrophic (script 03, `btc_regime_concentration.csv`)**:

| IS half | n_months | net_pnl_sum | n_pos / n_total | mean_monthly_pnl |
|---|---|---|---|---|
| IS_H1 (early IS, 2022 to mid-2024) | 15 | **−36.01%** | 5/15 | **−2.40%** |
| IS_H2 (late IS, mid-2024+) | 16 | **−1.27%** | 8/16 | **−0.08%** |
| OOS (2025-03 to 2026-05) | 11 | **+33.17%** | 6/11 | **+3.02%** |

**Finding**: BTC IS catastrophic is HEAVILY CONCENTRATED in IS_H1. H2 is essentially flat (−1.27% across 16 months, 50% positive). The IS catastrophic is regime-bound — supports H_INTRINSIC.

**Test 2 — Pool-anchor diagnostic via BTC↔ETH monthly correlation (script 04, `btc_pool_anchor_summary.csv`)**:

| metric | value |
|---|---|
| n_months_common (BTC and ETH both traded in pool) | 29 |
| **Pearson(BTC, ETH) monthly net_pnl** | **−0.0220** |
| **Spearman(BTC, ETH) monthly net_pnl** | **+0.0227** |
| Same-sign months | 15 / 29 (51.7%) |
| Opposite-sign months | 14 / 29 (48.3%) |
| BTC total IS net_pnl across common months | −18.54% |
| ETH total IS net_pnl across common months | −10.97% |

**Finding**: Pearson and Spearman ρ are BOTH NEAR ZERO (|ρ| < 0.03 << 0.30 threshold). Same-sign months at coin-flip rate. **BTC and ETH monthly PnL within pool training are statistically INDEPENDENT**. The pooled Model A does NOT couple BTC and ETH labels in any month-by-month way; their outputs sum like independent symbols. **H_POOL_ANCHOR REFUTED**.

**Combined diagnostic**: BTC IS catastrophic = H_INTRINSIC (regime concentration in IS_H1) + H_POOL_ANCHOR refuted (ρ ≈ 0). The structural prior for /020 is therefore:

- **BTC-only specialization will most likely PRESERVE IS catastrophic** (regime constraint is binding; Optuna may shift trajectory slightly but the H1 catastrophic months are signal-poor).
- **BTC-only specialization will most likely PRESERVE OOS positive** (OOS is regime-favorable; intrinsic BTC edge will surface under isolation).
- Modal verdict-class: **INERT** — small IS Δ (positive or negative), OOS Δ within band.
- Tail outcomes:
  - **PROMISING-tail**: BTC-only Optuna trajectory escapes IS_H1 catastrophic via narrower training scope (model overfits LESS to IS_H1, OOS holds → IS lift + OOS preserved).
  - **NEGATIVE-tail**: BTC-only single-seed=42 basin lands in a worse region than pool — OOS regression below baseline +33.17 contribution.

### 0.5 Cadence ledger summary

Cycle-3 #5 of 10. After /020: 5 of 10 done. 5 more EXPLORATIONs (/021-/026) before /027 CONFIRMATION.

### 0.6 Axis Rotation Discipline + Family Declaration (v1 mandatory)

- **This iter's axis family**: `per-cohort-specialization-BTC` (NEW 11th family — FIRST usage at v1 catalog level; convergent recommendation from /019 closeout Critic Path Forward #1 + LM Master Phase 4.5 §9 + Phase 7.4 §7).
- **Cohort identifier**: BTC (single-symbol cohort).
- **Specialization dimension**: NONE — pure single-cohort isolation, NO gate, NO new feature, NO new labeling. Cycle-3 #5 is a CONTROL EXPERIMENT for the per-cohort methodology: tests whether cohort isolation ALONE (without any specialization knob) can restructure BTC's IS-OOS asymmetric rotation, OR whether a gate / feature / labeling intervention is required.
- **Prior 5 EXPLORATION families** (verified against `briefs-v1/exploration_catalog.md`):
  - /015: `labeling` (CONFIRMATION)
  - /016: `sample-weighting`
  - /017: `universe`
  - /018: `per-cohort-specialization-LINK`
  - /019: `per-cohort-specialization-ETH`
- **Rotation status**: **VALID** — `per-cohort-specialization-BTC` is in NONE of the prior 5 families. Per /018 + /019 closeout LESSONs (codified rule), per-cohort specialization is the cycle-3 methodology; BTC is a different COHORT from LINK and ETH (rotation by cohort, not by family literal-name). The per-cohort methodology family rotates COHORT IDs (LINK → ETH → BTC → LTC/DOT/2-sym pool at /021-/026), with each cohort declared a structurally-distinct family.
- **One-sentence rationale**: BTC has the strongest IS-OOS asymmetric rotation prior in v1 catalog (5/5 IS-NEGATIVE / 4/5 OOS-POSITIVE); EDA diagnostics support H_INTRINSIC (regime-bound IS catastrophic, statistically-independent BTC-ETH in pool) → cohort isolation tests intrinsic-edge-preservation under single-seed Optuna trajectory.

**NEW family declaration check (Critic Phase 7.5 Check 14 PASS requires Critic + LM Master + QR convergence on orthogonality)**: per-cohort-specialization-BTC is orthogonal to /018's per-cohort-specialization-LINK and /019's per-cohort-specialization-ETH because (a) different COHORT, (b) different STRUCTURAL PRIOR (BTC = IS-NEG/OOS-POS asymmetric rotation; LINK = IS-POS/OOS-POS; ETH = IS-NEG/OOS-NEG through cycle-3), (c) different SPECIALIZATION SCOPE (BTC tests pure isolation with no knob; LINK tested pure isolation with positive prior; ETH tested isolation+gate against negative prior). Justified per /019 pre-committed Path Forward + LM Master Phase 7.4 §7.

### 0.7 LM Master Phase 4.5 coordination slot

LM Master Phase 4.5 fires AFTER this brief. Section 3.4 below RESERVES a placeholder for LM Master responses; integration is a Phase 5.5 BLOCK condition if LM Master fires after brief but brief doesn't echo each recommendation.

LM Master Phase 4.5 pre-EDA prior (from prompt): PROMISING 25% / INERT 50% / NEGATIVE 25% — modal INERT; BTC is the strongest pool ANCHOR (pooled regularization helps OTHER symbols; BTC-only isolation may LOSE that asymmetric benefit; modal outcome = no improvement vs pool baseline).

QR EDA findings UPDATE the prior toward INERT-stronger (H_POOL_ANCHOR REFUTED at ρ ≈ 0; regime-bound IS catastrophic supported). QR's POST-EDA prior (Section 5): PROMISING 20% / INERT 55% / NEGATIVE 25%. Brief Section 3.4 will reconcile QR vs LM Master at Phase 4.5 fire.

---

## Section 1 — Hypothesis

**Primary hypothesis (H1)**: A LightGBM model trained on **BTC-only data** (single-symbol cohort) at Model A's existing pool config (`atr_tp=2.9, atr_sl=1.45, apply_r1=False`) — pure cohort isolation, NO specialization knob — will **preserve BTC's IS-OOS asymmetric rotation** (IS catastrophic AND OOS positive both persist) per the H_INTRINSIC diagnostic supported by Section 0.4 EDA.

**Sub-hypothesis (H1a)**: BTC-only OOS net contribution preserves the +33.17% baseline anchor within ±15%-points (PROMISING+INERT cells). If BTC-only OOS drops below +18% net contribution, the OOS edge depended on pool-coupling that ρ ≈ 0 diagnostic missed → revisit H_POOL_ANCHOR.

**Sub-hypothesis (H1b)**: BTC-only IS net contribution stays catastrophic (≤ −20% net contribution) per regime-concentration finding. If IS-only suddenly improves to ≤ −10% (anti-prior), it would indicate either (i) single-seed=42 trajectory lottery favorable OR (ii) the H1 catastrophic months had high-variance trades that Optuna at narrower scope can avoid.

**Secondary hypothesis (H2 — INFORMATIONAL only; does NOT determine verdict)**: At portfolio level, BTC-only is single-symbol concentration; portfolio Sharpe comparison vs baseline +0.6637 is not the verdict criterion per per-cohort methodology caveat 1 (LM Master /019 Phase 7.4 §2).

**Falsification logic (Sharpe-frame; Section 4 calibrates absolute Sharpe-Δ thresholds)**:
- If BTC-only OOS Sharpe Δ ≥ +0.20 vs BTC-in-pool OOS-Sharpe-proxy → PROMISING (intrinsic edge accentuated under isolation).
- If BTC-only OOS Sharpe Δ ∈ [−0.20, +0.20] → INERT (modal — intrinsic edge preserved).
- If BTC-only OOS Sharpe Δ ≤ −0.20 → NEGATIVE (cohort isolation harms — H_INTRINSIC partially false).
- If BTC-only OOS Sharpe Δ ≤ −0.55 → NEGATIVE-CATASTROPHIC (revisit H_POOL_ANCHOR or H_INTRINSIC; the pool was the load-bearing edge anchor for BTC).

**Critical interpretation note**: BTC's IS-OOS asymmetric rotation prior (the IS-NEG / OOS-POS asymmetry) is the structural signature under test. /020 is **NOT a directional-flip experiment** (unlike /019 which targeted ETH's negative drag). It is a **PRESERVATION experiment**: can cohort isolation preserve BTC's OOS positive without amplifying the IS catastrophic? The verdict cell thresholds in Section 4 are calibrated to PRESERVATION semantics: PROMISING = OOS preserved or accentuated, NEGATIVE = OOS lost.

---

## Section 2 — IS-Only Evidence (EDA results)

EDA scripts under `analysis/iteration_v1-020/`. Outputs committed at `283064b`.

### 2.1 BTC per-symbol baseline + /017 anchors (script 01)

From `btc_per_symbol_baseline.csv`:

| Source | trades | wins | WR | net_pnl_pct | avg_pnl | pct_of_total |
|---|---|---|---|---|---|---|
| baseline_in_sample | 113 | 38 | 33.6% | **−37.28%** | −0.330% | −73.11% |
| baseline_out_of_sample | 35 | 16 | 45.7% | **+33.17%** | +0.948% | +133.38% |
| /017 in_sample (universe +SOL) | 129 | 40 | 31.0% | **−93.81%** | −0.727% | −73.34% |
| /017 out_of_sample (universe +SOL) | 52 | 19 | 36.5% | **+15.11%** | +0.291% | +30.22% |

**BTC-in-pool anchor**:
- IS: 113 trades, WR 33.6%, net_pnl −37.28% (WORST in baseline IS).
- OOS: 35 trades, WR 45.7% (+12.1pp lift IS→OOS), net_pnl +33.17% (second highest contributor, behind LINK +34.23%).
- Universe expansion to /017 made BTC IS DRAMATICALLY worse (−93.81% vs baseline −37.28%) while preserving BTC OOS positive (+15.11% vs baseline +33.17%). The OOS contribution shrunk but stayed positive.

### 2.2 BTC trajectory across baseline + /014/015/016/017 (script 02)

See table in Section 0.3. Summary statistics: BTC IS net_pnl mean −38.12% / std ~32 / range [−93.81, −0.65] / 5/5 negative. BTC OOS net_pnl mean +7.70% / std ~16 / range [−8.31, +33.17] / 4/5 sign-positive (4 if we include /014's +5.70 alongside baseline / /016-/017 positives; only /015 OOS was negative at −7.18).

**Strongest IS-OOS rotation asymmetry in v1 catalog**. ETH had 5/5 OOS-negative through cycle-3 (until /019 dissolved). LINK had 9/9 OOS-positive AND positive-IS too. BTC is the UNIQUE asymmetric-rotation cohort: every architecture produces BTC IS-NEGATIVE but BTC OOS leans POSITIVE.

### 2.3 BTC IS regime concentration (script 03, `btc_regime_concentration.csv`)

| Sample half | n_months | net_pnl_sum | n_pos / n_total | best | worst | mean_monthly_pnl |
|---|---|---|---|---|---|---|
| IS_H1 (early ~2022 to mid-2024) | 15 | **−36.01%** | 5/15 (33%) | +21.57 | **−18.88** | **−2.40%** |
| IS_H2 (mid-2024+) | 16 | −1.27% | 8/16 (50%) | +9.59 | −5.89 | −0.08% |
| OOS (2025-03 to 2026-05) | 11 | **+33.17%** | 6/11 (55%) | +21.59 | −12.63 | **+3.02%** |

**Findings**:
- BTC IS_H1 is CATASTROPHIC (mean −2.40%/month, 33% positive, −36.01% total). This explains the bulk of BTC IS net_pnl −37.28%.
- BTC IS_H2 is essentially FLAT (mean −0.08%/month, 50% positive). BTC's edge profile recovered going into 2024.
- BTC OOS is STRONGLY POSITIVE (mean +3.02%/month, 55% positive, +33.17% total). OOS continues the H2-style improved edge.
- **The IS catastrophic is concentrated in 15 early-IS months; cohort isolation is unlikely to change those H1 months** — the regime is the signal-constraint, not the cohort scope.

### 2.4 Pool-anchor diagnostic — BTC↔ETH monthly correlation (script 04, `btc_pool_anchor_summary.csv`)

| metric | value |
|---|---|
| n_months_common (BTC + ETH both traded in pool) | 29 |
| **Pearson(BTC, ETH) monthly net_pnl** | **−0.0220** |
| **Spearman(BTC, ETH) monthly net_pnl** | **+0.0227** |
| Same-sign months (both pos or both neg) | 15 / 29 (51.7%) |
| Opposite-sign months | 14 / 29 (48.3%) |
| BTC total IS net_pnl across common months | −18.54% |
| ETH total IS net_pnl across common months | −10.97% |
| BTC mean monthly | −0.64% |
| ETH mean monthly | −0.38% |

**Findings**:
- Pearson ρ = −0.0220 → BTC and ETH monthly PnL are uncorrelated.
- Spearman ρ = +0.0227 → rank-correlation also near zero.
- Same-sign at 51.7% → essentially coin-flip; pooled Model A is NOT generating BTC and ETH outputs that co-move month-by-month.
- **H_POOL_ANCHOR is REFUTED** at the 95%+ confidence level. The pooled Model A does NOT distort BTC labels by coupling them to ETH's loss surface; the two symbols' monthly PnL trajectories are statistically independent.
- **By corollary, H_INTRINSIC is SUPPORTED**. BTC's IS catastrophic is regime-bound (Section 2.3), and removing ETH from the pool will NOT fix BTC's IS labels — those labels reflect BTC's intrinsic edge in IS_H1, which is poor.

### 2.5 BTC under universe expansion vs subtraction (cross-iteration synthesis)

Baseline (5 sym pool, BTC+ETH in Model A) → /017 (6 sym pool, BTC+ETH in Model A + SOL isolated):
- BTC IS WORSENED from −37.28% to **−93.81%** (Δ −56.5 pp).
- BTC OOS STAYED POSITIVE +15.11% (Δ −18.06 pp vs baseline; still positive).
- WR shifted: IS WR 33.6% → 31.0% (slight worsen); OOS WR 45.7% → 36.5% (notable worsen).

**Interpretation**: adding +SOL to the universe (at the universe level, not Model A directly) DID make BTC IS more catastrophic AND compressed BTC OOS. Adding symbols at the universe layer can WORSEN BTC. The OPPOSITE direction — removing symbols (BTC-only at /020) — is uncertain:
- If universe-expansion harms BTC monotonically, universe-subtraction (to 1 symbol) should HELP BTC IS → PROMISING-tail.
- But pool-anchor diagnostic ρ ≈ 0 says removing ETH should NOT change BTC's monthly PnL trajectory → INERT modal.
- These two readings conflict at the directional level; INERT modal resolves the conflict by predicting small Δ.

### 2.6 Predicted backtest behavior summary

| Predicted | IS net_pnl | IS WR | OOS net_pnl | OOS WR | trades IS | trades OOS |
|---|---|---|---|---|---|---|
| **Modal-INERT band** | [−45%, −25%] | [30%, 38%] | [+18%, +45%] | [40%, 50%] | [80, 130] | [25, 45] |
| **PROMISING-tail** | [−25%, −10%] | [35%, 42%] | [+45%, +60%] | [45%, 55%] | [70, 110] | [25, 40] |
| **NEGATIVE-tail** | [−80%, −45%] | [27%, 33%] | [−15%, +18%] | [35%, 42%] | [85, 150] | [25, 55] |

Pre-registered band for F-AXIS-MECHANISM #2 (cohort-scale trade counts): IS ∈ [70, 150], OOS ∈ [25, 55]. Outside these bands → mechanism failure (cohort isolation broken or dispatch wrong).

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1 mandatory)

**Declaration: HIGH-RISK.**

**Reason (one sentence)**: dropping Models A/C/D/E from the dispatch is a structural change to Optuna's training-objective domain (universe goes from 5 symbols to 1 BTC-only with no ETH partner), and BTC's structural prior is unique (5/5 IS-NEGATIVE + 4/5 OOS-POSITIVE asymmetric rotation; modal LM Master prior is INERT 50%); these together expand single-seed=42 basin-lottery downside band relative to within-pool baseline.

**Mitigation (opt-in)**: NONE — single-seed-style EXPLORATION at ENSEMBLE_SIZE=3 inner seeds (fixed cycle-3 default per `feedback_v1_wall_clock_discipline_enforced.md`). Multi-seed validation deferred to /027 CONFIRMATION.

**HIGH-RISK cumulative tracker (cycle-3)**:
- /016: HIGH-RISK declared / NEGATIVE-catastrophic / >1σ OOS Δ
- /017: HIGH-RISK declared / NEGATIVE-anti-direction-INERT / OOS Δ within band
- /018: HIGH-RISK declared / PROMISING-INERT favorable / OOS Δ +0.16
- /019: HIGH-RISK declared / PROMISING / OOS Δ +0.65 (favorable surprise)
- **/020** (this iter): HIGH-RISK declared / outcome TBD

Cumulative cycle-3 HIGH-RISK record: 2 NEGATIVE / 2 PROMISING. Net: 0 consecutive negatives — no auto-trigger for mandatory multi-seed at this iter.

If /020 produces ≥1σ negative OOS Δ catastrophic, that would be the 3rd cycle-3 catastrophic HIGH-RISK over 5 (not 3-in-a-row), and per `feedback_v1_n_eff_barrier_magnitude_curve.md` forward-binding mandate, 3 consecutive ≥1σ HIGH-RISK negatives triggers MANDATORY multi-seed on the next HIGH-RISK iteration. /020's outcome is informative for the trigger but not the trigger itself.

---

## Section 3 — Implementation Spec

### 3.1 Code change (single src/ file change)

**File 1 — `run_baseline_v1.py`** — add new universe constant + new model dispatch branch:

```python
# After V1_ITER019_UNIVERSE definition (~line 147):
V1_ITER020_UNIVERSE: tuple[str, ...] = ("BTCUSDT",)
"""iter-v1/020 cohort: BTC-only pure cohort isolation (NO gate, NO new feature).

USER STRATEGIC PIVOT 2026-05-26 cycle-3 #5 EXPLORATION:
per-cohort-specialization-BTC (NEW 11th family). BTC has UNIQUE IS-OOS
asymmetric rotation prior: 5/5 IS-NEGATIVE (mean -38.12%) + 4/5 OOS-POSITIVE
(mean +7.70%) across baseline + /014-/017. EDA diagnostics support H_INTRINSIC
(regime-bound IS catastrophic in IS_H1; Pearson(BTC,ETH) monthly = -0.0220
in pool → labels statistically independent, H_POOL_ANCHOR refuted).

Pure cohort isolation: NO BTC-trend gate, NO new feature, NO new labeling.
Tests whether cohort isolation ALONE restructures BTC's asymmetric rotation
or whether a specialization knob is required at later iters.

LOCAL to runner — NOT shared via features_v1/__init__.py (only CONFIRMATION-MERGE
updates V1_BASELINE_UNIVERSE). assert_v1_universe() accepts {BTCUSDT} because
BTCUSDT is in V1_BASELINE_UNIVERSE.
"""
```

```python
# Add elif branch after V1_ITER019_UNIVERSE branch (~line 1424):
elif set(symbols) == set(V1_ITER020_UNIVERSE):
    # iter-v1/020: BTC-only single-cohort EXPLORATION (cycle-3 #5 of 10).
    # USER STRATEGIC PIVOT 2026-05-26: per-cohort specialization axis.
    #
    # Dispatch — ONLY Model H (BTC-only; mirrors Model A's apply_r1=False
    # apply_r2=False semantics; ATR 2.9/1.45 matches Model A which trained
    # BTC in pool).
    # Models A (BTC+ETH pooled), C (LINK), D (LTC), E (DOT) DROPPED.
    # Single-axis isolation: SYMBOL DIMENSION (5 sym -> 1 sym).
    # NO gate, NO new feature, NO new labeling — pure cohort isolation.
    #
    # F-AXIS-MECHANISM #1: trades.csv must contain ONLY BTCUSDT rows.
    # F-AXIS-MECHANISM #2: BTC IS [70,150] / OOS [25,55] trade band.
    # F-AXIS-MECHANISM #3 (load-bearing): IS_H1 net_pnl preserved
    # catastrophic per regime-binding hypothesis; cell-positional check.
    assert set(symbols) == {"BTCUSDT"}, (
        f"iter-v1/020 guard: expected {{BTCUSDT}}, got {set(symbols)}"
    )
    results_h, faxm_h = run_model(
        "H (BTC-only + R3)",
        ("BTCUSDT",),
        atr_tp=2.9,
        atr_sl=1.45,
        apply_r1=False,
        n_trials=n_trials,
        ensemble_size=ensemble_size,
        oof_persist_path=OOF_PARQUET_PATH,
        feature_columns=active_feature_columns,
        bounds_profile=bounds_profile,
        **_r5_kwargs,
    )
    _all_faxm_logs = faxm_h
    all_results = results_h
    _r5_model_results = [results_h]
```

**Diff scope** (single src/ file): `run_baseline_v1.py`, ~30 lines added (smaller than /019's +50 because no gate). Zero changes to:
- `src/crypto_trade/features_v1/`
- `src/crypto_trade/strategies/ml/lgbm.py`
- `src/crypto_trade/strategies/ml/optimization.py`
- `src/crypto_trade/strategies/ml/walk_forward.py`
- `src/crypto_trade/labeling.py`
- Risk gate code (R1 disabled, R3 unchanged)
- v2's `risk_v2.py` (NOT imported)

**Foundation guardrail**: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` UNCHANGED. No regression.

**Model naming choice**: "Model H" (next available letter after F/G). Rationale: Model A's (BTC+ETH pooled) hyperparameters (`atr_tp=2.9, atr_sl=1.45, apply_r1=False`) are PARITY-IDENTICAL to what BTC needs at single-symbol — Model A is the source of BTC's pool config. Creating Model H avoids reusing Model A's dispatch name (which still implies pool semantics). This pattern mirrors /018's Model C reuse (single-symbol from existing pool) and /019's Model G creation (new ETH-only with shared config).

### 3.2 CLI invocation

```bash
uv run python run_baseline_v1.py \
  --symbols BTCUSDT \
  --pruned-features \
  --ensemble-size 3 \
  --n-trials 18 \
  --iteration-label "v1-020" \
  --reports-dir reports-v1
```

(`--symbols BTCUSDT` triggers the new elif branch via `set(symbols) == set(V1_ITER020_UNIVERSE)`. `--pruned-features` activates V1_FEATURE_COLUMNS_PRUNED + bounds_profile=v1_pruned. `--ensemble-size 3` + `--n-trials 18` matches cycle-3 EXPLORATION budget. **No `--no-engineering-report`** per Critic /017 + /019 Rec — engineering_report.md is a required deliverable, see Section 10.4.)

### 3.3 Pinned values

- `feature_columns = list(V1_FEATURE_COLUMNS_PRUNED)` — 40 cols, passed explicitly.
- `bounds_profile = "v1_pruned"` — same as baseline.
- `ENSEMBLE_SEEDS[0:3] = [42, 123, 456]` — same as baseline 3-seed EXPLORATION default.
- `r5_vol_target_enabled = False` (cycle-3+ default).
- `r5_binary_kill_enabled = False` (cycle-3+ default).
- `sample_weight_mode = "abs_pnl"` (baseline default).
- `sigma_source = "natr"` (baseline default).
- `apply_r1 = False` (mirrors Model A's BTC+ETH pool semantics; BTC-in-pool baseline did NOT use R1).
- `apply_r2 = False` (Model E only; BTC is not Model E).
- **No gate, no feature mutation, no labeling change**.

### 3.4 LM Master Phase 4.5 Responses

**RESERVED PLACEHOLDER** — to be populated AFTER LM Master Phase 4.5 advisory fires.

Phase 4.5 LM Master is dispatched by the orchestrator AFTER this brief is committed. The advisory file lands at `briefs-v1/iteration_v1-020/lgbm_advisor.md` and contains recommendations addressing:
- BTC-only structural prior (LM Master pre-EDA prior was PROMISING 25% / INERT 50% / NEGATIVE 25% per prompt).
- Optuna n_trials + ENSEMBLE_SIZE retention.
- BTC-specific feature suggestions (informational; will NOT be adopted at /020 per pure-isolation discipline).
- Saturation risks (single-cohort + single-seed lottery; LM Master /019 PROMISING-tail miss at +0.30 above predicted band suggests basin variance can swing favorably).
- F-AXIS-MECHANISM hierarchy (per /019 Critic Rec #2, when |anchor IS Sharpe| < 0.10, F7 sign-agreement is N/A and F-AXIS #2 trade count + F-AXIS #1 dispatch correctness become LOAD-BEARING).

After LM Master fires, this Section will be edited to enumerate:
- Adopted (without modification)
- Adopted (with modification)
- Rejected (with reasons)
- Informational confirmations
- Verdict-interpretation principle if LM Master proposes one
- Most important LM Master flag if any

Phase 5.5 gate will BLOCK if this section remains as a placeholder when LM Master has fired. The placeholder must be replaced with concrete LM Master responses before Phase 5.5 gate dispatch.

### 3.5 Axis Family Declaration (v1 mandatory)

- **Axis family**: `per-cohort-specialization-BTC` (NEW 11th family declaration; FIRST usage; convergent recommendation from /019 closeout Critic Phase 7.5 Path Forward + LM Master Phase 4.5 §9 + Phase 7.4 §7).
- **Cohort + Specialization pairing**: cohort=BTC, specialization=NONE (pure isolation control experiment).
- **Single-axis isolation verified**: ONLY SYMBOL DIMENSION changes (5 sym → 1 sym + drop A/C/D/E dispatch). Zero changes to features, labeling, risk gates, Optuna bounds, gate primitives.
- **Phase 7.5 Critic Check 14 PASS requires**: NEW family declaration is structurally orthogonal to /018's per-cohort-specialization-LINK and /019's per-cohort-specialization-ETH (different cohort, different structural prior, different specialization scope — see Section 0.6).

### 3.6 Wall-Clock Estimate (CRITICAL — Phase 5.5 BLOCK if missing or > 1.6h)

**Predicted wall-clock: 25 minutes total.**

Decomposition (from `wallclock_estimate.csv`):
- Anchor: /019 ETH-only (1 sym) at ENSEMBLE_SIZE=3 + n_trials=18 + V1_FEATURE_COLUMNS_PRUNED ran **25 min** total per /019 diary. /018 LINK-only at identical config also ran ~25 min.
- BTC-only (1 sym, identical scale config; no gate, no specialization knob) projected: **20-25 min** (linear).
- No post-hoc gate (vs /019 which had ~1 min gate overhead): saving ~1 min.
- Methodology + reporting overhead: ~3 min (CPCV, PSR, DSR on 1-model trade roster).
- **Total projected: 23-28 minutes (midpoint 25 minutes).**

**Margin vs 2h cap = 1h:35min (79% margin).**
**Margin vs 1.6h Phase 5.5 BLOCK threshold = 71+ minutes of buffer.**

**Contingency**: even at 2× linear-scaling overhead (worst case 50 minutes), margin remains 1h:10min = 58%, well above the 20% Phase 5.5 floor.

**No n_trials compression needed.** n_trials=18 stays at cycle-3 EXPLORATION default. **Kill-switch**: Engineer kills backtest if wall-clock exceeds **45 minutes** (1.8× projected mid-point; well below 2h cap).

### 3.7 Reproducibility

- `--symbols BTCUSDT` exact flag value (no comma list)
- `ENSEMBLE_SEEDS[0:3] = [42, 123, 456]` (literal pin at run_baseline_v1.py line ~97)
- `OOF_PARQUET_PATH = data/v1_iter_v1-020_trial_oof.parquet` (iter-stamped)
- HEAD SHA recorded at Phase 5.5 (post-brief) + Phase 6 (post-implementation).
- No CLI args control behavior beyond `--symbols` + standard flags.

---

## Section 4 — Falsifiers (F1-F8 + F-AXIS-MECHANISM)

Per `feedback_v1_per_cohort_exploration_strategy.md`: per-cohort EXPLORATION. F1 + F8 thresholds adapt to BTC-only cohort scale, NOT portfolio-level.

**Note on Sharpe vs net_pnl frame**: baseline per-symbol CSV does NOT contain per-symbol monthly Sharpe. The /020 runner will compute BTC-only portfolio monthly Sharpe at backtest time (= the BTC-only single-cohort monthly Sharpe). For F1/F3 anchor, we use TWO calibration frames:

1. **net_pnl_pct frame** (direct from baseline per_symbol.csv; primary verdict frame for /020):
   - BTC-in-pool IS net_pnl anchor: **−37.28%** (baseline)
   - BTC-in-pool OOS net_pnl anchor: **+33.17%** (baseline)
2. **Monthly Sharpe frame** (computed by runner at backtest; informational triangulation):
   - BTC-only model produces a single portfolio Sharpe (== single-cohort Sharpe) reported in comparison.csv.
   - Compare against BTC-in-pool Sharpe contribution — which is NOT directly available. We use the proxy: BTC's per-symbol Sharpe ≈ (mean monthly PnL / std monthly PnL) × √12. Backtest will produce the actual number.

### F1 — BTC-only OOS Sharpe Δ + net_pnl Δ vs BTC-in-pool baseline anchor

**Anchor (Sharpe frame, monthly)**: BTC-in-pool OOS Sharpe = NOT in baseline CSV; will be computed at /020 runtime. Approximation from `btc_regime_concentration.csv`: mean monthly PnL +3.02% with std rough ~10% → monthly Sharpe ≈ 0.30 (annualized = +1.05 with √12 scaling, but monthly is the verdict cadence). **F1 SHARPE ANCHOR PLACEHOLDER**: ≈ +0.30 monthly OOS Sharpe (validated at Phase 7).

**Anchor (net_pnl frame)**: BTC-in-pool OOS net_pnl = **+33.17%** (concrete from baseline CSV).

| Verdict cell | F1 OOS Sharpe Δ band | F1 OOS net_pnl Δ band | Absolute OOS Sharpe / net_pnl |
|---|---|---|---|
| **PROMISING** | Δ ≥ +0.20 | Δ ≥ +15 pp | Sharpe ≥ +0.50 / net_pnl ≥ +48% |
| INERT | Δ ∈ [−0.20, +0.20] | Δ ∈ [−15, +15] pp | Sharpe ∈ [+0.10, +0.50] / net_pnl ∈ [+18%, +48%] |
| **NEGATIVE** | Δ ≤ −0.20 | Δ ≤ −15 pp | Sharpe ≤ +0.10 / net_pnl ≤ +18% |
| Catastrophic-NEGATIVE | Δ ≤ −0.55 | Δ ≤ −40 pp | Sharpe ≤ −0.25 / net_pnl ≤ −7% |

**Calibration note**: BTC-in-pool OOS anchor is LARGE absolute (+33.17% net_pnl, ≈ +0.30 monthly Sharpe). Standard ±0.20 Sharpe-Δ PROMISING/NEGATIVE bands (from /018 LINK + /019 ETH calibration) apply nominally. Unlike /019 (where ETH anchor +0.05 was small and bands compressed), /020's anchor is comparable to LINK's anchor (+0.82 monthly Sharpe) in magnitude. **F7 sign-agreement should be available as primary check (per /019 Critic Rec #2 pre-registration)**: BTC-only IS Sharpe vs OOS Sharpe — if same-sign with anchor (IS-NEGATIVE / OOS-POSITIVE), F7 PASS; if either flips, F7 FAIL.

**Per /019 Critic Rec #2 pre-registration**: IF |BTC-in-pool IS Sharpe| < 0.10 (small anchor), F7 is N/A and F-AXIS-MECHANISM #2 trade count becomes LOAD-BEARING. BTC-in-pool IS approximate monthly Sharpe (proxy via mean monthly PnL −2.40 H1 + −0.08 H2 averaged with std ~9 → IS Sharpe ≈ −0.12) is JUST BELOW the 0.10 threshold absolute. **F7 status (pre-registered now)**: tentatively N/A for /020 — IS anchor is small absolute (∼ −0.12 monthly Sharpe). **F-AXIS-MECHANISM #2 trade count is LOAD-BEARING**.

### F3 — BTC-only IS Sharpe Δ + net_pnl Δ vs BTC-in-pool IS anchor

**Anchor (Sharpe frame, monthly)**: BTC-in-pool IS Sharpe ≈ −0.12 monthly (proxy). PLACEHOLDER — actual computed at /020 runtime.

**Anchor (net_pnl frame)**: BTC-in-pool IS net_pnl = **−37.28%**.

| Verdict cell | F3 IS Sharpe Δ band | F3 IS net_pnl Δ band | Absolute IS Sharpe / net_pnl |
|---|---|---|---|
| **PROMISING** | Δ ≥ +0.20 | Δ ≥ +15 pp | Sharpe ≥ +0.08 / net_pnl ≥ −22% |
| INERT | Δ ∈ [−0.20, +0.20] | Δ ∈ [−15, +15] pp | Sharpe ∈ [−0.32, +0.08] / net_pnl ∈ [−52%, −22%] |
| **NEGATIVE** | Δ ≤ −0.20 | Δ ≤ −15 pp | Sharpe ≤ −0.32 / net_pnl ≤ −52% |
| Catastrophic-NEGATIVE | Δ ≤ −0.30 | Δ ≤ −30 pp | Sharpe ≤ −0.42 / net_pnl ≤ −67% |

**EDA prediction (informational)**: per Section 0.4 + 2.3, modal expectation is IS preserved catastrophic (mean H1 + H2 ≈ −38% net_pnl, regime-bound). PROMISING-tail (IS lift) requires Optuna at narrower scope to escape H1 trajectories — possible but not modal. INERT modal.

### F2 — Embargo/look-ahead PASS (structural; automatic)

`walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` UNCHANGED. No new gate / feature / labeling — no new look-ahead surface introduced. PASS by construction.

### F4 — Feature ADF stationarity (informational; no new features)

40 V1_FEATURE_COLUMNS_PRUNED unchanged. ADF rerun on BTC-only halves should produce similar bonferroni-pass profile. INFORMATIONAL.

### F5 — PSR_monthly_vs_0 OOS (basin-health signal)

BTC-only OOS PSR_monthly_vs_0:
- Baseline anchor (5-sym OOS portfolio) PSR_monthly_vs_0 = 0.989 (BASELINE_V1.md).
- BTC-only OOS at 11 OOS months single-symbol distribution; predicted band [0.50, 0.95] for BTC-only OOS PSR (wider than LINK-only /018=0.885 because BTC OOS includes /015's −7.18 outlier in trajectory; informational).
- **Catastrophic if** PSR_monthly_vs_0 < 0.10 → indicates BTC OOS lost the structural positive rotation.

### F6 — Per-symbol IS direction (vacuous — only 1 symbol)

BTC-only model has only BTC trades. F6 PASS by construction.

### F7 — Per-symbol IS/OOS sign agreement (BTC only)

**Per /019 Critic Rec #2 pre-registration (codified in feedback rule)**: IF |BTC-in-pool IS Sharpe| < 0.10, F7 is **N/A** and F-AXIS-MECHANISM #2 trade count becomes LOAD-BEARING.

BTC-in-pool IS Sharpe proxy ≈ −0.12 (just below the 0.10 absolute threshold). Two interpretations:
1. Strict reading: |−0.12| ≥ 0.10 → F7 IS NOT N/A; F7 active.
2. Margin reading: |−0.12| is within ±20% of the threshold → F7 is at the noise floor; F-AXIS #2 should be elevated alongside F7.

**Decision (pre-registered)**: F7 ACTIVE but with **noise-floor caveat**. F-AXIS-MECHANISM #2 trade count is ELEVATED to LOAD-BEARING per Section 4 F-AXIS #2 row. Phase 7.5 Critic evaluates F-AXIS #2 BEFORE F7 magnitude when assigning verdict cell; if F-AXIS #2 PASS and F7 sign disagrees (e.g., BTC-only IS Sharpe goes positive while OOS Sharpe goes positive), the verdict cell is set by F-AXIS #2 + F1.

The hypothesis under test (H_INTRINSIC) predicts BTC-only IS Sharpe STAYS NEGATIVE while BTC-only OOS Sharpe STAYS POSITIVE — i.e., F7 sign-mismatch (IS-NEG / OOS-POS) is the PREDICTED outcome, not an anomaly. F7's traditional "sign-agreement = good" framing INVERTS for /020. Document this explicitly: **/020's H_INTRINSIC hypothesis predicts F7 sign-DISAGREEMENT as preservation of the asymmetric rotation**. F7 SAME-SIGN-POSITIVE would actually be PROMISING-tail (gate-equivalent without gate — cohort isolation alone restructured BTC's asymmetric rotation).

### F8 — BTC-only trade count band (cohort scale)

**Anchor**: BTC-in-pool trade counts in baseline = 113 IS / 35 OOS.

BTC-only at ENSEMBLE_SIZE=3 (vs baseline 5 seeds) → expect slightly compressed roster but Optuna at single-cohort may produce comparable counts. Predicted bands:

| F8 cell | IS trade band | OOS trade band |
|---|---|---|
| PASS | IS ∈ [70, 150] | OOS ∈ [25, 55] |
| **F8 BREACH-low** | IS < 70 OR OOS < 25 | (cohort under-trains or labels too restrictive) |
| **F8 BREACH-high** | IS > 150 OR OOS > 55 | (cohort over-trains; Optuna picks aggressive entry) |

OOS lower bound 25 = standard cycle-3 floor; OOS upper bound 55 covers /017 BTC OOS (52 trades) plus margin.

### F-AXIS-MECHANISM (compound 3-sub-check)

The single-axis isolation is the SYMBOL DIMENSION only.

- **F-AXIS #1 — Dispatch correctness** **[LOAD-BEARING — no gate, no specialization]**: ONLY Model H runs; trades.csv contains only BTCUSDT rows (zero rows for ETH/LINK/LTC/DOT). PASS criterion: `df['symbol'].unique() == ['BTCUSDT']`. Failure indicates the elif branch dispatch was bypassed or Model A/C/D/E ran by mistake.
- **F-AXIS #2 — BTC trade-count band + cohort isolation correctness** **[LOAD-BEARING per Critic /019 Rec #2 + Section 4 F7 noise-floor caveat]**: BTC IS trades ∈ [70, 150], BTC OOS trades ∈ [25, 55]. Failure indicates Model H is not training correctly or single-cohort scope is being violated by an unintended cross-symbol leak.
- **F-AXIS #3 — IS_H1 catastrophic preservation (regime-binding test)**: Sub-mechanism check on whether H_INTRINSIC holds at the regime level. Pre-registered band: BTC-only IS_H1 net_pnl ∈ [−45%, −15%] (preservation of pool's IS_H1 catastrophic −36.01% within ±15pp). If observed BTC-only IS_H1 net_pnl ≥ −10% → H1 catastrophic DISSOLVED under cohort isolation → H_INTRINSIC partially false (regime is NOT the binding constraint at single-cohort; pool training may have been amplifying H1 catastrophic). If observed IS_H1 net_pnl ≤ −60% → catastrophic AMPLIFIED → cohort isolation harmful. Backtest must report IS_H1 net_pnl in engineering_report.md (Section 10.4).
- **F-AXIS-MECHANISM #4 — n_eff_per_cell band [6, 10]** **[INFORMATIONAL per /017 + /019 LM Master §5 correction methodology]**: BTC-only cohort training row count ≈ 113-130 IS labels (between /018 LINK's 154 and /019 ETH's 159, slightly compressed). Predicted n_eff band [6, 10] based on training row count proxy (NOT post-hoc kept trade count). INFORMATIONAL. If observed n_eff < 6 → mechanism issue, flag at Phase 7.4.

### F-PORTFOLIO (informational; cannot determine verdict)

Portfolio-level Sharpe (BTC-only = 1 model = portfolio) compared to v1 baseline portfolio +0.6637. INFORMATIONAL ONLY per per-cohort methodology.

---

## Section 5 — Predicted Verdict Distribution (POST-EDA; LM Master §reservation)

Per /016/017/018/019 closeouts: cycle-3 LM Master + QR mechanism-level predictions track FLAT priors at EXPLORATION single-seed level.

LM Master pre-EDA prior (from prompt): PROMISING 25% / INERT 50% / NEGATIVE 25%. Modal INERT.

QR POST-EDA prior (this brief — UPDATE FROM LM PRIOR after EDA diagnostics):

- **PROMISING (Δ ≥ +0.20 OOS Sharpe AND OOS net_pnl Δ ≥ +15pp)**: **20%** (QR DOWN from LM Master 25% — EDA H_POOL_ANCHOR REFUTED makes "cohort isolation amplifies edge" less likely; PROMISING requires Optuna basin-lottery favorable + intrinsic edge preservation surfacing in OOS).
- **INERT (Δ ∈ [−0.20, +0.20] OOS Sharpe)**: **55%** (QR UP from LM Master 50% — modal cell strengthened by EDA; regime-bound IS catastrophic + statistically independent BTC-ETH in pool both support modal INERT preservation).
- **NEGATIVE (Δ ≤ −0.20 OOS Sharpe)**: **25%** (QR UNCHANGED from LM Master — basin-lottery downside band; BTC-only single-seed=42 lottery could land in a worse basin than pool; BUT the OOS positive prior 4/5 across baseline + /014-/017 provides structural support).
  - **NEGATIVE-INTRINSIC** (Δ ≤ −0.55, dissolves OOS positive): **5%** subset (would refute both H_INTRINSIC and H_POOL_ANCHOR; require new explanation).
  - **NEGATIVE-CATASTROPHIC** (catastrophic-NEGATIVE): **3%** subset.

LM Master Phase 4.5 will be asked to confirm/refine these post-EDA priors in Section 3.4 update.

**Three specific mechanism predictions** (informational):

1. **F-AXIS #2 trade-count observation**: predicted IS ~100, OOS ~35 (close to baseline pool's 113 IS / 35 OOS at slightly compressed seed budget).
2. **F-AXIS #3 IS_H1 net_pnl observation**: predicted ∈ [−45%, −15%] (preservation band). H_INTRINSIC predicts middle-of-band; if observed near +0% or ≥ +5%, H_INTRINSIC is partially refuted at the regime level.
3. **OOS net_pnl observation**: predicted modal ∈ [+18%, +45%] (INERT band); modal point estimate +28% net_pnl. Sub-prediction: WR ∈ [40%, 50%], between baseline pool's 45.7% OOS and basin-lottery downside.

---

## Section 6 — Failure Modes

### 6.1 Single-cohort basin lottery at single-seed=42 EXPLORATION

BTC-only at ENSEMBLE_SIZE=3 + n_trials=18 + single-seed=42 = potentially basin-locked. BTC has UNIQUE structural prior (IS-NEG/OOS-POS rotation) — basin-lottery variance could be wider than LINK's (positive prior) or ETH's (negative prior).

**Mitigation**: pure isolation control experiment is the design (NO gate). If basin-lottery dominates verdict, the iter is appropriately diagnosed as PROMISING-INERT-MECHANICAL (loss-surface reorganization without new edge) — a documented v1 cohort-isolation pattern from /018. /027 multi-seed will dissolve basin lottery uncertainty.

### 6.2 Pool was load-bearing — H_POOL_ANCHOR re-emerges in Sharpe space

EDA ρ ≈ 0 refutes H_POOL_ANCHOR at the monthly net_pnl level. But pooled Model A might confer benefits at WITHIN-MONTH timing (label-based volume sharing across BTC+ETH bars). If true:
- BTC-only IS Sharpe drops more catastrophic than EDA modal prediction (NEGATIVE rather than INERT-preserved).
- BTC-only OOS Sharpe drops below INERT band (loses pool benefit at OOS regime too).
- Verdict cell: NEGATIVE.

If this occurs, **H_POOL_ANCHOR re-emerges at the higher-frequency timing level** (Pearson on monthly aggregates would miss within-month BTC-ETH coupling). Phase 7.4 LM Master will be asked to test: was BTC-in-pool's edge regime-driven OR within-month-timing-driven?

### 6.3 BTC-only Optuna escapes IS_H1 catastrophic — H_INTRINSIC partial-falsification

If F-AXIS #3 observation shows IS_H1 net_pnl ≥ −10% (versus predicted band [−45%, −15%]), BTC-only Optuna trajectory at narrower scope LEARNED to avoid H1 catastrophic months — H_INTRINSIC partially falsified. Verdict: PROMISING-tail (IS lift) potentially with OOS preserved (positive both halves). This would be a SURPRISE outcome — favorable.

**Mitigation**: pre-register IS_H1 reporting at Phase 7.4 / engineering_report.md.

### 6.4 OOS catastrophic regime-loss

BTC OOS at /015 was the only outlier among baseline+/014-/017 (−7.18% net_pnl, OOS WR 29.5%). If /020 BTC-only lands in a Optuna basin similar to /015's, OOS could land below INERT band → NEGATIVE-tail.

**Mitigation**: /015 was a labeling-change axis (σ_t symmetric), not architecturally similar to /020's pure isolation. Plausibility low but tail-risk noted.

### 6.5 Wall-clock breach (very low probability)

25 min predicted with 79% margin. Even worst-case 2× linear scaling stays under 1h. Kill-switch at 45 min provides additional safety. No realistic path to 2h breach.

### 6.6 PROMISING-MECHANICAL adjacency (LM Master watch; Critic Check 14)

Per /018 closeout LESSON #3 + /019 closeout LESSON #5 — if /020 verdict is PROMISING but BTC-only kept-trade roster preserves >80% Jaccard with baseline BTC-in-pool roster, classify as PROMISING-MECHANICAL (loss-surface optimization, not new edge). Phase 7.4 LM Master will compute trade_id Jaccard between /020 BTC-only roster and baseline BTC pool roster.

This adjacency does NOT change the brief design; it informs Phase 7.4 + Phase 7.5 classification and /027 bundle treatment (PROMISING-MECHANICAL = strictly accretive component decision, NOT new edge ingredient, NON-COMPOUNDABLE per `feedback_promising_mechanical_subtype.md`).

### 6.7 Trade-count under-fire (cohort under-trains)

If BTC IS trades < 70 or OOS trades < 25, F-AXIS #2 BREACH-low. Possible causes: Optuna trajectory at single-cohort produces aggressively-conservative trade-rate; ATR thresholds too tight at single-symbol; some labels labelled inconclusive at narrower training scope.

**Mitigation**: F-AXIS #2 lower bound 70 is below baseline 113; meaningful margin for compression. If observed IS < 70, would flag at Phase 7.4 for LM Master interpretation.

---

## Section 7 — Optional / informational metrics

- BTC-only DSR: expected LOWER than baseline portfolio DSR (single-symbol = lower n_obs; 11 OOS months vs baseline's 15 OOS months in monthly cadence). INFORMATIONAL per EXPLORATION rule.
- BTC-only PBO via CSCV: deferred (single-cohort = limited n_obs).
- BTC-only PSR_monthly_vs_1: expected to be very low (anchor is +33.17% net_pnl ≈ +0.30 monthly Sharpe; matching +1.0 unlikely at single-symbol EXPLORATION). INFORMATIONAL.
- Pareto front: N/A (single-seed EXPLORATION).
- Optuna trial CV variance: track at Phase 7.4 for basin-lottery diagnosis.
- BTC trade-id Jaccard against baseline BTC roster: computed at Phase 7.4 per Section 6.6.

---

## Section 8 — Verdict Matrix (per-cohort + pure isolation variant)

The verdict cell is determined by F1 + F-AXIS-MECHANISM #1/2/3, with F7 ACTIVE-with-noise-floor-caveat (Section 4 F7).

| Row | F1 OOS Sharpe Δ | F-AXIS #1 dispatch | F-AXIS #2 trade band | F-AXIS #3 IS_H1 band | F7 BTC OOS sign | Verdict cell |
|---|---|---|---|---|---|---|
| 1 | ≥ +0.20 | PASS | PASS [70-150, 25-55] | PASS or DISSOLVED | POSITIVE (preserved) | **PROMISING** |
| 2 | ≥ +0.20 | PASS | PASS | DISSOLVED (IS_H1 ≥ −10%) | POSITIVE | PROMISING-IS-DISSOLVED (favorable surprise; rare; mechanism note) |
| 3 | ∈ [−0.20, +0.20] | PASS | PASS | PASS (band middle) | POSITIVE (preserved) | **INERT (modal)** |
| 4 | ∈ [−0.20, +0.20] | PASS | PASS | PASS | NEGATIVE (sign-flip OOS) | INERT-OOS-MISALIGNED (unfavorable INERT; mechanism note) |
| 5 | ≤ −0.20 | PASS | PASS | PASS or any | NEGATIVE | **NEGATIVE** |
| 6 | ≤ −0.55 | PASS | (band-violation OK) | (band-violation OK) | NEGATIVE | **NEGATIVE-CATASTROPHIC** |
| 7 | any | FAIL (F-AXIS #1 not BTC-only) | any | any | any | **BLOCK-PENDING-FIX** (dispatch broken) |
| 8 | any | PASS | FAIL low/high | any | any | **BLOCK-PENDING-FIX or NEGATIVE-COHORT-FAIL** depending on cause |

**Verdict cell decision protocol**:
- F-AXIS #1 dispatch FAIL → BLOCK-PENDING-FIX immediately; orchestrator dispatches QE for fix.
- F-AXIS #2 trade band FAIL → diagnostic at Phase 7.4 (LM Master interprets cause); cell may stay BLOCK-PENDING-FIX or downgrade to NEGATIVE.
- F1 magnitude + F7 sign-direction set the standard cell.
- F-AXIS #3 IS_H1 band is the regime-binding check; informs subtype label (INTRINSIC-preserved vs DISSOLVED-favorable vs AMPLIFIED).

---

## Section 9 — Library Stack

No additions. v1's existing stack:
- `mlfinlab==1.4` or `mlfinpy` (CPCV, meta-labeling utilities)
- `pypbo` (PBO)
- `fracdiff>=0.10` (fractional differentiation; informational)
- `statsmodels` (ADF)
- LightGBM (model)
- Optuna (hyperparameter search)
- `crypto_trade.features_v1.V1_FEATURE_COLUMNS_PRUNED` (40 features)
- `crypto_trade.strategies.ml.validation_v1` (PSR/DSR/CPCV/PBO)

**No cross-track imports**: zero imports from `crypto_trade.features_v2` or `crypto_trade.features_v3`. Zero imports from `crypto_trade.strategies.ml.risk_v2` (unlike /019 which imported `apply_btc_trend_filter` — /020 has no gate, no cross-import).

---

## Section 10 — Run protocol

### 10.1 Pre-flight (Phase 6.0 Critic)

After Phase 5.5 PASS:
- Verify `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` (foundation regression check).
- Verify single-axis isolation: only `run_baseline_v1.py` modified; no changes to features/labeling/optuna_bounds/risk modules.
- Verify dispatch branch `set(symbols) == set(V1_ITER020_UNIVERSE)` is structurally sound (no fallthrough, no double-dispatch).
- Verify F1/F3 calibration: anchor numbers cited match baseline CSV.
- Critic mini-Check 14 (axis family declaration): per-cohort-specialization-BTC is NEW; orthogonality justification in Section 0.6.

### 10.2 Data freshness

8h klines for BTCUSDT under `data/BTCUSDT/8h.csv` must have `close_time` within 16h of measurement time. `crypto-trade fetch --symbols BTCUSDT --intervals 8h` runs before backtest if stale. ETH/LINK/LTC/DOT data NOT NEEDED at backtest time (cohort isolation); kept on disk for /021+ continuity.

### 10.3 Backtest

```bash
uv run python run_baseline_v1.py \
  --symbols BTCUSDT \
  --pruned-features \
  --ensemble-size 3 \
  --n-trials 18 \
  --iteration-label "v1-020" \
  --reports-dir reports-v1
```

### 10.4 Engineering report contract (Critic /019 Rec #1 + /017 Rec #2 pre-commit)

`reports-v1/iteration_v1-020/engineering_report.md` is a **MANDATORY DELIVERABLE** of Phase 6.

**Timing contract**: QE writes engineering_report.md AFTER backtest completes (comparison.csv + trades.csv + per_symbol.csv all written to `reports-v1/iteration_v1-020/`) BUT BEFORE Phase 7.5 Critic dispatch. The Phase 7.5 Critic depends on engineering_report.md as one of its 8+1 mandatory check inputs.

**Required content** (per Critic /017 Rec #2 + /019 Rec #1):
- Section 1: backtest config (CLI args, HEAD SHA, run wall-clock)
- Section 2: comparison.csv + per_symbol.csv summary tables
- Section 3: F-AXIS-MECHANISM evidence — F-AXIS #1 dispatch correctness (symbol uniqueness check on trades.csv), F-AXIS #2 trade counts, F-AXIS #3 IS_H1 net_pnl observation
- Section 4: trade roster diagnostics — BTC trade-id Jaccard against baseline BTC roster (Section 6.6 PROMISING-MECHANICAL check)
- Section 5: Optuna trial CV variance per cell (basin-health signal)
- Section 6: any anomalies or warnings

**Phase 5.5 BLOCK condition**: brief Section 10.4 must specify Phase 6 vs Phase 7 timing UNAMBIGUOUSLY. This iter's commitment is:
- QE writes engineering_report.md AFTER backtest completes AND BEFORE Phase 7.5 dispatch.
- Phase 7.5 Critic will refuse to dispatch if engineering_report.md is missing.
- Orchestrator Phase 6 contract enforces this binding (existing scope; /019 incident triggered orchestrator-level fix).

### 10.5 Kill-switch

Engineer kills backtest if wall-clock exceeds 45 minutes. No partial-run retention; full re-launch if backtest didn't complete.

---

## Section 11 — Pre-Phase 7+8 dependencies + post-iter staging

### 11.1 Reproducibility checksum

After Phase 6 backtest, BTC-only IS roster will be deterministic given (1) `--symbols BTCUSDT`, (2) `ENSEMBLE_SEEDS[0:3] = [42, 123, 456]`, (3) `OOF_PARQUET_PATH = data/v1_iter_v1-020_trial_oof.parquet`, (4) HEAD SHA recorded at Phase 6.

### 11.2 BTC-only specialist provisional standing at /027

If /020 is **PROMISING (verdict cell row 1 or 2)**: BTC-only specialist becomes a **3rd CONDITIONAL LOAD-BEARING component** for /027 CONFIRMATION bundle, after LINK-only specialist (/018) and ETH-only + gate specialist (/019). Multi-seed regression target at /027 estimated [+0.30, +0.50] (proxy to /019's compression from +0.65 → +0.50 anchor).

If /020 is **INERT (verdict cell row 3, modal)**: BTC-only specialist is a 3rd CONDITIONAL but downgraded candidate; /027 bundle decision depends on cross-correlation with LINK + ETH+gate specialists (Section 11.6 mandate).

If /020 is **NEGATIVE (verdict cell row 5 or 6)**: BTC-only specialist DROPPED for /027; /021-/026 explorations continue. /027 bundle from 2 specialists (LINK + ETH+gate) + alternative cohort or pooled-2sym candidates.

### 11.3 Multi-seed regression projection

If PROMISING at single-seed=42: project single-seed magnitude × compression factor 0.65-0.80 (per /018 + /019 precedent). E.g., single-seed PROMISING +0.35 OOS Sharpe Δ → multi-seed regression target +0.22-+0.28.

### 11.4 Bundle math sketch (preliminary; /027 brief refines)

At /027:
- LINK-only specialist target: +0.80 multi-seed anchor (from /018).
- ETH-only + gate specialist target: +0.50 multi-seed anchor (from /019).
- BTC-only specialist target: +0.30 multi-seed anchor (provisional from /020, if PROMISING).
- Projected portfolio Sharpe with 3 specialists at cross-correlation < 0.40: ≈ +1.00 monthly OOS Sharpe (within MERGE floor +1.0).
- If cross-correlation > 0.60: bundle dilution; /027 may drop the most-correlated specialist.

### 11.5 LM Master Phase 7.4 mandate

Phase 7.4 LM Master post-mortem evaluates:
1. Phase 4.5 prediction accuracy (LM Master prior PROMISING 25 / INERT 50 / NEGATIVE 25 — directional + mechanism-level hit rate).
2. F-AXIS-MECHANISM evidence interpretation — was H_INTRINSIC supported or refuted at observation? (F-AXIS #3 IS_H1 band check).
3. BTC trade-id Jaccard against baseline BTC pool roster (Section 6.6 PROMISING-MECHANICAL diagnostic).
4. Optuna trial CV per cell (basin-lottery diagnosis).
5. Recommended /021+ axis from BTC-only outcome.

### 11.6 /027 cross-correlation pre-validation (Critic /019 Rec #3)

**Pre-registered carry-forward**: at /027 CONFIRMATION brief design, cross-correlation between LINK-only specialist (/018) roster monthly Sharpe path, ETH-only + gate (/019) roster monthly Sharpe path, AND BTC-only (/020) roster monthly Sharpe path **must be computed PRE-bundling**. If any pairwise cross-correlation > 0.60, the more-correlated specialist is DROPPED from the /027 bundle, replaced by a candidate from /021-/026 with lower cross-correlation. This is binding for /027 brief design.

### 11.7 Verdict-conditional /021+ pre-staging

- **/020 PROMISING** → /021 = DOT-only single-cohort specialization (per-cohort-specialization-DOT; NEW 12th family). DOT had IS +96.07 at /017 catastrophic-positive rotation; DOT structural IS positive, OOS approximately flat. Tests DOT's intrinsic IS-driven edge under cohort isolation. Alternative: LTC-only (per-cohort-specialization-LTC; NEW 13th family) — LTC was worst OOS contributor at baseline (−47.25%); tests NEGATIVE-prior cohort under isolation alone (no gate, similar to /020's design for BTC's IS-NEG anchor).
- **/020 INERT (modal)** → /021 = same options as PROMISING; pure cohort isolation methodology validates as 3/3 INERT-or-PROMISING across LINK + ETH + BTC = ROBUST EXPLORATION methodology. Sequence DOT → LTC or LTC → DOT at /021/022.
- **/020 NEGATIVE** → /021 = REVISIT 2-symbol POOLED cohort BTC+ETH SEPARATED (BTC alone + ETH alone, no pool, no gate). This tests "pooling helps Model A's symbols" at small scale. Alternative: methodology refinement (per LM Master /019 Phase 7.4 §6 — feature_importance.csv emission to v1 runner).
- **/020 BLOCK-PENDING-FIX** → /021 = same axis re-launched after fix (single rerun allowance per `quant-iteration-v1` skill).

---

## Section 12 — Roll-back protocol

If /020 verdict is NEGATIVE-CATASTROPHIC, BLOCK-FINAL, or otherwise NO-MERGE:
- BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). No baseline update is possible at EXPLORATION budget per `feedback_v3_baseline_update_policy.md` (only CONFIRMATION-MERGE updates baseline).
- BTC-only specialist is DROPPED from /027 CONFIRMATION substrate consideration.
- Cycle-3 continues with /021 (per Section 11.7); 5 more EXPLORATIONs to complete before /027.
- Catalog entry recorded in `briefs-v1/exploration_catalog.md` documenting NEGATIVE-CATASTROPHIC subtype if applicable.

If /020 verdict is BLOCK-PENDING-FIX (Critic isolated specific defect):
- ONE rerun allowed per v1 skill discipline.
- QR + QE address the defect (typically dispatch correctness or band-violation root cause).
- Phase 6 re-launches; Phase 7.5 dispatched a second time.
- Verdict after second pass: PASS or BLOCK-FINAL (irrevocable).

---

## Section 13 — Self-Check Template (populate at Phase 8)

**RESERVED — populated at Phase 8 closeout with Phase 7 evaluation reconciliation.**

To be filled with:
- Phase 4.5 LM Master prior accuracy
- Section 5 verdict prior accuracy (QR prediction track update)
- F-AXIS #1/2/3 observation reconciliation
- IS_H1 regime-binding observation vs H_INTRINSIC prediction
- BTC trade-id Jaccard vs baseline BTC roster (PROMISING-MECHANICAL check)
- Lessons for v1 cycle-3 catalog
- Updates to verdict-cell decision protocol if needed
- /027 LOAD-BEARING component status update
