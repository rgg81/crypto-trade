# DIAG-G PRE-FLIGHT RATIFICATION — flagship feature parquet (rulings R1–R4)

> Persisted VERBATIM by the orchestrator from the Critic's read-only ratification, 2026-07-11.
> Gates DIAG-G scoring: confirms the walk-forward OOF parquet is scorable as-is (no regen).
> Three disclosures (R1, R3, AMENDMENT-003 S3-C4) MUST appear in the DIAG-G read.

**Track:** MN3 (two-year-holdout market-neutral). **Date:** 2026-07-11. **Mode:** read-only pre-flight ratification of interpretive rulings; my message IS the ruling (orchestrator persists).
**Model disclosure (mandated):** running on **Opus 4.8, NOT Fable** — the charter's Fable mandate is user-suspended for this phase (Fable rate-limit; user directed "continue on Opus"). Standard is unchanged; adversarial burden of proof unchanged.
**Blinding honored:** reads were PLAN.md, mn3_features.py, OI-BACKFILL-REPORT.md, mn3_crisis.py, mn3_diag_j.py, DIAG-J.md, DIAG-H.md only. No BASELINE_PORTFOLIO.md, no iter_*.py, no top20 diary, no CONFIRMATION-005, no sibling worktrees, no holdout/Stage-3 data touched.

## OVERALL: ALL FOUR RULINGS RATIFIED. **The parquet is scorable as-is — NO regeneration required.**

Three disclosures (from R1, R3, and a carried AMENDMENT-003 duty) MUST be surfaced in DIAG-G's read. None triggers a rebuild; they govern how DIAG-G *reports* what the flagship trained on.

---

## R1 — `mkt_fund_agg` = original §2.1 C3 LEVEL-z (NOT the AMENDMENT-001 onset). **RATIFIED-WITH-DISCLOSURE.**

This is the load-bearing ruling; I attacked it from four directions and it holds.

**Scope reading is textually correct.** AMENDMENT-001's own scope clause is dispositive: *"It supersedes ONLY the named items in §2.1–§2.2"* (PLAN:780–782). A §3.1 feature is not a named item in §2.1–§2.2. §3.1 independently declares the feature list *"EXACTLY these 24, immutable once DIAG-G runs"* and frozen at track open (PLAN:342). The two facts interlock: if resolving "C3's z[t]" to the onset were correct, AMENDMENT-001 would have silently mutated a §3.1 feature — contradicting its own declared scope. The only self-consistent reading is freeze-time resolution of the §3.1 reference.

**The reference resolves unambiguously at freeze time.** "C3's z[t]" at §3.1's track-open freeze denoted original C3: `z_FUND = robust z of F`, where `F[t]` = EW cross-sectional mean of `|funding_i[t]|` over the ≥15-member top-40 (PLAN:152–158). The implementation is that construction *exactly* — `af = |funding|` over `univ40 & isfinite`, `f_agg = nanmean(af)` gated at `n_f ≥ 15`, then `robust_z(f_agg)` (mn3_features.py:435–441). It does NOT implement AMENDMENT-001 §B2 (`R_FUND = ln(F_short/F_long)`, PLAN:834–840). Ruling matches code.

**Non-leaky — verified at source, not asserted.** `robust_z` is a trailing rolling median/MAD, window 270, `min_periods 135`, clip ±8 (mn3_crisis.py:226–240; RZ_MIN_PERIODS=135 at :92) — past-only. Window-includes-t is consistent with the module's [k−1] consumption (feature row t predicts label t+1..t+3, consumed at the t→t+1 fill), the same convention the crisis machine's own §2.5 corrupt-future/decision-lag leak battery already cleared. No look-ahead path.

**It is the CONSERVATIVE choice, not construct-resurrection — the adversarial crux.** The worry would be that the level sneaks a dead construct back in. The reverse is true. BOTH the level-as-trigger AND the onset-as-trigger are dead as *triggers* (onset frozen-as-failed under AMENDMENT-002, PLAN:961; surviving risk machine is GAP-only + DD-detector). Using the onset here would be the mutation — it would import a LATER §2.1 amendment into a frozen §3.1 list AND inject a formally-falsified construct as model fuel. Using the level honors the freeze-time referent. Furthermore the level's only failure mode (regime-persistence → ~8–9% vote occupancy → blows the calm budget) is a *trigger* pathology with no analog in the *feature* role — a tree has no calm-budget; "on 8% of the time" is legitimate interaction fuel (§3.1 names the three market-context features "interaction fuel"). The QE's role-distinction is sound.

**Internal consistency check (R1 vs R2) passes.** Both rulings apply one uniform principle — resolve the §3.1 reference against §2.1 as it stood at track-open freeze. R2 is the easy case (referent unchanged); R1 is the hard case (referent later amended). The QE is not cherry-picking a favorable definition; it applies the same rule to both. This *strengthens* R1.

**No data-snooping.** The parquet is unscored; the ruling is documented pre-run in the docstring; the level is the DEFAULT freeze-time referent, not an outcome-driven pick. The ratification LOCKS the level in: the QE may not switch to the onset after seeing DIAG-G's IC — that would be feature-selection-by-outcome, banned (§3.1:405).

**DISCLOSURE (must appear in DIAG-G's read):** *`mkt_fund_agg` is the original §2.1 C3 aggregate-|funding|-LEVEL robust-z (the freeze-time referent of "C3's z[t]"), NOT the AMENDMENT-001 §B2 onset-FUND transform, which is frozen-as-failed under AMENDMENT-002. This definition is locked pre-scoring and is immutable regardless of DIAG-G IC.*

## R2 — `mkt_corr` = raw ρ̄ via `c2_corr(...)["raw"]`. **RATIFIED (clean).**

§3.1 references "C2's ρ̄[t]" (PLAN:358) — the ρ̄ *quantity*, not C2's vote/z. Original §2.1 C2 and AMENDMENT-001 §B3 both carry the identical ρ̄ (median pairwise Pearson, trailing 90c, PIT top-20; §B3 states "ρ̄[t] unchanged", PLAN:843). Verified at source: `c2_corr` returns `{"raw": rho, "z": z, ...}` and the QE consumes `["raw"]` (mn3_features.py:434), i.e. the raw ρ̄ — NOT `["z"]` (the §B3 onset z_CORR, which would be the mutation). `rho[t]` is a trailing-90c window computation (per-pair floor CORR_MIN_OBS=60), past-only, consumed at [k−1] (mn3_crisis.py:281–314). Amendment-invariant and unambiguous. No disclosure needed.

## R3 — OI flow features consumed as sum/count per OI-BACKFILL §8.2. **RATIFIED-WITH-DISCLOSURE.**

**Matches the §8.2 prescription exactly.** The report mandates: *"Any consumer must normalize by the paired `count_*` column (sum/count = per-interval mean), never use raw sums"* (OI-BACKFILL §5.2:99–102; §8:160–161). Implementation: `tt_ls = sum_toptrader_long_short_ratio / count_toptrader_long_short_ratio` (exact name-pairing) and `taker_ls = sum_taker_long_short_vol_ratio / count_long_short_ratio` (mn3_features.py:298–299). The schema (OI-BACKFILL:15–17) contains only two count columns; toptrader pairs by name, and the taker sum's only available denominator is `count_long_short_ratio`. The stub artifact is a bar-grid artifact that reduces every column's interval count *together*, so `sum_taker/count_long_short` cancels the interval count and is stub-robust against the exact failure mode the report warns of. This is the only stub-robust consumption the data doc sanctions.

**No look-ahead — the shift(1) convention holds.** Every OI/flow input is `_shift1`'d before feature construction: `oi_lag`, `oi_val_lag`, `tt_lag`, `tk_lag` (mn3_features.py:383,392,394,396), and `_shift1` sets `out[1:] = x[:-1]` (row t holds x[t−1]; :188–192). A decision at candle t reads OI rows ≤ t−1 only, matching OI-BACKFILL §8.1. Normalization occurs at bar level *before* the temporal shift; the two operations are orthogonal. Clean.

**DISCLOSURE (must appear in DIAG-G's read):** *`taker_ls_oi_xz`'s numerator (`sum_taker_long_short_vol_ratio`, taker buy/sell volume ratio) and denominator (`count_long_short_ratio`, global L/S account-ratio interval count) are DIFFERENT underlying Binance series; the feature is the bar-mean taker ratio under the assumption that both were aggregated over the same 5-min intervals. It is stub-robust (the sanctioned §8.2 consumption) but is not a clean single-endpoint per-interval mean — do not interpret it as one.*

## R4 — min_periods majority-rule with §2 pins honored. **RATIFIED (clean; one immaterial note).**

Every fill verified. Majority rule `ceil(w/2)`: 3→2, 9→5, 21→11, 30→15, 63→32, 90→45, 189→95, 270→135 (mn3_features.py:142–155) — all arithmetically correct. The two anchor claims are confirmed at source, not taken on the QE's word:
- **9c→5** = the inherited DIAG-A/J funding convention: `mn3_diag_j.py:103` pins `FUND_MIN_OBS = 5  # ... DIAG-A convention`, and DIAG-J.md:13 records the same "inherited DIAG-A min-obs convention." ✓
- **270c→135** = the §2.1 robust-z convention: `RZ_MIN_PERIODS = 135` (mn3_crisis.py:92; PLAN §2.1:130). ✓

§2 explicit pins correctly override the majority where they exist: RV9 min 6 and RV90 min 45 (AMENDMENT-001 §B1, PLAN:827–828), RV30 min 20 (original §2.1 C1, PLAN:138). Critically, the QE distinguishes the *pinned* RV30 (min 20, used inside `rv_ownpctl` at :152,415) from *unpinned* 30c windows (dvol/amihud → majority min 15 at :146,155,389,424) — a subtle, correct application. Because these are past-only trailing windows, min_periods cannot introduce look-ahead; a higher floor only errs toward more NaN/conservatism.

**Immaterial note (no regen):** RV9 uses the §B1 pin (min 6) rather than the strict freeze-time majority fill (5). This is the more conservative choice and is consistent with R4's "honor §2 pins" rule; the effect is a de-minimis one-observation shift in the RV9 warmup boundary, incapable of moving a Spearman IC. Noted for the record, not a defect.

---

## Carried standing duty for the DIAG-G read (from AMENDMENT-003 §A/S3-C4, now triggered)

Not one of the four rulings, but it lands in the same read and intersects R4's RV features: PLAN AMENDMENT-003 S3-C4 (PLAN:1146–1148) pre-registered that *if* DIAG-H's S3-C1 control failed, the level-domination finding carries into DIAG-G's read because `rvratio_xz` / `rv_ownpctl` partially reconstruct the closed vol-structure family. DIAG-H.md confirms **S3-C1 FAILED — "vol-structure axis CLOSED FOREVER."** Therefore DIAG-G's read must carry the informational disclosure that `rvratio_xz` and `rv_ownpctl` partially reconstruct the now-closed vol-structure axis inside G. This is an *informational* duty (explicitly "not a G kill" per S3-C4) — it does not gate the parquet and does not trigger regeneration.

---

## Bottom line

Four rulings RATIFIED; zero rulings mis-define a feature the flagship trained on; the walk-forward OOF parquet is **scorable as-is with no ~12-min regeneration.** Before DIAG-G scoring proceeds, the three disclosures — (R1) `mkt_fund_agg` is the freeze-time level-z, not the frozen-as-failed onset; (R3) `taker_ls_oi_xz`'s cross-series denominator; (AMENDMENT-003 S3-C4) `rvratio_xz`/`rv_ownpctl` reconstruct the closed vol-structure axis — must appear in the DIAG-G read. The R1 definition is locked and immutable regardless of the IC DIAG-G is about to produce.

*— Quant Critic, MN3 track, 2026-07-11 (Opus 4.8, Fable-suspended phase). Pre-flight ratification; read-only; nothing run; the holdout remains sealed.*
