# iter-v3/084 — Research Brief — REFERENCE / METHODOLOGY iteration: PER_CELL_GAP fix + clean /059-config anchor re-run

**Iteration**: iter-v3/084 — cycle-3 slot #3 of 10. **TYPE: REFERENCE / METHODOLOGY** —
NOT a bold research axis. Scope is fixed (two declared things, below); no axis research.
**Purpose 1**: the `PER_CELL_GAP` methodology fix (/083 Critic FINAL `1116124` Rec #2).
**Purpose 2**: the clean /059-config 3-symbol anchor re-run on current data — restores the
canonical 3-symbol BCH/LDO/TRX configuration (REVERTS the /083 NEGATIVE FILUSDT expansion)
and produces the cycle-3 **EXPLORATION-MODE-REFERENCE** (the /060 → /077 precedent).
**Anchor**: BASELINE_V3.md `v0.v3-059` (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe
**+0.5791**), re-validated at the iter-v3/081 CONFIRMATION (IS +1.0894 / OOS +0.5999).
**Branch**: `iteration-v3/084` (off the /083 closeout merge `f50975d`).

---

## Section 0 — Data Split Declaration

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are **UNCHANGED** — sacred
constants, immutable. iter-v3/084 does not touch them and contains nothing that could.

- **IS window**: earliest available data per symbol → 2025-03-24. Each of the 3 per-symbol
  models (BCHUSDT, LDOUSDT, TRXUSDT) is walk-forward trained on a rolling 24-month window.
- **OOS window**: 2025-03-24 → present (~14 months).
- The walk-forward / CPCV backtest runs on the full continuous series; the reporting layer
  splits trade results at `OOS_CUTOFF_DATE` into `in_sample/` and `out_of_sample/`.
- **NO CHEATING**: this is a no-axis re-run of the canonical /059 configuration on
  freshly-fetched current data. `start_time` is never trimmed; no date range is
  cherry-picked; no parameter is tuned on OOS. The committed EDA
  `analysis/iteration_v3-084/canonical_config_and_anchor_staleness.py` reads ONLY
  source-code constants and prior-iteration artifacts — no OOS data, no model fit,
  no backtest. The QR sees /084's OOS for the first time in Phase 7.

## Section 0.5 — Iteration Type Declaration

**TYPE: REFERENCE / METHODOLOGY** (cycle-3 slot #3 of 10).

iter-v3/084 is neither a bold research axis nor a CONFIRMATION. It is the direct analogue
of cycle 1's iter-v3/077 — a fresh, no-axis run of the canonical configuration on current
data that establishes a clean EXPLORATION-MODE-REFERENCE, plus a single bundled methodology
fix. It carries the `feedback_v3` "revert the non-merged prior iteration" pattern (the /083
universe expansion was NEGATIVE/NO-MERGE — it is reverted exactly as /083 itself reverted
/082's funding family, and /079 reverted /078's ADA swap).

EXPLORATION mode: `run_baseline_v3.py --exploration --clean-oof --n-trials 35` →
`EXPLORATION_ENSEMBLE_SIZE = 3`, `ENSEMBLE_SEEDS` outer-42-lineage subset
`[191664963, 1662057957, 1405681631]`. **Wall-clock budget: ≤ 2h HARD CAP.** Estimate:
3-symbol universe, 35×3×3 = 315 Optuna trials — identical to /082's 3-symbol run, which
completed in **0.74h (44 min)**. iter-v3/084 estimate: **~0.74h**, well within the 2h cap.
This iteration does NOT run CONFIRMATION-spec — no `--seeds 2`, no `ENSEMBLE_SIZE` 5/10,
no bundle assembly.

## Section 1 — Hypothesis

iter-v3/084 makes one declared methodology change and one configuration revert:

1. **The `PER_CELL_GAP` methodology fix.** `PER_CELL_GAP = 43` in `run_baseline_v3.py:1497`
   is stale — it is the value `(42+1)` left over from the reverted iter-v3/068 42-candle
   timeout-widening, which was reverted to 21 candles at /069/070. With `timeout_candles =
   21` the per-cell single-symbol CSCV purge gap must be `(21+1) = 22`. Correcting `43→22`
   plus an `expected_gap` runtime guard is the SINGLE declared methodology change.

2. **The clean /059-config 3-symbol anchor re-run.** Restore the canonical /059
   configuration on current data: `V3_MODELS` reverts to 3 symbols (drop FILUSDT — /083 was
   NEGATIVE/NO-MERGE), `REQUIRED_GAP` reverts `88→66`, the 14-feature anchor stack (already
   in place since the /083 funding revert), the 11-knob config-accretion check reverts to
   /059-canonical 3-symbol.

**Hypothesis** (the falsifiable claim): the clean /059-config 3-symbol re-run on current
data **reproduces the /059 IS and OOS monthly Sharpe within ≈±0.10** — because /082 (the
same 3 incumbents on the same fresh data, FILUSDT absent) already produced IS monthly
Sharpe **+1.0776** (Δ −0.0118 vs /059's +1.0894), reproducing /059 within ~0.01 on the
gate-relevant metric. The `PER_CELL_GAP` fix changes the per-cell PBO number going forward
(43 over-purged; 22 is correct) but does NOT change the trade roster — PBO is a downstream
reporting artifact computed after the roster is fixed.

## Section 2 — IS-Only Numerical Evidence

iter-v3/084 is a REFERENCE iteration — it does NO new feature/label/symbol research, so
there is no new alpha-evidence table. The committed EDA
`analysis/iteration_v3-084/canonical_config_and_anchor_staleness.py` does two reference
jobs, both reading ONLY source-code constants and committed prior-iteration artifacts
(no OOS data, no model fit). Outputs: `config_audit_v059_canonical.csv`,
`anchor_staleness_incumbent_drift.csv`, `anchor_staleness_sharpe_framing.csv`.

### T1 — The /059-canonical 3-symbol config (the config-audit, Purpose 1)

| Knob | /083 value (4-sym) | /059-canonical (3-sym) — /084 RESTORES |
|---|---|---|
| `V3_MODELS` symbols | BCH, LDO, TRX, **FIL** | **BCH, LDO, TRX** (drop FIL) |
| `REQUIRED_GAP` | 88 = (21+1)×4 | **66 = (21+1)×3** |
| `V3_FEATURE_COLUMNS` count | 14 | 14 (already /059 anchor — no change) |
| `DEFAULT_ATR_MULTIPLIERS` | (2.0, 1.0) | (2.0, 1.0) — unchanged |
| `zscore_threshold` | 2.0 | 2.0 — unchanged |
| `adx_threshold` | 20.0 | 20.0 — unchanged |
| `vol_scale_floor_per_symbol` | {} | {} — unchanged |
| `block_long_for` / `block_short_for` | () / () | () / () — unchanged |
| `enable_per_symbol_drawdown_brake` | False | False — unchanged |

The 11-knob `_canonical_v059` config-accretion check: at /083 the first 2 rows
(`V3_MODELS symbols`, `REQUIRED_GAP`) carried the 4-symbol universe-expansion delta;
iter-v3/084 reverts ALL 11 rows to /059-canonical — the universe expansion is fully
unwound and the check guards 11/11 knobs against /059, restoring strict single-axis
discipline (here: zero axis — a pure baseline restore).

### T2 — The `PER_CELL_GAP` correction (the methodology fix, Purpose 1)

| | Value | Provenance |
|---|---|---|
| Stale runner value | `PER_CELL_GAP = 43` | `(42+1)` — iter-v3/068 timeout=42 leftover; timeout REVERTED to 21 at /069/070 |
| Correct value | `PER_CELL_GAP = 22` | `(timeout_candles+1) = (21+1)`; single-symbol cell — `n_symbols` does NOT enter |
| Test already correct | `PER_CELL_GAP = 22` | `tests/strategies/ml/test_per_cell_pbo_synthetic.py:38` — the runner is OUT OF SYNC with its own test |
| Direction of the error | over-purge | 43 removes MORE training data per per-cell test boundary than 22 → biases per-cell PBO **pessimistically** → did NOT invalidate /083 |

The per-cell CSCV is a **single-symbol** per-(symbol, month) cell — the purge gap is
`(timeout_candles+1)`, NOT `(timeout_candles+1)×n_symbols`. The `×n_symbols` factor applies
ONLY to the global pooled CPCV (`REQUIRED_GAP`), because the global CPCV interleaves all
symbols' candles into one sequence. The stale `43` confused the per-cell gap with the
old 42-candle global formula. The runner's own docstrings at `:1349` and `:1512` already
say "gap=22 within-cell" — the constant contradicts the docstring.

### T3 — The anchor-staleness tension (the question /084 resolves, Purpose 2)

The /083 closeout decomposition was framed in **net_pnl%** and found incumbent IS PnL
drifted ~70pp on current data. But the gate-relevant metric is **monthly Sharpe**, and
/082 — the same 3 incumbents on the same fresh data — reproduced /059's Sharpe within ~0.01:

| Framing | Number | Reading |
|---|---|---|
| net_pnl% (the /083 decomposition) | incumbent aggregate /082 = +42.34 vs /059 = +114.07 → Δ **−71.73 pp** (FIL absent) | "anchor drifted a lot" |
| monthly Sharpe (gate-relevant) | /082 IS monthly Sharpe +1.0776 vs /059 +1.0894 → Δ **−0.0118** | "anchor reproduces" |

`/082-vs-/083` incumbent net_pnl Δ = **+2.63 pp** (near-identical) — confirming FIL did
NOT perturb the incumbents (the /083 engineering report's "Optuna-landscape reshaping"
claim was mechanistically false; the Critic traced the runner and confirmed per-symbol
model isolation is total). The net_pnl%-vs-Sharpe tension is unresolved: net_pnl% says
"drifted ~70pp", Sharpe says "reproduces within 0.01". **iter-v3/084's clean run
definitively resolves it** — see Section 4.

## Section 3 — Proposed Changes

iter-v3/084 is a runner-configuration-only iteration: one methodology fix + a baseline
restore. No new code logic, no new feature/label/risk-gate, no model-architecture change.

### 3.1 The PER_CELL_GAP methodology fix (the SINGLE declared change)

In `run_baseline_v3.py`:

```python
# BEFORE (line 1497) — stale
PER_CELL_GAP = 43  # (timeout_candles + 1) within a single-symbol cell — iter-v3/068 timeout widen

# AFTER (iter-v3/084) — corrected to (timeout_candles + 1) = (21 + 1) = 22
PER_CELL_GAP = 22  # (timeout_candles + 1) = (21 + 1) within a SINGLE-symbol cell.
#                    iter-v3/084 FIX (/083 Critic FINAL `1116124` Rec #2): the runner
#                    held the stale (42+1)=43 left over from the iter-v3/068 42-candle
#                    timeout, which /069/070 REVERTED to 21. Single-symbol cell — the
#                    *n_symbols factor applies ONLY to the global pooled REQUIRED_GAP.
```

Add the `expected_gap` guard to the per-cell `combinatorial_purged_cv` call
(`run_baseline_v3.py:~1586-1592`) — currently called with NO `expected_gap`, so the
constant can silently drift again:

```python
# BEFORE
cell_splits = combinatorial_purged_cv(
    n_samples=n_candles_mat,
    n_splits=PER_CELL_N_SPLITS,
    n_test_splits=PER_CELL_K,
    gap=PER_CELL_GAP,
    embargo=0,
)

# AFTER — expected_gap self-assertion (same protection the global CPCV call already has)
cell_splits = combinatorial_purged_cv(
    n_samples=n_candles_mat,
    n_splits=PER_CELL_N_SPLITS,
    n_test_splits=PER_CELL_K,
    gap=PER_CELL_GAP,
    embargo=0,
    expected_gap=PER_CELL_GAP,
)
```

Fix the two stale runner string literals (cosmetic — the runtime assertion is correct,
but the /083 Phase 5.5 gate flagged them and they were not fixed before /083):

- `run_baseline_v3.py:2539` comment `# asserts REQUIRED_GAP == 66 (3-symbol universe,
  iter-v3/070)` — at /083 the comment said `== 66` but the run was 4-symbol `REQUIRED_GAP
  = 88`. At /084 the universe IS 3-symbol so `== 66` becomes correct again; update the
  iteration tag in the comment to `iter-v3/084`.
- `run_baseline_v3.py:2593` print `Gap: 88 (= (21+1)*3=66; ...)` — internally contradictory
  (`88` vs `(21+1)*3=66`). At /084 the universe is 3-symbol; correct it to read
  `Gap: 66 (= (21+1)*3; iter-v3/084 REVERT /083 FILUSDT expansion; 3-sym universe
  BCH+LDO+TRX; timeout UNCHANGED 10080 min)`.

### 3.2 The /059-config 3-symbol revert (baseline restore — NOT a new axis)

`V3_MODELS` reverts to the 3-symbol /059 universe (drop FILUSDT):

```python
# BEFORE (iter-v3/083 — universe EXPANSION, NEGATIVE/NO-MERGE)
V3_MODELS = (
    ("A (BCHUSDT)", "BCHUSDT"),
    ("C (LDOUSDT)", "LDOUSDT"),
    ("D (TRXUSDT)", "TRXUSDT"),
    ("F (FILUSDT)", "FILUSDT"),   # <- /083 axis, NEGATIVE
)

# AFTER (iter-v3/084 — REVERT to /059-canonical 3-symbol)
V3_MODELS = (
    ("A (BCHUSDT)", "BCHUSDT"),
    ("C (LDOUSDT)", "LDOUSDT"),
    ("D (TRXUSDT)", "TRXUSDT"),
)
```

`REQUIRED_GAP` reverts `88 → 66` in `src/crypto_trade/strategies/ml/validation_v3.py:62`:

```python
# BEFORE — iter-v3/083 4-symbol value
REQUIRED_GAP: int = (21 + 1) * 4  # 88

# AFTER — iter-v3/084 REVERT to /059-canonical 3-symbol
REQUIRED_GAP: int = (21 + 1) * 3  # 66
```

The 11-knob `_canonical_v059` config-accretion check (`run_baseline_v3.py:~904-922`):
revert the first 2 rows to /059-canonical 3-symbol — `V3_MODELS symbols` expected value
`("BCHUSDT", "LDOUSDT", "TRXUSDT")`, `REQUIRED_GAP` expected `66`. All 11 rows then equal
/059-canonical. The associated comment block and the PASS-print string update from the
/083 4-symbol narrative to the /084 baseline-restore narrative.

`V3_FEATURE_COLUMNS` is **already** the 14-feature /059 anchor stack — the /083 setup
reverted the /082 funding family 18→14. iter-v3/084 makes NO feature change.
`_verify_feature_columns` keeps asserting 14 + the closed-funding-name-absent guards;
only its iteration-tag comments update to `iter-v3/084`.

### 3.3 Runner / test housekeeping

- `ITERATION_LABEL` → `"v3-084"` (`run_baseline_v3.py:131`).
- `_verify_label_leakage_gap()` (`run_baseline_v3.py:~1047`) recomputes
  `(timeout_candles+1)*len(V3_MODELS) = (21+1)*3 = 66` from the 3-symbol `V3_MODELS` — it
  is already formula-driven; with `V3_MODELS` at 3 symbols and `REQUIRED_GAP = 66` the
  assertion passes. Only the docstring/comment iteration tag updates.
- `tests/strategies/ml/test_cpcv_embargo_assert.py`: `N_SYMBOLS` 4→3, `CORRECT_GAP`
  becomes `(21+1)*3 = 66`, `test_required_gap_matches_formula` asserts `REQUIRED_GAP ==
  66`. The stale-test comment updates to the /084 3-symbol narrative.
- `tests/strategies/ml/test_per_cell_pbo_synthetic.py`: ALREADY has `PER_CELL_GAP = 22`
  (line 38) — no change needed; the runner was out of sync with the test, and the fix
  brings the runner INTO sync. This test is the regression coverage for the fix.
- `tests/strategies/ml/test_v3_feature_count.py`: still asserts 14 features — no change;
  only its module docstring iteration tag may update to `iter-v3/084` for clarity.

### 3.4 No changes to labeling, features, risk gates, model architecture, seeds

ATR labeling `(2.0, 1.0)`, the 14-feature stack, the 7-primitive risk-gate stack,
`ENSEMBLE_SEEDS`, the Optuna search, the unified-ensemble architecture — ALL UNCHANGED
from /059. iter-v3/084 changes exactly: `PER_CELL_GAP` (the methodology fix), `V3_MODELS`
+ `REQUIRED_GAP` + the config-accretion check (the /059-config revert), and iteration-tag
strings. Nothing else.

## Section 4 — Expected OOS Impact

### 4.1 Pre-registered prediction

iter-v3/084 is a clean /059-config re-run, so the prediction is **reproduction of /059**:

| Metric | /059 anchor | iter-v3/084 prediction | Basis |
|---|---:|---|---|
| **IS monthly Sharpe** | +1.0894 | **+1.0894 ± 0.10** (band [+0.99, +1.19]) | /082 (3 incumbents, fresh data) produced +1.0776 — Δ −0.0118; /084 drops FIL and reverts 18→14 features, both moving back toward /059 |
| **OOS monthly Sharpe** | +0.5791 | **+0.5791 ± 0.10** (band [+0.48, +0.68]); a modest data-extent uplift toward [+0.60, +0.70] is plausible (the 2026-04/05 OOS months post-date the /059 fetch — the /077 finding showed OOS drifts up monotonically with calendar time) | /081 re-validation already showed OOS +0.5999 (Δ +0.021); /082's OOS +1.787 is the documented INERT-feature/3-seed-lottery artifact and is NOT a reproduction reference |
| **Incumbent IS net_pnl%** (aggregate) | +114.07 | **≈ +40 to +50** (band [+30, +60]) | /082 = +42.34, /083 = +44.97 — both ~70pp below /059; /084 expected to land in the same band (the net_pnl% "drift" is data-extent drift, real and expected) |
| IS / OOS trades | 171 / 94 | ~150–180 / ~85–105 | /082 3-sym: 176 / 89 |
| per-cell PBO | 0.1278 (at stale gap 43) | **changes — the gap fix is the cause** | 43 over-purged; 22 is correct → the per-cell PBO will move (likely modestly up — less-conservative purge); informational at EXPLORATION mode |

The two framings are predicted to **diverge by construction**: monthly Sharpe reproduces
/059 (band [+0.99, +1.19] IS); net_pnl% lands ~70pp below /059 (band [+30, +60] aggregate).
This is not a contradiction — monthly Sharpe is a risk-adjusted *per-month* ratio that is
robust to the data-extent-driven net_pnl% drift on a structurally low-edge symbol set
(TRX 29–34% WR, where small marginal feature shifts flip many trades and move net_pnl%
without moving the Sharpe ratio much).

### 4.2 Falsifier (LOCKED)

The hypothesis ("the clean /059-config 3-symbol re-run reproduces /059 within ≈±0.10") is
**rejected** if EITHER:

- **F1**: IS monthly Sharpe is OUTSIDE [+0.99, +1.19] (Δ vs /059 outside ±0.10).
- **F2**: OOS monthly Sharpe is OUTSIDE [+0.48, +0.68] (Δ vs /059 outside ±0.10).

If F1 or F2 fires, the /059 anchor does NOT reproduce on current data even on the
gate-relevant metric — the anchor is genuinely stale and /084's numbers become the
cycle-3 EXPLORATION-MODE-REFERENCE (see 4.3). If neither fires, the anchor reproduces and
/059 STAYS the validated cycle-3 anchor.

A secondary observational falsifier (informational, does NOT reject the hypothesis): if
the incumbent IS net_pnl% aggregate lands INSIDE [+90, +130] (i.e. it does NOT drift
~70pp), then the /083 "anchor drifted ~70pp" decomposition itself was wrong — that would
be a notable finding for the diary, but it does not bear on the Sharpe-framed hypothesis.

### 4.3 Re-anchor decision rule (LOCKED — for Phase 8)

This is the dispositive rule the iteration exists to apply:

- **IF** /084's IS monthly Sharpe lands within ±0.10 of /059 (inside [+0.99, +1.19])
  **AND** /084's OOS monthly Sharpe lands within ±0.10 of /059 (inside [+0.48, +0.68]):
  → **/059 STAYS the validated cycle-3 anchor.** The anchor is confirmed reproducible on
  current data on the gate-relevant metric. The ~70pp net_pnl% incumbent drift is recorded
  as a **secondary observation** (real, data-extent-driven, immaterial to gate decisions).
  Cycle-3 EXPLORATIONs /085-091 continue to anchor their Δ against /059's
  IS +1.0894 / OOS +0.5791. /084's own numbers are recorded as a current-code/current-data
  **reproduction confirmation** of /059, not a new reference.

- **IF** /084's IS OR OOS monthly Sharpe differs MATERIALLY from /059 (F1 or F2 fires):
  → **/084's IS/OOS monthly Sharpe numbers become the cycle-3 EXPLORATION-MODE-REFERENCE**
  (the exact /077-precedent: a fresh current-code run of the canonical config replacing a
  stale reference). Cycle-3 EXPLORATIONs /085-091 re-anchor their Δ against /084's numbers.
  The /092 CONFIRMATION continues to anchor against the canonical /059 CONFIRMATION
  baseline (a CONFIRMATION-mode number, separate from the EXPLORATION-mode reference, per
  BASELINE_V3.md's anchor-staleness note).

In BOTH branches: BASELINE_V3.md's canonical /059 CONFIRMATION baseline and tag
`v0.v3-059` are **UNCHANGED** — iter-v3/084 is an EXPLORATION-mode iteration and an
EXPLORATION cannot update the baseline. `OOS_CUTOFF_DATE` / `training_months` untouched.

### 4.4 OOS/IS ratio SUSPICIOUS gate (carried per `feedback_v3_oos_is_ratio_gate.md`)

For taxonomy completeness (iter-v3/084 is a REFERENCE iteration, not an axis — the
SUSPICIOUS gate is unlikely to be load-bearing, but is pre-registered): OOS/IS monthly
Sharpe ratio **> 3.0** → SUSPICIOUS. At the predicted IS +1.09 / OOS +0.58 the ratio is
~0.53 — far from the 3.0 gate. The OOS-DOMINANT sub-mode (IS Δ < 0 AND OOS Δ ≥ +0.20) is
also pre-registered: if /084 reproduces /059 on IS but OOS jumps ≥ +0.78 it would fire —
but that contradicts the reproduction hypothesis and would itself be a falsifier signal
(F2). A REFERENCE iteration that reproduces the anchor classifies as **REFERENCE-CONFIRMED
(NULL-style)** — see Section 8.

## Section 5 — Risk Mitigation

iter-v3/084 introduces NO new strategy, NO new feature, NO new risk primitive, NO new
symbol. The risk surface is **strictly a subset** of /059's — it reverts the /083 4th
symbol (removing FIL's exposure entirely) and corrects an over-conservative purge gap.
There is no incremental strategy risk to mitigate.

The 7-primitive risk-gate stack (BTC trend kill, vol scaling, ADX, Hurst regime, feature
z-score OOD, low-vol filter, hit-rate [disabled]) is carried verbatim from /059 with
IS-calibrated thresholds unchanged (`zscore_threshold=2.0`, `adx_threshold=20.0`,
`BTC_TREND_CONFIG.threshold_pct=15.0`). Simulated historical effect: identical to /059
(BASELINE_V3.md records the /059 gate behavior) — there is no delta to simulate because
the gate stack does not change.

The one methodology risk — that the `PER_CELL_GAP` fix could be a *leakage* hazard — is
explicitly addressed and **ruled out**: `43 → 22` REDUCES the purge gap. A reduced purge
gap removes LESS training data near each per-cell test boundary. Per López de Prado
(AFML Ch. 7), the purge gap exists to prevent label-overlap leakage; the per-cell label
horizon is `timeout_candles = 21` candles, so `(21+1) = 22` is the *minimum-correct* purge
gap. `22` is exactly the correct gap — it is NOT an under-purge (which would leak); `43`
was an over-purge (conservative, no leakage, but discards good training data). The fix
moves from over-conservative to correct, never to under-purge. The per-cell embargo stays
0 (the cell is single-symbol, single-month — no autocorrelated cross-cell leakage path).

## Section 6 — Risk Management Design

No risk-management design change. iter-v3/084 carries /059's design verbatim:

- **R1-class** (consecutive-SL cooldown): not in v3's stack — v3 uses the 7-gate stack.
- **Drawdown brake** (`enable_per_symbol_drawdown_brake`): `False` — /059 canonical
  (disabled per iter-v3/054); unchanged.
- **OOD detection** (feature z-score gate, `zscore_threshold=2.0`): unchanged from /059.
- **Concentration**: iter-v3/084 makes no concentration-control change. The BCH
  concentration fragility (BCH carried 95.76% IS / 108.86% OOS PnL at /059) is a KNOWN
  outstanding v3 problem — but it is NOT iter-v3/084's scope. /084 is a reference re-run;
  it neither fixes nor worsens concentration. The cycle-3 plan's Direction-2 (universe
  expansion) is the designated concentration lever; FILUSDT failed it at /083, and the
  /085-091 EXPLORATIONs will continue that line. /084's clean-anchor numbers make those
  future concentration EXPLORATIONs measurable (the purpose of the iteration).

The kill-switch design for iter-v3/084 itself: a 2h wall-clock HARD CAP (estimate 0.74h),
and the Section-4.2 falsifiers F1/F2. There is no mid-flight abandon condition beyond the
cap — a reference re-run either completes or it does not.

## Section 7 — Pre-Registered Failure-Mode Prediction

iter-v3/084 is a REFERENCE iteration; its "failure modes" are reproduction outcomes, not
axis-discovery outcomes. Pre-registered outcome distribution:

| Outcome | Pre-registered probability | Description |
|---|---:|---|
| **/059 reproduces — anchor CONFIRMED** | **≈ 65%** | IS and OOS monthly Sharpe both inside ±0.10 of /059. /082's IS Δ of −0.0118 is the strong prior. /059 stays the cycle-3 anchor; net_pnl% drift is a secondary note. |
| /059 reproduces on IS, OOS drifts up | ≈ 20% | IS inside band, OOS above +0.68 (the 2026-04/05 data-extent uplift, per the /077 finding). F2 fires → /084 becomes the EXPLORATION-MODE-REFERENCE. A *benign* re-anchor — the anchor moved because OOS data grew, not because the config is unstable. |
| /059 does NOT reproduce — IS materially off | ≈ 10% | IS outside [+0.99, +1.19]. F1 fires → /084 becomes the EXPLORATION-MODE-REFERENCE. Would mean even the gate-relevant metric drifted — a stronger staleness finding than the /083 net_pnl% decomposition implied. |
| 3-seed-lottery divergence (IS or OOS far off, suspicious ratio) | ≈ 5% | The /082-style INERT/lottery artifact — but /084 changes NO feature, so the Optuna search space is identical to /059's 14-feature surface; a large lottery swing is much less likely than at /082 (which added 4 columns). |

**Most-likely outcome: /059 reproduces, anchor CONFIRMED (≈65%).** The honest reckoning:
the /083 closeout framed the staleness in net_pnl% and the magnitude (~70pp) is genuinely
large — but /082's monthly-Sharpe Δ of −0.0118 is direct evidence that the gate-relevant
metric is robust to that net_pnl% drift. The iteration is designed so that BOTH the
≈65% (anchor confirmed) and the ≈30% (anchor moved → re-anchor) branches are clean,
pre-registered outcomes with a LOCKED decision rule (Section 4.3) — there is no outcome
that requires post-hoc rationalization.

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (classification taxonomy)

iter-v3/084 is a **REFERENCE / METHODOLOGY** iteration — it is neither a bold research
axis (no axis to classify PROMISING/NEGATIVE/INERT) nor a CONFIRMATION (no bundle to
validate, no baseline update). It cannot MERGE in the baseline-update sense and it does
not advance anything to the /092 CONFIRMATION.

**Pre-registered closeout classification: REFERENCE-CONFIRMED (NULL-style closeout).**
The standard EXPLORATION taxonomy (SUSPICIOUS → NEGATIVE → PROMISING → INERT → NULL) is
not the operative frame; the operative outcome is the Section-4.3 re-anchor decision rule.
The closeout is one of two pre-registered states:

### 8.1 REFERENCE-CONFIRMED — anchor reproduces (the ≈65% + ≈20%-IS-stable outcomes)

IS monthly Sharpe inside [+0.99, +1.19] AND OOS monthly Sharpe inside [+0.48, +0.68].
→ Diary outcome: **REFERENCE-CONFIRMED.** /059 STAYS the validated cycle-3 anchor.
/084's numbers recorded as a reproduction confirmation. The `PER_CELL_GAP` methodology
fix is recorded as a permanent strictly-accretive correction (per
`feedback_v3_promising_mechanical_subtype.md` — a methodology improvement, non-compoundable
as an edge ingredient). The ~70pp net_pnl% incumbent drift recorded as a secondary
observation. BASELINE_V3.md UNCHANGED. EXPLORATION closeout marker tag `v0.v3-084`
(explicitly NOT a baseline update — the /082/083 pattern).

### 8.2 REFERENCE-REANCHOR — anchor moved (F1 or F2 fires)

IS monthly Sharpe outside [+0.99, +1.19] OR OOS monthly Sharpe outside [+0.48, +0.68].
→ Diary outcome: **REFERENCE-REANCHOR.** /084's IS/OOS monthly Sharpe become the cycle-3
EXPLORATION-MODE-REFERENCE for /085-091 (the /077 precedent). The /092 CONFIRMATION still
anchors against the canonical /059 CONFIRMATION baseline. The `PER_CELL_GAP` fix recorded
as above. BASELINE_V3.md's canonical /059 number and tag `v0.v3-059` UNCHANGED (an
EXPLORATION-mode-reference correction is not a baseline change). Tag `v0.v3-084` as a
closeout marker.

In NEITHER state does iter-v3/084 update BASELINE_V3.md or advance an edge ingredient.
The methodology hard gates (DSR/PBO/PSR) are EXPLORATION-mode artifacts here per
`feedback_v3_dsr_mode_artifact.md` — informational only; the per-cell PBO will change
because the gap fix changes the per-cell purge, and that change is the *expected* effect
of the fix, not a result signal.

## Section 9 — Library Stack Declaration

No new dependencies. iter-v3/084 is a runner-configuration-only iteration — a constant
correction (`PER_CELL_GAP`), a guard addition (`expected_gap`), and a `V3_MODELS` /
`REQUIRED_GAP` revert. Pinned stack carried verbatim from /059/081/082/083:
`lightgbm 4.6.0`, `optuna 4.8.0`, `numpy 2.2.6`, `pandas 3.0.0`, `scikit-learn 1.8.0`,
`scipy 1.17.0`, `statsmodels 0.14.6`, `pyarrow 23.0.1`. The committed EDA
(`analysis/iteration_v3-084/canonical_config_and_anchor_staleness.py`) uses only the
Python standard library (`csv`, `pathlib`) — it reads source-code constants and
prior-iteration artifacts; it does not load data, fit a model, or import any third-party
library.

## Section 10 — QR Audit Trail (axis selection)

**Axis assignment.** iter-v3/084 has no research axis. Its scope was assigned by the
iter-v3/083 closeout: diary-v3/iteration_v3-083.md Section 6 (the QR anchor-staleness
recommendation), Section 9 (the MANDATORY `PER_CELL_GAP` fix), and Section 12 Rec #2 + #4,
all carried into `briefs-v3/cycle3_plan.md` Section 7's "TWO MANDATES recorded at the /083
closeout (carried into ... the iter-v3/084 setup)". iter-v3/084 executes exactly those two
mandates and nothing else. This is NOT an orchestrator ad-hoc axis pick — it is the
discharge of two pre-committed, Critic-mandated /084-setup obligations.

**Why this is the correct iteration.** Two prior precedents make iter-v3/084 a disciplined,
non-discretionary slot:

1. **The /060 → /077 precedent.** Cycle 1's /060 EXPLORATION-MODE-REFERENCE went stale; the
   /077 closeout ran a no-axis re-run of the canonical /060 config on current data and
   established a fresh current-code EXPLORATION-MODE-REFERENCE (IS +0.8236 / OOS +0.2078)
   for cycle-2 EXPLORATIONs /078+. iter-v3/084 is the exact cycle-3 analogue.
2. **The "revert the non-merged prior iteration" pattern.** /083's FILUSDT universe
   expansion was NEGATIVE/NO-MERGE. iter-v3/084 reverts it — the same established pattern
   as /083 reverting /082's funding family, /079 reverting /078's ADA swap, /077 reverting
   /076's `range_efficiency_50`.

**The `PER_CELL_GAP` defect provenance.** The /083 Critic Check-2 review (Critic FINAL
`1116124`) traced `PER_CELL_GAP = 43` to the iter-v3/068 42-candle timeout-widening
(`43 = 42+1`), which /069/070 reverted to 21 candles. The runner constant was never
updated; `tests/strategies/ml/test_per_cell_pbo_synthetic.py:38` already carried the
correct `22`, so the runner had been out of sync with its own regression test. The Critic
established the fix is conservative (over-purge → pessimistic PBO bias → no /083
invalidation) and recorded it as a MANDATORY /084-setup fix.

**EDA committed**: `analysis/iteration_v3-084/canonical_config_and_anchor_staleness.py`
(SHA recorded at the setup commit) — the config audit (Purpose 1) and the
anchor-staleness Sharpe-vs-net_pnl table (Purpose 2). It reads ONLY source constants and
prior-iteration artifacts; it touches no OOS data — `feedback_no_cheating.md` satisfied.

## Section 11 — Closeout SHA Block (backfilled at setup)

- **Brief SHA**: (this commit; backfilled by the immediately-following setup commit)
- **Setup commit SHA**: (the setup commit — `run_baseline_v3.py` ITERATION_LABEL `v3-084`
  + the PER_CELL_GAP fix + expected_gap guard + stale literals; `validation_v3.py`
  REQUIRED_GAP→66; V3_MODELS→3 symbols; config-accretion check→/059-canonical 3-symbol;
  test updates)
- **EDA SHA**: (the EDA commit — `analysis/iteration_v3-084/`)
- **Phase 5.5 gate SHA**: TBD (Engineer)
- **Engineering report SHA**: TBD (Engineer, Phase 6)
- **Critic FINAL SHA**: TBD (Phase 7.5)
- **Diary SHA**: TBD (Phase 8)
- **Tag**: `v0.v3-084` (EXPLORATION/REFERENCE closeout marker — NOT a baseline update;
  BASELINE_V3.md stays at `v0.v3-059`)
- **Reports**: `reports-v3/iteration_v3-084/`
