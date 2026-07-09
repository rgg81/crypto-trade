# EXPLORATION-004 — Long-Biased Multi-Factor + Leg-Decoupled Defense

## Section 0 — Provenance (pre-registration)

- **Frozen:** 2026-07-09, BEFORE any backtest run of this design. IS-only.
- **OOS sealed:** `OOS_CUTOFF = 2025-03-24`. Not looked at, not planned around.
- **Track:** baseline-blind top-20 L/S portfolio (this worktree).
- **Predecessors (the verified evidence base, all IS-only):**
  - `diary-portfolio-blind/PHASE7-003.md` + `REVIEW-003.md` + `analysis/portfolio/blind_diag_partition.py`
    — the partition diagnostic that resolved the attribution. The 2×3 table that
    is the load-bearing evidence for THIS design:
    | signal | midvol_short (skip-tail) | rank_neutral (no-skip L/S) | longonly_tophalf |
    |---|--:|--:|--:|
    | vol_low | +0.09 (−48% DD) | −0.14 (−79%) | **+0.51 (−87%)** |
    | rev_3 | −0.65 (−72%) | −0.66 (−87%) | **+0.26 (−92%)** |
    **Net finding:** rev_3 L/S is negative regardless of partition (shorting winners
    blows up in mania); rev_3 LONG-ONLY is +0.26 (real harvestable bounce alpha);
    vol_low LONG-ONLY is +0.51. The alpha is real, long-side-only, on BOTH signals.
  - `diary-portfolio-blind/EXPLORATION-001-engineering.md` — vol_low long-only
    Sharpe **+0.51**, MaxDD **−87%**, turnover **73x**, 2021 **+1.54**, 2022 **−1.53**,
    funding drag **+7216 bps** total (~+12%/yr; **+3722 bps in 2021 alone**). VT
    variant **UNDERPERFORMED** (+0.38 vs +0.51): VT de-levers calm years and is too
    slow/reactive to catch crypto's sharp regime switches (mean gross 0.78 — chronic
    de-lever because crypto vol > the 0.40 target).
  - `diary-portfolio-blind/EXPLORATION-002-engineering.md` — mid-vol tail-capped
    near-neutral L/S: Sharpe **+0.09**, MaxDD **−48.5%**, 2021 **−0.38**, 2022 **+0.89**,
    2021 funding **−240 bps** (NET INCOME). **Short-leg 2022 price P&L = +0.9280**
    (captured the broad bear deleveraging); **short-leg 2021 funding income = −2139.7 bps**
    (received mania funding). The mid-vol short CONSTRUCTION is a verified defensive
    substrate — it just carries ~0 net alpha.
  - `diary-portfolio-blind/EXPLORATION-003-engineering.md` + `REVIEW-003.md` — the
    single-signal z-blend through `midvol_short` FAILED (−0.36): the blend's SHORT band
    inherited rev_3's drag AND introduced a new failure mode (REVIEW-003 F3: a crashed
    coin has z(vol_low)≈−3, z(rev_3)≈+3 → blended z≈0 → SHORT band → squeezes in mania).
    Realized orthogonality **HELD in production** (corr −0.036 vs probe −0.006) → the
    failure is downstream of the signal (partition mismatch + short-side toxicity), NOT
    an orthogonality breakdown.
  - `briefs-portfolio-blind/EXPLORATION-001/002/003.md` — pre-registration rigor to match.
- **Blinding:** designed against `blind_engine.py`, `blind_signals.py`,
  `blind_universe.py`, `blind_funding.py`, `blind_diag_partition.py`, and the blind
  EXPLORATION-001/002/003 diaries only. No baseline artifact read. OOS never inspected.
- **Choice provenance:** direction (long-biased multi-factor + defense) chosen by the
  user; the leg-decoupled construction + BTC-drawdown long-leg scalar are this QR's
  design choices, forced by the partition diagnostic's attribution.

---

## Section 1 — Hypothesis (one paragraph)

**A long-biased, leg-decoupled multi-factor book that (a) LONGS the cross-sectional top of the `0.5·z(vol_low)+0.5·z(rev_3)` blend — capturing BOTH verified orthogonal long-side alpha sources where each is confirmed net-of-cost positive (vol_low +0.51, rev_3 +0.26, corr −0.036) — at gross_long=0.7, (b) SHORTS only the mid-volatility band by vol_low rank at gross_short=0.3 while SKIPPING the extreme-vol lottery tail, reusing the EXPLORATION-002 construction that delivered a verified partial funding dodge (2021 net funding −240 bps income at gross 0.5) and 2022 crash dampening (short-leg price P&L +0.93) WITHOUT any short-side alpha claim, and (c) overlays a past-only BTC-drawdown regime scalar on the LONG leg alone — de-risking long exposure linearly from 20% to 50% BTC drawdown-off-180d-peak down to a 0.30 floor, directly targeting the 2022 correlated-deleveraging crash that produced the −87% maxDD while leaving the short hedge at full gross exactly in the bear regime where it is confirmed most profitable — lifts the deployable IS Sharpe to ≥ +0.60 (= EW-top-20 + 0.15) at maxDD ≥ −50%, a combination that pure long-only (+0.51 / −87%) and near-neutral L/S (+0.09 / −48%) each individually failed to achieve, by decoupling the two verified alpha legs (multi-factor long) from the defensive leg (single-factor mid-vol short) so each signal drives only the side of the book where it is confirmed to work.**

---

## Section 2 — Chosen construction + crypto-native rationale

### 2.1 This is a MULTI-COMPONENT design (user-directed)

The user explicitly opted for the full engineering push over strict one-change. This
iteration integrates THREE components in one book: (1) multi-factor long blend,
(2) risk-capped mid-vol short, (3) long-leg regime defense. **The attribution that a
single-change iteration provides inline is delivered here by the INCREMENTAL RUN LADDER
(§3.6): R1→R2→R3 isolates multi-factor synergy, R3→R4 isolates short-leg defensive
value, R4→R5 isolates regime-gate defense value.** Each rung is one component added on
top of the prior, all in the same engine shell, all IS-only.

### 2.2 The core architectural decision — LEG-DECOUPLING (forced by the partition diagnostic)

Every prior builder fed ONE signal to BOTH legs through a single ranking. The partition
diagnostic (`blind_diag_partition.py`) proved this is the wrong architecture:

- **Long side:** vol_low long-only = +0.51; rev_3 long-only = +0.26. BOTH positive.
  The alpha is there, on the long side, for both signals.
- **Short side:** vol_low L/S = −0.14; rev_3 L/S = −0.66. BOTH negative. Shorting
  winners (rev_3) or high-vol (vol_low) blows up in mania regardless of partition.
- **The mid-vol tail-capped short** (EXPLORATION-002) is the ONE short construction
  that does not blow up: it carries ~0 net alpha but delivers verified DEFENSIVE value
  (funding dodge + crash dampening). Its defense is driven by vol_low's ranking (skip
  extreme vol, short the mid band).

**Therefore:** the long leg and the short leg must be driven by DIFFERENT signals.
The long leg uses the multi-factor blend (both alpha sources where they work); the
short leg uses vol_low alone (the defensive construction where its IC is structural, not
a blow-up source). A crashed coin (z(vol_low)≈−3, z(rev_3)≈+3) that the single-signal
blend pushed into the SHORT band (EXPLORATION-003's REVIEW-003 F3 failure) is here
**SKIPPED on both legs**: the blend ranks it mid (not in the long top-half) and vol_low
ranks it in the extreme-vol SKIP band (not shorted). The crashed-coin-into-short failure
mode is structurally eliminated by decoupling.

### 2.3 Component 1 — Multi-factor long blend (the alpha engine)

Reuse the existing, leak-safe, 23/23-tested `blended_signal(panel, univ)` =
`0.5·z_cs(vol_low) + 0.5·z_cs(rev_3)` (parameter-free equal-weight midpoint, no scan).
Feed it to the EXISTING `target_weights_longonly` builder at `long_frac=0.5` (top 10 of 20).
This is run R3 standalone (gross=1.0) for the multi-factor-synergy attribution, and is
the long-leg driver for R4/R5 (at gross_long=0.7).

**Crypto-native rationale:** vol_low captures the retail lottery-preference anomaly
(slow-decaying, defensive, low-turnover); rev_3 captures short-term mean reversion
(fast-decaying, bounce-on-crash, higher-turnover). At corr −0.036 they are genuinely
orthogonal at 8h — combining them targets a combined IC ≈ √(0.052² + 0.045²) = 0.069
(+33% over vol_low alone). The prior blend failure (EXPLORATION-003 −0.36) was on the
SHORT side through `midvol_short`; on the LONG side (longonly_tophalf) both parents are
individually positive, so the blend's long-side synergy is the open, genuinely-uncertain
question that R3 settles.

### 2.4 Component 2 — Risk-capped mid-vol short at gross_short=0.3 (the hedge)

The short leg is the EXPLORATION-002 construction verbatim — vol_low-ranked mid band
(short_frac=0.25 = 5 of 20), SKIP the extreme-vol tail (5 of 20) — but at gross_short=0.3
(0.6× EXPLORATION-002's 0.5 gross). This is a PARTIAL hedge, not a dollar-neutral leg:

| leg | signal | selection (n=20) | per-name weight | gross |
|---|---|---|---|---|
| LONG | blend (vol_low+rev_3) | top 10 by blend rank | +0.07 (= 0.7/10) | 0.7 |
| SHORT | vol_low only | mid-vol band (vol-ranks 11–15) | −0.06 (= 0.3/5) | 0.3 |
| SKIP | — | extreme-vol tail (vol-ranks 16–20) | 0 | 0 |
| **net** | | | | **+0.4** |

**Why 0.7/0.3 (net-long +0.4), not pure long-only and not near-neutral:**
- Pure long-only (gross 1.0) pays the FULL ~12%/yr funding tax (+7216 bps; +3722 bps in
  2021) and eats the full −87% crash. The funding tax consumed ~98% of the long book's
  gross price P&L over IS.
- Near-neutral (EXPLORATION-002, 0.5/0.5) dodged funding but had ~0 alpha (+0.09) — the
  short adds no alpha, and at 0.5 gross it offsets too much of the long return.
- **0.7/0.3 is the principled midpoint:** the long leg keeps 70% of gross (captures the
  bulk of the +0.51/+0.26 alpha) while the short leg at 30% provides a PARTIAL funding
  dodge (scales EXPLORATION-002's −2139 bps 2021 short income to ~−1283 bps, offsetting
  ~0.7×2659 ≈ +1860 bps of long payment → net 2021 funding ≈ +580 bps, vs long-only's
  +3722) AND partial crash dampening (scales the +0.93 2022 short-leg price P&L to ~+0.56).
  The short is sized small enough that its mania-year price drag (2021 −1.01 at gross 0.5
  → ~−0.61 at gross 0.3) does not dominate, but large enough to move the funding+DD needle.

**Why vol_low drives the short leg (not the blend):** the short leg's job is DEFENSE
(funding dodge + crash skip), not alpha. vol_low's ranking defines the mid-vol band
(established mid-caps) vs the extreme-vol tail (the 10–100× mooners that blew up every
L/S). The blend would pull crashed coins into the short band (EXPLORATION-003 F3);
vol_low alone keeps the short construction identical to the verified EXPLORATION-002
substrate.

### 2.5 Component 3 — BTC-drawdown long-leg regime scalar (the crash defense)

**Chosen defense: regime gate (NOT vol-target).** The decision is forced by EXPLORATION-001's
verified VT-underperformance finding (+0.38 vs +0.51):

- **Why VT is the wrong tool for crypto crash defense.** VT scales gross inversely to
  realized vol with a lagging lookback. Crypto's chronic high vol (vs a 0.40 target) means
  VT permanently de-levers the book (EXPLORATION-001 mean gross 0.78 — a chronic alpha
  tax). And the −87% maxDD is NOT a vol-clustering phenomenon — it is a REGIME SWITCH
  (correlated deleveraging: Luna May 2022, 3AC June-July, FTX Nov 2022). VT's lagging
  lookback de-risks AFTER the crash has hit and re-risks during bear-market relief rallies
  (catching the next leg down). VT reacts to vol level; the failure is a regime transition.
- **Why a BTC-drawdown regime gate is right.** Crypto alts are high-beta to BTC. When BTC
  draws down deeply, liquidity drains, leverage unwinds in cascades (BIS WP 1087, 2025:
  carry/funding shocks predict liquidation jumps), and the entire alt complex correlates
  downward — exactly the 2022 mechanism. A drawdown gate detects the crash regime DIRECTLY
  and, critically, is **MONOTONE during a sustained bear**: once BTC is −25% off peak it
  stays ≤ −25% until recovery, so the gate stays de-risked through the whole bear (unlike
  VT which re-levers on every bear-market bounce).

**Why the scalar applies to the LONG leg ONLY (the key crypto-native design choice):**
in a crash regime, the short leg is the HEDGE — it is confirmed profitable in 2022
(+0.93 price P&L, +0.89 Sharpe year) and receives funding income in stress. Scaling the
short down in a crash would scale down the book's only crash-profitable leg. The long leg
IS the crash exposure (10 alts correlating to ~1 with BTC's drawdown). So: de-risk the
long, keep the short. The book flips from net-long +0.4 (bull: capture alpha) toward
net-short (deep crash: long floor 0.30×0.7=0.21 vs short 0.3 → net −0.09) exactly when it
should. This is the defensive asymmetry the prior symmetric constructions could not express.

**Indicator + scalar (past-only, pre-registered defaults — risk-engineer calibrates §7):**

```
btc_dd[t]   = max(0, 1 - close_btc[t] / max(close_btc[t-L+1 .. t]))      # L = 540 (180d at 8h)
scalar[t]   = clip(1 - (btc_dd[t] - threshold) / band, floor, 1.0)       # threshold=0.20, band=0.30, floor=0.30
g_long[t]   = gross_long * scalar[t]                                     # applied at rebal: uses scalar[k-1]
g_short[t]  = gross_short                                                # NEVER scaled by the regime gate
```

- BTC within 20% of its 180d peak → scalar = 1.0 (full long).
- BTC −35% off peak → scalar = 0.5 (long halved).
- BTC ≤ −50% off peak → scalar = floor = 0.30 (long at 30% of budget; deep-crash floor
  maintains recovery exposure).
- Past-only: rolling max uses `close_btc[t-L+1 .. t]`, all known at `close[t]`. Decision
  uses `scalar[k-1]` (computed from close up to `close[k-1]`), filled at `open[k]`.

### 2.6 Honest prediction summary (pre-registered so a null is informative)

| metric | prediction (R5 primary) | confidence | key reference |
|---|---|---|---|
| IS Sharpe | **+0.55 to +0.72** | low-moderate. Multi-factor synergy + defense value are BOTH unverified at this construction. | best prior: vol_low long-only +0.51 |
| MaxDD | **−35% to −52%** | moderate. Regime gate on long leg is the direct lever; floor=0.30 keeps some crash exposure. | prior long-only −87%; near-neutral −48% |
| 2021 Sharpe | +0.8 to +1.4 | moderate-high. BTC near peak → full long; short is mild drag. | long-only 2021 +1.54 |
| 2022 Sharpe | −0.2 to +0.5 | moderate. Regime gate de-risks long; short profits at 0.3 gross. | long-only 2022 −1.53; near-neutral +0.89 |
| 2021 funding | +400 to +1400 bps | low-moderate (TIGHT on G-FUND). Short at 0.3 receives ~−1283 bps; long at 0.7 pays ~+2659 bps. | near-neutral −240 bps; long-only +3722 bps |
| Turnover | 70–110x/yr | moderate. Blend's rev_3 component raises long-leg churn vs vol_low's 73x. | long-only 73x; near-neutral 138x |
| 2x-cost Sharpe | +0.25 to +0.55 | low. Borderline on G-COST. | long-only 2x +0.44 |

---

## Section 3 — Exact implementation spec (for the quant-engineer)

### 3.1 Signals (REUSE existing — no new signal code)

- **Long-leg signal** = `blended_signal(panel, univ)` from `blind_signals.py` (already
  23/23-tested, leak-safe). `0.5·z_cs(vol_low) + 0.5·z_cs(rev_3)`, defaults FROZEN.
- **Short-leg signal** = `lowvol_signal(panel)` (re-exported from `blind_sanity_lowvol`,
  byte-identical to EXPLORATION-001/002). High = low vol = the ranking that defines the
  mid-vol band / extreme-tail skip.
- **rev_3 standalone (for R2 parity)** = `rev3_signal(panel)` from `blind_signals.py`.

### 3.2 NEW builder — `target_weights_longbias_ls` (leg-decoupled asymmetric L/S)

```python
def target_weights_longbias_ls(
    long_signal_row: np.ndarray,    # blended signal (drives LONG selection)
    short_signal_row: np.ndarray,   # vol_low signal (drives SHORT band + tail skip)
    univ_row: np.ndarray,
    gross_long: float,              # long-leg gross budget (e.g. 0.7), BEFORE scalar
    gross_short: float,             # short-leg gross budget (e.g. 0.3), NEVER scaled
    long_frac: float = 0.5,         # top long_frac of universe longed (10 of 20)
    short_frac: float = 0.25,       # mid-vol band shorted (5 of 20)
    long_scalar: float = 1.0,       # regime scalar applied to gross_long at this step
) -> np.ndarray:
    """Long-biased leg-decoupled L/S.

    LONG:   top `long_frac` of universe by `long_signal` rank, equal-weight,
            at gross_long * long_scalar each-name budget.
    SHORT:  mid-vol band (`short_frac`) by `short_signal` rank, equal-weight,
            at gross_short budget. SKIP the extreme-vol tail (lowest short_signal).
    LONG-PRECEDENCE on overlap: a name in both masks -> LONG only (short dropped,
            short gross reduced by one name's worth; NOT re-allocated — deterministic).

    Invariants (n>=4): all longs > 0; all shorts < 0; skipped names == 0;
    extreme-vol tail NEVER shorted; sum(w_long) = gross_long*long_scalar (minus any
    overlap drop); sum(w_short) = -gross_short (minus any overlap drop).
    """
    w = np.zeros_like(long_signal_row, dtype=float)
    m = univ_row & np.isfinite(long_signal_row) & np.isfinite(short_signal_row)
    n = int(m.sum())
    if n < 4:
        return w

    # LONG leg: rank by long_signal, top long_frac
    r_long = rankdata(long_signal_row[m]) - 1.0          # 0 = lowest blend
    k_long = max(1, int(round(n * long_frac)))
    long_threshold = n - k_long
    long_mask = r_long >= long_threshold

    # SHORT leg: rank by short_signal, mid band (0 = lowest = highest vol = tail to SKIP)
    r_short = rankdata(short_signal_row[m]) - 1.0
    k_short = max(1, int(round(n * short_frac)))
    short_hi = n - k_long                                 # same upper edge as long_threshold
    short_lo = max(0, short_hi - k_short)                 # short_lo <= r_short < short_hi
    short_mask = (r_short >= short_lo) & (r_short < short_hi)

    # LONG-PRECEDENCE: drop short where overlap
    short_mask = short_mask & ~long_mask

    n_long = int(long_mask.sum())
    n_short = int(short_mask.sum())
    if n_long == 0:
        return w
    g_l = gross_long * long_scalar
    w[m] = np.where(
        long_mask,
        g_l / n_long,
        np.where(short_mask, -gross_short / max(n_short, 1), 0.0),
    )
    return w
```

**Note on the short upper edge `short_hi = n - k_long`:** the short band sits immediately
below the long band on the vol_low ranking, identical to `target_weights_midvol_short`'s
partition (long_threshold − k_short). This means the short mid-band is defined relative to
the vol_low ranking, independent of the blend. A name just below the long cutoff on vol_low
is mid-vol → short candidate. The blend independently decides the longs. The two
selections are decoupled except for the long-precedence overlap rule.

### 3.3 NEW regime scalar — `btc_drawdown_scalar` (past-only long-leg defense)

```python
def btc_drawdown_scalar(
    panel: Panel,
    lookback: int = 540,        # 180 days at 8h
    threshold: float = 0.20,    # start de-risking at 20% BTC drawdown
    band: float = 0.30,         # ramp to floor over 30pp (full floor at -50% drawdown)
    floor: float = 0.30,        # long-leg gross retained in deepest crash
) -> np.ndarray:
    """Past-only BTC-drawdown-based long-leg regime scalar (T,).

    scalar[t] = clip(1 - (dd[t] - threshold)/band, floor, 1.0)
    dd[t]     = max(0, 1 - close_btc[t] / max(close_btc[t-L+1 .. t]))

    Monotone non-increasing in dd. Past-only: rolling max over close[t-L+1..t]
    (all known at close[t]). Returns (T,) array; scalar[k-1] is used at rebal step k.
    """
    col = panel.sym_col("BTCUSDT")
    if col is None:
        return np.ones(panel.close.shape[0])   # defensive: no BTC -> no gate
    close_btc = panel.close[:, col]
    T = close_btc.shape[0]
    out = np.ones(T)
    for t in range(T):
        lo = max(0, t - lookback + 1)
        window = close_btc[lo:t + 1]
        window = window[np.isfinite(window)]
        if len(window) < 2:
            continue
        peak = float(window.max())
        cur = close_btc[t]
        if not np.isfinite(cur) or peak <= 0 or cur <= 0:
            continue
        dd = max(0.0, 1.0 - cur / peak)
        out[t] = min(1.0, max(floor, 1.0 - (dd - threshold) / band)) if dd > threshold else 1.0
    return out
```

**Defaults are round/principled, NOT optimized:** 180d lookback captures the structural
peak within a ~12-month bear (2021-11 peak visible from 2022-02 through 2022-05 at 180d);
20% threshold = standard "correction" boundary; 50% (threshold+band) = "deep bear";
floor 0.30 retains recovery exposure. **The risk-engineer calibrates these IS-only (§7),
then FREEZES before the R5 gated run.** No param scan after the first R5 result.

### 3.4 Engine dispatch — extend `run_backtest` (additive, backward-compatible)

Add to `run_backtest(...)`:

```python
    # NEW params (default to no-op so existing modes are byte-identical):
    long_signal: np.ndarray | None = None,        # (T,C) long-leg signal; default = signal
    gross_long: float | None = None,              # default = gross
    gross_short: float | None = None,             # default = 0.0 (no short leg)
    long_scalar_series: np.ndarray | None = None, # (T,) regime scalar; default = ones
```

Add `"longbias_ls"` to the allowed `weighting` set. In the rebal block:

```python
    elif weighting == "longbias_ls":
        lsig = long_signal if long_signal is not None else sig
        gl = gross if gross_long is None else float(gross_long)
        gs = 0.0 if gross_short is None else float(gross_short)
        lsc = long_scalar_series[k - 1] if long_scalar_series is not None else 1.0
        w_tgt = target_weights_longbias_ls(
            lsig[k - 1], sig[k - 1], universe[k - 1], gl, gs, lf, sf, lsc
        )
```

Note: `sig` (the existing `signal` arg) is the SHORT-leg signal (vol_low); `long_signal`
is the blend. The VT path (`vol_target_ann`) is independent and remains available but is
NOT used in the primary R5 (regime gate replaces VT). Existing modes (`rank_neutral`,
`longonly_tophalf`, `ew_long`, `midvol_short`) are byte-identical — the new params default
to inert values.

### 3.5 Backtest configuration

| parameter | R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|---|
| `weighting` | `longonly_tophalf` | `longonly_tophalf` | `longonly_tophalf` | `longbias_ls` | `longbias_ls` |
| `signal` (short-leg/vol_low) | `lowvol_signal` | `rev3_signal` | `blended_signal` | `lowvol_signal` | `lowvol_signal` |
| `long_signal` | — | — | — | `blended_signal` | `blended_signal` |
| `gross` | 1.0 | 1.0 | 1.0 | — | — |
| `gross_long` / `gross_short` | — | — | — | 0.7 / 0.3 | 0.7 / 0.3 |
| `long_frac` / `short_frac` | 0.5 / — | 0.5 / — | 0.5 / — | 0.5 / 0.25 | 0.5 / 0.25 |
| `long_scalar_series` | — | — | — | — | `btc_drawdown_scalar(panel)` |
| `rebal` | 6 | 6 | 6 | 6 | 6 |
| `cost` | 5+2.5bps, fund ON | same | same | same | same |
| `funding` | `load_funding(panel)` | same | same | same | same |
| `vol_target_ann` | None | None | None | None | None |

### 3.6 Required runs — the incremental attribution ladder (all IS-only, one committed table)

| run | purpose | what the delta isolates |
|---|---|---|
| **R1** vol_low long-only | parity (+0.51) + alpha anchor | (parity check vs EXPLORATION-001) |
| **R2** rev_3 long-only | parity (+0.26) + second alpha anchor | (parity check vs partition diagnostic) |
| **R3** blend long-only | **multi-factor synergy (G-ALPHA-MF)** | R3 − max(R1,R2) = blend value-add on long side |
| **R4** blend long + mid-vol short 0.7/0.3 | **short-leg defensive value** | R4 − R3 = funding dodge + crash dampening − short alpha drag |
| **R5** R4 + long-leg BTC-dd scalar | **crash defense (G-DD, G-DEPLOY)** | R5 − R4 = regime-gate defense value (maxDD taming) |
| **B-EW** EW-top-20 | deployability benchmark | G-DEPLOY relative anchor (+0.45) |
| **B-BTC** B&H BTC | absolute benchmark | (+1.07; not expected to clear) |
| **R5×2** R5 at 2x cost | cost-robustness (G-COST) | cost sensitivity of the full book |
| **R3×2** R3 at 2x cost | multi-factor cost-robustness | is the blend's synergy cost-fragile? |
| **P-RN** rank_neutral parity | engine regression check | must reproduce −0.14 (EXPLORATION-001/002) |

- Per-year Sharpe reported for R1, R2, R3, R4, R5, B-EW.
- Funding-by-year (bps) reported for R3, R4, R5 (the funding-dodge attribution across the
  ladder).
- Per-leg price P&L by year reported for R4, R5 (long leg vs short leg contribution).
- **Overlap diagnostic** for R4/R5: fraction of rebal steps where ≥1 name is in both masks
  (long-precedence triggered). Expected low (blend's vol_low component keeps high-vol names
  out of longs); report to confirm.
- **Regime-scalar diagnostic** for R5: mean scalar, fraction of IS candles at scalar<1.0,
  fraction at floor; the scalar time-series vs the 2022 BTC drawdown (confirm it fired).
- Max per-name |w|, gross-leverage series, dollar-neutrality (mean|sum(w)|) for R4, R5.

### 3.7 Mandatory test extension (leak-safety + decoupling discipline)

Extend `tests/test_blind_engine.py`. Target: 23 existing + 7 new = 30 green. Existing 23
stay byte-identical (regression guard — R1/R2/parity depend on them).

1. **`test_longbias_ls_gross_and_sign_discipline`** — at every rebal with n≥4:
   sum(w_long) = gross_long × long_scalar (within overlap drop); sum(w_short) = −gross_short
   (within overlap drop); all longs > 0; all shorts < 0; skipped names == 0.
2. **`test_longbias_ls_long_precedence_on_overlap`** — construct a row where one name ranks
   in BOTH the long mask (high blend) and the short mid-band (mid vol_low) → assert its
   weight is POSITIVE (long), not negative. The short budget drops one name's worth.
3. **`test_longbias_ls_decoupled_selection`** — construct a row where the blend and vol_low
   DISAGREE (name A: high blend, mid vol_low; name B: low blend, mid vol_low) → assert A is
   longed, B is shorted. Each leg picks by ITS OWN signal. (Behavior lock, not desirability.)
4. **`test_longbias_ls_skips_extreme_tail_short`** — a name with very low vol_low signal
   (100× mooner) is in the SKIP band: weight 0, NEVER shorted. Inherits EXPLORATION-002's
   load-bearing defensive property on the short leg.
5. **`test_btc_drawdown_scalar_past_only`** — corrupt `panel.close[BTC_col, t:]` forward →
   `scalar[:t]` bit-identical. (Leak positive-control on the regime indicator.)
6. **`test_btc_drawdown_scalar_monotone_in_bear`** — construct a BTC close series that draws
   down monotonically from peak → scalar is non-increasing (defense ramps one way; never
   re-risks within a monotone drawdown). And a series that recovers → scalar non-decreasing.
7. **`test_longbias_with_scalar_end_to_end_no_future_leak`** — **LOAD-BEARING**: corrupt
   panel (close/open/vol/quote_volume, incl BTC col) and `long_scalar_series` forward from
   cutoff → `run_backtest(weighting="longbias_ls")` past weights/turnover/equity bit-identical
   to uncorrupted. End-to-end leak assertion for the entire new path.

---

## Section 4 — Pre-registered IS MERGE / NO-MERGE criteria (FROZEN)

Gates apply to the run indicated. All gates evaluated IS-only. Any single failure →
NO-MERGE; the diary records which gate and the observed value. Thresholds pre-registered
BEFORE any run.

| # | gate | threshold | what it tests |
|---|---|---|---|
| G-ALPHA-MF | **R3 Sharpe (blend long-only)** | `≥ max(R1, R2) + 0.07` (= **+0.58** at known R1=+0.51) | **multi-factor synergy.** The blend must beat the stronger single factor by a noise-marginal amount (overlap SE ≈ 0.05–0.08 → +0.07 is ~1–1.5σ). Orthogonal factors SHOULD synergyze (√2 IC lift → +33%); if R3 ≈ R1, there is no synergy — use vol_low-only as the long leg. |
| G-DEPLOY | **R5 Sharpe** | `≥ +0.60` **AND** `≥ EW-top-20 + 0.15` | **deployability.** See §4.1 for the honest threshold reasoning. |
| G-DD | **R5 MaxDD** | `≥ −50%` | **crash defense.** The regime gate must materially tame the −87% long-only / −48% near-neutral maxDD. −50% is the deployability-relevant drawdown ceiling. |
| G-REGIME | **R5 every per-year Sharpe** | `{2020..2025Q1}` all `≥ −1.0` | regime robustness; 2022 is the crux (defense + short profit must offset the long crash). |
| G-FUND | **R5 2021 funding drag** | `≤ +1500 bps` | funding dodge inherited from EXPLORATION-002; **TIGHT** — the 0.3 short gross offsets less than 0.5 did (predicted ~+580 bps net, but composition shift risk is real). |
| G-COST | **R5 2x-cost Sharpe** | `≥ +0.50` | cost-robustness of the full defended book. |

### 4.1 G-DEPLOY threshold — honest reasoning (why +0.60, not +1.0)

**+1.0 is not achievable and I will not pre-register a gate I am ~85% confident will fail.**
The evidence ceiling is binding: the BEST single construction is vol_low long-only +0.51
(half of B&H BTC's +1.07). The long-side alpha is real but weak; the barriers (funding tax,
crashes) are structural and severe. The multi-factor synergy (R3) might lift the long leg
to ~+0.58–0.65 IF the √2 IC lift converts; the short hedge + regime gate might add ~+0.05–0.10
of defensive Sharpe (lower vol/funding in the denominator) while costing some bull-year
return. An honest ceiling estimate for R5 is **+0.60 to +0.72**. Setting G-DEPLOY at +1.0
would make NO-MERGE the near-certain outcome and waste the iteration's informational value.

**+0.60 is the minimum meaningful deployability threshold** because:
1. It equals **EW-top-20 + 0.15** (EW=+0.45), the noise-marginal edge over naive
   (REVIEW-001 S3: overlap SE ≈ 0.05–0.08; +0.15 is ~2σ — the minimum claimable edge).
2. A book that clears +0.60 Sharpe AND maxDD ≥ −50% AND every-year ≥ −1.0 AND 2x-cost
   ≥ +0.50 is a **genuinely deployable defensive long-biased book** — it does not beat B&H
   BTC on raw return, but it beats it on the Sharpe-and-drawdown axis that is this track's
   objective, and it does so with a tamed crash profile that B&H BTC's −70%+ drawdowns lack.
3. Setting it higher (e.g. +0.70) would risk killing a +0.63 result that is real and
   deployable — the wrong yardstick (this is the equity-efficient-market error the user's
   directive warns against: demanding absolute return coherence over risk-adjusted merit).

**The REAL deployability signal is the conjunction of ALL gates**, not G-DEPLOY alone. A
book at Sharpe +0.60 / maxDD −42% / every-year ≥ −1.0 / 2x-cost +0.52 is a MERGE; a book at
Sharpe +0.60 / maxDD −65% is NOT (G-DD fails). The gates compound.

### 4.2 What makes me NO-MERGE (each failure points to a specific next step)

- **G-ALPHA-MF fails (R3 < +0.58):** the blend has no long-side synergy over vol_low alone.
  → Fallback: re-run R4/R5 with `long_signal = lowvol_signal` (vol_low-only long leg). If
  R5-vol_low-only passes G-DEPLOY, deploy that (multi-factor deferred). If it also fails,
  the long-side alpha ceiling is ~+0.51 and the book cannot reach +0.60 regardless of
  defense → the scope break (OI-universe or non-OHLCV mechanism) is forced.
- **G-DEPLOY fails (R5 < +0.60) but G-DD passes:** the defense works but the alpha engine
  is too weak. → The long-side OHLCV alpha is exhausted at this universe/frequency; next
  EXPLORATION is a scope break (OI-ranked universe, or funding/on-chain mechanism), not a
  defense-parameter tweak.
- **G-DD fails (R5 maxDD < −50%):** the BTC-drawdown gate is too slow/blunt for crypto's
  crash dynamics. → Risk-engineer refines: shorter lookback, lower threshold, lower floor,
  OR a long-leg-AND-short-leg scalar (symmetric de-risk). OR add a cross-sectional-
  dispersion co-trigger (crash = BTC dd + high XS dispersion).
- **G-REGIME-2022 fails:** the regime gate de-risked the long but the 2022 short leg
  underdelivered at 0.3 gross. → Increase gross_short (risk-engineer calibration) OR add a
  second short-side defense.
- **G-FUND fails (2021 > +1500 bps):** the 0.3 short gross dodges too little funding.
  → Increase gross_short (more mania funding income) — but this trades against short-side
  toxicity. Risk-engineer finds the IS sweet spot.
- **G-COST fails (2x < +0.50):** the book is cost-fragile (blend's rev_3 turnover).
  → EXPLORATION-005 = turnover-reduction primitive (hysteresis / eligibility-exit buffer,
  REVIEW-002 S1 — the highest-ROI cost axis regardless of /004's outcome).

---

## Section 5 — Predicted effect + informative null

### Predicted ladder (the attribution the diary will report)

| run | predicted Sharpe | predicted MaxDD | vs prior rung |
|---|---|---|---|
| R1 vol_low long | +0.51 (parity) | −87% | — |
| R2 rev_3 long | +0.26 (parity) | −92% | — |
| R3 blend long | **+0.50 to +0.62** | −85 to −90% | synergy test (G-ALPHA-MF) |
| R4 blend+short 0.7/0.3 | **+0.48 to +0.66** | −60 to −78% | short-leg defense value |
| R5 R4+regime gate | **+0.55 to +0.72** | −35 to −52% | crash-defense value (G-DD, G-DEPLOY) |

**The R4-vs-R3 delta is the subtlest and most important.** The short leg adds ~0 raw
alpha (EXPLORATION-002 proved mid-vol shorts are ~0 net-of-cost). So R4's Sharpe vs R3 is
NOT about return — it is about the DENOMINATOR: the short leg reduces portfolio vol (crash
dampening correlation) and reduces net funding (dodge). If R4 > R3 on Sharpe despite R4
having LESS raw return, the short leg's defensive value is confirmed and the construction
principle (mild net-long + risk-capped short) is validated. If R4 < R3, the short leg's
drag (turnover + mania-year price cost) exceeds its defensive benefit → the short should be
dropped (pure long-only + regime gate is the book).

### The informative null

**If G-DEPLOY fails (R5 < +0.60):** the long-side OHLCV alpha on the PIT-top-20-$-volume
universe at 8h has a hard ceiling around +0.51 (vol_low long-only), and no combination of
multi-factor blending, mild short hedging, and regime gating clears +0.60 deployable. This
is a genuine structural finding (not a tuning problem): the alpha sources DIAGNOSTIC-001
found are collectively too weak to overcome the funding tax + crash drawdown on this
universe at this frequency. It motivates a SCOPE BREAK:
1. **OI-ranked universe** (less adverse-selected than $-volume).
2. **Non-OHLCV mechanism** (funding carry per BIS WP 1087; on-chain Whale Ratio / MVRV-Z).
3. **Different frequency** (the 8h cross-section may be too coarse for these factors).

**If G-ALPHA-MF passes but G-DEPLOY fails:** the blend adds long-side synergy but the
defensive engineering can't lift the book to deployable. → Deploy the best defensive
single-factor book (vol_low long + regime gate) as an interim, and scope-break for alpha.

**If G-DD fails but G-DEPLOY would pass on Sharpe:** the regime gate is the wrong defense.
→ The −87% crash is not BTC-drawdown-predictable (maybe idiosyncratic alt deleveraging);
pivot to cross-sectional-dispersion gate or symmetric gross scalar.

---

## Section 6 — What this does NOT do (scope discipline)

This is a **multi-component** iteration (user-directed). The components are integrated
together BUT attributed via the incremental ladder (§3.6). Explicitly deferred:

- **NO blend-weight optimization.** `w_vol = w_rev = 0.5` is the parameter-free midpoint.
- **NO gross_long/gross_short scan** by the QR. The risk-engineer may calibrate gross_short
  IS-only (§7); the QR pre-registers 0.7/0.3 as the frozen default.
- **NO regime-gate parameter scan** by the QR. The risk-engineer calibrates
  lookback/threshold/band/floor IS-only (§7), then freezes. Max 4 param combos, documented.
- **NO vol-target on the primary R5.** VT is the REJECTED defense (§2.5). A VT-on-R4
  variant MAY be reported diagnostically if the QE/risk-engineer chooses, but is NOT gated
  and NOT expected to help (EXPLORATION-001 evidence).
- **NO turnover-reduction primitive.** Deferred to EXPLORATION-005 (the G-COST-fail path).
- **NO universe change.** Still PIT top-20 by 30-candle $-volume. OI-ranking is the
  scope-break candidate if G-DEPLOY fails.
- **NO signal-window change.** vol_window=12, rev_lookback=3 frozen.
- **NO funding model change.** Same post-S1 `load_funding` panel.
- **NO long-leg-only vs whole-gross scalar comparison as a GATE.** The long-leg-only scalar
  is the pre-registered choice (crypto-native: don't scale down your hedge in a crash). A
  whole-gross variant may be REPORTED diagnostically if the risk-engineer chooses.
- **NO OOS peek.** `OOS_CUTOFF = 2025-03-24` untouched.

---

## Section 7 — Risk primitive + risk-engineer handoff (LEAD AREAS)

The brief requires explicit risk-mitigation design. For EXPLORATION-004, the risk-engineer
LEADS three calibration areas. All calibration is **IS-only**, and final params are
**FROZEN before the gated run** (R4 for short sizing; R5 for the regime gate). The QR's
pre-registered defaults (§3.2–3.3) make the brief runnable without calibration; the
risk-engineer's job is to sharpen the params within the constraints below.

### 7.1 RISK-ENGINEER LEAD — Regime-gate calibration (the crash defense)

- **Indicator:** BTC drawdown from 180d rolling peak (default). Risk-engineer may test
  lookback ∈ {90d (270), 180d (540), 365d (1095)} IS-only. Constraint: pick ONE, freeze.
- **Scalar shape:** threshold/band/floor (default 0.20/0.30/0.30). Risk-engineer may test
  up to 3 combos IS-only on the R4 book (before applying to R5). Constraint: floor ≥ 0.20
  (maintain recovery exposure), threshold ∈ [0.15, 0.30] (don't fire in normal chop, don't
  miss the crash). Document each combo's IS maxDD + Sharpe; pick the one that delivers
  maxDD ≥ −50% with minimal Sharpe cost; FREEZE.
- **Validation:** the risk-engineer MUST confirm the scalar fired during the 2022 bear
  (scalar time-series vs BTC drawdown) and did NOT fire spuriously during 2020-21 bull
  (low false-positive rate). Report mean scalar, % candles at scalar<1.0, % at floor.
- **Multiple-testing note:** the regime gate has 4 params; the risk-engineer's IS sweep is
  a small grid (≤4 combos). The DSR/N_eff impact is acknowledged: this is an EXPLORATION
  (informational), not a CONFIRMATION. The gate's purpose is to verify the defense MECHANISM
  works (maxDD tames), not to claim a hair-cut-adjusted Sharpe.

### 7.2 RISK-ENGINEER LEAD — Risk-capped short sizing (gross_short)

- Default gross_short = 0.3. Risk-engineer may test ∈ {0.2, 0.3, 0.4} IS-only on R4.
  Constraint: pick ONE, freeze before R4 gate eval. The tradeoff: higher gross_short → more
  funding dodge + more 2022 dampening BUT more mania-year short toxicity (2021 drag).
- Report the IS funding-dodge curve (2021 net funding vs gross_short) and the 2021/2022
  per-year Sharpe vs gross_short. Pick the gross_short where 2021 Sharpe stays > 0 AND
  2021 funding ≤ +1500 bps.

### 7.3 RISK-ENGINEER LEAD — Vol-target diagnostic (NOT gated, informational)

- If reported: vol_target_ann ∈ {0.40, 0.60}, max_lev ∈ {2.0, 3.0}. The purpose is to
  CONFIRM or REJECT the EXPLORATION-001 finding (VT underperforms for long-biased crypto
  books) on this L/S construction. Not expected to help; reported for the diary.

### 7.4 Primary risk primitives in the book (not calibration — structural)

1. **Mid-vol tail-capped short** (inherited EXPLORATION-002): extreme-vol lottery tail is
   NEVER shorted (load-bearing test §3.7.4). This is the verified mania-blowup defense.
2. **Long-leg BTC-drawdown scalar:** de-risks long exposure in crash regimes (the 2022
   correlated-deleveraging defense). Long-leg-only → preserves the short hedge in bears.
3. **Gross budget:** total gross = gross_long + gross_short = 1.0 (same leverage as prior
   explorations); net-long +0.4 in calm, toward net-short in deep crash.
4. **The gates ARE the kill-switch.** No additional kill-switch pre-registered.

### 7.5 Report (do not gate on)

- Overlap rate (long∩short masks) per rebal — confirm decoupling is clean.
- Regime-scalar time-series vs BTC drawdown — confirm it fired in 2022, not in 2020-21.
- Per-leg per-year price P&L for R4/R5 — confirm both legs contribute (long: bull alpha;
  short: bear dampening).
- Realized cross-sectional rank-corr(vol_low, rev_3) over IS rebal steps — confirm ≈ −0.036.
- Max per-name |w| (expect long ~7%, short ~6%; flag > 20% — warmup edge may recur).
- Gross-leverage series (confirm mean ~1.0 in calm, drops in crash as long de-risks).

---

## Section 8 — Deliverable checklist for QE + risk-engineer

- [ ] Implement `target_weights_longbias_ls` (§3.2) + `"longbias_ls"` dispatch + new
      `run_backtest` params (§3.4) in `blind_engine.py`. Additive; existing 4 modes untouched.
- [ ] Implement `btc_drawdown_scalar` (§3.3) — past-only, monotone-in-bear. Lives in
      `blind_signals.py` or a new `blind_regime.py` (QE's choice; keep within blinding).
- [ ] 7 new tests in `tests/test_blind_engine.py` (§3.7). 30/30 green.
- [ ] Run script `analysis/portfolio/blind_exploration_004.py` producing the ladder table
      (R1, R2, R3, R4, R5, B-EW, B-BTC, R5×2, R3×2, P-RN) with per-year Sharpe (R1–R5, B-EW),
      funding-by-year (R3, R4, R5), per-leg price P&L (R4, R5), overlap diagnostic (R4, R5),
      regime-scalar diagnostic (R5).
- [ ] **Parity checks:** R1 MUST reproduce +0.51 (EXPLORATION-001 longonly, ±0.005);
      R2 MUST reproduce +0.26 (partition diagnostic, ±0.01); P-RN MUST reproduce −0.14
      (±0.01). If any drifts, STOP and fix before evaluating anything else.
- [ ] **Risk-engineer calibration pass** (§7.1, §7.2) IS-only → freeze gross_short +
      regime-gate params before R4/R5 gated runs. Document each combo tried.
- [ ] Hand results to QR for Phase-7 evaluation against G-ALPHA-MF / G-DEPLOY / G-DD /
      G-REGIME / G-FUND / G-COST. **Do not reveal OOS.**

---

**FROZEN.** Any change to the gates, construction, gross budgets, signal formulas, scalar
formula, or run list after the first backtest run invalidates this pre-registration and
must be recorded as a new EXPLORATION. The risk-engineer's IS-only calibration of
gross_short and regime-gate params (§7.1, §7.2) is the ONLY permitted parameter adjustment,
and its final values must be frozen and documented before the gated R4/R5 runs.
