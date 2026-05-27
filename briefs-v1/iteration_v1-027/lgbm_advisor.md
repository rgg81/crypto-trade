# LightGBM Master Advisor — iter-v1/027 — Phase 4.5 (Pre-Design)

## Context
- CYCLE-3 CLOSING CONFIRMATION. METHODOLOGY VALIDATION (NO-MERGE pre-committed)
- Bundle: Pool A (BTC slice; ETH dropped at replacement) + C' LINK specialist + D LTC + E DOT + G ETH+gate
- /026 GREEN-WITH-FIX: replacement-pool×LINK +0.4935 / ×ETH+gate -0.1412 (both PASS); C×E 5-model OOS +0.6027 BREACH
- /026 single-seed bundle: OOS Sharpe +0.5722 / 205 trades

## 1. Multi-seed regression magnitudes — bundle target +0.45 modal

Modal regression at `--seeds 2 × ENSEMBLE_SIZE=5` is **18-22%** of standalone (NOT 50%) because ENSEMBLE_SIZE=5 inner already collapses half the basin variance.

| Specialist | Single-seed | Modal multi-seed | LM Master band |
|---|---:|---:|---|
| C' LINK | +0.9789 | **+0.78** | [+0.55, +0.85] |
| G ETH+gate | +0.6990 | **+0.52** | [+0.32, +0.62] |

Applied to /026 reference +0.5722: specialists regressed contribute ~-0.11 portfolio Sharpe.

**Modal bundle multi-seed OOS Sharpe = +0.45 to +0.50** — at the **NEGATIVE-leaning edge** of pre-registered [+0.40, +0.75]. Bundle more likely to land INERT/NEGATIVE than PROMISING-METHODOLOGY.

## 2. Cross-correlation at multi-seed — DISSOLVES, doesn't amplify

Pool×LINK_spec OOS +0.4935 driven by 2/15 months (2025-08, 2025-11 risk-on rallies). Multi-seed averages out asymmetrically → **predicted multi-seed +0.35-0.42** (regress ~0.10 below single-seed). PASS.

C×E +0.6027 single-seed breach is STRUCTURALLY different — signal-level co-movement (LINK+DOT share altcoin/L1 regime), not basin lottery. Multi-seed WILL NOT dissolve. **Predicted +0.55-0.60 (stays above 0.50)**. Binding cycle-4 finding: 5-Model bundle has unresolvable altcoin concentration.

## 3. Bundle composition stability — std-of-Sharpe ±0.25

Per outer-seed-cap-2 empirical: ±0.20 single specialist, ±0.30 5-model bundle. At modal +0.45-0.50 mean, 2-seed Pareto spans [+0.25, +0.70]. Engineering report MUST emit `specialist_stability.csv` with per-(inner, outer) seed OOS Sharpe.

## 4. DSR / PBO / PSR predictions

| Gate | Predicted band | Methodology PASS | Merge PASS |
|---|---|---|---|
| DSR | [+0.30, +0.65] modal +0.45 | **borderline** (threshold 0.50) | NO |
| PBO | [0.30, 0.45] modal 0.38 | YES | YES |
| PSR_monthly_vs_0 | [0.75, 0.92] modal 0.85 | informational | NO |
| PSR_monthly_vs_1 | [0.08, 0.22] modal 0.13 | INERT | NO |

**DSR borderline** — modal +0.45 with n_trials=35 × 2 seeds = 70 trials → E[max_SR] ≈ 3.10; annualized observed Sharpe +0.45 × √12 ≈ 1.56 → DSR ≈ 0.45. **Modal BELOW 0.50 threshold**.

## 5. Implementation risk — F-AXIS #1 hard-asserts MANDATE

/024 dispatch-defect lesson applies. Brief §3.1 replacement filter is correct in form but UNCHECKED.

**MANDATE runner hard-asserts before `comparison.csv` emission**:
```python
assert set(r.symbol for r in results_a_btc_only) == {"BTCUSDT"}, \
    f"F-AXIS #1: Pool A leakage"
assert all(r.model_name in {"C' (LINK specialist /018)", "C_prime", "C'"} 
           for r in results_c_spec), "F-AXIS #1: C' contamination"
assert sum(1 for r in all_results 
           if r.symbol == "ETHUSDT" and r.model_name == "A (BTC+ETH pool)") == 0, \
    "F-AXIS #1: Pool A ETH bleed-through after filter"
```

Emit `replacement_filter_audit.csv` per §10.5.

## 6. Verdict priors RECALIBRATED — 30/30/35/25/6/4

| Verdict | QR | LM Master | Rationale |
|---|---|---|---|
| PROMISING-METHODOLOGY | 50% | **30%** | -20pp; modal bundle +0.45-0.50 lands at NEG edge of [+0.40, +0.75] |
| INERT (now modal) | 30% | **35%** | +5pp; structural ceiling at +0.50 |
| NEGATIVE | 15% | **25%** | +10pp; LTC drag + C×E correlation push below [-0.10] |
| NEGATIVE-BELOW-BAND | 5% | **6%** | +1pp; absolute OOS below +0.40 floor |
| BLOCK | 5% | **4%** | -1pp |

## 7. Most important point

**The /027 bundle has STRUCTURAL CEILING at OOS Sharpe ~+0.50 driven by LTC drag (Model D -1.05) and altcoin concentration (C×E OOS Pearson +0.60) that single-seed regression magnitude alone cannot break; expect modal multi-seed mean +0.45-0.50 landing INERT band (35%), validating per-cohort architecture as STABLE but NOT LIFT-PRODUCING at current 5-Model composition.**

## 8. /027 multi-seed budget defensible

`--seeds 2 × ENSEMBLE_SIZE=5 = 10 paths/cell` defensible because:
- v3 precedent (`feedback_v3_outer_seed_cap_2_v3.md`) caps at 2 outer
- v1 /015 ran identical config 9.8-12h on 4 models
- METHODOLOGY VALIDATION framing → variance-reduction need moderate
- Pushing to --seeds 5 → 9-15h serial → VIOLATES 6h cap

Don't push higher at /027. /028+ targeting merge-floor → push to --seeds 3-5 with parallel infrastructure.

## 9. /028+ cycle-4 staging

- **PROMISING-METHODOLOGY (30%)** → /028 = 3-symbol pool composition test (BTC+ETH+LINK with specialists overriding LTC+DOT dropped) per Critic Option C
- **INERT (35% modal)** → /028 = **D-specialist axis MANDATORY**. LTC -1.05 is the dominant ceiling. Sister: sample-weighting OR XGBoost head-to-head
- **NEGATIVE (25%)** → /028 = re-question per-cohort fundamentally; revisit /018+/019 robustness
- **NEGATIVE-BELOW-BAND (6%)** → bundle structural ceiling crystallized; rebuild from 3-component baseline at /028

**The C×E +0.60 OOS correlation is cycle-4 axis seed REGARDLESS of /027 verdict** — altcoin de-concentration mechanism required (per-symbol weight cap on LINK+DOT OR DOT specialist with anti-LINK gate).

## What I Did NOT Recommend
- Hyperparameter retuning (would break "validates /018+/019" claim)
- Adding funding/OI features (closed at /023+/025)
- Dropping D/E from /027 (cycle-4 scope, NOT /027)
- n_trials reduction below 35 (TPE saturation)

## Closing

**Confidence MEDIUM**. The brief framing is structurally sound; falsifiers well pre-registered. My modal prediction (+0.45-0.50) differs from QR's modal (+0.55) by 1 magnitude — normal pre-design uncertainty.

**Single most important thing for QR**: LTC drag irrecoverable within /027 scope; C×E correlation won't dissolve at multi-seed (different mechanism); **cycle-4 D-specialist EXPLORATION mandatory regardless of /027 verdict**. Brief §11.1/§11.2 should converge on D-specialist as unconditional cycle-4 priority.

Track record: cycle-3 LM Master methodology track **6/6 perfect** (DUAL GATE + HARD BLOCK both load-bearing at /025); directional 2/8. Phase 7.4 will close out cycle-3 with the multi-seed truth.
