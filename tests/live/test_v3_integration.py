"""iter-v3/132 live-integration tests.

Covers (per the plan at /home/roberto/.claude/plans/piped-jingling-haven.md
Phase 7):

1. V3_BASELINE_MODELS configuration correctness (Phase 1)
2. ModelConfig per-model no_confirm fields (Phase 1)
3. features_v3 cache invalidation (Phase 2)
4. live/data_pipeline v3 dispatch (Phase 2)
5. _refresh_groups v3 track (Phase 3)
6. _defer_xsymbol_if_btc_lagging v3 coverage (Phase 3)
7. ModelRunner v3 wrapper (Phase 4)
8. evaluate_order_with_no_confirm shared helper (Phase 5a)
9. trade_to_order no_confirm derivation (Phase 5c)
10. check_dry_run_exit no_confirm threading (Phase 5b/c)
11. OrderManager.check_no_confirm_exit real-mode method (Phase 5d)
12. seed_live_db_from_backtest --v3-trades support (Phase 6)

PRIMARY parity test (backtest reproduction at byte-equal /121) is run as
a separate full-cycle backtest reproduction outside the pytest suite;
see CLAUDE.md "v3 live deploy walkthrough" section.

Test style note (PR #3 reviewer feedback): structural checks below prefer
``inspect.signature`` (parameter introspection — refactor-stable) and
``isinstance`` / ``hasattr`` (object introspection) over
``inspect.getsource`` string matching. Where ``inspect.getsource`` is
still used (e.g. asserting one method is called *after* another inside
``_tick``), the failure mode is documented in the test docstring and
behavioral coverage exists elsewhere:
  - v3 BTC-lag deferral covered behaviorally in
    ``tests/live/test_btc_lag_defer.py::test_v3_symbol_deferred_when_btc_lags``.
  - v2-alias delegation covered behaviorally by
    ``tests/live/test_btc_lag_defer.py::test_back_compat_alias_dispatches_to_xsymbol_helper``.
"""

from __future__ import annotations

from pathlib import Path

from crypto_trade.backtest import evaluate_order_with_no_confirm
from crypto_trade.backtest_models import Order

# ----- Phase 1: V3_BASELINE_MODELS configuration -----


def test_v3_baseline_models_shape() -> None:
    """V3_BASELINE_MODELS contains 3 models pinned to iter-v3/121 canonical."""
    from crypto_trade.live.models import V3_BASELINE_MODELS

    assert len(V3_BASELINE_MODELS) == 3
    names = sorted(mc.name for mc in V3_BASELINE_MODELS)
    assert names == ["V3-BCH", "V3-LDO", "V3-TRX"]
    symbols = sorted(mc.symbols[0] for mc in V3_BASELINE_MODELS)
    assert symbols == ["BCHUSDT", "LDOUSDT", "TRXUSDT"]


def test_v3_baseline_models_feature_count() -> None:
    """V3 uses the 14-feature V3_FEATURE_COLUMNS_TOP_N stack."""
    from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N
    from crypto_trade.live.models import V3_BASELINE_MODELS

    for mc in V3_BASELINE_MODELS:
        assert len(mc.feature_columns) == 14
        assert mc.feature_columns == V3_FEATURE_COLUMNS_TOP_N


def test_v3_baseline_models_ensemble_seeds() -> None:
    """V3 uses 10-seed unified ensemble (outer=42 + outer=123 lineages)."""
    from crypto_trade.live.models import V3_BASELINE_MODELS

    for mc in V3_BASELINE_MODELS:
        assert len(mc.ensemble_seeds) == 10
        # First 5 = outer=42 lineage; matches run_baseline_v3.py ENSEMBLE_SEEDS
        assert mc.ensemble_seeds[0] == 191664963
        assert mc.ensemble_seeds[4] == 929893137


def test_v3_baseline_no_confirm_enabled() -> None:
    """V3 has /116 no_confirm primitive enabled at /121 baseline params."""
    from crypto_trade.live.models import V3_BASELINE_MODELS

    for mc in V3_BASELINE_MODELS:
        assert mc.enable_no_confirm_exit is True
        assert mc.no_confirm_trigger_atr == 0.50
        assert mc.no_confirm_k_candles == 4


def test_v3_baseline_drawdown_axes_closed() -> None:
    """V3 has /127 brake + /129 scaling DISABLED (axes CLOSED)."""
    from crypto_trade.live.models import V3_BASELINE_MODELS

    for mc in V3_BASELINE_MODELS:
        assert mc.risk_v2_config is not None
        cfg = mc.risk_v2_config
        assert cfg.enable_per_symbol_drawdown_brake is False
        assert cfg.enable_per_symbol_drawdown_scaling is False


def test_v3_baseline_training_hyperparams() -> None:
    """V3 overrides training_months=24, n_trials=35 (vs LiveConfig defaults 24/50)."""
    from crypto_trade.live.models import V3_BASELINE_MODELS

    for mc in V3_BASELINE_MODELS:
        assert mc.training_months == 24
        assert mc.n_trials == 35
        assert mc.cv_splits == 5


def test_v3_baseline_atr_multipliers() -> None:
    """V3 uses (2.0, 1.0) ATR multipliers (/121 DEFAULT_ATR_MULTIPLIERS)."""
    from crypto_trade.live.models import V3_BASELINE_MODELS

    for mc in V3_BASELINE_MODELS:
        assert mc.atr_tp_multiplier == 2.0
        assert mc.atr_sl_multiplier == 1.0


def test_v3_baseline_risk_wrapper_value() -> None:
    """risk_wrapper Literal extended to include 'v3'."""
    from crypto_trade.live.models import V3_BASELINE_MODELS

    for mc in V3_BASELINE_MODELS:
        assert mc.risk_wrapper == "v3"


# ----- Phase 2: features_v3 cache invalidation -----


def test_clear_btc_cache_v3_resets_to_none() -> None:
    """clear_btc_cache_v3() sets _BTC_CACHE_V3 back to None."""
    # Prime the cache with a placeholder DataFrame
    import pandas as pd

    import crypto_trade.features_v3.cross_btc_v3 as cb

    cb._BTC_CACHE_V3 = pd.DataFrame({"open_time": [1, 2, 3]})
    assert cb._BTC_CACHE_V3 is not None
    cb.clear_btc_cache_v3()
    assert cb._BTC_CACHE_V3 is None


def test_clear_eth_cache_v3_resets_to_none() -> None:
    """clear_eth_cache_v3() sets _ETH_CACHE_V3 back to None."""
    import pandas as pd

    import crypto_trade.features_v3.cross_btc_v3 as cb

    cb._ETH_CACHE_V3 = pd.DataFrame({"open_time": [1, 2, 3]})
    assert cb._ETH_CACHE_V3 is not None
    cb.clear_eth_cache_v3()
    assert cb._ETH_CACHE_V3 is None


def test_run_features_v3_clears_caches_at_entry() -> None:
    """run_features_v3 must call both cache-clear functions at the top.

    Source-inspection test: assertion at function body level prevents the
    'live tick #2 sees stale cross-asset frames' regression (commit 62d56dc).
    """
    import inspect

    from crypto_trade.features_v3 import run_features_v3

    src = inspect.getsource(run_features_v3)
    assert "clear_btc_cache_v3()" in src
    assert "clear_eth_cache_v3()" in src


# ----- Phase 2: data_pipeline v3 dispatch -----


def test_refresh_features_by_track_dispatches_v3() -> None:
    """refresh_features_by_track recognises track='v3' and routes to features_v3."""
    import inspect

    from crypto_trade.live.data_pipeline import refresh_features_by_track

    src = inspect.getsource(refresh_features_by_track)
    assert 'track == "v3"' in src
    assert "run_features_v3" in src


# ----- Phase 3: _refresh_groups + _defer_xsymbol_if_btc_lagging -----


def test_engine_defer_xsymbol_method_exists() -> None:
    """``_defer_xsymbol_if_btc_lagging`` method is present + signed correctly.

    Behavioral coverage for the v2+v3 risk_wrapper filter and the
    ``xsymbol_deferred_btc_lag`` decision_log payload lives in
    ``tests/live/test_btc_lag_defer.py`` (real engine + mocked refresh +
    deferral assertions). This test just guards the public surface.
    """
    import inspect

    from crypto_trade.live.engine import LiveEngine

    assert hasattr(LiveEngine, "_defer_xsymbol_if_btc_lagging")
    sig = inspect.signature(LiveEngine._defer_xsymbol_if_btc_lagging)
    assert {"self", "new_candles"}.issubset(sig.parameters)


def test_engine_refresh_groups_emits_v3_track() -> None:
    """_refresh_groups returns a v3 entry when a v3 model is configured.

    Behavioral check: instantiate ``LiveEngine`` with the V3-BCH baseline
    model and assert ``_refresh_groups`` produces a ('v3', ...) tuple.
    """
    from crypto_trade.live.engine import LiveEngine
    from crypto_trade.live.models import V3_BASELINE_MODELS, LiveConfig

    bch_only = tuple(m for m in V3_BASELINE_MODELS if m.symbols == ("BCHUSDT",))
    # Engine needs a BTC kline CSV for the init-time trend-filter sanity check.
    import pandas as pd

    btc_dir = Path(__file__).parent / "_tmp_refresh_groups_btc"
    btc_dir.mkdir(parents=True, exist_ok=True)
    btc_csv = btc_dir / "BTCUSDT" / "8h.csv"
    btc_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "open_time": 1_700_000_000_000,
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1000.0,
                "close_time": 1_700_000_000_000 + 8 * 3600 * 1000 - 1,
                "quote_asset_volume": 1.0,
                "number_of_trades": 1,
                "taker_buy_base_asset_volume": 1.0,
                "taker_buy_quote_asset_volume": 1.0,
                "ignore": 0,
            }
        ]
    ).to_csv(btc_csv, index=False)
    try:
        cfg = LiveConfig(
            data_dir=btc_dir,
            features_dir=btc_dir / "features",
            models=bch_only,
            db_path=btc_dir / "engine.db",
        )
        engine = LiveEngine(cfg)
        groups = engine._refresh_groups(("BCHUSDT",))
        tracks = [g[2] for g in groups]
        assert "v3" in tracks
    finally:
        import shutil

        shutil.rmtree(btc_dir, ignore_errors=True)


def test_engine_v2_alias_method_exists() -> None:
    """``_defer_v2_if_btc_lagging`` alias still present for back-compat.

    Behavioral dispatch through the alias is tested in
    ``test_btc_lag_defer.py::test_back_compat_alias_dispatches_to_xsymbol_helper``.
    """
    from crypto_trade.live.engine import LiveEngine

    assert hasattr(LiveEngine, "_defer_v2_if_btc_lagging")


# ----- Phase 4: ModelRunner v3 wrapper -----


def test_modelrunner_v3_wraps_inner_in_risk_v3_wrapper() -> None:
    """ModelRunner wraps a v3 ModelConfig's strategy in RiskV3Wrapper.

    Behavioral check: instantiate ModelRunner with a V3 baseline model and
    assert ``runner.strategy`` is a RiskV3Wrapper (subclass of RiskV2Wrapper).
    Reformatting ModelRunner.__init__ won't break this — only changing the
    wrapper class will, which IS the contract under test.
    """
    from crypto_trade.live.engine import ModelRunner
    from crypto_trade.live.models import V3_BASELINE_MODELS, LiveConfig
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy
    from crypto_trade.strategies.ml.risk_v3 import RiskV3Wrapper

    bch_model = next(m for m in V3_BASELINE_MODELS if m.symbols == ("BCHUSDT",))
    live_cfg = LiveConfig(models=(bch_model,))
    runner = ModelRunner(bch_model, live_cfg)
    assert isinstance(runner.strategy, RiskV3Wrapper)
    # Inner strategy access used elsewhere should still resolve through wrapper.
    assert isinstance(runner.inner_strategy, LightGbmStrategy)


# ----- Phase 5a: evaluate_order_with_no_confirm shared helper -----


def _make_order(
    direction: int,
    entry: float,
    stop_loss: float,
    take_profit: float,
    *,
    open_time: int = 0,
    timeout_time: int = 10**13,
    arm_time: int = 0,
    threshold_price: float = 0.0,
) -> Order:
    return Order(
        symbol="BCHUSDT",
        direction=direction,
        entry_price=entry,
        amount_usd=100.0,
        weight_factor=1.0,
        stop_loss_price=stop_loss,
        take_profit_price=take_profit,
        open_time=open_time,
        timeout_time=timeout_time,
        no_confirm_arm_time=arm_time,
        no_confirm_threshold_price=threshold_price,
    )


def test_evaluate_no_confirm_disabled_falls_through_to_check_order() -> None:
    """When enable_no_confirm=False, behaves identically to bare check_order."""
    order = _make_order(direction=1, entry=300.0, stop_loss=297.0, take_profit=306.0)
    state: dict = {}
    # No SL/TP hit, no timeout — should return None
    result = evaluate_order_with_no_confirm(
        order,
        1000,
        300.0,
        301.0,
        299.5,
        300.5,
        28_800_000,
        fee_pct=0.1,
        enable_no_confirm=False,
        no_confirm_state=state,
        state_key=id(order),
    )
    assert result is None


def test_evaluate_no_confirm_favorable_excursion_updates_state() -> None:
    """When favorable excursion reaches threshold, state flips to True."""
    order = _make_order(
        direction=1,
        entry=300.0,
        stop_loss=297.0,
        take_profit=306.0,
        arm_time=1000 + 4 * 28_800_000,  # K=4 candles
        threshold_price=301.5,  # 0.50 * 1.0% above entry
    )
    state: dict = {}
    # Candle 1: high=302 (above threshold 301.5) → confirmed=True
    result = evaluate_order_with_no_confirm(
        order,
        1000 + 28_800_000,  # ot of bar 2
        300.5,
        302.0,
        300.0,
        301.5,
        1000 + 2 * 28_800_000,  # ct of bar 2
        fee_pct=0.1,
        enable_no_confirm=True,
        no_confirm_state=state,
        state_key=id(order),
    )
    assert result is None  # not yet at arm_time, no exit
    assert state.get(id(order)) is True  # but excursion confirmed state


def test_evaluate_no_confirm_fires_at_arm_time_when_unconfirmed() -> None:
    """If arm_time elapsed AND favorable excursion never reached → no_confirm exit."""
    order = _make_order(
        direction=1,
        entry=300.0,
        stop_loss=297.0,
        take_profit=306.0,
        arm_time=1000 + 4 * 28_800_000,
        threshold_price=301.5,
    )
    state: dict = {}
    # Iterate 4 candles where high never reaches 301.5
    ct_at_arm = 1000 + 4 * 28_800_000
    # Final call: candle close_time exactly at arm_time
    result = evaluate_order_with_no_confirm(
        order,
        ct_at_arm - 28_800_000,  # ot of arm candle
        300.5,
        301.0,  # high < 301.5 (threshold) → still unconfirmed
        300.2,
        300.7,  # close
        ct_at_arm,
        fee_pct=0.1,
        enable_no_confirm=True,
        no_confirm_state=state,
        state_key=id(order),
    )
    assert result is not None
    assert result.exit_reason == "no_confirm"
    assert result.exit_price == 300.7  # closed at candle close
    assert id(order) not in state  # state popped on close


def test_evaluate_no_confirm_tp_wins_over_no_confirm_same_bar() -> None:
    """Same-bar precedence: TP wins over no_confirm if both would fire."""
    order = _make_order(
        direction=1,
        entry=300.0,
        stop_loss=297.0,
        take_profit=306.0,
        arm_time=1000 + 4 * 28_800_000,
        threshold_price=301.5,
    )
    state: dict = {}
    ct_at_arm = 1000 + 4 * 28_800_000
    # Candle hits TP (high=307) on the arm_time candle → TP wins
    result = evaluate_order_with_no_confirm(
        order,
        ct_at_arm - 28_800_000,
        300.5,
        307.0,  # TP hit
        300.0,
        306.5,
        ct_at_arm,
        fee_pct=0.1,
        enable_no_confirm=True,
        no_confirm_state=state,
        state_key=id(order),
    )
    assert result is not None
    assert result.exit_reason == "take_profit"
    assert id(order) not in state


# ----- Phase 5c: trade_to_order no_confirm derivation -----


def test_trade_to_order_back_compat_no_no_confirm() -> None:
    """When kwargs not passed, Order has no_confirm fields at 0/0.0."""
    from crypto_trade.live.models import LiveTrade
    from crypto_trade.live.order_manager import trade_to_order

    trade = LiveTrade(
        id="t1",
        symbol="BCHUSDT",
        direction=1,
        entry_price=300.0,
        stop_loss_price=297.0,
        take_profit_price=306.0,
        open_time=1000,
        timeout_time=99999,
    )
    o = trade_to_order(trade)
    assert o.no_confirm_arm_time == 0
    assert o.no_confirm_threshold_price == 0.0


def test_trade_to_order_derives_no_confirm_long() -> None:
    """Long trade no_confirm derivation matches backtest.create_order formula."""
    from crypto_trade.live.models import LiveTrade
    from crypto_trade.live.order_manager import trade_to_order

    trade = LiveTrade(
        id="t1",
        symbol="BCHUSDT",
        direction=1,
        entry_price=300.0,
        stop_loss_price=297.0,  # sl_pct = 0.01
        take_profit_price=306.0,
        open_time=1000,
        timeout_time=99999,
    )
    o = trade_to_order(
        trade,
        enable_no_confirm=True,
        no_confirm_trigger_atr=0.50,
        no_confirm_k_candles=4,
        interval_ms=28_800_000,
    )
    assert o.no_confirm_arm_time == 1000 + 4 * 28_800_000
    # threshold = 300 * (1 + 0.50 * 0.01) = 301.5
    assert abs(o.no_confirm_threshold_price - 301.5) < 1e-9


def test_trade_to_order_derives_no_confirm_short() -> None:
    """Short trade no_confirm derivation uses (1 - trigger_atr * sl_pct)."""
    from crypto_trade.live.models import LiveTrade
    from crypto_trade.live.order_manager import trade_to_order

    trade = LiveTrade(
        id="t2",
        symbol="LDOUSDT",
        direction=-1,
        entry_price=2.00,
        stop_loss_price=2.04,  # sl_pct = 0.02
        take_profit_price=1.92,
        open_time=2000,
        timeout_time=99999,
    )
    o = trade_to_order(
        trade,
        enable_no_confirm=True,
        no_confirm_trigger_atr=0.50,
        no_confirm_k_candles=4,
        interval_ms=28_800_000,
    )
    assert o.no_confirm_arm_time == 2000 + 4 * 28_800_000
    # threshold = 2.0 * (1 - 0.50 * 0.02) = 1.98
    assert abs(o.no_confirm_threshold_price - 1.98) < 1e-9


# ----- Phase 5b/c: check_dry_run_exit no_confirm threading -----


def test_check_dry_run_exit_no_confirm_kwarg_back_compat() -> None:
    """check_dry_run_exit signature accepts the no_confirm kwargs introduced
    in iter-v3/132 for v3 paper-trade evaluation (Phase 5b/c).

    Signature-level check is refactor-stable: ruff formatting, comment edits,
    and helper extractions can't break it. Only removing the kwarg can.
    """
    import inspect

    from crypto_trade.live.order_manager import OrderManager

    sig = inspect.signature(OrderManager.check_dry_run_exit)
    assert "enable_no_confirm" in sig.parameters
    assert "no_confirm_state" in sig.parameters


# ----- Phase 5d: real-mode check_no_confirm_exit -----


def test_check_no_confirm_exit_method_exists() -> None:
    """OrderManager.check_no_confirm_exit method is present and signed correctly."""
    import inspect

    from crypto_trade.live.order_manager import OrderManager

    assert hasattr(OrderManager, "check_no_confirm_exit")
    sig = inspect.signature(OrderManager.check_no_confirm_exit)
    params = set(sig.parameters)
    expected = {
        "self",
        "trade",
        "candle_high",
        "candle_low",
        "candle_close",
        "candle_close_time",
        "no_confirm_trigger_atr",
        "no_confirm_k_candles",
        "interval_ms",
        "no_confirm_state",
        "model_name",
    }
    assert expected.issubset(params)


def test_check_no_confirm_exit_skips_paper_trades() -> None:
    """Paper trades go through check_dry_run_exit; this method must skip them."""
    import inspect

    from crypto_trade.live.order_manager import OrderManager

    src = inspect.getsource(OrderManager.check_no_confirm_exit)
    assert "is_paper_trade(trade)" in src


def test_engine_real_no_confirm_runs_after_check_exchange_exits() -> None:
    """_check_real_no_confirm_exits is called in _tick AFTER check_exchange_exits."""
    import inspect

    from crypto_trade.live.engine import LiveEngine

    src = inspect.getsource(LiveEngine._tick)
    # The real-no_confirm pass comes after check_exchange_exits
    idx_exch = src.index("check_exchange_exits")
    idx_no_conf = src.index("_check_real_no_confirm_exits")
    assert idx_exch < idx_no_conf


def test_engine_rebuild_no_confirm_called_from_rebuild_risk_state() -> None:
    """_rebuild_risk_state must call _rebuild_no_confirm_state_for_seeded."""
    import inspect

    from crypto_trade.live.engine import LiveEngine

    src = inspect.getsource(LiveEngine._rebuild_risk_state)
    assert "_rebuild_no_confirm_state_for_seeded" in src


# ----- Phase 6: seed-live-db --v3-trades -----


def test_seed_live_db_v3_kwarg_exists() -> None:
    """seed_live_db_from_backtest has v3_trades_csvs kwarg."""
    import inspect

    from crypto_trade.live.db_seeder import seed_live_db_from_backtest

    sig = inspect.signature(seed_live_db_from_backtest)
    assert "v3_trades_csvs" in sig.parameters


# test_seed_live_db_counts_dict_has_v3_keys was removed: the behavioral test
# below (test_seed_live_db_v3_empty_run) calls seed_live_db_from_backtest and
# asserts both "v3_closed" and "v3_open" are present in the returned dict,
# which catches a missing-key regression more robustly than string-matching
# the source.


def test_seed_live_db_v3_empty_run(tmp_path: Path) -> None:
    """Seeder with empty v3_trades_csvs runs idempotently (no rows inserted)."""
    from crypto_trade.live.db_seeder import seed_live_db_from_backtest
    from crypto_trade.live.models import V3_BASELINE_MODELS, LiveConfig

    db_path = tmp_path / "test.db"
    cfg = LiveConfig(models=V3_BASELINE_MODELS, data_dir=tmp_path)
    counts = seed_live_db_from_backtest(
        db_path=db_path,
        v1_trades_csvs=[],
        v2_trades_csvs=[],
        v3_trades_csvs=[],
        live_config=cfg,
        reseed=False,
    )
    assert counts["v3_closed"] == 0
    assert counts["v3_open"] == 0


# ----- Phase 6: CLI extensions (smoke via argparse) -----


def test_cli_seed_live_db_has_v3_trades_flag() -> None:
    """argparse exposes --v3-trades + --track v3 on seed-live-db."""
    from crypto_trade.main import build_parser

    parser = build_parser()
    # Find seed-live-db subparser
    subparsers = next(a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction")
    seed_p = subparsers.choices["seed-live-db"]
    actions = {a.option_strings[0] if a.option_strings else a.dest for a in seed_p._actions}
    assert "--v3-trades" in actions

    # --track choices include v3
    track_action = next(a for a in seed_p._actions if "--track" in a.option_strings)
    assert "v3" in track_action.choices


def test_cli_live_track_v3() -> None:
    """argparse exposes --track v3 on live."""
    from crypto_trade.main import build_parser

    parser = build_parser()
    subparsers = next(a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction")
    live_p = subparsers.choices["live"]
    track_action = next(a for a in live_p._actions if "--track" in a.option_strings)
    assert "v3" in track_action.choices
