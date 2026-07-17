# Team 10 final pivot-02 — funding-pressure transfer and unwind

Status: **prospective, unregistered, unevaluated**

## Terminal evidence and structural diagnosis

The initial candidate `t10-rtre-core-v1` is terminal from insolvency. Pivot-01 candidate
`t10-dac-core-v1` is terminal after a complete solvent result. Its exact annualized return was
`-0.09328445205038527`, Sharpe `-1.86846407399797`, doubled-cost Sharpe
`-2.436836526128816`, Calmar `-0.30631265956122306`, maximum drawdown
`0.3045399827222629`, positive-quarter fraction `0.14285714285714285`, and trade count `9581`.
Bull, bear, chop, and stress Sharpes were respectively `-1.5124282333375314`,
`-2.200607191286561`, `-3.0617769845946468`, and `-1.5413188398402713`.

Negative evidence in every regime falsifies the volume-anchor convergence premise rather than one
regime classifier. Chop being worst directly contradicts its stated primary role. The large trade
count and further doubled-cost degradation show daily rank turnover compounds the problem. Maximum
drawdown also breaches `0.30`. These facts do not support a literal sign flip, parameter tweak,
neighbor search, or risk overlay.

## Genuine final mechanism change

Pivot-02 removes price-anchor distance and residual confirmation entirely. It uses strictly past
funding transfers as an economic crowding measure. Four lowest-pressure contracts are long; four
highest-pressure contracts are short. Persistent positive funding makes the price-return score
lower because crowded longs both pay the short sleeve and can unwind; low or negative pressure makes
the score higher because long carry is cheaper and crowded shorts can cover.

The schedule changes from daily to weekly, holding horizon from 24h to 168h, and gross from `0.20` to
`0.12`. Price data are an admissibility screen rather than the alpha signal. The exact final score is
captured once by A5 before selection and sizing. These are inseparable properties of the new funding
transfer mechanism, not controls on the terminal price-convergence book.

Expected roles are explicit: low-pressure longs participate in bull, high-positive-pressure shorts
receive funding and unwind in bear, and two-sided transfer/crowding normalization acts in chop. All
roles must pass independently.

Only A6-authorized native crypto base assets may enter. Stablecoin bases and tokenized/synthetic
TradFi, metal, commodity, and index products are excluded even when Binance offers perpetuals; a
stable quote does not change the base asset. Ticker heuristics remain forbidden.

This is pivot two of two. One exact no-control center is authorized. Controls, ablations, and
neighbors are forbidden; failure is DNF. Existing stability thresholds remain unwaived, and no
qualification claim may be made without official evidence.
