# iter-v3/047 BCH direction-axis candidates — ranking

## Context

iter-v3/047 reverts iter-v3/046 BCH ATR (mirror mechanism failed on stable-SL:TP
symbols). The KNOWN BCH bottleneck is direction asymmetry: LONG IS -25% toxic /
SHORT IS +49% positive (per iter-v3/046 EDA SHA `d86b1f9` Section 2.2 and re-confirmed
in `bch_diagnosis.csv` Table 01). iter-v3/047 axis must be a DIRECTION-ASYMMETRIC
mechanism.

The 4 candidate axes ranked by quantitative leverage and implementation complexity:

---

## Candidate 1 — BCH LONG signal filter (RECOMMENDED)

**Mechanism**: in `LightGbmStrategy.get_signal(symbol, open_time)`, if `symbol ==
"BCHUSDT"` and the model's predicted class is `+1` (LONG), set the signal to 0
(block). SHORT signals (-1) and zero signals (0) pass through unchanged. This is a
universal symbol-aware gate: ALL BCH LONG signals are blocked, regardless of
confidence.

**Quantitative basis**:
- Naive bundle weighted_pnl lift: IS Δ +-18.68; OOS Δ +-4.24.
- Trade reduction: -39 BCH IS LONG trades + ~21 OOS LONG trades = bundle
  trade-rate impact ~-15% (still well above trade-rate floor).
- Removes the 39-trade IS toxic block (mean per-trade -0.64% PnL).

**Implementation complexity**: LOW. ~5-10 LOC change in `LightGbmStrategy.get_signal()`
or wrapper layer. No new config field — symbol-specific block can be hardcoded as
"v3-only" exception (or controlled via a new `bch_block_long: bool = False` config flag
defaulting to False; True for v3 runner).

**Risks**:
- IS-only finding (LONG toxic on iter-v3/045 IS) may not generalize to OOS — but EDA
  Table 01 confirms LONG also toxic on OOS (-7% PnL, ~29% WR), supporting OOS lift.
- Bundle Sharpe lift is a proxy only — actual Sharpe depends on per-trade variance
  reduction (variance should DROP since BCH LONG was high-variance toxic block).
- Risk-gate interactions: BCH LONG suppressions may free risk capacity for other
  symbols' trades; net effect on BTC/portfolio risk gates expected to be neutral.

**PROMISING-MECHANICAL risk**: at single-seed, the LightGBM head may converge on
similar non-LONG signal patterns regardless of LONG-block filter (i.e., the LONG-block
is downstream and the model's hyperparameter selection may be insensitive to it).
PROMISING-MECHANICAL classification fires if ALGO/LDO/TRX trade rosters bit-identical
AND BCH SHORT trade roster bit-identical (only BCH LONG suppressed).

---

## Candidate 2 — BCH per-direction ATR (architectural)

**Mechanism**: extend the labeling architecture to support per-direction ATR multipliers.
For BCHUSDT LONG: tighter (or wider) ATR; for BCHUSDT SHORT: default. Requires:
- New config field `V3_ATR_MULTIPLIERS_PER_SYMBOL_PER_DIRECTION: dict[str, dict[int,
  tuple[float, float]]]` (or similar nested structure).
- Refactor of `add_dynamic_atr_barriers` to dispatch per direction.
- New tests + new docstring + brief sub-fix.

**Quantitative basis**: indirect. Helps ONLY if barrier geometry per direction is the
right primitive — but iter-v3/046 already showed wider SL hurts BCH overall, suggesting
the LONG-side may also worsen with wider SL. The LONG-side may instead want TIGHTER
barriers (rapid stop, fewer toxic trades) — but EDA Table 02 shows LONG SL exits are
already ~3.9% mean drag.

**Implementation complexity**: HIGH. Architectural refactor (nested config, label-
generation refactor, new tests). EXPLORATION 2h cap may not accommodate; setup +
testing easily 60-90 min before backtest starts.

**Risks**:
- Speculative direction (tighter LONG SL = even more SLs at lower individual loss; net
  lift unknown). Not directly EDA-supported.
- Architectural debt: new config nesting that may not generalize to other symbols.

---

## Candidate 3 — BCH LONG threshold tightening (per-direction confidence)

**Mechanism**: in `LightGbmStrategy.get_signal()`, BCH LONG requires higher predicted
probability to fire (e.g. >0.65 instead of >0.5 implicit). Lower-confidence LONG signals
become 0 (no trade).

**Quantitative basis**: requires per-trade confidence extraction (currently only the
final argmax direction is exposed). Need to either:
- Modify get_signal to pass through the per-class probability, AND add a per-symbol
  per-direction threshold lookup. Requires non-trivial wrapper extension.
- OR re-run the BCH model with a softmax bias that filters LONG predictions below a
  threshold during inference — but this is essentially same as Candidate 1 with a
  variable threshold.

**Implementation complexity**: MEDIUM-HIGH. Requires probability surface exposure plus
per-symbol-per-direction config. Subset of Candidate 2's architectural refactor.

**Risks**:
- Threshold (0.65 vs 0.55 vs 0.7) is a HYPERPARAMETER that needs IS calibration —
  introduces an Optuna-tunable parameter, which inflates the trial count and risks
  overfitting.
- Could end up suppressing same set of LONGs as Candidate 1 (if model rarely produces
  high-confidence LONGs anyway), making this MECHANICAL relative to Candidate 1.

---

## Candidate 4 — BCH LONG-only feature subset

**Mechanism**: train a SEPARATE BCH-LONG-only model with a different feature subset
(features that better discriminate LONG-side regimes). Requires:
- Per-direction model architecture (new layer of abstraction).
- Per-direction feature subset config.
- Doubled training time (LONG model + SHORT model per cell).
- New CV-fold gap accounting for two models.

**Quantitative basis**: NONE — would require its own EDA on per-direction feature
importance, which itself requires re-training per-direction models on iter-v3/045 data
to extract LONG-specific importance. Not feasible within EXPLORATION 2h cap.

**Implementation complexity**: VERY HIGH. Architectural rewrite of the per-cell model
loop. Out of scope for EXPLORATION.

**Risks**:
- Doubles model count → doubles Optuna trial budget OR halves trials per direction.
- Higher risk of overfit (smaller per-direction sample size).

---

## Recommended axis: Candidate 1 (BCH LONG signal filter)

**Why**:
1. **Largest quantitative leverage**: directly captures the IS+OOS lift estimated by
   counterfactual (-18.68 IS + -4.24 OOS bundle
   weighted_pnl).
2. **Simplest implementation**: ~5-10 LOC, single `if` statement. Within 2h
   EXPLORATION cap easily.
3. **Direct mechanism alignment**: addresses the EDA root cause (LONG-side toxicity)
   without architectural changes.
4. **PROMISING-MECHANICAL falsifier already established**: per
   `feedback_promising_mechanical_subtype.md` from iter-v3/013. If BCH SHORT trades
   bit-identical to iter-v3/045, the LONG block is mechanical accounting cleanup —
   classify accordingly.
5. **Reversible**: a single boolean config (`bch_block_long: bool = False` default
   False; True for v3 runner) is trivially reversed if it doesn't lift OOS.

**Expected behavioral effect**:
- BCH IS trade count: 94 → ~55 (LONG removed). -41% BCH-specific trade reduction.
- Bundle IS trade count: 250 → ~211. -16% bundle reduction (still well above floor).
- BCH IS net_pnl: +23.62% → +48.69% (LONG drag removed; SHORT side preserved bit-
  identical).
- BCH IS WR: 38.3% → 43.6% (the SHORT WR).

**Implementation plan**:
- New config flag in `LightGbmStrategy` (or a thin wrapper layer): `block_long_for:
  set[str] = field(default_factory=set)`. Defaults empty.
- `get_signal` checks: if symbol in `block_long_for` AND signal == +1, return 0.
- Runner: pass `block_long_for=BCHUSDT` for BCH model in iter-v3/047.
- Test: add `test_block_long_for_bch_dispatch.py` with 4 assertions (BCH LONG
  blocked, BCH SHORT passes, ALGO LONG passes, BCH zero passes).

This is the QR's recommendation. Setup commit will follow this brief Section 3.
