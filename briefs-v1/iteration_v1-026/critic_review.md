# Critic Review — iter-v1/026

**Type**: Sanity slot (pre-CONFIRMATION cross-correlation check, not a full EXPLORATION)
**Adjudication**: SOFT-PASS with 2 binding remediations
**Remediation #1**: Handled by QE (CSV persistence) — see below
**Remediation #2**: Handled in /027 brief framing (METHODOLOGY VALIDATION, not merge candidate)

---

## Critic Adjudication Summary

### Overall Verdict: SOFT-PASS

/026 is a sanity slot, not a full EXPLORATION. The cross-correlation analysis
is methodologically sound. Two binding remediations were issued:

### Remediation #1 (BINDING — QE responsibility)

**Finding**: `bundle_replacement_analysis.py` lines 181-198 compute the
production-semantic correlations (`pool_minus_LINK_ETH × LINK_specialist` and
`pool_minus_LINK_ETH × ETH+gate_specialist`) but only print them to stdout,
not persist to CSV.

**Required action**: Add 5-10 lines to write
`analysis/iteration_v1-026/replacement_pool_correlation.csv` with schema:
`pair, pearson_is, pearson_oos, pearson_combined, spearman_is, spearman_oos,
spearman_combined, threshold, pass, n_months_is, n_months_oos`.

**Routing rule**: If both replacement-pool Pearson < 0.50 → /027 CAN PROCEED
under METHODOLOGY VALIDATION framing. If either ≥ 0.50 → escalate to QR for
bundle composition revision.

**Status**: APPLIED. Results (from generated CSV):

| Pair | IS Pearson | OOS Pearson | Combined Pearson | PASS |
|---|---|---|---|---|
| pool_minus_LINK_ETH × LINK_specialist | −0.0854 | **+0.4935** | +0.0685 | YES |
| pool_minus_LINK_ETH × ETH+gate_specialist | −0.0085 | −0.1412 | −0.0516 | YES |

Both pairs PASS. /027 PROCEEDS under METHODOLOGY VALIDATION framing.

The OOS LINK pair (+0.4935) was the primary concern — it's strictly below 0.50.
The original 3-pair pool×LINK breach (+0.526) was an artifact of LINK being
INSIDE the pool. Removing LINK from the pool drops the correlation from +0.526
to +0.494: the breach was self-correlation, not structural co-movement.

### Remediation #2 (BINDING — QR/brief responsibility)

**Finding**: The /025 brief locked /027 target at +1.10 to +1.30 OOS Sharpe,
but the /026 single-seed reference bundle is +0.57 — a +0.53 gap to target.
The /027 brief must revise this target BEFORE the backtest runs to prevent
post-hoc rationalization.

**Required action**: /027 brief Section 2 (prediction) must pre-register a
realistic multi-seed OOS Sharpe band of **[+0.40, +0.75]**, NOT [+1.10, +1.30].
The +1.10–+1.30 target was incongruent with the catalog's own /018 entry
("bundle Sharpe target ≥+0.70 requires 5+ specialists at ~+0.50-0.80 each
with cross-correlation ≤0.3") and the observed D (LTC) OOS Sharpe of −1.05.

**Status**: TO BE APPLIED in /027 brief. This is QR domain.

---

## Key Critic Findings

### Finding 1 — 3-pair mandate: YELLOW

The original 3-pair mandate (pool × LINK, pool × ETH+gate, LINK × ETH+gate)
showed one OOS breach: pool × LINK OOS = +0.526. This is YELLOW per routing
rules (1 of 2 required-pair breach → flag for weight adjustment or specialist
removal; NOT RED = no bundle composition revision required before /027).

### Finding 2 — Production-semantic: GREEN (post-remediation)

The binding diagnostic is NOT the 3-pair mandate but the replacement-pool
correlations. The 3-pair mandate used the FULL POOL as one leg; the /027
bundle REPLACES LINK+ETH in the pool. Once LINK is removed, the OOS correlation
drops from +0.526 → +0.494 (PASS). The breach was self-correlation.

### Finding 3 — 5-Model 10-pair: YELLOW informational

C_link × E_dot OOS Pearson = +0.603 is a new pair breach not visible in the
3-pair mandate (because the 3-pair view aggregated D+E+A_btc as "pool"). This
is flagged for /027 Phase 7 QR evaluation: if multi-seed C × E Pearson stays
> 0.50, the bundle has unanticipated altcoin/L1 joint concentration.

### Finding 4 — Bundle Sharpe target: structural ceiling

Single-seed reference bundle = +0.57. Multi-seed regression expected to
LOWER this (C' from +0.98 → +0.80; G from +0.70 → +0.50). D (LTC) OOS =
−1.05 is the dominant drag. The /027 bundle will almost certainly NOT clear
the +1.0 merge floor. /027 verdict classification should be pre-registered as
CONFIRMATION-NEGATIVE-NO-MERGE (validating the architecture, not the edge).

---

## /026 → /027 Framing Decision

Per Critic adjudication, /026 changes the /027 framing:

**Before /026**: /027 = CONFIRMATION seeking MERGE at [+1.10, +1.30] OOS Sharpe.

**After /026**: /027 = **METHODOLOGY VALIDATION** (multi-seed validation of
cycle-3 per-cohort architecture); NOT a merge candidate. The 5-Model bundle
validates whether cycle-3's PROMISING ingredients hold under multi-seed
perturbation. Realistic target band [+0.40, +0.75].

This is an important distinction for the diary entry and cycle-4 planning:
- If /027 PASSES [+0.40, +0.75] under multi-seed → cycle-3 per-cohort
  methodology is VALIDATED as a structural improvement (below merge floor,
  but reproducibly positive).
- If /027 FAILS below +0.40 multi-seed → the methodology itself is suspect;
  cycle-4 needs a D-specialist or bundle re-composition before MERGE.

---

## Annotation on bundle_composition_validation.csv

The `bundle_composition_validation.csv` header clarification:

The +1.0063 IS Sharpe number visible in this file is computed over the
ADDITIVE-OVER-ALLOCATED bundle (full pool + LINK specialist + ETH specialist,
double-counting LINK and ETH). This was the initial additive estimate from the
`bundle_5model_estimate.py` script. It is NOT the REPLACEMENT-SEMANTIC
production bundle (which removes LINK+ETH from the pool before adding the
specialists).

The production-semantic LOCKED replacement bundle IS Sharpe = **+0.0640**
(monthly Sharpe, sqrt(12)) and OOS Sharpe = **+0.5700** — as reported in
`bundle_replacement_validation.csv`. The +0.57 OOS reference is the correct
single-seed anchor for /027 evaluation.

Do NOT cite the +1.0063 IS number from `bundle_composition_validation.csv` as
evidence of IS edge — it reflects the double-counted bundle semantics.

---

## Files Generated by QE Remediation #1

- `analysis/iteration_v1-026/bundle_replacement_analysis.py` — updated:
  added `spearman()` function + `per_sample_series` accumulator +
  `replacement_pool_correlation.csv` write block
- `analysis/iteration_v1-026/replacement_pool_correlation.csv` — NEW CSV
  persisting production-semantic replacement-pool Pearson + Spearman for
  both pairs × IS/OOS/combined with PASS column
