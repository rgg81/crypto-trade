# Team 05 final LDM pivot-02 QE plan

Status: prospective. Synthetic tests are not performance evidence.

The operative tests must establish:

1. future append and future corruption invariance;
2. exact `open_time + 8h <= decision_time` availability and numeric-millisecond equivalence;
3. contiguous-grid, staleness, duplicate-time, RangeIndex, and modal-grid rejection;
4. invalid high, low, and quote-volume observations remain unavailable, with exact 95/105 baseline
   and 19/21 recent validity floors, no zero-volume flooring, and explicit range, valid-share-floor,
   and raw-ratio boundary coverage;
5. A6 point-in-time membership exclusion from both impact-share denominators and outputs;
6. mapping, symbol, and eligible-order invariance;
7. synthetic improving/deteriorating depth ordering and exact expected sleeves;
8. invariance to per-symbol price scale and timestamp-wise market-wide volume scale, while
   symbol-specific volume-share migration changes the signal;
9. one direct A5 call with exact built-in finite rank scores, key/value rejection, and proof that
   returned scores drive span and selection;
10. Unix-anchor 168-hour schedule, canonical seed, exact 0.36 gross, zero net, 4% cap, and dynamic
    five-to-eight symbol sleeves;
11. open, close, signed flow, funding, auxiliary, position, and regime-label irrelevance;
12. root risk-policy byte identity and exhaustive proof that every organizer control is disabled;
13. exact six-file executable-source enumeration and sandbox/source-bundle acceptance;
14. family/trial schema validation and immutable A5 manifest ancestry.

Run lint, format checking, focused pytest, risk-policy validation, strategy smoke validation, and
the relevant frozen tournament suite serially. Do not run the official development evaluator until
materialization, all three A5 first-adds, A7 final-pivot family registration, final hashes, and A7
trial registration are complete.
