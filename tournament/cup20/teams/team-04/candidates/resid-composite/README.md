# resid-composite

`resid-narrow-short` with the formation horizon stopped being a single choice.

The cross-sectional score is the average of three market-residual momentum scores -- formation
windows of 42, 63 and 126 bars, all derived at import from the one `FORMATION_BARS` constant so a
neighbourhood point moves all three together -- each standardised across the cross-section before
averaging. Cadence returns to 21 bars, phase 10; the short sleeve stays at a fifth of the
cross-section against a long third, because that is what made `short_gross_pnl` positive on
trial #32.

The point of the composite is not a better horizon. It is that a single formation length is a
free parameter with a best in-sample value, and averaging three removes the choice rather than
optimising it.
