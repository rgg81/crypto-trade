"""Prospective Top40 correction for mixed-form UTC metric-window bounds.

The Phase-0 runner is immutable.  This additive adapter verifies that exact parent runner, then
installs one narrowly scoped metric adapter: both score bounds are rendered with the same explicit
UTC offset before pandas slicing, while the published window identity uses canonical date-only
strings required by the frozen coaching contract.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd

from crypto_trade.tournament import runner_v3

AMENDMENT_ID = "top40-v3-amendment-0001-utc-metric-bounds"
PARENT_RUNNER_SHA256 = "b4704dce1f2bfb7f624feea16bf1ec0bbc9ce345995856741551bb6d57c2ecc3"

_PARENT_COMPUTE_METRICS = runner_v3._compute_metrics
_PARENT_EVALUATOR_AUTHORITY_SHA256 = runner_v3._evaluator_authority_sha256
_INSTALL_LOCK = threading.Lock()


class Amendment0001Error(RuntimeError):
    """The prospective correction cannot prove its frozen parent authority."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise Amendment0001Error(f"cannot read frozen parent runner: {exc}") from exc
    return digest.hexdigest()


def verify_parent_runner() -> None:
    """Fail closed unless the loaded runner is the byte-exact Phase-0 parent."""

    path = Path(runner_v3.__file__).resolve()
    if not path.is_file() or path.is_symlink():
        raise Amendment0001Error("frozen parent runner path is missing or unsafe")
    if _sha256_file(path) != PARENT_RUNNER_SHA256:
        raise Amendment0001Error("frozen parent runner SHA-256 differs from Phase-0")
    current_metric = runner_v3._compute_metrics
    current_evaluator = runner_v3._evaluator_authority_sha256
    if current_metric not in {_PARENT_COMPUTE_METRICS, compute_metrics_with_utc_bounds}:
        raise Amendment0001Error("loaded parent metric authority was replaced unexpectedly")
    if current_evaluator not in {
        _PARENT_EVALUATOR_AUTHORITY_SHA256,
        evaluator_authority_sha256,
    }:
        raise Amendment0001Error("loaded parent evaluator authority was replaced unexpectedly")


def _explicit_utc(value: str) -> str:
    timestamp = runner_v3._as_utc_timestamp(value)
    return timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def _date_only(value: str) -> str:
    return runner_v3._as_utc_timestamp(value).strftime("%Y-%m-%d")


def compute_metrics_with_utc_bounds(
    base_daily: pd.Series,
    stressed_daily: pd.Series,
    btc_daily: pd.Series,
    config: Mapping[str, Any],
    authorized: runner_v3.AuthorizedWindow,
) -> dict[str, Any]:
    """Delegate to the frozen metric authority with homogeneous explicit UTC bounds."""

    normalized = dataclasses.replace(
        authorized,
        score_start=_explicit_utc(authorized.score_start),
        score_end_inclusive=_explicit_utc(authorized.score_end_inclusive),
    )
    packet = dict(
        _PARENT_COMPUTE_METRICS(
            base_daily,
            stressed_daily,
            btc_daily,
            config,
            normalized,
        )
    )
    scored_window = packet.get("scored_window")
    if not isinstance(scored_window, runner_v3.EvaluationWindow):
        raise Amendment0001Error("parent metric authority returned an invalid scored window")
    packet["scored_window"] = runner_v3.EvaluationWindow(
        _date_only(authorized.score_start),
        _date_only(authorized.score_end_inclusive),
        scored_window.metrics,
    )
    return packet


def evaluator_authority_sha256(root: Path) -> str:
    """Bind every amended result and journal request to this adapter's exact bytes."""

    parent_sha256 = _PARENT_EVALUATOR_AUTHORITY_SHA256(root)
    amendment_path = Path(__file__).resolve()
    payload = json.dumps(
        {
            "amendment_id": AMENDMENT_ID,
            "amendment_module_sha256": _sha256_file(amendment_path),
            "parent_evaluator_sha256": parent_sha256,
        },
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def install() -> None:
    """Install the correction once after verifying the immutable parent runner."""

    with _INSTALL_LOCK:
        verify_parent_runner()
        if runner_v3._compute_metrics is _PARENT_COMPUTE_METRICS:
            runner_v3._compute_metrics = compute_metrics_with_utc_bounds
        if runner_v3._evaluator_authority_sha256 is _PARENT_EVALUATOR_AUTHORITY_SHA256:
            runner_v3._evaluator_authority_sha256 = evaluator_authority_sha256


__all__ = [
    "AMENDMENT_ID",
    "Amendment0001Error",
    "PARENT_RUNNER_SHA256",
    "compute_metrics_with_utc_bounds",
    "evaluator_authority_sha256",
    "install",
    "verify_parent_runner",
]
