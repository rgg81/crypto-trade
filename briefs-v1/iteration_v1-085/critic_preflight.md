# Phase 6.0 Critic Pre-Flight — iter-v1/085

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: SPECIALIST — UNIUSDT single-coin cohort; NEW 4-feature mean-reversion set (feature-engineering set #1); fresh-alt MINE under the REFINED structure-gated selector (GATE 1 + GATE 2). Axis family `per-cohort-specialization-UNI`.

## Pre-Flight Checks

### Check 1 (mini) — Brief + New-Feature Look-Ahead Audit: PASS

Traced all four NEW features through their actual implementations (not the brief's prose). Every one is causal by construction:

- **`rev_extension_z_3`** (`mean_reversion_v1.py:104-122`): `ret_3 = log_close − log_close.shift(3)` (past-only); rolling-50 `mean`/`std(ddof=1)` are trailing windows `[t-49, t]` with `min_periods=50` (no expanding leak, no `center=True`); the load-bearing sign flip `(−raw_z)` is applied BEFORE `.shift(1).clip(−5,+5)`. The final `.shift(1)` guarantees bar `t`'s feature reads only bars `≤ t−1`. No future close, no centering, no forward index. CLEAN.
- **`vol_state_z_natr_30`** (`volatility_v1.py:90-105`): `ta.natr(length=30)` is a trailing EWM-smoothed TR (past-only by construction); rolling-90 z-norm `[t-89,t]` with `min_periods=90`; `.shift(1)` on output. CLEAN.
- **`rev_halflife_50`** (`composed_v1.py:273-323`): the AR(1) `phi` estimator loops `for i in range(ar_window, n+1)` and reads `ret_1_values[i-ar_window : i]` — a strictly trailing 50-bar window ending at `i-1`; `np.corrcoef` over the lag-1 pairs is backward-looking; `≥5`-obs guard and `std < 1e-12` guard prevent NaN/degenerate fits; half-life capped at 50; rolling-90 z-norm; `.shift(1)` on output. The autocorr/half-life estimator is backward-looking as required. CLEAN.
- **`rev_vol_gate_signed`** (`composed_v1.py:328-415`): pure pointwise product `rev_extension_z_3 × g(vol_state_z_natr_30)`; both inputs are already `.shift(1)`'d by their compute functions, so NO additional shift is needed and none is double-applied. The soft gate is a deterministic piecewise-linear function of a single bar's already-lagged value. NaN-vol → conservative `g=1` pass-through (does not fabricate signal). CLEAN.

No feature scaling / fracdiff / PCA / imputation is fit across train+test (A3 grep returned zero matches in `features_v1/`). No obvious or subtle look-ahead in the new code.

### Check 13 (mini) — Anti-Pattern Static Scan: PASS

Scanned QE's src/ surface (`features_v1/{mean_reversion,volatility,composed}_v1.py`, `features_v1/__init__.py`, `features/__init__.py` registration, `run_iteration_085.py`, the `v1-085` dispatch block in `run_baseline_v1.py`) plus the foundation:

- **A1 (train/test boundary)**: all `train_end_ms = test_start_ms` matches carry the `− embargo_ms` subtraction. `walk_forward.py:113` reads `train_end_ms = test_start_ms - embargo_ms`. Fix intact and UNCHANGED by QE's commits. PASS.
- **A2 (labeling-window σ_t)**: zero forward-window matches; active path `use_atr_labeling=True`. PASS.
- **A3 (scaler fit on combined)**: zero `fit_transform`/`StandardScaler`/`.fit(` matches in new feature code (LightGBM scale-invariant; features are self-contained rolling z-scores). PASS.
- **A12 (DSR/PSR wrong-granularity)**: N/A at SPECIALIST EXPLORATION layer. **A13 (report write-before-read)**: N/A pre-backtest.

Foundation regression tests present: `tests/test_lookahead_embargo.py` contains all four mandated tests.

### Foundation Regression: PASS

`walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms`; QE's commits did NOT touch the foundation embargo line. Track isolation re-verified: `grep "from crypto_trade.features_v2|features_v3"` across `features_v1/` returns ONLY docstring/comment references, ZERO actual imports. The Hurst R/S math in `composed_v1.py` is a documented BYTE-FOR-BYTE COPY (not an import) from `features_v3/regime_v3.py`, preserving track isolation.

### Check 14 — Axis Family Validation: PASS

Brief Section 0.6 declares `per-cohort-specialization-UNI` (NEW symbol cohort + NEW mean-reversion feature-family, under the cycle-7 per-symbol regime-specialist mandate; standard 5-family rotation SUSPENDED). The src/ diff matches exactly:
- NEW feature modules: mean-reversion feature-family (rev_extension_z_3, vol_state_z_natr_30, +rev_halflife_50, +rev_vol_gate_signed).
- NEW symbol cohort: `V1_ITER085_UNIVERSE = ("UNIUSDT",)`; dispatch UNIUSDT-gated with cohort-isolation assertion.
- **Section 3.3 confirmed**: NO new risk primitive — inherited R3/R5 stack unchanged (R1/R2 OFF, Model A pattern); reversion/regime logic lives in the FEATURES, not a gate. Declared family == observed change.

Rotation status VALID: UNIUSDT ∉ {DOT, ETH, BTC, AAVE} (live BUNDLE-002), ∉ {LINK, LTC, ATOM, ICP, FIL, CRV} (failed mining set), ∉ `V1_EXCLUDED_SYMBOLS`. Prior 5 cohorts (/064 ETH, /065 BTC, /078 AAVE, /083 FIL, /084 CRV) all distinct from UNI.

**Global invariant verified (the recurring /083+/084 leak bug):** `V1_FEATURE_COLUMNS_PRUNED == 48` asserted at `__init__.py:213-214`, in the runner pre-flight (`run_iteration_085.py:128, 236`), and at dispatch; the 4 NEW features are LOCAL-only in `V1_ITER085_FEATURE_COLUMNS == 52` (asserted `__init__.py:242-245`). The global PRUNED set did NOT grow.

### Cadence + Axis Sanity: PASS

`phase5p5_gate.md` OVERALL=PASS (committed `fbf600f8`; resolves the prior Section-2 reproducibility BLOCK at `b67fdefa`). LM Master advisory present (`82f02eb6`) and every recommendation addressed in Section 3.5 — including the adversarial honest reconciliation that the directive's "GATE 1 + GATE 2 passed" framing is FALSE (QR concurs, Section 2.1). Methodology lock (50 inner seeds × 30 trials × depth-5 × leaves-31) held exactly. Hash gate `c8b8e0a87abb280a` is order-independent.

### Falsifier Presence: PASS

Brief carries explicit, falsifiable, pre-registered HARD falsifiers (Section 4.2), and the GATE-2-WEAK caveat is carried HONESTLY (abstract line 9, Section 0.5 verdict frame, Section 1 "the most important caveat in the iteration," Section 2.1 "the honest read," LM Master CRITICAL section):

- **F1** — trade-rate floor: < 50 OOS OR < 50 IS trades → falsified. Modal ~90-140 OOS pre-registered.
- **F2** — three HARD sub-branches: F2-PRIMARY (`rev_extension_z_3` rank ≥ 14/52 in > 50% months → NEGATIVE-INERT regardless of Sharpe); F2-COLLECTIVE (< 30 gain summed AND none < 40/52); F2-SUSPICION (`rev_vol_gate_signed` rank 1 while `rev_extension_z_3` rank ≥ 8 → anti-signal, the /084 fingerprint).
- **F3** — load-bearing: realized 52-col IS Sharpe must exceed the −0.243 probe by **≥ +0.25** (clear +0.00) or → NEGATIVE-PROBE-FLAT + "burden of proof has shifted to the architecture" diary finding.
- **F4** — TS-mom-beat: ML IS Sharpe must exceed trivial min-horizon −0.2485 AND clear +0.00, with mandatory per-direction WR-symmetry check.

No multi-seed CONFIRMATION proposed anywhere (user directive honored — confirmed absent from Sections 0.5, 2.5, 4, 8, Kill-Switch).

## Notes (non-blocking; for the Phase 7.5 full review)

1. **Cosmetic warmup-NaN documentation drift.** `rev_extension_z_3` warmup-NaN counts disagree across artifacts (brief "~53", module docstring "52→53", runner "54"). Documentation only — code is causal regardless; LightGBM handles NaN warmup via `use_missing=True`. Reconcile in Phase 7.4.
2. **Computed-twice redundancy (benign).** `rev_extension_z_3` + `vol_state_z_natr_30` are computed once by their own groups and again inside `add_composed_v1_085_features` (`composed_v1.py:448-454`). Deterministic + identical → parquet correct (Phase 5.5 confirmed all 52 cols, 0 missing). Defensive, harmless.
3. **Attribution entanglement (acknowledged in brief).** 4 NEW columns on a NEW symbol at once means a NEGATIVE verdict can't cleanly isolate which feature bound — but the directive sanctions the 4-feature stack as one experiment, and F2 per-feature importance keeps the verdict interpretable for the /086 grind.

These notes do not gate the iteration. The pre-flight surface — look-ahead, anti-patterns, foundation regression, axis-family, global-invariant, track-isolation, falsifier completeness — is clean.

OVERALL=PASS
