# LDO Candidate Axes — iter-v3/045 QR-driven selection

Generated 2026-05-09. Reads `synthesis.md` (LDO bottleneck diagnosis) + `cycle3_plan.md` constraints
+ `feedback_v3_per_symbol_lifts_oos_breaks_is.md` rule + iter-v3/044 ALGO ATR (2.0, 1.5)
PROMISING precedent.

## Diagnosis Summary (from `synthesis.md`)

**LDO is a marginal bottleneck (not catastrophic like ALGO LONG was).**

- LDO IS @ iter-v3/044 = **+41.85% PnL, 15 trades, 46.7% WR** — POSITIVE contributor (173% pct_of_total)
- LDO OOS @ iter-v3/044 = **-3.07% PnL, 11 trades, 36.4% WR** — small drag (-2.87% pct_of_total)
- Direction asymmetry: structurally insignificant (1 LONG OOS trade; 4 LONG IS trades)
- Exit asymmetry IS: SL:TP = 1.14 (mild)
- Exit asymmetry OOS: SL:TP = 2.33 (worse but only 11 trades)
- Distribution shift IS→OOS: TP rate 46.7% → 27.3%, SL rate 53.3% → 63.6%
- LDO retains regime mismatch — natr 1.35× peer median (per iter-v3/032 EDA, structural)

**The LDO bottleneck is REGIME MISMATCH (NATR distribution-shift IS→OOS), not direction asymmetry.**

## Candidates Considered

### Candidate 1 — LDO ATR (2.0, 1.5) "wider SL" (HIGHEST PRIORITY)

**Mechanism**: Mirror iter-v3/044's PROMISING ALGO ATR (2.0, 1.5) — TP unchanged at 2.0×ATR, SL widened from 1.0×ATR to 1.5×ATR (+50%). Effective LDO barriers shift from (TP=10.01%, SL=5.01%) to (TP=10.01%, SL=7.51%). This gives LDO trades 50% more drawdown headroom before stop-out, addressing the OOS SL:TP=2.33 ratio (vs IS 1.14) — i.e. OOS sees more SL hits because OOS volatility regime is wider than the (1.0×ATR) barrier was calibrated for.

**Quantitative basis**:
- LDO IS SL:TP = 1.14 (53.3% SL rate); LDO OOS SL:TP = 2.33 (63.6% SL rate). +10pp SL rate IS→OOS.
- iter-v3/044 ALGO ATR (2.0, 1.5) was the analog: ALGO LONG SL:TP=4.5:1 IS → wider SL → ALGO swing +49 OOS.
- LDO's OOS WR collapse (46.7→36.4) is consistent with stop-outs near entry on regime-shifted noise — wider SL reduces those stop-outs.
- LDO mean SL = -4.21% IS (close to 1.0×ATR=5.01% theoretical) — at 1.5×ATR=7.51%, SL is wider than the typical adverse excursion.
- LDO LONG OOS: 1 trade, SL=-4.30% — would NOT have hit SL at 1.5×ATR=-7.51% threshold (would have likely timed out or recovered).

**Expected OOS lift**:
- Counterfactual: if LDO OOS SL rate compresses from 63.6% → 50% (matches IS), and the converted-from-SL trades become 50/50 TP-or-timeout with avg -1% (vs SL avg -4.5%), LDO OOS PnL lifts from -3.07% to ~+3 to +6%. Bundle OOS lift estimate: +3% PnL on bundle base ~107% → +0.05 to +0.10 OOS Sharpe.
- Most likely: LDO OOS PnL ≈ 0% to +5% (small positive lift), ALGO/TRX/BCH bit-identical.

**Risk profile**:
- ✓ Conforms to per-symbol-customization-but-with-IS-discipline rule (iter-v3/044 ALGO precedent + cycle 3 patterns).
- ✓ NOT the (1.5, 0.75) tighter-barrier variant that broke IS at iter-v3/039 — opposite direction (wider not tighter).
- ✗ Per-symbol customization risk per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` — but ALGO already opened this door; PRECEDENT-aligned not PRECEDENT-breaking.
- IS expectation: LDO IS may modestly increase trade count (wider SL → fewer SL-then-cooldown sequences → more entries). Predicted IS Sharpe Δ: -0.05 to +0.10 (within noise; less likely to break IS than (1.5, 0.75) was).
- Likelihood of NEGATIVE: 25-30% (cycle 3 pattern; 4 of last 4 cycle-3 axes were either NEGATIVE or marginal until iter-v3/044).

### Candidate 2 — LDO ATR (1.5, 0.75) RE-APPLY (REJECTED — VIOLATES RULE)

**Why rejected**: This is the iter-v3/032 LDO ATR (1.5, 0.75) configuration — the same one that REJECTED at iter-v3/039 multi-seed CONFIRMATION (broke IS aggregate -0.59 Sharpe vs +0.51 baseline). Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` and the cycle 3 plan's "REVERT per-symbol customizations" baseline, re-applying this exact config is forbidden without IS-axis pre-validation.

**Even though** my prompt enumerated this as candidate 1, the cycle 3 plan AND iter-v3/039 NO-MERGE rule explicitly forbid it. Cannot recommend.

### Candidate 3 — LDO per-symbol features (BTC-coupling-derived) (LOW PRIORITY)

**Mechanism**: Add per-symbol features to LDO model (e.g., btc_ret_30d, btc_realized_vol_50, btc_funding_rate). LDO uniquely uses btc_ret_14d at rank 5 in current importance — extending the BTC-coupling signature could improve LDO predictions.

**Quantitative basis**: LDO importance has btc_ret_14d at rank 5 (importance 331), much higher relative position than other symbols typically rank cross-asset features. This suggests LDO's signal is BTC-coupled. Adding 1-2 more BTC features (e.g., btc_realized_vol_50 if not in feature set) could amplify the signal.

**Risk profile**:
- ✗ iter-v3/030 LDO per-symbol features were CLOSED-NEGATIVE.
- ✗ Cycle 3 forbids per-symbol features without IS-axis pre-validation.
- Likelihood of NEGATIVE: 50%+ (cycle 3 pattern + iter-v3/030 precedent).

### Candidate 4 — LDO direction filter (gate LONG off) (LOW PRIORITY)

**Mechanism**: Use existing risk gates to block LDO LONG entries. LDO LONG OOS = -4.30% from 1 trade; LDO IS LONG = +14.40% from 4 trades. The gate would be data-snooping based on a 1-trade OOS observation.

**Risk profile**:
- ✗ Sample size is structurally insufficient (1 OOS trade).
- ✗ IS LONG is positive — gating it off would remove +14.40 from IS.
- Likelihood of NEGATIVE: 80%+ (kills positive IS; uses 1-trade data point).

### Candidate 5 — LDO sample weighting (REJECTED — TOO COMPLEX)

Out of scope for EXPLORATION. Sample weighting changes infrastructure and would be a Category 8 NEW labeling architecture variation — not a single-axis EXPLORATION.

## Recommendation: Candidate 1 — LDO ATR (2.0, 1.5)

**Rationale**:
1. **Strongest quantitative basis**: LDO OOS SL:TP=2.33 vs IS 1.14 (+10pp SL rate IS→OOS) — wider SL directly addresses the IS-OOS divergence in exit composition.
2. **Lowest risk**: PRECEDENT-aligned with iter-v3/044 ALGO ATR (2.0, 1.5) which was PROMISING. Wider SL is symmetric to the proven mechanism.
3. **Cleanest architectural decision**: V3_ATR_MULTIPLIERS_PER_SYMBOL becomes `{"ALGOUSDT": (2.0, 1.5), "LDOUSDT": (2.0, 1.5)}` — one new entry only. Default fallback preserves BCH+TRX bit-identity.
4. **Avoids the iter-v3/032 LDO (1.5, 0.75) trap**: This is OPPOSITE direction (wider barriers, not tighter). The (1.5, 0.75) failure was IS-breaking via increased SL whipsaws; wider barriers reduce SL whipsaws.
5. **Falsifiable prediction**: LDO IS SL rate should DROP from 53.3% toward ~40%. LDO OOS PnL should LIFT from -3.07% toward 0% or positive. ALGO+TRX+BCH bit-identical.

**Predicted outcome**:
- LDO IS SL rate: 53.3% → predicted [40%, 50%]
- LDO IS PnL: +41.85% → predicted [+35%, +50%] (small change; trade selection mostly preserved at TP=2.0 unchanged)
- LDO OOS PnL: -3.07% → predicted [0%, +6%]
- Bundle IS Sharpe: anchor +0.79 → predicted [+0.75, +0.85] (effectively neutral)
- Bundle OOS Sharpe: anchor reset (iter-v3/044 OOS not yet known to me — using last seen +0.5053 baseline)
   → predicted [+0.55, +0.75] — modest +0.05 to +0.20 lift
- Falsifier 1 (LDO trade roster bit-identical to iter-v3/044): if PASS → MECHANICAL classification
- Falsifier 2 (BCH+TRX+ALGO bit-identical): MUST PASS (single-axis discipline)
- Falsifier 3 (LDO OOS deepens to <-10%): wider SL backfires (low probability given mechanism)

**Catalog row pre-commits** (4 outcomes pre-registered in brief Section 11).
