# iter-v3/054 — EDA Synthesis: 5-criterion ranking of 4 candidate axes

Per Critic FINAL of iter-v3/053 (SHA `c056354`) Recommendation #1: the
15th-slot SWAP family is STRUCTURALLY EXHAUSTED at single-seed EXPLORATION.
CPCV positive-path count CONSTANT 29/45, median path Sharpe IDENTICAL
+0.3351, Q25 IDENTICAL -0.243 across iter-v3/051/052/053. iter-v3/054 MUST
exit the 15th-slot family.

## Ranking summary

| Axis | C1 ≤ 2h | C2 escape | C3 cycle-4 | C4 orthog | C5 revert | Verdict |
|---|---|---|---|---|---|---|
| A1: Per-symbol drawdown brake | YES (~1.5h impl + 1.25h backtest fits 3h split) | YES (NEW risk primitive, not feature) | HIGH (addresses LDO drag -13.96 to -17.44 across /051-/053) | YES (loss-stop semantics differs from prop-scaling CLOSED at /020) | YES (RiskV2Config flag toggle; zero feature-stack change) | **RECOMMENDED** |
| A2: DSR gate reformulation | YES (~1h analysis + 1h code + 0.5h test = well within cap) | YES (methodology axis, not feature) | HIGH (DSR=0 structural at n_eff=19 cycle-4 constant) | YES (gate reformulation doesn't touch model or features) | YES (revert one validation_v3.py function) | **RECOMMENDED-PARALLEL (can pair with A1)** |
| A3: CatBoost head-to-head | NO (7-10h full impl; 1.5-2h spike only) | YES (NEW model arch) | MEDIUM (cycle-4 finding is CPCV-invariance; CatBoost MAY help) | PARTIAL (iter-v3/016 XGBoost head-to-head NEGATIVE-clean precedent) | YES (--model flag) | **DEFER to multi-EXPLORATION-CONFIRMATION arc** |
| A4: Base-stack feature reordering | PARTIAL (depends on orthogonal candidate selection ease) | YES (replaces non-slot-15 base feature) | HIGH (directly tests CPCV-invariance hypothesis) | PARTIAL (any base-feature change is structurally adjacent to slot-15 SWAP) | YES (V3_FEATURE_COLUMNS_TOP_N change) | **VIABLE-SECONDARY (requires fresh EDA on orthogonal candidate)** |

## Recommended axis: A1 (Per-symbol drawdown brake)

**Reasoning**:

1. **C1 — 2h cap**: 1.5h implementation (~150 LOC: RiskV2Config fields, RiskV2Wrapper state machine, GateStats counter, 5 adversarial tests) + 1.25h backtest. Fits 3h split with hand-off (orchestrator can dispatch QE for implementation; QR resumes for Phase 5.5 gate).

2. **C2 — escape slot-15**: NEW risk primitive; orthogonal to feature-column axes that have been thrashing /051/052/053. CPCV path distribution WILL shift if the brake fires (trades change → CPCV split-by-block changes → median path Sharpe changes).

3. **C3 — cycle-4 finding**: LDO drag is the structural finding of cycle 4. LDO OOS weighted_pnl has ranged -13.96 to -17.44 across /051/052/053 with no 15th-slot axis touching it. A per-symbol drawdown brake is the canonical mechanism for stopping a symbol that has gone into structural negative-edge regime.

4. **C4 — orthogonal**: Per `feedback_v3_concentration_is_signal.md`, per-symbol PnL share caps are CLOSED (iter-v3/020: lottery-REWARD source). Drawdown brake is LOSS-STOP semantics, not proportional scaling. The memory rule explicitly enumerates 4 permitted orthogonal mechanisms — per-symbol drawdown brake is one (Carver *Leveraged Trading* Ch. 11 canonical formulation).

5. **C5 — easy revert**: RiskV2Config field `enable_per_symbol_drawdown_brake`. Set False → original /053 behavior bit-identical.

## Parallel-track candidate: A2 (DSR gate reformulation)

A2 is RECOMMENDED-PARALLEL — methodology-only axis, analysis-only, zero wall-clock backtest budget. If A1 takes 3h split, A2 can also be implemented in parallel within the same /054 iteration. However, this iteration is committed to ONE axis per `feedback_v3_axis_selection_quant_discipline.md` (single-axis EXPLORATION).

A2 is DEFERRED to /055-/060 (cycle 4 #5-#10) as a SEPARATE methodology axis. DSR reformulation does NOT shift the CPCV path distribution, so it is unlikely to fire PATH E (CPCV-INVARIANT NULL); but it ALSO does not produce a new Sharpe number — it changes the gate interpretation, not the strategy.

## Deferred: A3 (CatBoost head-to-head)

A3 fails C1 (1.5-2h spike only; full impl 7-10h). The methodology-only spike would provide preliminary evidence but does NOT clear MERGE gates (no walk-forward, no Optuna, no ensemble, no CPCV).

A3 is DEFERRED to a multi-EXPLORATION-CONFIRMATION arc (e.g. spike at /054 + full backtest at /061 CONFIRMATION pre-bundling).

## Viable secondary: A4 (Base-stack feature reordering)

A4 is VIABLE-SECONDARY but requires fresh EDA on orthogonal candidate selection. The /053 base-stack importance ranking (see `base_stack_importance_ranking.csv`) provides candidate marginal features, but selecting the replacement Category 1 feature with `|IC| < 0.50` against ALL 14 base features requires additional EDA passes (1h+).

If A1 fires NULL at /054, A4 becomes the natural /055 axis with a 2-iteration carry-over plan.

## PATH E (CPCV-INVARIANT NULL) — pre-registration

Per Critic /053 recommendation #3: brief Section 8 MUST pre-register **PATH E**:

> PATH E (CPCV-INVARIANT NULL): CPCV positive-path count, median path Sharpe, > and Q25 path Sharpe all match /051/052/053 to 2 decimals. If PATH E fires > alongside any other path, the axis is classified as 'failed to escape 15th-slot > saturation' and that axis family CLOSED at /054.

For per-symbol drawdown brake, PATH E firing would mean: even with a NEW risk primitive, the CPCV path distribution didn't move. This would imply the LDO trades that the brake skipped were already not driving the path-Sharpe variation — a SURPRISING but interpretable null. Per A1's mechanism, the brake SHOULD shift the path distribution (LDO accounts for ~20% of OOS trades), so PATH E firing would be unexpected.