"""The forward-data layer is the desk's only writer, so it is tested like one.

The failure this file exists to catch is not a crash. It is a frame that is subtly wrong, loads
cleanly through ``crypto_trade.tournament.snapshot.load_snapshot``, and makes the tournament
evaluator quietly compute the wrong thing. So the schema assertions are made against the REAL
snapshot parquet files -- both roots, column for column, dtype for dtype, and again after a parquet
round trip -- rather than against a literal repeated from the module under test.

Schema and key facts are read from both ``data/cup20/is`` and ``data/cup20/sealed``; fixture ROWS
come only from the IS side. The sealed tree carries a tripwire against its contents travelling, and
the two snapshots share a schema, so nothing is given up by keeping sealed values out of fixtures.

Every test here is network-free: the HTTP layer is stubbed with ``httpx.MockTransport``, which
exercises the real client code (pagination, weight pacing, backoff) without a socket.
"""

import ast
import dataclasses
import hashlib
import json
from pathlib import Path

import httpx
import pandas as pd
import pyarrow.parquet as pq
import pytest

from crypto_trade.cup20.activation import verify_activation
from crypto_trade.cup20_desk.live_data import (
    CONTRACT_LIFECYCLE_TRANSITIONS,
    DELISTING,
    EXCHANGE_INFO_ENDPOINT,
    FUNDING_RATE_ENDPOINT,
    KLINES_ENDPOINT,
    MANIFEST_FILENAME,
    MARK_PRICE_KLINES_ENDPOINT,
    PUBLIC_ENDPOINTS,
    SNAPSHOT_DATASETS,
    SNAPSHOT_FRAMES,
    SNAPSHOT_SCHEMAS,
    AppendInvarianceError,
    BinancePublicDataError,
    CacheDriftError,
    FrameSchemaError,
    LifecycleTransition,
    PublicMarketDataClient,
    _require_total_classification,
    append_frame,
    cache_manifest,
    conform_frame,
    empty_frame,
    fetch_forward,
    verify_cache_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
IS_ROOT = REPO_ROOT / "data" / "cup20" / "is"
SEALED_ROOT = REPO_ROOT / "data" / "cup20" / "sealed"
MODULE_PATH = REPO_ROOT / "src" / "crypto_trade" / "cup20_desk" / "live_data.py"

WINDOW_START = pd.Timestamp("2026-08-03T00:00:00Z")
WINDOW_END = pd.Timestamp("2026-08-10T00:00:00Z")
SYMBOLS = ("BTCUSDT", "ETHUSDT")

HOUR_MS = 3_600_000
PERPETUAL_DELIVERY_MS = 4_133_404_800_000

# Anything that can turn a public GET into an authenticated one. A module that imports none of
# these and mentions none of them cannot sign a request even by accident.
SIGNING_MODULES = frozenset(
    {
        "hmac",
        "crypto_trade.client",
        "crypto_trade.live",
        "crypto_trade.live.auth_client",
        "crypto_trade.config",
        "binance",
    }
)
SIGNING_TOKENS = (
    "hmac",
    "signature",
    "apiKey",
    "api_key",
    "api_secret",
    "X-MBX-APIKEY",
    "BinanceClient",
    "AuthClient",
    "listenKey",
    "/fapi/v1/order",
    "/fapi/v2/account",
)


# --------------------------------------------------------------------------------------------
# synthetic Binance payloads
# --------------------------------------------------------------------------------------------


def _milliseconds(timestamp: pd.Timestamp) -> int:
    return int(pd.Timestamp(timestamp).value // 1_000_000)


def _price(symbol: str, timestamp_ms: int) -> float:
    """Deterministic, positive, symbol-specific and time-varying."""
    base = 100.0 if symbol == "BTCUSDT" else 50.0
    return round(base + (timestamp_ms // HOUR_MS) % 97 * 0.25, 8)


def _kline_row(symbol: str, open_ms: int, interval_ms: int) -> list[object]:
    open_price = _price(symbol, open_ms)
    return [
        open_ms,
        f"{open_price:.8f}",
        f"{open_price * 1.01:.8f}",
        f"{open_price * 0.99:.8f}",
        f"{open_price * 1.002:.8f}",
        "12.5",
        open_ms + interval_ms - 1,
        f"{open_price * 12.5:.8f}",
        7,
        "6.25",
        f"{open_price * 6.25:.8f}",
        "0",
    ]


def _grid(start_ms: int, end_ms: int, step_ms: int) -> list[int]:
    first = start_ms + (-start_ms) % step_ms
    return list(range(first, end_ms + 1, step_ms))


class _StubBinance:
    """A minimal, deterministic public Binance USD-M stand-in."""

    def __init__(
        self,
        *,
        symbols: tuple[str, ...] = SYMBOLS,
        funding_interval_hours: int = 8,
        listed: tuple[str, ...] | None = None,
        funding_switch: pd.Timestamp | None = None,
        switch_interval_hours: int = 4,
        bar_skew_ms: int = 0,
        mark_skew_ms: int = 0,
    ) -> None:
        self.symbols = symbols
        self.funding_interval_hours = funding_interval_hours
        self.listed = symbols if listed is None else listed
        self.funding_switch = funding_switch
        self.switch_interval_hours = switch_interval_hours
        self.bar_skew_ms = bar_skew_ms
        self.mark_skew_ms = mark_skew_ms
        self.requests: list[httpx.Request] = []

    def funding_times(self) -> list[int]:
        """The symbol's whole funding history, so a schedule change is a fact about the data.

        Generated once over a window far wider than any request, then sliced -- exactly as a real
        venue's history behaves, and unlike a per-request grid, which would silently re-anchor the
        schedule to whatever start time the caller happened to ask for.
        """
        cursor = _milliseconds(pd.Timestamp("2026-07-01T00:00:00Z"))
        horizon = _milliseconds(pd.Timestamp("2026-09-01T00:00:00Z"))
        switch = None if self.funding_switch is None else _milliseconds(self.funding_switch)
        times: list[int] = []
        while cursor < horizon:
            times.append(cursor)
            hours = (
                self.switch_interval_hours
                if switch is not None and cursor >= switch
                else self.funding_interval_hours
            )
            cursor += hours * HOUR_MS
        return times

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self)

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path
        params = request.url.params
        if path == "/fapi/v1/exchangeInfo":
            return self._json(self._exchange_info())
        symbol = params["symbol"]
        start_ms = int(params["startTime"])
        end_ms = int(params["endTime"])
        if path == KLINES_ENDPOINT:
            return self._klines(
                symbol, start_ms, end_ms, 8 * HOUR_MS, int(params["limit"]), self.bar_skew_ms
            )
        if path == MARK_PRICE_KLINES_ENDPOINT:
            return self._klines(
                symbol, start_ms, end_ms, HOUR_MS, int(params["limit"]), self.mark_skew_ms
            )
        if path == FUNDING_RATE_ENDPOINT:
            return self._funding(symbol, start_ms, end_ms, int(params["limit"]))
        raise AssertionError(f"stub reached an unexpected endpoint: {path}")

    def _json(self, payload: object) -> httpx.Response:
        return httpx.Response(
            200,
            json=payload,
            headers={"X-MBX-USED-WEIGHT-1M": "10"},
        )

    def _klines(
        self, symbol: str, start_ms: int, end_ms: int, step_ms: int, limit: int, skew_ms: int = 0
    ) -> httpx.Response:
        opens = _grid(start_ms, end_ms, step_ms)[:limit]
        return self._json([_kline_row(symbol, value + skew_ms, step_ms) for value in opens])

    def _funding(self, symbol: str, start_ms: int, end_ms: int, limit: int) -> httpx.Response:
        times = [value for value in self.funding_times() if start_ms <= value <= end_ms][:limit]
        return self._json(
            [
                {
                    "symbol": symbol,
                    "fundingTime": value,
                    "fundingRate": f"{0.0001 + (value // HOUR_MS) % 5 * 0.00001:.8f}",
                    "markPrice": f"{_price(symbol, value):.8f}",
                }
                for value in times
            ]
        )

    def _exchange_info(self) -> dict[str, object]:
        return {
            "symbols": [
                {
                    "symbol": symbol,
                    "contractType": "PERPETUAL",
                    "quoteAsset": "USDT",
                    "marginAsset": "USDT",
                    "underlyingType": "COIN",
                    "status": "TRADING",
                    "onboardDate": _milliseconds(pd.Timestamp("2020-01-01T00:00:00Z")),
                    "deliveryDate": PERPETUAL_DELIVERY_MS,
                }
                for symbol in self.listed
            ]
        }


@pytest.fixture
def stub() -> _StubBinance:
    return _StubBinance()


@pytest.fixture
def forward(stub: _StubBinance) -> dict[str, pd.DataFrame]:
    return fetch_forward(
        SYMBOLS,
        WINDOW_START,
        WINDOW_END,
        transport=stub.transport(),
        sleep=lambda _seconds: None,
    )


# --------------------------------------------------------------------------------------------
# schema equality against the real sealed snapshot
# --------------------------------------------------------------------------------------------


@pytest.mark.parametrize("root", [IS_ROOT, SEALED_ROOT], ids=["is", "sealed"])
@pytest.mark.parametrize("name", SNAPSHOT_DATASETS)
def test_declared_schema_matches_the_real_snapshot(root: Path, name: str):
    """Column for column, in order, and dtype for dtype, against the bytes the tournament sealed."""
    actual = pd.read_parquet(root / f"{name}.parquet")
    schema = SNAPSHOT_SCHEMAS[name]
    assert tuple(actual.columns) == schema.columns
    assert tuple(str(dtype) for dtype in actual.dtypes) == tuple(
        str(dtype) for dtype in schema.pandas_dtypes
    )


@pytest.mark.parametrize("name", SNAPSHOT_DATASETS)
def test_empty_frame_carries_the_snapshot_dtypes(name: str):
    snapshot = pd.read_parquet(IS_ROOT / f"{name}.parquet")
    blank = empty_frame(name)
    assert tuple(blank.columns) == tuple(snapshot.columns)
    assert blank.dtypes.to_dict() == snapshot.dtypes.to_dict()


@pytest.mark.parametrize("root", [IS_ROOT, SEALED_ROOT], ids=["is", "sealed"])
@pytest.mark.parametrize("name", SNAPSHOT_DATASETS)
def test_written_parquet_matches_the_snapshot_arrow_schema(tmp_path: Path, root: Path, name: str):
    """The loader reads arrow, not pandas -- so the arrow schema is what must match."""
    written = tmp_path / f"{name}.parquet"
    append_frame(written, _sample(name, rows=5))
    expected = pq.ParquetFile(root / f"{name}.parquet").schema_arrow.remove_metadata()
    assert pq.ParquetFile(written).schema_arrow.remove_metadata().equals(expected)


@pytest.mark.parametrize("name", SNAPSHOT_FRAMES)
def test_fetched_frames_match_the_snapshot_dtypes(forward: dict[str, pd.DataFrame], name: str):
    snapshot = pd.read_parquet(IS_ROOT / f"{name}.parquet")
    fetched = forward[name]
    assert not fetched.empty
    assert tuple(fetched.columns) == tuple(snapshot.columns)
    assert fetched.dtypes.to_dict() == snapshot.dtypes.to_dict()


@pytest.mark.parametrize("name", SNAPSHOT_FRAMES)
def test_fetched_frames_survive_a_parquet_round_trip(
    tmp_path: Path, forward: dict[str, pd.DataFrame], name: str
):
    snapshot = pd.read_parquet(IS_ROOT / f"{name}.parquet")
    path = tmp_path / f"{name}.parquet"
    append_frame(path, forward[name])
    reloaded = pd.read_parquet(path)
    assert tuple(reloaded.columns) == tuple(snapshot.columns)
    assert reloaded.dtypes.to_dict() == snapshot.dtypes.to_dict()


def test_natural_keys_are_the_ones_the_desk_appends_on():
    assert SNAPSHOT_SCHEMAS["bars"].key == ("symbol", "open_time")
    assert SNAPSHOT_SCHEMAS["funding"].key == ("symbol", "funding_time")
    assert SNAPSHOT_SCHEMAS["mark_prices"].key == ("symbol", "mark_time")
    assert SNAPSHOT_SCHEMAS["contract_metadata"].key == ("symbol",)


@pytest.mark.parametrize("root", [IS_ROOT, SEALED_ROOT], ids=["is", "sealed"])
@pytest.mark.parametrize("name", SNAPSHOT_DATASETS)
def test_every_key_is_unique_in_the_snapshot(root: Path, name: str):
    """A key that is not unique in the snapshot is not a natural key."""
    snapshot = pd.read_parquet(root / f"{name}.parquet")
    assert not snapshot.duplicated(list(SNAPSHOT_SCHEMAS[name].key)).any()


# --------------------------------------------------------------------------------------------
# what fetch_forward actually fetches
# --------------------------------------------------------------------------------------------


def test_fetch_forward_bars_are_the_8h_decision_grid(forward: dict[str, pd.DataFrame]):
    bars = forward["bars"]
    assert set(bars["symbol"]) == set(SYMBOLS)
    assert bars["open_time"].min() == WINDOW_START
    assert bars["open_time"].max() == WINDOW_END - pd.Timedelta(hours=8)
    assert (bars["open_time"].dt.hour % 8 == 0).all()
    assert len(bars) == len(SYMBOLS) * 21


def test_fetch_forward_marks_are_8h_aligned_and_bar_coincident(forward: dict[str, pd.DataFrame]):
    """The evaluator looks a mark up at a bar open and nowhere else."""
    marks = forward["mark_prices"]
    assert (marks["mark_time"].dt.hour % 8 == 0).all()
    bars = forward["bars"]
    keys = set(zip(bars["symbol"], bars["open_time"], strict=True))
    assert set(zip(marks["symbol"], marks["mark_time"], strict=True)) == keys


def test_fetch_forward_funding_carries_the_floor_hour_mark(forward: dict[str, pd.DataFrame]):
    funding = forward["funding"]
    assert (funding["settlement_time"] == funding["funding_time"].dt.floor("h")).all()
    assert (funding["mark_time"] == funding["settlement_time"]).all()
    assert (funding["funding_interval_hours"] == 8.0).all()
    assert funding["funding_time"].min() >= WINDOW_START
    assert funding["funding_time"].max() < WINDOW_END


def test_fetch_forward_derives_a_four_hour_funding_interval():
    """The interval is derived from adjacent events, never assumed to be eight hours."""
    stub = _StubBinance(funding_interval_hours=4)
    frames = fetch_forward(
        SYMBOLS,
        WINDOW_START,
        WINDOW_END,
        transport=stub.transport(),
        sleep=lambda _seconds: None,
    )
    assert (frames["funding"]["funding_interval_hours"] == 4.0).all()
    off_grid = frames["funding"]["settlement_time"].dt.hour % 8 != 0
    assert off_grid.any(), "a 4h schedule must produce marks off the 8h grid"


def test_funding_intervals_agree_across_overlapping_windows(tmp_path: Path):
    """The derived interval must not depend on where the fetch window starts.

    A symbol whose funding schedule changes at the window's first event is the case that separates
    a derivation reading BACKWARD from one reading forward: read forward, the same event gets one
    interval when it is the first row fetched and another when a wider window supplies its
    predecessor -- and a rolling desk then aborts on its own arithmetic.
    """
    switch = WINDOW_START + pd.Timedelta(days=1)
    stub = _StubBinance(funding_switch=switch, switch_interval_hours=4)
    narrow = fetch_forward(
        SYMBOLS, switch, WINDOW_END, transport=stub.transport(), sleep=lambda _s: None
    )
    wide = fetch_forward(
        SYMBOLS, WINDOW_START, WINDOW_END, transport=stub.transport(), sleep=lambda _s: None
    )
    first = narrow["funding"].iloc[0]
    assert first["funding_time"] == switch
    assert first["funding_interval_hours"] == 8.0

    path = tmp_path / "funding.parquet"
    append_frame(path, narrow["funding"])
    result = append_frame(path, wide["funding"])
    assert result.unchanged == len(narrow["funding"])


def test_fetch_forward_contract_metadata_is_one_row_per_symbol(forward: dict[str, pd.DataFrame]):
    metadata = forward["contract_metadata"]
    assert list(metadata["symbol"]) == sorted(SYMBOLS)
    assert (metadata["metadata_source"] == "current_exchangeInfo").all()
    assert metadata["is_crypto"].all()


def test_fetch_forward_infers_metadata_for_a_delisted_symbol():
    """A symbol that has left exchangeInfo still needs a metadata row, marked as inferred."""
    stub = _StubBinance(listed=("BTCUSDT",))
    frames = fetch_forward(
        SYMBOLS,
        WINDOW_START,
        WINDOW_END,
        transport=stub.transport(),
        sleep=lambda _seconds: None,
    )
    metadata = frames["contract_metadata"].set_index("symbol")
    assert metadata.loc["ETHUSDT", "metadata_source"] == "archive_inference"
    assert metadata.loc["BTCUSDT", "metadata_source"] == "current_exchangeInfo"


def test_fetch_forward_is_deterministic(stub: _StubBinance):
    first = fetch_forward(
        SYMBOLS, WINDOW_START, WINDOW_END, transport=stub.transport(), sleep=lambda _s: None
    )
    second = fetch_forward(
        SYMBOLS, WINDOW_START, WINDOW_END, transport=stub.transport(), sleep=lambda _s: None
    )
    for name in SNAPSHOT_FRAMES:
        pd.testing.assert_frame_equal(first[name], second[name])


def test_fetch_forward_paginates_without_changing_the_result(
    stub: _StubBinance, forward: dict[str, pd.DataFrame]
):
    """A limit small enough to force many pages must produce the same frames."""
    paged = fetch_forward(
        SYMBOLS,
        WINDOW_START,
        WINDOW_END,
        transport=stub.transport(),
        sleep=lambda _s: None,
        kline_limit=5,
    )
    for name in SNAPSHOT_FRAMES:
        pd.testing.assert_frame_equal(paged[name], forward[name])
    assert len(stub.requests) > len(SYMBOLS) * 3


@pytest.mark.parametrize("skew", ["bar_skew_ms", "mark_skew_ms"])
def test_fetch_forward_refuses_an_off_grid_timestamp(skew: str):
    """Bar-open alignment is what makes the published mark panel readable by the evaluator.

    The mark panel keeps only marks coincident with a bar open, so nothing downstream re-checks the
    grid -- these two guards are where an off-grid venue timestamp has to stop.
    """
    stub = _StubBinance(**{skew: 30 * 60_000})
    with pytest.raises(ValueError, match="misaligned"):
        fetch_forward(
            SYMBOLS, WINDOW_START, WINDOW_END, transport=stub.transport(), sleep=lambda _s: None
        )


def test_fetch_forward_rejects_an_unaligned_window(stub: _StubBinance):
    with pytest.raises(ValueError, match="8h"):
        fetch_forward(
            SYMBOLS,
            WINDOW_START + pd.Timedelta(hours=1),
            WINDOW_END,
            transport=stub.transport(),
            sleep=lambda _s: None,
        )


def test_fetch_forward_touches_only_public_endpoints(stub: _StubBinance):
    fetch_forward(
        SYMBOLS, WINDOW_START, WINDOW_END, transport=stub.transport(), sleep=lambda _s: None
    )
    assert stub.requests
    for request in stub.requests:
        assert request.method == "GET"
        assert request.url.path in PUBLIC_ENDPOINTS
        assert "X-MBX-APIKEY" not in request.headers
        assert "signature" not in request.url.params
        assert not request.content


# --------------------------------------------------------------------------------------------
# append invariance
# --------------------------------------------------------------------------------------------


def _sample(name: str, rows: int = 4) -> pd.DataFrame:
    """Fixture rows come from the IS snapshot, never the sealed one.

    The two have identical schemas, so nothing is lost -- and ``data/cup20/sealed`` carries a
    tripwire against its contents leaving the organiser's hands. The sealed tree is still read for
    schema and key comparisons, which is what the desk actually has to match; its VALUES have no
    business in a test fixture.
    """
    return conform_frame(name, pd.read_parquet(IS_ROOT / f"{name}.parquet").head(rows))


def test_append_frame_creates_the_file_and_counts_every_row(tmp_path: Path):
    frame = _sample("bars")
    result = append_frame(tmp_path / "bars.parquet", frame)
    assert (result.appended, result.unchanged, result.total) == (len(frame), 0, len(frame))
    assert result.name == "bars"


@pytest.mark.parametrize("name", SNAPSHOT_FRAMES)
def test_an_identical_refetch_is_a_no_op(tmp_path: Path, name: str):
    path = tmp_path / f"{name}.parquet"
    frame = _sample(name)
    append_frame(path, frame)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    result = append_frame(path, frame)
    assert (result.appended, result.unchanged) == (0, len(frame))
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_a_genuinely_new_row_appends(tmp_path: Path):
    path = tmp_path / "bars.parquet"
    rows = _sample("bars", rows=6)
    append_frame(path, rows.head(4))
    result = append_frame(path, rows)
    assert (result.appended, result.unchanged, result.total) == (2, 4, 6)
    stored = pd.read_parquet(path)
    assert len(stored) == 6
    assert not stored.duplicated(["symbol", "open_time"]).any()


CHANGED_VALUES = {
    "bars": ("close", 1.0),
    "funding": ("funding_rate", 0.5),
    "mark_prices": ("mark_price", 1.0),
    "contract_metadata": ("metadata_source", "tampered"),
}


@pytest.mark.parametrize("name", SNAPSHOT_FRAMES)
def test_a_changed_value_on_an_existing_key_aborts(tmp_path: Path, name: str):
    path = tmp_path / f"{name}.parquet"
    frame = _sample(name)
    append_frame(path, frame)
    column, value = CHANGED_VALUES[name]
    revised = frame.copy()
    revised.loc[revised.index[0], column] = value
    revised = conform_frame(name, revised)
    with pytest.raises(AppendInvarianceError) as error:
        append_frame(path, revised)
    message = str(error.value)
    assert column in message
    for key_column in SNAPSHOT_SCHEMAS[name].key:
        assert key_column in message
        assert str(frame.iloc[0][key_column]) in message
    assert error.value.column == column
    assert error.value.name == name


def test_an_abort_preserves_both_values_and_leaves_the_file_untouched(tmp_path: Path):
    path = tmp_path / "bars.parquet"
    frame = _sample("bars")
    append_frame(path, frame)
    before = path.read_bytes()
    revised = frame.copy()
    revised.loc[revised.index[0], "close"] = 1.0
    with pytest.raises(AppendInvarianceError) as error:
        append_frame(path, conform_frame("bars", revised))
    assert error.value.existing == frame.iloc[0]["close"]
    assert error.value.incoming == 1.0
    assert path.read_bytes() == before


def test_a_nan_is_not_treated_as_a_revision(tmp_path: Path):
    """NaN != NaN would make every already-recorded null look like a revision."""
    path = tmp_path / "contract_metadata.parquet"
    frame = _sample("contract_metadata")
    frame.loc[frame.index[0], "delivery_date"] = pd.NaT
    frame = conform_frame("contract_metadata", frame)
    append_frame(path, frame)
    result = append_frame(path, frame)
    assert (result.appended, result.unchanged) == (0, len(frame))


def test_append_frame_rejects_a_frame_with_the_wrong_schema(tmp_path: Path):
    frame = _sample("bars").drop(columns=["quote_volume"])
    with pytest.raises(FrameSchemaError, match="quote_volume"):
        append_frame(tmp_path / "bars.parquet", frame)


def test_append_frame_rejects_duplicate_keys_in_the_incoming_frame(tmp_path: Path):
    frame = _sample("bars")
    doubled = conform_frame("bars", pd.concat([frame, frame.head(1)], ignore_index=True))
    with pytest.raises(ValueError, match="duplicate"):
        append_frame(tmp_path / "bars.parquet", doubled)


def test_append_frame_keeps_the_snapshot_row_order(tmp_path: Path):
    path = tmp_path / "bars.parquet"
    frame = _sample("bars", rows=40)
    append_frame(path, frame.iloc[::-1])
    stored = pd.read_parquet(path)
    expected = frame.sort_values(["open_time", "symbol"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(stored, expected)


# --------------------------------------------------------------------------------------------
# delisting is a transition, not a revision
# --------------------------------------------------------------------------------------------

LIVE_CONTRACT = {
    "symbol": "DELISTUSDT",
    "contract_type": "PERPETUAL",
    "quote_asset": "USDT",
    "margin_asset": "USDT",
    "is_crypto": True,
    "onboard_date": pd.Timestamp("2021-03-01T00:00:00Z"),
    "delivery_date": pd.Timestamp(PERPETUAL_DELIVERY_MS, unit="ms", tz="UTC"),
    "underlying_type": "COIN",
    "metadata_source": "current_exchangeInfo",
}

# What `crypto_trade.tournament.snapshot._contract_metadata` writes once the symbol has left live
# exchangeInfo: archive-inferred, with a real delivery date and an onboard date read off whatever
# bars that fetch happened to hold.
DELISTED_CONTRACT = LIVE_CONTRACT | {
    "onboard_date": pd.Timestamp("2026-08-03T00:00:00Z"),
    "delivery_date": pd.Timestamp("2026-08-06T08:00:00Z"),
    "underlying_type": "ARCHIVE_INFERRED_COIN",
    "metadata_source": "archive_inference",
}


def _metadata(*rows: dict[str, object]) -> pd.DataFrame:
    return conform_frame("contract_metadata", pd.DataFrame(list(rows)))


@pytest.fixture
def recorded_metadata(tmp_path: Path) -> Path:
    path = tmp_path / "contract_metadata.parquet"
    append_frame(path, _metadata(LIVE_CONTRACT))
    return path


def test_a_delisting_transitions_the_recorded_row(recorded_metadata: Path):
    """The event this exists for: a member leaves exchangeInfo and the desk keeps running."""
    result = append_frame(recorded_metadata, _metadata(DELISTED_CONTRACT))
    assert (result.appended, result.unchanged, result.transitioned) == (0, 0, 1)
    stored = pd.read_parquet(recorded_metadata).set_index("symbol").loc["DELISTUSDT"]
    assert stored["metadata_source"] == "archive_inference"
    assert stored["underlying_type"] == "ARCHIVE_INFERRED_COIN"
    assert stored["delivery_date"] == DELISTED_CONTRACT["delivery_date"]


def test_a_delisting_keeps_the_recorded_onboard_date(recorded_metadata: Path):
    """The archive branch infers ``onboard_date`` from the fetch window, so the record wins.

    Adopting the incoming value would let a desk that fetches one week at a time rewrite a 2021
    listing date to last Monday -- a fact getting worse on every tick, under a rule whose whole
    purpose is that recorded facts do not move.
    """
    append_frame(recorded_metadata, _metadata(DELISTED_CONTRACT))
    stored = pd.read_parquet(recorded_metadata).set_index("symbol").loc["DELISTUSDT"]
    assert stored["onboard_date"] == LIVE_CONTRACT["onboard_date"]


def test_an_earlier_onboard_date_is_a_revision_and_aborts(recorded_metadata: Path):
    """Later is a narrower window; earlier means the recorded value was simply wrong."""
    rewound = DELISTED_CONTRACT | {"onboard_date": pd.Timestamp("2020-01-01T00:00:00Z")}
    with pytest.raises(AppendInvarianceError, match="onboard_date"):
        append_frame(recorded_metadata, _metadata(rewound))


def test_a_second_identical_delisting_is_a_no_op(recorded_metadata: Path):
    """Idempotent, or the desk aborts on its own transition the tick after it fires."""
    append_frame(recorded_metadata, _metadata(DELISTED_CONTRACT))
    digest = hashlib.sha256(recorded_metadata.read_bytes()).hexdigest()
    result = append_frame(recorded_metadata, _metadata(DELISTED_CONTRACT))
    assert (result.appended, result.unchanged, result.transitioned) == (0, 1, 0)
    assert hashlib.sha256(recorded_metadata.read_bytes()).hexdigest() == digest


def test_a_delisted_contract_returning_to_live_aborts(recorded_metadata: Path):
    """The transition is one-way. A reversal is the record moving backwards."""
    append_frame(recorded_metadata, _metadata(DELISTED_CONTRACT))
    with pytest.raises(AppendInvarianceError, match="metadata_source"):
        append_frame(recorded_metadata, _metadata(LIVE_CONTRACT))


CONTRACT_IDENTITY_CHANGES = {
    "quote_asset": "USDC",
    "margin_asset": "USDC",
    "contract_type": "CURRENT_QUARTER",
    "is_crypto": False,
}


@pytest.mark.parametrize("column,value", sorted(CONTRACT_IDENTITY_CHANGES.items()))
def test_a_changed_contract_identity_aborts_even_alongside_a_delisting(
    recorded_metadata: Path, column: str, value: object
):
    """The allowlist is not a blanket bypass: it permits a state change, not a different contract.

    Bundled WITH a genuine delisting on purpose. Rejecting the change on its own would only prove
    the transition has to fire; rejecting it while the transition fires proves the allowlist is
    read column by column rather than as a licence over the whole row.
    """
    with pytest.raises(AppendInvarianceError, match=column):
        append_frame(recorded_metadata, _metadata(DELISTED_CONTRACT | {column: value}))


def test_an_identity_change_without_a_delisting_aborts(recorded_metadata: Path):
    with pytest.raises(AppendInvarianceError, match="quote_asset"):
        append_frame(recorded_metadata, _metadata(LIVE_CONTRACT | {"quote_asset": "USDC"}))


def test_a_delivery_date_may_only_be_brought_forward(recorded_metadata: Path):
    """A delisting brings an unknown or far-future delivery date onto a date that has arrived."""
    postponed = DELISTED_CONTRACT | {"delivery_date": pd.Timestamp("2200-01-01T00:00:00Z")}
    with pytest.raises(AppendInvarianceError, match="delivery_date"):
        append_frame(recorded_metadata, _metadata(postponed))


def test_a_delivery_date_becoming_unknown_aborts(recorded_metadata: Path):
    erased = DELISTED_CONTRACT | {"delivery_date": pd.NaT}
    with pytest.raises(AppendInvarianceError, match="delivery_date"):
        append_frame(recorded_metadata, _metadata(erased))


def test_an_unnamed_underlying_type_aborts(recorded_metadata: Path):
    """``followed`` columns move to a value named in advance, not to any value at all."""
    invented = DELISTED_CONTRACT | {"underlying_type": "INDEX"}
    with pytest.raises(AppendInvarianceError, match="underlying_type"):
        append_frame(recorded_metadata, _metadata(invented))


def test_a_transition_leaves_every_other_recorded_row_alone(tmp_path: Path):
    path = tmp_path / "contract_metadata.parquet"
    survivor = LIVE_CONTRACT | {"symbol": "STAYUSDT"}
    append_frame(path, _metadata(LIVE_CONTRACT, survivor))
    result = append_frame(path, _metadata(DELISTED_CONTRACT, survivor))
    assert (result.appended, result.unchanged, result.transitioned) == (0, 1, 1)
    stored = pd.read_parquet(path).set_index("symbol")
    assert stored.loc["STAYUSDT", "metadata_source"] == "current_exchangeInfo"
    assert stored.loc["STAYUSDT", "onboard_date"] == LIVE_CONTRACT["onboard_date"]


def test_an_aborted_transition_writes_nothing(recorded_metadata: Path):
    before = recorded_metadata.read_bytes()
    with pytest.raises(AppendInvarianceError):
        append_frame(recorded_metadata, _metadata(DELISTED_CONTRACT | {"quote_asset": "USDC"}))
    assert recorded_metadata.read_bytes() == before


@pytest.mark.parametrize("name", [name for name in SNAPSHOT_FRAMES if name != "contract_metadata"])
def test_no_other_frame_can_transition(tmp_path: Path, name: str):
    """The allowlist is scoped to one frame. A revised bar or mark still aborts.

    Proved on the frames themselves rather than by reading ``DELISTING.frame``: a bug that dropped
    the frame check would leave that attribute perfectly correct.
    """
    path = tmp_path / f"{name}.parquet"
    frame = _sample(name)
    append_frame(path, frame)
    column, value = CHANGED_VALUES[name]
    revised = frame.copy()
    revised.loc[revised.index[0], column] = value
    with pytest.raises(AppendInvarianceError, match=column):
        append_frame(path, conform_frame(name, revised))


def test_the_allowlist_is_declared_once_and_scoped_to_contract_metadata():
    assert CONTRACT_LIFECYCLE_TRANSITIONS == (DELISTING,)
    assert {transition.frame for transition in CONTRACT_LIFECYCLE_TRANSITIONS} == {
        "contract_metadata"
    }
    assert DELISTING.trigger == (
        "metadata_source",
        "current_exchangeInfo",
        "archive_inference",
    )


def test_every_metadata_column_is_classified_by_the_allowlist():
    """A column nobody classified could be swept into a permissive bucket by a later edit."""
    classified = (
        {DELISTING.trigger_column}
        | set(DELISTING.followed)
        | set(DELISTING.advanced)
        | set(DELISTING.deferred)
        | set(DELISTING.invariant)
    )
    assert classified == set(SNAPSHOT_SCHEMAS["contract_metadata"].values)


def test_an_incompletely_classified_transition_is_refused_at_declaration():
    """The import-time guard, exercised: forgetting a column must be loud, not permissive."""
    partial = dataclasses.replace(DELISTING, invariant=("contract_type", "quote_asset"))
    with pytest.raises(FrameSchemaError, match="margin_asset"):
        _require_total_classification(partial)


def test_a_transition_may_not_classify_a_column_twice():
    doubled = LifecycleTransition(
        name="doubled",
        frame="contract_metadata",
        trigger=("metadata_source", "current_exchangeInfo", "archive_inference"),
        followed={"underlying_type": (("COIN", "ARCHIVE_INFERRED_COIN"),)},
        advanced=("delivery_date",),
        deferred=("onboard_date", "delivery_date"),
        invariant=("contract_type", "quote_asset", "margin_asset", "is_crypto"),
    )
    with pytest.raises(FrameSchemaError, match="twice"):
        _require_total_classification(doubled)


def test_a_delisting_survives_a_fetch_that_no_longer_carries_the_symbol(recorded_metadata: Path):
    """After the delisting week the symbol has no bars, so no metadata row -- and no conflict."""
    append_frame(recorded_metadata, _metadata(DELISTED_CONTRACT))
    other = LIVE_CONTRACT | {"symbol": "STAYUSDT"}
    result = append_frame(recorded_metadata, _metadata(other))
    assert (result.appended, result.transitioned) == (1, 0)
    assert set(pd.read_parquet(recorded_metadata)["symbol"]) == {"DELISTUSDT", "STAYUSDT"}


# --------------------------------------------------------------------------------------------
# cache manifest
# --------------------------------------------------------------------------------------------


@pytest.fixture
def cache(tmp_path: Path, forward: dict[str, pd.DataFrame]) -> Path:
    root = tmp_path / "cache"
    for name in SNAPSHOT_FRAMES:
        append_frame(root / f"{name}.parquet", forward[name])
    (root / "notes.json").write_text(json.dumps({"phase": "bridge"}) + "\n")
    return root


def test_cache_manifest_binds_path_size_rows_and_digest(cache: Path):
    manifest = cache_manifest(cache)
    entries = {entry["path"]: entry for entry in manifest["files"]}
    assert set(entries) == {f"{name}.parquet" for name in SNAPSHOT_FRAMES} | {"notes.json"}
    for name in SNAPSHOT_FRAMES:
        path = cache / f"{name}.parquet"
        entry = entries[f"{name}.parquet"]
        assert entry["size"] == path.stat().st_size
        assert entry["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert entry["rows"] == len(pd.read_parquet(path))
    assert verify_cache_manifest(cache, manifest) == manifest


def test_manifest_ignores_its_own_stored_copy(cache: Path):
    manifest = cache_manifest(cache)
    (cache / MANIFEST_FILENAME).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    assert verify_cache_manifest(cache, manifest) == manifest


def test_manifest_detects_a_mutated_file(cache: Path):
    """A same-length mutation: only the digest can see this one."""
    manifest = cache_manifest(cache)
    path = cache / "bars.parquet"
    before = path.stat().st_size
    payload = bytearray(path.read_bytes())
    payload[len(payload) // 2] ^= 0xFF
    path.write_bytes(bytes(payload))
    assert path.stat().st_size == before
    with pytest.raises(CacheDriftError) as error:
        verify_cache_manifest(cache, manifest)
    assert "bars.parquet" in str(error.value)


def test_manifest_detects_a_truncated_file(cache: Path):
    manifest = cache_manifest(cache)
    path = cache / "funding.parquet"
    payload = path.read_bytes()
    path.write_bytes(payload[: len(payload) // 2])
    with pytest.raises(CacheDriftError) as error:
        verify_cache_manifest(cache, manifest)
    assert "funding.parquet" in str(error.value)


def test_manifest_detects_dropped_rows(cache: Path):
    """A rewrite that drops rows is still a valid parquet, and is still named."""
    manifest = cache_manifest(cache)
    path = cache / "mark_prices.parquet"
    pd.read_parquet(path).head(3).to_parquet(path, index=False)
    with pytest.raises(CacheDriftError) as error:
        verify_cache_manifest(cache, manifest)
    assert "mark_prices.parquet" in str(error.value)


def test_manifest_compares_the_row_count(cache: Path):
    """Proves the row-count comparison is load-bearing and not merely recorded."""
    manifest = cache_manifest(cache)
    entry = next(item for item in manifest["files"] if item["path"] == "bars.parquet")
    entry["rows"] += 1
    with pytest.raises(CacheDriftError, match="row-count drift") as error:
        verify_cache_manifest(cache, manifest)
    assert "bars.parquet" in str(error.value)


def test_manifest_detects_a_new_file(cache: Path):
    manifest = cache_manifest(cache)
    (cache / "extra.json").write_text("[]\n")
    with pytest.raises(CacheDriftError) as error:
        verify_cache_manifest(cache, manifest)
    assert "extra.json" in str(error.value)


def test_manifest_detects_a_missing_file(cache: Path):
    manifest = cache_manifest(cache)
    (cache / "notes.json").unlink()
    with pytest.raises(CacheDriftError) as error:
        verify_cache_manifest(cache, manifest)
    assert "notes.json" in str(error.value)


def test_manifest_entries_are_sorted_and_serialisable(cache: Path):
    manifest = cache_manifest(cache)
    paths = [entry["path"] for entry in manifest["files"]]
    assert paths == sorted(paths)
    assert json.loads(json.dumps(manifest)) == manifest


# --------------------------------------------------------------------------------------------
# paper-only, by inspection
# --------------------------------------------------------------------------------------------


def _imports(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
    return names


def _crypto_trade_source(module: str) -> Path | None:
    relative = Path(*module.split(".")).with_suffix(".py")
    candidate = REPO_ROOT / "src" / relative
    if candidate.is_file():
        return candidate
    package = REPO_ROOT / "src" / Path(*module.split(".")) / "__init__.py"
    return package if package.is_file() else None


def _transitive_crypto_trade_modules(entry: Path) -> dict[str, Path]:
    seen: dict[str, Path] = {"crypto_trade.cup20_desk.live_data": entry}
    pending = [entry]
    while pending:
        for name in _imports(pending.pop()):
            if not name.startswith("crypto_trade.") or name in seen:
                continue
            source = _crypto_trade_source(name)
            if source is None:
                continue
            seen[name] = source
            pending.append(source)
    return seen


def test_the_module_imports_nothing_that_can_sign():
    assert not _imports(MODULE_PATH) & SIGNING_MODULES


def test_no_transitively_imported_module_can_sign():
    """An import two hops away signs just as well as a direct one."""
    for name, source in _transitive_crypto_trade_modules(MODULE_PATH).items():
        assert not _imports(source) & SIGNING_MODULES, name


def test_the_module_mentions_no_credential_or_order_path():
    source = MODULE_PATH.read_text()
    assert [token for token in SIGNING_TOKENS if token in source] == []


def test_every_endpoint_literal_is_declared_public():
    literals = {
        node.value
        for node in ast.walk(ast.parse(MODULE_PATH.read_text()))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert {value for value in literals if value.startswith("/fapi")} == set(PUBLIC_ENDPOINTS)
    assert PUBLIC_ENDPOINTS == frozenset(
        {
            "/fapi/v1/klines",
            "/fapi/v1/markPriceKlines",
            "/fapi/v1/fundingRate",
            "/fapi/v1/exchangeInfo",
        }
    )


# --------------------------------------------------------------------------------------------
# being a polite client
# --------------------------------------------------------------------------------------------


def _counting_transport(responses: list[httpx.Response]) -> tuple[httpx.MockTransport, list[int]]:
    calls: list[int] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return responses[min(len(calls) - 1, len(responses) - 1)]

    return httpx.MockTransport(handler), calls


def test_a_ban_is_reported_at_once_and_never_retried():
    """Every request made while barred extends the bar -- retrying is the one thing not to do."""
    body = '{"code":-1003,"msg":"Way too many requests; IP banned until 1786758825127."}'
    transport, calls = _counting_transport([httpx.Response(418, text=body)])
    with PublicMarketDataClient(transport=transport, sleep=lambda _s: None) as client:
        with pytest.raises(BinancePublicDataError) as error:
            client.get_json(EXCHANGE_INFO_ENDPOINT)
    assert len(calls) == 1
    assert "2026-08-15" in str(error.value)
    assert "not retried" in str(error.value)


def test_a_rate_limit_is_retried_and_honours_retry_after():
    limited = httpx.Response(429, headers={"Retry-After": "7"}, text="{}")
    served = httpx.Response(200, json={"symbols": []}, headers={"X-MBX-USED-WEIGHT-1M": "3"})
    transport, calls = _counting_transport([limited, limited, served])
    slept: list[float] = []
    with PublicMarketDataClient(transport=transport, sleep=slept.append) as client:
        assert client.get_json(EXCHANGE_INFO_ENDPOINT) == {"symbols": []}
    assert len(calls) == 3
    assert 7.0 in slept


def test_the_client_pauses_when_the_weight_budget_runs_low():
    served = httpx.Response(200, json={"symbols": []}, headers={"X-MBX-USED-WEIGHT-1M": "2000"})
    transport, _calls = _counting_transport([served])
    slept: list[float] = []
    with PublicMarketDataClient(
        transport=transport, sleep=slept.append, weight_soft_limit=1_800
    ) as client:
        client.get_json(EXCHANGE_INFO_ENDPOINT)
    assert client.used_weight == 2000
    assert 60.0 in slept


def test_the_client_refuses_an_undeclared_endpoint(stub: _StubBinance):
    with PublicMarketDataClient(transport=stub.transport(), sleep=lambda _s: None) as client:
        with pytest.raises(ValueError, match="public"):
            client.get_json("/fapi/v1/order", params={"symbol": "BTCUSDT"})


def test_append_result_is_an_immutable_record(tmp_path: Path):
    result = append_frame(tmp_path / "bars.parquet", _sample("bars"))
    assert dataclasses.is_dataclass(result)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.appended = 99


def test_activation_freeze_still_verifies(monkeypatch):
    """The desk may not disturb one byte of what the tournament hash-bound."""
    monkeypatch.chdir(REPO_ROOT)
    verify_activation("tournament/cup20/activation-freeze.json")
