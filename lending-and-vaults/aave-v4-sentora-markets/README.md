# What sits in Sentora's Aave v4 markets

On 16 Nov 2026 (Ethereum block 26,427,832), **Sentora's three Aave v4 markets held $156.7M**. RLUSD was the biggest reserve at $71.0M, then USDe at $50.0M and kBTC at $35.7M. In the RLUSD Yield market, $41.9M of the $71.0M RLUSD supplied was borrowed, a utilisation of 58.9%.

| Reserve | Supplied |
| --- | --- |
| RLUSD | $71.03M |
| USDe | $49.97M |
| kBTC | $35.74M |
| Total | $156.74M |

Valued at today's prices, the markets passed $100M on 8 Nov, ten days after the first large deposit.

## Why it's interesting

Aave v4 splits lending into a shared liquidity hub and many spokes, and curators like Sentora run their own spokes with their own assets and settings. That makes each curated market a small, self-contained thing you can rebuild from its events alone.

The script shows how. Every reserve's principal is the sum of its `Supply` events minus its `Withdraw` events, and HyperSync returns all of them since launch in a few seconds. It then reads the same reserves from the spoke so you can see the replay and the chain agree.

## What it pulls

- `Supply`, `Withdraw`, `Borrow` and `AddReserve` logs from Sentora's three spokes on Ethereum, from Aave's [address book](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV4EthereumSentoraCurated.sol). Event signatures are from Aave's [ISpoke interface](https://github.com/aave/aave-v4/blob/main/src/spoke/interfaces/ISpoke.sol).
  - RLUSD Yield [`0x9ebf0c19bf7dfe859820cc09e846114b53814e52`](https://etherscan.io/address/0x9ebf0c19bf7dfe859820cc09e846114b53814e52)
  - OUSD Yield [`0xbb97b61ad6747d337e5805f2d159d275bb1f0828`](https://etherscan.io/address/0xbb97b61ad6747d337e5805f2d159d275bb1f0828)
  - Bluechip [`0xa37e7cdc557f3c7f745fb3f337b6439979662c46`](https://etherscan.io/address/0xa37e7cdc557f3c7f745fb3f337b6439979662c46)
- Per reserve, over a public Ethereum RPC, `getReserve()` for the underlying token and decimals, `getReservePrice()` on each spoke's oracle (8 decimals), `getReserveSuppliedAssets()` and `getReserveTotalDebt()`.

The replay and the day-by-day curve come from HyperSync. The supplied and borrowed totals in the finding are read from the spokes over RPC, so they include interest, and every dollar value uses the spoke's own oracle price, also read over RPC.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

It takes under a minute. Sample output from a run on 16 Nov 2026.

```
Supplied to Sentora's Aave v4 markets: $156,738,235
  RLUSD  $    71,029,780
  USDe   $    49,971,696
  kBTC   $    35,736,729
  PYUSD  $            20
  OUSD   $             9
RLUSD borrowed in the RLUSD Yield market: $41,854,282 of $71,029,595 supplied (58.9% utilization)
Supplied, day by day (USD at today's prices)
  2026-10-22               100
  ...
  2026-10-29        17,043,483
  ...
  2026-11-08       100,428,398
  ...
  2026-11-13       164,159,866
  ...
  2026-11-16       156,691,625
Checks at block 26,427,832
  RLUSD Yield RLUSD  replayed    70,988,487.30  onchain    71,035,099.94  interest  46,612.64
  RLUSD Yield USDe   replayed    49,999,999.34  onchain    49,999,999.34  interest       0.00
  ...
```

The script always reads up to the latest block, so your numbers will differ.

## Change the window or chain

- **Start block.** The query starts at `from_block` 23,000,000, before Aave v4 went live on Ethereum. Raise it to look at a recent stretch only.
- **Other spokes.** Swap the `SPOKES` dict for any other Aave v4 spoke and its oracle. The address book has one file per market in [src](https://github.com/bgd-labs/aave-address-book/tree/main/src).
- **Other chains.** Change `HYPERSYNC` to that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and `RPC` to a public RPC on the same chain.

## Check the numbers

The script checks itself. For every reserve it prints the replayed principal from HyperSync next to `getReserveSuppliedAssets()` from RPC at the same block, and the gap is interest earned since each deposit. You can also call `getReserveSuppliedAssets` on any spoke from its [Etherscan](https://etherscan.io/address/0x9ebf0c19bf7dfe859820cc09e846114b53814e52) page, or compare the totals with the markets in the [Aave app](https://app.aave.com).

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to replay every Supply, Withdraw
and Borrow on Sentora's three Aave v4 spokes on Ethereum, then reads each reserve's
supplied assets, debt and oracle price with eth_call. My HyperSync token is in the
ENVIO_API_TOKEN environment variable.

Add Repay events (from the ISpoke interface in github.com/aave/aave-v4) so the
replay also rebuilds net borrowed per reserve, and print a daily series of
supplied and borrowed for the RLUSD Yield market. Keep the standard library only.
Then check the replayed debt against getReserveTotalDebt() at the same block and
explain any gap.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Aave v4 docs](https://aave.com/docs/aave-v4)
- [Aave v4 source](https://github.com/aave/aave-v4)
- [Aave address book for Sentora's markets](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV4EthereumSentoraCurated.sol)
- [Envio Discord](https://discord.gg/envio)
