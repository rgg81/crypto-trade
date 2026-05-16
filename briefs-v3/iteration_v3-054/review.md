# Phase 7.5 Critic Review — iter-v3/054

OVERALL: **EXPLORATION-NEGATIVE** — PATH C-clean fires unambiguously per pre-registered Section 8 LOCKED thresholds (OOS Δ = -0.5053 << -0.30 trigger). PATH C-suspicious co-fires (IS-OOS daily ratio = 0.0000 outside [0.5, 2.0]). Saturation falsifier fires (881 main-run brake fires; BCH+LDO permanently braked in OOS). PATH E fires concurrently (CPCV 29/45 positive, median +0.3351, Q25 -0.243 — bit-identical to /051/052/053 to 4 decimals; FOURTH consecutive iteration). Per brief Section 8 hierarchy: PATH C-clean takes precedence. Drawdown-brake axis CLOSED + entire "NEW risk primitive" axis family CLOSED at single-seed EXPLORATION scope.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION — Cycle 4 #4 of 10. Spec: `--seeds 1 --n-trials 35 --clean-oof`; ENSEMBLE_SIZE=5; outer seed=42; 1.26h wall-clock under 2h cap.

## QR Response Considered (Round 2 only)

Round 1 PRELIMINARY skipped — orchestrator dispatched directly with FINAL mode. The verdict pathway is mechanically determined by Section 8 LOCKED PATH C-clean pre-registration: OOS Δ < -0.30 trigger fires with Δ = -0.5053 (1.68× the trigger magnitude). No QR clarification could change this verdict without violating `feedback_no_cheating.md` post-hoc renegotiation discipline.

## Per-Check Status (12 standard methodology checks)

### Check 1 — Look-Ahead Audit: PASS
Per-symbol drawdown brake state machine (`risk_v2.py:346-396`) is past-only by construction: state updated via `record_trade_result` after each closed trade. `dd_30d` computation uses `_brake_running_peak[sym]` and `_brake_cum_wpnl[sym]` accumulated from past closed trades. Signal-kill at line 313-315 reads current `_brake_on[sym]` flag reflecting only past closed trades.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP = 66 = (21+1)×3 UNCHANGED. Per-cell PBO mean = 0.1243 (`per_cell_pbo.csv`). frac_positive_paths = 0.6444 (45 paths). Identical to /053.

### Check 3 — Multiple-Testing Correction: EXPLORATION-INFORMATIONAL (PBO axis PASS; DSR/PSR FAIL = structural artifact)
- DSR = 0.0000 (informational per `feedback_v3_dsr_mode_artifact.md`; structural at n_eff=19)
- PSR = 0.0000 (structural: zero OOS trades collapses PSR)
- PBO mean = 0.1243 < 0.40 — PASS
- n_eff = 19 — matches /051/052/053 (cycle-4 structural constant)

### Check 4 — IC Correlation: PASS
14-feature stack carry-forward. No new features at /054 (axis is a risk gate). Max |IC| outside source-primitive carve-outs ≤ 0.62.

### Check 5 — ADF Stationarity: PASS (inherited from /053 base 14-feature stack)

### Check 6 — Pareto Dominance: WARN — single-seed degenerate point
seed=42 OOS metrics ALL = 0.0 (no trades). Most severe Pareto pathology in v3 history. Standard dominance check vacuous; verdict driven by Section 8.

### Check 7 — Reproducibility: PASS
Setup SHA `c21ce7e`; gate SHA `7ad6389`. ITERATION_LABEL="v3-054". Explicit feature_columns (asserts hurst_drift_50_200 NOT present, 14 features net). IS row PnL spot-check (TRX SHORT, weight 0.38): pnl -3.162%, net -3.262%, weighted -1.2394 — matches CSV.

### Check 8 — Hypothesis-Implementation Alignment: FAIL — implementation correct as specified, but brief spec has DESIGN DEFECT
- Implementation matches brief Section 3 byte-for-byte (verified line-by-line)
- BUT brief did NOT anticipate state machine DEADLOCK feedback loop:
  - State updates require `record_trade_result` → requires closed trade → requires `get_signal` non-NO_SIGNAL → requires `_brake_on[sym] == False`
  - Once `_brake_on[sym] = True`, the only escape route is a closed trade that the brake itself prevents
- This is a BRIEF DEFECT (design specification incompleteness), NOT implementation defect
- The methodology gap is in the ORACLE EDA (simulated brake on /053 trade roster where future trades exist regardless of state — fundamentally different from closed-loop production)
- Hypothesis ("brake reduces LDO OOS catastrophic streak by 5 trades, preserving 91 OOS trades") was not testable as designed; in production-mode brake-ON state monotonically drains OOS to zero

## Optional Checks 9-12

### Check 9 — Symbol Exclusion Enforcement: PASS
### Check 10 — Feature Isolation Enforcement: PASS
### Check 11 — Forming-Candle Audit: PASS (inherited from /053)
### Check 12 — Library Version Pinning: PASS (no new deps; stdlib `collections.deque`)

## Pre-Registered Path Adjudication

| Path | Trigger | Observed | Fired? |
|---|---|---|---|
| PATH A | IS Δ ≥ +0.05 AND OOS Δ ≥ +0.10 AND ratio in band AND fires ∈ [3, 25] AND CPCV shifted | All FAIL | NO |
| PATH B | N/A for risk primitives | — | NO |
| **PATH C-clean** | OOS Δ < -0.30 | OOS Δ = **-0.5053** (1.68× trigger) | **YES — UNAMBIGUOUS** |
| **PATH C-suspicious** | IS-OOS daily ratio OUTSIDE [0.5, 2.0] | ratio = **0.0000** | **YES** |
| PATH D | IS Δ in band AND OOS Δ in band AND fires ∈ [0, 25] | OOS Δ OUTSIDE band; fires >> 25 | NO |
| **Saturation falsifier** | fires < 3 OR fires > 25 | **881 main-run fires** | **YES** |
| **PATH E (CPCV-INVARIANT NULL)** | CPCV positive=29 AND median=+0.3351±0.005 AND Q25=-0.243±0.005 AND fires ≥ 5 | All 4 fire | **YES** |

**Primary classification: PATH C-clean (precedence per brief Section 8 hierarchy). Co-firing: PATH C-suspicious + Saturation falsifier + PATH E.**

## Critical Adversarial Findings

### 1. Brake state machine deadlock VERIFIED — structurally permanent in production backtest

`risk_v2.py:325-344`: `record_trade_result(trade)` invoked only when trade closes. `_update_drawdown_brake(trade)` at line 344 gated on closed trade. Once `_brake_on[sym] = True` (line 396 engagement), signal-kill at line 313 prevents subsequent signals → no entries → no closes → no state update → `_brake_on[sym]` stays True forever.

**No time-based escape mechanism**: 30-day rolling window expiry at `risk_v2.py:381` (`while deque[0][0] < cutoff: popleft()`) executes ONLY inside `_update_drawdown_brake`, which is never called when brake is ON.

Main-run brake state at IS-end:
- BCH: brake engaged on trade 81 (last IS trade, 2024-12-21, dd_30d=10.58). 93 days before OOS-start. Brake permanently ON in OOS.
- LDO: brake engaged near IS-end (~2025-02-08, dd_30d=10.22). 44 days before OOS-start. Brake permanently ON in OOS.
- TRX: brake OFF at IS-end (dd_30d=6.14 at last IS trade 2023-02-12, 771 days before OOS). TRX OOS=0 from independent cause (Optuna threshold + BTC trend filter killing all 18 TRX OOS signals; `seed_summary.json` btc_killed=18).

No `out_of_sample/` directory exists (no trades.csv produced). Consistent with brake-deadlock + TRX-independent-kill.

### 2. ORACLE EDA methodology defect — PATH-LATENT, not feature-specific

QR EDA simulated brake AS A FILTER on the /053 trade roster. In ORACLE mode, every trade in roster is processed by `_update_drawdown_brake` regardless of brake state. ORACLE's "5 OOS LDO trades skipped" was correctly computed in counterfactual but mechanically INVALID for predicting closed-loop backtest behavior.

**Methodology gap**: ORACLE EDA cannot model state-dependent feedback loops between gates and trade generation. For STATELESS gates (ADX, vol scaling, BTC trend), ORACLE is valid. For STATEFUL gates (drawdown brake, per-symbol cap with rolling window, cooldown timers, any gate where signal-emission updates persistent state), ORACLE is INVALID without explicit closed-loop simulation.

Brief acknowledged Optuna trajectory drift (30-50% deviation) but did NOT acknowledge qualitative deadlock failure mode. The 30-50% deviation framing assumed continuity. Actual divergence is DISCONTINUOUS: real backtest = 0 OOS trades; ORACLE = 91 OOS trades. 100% reduction is far outside the 30-50% caveat band.

### 3. CPCV-invariance pattern extends beyond 15th-slot family

iter-v3/054 was intended to be the EXIT axis from 15th-slot SWAP family — it added a RISK GATE primitive 11 with ZERO change to the feature-column stack vs base 14. Yet CPCV produced bit-identical 29/45 positive, +0.3351 median, -0.243 Q25 to 4 decimals.

**Updated structural finding**: single-seed CPCV stats at (3-sym universe, n_trials=35, ENSEMBLE_SIZE=5, base 14 features, seed=42) are determined by the (base feature stack, model architecture, walk-forward schedule) tuple, INVARIANT to:
- 15th-slot feature additions (/051, /052, /053)
- 15th-slot feature drops (/054 reverts to 14 features)
- Risk-gate primitives added downstream of the model (primitive 11 at /054)

The CPCV path-Sharpe distribution is anchored by the base 14-feature stack's generalization properties. 4-iteration invariance is systematic evidence requiring structural cycle-5 change.

### 4. PATH E pre-registration was effective

Credit to QR for executing /053 Critic recommendation #3 cleanly. The 4-iteration invariance is now systematic evidence (not coincidence). Without PATH E pre-registration, CPCV invariance could have been dismissed.

### 5. n_eff=19 cycle-4 structural constant extends to /054

n_eff=19 across /051/052/053/054 (4 iterations). At n_trials=525 the naive E[max_SR] saturates above realized Sharpe, mechanically forcing DSR=0. Cycle-4 EXPLORATION structural constant. CONFIRMATION at /061 will need either (a) increase n_trials, OR (b) reformulate DSR gate against n_eff (A2 axis QR deferred). **A2 is now MORE URGENT.**

## Recommendations to QR for iter-v3/055

1. **Add ORACLE EDA validity check for stateful primitives to memory rules**. Recommend new feedback file `feedback_v3_oracle_eda_validity.md`:
   - STATELESS gates: ORACLE EDA on prior trade roster IS VALID
   - STATEFUL gates: ORACLE EDA INVALID; requires closed-loop simulator OR formal deadlock-impossibility proof
   - Pre-registration requirement: brief Section 2 must explicitly classify axis as STATELESS or STATEFUL; if STATEFUL, must include deadlock analysis subsection

2. **Cycle-5 axis design must account for CPCV-determinism**. Adding risk gates or swapping 15th-slot features CANNOT shift CPCV path distribution. Cycle-5 axes must change: (a) base 14-feature stack, (b) universe (3-sym → 4+), (c) model architecture, (d) n_trials, or (e) ENSEMBLE_SIZE. Methodology-only axes (A2 DSR) won't shift CPCV — useful for gate-interpretation, can't exit cycle-4 deterministic regime.

3. **iter-v3/055 axis: PROMOTE A2 DSR gate reformulation**. Per QR brief Section 10.2: A2 methodology-only, ≤2h impl, addresses cycle-4 structural finding (DSR=0 at n_eff=19), zero CPCV-shift risk, zero deadlock risk. With A1 PATH C CLOSED and A3 CatBoost deferred (7-10h exceeds 2h cap), A2 is next viable axis. Parallel candidate: A4 (base-stack reordering) — requires fresh EDA on marginal base-14 feature with orthogonal (|IC|<0.5) replacement.

## Catalog Row

`| iter-v3/054 | 2026-05-11 | EXPLORATION cycle 4 #4 of 10: ADD per-symbol drawdown brake (NEW RiskV2 primitive 11; enable=True, threshold=10.0 wpnl, recovery=5.0 wpnl, window=30d) + DROP hurst_drift_50_200 from V3_FEATURE_COLUMNS_TOP_N (15→14 per /053 closeout PATH D PARK); V3_MODELS UNCHANGED 3-sym; REQUIRED_GAP=66 unchanged. Setup SHA c21ce7e; gate SHA 7ad6389. | -0.0520 (vs iter-v3/028 baseline +0.5101 → +0.4581) | **-0.5053** (vs iter-v3/028 baseline +0.5053 → **+0.0000**; BCH+LDO permanently braked in OOS via deadlock; TRX OOS=0 independent killed by BTC trend filter; OOS trades=0; IS-OOS daily ratio 0.0000 OUTSIDE [0.5, 2.0]; main-run brake fires 881 vs predicted ≤25; CPCV 29/45 positive median +0.3351 Q25 -0.243 IDENTICAL to /051/052/053 4th-consecutive) | EXPLORATION-NEGATIVE (PATH C-clean primary; PATH C-suspicious + Saturation + PATH E all co-fire) | NO — drawdown-brake axis CLOSED + entire "NEW risk primitive" axis family CLOSED at single-seed EXPLORATION scope; ORACLE EDA methodology defect confirmed for stateful primitives; new memory rule recommended `feedback_v3_oracle_eda_validity.md`. **CPCV-invariance pattern extends beyond 15th-slot family**: single-seed CPCV at (3-sym, n_trials=35, ENSEMBLE_SIZE=5, base 14 features, seed=42) is DETERMINISTIC regardless of 15th-slot changes OR risk-gate additions. Cycle-5 axes must change base feature stack / universe / model arch / n_trials / ENSEMBLE_SIZE to escape cycle-4 deterministic regime. iter-v3/055 PROMOTED axis: A2 DSR gate reformulation (methodology-only, ≤2h, addresses cycle-4 DSR=0 structural). Cycle 4 cadence advances 4/10. Tag NOT issued. |`

## Files Audited

- `briefs-v3/iteration_v3-054/research_brief.md` (SHA `78b7d00`)
- `briefs-v3/iteration_v3-054/phase5p5_gate.md` (SHA `7ad6389`)
- `briefs-v3/iteration_v3-054/engineering_report.md` (SHA `b376d93`)
- `reports-v3/iteration_v3-054/` (NOTE: no `out_of_sample/` directory — OOS trades=0)
- `src/crypto_trade/strategies/ml/risk_v2.py` (lines 140-163 RiskV2Config; 309-315 signal-kill; 325-344 record_trade_result; 346-396 state machine)
- `analysis/iteration_v3-054/synthesis.md` + `brake_synthesis.md` + EDA scripts (SHA `e565b82`)
- `briefs-v3/iteration_v3-053/review.md` (immediate predecessor)
