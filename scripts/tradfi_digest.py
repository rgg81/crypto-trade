"""TradFi paper-engine DIGEST — the periodic BOOK + DUAL-P&L report (NOT an alert source).

READ-ONLY. Reports, for the deployed iter-016 BEAR-GATED TSMOM paper desk (68 Binance single-stock
TradFi perps ex-PAYP, DAILY rebalance):

  * the held BOOK — per-name weight + $ exposure (long vs short), top legs, gross Σ|w| / net Σw;
  * BOTH equity tracks — PARITY (Yahoo-TR backtest book of record) + LIVE (perp − funding − cost),
    with since-launch % and since-last-rebalance %;
  * basis_gap (bps) = equity_live − equity_parity — the perp-vs-underlying tracking residual;
  * funding_cum ($ + a rough annualized carry note) — the net long-premium CARRY (a drag, ≈−0.7%/yr
    at book level per Phase-2b), NOT a dividend bridge;
  * funding AUDIT split — gross long-leg / short-leg / NET drag (annualized), direction −w·f (f>0 ⇒
    long pays / short earns), from the PRODUCTION public fapi funding (never testnet). Confirms the
    ~net-zero-but-not-quite value is the net-long tilt + asymmetric retail-long-premium funding;
  * the bear-gate regime state g = 1{EW-universe trailing-252d return < 0} (TSMOM sleeve gated OFF).

Per the HANDS-OFF mandate these are TEST RESULTS — report them, never act. `REPORT_DUE: yes` fires
on a NEW rebalance (the settled bar advanced since the last report) OR the first report of a new UTC
day; `--mark-pushed` records it fired (single `tradfi_digest_last_pushed` state key: {candle, day}).

Run:  uv run python scripts/tradfi_digest.py [--mark-pushed]
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT / "src"), str(_ROOT / "analysis" / "portfolio" / "tradfi")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import core_tradfi as ct  # noqa: E402
import iter_006_crashbrake as i6  # noqa: E402  — the EW-252d bear-state gate (regime read)
import live_weights_tradfi as lw  # noqa: E402  — for the settled universe resolution
import sizing_min_notional as sizing  # noqa: E402  — REUSE quantize_weight + _price for leg counts
import universe_tradfi as ut  # noqa: E402
from live_tradfi import (  # noqa: E402
    _DEFAULT_FILT,
    LIVE_EXCLUDED,
    TradfiPaperConfig,
    TradfiPaperEngine,
)

from crypto_trade.live.state_store import StateStore  # noqa: E402

DB = _ROOT / "data" / "tradfi_paper.db"
EQ = _ROOT / "data" / "tradfi_equity.csv"
DATA_DIR = str(_ROOT / "data")
DAY_MS = 86_400_000
PUSH_KEY = "tradfi_digest_last_pushed"


def _bear_gate_state(data_dir: str, today_ms: int) -> tuple[int | None, float]:
    """(g, trailing_252d_ret) at the freshest SETTLED bar — the iter-016 regime gate (best-effort).

    g = 1{EW-universe 252d return < 0} (TSMOM directional sleeve OFF). Reuses the SAME past-only
    `i6.bear_state` the champion gates on. Returns (None, nan) if the panel cannot be built.
    """
    try:
        coins = ct.load_tradfi(lw._universe(data_dir), data_dir)
        coins = {s: d[d.index < today_ms] for s, d in coins.items() if len(d[d.index < today_ms])}
        if not coins:
            return None, float("nan")
        pn = ct.panels(coins)
        close = pn["close"]
        g = int(i6.bear_state(close, i6.GATE_LOOKBACK).iloc[-1] > 0.5)
        mkt = i6.market_index(close)
        lb = i6.GATE_LOOKBACK
        r = float(mkt.iloc[-1] / mkt.iloc[-1 - lb] - 1.0) if len(mkt) > lb else float("nan")
        return g, r
    except Exception:  # noqa: BLE001 — the regime read is best-effort; never block the digest
        return None, float("nan")


def _quant_leg_counts(held: dict[str, float], equity: float) -> tuple[int, int, int, float]:
    """(n_quantized, n_dropped, n_no_price, gross_dropped) for the CONTINUOUS held book at ``eq``.

    Read-only feasibility snapshot: quantize each ideal leg to the uniform TradFi-perp filter (all
    69 share ``_DEFAULT_FILT``) at its latest local perp price (``sizing._price`` — no network) to
    show how many legs the LIVE track places vs drops at the sub-$5 min-notional floor. This is
    display-only; it never touches the ideal held book (parity stays continuous)."""
    n_quant = n_drop = n_noprice = 0
    gross_dropped = 0.0
    for sym, w in held.items():
        price = sizing._price(sym)
        if not price:
            n_noprice += 1
            continue
        _rw, ok = sizing.quantize_weight(w, price, _DEFAULT_FILT, equity)
        if ok:
            n_quant += 1
        else:
            n_drop += 1
            gross_dropped += abs(w)
    return n_quant, n_drop, n_noprice, gross_dropped


def _funding_split(data_dir: str) -> dict | None:
    """Gross long-leg / short-leg / net funding drag (annualized %/yr) — best-effort AUDIT line.

    Reuses ``reconcile_basis_tradfi.funding_drag`` (per-leg P&L = −w·f, so f>0 ⇒ long pays / short
    earns — the verified direction). Loads the deployed weight panel + perp fwd-returns + daily
    funding over the live perp window; returns None on any failure (never blocks the digest).
    Funding data is the PRODUCTION public fapi (``data/funding_rates/`` via
    ``portfolio.funding.refresh_funding`` @ https://fapi.binance.com), NOT testnet."""
    try:
        import perp_map_tradfi as pm
        import reconcile_basis_tradfi as rc

        _net, dw = lw.deployed_book(data_dir)
        dw = dw.drop(columns=list(LIVE_EXCLUDED), errors="ignore")
        pmap = {k: v for k, v in pm.perp_symbol_map(live=False).items() if k in dw.columns}
        idx = dw.index
        perp_rf = rc.fwd_ret(rc.load_perp_opens(pmap, idx))
        fd = rc.daily_funding(pmap, idx, funding_dir=_ROOT / "data" / "funding_rates")
        return rc.funding_drag(dw, perp_rf, fd)
    except Exception:  # noqa: BLE001 — audit line is best-effort; never block the digest
        return None


def main() -> int:
    mark = "--mark-pushed" in sys.argv
    if not DB.exists():
        print("DIGEST: n/a (no DB yet — engine never launched)")
        return 0

    st = StateStore(DB)
    held = json.loads(st.get_state("tradfi_held_w") or "{}")
    held = {k: float(v) for k, v in held.items() if k not in LIVE_EXCLUDED}
    last_candle = st.get_state("tradfi_last_candle")
    launch_candle = st.get_state("tradfi_launch_candle")
    equity0 = TradfiPaperConfig().equity_usd
    eq_parity = float(st.get_state("tradfi_equity_parity") or equity0)
    eq_live = float(st.get_state("tradfi_equity_live") or equity0)
    fund_cum = float(st.get_state("tradfi_funding_cum") or 0.0)

    as_of = pd.Timestamp(int(last_candle), unit="ms").date() if last_candle else "n/a"
    basis_gap = eq_live - eq_parity
    bps = basis_gap / equity0 * 1e4

    def _pct(x: float) -> str:
        return "n/a (1st bar)" if x != x else f"{x:+.2f}%"  # x != x ⇒ NaN

    # since-launch (both tracks) + since-last-rebalance (prev equity CSV row)
    ret_p = (eq_parity / equity0 - 1) * 100
    ret_l = (eq_live / equity0 - 1) * 100
    prev_p = prev_l = float("nan")
    eq_df = pd.read_csv(EQ) if EQ.exists() else pd.DataFrame()
    if len(eq_df) >= 2:
        prev_p = (eq_parity / float(eq_df["equity_parity"].iloc[-2]) - 1) * 100
        prev_l = (eq_live / float(eq_df["equity_live"].iloc[-2]) - 1) * 100

    # funding carry — cumulative $ + a rough annualized note over the launch→now span
    days = (
        (int(last_candle) - int(launch_candle)) / DAY_MS
        if last_candle and launch_candle
        else float("nan")
    )
    fund_pct = fund_cum / equity0 * 100
    fund_ann = fund_pct * 365.0 / days if days and days > 0 else float("nan")

    # funding AUDIT split — gross long-leg / short-leg / net drag (dir −w·f, prod-fapi source)
    fs = _funding_split(DATA_DIR)
    fund_split_str = ""
    if fs:
        fund_split_str = (
            f"  funding split (dir −w·f, f>0 ⇒ long pays/short earns; src prod fapi): "
            f"long-leg {fs['long_leg_ann_%']:+.2f}%/yr, "
            f"short-leg {fs['short_leg_ann_%']:+.2f}%/yr, NET {fs['net_ann_%']:+.2f}%/yr\n"
        )

    # regime gate
    today_ms = TradfiPaperEngine._today_ms()
    g, r252 = _bear_gate_state(DATA_DIR, today_ms)
    if g is None:
        regime = "regime n/a"
    else:
        regime = (
            f"g={g} ({'BEAR → TSMOM sleeve GATED OFF' if g else 'non-bear → TSMOM tilt ON'}, "
            f"EW-252d ret {r252 * 100:+.1f}%)"
        )

    gross = sum(abs(w) for w in held.values())
    net = sum(held.values())
    n_long = sum(1 for w in held.values() if w > 0)
    n_short = sum(1 for w in held.values() if w < 0)

    n_quant, n_drop, n_noprice, gross_drop = _quant_leg_counts(held, equity0)
    print(
        f"TRADFI BOOK + DUAL P&L  (as_of {as_of}, iter-016 bear-gated TSMOM, PAPER)\n"
        f"  PARITY = signal (ideal book, must match backtest — the correctness check)\n"
        f"  PARITY  ${eq_parity:,.0f}   since-launch {ret_p:+.2f}%   since-last {_pct(prev_p)}\n"
        f"  LIVE = executed (quantized fills + funding + basis on real perps, "
        f"same realistic cost)\n"
        f"  LIVE    ${eq_live:,.0f}   since-launch {ret_l:+.2f}%   since-last {_pct(prev_l)}   "
        f"(quantized perp − funding − cost)\n"
        f"  basis_gap ${basis_gap:,.0f} ({bps:+.0f}bps) = real execution gap "
        f"(perp basis + funding + quantization; slippage is in BOTH tracks, not here)\n"
        f"  funding_cum ${fund_cum:,.2f} ({fund_pct:+.3f}% ≈ {fund_ann:+.2f}%/yr carry, "
        f"on quant legs)\n"
        f"{fund_split_str}"
        f"  exec @ ${equity0:,.0f}: {n_quant} legs quantized / {n_drop} dropped "
        f"(sub-$5 min-notional, {gross_drop:.4f} gross)"
        + (f" / {n_noprice} no-price" if n_noprice else "")
        + "\n"
        f"  regime {regime}\n"
        f"  book: {len(held)} names (ex-PAYP)   {n_long} long / {n_short} short\n"
        f"  gross Σ|w| {gross:.3f} (${gross * eq_parity:,.0f})   "
        f"net Σw {net:+.3f} (${net * eq_parity:,.0f})"
    )
    if held:
        print("  top legs by |w|:")
        for s, w in sorted(held.items(), key=lambda kv: -abs(kv[1]))[:12]:
            side = "LONG " if w > 0 else "SHORT"
            sector = ut.SECTOR_MAP.get(s, "?")
            print(f"    {side} {s:10} {sector:9} {w:+.4f}   ${w * eq_parity:>+10,.0f}")

    # push trigger: settled bar advanced since last report OR first report of a new UTC day
    today = dt.datetime.now(dt.UTC).date().isoformat()
    last_pushed = json.loads(st.get_state(PUSH_KEY) or "{}")
    due = (last_candle is not None and str(last_candle) != last_pushed.get("candle")) or (
        last_pushed.get("day") != today
    )
    if mark:
        st.set_state(PUSH_KEY, json.dumps({"candle": str(last_candle), "day": today}))
        print(f"  (reported: candle {as_of}, day {today})")
    else:
        print(f"REPORT_DUE: {'yes' if due else 'no'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
