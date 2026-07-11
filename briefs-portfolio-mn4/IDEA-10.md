# IDEA-10 — Born-Diverse Ensemble (research brief)

**Track:** MN4 blind tournament · **Idea:** 10 · Born-Diverse Ensemble
**Pair:** QR+QE (Opus 4.8 — Fable rate-limited this session; user-directed. Disclosed per charter.)
**Date:** 2026-07-11 · **Status:** FROZEN construction, IS-gate FAIL → NOT reveal-ready

## 1. Hypothesis (the falsifiable claim)

Combine 3-4 genuinely-orthogonal slow signals into one book FROM BIRTH at
**inverse-trailing-vol weights** (a-priori, NOT IS-Sharpe-optimized). Claim:
**composite Sharpe ≥ best member AND composite maxDD shallower than every member,
via measured decorrelation.** If members are too correlated to add anything,
that is a FINDING (mechanism overlap), not a tuning failure.

Market-NEUTRAL, beta-hedged at the **composite** level (member neutrality does
not automatically compose). Per-construction Layer-2 crisis throttle.

## 2. Frozen construction (byte-exact)

| Axis | Value |
|---|---|
| Universe | PIT top-20 by trailing 30c quote-volume, ex-stables (`pit_topn_universe`) |
| Cadence | weekly — `rebal=21` candles (7d) |
| Weighting | `rank_neutral` (dollar-neutral, cross-sectional rank) per member + composite |
| Cost | 5 + 2.5 bps taker+slip + funding ON; 2×-cost GT twin at 10 + 5 bps |
| `weight_cap` | 0.12 (per-name |w| cap, same-leg pro-rata redistribution) |
| `min_members` | 8 (feasibility floor) |

**The 4 members** (each gross=1.0, weekly, funding ON, NO hedge, NO throttle in
Pass 1 — raw sleeves):

| # | Name | Mechanism | Lookback | Crypto-native rationale |
|---|---|---|---|---|
| M1 | `ts_mom90` | sum of BTC-RESIDUALIZED returns | 90c (30d) | Reflexive trend persistence; canonical L/S momentum on idiosyncratic movement, not BTC beta |
| M2 | `carry21` | −trailing mean funding rate | 21c (1w) | Perp carry: short crowded longs (high funding), long crowded shorts. BIS WP 1087 positioning edge |
| M3 | `reversal21` | −trailing 21c return | 21c (1w) | Cross-sectional mean-reversion; ANTI-correlated to M1 by design |
| M4 | `ownvol90` | −own_pctl(rv90, 270c) | 90c/270c | Vol-regime tilt: long names whose own vol recently contracted (managed-variance) |

**Composite weight rule (a-priori, NOT IS-Sharpe):**
`composite_signal[t,c] = Σ_i w_i[t-1] · z_cs(signal_i[t,c])`, where
`w_i[t] = (1/σ_i[t]) / Σ_j (1/σ_j[t])`, `σ_i[t]` = trailing 90c per-candle std
of member *i*'s Pass-1 engine returns (past-only). Equalizes risk contribution
across sleeves — the classic Carver/LdP risk-equalized ensemble. Consumed at
[t-1] inside the composite (the engine also consumes the composite signal at
[k-1] → two layers of past-only lag).

**Composite-level beta hedge (HedgeOverlay):**
- BTC leg ALWAYS on, sized from `mn_beta.rolling_beta` (270c, shrink 0.33, clip [0,3]).
- ETH leg armed when trailing-270c realized β of the BTC-hedged book on ETH > 0.10.
- Hedge legs pay taker+slip+funding like any position (no free hedge).

**Per-construction Layer-2 crisis throttle (principle-anchored):**
- Vol-target: `target_ann=0.20` (the standard CTA 20% target), `vol_lookback=90`, `max_lev=1.5`. Scales gross inverse-realized-vol → automatic crisis de-risk.
- DD brake: `threshold=0.15` → `scale=0.5` (half gross), `recovery=0.075`. Hysteresis on causal trailing DD.
- Both past-only, applied only at rebal steps (weekly cadence preserved).

## 3. IS scorecard (full)

Universe / funding / regime coverage (IS = 4929 candles, 2020-01-01 → 2024-06-30):
funding resolved for 745/747 panel syms (1 universe member LITUSDT NaN-masked);
regime occupancy CRASH 13.2% / MANIA 18.9% / CHOP 68.0% (all ≥ 5%).

### 3.1 Per-member + composite

| book | Sharpe 1× | Sharpe 2×-GT | maxDD | turn/yr | annRet | win |
|---|---|---|---|---|---|---|
| ts_mom90 | +0.931 | — | -47.3% | 41.5× | +33.0% | 0.47 |
| carry21 | **+1.250** | — | -53.4% | 53.5× | +47.0% | 0.52 |
| reversal21 | -0.906 | — | -89.5% | 75.9× | -37.4% | 0.50 |
| ownvol90 | -0.561 | — | -78.7% | 44.2× | -23.5% | 0.48 |
| **COMPOSITE** | **+0.496** | **+0.277** | **-29.7%** | **40.1×** | **+8.9%** | **0.51** |

### 3.2 Member correlation matrix (the diversification diagnostic)

```
            ts_mom90  carry21  reversal21  ownvol90
ts_mom90      +1.000   +0.100      -0.521    -0.627
carry21       +0.100   +1.000      -0.097    -0.192
reversal21   -0.521   -0.097       +1.000    +0.282
ownvol90     -0.627   -0.192       +0.282    +1.000
```
**Median pairwise member corr = -0.144 (genuinely ORTHOGONAL / anti-correlated).**
Mean inverse-vol weights (post-warmup): ts_mom90 0.240 · carry21 0.269 · reversal21 0.233 · ownvol90 0.271 (nearly equal risk budget — vols are comparable).

### 3.3 Composite per-year / per-half Sharpe

```
per-year: 2020:-0.33  2021:+2.28  2022:+0.30  2023:-0.44  2024:-1.36
per-half: 2020h1:-1.78 2020h2:+0.56 2021h1:+2.29 2021h2:+2.27
          2022h1:-0.28 2022h2:+0.87 2023h1:-0.61 2023h2:-0.31 2024h1:-1.36
```

### 3.4 Regime buckets (composite)

| bucket | n | Sharpe | β_BTC |
|---|---|---|---|
| CRASH | 637 | **-1.005** | -0.008 |
| MANIA | 912 | +0.235 | -0.039 |
| CHOP | 3290 | +0.802 | -0.022 |

### 3.5 Composite beta (post-hedge, realized)

Median rolling-270c β: **β_BTC = -0.026**, β_ETH = -0.014 (both ≈ 0 — the
composite-level HedgeOverlay delivers measured neutrality; member neutrality
indeed did NOT compose without it, as the directive warned). ETH leg armed on
4/232 rebals (rare). Hedge skipped on 1 rebal (warmup).

### 3.6 Layer-2 throttle forensics

DD-brake fired on **167 / 232** rebals (the book was braked ~72% of IS —
vol-target + the 2022 crash kept gross halved much of the time).
`book_scalar`: min 0.50 · med 1.00 · max 1.00. Vol-target: 20% ann / 90c / cap 1.5×.

### 3.7 Cost coverage

gross_lev mean 0.68 · turn/candle 0.0373 · funding drag −0.6 bp/candle (shorts
EARN positive funding on average — mania-era crowding) · cost_side 7.5 bp.
Ann turnover 40.1× → 3.0% one-way drag/yr. **2×-cost GT Sharpe +0.277 SURVIVES** the cost wall.

## 4. Falsifiable claim — verdict

| Claim | Result |
|---|---|
| composite Sharpe ≥ best member (+1.250) | **FALSIFIED** (+0.496, trails by -0.753) |
| composite maxDD shallower than EVERY member | **CONFIRMED** (-29.7% vs -47.3%/-53.4%/-89.5%/-78.7%) |
| members too correlated to add (mechanism overlap) | NO — median corr -0.144 (orthogonal) |

**The finding (honest, the directive's complementary case):** the members ARE
genuinely orthogonal (not overlapping) and DO diversify the DD (composite maxDD
~40% shallower than the best member, ~60% shallower than the worst). But TWO of
the four members (`reversal21` -0.91, `ownvol90` -0.56) are individually
negative-Sharpe over IS. **Inverse-vol weighting is return-agnostic** — it
equalizes risk contribution, not expected return — so it assigns the two losing
sleeves ~equal risk budget (0.23-0.27 each) and they drag the composite Sharpe
below the best member. This is NOT a tuning failure and NOT mechanism overlap;
it is the structural limitation of risk-equalization when some members are
negative-expected-return. Dropping the two losers post-hoc would be IS-selection
(mining) and is refused.

## 5. IS gate (principle-anchored, NOT IS-fitted)

| # | Check | Value | Verdict |
|---|---|---|---|
| a | Sharpe 1× > 0 | +0.496 | PASS |
| b | Sharpe 2× > 0 (cost-survival) | +0.277 | PASS |
| c | \|β_BTC post-hedge\| < 0.30 | -0.026 | PASS |
| d | CRASH-bucket Sharpe ≥ -0.5 | **-1.005** | **FAIL** |
| e | ≥ 130 IS return obs | 4838 | PASS |

**GATE VERDICT: FAIL → NOT reveal-ready.** The CRASH-bucket Sharpe -1.005 is
decisive: the charter requires "a winner in EVERY market condition (bull / bear
/ chop / crash / mania)", and the composite's alpha is sharply negative in the
acute regime despite the hedge (β ≈ 0 in crash) and the throttle (brake fired
167×). The throttle reduced the magnitude of crash losses (good for maxDD) but
cannot fix the Sharpe *sign* — the underlying alpha is regime-dependent
(mania-heavy: 2021 +2.28; 2023/2024 negative).

## 6. Risk mitigation / what is measured

- **Composite-level beta hedge**: HedgeOverlay BTC always + ETH armed; measured
  post-hedge β_BTC -0.026 (target: |β| < 0.30, achieved |β| < 0.03).
- **Layer-2 throttle**: vol-target 20% + dd_brake 15%→0.5×; brake fired 167×.
- **Cost-survival**: 2×-cost Sharpe +0.277 (survives); weekly cadence + low gross.
- **Concentration**: `weight_cap=0.12` per-name, `min_members=8` feasibility floor.

## 7. What this resolved (the value of the experiment)

1. **Diversification-as-design DELIVERS on the robustness axis** (maxDD
   -29.7%, cost-surviving, β ≈ 0) — the most controlled-risk book by
   construction, exactly the charter's "very controlled risk" mandate. This
   part of the claim is real and measured.
2. **But diversification-as-design does NOT automatically deliver Sharpe** when
   some members are negative-expected-return: inverse-vol risk-equalization is
   return-agnostic. This is a clean, generalizable structural finding.
3. **The all-weather bar is not met**: CRASH Sharpe -1.005, 2023/2024 negative.
   The ensemble inherited the members' mania-dependence.

## 8. NOT reveal-ready — banked as a documented finding

No holdout token spent. The construction is frozen byte-exact
(`mn4_idea10_signals.py` + `mn4_idea10_run.py`); the IS scorecard is banked in
`data/mn4_idea10/scorecard.json`. A holdout reveal is **refused** because the IS
gate fails on a structural, charter-anchored check (CRASH Sharpe). The 2-year
holdout remains pristine for a genuinely all-weather construction.
