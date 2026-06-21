"""Fill-quality / slippage tracking — actual fills vs the reference price, MODE-AWARE.

CRITICAL distinction (per the user) — what "fill quality" means depends on the run mode:
  - PAPER / dry-run : fills are SIMULATED at the reference price -> zero slippage by construction.
    There is nothing real to measure; the engine assumes it fills at the close-proxy.
  - TESTNET (test Binance) : REAL orders on the testnet matching engine, but its liquidity is thin /
    artificial -> fills happen, but the slippage is NOT representative of production. Informational
    only. The effective FEE RATE (commission/notional) IS real (the fee tier is real).
  - LIVE : real money + real liquidity -> the ONLY mode where slippage is the true number to trust.

So this prints the MODE prominently and labels the slippage accordingly. The robust signal in every
mode is the effective fee rate (should be ~5 bps taker, matching the backtest cost assumption); the
slippage-vs-reference is reported but flagged non-representative on testnet.

Reference = the close of the last COMPLETE candle (the close-proxy the engine sized the leg at).
Looks at fills in the last ~9h (since the last rebalance). Prints `FILLQUAL: OK|INFO|n/a`.
"""

from __future__ import annotations

import glob
import os
import sys
import time

sys.path.insert(0, "src")

WINDOW_MS = 9 * 60 * 60 * 1000
EXPECT_FEE_BPS = 5.0           # taker 0.05%/side — the backtest cost assumption


def _mode(settings) -> str:
    url = (settings.auth_base_url or "").lower()
    if not settings.binance_api_key:
        return "PAPER"
    return "TESTNET" if "testnet" in url else "LIVE"


def _ref_close(symbol: str) -> float | None:
    path = f"data/{symbol}/8h.csv"
    if not os.path.exists(path):
        return None
    try:
        import pandas as pd
        return float(pd.read_csv(path, usecols=["close"])["close"].iloc[-1])
    except Exception:
        return None


def main() -> None:
    from crypto_trade.config import load_settings
    from crypto_trade.live.auth_client import AuthenticatedBinanceClient
    s = load_settings()
    mode = _mode(s)
    if mode == "PAPER":
        print("FILLQUAL: n/a  (MODE=PAPER — fills simulated at the reference; no real slippage)")
        return

    a = AuthenticatedBinanceClient(
        api_key=s.binance_api_key, api_secret=s.binance_api_secret, base_url=s.auth_base_url)
    start = int(time.time() * 1000) - WINDOW_MS
    held = [p["symbol"] for p in a.get_positions() if float(p.get("positionAmt", 0) or 0) != 0]
    if not glob.glob("data/*USDT/8h.csv"):
        print(f"FILLQUAL: n/a  (MODE={mode} — no kline data for reference)")
        return

    n = 0
    notional = commission = slip_w = 0.0      # slip_w = notional-weighted adverse slippage bps
    for sym in held:
        ref = _ref_close(sym)
        try:
            fills = a.get_user_trades(sym, start_time=start)
        except Exception:
            continue
        for f in fills:
            px = float(f.get("price", 0) or 0)
            qty = float(f.get("qty", 0) or 0)
            if px <= 0 or qty <= 0:
                continue
            notl = px * qty
            n += 1
            notional += notl
            if f.get("commissionAsset") == "USDT":
                commission += float(f.get("commission", 0) or 0)
            if ref and ref > 0:
                sign = 1.0 if f.get("side") == "BUY" else -1.0   # +adverse = filled worse than ref
                slip_w += sign * (px / ref - 1.0) * 1e4 * notl

    if n == 0:
        print(f"FILLQUAL: OK  (MODE={mode} — no fills in last {WINDOW_MS // 3_600_000}h)")
        return
    fee_bps = commission / notional * 1e4 if notional else 0.0
    slip_bps = slip_w / notional if notional else 0.0
    if mode == "TESTNET":
        note = " [TESTNET liquidity — slippage NON-REPRESENTATIVE; real slippage only on --live]"
        status = "INFO"
    else:
        note = ""
        status = "OK"
    print(f"FILLQUAL: {status}  (MODE={mode}, {n} fills, notional ${notional:,.0f}, "
          f"fee {fee_bps:.1f}bps vs {EXPECT_FEE_BPS:.0f}bps assumed, "
          f"adverse slippage {slip_bps:+.1f}bps){note}")
    print(f"  checked {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")


if __name__ == "__main__":
    main()
