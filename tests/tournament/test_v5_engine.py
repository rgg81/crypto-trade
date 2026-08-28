"""Evaluator behaviour at the exposure caps."""

from __future__ import annotations

import pandas as pd
import pytest

from crypto_trade.tournament.v5 import engine


def test_a_marginal_cap_breach_is_projected_rather_than_raised():
    """One bar 7.6e-5 over a cap must not destroy a 3.5-year evaluation.

    team-14 -- the one lane mandated to run non-zero net, and therefore the one forced to work at
    the boundary -- lost its entire trial to a single bar out of 3834 whose net was 0.250076
    against a 0.25 cap. Floating-point accumulation in its own normalisation, not an attempt to
    breach. The charter has the evaluator enforce exposure reductions and score ruin rather than
    raise it, so a breaching submission is projected and the breach recorded.
    """

    cfg = engine.EvaluatorConfig()
    weights = pd.Series({"AAAUSDT": 0.100038, "BBBUSDT": 0.100038, "CCCUSDT": 0.05})

    breach = engine._weight_limit_breach(weights, cfg)
    assert breach is not None and "net" in breach

    projected, _ = engine._project_into_caps(weights, cfg)
    assert abs(float(projected.sum())) <= cfg.max_abs_net_exposure + 1e-9
    # The projection preserves direction: a book mandated to run net long stays net long.
    assert float(projected.sum()) > 0.0


def test_a_book_inside_the_caps_reports_no_breach():
    """The other direction, so the reporter cannot be trivially always-on."""

    cfg = engine.EvaluatorConfig()
    balanced = pd.Series({"AAAUSDT": 0.09, "BBBUSDT": -0.09, "CCCUSDT": 0.05})

    assert engine._weight_limit_breach(balanced, cfg) is None


def test_the_post_projection_validator_still_raises():
    """After the organizer's own projection a breach would be an organizer bug, and must stop."""

    cfg = engine.EvaluatorConfig()
    illegal = pd.Series({"AAAUSDT": 0.5, "BBBUSDT": 0.5})

    with pytest.raises(ValueError, match="exceeds cap"):
        engine._validate_weight_limits(illegal, cfg, pd.Timestamp("2022-01-01", tz="UTC"))
