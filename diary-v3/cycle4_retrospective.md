# Cycle 4 Retrospective — iter-v3/093-100

**Date**: 2026-05-18
**Cycle**: 4 (the fourth post-bootstrap EXPLORATION cycle) — iter-v3/093 through iter-v3/100, 8 iterations
**Canonical baseline throughout**: **iter-v3/059** (`v0.v3-059`) — per-symbol LightGBM,
triple-barrier ATR 2.0/1.0 + 21-candle timeout, 14-feature `V3_FEATURE_COLUMNS`,
IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**.
**BASELINE_V3.md UNCHANGED** — every cycle-4 iteration was NO-MERGE; the canonical
baseline did not move.

> Cycle 4 was capped at 8 iterations rather than the standard 10: per the user
> directive (2026-05-18) cycle 4 was to grind "a bit more" and then cycle 5 opens
> on the excluded-coins re-evaluation. /098/099/100 are the post-directive grind;
> /101 (cycle-5 opener) is the excluded-coins re-evaluation EDA.

---

## The 8-iteration ledger

| # | iter | Axis | Outcome | One-line result |
|---|------|------|---------|-----------------|
| 1 | /093 | Derivatives-microstructure regime-conditioned book (funding/basis/cross-asset-BTC vol-regime classifier gating position SIZE on the /059 base book) | **BLOCKED** | Critic Phase-7.5 OVERALL=BLOCK — the base book was NOT held bit-frozen; the central result (OOS +1.78 / IS +0.79) is CONFOUNDED and is not a usable data point about the regime overlay. |
| 2 | /094 | Derivatives ORDER-FLOW directional ALPHA (22-feature order-flow panel → triple-barrier label) | **NULL-AT-EDA** | Phase-1 GO/NO-GO NO-GO. Barrier-label-IC 0.0981 at the ~0.10 price-myopic ceiling; the literature's signed-taker-imbalance headline is the weakest group (sub-0.04, sign-flipping). The Anastasopoulos et al. daily Sharpe-3.6 result does not transfer to v3's per-symbol 8h construction. |
| 3 | /095 | Crypto cointegration / relative-value statistical arbitrage | **NULL-AT-EDA** | Phase-1 GO/NO-GO NO-GO on 3 independent gates. Only 14.77% of in-formation-cointegrated spreads survive into the next month; the faithful walk-forward book is net- AND gross-negative; trade-rate floor failed ~3×. |
| 4 | /096 | POOLED cross-symbol model (one LightGBM on concatenated BCH+LDO+TRX; v1's Model A construction) | **NULL-AT-EDA** | Phase-1 GO/NO-GO NO-GO. LOSO transfer rank-IC +0.0698 headline, but every held-out symbol's 95% block-bootstrap CI straddles zero; TRX transfer IC negative; only 4 of 14 features sign-consistent across symbols. Pooling cannot manufacture cross-symbol signal that is not there. |
| 5 | /097 | SYMBOL-UNIVERSE RE-SELECTION (`V3_MODELS` BCH/LDO/TRX → LDO/GALA/ADA, screened on within-symbol CV-IC) | **NEGATIVE** (Section-8 8.2 NEGATIVE-no-transfer) | Full backtest. IS −0.37 / OOS −0.93 (sign flip) vs /059. The within-symbol-CV-IC screen selected genuine-IS-signal symbols but the re-anchored universe did not transfer OOS. |
| 6 | /098 | FEATURE EXPANSION (14-feature stack + researched candidate families: order-flow, microstructure, cross-asset) | **NULL-AT-EDA** | Phase-1 GO/NO-GO NO-GO. No candidate feature family cleared the OOS-robustness bar; the binding constraint is the label/signal, not the feature space. |
| 7 | /099 | LABELING RE-ARCHITECTURE — abstention-aware 3-class label {LONG, SHORT, NO-TRADE} | **NULL-AT-EDA** | Phase-1 GO/NO-GO NO-GO. The decisive premise — the NO-TRADE class is feature-learnable at decision time — fails out-of-window. |
| 8 | /100 | REGIME-SWITCHING two-expert mixture (separate LightGBMs on trending vs mean-reverting regime sub-samples; past-only Hurst/ADX routing) | **NULL-AT-EDA** | Phase-1 GO/NO-GO NO-GO. The decisive premise — trending vs mean-reverting sub-samples carry separately-learnable feature→label structure — fails the held-out-fold horse race; the mixture does not beat the pooled model. |

**Tally**: 1 BLOCKED, 1 NEGATIVE, 6 NULL-AT-EDA. **Zero PROMISING. Zero merge candidate.**
Six of eight axes were killed cheaply at a committed Phase-1 IS-only EDA — no
backtest, no Critic, no agent dispatch — the fail-fast discipline (`feedback_fail_fast.md`)
working as designed: resources do not go to foreseeably-modest axes.

---

## Bottom line — no edge found; the binding constraint confirmed

Cycle 4 found **no edge beyond /059 anywhere.** The canonical baseline is unchanged.

The binding constraint, confirmed across cycle 4 from **seven independent attack
angles**, is the **thin per-symbol 8h triple-barrier feature→label signal of the
mid-cap altcoin universe** (BCH/LDO/TRX):

- **Derivatives microstructure** (/093 regime overlay, /094 order-flow alpha) — crypto-native
  non-OHLCV feeds carry no transferable directional alpha on v3's per-symbol 8h
  architecture, in either the risk-overlay role or the directional-feature role.
  Consistent with the cycle-3 7-FEED STRUCTURAL VERDICT (/082 funding, /086 basis).
- **Cointegration statistical arbitrage** (/095) — a genuinely different strategy class;
  crypto spreads decohere too fast (14.77% next-month cointegration survival) for a
  walk-forward pairs book.
- **Pooled vs single models** (/096) — pooling triples the training rows but cannot
  manufacture cross-symbol signal; the LOSO transfer IC is statistically
  indistinguishable from zero on all three symbols.
- **Symbol screening** (/097) — re-anchoring onto the highest-within-symbol-CV-IC
  altcoins does not transfer OOS.
- **Researched feature families** (/098) — no expansion of the 14-feature stack clears
  the OOS-robustness bar; the feature space is not the binding constraint.
- **Labeling re-architecture** (/099) — an abstention-aware 3-class label does not lift
  the signal; the NO-TRADE class is not feature-learnable out-of-window.
- **Regime-switching** (/100) — a two-expert trending/mean-reverting mixture does not
  beat a single pooled model; the regime sub-samples do not carry separately-learnable
  structure.

The /096 EDA quantified the constraint directly: the within-symbol purged-CV
feature→label rank-IC of the 14-feature stack vs the /059 triple-barrier label is
roughly **+0.025 on BCH and +0.029 on TRX** — barely above zero — with **LDO's
+0.178 the strongest in v3's history, and even that is modest.** /059's OOS +0.58
is essentially carried by LDO alone.

Cycle 4's structural lesson: the thin signal is **not a feature problem, not a model
problem, not a labeling problem, and not a strategy-class problem within the altcoin
universe** — it has survived a direct attack from all of those. The open question
cycle 4 could not answer is whether the thin signal is a property of the **mid-cap
altcoin universe v3 has been confined to for 100 iterations**, or a property of **8h
crypto triple-barrier prediction generally.**

**Cycle 5 opens on exactly that question** — iter-v3/101, an IS-only re-evaluation
EDA screening the v3-EXCLUDED liquid majors (the v1+v2 symbols) on the same
within-symbol feature→label IC metric, to test whether the excluded majors carry
the genuine signal the mid-cap altcoins lack.
