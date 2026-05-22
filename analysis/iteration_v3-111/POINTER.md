# iter-v3/111 — Analysis Pointer Note

**iter-v3/111 reuses the iter-v3/110 EDA verbatim. No new screen is run.**

iter-v3/111 is the Critic-mandated (`briefs-v3/iteration_v3-110/review.md` Recommendation 4)
clean re-test of iter-v3/110's symbol-selection axis. iter-v3/110 closed
EXPLORATION-NEGATIVE on a **label confound** — the runner trained every model under
a stale `label_mode="trend_scanning"` (carry-over from iter-v3/105) instead of the
brief-declared `triple_barrier`. The /110 *axis design* (the CRV/AAVE/GRT/ADA
universe choice) survives; only the as-run *measurement* was void. iter-v3/111
re-runs the identical universe on a `triple_barrier`-corrected runner.

## The IS evidence for iter-v3/111 is `analysis/iteration_v3-110/` (commit `cfeaf34`)

The /110 EDA screened the v3-eligible symbol universe under
`label_mode="triple_barrier"` — the *correct* label geometry for iter-v3/111's
backtest. This is verified in `analysis/iteration_v3-110/_shared.py` lines 21-25:

> Label faithfulness — replicates `labeling.label_trades` (label_mode=
> "triple_barrier") exactly: ATR triple-barrier, atr_tp=2.0 / atr_sl=1.0, ATR
> column `natr_21_raw`, 21-candle (10080-min / 8h) timeout, fee 0.1%.

Because the /110 screen was already computed under `triple_barrier`, it is the
valid IS evidence for the /111 backtest — the EDA and the (corrected) backtest
will share one label geometry. **Re-running the screen would produce
bit-identical tables.** Per the iter-v3/111 dispatch ("The /110 research basis is
VALID and REUSED — do NOT redo it"), no new EDA is run.

## Files reused (all committed at `cfeaf34`)

`analysis/iteration_v3-110/`:
- `_shared.py` — the /059-faithful IS-only `triple_barrier` labeler (22-symbol
  generalization of /109's `_shared.py`); asserts `close_time < OOS_CUTOFF_MS`
  (`1742774400000`) per symbol before any computation.
- `symbol_signal_screen.py` — per-symbol walk-forward feature→label AUC + a
  per-symbol permutation null across 21 candidates.
- `universe_construction.py`, `t6_recompute.py`, `gated_book_2to1.py`,
  `universe_finalize.py` — universe ranking, gated-tail 2:1-barrier book,
  leave-one-out bake-off.
- Result tables T1–T10 (`T1_per_symbol_signal.csv` … `T10_signal_margin.csv`).

The headline EDA numbers cited in the iter-v3/111 brief Section 2 are read
directly from these committed CSVs.

## What changed at iter-v3/111 vs iter-v3/110

NOT a research-design change. iter-v3/111 is the **runner correction** — the
two-line `label_mode` revert iter-v3/105 mandated for the /106 setup, never
discharged because iter-v3/106–109 were all NULL-AT-EDA, plus the
`_canonical_v059` accretion-guard extension. The precise `src/` edits are
specified in the iter-v3/111 brief Section 3.5 (the QE's Phase 6 work). The QR
does not edit `src/`.
