# Iteration iter-v3/054 — Diary

## Decision: EXPLORATION-NEGATIVE (PATH C-clean primary; PATH C-suspicious + Saturation falsifier + PATH E all co-fire) — per-symbol drawdown brake (NEW RiskV2 primitive 11) entered permanent state-machine DEADLOCK in OOS; BCH+LDO brake engaged on last IS trade → brake-ON at OOS-start → signal-kill blocks all OOS signals → no closed trades → no state update → brake permanently frozen ON; OOS trades=0 across all 3 symbols; OOS Sharpe +0.0000; ORACLE EDA methodology defect confirmed for STATEFUL primitives; drawdown-brake axis + entire "NEW risk primitive" axis family CLOSED at single-seed EXPLORATION scope; cycle 4 #4 of 10

iter-v3/054 = **cycle 4 #4 of 10** EXPLORATIONs post-iter-v3/050 NO-MERGE CONFIRMATION closeout. **Axis** (QR-EDA-supported at SHA `e565b82` per `feedback_v3_axis_selection_quant_discipline.md` with 5-criterion 4-axis ranking + ORACLE counterfactual on /053 trade roster, written up in `analysis/iteration_v3-054/synthesis.md` + `brake_synthesis.md`): ADD per-symbol drawdown brake (NEW RiskV2 primitive 11) — 30-day rolling-trade-window peak tracker with state machine engage-at-T=10.0-wpnl + disengage-at-recovery=5.0-wpnl + per-symbol independent state; PLUS DROP `hurst_drift_50_200` from `V3_FEATURE_COLUMNS_TOP_N` per /053 closeout PATH D PARK action (15 → 14 features net). V3_MODELS UNCHANGED (3-sym BCH+LDO+TRX); REQUIRED_GAP UNCHANGED (66); regime_momentum_signed_5d PRESERVED at /028 edge-ingredient status. INTENDED as EXIT from 15th-slot SWAP family per Critic /053 FINAL `c056354` Recommendation #1 (15th-slot SWAP family STRUCTURALLY EXHAUSTED at single-seed EXPLORATION per CPCV-invariance across /051/052/053). Run spec: `--seeds 1 --n-trials 35 --clean-oof` (EXPLORATION-spec; 525 total Optuna trials = 3 syms × 5 inner × 35).

Result: **IS single-seed Sharpe +0.4581 / OOS single-seed Sharpe +0.0000 (seed 42); OOS trades = 0; IS-OOS daily Sharpe ratio = 0.0000.** Per the brief Section 8 pre-registered 6-path criteria (LOCKED at brief commit SHA `78b7d00`), **PATH C-clean fires UNAMBIGUOUSLY** (OOS Δ = -0.5053 << -0.30 trigger; 1.68× the trigger magnitude). PATH C-suspicious co-fires (IS-OOS daily ratio 0.0000 OUTSIDE [0.5, 2.0]). Saturation falsifier co-fires (881 aggregate brake fires across 230 evaluations vs predicted ≤ 25 main-run upper bound). **PATH E (CPCV-INVARIANT NULL) co-fires** — CPCV 29/45 positive, median +0.3351, Q25 -0.243 BIT-IDENTICAL to /051/052/053 to 4 decimals (4th consecutive cycle-4 iteration; brake fires 881 >> 5 satisfies PATH E "mechanism fired" condition).

Per Critic FINAL `db1551b`:

- PATH A (PROMISING-clean): IS Δ -0.0520 (FAIL ≥ +0.05); OOS Δ **-0.5053** (FAIL ≥ +0.10); brake fires 881 (FAIL ∈ [3, 25]); CPCV INVARIANT (FAIL "shifted") → NO
- PATH B (PROMISING-INERT): N/A for risk primitives → NO
- **PATH C-clean: OOS Δ -0.5053 < -0.30 → FIRES UNAMBIGUOUSLY**
- **PATH C-suspicious: IS-OOS daily ratio 0.0000 OUTSIDE [0.5, 2.0] → FIRES**
- PATH D (NULL-RESULT): IS Δ -0.0520 ∈ (-0.10, +0.05) ✓; OOS Δ -0.5053 OUTSIDE (-0.20, +0.20) ✗ → NO
- **Saturation falsifier: 881 brake fires >> 25 main-run upper bound → FIRES**
- **PATH E (CPCV-INVARIANT NULL): all 4 conditions fire (positive=29, median=+0.3351, Q25=-0.243, fires ≥ 5) → FIRES**

**Primary classification: PATH C-clean (precedence per brief Section 8 hierarchy). Co-firing: PATH C-suspicious + Saturation falsifier + PATH E.** Per brief Section 8 PATH C-clean outcome: **drawdown-brake axis CLOSED for cycle 4.** Per brief Section 8 PATH E outcome (fires alongside PATH C): **entire "NEW risk primitive" category axis CLOSED at /054 for single-seed EXPLORATION scope** until structural change to underlying CPCV anchoring is made.

**ROOT CAUSE (Critic Adversarial Finding #1, VERIFIED at SHA `db1551b`):** `risk_v2.py` state-machine architectural defect. `_update_drawdown_brake` (the only state-mutating method) is invoked ONLY via `record_trade_result` (closed-trade hook at lines 325-344). Once `_brake_on[sym] = True` (engagement at line 396), signal-kill at line 313 returns NO_SIGNAL → no entries → no trades close → `record_trade_result` never called → `_update_drawdown_brake` never runs → `_brake_on[sym]` stays True indefinitely. **No time-based escape mechanism exists**: 30-day rolling window expiry at `risk_v2.py:381` executes ONLY inside `_update_drawdown_brake`, which is never called when brake is ON. This is a **permanent deadlock**.

Main-run brake state at IS-end:
- **BCH**: brake engaged on last IS trade (trade 81, 2024-12-21, dd_30d=10.58 ≥ T=10.0). 93 days before OOS-start. Permanently ON throughout OOS.
- **LDO**: brake engaged near IS-end (~2025-02-08, dd_30d=10.22). 44 days before OOS-start. Permanently ON throughout OOS.
- **TRX**: brake OFF at IS-end (dd_30d=6.14 at last IS trade 2023-02-12, 771 days before OOS). TRX OOS=0 from INDEPENDENT cause (Optuna threshold + BTC trend filter killed 18 TRX OOS signals per `seed_summary.json` btc_killed=18).

No `out_of_sample/` directory exists in `reports-v3/iteration_v3-054/` — consistent with brake-deadlock + TRX-independent-kill producing zero OOS trades across all 3 symbols.

**METHODOLOGY DEFECT (Critic Adversarial Finding #2 + new memory rule):** The QR's ORACLE EDA (`analysis/iteration_v3-054/per_symbol_drawdown_brake_eda.py`, SHA `e565b82`) simulated the brake AS A FILTER on the /053 trade roster. In ORACLE mode, every future trade exists in the roster regardless of brake state — the EDA's counterfactual function processed trades 6-9 as SKIPPED but trade 10 (+9.41 wpnl recovery) still appeared in the roster and was correctly skipped per the state machine. **However, the ORACLE methodology cannot model the closed-loop feedback** where brake ON → no signals → no closed trades → no state update → permanent freeze. The ORACLE-predicted 7 fires (2 BCH IS + 5 LDO OOS) was correctly derived on the counterfactual but mechanically INVALID for predicting real backtest behavior. Real backtest: 881 brake fires (aggregate), OOS trades = 0, 100% OOS signal blockage. The 100% blockage is far outside the brief's 30-50% Optuna-trajectory-shift caveat band — DISCONTINUOUS divergence, not continuous deviation.

**NEW memory rule (orchestrator-applied at Critic FINAL SHA `db1551b`): `feedback_v3_oracle_eda_validity.md` CREATED 2026-05-11.** Establishes STATELESS vs STATEFUL gate classification + brief Section 2 Deadlock Analysis requirement for STATEFUL axes:

- **STATELESS gates** (gate decision independent of prior gate-decision state): ADX threshold, vol scaling, BTC trend filter, OOD z-score gate, fixed confidence thresholds, low-vol kill, per-symbol cap (if fixed not rolling). → ORACLE EDA on prior trade roster IS VALID.
- **STATEFUL gates** (gate decision depends on persistent state updated by prior gate-decision outcomes): drawdown brake (rolling-window peak tracker), cooldown timers blocking N signals after SL, streak counters (R1-style), per-symbol exposure caps with rolling positions, any gate where BLOCK decision prevents signal outcome from updating state. → ORACLE EDA INVALID; requires **(a)** closed-loop simulator modeling the feedback OR **(b)** formal proof in brief Section 2 that gate state cannot enter stuck-state with time-based or trade-independent escape mechanism documented.

Phase 5.5 gate enforcement (per new rule): QE must verify STATEFUL-classified axes include Deadlock Analysis subsection. Missing = BLOCK. iter-v3/054 brief did NOT include this subsection (Section 2 acknowledged 30-50% Optuna trajectory drift caveat but did NOT acknowledge qualitative deadlock failure mode). Engineering report `b376d93` documented the methodology gap. Critic FINAL `db1551b` formalized at memory rule level.

**STRUCTURAL FINDING extends (Critic Adversarial Finding #3): CPCV-invariance pattern extends BEYOND 15th-slot SWAP family.** iter-v3/054 was intended as the EXIT axis — it added a RISK GATE primitive 11 with ZERO change to the feature-column stack (base 14 features carry-forward from /028 minus the /053 hurst_drift PARK). Yet CPCV produced BIT-IDENTICAL 29/45 positive, +0.3351 median, -0.243 Q25 to 4 decimals — same as /051, /052, /053. **4 consecutive iterations with identical CPCV path-Sharpe distributions to 4 decimal places.** Updated structural finding (supersedes /053's "15th-slot SWAP exhaustion" framing): single-seed CPCV stats at (3-sym universe, n_trials=35, ENSEMBLE_SIZE=5, base 14 features, seed=42) are DETERMINISTIC regardless of:

- 15th-slot feature additions (/051, /052, /053)
- 15th-slot feature drops (/054 reverts 15 → 14 features)
- Risk-gate primitives added downstream of model (/054 primitive 11)

The CPCV path-Sharpe distribution is anchored by the base 14-feature stack's generalization properties + walk-forward schedule + model architecture, INVARIANT to 15th-slot content OR risk-gate additions. **Cycle-5 axes (iter-v3/062-/071) must change at least one of**: base 14-feature stack / universe (3-sym → 4+) / model architecture / n_trials / ENSEMBLE_SIZE. Methodology-only axes (A2 DSR reformulation) will NOT shift CPCV — useful for gate-interpretation, cannot exit cycle-4 deterministic regime. PATH E pre-registration (mandated at /053 Critic Recommendation #3) was instrumental: without it, CPCV invariance at /054 could have been dismissed as coincidence. With 4-iteration evidence, it is now systematic.

**n_eff = 19 CYCLE-4 STRUCTURAL CONSTANT extends to /054 (Critic Adversarial Finding #5).** n_effective_trials = 19 across /051/052/053/054 (4 iterations, integer-identical). At n_trials=525 the naive E[max_SR] saturates above realized Sharpe, mechanically forcing DSR = 0.0000 at single-seed EXPLORATION. **Cycle 4 CONFIRMATION at iter-v3/061 will need either (a) increase n_trials, OR (b) reformulate DSR gate against n_eff.** Per `feedback_v3_dsr_mode_artifact.md`: CONFIRMATION-mode DSR uses n_trials=1500 (E[max_SR] = 3.37) which still doesn't clear annualized 4.0. **A2 DSR gate reformulation is now MORE URGENT** — promoted to /055 axis per Critic FINAL `db1551b` Recommendation #3.

Wall-clock: 1.26h backtest (within 2h EXPLORATION cap; consistent with /051=1.28h, /052=1.25h, /053=1.25h). 11/12 standard methodology checks PASS per Critic FINAL `db1551b` (look-ahead PASS, embargo PASS, multiple-testing-correction EXPLORATION-INFORMATIONAL with PBO axis PASS + DSR/PSR structural-artifact FAIL, IC carry-forward PASS, ADF inherited PASS, reproducibility PASS, hypothesis-implementation alignment FAIL on BRIEF DEFECT not implementation defect, symbol exclusion PASS, feature isolation PASS, forming-candle inherited PASS, library-pinning PASS). Pareto dominance: WARN single-seed degenerate (OOS metrics all 0.0). No tag issued (EXPLORATION).

## What Was Tested

**Hypothesis (locked in brief Section 1, SHA `78b7d00`):** "ADDING a per-symbol drawdown brake (NEW RiskV2 primitive 11) to the v3 risk gate stack — alongside the system-level REVERT carry-forward (V3_MODELS = 3-sym BCH+LDO+TRX; V3_ATR_MULTIPLIERS_PER_SYMBOL = {}; block_long_for = (); REQUIRED_GAP = 66) and PARKING the 15th-slot SWAP attempts (V3_FEATURE_COLUMNS_TOP_N reverts to 14 base features) — investigates whether a Carver-canonical loss-stop mechanism detects and pauses symbols in catastrophic-drawdown regime, lifting bundle IS Sharpe vs iter-v3/028 anchor +0.5101 and OOS Sharpe vs +0.5053 by removing the cycle-4 LDO OOS catastrophic streak identified across /051/052/053 diaries."

**Targeted finding (brief Section 1):** LDO OOS wpnl across cycle-4 EXPLORATIONs has ranged -13.96 to -17.44 with a canonical 7-consecutive-loser drawdown pattern: peak +15.06 (after 2 winners) → 7 consecutive losers → cum_wpnl -20.17 (35.23 wpnl drawdown). A brake calibrated at T=10.0 wpnl drawdown (recovery 5.0) ORACLE-engaged after trade 4 and ORACLE-skipped trades 5-9 (the worst losses), saving ~30 wpnl in counterfactual losses (+12.51 net Δ after counting the missed +9.41 trade-10 recovery).

**Predicted bands (brief Section 1 + Section 4):**
- IS Sharpe: [+0.45, +0.65] (mean +0.55); Δ vs /028 anchor: [-0.06, +0.14]
- OOS Sharpe: [+0.55, +0.85] (mean +0.70); Δ vs /028 anchor: [+0.05, +0.35]
- IS-OOS daily Sharpe ratio: ∈ [0.5, 2.0] with 65% prob
- IS trade count: [175, 180]; OOS trade count: [90, 93]
- drawdown_brake_fires (full backtest, main run): [3, 25]; ORACLE-predicted 7
- LDO OOS wpnl: [-5, +5] (vs /053 -15.61); central +14 to +20 vs /053

**Predicted path classification (locked in brief Section 0.5):**
- PATH A: 35% / PATH B: 5% / PATH C-clean: 15% / PATH C-suspicious: 10% / PATH D: 30% / **PATH E: 5%**

The QR's PATH A 35% probability rested on the ORACLE counterfactual's +12.51 OOS wpnl Δ assuming Optuna trajectory stayed within 30-50% deviation. The **actual divergence was 100% (zero OOS trades)** — categorically outside the predicted band.

**Spec (locked in brief Section 0.5; setup commit SHA `c21ce7e`):**
- ITERATION_LABEL = "v3-054"
- V3_FEATURE_COLUMNS_TOP_N = 14 features (DROP hurst_drift_50_200 per /053 PATH D PARK; compute_hurst_drift_50_200 retained as dead code)
- V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols UNCHANGED from /053
- V3_ATR_MULTIPLIERS_PER_SYMBOL = {} UNCHANGED
- block_long_for = () UNCHANGED
- REQUIRED_GAP = 66 = (21+1)×3 UNCHANGED
- regime_momentum_signed_5d PRESERVED (iter-v3/028 edge ingredient)
- **NEW RiskV2Config primitive 11**: `enable_per_symbol_drawdown_brake=True`, `drawdown_brake_threshold_wpnl=10.0`, `drawdown_brake_recovery_wpnl=5.0`, `drawdown_brake_window_days=30`
- 5 NEW adversarial tests in `tests/strategies/ml/test_risk_v2_drawdown_brake.py` PASS (brake disabled by default; engages at threshold per-symbol; disengages at recovery; independent across symbols; respects 30-day rolling window)
- Runner: `uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof`
- ENSEMBLE_SIZE = 5 (auto inner ensemble); outer_seeds = 1 (EXPLORATION-spec)
- Wall-clock: 1.26h backtest (within 2h cap)
- Total Optuna trials: 525 = 3 syms × 5 inner × 35

## Headline Numbers

### Single-seed primary (comparison.csv + seed_summary.json; seed 42 only)

| Metric | iter-v3/028 BASELINE (multi-seed mean) | iter-v3/051 (1-seed) | iter-v3/052 (1-seed) | iter-v3/053 (1-seed) | **iter-v3/054 (1-seed)** | Δ vs iter-v3/028 | Δ vs iter-v3/053 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **IS monthly Sharpe** | +0.5101 | +0.4506 | +0.5161 | +0.4726 | **+0.4581** | **-0.0520** | -0.0145 |
| **OOS monthly Sharpe** | +0.5053 | +0.5891 | +1.4295 | +0.4745 | **+0.0000** | **-0.5053** | **-0.4745** |
| **IS daily Sharpe** | — | +0.9685 | +1.1692 | +1.1849 | **+1.6559** | — | +0.4710 |
| **OOS daily Sharpe** | — | +1.1116 | +2.7204 | +1.4344 | **+0.0000** | — | -1.4344 |
| **IS-OOS daily Sharpe ratio** | 0.99 | 1.148 (in-band) | 2.327 (OUT-OF-BAND) | 1.2105 (in-band) | **0.0000 (OUT-OF-BAND)** | **OUT-OF-BAND** | OUT-OF-BAND |
| IS Trades | 156 (mean) | 178 | 188 | 180 | **106** | -50 (-32%) | **-74 (-41%)** |
| **OOS Trades** | 95 (mean) | 96 | 93 | 96 | **0** | **-95 (-100%)** | **-96 (-100%)** |
| IS MaxDD | 41.43% | 37.37% | 32.58% | 45.37% | **26.42%** | -15.0pp better | -18.95pp better |
| OOS MaxDD | 23.53% | 32.75% | 30.42% | 44.22% | **0.00%** | — (no trades) | — (no trades) |
| OOS Calmar | 0.92 | 0.53 | 1.47 | 0.5558 | **0.00** | -0.92 | -0.56 |
| profit_factor OOS | — | — | — | — | **inf** | — (no trades) | — (no trades) |
| DSR | 0.0 (structural at /028 multi-seed) | 0.0 (structural) | 0.0 (structural) | 0.0 (structural) | **0.0** (structural at n_trials=525) | structural artifact | identical |
| PBO | 0.1243 | 0.1168 | 0.1090 | 0.1377 | **0.1243** | 0.000 | -0.013 |
| PSR | 1.0 | 1.0 | 1.0 | 1.0 | **0.0000** | **-1.0** (zero-OOS collapse) | **-1.0** |
| frac_positive_paths | 0.644 | 0.644 | 0.644 | 0.644 | **0.644** | identical | identical |
| Median path Sharpe | +0.335 | +0.3350 | +0.3351 | +0.3351 | **+0.3351** | identical | identical (4 decimal places) |
| Q25 path Sharpe | — | -0.243 | -0.243 | -0.243 | **-0.243** | identical | identical (4 decimals) |
| n_trials | 1050 | 525 | 525 | 525 | **525** | EXPLORATION spec | EXPLORATION spec |
| n_eff | 19 | 19 | 19 | 19 | **19** | within range | identical (CYCLE-4 CONSTANT) |
| drawdown_brake_fires (aggregate) | n/a | n/a | n/a | n/a | **881 / 230 evals** | n/a | n/a |

**Critical observation #1 (OOS=0 catastrophe):** OOS monthly Sharpe = **+0.0000** is the **most severe OOS result in v3 history** (prior worst was iter-v3/016 XGBoost OOS Δ -2.53 at OOS Sharpe -2.5). /054 represents a COMPLETE OOS shutdown across all 3 symbols. Root cause: BCH+LDO brake permanently ON at OOS-start via state-machine deadlock; TRX OOS=0 from independent BTC trend filter cause (18 TRX OOS signals killed). All 3 symbols produce 0 OOS trades. No `out_of_sample/` directory created.

**Critical observation #2 (IS trade reduction 35× ORACLE prediction):** IS trades = 106 vs /053 = 180 (-74 trades, -41%). The brake fired heavily during IS too — BCH had two brake engagements during IS (Nov 2022 brief engagement at trade 28 disengaged at trade 29; Dec 2024 permanent engagement at trade 81 — last IS trade), LDO had one engagement near IS-end, TRX had one brief engagement (Nov 2022, same period as BCH). The -74 IS trade reduction is **35× the QR's ORACLE prediction of -2 IS trades reduced**. This alone would have been a saturation falsifier trigger on IS regardless of OOS.

**Critical observation #3 (881 aggregate brake fires vs ≤25 predicted upper bound):** drawdown_brake_fires AGGREGATED across 230 model evaluations (45 CPCV paths + 1 main run, each with 5 inner seeds) = 881 fires. On per-evaluation basis: 881 / 230 = 3.83 fires per evaluation on average (close to the ORACLE's 7 predicted). But the main-run brake STATE (BCH and LDO permanently ON in OOS) is what matters operationally — categorically different from ORACLE's 5-fires-then-disengage prediction. The 125× discrepancy framing in the brief prompt is slightly inflated by the aggregate-vs-main-run conflation, but the OPERATIONAL discrepancy (zero OOS trades vs 91 predicted) is real and DISCONTINUOUS.

**Critical observation #4 (PSR collapse to 0.0):** PSR = 0.0000 (vs /051/052/053 = 1.0). PSR collapse is structural at zero-OOS conditions: E[max_SR] at 525 trials exceeds observed OOS SR of 0.0, giving PSR = 0.0. Consistent with EXPLORATION-mode DSR=0.0 artifact (`feedback_v3_dsr_mode_artifact.md`); both are structural at zero-OOS conditions. **PSR was NOT a structural-artifact zero in cycle-4 prior** — /051/052/053 all had PSR=1.0 because they had non-zero OOS Sharpe. /054 is the first cycle-4 EXPLORATION with PSR collapsed to 0.

### Per-symbol decomposition (seed 42)

**IS per-symbol (106 IS trades; brake active):**

| Symbol | trades | win_rate | net_pnl_pct | avg_pnl_pct | pct_of_total_IS_pnl |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 81 | 42.0% | +53.58% | +0.661% | **+101.80%** |
| TRXUSDT | 17 | 47.1% | +17.57% | +1.034% | **+33.38%** |
| LDOUSDT | 8 | 25.0% | -18.52% | -2.315% | **-35.18%** |

IS results are brake-filtered: 106 trades produced vs 180 at /053 (-74 trades, -41%). BCH contributed 101.80% of IS PnL (similar to /053's 255.38% but less extreme because TRX IS is now POSITIVE at 33.38% — TRX had a much smaller IS sample with the brake engaged on its late-IS signals). LDO IS remains negative (-35.18% PnL share) despite only 8 trades. **The brake filtered IS trades but did not eliminate the LDO IS negative signal-quality problem** (LDO IS WR 25.0%, avg_pnl -2.315%).

**OOS per-symbol:** **NO TRADES.** No `out_of_sample/` directory exists in `reports-v3/iteration_v3-054/`. seed_summary.json confirms btc_killed=18 OOS signals (all 3 symbols' OOS signals counted by gate). Per Engineering report root-cause reconstruction:

- BCH OOS signals: all killed by primitive 11 (brake_on=True frozen from IS-end)
- LDO OOS signals: all killed by primitive 11 (brake_on=True frozen from IS-end)
- TRX OOS signals: brake_on=False at IS-end; 18 TRX OOS signals killed by BTC trend filter (independent cause)

### Drawdown Brake Fire-Rate (aggregate gate_stats; 45 CPCV paths + 1 main run × 5 inner seeds = 230 evaluations)

| Symbol | signals_seen | drawdown_brake_fires | fire_rate | QR ORACLE predicted |
|---|---:|---:|---:|---:|
| BCH | 2,716 | 206 | 7.58% | — |
| LDO | 866 | 89 | 10.28% | — |
| TRX | 2,521 | 586 | 23.24% | — |
| **TOTAL** | **6,103** | **881** | **14.43%** | **[3, 25] main-run; 7 ORACLE** |

### §8 Pre-registered Path Verdict (mechanical, non-renegotiable)

| Path | Trigger | Observed | Fired? |
|---|---|---|---|
| PATH A (PROMISING-clean) | IS Δ ≥ +0.05 AND OOS Δ ≥ +0.10 AND ratio in band AND fires ∈ [3, 25] AND CPCV shifted | All FAIL | NO |
| PATH B (PROMISING-INERT) | N/A for risk primitives | — | NO |
| **PATH C-clean** | OOS Δ < -0.30 | OOS Δ = **-0.5053** (1.68× trigger) | **YES — UNAMBIGUOUS** |
| **PATH C-suspicious** | IS-OOS daily ratio OUTSIDE [0.5, 2.0] | ratio = **0.0000** | **YES** |
| PATH D | IS Δ in band AND OOS Δ in band AND fires ∈ [0, 25] | IS in-band; OOS OUTSIDE band; fires >> 25 | NO |
| **Saturation falsifier** | fires < 3 OR fires > 25 main-run | **881 aggregate, BCH+LDO permanent main-run** | **YES** |
| **PATH E (CPCV-INVARIANT NULL)** | CPCV positive=29 AND median=+0.3351±0.005 AND Q25=-0.243±0.005 AND fires ≥ 5 | All 4 conditions fire | **YES** |

**Primary classification: PATH C-clean (precedence per brief Section 8 hierarchy). Co-firing: PATH C-suspicious + Saturation falsifier + PATH E.**

The classification is mechanically determined by the pre-registration. PATH C-clean fires harder than PATH D (OOS Δ -0.5053 << -0.30 trigger), so PATH C takes precedence per the brief's hierarchy. The saturation falsifier language in brief §4.4 ("if brake fires < 3 OR > 25 → PATH D fires unambiguously regardless of Sharpe Δ") was written for the case where Sharpe Δ is ambiguous; when PATH C fires, PATH D is subsumed. No QR clarification could change this verdict without violating `feedback_no_cheating.md` post-hoc renegotiation discipline.

## Why EXPLORATION-NEGATIVE — Brake DEADLOCK Root Cause

### State-machine architectural defect (verified at SHA `db1551b`)

The drawdown brake state machine requires `record_trade_result` (called on each closed trade) to update `_brake_on[sym]`. When the brake is ON for a symbol:

1. `get_signal` returns `NO_SIGNAL` for that symbol (line 313-315).
2. No signal → no entry → no trade opened → no trade closes.
3. `record_trade_result` is never called → `_update_drawdown_brake` never runs.
4. `_brake_on[sym]` stays True indefinitely.

**This is a permanent deadlock**: the only escape route requires a closed trade, which the brake itself prevents. The 30-day rolling window cannot expire the brake — expiry only happens inside `_update_drawdown_brake` (line 381 `while deque[0][0] < cutoff: popleft()`), which is never called when brake is ON.

### Symbol-specific behavior

- **BCH**: brake first engaged at IS trade 28 (2022-11-28), dd_30d crossed T=10.0 threshold. Disengaged at trade 29 (2023-01-12) when dd_30d recovered to ≤ recovery=5.0. Then **re-engaged at trade 81 — the very last IS trade (2024-12-21, dd_30d=10.58)** — and stays on. No subsequent BCH trades close in OOS to update state.
- **LDO**: brake engaged on the losing streak that finishes LDO's 8 IS trades (~2025-02-08, dd_30d=10.22). Stays on for ~44 days before OOS-start. No LDO trades close in OOS.
- **TRX**: brake engaged briefly at trade 28 (2022-11-28, same period as BCH — same systematic market drawdown signal), disengaged shortly after, remained OFF through IS-end (dd_30d=6.14 at last IS trade 2023-02-12, 771 days before OOS start). TRX brake state DID NOT cause TRX OOS=0. **TRX OOS=0 from INDEPENDENT cause**: Optuna threshold at single-seed n_trials=35 produced no TRX OOS-viable signals (consistent with TRX's 17 IS trades all closing before 2023-02, 2.5 years before OOS; model learned a signal that fires only in very specific IS-era conditions). 18 TRX OOS signals reached the BTC trend filter and were killed.

### Carver canonical formulation does not anticipate this failure mode

Carver *Leveraged Trading* Ch. 11 applies to live trading systems where trades ALWAYS eventually close (even if delayed by adverse market), so the state machine always receives updates. In a backtest where blocked signals produce no trades, the state machine can freeze permanently. The QR brief Section 2.4 acknowledged "Optuna trajectory shifts when the brake is active. The ORACLE counterfactual applies the brake to TRUE trades; at backtest time the model sees fewer trades and the per-symbol-fit Optuna draws may shift" anticipating a 30-50% deviation. It did NOT anticipate a 100% OOS signal blockage because the deadlock mechanism was not modeled in the EDA's counterfactual function.

This is a **brief DESIGN DEFECT (specification incompleteness)**, NOT an implementation defect. The implementation in `src/crypto_trade/strategies/ml/risk_v2.py` is byte-for-byte correct as specified (Critic Check 8 FAIL on Hypothesis-Implementation Alignment cites BRIEF DEFECT, not implementation). The 5 adversarial tests all PASS. The state machine logic (engage at dd_30d ≥ T, disengage at dd_30d ≤ recovery, 30-day window via deque expiry) matches Section 3.4 pseudocode exactly.

### Engineering observations for any future drawdown-brake redesign

(Recorded from Engineering report SHA `b376d93` — strictly factual observations, NOT a commitment to redesign at /055):

- A time-based check (e.g., "if 30 days have elapsed since last trade and no trade has closed, reset peak to current cum_wpnl") would break the deadlock. Implementable but requires different API: `get_signal` would need current open_time to compare against last recorded close_time. Constitutes a new brief, new tests, new EDA.
- A simpler alternative: brake disengage condition could be "30 calendar days have elapsed since brake engagement AND dd_30d has not increased." Avoids closed-trade dependency entirely.
- Both alternatives require new EDA simulation modeling the deadlock correctly — ORACLE approach is INSUFFICIENT for deadlock analysis.

Per `feedback_no_cheating.md`, a re-run after a fix is FORBIDDEN in the same iteration. /054 verdict is final.

## ORACLE EDA Methodology Defect — STATELESS vs STATEFUL Classification

### What ORACLE EDA does

QR EDA at SHA `e565b82` computed brake counterfactual on /053 trade roster: apply brake AS FILTER to existing trades, mark trades as SKIPPED based on state machine, compute counterfactual Sharpe. In ORACLE mode, every future trade exists in the roster regardless of brake state.

### Why ORACLE was INVALID for /054

ORACLE methodology cannot model state-dependent feedback loops between gates and trade generation. For STATELESS gates (ADX, vol scaling, BTC trend), ORACLE is VALID — those gates make per-bar decisions independent of prior gate-decision state. For STATEFUL gates (drawdown brake, per-symbol cap with rolling window, cooldown timers, any gate where signal-emission updates persistent state), **ORACLE is INVALID without explicit closed-loop simulation**.

The specific oversight in /054 EDA: it assumed that after 30 calendar days without a trade, the rolling window would expire the old peak entries and the brake would disengage. This would be correct if `_update_drawdown_brake` were called on a time-based schedule. But the implementation calls it ONLY on closed trades. There is no time-based expiry path outside of trade closures.

### NEW memory rule codification

**`feedback_v3_oracle_eda_validity.md` CREATED 2026-05-11** (orchestrator-applied at Critic FINAL SHA `db1551b`). Codifies:

**STATELESS gates** (gate decision independent of prior gate-decision state): ADX threshold, vol scaling, BTC trend filter, OOD z-score gate, fixed confidence thresholds, low-vol kill, per-symbol cap (if symbol-level fixed not rolling-window-stateful). → ORACLE EDA on prior trade roster IS VALID.

**STATEFUL gates** (gate decision depends on persistent state updated by prior gate-decision outcomes): drawdown brake (rolling-window peak tracker), cooldown timers blocking N signals after SL, streak counters (R1-style consecutive-SL armed state), per-symbol exposure caps with rolling positions, any gate where decision to BLOCK signal prevents that signal's outcome from updating subsequent state. → ORACLE EDA INVALID. Requires:
- **(a)** closed-loop simulator that models the feedback (e.g., once gate engages, simulate "no trades for N days, gate state frozen") OR
- **(b)** formal proof in brief Section 2 that the gate state cannot enter a stuck-state

**Brief Section 2 requirement for STATEFUL axes** (new rule mandate): include a "Deadlock Analysis" subsection with:
1. Enumeration of all gate states reachable
2. Proof that NO state has zero escape probability under realistic trade flow
3. Either time-based escape mechanism documented, OR independent-of-trades escape mechanism, OR closed-loop simulator results showing OOS trade count > floor under all entry-state scenarios

**Phase 5.5 gate enforcement**: QE must verify brief Section 2 includes Deadlock Analysis for STATEFUL axes. Missing deadlock analysis = BLOCK at gate.

### Examples of common gate patterns classified

- Rolling-window peak tracker (iter-v3/054 brake) — UNSAFE without time-based escape (deadlock-class)
- Cooldown after stop-loss (R1) — SAFE because cooldown counter decrements per-bar independent of trade outcomes
- Streak counter (consecutive-SL) — SAFE because resets on first non-SL outcome
- Exposure cap (current position count) — SAFE because position close updates state
- Drawdown brake with time-based reset (hypothetical "clear after 30 days regardless of trade flow") — SAFE because escape independent of trades
- Drawdown brake without time-based reset (iter-v3/054 actual implementation) — UNSAFE; deadlock-class

This rule applies to ALL future axes (cycle 4 #5+, cycle 5+). It does NOT retroactively invalidate prior axis decisions per `feedback_no_cheating.md` post-hoc renegotiation discipline. iter-v3/054 verdict remains EXPLORATION-NEGATIVE PATH C-clean per Section 8 LOCKED criteria.

## CPCV-Invariance Pattern Extends Beyond 15th-Slot SWAP Family

The /053 closeout introduced the "15th-slot SWAP family STRUCTURALLY EXHAUSTED" framing based on 3-iteration CPCV identity. iter-v3/054 was DESIGNED to be the EXIT axis — it added a RISK GATE primitive 11 with ZERO change to the feature-column stack vs base 14. **Yet CPCV produced bit-identical 29/45 positive, +0.3351 median, -0.243 Q25 to 4 decimals.**

| CPCV statistic | iter-v3/051 | iter-v3/052 | iter-v3/053 | **iter-v3/054** | Pattern |
|---|---:|---:|---:|---:|---|
| 15th-slot feature | fracdiff_d05_close | regime_momentum_signed_3d | hurst_drift_50_200 | **NONE (reverted 15→14)** | Different content each iteration |
| Risk-gate addition | NONE | NONE | NONE | **Primitive 11 (drawdown brake)** | NEW axis at /054 |
| Paths positive (of 45) | 29 | 29 | 29 | **29** | INVARIANT |
| Median path Sharpe | +0.335 | +0.3351 | +0.3351 | **+0.3351** | INVARIANT to 4 decimals |
| Q25 path Sharpe | -0.243 | -0.243 | -0.243 | **-0.243** | INVARIANT to 4 decimals |
| Q75 path Sharpe | +0.884 | +0.838 | +0.838 | **+0.838** | INVARIANT from /052 onward |
| PBO (per-cell mean) | 0.1168 | 0.1090 | 0.1377 | **0.1243** | minor oscillation |
| n_eff | 19 | 19 | 19 | **19** | INVARIANT (cycle-4 constant) |

### Updated structural finding (supersedes /053's 15th-slot SWAP exhaustion framing)

**Single-seed CPCV stats at (3-sym universe, n_trials=35, ENSEMBLE_SIZE=5, base 14 features, seed=42) are DETERMINISTIC regardless of:**

- 15th-slot feature additions (/051, /052, /053)
- 15th-slot feature drops (/054 reverts 15 → 14)
- Risk-gate primitives added downstream of the model (/054 primitive 11)

The CPCV path-Sharpe distribution is anchored by the (base feature stack × walk-forward schedule × model architecture × ENSEMBLE_SIZE × seed) tuple, INVARIANT to 15th-slot content OR risk-gate additions. **4-iteration invariance is systematic evidence (not coincidence) requiring structural cycle-5 change.**

### Cycle-5 axes must change one of

To shift the CPCV path distribution at cycle-5 (iter-v3/062-/071), an axis must change at least ONE of:

1. **Base 14-feature stack** (replace a base feature, not add 15th-slot)
2. **Universe** (3-sym → 4+; e.g. expansion BCH+LDO+TRX → BCH+LDO+TRX+SOL or similar)
3. **Model architecture** (LightGBM → CatBoost; deferred A3 from /054 brief 4-axis ranking)
4. **n_trials** (35 → higher, addresses n_eff=19 saturation simultaneously)
5. **ENSEMBLE_SIZE** (5 → higher; affects inner ensemble variance)

**Methodology-only axes (A2 DSR reformulation) will NOT shift CPCV distribution** — useful for gate-interpretation, cannot exit cycle-4 deterministic regime. But A2 IS still PROMOTED to /055 per separate Critic recommendation because it addresses the cycle-4 DSR=0 structural finding without consuming wall-clock budget on a backtest.

### PATH E pre-registration was instrumental

Per Critic FINAL `db1551b` Adversarial Finding #4: Credit to QR for executing /053 Critic recommendation #3 cleanly. The PATH E (CPCV-INVARIANT NULL) pre-registration in brief Section 8 made the 4-iteration invariance observable as a systematic finding rather than dismissible coincidence. **Without PATH E pre-registration, CPCV invariance at /054 could have been overlooked given the dramatic OOS=0 result distracting from the CPCV-level diagnostic.**

## n_eff = 19 Cycle-4 Structural Constant — DSR = 0 Inevitable

n_effective_trials = 19 across /051/052/053/054 (4 iterations, integer-identical). The 14-feature stack's effective independent trial count saturates at ~19 well below the naive n_trials count of 525. This is the **CYCLE-4 STRUCTURAL CONSTANT.**

DSR = 0 at single-seed EXPLORATION is **mechanically inevitable**:

```
E[max_SR] ≈ Z_alpha × sqrt(2 × ln(n_eff))
         ≈ 1.645 × sqrt(2 × ln(19))
         ≈ 1.645 × 2.43
         ≈ 4.00
```

Realized OOS daily Sharpe of ~1.4 (cycle-4 representative) does not clear E[max_SR] ≈ 4.00 threshold. DSR mechanically lands at exactly 0.0 (lower-bound clamp). At /054 specifically, realized OOS daily Sharpe = 0.0 (zero trades), trivially below threshold.

Per `feedback_v3_dsr_mode_artifact.md`: EXPLORATION-mode DSR is INFORMATIONAL ONLY; CONFIRMATION-mode DSR uses n_trials=1500 (E[max_SR] = 3.37) which still doesn't clear annualized 4.0. **Cycle 4 CONFIRMATION at iter-v3/061 will need to either (a) increase n_trials to ≥ 100 per cell, OR (b) propose alternative multiple-testing gate** per Critic FINAL `db1551b` Adversarial Finding #5. **A2 DSR gate reformulation is now URGENT** — promoted to /055 axis per Critic FINAL Recommendation #3.

## Memory Rule Updates

### NEW (orchestrator-applied at Critic FINAL SHA `db1551b`)

- **`feedback_v3_oracle_eda_validity.md` CREATED 2026-05-11** — STATELESS vs STATEFUL gate classification + brief Section 2 Deadlock Analysis requirement for STATEFUL axes + Phase 5.5 gate enforcement. Codifies that STATEFUL axes require closed-loop simulator OR formal deadlock-impossibility proof.

### Carried forward / referenced

- **`feedback_v3_lr_pf_methodology.md` UNCHANGED** at /054 — created at /053 closeout; applies to feature axes not risk primitives.
- **`feedback_v3_engineered_features_dont_stack.md` UNCHANGED** — not invoked at /054 (no feature stacking).
- **`feedback_v3_axis_selection_quant_discipline.md` fired at /054** — QR EDA at SHA `e565b82` produced numerical 4-axis ranking BEFORE locking brief; orchestrator pick PRELIMINARILY SUPPORTED. Section 10.2 in brief documents 4-axis ranking.
- **`feedback_v3_strict_10_to_1_cadence.md` advances 4/10** for cycle 4. iter-v3/054 is cycle 4 #4; 6 more EXPLORATIONs needed before iter-v3/061 CONFIRMATION.
- **`feedback_v3_dsr_mode_artifact.md` UNCHANGED** — DSR=0.0 at /054 is INFORMATIONAL ONLY per established interpretation. n_eff=19 cycle-4 STRUCTURAL CONSTANT confirmed at 4 iterations.
- **`feedback_v3_concentration_is_signal.md` REFERENCED** — per-symbol drawdown brake explicitly permitted at /020 closure as one of 4 orthogonal mechanisms (vs proportional scaling CLOSED). /054 confirms the mechanism is permitted in PRINCIPLE; the /054 IMPLEMENTATION's deadlock failure is independent of the orthogonality permission. A redesigned brake with time-based escape would still be a permitted axis.
- **`feedback_v3_structural_over_knob_exploration.md` REFERENCED** — NEW risk primitive ranked Category 4 priority. /054 axis was Category-4 compliant; the failure is methodological (ORACLE EDA for STATEFUL gate), not categorical.
- **`feedback_risk_mitigation_design.md` REFERENCED** — brief Section 5 included R11 with IS-calibrated thresholds and simulated historical effect; mandate technically satisfied but the simulated effect was based on invalid ORACLE methodology.
- **`feedback_no_cheating.md` ENFORCED** — re-run after fix is FORBIDDEN; /054 verdict is final.
- **`feedback_axis_saturation_predictor.md` FIRED** — brief Section 4.4 included behavioral effect predictor (predicted 7 brake fires; observed 881 aggregate / BCH+LDO permanent main-run). Predicted upper bound 15 fires; observed >> 25 main-run. Saturation falsifier FIRES per brief Section 8.

## Cycle 4 Cadence: 4/10 EXPLORATIONs Advanced

Per `feedback_v3_strict_10_to_1_cadence.md`:

- **Cycle 4 #1 of 10 = iter-v3/051** (fracdiff_d05_close ADD UNIVERSAL; EXPLORATION-NULL-RESULT PATH D; PARKED)
- **Cycle 4 #2 of 10 = iter-v3/052** (regime_momentum_signed_3d SWAP UNIVERSAL; EXPLORATION-NEGATIVE PATH C-suspicious; CLOSED)
- **Cycle 4 #3 of 10 = iter-v3/053** (hurst_drift_50_200 SWAP UNIVERSAL; EXPLORATION-NULL-RESULT PATH D; PARKED — LR-PF methodology refined)
- **Cycle 4 #4 of 10 = iter-v3/054** (per-symbol drawdown brake NEW RiskV2 primitive 11 + REVERT hurst_drift; **EXPLORATION-NEGATIVE PATH C-clean primary + PATH C-suspicious + Saturation + PATH E all co-fire**; drawdown-brake axis CLOSED + entire "NEW risk primitive" axis family CLOSED at single-seed EXPLORATION scope; **ORACLE EDA methodology defect** confirmed for STATEFUL primitives; new memory rule `feedback_v3_oracle_eda_validity.md` CREATED)
- **Cycle 4 #5 of 10 = iter-v3/055** (TBD — A2 DSR gate reformulation PROMOTED per Critic FINAL Recommendation #3)
- **Cycle 4 #6-#10 = iter-v3/056-iter-v3/060** (TBD)
- **Cycle 4 CONFIRMATION at iter-v3/061** (SEPARATE single-seed iter-v3/060 first; do NOT collapse the 10th EXPLORATION into CONFIRMATION per `feedback_v3_strict_10_to_1_cadence.md`)
- **6 more EXPLORATIONs remain** before cycle 4 CONFIRMATION: iter-v3/055 through iter-v3/060
- **Cadence wall-clock caps**: EXPLORATION 2h, CONFIRMATION 6h. iter-v3/054 actual: 1.26h backtest within cap.

**Cycle 4 hypothesis status** (carry-forward from /050 closeout): "lift IS Sharpe to ≥ +0.5101 (BASELINE_V3.md update gate floor) while preserving OOS Sharpe ≥ +0.5053 via UNIVERSAL axes (per-symbol customizations rejected at bundle level)." iter-v3/054 result: IS +0.4581 BELOW +0.5101 floor by -0.0520; OOS +0.0000 BELOW +0.5053 floor by -0.5053. **PATH C-clean NEGATIVE classification means no axis advance.** The cycle 4 hypothesis is NOT YET satisfied via clean PROMISING; 6 EXPLORATIONs remaining. **Cycle 4 cumulative score: 0 PROMISING-clean / 1 PROMISING-INERT (N/A risk primitives) / 2 NULL-RESULT / 2 NEGATIVE / 0 axes-advance after 4 of 10 EXPLORATIONs.** The structural finding (CPCV-determinism + n_eff=19) is the primary cycle-4 contribution so far, NOT axis advancement.

## iter-v3/055 PROMOTED Axis

Per Critic FINAL `db1551b` Recommendation #3 + brief Section 10.2 4-axis ranking + remaining-axis filter post-/054 PATH C-clean closure of A1:

### PROMOTED: A2 — DSR gate reformulation (methodology-only)

**Rationale (5-criterion compliance):**
- C1 ≤2h impl: YES (methodology-only; ~1.5h DSR computation modification + Critic gate update + reporting)
- C2 escape slot-15: YES (methodology-only axis; doesn't touch feature stack or CPCV computation)
- C3 addresses cycle-4 structural finding: HIGH (DSR=0 structural at n_eff=19 cycle-4 CONSTANT; reformulation directly addresses /054 Critic Adversarial Finding #5)
- C4 orthogonal to CLOSED precedents: YES (DSR formulation is methodology-axis; no closed precedent for it)
- C5 zero revert cost: YES (DSR reformulation can be feature-flagged; existing absolute-threshold DSR remains computable in parallel)

**Mechanism:** Replace DSR > 0.95 absolute threshold with **relative DSR** (rank-percentile of CPCV path Sharpes against expected null distribution). Fixes the structural DSR=0 artifact at EXPLORATION-spec n_trials=525 and n_eff=19 cycle-4 CONSTANT. Per `feedback_v3_dsr_mode_artifact.md`: EXPLORATION-mode DSR is INFORMATIONAL ONLY; CONFIRMATION-mode DSR uses n_trials=1500 (E[max_SR]=3.37) which still doesn't clear annualized 4.0. Reformulated DSR could enable IS Sharpe +0.50 to clear MERGE gate at iter-v3/061 CONFIRMATION.

**Implementation cost:** ~1.5h (DSR computation modification + Critic gate update); analysis-only — no wall-clock budget consumption on backtest.

**Aligns with cycle 4 hypothesis:** DSR reformulation could enable iter-v3/061 CONFIRMATION to PASS Gate 6 (PSR > 0.95) and revised Gate 3 (DSR reformulated) without requiring base-stack changes. Critical for cycle-4 CONFIRMATION viability given 4 consecutive iterations confirming n_eff=19 saturation.

**Note: A2 does NOT shift CPCV distribution** — useful for gate-interpretation but cannot exit cycle-4 deterministic regime. Cycle-5 (iter-v3/062-/071) still requires structural change to base feature stack / universe / model arch / n_trials / ENSEMBLE_SIZE per /054 updated structural finding.

### SECONDARY: A4 — Base-stack feature reordering (requires fresh EDA)

**Rationale:** Per /053 closeout HIGH-priority #4 + /054 brief Section 10.2 4-axis ranking (VIABLE-SECONDARY).

**Mechanism:** Identify mid-table feature in base 14 (e.g. rank 8-12 at /054 last_month_portfolio.csv) and replace with genuinely orthogonal Category 1 feature (|IC| < 0.50 against ALL existing 14 base features). Directly tests CPCV path distribution response to non-slot-15 changes — would be the **first cycle-4 axis with potential to shift CPCV distribution**.

**Implementation cost:** 2h+ (EDA + adversarial tests + backtest). Requires fresh EDA on which base-14 feature is marginal at /054 + orthogonal candidate selection.

**Why SECONDARY not PRIMARY:** A2 is methodology-only ≤2h with zero CPCV-shift risk and zero deadlock risk; A4 requires fresh EDA which extends QR Phase 5 budget. A4 is RECOMMENDED for iter-v3/056 or /057 if A2 lands cleanly at /055.

### CLOSED axes (after /054)

- ~~A1 Per-symbol drawdown brake~~ — CLOSED at /054 (PATH C-clean + PATH E + Saturation falsifier); entire "NEW risk primitive" axis family CLOSED at single-seed EXPLORATION scope until structural change to CPCV anchoring
- ~~A3 CatBoost head-to-head~~ — DEFER multi-iter arc (7-10h impl exceeds 2h cap)
- ~~15th-slot SWAP family~~ — CLOSED at /053 (CPCV-INVARIANT NULL pattern; 4-iteration evidence)
- ~~LDO removal investigation~~ — DEFERRED to multi-seed CONFIRMATION; pre-falsified at /052 EDA SHA `0a10581`
- ~~ADX gate tuning~~ — CLOSED at /015 (`feedback_v3_adx_axis_asymmetric_v3.md`)
- ~~Per-symbol PnL caps~~ — CLOSED at /020 (`feedback_v3_concentration_is_signal.md`)
- ~~Per-symbol ATR multipliers~~ — CLOSED at /045-/050 (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`)

## Architectural Decisions

- **BASELINE_V3.md UNCHANGED at iter-v3/028** (+0.5101 IS / +0.5053 OOS; SHA `b0576df`). EXPLORATION; no MERGE gate evaluation.
- **iter-v3/028 architecture PRESERVED** as cycle 4 baseline (V3_MODELS = 3-sym; V3_ATR_MULTIPLIERS_PER_SYMBOL = {}; block_long_for = (); REQUIRED_GAP = 66).
- **V3_FEATURE_COLUMNS_TOP_N reverted to 14 features at /054 setup** (DROP hurst_drift_50_200 per /053 PATH D PARK action). compute_hurst_drift_50_200 retained as dead code in `engineered_v3.py` (zero revert cost). 5 adversarial tests in `test_hurst_drift_50_200_universal.py` retained as dead-code coverage.
- **Primitive 11 (per-symbol drawdown brake) PARKED at /054 closeout** (not REVERTED). RiskV2Config fields (`enable_per_symbol_drawdown_brake`, `drawdown_brake_threshold_wpnl`, `drawdown_brake_recovery_wpnl`, `drawdown_brake_window_days`) retained as disable-by-default (backward-compatible). 5 adversarial tests in `tests/strategies/ml/test_risk_v2_drawdown_brake.py` retained as dead-code coverage. State machine implementation retained as zero-revert-cost dead code. **Mechanism is deadlock-class as currently designed**; future redesign with time-based escape would constitute a NEW axis at later iteration (not /055).
- **regime_momentum_signed_3d UNIVERSAL axis CLOSED at /052** (PATH C-suspicious). Compute function retained as dead-code dispatch UNCHANGED at /054.
- **regime_momentum_signed_5d PRESERVED** in V3_FEATURE_COLUMNS_TOP_N (iter-v3/028 edge ingredient). At /054 portfolio importance rank 14/14 — Optuna's IS-sample-adapted ranking with brake-filtered trades; family proven status preserved per `feedback_v3_engineered_features_proven.md`.
- **fracdiff_d05_close PARKED at /051** UNCHANGED.
- **hurst_drift_50_200 PARKED at /053** UNCHANGED.
- **Per-symbol architecture (V3_FEATURES_PER_SYMBOL + V3_ATR_MULTIPLIERS_PER_SYMBOL) PRESERVED as code infrastructure** — validated at multi-seed (/050); no architectural defects.
- **Primitive 10 (`block_long_for`) wired value `()`** UNCHANGED from /053. Mechanism + tests + GateStats counter PRESERVED as code.
- **LDO removal axis DEFERRED** to multi-seed CONFIRMATION (iter-v3/061+) where single-seed lottery artifacts dissolve. Returning to LDO removal at /055 requires fresh /054-trade-roster EDA (which is degenerate at /054 given IS-only 8 LDO trades + OOS=0).
- **`--clean-oof` guardrail RETAINED** (SHA `6a216b5`). Behavior correct at /054.
- **NO TAG ISSUED.** EXPLORATION; only CONFIRMATION-MERGE iterations get `v0.v3-NNN` tags.

## See Also

- `briefs-v3/iteration_v3-054/research_brief.md` — Phase 5 brief (SHA `78b7d00`; per-symbol drawdown brake; 6-path criteria with PATH E pre-registered per /053 Critic Recommendation #3)
- `briefs-v3/iteration_v3-054/phase5p5_gate.md` — Phase 5.5 gate PASS (SHA `7ad6389`)
- `briefs-v3/iteration_v3-054/engineering_report.md` — Phase 6/7 engineering report (SHA `b376d93`; PATH C-clean + PATH C-suspicious + Saturation + PATH E classification; deadlock root cause)
- `briefs-v3/iteration_v3-054/review.md` — Phase 7.5 Critic FINAL (SHA `db1551b`; EXPLORATION-NEGATIVE PATH C-clean primary; CPCV-invariance extends beyond 15th-slot; ORACLE EDA methodology defect; new memory rule recommendation)
- `reports-v3/iteration_v3-054/comparison.csv` — primary numerical results (single-seed; OOS metrics all 0.0)
- `reports-v3/iteration_v3-054/seed_summary.json` — per-seed data (1 outer seed; btc_killed=18 OOS)
- `reports-v3/iteration_v3-054/dsr.json` — DSR/PBO/PSR/n_eff (n_trials=525 EXPLORATION-spec; PSR=0.0 zero-OOS collapse)
- `reports-v3/iteration_v3-054/per_cell_pbo.csv` — per-cell PBO (mean 0.1243)
- `reports-v3/iteration_v3-054/cpcv_paths.csv` — CPCV path data (45 paths; bit-identical to /051/052/053 on median + Q25 + positive-count)
- `reports-v3/iteration_v3-054/in_sample/per_symbol.csv` — IS per-symbol PnL attribution (BCH +101.80%, TRX +33.38%, LDO -35.18%)
- `reports-v3/iteration_v3-054/in_sample/model_importance_last_month_*.csv` — feature importance per symbol + portfolio (14 features; regime_momentum_signed_5d rank 14/14 portfolio at brake-filtered IS sample)
- `reports-v3/iteration_v3-054/in_sample/trades.csv` — IS trade roster (106 trades; brake-filtered)
- **NO `reports-v3/iteration_v3-054/out_of_sample/` directory** — OOS trades=0 (no CSV produced)
- `analysis/iteration_v3-054/cycle4_axis_ranking_eda.py` + `per_symbol_drawdown_brake_eda.py` + `synthesis.md` + `candidate_axes_ranking.md` + `brake_synthesis.md` (SHA `e565b82`) — QR EDA with 4-axis ranking + ORACLE counterfactual on /053 trade roster (predicted 7 brake fires; INVALID ORACLE methodology for STATEFUL primitive)
- `src/crypto_trade/strategies/ml/risk_v2.py` (lines 140-163 RiskV2Config; 309-315 signal-kill; 325-344 record_trade_result; 346-396 state machine) — primitive 11 implementation
- `src/crypto_trade/features_v3/__init__.py` — V3_FEATURE_COLUMNS_TOP_N (14 elements at /054; DROP hurst_drift_50_200)
- `run_baseline_v3.py` — ITERATION_LABEL "v3-054"; V3_MODELS 3-sym; block_long_for=(); RiskV2Config with brake fields wired
- `tests/strategies/ml/test_risk_v2_drawdown_brake.py` — 5 adversarial tests (PASS at /054; retained as dead-code coverage at /055 setup)
- `tests/features_v3/test_hurst_drift_50_200_universal.py` — 5 adversarial tests (PASS; dead-code coverage at /054)
- `tests/features_v3/test_regime_momentum_signed_3d_universal.py` — 5 adversarial tests (PASS; dead-code coverage)
- `tests/features_v3/test_fracdiff_d05_universal.py` — 5 adversarial tests (PASS; dead-code coverage)
- `BASELINE_V3.md` — UNCHANGED at iter-v3/028 (+0.5101 IS / +0.5053 OOS; SHA `b0576df`)
- Setup commit SHA `c21ce7e` — RiskV2Config primitive 11 fields + state machine + V3_FEATURE_COLUMNS_TOP_N revert 15 → 14
- Gate commit SHA `7ad6389` — Phase 5.5 gate
- Engineering report commit SHA `b376d93`
- Critic FINAL commit SHA `db1551b`
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_oracle_eda_validity.md` — **NEW (2026-05-11; orchestrator-applied at /054 Critic FINAL `db1551b`)** — STATELESS vs STATEFUL gate classification; STATEFUL axes require closed-loop simulator OR deadlock-impossibility proof; Phase 5.5 gate enforcement
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_lr_pf_methodology.md` — UNCHANGED at /054 (created at /053)
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_engineered_features_dont_stack.md` — UNCHANGED at /054 (not invoked; no feature stacking)
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_axis_selection_quant_discipline.md` — fired at /054 EDA pre-falsifier disclosure
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_concentration_is_signal.md` — per-symbol drawdown brake permitted as orthogonal mechanism; /054 confirms permission in principle, deadlock failure is independent
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_structural_over_knob_exploration.md` — NEW risk primitive ranked Category 4 priority; /054 axis was compliant; failure methodological not categorical
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_strict_10_to_1_cadence.md` — cycle 4 cadence 4/10 advanced
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_dsr_mode_artifact.md` — DSR EXPLORATION-INFORMATIONAL interpretation; n_eff=19 cycle-4 STRUCTURAL CONSTANT confirmed at 4 iterations
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_risk_mitigation_design.md` — Risk Mitigation Section 5 requirements; /054 brief technically satisfied with R11; simulated effect was based on invalid ORACLE methodology
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_no_cheating.md` — ENFORCED; re-run after fix FORBIDDEN
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_axis_saturation_predictor.md` — FIRED at /054 (predicted 7 brake fires; observed 881 aggregate / BCH+LDO permanent main-run)
- `diary-v3/iteration_v3-053.md` — immediate predecessor (EXPLORATION-NULL-RESULT PATH D; LR-PF methodology; 15th-slot SWAP family exhausted; PATH E pre-registration mandate)
- `diary-v3/iteration_v3-052.md` — cycle 4 #2 of 10 (EXPLORATION-NEGATIVE PATH C-suspicious; CLOSED)
- `diary-v3/iteration_v3-051.md` — cycle 4 #1 of 10 (EXPLORATION-NULL-RESULT PATH D; fracdiff PARKED)
- `diary-v3/iteration_v3-050.md` — cycle 3 CONFIRMATION-NO-MERGE-revert closeout
- `diary-v3/iteration_v3-028.md` — first CONFIRMATION-MERGE (BASELINE_V3.md anchor; regime_momentum_signed_5d edge ingredient)
- `briefs-v3/exploration_catalog.md` — iter-v3/054 catalog row at diary closure (EXPLORATION-NEGATIVE PATH C-clean + PATH E co-fire verdict; drawdown-brake axis CLOSED + entire "NEW risk primitive" axis family CLOSED at single-seed EXPLORATION scope; ORACLE EDA methodology defect confirmed for STATEFUL primitives; new memory rule `feedback_v3_oracle_eda_validity.md` CREATED; CPCV-invariance pattern extends beyond 15th-slot family; iter-v3/055 PROMOTED axis A2 DSR gate reformulation methodology-only ≤2h)
