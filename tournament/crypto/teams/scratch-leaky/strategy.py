"""scratch-leaky — organizer harness self-test (NOT a competitor; deleted pre-Phase-1).

Deliberately cheats three ways; the harness must FAIL it on the right checks:
  1. next-candle close peek        -> truncation/corruption must fail
  2. full-sample z-normalisation   -> truncation must fail
  3. future aux-funding peek       -> truncation/corruption must fail
"""


def build_raw_weights(pn, aux):
    close = pn["close"]
    peek = close.shift(-1) / close - 1.0  # (1) tomorrow's return
    z = (close - close.mean()) / close.std()  # (2) full-sample stats
    f = aux["funding"].shift(-2)  # (3) future funding
    return (peek + 0.001 * z - 10.0 * f).fillna(0.0)
