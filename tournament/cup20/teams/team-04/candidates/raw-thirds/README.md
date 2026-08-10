# raw-thirds

The mandate's decisive ablation: `baseline-thirds` with one constant changed.

`MARKET_REMOVAL = 0.0` instead of `1.0`, so the cross-section is ranked on the trailing 63-bar
raw log return rather than on the same return with an estimated market component removed.
Everything else -- the beta regression that decides which names have enough history to be ranked,
the skip, the sleeve widths, the cadence, the phase, the risk policy -- is byte-identical to the
baseline. If this book performs like the residual book, the lane is a beta ranking with extra
steps, and that is the thing worth knowing before anything else.
