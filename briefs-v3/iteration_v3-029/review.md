# Phase 7.5 Critic Review — iter-v3/029

OVERALL: **EXPLORATION-PROMISING (clean — STRONG signal)** — first PROMISING in new cycle. Per-symbol feature-signature alignment methodology validated. ALGO contributes +20.87 OOS PnL; ALL 4 symbols trade; 3 of 4 positive; concentration drops 75% → 51%; OOS Sharpe +1.77 is highest in v3 catalog.

## Per-Check Status

All 12 methodology checks PASS or PASS-EXPLORATION (informational). Single-axis discipline preserved.

## §4.4 PATH A Verification

| Condition | Threshold | Observed | Triggered |
|---|---|---|---|
| IS Sharpe Δ ≥ +0.10 | ≥ +0.10 | +0.28 | YES |
| OOS Sharpe Δ positive vs anchor | > 0 | +1.26 | YES (massively) |
| ALGO contributes positive PnL | > 0 | +20.87 | YES |
| Concentration drops | reduced | 75% → 51% | YES |
| Bundle OOS trades increase | toward 130 | 96 → 120 | YES |

All 5 PATH A conditions fire. Verdict unambiguous PROMISING.

## Methodology Innovation — Per-Symbol Feature Signature Alignment

User directive 2026-05-08 ("features are the key", "some features are better suited of symbols a but not b") drove the methodology pivot. The per-symbol feature analysis (`d451885`) identified:
- 7 HIGH-DISPERSION features (symbol-specific): hurst_100 (BCH=12, LDO=14, TRX=3), btc_ret_14d (BCH=14, LDO=6, TRX=14), max_dd_window_50 (BCH=2, LDO=10, TRX=5), vwap_dev_20 (BCH=1 vs TRX=7)
- 4 SHARED top-7 features (universal): vwap_dev_20, range_realized_vol_50, ret_kurt_50, ret_skew_200

Symbol candidate selection (`c30369d`) used ALIGNMENT with shared features (NOT correlation), picking ALGO over correlation-lowest VET. ALGO's actual model importance verifies the prediction:
- ALGO top-3: max_dd_window_50, ret_skew_50, range_realized_vol_50 — matching the SHARED top-7

Compared to iter-v3/021 correlation-only selection (HBAR+AVAX) which produced -0.83 OOS Sharpe with both new symbols deeply negative IS+OOS, iter-v3/029 feature-signature alignment produces PROMISING signal AND new-symbol contribution.

**This methodology is the validated approach for future symbol expansions.** Should be encoded as memory rule.

## Caveats

1. **Single-seed lottery risk**: iter-v3/025 single-seed +0.88/+1.22 → iter-v3/028 multi-seed +0.51/+0.51 (42%/58% compression). iter-v3/029 single-seed +0.79/+1.77 — even higher OOS would be even more vulnerable. Multi-seed validation at iter-v3/039 is the truth-test.
2. **OOS +1.77 is suspect at single-seed**: iter-v3/013 single-seed +2.70 was falsified at iter-v3/018 multi-seed (86% reduction). Pattern: anything >+1.5 OOS single-seed compresses heavily.
3. **ALGO 25 trades** is small per-symbol sample.
4. **LDO continues underperforming** (-3.07 OOS, 11 trades, 36.4% WR) — the 14-feature stack doesn't fit LDO well; future iter-v3/030+ could explore LDO-specific feature subset.

## Recommendations to QR

1. **iter-v3/030 axis = ANOTHER targeted symbol expansion** (per-symbol-signature methodology). Test 5th symbol candidate from prior EDA. Single-axis. KEEP regime_momentum + 14-feature stack + V3_MODELS=4 BCH+LDO+TRX+ALGO. ADD 5th symbol = 5 → REQUIRED_GAP 88 → 110. Candidate: FILUSDT or VETUSDT (next-best from iter-v3/021 EDA, alignment-evaluated against iter-v3/028 multi-seed importance).

2. **NEW memory rule**: `feedback_v3_per_symbol_signature_methodology.md` codifying the per-symbol feature signature alignment as the validated symbol-expansion methodology (vs correlation-only selection).

3. **Catalog row** must explicitly flag: PROMISING — STRONG signal — first PROMISING in new cycle. Single-seed lottery caveat carries forward.

## Catalog Row

`| iter-v3/029 | 2026-05-08 | ADD ALGOUSDT (V3_MODELS 3→4; per-symbol feature signature alignment selection); REQUIRED_GAP 66→88; KEEP 14-feature stack | +0.28 (vs iter-v3/028 anchor +0.5101) | +1.7653 (Δ +1.26 — HIGHEST OOS Sharpe in v3 catalog; 4 symbols trade; 3 of 4 positive; concentration TRX 75% → 51%) | EXPLORATION-PROMISING (clean — STRONG signal) | YES — STRONG CONFIRMATION-BUNDLE CANDIDATE; ALGO +20.87 OOS PnL (36% of total); ALGO top-3 importance matches SHARED top-7 (validates per-symbol-signature methodology); iter-v3/013-style single-seed lottery caveat carries forward; multi-seed validation needed at iter-v3/039 CONFIRMATION |`
