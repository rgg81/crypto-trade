"""v2 feature registry — diversification track.

Isolated from ``crypto_trade.features`` (the v1 package). v2 code must NEVER
import from the v1 package; the first iteration's QE audits for such imports.

iter-v2/001 will implement the feature modules and register them here. This
scaffold only establishes the package structure and an empty registry so the
import surface is stable before any iteration runs.
"""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

GROUP_REGISTRY: dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {}


def _register(name: str, fn: Callable[[pd.DataFrame], pd.DataFrame]) -> None:
    GROUP_REGISTRY[name] = fn


def list_groups() -> list[str]:
    return sorted(GROUP_REGISTRY.keys())


def generate_features_v2(df: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    """Run the selected v2 feature groups on *df* and return the augmented frame."""
    for group_name in groups:
        fn = GROUP_REGISTRY[group_name]
        df = fn(df)
        df = df.copy()
    return df


__all__ = [
    "GROUP_REGISTRY",
    "generate_features_v2",
    "list_groups",
]
