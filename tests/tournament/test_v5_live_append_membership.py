"""Incrementally-computed membership must match the rule the tournament selected on.

seasoned_membership applies persistence only once a week has persistence_window_weeks of PRIOR
reconstitutions inside the grid it is handed. An incremental append that passes only the new weeks
therefore gets a laxer rule than every week before it -- silently, because the function is doing
exactly what it documents.

That shipped once. The four weeks from 2026-08-03 came out with three to five wrong symbols each,
admitting newly liquid names and dropping established ones: the RIVER failure the seasoned rule
exists to prevent, reintroduced by the shape of the call.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament.v5.universe import seasoned_membership

REPO = Path(__file__).resolve().parents[2]
WEEKS = 40
SYMBOLS = [f"S{i:02d}USDT" for i in range(50)]


@pytest.fixture(scope="module")
def market() -> tuple[pd.DataFrame, pd.DataFrame]:
    """A universe where a late entrant becomes liquid only in the final weeks."""

    generator = np.random.default_rng(4)
    start = pd.Timestamp("2025-01-06", tz="UTC")
    index = pd.date_range(start, periods=WEEKS * 7 * 3, freq="8h", tz="UTC")
    rows = []
    for position, symbol in enumerate(SYMBOLS):
        # Established names carry volume throughout; the last five only ramp up at the end.
        base = 5e7 * (1.0 + position % 7)
        volume = np.full(len(index), base)
        if position >= len(SYMBOLS) - 5:
            # Dormant, then abruptly the most liquid names in the book -- the RIVER shape.
            volume[: int(len(index) * 0.6)] = 1.0e3
            volume[int(len(index) * 0.6) :] = 5e9
        rows.append(
            pd.DataFrame(
                {
                    "open_time": index,
                    "symbol": symbol,
                    "close": 100.0 + generator.normal(0, 1, len(index)).cumsum() * 0.01,
                    "quote_volume": volume,
                }
            )
        )
    bars = pd.concat(rows, ignore_index=True)
    metadata = pd.DataFrame(
        {
            "symbol": SYMBOLS,
            "contract_type": "PERPETUAL",
            "quote_asset": "USDT",
            "margin_asset": "USDT",
            "is_crypto": True,
            "onboard_date": start - pd.Timedelta(days=400),
            "delivery_date": pd.Timestamp("2100-01-01", tz="UTC"),
        }
    )
    return bars, metadata


def _grid(weeks: int) -> pd.DatetimeIndex:
    """A Monday grid; seasoned_membership rejects anything else."""

    first = pd.Timestamp("2025-01-06", tz="UTC") + pd.Timedelta(weeks=17)
    return pd.date_range(first, periods=weeks, freq="7D", tz="UTC")


def test_a_short_grid_and_an_armed_grid_disagree(market):
    """The failure itself: passing only the new weeks changes who is admitted.

    If this ever stops failing, the exemption has changed and the guard below is measuring nothing.
    """

    bars, metadata = market
    full = _grid(20)
    new = full[-3:]

    short = seasoned_membership(bars, metadata, new, size=20, persistence_rank=25)
    armed_grid = pd.date_range(new[0] - pd.Timedelta(weeks=10), new[-1], freq="7D", tz="UTC")
    armed = seasoned_membership(bars, metadata, armed_grid, size=20, persistence_rank=25)
    armed = armed[armed["reconstitution_time"].isin(new)]

    a = short.sort_values(["reconstitution_time", "symbol"]).reset_index(drop=True)
    b = armed.sort_values(["reconstitution_time", "symbol"]).reset_index(drop=True)
    assert not a.equals(b), (
        "a short grid no longer differs from an armed one; the persistence exemption changed "
        "and the incremental append's arming may now be measuring nothing"
    )


def test_arming_the_grid_reproduces_the_full_history_computation(market):
    """The fix: arm backwards, discard the extension, match a computation over all weeks."""

    bars, metadata = market
    full = _grid(20)
    new = full[-3:]

    whole = seasoned_membership(bars, metadata, full, size=20, persistence_rank=25)
    whole = whole[whole["reconstitution_time"].isin(new)]

    armed_grid = pd.date_range(new[0] - pd.Timedelta(weeks=10), new[-1], freq="7D", tz="UTC")
    incremental = seasoned_membership(bars, metadata, armed_grid, size=20, persistence_rank=25)
    incremental = incremental[incremental["reconstitution_time"].isin(new)]

    a = whole.sort_values(["reconstitution_time", "symbol"]).reset_index(drop=True)
    b = incremental.sort_values(["reconstitution_time", "symbol"]).reset_index(drop=True)
    assert a.equals(b), "an armed incremental grid must match computing the whole history"


def _script():  # type: ignore[no-untyped-def]
    """Load the live-append script as a module.

    The two tests above bind ``seasoned_membership``; this binds the caller. A test of the helper
    is not a test of the path -- the defect was never in the rule, it was in how the script invoked
    it, and a guard that cannot see the invocation cannot catch it coming back.
    """

    path = REPO / "scripts" / "top40v5_live_append.py"
    spec = importlib.util.spec_from_file_location("v5_live_append", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["v5_live_append"] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def test_the_script_arms_persistence_for_the_weeks_it_appends(market, capsys):
    """extend_membership must reproduce a whole-history computation over the weeks it adds."""

    bars, metadata = market
    script = _script()
    full = _grid(20)
    prior = seasoned_membership(bars, metadata, full[:-3], size=20, persistence_rank=25)

    # The script calls seasoned_membership with the production defaults, so the reference has to
    # use them too -- pin the fixture's selectivity rather than the call's arguments.
    monkey = {"size": 20, "persistence_rank": 25}
    real = script.seasoned_membership
    script.seasoned_membership = lambda b, m, g: real(b, m, g, **monkey)
    try:
        appended = script.extend_membership(prior, bars, metadata, full[-1] + pd.Timedelta(days=1))
    finally:
        script.seasoned_membership = real
    capsys.readouterr()

    whole = seasoned_membership(bars, metadata, full, **monkey)
    new_weeks = full[-3:]
    got = appended[appended["reconstitution_time"].isin(new_weeks)]
    want = whole[whole["reconstitution_time"].isin(new_weeks)]

    got = got.sort_values(["reconstitution_time", "symbol"]).reset_index(drop=True)
    want = want.sort_values(["reconstitution_time", "symbol"]).reset_index(drop=True)
    assert list(got["symbol"]) == list(want["symbol"]), (
        "the incremental append admitted a different universe than a full rebuild would; "
        "persistence is not being armed before the first new week"
    )


def test_the_script_preserves_the_existing_frame_dtypes(market, capsys):
    """A membership frame read from parquet sets the dtype; freshly-computed rows must match it.

    Same class as the datetime64[us]/[ns] defect that moved net_return ~10% on published rows --
    there the append was cast and the membership frame was not, which is a fix that covers three of
    four writes and reads as complete.
    """

    bars, metadata = market
    script = _script()
    full = _grid(20)
    prior = seasoned_membership(bars, metadata, full[:-3], size=20, persistence_rank=25)
    prior = prior.astype({"liquidity_rank": "int32"})
    prior["reconstitution_time"] = prior["reconstitution_time"].astype("datetime64[us, UTC]")

    real = script.seasoned_membership
    script.seasoned_membership = lambda b, m, g: real(b, m, g, size=20, persistence_rank=25)
    try:
        appended = script.extend_membership(prior, bars, metadata, full[-1] + pd.Timedelta(days=1))
    finally:
        script.seasoned_membership = real
    capsys.readouterr()

    assert appended["liquidity_rank"].dtype == prior["liquidity_rank"].dtype
    assert appended["reconstitution_time"].dtype == prior["reconstitution_time"].dtype


# --- symbol sourcing -------------------------------------------------------------------------
#
# The universe the desks trade must be the universe they were selected on, which means every path
# that can add a symbol has to apply the same admission rule. There are two such paths, and both
# have now failed the same way: the membership recompute above applied a laxer persistence rule,
# and the exchangeInfo fetch below applied a laxer eligibility rule.


def _exchange_info(*symbols: str) -> dict:
    return {
        "symbols": [
            {
                "symbol": s,
                "contractType": "PERPETUAL",
                "quoteAsset": "USDT",
                "marginAsset": "USDT",
                # Binance reports COIN for stablecoin pegs and gold tokens alike. That is the whole
                # trap: a filter built from exchangeInfo's own fields admits all of them.
                "underlyingType": "COIN",
                "onboardDate": 1_700_000_000_000,
                "deliveryDate": 4_133_404_800_000,
            }
            for s in symbols
        ]
    }


def test_live_contracts_applies_the_charter_eligibility_rule(monkeypatch):
    """Stablecoin pegs, gold-backed tokens and non-ASCII names must never enter.

    A peg pair carries enormous quote volume and almost no volatility. In a Top-40 book ranked on
    quote volume and sized at a common ex-ante risk unit, admitting one is not a rounding error --
    it is a very large position in an instrument that cannot move.
    """

    script = _script()
    monkeypatch.setattr(
        script,
        "_get",
        lambda url, **kw: _exchange_info(
            "BTCUSDT", "USDCUSDT", "USTCUSDT", "PAXGUSDT", "XAUTUSDT", "龙虾USDT", "BTCUSDT_240329"
        ),
    )
    assert set(script._live_contracts()) == {"BTCUSDT"}


def test_live_contracts_admits_an_ordinary_new_listing(monkeypatch):
    """The other direction, so the rule cannot be trivially reject-everything.

    Without this the eligibility guard above is satisfied by a filter that admits nothing, which
    would silently restore the closed universe the fetch exists to open.
    """

    script = _script()
    monkeypatch.setattr(
        script, "_get", lambda url, **kw: _exchange_info("BTCUSDT", "DOSUSDT", "GAIBUSDT")
    )
    assert set(script._live_contracts()) == {"BTCUSDT", "DOSUSDT", "GAIBUSDT"}


def test_live_contracts_rejects_non_perpetual_and_non_usdt(monkeypatch):
    """The exchangeInfo-level filters still have to hold on their own."""

    script = _script()
    payload = _exchange_info("AAAUSDT", "BBBUSDT", "CCCUSDT")
    payload["symbols"][0]["contractType"] = "CURRENT_QUARTER"
    payload["symbols"][1]["quoteAsset"] = "BUSD"
    payload["symbols"][2]["marginAsset"] = "BTC"
    monkeypatch.setattr(script, "_get", lambda url, **kw: payload)
    assert script._live_contracts() == {}


def test_metadata_rows_store_the_sentinel_the_way_the_builder_does(monkeypatch):
    """New listings join a frame the evaluator reads; they must be shaped like every other row.

    A perpetual's deliveryDate is a far-future sentinel and the canonical builder stores it as-is --
    514 of the snapshot's 671 rows carry 2100-12-25, and exactly one is NaT. Collapsing the sentinel
    to NaT looked tidier and would have made new listings the only differently-shaped rows in the
    frame: an incremental path applying a different rule from the from-scratch builder, which is
    the shape of both universe defects this file exists for.
    """

    script = _script()
    rows = script._metadata_rows({"DOSUSDT": _exchange_info("DOSUSDT")["symbols"][0]}, ["DOSUSDT"])
    assert list(rows["symbol"]) == ["DOSUSDT"]
    assert bool(rows["is_crypto"].iloc[0]) is True
    assert rows["delivery_date"].iloc[0] == pd.Timestamp(4_133_404_800_000, unit="ms", tz="UTC")
    assert rows["onboard_date"].iloc[0] == pd.Timestamp(1_700_000_000_000, unit="ms", tz="UTC")


def test_metadata_rows_keep_nat_when_binance_omits_delivery_date(monkeypatch):
    """The one case that IS NaT, so the rule above cannot be satisfied by never producing NaT."""

    script = _script()
    info = _exchange_info("DOSUSDT")["symbols"][0]
    del info["deliveryDate"]
    rows = script._metadata_rows({"DOSUSDT": info}, ["DOSUSDT"])
    assert pd.isna(rows["delivery_date"].iloc[0])
    assert str(rows["delivery_date"].dtype).endswith("UTC]"), "must stay tz-aware even when all-NaT"


def test_metadata_rows_survive_being_matched_to_a_tz_aware_frame():
    """The columns must be tz-AWARE even when every value is NaT.

    This is the whole failure, and the test above could not see it. Every perpetual carries a
    sentinel deliveryDate, so delivery_date comes out all-NaT, and pandas types an all-NaT column as
    tz-naive datetime64[ns]. _match_dtypes then tries to astype it to the snapshot's tz-aware dtype
    and pandas refuses naive -> aware outright, with a TypeError.

    Checking the frame's own contents passed happily while the append crashed on every run that saw
    a new listing, and the desks sat 40h stale behind a watchdog that degraded quietly. So assert
    against a frame shaped like the snapshot's, which is the thing it actually has to survive.
    """

    script = _script()
    rows = script._metadata_rows(
        {"DOSUSDT": _exchange_info("DOSUSDT")["symbols"][0]}, ["DOSUSDT"]
    )
    existing = pd.DataFrame(
        {
            "symbol": pd.Series(["BTCUSDT"], dtype="object"),
            "contract_type": pd.Series(["PERPETUAL"], dtype="object"),
            "quote_asset": pd.Series(["USDT"], dtype="object"),
            "margin_asset": pd.Series(["USDT"], dtype="object"),
            "is_crypto": pd.Series([True], dtype="bool"),
            "onboard_date": pd.Series([pd.Timestamp("2019-09-08", tz="UTC")]),
            "delivery_date": pd.Series([pd.NaT], dtype="datetime64[ns, UTC]"),
            "underlying_type": pd.Series(["COIN"], dtype="object"),
            "metadata_source": pd.Series(["current_exchangeInfo"], dtype="object"),
        }
    )

    matched = script._match_dtypes(rows, existing)
    combined = pd.concat([existing, matched], ignore_index=True)
    for column in existing.columns:
        assert combined[column].dtype == existing[column].dtype, (
            f"{column} changed dtype on concat: {combined[column].dtype} != "
            f"{existing[column].dtype}"
        )
