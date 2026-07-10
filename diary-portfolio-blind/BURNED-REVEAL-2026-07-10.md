# BURNED-WINDOW REVEAL — 2026-07-10 (user-authorized, one-off)

**Authorization:** explicit user instruction 2026-07-10 ("please show me OOS I need to know" →
confirmed "Reveal — run the current books on it"), overriding the phase quarantine the user set
at phase start. Script: `analysis/portfolio/blind_burned_reveal.py` (one-off; the weekly
runner's burned-window guard is untouched). Output: `paper-l1/burned_reveal_2026-07-10.txt`.

## STATUS OF THIS WINDOW AFTER THIS DOCUMENT
**[2025-03-24, 2026-07-09] is now DESIGN-CONTAMINATED for the current books (L1, ENSEMBLE-L1,
their V0 references).** Every number below is INFORMATIONAL ONLY and can NEVER be cited as
validation or falsification-grade evidence for these constructions: the /006–/007 redesign
exists because /005 failed on this window, so any evaluation of the redesign here is
selection-contaminated by construction. The forward test (PROTOCOL-ENSEMBLE-L1-FORWARD, T0
2026-07-15) remains the only clean venue. Future design iterations must treat this window as
seen.

## Headline (today's complete 747-coin panel, 1419 candles)

| Book | Sharpe | ann | maxDD | worst-mo | 2025-part | 2026-part | mo-win |
|---|---|---|---|---|---|---|---|
| **ENSEMBLE-L1 (fwd book)** | **−0.205** | −5.6% | −25.5% | −9.3% @2026-05 | +0.62 | **−1.52** | 53% |
| V0-ENSEMBLE | −0.230 | −7.4% | −26.2% | −10.1% @2026-05 | +0.35 | −1.16 | 47% |
| L1 single-phase Wed@00h | +0.404 | +7.7% | −24.4% | −11.0% @2025-04 | +1.14 | −0.21 | 53% |
| V0 single-phase (=/005) | +0.139 | −0.5% | −27.6% | −20.7% @2025-04 | +0.35 | −0.09 | 47% |

Overlay delta (ENS-L1 − V0-ENS): **+0.025** (IS mean was +0.614). Window rho_bar +0.457.

## DISCOVERY 1 — CONFIRMATION-005's OOS numbers were partly a DATA ARTIFACT
The reveal's integrity anchor (single-phase V0 must reproduce CONFIRMATION-005's +0.219/−73.0%)
**MISMATCHED**: today's complete data gives **+0.139 / −27.6%**. Attribution (high confidence):
the `fetch --all` starvation bug (found+fixed 2026-07-10, see PROTOCOL-L1-FORWARD §7) had frozen
~35 top-volume coins' klines since ~2026-02-28; CONFIRMATION-005 (run 2026-07-10, pre-fix)
evaluated the last ~4.5 months of its window on that degraded panel (universe drawn from live
feeds only; also explains its 1322-candle count vs 1413 for the nominal window). **The −73%
maxDD headline was largely a degraded-universe artifact** (today: −27.6%). The FAIL verdict
itself SURVIVES on complete data (+0.139 < the frozen +0.30 floor) — but via the Sharpe
condition only; the maxDD condition (−60%) would NOT have fired, and the "intra-rebal squeeze
blow-up" narrative in CONFIRMATION-005's diagnosis was substantially data-artifact.

## DISCOVERY 2 — the phase-honest edge is ≈ −0.2 on this window; the overlay added ≈ nothing
- The ensemble (= phase-honest level) of L1 is **−0.205**: the cross-sectional edge did not
  persist into 2025-26 at the phase-honest level. The single-phase +0.404 is another favorable
  Wednesday draw — the same phase lottery, this time flattering.
- The C1+C2 overlay: **+0.025** here vs +0.61 IS. Only ONE mania month occurred (2025-05, book
  +3.61% — consistent with the mania fix, but n=1); the overlay had almost nothing to act on.

## DISCOVERY 3 — the IS crash alpha did NOT persist (the mechanistic core)
Frozen-rule buckets in the window: **8 crash months** (2025-11, 2025-12, 2026-01, 2026-02,
2026-03, 2026-04, 2026-06, 2026-07-partial) — a sustained drawdown regime — and 1 mania month.
**ENS-L1 crash bucket: mean −1.35%/mo, short_px +0.312, long_px −0.325.** Compare IS crash:
+0.93%/mo with short_px +1.204. The short-leg crash insurance that carried the book in-sample
(IS aggregate +1.53 over 20 crash months) weakened to +0.31 over 8 months here — insufficient
to cover the long leg's losses. The 2026 bleed (−1.52 part-year Sharpe) is a sustained
crash-regime loss, not a single squeeze. **The forward M-crash gate (crash > 0 AND short_px > 0
AND ≥ fwd V0-ENSEMBLE − 0.25pp) is testing exactly the failure mode this window exhibits — if
this regime behavior persists forward, the ensemble will fail it, as designed.**

## Monthly returns, ENSEMBLE-L1 (burned window)
2025: +1.03, −7.78, +3.61, +4.57, +2.44, +2.29, −1.27, +9.74, −5.94, +0.37 (Mar–Dec)
2026: +4.66, −2.40, −2.94, +0.60, −9.28, −5.05, −0.09 (Jan–Jul-partial)

## Caveats (permanent)
1. Selection-contaminated window — informational only, both directions (can't validate, can't
   cleanly damn).
2. 15.5 months → SE(Sharpe) ≈ 0.9: −0.205 is indistinguishable from +0.5 or −0.9.
3. The restored-coin data for 2026-03+ was backfilled 2026-07-10; the PIT universe recomputation
   on today's panel is the honest record of what traded, but no live run observed it in real
   time.
4. Forward gates stay FROZEN (moving them post-reveal would be contamination). What this reveal
   legitimately updates is the USER's expectation and track-level resource decisions: if the
   burned-window regime persists, expect the forward test to fail its checkpoint/primary — the
   system working as designed.
