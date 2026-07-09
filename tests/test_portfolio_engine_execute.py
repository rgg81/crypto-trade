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
        paper_untradeable=paper_untradeable,
        testnet=testnet,
        dry_run=False,
        leverage=1.0,
        min_notional_buffer=1.20,
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


# ---- v20: transient -4131 is strike-based (retry), not paper-on-first-failure ----

_PCT_PRICE = '400 Bad Request: {"code":-4131,"msg":"Filter failure: PERCENT_PRICE"}'
_XYZ_PLAN = {
    "legs": [{"symbol": "XYZUSDT", "side": "BUY", "price": "1.0", "delta_notional_usd": 100.0}]
}


def _engine_thin(thin_sym: str) -> PortfolioEngine:
    """Engine whose ORDER for thin_sym raises -4131 (a transient thin-book rejection)."""
    eng = _engine(paper_untradeable=True, testnet=True)

    def place(symbol, side, qty):
        if symbol == thin_sym:
            raise Exception(_PCT_PRICE)  # noqa: TRY002
        eng.auth.orders.append((symbol, side, qty))

    eng.auth.place_market_order = place
    return eng


def test_transient_4131_retries_not_papered_on_first_failure():
    eng = _engine_thin("XYZUSDT")
    strikes: dict = {}
    res = eng.execute(_XYZ_PLAN, paper_syms=set(), strikes=strikes)

    assert res["papered"] == 0
    assert res["retrying"] == 1
    assert res["errors"] == 0
    assert "XYZUSDT" not in res["new_paper"]  # NOT frozen on a one-off
    assert strikes["XYZUSDT"] == 1


def test_transient_4131_papers_only_after_n_consecutive_strikes():
    eng = _engine_thin("XYZUSDT")
    strikes: dict = {}
    # strikes 1 and 2 → retry, not papered
    for _ in range(2):
        res = eng.execute(_XYZ_PLAN, paper_syms=set(), strikes=strikes)
        assert res["papered"] == 0 and res["retrying"] == 1
    # 3rd consecutive strike → now papered (persistent, not transient)
    res = eng.execute(_XYZ_PLAN, paper_syms=set(), strikes=strikes)
    assert res["papered"] == 1
    assert "XYZUSDT" in res["new_paper"]
    assert "XYZUSDT" not in strikes  # cleared once papered


def test_transient_strike_resets_on_fill():
    eng = _engine(paper_untradeable=True, testnet=True)
    n = {"calls": 0}

    def place(symbol, side, qty):
        n["calls"] += 1
        if n["calls"] == 1:
            raise Exception(_PCT_PRICE)  # noqa: TRY002 — fail once, then fill
        eng.auth.orders.append((symbol, side, qty))

    eng.auth.place_market_order = place
    strikes: dict = {}
    r1 = eng.execute(_XYZ_PLAN, paper_syms=set(), strikes=strikes)
    assert r1["retrying"] == 1 and strikes.get("XYZUSDT") == 1
    r2 = eng.execute(_XYZ_PLAN, paper_syms=set(), strikes=strikes)  # now fills
    assert r2["placed"] == 1
    assert "XYZUSDT" not in strikes  # a fill clears the streak


# ---- v20: startup reconcile un-sticks papered symbols that hold a real position ----


def test_reconcile_unsticks_papered_symbol_with_live_position():
    eng = _engine(paper_untradeable=True, testnet=True)
    saved: dict = {}
    # LINK is papered AND holds a real position (wrongly frozen); TLM papered, no real position.
    eng._load_paper = lambda: ({"LINKUSDT", "TLMUSDT"}, {"LINKUSDT": -0.02, "TLMUSDT": 0.024})
    eng._save_paper = lambda syms, held: saved.update({"syms": set(syms), "held": dict(held)})
    eng.auth.get_positions = lambda: [
        {"symbol": "LINKUSDT", "positionAmt": "5.0"},  # live position → un-stick
        {"symbol": "BTCUSDT", "positionAmt": "0.1"},
        {"symbol": "TLMUSDT", "positionAmt": "0"},  # no live position → stays papered
    ]
    eng._paper_strikes = {"LINKUSDT": 2}

    eng._reconcile_paper_vs_positions()

    assert saved["syms"] == {"TLMUSDT"}  # LINK dropped, TLM retained
    assert "LINKUSDT" not in saved["held"]
    assert "TLMUSDT" in saved["held"]
    assert "LINKUSDT" not in eng._paper_strikes  # strike streak cleared for the un-stuck symbol


def test_reconcile_noop_when_no_overlap():
    eng = _engine(paper_untradeable=True, testnet=True)
    saved: dict = {}
    eng._load_paper = lambda: ({"TLMUSDT"}, {"TLMUSDT": 0.024})
    eng._save_paper = lambda syms, held: saved.update({"syms": set(syms), "held": dict(held)})
    eng.auth.get_positions = lambda: [{"symbol": "BTCUSDT", "positionAmt": "0.1"}]

    eng._reconcile_paper_vs_positions()

    assert saved == {}  # nothing un-stuck → no save


# ---- min-notional buffer: skip boundary dust legs so they can't be rejected -4164 ----


def test_min_notional_buffer_skips_boundary_dust_leg():
    """A leg sized just ABOVE the $5 floor but WITHIN the 1.20 buffer ($5-$6) is SKIPPED, not sent —
    so a price drift down before the staggered execution can't get it rejected -4164 (the 2026-07-09
    SKYAI $5.31 case). A leg above the buffer ($6+) still places normally."""
    eng = _engine(paper_untradeable=True, testnet=True)
    eng._min_notional = lambda s: 5.0  # $5 floor → buffered skip threshold = $6.00
    eng._round_qty = lambda s, q: (
        q
    )  # identity: qty == notional/price, so we control notional directly
    plan = {
        "legs": [
            {"symbol": "SKYAIUSDT", "side": "SELL", "price": "1.0", "delta_notional_usd": 5.31},
            {"symbol": "BTCUSDT", "side": "BUY", "price": "1.0", "delta_notional_usd": 7.00},
        ]
    }
    res = eng.execute(plan, paper_syms=set())

    assert res["skipped"] == 1  # SKYAI dust leg ($5.31, within buffer) skipped
    assert res["placed"] == 1  # BTC ($7, above buffer) placed
    assert res["errors"] == 0
    assert all(o[0] != "SKYAIUSDT" for o in eng.auth.orders)  # never sent → no -4164 possible
    assert ("BTCUSDT", "BUY", 7.00) in eng.auth.orders
