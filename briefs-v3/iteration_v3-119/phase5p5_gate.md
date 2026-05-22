# Phase 5.5 Gate — iter-v3/119

OVERALL: BLOCK

## Per-Section Status

- Section 0 (Data Split): PASS
- Section 1 (Hypothesis): PASS
- Section 2 (IS-Only Evidence): PASS — committed script: `analysis/iteration_v3-119/` (SHA `7aa5cc5`)
- Section 3 (Proposed Changes): PASS
- Section 3.5 (Code-Change Manifest): INVALID — see Reasons
- Section 4 (Expected OOS Impact): PASS
- Section 5 (Risk Mitigation): PASS
- Section 6 (Risk Management Design): PASS
- Section 7 (Failure-Mode Prediction): PASS
- Section 8 (MERGE/NO-MERGE Criteria): PASS
- Section 9 (Library Stack): PASS

## Per-Gate Detail (gates from the orchestrator prompt)

1. **Parameter provenance**: PASS. Section 0 declares ZERO tuned scalars.
   `ret_5d` lookback (15 bars) is INHERITED from the /025 value primitive.
   `taker_buy_imbalance_20` window (20 bars) is INHERITED from the existing
   v3 feature inventory (the column is present in production parquets). The
   sign threshold is the natural zero-cross — no tunable scalar. The
   provenance table is complete and cites source files and line numbers.

2. **Section 3.5 code-change manifest**: INVALID — one factual error (see Reasons).
   The manifest correctly identifies all 6 changes (Change 0 through Change 6),
   correctly pins the function location in `engineered_v3.py`, correctly
   identifies the V3_FEATURE_COLUMNS_TOP_N slot swap, correctly specifies
   the runner guard update, the parquet regeneration CLI, the unit test, and
   the integration test. The single defect is a wrong module attribution
   for the `taker_buy_imbalance_20` primitive (see Reasons).

3. **Section 4 falsifier (SSC-RISK-aware)**: PASS. C6 T9 SSC ratio = 1.48×
   (FALSE — below the 2.0× threshold). The brief correctly applies the
   standard-width falsifier band rather than the SSC-RISK-tightened band.
   Mode 4 inversion is pre-registered (Section 7 Mode 4, 10% prior) as a
   potential failure even though SSC-RISK passed. Sections 4 and 7 are
   consistent.

4. **Section 7 modes**: PASS. Seven modes pre-registered with probability
   priors and first-match-wins semantics. Mode 2 (INERT-at-importance,
   covering the /015 dead-path lookalike) is at 15%. Mode 3 (per-symbol
   role-reversal). Mode 4 (catastrophic regime artifact). Mode 5 (null at
   production, /015 tbr_zscore_30 pattern). Mode 6 (suspicious OOS-dominant).
   Mode 7 (suspicious IS-dominant). The importance prediction for C6
   (rank 11/11/15, gain 55/24/12% mean ~30%) is documented in Section 2.5
   T5 and cross-referenced in Section 5 R3 and Section 8 criterion 6.

5. **Section 5 risks**: PASS. Seven risks with mitigations and IS-calibrated
   thresholds. The most important risk — R3 INERT-at-importance (/015
   lookalike) — is explicitly covered. R2 covers the SSC-RISK /118 failure
   mode. R7 covers the /118 ema_signed_volregime accidental-retention risk.

6. **Sister-of-C3 lineage check**: PASS. Section 1 Hypothesis explicitly
   states the regime classifier is `taker_buy_imbalance_20` (microstructure
   order-flow primitive) — structurally orthogonal to vol-regime (return-
   volatility) and hurst-regime (long-memory). Section 10.5 explains why C6
   reuses the `ret_5d` value primitive (from /025, which is LIVE in
   V3_FEATURE_COLUMNS) but pairs it with an orthogonal regime classifier.
   The /118 closure was the REGIME CLASSIFIER (vol-regime), not the value
   primitive. The brief correctly traces this lineage. The dead-path
   `tbr_zscore_30` (/015) is distinguished: the /015 dead-path was a
   standalone INERT primitive; C6 uses `taker_buy_imbalance_20` ONLY inside
   `sign(.)` — the magnitude never enters the model.

7. **/120 CONFIRMATION precommitment**: PASS. Section 0.5 declares /119 as
   FINAL EXPLORATION (#10 of 10) with iter-v3/120 as the mandatory cycle-6
   CONFIRMATION. Section 6 includes a gate-implication table for /120.
   Section 10.7 trajectory recaps the /120 SINGLE-COMPONENT CONFIRMATION
   protocol (bundles /116 no_confirm + /119 if PROMISING). The /118 diary
   Section 8.2 pre-registered /120 specs are externally referenced; the /119
   brief does not restate them verbatim but clearly defers to them.

## Reasons (BLOCK)

- **Section 3.5 (Code-Change Manifest) — INVALID: Wrong source module for
  `taker_buy_imbalance_20`.**

  The brief states (Section 0 parameter table, Change 1 docstring, Change 1
  `add_engineered_v3_features` comment, R5 risk mitigation, and Section 10.6
  provenance summary) that `taker_buy_imbalance_20` is computed by
  `volume_micro_v3.py` / `add_volume_micro_v3_features`. This is factually
  incorrect.

  **Actual location**: `src/crypto_trade/features_v3/microstructure_v3.py`,
  function `add_taker_buy_imbalance_20`, dispatched via
  `GROUP_REGISTRY["microstructure_v3"]` = `add_microstructure_v3_features`
  (verified in `src/crypto_trade/features_v3/__init__.py` line 89). The
  `volume_micro_v3.py` module / `add_volume_micro_v3_features` function is a
  separate module serving `GROUP_REGISTRY["volume_micro"]` (VWAP deviation,
  volume CV, OBV slope, HL range ratio — NOT taker-buy imbalance).

  **Impact**: the QE, following Section 3.5 Change 1 verbatim, would produce:
  - A `compute_ret5d_signed_tbi` docstring citing `volume_micro_v3` as the
    upstream source for `taker_buy_imbalance_20`.
  - Section 5 R5 risk mitigation text citing `volume_micro_v3` for the
    past-only property.
  - The Change 6 integration test comments and docstring citing the wrong
    module.
  These would constitute factually incorrect documentation committed to the
  codebase.

  **Specific occurrences to correct**:
  1. Section 0 parameter table, row 2: `INHERITED from volume_micro_v3.py
     default` → `INHERITED from microstructure_v3.py default`; and
     `Source: existing primitive in data/features_v3/*.parquet (verified
     column present in all 3 symbol parquets)` — this claim is unverifiable
     from the worktree (parquets not present), though it is plausible given
     the column appears in GROUP_REGISTRY dispatch. The module attribution
     must be corrected.
  2. Change 1 docstring line: `(precomputed by add_volume_micro_v3_features;
     past-only by construction)` → `(precomputed by add_microstructure_v3_features
     via add_taker_buy_imbalance_20; past-only by construction)`.
  3. Change 1 docstring Args section: `taker_buy_imbalance_20 (from
     volume_micro_v3)` → `taker_buy_imbalance_20 (from microstructure_v3)`.
  4. Section 5 R5 mitigation: `taker_buy_imbalance_20 is precomputed
     past-only by volume_micro_v3` → `taker_buy_imbalance_20 is precomputed
     past-only by microstructure_v3 (add_taker_buy_imbalance_20)`.
  5. Section 10.6 provenance: `taker_buy_imbalance_20 20-bar window from
     volume_micro_v3` → `taker_buy_imbalance_20 20-bar window from
     microstructure_v3`.

  No other sections are affected. All other content in Section 3.5 is
  correct: the function placement in `engineered_v3.py`, the GROUP_REGISTRY
  ordering (microstructure_v3 runs BEFORE engineered_v3 in the registry —
  confirmed at `__init__.py` line 89 vs line 110+ for engineered), the
  past-only property of the column itself (the `shift(1)` is verified in
  `microstructure_v3.py:70`), and the parquet column-count estimate of 95.

## Disposition

**BLOCK — QR must correct the 5 module-attribution occurrences listed above
and re-submit the brief. No other sections require changes. Upon re-submission,
the gate re-runs on the corrected brief only.**

Action required: QR corrects `research_brief.md`, re-commits on
`iteration-v3/119`, and re-triggers the Phase 5.5 gate. The Engineer does
NOT proceed to Phase 6 until OVERALL=PASS.

---

## Round 2 — Re-verify (after QR fix at SHA `0060659`)

OVERALL: PASS

### Defect check

`grep -n "volume_micro_v3" research_brief.md` → **0 occurrences** (zero — defect resolved).

All 5 corrected locations now read `microstructure_v3` / `add_taker_buy_imbalance_20`:

| # | Line | Corrected text |
|---|---:|---|
| 1 | 60 | Section 0 param table row 2: `INHERITED from microstructure_v3.py default` |
| 2 | 382 | Change 1 docstring: `(precomputed by add_taker_buy_imbalance_20; past-only by construction)` |
| 3 | 392–402 | Change 1 docstring Args: `taker_buy_imbalance_20 (from microstructure_v3)` |
| 4 | 625 | Section 5 R5: `taker_buy_imbalance_20 is precomputed past-only by microstructure_v3` |
| 5 | 817 | Section 10.6 provenance: `microstructure_v3) or structurally fixed` |

### No-new-defect check

No substantive content outside the 5 corrected strings was altered. All ten mandatory sections remain intact and status-unchanged from Round 1. Substance is confirmed intact.

### Disposition

PASS — proceed to Phase 6 implementation.
