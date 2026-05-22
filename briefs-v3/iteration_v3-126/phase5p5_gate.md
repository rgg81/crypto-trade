# Phase 5.5 Gate — iter-v3/126

OVERALL: PASS

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 and training_months=24 confirmed unchanged; IS window named (per-symbol earliest ≥2020-01-01/2022-09-22 through 2025-03-24); OOS window named (2025-03-24 through current extent); 24h source path named (data/features_v3_24h/<SYM>_24h_features.parquet offset_id=0)
- Section 1 (Hypothesis): PASS — single sentence; specific feature d24_ret_autocorr_lag1_50; IS Δ band [+0.05,+0.30] vs /121 ADJUSTED ~+1.06; OOS Δ band [+0.00,+0.30] vs /121 PUBLIC +0.9682; falsifier stated (NEGATIVE-INERT if bands not met, axis class narrowed)
- Section 2 (IS-Only Evidence): PASS — committed script: analysis/iteration_v3-126/multifreq_24h_stack_eda.py (SHA dd9fc2d, committed before brief SHA 6411e11); 7 tables T1-T7 with numerical evidence; IS-only fence asserted (close_time < OOS_CUTOFF_MS=1742774400000); 0 look-ahead violations confirmed; T5 importance ranks 2/1/3 across BCH/LDO/TRX; T6 AUC lift positive 3/3 symbols
- Section 3 (Proposed Changes): PASS — 5 enumerated changes: (1) new add_multifreq_v3_24h_features in multifreq_v3.py; (2) GROUP_REGISTRY + V3_FEATURE_COLUMNS_TOP_N 14→15; (3) runner V3_MODELS revert ATOM/RUNE/UNI→BCH/LDO/TRX, ITERATION_LABEL v3-125→v3-126, pre-flight assertions; (4) parquet regen; (5) adversarial integration test
- Section 4 (Expected OOS Impact): PASS — per-criterion anchor annotation per /122 Critic Rec 3; PUBLIC=/121 multi-seed IS+1.3108/OOS+0.9682; ADJUSTED=/121 arch-adj EXPLORATION-mode IS≈+1.06/OOS≈+0.95; IS band [+1.11,+1.36] and OOS band [+0.95,+1.25] stated; behavioral-effect predictor 10-30% IS trade-roster change
- Section 5 (Risk Mitigation): PASS — 7-gate RiskV2 + /116 no_confirm bit-identical to /121; look-ahead risk mitigated by T2 audit + integration test; merge_asof misalignment risk bounded (TRX max_lag 88h documented)
- Section 6 (Risk Management Design): PASS — MaxDD band [20%,40%] with CATASTROPHIC threshold >50%; concentration band [80%,99%] with CATASTROPHIC threshold; trade-rate band [80,130] INFORMATIONAL at EXPLORATION; no_confirm stateless w.r.t. new feature
- Section 7 (Failure-Mode Prediction): PASS — 7 failure modes F1-F7 with mechanisms (NEGATIVE-clean, NEGATIVE-INERT, NEGATIVE-catastrophic, SUSPICIOUS-OOS-DOMINANT, PROMISING-PARTIAL, PROMISING-strong, PROMISING-MECHANICAL); each has diagnosis path
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 5 NEGATIVE criteria + 3 PROMISING criteria; each criterion declares anchor (PUBLIC vs ADJUSTED) per /122 Rec 3; falsifier numbers locked pre-backtest
- Section 9 (Library Stack): PASS — no new library dependencies; lightgbm==4.6.0, numpy>=2.0, pandas>=2.2 confirmed; adversarial integration test spec with 9 assertions enumerated

## Single-Axis Verification
One primary variable: V3_FEATURE_COLUMNS_TOP_N 14→15 via APPEND d24_ret_autocorr_lag1_50 (plus mandatory V3_MODELS revert ATOM/RUNE/UNI→BCH/LDO/TRX to restore /121 baseline universe). The V3_MODELS revert is not a second axis — it is a baseline-restore required by /125 NEGATIVE-catastrophic closeout so that /126 tests the multi-frequency axis at the correct anchor. All other parameters (ATR, K, no_confirm, REQUIRED_GAP, gates) are bit-identical to /121. PASS

## Reasons (if BLOCK)
N/A — OVERALL=PASS
