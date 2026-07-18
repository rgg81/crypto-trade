# Amendment 0003 scored-stage concatenation addendum

Status: prospective until the unique stage-stitch freeze commit is verified.

The frozen Amendment 0003 implementation failed closed before publishing a report because it
required the validation replay's unscored training prefix to equal the standalone scored train
artifact. That requirement is incorrect at a stage boundary: the standalone train run performs
its authorized end-of-stage settlement, while the validation replay continues state through the
same date. The date grids matched, but the prefixes were therefore not identical.

This addendum does not change any model, metric, threshold, split, cost, seed, data authority, or
released validation packet. It implements the charter's predeclared construction literally:

1. use the immutable train run's scored daily returns through 2022-06-30;
2. use only the released validation run's scored daily returns from 2022-07-01 through
   2023-06-30;
3. concatenate those non-overlapping stages on the exact UTC daily grid; and
4. apply the already-frozen V3 public qualification factory.

The validation replay prefix remains useful only as warm-up and state-continuation evidence. It is
not substituted for IS and is not disclosed. Before the corrected calculation, the addendum
freeze binds the unchanged parent activation, released validation journal, committed addendum
bytes, and focused tests. The final report remains aggregate-only.
