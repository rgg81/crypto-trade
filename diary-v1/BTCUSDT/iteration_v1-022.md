# Diary — iter-v1/022 (BTCUSDT) — CONFIRMATION (K=20) — NO-MERGE (funding-contra-readmit OOS was a K=5 lottery)

**Axis:** K=20 confirmation of the iter-021 funding-contra-readmit (config bit-identical: iter-020
stack + funding-contra-crowd re-admission q_f=0.50).

**Result:** IS Sharpe **+0.7181** (strongest IS of the campaign) / OOS **−0.9201** (NEGATIVE).
101/52 trades, 20/20 seeds. (iter-021 K=5 was +0.52 / +0.22.)

**Verdict: CONFIRMATION-NO-MERGE. The iter-021 improved OOS (+0.22) was a K=5 BASIN-LOTTERY —
it collapsed to −0.92 at K=20.** iter-020 (no readmit) REMAINS the baseline.
- OOS swung **+0.22 (K=5) → −0.92 (K=20)** from the seed count alone. The funding-contra-readmit ADDS
  model-timing-dependent trades (which gate-skipped rows get re-admitted/sized depends on the
  seed-varying conviction) → it RE-INTRODUCED the seed-lottery that iter-020's deterministic stack
  (trend-state direction + conviction gate) had TAMED.
- OOS concentration worse, not better: top-1 trade = 306% of net, only 15/52 winners — the re-admitted
  trades BLEED in OOS. The readmit thickened the COUNT (38→52) but the added trades don't generalize.
- **Re-confirms iter-020 is the more ROBUST config.** Thickening the book HURT OOS robustness. NO-MERGE;
  iter-020 (IS +0.37 / OOS +0.09) stays the baseline.

**The pattern (now triply-confirmed across iter-016/021):** any mechanism that makes the OOS edge depend
on the model's seed-varying TIMING/SELECTION is a K=5 lottery that collapses at K=20. Only the
DETERMINISTIC parts (trend-state direction, IS-calibrated conviction gate) generalize. iter-020's
thin-but-both-positive OOS is the robust CEILING of this trend-following approach — adding trades to
broaden it keeps collapsing.

**Methodology working:** 3rd K=5 false-positive caught at K=20 (iter-016, iter-021). The K=20 gate +
the deterministic-vs-seed-varying distinction are doing exactly their job — protecting the baseline
from lottery merges.

**Next (honest fork — surfaced to user; user is grinding BTC):**
1. **Accept iter-020 as the robust BTC baseline** (thin OOS is intrinsic; further trend-stack
   OOS-thickening keeps hitting the lottery wall) and extend the stack to the other coins
   (user: "work with others soon").
2. **Genuinely different OOS-broadening:** the FE's non-directional volatility-MAGNITUDE target
   (iter-014: the |move| signal is sub-period-stable) — the one untried lever that doesn't rely on
   the seed-varying directional timing. Bigger pivot.
3. Do NOT keep tuning the readmit/gate knobs — they add seed-varying trades that collapse at K=20.
   The OOS strengthening must come from a DETERMINISTIC or genuinely-generalizing source, not "more trades."
