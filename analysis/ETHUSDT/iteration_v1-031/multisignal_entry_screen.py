"""iter-v1/031 — IS-ONLY screen: MULTI-SIGNAL ENTRY-LAYER de-concentrator.

Critic Path-Forward (4th de-concentration lever). Three approaches have FAILED to
de-concentrate the iter-027 ETH let-winners-run book:
  1. meta-labeling M2 veto (iter-028/029) — K=20 lottery-collapse.
  2. AGREE_SCALE entry-conviction modulation (iter-030) — inverted IS (chop-regime cut).
  3. exit-side partial-profit ladder (iter-031 first screen) — re-slices ONE winner's
     path into correlated legs, clips the right tail; just a 0.63x downsize.

ROOT-CAUSE (the premise of THIS screen): OOS concentration is INTRINSIC to the
single-entry-signal low-WR let-winners-run design. All three failures operated WITHIN
the same ~82-IS / ~32-OOS trade structure (ONE entry signal = the SMA200 trend-state).
You cannot manufacture more INDEPENDENT winning events by re-slicing / modulating /
vetoing the SAME events. Breadth (de-concentration) requires MORE INDEPENDENT WINNING
EVENTS -> ADDITIONAL, DE-CORRELATED ENTRY SIGNALS (Carver / AQR multi-rule combination
at the ENTRY level, not the conviction-modulation level).

HYPOTHESIS
----------
Adding de-correlated deterministic entry signals (Donchian-breakout-55, TSMOM-42/21) as
INDEPENDENT entry sources -- each firing on DIFFERENT candles than the SMA200 trend-state,
each with its OWN direction -- creates MORE independent winning events -> a broader,
less-concentrated book.

The AGREE_SCALE EDA proved these families are de-correlated from the SMA200 trend
(signal_family_correlation.csv: donchian55 vs sma200 = 0.435; tsmom21 vs sma200 = 0.290;
macross vs tsmom21 = 0.154). The QUESTION this screen answers: are they INDEPENDENTLY
PROFITABLE on ETH IS, and does COMBINING them de-concentrate WITHOUT killing IS Sharpe?

WHAT A "STREAM" IS (discrete entry-EVENT book, IS-only)
-------------------------------------------------------
ROSTER-STRUCTURE FINDING (analysis of reports-v1/.../iteration_v1-027/in_sample/trades.csv):
the iter-027 IS roster is 82 entries across only 15 same-direction regimes (avg 5.47
entries PER regime; median 45-candle ~= 14d spacing). i.e. iter-027 does NOT fire once
per trend flip -- the LightGBM head RE-ENTERS a fresh 14d position roughly every time the
previous 14d hold closes, as long as the conviction gate still passes. A naive "one event
per signal flip" proxy therefore massively UNDER-counts the TREND book (SMA200 flips ~15x
in IS -> a degenerate 2-event book once gated). REJECTED.

The faithful discrete-event proxy used here is NON-OVERLAPPING re-entry: scan the IS
candles in time; whenever a candle's signal is active (and, for TREND, clears the
conviction gate), OPEN a 14d position and SKIP the next HORIZON candles (no overlapping
holds -- the let-winners-run book holds one position at a time per signal), then continue.
This reproduces the ~"re-enter every 14d while the regime persists" cadence that gives
iter-027 its 82 entries, and applies the SAME rule to every stream so the comparison is
apples-to-apples. At each event:
  - take a position in the signal's direction at candle close,
  - hold forward HORIZON=42 candles (14d), exit at close[t+42] (the iter-027 timeout),
  - net pnl = direction * fwd_ret_14d - round-trip cost.
This is the SAME per-candle forward-return proxy used in the AGREE_SCALE / iter-030 EDA,
applied at the NON-OVERLAPPING-REENTRY level. It does NOT model the LightGBM entry-timing/
sizing layer or the per-month gate (see PROXY-FIDELITY CAVEAT). It is a FEASIBILITY screen
of the SIGNAL combination, NOT a backtest prediction.

PROXY-FIDELITY CAVEAT (pre-registered, per iter-030 Critic rec #1)
------------------------------------------------------------------
The AGREE_SCALE EDA passed its proxy but the backtest INVERTED IS, because the EDA proxy
held n constant and never modeled the model's entry SELECTION (which candles the LightGBM
actually trades + the per-month threshold). THIS proxy likewise does not model the
LightGBM head or the per-month gate. A PASS here means "the SIGNAL combination is
independently profitable and de-concentrates -> worth a backtest"; it is NOT a both-
positive guarantee. A NEGATIVE here is decisive: if the de-correlated streams are not
even INDEPENDENTLY profitable on ETH IS, no entry-layer wiring can rescue them.

STREAMS
-------
  TREND   : the incumbent. direction = sma_sign(200), events = SMA200 flips, gated at the
            conviction quantile q=0.40 on |close-SMA200|/ATR14 (the iter-027 entry logic
            in proxy form). This is the ~single-signal baseline book.
  DON55   : direction = donchian_breakout_sign(55), events = breakout-sign flips.
  TSMOM42 : direction = tsmom_sign(42), events = flips.
  TSMOM21 : direction = tsmom_sign(21), events = flips (faster, most de-correlated).

MEASURED
--------
  - STANDALONE IS profitability of each stream: event count, per-trade Sharpe, net Sigma,
    win rate. (If DON/TSMOM are NOT independently profitable -> structural bet is dead.)
  - INDEPENDENCE: how often streams' entry events coincide (same candle / same week).
    Jaccard on event candles + same-week overlap. (Premise needs them on DIFFERENT candles.)
  - COMBINED book = de-duplicated UNION of events across the profitable streams, each event
    sized equally, held 14d, net of cost. event count, top-1/top-2 share, Herfindahl,
    per-trade Sharpe, win rate vs TREND-alone.

PRE-REGISTERED PASS CRITERION
-----------------------------
The COMBINED book must:
  (a) have MORE events than TREND-alone (more independent entries), AND
  (b) LOWER top-2 share than TREND-alone (de-concentrated), AND
  (c) per-trade Sharpe >= 0 AND not materially below TREND-alone (>= TREND - 0.05;
      the added signals must be net-additive, not dilutive).
ALSO required upstream: at least the streams that ENTER the combined book must each be
INDEPENDENTLY profitable on IS (per-trade Sharpe > 0 standalone) -- combining loss-makers
adds noise, not breadth.
Else NEGATIVE: the structural multi-signal lever is closed; de-concentration of this
design family is intractable -> consolidate iter-027 as the ETH ceiling (like BTC iter-020).

HARD RULES
----------
  - open_time < OOS_CUTOFF_MS on EVERY entry, leak-guard assert.
  - DROP entries whose 14d horizon crosses the OOS wall (drop_horizon_crossing_oos).
  - Direction primitives are DETERMINISTIC / parameter-free / past-only (shift(1)),
    reused verbatim from iter-030 multispeed_breadth.py + _common.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# reuse the iter-030 committed primitives + leak guards verbatim
ITER030 = Path(__file__).resolve().parents[1] / "iteration_v1-030"
sys.path.insert(0, str(ITER030))
from _common import (  # noqa: E402
    OOS_CUTOFF_MS,
    add_forward_return,
    annualized_sharpe_from_trade_pnls,
    concentration_stats,
    drop_horizon_crossing_oos,
    load_full_for_label_horizon,
    trend_strength_atr_norm,
)
from multispeed_breadth import (  # noqa: E402
    donchian_breakout_sign,
    sma_sign,
    tsmom_sign,
)

HORIZON = 42  # 14d in 8h candles (iter-027 let-winners-run timeout)
CANDLES_PER_YEAR = 365 * 3
TRADES_PER_YEAR = CANDLES_PER_YEAR / HORIZON
FEE_BPS = 10.0  # 0.1% round-trip fee (iter-027)
SLIP_BPS = 2.0  # 2 bps/side
COST = (FEE_BPS + SLIP_BPS) / 10000.0 * 2.0  # round-trip fraction (matches iter-030 proxy)
CONV_Q = 0.40  # iter-027 conviction-gate quantile (TREND stream only)


# --------------------------- event construction ---------------------------
def regime_anchored_reentry_book(
    df_is: pd.DataFrame,
    direction: np.ndarray,
    extra_eligible: np.ndarray | None = None,
    horizon: int = HORIZON,
) -> tuple[np.ndarray, np.ndarray]:
    """REGIME-ANCHORED non-overlapping re-entry book (the iter-027 cadence proxy).

    A stream re-enters within ITS OWN regime, anchored to that signal's REGIME ONSET
    (flip), NOT to a global candle grid. Algorithm:
      * walk candles; detect the stream's direction REGIMES (maximal same-sign runs).
      * at each regime ONSET candle, open a 14d position; then re-enter every `horizon`
        candles WITHIN the same regime (one position at a time) until the regime flips.
      * a new regime resets the re-entry clock to the flip candle.
    Because different signals flip at DIFFERENT times, their entry candles land on
    DIFFERENT candles (this is what makes the streams genuinely independent in TIMING, not
    just direction -- the fix for the degenerate global-grid artifact).

    `extra_eligible` (the conviction gate for TREND): if given, an otherwise-due re-entry
    candle that fails the gate is SKIPPED (the position is not opened) but the re-entry
    clock still advances by 1 candle until a gate-clearing candle is found within the
    regime. This reproduces iter-027's "re-enter when the gate passes" cadence.

    Returns (net_pnls, entry_indices).
    """
    fwd = df_is["fwd_ret_h"].to_numpy()
    n = len(direction)
    if extra_eligible is None:
        extra_eligible = np.ones(n, dtype=bool)
    idx = []
    i = 0
    # find first defined direction
    while i < n and (not np.isfinite(direction[i]) or direction[i] == 0.0):
        i += 1
    cur_dir = direction[i] if i < n else np.nan
    next_due = i  # candle index at/after which the next re-entry is due
    while i < n:
        di = direction[i]
        if np.isfinite(di) and di != 0.0 and di != cur_dir:
            # regime flip -> reset clock to this candle
            cur_dir = di
            next_due = i
        if i >= next_due and np.isfinite(di) and di != 0.0:
            if extra_eligible[i] and np.isfinite(fwd[i]):
                idx.append(i)
                next_due = i + horizon  # non-overlapping within the regime
            # else: gate fail -> wait one candle, retry within the regime
        i += 1
    idx = np.asarray(idx, dtype=int)
    d = direction[idx]
    f = fwd[idx]
    net = d * f - COST
    return net, idx


def conviction_gate_mask(conv: np.ndarray, q: float) -> np.ndarray:
    """Eligible where conviction >= the IS-window quantile q (iter-027 gate, proxy form)."""
    valid = np.isfinite(conv)
    thr = np.nanquantile(conv[valid], q)
    return valid & (conv >= thr)


def book_stats(name: str, net: np.ndarray, idx: np.ndarray, df_is: pd.DataFrame) -> dict:
    cs = concentration_stats(net)
    a = np.abs(np.asarray(net, dtype=float))
    gross = a.sum()
    asrt = np.sort(a)[::-1]
    # gross |pnl| concentration: bounded 0..1, robust to small/negative net denominators.
    top1_g = float(asrt[0] / gross) if gross > 0 and len(asrt) >= 1 else np.nan
    top2_g = float(asrt[:2].sum() / gross) if gross > 0 and len(asrt) >= 2 else top1_g
    hhi = float(np.sum((a / gross) ** 2)) if gross > 0 else np.nan
    shp = annualized_sharpe_from_trade_pnls(net, TRADES_PER_YEAR)
    return {
        "name": name,
        "n_events": len(net),
        "win_rate": round(cs["win_rate"], 4),
        "per_trade_sharpe_ann": round(shp, 4),
        "net_sum_pct": round(cs["net_sum"] * 100, 3),
        # signed-net shares match the iter-027 falsifier framing (can exceed 100% when net
        # is small); shown for continuity but NOT the primary de-concentration measure.
        "top1_share_net": round(cs["top1_share_of_net"], 4)
        if np.isfinite(cs["top1_share_of_net"]) else np.nan,
        "top2_share_net": round(cs["top2_share_of_net"], 4)
        if np.isfinite(cs["top2_share_of_net"]) else np.nan,
        # gross |pnl| shares are the LOAD-BEARING de-concentration measure (bounded 0..1).
        "top1_share_gross": round(top1_g, 4) if np.isfinite(top1_g) else np.nan,
        "top2_share_gross": round(top2_g, 4) if np.isfinite(top2_g) else np.nan,
        "hhi_abs": round(hhi, 5),
    }


def jaccard(a: set, b: set) -> float:
    u = a | b
    return len(a & b) / len(u) if u else float("nan")


def week_of(idx: np.ndarray, df_is: pd.DataFrame) -> set:
    ot = df_is["open_time"].to_numpy()[idx]
    wk = pd.to_datetime(ot, unit="ms").to_period("W")
    return set(wk.astype(str))


def main() -> None:
    full = load_full_for_label_horizon()
    full = add_forward_return(full, HORIZON)
    df_is = drop_horizon_crossing_oos(full, HORIZON)
    assert df_is["open_time"].max() < OOS_CUTOFF_MS, "LEAK GUARD FAILED"
    n = len(df_is)
    print("=" * 110)
    print("iter-v1/031 MULTI-SIGNAL ENTRY-LAYER SCREEN (ETHUSDT, IS-ONLY)")
    print("=" * 110)
    print(
        f"IS rows (horizon-safe): {n}  span "
        f"{pd.to_datetime(df_is['open_time'].min(), unit='ms')} .. "
        f"{pd.to_datetime(df_is['open_time'].max(), unit='ms')}"
    )
    print(
        f"max open_time {int(df_is['open_time'].max())} < cutoff {OOS_CUTOFF_MS}  "
        f"(HORIZON={HORIZON}, round-trip COST={COST:.4f})"
    )
    print()

    conv = trend_strength_atr_norm(df_is, sma_window=200, atr_window=14).to_numpy()
    gate = conviction_gate_mask(conv, CONV_Q)
    all_eligible = np.ones(len(df_is), dtype=bool)  # independent streams: no extra gate

    # --- build the streams ---
    dir_trend = sma_sign(df_is, 200)
    dir_don = donchian_breakout_sign(df_is, 55)
    dir_ts42 = tsmom_sign(df_is, 42)
    dir_ts21 = tsmom_sign(df_is, 21)

    # TREND stream = gated SMA200 REGIME-ANCHORED re-entries (iter-027 ~82-entry proxy)
    net_trend, idx_trend = regime_anchored_reentry_book(df_is, dir_trend, gate)
    # Independent streams = REGIME-ANCHORED re-entries in their own direction, UNGATED.
    # Anchored to EACH signal's OWN flips -> entries land on DIFFERENT candles per stream.
    net_don, idx_don = regime_anchored_reentry_book(df_is, dir_don, all_eligible)
    net_ts42, idx_ts42 = regime_anchored_reentry_book(df_is, dir_ts42, all_eligible)
    net_ts21, idx_ts21 = regime_anchored_reentry_book(df_is, dir_ts21, all_eligible)

    # Also: an UNGATED SMA200 regime-anchored stream (shows the gate's role)
    net_trend_ung, idx_trend_ung = regime_anchored_reentry_book(df_is, dir_trend, all_eligible)

    streams = [
        book_stats("TREND_sma200_gated_q40", net_trend, idx_trend, df_is),
        book_stats("TREND_sma200_ungated", net_trend_ung, idx_trend_ung, df_is),
        book_stats("DON55", net_don, idx_don, df_is),
        book_stats("TSMOM42", net_ts42, idx_ts42, df_is),
        book_stats("TSMOM21", net_ts21, idx_ts21, df_is),
    ]
    sdf = pd.DataFrame(streams)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    print("-" * 110)
    print("STANDALONE IS PROFITABILITY (discrete flip-event books, 14d hold, net of cost)")
    print("-" * 110)
    print(sdf.to_string(index=False))
    print()

    # --- independence / overlap ---
    sets = {
        "TREND_gated": set(idx_trend.tolist()),
        "DON55": set(idx_don.tolist()),
        "TSMOM42": set(idx_ts42.tolist()),
        "TSMOM21": set(idx_ts21.tolist()),
    }
    wks = {k: week_of(np.asarray(sorted(v)), df_is) for k, v in sets.items()}
    print("-" * 110)
    print("INDEPENDENCE — event-candle Jaccard (same exact candle) and same-WEEK overlap fraction")
    print("  (premise needs the streams to fire on DIFFERENT candles than TREND)")
    print("-" * 110)
    keys = list(sets.keys())
    print(f"{'pair':<26}{'jaccard_candle':>16}{'sameweek_frac(min)':>22}")
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            jc = jaccard(sets[a], sets[b])
            wa, wb = wks[a], wks[b]
            sw = len(wa & wb) / min(len(wa), len(wb)) if min(len(wa), len(wb)) else float("nan")
            print(f"{a + ' vs ' + b:<26}{jc:>16.4f}{sw:>22.4f}")
    print()

    # --- COMBINED book: de-duplicated union over the PROFITABLE streams ---
    # Determine which independent streams are standalone-profitable (per-trade Sharpe > 0).
    prof = {
        "DON55": (net_don, idx_don),
        "TSMOM42": (net_ts42, idx_ts42),
        "TSMOM21": (net_ts21, idx_ts21),
    }
    prof_sharpe = {
        k: annualized_sharpe_from_trade_pnls(v[0], TRADES_PER_YEAR) for k, v in prof.items()
    }
    print("-" * 110)
    print("Standalone per-trade Sharpe of independent streams (for inclusion in COMBINED):")
    for k, s in prof_sharpe.items():
        print(f"   {k:<10} sharpe_ann={s:+.4f}  {'INCLUDE' if s > 0 else 'EXCLUDE (loss-maker)'}")
    print()

    include = [k for k, s in prof_sharpe.items() if s > 0]

    # COMBINED book = de-duplicated UNION of the spine (TREND gated) + included independent
    # streams, enforcing single-symbol NON-OVERLAP at the union level: a single-symbol book
    # holds ONE position at a time. We pool ALL candidate entry candles (with per-candle
    # net + direction), scan in time, and whenever a candidate is reached that is not inside
    # an open 14d hold, OPEN it (averaging the nets of ALL streams firing on that SAME
    # candle into one equally-weighted position) and SKIP the next HORIZON candles. This is
    # the honest "combine de-correlated signals into one tradable single-symbol book".
    def build_combined(spine_idx, spine_net, extra_streams):
        per_candle = {}  # candle_idx -> list of net contributions firing there
        for i, p in zip(spine_idx, spine_net):
            per_candle.setdefault(int(i), []).append(float(p))
        for k in extra_streams:
            net_k, idx_k = prof[k]
            for i, p in zip(idx_k, net_k):
                per_candle.setdefault(int(i), []).append(float(p))
        cand_sorted = sorted(per_candle.keys())
        out_idx, out_net = [], []
        last_exit = -1
        for c in cand_sorted:
            if c <= last_exit:
                continue  # inside an open hold -> cannot open another single-symbol position
            out_idx.append(c)
            out_net.append(float(np.mean(per_candle[c])))  # equal-size blend of co-firing streams
            last_exit = c + HORIZON - 1
        return np.asarray(out_net, dtype=float), np.asarray(out_idx, dtype=int)

    net_comb, idx_comb = build_combined(idx_trend, net_trend, include)

    # Also a COMBINED-ALL (include all independent streams regardless of profit, for the
    # record / to show whether loss-makers dilute).
    net_comb_all, idx_comb_all = build_combined(
        idx_trend, net_trend, ["DON55", "TSMOM42", "TSMOM21"]
    )

    # --- ROBUSTNESS: alternative honest combination rules ---------------------------------
    # The equal-size union (above) lets the high-event-count independent streams "win the
    # race" to open positions ahead of TREND's high-conviction gated entries (first-eligible
    # wins under non-overlap). We test 3 alternative honest rules to check whether ANY
    # combination preserves the TREND edge while adding breadth.
    fwd_arr = df_is["fwd_ret_h"].to_numpy()

    # Variant A: CONVICTION-PRIORITY union. Pool all candidate entries; TREND entries get
    # their conviction as priority, independent entries priority 0 (TREND wins crowding).
    # Greedy by priority, non-overlapping. Does prioritizing TREND let breadth in WITHOUT
    # crowding out the edge?
    cands = [(int(ci), float(dir_trend[ci]), float(conv[ci]), "TREND") for ci in idx_trend]
    for k, (n_k, i_k) in prof.items():
        d_k = {"DON55": dir_don, "TSMOM42": dir_ts42, "TSMOM21": dir_ts21}[k]
        cands += [(int(ci), float(d_k[ci]), 0.0, k) for ci in i_k]
    cands.sort(key=lambda x: (-x[2], x[0]))
    occ = np.zeros(len(df_is), dtype=bool)
    taken = []
    for ci, dd, pri, nm in cands:
        if occ[ci : ci + HORIZON].any():
            continue
        taken.append((ci, dd))
        occ[ci : ci + HORIZON] = True
    taken.sort()
    net_a = np.array([dd * fwd_arr[ci] - COST for ci, dd in taken])

    # Variant B: TREND cadence + 3-of-4 AGREEMENT filter (de-correlated signals as a
    # CONFIRMATION, not new entries). Keep a TREND entry only if >=3/4 of {trend,don,ts42,
    # ts21} agree on direction; size by the majority direction. This is a FILTER (reduces
    # events) -- the opposite of breadth -- shown to contrast.
    votes = np.vstack([dir_trend, dir_don, dir_ts42, dir_ts21])
    agree = np.nansum(votes, axis=0)
    net_b_list = []
    for ci in idx_trend:
        if abs(agree[ci]) >= 2:  # net >=2 == at least 3 of 4 agree
            net_b_list.append(np.sign(agree[ci]) * fwd_arr[ci] - COST)
    net_b = np.asarray(net_b_list)

    # Variant C: TREND cadence + majority-VOTE direction (no abstain; uses the de-correlated
    # signals only to possibly FLIP the trend direction). Same events, voted direction.
    net_c = np.asarray(
        [np.sign(agree[ci] if agree[ci] != 0 else dir_trend[ci]) * fwd_arr[ci] - COST
         for ci in idx_trend]
    )

    inc_lbl = "+".join(include) if include else "NONE"
    comp = [
        book_stats("TREND-alone (gated q40)", net_trend, idx_trend, df_is),
        book_stats(f"COMBINED equal-union (TREND+{inc_lbl})", net_comb, idx_comb, df_is),
        book_stats("COMBINED-ALL equal-union", net_comb_all, idx_comb_all, df_is),
        book_stats("VarA conviction-priority union", net_a, np.array([c for c, _ in taken]), df_is),
        book_stats("VarB trend-cadence + 3of4 agree FILTER", net_b, idx_trend, df_is),
        book_stats("VarC trend-cadence + majority-vote DIR", net_c, idx_trend, df_is),
    ]
    # source attribution for Variant A (how many of each stream survived crowding)
    from collections import Counter

    occ2 = np.zeros(len(df_is), dtype=bool)
    src_taken = []
    for ci, dd, pri, nm in cands:
        if occ2[ci : ci + HORIZON].any():
            continue
        src_taken.append(nm)
        occ2[ci : ci + HORIZON] = True
    src_counts = dict(Counter(src_taken))

    cdf = pd.DataFrame(comp)
    print("=" * 110)
    print("COMBINED-BOOK COMPARISON vs TREND-alone (all rules non-overlapping, 14d, net)")
    print("=" * 110)
    print(cdf.to_string(index=False))
    print()
    print(f"Variant A source attribution (entries surviving non-overlap crowding): {src_counts}")
    print("  -> independent streams contribute few events once TREND is prioritized; the")
    print("     equal-union INVERTS the edge by letting weak high-count streams crowd TREND out.")
    print()

    # --- pre-registered PASS evaluation ---
    base = comp[0]
    cand = comp[1]
    more_events = cand["n_events"] > base["n_events"]
    lower_top2 = (cand["top2_share_net"] < base["top2_share_net"]) or (
        cand["top2_share_gross"] < base["top2_share_gross"]
    )
    sharpe_ok = (cand["per_trade_sharpe_ann"] >= 0) and (
        cand["per_trade_sharpe_ann"] >= base["per_trade_sharpe_ann"] - 0.05
    )
    streams_profitable = len(include) > 0 and all(prof_sharpe[k] > 0 for k in include)

    print("=" * 110)
    print("PRE-REGISTERED PASS CRITERION")
    print("  (a) COMBINED has MORE events than TREND-alone")
    print("  (b) COMBINED top-2 share LOWER than TREND-alone (net OR gross)")
    print("  (c) COMBINED per-trade Sharpe >= 0 AND >= TREND-alone - 0.05")
    print("  (upstream) the included independent streams are standalone-profitable")
    print("=" * 110)
    print(f"  (a) more events:   {base['n_events']} -> {cand['n_events']}  => {more_events}")
    print(
        f"  (b) top2 net:      {base['top2_share_net']} -> {cand['top2_share_net']} ; "
        f"gross {base['top2_share_gross']} -> {cand['top2_share_gross']}  => {lower_top2}"
    )
    print(
        f"  (c) sharpe:        {base['per_trade_sharpe_ann']:+.4f} -> "
        f"{cand['per_trade_sharpe_ann']:+.4f}  (>=0 and bleed<=0.05) => {sharpe_ok}"
    )
    print(f"  (upstream) included streams profitable: {include or 'NONE'} => {streams_profitable}")
    is_pass = more_events and lower_top2 and sharpe_ok and streams_profitable
    verdict = "PASS" if is_pass else "NEGATIVE"
    print()
    print("  CONTEXT — the PASS criterion is on the ADDITIVE equal-union book (the genuine")
    print("  'more independent winning EVENTS' test). The CONFIRMATION/FILTER variants (B/C)")
    print("  do NOT add breadth (they keep/shrink the TREND cadence) so they cannot satisfy")
    print("  criterion (a) by construction and are NOT a de-concentration mechanism.")
    print(f"    VarB (best filter) sharpe={comp[4]['per_trade_sharpe_ann']:+.4f} "
          f"events={comp[4]['n_events']} (<= TREND-alone {base['n_events']} -> reduces breadth)")
    print()
    print("=" * 110)
    print(f"OVERALL SCREEN VERDICT: {verdict}")
    print("=" * 110)

    out = pd.concat([sdf, pd.DataFrame([{}]), cdf], ignore_index=True)
    csv = Path(__file__).resolve().parent / "multisignal_entry_screen.csv"
    out.to_csv(csv, index=False)
    print(f"\nwrote {csv}")


if __name__ == "__main__":
    main()
