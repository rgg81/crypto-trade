# iter-v3/071 EDA synthesis — META-LABELING axis (cycle 2 #1)

## Axis
META-LABELING (López de Prado AFML Ch. 3): M2 secondary classifier vets M1's direction signals (binary take/skip). LOCKED per `feedback_v3_iter017_metalabeling_mandate.md` + iter-v3/070 cycle-2 priority #1. The iter-v3/017 attempt was EXPLORATION-NEGATIVE PATH C (over-filter).

## T1 — M1 signal quality (the M2 target distribution)
PORTFOLIO IS roster: 159 trades — TP 49 / SL 101 / timeout 9. M2 positive rate (net_pnl>0) = 36.5%.
LDO IS roster: 11 trades — TP 3 / SL 8 / timeout 0. M2 positive rate = 27.3%.

## T3 — same-feature M2 separability (DECISIVE for Path)
PORTFOLIO: best |AUC-0.5| across 14 M1 features on M1-fired bars = 0.1222 (RESIDUAL-SIGNAL).
LDO: best |AUC-0.5| = nan (INSUFFICIENT).

## T4 — per-symbol M2 viability
LDO: 11 M1-fired bars full-IS, 3 TP-hit / 8 non-TP, ~0.42 samples/month → flag=THIN-PER-MONTH.

## T5 — trade-count reduction prediction
At the /017-empirical 25% trade-level reduction: OOS 102 → 76 (5.43/month → BELOW-FLOOR). /060 OOS is ALREADY 7.29/month — below the 10/month floor; M2 filtering only worsens it.

## PATH DECISION
**Path A.**

Path A — Full meta-labeling via `--model metalabeling`. T3 best same-feature |AUC-0.5| = 0.1222 >= 0.12: there is residual TP/non-TP structure in M1's own features that a same-feature M2 tree could exploit. The EXISTING `MetaLabelingStrategy` is wired and tested; activating it is a zero-new-code structural axis.

Path B (M1-proba gating) is NOT selected: it is not true meta-labeling (no M2 model) and the cycle-2 mandate is a STRUCTURAL axis. Path C (pooled M2) is NOT selected: pooling across BCH/LDO/TRX dilutes the LDO-specific precision the axis targets, and per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` per-symbol structure is the v3 norm.

LDO viability (T4): flag=THIN-PER-MONTH. LDO's per-month M2 cells are THIN — M2 may go inactive on LDO month-cells (metalabeling.py:445 n_m1_pos<5 skip), in which case M1's LDO signal passes through unfiltered. This is a known limitation the brief Section 4/7 must pre-register.
