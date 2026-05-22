# Phase 5.5 Gate — iter-v3/101

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24` explicitly
  declared immutable; IS window and OOS window named in absolute dates; all 4 EDA scripts
  confirmed IS-only via `load_is()` helper filtering `open_time < OOS_CUTOFF_MS`.
- Section 1 (Hypothesis): PASS — one-sentence hypothesis is specific: rank-normalizing the
  `sample_weight` strips the ATR-magnitude vol-chasing tilt (corr(weight,|fwd-return|)=+1.00 on
  LDO) while preserving the edge ordering, lifting held-out directional accuracy +0.0218 CI
  strictly above zero. Mechanism, direction, and IS proxy evidence are all named.
- Section 2 (IS-Only Evidence): PASS — four committed EDA scripts at `analysis/iteration_v3-101/`
  (commit `247c4d3`): `eda1_signal_and_weight_characterization.py`,
  `eda2_weight_decomposition.py`, `eda3_weight_horse_race.py`, `eda4_w2_robustness.py`.
  Output tables (`T1`-`T4`) committed alongside. Numerical tables cover ANGLE A/H
  (uniqueness near-no-op: rank-corr 0.992-0.997, kills the /100 uniqueness recommendation),
  ANGLE B/D (BCH win-rate tercile spread +0.652; W1 uniform ablation dACC -0.0074 proves
  weighting IS useful), ANGLE C (corr(weight,|fwd-return|) +1.00 on LDO/+0.995 on TRX),
  ANGLE C-race (4-design horse race — W2 CI [+0.0088,+0.0333] strictly above zero, 3/3
  symbol sign-consistent, only winner), ANGLE F (multi-seed stability: 4/5 seeds positive,
  mean +0.0115), ANGLE G (BCH share moves from -15.3% toward -10.8% under W2). Category-
  matching is absent; all claims are backed by committed numerical output.
- Section 3 (Proposed Changes): PASS — enumerated and exact: (1) `labeling.py`: add
  `weight_mode: str = "magnitude"` param, default reproduces /059 bit-for-bit, rank path uses
  `pd.Series(weights).rank(pct=True)`; (2) `lgbm.py`: thread `weight_mode` through
  `__init__` and the `label_trades` call; (3) `run_baseline_v3.py`: set
  `weight_mode="rank_normalized"` in `common_kwargs`, bump `ITERATION_LABEL` to `"v3-101"`.
  `V3_EXCLUDED_SYMBOLS` explicitly confirmed unchanged. `sample_uniqueness` explicitly NOT
  enabled. No other change stated.
- Section 4 (Expected OOS Impact): PASS — predicted OOS band [+0.73, +1.03], IS band
  [+0.95, +1.20]; explicit falsifiers F1-F5 with locked numerical thresholds (F1: OOS < +0.30;
  F2: IS < +0.70; F3: BCH IS share negative OR > 99.5%; F4: roster bit-identical or <5%
  change; F5: OOS mean-duration gap > +1.0); behavioral-effect predictor present (OOS roster
  changes 5-25% = 70-118 trades; below-5% triggers F4-adjacent INERT classification). All
  falsifiers are gates distinct from the prediction.
- Section 5 (Risk Mitigation): PASS — R1-R5 stack from /059 inherited unchanged; per-symbol
  cap explicitly confirmed disabled (per /020 closeout); simulated historical effect via
  ANGLE G W2 vs W0 (W2 improved all 3 symbols, moved BCH share from -15.3% to -10.8%); no
  new gate introduced so no new IS calibration required; structural argument for why the
  axis itself is a training-objective risk control is present.
- Section 6 (Risk Management Design): PASS — deeper structural argument present: current
  weight is a latent risk defect (corr=+1.00 with |fwd-return| on LDO) that no live gate
  fixes; rank-normalization is the training-objective analogue of a per-trade exposure cap;
  W2 selected over W3/W4 because W2 is monotone (preserves ordering) while W3/W4 are more
  aggressive interventions with CIs straddling zero; W1 ablation explicitly falsified.
- Section 7 (Failure-Mode Prediction): PASS — two explicit forward-looking failure modes:
  (1) INERT/PROMISING-MECHANICAL (most likely — monotone rank transform barely shifts
  LightGBM tree splits; roster <5%; Falsifier F4); (2) NEGATIVE (rank-flat flattens BCH
  edge proxy, Falsifiers F1/F2). Evidence for and against each mode cited. Justification
  for why the experiment still runs (EDA #3 CI strictly above zero — not a dead axis) is
  present and persuasive.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — six-level classification taxonomy with locked
  disjunctive precedence: BLOCKED / NEGATIVE / SUSPICIOUS / INERT/PROMISING-MECHANICAL /
  PROMISING / NULL-RESULT. Each level has locked numerical criteria referencing specific
  falsifiers. Pre-registered before backtest. BASELINE_V3.md explicitly not updated by this
  EXPLORATION. Tag v0.v3-101 declared a closeout marker only.
- Section 9 (Library Stack): PASS — no new library; `pandas.Series.rank` already a
  dependency; all pinned versions stated (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6,
  pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1);
  integration-test mandate is specific: unit test for magnitude byte-identity + rank
  monotonicity + invalid-mode raise; integration smoke test for end-to-end train with
  `weight_mode="rank_normalized"` asserting `sample_weight` vector is rank-normalized and
  no train/test boundary is crossed; Phase-6 preflight verification of `common_kwargs`.
- Section 10 (QR Audit Trail): PASS — documents that axis selection was QR-led with EDA
  basis; records that EDA #1/ANGLE H falsified the /100-recommended uniqueness half
  (near-no-op, rank-corr 0.992-0.997); records QR's rationale for choosing the magnitude-
  reweight over an 8th feature family (cycle 4's /098 feature-expansion GO/NO-GO EDA found
  no candidate clears OOS-robustness bar); user's 2026-05-18 directive explicitly named
  "risk management" which this axis satisfies at the training-objective layer.

## Reasons for PASS

All 10 mandatory sections are present and substantive. Hypothesis is specific (mechanism,
evidence, direction, proxy metric with CI). Section 2 evidence is numerical (not
category-matching), from 4 committed scripts with committed CSV output. Section 4 falsifiers
are enumerated, locked, and reference-distinct from predictions. Section 7 failure-mode
prediction is genuinely forward-looking. Section 8 classification taxonomy is
disjunctive-precedence and pre-registered before the backtest. ONE variable changes;
multi-variable contamination is absent. The default `weight_mode="magnitude"` reproduces
/059 behavior by construction.

## Phase 6 Verify Items

The following are HARD checks the Engineer must enforce as named integration tests
(per iter-v3/093 lesson — soft checks are not sufficient):

1. `common_kwargs` carries `weight_mode="rank_normalized"` at runtime (not just in source).
2. `ITERATION_LABEL == "v3-101"` at runtime.
3. `weight_mode="magnitude"` call to `label_trades` produces byte-identical weights to a
   no-`weight_mode` call (the v1/v2 no-regression guarantee).
4. `weight_mode="rank_normalized"` produces weights in [1, 10] that are a monotone
   transform of the magnitude weights (rank-correlation == 1.0).
5. An invalid `weight_mode` value raises `ValueError`.
