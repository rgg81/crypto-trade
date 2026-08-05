# tests/cup20/test_config.py
import copy
import tomllib
from pathlib import Path

import pytest

from crypto_trade.cup20.config import (
    _FROZEN_SCALARS,
    IS_END,
    SEALED_END,
    SEALED_START,
    load_config,
    validate_config,
)
from crypto_trade.cup20.universe import LIQUIDITY_MEASURE

CONFIG_PATH = Path("tournament/cup20/config.toml")
ACQUISITION_CONFIG_PATH = Path("tournament/cup20/snapshot-config.toml")


def test_windows_are_frozen_utc_timestamps():
    assert str(IS_END) == "2024-08-01 00:00:00+00:00"
    assert str(SEALED_START) == "2024-08-01 00:00:00+00:00"
    assert str(SEALED_END) == "2026-08-01 00:00:00+00:00"


def test_load_config_returns_bytes_hash_and_policy():
    loaded = load_config(CONFIG_PATH)
    assert len(loaded.sha256) == 64
    assert loaded.raw["universe"]["target_size"] == 20
    assert loaded.raw["universe"]["entry_rank"] == 20
    assert loaded.raw["universe"]["exit_rank"] == 25
    assert loaded.raw["universe"]["lookback_days"] == 180
    assert loaded.raw["execution"]["taker_fee_bps_per_side"] == 5.0
    assert loaded.raw["execution"]["slippage_bps_per_side"] == 2.5
    assert loaded.raw["risk_unit"]["target_annualized_volatility"] == 0.10
    assert loaded.raw["research"]["trial_budget"] == 12
    assert loaded.raw["selection"]["advancing_slots"] == 3
    assert loaded.raw["floors"]["minimum_realized_volatility"] == 0.06
    assert len(loaded.raw["mandates"]) == 12


def test_machine_contract_declares_the_implemented_liquidity_measure():
    """The contract must name the statistic `build_membership` actually computes.

    This exists because it once did not. The config declared a median while the code ranked on the
    mean, and nothing failed: the statistic was named only in a descriptive string in the
    ACQUISITION config, which no validator reads, and every universe fixture used volumes that are
    constant inside each lookback window -- where mean and median are equal. The frozen scalar is
    now imported from the implementation rather than repeated as a literal, so the two cannot
    disagree without failing at load.
    """
    assert load_config(CONFIG_PATH).raw["universe"]["liquidity_measure"] == LIQUIDITY_MEASURE


def test_validate_config_rejects_a_liquidity_measure_the_code_does_not_implement():
    loaded = load_config(CONFIG_PATH)
    tampered = copy.deepcopy(dict(loaded.raw))
    tampered["universe"]["liquidity_measure"] = "mean-daily-quote-volume"
    with pytest.raises(ValueError, match="liquidity_measure"):
        validate_config(tampered)


def test_acquisition_config_declares_the_same_liquidity_measure():
    """Both configs describe the same ranking, so both must name it the same way.

    The acquisition config's `liquidity_measure` is descriptive -- `point_in_time_top40` hardcodes
    the median -- but it is where the correct statistic was written down all along while the
    implementation did something else, so it is worth tying down rather than leaving as prose.
    """
    acquisition = tomllib.loads(ACQUISITION_CONFIG_PATH.read_text())
    assert acquisition["universe"]["liquidity_measure"] == LIQUIDITY_MEASURE


def test_validate_config_rejects_drift():
    loaded = load_config(CONFIG_PATH)
    tampered = {
        key: dict(value) if isinstance(value, dict) else value for key, value in loaded.raw.items()
    }
    tampered["universe"]["target_size"] = 40
    with pytest.raises(ValueError):
        validate_config(tampered)


def test_validate_config_rejects_unknown_table():
    loaded = load_config(CONFIG_PATH)
    tampered = dict(loaded.raw)
    tampered["surprise"] = {}
    with pytest.raises(ValueError):
        validate_config(tampered)


def test_validate_config_rejects_changed_team_roster():
    loaded = load_config(CONFIG_PATH)
    tampered = copy.deepcopy(loaded.raw)
    tampered["teams"][-1] = "team-99"
    with pytest.raises(ValueError):
        validate_config(tampered)


def test_validate_config_rejects_non_covering_mandates():
    loaded = load_config(CONFIG_PATH)
    tampered = copy.deepcopy(loaded.raw)
    del tampered["mandates"]["team-12"]
    with pytest.raises(ValueError):
        validate_config(tampered)


def test_validate_config_rejects_non_distinct_mandates():
    loaded = load_config(CONFIG_PATH)
    tampered = copy.deepcopy(loaded.raw)
    tampered["mandates"]["team-02"] = tampered["mandates"]["team-01"]
    with pytest.raises(ValueError):
        validate_config(tampered)


def test_validate_config_rejects_changed_cost_multipliers():
    loaded = load_config(CONFIG_PATH)
    tampered = copy.deepcopy(loaded.raw)
    tampered["execution"]["cost_multipliers"] = [1, 2]
    with pytest.raises(ValueError):
        validate_config(tampered)


def test_validate_config_rejects_missing_cost_multipliers():
    loaded = load_config(CONFIG_PATH)
    tampered = copy.deepcopy(loaded.raw)
    del tampered["execution"]["cost_multipliers"]
    with pytest.raises(ValueError):
        validate_config(tampered)


# --- the frozen table must cover EVERY number, not the ones some task happened to read ------
#
# The charter says "activation MUST fail on disagreement", and that promise is worth exactly what
# _FROZEN_SCALARS covers. Eleven of the thirteen [floors] were absent from it, so a config declaring
# `net_sharpe = 0.30` against a charter saying 0.80 would load, validate, freeze and verify without
# a word -- and the floors ARE the qualification gate. The table had grown by hand alongside
# whichever task read a given key, which is why the gap tracked no principle at all.
#
# These two tests replace "remember to add it" with a check. The first proves the table is complete
# against the real config; the second proves each entry is load-bearing rather than decorative.

_LISTS_VALIDATED_SEPARATELY = {
    ("teams",),  # exact roster, checked against TEAM_IDS
    ("execution", "cost_multipliers"),  # frozen at (1, 2, 3) by its own branch
}


def _numeric_paths(node, prefix=()):
    """Every path in the config whose value is a number (bool excluded -- TOML has none here)."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _numeric_paths(value, (*prefix, key))
    elif isinstance(node, list):
        if prefix not in _LISTS_VALIDATED_SEPARATELY:
            raise AssertionError(f"config list at {prefix} is validated by nothing")
    elif isinstance(node, (int, float)) and not isinstance(node, bool):
        yield prefix


def test_every_numeric_policy_value_is_in_the_frozen_table():
    raw = load_config(CONFIG_PATH).raw
    numeric = set(_numeric_paths(raw))
    assert numeric, "walked the config and found no numbers at all"
    missing = sorted(".".join(path) for path in numeric - set(_FROZEN_SCALARS))
    assert missing == [], f"numeric policy values outside the frozen contract: {missing}"


def test_no_frozen_entry_is_stale():
    """Every frozen path must still exist in the config, with the frozen value."""
    raw = load_config(CONFIG_PATH).raw
    for path, expected in _FROZEN_SCALARS.items():
        node = raw
        for component in path:
            assert component in node, f"frozen path {'.'.join(path)} is not in the config"
            node = node[component]
        assert node == expected, f"frozen path {'.'.join(path)} disagrees with the config"


@pytest.mark.parametrize("path", sorted(_FROZEN_SCALARS, key=lambda p: ".".join(p)))
def test_each_frozen_scalar_is_individually_binding(path):
    """Mutating any one frozen value must fail validation. Without this, an entry can be present in
    the table and still be inert -- which is indistinguishable from being absent."""
    tampered = copy.deepcopy(dict(load_config(CONFIG_PATH).raw))
    node = tampered
    for component in path[:-1]:
        node = node[component]
    current = node[path[-1]]
    node[path[-1]] = "drift" if isinstance(current, str) else current + 1
    with pytest.raises(ValueError, match=".".join(path)):
        validate_config(tampered)
