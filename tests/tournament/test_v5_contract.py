"""Every configured number must be justified, or the edition does not activate.

The organizer has seen prior editions' results over the window this edition uses as its historical
observation, which makes "why is this number what it is?" load-bearing. An unanswerable one is
indistinguishable from a number fitted after the fact, so the contract admits exactly four sources
and no "judgement" tag.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from crypto_trade.tournament.v5 import contract

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "tournament" / "top40-v5" / "config.toml"


def _raw() -> dict[str, object]:
    with CONFIG.open("rb") as handle:
        return tomllib.load(handle)


def test_the_shipped_config_is_internally_complete() -> None:
    loaded = contract.load_config(CONFIG)
    assert loaded.provenance
    assert set(loaded.counts_by_source()) <= {"structural", "inherited", "calibrated", "derived"}


def test_every_justified_number_is_covered() -> None:
    loaded = contract.load_config(CONFIG)
    assert set(contract.numeric_keys(loaded.raw)) == set(loaded.provenance)


def test_a_number_without_provenance_cannot_load() -> None:
    """The mechanism that makes ex-post fitting visible rather than merely discouraged."""

    raw = _raw()
    raw["selection"]["floors"]["minimum_sneaked_in_threshold"] = 0.42  # type: ignore[index]
    with pytest.raises(contract.ContractError, match="carry no provenance"):
        contract.validate_provenance(raw)


def test_an_orphaned_provenance_tag_is_rejected() -> None:
    """A tag with no number is a claim about something that no longer exists."""

    raw = _raw()
    raw["provenance"]["selection.floors.a_threshold_we_deleted"] = "structural"  # type: ignore[index]
    with pytest.raises(contract.ContractError, match="not justified numbers"):
        contract.validate_provenance(raw)


@pytest.mark.parametrize(
    "tag",
    ["judgement", "because I said so", "inherited", "calibrated", "guess:0.5", ""],
)
def test_a_malformed_or_unsourced_tag_is_rejected(tag: str) -> None:
    """There is deliberately no judgement tag, and a bare source with no artifact is not one."""

    raw = _raw()
    raw["provenance"]["execution.max_gross_exposure"] = tag  # type: ignore[index]
    with pytest.raises(contract.ContractError, match="malformed"):
        contract.validate_provenance(raw)


@pytest.mark.parametrize(
    "tag",
    ["structural", "inherited:top40-v4-r2", "calibrated:a1b2c3", "derived:9f8e7d"],
)
def test_the_four_admissible_sources_are_accepted(tag: str) -> None:
    raw = _raw()
    raw["provenance"]["execution.max_gross_exposure"] = tag  # type: ignore[index]
    assert contract.validate_provenance(raw)["execution.max_gross_exposure"] == tag


def test_a_missing_provenance_table_is_rejected() -> None:
    raw = _raw()
    del raw["provenance"]
    with pytest.raises(contract.ContractError, match="missing its \\[provenance\\] table"):
        contract.validate_provenance(raw)


def test_booleans_are_not_treated_as_numbers_needing_justification() -> None:
    """A switch is a design decision recorded in the charter, not a fittable threshold."""

    keys = contract.numeric_keys(_raw())
    assert "execution.require_traded_bar_to_fill" not in keys
    assert "universe.require_traded_bars" not in keys
    assert "risk_unit.enabled" not in keys


def test_identity_and_path_sections_are_not_justified() -> None:
    """Paths cannot be fitted to an outcome; demanding provenance for them would be noise."""

    keys = contract.numeric_keys(_raw())
    assert not any(key.startswith(("paths.", "data.", "research.")) for key in keys)


# -- placeholders ------------------------------------------------------------------------


def test_the_shipped_config_cannot_be_activated_yet() -> None:
    """A half-justified contract is a normal intermediate state; reaching activation is not."""

    loaded = contract.load_config(CONFIG)
    with pytest.raises(contract.ContractError, match="placeholder provenance"):
        contract.assert_no_placeholder_provenance(loaded)


def test_a_fully_justified_contract_passes_the_activation_gate() -> None:
    raw = _raw()
    raw["provenance"] = {  # type: ignore[index]
        key: "calibrated:a1b2c3d4" for key in contract.numeric_keys(raw)
    }
    loaded = contract.LoadedConfig(
        path=CONFIG, raw=raw, provenance=contract.validate_provenance(raw)
    )
    contract.assert_no_placeholder_provenance(loaded)


# -- windows -------------------------------------------------------------------------------


def test_declared_windows_are_ordered() -> None:
    contract.validate_windows(_raw())


def test_an_out_of_order_window_is_rejected() -> None:
    raw = _raw()
    raw["splits"]["historical_start"] = "2019-01-01T00:00:00Z"  # type: ignore[index]
    with pytest.raises(contract.ContractError, match="must precede"):
        contract.validate_windows(raw)


def test_an_unparseable_boundary_is_rejected_at_activation() -> None:
    """V4 aborted at its first trial on a timezone mismatch inside a metric slice, after
    twenty-five activation tests passed without exercising that path."""

    raw = _raw()
    raw["splits"]["development_start"] = "not-a-date"  # type: ignore[index]
    with pytest.raises(contract.ContractError, match="not a timestamp"):
        contract.validate_windows(raw)


def test_a_missing_boundary_is_rejected() -> None:
    raw = _raw()
    del raw["splits"]["forward_paper_start"]  # type: ignore[index]
    with pytest.raises(contract.ContractError, match="missing forward_paper_start"):
        contract.validate_windows(raw)


def test_the_historical_window_is_labelled_as_contaminated() -> None:
    """It is byte-identical to a released sealed window from another edition, so the label is
    not a formality: it is what stops the result being read as a clean out-of-sample test."""

    raw = _raw()
    assert raw["splits"]["historical_evidence_label"] == (  # type: ignore[index]
        "candidate-relative-organizer-contaminated"
    )
    assert raw["splits"]["historical_visible_to_teams"] is False  # type: ignore[index]


def test_fallback_promotion_is_disallowed_in_the_contract() -> None:
    """V4-R2 declared this and the code had been patched so the raise never fired."""

    raw = _raw()
    assert raw["selection"]["fallback_promotion_allowed"] is False  # type: ignore[index]
    assert raw["selection"]["mode"] == "bar-not-rank-cut"  # type: ignore[index]
