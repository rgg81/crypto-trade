# iter-v1/092 — Phase 8 Diary (XRP-IMPROVED — BTC-regime kill gate)

**Date**: 2026-06-12
**Track**: v1 (refactored)
**Branch**: `iteration-v1/092`
**TYPE**: SPECIALIST — single-symbol XRPUSDT, risk-primitive axis (post-aggregator RULE gate), EXPLORATION (3rd machinery axis of cycle-7). R6 = `enable_btc_regime_kill=True, btc_regime_kill_thr=0.067, btc_regime_kill_lookback=42b` (suppress ALL XRP entries when `btc_ret_42 > +0.067`, IS abs-median, past-only). Tested on the held XRP/088 PROMISING-diversifier seat (ungated). fail-fast=2.0 ON.
**Cycle**: 7, machinery axis
**Author**: QR (autopilot)
**Tag**: `v0.v1-092`

---

## Headline

**EXPLORATION-NEGATIVE. NO-MERGE. The BTC-regime kill gate DEGRADES XRP's IS Sharpe even when verified armed: 0.3783 (ungated /088) → 0.3007 (gated /092). F1 FAILS HARD (0.3007 vs the +0.578 floor, AND below the ungated 0.3783 anchor). The EDA-identified BTC_UP loser bucket (57 IS entries, WR ~0.35, net −36.71%) is REAL — but suppressing it does NOT make the strategy better, because a sequential single-position backtest REPLACES every suppressed entry with a later, net-worse one. The pre-registered offline-subtraction projection (+0.81 IS) was catastrophically falsified by the real backtest (−0.078 IS).**

The BTC-regime-binary-kill axis for XRP is **CLOSED**. The XRP seat stays the held **UNGATED /088** PROMISING diversifier. BUNDLE-002 (`v0.v1-082`) UNCHANGED.

---

## Result (comparison.csv, fresh 09:30 corrected run)

| Metric | Ungated /088 (=void /092 config) | GATED /092 (corrected) | Δ |
|---|---:|---:|---:|
| **IS Sharpe** | **0.3783** | **0.3007** | **−0.078** |
| IS trades | 219 | 179 | −40 (−18.3%) |
| IS WR | 42.5% | 44.7% | +2.2pp |
| IS PF | 1.1293 | 1.1222 | −0.007 |
| IS MaxDD | 26.29% | **41.82%** | **+15.53pp (WORSE)** |
| **OOS Sharpe** | **0.5158** | **0.5952** | +0.079 |
| OOS trades | 84 | 75 | −9 (−10.7%) |
| OOS WR | 42.9% | 45.3% | +2.4pp |
| OOS PF | 1.1468 | 1.1845 | +0.038 |
| OOS MaxDD | 18.90% | 15.78% | −3.12pp |
| OOS/IS ratio | 1.31 | 1.9792 | — |

DSR (gated): −70.30 IS / −34.96 OOS; n_eff_trials=1; PSR_monthly_vs_0 0.714/0.802 (INFORMATIONAL for SPECIALIST). R5 fire-rate 0.0 both windows (R5 NOT involved in the IS DD blowout).

The gate removed **40 net IS trades** (NOT the projected 57) and **9 OOS** (NOT 12). IS Sharpe FELL; the modest OOS rise is a path-dependent reshuffle artifact (favorable replacement draws), NOT a positive signal.

---

## Falsifiers (research_brief.md) — F1 FAILS HARD

| ID | Condition | Actual | Verdict |
|---|---|---|---|
| **F1** | IS Sharpe ≥ +0.578 (Δ ≥ +0.20 vs /088) | **0.3007** | **FAILS HARD** (below floor AND below ungated 0.3783) |
| F2 | 20–45% IS entries suppressed | 18.3% IS / 10.7% OOS | **BELOW band** (reshuffle suppressed less than modeled) |
| F3 | ≥50 OOS trades | 75 | passes (moot given F1) |
| F4 | regime-breadth improves | — | moot given F1 |

---

## THE HEADLINE LEARNING — projection-falsification (the load-bearing finding)

**The offline subtraction projected +0.81 IS Sharpe; the real backtest delivered −0.078 IS Sharpe.** That is a −0.89 projection error and the most valuable output of this iteration.

The pre-registered projection (`rerun_projection.md`, committed BEFORE the re-run) offline-subtracted the 57 IS / 12 OOS BTC_UP entries from the /088 roster and asserted *"subtraction is analytically exact (0 overlapping trades, sequential position model)."* It predicted IS 219→162 (26% suppressed), IS Sharpe RISING ~+0.81, OOS 84→72.

**Why it broke — the position model is SEQUENTIAL (single-position):**

1. **Slot-freeing replacement.** Suppressing a BTC_UP entry at candle T FREES the position slot, so the walk-forward enters on a *later* candle previously blocked by the open T-position. The forensic (`projection_divergence.py`) counts **25 IS replacement trades** at **WR 0.280** (well below the gated mean 0.447), contributing **−24.33 wpnl** — strictly worse than the −17.10 removed. Net IS wpnl moved **−7.23** vs the projected **+5.21** → projection error **−12.44**.
2. **Suppression cascade.** Gross removed was **65, not 57** — replacements freed by earlier BTC_UP suppressions *also* landed in BTC_UP and got re-suppressed (multi-round, invisible to a static filter). Net trade count went 219→179 (−40), not 219→162 (−57).

The reshuffled 179-trade roster is a *different, net-worse* roster than "088 minus 57 losers." The IS MaxDD blowing out to 41.82% is the tell: removing 65 entries and inserting 25 low-WR replacements re-clustered the loss path (2024-03 −16.00%, 2025-01 −16.12% concentrate it) and removed diversifying winners that were dampening the equity curve.

**Generalizable rule (now load-bearing): NEVER trust offline post-hoc trade-subtraction projections for ENTRY gates in a path-dependent / sequential backtest.** "Zero concurrent overlaps" is necessary but NOT sufficient for subtractive exactness — the binding condition is *"suppressing an entry never frees a slot,"* which is unsatisfiable in a single-position model. An entry gate's effect must be simulated by the backtest itself. **The backtest is the only valid arbiter** — this vindicates the user's "the backtest is the proof, no side scripts" directive at the mechanism level, not just as policy.

The pre-registration was methodologically exemplary even though the projection itself was wrong: it converted a wrong prior into a CLEAN falsification rather than a post-hoc rationalization.

---

## The dispatch-bug saga (void run → forensic → fix → verified-armed re-run) + process lesson

**Run 1 was VOID.** A dispatch-wiring defect (`run_baseline_v1.py:8385` `elif` lacked the `iteration_label` guard; `V1_ITER088_UNIVERSE == V1_ITER092_UNIVERSE == ("XRPUSDT",)`, so the /088 branch short-circuited /092 and built the strategy with `enable_btc_regime_kill=False`). The gate never armed; the IS roster came out **BIT-IDENTICAL to /088** (219 trades, IS 0.3783). A 3-agent forensic (`analysis/iteration_v1-092/gate_fire_forensic.py`) diagnosed it.

**THE PROCESS LESSON.** The smoking gun was `run.log` line 49 printing **`[iter-v1/088]`** instead of `[iter-v1/092]` — and the orchestrator MISSED that banner mid-run, dismissing it as cosmetic during liveness checks. **The dispatch-banner is a load-bearing liveness signal, not cosmetic.** A run whose banner names the wrong iteration is VOID at line 49, before a single metric is worth reading. Going forward the run-validation checklist verifies the `[iter-v1/NNN]` banner FIRST, before any metric plausibility, so the void-run class is caught at launch, not by a 3-agent forensic post-mortem.

**The fix (commit `77947a3d`):** added `iteration_label` guards to BOTH the /087 and /088 dispatch branches (`run_baseline_v1.py:8191`, `:8385`, plus /092 at `:8990`), closing the sibling-collision; and added a **FAIL-LOUD assertion** in `lgbm.py` (~644) so `enable_btc_regime_kill=True` with a failed index build now RAISES `FileNotFoundError` instead of silently no-op'ing — hardening against the exact silent-no-op class that produced the void run. 30/30 tests pass; Critic Phase 6.0-v2 PASS (`89852828`).

**The corrected re-run is VERIFIED ARMED:** `run.log` line 49 prints `[iter-v1/092] ... R6=ON BTC-regime kill thr=0.067 lookback=42b`; line 52 prints `[lgbm] BTC-regime kill gate: loaded 7061 BTC candles`; IS trade count 179 ≠ 219 confirms the gate fired and suppressed entries. The void run's smoking-gun banner is gone. The void log is preserved at `reports-v1/iteration_v1-092/run_VOID_dispatch_bug.log`.

---

## Did the model change? NO — confirmed (it's 100% an accounting story)

The BTC-regime kill is a **post-aggregator RULE gate** — it filters the signal stream *after* `get_signal`, so the per-month LightGBM fits, Optuna trajectories, and gain ledger are gate-independent. Feature importance is byte-identical to /088 (`vol_atr_14` rank 1 @ 9531.10, `trend_adx_14` rank 2, `stat_autocorr_lag5` rank 3, … `eth_vs_btc_ret_ratio_30` @ 0.0 rank 48). The model trained on identical data both runs; only the realized trade roster differs. There is no ML-overfit/leakage surface here — it is purely position-accounting. (Note: `btc_funding_spread_30_90` is already an in-model feature at rank 9 — BTC-context is partially priced into the model's signal already, so the external gate is partly redundant with information the tree already has.)

---

## Decision: NO-MERGE

- The BTC-regime-binary-kill gate DEGRADES XRP's IS Sharpe even when verified armed (F1 FAILS HARD). **The BTC-regime-binary-kill axis for XRP is CLOSED.**
- The XRP seat stays the held **UNGATED /088** PROMISING diversifier (re-assess as OOS accrues past Nov-2025 per /089).
- **BUNDLE-002 (`v0.v1-082`; DOT+ETH+BTC+AAVE; IS +0.72 / OOS +1.00) UNCHANGED.**

---

## Critic verdict (Phase 7.5, `briefs-v1/iteration_v1-092/review.md`)

**EXPLORATION-NEGATIVE — F1 IS-Sharpe falsifier FAILS HARD (0.3007 vs floor 0.578, and below the ungated /088 anchor 0.3783) on a VALID test (gate verified armed). The hypothesis was cleanly falsified; the projection-falsification (offline +0.81 vs actual −0.078) is correctly attributed to sequential-position-model reshuffling. NOT a BLOCK — the exploration completed successfully as a negative result. BTC-regime-binary-kill axis for XRP CLOSED; XRP seat stays the held UNGATED /088 PROMISING diversifier; BUNDLE-002 (`v0.v1-082`) UNCHANGED.**

- **Validity adjudicated VALID** (gate verified armed via run.log lines 49/52, 179 ≠ 219; dispatch fix confirmed in source at 8191/8385/8990). F1 cleanly fails on a valid test → EXPLORATION-NEGATIVE is correct; BLOCK reserved for invalid/unevaluable tests or methodology breach, neither of which applies. BLOCK-PENDING-FIX was already consumed by the dispatch fix; no second defect → BLOCK-FINAL N/A.
- **Checks 1 (look-ahead) / 2 (embargo) / 7 (reproducibility) / 8 (hypothesis-impl alignment) / 13 (anti-pattern scan) / 14 (axis-family `risk-primitive` VALID) all PASS.** Check 3 (DSR/PSR) FAIL is INFORMATIONAL for SPECIALIST. Checks 4/5 INFORMATIONAL (no new feature). Check 6 N/A (single outer seed).
- **Projection-falsification attribution ATTRIBUTION CORRECT** — root cause (slot-freeing + cascade) precisely identified, divergence quantified (gross 65, 25 replacements @ WR 0.280, net wpnl −7.23 vs +5.21 projected = −12.44 error). Generalizable rule endorsed; pre-registration praised as methodologically exemplary.
- **Lock INTACT** (threshold 0.067 = IS abs-median, never OOS-touched; opt-in default-OFF byte-identical to /088; PRUNED 48; depth-5 / 50×30 / single outer seed / no multi-seed CONFIRMATION).
- Critic recommends recording the entry-gate-subtraction-forbidden rule in feedback memory and adding a dispatch-banner liveness check to the run-validation checklist.

---

## Path Forward (from Critic — first-tier candidates for next XRP iter)

The last 5 XRP-adjacent SPECIALIST families were universe (/086–/088), sample-weighting (/090), risk-primitive (/091, /092). Critic proposes axes from families NOT in that recent set (advisory; QR may adopt/modify/reject):

1. **btc_trend in-model composed feature (`ret_5d_xrp × sign(btc_ret_42 − thr)`)** — feature-family — encode the BTC-regime interaction INSIDE the model so the tree learns to down-weight (not hard-suppress) XRP signals in BTC_UP. No entries are mechanically blocked → the slot-cascade replacement pathology is eliminated entirely; the model simply emits weaker conviction. Directly addresses the sequential-reshuffle root cause that killed the RULE gate. **(LM 7.4 idea #1 concurs — this is the cleanest "do it inside the model" answer.)**
2. **XRP labeling-horizon / barrier re-derivation** — labeling — the OOS failure is "trend-wrong-way" (directionally premature). Test an asymmetric ATR barrier or shorter timeout, re-calibrated IS-only on XRP's own regime distribution, to test whether the drag is horizon-mismatch rather than a regime-gating problem. Labeling absent from the last 5.
3. **XRP model-architecture / depth-region probe** — model-arch — the /088 XRP head was tuned at the depth-5 / 31-leaf region inherited from the ETH cell. A one-off XRP-only bounds-profile re-derivation tests whether XRP's edge is region-locked to a config borrowed from a different cohort.

---

## Next Iteration Ideas

1. **`btc_trend_interaction_signed` in-model composed feature** (Critic #1 + LM 7.4 #1) — `stat_return_5 × sign(btc_ret_42 − 0.067)`; Category-2 composed, use importance≥30 carve-out not strict |IC|<0.5; predicted rank 8–15. The mechanism-correct successor to this CLOSED gate axis (feature-MODAL mandate satisfied).
2. **XRP-vs-BTC relative strength, RETURN-space** (LM 7.4 #2) — `xrp_ret_42 − btc_ret_42` z-scored + `xrp/btc` realized-vol ratio. Distinct from the v3-CLOSED cross-asset OHLCV axis (v1 includes BTC; this is a return-difference object, not a price-level primitive). Gate on rolling-window T5 importance; drop if rank 14/14.
3. **OI × funding crowding composite** (LM 7.4 #3) — `funding_rate_zscore_30 × sign(oi_delta_30_z90)`, building on the already-rank-7 `oi_delta_30_z90`; genuinely unused interaction family.
4. **XRP labeling-horizon re-derivation** (Critic #2) — asymmetric ATR barrier / shorter timeout, IS-only on XRP regime distribution.
5. **Methodology hardening** — codify the entry-gate-subtraction-forbidden rule in feedback memory + add the dispatch-banner liveness check to the run-validation checklist.

NO multi-seed CONFIRMATION.

---

## Catalog

iter-v1/092 → `risk-primitive`/post-aggregator-RULE axis (R6 BTC-regime kill `btc_ret_42 > +0.067`, IS abs-median, past-only, lookback 42b; 3rd machinery axis of cycle-7; suppress ALL XRP entries in BTC_UP) | tested on the held XRP/088 ungated PROMISING-diversifier seat | **EXPLORATION-NEGATIVE, NO-MERGE** — gate DEGRADES IS Sharpe **0.3783 → 0.3007** (Δ −0.078; F1 FAILS HARD vs +0.578 floor AND below ungated anchor) / IS 219→179 trades (−40, 18.3%) / IS MaxDD WORSENED 26.29%→41.82%; OOS rose modestly 0.5158→0.5952 (path-dependent reshuffle artifact, NOT signal) / OOS 84→75 trades | **HEADLINE LEARNING — projection-falsification: pre-registered offline trade-subtraction projected +0.81 IS, real backtest delivered −0.078 IS (error −0.89). ROOT: SEQUENTIAL single-position model — suppressing a BTC_UP entry FREES the slot for a later net-worse entry (25 replacements @ WR 0.280, −24.33 wpnl vs −17.10 removed) + suppression cascade (gross removed 65 not 57). GENERALIZABLE: NEVER trust offline post-hoc trade-subtraction projections for ENTRY gates in path-dependent backtests; "0 concurrent overlaps" ≠ subtractive; the backtest is the only arbiter (vindicates no-side-scripts directive)** | model byte-identical to /088 (post-aggregator RULE gate, feature_importance unchanged → 100% accounting story, no ML/leakage surface) | **DISPATCH-BUG SAGA: run 1 VOID (sibling-universe collision short-circuited /092 to the /088 branch, gate never armed, IS bit-identical 219 trades); the `[iter-v1/088]` mid-run banner was the smoking gun, dismissed as cosmetic during liveness checks (PROCESS LESSON: verify `[iter-v1/NNN]` banner FIRST); fix `77947a3d` added iteration_label dispatch guards + FAIL-LOUD assertion (RAISES not silent no-op); re-run VERIFIED ARMED (run.log "loaded 7061 BTC candles", 179≠219)** | **BTC-regime-binary-kill axis for XRP CLOSED** (degrades IS even verified armed; binary kill throws away winning BTC_UP trades — edge is directional-conditional not regime-binary → next XRP iter = in-model composed feature per LM 7.4 #1 + Critic #1) | Critic Phase 7.5 (`briefs-v1/iteration_v1-092/review.md`): EXPLORATION-NEGATIVE on a VALID test, NOT a BLOCK; Checks 1/2/7/8/13/14 PASS, projection-attribution CORRECT, lock INTACT | XRP seat stays held UNGATED /088 PROMISING diversifier; BUNDLE-002 (`v0.v1-082`) UNCHANGED. Tag `v0.v1-092`.
