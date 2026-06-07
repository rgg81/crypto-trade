"""
Tests for the N-aware bundle concentration metric (H3 fix).

Finding H3: when one specialist has negative OOS PnL, dividing top_sym_pnl by
the net total_oos_pnl can yield concentration > 100%, which is a meaningless
artifact.  The fix uses max(total_oos_pnl, sum_of_positives) as the denominator
so that concentration is always capped at 100%.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Pure helper that mirrors the fixed logic in compose_bundle_001.py
# ---------------------------------------------------------------------------
def _compute_top_sym_conc(per_sym_pnl: list[float]) -> float:
    """Compute top-symbol OOS concentration (%) using the N-aware denominator.

    This is the fixed formula from compose_bundle_001.py (H3).  Extracted here
    so the test does not import the full script (which has heavyweight side
    effects on import: file I/O, SPECIALISTS constant resolution, etc.).
    """
    if not per_sym_pnl:
        return 0.0
    total_oos_pnl = sum(per_sym_pnl)
    sum_of_positives = sum(p for p in per_sym_pnl if p > 0)
    top_sym_pnl = max(per_sym_pnl)
    denom = max(total_oos_pnl, sum_of_positives)
    return top_sym_pnl / denom * 100 if denom != 0 else 0.0


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestConcentrationCapAt100:
    """Verify concentration <= 100% when PnL signs are mixed."""

    def test_sign_mixed_pnl_capped_at_100(self):
        """Main regression case: one specialist positive, one negative.

        Example: +10% winner, -3% loser.
        Old formula: 10 / (10 + -3) * 100 = 10/7*100 ≈ 142.9%  (WRONG)
        New formula: 10 / max(7, 10) * 100 = 10/10*100 = 100%   (CORRECT)
        """
        per_sym_pnl = [10.0, -3.0]
        conc = _compute_top_sym_conc(per_sym_pnl)
        assert conc <= 100.0, f"Concentration must be ≤ 100%, got {conc:.2f}%"
        assert conc == 100.0, f"Expected exactly 100.0%, got {conc:.2f}%"

    def test_all_positive_pnl_standard_case(self):
        """All positive specialists: denominator = total = sum_of_positives."""
        per_sym_pnl = [5.0, 3.0, 2.0]
        conc = _compute_top_sym_conc(per_sym_pnl)
        # top = 5.0, total = 10.0, sum_of_positives = 10.0
        # conc = 5/10*100 = 50%
        assert abs(conc - 50.0) < 1e-9, f"Expected 50.0%, got {conc:.2f}%"

    def test_all_negative_pnl_returns_zero(self):
        """All losers: sum_of_positives = 0, denom = max(total, 0) = total (negative).

        When denom is negative (total<0, sum_of_pos=0) we fall into the
        denom != 0 branch.  The concentration then becomes negative, which is
        semantically odd.  A guard: any all-negative portfolio should be flagged
        but must not blow up.  We just verify no exception is raised and the
        result is numeric.
        """
        per_sym_pnl = [-2.0, -5.0]
        conc = _compute_top_sym_conc(per_sym_pnl)
        # top = -2.0, total = -7.0, sum_of_positives = 0
        # denom = max(-7.0, 0) = 0  → returns 0.0
        assert conc == 0.0, f"All-negative portfolio: expected 0.0%, got {conc:.2f}%"

    def test_empty_portfolio_returns_zero(self):
        """Edge case: no symbols."""
        conc = _compute_top_sym_conc([])
        assert conc == 0.0

    def test_single_specialist_gives_100_pct(self):
        """Single positive specialist is 100% of the bundle by definition."""
        per_sym_pnl = [7.5]
        conc = _compute_top_sym_conc(per_sym_pnl)
        assert abs(conc - 100.0) < 1e-9, f"Expected 100.0%, got {conc:.2f}%"

    def test_concentration_never_exceeds_100_with_large_negative(self):
        """Stress test: large negative drags net total far below max winner."""
        per_sym_pnl = [50.0, -40.0]
        conc = _compute_top_sym_conc(per_sym_pnl)
        # Old: 50 / (50 - 40) * 100 = 500%  (catastrophically wrong)
        # New: 50 / max(10, 50) * 100 = 50/50*100 = 100%
        assert conc <= 100.0, f"Must be ≤ 100%, got {conc:.2f}%"
        assert abs(conc - 100.0) < 1e-9

    def test_three_specialists_one_negative(self):
        """Three specialists, one negative; winner is not the full sum."""
        per_sym_pnl = [8.0, 4.0, -2.0]
        conc = _compute_top_sym_conc(per_sym_pnl)
        # total = 10.0, sum_of_positives = 12.0
        # denom = max(10, 12) = 12
        # conc = 8/12*100 ≈ 66.67%
        assert conc <= 100.0
        expected = 8.0 / 12.0 * 100
        assert abs(conc - expected) < 1e-9, f"Expected {expected:.4f}%, got {conc:.4f}%"

    def test_equal_positive_pnl_gives_correct_share(self):
        """Four specialists all equal: each should be 25%."""
        per_sym_pnl = [5.0, 5.0, 5.0, 5.0]
        conc = _compute_top_sym_conc(per_sym_pnl)
        assert abs(conc - 25.0) < 1e-9, f"Expected 25.0%, got {conc:.2f}%"
