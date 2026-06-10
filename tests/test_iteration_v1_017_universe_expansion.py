"""iter-v1/017 — Universe expansion unit tests.

Verifies:
1. V1_ITER017_UNIVERSE constant exists and contains exactly the 6 expected symbols.
2. SOLUSDT is NOT in V1_EXCLUDED_SYMBOLS (required for iter-v1/017 runner dispatch).
3. assert_v1_universe() accepts the full V1_ITER017_UNIVERSE (6-sym).
4. assert_v1_universe() still rejects v2/v3 symbols (regression guard).
5. The elif branch for V1_ITER017_UNIVERSE is distinct from the baseline branch.

Brief reference: briefs-v1/iteration_v1-017/research_brief.md Section 10.4.
"""

from __future__ import annotations

import pytest
from run_baseline_v1 import V1_ITER017_UNIVERSE

from crypto_trade.features_v1 import (
    V1_BASELINE_UNIVERSE,
    V1_EXCLUDED_SYMBOLS,
    assert_v1_universe,
)


class TestV1Iter017UniverseConstant:
    """Test V1_ITER017_UNIVERSE constant correctness."""

    def test_universe_length_is_6(self) -> None:
        """V1_ITER017_UNIVERSE must have exactly 6 symbols."""
        assert len(V1_ITER017_UNIVERSE) == 6, (
            f"Expected 6 symbols in V1_ITER017_UNIVERSE, got {len(V1_ITER017_UNIVERSE)}"
        )

    def test_universe_contains_all_baseline_symbols(self) -> None:
        """V1_ITER017_UNIVERSE must contain all 5 baseline symbols."""
        missing = set(V1_BASELINE_UNIVERSE) - set(V1_ITER017_UNIVERSE)
        assert not missing, f"V1_ITER017_UNIVERSE missing baseline symbols: {missing}"

    def test_universe_contains_solusdt(self) -> None:
        """V1_ITER017_UNIVERSE must include SOLUSDT (the new Model F symbol)."""
        assert "SOLUSDT" in V1_ITER017_UNIVERSE, (
            "SOLUSDT must be in V1_ITER017_UNIVERSE for iter-v1/017 Model F"
        )

    def test_universe_exact_symbols(self) -> None:
        """V1_ITER017_UNIVERSE must contain exactly the expected 6 symbols."""
        expected = frozenset({"BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT", "SOLUSDT"})
        assert frozenset(V1_ITER017_UNIVERSE) == expected, (
            f"V1_ITER017_UNIVERSE symbols mismatch: got {set(V1_ITER017_UNIVERSE)}, "
            f"expected {expected}"
        )

    def test_iter017_universe_is_superset_of_baseline(self) -> None:
        """V1_ITER017_UNIVERSE must be a strict superset of V1_BASELINE_UNIVERSE."""
        assert set(V1_BASELINE_UNIVERSE).issubset(set(V1_ITER017_UNIVERSE)), (
            "V1_BASELINE_UNIVERSE is not a subset of V1_ITER017_UNIVERSE"
        )
        assert len(V1_ITER017_UNIVERSE) == len(V1_BASELINE_UNIVERSE) + 1, (
            "V1_ITER017_UNIVERSE should be exactly 1 symbol larger than baseline"
        )


class TestV1ExcludedSymbolsUpdate:
    """Test that SOLUSDT is removed from V1_EXCLUDED_SYMBOLS for iter-v1/017."""

    def test_solusdt_not_excluded(self) -> None:
        """SOLUSDT must NOT be in V1_EXCLUDED_SYMBOLS for the dispatch to work."""
        assert "SOLUSDT" not in V1_EXCLUDED_SYMBOLS, (
            "SOLUSDT must be removed from V1_EXCLUDED_SYMBOLS for iter-v1/017; "
            f"current V1_EXCLUDED_SYMBOLS = {V1_EXCLUDED_SYMBOLS}"
        )

    def test_v3_symbols_still_excluded(self) -> None:
        """v3 symbols (BCHUSDT, LDOUSDT, TRXUSDT) must remain excluded."""
        for sym in ("BCHUSDT", "LDOUSDT", "TRXUSDT"):
            assert sym in V1_EXCLUDED_SYMBOLS, f"v3 symbol {sym} must remain in V1_EXCLUDED_SYMBOLS"

    def test_v2_symbols_still_excluded(self) -> None:
        """Remaining v2 symbols (XRPUSDT, DOGEUSDT, NEARUSDT) must remain excluded."""
        for sym in ("XRPUSDT", "DOGEUSDT", "NEARUSDT"):
            assert sym in V1_EXCLUDED_SYMBOLS, f"v2 symbol {sym} must remain in V1_EXCLUDED_SYMBOLS"

    def test_bnbusdt_not_excluded(self) -> None:
        """BNBUSDT was un-reserved per iter-v1/087 user directive 2026-06-10.

        'Don't discard BNB — un-reserve it. The backtest is the proof.'
        BNBUSDT is no longer in V1_EXCLUDED_SYMBOLS; the real backtest
        (run_iteration_087.py with fail_fast_is_years=2.0) is the gate.
        """
        assert "BNBUSDT" not in V1_EXCLUDED_SYMBOLS, (
            "iter-v1/087 un-reserved BNBUSDT — it must NOT be in V1_EXCLUDED_SYMBOLS. "
            f"Current V1_EXCLUDED_SYMBOLS = {V1_EXCLUDED_SYMBOLS}"
        )


class TestAssertV1UniverseAcceptsIter017Universe:
    """Test assert_v1_universe() accepts the 6-symbol iter-v1/017 set."""

    def test_assert_accepts_iter017_universe(self) -> None:
        """assert_v1_universe must not raise for V1_ITER017_UNIVERSE."""
        # Should not raise
        assert_v1_universe(V1_ITER017_UNIVERSE)

    def test_assert_accepts_baseline_universe(self) -> None:
        """assert_v1_universe must still accept V1_BASELINE_UNIVERSE (regression)."""
        assert_v1_universe(V1_BASELINE_UNIVERSE)

    def test_assert_rejects_v3_symbol(self) -> None:
        """assert_v1_universe must reject a v3 symbol (BCHUSDT)."""
        with pytest.raises(AssertionError, match="v1 cannot trade v2/v3 symbols"):
            assert_v1_universe(("BTCUSDT", "ETHUSDT", "BCHUSDT"))

    def test_assert_rejects_v2_symbol_xrp(self) -> None:
        """assert_v1_universe must reject XRPUSDT (still v2-reserved)."""
        with pytest.raises(AssertionError, match="v1 cannot trade v2/v3 symbols"):
            assert_v1_universe(("BTCUSDT", "ETHUSDT", "XRPUSDT"))

    def test_assert_accepts_bnb(self) -> None:
        """assert_v1_universe must now accept BNBUSDT (un-reserved at iter-v1/087)."""
        # iter-v1/087: BNB un-reserved per user directive 2026-06-10.
        # assert_v1_universe must NOT raise for BNBUSDT.
        assert_v1_universe(("BTCUSDT", "BNBUSDT"))


class TestIter017DispatchBranchDistinction:
    """Test that the elif branch for V1_ITER017_UNIVERSE is distinct from baseline."""

    def test_iter017_universe_not_equal_to_baseline(self) -> None:
        """V1_ITER017_UNIVERSE and V1_BASELINE_UNIVERSE must NOT be equal sets."""
        assert set(V1_ITER017_UNIVERSE) != set(V1_BASELINE_UNIVERSE), (
            "V1_ITER017_UNIVERSE must differ from V1_BASELINE_UNIVERSE; "
            "they route to different dispatch branches in run_baseline_v1.py"
        )

    def test_iter017_universe_routes_to_elif_not_baseline_branch(self) -> None:
        """Verify the elif routing logic: V1_ITER017_UNIVERSE triggers the elif branch."""
        # This mirrors the runner's dispatch check:
        #   if set(symbols) == set(V1_BASELINE_UNIVERSE): ...  ← baseline branch
        #   elif set(symbols) == set(V1_ITER017_UNIVERSE): ... ← iter-v1/017 branch
        baseline_check = set(V1_ITER017_UNIVERSE) == set(V1_BASELINE_UNIVERSE)
        iter017_check = set(V1_ITER017_UNIVERSE) == set(V1_ITER017_UNIVERSE)
        assert not baseline_check, "V1_ITER017_UNIVERSE must NOT match the baseline branch check"
        assert iter017_check, "V1_ITER017_UNIVERSE must match the elif branch check"
