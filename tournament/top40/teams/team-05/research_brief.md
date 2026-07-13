# T05-AER12-H80-R72-v1 — auction-excursion rejection

**Hypothesis.** Repeated recovery from scale-free lower excursions reveals persistent auction support, while repeated rejection of upper excursions reveals supply; after removing ordinary return, volatility, liquidity, beta, and funding exposures, the former should outperform the latter over the next 8h.

## Frozen specification

At decision `t`, use only 8h transaction bars with `close_time <= t`; the fill is the hidden transaction open at `t` and label is `y(i,t)=log(O(i,t+8h)/O(i,t))`. For a completed bar `j`, require an immediately preceding bar (`open_time[j]-open_time[j-1]=8h`), valid positive OHLC, and `rho=TR/Cprev>1e-8`, where `TR=max(H,Cprev)-min(L,Cprev)`. Define

`u=(H-max(O,C))/TR`, `d=(min(O,C)-L)/TR`, `b=(C-O)/TR`, and `q=(d-u)*(1+0.5*sign(d-u)*b)`.

Thus gaps enlarge `TR` but are neither wick nor body; a missing/nonadjacent predecessor makes `q` missing. Over the last 12 scheduled bars require at least 9 valid values, then `A=median(q)*abs(mean(sign(q)))`. No imputation crosses a gap.

Every adjacent close return is logarithmic: `r(i,k)=log(C(i,k)/C(i,k-1))`, defined only when the two bar opens are exactly 8h apart. The 24h and 7d nuisances are respectively the sums of the last 3 and 21 contiguous `r` values; any missing value invalidates that horizon. Annualized 21-bar close volatility is `sqrt(1095*mean(r^2))` (at least 18 valid values among the last 21 scheduled slots); log median quote volume uses those 21 slots (18 minimum). For beta, take the last 63 scheduled adjacent-return slots ending at the latest closed bar and let `V` be the aligned valid symbol/BTC pairs, requiring `|V|>=50`. With means computed only on `V`, `beta=sum_V((r_i-mean(r_i))*(r_B-mean(r_B)))/sum_V((r_B-mean(r_B))^2)`; require `sum_V((r_B-mean(r_B))^2)/|V|>1e-12`, otherwise the symbol is invalid. The last actual funding rate must be strictly before `t` and no older than 16h (otherwise zero plus a missing indicator). BTC absence or fewer than 10 fully valid names requests flat `{}`.

Cross-sectionally transform each column by `z=clip((x-median)/(1.4826*MAD),-3,3)`; a zero-MAD nuisance is zero, but `MAD(A)=0` returns flat `{}` because no cross-sectional alpha dispersion exists. With symbol ordering ascending, let `X=[1,z(r24),z(r7d),z(vol),z(logQV),z(beta),z(funding),funding_missing]` and `e=z(A)-X*pinv(X,rcond=1e-10)*z(A)`. Funding is only a nuisance/cashflow control, not the alpha thesis. Rank `e` ascending with symbol tie-break into percentile `p=(rank-1)/(N-1)`.

Stateful tail hysteresis uses prior requested sets. Retain longs while `p>=0.55` and shorts while `p<=0.45`; keep the strongest at most `K=min(6,max(2,ceil(0.15N)))` per side, then fill vacancies from new `p>=0.80` longs or `p<=0.20` shorts in extreme-score/symbol order. If either side has fewer than two names, return `{}`.

An independent risk state uses completed BTC bars: `v=sqrt(1095/(4*log(2))*mean(log(H/L)^2))` over the last 90 slots, 75 minimum. Enter stress at `v>0.80`, exit only at `v<0.65`, retain state at equality, and assume stress when unavailable. Gross ceiling `G` is 0.72 normally and 0.36 in stress.

On a rebalance, let `g=min(G/2,0.06*min(nLong,nShort))`, desired `d_i=+g/nLong` or `-g/nShort`, and solve, in sorted-symbol order,

`min sum((w-d)^2)+4*sum((w-w_prev)^2)`

subject to `sum(w)=0`, `sum(side_i*w_i)=2g`, `z(beta)'w=0`, `z(funding)'w=0`, and `0<=side_i*w_i<=0.08`. Use deterministic SLSQP (`ftol=1e-12`, `maxiter=500`, start `d`); accept only success and equality residual `<=1e-8`. Omit a zero-MAD factor constraint. If infeasible, drop funding neutrality; if still infeasible, drop beta neutrality; if still infeasible, return `{}`. Record fallback level. Evaluate every 8h; emit a mapping only when selected sets, PIT membership, or stress state changes, or 72h elapsed since the last mapping; otherwise return `None` and hold quantities. Membership loss removes the symbol immediately from the mapping.

## Reality, validation, and decision rule

The evaluator charges actual events `funding_pnl=-signed_mark_notional*rate` to the carried position before same-boundary rebalance, 5 bp taker fee plus 2.5 bp slippage per executed side (15 bp combined at 2x costs), next-open fills, and a 0.10% prior-24h quote-volume fill cap. Unfilled gaps persist. PIT Top-40 Monday membership governs both sleeves; suspension/delist exits are participation-capped and any residual receives the common adverse settlement. Current exchange filters are not backfilled; forward paper applies then-current filters.

Use seven expanding IS folds with half-open validations `[2021-01-01,2021-07-01)`, `[2021-07-01,2022-01-01)`, `[2022-01-01,2022-07-01)`, `[2022-07-01,2023-01-01)`, `[2023-01-01,2023-07-01)`, `[2023-07-01,2024-01-01)`, and `[2024-01-01,2024-07-01)` UTC; training begins 2020-02-03 and ends before each validation. Purge the preceding 8h label and exclude the first 24h after every validation from all later training. Reset strategy/QP state per fold. Seed is `20260713`; trial namespace seed is `2026071305`. The complete predeclared grid is `L in {6,12,21} x entry in {0.75,0.80} x retention in {(0.50,0.50),(0.55,0.45)} x Kmax in {4,6} x stress multiplier in {0.50,0.75} x refresh in {24h,72h}` = 96 configurations, including ablations; public-OOS views are zero.

One vectorized IS-only feasibility screen (not a canonical score) found mean next-bar rank IC `+0.0083` (`t=3.56`) and 99.16% notional within the fill proxy, but naive continuous 8h remapping had price Sharpe 0.13, turnover 0.331 gross/8h, and net Sharpe -2.27. That mapping is rejected; tail hysteresis is essential.

QE accepts only if invariance tests pass byte-for-byte; QP level 1 occurs on at least 95% of nonflat rebalances; mean target L1 turnover is `<=0.04/8h`; OOF net Sharpe is `>=0.75`, OOF 2x-cost Sharpe `>=0.25`, max drawdown `<=0.30`, positive-quarter fraction `>=0.625`; and both realized sleeves satisfy the charter exposure/notional floors. Falsify if any gate fails, median fold net return is nonpositive, or IC is nonpositive in at least four folds. No OOS access is permitted before this gate.
