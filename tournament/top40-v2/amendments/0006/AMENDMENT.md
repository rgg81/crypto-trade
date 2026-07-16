# Top-40 V2 Amendment 0006 — pure-crypto-only universe

Status: **DRAFT — INDEPENDENT REVIEW, FREEZE, AND INTEGRATION REQUIRED**

## Decision

The Top-40 V2 universe is restricted to native crypto assets. A Binance USD-M listing is not, by
itself, evidence that an instrument is crypto. Stablecoins, leveraged tokens, tokenized metals or
commodities, equities, ETFs, indexes, foreign exchange, premarket instruments, and other direct
TradFi exposures are ineligible even when Binance offers them as perpetual contracts.

This amendment certifies the already-frozen snapshot; it does not rebuild it, change a liquidity
rank, alter a historical result, or silently modify the frozen snapshot builder. The audit must
pass before and after every active command. The existing active entrypoint remains unchanged while
this draft is reviewed.

## Exact data authority

The audit accepts only these bytes:

| Authority | Rows | Bytes | SHA-256 |
| --- | ---: | ---: | --- |
| `tournament/top40/data_manifest.json` | 12 files | 6,541 | `077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3` |
| `data/top40/snapshot-v1/membership.parquet` | 12,866 | 134,866 | `f51c9eb207c1da51cc4b9ff6045bb5e914828015b5c9c214f0e2673cd868eb14` |
| `data/top40/snapshot-v1/contract_metadata.parquet` | 667 | 15,984 | `0995d50011e73de880358b994031fdf8bb58e75ab8901de2c5601e7abed05243` |
| `data/top40/snapshot-v1/exchange_info.json` | 832 | 1,682,464 | `aab4219452e61cfa5e135518ed182c98fd7e527d13bc240e891bb6b550deeb64` |

The manifest must itself contain the same exact path, row, size, and hash bindings. Each file is
opened descriptor-relatively without following symlinks, must be a bounded regular file with a
stable inode/size/mtime across the read, and is parsed only from bytes whose SHA-256 was verified.
The repository-owned manifest and amendment authorities must be single-link files. The three
binary snapshot files retain their intentional cross-worktree hard links and therefore rely on
the descriptor checks plus exact frozen size and SHA-256 rather than a single-link requirement.

## Eligibility rule

Every one of the 667 contract-metadata candidates and every distinct weekly membership symbol
must pass. For a current `exchangeInfo` entry, eligibility is the conjunction of all of these
conditions:

1. The symbol is exact uppercase ASCII `[A-Z0-9]+USDT`, with a nonempty base.
2. `baseAsset` exactly equals the symbol base, and `quoteAsset` and `marginAsset` are exactly
   `USDT`.
3. `contractType` is exactly `PERPETUAL`; values such as `TRADIFI_PERPETUAL` do not match.
4. `underlyingType` is exactly `COIN`.
5. The exact base is not a reviewed stablecoin, leveraged-token, metal, or commodity base.
6. No normalized subtype is exactly TradFi, ETF, Index, Pre-IPO, Commodity, Equity, Stock,
   Forex/FX, Metal, Metals, or Precious Metal.
7. The frozen metadata classification exactly mirrors the current exchange entry.

The subtype denylist is defense in depth, not an open-world classifier. Exact `PERPETUAL` and
`COIN` equality are primary, and any new or unknown direct exposure requires a new reviewed
classification before a future snapshot may include it.

Stablecoin matching is by exact base, never by substring or suffix. In particular, `FRAX` is not
the `frxUSD` stablecoin: `FRAXUSDT` is the renamed scarce native FRAX asset (formerly FXS) and is
not denied. Likewise, native tokens such as `S`, `M`, `ENA`, `SKY`, `STBL`, `USUAL`, and `RESOLV`
are not rejected merely because their projects relate to stablecoins or real-world assets.

Binance's `RWA` subtype is a crypto-sector label and is not forbidden on its own. `CFGUSDT` and
`MANTRAUSDT` are native protocol tokens and remain eligible when all exact contract checks pass.
Direct commodity-backed tokens such as `PAXGUSDT` and `XAUTUSDT` are rejected at the asset level;
direct commodities such as `XAUUSDT` also fail the exact contract and underlying-type checks.

## Archive-only authority

Binance does not publish complete historical `exchangeInfo`. An archive-only contract is accepted
only if metadata says exact `PERPETUAL`, `USDT` quote and margin, `ARCHIVE_INFERRED_COIN`, and
`archive_inference`, and the complete archive-only set equals this independently reviewed list:

```text
1000BTTCUSDT AKROUSDT ANCUSDT ANTUSDT AUDIOUSDT BDXNUSDT BTSUSDT BTTUSDT
BZRXUSDT COCOSUSDT DODOUSDT EOSUSDT FRONTUSDT GALUSDT HNTUSDT KEEPUSDT
LENDUSDT LUNAUSDT MATICUSDT MBLUSDT NUUSDT RNDRUSDT SRMUSDT SXPUSDT
TOMOUSDT YFIIUSDT
```

An unlisted archive-only symbol fails closed. A missing reviewed symbol also fails, preventing a
quiet change to the scope of inference.

## Deterministic evidence

`pure_crypto_universe_v6.audit_pure_crypto_universe` returns a canonical, timestamp-free report.
It binds all four authorities and reports candidate/member counts, current versus archive-only
classifications, every current `underlyingType`, non-COIN exclusions by type, defense-in-depth
subtype exclusions, and the accepted RWA-sector symbols. A successful report contains no
violations; any classification uncertainty raises and produces no passing report.

The expected frozen-snapshot invariants are 667 candidate symbols, 26 archive-only candidates,
641 current candidates, 12,866 membership rows, 321 distinct members, 303 current members, 18
archive-only members, and zero violations. The exact canonical report SHA-256 must be recorded by
independent review before freeze.

## Integration and lifecycle

`amendment_0006_v2.run` is a non-active wrapper candidate, exposed for review at
`scripts/top40_v2_tournament_pure_crypto_v6.py`. It verifies the exact frozen Amendment
0004 runner, obtains the pure-crypto report, delegates the command, repeats both verifications
after success, failure, or interruption, and requires the two report byte strings to be identical.
It also SHA-pins the audit-module bytes and captures every audit callable identity used by the
wrapper. `scripts/top40_v2_tournament_v6_candidate.py` is the additive entrypoint candidate; the
historical active path does not import it yet.

Amendment 0004 may atomically publish a legitimate result before the wrapper reaches its post-run
check. Amendment 0006 does not claim it can roll back that publication. Safety relies on the exact
immutable pre-audit, Amendment 0004's own snapshot-manifest and file-hash verification during the
operation, and the unconditional post-audit/authority check that makes any discrepancy terminal
and visible.

Activation requires, in order:

1. serialized tests against the real frozen snapshot and focused adversarial fixtures;
2. independent static review of the exact implementation bytes and canonical report;
3. an immutable amendment freeze binding implementation, review, report, and parent authority;
4. a separately reviewed active-entrypoint replacement and integration freeze; and
5. rebasing any still-draft downstream amendment, including Amendment 0005, onto the new active
   authority.

Registrations and result-bearing runs should remain paused until those steps complete. Builder
hardening for future snapshots is a separate prospective change: it may reuse this policy, but it
cannot edit the Phase-0 builder or manifest under this certification amendment.
