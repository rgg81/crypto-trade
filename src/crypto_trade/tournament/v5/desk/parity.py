"""One definition of "does the live desk still agree with the backtest".

Both the healthcheck and the digest import :func:`desk_parity` -- the same function, not two
independently-derived opinions. That is what "the stats and the parity must raise the same signal"
means at the code level: the integrity report and the performance report read one fact, so they
cannot disagree about whether a desk has diverged from the evaluator it is supposed to *be*.

If a third place ever needs to report desk state, call this rather than re-deriving parity from
``attempt.json``. A second implementation of "what counts as a parity break" is precisely how the
guarantee stops holding, and it would hold for long enough that nobody would notice it had stopped.

States
------
``OK``
    The last tick passed, or failed for a reason that is not a parity break -- a fetch timeout, an
    unclosed bar. Parity holds through ``verified_through``, the last published boundary.
``BROKEN``
    The last tick's replay genuinely disagreed with the frozen record. **The worst state a desk can
    report.** It means the live desk and the backtest have diverged, structurally. It outranks every
    other class; escalate above an ordinary LATE or FAIL.
``UNVERIFIED``
    No launch reconstruction and no tick yet. Pre-launch only.

An operational failure is never parity-broken. Conflating a transient fetch error with a genuine
divergence would make the strongest signal in the system noisy, and a noisy alarm is the one that
gets ignored on the day it matters.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

# Exception names that mean the replay disagreed with the frozen record, as opposed to failing.
PARITY_BREAKING = frozenset({"HistoricalParityError", "AppendInvarianceError", "DeskParityError"})

OK = "OK"
BROKEN = "BROKEN"
UNVERIFIED = "UNVERIFIED"


class DeskParityError(RuntimeError):
    """A tick's replay reproduced a different number than the frozen record holds."""


@dataclasses.dataclass(frozen=True, slots=True)
class Parity:
    state: str
    verified_through: str | None
    detail: str

    @property
    def broken(self) -> bool:
        return self.state == BROKEN

    def line(self) -> str:
        through = self.verified_through or "—"
        return f"parity {self.state:<10} verified_through {through}  {self.detail}".rstrip()


def desk_parity(desk_root: str | Path) -> Parity:
    """Read one desk's parity state from its own attempt and boundary records."""

    root = Path(desk_root)
    attempt_path = root / "attempt.json"
    boundary_path = root / "boundary.json"

    verified = None
    if boundary_path.is_file():
        try:
            verified = json.loads(boundary_path.read_text(encoding="utf-8")).get("boundary")
        except json.JSONDecodeError:
            return Parity(BROKEN, None, "boundary.json is unreadable")

    if not attempt_path.is_file():
        if verified is None:
            return Parity(UNVERIFIED, None, "no launch reconstruction and no tick yet")
        return Parity(OK, verified, "published, no attempt record")

    try:
        attempt = json.loads(attempt_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return Parity(BROKEN, verified, "attempt.json is unreadable")

    status = str(attempt.get("status", ""))
    error = str(attempt.get("error_type", ""))
    if error in PARITY_BREAKING:
        return Parity(BROKEN, verified, f"{error}: {str(attempt.get('error', ''))[:160]}")
    if status == "FAILED":
        # An operational failure. Parity still holds through the last published boundary.
        return Parity(OK, verified, f"last tick failed ({error or 'unknown'}), not a parity break")
    return Parity(OK, verified, "last tick reproduced the frozen record")


__all__ = ["BROKEN", "OK", "PARITY_BREAKING", "UNVERIFIED", "DeskParityError", "Parity", "desk_parity"]
