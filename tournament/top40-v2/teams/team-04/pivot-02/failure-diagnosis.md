# BER zero-trade diagnosis

## Observed visible-IS evidence

The completed `team-04-ber-reference-001` development run reported 3,732 decisions, zero trades,
net Sharpe `0`, annualized return `0`, doubled-cost Sharpe `0`, and zero Sharpe in bull, bear, chop,
and stress. That is terminal under BER's preregistered falsifier. No control can manufacture alpha
from a book that never forms.

## Static failure chain

BER did not distinguish organizer UTC storage conventions from malformed time. Its timestamp
normalizer rejected every timezone-naive timestamp. Its feature extractor then demanded one and
only one row for every member of a hand-built 73-close grid, including exact open and close-time
equalities, for at least 24 symbols at the same scheduled decision. Any convention mismatch made
the whole scheduled cross section empty. The only downstream path was
`score_boundary({}) -> {}`; portfolio construction therefore never ran.

In particular, a valid Binance-style inclusive close timestamp can be one millisecond before the
next eight-hour boundary rather than exactly `open_time+8h`; BER rejected that representation too.
Either that mismatch or timezone-naive organizer storage is sufficient to reproduce the observed
all-empty path. The result does not identify which representation dominated without inspecting
prohibited report data, so PARD removes both assumptions.

The all-zero result proves a global availability gate failed on every opportunity. Static source
shows the timestamp/grid gate is upstream of every score and is sufficient to produce exactly that
result. The run provides no evidence for or against the economic reversal sign because BER never
held exposure.

## PARD repair boundary

PARD is a new economic mechanism, not a BER patch. It removes shock reversal and its exact-open
grid. It reads only causal `close_time` and `close` fields; normalizes aware, timezone-naive, and
numeric organizer UTC encodings; sorts actual completed observations; requires a contiguous 8-hour
suffix; permits at most two bars of staleness; and excludes an individual symbol before applying a
20-name cross-sectional minimum. Synthetic tests explicitly make timezone-naive organizer frames
the reference case so the BER failure mode cannot hide behind aware-only fixtures again.

This availability repair is necessary but not sufficient evidence. PARD must still produce
nonempty A5 score rows, trades, positive net and doubled-cost IS Sharpe, positive annualized return,
and positive bull, bear, and chop performance. Otherwise its family terminates before controls.
