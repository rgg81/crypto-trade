# Phase 5.5 Gate — iter-v3/111

OVERALL: PASS

Iteration type: EXPLORATION (cycle-6 EXPLORATION #2 of 10)
Wall-clock cap: 2h HARD CAP; run config `--exploration --n-trials 35`; ENSEMBLE_SIZE=3
Branch: `iteration-v3/111` — CORRECT (verified `git branch --show-current`)
Worktree root: `/home/roberto/crypto-trade/.worktrees/quant-research` — CORRECT

---

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24`
  explicitly declared unchanged/immutable. IS window (earliest kline per symbol → 2025-03-24)
  and OOS window (2025-03-24 → ~2026-05-18) named in absolute dates. IS-only EDA asserted via
  `OOS_CUTOFF_MS` filter in the reused `analysis/iteration_v3-110/_shared.py` (lines 21–25
  referenced in brief). No data-window change vs /110 or /059.

- Section 0.5 (Iteration Type): PASS — TYPE: EXPLORATION declared. Single axis (V3_MODELS
  universe swap). Wall-clock budget 2h. Run config `--exploration --n-trials 35`. ENSEMBLE_SIZE=3
  correctly stated (correcting the /110 brief's stale "single-seed" wording per /110 diary Lesson
  5). Cycle-6 cadence position (EXPLORATION #2 of 10; /120 is the mandatory separate CONFIRMATION)
  correctly accounted.

- Section 1 (Hypothesis): PASS — One sentence: replacing BCH/LDO/TRX with the signal-screened
  CRV/AAVE/GRT/ADA universe produces an IS-positive, less-concentrated v3 book because the /109
  permutation null is specific to the BCH/LDO/TRX feature→label joint distribution. Specific and
  falsifiable (references the /109 permutation null as the domain-of-validity claim, lists Section
  8 as the explicit falsifier). The distinction from /110 (same hypothesis, now cleanly testable
  because runner is corrected) is correctly characterised.

- Section 2 (IS-Only Numerical Evidence): PASS — committed EDA scripts at `analysis/iteration_v3-110/`
  (commit `cfeaf34`) REUSED verbatim with documented justification: the /110 EDA was already computed
  under `triple_barrier` (the correct label geometry), so the reuse is sound. Pointer note committed
  at `analysis/iteration_v3-111/POINTER.md` (confirmed present on disk). Numerical tables T1–T10
  reproduced in the brief: permutation null on incumbents (T1/T10), raw gated books U_B vs
  incumbent (T9), composite signal ranking (T6), per-symbol gated books (T7), LOO variants (T8),
  PnL-proxy correlation (T5). All rows asserted IS-only (`close_time < OOS_CUTOFF_MS`). No
  category-matching without numbers.

- Section 3 (Proposed Changes): PASS — enumerated changes: (a) V3_MODELS wholesale universe swap
  (BCH/LDO/TRX → CRV/AAVE/GRT/ADA); (b) runner label correction items 1–10 in Section 3.5 (the
  Critic-mandated correction, not a new research axis). V3_EXCLUDED_SYMBOLS disjointness check
  noted (CRV/AAVE/GRT/ADA not in the excluded list). Feature columns, labeling params, risk gates
  all explicitly stated UNCHANGED.

- Section 4 (Expected OOS Impact): PASS — predicted OOS monthly Sharpe −0.10 to +0.70 (central
  +0.30); predicted IS +0.30 to +1.00 (central +0.60). Anchored on the /060 EXPLORATION-mode
  reference (+0.8325 IS / +0.1403 OOS) per `feedback_v3_cycle1_axis_pass_criteria.md`. Behavioral-
  effect predictor present (IS trades 180–320, OOS trades 90–180). Explicit falsifier cross-
  referenced to Section 8.

- Section 5 (Risk Mitigation): PASS — concentration mitigation via structural universe choice
  (top-symbol share 140% → 42%), 7-gate RiskV2 stack carried unchanged, drawdown brake explicitly
  kept disabled (per /054 STATEFUL-gate finding), LOO robustness from T8, runner correction
  closing the stale-state bug class.

- Section 6 (Risk Management Design): PASS — 7-primitive table present with per-gate status and
  fire-rate predictions for the new CRV/AAVE/GRT/ADA universe. Regime coverage discussed (sector
  diversity: DeFi, indexing, large-cap L1). No new primitive introduced.

- Section 7 (Failure-Mode Prediction): PASS — 5 failure modes pre-registered: Mode 1 (IS AUC
  does not survive IS→OOS regime shift), Mode 2 (PROMISING-MECHANICAL — concentration win without
  edge win), Mode 3 (AAVE OOS dragger — weakest IS evidence, pre-registered dead-path risk),
  Mode 4 (ADA OOS dragger — dead-path symbol, 5-seed-ensemble wash risk), Mode 5 (process —
  second label carry-over if correction does not land, pre-empted by Section 3.5 + Section 3.6).
  Each mode includes expected metric signatures and gate-catchment. All forward-looking, verifiable
  against Phase 8 diary outcomes.

- Section 8 (MERGE/NO-MERGE Criteria): PASS — EXPLORATION (no merge, no baseline update).
  LOCKED numerical criteria pre-registered against /060 anchor per
  `feedback_v3_cycle1_axis_pass_criteria.md`: PROMISING requires IS ≥ +0.9325 (Δ ≥ +0.10) AND
  OOS ≥ +0.3403 (Δ ≥ +0.20) AND frac_positive_paths ≥ 0.50 AND OOS/IS ≥ 0.40 AND top-symbol
  OOS share ≤ 70% AND OOS trades ≥ 130. PROMISING-MECHANICAL, NEGATIVE, INERT bands all defined.
  NEGATIVE-SUSPICIOUS band (daily IS/OOS ratio outside [0.5, 2.0]) included. No post-hoc
  renegotiation possible.

- Section 9 (Library Stack): PASS — no new library. Reused EDA stack listed with pinned versions
  (lightgbm==4.6.0, scikit-learn==1.8.0, scipy==1.17.0, numpy==2.2.6, pandas==3.0.0,
  pyarrow==23.0.1). Phase 6 backtest stack listed (optuna==4.8.0, statsmodels==0.14.6). No
  mlfinlab/fracdiff/pypbo version change. No fallback. `pyproject.toml` declared unchanged.

- Section 10 (QR Audit Trail): PASS — origin documented (Critic-mandated corrected re-test from
  /110 review.md Rec 4 + /110 diary Section 9). EDA reuse basis justified with source-line
  reference (`analysis/iteration_v3-110/_shared.py` lines 21–25). Axis-selection rationale
  carried from /110 (cycle-6 axis menu item 1; /109 permutation null universe-specific finding;
  no prior wholesale replacement). AAVE and ADA dead-path disclosures with new quantitative
  evidence. Dead-path rule satisfied.

---

## Section 3.5 `label_mode` Revert — Cross-Check Against Actual Runner

The brief's Section 3.5 specifies five correction items. Cross-checked against the CURRENT state
of `run_baseline_v3.py` (NOT the post-Phase-6 state):

**Item 1 — Revert `label_mode="trend_scanning"` → `"triple_barrier"` and neutralize
`trend_scan_grid` at `_build_v3_model`'s `common_kwargs`.**

Actual runner state: line 1917 reads `label_mode="trend_scanning"` and line 1918 reads
`trend_scan_grid=(5, 8, 13, 21)`. These two lines are PRESENT and WRONG — exactly what Section
3.5 item 1 identifies as requiring the revert. The brief's line references (1917–1918) are
ACCURATE. The scope note (propagates to all four symbol models via common_kwargs passed at lines
1925/1927/1932) is ACCURATE.

**Item 2 — Fix pre-flight assertion target at `run_baseline_v3.py:1125`.**

Actual runner state: line 1125 reads `expected_label_mode = "trend_scanning"`. The comment block
at 1114–1118 reads "iter-v3/105: label_mode must be 'trend_scanning' — the ONE clean variable".
The assertion block at 1126–1132 enforces `trend_scanning`. The `trend_scan_grid` assertion block
at 1134–1146 and the embargo gate at 1147–1158 are present and active (they would reject a
`triple_barrier` runner if left untouched). The print at 1159–1163 announces `label_mode
(iter-v3/105): 'trend_scanning'`. All of this is exactly the stale pre-flight state Section 3.5
item 2 identifies as requiring correction. The brief's line references (1125 for the target
variable; 1126–1163 for the assertion/print block; 1134–1146 for the grid block; 1147–1158 for
the embargo gate) are ACCURATE.

**Item 3 — Rewrite stale `iter-v3/105` comment blocks at lines 1114–1118 and 1912–1916.**

Actual runner state: line 1114–1118 contains the exact stale comment ("iter-v3/105: label_mode
must be 'trend_scanning' — the ONE clean variable for this iteration"). Lines 1912–1916 contain
the exact stale comment ("iter-v3/105: trend-scanning label (one clean variable). Replaces the
fixed 21-candle triple-barrier TRAINING label"). Both blocks are present and stale. The brief's
line references are ACCURATE.

**Item 4 — Extend `_canonical_v059` guard at lines 1032–1050 to add `label_mode` and
`trend_scan_grid` entries.**

Actual runner state: the guard at 1032–1050 contains 11 knobs and does NOT include `label_mode`
or `trend_scan_grid` — confirming the exact blind spot Section 3.5 item 4 identifies. The guard's
failure message references "ALL 11 knobs" (line 1057). The brief's instruction to add two entries
(`label_mode` canonical `triple_barrier` and `trend_scan_grid` neutralized/default) and update the
knob count print (line 1060–1064) is ACCURATE and complete. The mechanism (reading `label_mode`
from the `_p13_lgbm` instance already built at 1071–1100) is correctly described — `_p13_lgbm` is
assigned at line 1100 as `_p13_inner`, which is the unwrapped `LightGbmStrategy` instance. The
`label_mode` attribute is confirmed present on `LightGbmStrategy` (line 1119 checks
`hasattr(_p13_lgbm, "label_mode")`).

**Item 5 — Bump `ITERATION_LABEL` at line 131: `"v3-110"` → `"v3-111"`.**

Actual runner state: line 131 reads `ITERATION_LABEL = "v3-110"`. The brief's line reference and
the target value are ACCURATE.

**Item 6 — `REQUIRED_GAP` and `V3_MODELS` already correct.**

Actual runner state: `V3_MODELS` at lines 190–195 is already the 4-tuple CRV/AAVE/GRT/ADA (set
at /110 commit `f7e564f`). `REQUIRED_GAP` is imported from `validation_v3.py` where it is defined
as `(21+1)*4 = 88` (line 76 of `validation_v3.py`). The `_canonical_v059` guard at line 1039
asserts `REQUIRED_GAP == 88`. The brief's statement that no edit is needed is ACCURATE.

**Item 7 — Clean stale `Gap:` diagnostic print string at lines 2769–2770.**

Actual runner state: line 2769–2771 reads `Gap: {REQUIRED_GAP} (= (21+1)*3; iter-v3/088
RE-ARCHITECTURE reverts /087's 6-sym expansion to the 3-sym /059 universe BCH+LDO+TRX; timeout
UNCHANGED 10080 min)`. This is the stale string the Critic flagged. The brief's line references
(2769–2770) and the proposed rewrite are ACCURATE. Note: line 2715 also carries a stale comment
`# asserts REQUIRED_GAP == 66 (3-symbol /059 universe, iter-v3/088)` — this is an additional
cosmetic stale comment not listed in Section 3.5. It does not affect correctness (the assertion
itself is against the imported `REQUIRED_GAP` constant = 88) but the QE should clean it as part
of the cosmetic sweep at item 7. This gap is minor and does not block the gate.

**Item 8–10 — Data freshness pre-flight, CPCV n_paths, pre-flight symbol references.**

These are Phase 6 procedural mandates (data freshness check, CPCV unchanged, no
BCHUSDT/LDOUSDT/TRXUSDT references in pre-flight build calls). They are correctly stated and do
not require runner edits beyond the Phase 6 confirmation step.

**Section 3.5 `label_mode` revert verdict: CORRECTLY AND COMPLETELY SPECIFIED.** All five
mandatory corrections (revert at 1917–1918, pre-flight fix at 1125/1126–1163, comment rewrite at
1114–1118/1912–1916, guard extension at 1032–1050, ITERATION_LABEL bump at 131) are accurately
identified with correct line references cross-checked against the actual current runner. The
brief's description of what each correction does and why is technically accurate. No correction is
missing, mis-scoped, or pointing at wrong lines.

---

## Cadence Check

- Cycle-6 EXPLORATION cadence: iter-v3/110–119 (10 EXPLORATIONs); iter-v3/120 is the mandatory
  separate CONFIRMATION. This is EXPLORATION #2 of 10. iter-v3/110 consumed slot #1 (confounded
  run; UNRESOLVED verdict); iter-v3/111 consumes slot #2.
- The 10:1 cadence rule (`feedback_v3_strict_10_to_1_cadence.md`) is respected.
- Wall-clock: /110 ran in 1.08h on the identical 4-symbol universe; iter-v3/111 corrects the
  runner only (no new feature/labeling complexity). 2h HARD CAP is realistic.
- Run config `--exploration --n-trials 35` sets ENSEMBLE_SIZE=3. CONFIRMED correct.

---

## Reasons (none — OVERALL: PASS)

All 10 mandatory brief sections (0, 0.5, 1–9, 10) are present and valid. Section 3.5's
`label_mode` revert is correctly and completely specified with accurate line references. No
blocking gaps identified.
