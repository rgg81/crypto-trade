"""Tiny organizer-owned strategy used only by the Phase-0 sandbox canary."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

_EXPECTED_SEED = 20260718
_EXPECTED_SYMBOL = "BTCUSDT"
_EXPECTED_WEIGHT = 0.03125


class SandboxCanaryStrategy:
    def target_weights(self, context, *, seed: int) -> dict[str, float]:
        if seed != _EXPECTED_SEED:
            raise RuntimeError("sandbox canary received the wrong seed")
        if tuple(context.eligible_symbols) != (_EXPECTED_SYMBOL,):
            raise RuntimeError("sandbox canary received the wrong membership")
        bars = context.bars.get(_EXPECTED_SYMBOL)
        if bars is None or len(bars) != 1:
            raise RuntimeError("sandbox canary did not receive exactly one closed bar")
        if pd.Timestamp(bars.iloc[0]["open_time"]) != pd.Timestamp(
            "2026-07-18T00:00:00Z"
        ):
            raise RuntimeError("sandbox canary received the wrong closed bar")
        if len(context.funding) != 1 or float(context.funding.iloc[0]["funding_rate"]) != 0.0001:
            raise RuntimeError("sandbox canary did not receive settled synthetic funding")

        # The production worker remaps imported packages onto its read-only staged venv mount
        # before hiding the repository.  Checking both remapped paths makes this a runtime proof,
        # not merely a parent-side configuration assertion.
        runtime_paths = (Path(np.__file__).resolve(), Path(pd.__file__).resolve())
        if not all("runtime-site-packages" in path.parts for path in runtime_paths):
            raise RuntimeError("sandbox canary is not using the staged repo-local venv")
        if not np.isfinite(np.asarray([float(bars.iloc[0]["close"])]))[0]:
            raise RuntimeError("sandbox canary numeric runtime is unavailable")
        return {_EXPECTED_SYMBOL: _EXPECTED_WEIGHT}


def build_strategy() -> SandboxCanaryStrategy:
    return SandboxCanaryStrategy()
