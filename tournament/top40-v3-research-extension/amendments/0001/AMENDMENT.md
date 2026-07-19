# Amendment 0001: pandas-3 UTC metric slicing compatibility

The first development request failed before any metric packet or artifact was produced. The frozen
V3 runner slices a UTC-indexed daily series with `authorized.score_start`, which contains an
explicit `Z`, and `authorized.score_end_inclusive`, which is a date-only string. Pandas 3 raises
`ValueError: Both dates must have the same UTC offset` for this mixed-bound slice.

This prospective amendment:

1. converts both existing authorized bounds to UTC `Timestamp` objects;
2. selects the same inclusive dates with boolean index masks;
3. calls the unchanged V3 metric, regime, and bootstrap functions;
4. preserves the original `EvaluationWindow` start and end strings;
5. installs the compatibility only around one serial runner call and restores the original global
   function in a `finally` block.

It does not change candidate code, data, dates, costs, execution, regimes, metric formulas,
thresholds, trial accounting, or any sealed-stage permission. The failed baseline request remains
the first consumed Team 06 attempt and is not rerun.
