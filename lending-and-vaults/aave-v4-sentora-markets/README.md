# What sits in Sentora's Aave v4 markets

On 17 Nov 2026 (Ethereum block 26,433,908), **Sentora's three Aave v4 markets held $155.7M**, rebuilt from their events with HyperSync. RLUSD was the biggest reserve at $70.0M, then USDe at $50.0M and kBTC at $35.7M. In the RLUSD Yield market, $41.8M of the $70.0M RLUSD supplied was borrowed, a utilisation of 59.8%.

| Reserve | Supplied |
| --- | --- |
| RLUSD | $70.02M |
| USDe | $49.98M |
| kBTC | $35.71M |
| Total | $155.71M |

Valued at 17 Nov 2026 prices, the markets passed $100M on 8 Nov, ten days after the first large deposit.

## Why it's interesting

Aave v4 splits lending into a shared liquidity hub and many spokes, and curators like Sentora run their own spokes with their own assets and settings. That makes each curated market a small, self-contained thing you can rebuild from its events alone.

The script shows how. Aave v4 keeps every position in shares, and each `Supply`, `Withdraw`, `Borrow` and `Repay` event carries both the shares and the amount. HyperSync returns all of them since launch in a few seconds, so the script can count the shares in each reserve and turn them into assets with the rate from the latest event. It then reads the same reserves from the spoke so you can see the replay and the chain agree.

## What it pulls

- `Supply`, `Withdraw`, `Borrow`, `Repay`, `LiquidationCall`, `ReportDeficit` and `AddReserve` logs from Sentora's three spokes on Ethereum, from Aave's [address book](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV4EthereumSentoraCurated.sol). Event signatures are from Aave's [ISpoke interface](https://github.com/aave/aave-v4/blob/main/src/spoke/interfaces/ISpoke.sol).
  - RLUSD Yield [`0x9ebf0c19bf7dfe859820cc09e846114b53814e52`](https://etherscan.io/address/0x9ebf0c19bf7dfe859820cc09e846114b53814e52)
  - OUSD Yield [`0xbb97b61ad6747d337e5805f2d159d275bb1f0828`](https://etherscan.io/address/0xbb97b61ad6747d337e5805f2d159d275bb1f0828)
  - Bluechip [`0xa37e7cdc557f3c7f745fb3f337b6439979662c46`](https://etherscan.io/address/0xa37e7cdc557f3c7f745fb3f337b6439979662c46)
- Per reserve, over a public Ethereum RPC, `getReserve()` for the underlying token and decimals and `getReservePrice()` on each spoke's oracle (8 decimals). `getReserveSuppliedAssets()` and `getReserveTotalDebt()` are read only as a check.

The supplied and borrowed totals in the finding and the day-by-day curve come from HyperSync. Supplied is each reserve's supply shares times the rate in its latest `Supply` or `Withdraw`, and borrowed is its drawn shares times the rate in its latest `Borrow`. Every dollar value uses the spoke's own oracle price, read over RPC.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

It takes under a minute. Sample output from a run on 17 Nov 2026.

```
Supplied to Sentora's Aave v4 markets: $155,714,634
  RLUSD  $    70,023,066
  USDe   $    49,979,772
  kBTC   $    35,711,767
  PYUSD  $            20
  OUSD   $             9
RLUSD borrowed in the RLUSD Yield market: $41,839,131 of $70,022,881 supplied (59.8% utilization)
Supplied, day by day (USD at today's prices, principal)
  2026-10-22               100
  ...
  2026-10-29        17,043,846
  ...
  2026-11-08       100,437,669
  ...
  2026-11-13       164,321,014
  ...
  2026-11-17       155,663,810
Check (RPC getReserveSuppliedAssets and getReserveTotalDebt at block 26,433,908)
  RLUSD Yield RLUSD  supplied    70,026,818.30  RPC    70,027,095.92  gap    -277.62  |  borrowed    41,841,483.78  RPC    41,861,497.16  gap -20,013.38
  RLUSD Yield USDe   supplied    49,999,999.34  RPC    49,999,999.34  gap       0.00  |  borrowed             0.00  RPC             0.00  gap       0.00
  ...
```

The script always reads up to the latest block, so your numbers will differ.

## Change the window or chain

- **Start block.** The query starts at `from_block` 23,000,000, before Aave v4 went live on Ethereum. Raise it to look at a recent stretch only.
- **Other spokes.** Swap the `SPOKES` dict for any other Aave v4 spoke and its oracle. The address book has one file per market in [src](https://github.com/bgd-labs/aave-address-book/tree/main/src).
- **Other chains.** Change `HYPERSYNC` to that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and `RPC` to a public RPC on the same chain.

## Check the numbers

The script checks itself. For every reserve it prints the supplied and borrowed amounts rebuilt from HyperSync next to `getReserveSuppliedAssets()` and `getReserveTotalDebt()` read over RPC at the same block. On 17 Nov 2026 supplied matched to within $278 of $70.0M RLUSD, the interest earned since the reserve's last event. Borrowed sat $20K (0.05%) below `getReserveTotalDebt()`, because the events give drawn debt only and the RPC figure also counts Aave v4's premium debt and interest since the last borrow. You can also call `getReserveSuppliedAssets` on any spoke from its [Etherscan](https://etherscan.io/address/0x9ebf0c19bf7dfe859820cc09e846114b53814e52) page, or compare the totals with the markets in the [Aave app](https://app.aave.com).

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to replay every Supply, Withdraw,
Borrow and Repay on Sentora's three Aave v4 spokes on Ethereum and rebuild supplied
and borrowed per reserve from shares. My HyperSync token is in the ENVIO_API_TOKEN
environment variable.

Print a daily series of supplied and borrowed for the RLUSD Yield market, valuing
shares with the rate in the last event of each day. Keep the standard library only.
Then check the last day against getReserveSuppliedAssets() and getReserveTotalDebt()
at the same block and explain any gap.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Aave v4 docs](https://aave.com/docs/aave-v4)
- [Aave v4 source](https://github.com/aave/aave-v4)
- [Aave address book for Sentora's markets](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV4EthereumSentoraCurated.sol)
- [Envio Discord](https://discord.gg/envio)
