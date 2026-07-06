"""Unit tests for PortfolioEngine.execute() paper-fallback at the set_leverage step.

Regression for the 2026-07-06 finding: a prod-listed / testnet-unlisted symbol (e.g. TLMUSDT —
TRADING on production, NOT LISTED on testnet) fails set_leverage with -4141 "Symbol is closed".
That code is swallowed inside _ensure_leverage, so before the fix the order was still attempted and
failed downstream with a -1111 precision cascade (errors=1, missing leg) instead of being papered.
The fix makes _ensure_leverage PROPAGATE untradeability so execute() papers it (testnet) or skips it
as an error leg (production, where papering a real position would fabricate P&L).
"""

from __future__ import annotations

from types import SimpleNamespace

from crypto_trade.portfolio.engine import PortfolioEngine

_CLOSED = 'RuntimeError 400 Bad Request: {"code":-4141,"msg":"Symbol is closed."}'


class _FakeAuth:
    """Minimal auth double: TLMUSDT is closed on this venue; everything else trades."""

    def __init__(self):
        self.orders: list = []
        self.lev_calls: list = []

    def set_leverage(self, symbol, lev):
        self.lev_calls.append((symbol, lev))
        if symbol == "TLMUSDT":
            raise Exception(_CLOSED)  # noqa: TRY002 — mimic the httpx error string shape

    def place_market_order(self, symbol, side, qty):
        self.orders.append((symbol, side, qty))


def _engine(*, paper_untradeable: bool, testnet: bool) -> PortfolioEngine:
    """A PortfolioEngine with __init__ bypassed — only the attrs execute() touches are wired up."""
    eng = PortfolioEngine.__new__(PortfolioEngine)
    eng.cfg = SimpleNamespace(
        paper_untradeable=paper_untradeable, testnet=testnet, dry_run=False, leverage=1.0
    )
    eng.auth = _FakeAuth()
    eng._lev_set = set()
    eng._round_qty = lambda s, q: 100.0  # non-dust so the min-notional guard doesn't skip the leg
    eng._min_notional = lambda s: 0.0
    return eng


_PLAN = {
    "legs": [
        {"symbol": "TLMUSDT", "side": "BUY", "price": "1.0", "delta_notional_usd": 100.0},
        {"symbol": "BTCUSDT", "side": "SELL", "price": "60000.0", "delta_notional_usd": 100.0},
    ]
}


def test_untradeable_symbol_is_papered_on_testnet():
    eng = _engine(paper_untradeable=True, testnet=True)  # _paper_enabled() -> True
    res = eng.execute(_PLAN, paper_syms=set())

    assert res["papered"] == 1
    assert res["errors"] == 0
    assert "TLMUSDT" in res["new_paper"]
    assert res["placed"] == 1  # BTC still placed
    # the closed symbol's ORDER is never attempted (no -1111 cascade)
    assert all(o[0] != "TLMUSDT" for o in eng.auth.orders)
    assert ("BTCUSDT", "SELL", 100.0) in eng.auth.orders


def test_untradeable_symbol_is_skipped_as_error_on_production():
    # paper-fallback OFF (production): the symbol can't be papered (would fabricate real P&L),
    # so it's an error leg — but STILL no order is attempted, and the rest of the book trades.
    eng = _engine(paper_untradeable=False, testnet=False)  # _paper_enabled() -> False
    res = eng.execute(_PLAN, paper_syms=set())

    assert res["papered"] == 0
    assert res["errors"] == 1
    assert res["new_paper"] == set()
    assert res["placed"] == 1  # BTC still placed
    assert all(o[0] != "TLMUSDT" for o in eng.auth.orders)


def test_benign_leverage_error_still_places_the_order():
    # A non-untradeable set_leverage hiccup must NOT paper/skip — the order still goes through.
    eng = _engine(paper_untradeable=True, testnet=True)

    def flaky_set_leverage(symbol, lev):
        eng.auth.lev_calls.append((symbol, lev))
        raise Exception('400 Bad Request: {"code":-4046,"msg":"No need to change leverage."}')  # noqa: TRY002

    eng.auth.set_leverage = flaky_set_leverage
    plan = {
        "legs": [
            {"symbol": "ETHUSDT", "side": "BUY", "price": "3000.0", "delta_notional_usd": 100.0}
        ]
    }
    res = eng.execute(plan, paper_syms=set())

    assert res["placed"] == 1
    assert res["papered"] == 0 and res["errors"] == 0
    assert ("ETHUSDT", "BUY", 100.0) in eng.auth.orders
