# iter-v3/100 — Phase-1 GO/NO-GO EDA — VERDICT: NO-GO

**Axis:** a per-symbol two-expert REGIME-SWITCHING MIXTURE — separate
LightGBM models trained on the trending vs mean-reverting regime sub-samples
of each symbol's IS data (a past-only Hurst/ADX regime split), the live model
selected by the contemporaneous past-only regime.

**Decisive premise tested:** do the trending vs mean-reverting regime
sub-samples carry GENUINELY DIFFERENT, SEPARATELY-LEARNABLE feature->label
structure — enough that two regime-specialist experts beat the single /059
model?

**Decision: NO-GO.** Killed at the EDA — no brief, no runner change, no
backtest. `OOS_CUTOFF_DATE`/`training_months` untouched; OOS never touched.

## Methodology (non-circular, OOS-robust — the /096/097 lesson)

/096/097 proved IS-CV-IC does NOT predict OOS. This EDA is NOT a naive
IS-CV-IC ranking. The load-bearing test (T3) is a **held-out-fold horse
race**: expanding-window walk-forward over the last 8 one-month IS folds; per
fold, train ONE pooled LightGBM on all prior IS candles AND TWO regime-expert
LightGBMs each on the prior IS candles of one regime; on the held-out fold,
route each candle to its regime expert (the mixture) and compare the mixture
vs the pooled model on directional accuracy and net side-PnL. Regime routing
is PAST-ONLY (Hurst/ADX at the candle close, trailing windows only). Labels
replicate `labeling.py:label_trades` exactly (ATR triple-barrier 2.0/1.0,
`natr_21_raw`, timeout 21 candles, fee 0.1%). Significance is a candle-level
block bootstrap, block = the 21-bar label horizon.

## Gates (GO rule = g1 AND g2 AND g3 AND g4)

| Gate | Statistic | Threshold | Value | Verdict |
|---|---|---|---:|---|
| g1 separability | pooled minority-regime fraction | >= 0.20 | **0.4942** | PASS |
| g2 structure-diff | mean own-minus-other-regime held-out AUC gap | >= 0.04 | **-0.0033** | **FAIL** |
| g3 mixture-lift | mixture-minus-pooled held-out acc lift; mean > 0 AND CI_lo > 0 | mean>0 & CI_lo>0 | **+0.0068** | **FAIL** |
| g4 mixture-PnL | mixture-minus-pooled held-out side-PnL lift; mean > 0 | mean > 0 | **-0.0155** | **FAIL** |

T3 acc_lift block-bootstrap 95% CI = **[-0.0110, +0.0283]** — straddles zero.

## The result read — the regime split is REAL but carries no SEPARABLE structure

- **g1 PASS — the split is real and well-balanced.** The past-only
  Hurst-100 > 0.5 AND ADX-14 >= IS-median conjunction places ~49% of candles
  trending / ~51% mean-reverting on every symbol (BCH 49.4/50.6, LDO
  49.2/50.9, TRX 49.6/50.4). Both experts would have ample data — the axis is
  not killed by a degenerate 95/5 split.

- **g2 FAIL — the regimes do NOT carry different feature->label maps.** The
  cross-regime degradation test (train an expert on regime A, score it
  held-out on regime A vs regime B) shows the mean own-minus-other AUC gap is
  **-0.0033 — essentially zero, and the WRONG sign**. Decomposed: the
  **mean-rev experts score the held-out TRENDING fold BETTER than their own
  regime** (gaps -0.045 BCH / -0.067 LDO / -0.119 TRX), while the trending
  experts score the mean-rev fold slightly worse (+0.024 / +0.026 / +0.159).
  If the two regimes carried genuinely different structure, each expert would
  score its OWN regime best (positive gap both ways). They do not. The
  trending sub-sample is simply intrinsically harder to predict; there is no
  regime-specific structure for a specialist to exploit — only one shared,
  thin feature->label map with a harder and an easier slice.

- **g3 FAIL — the decisive gate.** The two-expert mixture's held-out-fold
  directional accuracy beats the pooled model by **+0.0068 — statistically
  indistinguishable from zero** (95% CI [-0.011, +0.028] straddles zero
  widely). The per-symbol split is the fold-lottery signature, NOT a
  consistent edge: the mixture "wins" on BCH (+0.0144) and TRX (+0.0248) and
  LOSES on LDO (-0.0187). A genuine regime-specialist gain would be
  sign-consistent across all three symbols; this is noise.

- **g4 FAIL — and it does not convert to PnL.** Mixture side-PnL lift
  **-0.0155**, dragged negative by LDO (-0.3791) — splitting LDO's already-thin
  2,641-candle IS sample in two halves each expert overfits, and the mixture
  underperforms the pooled LDO model materially. The marginal BCH/TRX acc
  gains do not survive into a positive aggregate PnL.

The honest read: the trending vs mean-reverting regime split is a real,
well-balanced partition of the data — but the two halves do NOT carry
different, separately-learnable structure. Routing to a regime expert merely
halves each expert's training set; on LDO (the thinnest symbol) this strictly
HURTS. This is the same binding constraint /094-/099 hit, in a new dress: the
v3 per-symbol BCH/LDO/TRX 8h triple-barrier signal is so thin that there is
not even enough regime-conditional structure for two specialists to beat one
generalist. A two-expert mixture has no learnable lift to capture.

This NO-GO is consistent with `feedback_v3_engineered_features_proven.md` —
`regime_momentum_signed_5d` (= ret_5d × sign(hurst_100 − 0.5)) ALREADY encodes
the regime×momentum interaction as a FEATURE inside the single /059 model and
is in the 14-feature stack. The pooled model already has the regime signal it
needs; promoting regime from a feature to a model-construction split adds
nothing and costs each expert half its data.

## Cost

Killed for the cost of one committed IS-only EDA script — no `fetch`, no
runner change, no backtest, no Critic, no agent dispatch. The fail-fast WIN
(`feedback_fail_fast.md`).

## Next-axis recommendation

See `diary-v3/iteration_v3-100.md` Section 4.

## Artifacts

`regime_split_go_nogo_eda.py` + `T1_regime_separability.csv` +
`T2_cross_regime_structure.csv` + `T3_mixture_horse_race.csv` +
`T3_bootstrap_ci.csv` + `T4_go_nogo_verdict.csv`.
