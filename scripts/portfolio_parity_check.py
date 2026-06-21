"""Parity / drift check — is the LIVE exchange book what the v3 STRATEGY says it should hold?

The health check confirms the book *looks* sane (gross, concentration, margin). This confirms it is
*correct*: it recomputes the strategy's intended target weights (the SAME code + close-proxy forming
the engine uses) and compares, per name, against the LIVE Binance positions. It flags real execution
divergences — a leg that should be held but ISN'T (failed entry), one held that the strategy EXITED
(failed close), a WRONG-SIDE position, or a grossly MIS-SIZED one — while tolerating benign price
drift (a fixed coin position's $-weight moves with markPrice) and sub-min-notional dust.

Prints one line `PARITY: OK | DRIFT` + any `DRIFT:` detail lines. Exit 0 always.

Caveat — 8h boundary transient: right after a candle close (00/08/16 UTC) the engine spends ~5-7 min
refreshing before it rebalances; a check landing in that window can show transient drift. The output
notes minutes-since-boundary so the monitor can treat a near-boundary DRIFT as likely-transient and
re-check next tick.
"""

from __future__ import annotations

import sys
import time

sys.path.insert(0, "src")

EQUITY = 10_000.0          # notional base — must match run_portfolio_testnet.py PortfolioConfig
MIN_NOTIONAL = 5.0        # Binance min order; names below this in $ are untradeable dust
DUST_W = MIN_NOTIONAL / EQUITY                 # ~0.0005 weight; |w| below this == effectively flat
ABS_TOL = 0.015                                # absolute weight tolerance (price drift headroom)
REL_TOL = 0.50                                 # relative tol for mis-size (catches half-fills)


def _mins_since_boundary() -> int:
    now = time.gmtime()
    secs = (now.tm_hour % 8) * 3600 + now.tm_min * 60 + now.tm_sec
    return secs // 60


def main() -> None:
    from crypto_trade.config import load_settings
    from crypto_trade.live.auth_client import AuthenticatedBinanceClient
    from crypto_trade.portfolio import strategy

    s = load_settings()
    if not s.binance_api_key:
        print("PARITY: SKIP (no creds)")
        return
    a = AuthenticatedBinanceClient(
        api_key=s.binance_api_key, api_secret=s.binance_api_secret, base_url=s.auth_base_url)

    # LIVE book -> per-coin weight (positionAmt * markPrice / equity)
    live_w: dict[str, float] = {}
    for p in a.get_positions():
        amt = float(p.get("positionAmt", 0) or 0)
        if amt == 0:
            continue
        mark = float(p.get("markPrice", 0) or 0)
        live_w[p["symbol"]] = amt * mark / EQUITY

    # STRATEGY target -> the SAME computation the engine does (close-proxy forming, current data)
    coins = strategy.load_universe()
    forming = strategy.forming_from_close(coins)
    tgt = strategy.next_target_weights(strategy.append_forming(coins, forming))
    meta = tgt.pop("_meta")
    tgt_w = {k: float(v) for k, v in tgt.items()}

    flags: list[str] = []
    for sym in sorted(set(tgt_w) | set(live_w)):
        tw, lw = tgt_w.get(sym, 0.0), live_w.get(sym, 0.0)
        if abs(tw) < DUST_W and abs(lw) < DUST_W:
            continue                                            # both ~flat (incl. TNSR-style dust)
        if abs(tw) >= DUST_W and abs(lw) < DUST_W:
            flags.append(f"MISSING {sym}: target {tw:+.4f} but live ~0 (failed entry?)")
        elif abs(lw) >= DUST_W and abs(tw) < DUST_W:
            flags.append(f"EXTRA   {sym}: live {lw:+.4f} but strategy exited (failed close?)")
        elif (tw > 0) != (lw > 0):
            flags.append(f"WRONGSIDE {sym}: target {tw:+.4f} vs live {lw:+.4f}")
        elif abs(lw - tw) > max(ABS_TOL, REL_TOL * abs(tw)):
            flags.append(f"MISSIZED {sym}: target {tw:+.4f} vs live {lw:+.4f}")

    mins = _mins_since_boundary()
    status = "DRIFT" if flags else "OK"
    near = " (NEAR 8h boundary, likely transient)" if (flags and mins < 12) else ""
    print(f"PARITY: {status}  (as_of={meta['as_of']}, target_n={len(tgt_w)}, live_n={len(live_w)}, "
          f"{mins}min since 8h boundary){near}")
    for f in flags:
        print(f"  DRIFT: {f}")
    print(f"  checked {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")


if __name__ == "__main__":
    main()
