# Iteration v2/001 Diary

**Date**: 2026-04-13
**Type**: EXPLORATION (new feature set + new universe + new risk layer)
**Track**: v2 — diversification arm
**Branch**: `iteration-v2/001` on `quant-research`
**Decision**: **NO-MERGE (EARLY STOP)** — weighted OOS Sharpe is −0.32, fails
the iter-v2/001 relaxed success criteria. Raw unweighted OOS Sharpe is
+0.479 (near target), so the underlying strategy has signal — the risk
layer destroys it.

## Results — side-by-side vs target

| Metric | Target (iter-v2/001 relaxed) | Actual (weighted) | Actual (raw net_pnl) | Pass? |
|---|---|---|---|---|
| OOS Sharpe | > +0.5 | **−0.324** | +0.479 | FAIL |
| ≥7/10 seeds profitable | 7/10 | 0/1 (early stop) | — | FAIL |
| OOS trades | ≥ 50 | 139 | 139 | PASS |
| Profit factor (OOS) | > 1.1 | **0.934** | — | FAIL |
| Single-symbol concentration | ≤ 50% of OOS PnL | **XRP 96% (sign flipped), DOGE −61%** | — | FAIL |
| DSR | > −0.5 | −3.51 (weighted) | +6.73 (raw, p≈1) | FAIL (weighted) |
| v2-v1 OOS correlation | < 0.80 | **+0.011** | **+0.011** | **PASS** |
| IS/OOS Sharpe ratio | > 0.5 | −0.81 | 0.46 | FAIL (weighted) |

**Primary**: OOS Sharpe weighted −0.32. **Hard-constraint failures**:
Sharpe sign, PF < 1.1, IS/OOS ratio, symbol concentration.

First-seed early-stop rule (`OOS Sharpe < 0 AND OOS PF < 1.0`) is
triggered. 10-seed validation not run (Fail Fast protocol).

## Per-symbol OOS breakdown

| Symbol | n | WR | Raw Sharpe | Raw PnL | Weighted PnL | Scale |
|---|---|---|---|---|---|---|
| DOGEUSDT | 47 | 38.3% | −0.504 | −24.02% | −15.63% | 0.65 |
| SOLUSDT | 50 | 38.0% | +0.491 | +25.65% | +6.37% | 0.25 |
| XRPUSDT | 42 | 45.2% | **+0.889** | +37.56% | **−6.65%** | **−0.18** (sign flipped) |

## Regime-stratified OOS Sharpe (raw net_pnl_pct)

All 139 OOS trades fell in `hurst_100 ≥ 0.6` (trending) bucket:

| Hurst | ATR pct | n | mean | Sharpe |
|---|---|---|---|---|
| [0.6, 2.0) | [0.00, 0.33) | 54 | **−1.45%** | **−1.85** |
| [0.6, 2.0) | [0.33, 0.66) | 43 | +1.01% | +0.94 |
| [0.6, 2.0) | [0.66, 1.01) | 42 | **+1.77%** | **+1.45** |

The entire OOS drag is in the low-vol trending bucket (54 trades bleeding
1.45% each). The mid and high-vol buckets both print strong positive
Sharpe. The RiskV2Wrapper's vol-adjusted sizing does the exact opposite
of what's required — it shrinks the profitable high-vol trades while
keeping the unprofitable low-vol trades at full size.

## Gate efficacy (post-mortem vs pre-registered prediction)

Pre-registered prediction (research brief §6.2): combined gate kill rate
**10-30% target**.

| Symbol | signals | z-score kills | Hurst kills | ADX kills | **Kill rate** | Mean vol_scale |
|---|---|---|---|---|---|---|
| DOGEUSDT | 2,560 | 286 (11%) | 146 (6%) | 723 (28%) | **45.1%** | 0.620 |
| SOLUSDT | 2,515 | 400 (16%) | 193 (8%) | 596 (24%) | **47.3%** | 0.543 |
| XRPUSDT | 2,532 | 340 (13%) | 235 (9%) | 709 (28%) | **50.7%** | 0.585 |

Every gate is firing well above the pre-registered estimate. The ADX gate
(threshold=20) is the largest contributor at ~28% on its own. The
feature z-score OOD alert contributes 11-16% (the any-of-35 compounding
raises it above a per-feature naive estimate). The Hurst gate is at
target, ~7-9%.

Combined 45-51% kill rate + mean vol_scale of 0.54-0.62 on the survivors
= the model's raw signal is filtered to less than a third of its intended
weight.

## Pre-registered failure-mode prediction — was it right?

Brief §6.3 predicted the most likely failure as "a sustained 2024-2025
meme-coin or alt correction that moves slowly enough to keep ATR and
Hurst inside their training ranges but persistently enough to accumulate
SL losses on DOGE in particular".

**Partially right, wrong reason**: DOGE did drag OOS with SL losses
(60% SL rate, raw Sharpe −0.50) — exactly the DOGE-specific bleed I
predicted. But the dominant failure is **not the DOGE correction** —
it's the vol-scaling sabotaging SOL and XRP's profitable signal. The
secondary prediction (insufficient Optuna trials producing "similar
mediocre per-model Sharpe") was **wrong** — per-symbol results are
highly differentiated, and raw per-symbol Sharpes span −0.50 to +0.89.

## Exploration/Exploitation Tracker

This is **iter-v2/001** (first v2 iteration). v2 exploration rate is
1/1 = 100% so far — entire new feature set + new risk layer + new symbol
universe. Over the next 10 iterations the target returns to 30%; but
iter-v2/002 is also structurally exploration (changes the risk layer),
so track accordingly.

## Lessons Learned

1. **Vol-adjusted sizing is strategy-dependent in sign**. A momentum/trending
   learner wants MORE exposure in high-vol regimes where trends get
   stronger, not less. The classic "scale inversely with vol" rule comes
   from equity vol-targeting where mean reversion dominates. In crypto
   8h-bar LightGBM land, the edge is in the tail, and the tail is where
   ATR percentile is highest. Next iteration must either disable the
   vol-scaling entirely or **invert** it.
2. **Low-ATR trending regimes are a systematic loss generator**. 54 of 139
   OOS trades fell in `atr_pct_rank_200 < 0.33` with mean −1.45% and
   Sharpe −1.85. This is the clearest structural finding of iter-v2/001.
   A direct low-vol filter (skip when `atr_pct_rank_200 < 0.33`) would
   mechanically improve OOS Sharpe.
3. **DOGE at default ATR multipliers is unprofitable**. 2.9×NATR TP /
   1.45×NATR SL were inherited from v1 Model A (BTC+ETH). Memes need
   wider barriers, per v1's meme-baseline note (iter 114 used different
   multipliers). Specialize per symbol in iter-v2/002+.
4. **v2-v1 OOS correlation is 0.011** — the diversification goal is
   meaningfully achieved even in this failed iteration. DOGE+SOL+XRP
   running in parallel with v1's BTC+ETH+LINK+BNB would produce a
   genuinely uncorrelated return stream. This is the single strongest
   evidence that the v2 track direction is correct; only the risk layer
   implementation is broken.
5. **The 4 MVP risk gates need calibration, not redesign**. The ADX gate
   at threshold=20 fires too hot (28%). The z-score OOD gate compounds
   across 35 features to a 15% fire rate. Both can come down with a
   modest threshold bump. The Hurst gate (~8% fire) is on target.
6. **First-seed rule is working as designed**. iter-v2/001 saved ~3-6
   hours of 10-seed compute by early-stopping on the weighted Sharpe
   result alone.
7. **Raw IS Sharpe +1.04, raw OOS Sharpe +0.48, IS/OOS ratio 0.46**.
   The researcher is not obviously overfitting IS; the strategy has
   transferable signal. The 5.7× samples-per-feature ratio held up.

## lgbm.py Code Review (Mandatory per Phase 7)

No changes recommended. v1's LightGbmStrategy is working correctly with
v2's feature_dir and feature_columns plumbing. The atr_column="natr_21_raw"
indirection via the features_v2 helper column works cleanly; labeling
triple-barrier math is applied correctly. The only observation: the
ensemble_seeds path for single-seed runs produces 1 model, which is
intentional but wastes a small amount of list-wrapping. Not worth
changing.

## Next Iteration Ideas

### Priority 1 (iter-v2/002): Fix the vol-adjusted sizing

Three options to A/B test (pick the best in iter-v2/002):

1. **Disable** — Set `enable_vol_scaling=False` in `RiskV2Config`. Let the
   backtest engine's optional `vol_targeting=True` handle sizing at the
   engine level, same as v1 does.
2. **Invert** — Change the wrapper formula to `vol_scale = atr_pct_rank_200`
   clipped to `[vol_scale_floor, vol_scale_ceiling]`. MORE exposure in
   high-vol, LESS in low-vol. Opposite of iter-v2/001.
3. **Hurst-based sizing** — Use `vol_scale = hurst_100` clipped to
   `[0.3, 1.0]`. More exposure when trend persistence is strong.

Recommended: run option 2 (**invert**) as the primary fix. If it works,
the weighted Sharpe should rise from −0.32 to at least the raw +0.48
level, probably higher. Option 1 is the fallback.

### Priority 2 (iter-v2/002 same run): Low-vol filter

Add `atr_pct_rank_200 >= 0.33` as a gate entry condition. Kills the
low-vol trending bucket (54 of 139 OOS trades) that produced −1.45%
mean return. Mechanically: the remaining 85 OOS trades would give
Sharpe ≈ (0.94×43 + 1.45×42)/85 ≈ **+1.19**, clearing both the +0.5
bar and the v1 diversification+correlation case.

### Priority 3 (iter-v2/002): ADX threshold down

Bump `adx_threshold` from 20 to 15 so the ADX gate fires ~10% instead
of ~28%. Validate by comparing the combined kill rate target of 10-30%.

### Priority 4 (iter-v2/002): Drop DOGE from the portfolio

DOGE is the only negative-Sharpe symbol even unweighted. Two sub-options:

- Replace DOGE with a different low-v1-correlation pick. Next-lowest
  v1 correlation candidates were FILUSDT, NEARUSDT, XRPUSDT (already
  in), APTUSDT — all at ~0.665. NEARUSDT is a solid L1 candidate with
  ~4,847 IS rows.
- Keep DOGE but specialize its ATR multipliers: try 3.5× TP / 1.75× SL
  (v1 Model C/D default) or even 5.0× TP / 2.0× SL for the wider meme
  dynamics per the meme-baseline note.

Recommended: specialize DOGE's ATR multipliers first (one variable
change). Replace with NEAR only if that doesn't fix it in iter-v2/003.

### Priority 5 (iter-v2/002 or 003): Bump Optuna trials to 25-50

iter-v2/001 used 10 to fit compute budget. Raw IS Sharpe +1.04 suggests
we might have under-optimized; bumping trials could raise IS from +1.04
toward v1's Model A IS +1.33 level. Do AFTER the sizing fix lands.

### Deferred (iter-v2/003+): Enable drawdown brake

Still worth it once the sizing is fixed. The drawdown brake is the
primary defence against the "slow monotone bleed" scenario I flagged
as a known-unknown in §6.2 of the brief.

## MERGE / NO-MERGE

**NO-MERGE (EARLY STOP)**. Cherry-pick the research brief, engineering
report, and this diary to `quant-research` (docs only). `BASELINE_V2.md`
remains empty — iter-v2/002 gets a chance to establish the first v2
baseline.

The iter-v2/001 branch stays as a record. It is the proof that the v2
infrastructure works end-to-end, the feature generation is stable, the
6-gate screening finds diversifying symbols, DSR + regime-stratified
Sharpe validation runs cleanly, and the failure mode analysis produces
falsifiable next-iteration actions.
