# iter-v3/120 — Research Brief (CYCLE 6 CONFIRMATION — TWO-COMPONENT bundle, FIRST multi-mechanism bundle in v3 history)

**Branch**: `iteration-v3/120`
**EDA cross-reference SHAs**: `52444c9` (iter-v3/116 EDA — RULE-layer no_confirm), `7aa5cc5` (iter-v3/119 EDA — FEATURE-layer C6 `ret5d_signed_tbi`)
**Setup commit SHA**: TBD (this commit cycle — single commit per dispatch)
**Iteration type**: **CYCLE 6 CONFIRMATION** (mandatory after 10/10 EXPLORATIONs /110–/119)
**Bundle**: TWO-COMPONENT — /116 no_confirm exit primitive (RULE-layer PROMISING-MECHANICAL) + /119 C6 `ret5d_signed_tbi` (FEATURE-layer PROMISING-FEATURE-MECHANICAL)
**Precedent**: FIRST multi-mechanism CONFIRMATION bundle in v3 history. All prior CONFIRMATIONs (/018 BOOTSTRAP, /028, /039, /059) were single-axis decisions.

---

## Section 0 — Hand-chosen Parameters Provenance

Per `feedback_v3_brief_parameter_provenance.md`: every hand-chosen parameter must name its EXPLORATION source iteration + the committed analysis table + an auditable IS-only temporal fence.

**Component A (RULE-layer no_confirm) — three hand-chosen scalars inherited from /116 EXPLORATION:**

| Parameter | Value | Source iteration | EDA table | Provenance |
|---|---:|---|---|---|
| `no_confirm_trigger_atr` | **0.50** | /116 | `analysis/iteration_v3-116/T7_early_exit_grid.csv` row "(0.50, 4)" | DECLARED hand-chosen at /116 brief Section 0. Grid `[0.25, 0.50, 0.75, 1.00]` swept IS-only. `0.50` is round-number midpoint, NOT per-symbol optimum (per-symbol optima `BCH 0.50, LDO 1.00, TRX 0.50` would have re-opened closed /073 per-symbol-asymmetry axis). Chosen as the only cell with positive IS Sharpe lift on all 3 symbols in the entire 16-cell grid (`BCH +0.1253, LDO +0.0068, TRX +0.0415`). NOT swept at /120 — CONFIRMATION inherits unchanged. |
| `no_confirm_k_candles` | **4** | /116 | `analysis/iteration_v3-116/T7_early_exit_grid.csv` row "(0.50, 4)" | DECLARED hand-chosen at /116 brief Section 0. Grid `[2, 3, 4, 5]` swept IS-only. `4` is roughly the median holding time of the static triple-barrier book (~32 hours at 8h interval) — the first-third of the 21-candle timeout, a parsimonious "fast-confirm or cut" window. NOT swept at /120. |
| `enable_no_confirm_exit` | **True** | /120 (this iteration) | n/a | Re-enables the /116 primitive (currently False in main following /117 mechanical REVERT at SHA `45fbd57`). This is the SINGLE substantive runner-code change Component A introduces vs the /119 head state. |

**Component B (FEATURE-layer C6) — three hand-chosen scalars inherited from /119 EXPLORATION:**

| Parameter | Value | Source iteration | EDA table | Provenance |
|---|---:|---|---|---|
| `ret_5d` lookback (for C6's `ret_5d` value primitive) | **15 8h candles** (~5 days) | /119 | `analysis/iteration_v3-119/T1_candidate_catalog.csv` row "C6_ret5d_signed_tbi" | DECLARED hand-chosen at /119 brief Section 0. Matches the /025 PROMISING-strong precedent's `ret_5d` value primitive (in `regime_momentum_signed_5d`). Standard cross-cycle horizon; NOT swept. |
| `taker_buy_imbalance_20` window (for C6's regime classifier) | **20 8h candles** (~6.7 days) | /119 | `analysis/iteration_v3-119/T1_candidate_catalog.csv` | DECLARED hand-chosen at /119 brief Section 0. Matches the V3 canonical microstructure window (also the /015 dead-path `tbr_zscore_30` family lookback range). NOT swept. |
| Sign convention | **+1 if tbi > 0; −1 if tbi < 0; NaN at exact 0** | /119 | inherent | Inherent to `sign(x)`. NaN-at-zero by design preserves discrete ±1 contract; zero-imbalance is sign-undefined. |

**Component A+B integration — no NEW hand-chosen parameters.** /120 is purely a multi-seed re-evaluation of two pre-evaluated EXPLORATION primitives in the same bundle. The bundle introduces ZERO new tuned-or-hand-chosen scalars beyond what /116 and /119 already declared.

**Auditable temporal fence**:
- /116 EDA SHA `52444c9` — every script asserts `close_time < OOS_CUTOFF_MS = 1742774400000`.
- /119 EDA SHA `7aa5cc5` — every script asserts `close_time < OOS_CUTOFF_MS = 1742774400000`.
- Per `feedback_v3_axis_selection_quant_discipline.md`, CONFIRMATION may rely on EXPLORATION EDAs; NO new EDA is mandated at /120. The cross-reference to the source EDAs above is the QR's audit trail.

---

## Section 0.5 — Iteration Type Declaration

- **TYPE**: **CYCLE 6 CONFIRMATION** (mandatory)
- **Cycle 6 cadence**: COMPLETE — 10/10 EXPLORATIONs at /110–/119 + 1 CONFIRMATION at /120 per `feedback_v3_strict_10_to_1_cadence.md` and `feedback_v3_cadence_discipline.md`.
- **Run mode**: default CONFIRMATION (NO `--exploration` flag → ENSEMBLE_SIZE = CONFIRMATION_ENSEMBLE_SIZE = 10).
- **Optuna budget**: `--n-trials 35` per (symbol × walk-forward month). Total trials = 35 × 3 sym × 10 seeds = **1050 trials** — same envelope as /059 canonical.
- **Wall-clock target**: ~3.6h (per /058, /059 baselines; HARD CAP **6h** per `feedback_v3_cadence_discipline.md`).
- **Runner invocation**: `uv run python run_baseline_v3.py --n-trials 35 --clean-oof` (no `--exploration`, no `--seeds` — `--seeds` is deprecated since /059 per `feedback_v3_outer_seed_cap_2_v3.md` evolution; unified 10-seed lineage is internal).
- **Anchor (canonical baseline)**: `v0.v3-059` (BASELINE_V3.md tag) — IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791** (10-seed CONFIRMATION). This is the BOTH-must-improve target per `feedback_v3_strict_both_is_oos_baseline.md`.
- **Component-alone reference anchors (for Falsifier 1 stacking-linearity)**: /116 single-seed EXPLORATION IS +0.6246 / OOS +1.1089; /119 single-seed EXPLORATION IS +0.8492 / OOS +0.8420. These are EXPLORATION-mode 3-seed numbers — under multi-seed unified-10-seed compression they are expected to compress materially (the /060 → /059 compression direction was a 5.0× monthly-Sharpe reduction on /060 OOS = 0.1403 vs /059 OOS = 0.5791; the /116/119 component-alone multi-seed numbers do not exist on disk, but Falsifier 1 anchors against the single-seed-mode EXPLORATION reference per the /119 diary §7.2 stated semantic).

**Cycle 6 EXPLORATION precedents (10/10 — per `feedback_v3_iter018_confirmation_baseline_validation.md` mandate)**:

| Slot | Iter | Date | Axis | Verdict | Bundle contribution |
|---|---|---|---|---|---|
| 1 | /110 | 2026-05-19 | Universe / symbol selection (CRV/AAVE/GRT/ADA) | UNRESOLVED (label-confound) | none |
| 2 | /111 | 2026-05-19 | Universe / symbol selection (clean re-test) | NEGATIVE clean | none |
| 3 | /112 | 2026-05-19 | Pooled-vs-per-symbol architecture | NEGATIVE | none |
| 4 | /113 | 2026-05-19 | Multi-frequency features on 8h | NEGATIVE | none |
| 5 | /114 | 2026-05-19 | Risk management (LDO kill-switch) | NEGATIVE (Check 1 + Check 8 FAIL) | none |
| 6 | /115 | 2026-05-19 | Labeling architecture (coherent horizon-exit) | NEGATIVE | none |
| 7 | **/116** | 2026-05-20 | Exit-layer / trade-construction (no_confirm) | **PROMISING-MECHANICAL** (RULE form) | **Component A** |
| 8 | /117 | 2026-05-20 | Candle frequency (24h-multi-offset) | NEGATIVE catastrophic | none |
| 9 | /118 | 2026-05-20 | NEW engineered-feature lineage (vol-regime composed) | NEGATIVE catastrophic | none |
| 10 | **/119** | 2026-05-20 | NEW engineered-feature lineage (microstructure-regime composed) | **PROMISING-FEATURE-MECHANICAL** (FEATURE form) | **Component B** |
| **CONF** | **/120** | 2026-05-20 | **Multi-mechanism /116+/119 bundle CONFIRMATION** | **TBD (this iteration)** | **A + B LOCKED** |

**Cycle 6 outcome**: 2 PROMISING mechanical primitives (RULE-form at /116, FEATURE-form at /119) + 8 NEGATIVE/UNRESOLVED + 0 new edge ingredients across 10 EXPLORATIONs.

---

## Section 1 — Testable Hypothesis (ONE sentence)

> The two-component bundle (/116 `enable_no_confirm_exit=True` with `trigger_atr=0.50` / `k_candles=4` + /119 C6 `ret5d_signed_tbi` at index 14 of the 15-feature `V3_FEATURE_COLUMNS_TOP_N`) jointly carries strictly-accretive lift on the /059 canonical baseline that survives multi-seed validation — producing IS monthly Sharpe ≥ **+1.0894** AND OOS monthly Sharpe ≥ **+0.5791** (BOTH-must-improve per `feedback_v3_strict_both_is_oos_baseline.md`), while clearing all three pre-committed binding falsifiers (stacking-linearity, TRX-concentration, sister-redistribution stability) and the Critic Rec 2 regime-cost IS floor (≥ +0.59) and the Critic Rec 3 per-symbol cascade-attribution falsifier (broad-based positive Δ vs /059 on ≥ 2 of 3 symbols).

---

## Section 2 — IS-Only Numerical Evidence (CROSS-REFERENCE to /116 + /119 EDAs)

Per `feedback_v3_axis_selection_quant_discipline.md`: CONFIRMATIONs may rely on EXPLORATION EDAs. NO new EDA is mandated at /120. This section cross-references the source EDA tables for each component.

### Section 2.1 — Component A source EDA (/116 SHA `52444c9`)

**EDA directory**: `analysis/iteration_v3-116/` — 10 result tables across 3 structural hypotheses (Axis A regime-conditioned barrier NO-GO at shuffle placebo; Axis B scaled-entry NO-GO 0/81 cells; Axis C early-exit chosen on residual-uncertainty criterion). Auditable temporal fence: every script asserts `close_time < OOS_CUTOFF_MS = 1742774400000`.

**Key tables (load-bearing for Component A)**:

| Table | Headline finding | Bundle relevance |
|---|---|---|
| `T7_early_exit_grid.csv` (16 cells) | `(trigger=0.50, K=4)` is the only cell with positive IS Sharpe lift on all 3 symbols: BCH +0.1253, LDO +0.0068, TRX +0.0415 | Justifies the hand-chosen `(0.50, 4)` parameters |
| `T8_cuts_losers.csv` (48 cells × 3 sym) | g2 mechanism gate FAILED 48/48: the rule cuts modestly-below-average WINNERS held-to-barrier (BCH +3.75%, LDO +2.90%, TRX +3.26%), NOT losers | EDA's static-direction counterfactual mis-frames the production mechanism (see /116 diary §2.3) |
| `T4_go_nogo_verdict.csv` row C | Axis C NO-GO on formal gates; chosen on residual-uncertainty criterion (only axis with any positive IS lift) | Documents the QR's bolder-than-dispatch pivot at /116 |

**Production-confirmed mechanism (/116 diary §2.2)**: the slot-freeing cascade — at OOS, the no_confirm exit frees the symbol slot ~9 candles earlier than SL/timeout, allowing subsequent LightGBM signals to enter. 11 new OOS entries at +3.67% mean PnL traceable bar-by-bar (October 2025 attribution: TRX 2025-10-12 + BCH 2025-10-28 documented in /116 engineering report).

**ALL 3 symbols positive OOS Δ vs /060 at single-seed EXPLORATION** (`/116 diary §2.2.1`): BCH +31.55, LDO +12.00, TRX +16.04. Broad-based distribution distinguishes /116 from /114 frozen-baseline artifact.

### Section 2.2 — Component B source EDA (/119 SHA `7aa5cc5`)

**EDA directory**: `analysis/iteration_v3-119/` — 8 result tables across a 4-category screen of NEW engineered features on STRUCTURALLY DIFFERENT primitives from /118's vol-regime branch (Cat-i volume, Cat-ii vwap-volatility, Cat-iii tail/higher-moment, Cat-iv microstructure). Auditable temporal fence: every script asserts `close_time < OOS_CUTOFF_MS = 1742774400000`.

**Key tables (load-bearing for Component B)**:

| Table | Headline finding | Bundle relevance |
|---|---|---|
| `T6_go_nogo_verdict.csv` | C6_ret5d_signed_tbi GO verdict (winner across 6 candidates); cleared NEW SSC-RISK pre-Falsifier at max-single-symbol/POOLED ratio 1.48× (under 2× threshold) | Justifies C6 as the /119 axis selection |
| `T7_multivariate_lift_screen.csv` | C6 produced POOLED multivariate AUC lift +0.0083 (best of 6 candidates); BCH +0.0057 / LDO +0.0123 / TRX +0.0053 (all 3 positive) | EDA verdict: PRODUCTION-RELEVANT POOLED lift, broad-based |
| `T9_ssc_risk_gate.csv` | C6 ssc_ratio 1.48× — UNDER the 2× SSC-RISK threshold (vs C5 2.21×, C4 2.12×) | Pre-Falsifier PASSED (single-symbol-carrier risk mitigated) |
| `T2_linear_redundancy_pre_falsifier.csv` row C6 | C6 pooled R² = 0.5099 — PASS-CARVEOUT (Category-2 composed feature inherits algebraic-sister IC by construction; per `feedback_v3_engineered_feature_pivot.md` carve-out, the strict 0.50 / 0.70 IC gate is replaced by importance ≥ 30 threshold) | Documents the carve-out invocation |

**Production-confirmed mechanism (/119 diary §5)**: feature-MECHANICAL loss-surface reorganization via algebraic-sister cannibalization.
- `regime_momentum_signed_5d` (C6's IC=−0.7229 algebraic sister sharing the `ret_5d` value primitive) lost **65.3%** of importance at single-seed (506.67 → 175.67).
- Combined "ret_5d × regime-sign" sister-family NET DROPS **35.1%** (506.67 → 328.67); C6's own allocation only 2.6% of total split-budget (153 / 5847) — mechanically insufficient as direct edge.
- 178 "saved" splits redistribute to 4 rank-rising anchor features: `max_dd_window_50` (rank 5→1), `ret_kurt_50` (7→3), `hurst_100` (11→8), `ret_skew_50` (12→9).
- Anchor-rank preservation Spearman ρ = **0.7714** on the 14 anchor features — NOT chaotic shuffle.

**ALL 3 symbols positive IS Δ vs /060 at single-seed EXPLORATION** (`/119 diary §3.3`): BCH +4.57, LDO +18.75, TRX +37.63. Broad-based per-symbol cascade — anti-/118 signature.

### Section 2.3 — Per-component classification cross-walk

| Component | Source | Layer | Subtype | Memory file | Non-compoundable-as-signal invariant |
|---|---|---|---|---|---|
| A — no_confirm | /116 | RULE | PROMISING-MECHANICAL | `feedback_promising_mechanical_subtype.md` | YES — slot-freeing book composition, not new edge signal |
| B — C6 ret5d_signed_tbi | /119 | FEATURE | PROMISING-FEATURE-MECHANICAL | `feedback_v3_promising_feature_mechanical.md` (NEW at /119) | YES — split-budget redistribution catalyst, not direct edge contribution |

**Cross-layer orthogonality basis (per /119 diary §6.3)**: the two mechanisms operate at structurally distinct layers (RULE-layer trade-roster composition vs FEATURE-layer loss-surface redistribution). They CAN in principle coexist as separate strictly-accretive component decisions in a single CONFIRMATION bundle. Stacking-linearity is NOT guaranteed and is the subject of Falsifier 1.

### Section 2.4 — /059 canonical baseline anchor values (byte-exact from BASELINE_V3.md)

| Metric | /059 value | Source |
|---|---:|---|
| IS monthly Sharpe | **+1.0894** | `reports-v3/iteration_v3-059/comparison.csv:2` |
| OOS monthly Sharpe | **+0.5791** | `reports-v3/iteration_v3-059/comparison.csv:2` |
| IS daily Sharpe | +2.7092 | `reports-v3/iteration_v3-059/comparison.csv:3` |
| OOS daily Sharpe | +1.4359 | `reports-v3/iteration_v3-059/comparison.csv:3` |
| OOS/IS monthly Sharpe ratio | 0.5316 | `reports-v3/iteration_v3-059/comparison.csv:2` |
| IS trades | 171 | `reports-v3/iteration_v3-059/comparison.csv:7` |
| OOS trades | 94 | `reports-v3/iteration_v3-059/comparison.csv:7` |
| OOS MaxDD | 34.53% | `reports-v3/iteration_v3-059/comparison.csv:5` |
| PBO mean | 0.1278 | `reports-v3/iteration_v3-059/dsr.json` |
| frac_positive_paths | 0.6444 | `reports-v3/iteration_v3-059/dsr.json` |
| CPCV path Sharpe Q75 | 0.8378 | `reports-v3/iteration_v3-059/dsr.json` |
| DSR_relative_legacy | 0.1134 | `reports-v3/iteration_v3-059/dsr.json` |
| PSR | 1.0 | `reports-v3/iteration_v3-059/dsr.json` |
| BCH IS %_of_total_pnl | 95.76% | `reports-v3/iteration_v3-059/in_sample/per_symbol.csv` |
| BCH OOS weighted_pnl | +24.75 | `reports-v3/iteration_v3-059/comparison.csv` |
| LDO OOS weighted_pnl | -6.18 | `reports-v3/iteration_v3-059/comparison.csv` |
| TRX OOS weighted_pnl | +4.16 | `reports-v3/iteration_v3-059/comparison.csv` |

### Section 2.5 — Component-alone single-seed EXPLORATION reference values

| Iteration | Mode | IS Sharpe | OOS Sharpe | OOS Trades | OOS MaxDD | n_trials | seeds |
|---|---|---:|---:|---:|---:|---:|---:|
| /116 EXPLORATION | 3-seed | +0.6246 | +1.1089 | 107 | 21.88% | 35 | 3 |
| /119 EXPLORATION | 3-seed | +0.8492 | +0.8420 | 103 | 32.82% | 35 | 3 |
| /060 EXPLORATION (anchor) | 3-seed | +0.8325 | +0.1403 | (anchor) | (anchor) | 35 | 3 |
| **/059 CONFIRMATION (canonical)** | **10-seed** | **+1.0894** | **+0.5791** | **94** | **34.53%** | **35** | **10** |

**Important compression context**: the 3-seed EXPLORATION numbers compress materially under 10-seed unified-ensemble CONFIRMATION. /060 vs /059 comparison illustrates: 3-seed /060 OOS +0.1403 → 10-seed /059 OOS +0.5791 (the same underlying axis under 10-seed compression). The direction of compression for /116/119 is NOT pre-determinable; Falsifier 1 is calibrated against the EXPLORATION-mode reference per the /119 diary §7.2 stated semantic (multi-seed component-alone numbers do not exist on disk).

---

## Section 3 — Proposed Changes (Bundle Composition vs /059 Canonical)

The /120 setup-commit takes /119 head state (V3_FEATURE_COLUMNS_TOP_N = 15 features with `ret5d_signed_tbi` at index 14; `compute_ret5d_signed_tbi` in `engineered_v3.py:834-888`; GROUP_REGISTRY microstructure_v3 BEFORE engineered_v3) and flips `enable_no_confirm_exit` False → True to re-enable Component A (currently REVERTED at /117 SHA `45fbd57` and persisting through /118/119 head).

### Sub-fix 1 — Component A: re-enable no_confirm exit primitive

File: `run_baseline_v3.py:2037` — flip `enable_no_confirm_exit=False` → `True` in BacktestConfig builder. Carry over `no_confirm_trigger_atr=0.50` + `no_confirm_k_candles=4` from existing /117–/119-head defaults (unchanged values; just the enable flag).

```python
# Before (/119 head state — REVERTED from /116 per /117 mechanical revert SHA `45fbd57`)
enable_no_confirm_exit=False,
no_confirm_trigger_atr=0.50,
no_confirm_k_candles=4,

# After (/120 CONFIRMATION — re-applies /116 RULE-layer primitive)
enable_no_confirm_exit=True,
no_confirm_trigger_atr=0.50,
no_confirm_k_candles=4,
```

The triple-barrier label estimand (`labeling.py`) is UNCHANGED. The static `2.0/1.0` ATR barrier geometry is UNCHANGED. The /116 primitive is a pure execution-layer overlay on top of unchanged barriers — `grep no_confirm labeling.py` returns zero matches (verified at /116 Critic Check 1).

### Sub-fix 2 — Component B: KEEP /119 C6 `ret5d_signed_tbi` at index 14 of V3_FEATURE_COLUMNS_TOP_N

File: `src/crypto_trade/features_v3/__init__.py:178-221` — UNCHANGED from /119 head state.

```python
V3_FEATURE_COLUMNS_TOP_N: tuple[str, ...] = (
    # ... 14 anchor features (BASELINE_V3 /059 spec)
    "ret5d_signed_tbi",  # 15th — engineered [iter-v3/119: order-flow-regime × momentum]
)
```

C6's implementation (`engineered_v3.py:834-888` `compute_ret5d_signed_tbi`) is past-only by construction:
- `ret_5d = log_close − log_close.shift(15)` (past-only by `shift(15)`)
- `taker_buy_imbalance_20 = tbr.shift(1).rolling(20).mean()` (past-only by `shift(1)` + 20-bar rolling)
- Zero-imbalance edge case: NaN by design (`sign(0)` undefined → NaN propagates)

GROUP_REGISTRY ordering (`features_v3/__init__.py:78-89`) places `microstructure_v3` BEFORE `engineered_v3` — critical dependency-satisfaction (so `taker_buy_imbalance_20` exists when `compute_ret5d_signed_tbi` runs). UNCHANGED from /119.

Per the Code-Defect-Retention policy from /118 closeout: `compute_ema_signed_volregime` STAYS in `engineered_v3.py` as code-museum (preserves implementation in case the lineage is ever re-opened under a different protocol); the column is absent from `V3_FEATURE_COLUMNS_TOP_N`. UNCHANGED.

### Sub-fix 3 — Runner setup housekeeping

File: `run_baseline_v3.py`:
- Line 131: `ITERATION_LABEL = "v3-119"` → `"v3-120"`.
- Line 2032 et al: MODEL_SPECS prefix `"v3-119-..."` → `"v3-120-..."`.
- Line 1145, 1150–1169: pre-flight accretion guard messages updated from "REVERTED" semantics to "RE-ENABLED" for `enable_no_confirm_exit`; the assertion at line 2959 must INVERT (was `is False`, becomes `is True`).
- Line 2953, 2964–2975: pre-flight assertion block — flip the `enable_no_confirm_exit is False` assertion to `is True`; adjust the surrounding `# iter-v3/117: REVERT` comment to `# iter-v3/120: RE-ENABLE from /116 CONFIRMATION bundle`.
- Feature-count guard at lines 432–442 (`n != 15` already in place from /119) — UNCHANGED.
- ABSENT-ban for `ema_signed_volregime` at lines 593–599 — UNCHANGED (carried from /119).

### Sub-fix 4 — Bundle state pre-flight assertions (NEW at /120)

Add a single new pre-flight verification block to confirm BOTH components are active:

```python
# iter-v3/120 pre-flight bundle-state verification
assert _pf_cfg.enable_no_confirm_exit is True, (
    "PREFLIGHT FAIL: enable_no_confirm_exit must be True for iter-v3/120 "
    "TWO-COMPONENT bundle (Component A)."
)
assert _pf_cfg.no_confirm_trigger_atr == 0.50, "PREFLIGHT FAIL: trigger_atr must be 0.50"
assert _pf_cfg.no_confirm_k_candles == 4, "PREFLIGHT FAIL: k_candles must be 4"
assert "ret5d_signed_tbi" in V3_FEATURE_COLUMNS_TOP_N, (
    "PREFLIGHT FAIL: ret5d_signed_tbi must be in V3_FEATURE_COLUMNS_TOP_N for "
    "iter-v3/120 TWO-COMPONENT bundle (Component B)."
)
assert len(V3_FEATURE_COLUMNS_TOP_N) == 15, (
    "PREFLIGHT FAIL: V3_FEATURE_COLUMNS_TOP_N must be 15 features for iter-v3/120 "
    "(14 anchor + ret5d_signed_tbi)."
)
print(
    "  iter-v3/120 pre-flight: enable_no_confirm_exit=True (Component A re-enabled), "
    "ret5d_signed_tbi PRESENT at V3_FEATURE_COLUMNS_TOP_N[14] (Component B preserved); "
    "bundle state VERIFIED  PASS"
)
```

### Sub-fix 5 — CONFIRMATION-mode flag (no `--exploration`)

The runner invocation MUST omit `--exploration` so `ENSEMBLE_SIZE = CONFIRMATION_ENSEMBLE_SIZE = 10` (per the runner default at line 96; the assertion at line 394 enforces this). `--seeds` is also omitted (deprecated since /059 per `feedback_v3_outer_seed_cap_2_v3.md` evolution — unified 10-seed lineage internal).

```bash
uv run python run_baseline_v3.py --n-trials 35 --clean-oof
```

Per BASELINE_V3.md "Code Configuration": this invocation produces 1050 total Optuna trials (35 × 3 sym × 10 seeds) — same envelope as /059.

### Section 3.5 — Code-change manifest

**NO new feature implementation.** No new function added. No new test added. Only:

1. **Runner config flag flip** — `enable_no_confirm_exit` False → True at `run_baseline_v3.py:2037`.
2. **Pre-flight assertion inversion** — `enable_no_confirm_exit is False` → `is True` at `run_baseline_v3.py:2959–2975`.
3. **Pre-flight accretion-guard expected values** — update the 3-tuple at `run_baseline_v3.py:1150–1152` to expect `(True, 0.50, 4)` instead of `(False, 0.50, 4)`; update the message block at lines 1161–1169 from "REVERTED" semantics to "RE-ENABLED".
4. **NEW bundle-state pre-flight block** — single 12-line assertion block per Sub-fix 4 above.
5. **ITERATION_LABEL + MODEL_SPECS prefixes** — `"v3-119"` → `"v3-120"`; standard housekeeping.
6. **Brief commit** — this file at `briefs-v3/iteration_v3-120/research_brief.md`.

**Knobs UNCHANGED vs /119 head state** (and therefore vs /059 canonical except for Sub-fixes 1–4):
- V3_MODELS = BCHUSDT, LDOUSDT, TRXUSDT
- V3_FEATURE_COLUMNS_TOP_N (15) — preserved from /119 (14 anchor + ret5d_signed_tbi at index 14)
- ATR multipliers — (atr_tp=2.0, atr_sl=1.0); V3_ATR_MULTIPLIERS_PER_SYMBOL = {} empty
- 7-primitive RiskV2 stack — vol scaling, ADX 20.0, Hurst regime, zscore 2.0, low-vol filter, hit-rate (DISABLED), BTC trend kill (15.0%); regime gate, per-symbol cap, per-symbol drawdown brake all DISABLED
- Triple-barrier labeling — 21-candle (10080-min) timeout
- ENSEMBLE_SIZE = 10 (unified 10-seed lineage `(191664963, …, 1952249162)`)
- CPCV n_paths = 45, embargo = 27, REQUIRED_GAP = 66
- Walk-forward POST-FIX at `e149e9d` (carry-forward from /058+)
- Optuna `n_jobs=1`, `colsample_bytree` Optuna-tuned (NOT hardcoded 1.0)
- Sacred constants UNCHANGED: `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24`

---

## Section 4 — Pre-registered Falsifiers (BINDING — non-negotiable)

These three falsifiers are the carry-forward from the /119 closeout Critic FINAL (`bb654ab`) and the /116 closeout Critic Recs 2+3. They are pre-registered in numerical form and cannot be renegotiated post-hoc.

### Falsifier 1 — Stacking-linearity (BINDING)

> At /120 multi-seed (10-seed unified ensemble), if the /116+C6 bundle OOS monthly Sharpe is LOWER than max(/116-only multi-seed OOS Sharpe, C6-only multi-seed OOS Sharpe) − 0.10, the bundle is NEGATIVE-no-stacking and Component B (C6) is DROPPED for /120 MERGE.

**Numerical instantiation under EXPLORATION-mode reference (the only multi-seed-component-alone numbers that exist on disk are zero — the /116 and /119 EXPLORATIONS are 3-seed single-mode runs)**:

- /116 single-seed OOS = **+1.1089**; /119 single-seed OOS = **+0.8420**.
- max(/116-only, C6-only) − 0.10 reference value = max(1.1089, 0.8420) − 0.10 = **+1.0089** (using the LARGER single-seed reference).
- **F1 firing threshold (single-seed reference)**: bundle multi-seed OOS Sharpe < **+1.0089** → F1 FIRES → DROP Component B (C6); revert to /116-only.
- **Multi-seed compression caveat**: at 10-seed CONFIRMATION, single-seed numbers typically compress 50–80% (the /060 → /059 reference produced 0.1403 → 0.5791 — that direction is *expansion* with the multi-seed Pareto picking sharper than the single-seed at certain hyperparameter regions; the converse compression /065 single-seed +1.20 → /070 multi-seed Pareto +0.0 is also on record). Reading F1 literally against the single-seed +1.0089 reference is therefore **conservative-in-the-DROP-direction**: if the bundle multi-seed OOS lands well below this number but well above /059 +0.5791, the BOTH-must-improve gate may still PASS while F1 mechanically fires — in which case Component B is dropped and /116-only is re-evaluated against /059.
- **Sister condition (carry-forward from /119 diary §7.2)**: the bundle MUST beat the MAX (not the average) of the two component-alone numbers minus 0.10. If the bundle lands between the smaller and the larger of the two component-alone Sharpes minus 0.10, the smaller-OOS component is the one with no marginal contribution and would be the natural DROP candidate. Pre-registered fallback per /119 diary: revert to /116-only (the RULE-layer mechanism with bar-by-bar attributable mechanism documentation from cycle-6 diary).

### Falsifier 2 — TRX-concentration (BINDING)

> At /120 multi-seed, if TRX multi-seed mean OOS weighted PnL share > 50% of positive-symbol total → BLOCK C6 inclusion (keep /116 alone); 50–65% → concentration-watch flag (does NOT fire BLOCK); > 65% → full BLOCK. LDO multi-seed portfolio share worse than −25% → flag.

**Numerical instantiation**:

- TRX positive-PnL share at /119 single-seed = 33.89 / (33.89 + 31.22) = **52.05%** of positive-symbol total — exactly at the 50–65% concentration-watch band.
- **F2 firing thresholds**:
  - TRX positive-PnL share ∈ [0%, 50%]: PASS (Component B retained).
  - TRX positive-PnL share ∈ (50%, 65%]: **CONCENTRATION-WATCH FLAG** (does NOT mechanically fire BLOCK; flagged in diary; bundle re-evaluated under tighter scrutiny but advances to MERGE if Falsifiers 1+3 PASS and BOTH-must-improve gate PASSES).
  - TRX positive-PnL share > 65%: **F2 FULL BLOCK** → DROP Component B (C6); revert to /116-only.
- LDO portfolio share < −25% (i.e., LDO drag worse than 25 absolute % of total weighted PnL): **FLAG** (does NOT mechanically fire BLOCK).
- **Multi-seed expansion caveat**: at 10-seed CONFIRMATION, per-symbol concentrations may compress (multi-seed averaging dilutes single-symbol single-seed lottery shares). The 50/65% bands are calibrated against the single-seed reference and are conservative-in-the-RETAIN direction.

### Falsifier 3 — Sister-redistribution stability (BINDING)

> At /120 multi-seed, if `regime_momentum_signed_5d` importance falls by > 50% in multi-seed mean (vs the /060 anchor importance of 506.67) AND `ret5d_signed_tbi` (C6) importance fails to exceed 5% of portfolio total importance → "allocation cannibal without contribution" → BLOCK C6 inclusion.

**Numerical instantiation**:

- /060 anchor `regime_momentum_signed_5d` portfolio importance = **506.67** (from /119 diary §3.5 row 14).
- /060 anchor C6 importance = N/A (C6 did not exist at /060).
- /119 single-seed `regime_momentum_signed_5d` portfolio importance = **175.67** (drop of −65.3% — F3 fired at single-seed for the sister-fall leg alone, but C6 share at 2.6% did NOT exceed 5%, so the conjunctive F3 FAILED at single-seed by the "cannibal without contribution" definition).
- **F3 firing condition (conjunctive)**: BOTH of:
  - (a) `regime_momentum_signed_5d` multi-seed mean importance < 506.67 × 0.5 = **253.34** (i.e., > 50% drop) AND
  - (b) `ret5d_signed_tbi` multi-seed mean importance < 5% of multi-seed portfolio total importance (the /119 single-seed total was 5847.67; 5% = 292.4 — but the multi-seed total may differ; the gate is the RATIO not the absolute value).
- **F3 FIRES if BOTH (a) AND (b)** → DROP Component B (C6); revert to /116-only.
- **F3 PASSES if EITHER (a) does not hold OR (b) does not hold** (i.e., either the sister importance is preserved enough OR C6 contributes meaningfully).
- **Single-seed reference behavior**: at single-seed (a) held (sister dropped 65.3%); (b) held (C6 share 2.6% < 5%) — so a strict conjunctive F3 reading on single-seed numbers would have fired. The justification for not firing at /119 was that single-seed EXPLORATION-mode importance numbers are unreliable individually; F3 is calibrated at the /120 multi-seed level where the importance statistics are stable.

### Falsifier 4 — Critic Rec 2: regime-cost IS NEGATIVE floor (BINDING — relaxed from standard envelope)

Per /116 Critic Rec 2 (carried forward into /120 mandate): Component A (no_confirm) has a documented expected IS-cost from regime-adaptive truncation (the /116 IS spans 2022 bear + 2023 chop where the rule cuts trades that recover; the OOS is 2025–2026 uptrend where the slot-freeing cascade dominates). The standard /059 IS − 0.10 = +0.99 floor is INSUFFICIENT to accommodate this expected mechanism.

**QR's judgment (one of /116 Critic Rec 2's suggested floors)**: **IS Sharpe NEGATIVE floor = /059 IS − 0.30 = +0.79**.

- Rationale for choosing /059 IS − 0.30 (NOT the looser − 0.50 = +0.59 option): the /116 single-seed IS drop was −0.2079 vs the /060 EXPLORATION-mode anchor (+0.6246 vs +0.8325). Under multi-seed compression the IS drop may amplify but is unlikely to exceed −0.30 vs /059 if the rule's expected dual-channel signature (IS-cost in bear/chop, OOS-lift in uptrend) holds. − 0.50 would dilute the IS gate to where it tolerates a model that has lost contact with the IS signal entirely; − 0.30 retains enough IS discipline to refuse a model where the no_confirm channel has materially broken the IS Sharpe.
- Alternative IS NEGATIVE floor at /059 IS − 0.50 = +0.59 (the looser option) is REJECTED here. Rationale: /119 alone at single-seed produced IS +0.8492 (a −0.24 drop from /059), so /059 IS − 0.30 = +0.79 is achievable at the bundle if the C6 IS-component holds even partially.

**F4 firing condition**: bundle multi-seed IS monthly Sharpe < **+0.79** → IS leg NEGATIVE → NO-MERGE on the IS-floor leg.

If bundle IS Sharpe ∈ [+0.79, +1.0894) AND OOS gate PASSES (≥ +0.5791): the IS leg is "regime-cost-acceptable but below /059" — BASELINE_V3.md does NOT update (per `feedback_v3_strict_both_is_oos_baseline.md` BOTH-must-improve), but the bundle classification advances to PARTIAL-MERGE candidate with QR diary documenting the IS regime-cost decomposition.

### Falsifier 5 — Critic Rec 3: per-symbol cascade-attribution (BINDING)

Per /116 Critic Rec 3 (carried forward into /120 mandate): pre-register at the 10-seed multi-seed level that if per-symbol OOS `net_pnl_pct` Δ vs /059 is NOT broad-based positive across at least 2 of 3 symbols, the bundle is reclassified PROMISING-FALSIFIED-AT-CONFIRMATION.

**Numerical instantiation**:

- /059 per-symbol OOS `weighted_pnl`:
  - BCH: +24.75
  - LDO: −6.18
  - TRX: +4.16
- **F5 firing condition**: bundle multi-seed `weighted_pnl` Δ vs /059 is POSITIVE on < 2 of 3 symbols → bundle is reclassified PROMISING-FALSIFIED-AT-CONFIRMATION → NO-MERGE (regardless of headline IS/OOS Sharpe).
- Equivalent statement: ≥ 2 of {BCH multi-seed OOS > +24.75, LDO multi-seed OOS > −6.18, TRX multi-seed OOS > +4.16} must hold for F5 to PASS.
- Single-seed reference behavior (informational only): /119 single-seed Δ vs /059 was BCH OOS +6.47 (+24.75 → +31.22), LDO OOS −3.85 (−6.18 → −10.03), TRX OOS +29.73 (+4.16 → +33.89) — 2/3 positive (BCH, TRX); LDO regressed. F5 PASSED at /119 single-seed by 2/3 cascade.

### Aggregate falsifier summary

The bundle CONFIRMATION-MERGES with both components only if **ALL FIVE falsifiers PASS** at multi-seed:

| Falsifier | Condition | PASS direction |
|---|---|---|
| F1 stacking-linearity | bundle OOS ≥ max(/116-only, C6-only) − 0.10 = ≥ **+1.0089** (single-seed reference) | bundle OOS multi-seed ≥ +1.0089 (with multi-seed expansion/compression caveat per F1) |
| F2 TRX-concentration | TRX positive-PnL share ≤ 65% (PASS); ∈ (50%, 65%] is FLAG-only | TRX share ≤ 65% |
| F3 sister-redistribution | NOT BOTH (regime_momentum_signed_5d drop > 50% AND C6 share < 5%) | EITHER sister importance ≥ **253.34** OR C6 share ≥ 5% portfolio total |
| F4 IS regime-cost floor | bundle IS multi-seed ≥ **+0.79** (= /059 IS − 0.30) | IS ≥ +0.79 |
| F5 per-symbol cascade | ≥ 2 of 3 symbols positive Δ vs /059 (BCH > +24.75, LDO > −6.18, TRX > +4.16) | broad-based ≥ 2/3 |

**+ BOTH-must-improve gate** (per `feedback_v3_strict_both_is_oos_baseline.md`):
- IS multi-seed ≥ **+1.0894** AND OOS multi-seed ≥ **+0.5791** → BASELINE_V3.md updates.
- If IS < +1.0894 OR OOS < +0.5791 → BASELINE_V3.md DOES NOT update (regardless of falsifier status).

**+ v3 hard methodology gates** (per ITERATION_PLAN_8H_V3.md + BASELINE_V3.md):
- PBO < 0.40 (Gate 5)
- PSR > 0.95 (Gate 6)
- frac_positive_paths ≥ 0.55 (Gate 10-CPCV)
- DSR_relative (legacy) — INFORMATIONAL only at /120 per /059 closeout (threshold needs cycle 1 recalibration; not a binding gate at cycle 6 CONFIRMATION).

---

## Section 5 — Risk Mitigation

Standard `feedback_v3_risk_mitigation_design.md` framework. R1–R5:

**R1 — Cool-downs**: standard /059 post-trade 2-candle cooldown (engine state per-`(model, symbol)`); UNCHANGED. Component A (no_confirm) operates BEFORE the cooldown timer arms — the no_confirm exit triggers a normal trade close with its own subsequent cooldown, so cool-down semantics are preserved.

**R2 — Drawdown scaling**: enable_per_symbol_drawdown_brake=False (per /054 stateful-deadlock closure). UNCHANGED.

**R3 — OOD detection**: z-score OOD gate at threshold 2.0 (per iter-v3/011). UNCHANGED. C6 (`ret5d_signed_tbi`) is structurally bounded by `sign(tbi) × log_return_5d` — bounded in [−Δ_max, +Δ_max] where Δ_max is the IS-window max |5-day log-return|; ADF stationarity 100% at IS-end month per /119 EDA (BCH ADF=−7.753, LDO=−8.128, TRX=−10.295, all p=0.0). C6 does NOT trigger new OOD failure modes vs /059's 14-feature stack.

**R4 — Vol kill-switch**: BTC trend filter at 15.0% threshold (per cycle-1 closure). UNCHANGED.

**R5 — Concentration caps**: NO per-symbol PnL share caps (per iter-v3/020 PATH C closure — concentration is signal in 3-symbol universe, NOT lottery risk). Falsifier 2 (TRX-concentration) is the structural BLOCK gate that replaces a hard cap with a multi-seed threshold-conditional component-drop. UNCHANGED on R5 architecture; F2 layered on top as a CONFIRMATION-specific binding falsifier.

**Component-specific risk considerations**:

- **Component A (no_confirm)** introduces a NEW exit_reason category in the trade log. The trade roster at /120 will have a 4th exit type alongside `take_profit`, `stop_loss`, `timeout`. Risk: a no_confirm exit at small negative PnL (mean −0.84% IS / −0.80% OOS at /116 single-seed) creates an early-truncation channel that, in a sustained bear regime, could cumulate small negatives faster than the SL/timeout it preempts. Mitigation: the F4 IS NEGATIVE floor (+0.79) bounds the cumulative IS-channel cost; the F5 per-symbol cascade gate ensures the rule does not destroy IS performance on any 2 of 3 symbols.
- **Component B (C6 `ret5d_signed_tbi`)** introduces split-budget redistribution that elevates 4 anchor features (max_dd_window_50, ret_kurt_50, hurst_100, ret_skew_50). Risk: at multi-seed, the redistribution may produce model variance that the single-seed EXPLORATION did not surface. Mitigation: F3 (sister-redistribution stability) catches the "allocation cannibal without contribution" failure mode; ensemble averaging across 10 seeds dilutes single-seed lottery effects.

**Bundle interaction risk**: the two mechanisms operate at structurally distinct layers but are not fully orthogonal in practice — the no_confirm exit may interact with the new feature-importance distribution. Specifically: if C6 catalyzes models that produce more confident long-trend signals (via the elevated `max_dd_window_50` + `ret_kurt_50` regime-persistence weighting), then no_confirm at trigger=0.50/K=4 may fire on a different distribution of entries than at /116. Mitigation: F1 (stacking-linearity) is the empirical test for whether the bundle is super-additive, additive, or sub-additive at the OOS Sharpe level.

---

## Section 6 — Risk Management (Operational)

UNCHANGED from /059. Per BASELINE_V3.md "Code Configuration":
- 7-primitive RiskV2 gate stack
- Standard CPCV with n_paths=45, embargo=27, REQUIRED_GAP=66
- Walk-forward POST-FIX at `e149e9d` (carry-forward)
- OOF parquet guardrail `--clean-oof` flag active

No new RiskV2 primitive introduced at /120. No new R-layer code path. Component A is an exit-layer overlay on the backtest engine; Component B is a feature-list extension only.

---

## Section 7 — Pre-registered Failure Modes

Per `feedback_v3_promising_mechanical_subtype.md` + `feedback_v3_promising_feature_mechanical.md`, the bundle has the following pre-registered failure modes — each mapped to the responsive falsifier or gate:

**Mode A (modal — pre-registered as the MOST LIKELY outcome)**: bundle multi-seed at /120 produces IS Sharpe ∈ [+0.79, +1.0894] AND OOS Sharpe ∈ [+0.5791, +1.0]. ALL 5 falsifiers PASS. BOTH-must-improve gate PARTIAL FAIL (one of IS/OOS misses /059). Verdict: **CONFIRMATION-NO-MERGE — bundle valid but does not strictly beat /059**. BASELINE_V3.md UNCHANGED. Both components advance to cycle-7 as accepted strictly-accretive primitives; cycle-7 axis design must adapt.
- Probability estimate: **~50%** (multi-seed compression of the EXPLORATION single-seed gains is the modal expectation; /116 OOS +1.1089 single-seed compressing to ~+0.7 multi-seed is consistent with prior cycle compression direction; /119 OOS +0.8420 single-seed compressing to ~+0.5 multi-seed is consistent; stacking-linearity makes the bundle estimate hover around +0.6–0.8).

**Mode B (Falsifier 1 fires)**: bundle multi-seed OOS < max(/116-only, C6-only) − 0.10. The two mechanisms negatively interact (e.g., FEATURE-layer redistribution shifts the entry distribution into trades that no_confirm preferentially truncates, destroying the slot-freeing cascade's beneficial entries). Verdict: **DROP Component B (C6); revert to /116-only for /120 MERGE evaluation; re-evaluate /116-alone against /059 BOTH-must-improve gate**. If /116-only PASSES BOTH-must-improve → /120 MERGES with Component A only; BASELINE_V3.md updates with RULE-layer single-mechanism baseline. If /116-only also fails → cycle-6 closes NO-MERGE.
- Probability estimate: ~20%.

**Mode C (Falsifier 2 fires — TRX > 65%)**: TRX dominates the positive-symbol total beyond the 65% concentration ceiling. Indicates that the C6 + no_confirm combination is producing a single-symbol-carrier outcome rather than a broad-based effect. Verdict: **DROP Component B (C6); revert to /116-only**. Same downstream tree as Mode B.
- Probability estimate: ~10% (TRX has been a /119-single-seed concentration carrier at 52.05% — multi-seed compression may push it either direction).

**Mode D (Falsifier 3 fires — sister-redistribution + C6-no-contribution)**: at multi-seed, the C6 importance falls below 5% of total while `regime_momentum_signed_5d` falls > 50%. Indicates C6 is an unstable feature that cannibalizes sister allocation without holding its own weight in the multi-seed model. Verdict: **DROP Component B (C6); revert to /116-only**. Same downstream tree.
- Probability estimate: ~10%.

**Mode E (Falsifier 4 fires — IS regime-cost floor breach)**: bundle multi-seed IS < +0.79. The no_confirm rule's IS-channel cost (Component A) is more severe than the regime-cost ceiling tolerates. Verdict: **NO-MERGE on the IS leg** regardless of OOS performance. BASELINE_V3.md UNCHANGED.
- Probability estimate: ~5%.

**Mode F (Falsifier 5 fires — per-symbol cascade collapse)**: < 2 of 3 symbols positive Δ vs /059 on OOS `weighted_pnl`. Indicates the bundle is concentrating into a single-symbol carrier (e.g., TRX absorbing all positive Δ while BCH and LDO regress). Verdict: **PROMISING-FALSIFIED-AT-CONFIRMATION**; NO-MERGE.
- Probability estimate: ~5%.

**Mode G (modal SUCCESS — multi-seed beats /059 on BOTH legs)**: bundle multi-seed IS ≥ +1.0894 AND OOS ≥ +0.5791; ALL 5 falsifiers PASS. Verdict: **CONFIRMATION-MERGE**; BASELINE_V3.md updates to multi-mechanism baseline (FIRST in v3 history). Both components accepted as strictly-accretive primitives on /059.
- Probability estimate: ~10% (the BOTH-must-improve gate has been a chronic v3 obstacle — only /028 cleared it; multi-seed compression direction makes this harder, not easier).

**Mode H (catastrophic)**: bundle multi-seed both IS AND OOS materially below /059 + multiple falsifiers fire. Indicates BOTH components dissolve at multi-seed (similar to /013 → /018 BOOTSTRAP dissolution). Verdict: **NO-MERGE, cycle-6 closes NO-MERGE**. BASELINE_V3.md UNCHANGED. Cycle-7 must structurally reorient (no edge ingredients found in cycle 6).
- Probability estimate: <5%.

**Aggregate**: the modal expectation is Mode A (PARTIAL — bundle valid but does not beat /059 on BOTH legs). Mode G (full SUCCESS) probability is bounded by the BOTH-must-improve gate's historical difficulty. Mode H (catastrophic) is bounded by the validated EXPLORATION-mode positive lift on both components — neither component is starting from a NEGATIVE EXPLORATION outcome.

---

## Section 8 — LOCKED Acceptance Criteria (first-match-wins MERGE / NO-MERGE)

Acceptance gates are evaluated in the order below. First-match-wins; the first failed gate determines the verdict.

### 8.1 — Hard methodology gates (any FAIL → NO-MERGE on the methodology leg)

| Gate | Threshold | /059 reference | /120 PASS condition |
|---|---|---:|---|
| Gate 5 PBO | < 0.40 | 0.1278 | bundle PBO mean < 0.40 |
| Gate 6 PSR | > 0.95 | 1.0 | bundle PSR > 0.95 |
| Gate 10-CPCV | ≥ 0.55 frac_positive_paths | 0.6444 | bundle ≥ 0.55 |
| OOS trades floor | ≥ 130 aggregate | 94 | bundle ≥ 130 (informational at /059 below floor; informational here too — would NOT mechanically block MERGE since /059 was bootstrapped below the floor) |
| OOS/IS Sharpe ratio (Gate 3) | ≥ 0.5 | 0.5316 | bundle ratio ≥ 0.5 (BINDING per /018 BOOTSTRAP rule) |

### 8.2 — Pre-committed falsifiers (any FAIL → component-DROP or NO-MERGE per Falsifier-specific verdict tree)

| Falsifier | PASS condition (recap from Section 4) |
|---|---|
| F1 stacking-linearity | bundle multi-seed OOS ≥ max(+1.1089, +0.8420) − 0.10 = ≥ +1.0089 (single-seed reference; multi-seed expansion caveat applies) |
| F2 TRX-concentration | TRX multi-seed positive-PnL share ≤ 65% |
| F3 sister-redistribution stability | NOT BOTH (regime_momentum_signed_5d multi-seed importance < 253.34 AND C6 multi-seed importance < 5% of total) |
| F4 IS regime-cost floor | bundle multi-seed IS Sharpe ≥ +0.79 |
| F5 per-symbol cascade | ≥ 2 of 3 symbols multi-seed OOS weighted_pnl > /059 baseline (BCH > +24.75, LDO > −6.18, TRX > +4.16) |

### 8.3 — BOTH-must-improve BASELINE_V3.md update gate (per `feedback_v3_strict_both_is_oos_baseline.md`)

BASELINE_V3.md updates ONLY if:
- bundle multi-seed IS Sharpe **≥ +1.0894** AND
- bundle multi-seed OOS Sharpe **≥ +0.5791**.

If either fails, BASELINE_V3.md DOES NOT update — even if all hard methodology gates and all five falsifiers PASS.

### 8.4 — First-match-wins decision tree

```
1. If Gate 5/6/10-CPCV/Gate 3 FAIL → NO-MERGE (methodology floor breach).
2. If F4 (IS regime-cost floor) FIRES → NO-MERGE (IS leg breach).
3. If F1 (stacking-linearity) FIRES →
     DROP Component B; re-evaluate /116-only against the same gates.
       If /116-only PASSES all gates + BOTH-must-improve → MERGE (Component A only); BASELINE_V3.md updates.
       If /116-only PASSES gates but fails BOTH-must-improve → CONFIRMATION-NO-MERGE; BASELINE_V3.md UNCHANGED; Component A accepted but does not displace /059.
       If /116-only FAILS gates → cycle-6 closes NO-MERGE.
4. If F2 (TRX > 65%) or F3 (sister + cannibal) FIRES →
     DROP Component B; same downstream tree as branch 3.
5. If F5 (per-symbol cascade < 2/3) FIRES → PROMISING-FALSIFIED-AT-CONFIRMATION; NO-MERGE; BASELINE_V3.md UNCHANGED.
6. If ALL FALSIFIERS PASS:
   6a. If BOTH-must-improve PASSES (bundle IS ≥ +1.0894 AND OOS ≥ +0.5791) → CONFIRMATION-MERGE (both components); BASELINE_V3.md updates to multi-mechanism baseline.
   6b. If BOTH-must-improve PARTIAL (one leg holds, one misses) → CONFIRMATION-NO-MERGE (partial); BASELINE_V3.md UNCHANGED; both components accepted as strictly-accretive primitives for cycle-7 priorities.
   6c. If BOTH-must-improve FAILS on both legs but bundle is positive → CONFIRMATION-NO-MERGE; BASELINE_V3.md UNCHANGED.
```

### 8.5 — Critic Phase 7.5 review

Per ITERATION_PLAN_8H_V3.md, the Critic's 8 mandatory checks + OVERALL=MERGE/BLOCK adjudicates after Engineer's Phase 6 commit. The Critic's OVERALL verdict is FINAL — Section 8.4's decision tree is the QR's first-match-wins read of the Phase 7 results; the Critic may OVERRIDE on substantive grounds (per /116 UPGRADE-direction precedent or /114 DOWNGRADE-direction precedent).

---

## Section 9 — Library Stack + Reproducibility

UNCHANGED from /059 / /116 / /119:

- `lightgbm == 4.6.0`
- `optuna == 4.8.0`
- `numpy == 2.2.6`
- `pandas == 3.0.0`
- `scikit-learn == 1.8.0`
- `scipy == 1.17.0`
- `statsmodels == 0.14.6`
- `pyarrow == 23.0.1`
- `mlfinlab == 1.4` (primary)
- `pypbo`
- `fracdiff >= 0.10`

Run invocation: `uv run python run_baseline_v3.py --n-trials 35 --clean-oof`.

Determinism: ENSEMBLE_SEEDS pinned to the 10-tuple `(191664963, 1662057957, 1405681631, 942484272, 929893137, 33158374, 1465339467, 1273345680, 115579757, 1952249162)` per `feedback_explicit_feature_columns.md` + BASELINE_V3.md. `V3_FEATURE_COLUMNS_TOP_N` explicit-list-pass to `LightGbmStrategy` per `feedback_explicit_feature_columns.md`.

Reproducibility stamp (to be filled by Phase 6 Engineer):
- Setup commit SHA: TBD (this commit cycle)
- Phase 5.5 gate SHA: TBD
- Engineering report SHA: TBD
- Critic FINAL SHA: TBD
- Wall-clock: TBD (cap 6h)
- Hardware: 12th Gen Intel Core i9-12900HK / 58 GiB RAM / WSL2 Linux x86_64 / Linux 6.6.114.1

---

## Section 10 — QR Audit Trail (Phase 1-5)

Per `feedback_v3_axis_selection_quant_discipline.md` (the iter-v3/044 mandate): the QR must document the EDA-driven quantitative basis for every axis selection. For a CONFIRMATION inheriting two PROMISING EXPLORATIONs, the audit trail is the cross-reference to the source iteration QR audit trails + the bundle composition decision tree.

### 10.1 — How the CONFIRMATION composition was decided

The /120 composition is **NOT a QR choice** — it is **pre-committed by the /116 and /119 closeouts** (Critic FINAL `0fc18c2` on /116 + Critic FINAL `bb654ab` on /119). Both closeouts pre-committed /120 as a TWO-COMPONENT bundle with three pre-committed binding falsifiers. This brief carries those decisions verbatim.

**Decision chain**:

1. **/116 Phase 7.5 Critic FINAL (`0fc18c2`)** UPGRADE-overrode the mechanical first-match-wins NEGATIVE to PROMISING-MECHANICAL on three independent legs (regime-cost mechanism, broadly-distributed mechanistically-traceable OOS lift, mechanical book-composition diagnostic). The PROMISING-MECHANICAL classification per `feedback_promising_mechanical_subtype.md` makes Component A a strictly-accretive component decision (NOT a new edge ingredient) advancing to /120 CONFIRMATION at multi-seed unified ensemble validation, with a pre-registered cascade-attribution falsifier (= F5 in this brief).

2. **/119 Phase 7.5 Critic FINAL (`bb654ab`)** classified Component B as PROMISING-FEATURE-MECHANICAL (NEW sister-subtype to /116's PROMISING-MECHANICAL). The FEATURE-form analog inherits the non-compoundable-as-signal-source invariant from `feedback_promising_mechanical_subtype.md`. The Critic FINAL pre-committed three binding falsifiers for /120 (stacking-linearity, TRX-concentration, sister-redistribution stability — = F1+F2+F3 in this brief).

3. **/116 Critic Rec 2 (regime-cost IS-band)** is carried forward as F4 in this brief; the QR's judgment chose the middle option (/059 IS − 0.30 = +0.79) per Section 4 rationale.

4. **Cross-layer orthogonality justification** (per /119 diary §6.3) is the basis for bundling rather than running sequentially: the mechanisms operate at structurally distinct layers (RULE-layer slot-freeing vs FEATURE-layer split-budget redistribution), so they CAN coexist as separate strictly-accretive component decisions. The multi-seed budget is single-shot per cycle (one CONFIRMATION); running them sequentially would require a 2-cycle path (cycle-6 CONFIRMATION-A + cycle-7 CONFIRMATION-B), which is the alternative the /119 Critic FINAL considered and rejected.

5. **No QR-original axis selection at /120**. Per `feedback_v3_iter018_confirmation_baseline_validation.md`, CONFIRMATIONs are multi-seed re-evaluations of pre-evaluated EXPLORATION primitives — NOT bundle-assembly axes. This brief is structurally constrained to executing the pre-committed bundle composition with the pre-committed binding falsifiers.

### 10.2 — Provenance of every numerical value in Sections 1–9

- /059 anchor values (IS +1.0894, OOS +0.5791, etc.): byte-exact from BASELINE_V3.md "Headline Metrics" + `reports-v3/iteration_v3-059/comparison.csv` / `dsr.json`.
- /116 single-seed reference values (IS +0.6246, OOS +1.1089): byte-exact from `reports-v3/iteration_v3-116/comparison.csv:2` and /116 diary §2.1.
- /119 single-seed reference values (IS +0.8492, OOS +0.8420): byte-exact from `reports-v3/iteration_v3-119/comparison.csv:2` and /119 diary §3.1.
- /060 EXPLORATION-mode anchor (IS +0.8325, OOS +0.1403): byte-exact from `reports-v3/iteration_v3-060/comparison.csv` and /119 diary §3.1.
- Component-alone importance numbers (`regime_momentum_signed_5d` 506.67 → 175.67, C6 share 2.6%, anchor-rank Spearman ρ = 0.7714): byte-exact from /119 diary §3.5 + §5.1, sourced from `reports-v3/iteration_v3-119/in_sample/model_importance_last_month_portfolio.csv`.
- Per-symbol OOS attribution numbers (/119: BCH +31.22 / LDO −10.03 / TRX +33.89; /116: BCH +22.86 / LDO −13.08 / TRX +46.80): byte-exact from `reports-v3/iteration_v3-116/out_of_sample/per_symbol.csv` and `reports-v3/iteration_v3-119/out_of_sample/per_symbol.csv` respectively (also reproduced in the source diary entries).
- Falsifier threshold expressions: derived in Section 4 from the source diary §7.2 + Critic FINAL Recs (F1+F2+F3) and /116 Critic Recs 2+3 (F4+F5).

### 10.3 — What this brief does NOT contain

- **No new EDA tables**: per `feedback_v3_axis_selection_quant_discipline.md`, CONFIRMATIONs may rely on EXPLORATION EDAs. Section 2 cross-references /116 EDA SHA `52444c9` and /119 EDA SHA `7aa5cc5`.
- **No new hand-chosen parameters**: per Section 0 above, every scalar parameter is inherited from /116 or /119 EXPLORATIONs.
- **No new code module or function**: per Section 3.5 above, ONLY runner-config flips + ITERATION_LABEL bump + bundle-state pre-flight assertions.
- **No new feature**: C6 implementation in `engineered_v3.py:834-888` is UNCHANGED from /119.

### 10.4 — Out-of-scope items deferred to cycle-7

Per the cycle-6 closeout decision tree (from /119 diary §10.3):

| /120 outcome | BASELINE_V3.md decision | Cycle-7 priority |
|---|---|---|
| Mode G (bundle MERGES, both components, BOTH-must-improve PASSES) | UPDATE — multi-mechanism baseline | Cycle-7 reorients on the NEW multi-mechanism baseline; structural axes per /119 diary §8.2 |
| Mode B/C/D + /116-only PASSES (RULE-layer only MERGES) | UPDATE — /116-only baseline | Same as Mode G but with the FEATURE-MECHANICAL precedent informing future feature-engineering axes |
| Mode A (PARTIAL, no MERGE) | UNCHANGED at /059 | Cycle-7 must adapt: BOTH-must-improve has been the binding constraint; cycle-7 axes must move STRUCTURALLY rather than by adding more strictly-accretive mechanical primitives |
| Mode E/F/H (NO-MERGE) | UNCHANGED at /059 | Cycle-7 must STRUCTURALLY reorient (per /119 diary §8.2 candidate axes: cross-asset/external feeds, longer-cadence labels, NEW model architecture) |

The /120 brief makes NO cycle-7 axis commitments — those are the next cycle QR's mandate per the cycle-6 closure tree.

---

## END OF BRIEF

**Phase 5.5 gate expectation**: this brief contains all 10 mandatory sections (0, 0.5, 1, 2, 3, 3.5, 4, 5, 6, 7, 8, 9, 10) + the CONFIRMATION-specific augmentations (Section 0.5 cycle-6 cadence precedents; Section 4 5 pre-committed binding falsifiers; Section 8 first-match-wins decision tree). Engineer's Phase 5.5 verification should confirm: (a) bundle-state pre-flight assertions specified at Section 3 Sub-fix 4; (b) all 5 falsifier numerical thresholds explicit at Section 4; (c) /059 anchor byte-exact values at Section 2.4; (d) cross-reference SHAs for /116 EDA `52444c9` and /119 EDA `7aa5cc5` cited at Section 0 + Section 2.1+2.2; (e) runner invocation `uv run python run_baseline_v3.py --n-trials 35 --clean-oof` (no `--exploration`, no `--seeds`) at Section 0.5 + Section 3 Sub-fix 5.

**Sacred constants verified UNCHANGED**: `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24`.

**THE PRIME DIRECTIVE**: produce brief + run /120 CONFIRMATION backtest. NO EDA-kill. 6h hard cap on backtest.
