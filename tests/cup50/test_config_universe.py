from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup50.availability import load_unavailability_audit, unavailable_symbols
from crypto_trade.cup50.config import IS_START, OOS_END, OOS_START, load_config
from crypto_trade.cup50.universe import (
    assert_append_invariant,
    build_membership,
    canonical_daily_quote_volume,
    classify_current_exchange_contracts,
    derive_listing_episodes,
    episode_eligibility,
    members_at,
    pure_crypto_symbols,
)


def test_current_exchange_classification_is_positive_and_archive_inference_fails_closed() -> None:
    metadata = pd.DataFrame(
        [
            {
                "symbol": "BTCUSDT",
                "contract_type": "PERPETUAL",
                "quote_asset": "USDT",
                "margin_asset": "USDT",
                "underlying_type": "COIN",
                "metadata_source": "current_exchangeInfo",
            },
            {
                "symbol": "OLDUSDT",
                "contract_type": "PERPETUAL",
                "quote_asset": "USDT",
                "margin_asset": "USDT",
                "underlying_type": "ARCHIVE_INFERRED_COIN",
                "metadata_source": "archive_inference",
            },
            {
                "symbol": "AMZNUSDT",
                "contract_type": "TRADIFI_PERPETUAL",
                "quote_asset": "USDT",
                "margin_asset": "USDT",
                "underlying_type": "EQUITY",
                "metadata_source": "current_exchangeInfo",
            },
        ]
    )
    classified = classify_current_exchange_contracts(metadata)
    assert classified["classification"].tolist() == ["crypto", "unknown", "unknown"]
    assert pure_crypto_symbols(classified) == frozenset({"BTCUSDT"})
    reviewed = classify_current_exchange_contracts(
        metadata, historical_classifications={"OLDUSDT": "crypto"}
    )
    assert pure_crypto_symbols(reviewed) == frozenset({"BTCUSDT", "OLDUSDT"})


def _bars(symbols: list[str], start: str, days: int) -> pd.DataFrame:
    rows = []
    for day in pd.date_range(start, periods=days, freq="D", tz="UTC"):
        for symbol_number, symbol in enumerate(symbols):
            for hour in (0, 8, 16):
                opened = day + pd.Timedelta(hours=hour)
                rows.append(
                    {
                        "open_time": opened,
                        "close_time": opened + pd.Timedelta(hours=8) - pd.Timedelta(milliseconds=1),
                        "symbol": symbol,
                        "quote_volume": float(1000 - symbol_number),
                    }
                )
    return pd.DataFrame(rows)


def test_frozen_config_and_exact_window() -> None:
    loaded = load_config("tournament/cup50/config.toml")
    assert loaded.raw["universe"]["target_size"] == 50
    assert loaded.raw["research"]["strategy_history_days"] == 180
    assert IS_START == pd.Timestamp("2021-03-15T00:00:00Z")
    assert OOS_START == pd.Timestamp("2024-02-01T00:00:00Z")
    assert OOS_END == pd.Timestamp("2026-08-01T00:00:00Z")


def test_frozen_unavailability_audit_is_half_open_and_canonical() -> None:
    windows = load_unavailability_audit("tournament/cup50/historical-unavailability.json")
    assert len(windows) == 5
    assert unavailable_symbols(windows, pd.Timestamp("2022-05-13T08:00:00Z")) == {
        "LUNAUSDT"
    }
    assert unavailable_symbols(windows, pd.Timestamp("2022-05-16T00:00:00Z")) == set()
    with pytest.raises(ValueError, match="canonical 8h boundaries"):
        load_unavailability_audit(
            {
                "schema_version": 1,
                "namespace": "cup50",
                "policy_id": "causal-no-replacement-unavailability-v1",
                "freeze_phase": "pre-activation-before-feedback",
                "windows": [
                    {
                        "symbol": "AUSDT",
                        "start": "2024-01-01T00:01:00Z",
                        "end": "2024-01-01T08:00:00Z",
                        "reason": "test",
                    }
                ],
            }
        )


def test_team_visible_is_unavailability_audit_has_no_oos_window() -> None:
    windows = load_unavailability_audit("tournament/cup50/is-unavailability.json")
    assert [window.symbol for window in windows] == [
        "ICPUSDT",
        "LUNAUSDT",
        "TLMUSDT",
        "TOMOUSDT",
    ]
    assert all(window.end <= OOS_START for window in windows)


def test_complete_days_and_lexical_ties_without_hysteresis() -> None:
    symbols = [f"S{number:02d}USDT" for number in range(51)]
    bars = _bars(symbols, "2024-01-01", 181)
    # Force all medians to tie. Lexicographic order alone selects the first 50.
    bars["quote_volume"] = 1.0
    volume = canonical_daily_quote_volume(bars)
    boundary = pd.Timestamp("2024-06-30T00:00:00Z")
    eligible = pd.DataFrame(True, index=[boundary], columns=symbols)
    membership = build_membership(
        volume,
        eligible=eligible,
        reconstitution_times=[boundary],
        lookback_days=180,
        target_size=50,
    )
    assert list(membership["symbol"]) == sorted(symbols)[:50]

    # One missing canonical bar makes that entire symbol/day incomplete.
    damaged_row = bars.index[
        (bars["symbol"] == symbols[0])
        & (bars["open_time"].dt.normalize() == boundary - pd.Timedelta(days=1))
        & (bars["open_time"].dt.hour == 8)
    ][0]
    damaged = bars.drop(damaged_row)
    damaged_volume = canonical_daily_quote_volume(damaged)
    damaged_membership = build_membership(
        damaged_volume,
        eligible=eligible,
        reconstitution_times=[boundary],
        lookback_days=180,
        target_size=50,
    )
    assert symbols[0] not in set(damaged_membership["symbol"])


def test_boundary_day_is_excluded() -> None:
    symbols = ["AUSDT", "BUSDT"]
    bars = _bars(symbols, "2024-01-01", 181)
    boundary = pd.Timestamp("2024-06-30T00:00:00Z")
    bars.loc[
        (bars["symbol"] == "BUSDT") & (bars["open_time"].dt.normalize() == boundary),
        "quote_volume",
    ] = 1e30
    volume = canonical_daily_quote_volume(bars)
    eligible = pd.DataFrame(True, index=[boundary], columns=symbols)
    result = build_membership(
        volume,
        eligible=eligible,
        reconstitution_times=[boundary],
        lookback_days=180,
        target_size=1,
    )
    assert result.iloc[0]["symbol"] == "AUSDT"


def test_pure_crypto_fails_unknown_and_non_crypto_closed() -> None:
    metadata = pd.DataFrame(
        [
            ["BTCUSDT", "PERPETUAL", "USDT", "USDT", "native-crypto"],
            ["USDCUSDT", "PERPETUAL", "USDT", "USDT", "stablecoin"],
            ["MYSTERYUSDT", "PERPETUAL", "USDT", "USDT", "unknown"],
            ["BADMARGIN", "PERPETUAL", "USDT", "BTC", "crypto"],
            ["BTCUPUSDT", "PERPETUAL", "USDT", "USDT", "native-crypto"],
            ["FDUSDUSDT", "PERPETUAL", "USDT", "USDT", "native-crypto"],
        ],
        columns=["symbol", "contract_type", "quote_asset", "margin_asset", "classification"],
    )
    assert pure_crypto_symbols(metadata) == {"BTCUSDT"}


def test_listing_episodes_are_archive_derived() -> None:
    bars = _bars(["AUSDT"], "2024-01-01", 2)
    later = _bars(["AUSDT"], "2024-01-10", 1)
    episodes = derive_listing_episodes(pd.concat([bars, later], ignore_index=True))
    assert len(episodes) == 2
    assert episodes[1].start == pd.Timestamp("2024-01-10T00:00:00Z")


def test_zero_trade_placeholders_split_episodes_and_relisting_requires_full_lookback() -> None:
    first = _bars(["AUSDT"], "2024-01-01", 2)
    placeholders = _bars(["AUSDT"], "2024-01-03", 2)
    placeholders["quote_volume"] = 0.0
    relisted = _bars(["AUSDT"], "2024-01-05", 2)
    episodes = derive_listing_episodes(
        pd.concat([first, placeholders, relisted], ignore_index=True)
    )
    assert len(episodes) == 2
    boundaries = [
        pd.Timestamp("2024-01-03T00:00:00Z"),
        pd.Timestamp("2024-01-04T00:00:00Z"),
        pd.Timestamp("2024-01-06T00:00:00Z"),
    ]
    eligibility = episode_eligibility(episodes, boundaries, lookback_days=1)
    assert eligibility["AUSDT"].tolist() == [True, False, True]


def test_daily_volume_ignores_corrupted_rows_after_frozen_end() -> None:
    bars = _bars(["AUSDT"], "2024-01-01", 2)
    end = pd.Timestamp("2024-01-03T00:00:00Z")
    future = pd.DataFrame([[end, "corrupt-future-time", "AUSDT", np.nan]], columns=bars.columns)
    expected = canonical_daily_quote_volume(bars, end=end)
    observed = canonical_daily_quote_volume(pd.concat([bars, future], ignore_index=True), end=end)
    pd.testing.assert_frame_equal(expected, observed, check_exact=True)


def test_membership_append_invariance_detects_rewrite() -> None:
    before = pd.DataFrame(
        [[pd.Timestamp("2024-01-01T00:00:00Z"), "A", 1, 10.0]],
        columns=(
            "reconstitution_time",
            "symbol",
            "liquidity_rank",
            "median_daily_quote_volume",
        ),
    )
    after = pd.concat(
        [
            before,
            pd.DataFrame(
                [[pd.Timestamp("2024-01-08T00:00:00Z"), "B", 1, 11.0]],
                columns=before.columns,
            ),
        ],
        ignore_index=True,
    )
    assert_append_invariant(before, after, cutoff=pd.Timestamp("2024-01-08T00:00:00Z"))
    corrupted = after.copy()
    corrupted.loc[0, "median_daily_quote_volume"] = np.nextafter(10.0, 11.0)
    with pytest.raises(AssertionError):
        assert_append_invariant(before, corrupted, cutoff=pd.Timestamp("2024-01-08T00:00:00Z"))


def test_last_january_membership_is_active_at_february_holdout_start() -> None:
    membership = pd.DataFrame(
        [
            [pd.Timestamp("2024-01-29T00:00:00Z"), "A", 1, 10.0],
            [pd.Timestamp("2024-02-05T00:00:00Z"), "B", 1, 11.0],
        ],
        columns=(
            "reconstitution_time",
            "symbol",
            "liquidity_rank",
            "median_daily_quote_volume",
        ),
    )
    assert members_at(membership, pd.Timestamp("2024-02-01T00:00:00Z")) == ("A",)
