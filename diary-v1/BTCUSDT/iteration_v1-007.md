# Diary — iter-v1/007 (BTCUSDT) — EXPLORATION

**Axis:** orthogonal NON-OHLCV feature, NEW family (Open Interest) — `btc_oi_delta_5_z30` (fast
5-bar OI delta, 30-bar z) added to the 41-col prune. R2 OFF. K=5 screen, n_trials=35, slippage 2 bps.
FE: best non-funding raw purged-CV dir_acc OOF lift (+0.0118); near-zero univariate IC (+0.0046) →
the hypothesis was a NON-LINEAR positioning signal a depth-4 tree might exploit.

**Result (vs iter-004 prune-only K=20 IS −0.17 / OOS +0.48):**
IS Sharpe **−0.4723** / OOS **−0.0266**, ratio **+0.06 (both negative)**, dispersion 42.42, 191/84
trades, IS net −20.08, OOS net −0.33. Clean run, 5/5 seeds trained.

**Verdict: NEGATIVE.**
- Worst IS of the batch (−0.47, below the prune-only anchor −0.17). OOS flat-negative (−0.03).
- `btc_oi_delta_5_z30` trained at **rank 29/42** (verifiability fix) — bottom third, identical to
  funding z90's rank. The tree did NOT extract a useful non-linear OI signal; the dir_acc OOF lift
  did not transfer to the bagged specialist.

## ORTHOGONAL-FEATURE AXIS CLOSED FOR BTC
Pre-registered at iter-006 review (Proposed Change #3): if OI also NEGATIVE → axis closed. It is.
Complete sweep:

| iter | feature | family | IS | OOS | import. rank | verdict |
|---|---|---|---|---|---|---|
| 005 | btc_funding_spread_30_90 | funding | −0.43 | +0.85 | 16/42 | NEG (inverted) |
| 006 | funding_rate_zscore_90 | funding | −0.40 | −0.42 | 29/42 | NEG (both-neg) |
| 007 | btc_oi_delta_5_z30 | OI | −0.47 | −0.03 | 29/42 | NEG (both-neg) |

Plus FE IS-only pre-screen: `basis_zscore_30` degrades dir_acc (confirms iter-040 retirement),
`long_short_zscore_30` zero IC, cross-asset ratios DEAD (0% coverage). Three live families tested,
every added feature lands bottom-third importance, every profile negative or inverted. **No
orthogonal non-OHLCV feature rescues BTC's noise-floor signal** (FE: max |IS-IC| 0.028, prune-only
purged-CV R² −0.095). The orthogonal-feature lever is exhausted for the BTC specialist.

**OOS-vigilance:** iter-007 used the same IS-only FE analysis (`feature_ortho_scan.py`, verified
strict pre-cutoff filter + leak guard at iter-006). No new OOS-touching analysis introduced.

**Lessons**
- A non-linear hypothesis (positive OOF dir_acc lift, near-zero linear IC) is NOT a rescue path when
  the base signal is at the noise floor — the tree allocates the added feature to bottom-third gain
  and IS degrades. Three orthogonal families, three bottom-third ranks.
- The orthogonal-feature campaign was correct to run (cheap K=5 screens, decisive sweep) but is now
  conclusively negative. Stop adding features to BTC; change WHAT we predict or WHEN we trade.

**Next:** iter-v1/008 — PIVOT AXIS (no more feature swaps). Dispatch the QR for an IS-only Phase 1/2
analysis of the two untouched non-feature levers: (a) **label horizon/mode** (current = ATR
triple-barrier tp2.9/sl1.45/7d-timeout; alternatives = longer timeout, fixed_horizon at a longer
N, or trend_scanning) — does BTC have a more learnable signal at a different prediction target?; and
(b) **regime gate** — does BTC have a coherent IS edge conditional on a regime (trend/vol state),
such that gating out the noise-floor regimes flips IS positive? QR recommends the iter-008 config on
IS-only evidence. If BOTH levers also fail to give BTC a coherent IS edge → escalate to the user the
evidence-based case that BTC at 8h may not be tractable with this architecture, and propose a symbol
pivot (the FE's open question — BTC at max |IS-IC| 0.028 may be the wrong FIRST symbol).
