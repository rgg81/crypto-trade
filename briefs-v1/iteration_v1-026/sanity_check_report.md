# iter-v1/026 — Sanity Check Report (one-page summary)

**Date**: 2026-05-27
**Branch**: iteration-v1/026 (from iteration-v1/025 HEAD `d0f1585`)
**Scope**: Pre-CONFIRMATION cross-correlation sanity check
**Wall-clock**: ~25 minutes (well under the 15-30 min target)
**Verdict**: **YELLOW** (proceed to /027 with modified target band)

---

## Three key cross-correlation numbers (LM Master /025 §4 mandate)

| Pair | IS Pearson | OOS Pearson | Combined Pearson | Verdict |
|---|---|---|---|---|
| pool × LINK | +0.0601 | **+0.5260** | +0.1904 | **OOS BREACH** |
| pool × ETH+gate | −0.0795 | −0.1042 | −0.0855 | strongly safe |
| LINK × ETH+gate | −0.2572 | +0.1269 | −0.1035 | safe |

**OOS pool × LINK Pearson +0.5260** breaches the 0.50 threshold but is driven
by 2 of 15 OOS months (2025-08 and 2025-11 — joint risk-on rallies for both
the pool and LINK). Dropping either month brings Pearson below 0.45. Spearman
+0.489 is at-threshold (not above), confirming partial outlier inflation.

---

## NEW SURPRISE — 5-Model bundle 10-pair check

When the bundle is evaluated as the LOCKED 5-Model composition per /025
brief Section 11.6 (A_btc + C_link_spec + D_ltc + E_dot + G_eth_spec):

| Pair (OOS) | Pearson | Spearman | Verdict |
|---|---|---|---|
| **C_link × E_dot** | **+0.6027** | +0.4250 | **BREACH on Pearson** |
| 9 other OOS pairs | various | various | all PASS |

This breach was NOT visible in the original 3-pair mandate because the
3-pair view aggregated D + E + A_btc into "pool". Mechanism candidate:
LINK and DOT share altcoin/L1 risk-on regime exposure.

---

## /027 GREEN/YELLOW/RED Verdict

**YELLOW** — proceed with modifications.

- 3-pair mandate: 1 of 2 required pairs breached. Per routing rules YELLOW
  ("flag for weight adjustment or single-specialist removal").
- 5-Model 10-pair: 1 of 10 breached. Also YELLOW.
- NOT RED — no requirement for bundle composition revision before /027.
- NOT GREEN — /027 brief must acknowledge breaches in Section 2 prediction.

---

## Bundle Sharpe target validation — STRUCTURAL CONCERN

The /025 brief states /027 target = **+1.10 to +1.30 OOS Sharpe at multi-seed**.
Single-seed reference bundle Sharpe (per /025 LOCKED 5-Model composition):

| Component | OOS Trades | OOS Sharpe (sqrt(12) monthly) |
|---|---|---|
| A_btc_approx | 35 | +0.452 |
| C_link_spec | 48 | +1.086 |
| D_ltc | 34 | **−1.050** |
| E_dot | 46 | −0.091 |
| G_eth_spec | 42 | +0.677 |
| **BUNDLE (sum)** | **205** | **+0.570** |

- Single-seed reference bundle = **+0.57** (essentially same as baseline pool +0.57).
- Gap to /027 target lower bound (+1.10) = **+0.53 Sharpe units**.
- Multi-seed regression at C' (+0.98 → +0.80) and G (+0.70 → +0.50) is expected
  to LOWER not raise this estimate.
- Bundle MaxDD 49.18% is +15pp WORSE than baseline pool's 33.77%.

**The bundle target of +1.10 to +1.30 is structurally implausible** given the
heavy negative drag from Model D (LTC OOS Sharpe −1.05). The single-best
lever to lift the bundle is an LTC specialist (cycle-4 axis per /025 Path
Forward candidate 1) — but that is outside /027's scope.

Realistic /027 multi-seed target band: **[+0.40, +0.75]**.

---

## /027 readiness assessment

- **/027 can proceed**: YES.
- **BASELINE_V1.md anchor**: STABLE — comparison.csv IS Sharpe +0.2829 / OOS
  +0.6637 / IS trades 621 / OOS trades 189 ALL match bit-exactly with
  BASELINE_V1.md.
- **Required modifications to /027 brief**:
  1. Pre-register realistic multi-seed target band [+0.40, +0.75] (NOT
     [+1.10, +1.30]). This is the load-bearing modification — it prevents
     post-hoc rationalization at /027 closeout. The +1.10–+1.30 target was
     incongruent with the catalog's own /018 entry which said "bundle
     Sharpe target ≥+0.70 multi-seed mean requires 5+ specialists at
     ~+0.50-0.80 each with cross-correlation ≤0.3".
  2. Brief Section 7 (most important point) must flag C_link × E_dot OOS
     Pearson +0.603 — Phase 7 QR evaluation must report whether multi-seed
     dissolves this correlation.
  3. Brief Section 2 prediction must acknowledge that even if all gates
     PASS, the bundle is unlikely to clear the >1.0 OOS Sharpe MERGE floor.
     /027 verdict is most likely CONFIRMATION-NEGATIVE-NO-MERGE-but-PROMISING-
     INERT — confirming the per-cohort specialization architecture as
     stable while remaining below the basin-escape lift threshold.

- **Recommended /027 framing**: /027 is the **multi-seed validation of the
  per-cohort methodology** (cycle-3's primary methodology contribution),
  NOT a merge candidate. The 5-Model bundle architecture validates whether
  cycle-3's PROMISING ingredients hold under multi-seed perturbation — a
  necessary check before declaring cycle-3 closed.

---

## Path forward (cycle-4, post-/027)

Per /025 review Path Forward + the /026 evidence above:

1. **D_ltc specialist** (Model D' LTC) — `per-cohort-specialization-LTC`
   sister axis to /018's LINK methodology. /022 LTC EXPLORATION was
   NEGATIVE-catastrophic but as a global axis change; per-cohort isolation
   methodology has not been tested. HIGH priority for cycle-4.

2. **E_dot specialist** (Model E' DOT) — `per-cohort-specialization-DOT`
   similar rationale to D'.

3. **Drop D and E from the production bundle entirely** — if D and E baseline
   models are persistently net-negative in OOS, the optimal production
   ensemble is C' + G + A_btc-only (3 components, OOS Sharpe estimate
   approaching +0.90 single-seed reference).

These are NOT /027 scope. They are cycle-4 EXPLORATIONS.

---

**Sanity check complete. /027 GREEN-LIGHT with explicit modifications above.**
