"""Tests for _parse_bundle_config allow-list fix (C4/H4 -- 2026-06-07).

Prior to this fix, _parse_bundle_config used a hardcoded set
{"baseline", "v1-036", "v1-043"} which silently rejected every
SPECIALIST iteration label (v1-063, v1-064, ..., v1-077 and beyond).
The fix replaces the set with a regex pattern ^(baseline|v1-[0-9]{3})$
so any v1-NNN label where NNN in [001..999] is accepted.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# Import the function under test directly from the runner module.
# The runner is not a package, so we import via importlib to avoid
# side-effects from argparse.parse_args() in the module's __main__ guard.
_RUNNER_PATH = Path(__file__).parent.parent / "run_baseline_v1.py"


def _load_runner():
    """Load run_baseline_v1 as a module without executing main()."""
    spec = importlib.util.spec_from_file_location("run_baseline_v1", _RUNNER_PATH)
    mod = importlib.util.module_from_spec(spec)
    # Inject into sys.modules so relative imports inside the runner resolve.
    sys.modules["run_baseline_v1"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_runner = _load_runner()
_parse_bundle_config = _runner._parse_bundle_config


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSpecialistLabelsAccepted:
    """C4/H4: SPECIALIST iteration labels v1-NNN must be accepted."""

    def test_three_specialist_labels_sum_to_one(self):
        result = _parse_bundle_config("v1-063:0.33,v1-064:0.33,v1-065:0.34")
        assert result == {"v1-063": 0.33, "v1-064": 0.33, "v1-065": 0.34}

    def test_specialist_label_v1_077(self):
        result = _parse_bundle_config("v1-077:1.0")
        assert result == {"v1-077": 1.0}

    def test_specialist_label_v1_001(self):
        result = _parse_bundle_config("v1-001:1.0")
        assert result == {"v1-001": 1.0}

    def test_specialist_label_v1_999(self):
        result = _parse_bundle_config("v1-999:1.0")
        assert result == {"v1-999": 1.0}

    def test_baseline_still_accepted(self):
        result = _parse_bundle_config("baseline:1.0")
        assert result == {"baseline": 1.0}

    def test_baseline_plus_specialist(self):
        result = _parse_bundle_config("baseline:0.50,v1-063:0.50")
        assert result == {"baseline": 0.50, "v1-063": 0.50}

    def test_four_specialists(self):
        result = _parse_bundle_config("v1-063:0.25,v1-064:0.25,v1-065:0.25,v1-066:0.25")
        assert len(result) == 4
        assert abs(sum(result.values()) - 1.0) < 1e-6

    def test_whitespace_around_tokens_tolerated(self):
        result = _parse_bundle_config(" v1-063:0.50 , v1-064:0.50 ")
        assert result == {"v1-063": 0.50, "v1-064": 0.50}


class TestInvalidLabelsStillRejected:
    """Invalid component labels must still raise ValueError."""

    def test_random_string_rejected(self):
        with pytest.raises(ValueError, match="Unknown component"):
            _parse_bundle_config("randomstring:1.0")

    def test_v2_label_rejected(self):
        with pytest.raises(ValueError, match="Unknown component"):
            _parse_bundle_config("v2-063:1.0")

    def test_v3_label_rejected(self):
        with pytest.raises(ValueError, match="Unknown component"):
            _parse_bundle_config("v3-063:1.0")

    def test_v1_without_three_digit_suffix_rejected(self):
        with pytest.raises(ValueError, match="Unknown component"):
            _parse_bundle_config("v1-63:1.0")

    def test_v1_with_four_digit_suffix_rejected(self):
        with pytest.raises(ValueError, match="Unknown component"):
            _parse_bundle_config("v1-0636:1.0")

    def test_empty_component_rejected(self):
        with pytest.raises(ValueError):
            _parse_bundle_config(":1.0")

    def test_weights_not_summing_to_one_rejected(self):
        with pytest.raises(ValueError, match="weights sum to"):
            _parse_bundle_config("v1-063:0.30,v1-064:0.30")

    def test_missing_colon_rejected(self):
        with pytest.raises(ValueError, match="expected 'component:weight'"):
            _parse_bundle_config("v1-063")

    def test_non_float_weight_rejected(self):
        with pytest.raises(ValueError, match="Invalid weight"):
            _parse_bundle_config("v1-063:abc")
