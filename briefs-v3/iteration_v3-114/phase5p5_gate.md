# Phase 5.5 Gate — iter-v3/114

OVERALL: PASS

Iteration type: EXPLORATION (cycle-6 slot #5 of 10)
Cadence check: wall-clock ≤ 2h budget declared; `--exploration --n-trials 35`;
  ENSEMBLE_SIZE=3; single axis (LDO realvol kill_LOW gate); PASS

Brief SHA checked: 4cdc985 (docs(iter-v3/114): research brief — Section 3.5 runner-guard update)
Prior gate: 953bfbe (BLOCK — Section 3.5 missing runner guard update)
Re-check result: BLOCK gap resolved — see Runner-Guard Verification below.

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24
  confirmed unchanged; IS window 2022-09-22→2025-03-24; OOS window 2025-03-24→2026-05;
  immutability stated explicitly
- Section 0.5 (Iteration Type Declaration): PASS — TYPE=EXPLORATION; run command
  declared; ENSEMBLE_SIZE=3; wall-clock ≤ 2h; single-axis declared; cadence slot #5
  of 10 documented
- Section 1 (Hypothesis): PASS — one sentence, specific mechanism (LDO low-vol-chop
  regime forces SL/timeout via 2:1 ATR barrier needing movement; kill_LOW gate halts
  LDO in that regime), cites IS evidence (/113 OOS LDO attribution), predicts OOS lift
- Section 2 (IS-Only Evidence): PASS — committed script at
  `analysis/iteration_v3-114/` (EDA SHA d8a9725); 3 scripts + 19 result tables;
  IS-only assertion confirmed at _shared.py:130-131 (`close_time < OOS_CUTOFF_MS`);
  OOS roster touch explicitly fenced (T9/A2 coverage annex, not threshold tuning);
  deadlock-impossibility proved (T1); trigger ranking table (S1); surgicality override
  documented (S4); counterfactual delta computed (S2/S3); threshold sweep (T3);
  honest caveats declared (§2.6: 9-trade IS roster thin; per-bar OOS polarity
  sign-flips; candle-panel directional evidence null); verdict SHARPENED-GO
- Section 3 (Proposed Changes): PASS — labeling unchanged; symbols unchanged (BCH/
  LDO/TRX); V3_FEATURE_COLUMNS revert 22→14 specified (drops 8 d_* daily features);
  sole axis: enable RiskV3 primitive 9 LDO-scoped with kill_LOW ldo_realvol_zscore
  trigger; REQUIRED_GAP=66 confirmed unchanged
- Section 3.5 (Implementation Feasibility): PASS — runner-guard gap resolved by
  brief commit 4cdc985; see Runner-Guard Verification below
- Section 4 (Expected OOS Impact): PASS — anchor declared (/060 IS+0.8325/OOS+0.1403);
  IS point estimate +0.87 with 80% interval [+0.78, +0.98]; OOS point estimate +0.18
  with 80% interval [-0.10, +0.45]; falsifier declared (OOS < -0.10 OR IS < +0.7325);
  PROMISING bar declared (IS Δ≥+0.10 AND OOS Δ≥+0.20 AND frac_positive_paths≥0.50);
  SUSPICIOUS gate (OOS/IS > 3.0) declared; behavioural-effect predictor pre-registered
  on two correct channels (Channel A: 13.0% IS LDO candle suppression; Channel B: ≥1
  LDO IS trade suppressed)
- Section 5 (Risk Mitigation): PASS — threshold IS-calibrated (T3 sweep, not OOS-tuned);
  ORACLE counterfactual documented (+2.36 IS weighted-PnL delta); deadlock risk
  explicitly mitigated (exogenous trigger, no closed feedback loop); look-ahead risk
  mitigated (shift(1) + searchsorted left-1); over-suppression risk bounded (13% panel
  fire-rate); inherited 7-primitive stack unchanged
- Section 6 (Risk Management Design): PASS — 8-primitive table with fire-rate
  predictions; gate-fire order declared (primitive 9 fires before model inference);
  regime coverage documented (LDO low-realized-vol regime only; BCH/TRX zero coverage);
  dead-path precedent (primitive 9 /022/074 TRX-BTC-stress) addressed head-on with
  three material distinctions (different symbol, different trigger family, opposite
  polarity)
- Section 7 (Failure-Mode Prediction): PASS — modal outcome pre-registered as
  INERT-to-mildly-negative; mechanism predicted (thin signal diluted in BCH-dominated
  portfolio); IS/OOS predicted intervals match Section 4; second failure mode
  (Channel B inertia — 0 LDO trades suppressed) pre-registered; clean PROMISING
  outcome described as less-likely; gates that would catch each failure mode identified
- Section 8 (MERGE/NO-MERGE Criteria): PASS — EXPLORATION-only (no baseline update);
  PROMISING criteria locked (C1–C6 including Channel B non-inertia and BCH/TRX
  bit-identity checks); NEGATIVE criteria locked (F1 OOS < -0.10, F2 IS < +0.7325);
  INERT criteria locked; SUSPICIOUS flag defined; trade-rate floor deferred to
  CONFIRMATION-bundle level per feedback_v3_trade_rate_floor_bundle_level.md
- Section 9 (Library Stack Declaration): PASS — no new libraries; pinned versions
  (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0,
  scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1); new builder uses only numpy/
  pandas/pathlib; no mlfinlab/mlfinpy/pypbo/fracdiff paths added
- Section 10 (QR Audit Trail): PASS — axis source documented (iter-v3/113 diary
  Section 9); QR EDA-driven trigger selection supersedes diary framing; surgicality
  override justified (S4); honest SHARPENED-GO disclosure; dead-path due diligence
  documented (/022 NEGATIVE + /074 INERT both TRX-scoped BTC-stress); EDA SHA
  d8a9725 recorded

## Cadence Check
- EXPLORATION slot #5 of 10 for cycle 6: PASS (slots #1-#4 consumed by /110, /111,
  /112, /113; iter-v3/120 is the mandatory cycle-6 CONFIRMATION; cadence ratio on
  track)
- Wall-clock budget ≤ 2h: PASS (declared; comparable EXPLORATIONs ran 0.4-1.1h)
- --exploration --n-trials 35, ENSEMBLE_SIZE=3: PASS (declared in Section 0.5)
- Single axis: PASS (sole axis is the LDO realvol kill_LOW gate; 22→14 feature
  revert is mandatory /113-closeout housekeeping, not a second axis)

## Section 3.5 Feasibility Verification

**RiskV2Config fields (2 new fields + ldo_realvol_lookback_bars):** IMPLEMENTABLE.
Neither `enable_ldo_realvol_gate`, `ldo_realvol_zscore_floor`, nor
`ldo_realvol_lookback_bars` exists in `src/crypto_trade/strategies/ml/risk_v2.py`
today. The fields are additive to the existing dataclass; no conflict.

**RiskV3Wrapper builder `_build_ldo_realvol_lookup`:** IMPLEMENTABLE. The existing
`_build_btc_regime_lookup` (risk_v3.py:49-110) is an exact template. The new builder
is byte-faithful to `_shared.build_ldo_realvol_zscore` (analysis/iteration_v3-114/
_shared.py:290-309). Construction: load `data/LDOUSDT/8h.csv`, 1-period log returns,
30-bar trailing rolling std with `.shift(1)` (past-only), expanding-mean/std
normalisation. Return dict with `open_time` and `ldo_realvol_zscore` arrays.

**RiskV3Wrapper gate method `_ldo_realvol_gate_fires`:** IMPLEMENTABLE. The
`searchsorted(..., side="left") - 1` past-only contract mirrors the existing
`_regime_gate_fires` (risk_v3.py:276-311). Returns False on NaN/missing/no-prior-bar.

**OR-composition in `get_signal`:** IMPLEMENTABLE. The existing `_regime_gate_fires`
check (risk_v3.py:373-376) is extended with OR logic. The existing BTC-stress path
is inert in /114 (`enable_regime_gate=False`); only the kill_LOW path fires in
practice. The OR preserves composability for future iterations.

**Runner `RiskV2Config` flip:** The brief specifies `regime_gate_symbols=("LDOUSDT",)`,
`enable_ldo_realvol_gate=True`, `ldo_realvol_zscore_floor=0.30`,
`ldo_realvol_lookback_bars=90`. These are implementable as new fields.

**V3_FEATURE_COLUMNS 22→14 revert:** VERIFIED. `V3_FEATURE_COLUMNS_TOP_N` currently
contains 22 entries at `src/crypto_trade/features_v3/__init__.py:170` (the /113
state: 14 canonical 8h features + 8 d_* daily features added at /113 commit
`0bd50fd`). Section 3.5 correctly specifies deleting the 8 `d_*` entries and the
/113 commentary block (lines ~290-303), restoring the 14-feature state. The
`multifreq_v3` module and its `GROUP_REGISTRY` registration stay as dormant
infrastructure (zero revert cost — established v3 dead-code pattern). The
`_verify_feature_columns` count will return to 14. IMPLEMENTABLE.

**ITERATION_LABEL → "v3-114":** Current value is `"v3-113"` at run_baseline_v3.py:131.
Change to `"v3-114"` is straightforward. IMPLEMENTABLE.

**`label_mode` stays `triple_barrier`:** CONFIRMED at runner. PASS.

**`V3_MODELS`=BCH/LDO/TRX:** CONFIRMED unchanged. PASS.

**`REQUIRED_GAP`=66:** CONFIRMED. `(timeout_candles=21 + 1) × n_symbols=3 = 66`.
PASS.

**Test addition (Section 3.5(6)):** Three adversarial tests specified for
`test_regime_gate.py`. IMPLEMENTABLE against existing test infrastructure.

## Runner-Guard Verification (the prior BLOCK gap)

The prior gate (953bfbe) BLOCKed on Section 3.5 missing specification of the
run_baseline_v3.py:826-831 guard update. Brief commit 4cdc985 adds Section 3.5
(3-guard). This section is verified against the actual runner:

**Lines 826-831 in run_baseline_v3.py — CONFIRMED as specified.** The current
guard reads exactly:

```
if strat_check.config.regime_gate_symbols != ():
    raise RuntimeError(
        f"RiskV2Config.regime_gate_symbols = {strat_check.config.regime_gate_symbols} "
        "— expected () (empty). iter-v3/075: the /074 regime gate is reverted; "
        "regime_gate_symbols must be empty."
    )
```

This matches the brief's description of the current state. Setting
`regime_gate_symbols=("LDOUSDT",)` as Section 3.5(3) specifies would cause this
guard to raise RuntimeError and crash Phase 6.

**Lines 818-825 in run_baseline_v3.py — CONFIRMED as specified.** The adjacent
`enable_regime_gate=False` guard is at exactly lines 818-825:

```
if strat_check.config.enable_regime_gate:
    raise RuntimeError(
        "RiskV2Config.enable_regime_gate = True — expected False. ..."
    )
```

iter-v3/114 keeps `enable_regime_gate=False`, so this guard is COMPATIBLE with the
/114 config and correctly must NOT be touched. The brief specifies this explicitly.

**Brief (3-guard) replacement specification:** The brief specifies BOTH replacement
guards precisely — (a) `!= ("LDOUSDT",)` check with the iter-v3/114 error message,
and (b) `not enable_ldo_realvol_gate` check with the iter-v3/114 error message.
This is a concrete, non-ambiguous implementation instruction. The QE can implement
this without any design judgement.

**Diff scope verified:** git diff b27c305..4cdc985 confirms the (3-guard) block is
the ONLY change between the original blocked brief and the re-submitted brief. No
other section was modified — all prior PASS verdicts are unchanged.

BLOCK gap: RESOLVED.

## Dead-Path Justification Check

PASS. The brief (Section 6, Section 10) documents that iter-v3/114 is materially
different from the closed /022/074 primitive-9 dead path across three axes: (1)
different target symbol (LDO vs TRX); (2) different trigger family (ldo_realvol_zscore
vs abs(btc_drawdown_pct)/abs(btc_vol_zscore)); (3) opposite gate polarity (kill_LOW
vs kill_HIGH). The EDA (S1) explicitly tests the two BTC triggers already in primitive
9 and shows they do NOT separate LDO losers (IS std_gap +0.19/+0.06) — this is new
committed IS-only evidence that justifies the re-activation of the primitive for a
different symbol/trigger/polarity. The BASELINE_V3.md "Dead Ideas" records primitive
9 as "CLOSED across two data points" and Section 10 acknowledges this head-on.
The justification is sound and EDA-grounded.

## Deadlock-Impossibility Argument Check

PASS. The argument is sound and not hand-waved. Section 2.1 (T1) establishes the
formal criterion: the trigger value at every bar is a function of LDO price (1-period
log returns), not LDO trade outcomes. The kill-switch halts LDO trading; it does not
halt LDO price. The gate-state transition function therefore has no dependence on the
gate's own action. The T1 table explicitly classifies all three candidate triggers by
"depends on LDO trades?" and "deadlock possible?" — all three are exogenous, all three
are deadlock-free. The EDA `_shared.build_ldo_realvol_zscore` (analysis/iteration_v3-114/
_shared.py:290-309) confirms the construction reads only `close` column from LDO 8h
CSV. The contrast with /054 is explicit: /054's trigger was an endogenous LDO PnL
streak; the /114 trigger is an LDO price-derived series, making the /054 failure mode
structurally impossible here.
