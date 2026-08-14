"""Workaround shim for an ORGANISER-SIDE DEFECT in ``scripts/cup20_evaluate.py``.

The defect
----------
``scripts/cup20_evaluate.py`` calls ``kind_for_mode(...)`` at line 186 but never imports it, so
every scored mode -- point, ablation, neighbourhood, falsification -- dies with
``NameError: name 'kind_for_mode' is not defined`` immediately after the snapshot loads and
immediately before the accepted trial is resolved. Only ``--check`` returns early enough to
survive. The function exists and is correct: it is defined at
``src/crypto_trade/cup20/trials.py:595``, exported from ``crypto_trade.cup20.__init__``, and
``tests/cup20/test_trials.py`` asserts that the string ``"kind_for_mode("`` appears in the script's
own source. Only the import line is missing.

Why this shim rather than a one-line fix to the script
------------------------------------------------------
A team may write only under its own directory; editing an organiser file would be a pre-flight
disqualification, and editing the harness a team is scored by is exactly the thing that must never
be allowed to happen quietly. So nothing outside this directory is touched. This loads the
organiser's own script as a module, binds the missing name to the organiser's own function from the
organiser's own module, and calls the organiser's own ``main()`` with the arguments as given.

No configuration, no scoring logic, no floor, no journal record and no number is affected. The
name bound here is the one the script already intends to call, taken from where the script's own
import block should have taken it. Argument handling, the blindness scan, trial resolution, the
evaluation and the packet are all unmodified organiser code.

This is reported to the organiser in the research certificate. It affects every remaining team and
should be fixed centrally by adding ``kind_for_mode`` to the ``crypto_trade.cup20.trials`` import
block of ``scripts/cup20_evaluate.py``.

Usage: exactly the flags ``cup20_evaluate.py`` takes.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from crypto_trade.cup20.trials import kind_for_mode

REPO = Path(__file__).resolve().parents[5]
SCRIPT = REPO / "scripts" / "cup20_evaluate.py"


def main() -> None:
    spec = importlib.util.spec_from_file_location("cup20_evaluate_organiser", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # __name__ is not "__main__", so main() does not auto-run
    if not hasattr(module, "kind_for_mode"):
        module.kind_for_mode = kind_for_mode
    sys.argv = [str(SCRIPT), *sys.argv[1:]]
    module.main()


if __name__ == "__main__":
    main()
