"""Focused tests for the non-active pure-crypto Amendment 0006 draft."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from crypto_trade.tournament import amendment_0006_v2 as amendment
from crypto_trade.tournament import pure_crypto_universe_v6 as universe

ROOT = Path(__file__).resolve().parents[2]


def _contract(symbol: str = "BTCUSDT", **replacements: Any) -> dict[str, Any]:
    contract: dict[str, Any] = {
        "symbol": symbol,
        "baseAsset": symbol[:-4],
        "quoteAsset": "USDT",
        "marginAsset": "USDT",
        "contractType": "PERPETUAL",
        "underlyingType": "COIN",
        "underlyingSubType": ["PoW"],
    }
    contract.update(replacements)
    return contract


def _assert_symbol_set_record(record: dict[str, Any]) -> None:
    assert record["count"] == len(record["symbols"])
    assert record["symbols"] == sorted(set(record["symbols"]))
    payload = json.dumps(record["symbols"], ensure_ascii=True, separators=(",", ":")).encode(
        "utf-8"
    )
    assert record["sha256"] == hashlib.sha256(payload).hexdigest()


def test_real_frozen_snapshot_passes_with_exact_pure_crypto_sets() -> None:
    report = universe.audit_pure_crypto_universe(ROOT)

    assert report["status"] == "passed"
    assert report["violations"] == []
    assert (
        report["counts"]
        | {
            "contract_metadata_rows": 667,
            "contract_metadata_symbols": 667,
            "current_metadata_symbols": 641,
            "archive_only_metadata_symbols": 26,
            "membership_rows": 12_866,
            "membership_symbols": 321,
            "membership_current_symbols": 303,
            "membership_archive_only_symbols": 18,
            "current_exchange_symbols": 832,
            "current_exchange_non_coin_contracts": 133,
            "violations": 0,
        }
        == report["counts"]
    )

    accepted = report["accepted_symbol_sets"]
    assert accepted["all_contract_metadata"]["count"] == 667
    assert accepted["current_contract_metadata"]["count"] == 641
    assert accepted["archive_only_contract_metadata"]["count"] == 26
    assert accepted["all_membership"]["count"] == 321
    for record in accepted.values():
        _assert_symbol_set_record(record)

    classifications = report["classifications"]
    assert classifications["accepted_rwa_sector_metadata_symbols"] == [
        "CFGUSDT",
        "MANTRAUSDT",
    ]
    assert set(classifications["accepted_rwa_sector_membership_symbols"]).issubset(
        {"CFGUSDT", "MANTRAUSDT"}
    )
    assert classifications["current_exchange_underlying_type_counts"]["counts"] == {
        "COIN": 699,
        "COMMODITY": 8,
        "EQUITY": 117,
        "INDEX": 3,
        "KR_EQUITY": 3,
        "PREMARKET": 2,
    }
    assert classifications["current_exchange_raw_subtype_vocabulary"]["counts"]["RWA"] == 4
    assert classifications["current_exchange_normalized_subtype_vocabulary"]["counts"]["rwa"] == 4
    direct_non_crypto = classifications["current_exchange_exclusion_cohorts"][
        "direct-non-crypto-base"
    ]
    assert direct_non_crypto["denominator_count"] == 832
    assert {"PAXGUSDT", "XAUTUSDT"}.issubset(direct_non_crypto["symbols"])


def test_canonical_report_bytes_are_deterministic() -> None:
    first = universe.audit_report_bytes(ROOT)
    second = universe.audit_report_bytes(ROOT)
    assert first == second
    assert universe.audit_report_sha256(ROOT) == hashlib.sha256(first).hexdigest()


@pytest.mark.parametrize(
    ("symbol", "reason"),
    [
        ("USDEUSDT", "stablecoin-base"),
        ("BTCUPUSDT", "leveraged-token-base"),
        ("PAXGUSDT", "direct-non-crypto-base"),
        ("XAUTUSDT", "direct-non-crypto-base"),
        ("btcusdt", "symbol-format"),
        ("龙虾USDT", "symbol-format"),
        ("BTC_USDT", "symbol-format"),
        ("BTCUSDC", "symbol-format"),
    ],
)
def test_exact_name_policy_rejects_non_crypto_assets(symbol: str, reason: str) -> None:
    assert reason in universe.symbol_policy_violations(symbol)


def test_frax_and_native_rwa_protocol_tokens_are_not_stable_or_tradfi() -> None:
    assert "FRAX" not in universe.STABLE_BASES
    assert (
        universe.current_contract_violations(_contract("FRAXUSDT", underlyingSubType=["DeFi"]))
        == ()
    )
    assert (
        universe.current_contract_violations(_contract("CFGUSDT", underlyingSubType=["RWA"])) == ()
    )
    assert (
        universe.current_contract_violations(_contract("MANTRAUSDT", underlyingSubType=["RWA"]))
        == ()
    )


def test_current_contract_rule_is_an_exact_and_not_a_contains_check() -> None:
    tradfi = _contract(
        "AAPLUSDT",
        contractType="TRADIFI_PERPETUAL",
        underlyingType="EQUITY",
        underlyingSubType=["TradFi"],
    )
    reasons = universe.current_contract_violations(tradfi)
    assert "contract-type-not-perpetual" in reasons
    assert "forbidden-underlying-type" in reasons
    assert "forbidden-underlying-subtype:tradfi" in reasons

    wrong_base = _contract("BTCUSDT", baseAsset="ETH")
    assert "base-asset-mismatch" in universe.current_contract_violations(wrong_base)
    wrong_margin = _contract("BTCUSDT", marginAsset="USDC")
    assert "margin-asset-not-usdt" in universe.current_contract_violations(wrong_margin)


@pytest.mark.parametrize(
    "subtypes",
    [None, "DeFi", ["DeFi", "DeFi"], [" DeFi"], [1]],
)
def test_subtype_shape_is_strict(subtypes: object) -> None:
    assert universe.current_contract_violations(_contract("BTCUSDT", underlyingSubType=subtypes))


def test_unknown_sector_tag_is_not_the_primary_open_world_classifier() -> None:
    assert (
        universe.current_contract_violations(
            _contract("BTCUSDT", underlyingSubType=["FutureNativeCryptoSector"])
        )
        == ()
    )


def test_archive_only_authority_is_exact_not_a_subset() -> None:
    assert len(universe.REVIEWED_ARCHIVE_ONLY_CRYPTO) == 26
    assert universe.REVIEWED_ARCHIVE_ONLY_CRYPTO == frozenset(
        {
            "1000BTTCUSDT",
            "AKROUSDT",
            "ANCUSDT",
            "ANTUSDT",
            "AUDIOUSDT",
            "BDXNUSDT",
            "BTSUSDT",
            "BTTUSDT",
            "BZRXUSDT",
            "COCOSUSDT",
            "DODOUSDT",
            "EOSUSDT",
            "FRONTUSDT",
            "GALUSDT",
            "HNTUSDT",
            "KEEPUSDT",
            "LENDUSDT",
            "LUNAUSDT",
            "MATICUSDT",
            "MBLUSDT",
            "NUUSDT",
            "RNDRUSDT",
            "SRMUSDT",
            "SXPUSDT",
            "TOMOUSDT",
            "YFIIUSDT",
        }
    )


def test_membership_ranks_allow_early_short_sets_but_require_contiguous_max_40() -> None:
    valid = pd.DataFrame(
        {
            "reconstitution_time": ["2020-02-03", "2020-02-03", "2020-02-10"],
            "liquidity_rank": [1, 2, 1],
        }
    )
    universe._validate_membership_ranks(valid)

    gap = pd.DataFrame(
        {
            "reconstitution_time": ["2020-02-03", "2020-02-03"],
            "liquidity_rank": [1, 3],
        }
    )
    with pytest.raises(universe.PureCryptoUniverseError, match="contiguous"):
        universe._validate_membership_ranks(gap)

    too_many = pd.DataFrame(
        {
            "reconstitution_time": ["2020-02-03"] * 41,
            "liquidity_rank": list(range(1, 42)),
        }
    )
    with pytest.raises(universe.PureCryptoUniverseError, match="N <= 40"):
        universe._validate_membership_ranks(too_many)


def test_wrapper_audits_and_pins_before_and_after_success(monkeypatch) -> None:
    events: list[str] = []

    monkeypatch.setattr(
        amendment, "verify_parent_authorities", lambda root: events.append("authority")
    )
    monkeypatch.setattr(
        amendment,
        "_PURE_REPORT_BYTES",
        lambda root: events.append("audit") or b"same",
    )
    monkeypatch.setattr(amendment, "_A4_RUN", lambda values, root: events.append("delegate") or 0)

    assert amendment.run(["research-status"], root=ROOT) == 0
    assert events == ["authority", "audit", "delegate", "audit", "authority"]


def test_wrapper_postchecks_after_baseexception(monkeypatch) -> None:
    events: list[str] = []

    monkeypatch.setattr(
        amendment, "verify_parent_authorities", lambda root: events.append("authority")
    )
    monkeypatch.setattr(
        amendment,
        "_PURE_REPORT_BYTES",
        lambda root: events.append("audit") or b"same",
    )

    def interrupt(values, root):
        events.append("delegate")
        raise KeyboardInterrupt

    monkeypatch.setattr(amendment, "_A4_RUN", interrupt)
    with pytest.raises(KeyboardInterrupt):
        amendment.run(["research-status"], root=ROOT)
    assert events == ["authority", "audit", "delegate", "audit", "authority"]


def test_wrapper_prioritizes_post_integrity_failure(monkeypatch) -> None:
    calls = 0

    monkeypatch.setattr(amendment, "verify_parent_authorities", lambda root: None)

    def audit(root):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise universe.PureCryptoUniverseError("post audit failed")
        return b"same"

    def fail(values, root):
        raise RuntimeError("delegated failure")

    monkeypatch.setattr(amendment, "_PURE_REPORT_BYTES", audit)
    monkeypatch.setattr(amendment, "_A4_RUN", fail)
    with pytest.raises(universe.PureCryptoUniverseError, match="post audit failed") as exc_info:
        amendment.run(["research-status"], root=ROOT)
    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_candidate_entrypoint_is_additive_and_old_active_path_is_not_edited() -> None:
    assert "scripts/top40_v2_tournament_pure_crypto_v6.py" in amendment.IMPLEMENTATION_FILE_PATHS
    assert "scripts/top40_v2_tournament_active.py" not in amendment.IMPLEMENTATION_FILE_PATHS
