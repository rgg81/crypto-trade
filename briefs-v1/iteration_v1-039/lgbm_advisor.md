# LightGBM Master Advisor — iter-v1/039 — Phase 4.5 (Pre-Design)

## Context Read
- Track: v1, baseline `v0.v1-baseline-corrected` (IS Sharpe +0.2829 / OOS Sharpe +0.6637 / 621 IS trades / 189 OOS trades / R2 fire rate IS 71.2%, OOS 63.0%).
- Prior iter /038 still running — same risk-primitive family, different mechanism (vol CEILING scale-down vs /039 binary KILL on DD).
- QR's tentative axis: per-symbol p75 rolling-30d DD binary brake; per-symbol thresholds (BTC 3.88%, ETH 4.31%, LINK 6.44%, LTC 6.60%, DOT 2.77%); recovery = threshold × 0.5.
- EDA prior (`eda_findings.md` §4): **mechanism BACKWARD on 3 of 5 symbols** — skipped trades on LINK mean +2.059%/trade vs retained +0.186%; aggregate Δ-IS-PnL ≈ **−64.07%** on the IS sum. This is a NEGATIVE-prior axis.

## Recommended Hyperparameter Direction

### 1. Hold HP grid CONSTANT vs /038
- **What**: `num_leaves [16,63]`, `max_depth [3,7]`, `min_data_in_leaf [20,300]`, `learning_rate [0.01,0.1]`, `lambda_l1 [0,3]`, `lambda_l2 [0,3]`, `feature_fraction [0.5,1.0]`, `bagging_fraction [0.5,1.0]`, `bagging_freq [0,10]` — same Optuna bounds as `run_baseline_v1.py` default. `n_trials=18`, single seed=42, ENSEMBLE_SIZE=3.
- **Why**: brake fires POST-prediction at the gate layer; model training is UNCHANGED. Mixing HP search with the gate axis breaks single-axis isolation (Critic Check 14 Axis Family violation).
- **Risk**: zero — guaranteed clean attribution.

### 2. FLAG confidence_threshold compensation incentive (DO NOT pin, but instrument)
- **What**: Optuna may LOWER `confidence_threshold` to recover the ~30% skipped trade volume (more entries at threshold=lower offsets the binary kill). Brief Section 3 must record per-cell `best_confidence_threshold` and compare distribution against /038 + baseline.
- **Why**: gate-kill ~30% IS trades is a large incentive; Optuna's IS objective sees the kill as "model is wrong on those candidates" and will tilt toward lower-threshold/higher-recall regions to refill the trade count.
- **Risk**: if observed `confidence_threshold` drops > 15% vs baseline, the axis is no longer "binary kill on DD" alone — it's compounded with a threshold migration. Flag as MIXED-AXIS in post-mortem.

### 3. ensemble_size = 3, n_trials = 18 (EXPLORATION-spec)
- **What**: no bump. Drawdown brake is deterministic rule on backtest PnL state — no prediction-variance source for the inner ensemble to reduce. n_trials=18 single-seed=42 is adequate.
- **Why**: gate firing is independent of model stochasticity. Ensemble averaging gives nothing to the gate decision.
- **Risk**: none.

## Recommended Feature-Engineering Direction

**NONE this iteration.** This is a pure RULE-layer / risk-primitive axis. V1_FEATURE_COLUMNS (193 cols) unchanged. Feature-importance sanity check (see post-mortem hint below) is verification, not engineering.

## Saturation Risks to Flag

**(a) Mechanism-backward EDA is the dominant signal.** LINK's skipped-trade mean of +2.059%/trade (vs retained +0.186%) means the brake removes the SINGLE RICHEST DECILE of the IS roster. This is not a "tunable knob" — inverting the threshold won't fix it because the brake's hypothesis (high-DD → hostile regime) is REFUTED for v1's per-symbol PnL on a momentum-leaning model. Brief Section 0/2 must declare HIGH-RISK and the EDA NEGATIVE prior explicitly.

**(b) STATEFUL DEADLOCK risk — BACKTEST vs LIVE asymmetry.** At backtest layer, `cum_pnl` is computed from the full UN-GATED realized roster as a counterfactual reference (the brake reads PnL history that includes trades the brake itself would have suppressed). **No deadlock at backtest** because `dd` keeps moving regardless of gate decisions. At LIVE deployment, `cum_pnl` is real-only (brake's own suppression freezes the curve) — ORACLE longest-on runs of 97.7d BTC / 67.7d LINK / 69.3d DOT could become UNBOUNDED in closed-loop. **Brief Section 2 MUST acknowledge: "Backtest uses counterfactual full-history PnL; live deployment requires deadlock-impossibility instrumentation (time-decay max_on_bars OR probe-trade OR signal-equity-curve substitute) before testnet handoff."** Per `feedback_v3_oracle_eda_validity.md` (iter-v3/054 deadlock precedent), this is the load-bearing structural caveat — closed-loop simulator OR time-decay recovery rule mandatory pre-CONFIRMATION.

**(c) Trade-count floor margin is THIN.** EDA predicts 189 → ~133 OOS trades (29.8% kill rate). The skill's ≥130 OOS floor holds barely; per-symbol OOS-trades/month for DOT/LTC may dip BELOW the 10/month floor. F-AXIS #4 should track per-symbol monthly trade count, not just portfolio aggregate.

## Falsifier Formulation for Brief Section 4

- **F-AXIS #2 wiring**: dispatch banner `[v1-039] drawdown_brake ARMED for {sym}: threshold={thresh:.3%} recovery={rec:.3%}` for all 5 symbols at strategy init; runtime assert `brake_state in {ON, OFF}` per bar. PASS = banner ≥5 lines + zero assert failures.
- **F-AXIS #3 LOAD-BEARING per-symbol mechanism**: per-symbol skip rate ∈ [EDA_pred − 10%, EDA_pred + 10%]. BTC ∈ [21.9%, 41.9%], ETH ∈ [23.1%, 43.1%], LINK ∈ [15.3%, 35.3%], LTC ∈ [15.0%, 35.0%], DOT ∈ [25.5%, 45.5%]. Three or more symbols outside band = mechanism-wiring FAIL.
- **F-AXIS #4 trade-count**: IS trade count = 621 − N_skipped where N_skipped ∈ [167, 203] (185 ± 10%). Binary kill is deterministic — no model retraining gate semantic — so observed N_skipped should match counterfactual ORACLE within rounding except for the closed-loop-vs-counterfactual gap (TBD: small if brake fires on full-history PnL; large if on real-only PnL). Brief MUST specify which PnL feed the implementation uses.
- **F-AXIS #5 wall-clock**: ~50 min anchored on /038 (gate adds a constant-time per-bar check; no model retraining cost). Cap at 75 min hard.
- **F-AXIS #6 (recommended new) feature-importance stability**: top-5 feature ranks per cohort (A/C/D/E) match baseline ±2 positions across all 4 cohorts. Brake is post-prediction, so importance MUST be unchanged. FAIL = wiring defect (gate reading state inside training loop).

## What I Did NOT Recommend, and Why

- **No HP grid widening / narrowing**: clean single-axis isolation; HP-axis trades belong in a separate iteration.
- **No mechanism INVERSION** ("skip on LOW DD, enable on HIGH DD"): mechanically interesting per EDA §4 evidence (skipped-trade mean is HIGHER than retained on BTC+LINK), but that's a DIFFERENT primitive — separate brief. Flag in /039 closeout diary for /040 candidate.
- **No closed-loop simulator implementation this iteration**: simulator is INFRA (~2 days), not an EXPLORATION axis. /039's deliverable is the ORACLE-evidence verdict + structural insight. If closed-loop is mandatory pre-CONFIRMATION, /045+ adds it.

## Closing Note

**Confidence rating: MEDIUM — high confidence of NON-ZERO behavioral effect (the gate WILL fire and WILL skip ~185 trades), but LOW confidence of NON-NEGATIVE Sharpe outcome.** Probability distribution: PROMISING 10% / INERT 15% / NEGATIVE 60% / NEGATIVE-CATASTROPHIC 15%. The EDA's mechanism-backward finding on LINK is the load-bearing signal — proceeding as a clean single-axis test of the binary-KILL-on-DD primitive is defensible because v1 needs to PROVE the EDA prior in closed-loop and definitively close the axis. Single most important non-ignorable: **Brief Section 2 must explicitly state the counterfactual-vs-real PnL feed choice** AND **declare deadlock-impossibility live-deployment caveat** per `feedback_v3_oracle_eda_validity.md`. Without that wording, /039 cannot legitimately graduate to CONFIRMATION even if it passes EXPLORATION.

---

## Report-Back (under 300 words)

**Three strongest LM Master recommendations:**

1. **Hold HP grid CONSTANT** (same Optuna bounds as /038; n_trials=18, single seed=42, ENSEMBLE_SIZE=3). Gate fires POST-prediction so model HP space is irrelevant; mixing breaks single-axis attribution and Critic Check 14.

2. **FLAG confidence_threshold compensation incentive in Brief Section 3.** Binary kill at ~30% IS trade rate creates a strong Optuna incentive to LOWER `confidence_threshold` to refill recall. Instrument per-cell `best_confidence_threshold` distribution vs baseline; flag MIXED-AXIS in post-mortem if drop > 15%.

3. **Add F-AXIS #6 feature-importance stability falsifier.** Top-5 ranks per cohort (A/C/D/E) must match baseline within ±2 positions. Brake is post-prediction so importance MUST be unchanged — divergence = wiring defect (gate state leaking into training loop). Cheap sanity check.

**Confidence that axis produces non-zero behavioral effect: HIGH** (~95%). EDA shows gate will fire on ~29.8% IS trades (185/621), ~5/15 OOS trades/month. F-AXIS #4 trade-count will register clear delta.

**Confidence axis produces NON-NEGATIVE Sharpe: LOW** (~10% PROMISING / 15% INERT / 60% NEGATIVE / 15% catastrophic). LINK's skipped-trade mean of +2.059%/trade vs retained +0.186%/trade means the brake removes the IS roster's richest decile. Mechanism is BACKWARD on 3 of 5 symbols.

**Stateful-deadlock pre-flight recommendation:** Brief Section 2 MUST explicitly state which PnL feed the implementation uses — **counterfactual full-history PnL (backtest-safe, no deadlock possible) vs real-only PnL (live-faithful but deadlock-vulnerable)**. ORACLE longest-on runs (BTC 97.7d / LINK 67.7d / DOT 69.3d) become UNBOUNDED in closed-loop real-only. Per `feedback_v3_oracle_eda_validity.md` (iter-v3/054 deadlock precedent), pre-CONFIRMATION graduation requires EITHER (a) time-decay recovery `max_on_bars=30` (~10 days) OR (b) probe-trade mechanism OR (c) closed-loop simulator with formal deadlock-impossibility proof. Without explicit Section 2 wording, /039 cannot legitimately graduate past EXPLORATION.

File written to: `/home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-039/lgbm_advisor.md` (Phase 4.5 section content above; orchestrator will persist).
