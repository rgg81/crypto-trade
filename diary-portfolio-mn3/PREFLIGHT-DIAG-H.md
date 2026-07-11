# MN3 PRE-FLIGHT RULING — Sketch H sleeve distinctness (S3 vs closed vol_low; S2 vs closed OI-fade) + S2 sign-provenance discount

> Persisted VERBATIM by the orchestrator from the Critic's read-only dispatch, 2026-07-11.
> Binding per PLAN §3.2 ("Critic must ratify the distinction or the sleeve is dropped pre-run").
> Registered as PLAN-AMENDMENT-003 (PLAN.md) before DIAG-H's scored run.

**Role:** Quant Critic, adversarial pre-flight. **Dispatch:** orchestrator, per PLAN.md §1.3/§3.2/§6.1 mandate ("Critic must ratify the distinction or the sleeve is dropped pre-run"). **Status:** binding pre-registration input; to be recorded verbatim in `diary-portfolio-mn3/` and reproduced (conditions + discount language) in the DIAG-H script header and a dated PLAN-AMENDMENT **before** DIAG-H's scored run.

**Artifacts read (auditability):** `ORCHESTRATOR_BRIEF_MN3.md`; `diary-portfolio-mn3/PLAN.md` in full (incl. AMENDMENT-001/002); `diary-portfolio-mn3/DIAG-J.md` (level-control mechanics, sanctioned precedent); closed-family characterization via sanctioned governance reads only: `diary-portfolio-blind/DIAGNOSTIC-001-signal-ic.md`, `diary-portfolio-blind/EXPLORATION-001-engineering.md` + `EXPLORATION-005-engineering.md` (signal spec lines only), `diary-portfolio-blind/TRACK-CONCLUSION-2026-07-10.md`, `analysis/portfolio/blind_signal_ic_probe.py` (closed-signal construction pin: `vol_low = -ret.rolling(12, min_periods=6).std()`), `diary-portfolio-mn/SURVEY-001-CLOSEOUT.md` (DIAG-C row), `diary-portfolio-mn/DIAGNOSTIC-C-crowding.md`. **NOT touched:** `BASELINE_PORTFOLIO.md`, `analysis/portfolio/iter_*.py`, `diary-portfolio-top20/`, `CONFIRMATION-005.md`, sibling worktrees, any holdout data.

---

## 1. Sleeve S3 (RV9/RV90 term-structure) vs CLOSED vol_low

### 1.1 What the closed family actually was (from the record, not the QR's summary)

The closed object is precise: cross-sectional rank on the **LEVEL of trailing 12-candle realized vol** (`lowvol_signal(window=12)`, i.e. `-ret.rolling(12, min_periods=6).std()`), long low / short high, PIT top-20, held through EXPLORATION-001→005 unchanged. It closed because the IS edge was substantially rebal-phase luck (+0.91 was rank 3/21 phases), the crash-alpha didn't persist, and the burned reveal showed phase-honest edge ≈ −0.2.

### 1.2 Adversarial findings

**(a) The mechanism story is NOT genuinely different — and I reject that leg of the QR's claim.** DIAGNOSTIC-001's registered rationale for vol_low reads: "retail… lottery preference — systematic overpayment for high-vol, high-skew names (memes, low-cap pumps, **recently-spiked coins**)". S3's registered payer — "lottery-demand overpricing of recent action" — is a **subset of the same payer narrative**, near-verbatim. If S3's ratification rested on the mechanism story, I would REJECT. It does not rest there.

**(b) Expected cross-sectional correlation is MATERIAL, not negligible.** The closed level uses a 12c window; S3's numerator is a 9c window — **the two signals share their numerator almost exactly** (RV9 ≈ RV12). Decomposing ln-vol into a persistent name fixed effect a_i, a transient state s_i(t), and estimation noise: the level rank loads on (a_i + s_i); the ratio rank loads on (s_i + noise − slow state). With top-40 crypto's large persistent dispersion in a_i, I expect mean per-candle Spearman ρ(rank(RV9/RV90), rank(RV12)) ≈ **+0.3 to +0.6**, concentrated on the SHORT side (a name at spike onset is simultaneously high-ratio and high-level). Anyone claiming "different object" must confront that number empirically, not assert it.

**(c) The construction difference is nonetheless real, and it is real in exactly the dimension that killed vol_low.** Dividing by own RV90 removes the persistent fixed effect a_i — which is what the closed rank was dominated by (a quasi-static long-majors/short-memes tilt; turnover 73×/yr BECAUSE the ranking barely moved). S3 ranks the transient component: membership rotates, and the books genuinely diverge on the long side (a post-spike meme has decaying RV9 against elevated RV90 → low ratio → S3 LONGS a name vol_low structurally SHORTED). The component S3 trades was never tested by the old track. This is a distinct object with an overlapping narrative — the honest characterization, and the case DIAG-J's rank-regression control exists to arbitrate. That machinery is built, leak-tested, and has demonstrated teeth (it just killed family J as I-in-disguise).

### 1.3 VERDICT: **RATIFIED-WITH-CONDITIONS** — all four conditions HARD; any failure drops the sleeve pre-composite

**S3-C1 — Mandatory level-controlled read in DIAG-H (kill-only), mirroring DIAG-J verbatim.**
- **Control variable:** the closed family's signal, verbatim: per-name std of trailing 12 8h log returns (min_periods 6), per-candle cross-sectional rank over the sleeve's scored member set.
- **Method:** DIAG-J's implemented mechanics — per-candle cross-sectional OLS-with-intercept rank-regression of rank(RV9/RV90) on rank(RV12); the residual is the level-controlled (lc) signal. Raw IC and lc IC = mean per-candle Spearman vs forward-21c residual TOTAL return (the horizon the weekly sleeve trades), full IS + registered halves (H1 2020-01→2022-03 / H2 2022-04→2024-06).
- **Pass/fail (all three required):** (i) the raw sleeve gate (PLAN §3.2 kill (a)) passes unchanged; (ii) **retention = mean(lc IC)/mean(raw IC) ≥ 0.50 with sign(lc IC) = sign(raw IC)** — the DIAG-J kill-(c) threshold, mirrored; (iii) lc IC sign-stable across both IS halves. Degenerate-denominator fallback (no new thresholds invented beyond it): if |raw IC| < 0.005, retention is UNDEFINED and the sleeve passes only if mean per-candle |ρ(rank(RV9/RV90), rank(RV12))| < 0.50.
- **Consequence of failure:** S3 is vol_low-in-disguise → **sleeve DROPPED pre-composite; the vol-structure axis stays CLOSED** — no re-registration, no re-parameterization, no standalone spin-out ever (extending DIAG-C §7.2's no-rebrand precedent). H proceeds with the remaining sleeves.
- **Report (informational, non-gating):** the mean cross-sectional Spearman ρ(rank ratio, rank RV12), full IS and per half, against my +0.3/+0.6 expectation.

**S3-C2 — Direction frozen.** LONG low-ratio / SHORT high-ratio. A measured opposite sign is a sleeve FAIL, never a re-orientation (DIAG-C D10 precedent).

**S3-C3 — Disclosure duty.** Every family-H document carries: "S3's payer story overlaps the closed vol_low family's registered rationale (DIAGNOSTIC-001 explicitly included 'recently-spiked coins'); S3's distinctness rests on the OBJECT (own-history normalization removes the persistent vol fixed effect) and the S3-C1 empirical control — not on a distinct payer."

**S3-C4 — Carry-through to G.** If S3-C1 fails, the finding (ratio is level-dominated) must be disclosed in DIAG-G's read: `rvratio_xz` / `rv_ownpctl` would then partially reconstruct the closed family inside G. Informational duty for G (a feature in a 24-feature model is not a vol-structure book), not a G kill — but the finding is carried, not buried.

---

## 2. Sleeve S2 (Δlog OI 90c continuation) vs CLOSED OI-fade

### 2.1 (i) Family distinctness: **RATIFIED-WITH-CONDITIONS**

The closed family C was the crowding **FADE** (rank-sum of ΔOI/funding/taker z, trade against the crowded side), killed precisely because its ΔOI component is **continuation-signed** (IC +0.0075/+0.0086/+0.0107 at h=1/3/9, t up to +4.1) — the fade premise was wrong-signed. S2 is the **negation of the killed trade**, and DIAG-C §7.2 itself pre-adjudicated the taxonomy: "a hypothetical 'OI-build continuation' sort would be a NEW family (opposite mechanism, fresh registration)." The payer genuinely flips (later-arriving leveraged entrants vs liquidation-cascade fragility). A dead fade cannot re-enter through a door that points the other way; the anti-gaming risk here is not vol_low-style rebranding. Two adversarial caveats, one of which becomes a hard condition:

**(a) DIAG-C's own evidence warned this axis "does not merit" a family on |IC| ≈ 0.011 with a brutal churn profile.** S2's construction answers the churn objection (90c formation window vs DIAG-C's 1c-change z; weekly rebal) — legitimate design, but it means S2's evidential basis is a re-read, and DIAG-H's kill criteria are the arbiter. No condition needed; the gate exists.

**(b) The REAL side-door for S2 is not OI-fade — it is closed resid-mom-standalone.** Δlog OI over 90c plausibly proxies 90c price momentum (OI builds in trends; DIAG-C's transferable finding — "OI build = inflow confirmation" — is itself a trend-confirmation statement). E′ (residual momentum) is closed; it died on COSTS with genuine ICs, and a slow 90c re-parameterization at weekly cadence that clears the cost wall is exactly the §6.1 scenario. Expected rank correlation with trailing 90c residual return: positive, plausibly +0.2 to +0.5, era-dependent. Distinctness must hold against ALL closed families, not only the one the QR named. Hence:

**S2-C1 — Mandatory momentum-controlled read in DIAG-H (kill-only), same machinery as S3-C1.**
- **Control variable:** per-name trailing 90-candle cumulative residual return (mn_beta residual series — matching S2's formation window), per-candle cross-sectional rank.
- **Method/pass/fail:** identical structure to S3-C1 — rank-regression of rank(z ΔlogOI 90c) on rank(resid ret 90c); retention ≥ 0.50 with matching sign; sign-stable across the registered halves (disclosed asymmetric for S2: OI coverage starts ~2021-12, DIAG-C precedent); same |raw IC| < 0.005 fallback with |ρ| < 0.50.
- **Consequence of failure:** S2 is resid-mom-in-disguise → sleeve DROPPED; consistent with DIAG-C §7.2, **no standalone OI-continuation family becomes registrable on this evidence**.

**S2-C2 — Direction frozen.** LONG high-ΔOI / SHORT low. Opposite measured sign = FAIL, not re-orientation. (Note the trap explicitly: a wrong-signed S2 measurement would be evidence FOR the killed fade — re-orienting would literally reopen the closed family. Banned.)

### 2.2 (ii) Sign-provenance contamination: discount REQUIRED — pre-registered NOW, verbatim

**Facts.** S2's continuation sign was selected from MN-v2 DIAG-C, measured over ~2021-12→2025-12. This overlaps the MN3 holdout's W1+W2 (2024-07→2025-12) — **18 of the 24 holdout months, 75% of the reveal window**. One binary DOF (the sign) was chosen partly on the evaluation window: over W1+W2 the sign is selection-guaranteed not to be wrong in expectation. Additionally, MN3's IS lies entirely inside DIAG-C's measurement window, so a DIAG-H IS pass for S2 is partially circular — necessary, but weaker independent evidence than for S1/S3/S4. **The only uncontaminated windows for S2's sign are W3 (2026-01→2026-06, 6 months, never OI-evaluated) and post-2026-06 Stage-3 data.** This must appear in every family-H document.

**Pre-registered discount (binding at any family-H Stage-2 reveal; to be reproduced in the frozen decision map BEFORE the reveal):**

1. The map pre-commits per-sleeve attribution of the composite over the full holdout AND split at 2025-12-31 (W1+W2 vs W3).
2. The map's edge read is computed twice: **READ-1** = full composite, full holdout (headline). **READ-2 (S2-discounted)** = composite ex-S2 over 2024-07→2025-12 (remaining sleeves re-weighted by the same a-priori inverse-trailing-vol rule — no new weights invented) chained with the full composite over 2026-01→2026-06. **FULL PASS requires BOTH reads to clear the map's pre-committed thresholds.** READ-1 pass + READ-2 fail **caps the family verdict at PARTIAL** (the family-I §3.3 structure: Stage-3 becomes the real arbiter; no clean Stage-2 pass is available to a composite whose pass depends on S2's contaminated-window contribution).
3. **S2's W1+W2 sleeve attribution carries ZERO evidential weight for the continuation-sign claim**, ever. (Its cost/turnover/interaction realization over W1+W2 remains reportable — the sign is the contaminated DOF, not the plumbing.)
4. Form of the discount is structural (dual read + verdict cap), deliberately NOT a numeric Sharpe haircut: the contaminated selection is 1 bit chosen on a |IC| ≈ 0.011 diagnostic; any numeric haircut would be pseudo-precision and itself a fitted parameter.

---

## 3. Ledger accounting + one out-of-scope flag

- **Ledger:** the S3-C1 and S2-C1 control reads are FALSIFICATION ARMS (kill-only; no selection, no re-orientation, no re-weighting may ever key off them) and therefore do NOT increment family H's 4-trial ledger — the DIAG-C attribution precedent. If any design choice is ever conditioned on them, they convert to registered trials retroactively.
- **Flagged, not ruled (outside this dispatch):** S1 (carry sleeve) has the mirror-image problem on **W3**, which is FULLY REVEALED for the funding-carry family (A3-1) and per charter "can never count as evidence for that family." The family-H decision map must address S1's W3 weight symmetrically before any reveal; the READ-2 dual-read structure above is the template. I am not ruling on S1 here — but a family-H map that reaches me without an S1/W3 treatment will fail its reveal pre-flight.

---

## 4. Summary

| Sleeve | Verdict | Hard conditions |
|---|---|---|
| **S3** RV9/RV90 term-structure | **RATIFIED-WITH-CONDITIONS** | S3-C1 level-control vs rank(RV12) (retention ≥ 0.50, sign-matched, half-stable; fail → dropped, vol-structure axis stays closed forever); S3-C2 direction frozen; S3-C3 mechanism-overlap disclosure; S3-C4 carry-through to G |
| **S2** Δlog OI 90c continuation | **RATIFIED-WITH-CONDITIONS** (family-distinct from OI-fade — opposite trade, DIAG-C §7.2 pre-adjudicated) | S2-C1 momentum-control vs rank(90c residual return) (same bar; fail → dropped, no OI-continuation family registrable); S2-C2 direction frozen; §2.2 sign-provenance discount pre-registered verbatim (dual read, W1+W2 zero weight for the sign, PARTIAL cap) |

DIAG-H may proceed with all four sleeves once these conditions are recorded in the DIAG-H script header and a dated PLAN-AMENDMENT, before the scored run. A wrong RATIFY here cannot survive into the composite: both ratifications are conditional on empirical controls whose failure closes the respective side door permanently — the anti-gaming failure §6.1 exists to prevent is guarded by measurement, not by my judgment of the QR's narrative.

*— Quant Critic, MN3 track, 2026-07-11. Pre-flight ruling; read-only; nothing run; the holdout remains untouched.*
