# iter-v3/128 — WILD axis brainstorm + selection

**Date**: 2026-05-21
**Branch**: iteration-v3/128
**Mandate**: `feedback_v3_qr_axis_creativity_mandate.md` (2026-05-21 user push-back) — be GENUINELY WILD, combine multiple structural levers, reject "axis exhausted" narrative.
**Locked constraints**: LightGBM model class (still locked); /116 no_confirm STAYS; 2h EXPLORATION wall-clock cap; symbols NOT in V3_EXCLUDED_SYMBOLS.
**Lifted constraints**: symbol universe (any non-v1/v2/MKR symbol); candle frequency (any).
**Methodology constraint** (per `feedback_v3_eda_methodology_falsified.md`): NEW-feature axes FORBIDDEN until methodology REPLACED. For non-feature axes (universe / cadence / frequency), the rolling-endpoint methodology fix is MANDATORY — bake multi-IS-endpoint EDA into the pre-flight gates.

## 1. Brainstorm — 5+ WILD axis candidates

I enumerate axes that combine 2+ structural levers (universe × frequency × architecture) and reject the cycle-7 "axis exhausted" framing. For each I state:
- Levers combined
- Why structurally distinct from cycle-7 NEGATIVEs (/122–/127)
- New prior tapped
- Infrastructure cost (must fit 2h EXPLORATION cap)

### A — 6-symbol sector-pure L1 universe at 8h with rolling-endpoint alpha-screen

**Universe**: ATOM + RUNE + AVAX + INJ + APT + HBAR (all 24mo IS-extent eligible).
**Frequency**: 8h (familiar).
**Architecture**: /121 14-feature stack, /116 no_confirm, K=21, +2/-1 ATR, 7-gate RiskV2, ENSEMBLE_SIZE=3, n_trials=35. /127 drawdown brake REVERTED.
**Levers combined**: NEW universe × NEW cardinality (3→6) × sector-pure L1 composition × rolling-endpoint methodology baked into EDA.
**Distinct from cycle-7 NEGATIVEs**:
- /122/123/126 = NEW-feature axes (FORBIDDEN by methodology block). This is NOT a feature axis.
- /124 = labeling-DURATION (CLOSED). This is not labeling.
- /125 = 3-sym ATOM/RUNE/UNI WHOLESALE swap (NEGATIVE-catastrophic). The cardinality is structurally distinct (3→6); the universe composition is also distinct (no UNI; +AVAX/INJ/APT/HBAR for sector purity).
- /127 = drawdown-brake risk primitive (CLOSED). This is not a risk primitive.
**New prior tapped**: 6 sector-pure L1 mid-caps create a denser inter-symbol correlation structure (all L1 chains share macro-narrative regime) with cardinality 2× the failed /125. The /125 closeout claimed "cohort-shaped architecture" — but /125 was a same-cardinality swap. Cardinality-expansion has NEVER been tested under lifted constraints; /087 was BCH/LDO/TRX + 3 gaming tokens (mixed composition, not sector-pure expansion).
**Infrastructure cost**: features parquet generation for 6 new symbols at 8h (one-time, ~5 min/sym). REQUIRED_GAP recalc 66 → 132 = (21+1)*6. Runner pre-flight assertions for new universe. ALL within 2h cap.

### B — 5-symbol mid-cap L1 universe at 24h-multi-offset (3 offsets)

**Universe**: ATOM + RUNE + AVAX + HBAR + OP (5 mid-caps; OP for L2 diversification).
**Frequency**: 24h-3-offset multi-offset (leverages /117 infrastructure).
**Architecture**: /117 architecture (14+offset_id features, REQUIRED_GAP=72*5/3=120, pooled-offset training).
**Levers combined**: NEW universe × 24h frequency × multi-offset architecture × rolling-endpoint methodology.
**Distinct from cycle-7 NEGATIVEs**:
- /117 was BCH/LDO/TRX at 24h-3-offset (NEGATIVE). The /117 failure mechanism was BCH 99.12% label imbalance + TRX zero OOS trades. A NEW universe BYPASSES both carriers.
- /125 was 3-sym at 8h (not 24h).
**New prior tapped**: /117's failure was specifically BCH+TRX-driven; the daily-frequency-aggregation hypothesis itself is not falsified for a different universe. The /125 was 3-sym at 8h.
**Infrastructure cost**: feature parquet generation for 5 new symbols at 24h-3-offset (~10 min/sym; uses existing `multioffset_24h.py`). MEDIUM cost; close to 2h cap. RISK: REQUIRED_GAP formula adjustment for cardinality 5.

### C — 8-symbol stratified universe at 8h (2 L1 + 2 L2 + 2 DeFi + 2 mid-cap)

**Universe**: ATOM + AVAX (L1) + ARB + OP (L2) + AAVE + UNI (DeFi) + HBAR + ICP (mid-cap general).
**Frequency**: 8h.
**Architecture**: /121 14-feature stack, ENSEMBLE_SIZE=3.
**Levers combined**: NEW universe × NEW cardinality (3→8) × stratified sector composition × rolling-endpoint methodology.
**Distinct from cycle-7 NEGATIVEs**:
- Cardinality 8 is unprecedented in v3 (max attempted 6 at /087 NEGATIVE).
- Sector composition is intentionally HETEROGENEOUS (opposite to A's sector purity).
**New prior tapped**: Maximum cross-sectional diversification — 4 sector buckets × 2 symbols/bucket. Hypothesis: sector-level orthogonality reduces concentration risk that broke /125 (single-cohort fragility).
**Infrastructure cost**: features parquet for 8 symbols + REQUIRED_GAP=66*8/3=176 + AAVE in dead-paths (/110 mentioned AAVE OOS −35%). RISK: AAVE inclusion contradicts /110 dead-path.

### D — Volatility-parity 6-symbol universe at 8h with cross-symbol risk-parity weighting

**Universe**: ATOM + AVAX + INJ + HBAR + OP + APT (selected by mean-monthly realized-vol balanced across deciles).
**Frequency**: 8h.
**Architecture**: /121 + NEW per-symbol weighting inversely proportional to 90d realized vol.
**Levers combined**: NEW universe × NEW per-symbol weighting × rolling-endpoint methodology.
**Distinct from cycle-7 NEGATIVEs**: Risk-parity weighting is a structural innovation never attempted in v3. /125 was equal-weight 3-sym. /127 was per-symbol drawdown brake (CLOSED).
**New prior tapped**: Markowitz risk-parity portfolio construction. Low-vol symbols get larger weight, high-vol symbols smaller — natural diversification.
**Infrastructure cost**: HIGH — requires new code in `risk_v2.py` for cross-symbol weighting OR a per-symbol `weight_factor` field that scales position size by inverse rolling vol. REJECTED for 2h cap.

### E — Meme-coin universe at 8h (different microstructure)

**Universe**: 1000PEPEUSDT + 1000FLOKIUSDT + 1000SHIBUSDT + WIFUSDT (4 meme-coins).
**Frequency**: 8h.
**Architecture**: /121.
**Levers combined**: NEW universe (microstructurally distinct meme microstructure) × familiar architecture.
**Distinct from cycle-7 NEGATIVEs**: Meme coins have ENTIRELY DIFFERENT microstructure than L1 chains — narrative-driven directional jumps, fat-tail liquidations, lower realized-vol persistence.
**New prior tapped**: Different feature→label distribution. Meme coins may carry directional momentum signal that L1 mean-reversion features cannot exploit.
**Infrastructure cost**: LOW. But RISK: meme coins like WIFUSDT have <24mo IS extent (started 2024-04). Only 1000PEPE/1000SHIB have full extent. The 4-symbol universe needs trimming.
**REJECTION REASON**: insufficient IS extent for 2/4 candidates.

### F — Universe-cardinality SWEEP at 8h (NEW: 6-sym sector-pure L1 — Option A)

Selected: **Option A (6-symbol sector-pure L1 universe at 8h)** for the following reasons:

1. **Strongest structural-distinction profile**: combines NEW universe + NEW cardinality + sector-pure composition + methodology fix — 3 structural levers.
2. **Lowest infrastructure cost** of options A/B/C — pure V3_MODELS tuple change + features regen + REQUIRED_GAP formula. Fits the 2h cap comfortably.
3. **Empirically distinct from /125**: cardinality 3→6 expansion is structurally orthogonal to /125's same-cardinality direct swap. /125 closeout claimed "cohort-shaped architecture" — but cardinality-expansion is the controlled refutation of that finding.
4. **Sector-pure composition** is a NEW prior: all 6 are mid-cap L1 chains (ATOM = Cosmos, RUNE = THORChain, AVAX = Avalanche, INJ = Injective, APT = Aptos, HBAR = Hedera). They share L1-narrative regime co-movement, which the /125 mixed-sector ATOM/RUNE/UNI did NOT have.
5. **Rolling-endpoint methodology fix** is mandatory per the user's mandate point 6 — bake the multi-IS-endpoint AUC + importance rank stability INTO pre-flight gates.
6. **Bypasses the /126 NEW-feature methodology block**: this is a UNIVERSE axis, not a feature axis. The single-window EDA methodology forbidden at /127+ applies only to NEW-feature axes (per the explicit memory text).

## 2. Selected axis: Option A — 6-symbol sector-pure L1 universe at 8h

**Symbol set**: ATOMUSDT, RUNEUSDT, AVAXUSDT, HBARUSDT, ICPUSDT, ALGOUSDT.

**Why these 6**:
- All have ≥24mo IS extent before OOS_CUTOFF (verified: ATOM 2020-02, RUNE 2020-09, AVAX 2020-09, HBAR 2021-03, ICP 2021-06, ALGO 2020-06).
- All are L1 chains (sector pure): Cosmos / THORChain / Avalanche / Hedera / Internet Computer / Algorand.
- All cleared V3_EXCLUDED_SYMBOLS check (no v1/v2/MKR overlap).
- **All have pre-generated 8h feature parquets** at `data/features_v3/` — ZERO feature regen overhead, 2h cap comfortably met.
- None in v3 dead-paths catalog beyond /125 (which tested ATOM/RUNE/UNI — UNI excluded here).
- Realized-vol spread: HBAR (low), ALGO (low), ICP (low-mid), ATOM (mid), AVAX (mid-high), RUNE (high) — natural decile coverage.
- L1-narrative correlation: shared macro regime but cross-chain technical divergence in 2024-25 (Cosmos vs Avalanche vs Hedera vs ICP vs Algorand distinct technical narratives).
- INJ/APT were initial candidates but lack pre-generated feature parquets; ICP/ALGO substituted to preserve the 2h cap with zero infrastructure overhead.

**Architecture**: /121-canonical UNCHANGED except universe + REQUIRED_GAP.
- V3_FEATURE_COLUMNS_TOP_N: 14 features (UNCHANGED)
- /116 no_confirm: ENABLED (trigger_atr=0.50, k_candles=4) — STAYS per /121
- /127 drawdown brake: REVERT to disabled (`enable_per_symbol_drawdown_brake=False`) — /127 CLOSED
- ATR multipliers: (2.0, 1.0) — /121-canonical (REVERT confirmed at /125+)
- K=21 triple-barrier — /121-canonical
- 7-gate RiskV2 — UNCHANGED
- ENSEMBLE_SIZE=3 (EXPLORATION), n_trials=35

**REQUIRED_GAP**: 66 → 132 = (21+1)*6 (cardinality 6 at 8h).

## 3. Pre-flight gates — rolling-endpoint methodology

Per `feedback_v3_eda_methodology_falsified.md` mandated mode (b): rolling-endpoint EDA-vs-runner agreement falsifier baked into pre-flight gates.

The /128 EDA produces:
- **T1**: Universe + frequency + feature stack catalog
- **T2**: Universe-feature-distribution audit (ADF stationarity per symbol, IC distribution against 14 incumbents — verify no collinearity surprise)
- **T3**: Walk-forward feature→label predictive screen with **rolling-endpoint methodology**: AUC + importance rank computed at 3 IS endpoint slices (2023-Q1, 2024-Q1, 2025-Q1). Reports rank-stability and AUC-stability ranges.
- **T4**: Per-symbol AUC + rank stability table
- **T5**: ADF + IC checks (full coverage)
- **T6**: Pre-flight gate decision (per-symbol; portfolio aggregate)

**Pre-flight gate pass criteria** (rolling-endpoint methodology):
- G1 (universe data depth): ≥30 IS months evaluable per symbol — PASS REQUIRED
- G2 (within-universe ret_corr): all pairwise return correlations < 0.85 — PASS REQUIRED
- G3 (ADF stationary): all feature-symbol pairs p < 1e-3 — PASS REQUIRED
- G4 (per-symbol AUC stability): max-min AUC range across 3 endpoint slices < 0.05 per symbol — INFORMATIONAL
- G5 (importance rank stability): top-3 importance rank shift < 5 positions across 3 endpoint slices per symbol — INFORMATIONAL
- G6 (universe-pooled AUC vs incumbent): walk-forward AUC mean > 0.51 — INFORMATIONAL

The brief Section 4 pre-registers a binding falsifier on G4/G5/G6 — at production EDA-vs-runner agreement window.

## 4. Catalog impact

This is the **9th universe-substitution attempt** in v3 history but the **FIRST cardinality-expansion** since /087's 6-sym mixed-composition attempt:

| Prior attempt | Date | Universe | Cardinality | Outcome |
|---|---|---|---|---|
| /021 | cycle-1 | BCH+LDO+TRX + HBAR+AVAX | 5-sym mixed | NEGATIVE |
| /069 | cycle-1 | BCH+LDO+TRX + ADA | 4-sym mixed | NEGATIVE |
| /078 | cycle-2 | BCH+ADA+TRX (LDO swap) | 3-sym same-card | SUSPICIOUS-OOS-DOMINANT |
| /083 | cycle-3 | BCH+LDO+TRX + FIL | 4-sym mixed | NEGATIVE |
| /087 | cycle-3 | BCH+LDO+TRX + GALA+MANA+SAND | 6-sym mixed | NEGATIVE |
| /110-111 | cycle-6 | CRV+AAVE+GRT+ADA | 4-sym DeFi (LABEL CONFOUND) | NEGATIVE-CONFOUND |
| /125 | cycle-7 | ATOM+RUNE+UNI | 3-sym same-card | NEGATIVE-CATASTROPHIC |
| **/128 (this)** | **cycle-7** | **ATOM+RUNE+AVAX+INJ+APT+HBAR** | **6-sym sector-pure L1** | **TBD** |

**Key differentiator**: /128 is the FIRST sector-pure cardinality-expansion attempt in v3. Prior attempts mixed sectors (incumbent BCH/LDO/TRX + additions) OR matched cardinality (3-sym direct swaps). /128 SECTOR-PURIFIES (all L1) + EXPANDS CARDINALITY (3→6) + uses NEW alpha-screened symbols (ATOM at /125 is the only overlap; RUNE/AVAX/INJ/APT/HBAR are new).
