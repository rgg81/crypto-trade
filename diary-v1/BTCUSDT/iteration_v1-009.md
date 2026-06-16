# Diary — iter-v1/009 (BTCUSDT) — EXPLORATION — frequency-emulation / label-mode axis

**Axis (user-mandated):** emulate a different trading frequency within 8h candles via the LABEL MODE
+ execution horizon. Config (FE Phase 4 PRIMARY + QE Phase 6 execution-consistency): 19-col hybrid
short+regime feature set; `label_mode="fixed_horizon"` N=21 (7d), `use_atr_labeling=False`;
EXECUTION made consistent with the horizon — `atr_tp=100.0` (TP NON-BINDING → 7d timeout binds, "let
winners run"), `atr_sl=1.45` ("cut losers"), exec timeout = 7d. R2 OFF. K=5, n_trials=35, slippage 2.

**Result (vs prior screens — all prior IS ≈ −0.40/−0.47):**
IS Sharpe **−0.0878** / OOS **−0.7442**, 171/78 trades, dispersion 40.98, IS net **+4.43%** / OOS net
**−15.94%**. 5/5 seeds trained.

**Verdict: NEGATIVE on the coherence gate (both Sharpe negative) — but a genuine partial success.**

### The mechanism WORKED exactly as designed (QE execution-consistency validated in the real run)
- Exit mix: **0 take_profit** (IS+OOS) — confirms winners ran to the timeout, not truncated at a TP
  barrier. Exits = stop_loss (106 IS / 47 OOS) + timeout (65 IS / 31 OOS) only.
- **Payoff asymmetry materialized:** IS avg win **+6.46%** vs avg loss **−3.11%** → payoff **2.08**;
  OOS avg win +4.26% vs avg loss −2.43% → payoff **1.75**. "Cut losers, let winners run" is live.

### The binding constraint is the HIT RATE / regime, not the label or features
- Win rate **32.7% IS / 33.3% OOS**. At a ~33% win rate the breakeven payoff is exactly **2.0**.
- IS payoff 2.08 clears breakeven by a hair → IS total net +4.43% (but Sharpe −0.09: the equity curve
  is lumpy/volatile relative to the small drift — positive-skew profile the symmetric Sharpe penalizes).
- OOS payoff 1.75 sits **BELOW** the 2.0 breakeven → OOS net −15.94%, Sharpe −0.74. The whole OOS loss
  is the payoff slipping under breakeven, i.e. the model's directional edge isn't robust OOS.

### Best IS of the campaign + the proxy-overprediction lesson (again)
- IS −0.09 is the closest-to-zero IS across iter-001→009 (prior best −0.17). The label-mode change
  DID improve IS learnability — directionally consistent with the FE proxy, just far smaller.
- **FE IS Sharpe PROXY was +1.28 (8/8 seeds); the real backtest IS was −0.09.** Third time an offline
  proxy massively overpredicted vs the bagged specialist (cf. funding standalone-importance rank
  8→29). Offline purged-CV proxies ignore SL truncation of would-be winners, fees+slippage, the R3/R5
  gates, the confidence-threshold trade filter, and the K-study bagging. **Weight the backtest, not
  the proxy.** (Logged for the FE: report proxies as direction-only, never magnitude.)

**OOS-vigilance:** FE iter-009 scripts verified IS-only (5 scripts, strict pre-cutoff filter +
leak-guard assert each). QE wiring kept /002-/007 byte-identical; no OOS touched in design.

**Lessons**
- The let-winners-run asymmetric-payoff structure is the right crypto-native frame (capture trend
  persistence, cut losers) and it WORKS — but a ~33% blind hit rate sits exactly at breakeven, so the
  strategy is only as good as its trade SELECTION. The next lever is raising the hit rate / trading
  only favorable regimes — NOT more features or another horizon in isolation.
- This is the iter-008 regime question reborn under the correct (Sharpe + let-winners-run) frame: a
  TRENDING/high-vol regime should raise both the hit rate AND the payoff for a let-winners-run book.

**Next:** iter-v1/010 — KEEP the fixed_horizon let-winners-run execution; add a **regime gate** so the
book only trades when crypto trend-persistence favors the asymmetric payoff (trend/vol state). This
directly attacks the diagnosed hit-rate constraint AND executes the user's mandated Sharpe-lens
re-examination of the iter-008 regimes (always-LONG out-RETURNED the model there, but on a SHARPE /
let-winners-run basis the trending regime may be the edge). Crypto-QR designs the gate IS-only
(which regime, threshold, retained trade count ≥~10/mo). Alternative horizon (fixed_horizon N9/3d,
FE's highest proxy) held in reserve if the regime gate fails.
