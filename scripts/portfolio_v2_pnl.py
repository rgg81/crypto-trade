"""All-in cost accounting for the LIVE v2 testnet portfolio — the REALISTIC bottom line.

These are REAL exchange trades (Binance testnet matching engine), so Binance's own ledger is the
source of truth and we reconcile to it. Every cash flow the exchange records is summed and checked
against the actual wallet balance to the cent — if it ties out, nothing is missing by construction:

    seed(TRANSFER) + REALIZED_PNL + FUNDING_FEE + COMMISSION [+ other] == wallet balance
    wallet balance + unrealized mark PnL       == margin balance (true equity)
    margin balance − seed                      == ALL-IN P/L (price + funding + fees)

So the headline number is `totalMarginBalance − seed`: it already contains realized PnL, funding
paid/earned, trading commissions, AND open-position mark-to-market. Slippage is baked into
realized/unrealized (it lands in the fill price). The one thing NOT production-representative on
testnet is fill quality / funding RATES (thin/artificial liquidity) — see
`portfolio_fill_quality.py`; commission rate is real. Complements the fast
`portfolio_v2_healthcheck.py` (whose one-line `uPnL` is MARK-ONLY).

Read-only. Run:
  cd .worktrees/quant-portfolio && export PATH="$HOME/.local/bin:$PATH" \
    && set -a; source ~/.binance_testnet_v2_env; set +a \
    && export BINANCE_AUTH_BASE_URL=https://testnet.binancefuture.com \
    && uv run python scripts/portfolio_v2_pnl.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, "src")

# income types that fund the account (not a trading result) — netted into the "seed"
DEPOSIT_TYPES = {"TRANSFER", "WELCOME_BONUS", "COIN_SWAP_DEPOSIT"}
# the three trading-cost / trading-result buckets we attribute explicitly
TRADE_TYPES = ("REALIZED_PNL", "FUNDING_FEE", "COMMISSION")


def _prod_funding_runrate(positions: list):
    """Real-rate funding run-rate on the CURRENT book. Testnet funding settles at artificial rates
    (caps slammed flat — e.g. SIREN -3.75%/8h vs +0.019% real), so to see what funding would
    ACTUALLY cost we query PRODUCTION premiumIndex (public, no auth — same host the engine fetches
    klines from) ONCE and sum -signed_notional*rate per funding interval. Sign matches convention:
    long + positive rate => we pay; short + positive rate => we receive. Assumes 8h funding (3/day).
    """
    import json
    import urllib.request

    try:
        raw = json.load(
            urllib.request.urlopen("https://fapi.binance.com/fapi/v1/premiumIndex", timeout=15)
        )
    except Exception:
        return None
    rate = {d["symbol"]: float(d.get("lastFundingRate", 0) or 0) for d in raw}
    per_day = 0.0
    cov = miss = 0
    for p in positions:
        amt = float(p.get("positionAmt", 0) or 0)
        if amt == 0:
            continue
        sym = p["symbol"]
        if sym not in rate:
            miss += 1
            continue
        cov += 1
        notion = amt * float(p.get("markPrice", 0) or 0)
        per_day += -notion * rate[sym] * 3  # 3 funding intervals/day (8h); + = we receive
    return per_day, cov, miss


def _fetch_all_income(a) -> list:
    """Full income history, de-duped by tranId (paginates by advancing startTime)."""
    rows: dict = {}
    start = 1_609_459_200_000  # 2021-01-01, well before any deploy
    for _ in range(50):  # 50 * 1000 = 50k-row backstop
        page = a.get_income(start_time=start, limit=1000)
        if not page:
            break
        for inc in page:
            # NB: a single fill emits REALIZED_PNL *and* COMMISSION under the SAME tranId, so the
            # key MUST include incomeType (+symbol/time/income) or realized rows get deduped away.
            key = (
                inc.get("tranId"), inc.get("incomeType"), inc.get("symbol"),
                inc.get("time"), inc.get("income"),
            )
            rows[key] = inc
        newest = max(int(r.get("time", 0)) for r in page)
        if len(page) < 1000:
            break
        start = newest + 1  # +1ms; tranId de-dupe absorbs any same-ms boundary overlap
    return list(rows.values())


def main() -> None:
    from crypto_trade.config import load_settings
    from crypto_trade.live.auth_client import AuthenticatedBinanceClient

    s = load_settings()
    if not s.binance_api_key:
        print("[v2 PnL] no creds — skipped")
        return
    base = os.environ.get("BINANCE_AUTH_BASE_URL", "https://testnet.binancefuture.com")
    mode = "TESTNET" if "testnet" in base else ("LIVE" if s.binance_api_key else "PAPER")
    a = AuthenticatedBinanceClient(
        api_key=s.binance_api_key, api_secret=s.binance_api_secret, base_url=base
    )

    acct = a.get_account()
    wallet = float(acct.get("totalWalletBalance", 0) or 0)
    unreal = float(acct.get("totalUnrealizedProfit", 0) or 0)
    equity = float(acct.get("totalMarginBalance", 0) or 0)  # == wallet + unreal (true equity)
    positions = [p for p in a.get_positions() if float(p.get("positionAmt", 0) or 0) != 0]

    income = _fetch_all_income(a)
    buckets: dict = {}
    fund_by_sym: dict = {}
    t_lo = t_hi = None
    for inc in income:
        typ = inc.get("incomeType")
        amt = float(inc.get("income", 0) or 0)
        buckets[typ] = buckets.get(typ, 0.0) + amt
        t = int(inc.get("time", 0) or 0)
        if t and typ not in DEPOSIT_TYPES:  # span over TRADING activity, not the initial deposit
            t_lo = t if t_lo is None else min(t_lo, t)
            t_hi = t if t_hi is None else max(t_hi, t)
        if typ == "FUNDING_FEE":
            sym = inc.get("symbol", "?")
            fund_by_sym[sym] = fund_by_sym.get(sym, 0.0) + amt

    seed = sum(v for k, v in buckets.items() if k in DEPOSIT_TYPES)  # net deposits = capital base
    realized = buckets.get("REALIZED_PNL", 0.0)
    funding = buckets.get("FUNDING_FEE", 0.0)
    commission = buckets.get("COMMISSION", 0.0)
    # anything the exchange recorded that we didn't bucket above (deposits + 3 trade types)
    known = DEPOSIT_TYPES | set(TRADE_TYPES)
    other = {k: v for k, v in buckets.items() if k not in known}
    other_sum = sum(other.values())

    settled = realized + funding + commission + other_sum  # all banked cash flows (ex-deposits)
    trading_all_in = settled + unreal  # strategy P/L with EVERY cost in (fees, funding, mark)
    all_in = equity - seed  # account P/L vs capital put in
    ret_pct = (all_in / seed * 100) if seed else float("nan")
    # COMPLETENESS CHECK: the exchange ledger (seed + settled) should reconstruct the wallet to the
    # cent. Any gap is a fixed pre-existing OPENING balance — unless it GROWS, which would mean a
    # cost bucket we're not capturing. Small+stable => every cost is accounted for.
    opening = wallet - seed - settled
    days = (t_hi - t_lo) / 86_400_000 if (t_lo and t_hi and t_hi > t_lo) else 0.0

    print(f"[v2 PnL all-in] MODE={mode}  equity=${equity:,.2f}  "
          f"all-in P/L={all_in:+,.2f} ({ret_pct:+.2f}% vs ${seed:,.0f} seed)")
    print(f"  trading all-in {trading_all_in:+.2f}: realized {realized:+.2f} | "
          f"funding {funding:+.2f} | commission {commission:+.2f} | unreal {unreal:+.2f}"
          + (f" | other {other_sum:+.2f}" if other else ""))
    if days > 0:
        ann = funding / days * 365
        top = sorted(fund_by_sym.items(), key=lambda kv: kv[1])[:3]  # most-negative first
        topstr = ", ".join(f"{k} {v:+.2f}" for k, v in top)
        note = " [testnet rates NON-representative]" if mode == "TESTNET" else ""
        print(f"  funding {funding:+.2f} / {days:.1f}d (~{ann:+,.0f}/yr){note} "
              f"— top payers: {topstr}")
    # what funding would ACTUALLY run at, on real production rates (the meaningful forward number)
    overlay = _prod_funding_runrate(positions)
    if overlay:
        pday, cov, miss = overlay
        missnote = f", {miss} not on prod" if miss else ""
        print(f"  prod-rate funding overlay (REAL rates, live book, 8h assumption): "
              f"~${pday:+.2f}/day (~${pday * 365:+,.0f}/yr) [{cov} syms{missnote}]")
    if other:
        print(f"  OTHER income types (surfaced, not dropped): {other}")
    tol = max(2.0, 0.001 * seed)  # opening dust tolerance; larger/growing gap => missing bucket
    verdict = "OK (opening dust)" if abs(opening) < tol else "GAP — cost bucket may be missing"
    print(f"  reconcile: seed ${seed:,.0f} + settled ${settled:+,.2f} = ${seed + settled:,.2f} "
          f"vs wallet ${wallet:,.2f} -> opening ${opening:+.2f} [{verdict}]")


if __name__ == "__main__":
    main()
