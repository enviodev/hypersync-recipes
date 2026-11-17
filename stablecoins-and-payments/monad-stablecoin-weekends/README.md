# Stablecoins on Monad, weekdays and weekends

In the 30 days from 11 Oct to 9 Nov 2026, **$17.49B of dollar stablecoins moved on Monad across 11.5M transfers** from 84.6K sending addresses. Weekdays averaged $701.0M a day and weekends $307.8M a day. The busiest day was Tuesday 13 Oct, at $1.33B.

| | Days | Volume a day | Transfers a day |
| --- | --- | --- | --- |
| Weekdays | 21 | $701.0M | 411,395 |
| Weekends | 9 | $307.8M | 318,571 |

USDC carried $13.07B of the total, then mUSD at $1.26B and AUSD at $1.10B.

## Why it's interesting

Weekday and weekend patterns tell you what kind of activity a chain has. Payments and business flows tend to follow the working week, while trading and games keep going on Saturdays. On Monad, weekend days move less than half the value of a weekday but still carry about three quarters of the transfers, so a lot of smaller transfers keep going all week.

## What it pulls

- Every ERC-20 `Transfer` log on the seven dollar tokens listed on Monad's [tokens and bridges page](https://docs.monad.xyz/developer-essentials/network-information/tokens-and-bridges). Staked and wrapped yield versions are left out.
  - USDC [`0x754704Bc059F8C67012fEd69BC8A327a5aafb603`](https://monadscan.com/address/0x754704Bc059F8C67012fEd69BC8A327a5aafb603), which also matches [Circle's list](https://developers.circle.com/stablecoins/usdc-contract-addresses)
  - AUSD, USDT0, mUSD, USD1, GHO and USDe, with addresses in `TOKENS`
- Every transfer counts once at face value, mints and burns included. A payment that hops through a router counts at each hop, so this is transfer volume, not unique payment value. Days are UTC.

The volumes and counts come from HyperSync. The script uses Monad's public RPC only to find the first and last block of the window.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                  # the last 30 full UTC days
python3 script.py 30 2026-11-10    # the window above
```

The 30-day run reads about 11.5M transfers in 32 parallel chunks. Sample output from the window above, and the full run is in `out.txt`.

```
Stablecoin transfers on Monad, 2026-10-11 to 2026-11-09 UTC (blocks 112,319,869 to 120,886,884)
11,506,430 transfers, $17.49B moved, 84,599 sending addresses

By token:  USDC $13.07B  AUSD $1.10B  USDT0 $988.2M  mUSD $1.26B  USD1 $0.7M  GHO $382.8M  USDe $689.8M

Weekend days: 9, $2.77B total, $307.8M a day, 318,571 transfers a day
Weekdays:     21, $14.72B total, $701.0M a day, 411,395 transfers a day
Weekend share of volume: 15.8%
Busiest day: 2026-10-13 (Tuesday), $1.33B
```

After that it prints the daily table and the top senders and receivers.

## Change the window or chain

- **Window.** The first argument is the number of days and the second is an end date (UTC, not included).
- **Tokens.** Add or drop entries in `TOKENS`, with each token's decimals.
- **Chain.** Change `HS` to another chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), `RPC` to a public RPC on that chain, and `TOKENS` to its stablecoins.

## Check the numbers

Both checks use Monad's public RPC as the comparison.

- **Receipts.** For 35 sampled blocks, `eth_getBlockReceipts` from `https://rpc.monad.xyz` returns the same stablecoin `Transfer` logs as HyperSync, log for log and value for value.
- **Supply.** For all seven tokens, the change in `totalSupply()` between block 112,319,868 and block 120,886,884 equals the mints minus burns HyperSync sees in between.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every Transfer of
Monad's dollar stablecoins over 30 days and compare weekdays with weekends. My
HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add an hour-of-day breakdown in UTC, split into weekdays and weekends, and count
transfers under $10 separately from the rest. Keep the standard library only.
Then check the transfer count for one block against eth_getBlockReceipts on
https://rpc.monad.xyz.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Monad tokens and bridges](https://docs.monad.xyz/developer-essentials/network-information/tokens-and-bridges)
- [Envio Discord](https://discord.gg/envio)
