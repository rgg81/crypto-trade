"""All-in cost accounting for the LIVE v2 testnet portfolio — the REALISTIC bottom line.

These are REAL exchange trades (Binance testnet matching engine), so Binance's own ledger is the
source of truth and we reconcile to it. Every cash flow the exchange records is summed and checked
against the actual wallet balance to the cent — if it ties out, nothing is missing by construction:

    seed(TRANSFER) + REALIZED_PNL + FUNDING_FEE + COMMISSION [+ other] == wallet balance
    wallet balance + unrealized mark PnL       == margin balance (true equity)
    margin balance − seed                      == ALL-IN P/L (price + funding + fees)

BUT testnet FUNDING is an ARTIFACT — testnet slams the ±3.75%/8h cap flat (e.g. SIREN settles at
−3.75% every 8h vs a real +0.0001–0.0003), so the raw ledger funding is meaningless for a
real-money forecast. Per user directive, the HEADLINE P/L is stated on a **PRODUCTION-funding
basis**: every real funding settlement is repriced to what it WOULD have cost at production rates.
Funding is linear in the rate and the position notional is identical either way, so per
(symbol, funding_time):  prod_income = testnet_income × (prod_rate / testnet_rate)  — the notional
cancels. prod_rate/testnet_rate come from the public historical fundingRate endpoints (prod =
fapi.binance.com, testnet = testnet.binancefuture.com). The actual testnet funding is retained ONLY
for the reconcile-to-wallet integrity check (the wallet physically contains testnet funding).

So the headline `all-in P/L` = equity − seed, with the testnet funding artifact swapped out for the
production-repriced figure. Slippage is baked into realized/unrealized (it lands in the fill price);
commission rate IS real. The one thing still NOT production-representative is fill quality (thin
testnet liquidity) — see `portfolio_fill_quality.py`. Complements the fast
`portfolio_v2_healthcheck.py` (whose one-line `uPnL` is MARK-ONLY).

Read-only. Run:
  cd .worktrees/quant-portfolio && export PATH="$HOME/.local/bin:$PATH" \
    && set -a; source ~/.binance_testnet_v2_env; set +a \
    && export BINANCE_AUTH_BASE_URL=https://testnet.binancefuture.com \
    && uv run python scripts/portfolio_v2_pnl.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

sys.path.insert(0, "src")

# income types that fund the account (not a trading result) — netted into the "seed"
DEPOSIT_TYPES = {"TRANSFER", "WELCOME_BONUS", "COIN_SWAP_DEPOSIT"}
# the three trading-cost / trading-result buckets we attribute explicitly
TRADE_TYPES = ("REALIZED_PNL", "FUNDING_FEE", "COMMISSION")

PROD_BASE = "https://fapi.binance.com"
TEST_BASE = "https://testnet.binancefuture.com"
EIGHT_H_MS = 8 * 3600 * 1000


def _get_json(url: str):
    try:
        return json.load(urllib.request.urlopen(url, timeout=20))
    except Exception:
        return None


def _fetch_funding_rates(sym: str, start_ms: int, end_ms: int, base: str):
    """Historical funding rates for one symbol on one venue → [(fundingTime_ms, rate), ...].

    Returns None if the FETCH ITSELF failed (network/timeout/418), as distinct from [] meaning
    the venue answered and genuinely has no history for this symbol. Callers must not conflate
    the two: on 2026-07-28 a transient fetch failure on BCHUSDT was reported as "not on prod →
    assumed 0" for a symbol that is plainly TRADING on production, silently dropping ~103
    settlements from the repricing.
    """
    url = (
        f"{base}/fapi/v1/fundingRate?symbol={sym}&startTime={start_ms}&endTime={end_ms}&limit=1000"
    )
    data = _get_json(url)
    if data is None:  # one cheap retry — these failures are overwhelmingly transient
        data = _get_json(url)
    if data is None:
        return None
    rows = []
    if isinstance(data, list):
        for r in data:
            try:
                rows.append((int(r["fundingTime"]), float(r["fundingRate"])))
            except (KeyError, TypeError, ValueError):
                continue
    return rows


def _nearest_rate(rows, t_ms: int, tol_ms: int = 2 * 3600 * 1000):
    """Rate whose fundingTime is closest to t_ms, within tol (funding is on 8h marks; income time
    may be ±ms/seconds off, and prod/testnet timestamps differ by ~1ms). None if none within tol."""
    best, best_d = None, None
    for ft, r in rows:
        d = abs(ft - t_ms)
        if best_d is None or d < best_d:
            best, best_d = r, d
    return best if (best_d is not None and best_d <= tol_ms) else None


def _prod_repriced_funding(funding_events: list):
    """Reprice every REAL testnet funding settlement to its PRODUCTION-rate equivalent.

    funding_events: [(symbol, time_ms, testnet_income), ...] (one row per FUNDING_FEE settlement).
    Per event:  prod_income = testnet_income × (prod_rate / testnet_rate)  — notional cancels.
    Returns dict with prod_total, testnet_matched (raw testnet $ that WAS repriced),
    n_matched, n_unmatched, missing_syms (symbols the venue confirms have no prod funding history —
    e.g. testnet-only listings; their events are assumed 0 prod funding since we couldn't hold them
    on production), failed_syms (symbols whose prod fetch ERRORED — an unknown, NOT a delisting;
    reported separately so a network blip is never read as "not on prod"), and per-symbol
    (testnet, prod) contributions for the top-payer display.
    """
    out = {
        "prod_total": 0.0,
        "testnet_matched": 0.0,
        "n_matched": 0,
        "n_unmatched": 0,
        "missing_syms": [],
        "failed_syms": [],
        "by_sym": {},
    }
    if not funding_events:
        return out
    by_sym: dict = {}
    for sym, t, inc in funding_events:
        by_sym.setdefault(sym, []).append((t, inc))
    lo = min(t for _, t, _ in funding_events) - EIGHT_H_MS
    hi = max(t for _, t, _ in funding_events) + EIGHT_H_MS
    for sym, evs in by_sym.items():
        prod_rows = _fetch_funding_rates(sym, lo, hi, PROD_BASE)
        if prod_rows is None:  # fetch ERRORED — unknown, not evidence of a delisting
            out["failed_syms"].append(sym)
            out["n_unmatched"] += len(evs)
            continue
        if not prod_rows:  # venue answered: symbol genuinely has no prod funding history
            out["missing_syms"].append(sym)
            out["n_unmatched"] += len(evs)
            continue
        test_rows = _fetch_funding_rates(sym, lo, hi, TEST_BASE)
        s_tn = s_prod = 0.0
        for t, inc in evs:
            pr = _nearest_rate(prod_rows, t)
            tr = _nearest_rate(test_rows, t)
            if pr is None or tr is None or tr == 0.0:
                out["n_unmatched"] += 1
                continue
            pinc = inc * (pr / tr)
            out["prod_total"] += pinc
            out["testnet_matched"] += inc
            out["n_matched"] += 1
            s_tn += inc
            s_prod += pinc
        if s_tn or s_prod:
            out["by_sym"][sym] = (s_tn, s_prod)
    return out


def _prod_funding_runrate(positions: list):
    """FORWARD real-rate funding run-rate on the CURRENT book (a snapshot, distinct from the
    repriced HISTORICAL accumulation above). Queries production premiumIndex ONCE and sums
    -signed_notional*rate per 8h interval. + = we receive. Assumes 8h funding (3/day)."""
    raw = _get_json(f"{PROD_BASE}/fapi/v1/premiumIndex")
    if not isinstance(raw, list):
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
        per_day += -notion * rate[sym] * 3
    return per_day, cov, miss


def _fetch_all_income(a) -> list:
    """Full income history, de-duped by composite key (paginates by advancing startTime)."""
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
                inc.get("tranId"),
                inc.get("incomeType"),
                inc.get("symbol"),
                inc.get("time"),
                inc.get("income"),
            )
            rows[key] = inc
        newest = max(int(r.get("time", 0)) for r in page)
        if len(page) < 1000:
            break
        start = newest + 1  # +1ms; de-dupe absorbs any same-ms boundary overlap
    return list(rows.values())


def main() -> None:
    from crypto_trade.config import load_settings
    from crypto_trade.live.auth_client import AuthenticatedBinanceClient

    s = load_settings()
    if not s.binance_api_key:
        print("[v2 PnL] no creds — skipped")
        return
    base = os.environ.get("BINANCE_AUTH_BASE_URL", TEST_BASE)
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
    funding_events: list = []
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
            funding_events.append((inc.get("symbol", "?"), t, amt))

    seed = sum(v for k, v in buckets.items() if k in DEPOSIT_TYPES)  # net deposits = capital base
    realized = buckets.get("REALIZED_PNL", 0.0)
    funding_tn = buckets.get("FUNDING_FEE", 0.0)  # ACTUAL testnet funding (artifact; for reconcile)
    commission = buckets.get("COMMISSION", 0.0)
    known = DEPOSIT_TYPES | set(TRADE_TYPES)
    other = {k: v for k, v in buckets.items() if k not in known}
    other_sum = sum(other.values())

    # --- reprice funding to PRODUCTION rates (the headline basis) ---
    rp = _prod_repriced_funding(funding_events)
    funding_prod = rp["prod_total"]

    # reconcile uses the ACTUAL testnet ledger (that's what physically sits in the wallet)
    settled_tn = realized + funding_tn + commission + other_sum
    opening = wallet - seed - settled_tn
    all_in_tn = equity - seed  # raw, testnet-funding basis (shown small, as an aside)

    # headline: swap the testnet funding artifact for the production-repriced figure
    all_in = all_in_tn - funding_tn + funding_prod
    equity_prodadj = seed + all_in
    ret_pct = (all_in / seed * 100) if seed else float("nan")

    days = (t_hi - t_lo) / 86_400_000 if (t_lo and t_hi and t_hi > t_lo) else 0.0

    print(
        f"[v2 PnL — PROD-funding basis] MODE={mode}  equity(prod-adj)=${equity_prodadj:,.2f}  "
        f"all-in P/L={all_in:+,.2f} ({ret_pct:+.2f}% vs ${seed:,.0f} seed)"
    )
    print(
        f"  breakdown: realized {realized:+.2f} | funding(PROD) {funding_prod:+.2f} | "
        f"commission {commission:+.2f} | unreal {unreal:+.2f}"
        + (f" | other {other_sum:+.2f}" if other else "")
        + f" | dust {opening:+.2f}"
    )

    # funding repricing detail
    miss = rp["missing_syms"]
    missnote = f"; {len(miss)} sym(s) not on prod → assumed 0: {','.join(miss[:4])}" if miss else ""
    failed = rp["failed_syms"]
    failnote = (
        f"; ⚠ {len(failed)} sym(s) prod-funding FETCH FAILED (transient, NOT a delisting; "
        f"their funding is excluded → rerun): {','.join(failed[:4])}"
        if failed
        else ""
    )
    unm = f", {rp['n_unmatched']} unmatched" if rp["n_unmatched"] else ""
    annp = (funding_prod / days * 365) if days > 0 else 0.0
    print(
        f"  FUNDING repriced testnet→prod: ledger {funding_tn:+.2f} → prod-equivalent "
        f"{funding_prod:+.2f} over {days:.1f}d (~{annp:+,.0f}/yr) "
        f"[{rp['n_matched']} settlements{unm}{missnote}{failnote}]"
    )
    # biggest movers (by absolute testnet contribution — where the artifact bit hardest)
    tops = sorted(rp["by_sym"].items(), key=lambda kv: abs(kv[1][0]), reverse=True)[:3]
    if tops:
        tstr = ", ".join(f"{k}: testnet {tn:+.2f}→prod {pr:+.2f}" for k, (tn, pr) in tops)
        print(f"    top artifact swings: {tstr}")

    # forward run-rate on the current book (snapshot, complements the historical accumulation)
    overlay = _prod_funding_runrate(positions)
    if overlay:
        pday, cov, missf = overlay
        mn = f", {missf} not on prod" if missf else ""
        print(
            f"    prod forward run-rate (current book, 8h): ~${pday:+.2f}/day "
            f"(~${pday * 365:+,.0f}/yr) [{cov} syms{mn}]"
        )
    if other:
        print(f"  OTHER income types (surfaced, not dropped): {other}")

    # integrity: the actual testnet ledger must reconstruct the wallet to the cent
    tol = max(2.0, 0.001 * seed)
    verdict = "OK (opening dust)" if abs(opening) < tol else "GAP — cost bucket may be missing"
    print(
        f"  reconcile (actual testnet ledger, ties to wallet): seed ${seed:,.0f} + "
        f"settled(testnet) ${settled_tn:+,.2f} = ${seed + settled_tn:,.2f} vs wallet "
        f"${wallet:,.2f} → opening ${opening:+.2f} [{verdict}]"
    )
    print(
        f"    (raw testnet-funding all-in would read {all_in_tn:+.2f}; the "
        f"{funding_prod - funding_tn:+.2f} swing is the removed testnet funding artifact)"
    )


if __name__ == "__main__":
    main()
