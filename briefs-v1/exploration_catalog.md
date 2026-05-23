# v1 EXPLORATION Catalog

Per `quant-iteration-v1` skill §"Iteration Cadence Discipline". Every EXPLORATION's Phase 8 diary appends a one-line entry below. CONFIRMATION iterations consume this catalog to bundle the best EXPLORATION axes.

**Cadence rule**: a CONFIRMATION cannot launch until ≥10 EXPLORATION precedents accumulate since the last CONFIRMATION (or since iter-v1/001 if no prior CONFIRMATION).

**Axis Rotation Discipline** (v1-only): if the last 5 EXPLORATIONs were all from the same axis family, the NEXT EXPLORATION MUST be from a different family. Phase 5.5 gate enforces this from brief Section 0.6.

Axis families: `feature-family`, `model-arch`, `labeling`, `universe`, `risk-primitive`, **`methodology`** (NEW 6th family added at iter-v1/001 to cover infrastructure / reporting / validation wiring iterations).

## Ledger

| iter-v1-NNN | YYYY-MM-DD | axis varied | axis family | IS Sharpe Δ | OOS Sharpe (informational) | verdict | confirmation candidate? |
| ----------- | ---------- | ----------- | ----------- | ----------- | -------------------------- | ------- | ----------------------- |
| iter-v1/001 | 2026-05-23 | methodology-layer wiring (PSR×3 + N_eff-corrected DSR + ADF + IC + dsr.json) | methodology | 0.0000 (invariant by construction; F1 trade-roster byte-identical IS=621, OOS=189) | +0.6637 (unchanged from BASELINE_V1.md; methodology axis preserves predictions) | EXPLORATION-PROMISING (PROMISING-METHODOLOGY subtype) | NO (non-compoundable measurement substrate — sister to v3 PROMISING-MECHANICAL; informs iter-v1/002+ but not bundled into CONFIRMATION as an "edge ingredient") |

### Detailed verdict notes — iter-v1/001

`F1=PASS (trade roster byte-identical: IS=621, OOS=189); F2=PASS (5/5 artifacts: comparison.csv 4 new rows + dsr.json × 2 halves + adf_test.csv × 2 halves + ic_matrix.csv × 2 halves); F3=PASS-with-caveat (n_eff=50==n_trials=50; svd_randomized_no_compression; truthful PCA outcome distinct from naive_fallback per Critic resolution of Q2 in review.md); F4=PASS (13 raw-α failures; 1 undeclared vol_vwap to be added to iter-v1/002+ exception list; 37-unit margin to 50 ceiling); F5=PASS (PSR monotonic both halves: IS 0.7231≥0.1224, OOS 0.7430≥0.3325). Measurement layer wired; trade roster invariant; informs iter-v1/002+ via IC-redundancy structure (0.851 MR×momentum, 0.822 trend×volatility cross-family) + ADF exception list expansion (vol_vwap) + per-cell N_eff design correction (LM Master Phase 7.4 Rec #2: n_eff_per_cell_median ≈ 9 vs global flatten 50).`
