# iter-v3/047 BCH direction-asymmetric diagnosis — synthesis

## Headline finding

BCH LONG side is the IS bottleneck. iter-v3/045 (BCH default ATR) baseline confirms
the iter-v3/046 EDA finding:

| Direction | n_IS | WR_IS | net_pnl_IS | n_OOS | WR_OOS | net_pnl_OOS |
|---|---:|---:|---:|---:|---:|---:|
| LONG  | 39 | 30.77% | -25.0718% | 21 | 28.57% | -7.4413% |
| SHORT | 55 | 43.64% | 48.6918% | 17 | 52.94% | 18.1932% |

BCH LONG is toxic in BOTH IS (-25% PnL, ~31% WR) AND OOS (-7% PnL, ~29% WR). The SHORT
side carries BCH's positive contribution (+49% IS / +18% OOS).

## Per-direction exit composition (IS)

LONG side (n=39):
- Stop-loss: 25 (64.1%) mean PnL -3.9586%
- Take-profit: 9 (23.08%) mean PnL 7.4271%
- Timeout: 5 (12.82%) mean PnL 1.4097%

LONG SL rate is the dominant exit; LONG TP rate is depressed.

## Counterfactual — naive removal of all BCH LONG trades

| Period | bundle_weighted_pnl | minus_BCH_LONG | Δ |
|---|---:|---:|---:|
| iter-v3/045 IS  | 75.3967 | 94.0748 | **+-18.6781** |
| iter-v3/045 OOS | 96.9943 | 101.2322 | **+-4.2379** |

If BCH LONG signals were universally suppressed, bundle weighted_pnl would lift by
+-18.68 on IS AND +-4.24 on OOS (NAIVE — ignores
risk-gate ripple effects on other symbols).

This is the upper-bound IS+OOS lift estimate for the LONG-suppression mechanism. Bundle
Sharpe lift estimate (proportional to PnL/sigma; sigma assumed unchanged): if iter-v3/045
bundle weighted_pnl IS = 75.3967 corresponds to bundle IS Sharpe +0.7459 (single-seed),
then a +-18.68 weighted_pnl bump ≈ +-0.1848
relative to the +0.7459 anchor. (First-order proxy only; actual Sharpe depends on per-trade
variance.)

## Temporal stability of LONG toxicity

Of 18 IS months with at least 1 BCH LONG trade,
11 were net-negative. (See bch_diagnosis.csv table 04 for per-month
breakdown.) If LONG toxicity were concentrated in 1-2 anomalous months, suppression would
be unfair generalization. Persistent across multiple months supports the LONG-suppression
mechanism.

## Reproducibility check

iter-v3/045 (default ATR) and iter-v3/046 (wider SL) both show the same LONG-vs-SHORT
asymmetry pattern (see bch_diagnosis.csv table 05). The LONG-toxic pattern is NOT a
single-config artifact.

## Interpretation

The BCH LONG side fails for a structural reason — the LightGBM model produces probabilistic
signals for LONG positions on candles where the LONG side later proves toxic. Wider SL
(iter-v3/046) made it WORSE because each LONG-toxic trade now absorbed deeper losses
before stopping out.

Direction-asymmetric mechanisms address this: stop taking BCH LONGs altogether
(simplest), tighten the LONG-side confidence threshold (less aggressive), or use a
LONG-only barrier customization (architectural complexity).

The QR's recommended axis (see candidate_axes_ranking.md) prioritizes SIMPLICITY and
DIRECT mechanism alignment with the EDA finding.
