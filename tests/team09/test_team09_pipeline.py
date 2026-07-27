from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path
from types import SimpleNamespace

import httpx
import numpy as np
import pandas as pd
import pytest

from crypto_trade.team09 import backtest
from crypto_trade.team09.authority import (
    CANDIDATE_ID,
    EVALUATOR_AUTHORITY_SHA256,
    STRATEGY_SHA256,
    release_team_root,
    verify_deployment_authority,
    verify_frozen_authority,
)
from crypto_trade.team09.backtest import (
    historical_terminal_held_symbols,
    load_frozen_snapshot,
    run_replay,
    verify_historical_parity,
)
from crypto_trade.team09.live import (
    _BOUNDARY_FILL_EVENT_TYPES,
    _gate_frame,
    _modeled_equity_after_execution,
    _position_frame,
)
from crypto_trade.team09.live_data import (
    BRIDGE_START,
    Team09PublicDataClient,
    _append_invariant_cache,
    _causal_accounting_rows,
    _resolve_accounting_admissions,
    classify_current_contracts,
    classify_known_contracts,
    resolve_contract_lifecycle,
    verify_live_cache_manifest,
    write_live_cache_manifest,
)
from crypto_trade.team09.report import (
    load_released_daily_returns,
    period_statistics,
)


def _contract(symbol: str, **overrides: object) -> dict[str, object]:
    base = symbol.removesuffix("USDT")
    result: dict[str, object] = {
        "symbol": symbol,
        "status": "TRADING",
        "contractType": "PERPETUAL",
        "underlyingType": "COIN",
        "underlyingSubType": ["Layer-1"],
        "quoteAsset": "USDT",
        "marginAsset": "USDT",
        "baseAsset": base,
        "onboardDate": 1_700_000_000_000,
        "deliveryDate": 4_133_404_800_000,
    }
    result.update(overrides)
    return result


def test_frozen_team09_authority_is_exact() -> None:
    authority = verify_frozen_authority()
    assert authority.candidate_id == CANDIDATE_ID
    assert authority.strategy_sha256 == STRATEGY_SHA256
    assert authority.evaluator_authority_sha256 == EVALUATOR_AUTHORITY_SHA256
    deployment = verify_deployment_authority()
    assert authority.deployment_bundle_sha256 == deployment.bundle_sha256
    assert authority.deployment_manifest_sha256 == deployment.manifest_sha256
    assert authority.deployment_git_commit == deployment.git_commit
    assert "BNXUSDT" in historical_terminal_held_symbols()


def test_pure_crypto_live_policy_excludes_stable_and_tradfi() -> None:
    exchange_info = {
        "symbols": [
            _contract("BTCUSDT"),
            _contract("USDCUSDT", baseAsset="USDC"),
            _contract(
                "XAUUSDT",
                baseAsset="XAU",
                contractType="TRADIFI_PERPETUAL",
                underlyingType="INDEX",
                underlyingSubType=["TradFi"],
            ),
        ]
    }
    accepted, excluded = classify_current_contracts(exchange_info)
    assert set(accepted) == {"BTCUSDT"}
    assert "stablecoin-base" in excluded["USDCUSDT"]
    assert "direct-non-crypto-base" in excluded["XAUUSDT"]
    assert "forbidden-underlying-type" in excluded["XAUUSDT"]


def test_inactive_pure_contract_remains_in_historical_registry() -> None:
    inactive = _contract("BTCUSDT", status="SETTLING")
    current = {"symbols": [inactive, _contract("ETHUSDT")]}
    active, active_exclusions = classify_current_contracts(current)
    known, classification_exclusions = classify_known_contracts(
        current
    )
    assert set(active) == {"ETHUSDT"}
    assert active_exclusions["BTCUSDT"] == ("status-not-trading",)
    assert set(known) == {"BTCUSDT", "ETHUSDT"}
    assert classification_exclusions == {}


def test_rest_invalid_symbol_uses_checksum_verified_daily_archive() -> None:
    key = (
        "data/futures/um/daily/klines/BTCSTUSDT/8h/"
        "BTCSTUSDT-8h-2026-07-22.zip"
    )
    member = "BTCSTUSDT-8h-2026-07-22.csv"
    csv_payload = (
        "open_time,open,high,low,close,volume,close_time,quote_volume,count,"
        "taker_buy_volume,taker_buy_quote_volume,ignore\n"
        "1784678400000,319.408,319.408,319.408,319.408,0,"
        "1784707199999,0,0,0,0,0\n"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member, csv_payload)
    archive_bytes = buffer.getvalue()
    digest = hashlib.sha256(archive_bytes).hexdigest()
    request_counts: dict[str, int] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        request_counts[path] = request_counts.get(path, 0) + 1
        if path == "/fapi/v1/klines":
            return httpx.Response(
                400,
                json={"code": -1122, "msg": "Invalid symbol status."},
            )
        if request.url.host == "s3-ap-northeast-1.amazonaws.com":
            return httpx.Response(
                200,
                text=(
                    "<ListBucketResult><IsTruncated>false</IsTruncated>"
                    f"<Contents><Key>{key}</Key></Contents></ListBucketResult>"
                ),
            )
        if path.endswith(".zip.CHECKSUM"):
            return httpx.Response(
                200,
                text=f"{digest}  {Path(key).name}\n",
            )
        if path.endswith(".zip"):
            return httpx.Response(200, content=archive_bytes)
        raise AssertionError(f"unexpected request: {request.url}")

    with Team09PublicDataClient(
        transport=httpx.MockTransport(handler),
        pause_seconds=0.0,
    ) as client:
        frame = client.transaction_bars(
            "BTCSTUSDT",
            start=pd.Timestamp("2026-07-22T00:00:00Z"),
            end_inclusive=pd.Timestamp("2026-07-22T07:59:59.999Z"),
        )
        provenance = client.archive_provenance()
    assert request_counts["/fapi/v1/klines"] == 1
    assert frame["open_time"].tolist() == [
        pd.Timestamp("2026-07-22T00:00:00Z")
    ]
    assert frame["open"].tolist() == [319.408]
    assert provenance[0]["archive_path"] == key
    assert provenance[0]["archive_sha256"] == digest


def test_live_cache_aborts_if_a_sealed_value_changes(tmp_path: Path) -> None:
    path = tmp_path / "bars.parquet"
    original = pd.DataFrame(
        {
            "open_time": [pd.Timestamp("2026-07-01T00:00:00Z")],
            "symbol": ["BTCUSDT"],
            "close": [100.0],
        }
    )
    _append_invariant_cache(
        path,
        original,
        keys=("open_time", "symbol"),
        values=("close",),
    )
    revised = original.assign(close=101.0)
    with pytest.raises(RuntimeError, match="APPEND-INVARIANCE ABORT"):
        _append_invariant_cache(
            path,
            revised,
            keys=("open_time", "symbol"),
            values=("close",),
        )


def test_new_accounting_symbols_are_causally_admitted() -> None:
    boundary = pd.Timestamp("2026-07-27T00:00:00Z")
    prior = {"OLDUSDT": BRIDGE_START.isoformat()}
    admissions = _resolve_accounting_admissions(
        {
            "accounting_symbols": ["OLDUSDT", "NEWUSDT"],
        },
        prior=prior,
        accounting_symbols=("OLDUSDT", "NEWUSDT"),
        boundary=boundary,
    )
    assert admissions == {
        "NEWUSDT": boundary.isoformat(),
        "OLDUSDT": BRIDGE_START.isoformat(),
    }

    frame = pd.DataFrame(
        {
            "funding_time": [
                BRIDGE_START,
                BRIDGE_START,
                boundary,
            ],
            "symbol": ["OLDUSDT", "NEWUSDT", "NEWUSDT"],
            "funding_rate": [0.001, 0.002, 0.003],
            "mark_price": [100.0, 200.0, 201.0],
        }
    )
    causal = _causal_accounting_rows(
        frame,
        time_column="funding_time",
        admissions=admissions,
    )
    assert causal[["funding_time", "symbol"]].to_dict("records") == [
        {"funding_time": BRIDGE_START, "symbol": "OLDUSDT"},
        {"funding_time": boundary, "symbol": "NEWUSDT"},
    ]


def test_accounting_admission_revision_aborts() -> None:
    boundary = pd.Timestamp("2026-07-27T08:00:00Z")
    with pytest.raises(
        RuntimeError,
        match="APPEND-INVARIANCE ABORT: accounting admission revised",
    ):
        _resolve_accounting_admissions(
            {
                "accounting_symbols": ["BTCUSDT"],
                "accounting_admission_boundaries": {
                    "BTCUSDT": BRIDGE_START.isoformat(),
                },
            },
            prior={
                "BTCUSDT": pd.Timestamp(
                    "2026-07-27T00:00:00Z"
                ).isoformat(),
            },
            accounting_symbols=("BTCUSDT",),
            boundary=boundary,
        )


def test_live_cache_manifest_detects_tampering(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    pd.DataFrame({"open_time": [], "symbol": []}).to_parquet(
        cache / "bars.parquet", index=False
    )
    pd.DataFrame({"open_time": [], "symbol": []}).to_parquet(
        cache / "forming-bars.parquet", index=False
    )
    pd.DataFrame({"mark_time": [], "symbol": []}).to_parquet(
        cache / "mark_prices.parquet", index=False
    )
    pd.DataFrame({"funding_time": [], "symbol": []}).to_parquet(
        cache / "funding.parquet", index=False
    )
    pd.DataFrame({"symbol": []}).to_parquet(
        cache / "contract_metadata.parquet", index=False
    )
    for name, payload in (
        ("archive-kline-provenance.json", []),
        ("archive-symbols.json", []),
        ("candidate-symbols.json", []),
        ("classified-contracts.json", {}),
        ("contract-lifecycle.json", {}),
        ("excluded-contracts.json", {}),
        (
            "diagnostics.json",
            {"boundary": "2026-07-01T00:00:00+00:00"},
        ),
    ):
        (cache / name).write_text(f"{__import__('json').dumps(payload)}\n")
    exchange = cache / "exchange-info"
    exchange.mkdir()
    (exchange / "20260701T000000Z-1.json").write_text(
        '{"serverTime": 1, "symbols": []}\n'
    )
    write_live_cache_manifest(
        cache,
        boundary=pd.Timestamp("2026-07-01T00:00:00Z"),
    )
    assert verify_live_cache_manifest(cache) is not None
    (cache / "candidate-symbols.json").write_text('["BTCUSDT"]\n')
    with pytest.raises(RuntimeError, match="drift"):
        verify_live_cache_manifest(cache)


def test_forward_gate_uses_daily_metrics_but_keeps_bar_count() -> None:
    timestamps = pd.date_range("2026-08-01", periods=6, freq="8h", tz="UTC")
    forward = pd.DataFrame(
        {
            "timestamp": timestamps,
            "net_return": [0.01, -0.005, 0.004, 0.002, -0.001, 0.003],
        }
    )
    gate = _gate_frame(forward).iloc[0]
    daily = (
        pd.Series(forward["net_return"].to_numpy(), index=timestamps)
        .groupby(timestamps.floor("D"))
        .apply(lambda values: np.prod(1.0 + values) - 1.0)
    )
    from crypto_trade.tournament.metrics_v3 import compute_window_metrics

    assert gate["observations"] == 6
    assert gate["daily_observations"] == 2
    assert gate["net_sharpe"] == pytest.approx(
        compute_window_metrics(daily).net_sharpe
    )


def test_boundary_ledger_includes_real_forced_exits_and_drops_quantity_dust() -> None:
    assert {"forced_exit", "conservative_settlement"}.issubset(
        _BOUNDARY_FILL_EVENT_TYPES
    )
    tick = SimpleNamespace(
        boundary=pd.Timestamp("2026-07-01T00:00:00Z"),
        held_weights=pd.Series({"BTCUSDT": 0.1}),
        held_quantities=pd.Series({"BTCUSDT": 1.0, "ONEUSDT": 1e-11}),
    )
    positions = _position_frame(tick)
    assert positions["symbol"].tolist() == ["BTCUSDT"]
    assert positions["side"].tolist() == ["LONG"]


def test_forced_exit_cost_is_not_double_counted_in_modeled_equity() -> None:
    boundary = pd.Timestamp("2026-07-01T08:00:00Z")
    returns = pd.DataFrame(
        {"equity": [100.0]},
        index=pd.DatetimeIndex([boundary - pd.Timedelta(hours=8)]),
    )
    events = pd.DataFrame(
        {
            "event_type": ["forced_exit"],
            "phase": ["after_return"],
            "fee": [1.0],
            "slippage": [1.0],
            "cashflow": [0.0],
        }
    )
    assert (
        _modeled_equity_after_execution(returns, events, boundary=boundary)
        == 100.0
    )


def test_absent_contract_lifecycle_uses_current_horizon_not_replay_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    replay_boundary = pd.Timestamp("2026-07-20T00:00:00Z")
    horizon = pd.Timestamp("2026-07-23T08:00:00Z")
    monkeypatch.setattr(
        "crypto_trade.team09.live_data.current_boundary",
        lambda: horizon,
    )
    full = pd.DataFrame(
        {
            "open_time": [
                pd.Timestamp("2026-07-22T16:00:00Z"),
                horizon,
            ],
            "symbol": ["BTCUSDT", "BTCUSDT"],
        }
    )
    client = SimpleNamespace(transaction_bars=lambda *args, **kwargs: full)
    lifecycle = resolve_contract_lifecycle(
        ("BTCUSDT",),
        {},
        full.iloc[[0]],
        full.iloc[0:0],
        replay_boundary=replay_boundary,
        client=client,
    )
    assert lifecycle["BTCUSDT"]["delivery_date"] == (
        horizon + pd.Timedelta(hours=8)
    ).isoformat()


def test_snapshot_payload_hashes_are_checked(monkeypatch: pytest.MonkeyPatch) -> None:
    real_sha256 = backtest.sha256_file

    def changed_parquet(path: str | Path) -> str:
        return "0" * 64 if Path(path).suffix == ".parquet" else real_sha256(path)

    monkeypatch.setattr(backtest, "sha256_file", changed_parquet)
    with pytest.raises(RuntimeError, match="snapshot hash drift"):
        backtest.load_frozen_snapshot()


def test_released_all_period_statistics_match_tournament() -> None:
    if not (release_team_root() / "daily_returns.csv").is_file():
        pytest.skip("local atomic tournament release is not present")
    statistics = period_statistics(load_released_daily_returns())
    assert statistics["is"]["observations"] == 1610
    assert statistics["historical_oos"]["observations"] == 730
    assert statistics["all_periods"]["observations"] == 2340
    assert statistics["is"]["cumulative_return"] == pytest.approx(
        0.7224897722169878, abs=1e-15
    )
    assert statistics["historical_oos"]["cumulative_return"] == pytest.approx(
        0.5244237275061574, abs=1e-15
    )
    assert statistics["all_periods"]["cumulative_return"] == pytest.approx(
        1.6258042791542535, abs=1e-15
    )
    naive = load_released_daily_returns()
    naive.index = naive.index.tz_localize(None)
    assert period_statistics(naive)["all_periods"]["observations"] == 2340


@pytest.mark.parity
def test_full_frozen_replay_is_exactly_golden() -> None:
    if not (release_team_root() / "targets.parquet").is_file():
        pytest.skip("local atomic tournament release is not present")
    replay = run_replay(
        load_frozen_snapshot(),
        cost_multipliers=(1.0,),
    )
    assert verify_historical_parity(replay)["status"] == "PASS"
