# Phase 7.5 Critic Review — iter-v3/120 — PRELIMINARY

## Iteration Type (from Brief Section 0.5)
TYPE: CYCLE 6 CONFIRMATION (first multi-mechanism bundle in v3 history; 10/10 EXPLORATIONs /110–/119 completed; /116 Component A + /119 Component B bundled at 10-seed unified ensemble).

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

No /120-specific feature or backtest code introduced. Bundle is the union of:
- Component A computation at `src/crypto_trade/backtest.py:251-287` + arm-time/threshold derivation at lines 654-667. `no_confirm_arm_time = open_time + k_candles * interval_ms` and `no_confirm_threshold_price = entry_price * (1.0 ± trigger_atr * sl_pct)` — both knowable strictly at trade entry. Audited PASS at /116 Critic Round 1.
- Component B computation at `src/crypto_trade/features_v3/engineered_v3.py:834-888`. `ret_5d = log_close - log_close.shift(15)` and `taker_buy_imbalance_20.shift(1).rolling(20).mean()` — both past-only by construction. Audited PASS at /119 Critic Round 1.

The /120 setup commit added ZERO feature/backtest code (only runner-state flag flips + assertions per Sub-fix 1-5). PASS.

### Check 2 — Embargo Width: PASS

REQUIRED_GAP = 66 = (timeout_candles=21 + 1) × n_symbols=3. CPCV embargo=27 ≈ 1% of 2742-candle IS window. CPCV n_paths=45 unchanged from /059. Walk-forward POST-FIX at `e149e9d` carry-forward. PASS.

### Check 3 — Multiple-Testing Correction: SPLIT VERDICT

- **DSR = 0.0** — Raw threshold FAIL, but structural artifact inherited from /059 (`feedback_v3_dsr_mode_artifact.md`). Not BLOCK-triggering on its own per brief Section 8.1.
- **PBO = 0.0957 < 0.40**: PASS.
- **PSR = 1.0 > 0.95**: PASS.
- **frac_positive_paths = 0.6444 ≥ 0.55**: PASS (29 of 45 CPCV paths positive).
- n_trials = 1050 (35 × 3 × 10) matches /059 exactly. n_eff = 19.

Mechanically PASS on PBO + PSR + frac_positive_paths.

### Check 4 — IC Correlation Between Feature Families: PASS

15×15 IC matrix. High pairwise ICs pre-registered under Category-2 algebraic-sister carve-out (`feedback_v3_engineered_feature_pivot.md`):
- `regime_momentum_signed_5d` × `vwap_dev_20`: +0.7642 (pre-registered, /025 inheritance)
- `ret5d_signed_tbi` × `regime_momentum_signed_5d`: -0.7229 (pre-registered, algebraic sister via shared `ret_5d`)
- `ret5d_signed_tbi` × `vwap_dev_20`: -0.5668

Max non-carve-out pair: `regime_momentum_signed_5d` × `sym_vs_btc_ret_7d` = +0.6189 (< 0.70). Carve-out replacement gate (importance ≥ 30): C6 per-symbol importance BCH 36.4, LDO 34.7, TRX 57.5 — all ≥ 30. PASS.

### Check 5 — ADF Stationarity: PASS

C6 stationary at IS-end month across all 3 symbols (BCH ADF=-7.753, LDO=-8.128, TRX=-10.295; all p=0.0). /059 14-feature stack carries forward unchanged. PASS.

### Check 6 — Pareto Dominance: PASS (via frac_positive_paths gate)

Per `feedback_v3_unified_10seed_baseline.md`, Gate 10 per-seed Pareto replaced at /059+ by `cpcv_frac_positive_paths_gate_pass`. Observed 0.6444 PASS. CPCV path Sharpe distribution: min=-1.318, Q25=-0.243, Q50=+0.335, Q75=+0.838, max=+1.880. PASS.

### Check 7 — Reproducibility: PASS

Setup SHA `294ac0e` stamped. Engineering report SHA `55f2246`. Brief SHA `26d99f2`. Gate SHA `1145c30`. ENSEMBLE_SEEDS pinned to 10-tuple. `feature_columns=_feature_columns` explicit (no auto-discovery). Pre-flight bundle-state assertions fire 4 distinct guards. Wall-clock 3.14h within 6h cap; aligns with /059 CONFIRMATION 3.60h baseline. PASS.

### Check 8 — Hypothesis-Implementation Alignment: PASS

Bundle state implemented per Brief Section 1: `enable_no_confirm_exit=True`, `no_confirm_trigger_atr=0.50`, `no_confirm_k_candles=4`, `ret5d_signed_tbi` at index 14 of V3_FEATURE_COLUMNS_TOP_N (len==15). Pre-flight bundle-state assertions verify joint state. No scope creep. 7-gate RiskV2 stack, training_months=24, OOS_CUTOFF_DATE=2025-03-24, ENSEMBLE_SIZE=10, n_trials=35 all unchanged from /059. PASS.

## Falsifier Status Summary (binding, pre-committed at brief Section 4)

| F# | Status | Observed | Threshold |
|---|---|---|---|
| F1 stacking-linearity | PASS | OOS +1.6946 | ≥ +1.0089 |
| F2 TRX-concentration | PASS | TRX 18.79% of positive total | ≤ 65% (50% flag) |
| F3 sister-redistribution | **FIRES** | regime_momentum 171.9 < 253.34 AND C6 share 2.72% < 5% (BOTH legs hold) | NOT BOTH |
| F4 IS regime-cost floor | **FAILS** | IS +0.7293 < +0.79 | ≥ +0.79 |
| F5 per-symbol cascade | PASS | 3/3 symbols positive Δ vs /059 | ≥ 2/3 |

**BOTH-must-improve gate**: IS +0.7293 < /059 IS +1.0894 → BASELINE_V3.md does NOT update per `feedback_v3_strict_both_is_oos_baseline.md`.

**Mechanical verdict per brief Section 8.4 first-match-wins**: CONFIRMATION-NO-MERGE — F3 FIRES mandates DROP Component B and revert to /116-only; F4 FAILS mandates NO-MERGE on IS leg; BOTH-must-improve gate independently confirms BASELINE_V3.md does not update.

## The Central Adjudication

The bundle achieves an **all-time v3 OOS record** monthly Sharpe (+1.6946 vs prior record /059 at +0.5791; Δ +1.12). F1, F2, F5 PASS broadly: 3/3 symbols positive OOS Δ (BCH +24.87, LDO +9.07, TRX +7.99 weighted_pnl), TRX concentration 18.79% (well below 50% flag), super-additive vs single-seed reference. Hard methodology gates (PBO, PSR, frac_positive_paths) all PASS.

Yet F3 and F4 fire as pre-committed:
- **F3 fire numerical proof**: regime_momentum_signed_5d importance = 171.9 (66.1% drop from /060 anchor 506.67, below 253.34 threshold). C6 portfolio share = 128.6 / 4731.2 = 2.72% (below 5%). BOTH legs hold. Multi-seed pattern remarkably stable vs /119 single-seed.
- **F4 fire numerical proof**: IS = +0.7293 below +0.79 floor by 0.0607. BCH IS net_pnl_pct dropped 69.31 pct vs /059 — regime-cost mechanism predicted by the brief DID fire on the IS side; Optuna at multi-seed did not recover enough.

Substantive question: is the OOS record **driven by Component A alone** (C6 = redistribution catalyst that cannibalizes regime_momentum without contributing direct edge), in which case dropping C6 per F3 yields /116-only whose 10-seed OOS Sharpe is currently unknown? Engineering report Section 11.3 flags the attribution gap.

The brief's Section 8.4 first-match-wins decision tree explicitly handles the F3-DROP branch: "DROP Component B; re-evaluate /116-only against the same gates". But no /116-only 10-seed report exists on disk.

## Clarifications Requested from QR

1. **Attribution gap (central question)**: F3 mandates "DROP Component B; revert to /116-only for MERGE evaluation" but /116-only 10-seed CONFIRMATION-spec metrics do not exist. What's the QR's pre-committed handling for this branch when /116-only is unevaluated? Specifically: (a) Close cycle 6 CONFIRMATION-NO-MERGE without isolating Component A's 10-seed contribution? OR (b) Authorize a post-/120 /116-only 10-seed methodology iteration before cycle 7 axis selection?

2. **F4 knife-edge fail (0.0607)**: F4 fires per pre-committed +0.79 floor (chosen at /059 IS − 0.30). Miss is well within the 10-seed multi-seed compression band the brief documented. Does the QR claim F4 is genuine binding-fail OR knife-edge artifact? (Critic position: pre-commitment is binding contract.)

3. **F3 mechanism scope clarification**: F3 mechanism is "C6 cannibalizes without contributing direct edge". /120 confirms redistribution (sister −66.1%) AND C6's 2.72% direct share is insufficient. Yet OOS lift is +1.12 — far exceeding what 2.72% direct edge can produce. Does the QR claim: (a) Component A acts on a C6-reshaped feature landscape (interaction effect — bundle should be retained), (b) Component A acts alone, C6 net-neutral (DROP harmless), or (c) third mechanism?

4. **BASELINE_V3.md leg**: IS +0.7293 < /059 IS +1.0894 mandates no baseline update. Confirm UNCHANGED at /059, OR propose all-time-OOS-record exception?

5. **Cycle-7 framing**: Under mechanical NO-MERGE, cycle 7 must structurally reorient. Does the QR commit to cycle-7 axis menu from /119 diary §8.2 candidates (cross-asset/external feeds, longer-cadence labels, NEW model architecture), OR start cycle 7 with a /116-only 10-seed methodology validation (iter-v3/121-METHODOLOGY) to settle the attribution before axis selection?

## Preliminary Direction

The pre-committed falsifiers F3 and F4 fire on unambiguous numerical evidence; the mechanical verdict is **CONFIRMATION-NO-MERGE** per brief Section 8.4 first-match-wins. BASELINE_V3.md does NOT update per BOTH-must-improve gate breaking on the IS leg.

The all-time v3 OOS record is a notable structural finding but does not override pre-committed binding falsifiers.

**One-line recommendation**: Cycle 6 closes with CONFIRMATION-NO-MERGE per pre-committed F3+F4. A post-/120 /116-only 10-seed methodology validation iteration (iter-v3/121-METHODOLOGY) is **WARRANTED** before cycle 7 axis selection — the binding F3 component-drop branch mandates re-evaluating /116-only, currently unevaluated at CONFIRMATION-spec 10-seed level.
