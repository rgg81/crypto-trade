# iter-v1/033 Bundle EDA — Numerical Highlights

## 1. Per-Symbol Baseline OOS Monthly Sharpe (annualized)

- **BTC** baseline OOS monthly Sharpe = 0.502
- **ETH** baseline OOS monthly Sharpe = 1.0215
- **LINK** baseline OOS monthly Sharpe = 0.884
- **LTC** baseline OOS monthly Sharpe = -1.1305
- **DOT** baseline OOS monthly Sharpe = -0.094

## 2. Specialist Pairwise OOS Pearson Correlation (monthly PnL)

| Pair | OOS Pearson | IS Pearson |
|---|---|---|
| /018 ↔ /019 | +0.1418 | -0.2471 |
| /018 ↔ /028 | +0.3256 | -0.0793 |
| /018 ↔ /031 | +0.2890 | +0.0376 |
| /019 ↔ /028 | +0.2539 | +0.2657 |
| /019 ↔ /031 | -0.3542 | +0.1631 |
| /028 ↔ /031 | -0.1550 | +0.3674 |

**Interpretation**: bundle additivity requires OOS Pearson < 0.50 across pairs. Any pair exceeding 0.50 contributes correlated-drag to the bundle.

## 3. Specialist Replacement Table (per-symbol OOS Sharpe)

| Symbol | Baseline OOS Sharpe | Specialist | Specialist OOS Sharpe | Δ |
|---|---|---|---|---|
| BTC | +0.5020 | BASELINE (no change) | +0.5020 | +0.0000 |
| ETH | +1.0215 | /019 ETH+gate | +0.6990 | -0.3225 |
| LINK | +0.8840 | /018 LINK | +0.9789 | +0.0949 |
| LTC | -1.1305 | /028 LTC+atr_sl=1.0 | +0.3310 | +1.4615 |
| DOT | -0.0940 | BASELINE (no change) | -0.0940 | +0.0000 |

## 4. Bundle Sharpe Projection

| Scenario | Computation | Value |
|---|---|---|
| Naive RMS uncorrelated (upper bound) | sqrt(sum(s_i^2) / n) | +0.6029 |
| Naive average per-symbol (lower bound) | sum(s_i) / n | +0.4834 |
| Half-diversified (sum/sqrt(n)) | sum(s_i) / sqrt(n) | +1.0809 |
| Option A multi-seed deflated (× 0.65 lottery) | half-div × 0.65 | +0.7026 |
| Option B (A + /031 axis-only +0.21) | Option A + 0.21 | +0.9126 |

**Key Verdict for /033**: bundle multi-seed mean projected ≈ +0.70 (Option A) or +0.91 (Option B).
Hard merge floor +1.0 requires Option B with NO basin drift (i.e. axis stack actually compounds). The +0.21 /031 axis-only component is the LOAD-BEARING uncertainty.

## 5. CRITICAL — /032 Frozen-HP Adjudication

- /031 headline +1.04 OOS Δ = **axis +0.21** + **basin +0.83**
- The +0.83 basin component is SINGLE-DRAW LOTTERY — NOT compoundable at multi-seed
- Bundle projections use ONLY the **axis +0.21** component (Option B)
- Option A (without /031) is the conservative baseline — same as Option B - 0.21