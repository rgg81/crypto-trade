"""Tests for `crypto_trade.live.db_seeder` (Option B — seed DB from backtest CSVs)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from crypto_trade.live.db_seeder import (
    _build_symbol_to_model,
    _resolve_cooldown_candles,
    seed_live_db_from_backtest,
)
from crypto_trade.live.models import (
    BASELINE_MODELS,
    COMBINED_MODELS,
    LiveConfig,
    ModelConfig,
    V2_BASELINE_MODELS,
)
from crypto_trade.live.state_store import StateStore


def _toy_trades_csv(path: Path, rows: list[dict]) -> None:
    cols = [
        "symbol",
        "direction",
        "entry_price",
        "exit_price",
        "weight_factor",
        "open_time",
        "close_time",
        "exit_reason",
        "pnl_pct",
        "fee_pct",
        "net_pnl_pct",
        "weighted_pnl",
    ]
    df = pd.DataFrame(rows)
    df = df[cols]
    df.to_csv(path, index=False)


def _row(
    symbol: str,
    direction: int,
    open_time: int,
    close_time: int,
    weight_factor: float = 1.0,
    exit_reason: str = "stop_loss",
) -> dict:
    return {
        "symbol": symbol,
        "direction": direction,
        "entry_price": 100.0,
        "exit_price": 95.0 if direction == 1 else 105.0,
        "weight_factor": weight_factor,
        "open_time": open_time,
        "close_time": close_time,
        "exit_reason": exit_reason,
        "pnl_pct": -5.0,
        "fee_pct": 0.1,
        "net_pnl_pct": -5.1,
        "weighted_pnl": -5.1 * weight_factor,
    }


def test_symbol_to_model_mapping():
    m = _build_symbol_to_model(COMBINED_MODELS)
    assert m["BTCUSDT"] == "A"
    assert m["ETHUSDT"] == "A"
    assert m["LINKUSDT"] == "C"
    assert m["LTCUSDT"] == "D"
    assert m["DOTUSDT"] == "E"
    assert m["DOGEUSDT"] == "V2-DOGE"
    assert m["NEARUSDT"] == "V2-NEAR"


def test_cooldown_candles_resolution():
    """v1 (cooldown_candles=None) falls back to LiveConfig (2). v2 uses 4."""
    live = LiveConfig()  # cooldown_candles=2
    cds = _resolve_cooldown_candles(COMBINED_MODELS, live)
    assert cds["A"] == 2
    assert cds["C"] == 2
    assert cds["D"] == 2
    assert cds["E"] == 2
    assert cds["V2-DOGE"] == 4
    assert cds["V2-SOL"] == 4
    assert cds["V2-XRP"] == 4
    assert cds["V2-NEAR"] == 4


def test_seed_inserts_trades_and_cooldown(tmp_path):
    """Basic happy path: seed BTC + DOGE, see them in DB + cooldown keys set."""
    v1_csv = tmp_path / "v1.csv"
    v2_csv = tmp_path / "v2.csv"
    _toy_trades_csv(
        v1_csv,
        [
            _row("BTCUSDT", 1, 1_000_000, 2_000_000),
            _row("BTCUSDT", -1, 3_000_000, 4_000_000, exit_reason="take_profit"),
            _row("LTCUSDT", -1, 1_500_000, 2_500_000),
        ],
    )
    _toy_trades_csv(
        v2_csv,
        [
            _row("DOGEUSDT", 1, 1_000_000, 2_000_000, weight_factor=0.5),
            _row("DOGEUSDT", 1, 5_000_000, 6_000_000, weight_factor=0.0),  # killed
        ],
    )

    db = tmp_path / "live.db"
    cfg = LiveConfig(models=COMBINED_MODELS)
    counts = seed_live_db_from_backtest(
        db, [v1_csv], [v2_csv], cfg, as_of_ms=None
    )

    assert counts["v1_closed"] == 3
    assert counts["v2_closed"] == 1
    assert counts["skipped_zero_weight"] == 1
    assert counts["v1_open"] == 0
    assert counts["v2_open"] == 0

    store = StateStore(db)
    all_trades = store.get_all_trades()
    assert len(all_trades) == 4
    by_sym = {t.symbol for t in all_trades}
    assert by_sym == {"BTCUSDT", "LTCUSDT", "DOGEUSDT"}

    # Cooldown keys per (model, symbol) — latest close_time + cooldown_candles*8h
    btc_key = store.get_state("cooldown_A_BTCUSDT")
    assert btc_key is not None
    # Latest BTC close was 4_000_000, cooldown_candles=2 → +2*28_800_000 = 61_600_000
    assert int(btc_key) == 4_000_000 + 2 * 28_800_000

    ltc_key = store.get_state("cooldown_D_LTCUSDT")
    assert ltc_key is not None
    assert int(ltc_key) == 2_500_000 + 2 * 28_800_000

    # v2 cooldown_candles=4
    doge_key = store.get_state("cooldown_V2-DOGE_DOGEUSDT")
    assert doge_key is not None
    assert int(doge_key) == 2_000_000 + 4 * 28_800_000


def test_seed_as_of_seeds_open_at_cutoff_as_closed(tmp_path):
    """Trades that opened before as_of_ms are seeded as 'closed' with their full
    CSV close info — even if their close_time falls after as_of. This keeps
    cum_weighted_pnl / VT state correct when the live engine takes over at
    catch-up start. Trades that opened after as_of are skipped."""
    v1_csv = tmp_path / "v1.csv"
    _toy_trades_csv(
        v1_csv,
        [
            _row("BTCUSDT", 1, 1_000_000, 2_000_000),  # closed before cutoff
            _row("BTCUSDT", -1, 3_000_000, 5_000_000),  # spans cutoff (open<cutoff<close)
            _row("BTCUSDT", 1, 6_000_000, 7_000_000),  # opens after cutoff — skipped
        ],
    )

    db = tmp_path / "live.db"
    cfg = LiveConfig(models=BASELINE_MODELS)
    counts = seed_live_db_from_backtest(
        db, [v1_csv], [], cfg, as_of_ms=4_000_000
    )

    assert counts["v1_closed"] == 2  # both pre-cutoff opens, both seeded closed
    assert counts["v1_open"] == 0
    assert counts["skipped_after_cutoff"] == 1

    store = StateStore(db)
    closed = [t for t in store.get_all_trades() if t.status == "closed"]
    assert len(closed) == 2
    # The trade that spanned the cutoff carries its real exit info
    spanning = [t for t in closed if t.open_time == 3_000_000][0]
    assert spanning.exit_time == 5_000_000
    assert spanning.exit_price == 105.0
    assert spanning.exit_reason == "stop_loss"


def test_seed_skips_unknown_symbols(tmp_path):
    """A symbol not in any ModelConfig is skipped without raising."""
    v1_csv = tmp_path / "v1.csv"
    _toy_trades_csv(
        v1_csv,
        [
            _row("BTCUSDT", 1, 1_000_000, 2_000_000),
            _row("BNBUSDT", 1, 1_000_000, 2_000_000),  # old v1 baseline (replaced by LTC)
        ],
    )
    db = tmp_path / "live.db"
    cfg = LiveConfig(models=BASELINE_MODELS)
    counts = seed_live_db_from_backtest(db, [v1_csv], [], cfg)
    assert counts["v1_closed"] == 1
    assert counts["skipped_unknown_symbol"] == 1


def test_seed_then_rebuild_state_matches(tmp_path):
    """After seeding, _rebuild_risk_state should reconstruct the same R2 cum/peak the seeder
    produced from the backtest's weighted_pnl values.
    """
    from crypto_trade.live.engine import LiveEngine

    v1_csv = tmp_path / "v1.csv"
    # 3 DOT trades to populate R2 (Model E enables R2)
    _toy_trades_csv(
        v1_csv,
        [
            # Profitable opener — peak goes up
            {
                "symbol": "DOTUSDT", "direction": 1,
                "entry_price": 5.0, "exit_price": 5.50,
                "weight_factor": 1.0,
                "open_time": 1_000_000, "close_time": 2_000_000,
                "exit_reason": "take_profit",
                "pnl_pct": 10.0, "fee_pct": 0.1, "net_pnl_pct": 9.9,
                "weighted_pnl": 9.9,
            },
            # Loss — cum drops, dd opens
            {
                "symbol": "DOTUSDT", "direction": -1,
                "entry_price": 5.0, "exit_price": 5.40,
                "weight_factor": 1.0,
                "open_time": 3_000_000, "close_time": 4_000_000,
                "exit_reason": "stop_loss",
                "pnl_pct": -8.0, "fee_pct": 0.1, "net_pnl_pct": -8.1,
                "weighted_pnl": -8.1,
            },
            # Another loss
            {
                "symbol": "DOTUSDT", "direction": 1,
                "entry_price": 5.0, "exit_price": 4.75,
                "weight_factor": 1.0,
                "open_time": 5_000_000, "close_time": 6_000_000,
                "exit_reason": "stop_loss",
                "pnl_pct": -5.0, "fee_pct": 0.1, "net_pnl_pct": -5.1,
                "weighted_pnl": -5.1,
            },
        ],
    )
    # Use dry_run.db because LiveEngine (with dry_run=True) reads from
    # data_dir/dry_run.db regardless of the configured db_path.
    db = tmp_path / "dry_run.db"
    cfg = LiveConfig(models=BASELINE_MODELS, dry_run=True, db_path=db, data_dir=tmp_path)
    seed_live_db_from_backtest(db, [v1_csv], [], cfg)

    # Spin up an engine so its _rebuild_risk_state runs over the seeded rows
    engine = LiveEngine(cfg)
    engine._rebuild_risk_state()
    # Model E has R2 enabled. Expect:
    #   cum  = 9.9 - 8.1 - 5.1 = -3.3
    #   peak = max(0, 9.9, 9.9-8.1, -3.3) = 9.9 (high water after first trade)
    #   dd   = 9.9 - (-3.3) = 13.2
    assert engine._cum_weighted_pnl["E"] == pytest.approx(-3.3, abs=1e-9)
    assert engine._peak_weighted_pnl["E"] == pytest.approx(9.9, abs=1e-9)
