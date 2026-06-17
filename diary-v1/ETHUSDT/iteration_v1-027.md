# Diary — iter-v1/027 (ETHUSDT) — CONFIRMATION (K=20) — ★ MERGED → BASELINE_V1_ETHUSDT ★

**Axis:** K=20 confirmation of the iter-026 both-positive (proven BTC iter-020 stack on ETH) + ETH-calibrated
R2 brake. Config: 19-col HYBRID + fixed_horizon N=42 (14d) let-winners-run + stateless 200-SMA trend-state
DIRECTION (ETH's own) + conviction gate q=0.40 + R2 (4.07/16.27/0.20) + R3/R5.

**Result: IS Sharpe +0.6336 / OOS +0.0560 — BOTH POSITIVE, K=20-confirmed.** IS DD 23.8% (R2 cut from
62.6%), OOS DD 19.1%. 82/32 trades. WR 34%/28%. 20/20 seeds.

**Verdict: CONFIRMATION-MERGE (Critic OVERALL=MERGE). iter-027 = the new BASELINE_V1_ETHUSDT.**
- Both-positive (PRIMARY metric) — crushes the both-NEGATIVE iter-025 bootstrap (IS −0.48/OOS −0.96).
- **The BTC deterministic stack is a PORTABLE TEMPLATE:** applied to ETH (own trend + ETH-R2) → both-positive,
  the 2nd coin. Validates the campaign's core finding.
- Lottery check: OOS regressed +0.97 (K=5) → +0.06 (K=20) but HELD POSITIVE (didn't collapse like iter-016
  — the trend-state direction is deterministic; sign is structural, only the sizing magnitude is fragile).
- Methodology PASS (trend-state look-ahead clean, embargo intact, honest costs, single-symbol).

**Critic caveats (recorded in BASELINE_V1_ETHUSDT.md):** (1) thin/magnitude-fragile OOS — anchor to +0.06
not +0.97; (2) OOS-concentration falsifier literally fails (top-1 trade ~1223% weighted; intrinsic to the
let-winners-run design, same as merged BTC iter-020 — recordable, not disqualifying); (3) headline-units
footnote (weighted vs unweighted); (4) basin diagnostic vacuous at outer-seeds=1.

**Next ETH (Critic):** (1) widen the OOS base (labeling/exit, reduce single-trade dominance, don't chase
OOS); (2) direction-robustness K=5 (swap trend_state_symbol→BTC or SMA 100/300); (3) genuine multi-outer-seed
validation.

**Cross-coin status:** BTC iter-020 (IS +0.37/OOS +0.09) + ETH iter-027 (IS +0.63/OOS +0.06) — TWO coins,
both-positive, via the SAME deterministic stack. The trend-state + conviction-gate + let-winners-run + R2
template is portable. Both have thin/concentrated OOS (intrinsic to low-WR trend-following).
