# REVEAL-G-result — the MN3-G sealed-holdout reveal of the slow-c1 continuous book: **TIER = FAIL**

**Track:** MN3 (two-year sealed holdout, market-neutral). **Role:** Quant Researcher (Stage-2 reveal
execution + verdict). **Map scored against:** `briefs-portfolio-mn3/REVEAL-G.md` (FROZEN pre-reveal §5
decision map; construction hash-pinned §1). **Runner:** `analysis/portfolio/mn3_reveal_g.py` (new
measurement scaffolding; the CONSTRUCTION is imported byte-frozen from `mn3_exploration_g` +
`mn3_features` + `mn3_g_oof_slow` logic — zero parameter change). **Full execution log (the permanent
record incl. the audit banner):** `logs/mn3_reveal_g.log`. **Machine summary:**
`data/mn3_g_slow_full/reveal_g_summary.json`. **NOT committed** (the orchestrator commits + dates).

**THE ONE-PER-FAMILY-FOREVER HOLDOUT REVEAL FIRED EXACTLY ONCE. `MN3-G` IS SPENT FOREVER.** Audit
banner count = 1; `REVEAL-LEDGER.md` spend-line count = 1; the guard's own parser confirms `MN3-G`
is no longer available. This was a USER-AUTHORIZED override of the §0 governance concern (the
EXPLORATION-G IS TIER was FAIL on a *mechanism-provenance* falsifier; the user directed "just reveal
it, this data was not used" — the holdout is genuinely unseen for this construction, a clean 2-year
test). The Critic pre-flight was stopped by user direction.

> **MODEL NOTE (charter deviation, disclosed).** The MN3 charter mandates ALL AGENTS ON FABLE. Fable is
> **user-suspended this phase** (Fable-5 rate limit; user direction "continue on Opus"). This reveal was
> authored + executed on **Opus 4.8, NOT Fable** — same posture as DIAG-G / EXPLORATION-G / REVEAL-G.md.
> The construction was byte-frozen (hash-pinned) BEFORE the reveal; the holdout was sealed; `MN3-G` was
> unspent as of the pre-flight (ledger verified zero spends). Adversarial burden unchanged.

---

## 0. THE AUDIT BANNER (verbatim; the permanent one-per-family record)

```
========================================================================
MN3 HOLDOUT REVEAL — SANCTIONED, TOKEN SPENT (single-use FOREVER)
  token   : MN3-G
  window  : [2020-01-01T00:00:00Z, 2026-07-01T00:00:00Z)
  at      : 2026-07-11T19:35:24Z
  ledger  : diary-portfolio-mn3/REVEAL-LEDGER.md
  This banner + the ledger entry are the audit record. The token(s)
  above are now DEAD — a second reveal for these families is refused
  by this guard for the track's lifetime (PLAN §6.1).
========================================================================
```

Ledger line: `- SPENT token=MN3-G at=2026-07-11T19:35:24Z window=[2020-01-01T00:00:00Z,2026-07-01T00:00:00Z) note=family-reveal`

---

## 1. Pre-spend gates (the hard order; ALL passed BEFORE the token was spent)

| step | gate | result |
|---|---|---|
| 1 | SHA-256 construction pins (§1: mn3_exploration_g / mn3_g_oof_slow / mn3_split / IS parquet) | **all 4 MATCH** — construction byte-frozen |
| 2 | `mn3_panel_health()` FIRST | OK/DEGRADED (live-feed staleness only; holdout is historical — proceeded) |
| 3 | panel PRE-CLIP to `< 2026-07-01` | dropped **30 Stage-3 candles**; full panel T=7119 [2020-01-01 .. 2026-06-30], C=747; holdout candles = 2190 |
| 4 | MUST-1 purge assert (horizon 21) over IS+HOLDOUT | **PASS all 54 WF months** (last_train+21 < b_idx) |
| — | dress rehearsal (pre-spend, no token) | fit-loop **BIT-IDENTICAL** to frozen on 3 IS months; scoring stack reproduced frozen IS scorecard EXACTLY (+1.0376 / +0.7035 / −21.56%) |

The single guarded reveal was `build_g_matrix(panel, reveal_token="MN3-G")` — its internal
`mn3_guard_grid` spent the token, fired the banner, appended the ledger. No other code path touched the
guard. The OOF retrain then ran 54 months × 8 configs × 5 seeds (purge=21); Stage-3 candles never
entered the panel (max OOF candle = 2026-06-30 16:00).

---

## 2. THE HOLDOUT SCORECARD — the four §5 reads, realized vs FROZEN thresholds

Holdout `[2024-07-01, 2026-07-01)`, honest cost, as-shipped **THROTTLED** book (frozen NEUTRAL
disposition — NOT re-decided), n = 2189 scored candles.

| read | realized (holdout) | frozen §5 threshold | PASS/FAIL |
|---|---|---|---|
| **N — neutrality** (highest power) | β_BTC **+0.0164** (se 0.012), β_ETH **+0.0252** (se 0.008), crash-bucket β_BTC **+0.0501** (n=269 ≥30) | \|β_BTC\|≤0.15 AND \|β_ETH\|≤0.20 AND crash\|β_BTC\|≤0.25 | **N HOLDS** |
| **C — crash-preservation** (load-bearing) | CRASH net **−9.86 bps/cd** (t −1.59); fresh CRASH quintile-spread **t −2.87** | CRASH net > 0 AND quintile-spread t > 0 | **C BROKEN** |
| **D — drawdown** | maxDD **−35.90%** | controlled ≥ −33%; catastrophic < −45% | **elevated** (not catastrophic) |
| **S — edge** (lowest power; net-2× GT twin) | net-2× Sharpe **−0.2765** | positive ≥ +0.30; weak [−1.0,+0.30); clear-neg < −1.0 | **weak** |

**A FAIL trigger fired: C BROKEN.** The frozen MECE tier: `FAIL = ¬(N ∧ C ∧ D≥−45% ∧ S≥−1.0)`. Here
N HOLDS, D not-catastrophic (−35.90% > −45%), S not-clear-negative (−0.28 > −1.0) — but **C is BROKEN**,
which alone forces **FAIL**. The tier is what the frozen map says; no re-weight, no re-gate.

---

## 3. THE VERDICT, STATED PLAINLY: the crash-robust claim did NOT hold on 2 years of unseen data

**The flagship's cost-surviving crash-robust claim FAILED to generalize.** Two of its three pillars
did not transfer; the load-bearing one INVERTED:

- **Crash-robustness INVERTED (the FAIL).** On IS, CRASH was the book's BEST regime (+6.56 bps/cd,
  64.6% of P&L) and the fresh CRASH quintile-spread was **t +11.03**. On the holdout, CRASH is the
  book's **WORST** regime (**−9.86 bps/cd**, t −1.59) and the fresh CRASH quintile-spread **inverted to
  t −2.87** (right-signed would be > 0). This is not a weakening — it is a **sign flip**. The entire
  crowding-syndrome crash-robustness mechanism, the strongest signal the MN/MN3 effort had measured on
  IS, is an **IS artifact**: it does not survive out-of-sample.
- **Edge went weak-negative.** net-2× Sharpe **−0.2765** (net-1× −0.096; ann ret −5.85%; ann vol 26.4%).
  The book lost money at honest 2× cost in the holdout — below the +0.30 DEPLOY floor and below zero.
- **Drawdown was elevated.** maxDD **−35.90%** — ~14pp deeper than the IS −21.56% and past the −33%
  controlled floor (not catastrophic, so not itself a FAIL trigger, but well outside the IS profile).
- **Neutrality TRANSFERRED (the one pillar that held).** β_BTC +0.0164, β_ETH +0.0252, crash-bucket
  β_BTC +0.0501 — all comfortably inside the CONFIRMATION-A transfer bounds, at ~10–30× headroom. The
  BTC-only minimal-L2 projection generalized cleanly (the highest-power test). This is the only layer
  that confirmed out-of-sample.

**The §5.1 IS falsifier foreshadowed this exactly.** EXPLORATION-G's mechanism-provenance FAIL found
that the slow label's win was an **un-registered signal improvement** (IC +0.037→+0.050, gross
+12%→+20%), not the registered turnover cure. The reveal shows that un-registered "better signal" —
including its crash edge — **did not generalize**. The falsifier that closed G on IS predicted the
holdout outcome: the smuggled alpha was overfit.

---

## 4. The leak §0.5 worried about did NOT materialize — which makes the FAIL MORE damning, not less

`REVEAL-G.md` §0.5 disclosed a favorable-regime leak: I knew the holdout was "crash-heavy, mania-free"
and worried a strong result could be a crash tailwind. **The realized full-2-year composition is not
that window:** **CRASH 12.3% (n=270) / MANIA 5.0% (n=109) / CHOP 82.7% (n=1811)** — CHOP-dominated,
only marginally more crash than the IS 11.5%, and NOT mania-free. (The "crash-heavy, mania-free"
characterization was the 2026-H1 sub-slice from the *separate* CONFIRMATION-A reveal, not the full
holdout.)

Per the map's pre-committed logic (§0.5 defense 4, the load-bearing inversion): **a window with MORE
crash than IS is exactly where a spurious crash-robustness claim breaks — and it did.** The book was
handed a slightly crash-ENRICHED window (which should HELP a genuinely crash-robust book) and its crash
edge still inverted. The FAIL cannot be excused by "the earning regime was absent"; the earning regime
(CRASH, per IS) was over-sampled, and the book LOST there. That is a clean, high-power falsification.

---

## 5. Reported context (per the map; never a FAIL trigger)

- **Per-half path (net, throttled 1×):** 2024-H2 +0.03% (flat) · 2025-H1 **−16.71%** (−3.12 bps/cd, the
  loss) · 2025-H2 −1.47% (flat) · 2026-H1 **+7.98%** (+2.11 bps/cd, recovered). The damage is
  concentrated in 2025-H1; the book was flat-to-positive in the other three halves.
- **Regime buckets:** CRASH −9.86 bps/cd (t −1.59) · MANIA −3.30 bps/cd (t −0.51) · CHOP **+1.38 bps/cd**
  (t +0.77). Worst-bucket t −1.59. The book earns mildly in CHOP (the workhorse) and loses in both
  CRASH and MANIA — the exact inverse of the IS regime signature (IS earned in CRASH, lost in MANIA).
- **Throttle:** scalar<1 on 20.1% of scored candles (IS 18.7%), mean 0.9349, min 0.500. It fired at an
  IS-like rate but did not rescue: throttled Sharpe −0.096 vs un-throttled −0.076 (throttle mildly HURT
  return OOS), throttled maxDD −35.90% vs un-throttled −37.54% (throttle helped DD ~1.6pp). A scalar
  ∈[0.5,1] cannot manufacture positive alpha, and here it did not.
- **21-phase Sharpe:** min −1.199 / med −0.022 / max +1.258; **positive 10/21**. No phase lottery; the
  median ≈ 0 is consistent with the weak-negative headline.
- **Neutrality context:** rolling-270 \|β_BTC\| max 0.1472, within-0.10 on 89.4%; G3 max \|Σw\|/gross =
  0.0000 (perfect dollar-neutral); max single-name gross share 7.4% (well under any cap).
- **Turnover:** 63.6×/yr (IS 61.8×; under the 104× geometric ceiling).

---

## 6. IS-parity — book reproduced to ~1%; NOT bit-identical; root cause is a benign funding data-layer extent-dependence (NO leak)

The full-panel IS slice reproduced the frozen EXPLORATION-G IS scorecard to **~1%**, NOT bit-identical:

| metric | full-panel IS | frozen | delta |
|---|---|---|---|
| net-2× Sharpe | +0.7132 | +0.7035 | +0.010 |
| net-1× Sharpe | +1.0489 | +1.0376 | +0.011 |
| maxDD | −20.42% | −21.56% | +0.011 |
| turnover | 61.9× | 61.8× | +0.07 |
| pooled IC | +0.0475 | +0.0502 | −0.003 |
| CRASH quintile-t | +10.47 | +11.03 | −0.56 |
| rolling \|β_BTC\| max | 0.0728 | 0.0705 | +0.002 |

**Root cause (forensically pinned, disclosed in full).** The OOF-prediction IS-parity was NOT
bit-identical (max\|delta\| 0.219), and a targeted extent-invariance test (two IS-only builds of
different length, shared candles) localized the drift **entirely to the 6 funding-derived features**
(`fund_lvl_xz`, `fund_lvl_ownpctl`, `fund_mom21_xz`, `fund_mom63_xz`, `fund_abs_xz`, `mkt_fund_agg`);
**all 18 non-funding features are bit-identical / extent-invariant.** `blind_funding.load_funding` is
mildly panel-length-dependent (the `present[j]` all-NaN column mask + the `k ≤ T−2` last-candle drop),
so the funding features shift slightly on shared candles when computed on a longer panel. The `mkt_fund_agg`
robust-z amplifies a tiny funding shift into a larger feature delta, which propagates through the model.

**Why this is NOT a leak and does NOT touch the verdict:** (a) the panel was clipped to `< 2026-07-01`
BEFORE the build, so **no Stage-3 funding data entered** (verified: max OOF candle 2026-06-30 16:00);
(b) holdout funding features are past-only within the holdout (a settlement is bucketed to the candle it
is paid by; the feature is a trailing mean) — the extent-dependence is a static per-column mask, not a
per-candle future leak; (c) it is a property of the frozen construction's own data layer (the frozen
book run on a longer panel would produce the same slightly-shifted funding features), not a defect in
the reveal runner; (d) the book reproduced to ~1% — the construction is faithful. **Decisively, the FAIL
is robust to it:** C BROKEN fired with CRASH net −9.86 bps/cd and quintile-spread **t −2.87** — a
sign-flipped, high-magnitude falsification. A ≤1% funding-feature perturbation cannot flip a t −2.87 to
positive. The tier stands.

---

## 7. Pre-committed consequence (frozen §9; no rescue) — **FAMILY G IS CLOSED FOREVER**

Per REVEAL-G.md §6/§9, binding and executed:

- **The reveal is SPENT FOREVER.** `MN3-G` is dead (banner + ledger, 2026-07-11T19:35:24Z). No rescue,
  no second look, no re-parameterization, no re-gate, no "the funding-parity was off so discount it,"
  no "a favorable regime didn't fully materialize so discount it." **A FAIL is as final as a SUCCESS.**
  No adjustment to this construction can earn a second reveal — that would be a new family, not a rescue
  of G.
- **Family G is CLOSED FOREVER.** It does NOT proceed to Stage-3. The born-ensemble/capstone path stays
  dormant with no surviving standalone member (S4/Amihud is the only other survivor; G was the last live
  family; the field ends with no MN3 deployable book).
- **Banked structural knowledge (archived regardless):** (1) the crowding-syndrome crash edge that read
  t +11.03 on IS **inverts to t −2.87 out-of-sample** — a textbook overfit crash signal; the §5.1
  mechanism-provenance falsifier that closed G on IS correctly predicted it. (2) The BTC-only minimal-L2
  beta projection **generalizes cleanly** (β transferred at ~10–30× headroom, the third MN/MN3 reveal to
  confirm neutrality-transfer — reusable). (3) `load_funding` is panel-length-dependent via `present[j]`
  / `k≤T−2`; any future funding-feature construction that must be bit-reproducible across panel extents
  should pin the funding column set and drop the T−2 boundary explicitly.

**What CAN be claimed:** neutrality transferred out-of-sample. **What CANNOT be claimed:** any edge, any
crash-robustness, any deployability. The honest one-line summary: **the flagship's cost-surviving
crash-robust claim did NOT hold on 2 years of unseen data — the crash edge inverted (IS t+11.03 →
holdout t−2.87), the net-2× edge went weak-negative (−0.28), and drawdown was elevated (−35.90%); only
neutrality generalized.** The reveal did its job: it converted a design-contaminated IS story into a
clean out-of-sample refutation. A FAIL on unseen data is the methodology working.

---

*— QR, MN3 track (Opus 4.8, Fable-suspended phase disclosed). Reveal spent; no re-gating; no new
numbers beyond the single sanctioned holdout read. `MN3-G` DEAD; family G CONCLUDED. The MN3 sealed
holdout is now consumed for family G; the crash-robust-book line resolves to "neutrality transferred,
edge + crash-robustness refuted out-of-sample."*
