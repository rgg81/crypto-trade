# iter-013 RISK NOTE — bounded directional (TSMOM) sleeve on the iter-011 neutral book

**Date:** 2026-07-01 · **Track:** portfolio-tradfi · **Role:** Risk Engineer
**Cadence:** EXPLORATION (IS-only, `< OOS_CUTOFF 2025-03-24`; **OOS HIDDEN** — no `--confirm`, no OOS number computed)
**Neutral book entering iter-013:** iter-011 = MOM + 0.5·LTR — net **+0.33** / **11/16** positive years / bull **+0.26** / bear **+0.35** / chop **+0.60** / maxDD **−49%** / net-beta **+0.00**.
**User mandate (2026-07-01):** relax PURE market-neutrality with a SMALL, controlled directional tilt to win the low-dispersion bull melt-up years the cross-sectional neutral book structurally misses (2013/2017/2019). USER BAR: net **≥0.5 AND positive EVERY year (16/16)**.
**Source of truth (every number below):** `analysis/portfolio/tradfi/iter_013_directional.py` (IS-only). Reproduce: `uv run python analysis/portfolio/tradfi/iter_013_directional.py`.

---

## 1. Mechanism — bounded blend of a FROZEN neutral engine + a TSMOM directional sleeve

The neutral book is CROSS-SECTIONAL (ranks names against each other, dollar/sector-neutral → net market exposure ≈0). In a melt-up where dispersion collapses there is no cross-sectional spread → it earns ~0 (2017 −1.11, 2019 −0.96 on the neutral book). A TIME-SERIES-MOMENTUM sleeve (Moskowitz-Ooi-Pedersen 2012) instead sizes each name by the **sign of its OWN trailing 12-month total return** (long uptrenders / short downtrenders), inverse-vol scaled. On a stock universe in a bull market MOST names uptrend → TSMOM is **NET-LONG** → it carries market beta → it earns the melt-up. This is the theory-pinned way to add a CONTROLLED tilt without abandoning the neutral engine.

```
tsmom_raw = gross_norm( sign(close/close.shift(252) - 1) / rvol )     # NET-LONG in bull tape
neutral   = gross_norm( iter011.mom_ltr_raw(pn, 0.5) )                # FROZEN neutral engine
book(lam) = (1 - lam)*neutral + lam*tsmom_raw                         # signal-level blend, lam SMALL
net, w    = iter003.banded_net(book(lam), ret_fwd, delta=0.005)       # band + 15% vol-target UNCHANGED
```

- **Signal-level blend, both unit-gross first** → `lam` is a clean mixing fraction. Neutral contributes ~0 net dollar; tsmom contributes +beta; so the combined net-long tilt ≈ `lam·(tsmom net-long)` — **monotonic in lam**. The band's own gross-norm preserves the net/gross RATIO, so the tilt **survives** into the deployed book (a per-bar directional tilt is NOT a uniform gross scale, so unlike iter-008's de-lever it is not re-normalized away).
- **12m (252d) lookback + sign() are THEORY-PINNED, NOT swept.** sign() (not the raw return) is canonical MOP: every name contributes equal SIGNED gross, inverse-vol scaled — no single +300% trender dominates. `lam=0` reproduces iter-011 (pre-registered identity, PASS).

## 2. Pre-registered settings (SMALL, NOT max-net-fit)

- **TSMOM_LOOKBACK = 252** (12m) — Moskowitz-Ooi-Pedersen trend horizon; fixed, not swept.
- **lam ∈ {0.15, 0.25, 0.35}** — pre-registered SMALL mixing fractions. We do **not** max-net-fit lam; we pick the smallest lam that fixes the melt-up years without blowing up net-beta/bear.
- **band delta = 0.005 / 15% vol-target / 6 bps/side cost** — inherited from iter-003/core, UNCHANGED.
- **VIX brake base=20 / floor=0.50, `.shift(1)`** — iter-008, UNCHANGED; outer scalar on the vol-targeted net (only place a de-lever survives).

## 3. Controlled-tilt quantification — the beta we are buying

Two IS-only measures: **net-long fraction** = mean `Σw / Σ|w|` of the deployed banded book (static, leverage-free); **net market-beta** = OLS beta of the deployed vol-targeted daily net on the **equal-weight universe daily return** (the PIT market proxy — the universe excludes SPY/QQQ).

## 4. IS results (2010-2025, IS-only)

**TSMOM standalone** (same band/vol-target/cost): net **+0.88** / **12/16** / net-beta **+0.32** / net-long **+0.51** / maxDD **−32%** / bull **+1.97** / bear **−1.69** / chop **−0.55**. Strongly directional; its own bad years are reversals/bears (2016 −1.27, 2022 −0.52, 2015 −0.12) and the 2019 V-bottom whipsaw (only +0.13).

**Bounded combined book:**

| lam | net | +yrs | net-beta | net-long | maxDD | turn | bull/bear/chop |
|----:|----:|:----:|---------:|---------:|------:|-----:|----------------|
| 0.00 (neutral) | +0.33 | 11/16 | +0.00 | +0.00 | −49% | 0.0961 | +0.26/+0.35/+0.60 |
| 0.15 | +0.51 | 11/16 | +0.07 | +0.08 | −37% | 0.0948 | +0.62/−0.08/+0.38 |
| **0.25** | **+0.63** | **13/16** | **+0.12** | **+0.15** | **−32%** | 0.0939 | +0.87/−0.31/+0.18 |
| 0.35 | +0.72 | 13/16 | +0.17 | +0.22 | −28% | 0.0917 | +1.10/−0.62/+0.11 |

**Per-year melt-up fix (neutral → combined):** 2013\* +0.46→+1.40 (0.25), 2017\* **−1.11→+0.28** FLIPS at lam≥0.25, 2020 −0.13→+0.50. **2019\* NEVER flips** (−0.96→−0.71 at 0.25, −0.58 at 0.35): the 12m trend signal was still SHORT entering the 2019 rally because names had crashed in 2018-Q4 — the classic TSMOM V-bottom whipsaw. **2010** (ragged: <252d history → 0 TSMOM weight) and **2018** (Q4 Fed-tightening bear; net-long HURTS) also stay negative.

**VIX brake — added-bear management (bear WITH/WITHOUT):**

| lam | bear | bear+VIX | maxDD | maxDD+VIX | +yrs | +yrs+VIX | net | net+VIX |
|----:|-----:|---------:|------:|----------:|:----:|:--------:|----:|--------:|
| 0.15 | −0.08 | **+0.10** | −37% | −33% | 11/16 | 12/16 | +0.51 | +0.49 |
| 0.25 | −0.31 | **−0.20** | −32% | −28% | 13/16 | 13/16 | +0.63 | +0.61 |
| 0.35 | −0.62 | −0.58 | −28% | −26% | 13/16 | 13/16 | +0.72 | +0.71 |

The exogenous VIX brake lifts bear at every lam and cuts maxDD ~4pts, at essentially zero net cost (−0.02) — it genuinely manages the beta the directional sleeve adds. **Recommend VIX brake ON.**

## 5. Chosen setting + verdict

**Chosen: lam = 0.25, VIX brake ON.** It is the smallest lam that materially fixes the melt-ups (2017 flips to +0.28, 2013 strengthens, 2020 flips) and lifts the year count to **13/16**, at a genuinely **CONTROLLED** tilt: **net-beta +0.12** and **net-long +0.15** (≈1/8 of a long-only ~1 beta; 85% of the book stays neutral). lam=0.35 buys +0.09 more net purely by taking on **double the bear drag** (−0.31→−0.62) and higher beta — that is max-net-fitting the tilt, which the mandate forbids; 0.25 is the disciplined pick.

**Honest read vs the USER BAR (net≥0.5 AND 16/16):** the net≥0.5 half is **MET and exceeded** (+0.63 at lam=0.25; even lam=0.15 clears at +0.51). The 16/16 half is **NOT reached** — best-achievable is **13/16**. Three residual negatives are structural, not fixable by a *small* tilt: **2010** (ragged — no 12m TSMOM history yet), **2018** (Q4 bear — any net-long sleeve loses; VIX brake only softens), **2019** (TSMOM whipsaw off the 2018 V-bottom — the trend signal points the wrong way into the rally). Relaxing neutrality **does** buy the two low-dispersion melt-ups it was designed for (2013, 2017) plus 2020, at a controlled +0.12 beta — a real accretive directional step, but it does **not** clear the perfect-year bar. I do **not** overfit lam to chase 16/16.

## 6. Leak safety + honesty

- **Leak PASS.** In-script future-bar self-check (corrupt close + ret_fwd after a cutoff → combined AND combined+VIX IS net before the cutoff bit-identical, atol 1e-12, lam=0.25). TSMOM reads `close.shift(252)` + trailing-63 rvol (pure past); the blend feeds the strictly causal iter-003 band; VIX is ffill-then-`.shift(1)`.
- **Identity PASS.** lam=0 reproduces the iter-011 neutral book (net +0.33, 11/16, beta +0.00).
- **OOS HIDDEN.** Every metric is the IS slice only; no OOS number is computed (no `--confirm` path exercised). Do NOT tune lam / the 12m lookback.
- iter-001..012 / core / neutral signal UNCHANGED; `data/` untouched; suite green (63 passed).

## Handoff to Quant Research

Bounded TSMOM is a **PROMISING controlled-directional accretive step**: net +0.33→**+0.63** at a controlled **+0.12 beta**, +yrs 11→**13/16**, fixing 2013+2017+2020. It does **not** clear the 16/16 perfect-year bar (2010 ragged, 2018 Q4 bear, 2019 TSMOM whipsaw persist). QR may adopt lam=0.25+VIX, choose a different pre-registered lam, or reject — but note that pushing lam higher only buys net by adding bear/beta, and the residual negatives are structural (not a tuning problem). If a genuine 16/16 is required, the 2019 whipsaw argues for a *faster/blended* trend horizon or an explicit V-bottom re-entry rule — a separate iteration, NOT a lam tweak.
