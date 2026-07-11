# DIAG-H — born-ensemble multi-sleeve MN composite: FAMILY DEAD (kill a), one standalone survivor surfaced

**Track:** MN3 (two-year-holdout market-neutral). **Date:** 2026-07-11. **IS-only** 2020-01-01→2024-06-30; holdout SEALED (guard passed, zero reveals — ledger untouched). Frozen spec PLAN §3.2 + binding conditions PLAN-AMENDMENT-003 (Critic pre-flight, `PREFLIGHT-DIAG-H.md`). Multiple-testing budget: 4 registered trials (one per sleeve); the two C1 controls are ledger-neutral falsification arms.

> **Execution note (charter deviation, disclosed).** The pre-registered module `analysis/portfolio/mn3_diag_h.py` (1014 lines, 21 unit tests) was built by the Fable QR, which hit the Fable-5 rate limit at the scored-run boundary. Per user direction ("finalize with opus"), the **single registered scored execution** and this diary were finalized on **Opus 4.8**, not Fable. The module was frozen and Critic-conditioned BEFORE the run; the run is deterministic; the verdict is mechanical (`main()` prints `FAMILY H: DEAD/ALIVE`). Pre-registration integrity is intact — who typed the command did not touch the frozen spec. Full scored log: `logs/mn3_diag_h_scored.log`.

## Verdict (frozen kill criteria, mechanical): **FAMILY H DEAD — kill (a) fired.**
Sleeves passing gate AND C1-where-applicable: **{S4} = 1/4.** Kill (a) "<2 sleeves pass" FIRED. Kill (b) not evaluable (needs ≥2). The born-ensemble doctrine has too few orthogonal profitable sleeves to compose — **the user's "diversification-from-birth" construction did not find its members.**

## Scorecard — sleeve gate (net-of-2×-cost, phase-agnostic headline over 21-phase weekly sweep; GT twin re-run PASS on all four)

| Sleeve | net2×/yr | phase-agnostic | 21-phase positive | H1 / H2 sign-stable? | CRASH / MANIA / CHOP | turnover | GATE |
|---|---|---|---|---|---|---|---|
| **S1** carry-flow | **+75.0%** | med +80.9% | 21/21 | **NO** (+176.8% / −9.3%) | −92.9 / +108.9 / +95.4 | 126× | **FAIL** (half-unstable) |
| **S2** OI-structure (Δlog OI 90c cont.) | −15.8% | med −19.4% | 8/21 | yes (−13.8 / −16.0) | −193.7 / −42.6 / +16.9 | 115× | **FAIL** (negative) |
| **S3** vol-term-structure (RV9/RV90) | −53.6% | med −52.0% | 0/21 | yes (−74.8 / −36.1) | −9.0 / −47.9 / −61.9 | 165× | **FAIL** (negative) |
| **S4** liquidity-provision (Amihud) | **+17.0%** | med +13.9% | 19/21 | **YES** (+13.9 / +19.5) | **+54.0 / +25.8 / +7.4** | **74×** | **PASS** |

## AMENDMENT-003 C1 falsification arms (kill-only, ledger-neutral) — both did their job

**S3-C1 (ratio | RV12 level): FAIL → S3 DROPPED; vol-structure axis CLOSED FOREVER.**
Raw IC −0.0130 (t/√21 −0.93); level-controlled IC **+0.0255** — the sign **FLIPS** under level-control. rho(rank ratio, rank RV12) = **+0.446** full (H1 +0.511 / H2 +0.392), squarely inside the Critic's pre-stated +0.3/+0.6 expectation. Retention = **−1.965, sign_match = FALSE.** The raw sleeve's weak edge is entangled with the closed vol_low LEVEL (ρ 0.446); the level-*orthogonal* component points the **opposite** way, so the frozen-direction (LONG low-ratio) sleeve is not a valid distinct object. Both the gate (net2× −53.6%) and the C1 control kill it independently. **Per S3-C1 + S3-C2, the vol-structure axis stays CLOSED — no re-registration, re-parameterization, or spin-out, ever.** The Critic's suspicion (§1.2: "distinct object with an overlapping narrative — the case DIAG-J's control exists to arbitrate") is vindicated: it did not survive arbitration.

**S2-C1 (zΔOI90 | resid-mom 90c): PASS → S2 is genuinely distinct (but dead on the gate).**
Raw IC −0.0523, LC IC −0.0448, retention **+0.856, sign_match TRUE, half-stable.** rho(sig, ctrl) +0.289 — below the momentum-proxy worry. **S2 is NOT resid-mom-in-disguise; the OI-continuation object stands on its own** (the side-door the Critic flagged is clear). The machinery cleared it honestly. S2 nonetheless FAILS the gate (net2× −15.8%; CRASH −193.7% — long-rising-OI into liquidation cascades is exactly as toxic as the mechanism predicts). Distinctness held; profitability did not.

## Kill (b) — decorrelation (informational; not reached, <2 sleeves passed)
All-sleeve weekly-return (21c-block, ensemble net) correlation matrix — genuinely low across the board (the ensemble doctrine's *premise* was sound; the members just weren't profitable):

```
        S1      S2      S3      S4
S1   +1.00   +0.27   -0.19   -0.21
S2   +0.27   +1.00   -0.49   +0.31
S3   -0.19   -0.49   +1.00   -0.27
S4   -0.21   +0.31   -0.27   +1.00
```
S4 is negatively correlated with S1 (−0.21) and S3 (−0.27) — had a second profitable sleeve existed, the decorrelation to compose it was present. The failure is **member alpha, not member overlap.**

## Data hygiene / leak battery
- Panel T=4929 IS candles, 747 syms; PIT top-40 mean 35.5 members/candle (232 ever-members). Occupancy sanity check PASS (CRASH 13.2% / MANIA 18.8% / CHOP 68.0%, all ≥5%).
- Funding coverage 100.0% mean/min over 4651 live candles; LITUSDT (no funding) excluded from every tradable set (silent-zero guard fired, loud warn).
- OI: 231/232 ever-members carry archive; **S2 sleeve start 2021-12-01** (first candle with ≥25 of top-40 carrying consumable OI under the pinned shift(1)) — matches the PLAN's ~2021-12 expectation; S2 halves disclosed asymmetric (H1 only 270 candles).
- GT 2×-cost twin re-run PASS on all four sleeves (statelessness proven, not assumed).
- Leak battery 6/6: corrupt-future bit-identity per sleeve (S2 includes the ≤t0 shift(1) proof), decision-lag (fwd21 moves exactly rows t0−21..t0−1, t0 untouched), injected-leak positive control drives IC to +1.000 (harness detects leakage).

## S3-C3 mechanism-overlap disclosure (mandatory, verbatim duty)
S3's payer story overlaps the closed vol_low family's registered rationale (DIAGNOSTIC-001 explicitly included "recently-spiked coins"); S3's distinctness rested on the OBJECT (own-history normalization removing the persistent vol fixed effect) and the S3-C1 empirical control — not on a distinct payer. **The control FAILED; the overlap was real; the axis is closed.**

## The standalone finding — S4 (Amihud liquidity-provision)
DIAG-H is dead as an *ensemble*, but it surfaced the **first clean all-weather, cost-surviving, crash-robust single sleeve** the MN/MN3 effort has produced:
- **Positive in every regime bucket** — CRASH **+54.0%** (best), MANIA +25.8%, CHOP +7.4% — the crash-robustness the whole track has been hunting, in the bucket every other mechanism (S1 carry, S2 OI) is toxic in.
- Gate-clean: net2× +17.0%/yr, 19/21 phases positive, H1/H2 sign-stable (+13.9 / +19.5), lowest turnover (74×).
- Mechanism: LONG high-Amihud (thinner half of the liquid top-40) / SHORT low-Amihud (most liquid), beta-projected. Payer = immediacy demanders in the thinner names; the illiquidity premium is *structurally largest when liquidity is scarcest* (crashes) — consistent with the +54% CRASH read, not a fit.

**Governance:** under the frozen kill criteria the ensemble path (EXPLORATION-H composite, kill (c)) is closed — that needed ≥2 survivors. S4 as a **standalone construction** is a separate, live option: per PLAN §3.2's anti-gaming rule it would share family H's one-forever holdout token, and it would require its own pre-registered EXPLORATION (single-sleeve, crisis-machine Layer-2 throttle, full 21-phase, honest S4-long-side cost stress — the amendment already flagged S4's long side as structurally costlier). This is a USER/next-step decision, not a mechanical continuation — surfaced here, not acted on.

## Cross-family reads banked
- **S1 re-confirms the funding-carry regime signature a third time** (DIAG-A → CONFIRMATION-A → here): mania-rich (+108.9%), CHOP-positive (+95.4%), **crash-toxic (−92.9%)**, and H2-dead (−9.3% 2022-04→2024-06). Family I inherits this with eyes open — funding carry is a CHOP/MANIA harvester, not an all-weather payer.
- **Amihud illiquidity is the crash-positive axis** carry/OI/vol-structure all lack — the one lens that pays *because* the others are stressed.

## Ledger
Family H: 4 registered trials spent (S1–S4). C1 arms ledger-neutral (no design choice keyed off them). No amendment used beyond the pre-registered AMENDMENT-003. Holdout untouched; REVEAL-LEDGER zero spends. Tests 21/21 (DIAG-H file) green, ruff clean. Nothing about the ensemble is revived; S3/vol-structure axis closed permanently.

*— Orchestrator (Opus 4.8, Fable-limit finalization), MN3 track, 2026-07-11. Frozen module run once; mechanical verdict transcribed; no post-hoc re-gating; the holdout remains sealed.*
