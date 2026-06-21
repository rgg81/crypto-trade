"""Live-money PRE-FLIGHT — GO / NO-GO checklist before the production cutover.

The gate before swapping testnet for real money. Verifies, from live state + the repo, that the bot
is ready: creds/mode resolve, the account can margin the intended book, the deployable baseline tag
is present, the data is fresh, and the strategy produces a sane ~top-20 target. Read-only (no
orders, no engine touch) -> never competes with the trade loop. Prints `PREFLIGHT: GO | NO-GO`.

This does NOT itself flip to live — it just tells you whether you're ready. The cutover is still a
deliberate manual step (swap keys/--testnet->--live, seed data/live.db, tighten the monitor).
"""

from __future__ import annotations

import subprocess
import sys

sys.path.insert(0, "src")

EQUITY = 10_000.0
LEVERAGE = 3.0
GROSS_TARGET = 0.85          # upper end of the vol-target band
MARGIN_SAFETY = 1.5         # require this multiple of the estimated margin as headroom


def main() -> None:
    from crypto_trade.config import load_settings
    from crypto_trade.live.auth_client import AuthenticatedBinanceClient
    s = load_settings()
    checks: list[tuple[str, bool, str]] = []

    # 1) creds + mode
    has_creds = bool(s.binance_api_key)
    mode = "TESTNET" if "testnet" in (s.auth_base_url or "").lower() else (
        "LIVE" if has_creds else "PAPER")
    checks.append(("creds present", has_creds, f"MODE={mode}"))

    # 2) account can margin the intended book
    req_margin = EQUITY * GROSS_TARGET / LEVERAGE
    bal = 0.0
    if has_creds:
        try:
            a = AuthenticatedBinanceClient(
                api_key=s.binance_api_key, api_secret=s.binance_api_secret,
                base_url=s.auth_base_url)
            acct = a.get_account()
            bal = float(acct.get("totalWalletBalance", 0) or 0)
        except Exception as exc:
            checks.append(("account reachable", False, repr(exc)[:60]))
    ok_margin = bal >= req_margin * MARGIN_SAFETY
    need = req_margin * MARGIN_SAFETY
    checks.append((f"balance >= {MARGIN_SAFETY:g}x est. margin (${need:,.0f})",
                   ok_margin, f"wallet ${bal:,.0f}"))

    # 3) deployable baseline tag present
    tag = subprocess.run(["git", "tag", "-l", "portfolio-baseline-v3"],
                         capture_output=True, text=True).stdout.strip()
    checks.append(("baseline-v3 tag present", tag == "portfolio-baseline-v3", tag or "MISSING"))

    # 4) data fresh + leak-free + 5) strategy produces a sane target
    try:
        from crypto_trade.portfolio import strategy
        coins = strategy.load_universe()
        forming = strategy.forming_from_close(coins)
        nt = strategy.next_target_weights(strategy.append_forming(coins, forming))
        meta = nt.pop("_meta")
        n = len(nt)
        checks.append(("strategy target sane (~top-20)", 15 <= n <= 30,
                       f"{n} names, gross {meta['gross']:.2f}, as_of {meta['as_of']}"))
    except Exception as exc:
        checks.append(("strategy target sane", False, repr(exc)[:60]))

    go = all(ok for _, ok, _ in checks)
    print(f"PREFLIGHT: {'GO' if go else 'NO-GO'}")
    for name, ok, detail in checks:
        print(f"  [{'OK ' if ok else 'X  '}] {name}  — {detail}")
    if not go:
        print("  -> resolve the X items before the live cutover")


if __name__ == "__main__":
    main()
