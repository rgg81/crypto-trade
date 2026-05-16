"""Tests for the fetch-spot CLI subcommand (iter-v3/086).

Verifies:
1. The subcommand is registered in build_parser() with the correct flags.
2. The microsecond-to-millisecond timestamp normalisation (_to_ms logic) —
   the load-bearing conversion documented in brief Section 3.2.
3. The --track v3 flag is accepted by the features subcommand.
4. _cmd_features routes to run_features_v3 when --track v3 is passed.
"""

from __future__ import annotations

import pytest

from crypto_trade.main import build_parser  # noqa: E402

# ---------------------------------------------------------------------------
# 1. fetch-spot subcommand registration
# ---------------------------------------------------------------------------


def test_fetch_spot_registered():
    """fetch-spot subcommand exists and accepts --symbols."""
    parser = build_parser()
    args = parser.parse_args(["fetch-spot", "--symbols", "BCHUSDT,LDOUSDT"])
    assert args.command == "fetch-spot"
    assert "BCHUSDT" in args.symbols
    assert "LDOUSDT" in args.symbols


def test_fetch_spot_default_interval():
    parser = build_parser()
    args = parser.parse_args(["fetch-spot", "--symbols", "BCHUSDT"])
    assert args.intervals == "8h"


def test_fetch_spot_custom_output_dir():
    parser = build_parser()
    args = parser.parse_args(
        ["fetch-spot", "--symbols", "BCHUSDT", "--output-dir", "/tmp/spot_test"]
    )
    assert args.output_dir == "/tmp/spot_test"


def test_fetch_spot_symbols_required():
    """fetch-spot --symbols is required (no default)."""
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["fetch-spot"])


# ---------------------------------------------------------------------------
# 2. Microsecond-to-millisecond normalisation (the load-bearing conversion)
# ---------------------------------------------------------------------------


def _to_ms_reference(val: int) -> int:
    """Mirror of the inline _to_ms inside _cmd_fetch_spot."""
    return val // 1000 if val >= 1_000_000_000_000_000 else val


def test_to_ms_millisecond_epoch_unchanged():
    """A 13-digit millisecond epoch must pass through unchanged."""
    ms_epoch = 1_735_689_600_000  # 2025-01-01 00:00:00 UTC in ms (13 digits)
    assert _to_ms_reference(ms_epoch) == ms_epoch


def test_to_ms_microsecond_epoch_converted():
    """A 16-digit microsecond epoch must be divided by 1000."""
    us_epoch = 1_735_689_600_000_000  # same instant in µs (16 digits)
    expected_ms = 1_735_689_600_000
    assert _to_ms_reference(us_epoch) == expected_ms


def test_to_ms_boundary():
    """The boundary: exactly 1e15 is treated as µs (>= threshold)."""
    assert _to_ms_reference(1_000_000_000_000_000) == 1_000_000_000_000


def test_to_ms_just_below_boundary():
    """Just below 1e15 is treated as ms."""
    val = 999_999_999_999_999
    assert _to_ms_reference(val) == val


def test_to_ms_converts_2025_jan_archive_epoch():
    """Spot archives from 2025-01 onward use µs. Verify the known 2025-01-01 epoch."""
    # 2025-01-01 00:00:00 UTC
    # ms:  1_735_689_600_000
    # µs:  1_735_689_600_000_000
    assert _to_ms_reference(1_735_689_600_000_000) == 1_735_689_600_000


# ---------------------------------------------------------------------------
# 3. --track v3 accepted by features subcommand
# ---------------------------------------------------------------------------


def test_features_track_v3_accepted():
    parser = build_parser()
    args = parser.parse_args(
        ["features", "--symbols", "BCHUSDT", "--interval", "8h", "--track", "v3"]
    )
    assert args.track == "v3"


def test_features_track_v3_not_default():
    parser = build_parser()
    args = parser.parse_args(["features", "--symbols", "BCHUSDT"])
    assert args.track == "v1"  # default unchanged


# ---------------------------------------------------------------------------
# 4. _cmd_features routes to run_features_v3 for --track v3
# ---------------------------------------------------------------------------


def test_cmd_features_v3_dispatches_to_features_v3():
    from unittest.mock import patch

    from crypto_trade.config import Settings
    from crypto_trade.main import _cmd_features

    settings = Settings(binance_api_key="", binance_api_secret="")
    parser = build_parser()
    args = parser.parse_args(
        [
            "features",
            "--symbols",
            "BCHUSDT,LDOUSDT,TRXUSDT",
            "--interval",
            "8h",
            "--format",
            "parquet",
            "--track",
            "v3",
        ]
    )
    with (
        patch("crypto_trade.features_v3.run_features_v3", return_value=[]) as v3_run,
        patch("crypto_trade.features_v3.list_groups", return_value=["regime"]),
        patch("crypto_trade.features_v2.run_features_v2") as v2_run,
        patch("crypto_trade.features.run_features") as v1_run,
    ):
        _cmd_features(args, settings)
        assert v3_run.call_count == 1
        assert v2_run.call_count == 0
        assert v1_run.call_count == 0
        call_kwargs = v3_run.call_args.kwargs
        assert set(call_kwargs["symbols"]) == {"BCHUSDT", "LDOUSDT", "TRXUSDT"}
        assert call_kwargs["output_dir"].endswith("features_v3")
