# Aero on Robinhood Chain and Ethereum, day by day

Aero opened on Robinhood Chain and on Ethereum on the same day, 21 Oct 2026. Over the 25 full UTC days from 22 Oct to 15 Nov 2026, **Aero did $1.70B across 1.69M swaps on Robinhood Chain and $2.02B across 249K swaps on Ethereum**.

| | Robinhood Chain | Ethereum |
| --- | --- | --- |
| Swap volume | $1,696.5M | $2,016.4M |
| Swaps | 1,692,885 | 249,107 |
| Average swap | $1,002 | $8,094 |
| Pools | 114 | 124 |

- Robinhood Chain did 84% of Ethereum's volume with 6.8 times as many swaps.
- Robinhood Chain traded more than Ethereum on 7 of the 25 days.
- In the last 7 days (9 to 15 Nov) Robinhood Chain did $563.2M across 656K swaps and Ethereum did $667.4M across 81K.

## Why it's interesting

The same DEX went live on two chains on the same day, so it's a clean comparison. Volume says the two are close. The swap count says the trading looks very different, with lots of everyday-size trades on Robinhood Chain and fewer, bigger ones on Ethereum. If you're building on either chain, that's the kind of flow to expect, and you only see it when you read every swap rather than a daily total.

It's also a nice pattern to reuse. Find every pool from the factories' `PoolCreated` events, then pull every `Swap` from those pools, all from HyperSync with no node.

## What it pulls

- `PoolCreated` logs from Aero's three factories on each chain. The addresses come from Aero's [deployment addresses](https://github.com/dromos-labs/metadex-slipstream-public/tree/main/deployment-addresses) (`cl-robinhood.json`, `pools-robinhood.json`, `cl-ethereum.json` and `pools-ethereum.json`).
  - CL pool factory on Robinhood Chain, `0xc63d7338c178e805c544b8f897066bd3bbcbe136`
  - CL pool factory on Ethereum, [`0xf4fd2e6c5b60c5b365cd1b96dd6245e6d60414c2`](https://etherscan.io/address/0xf4fd2e6c5b60c5b365cd1b96dd6245e6d60414c2)
  - Volatile pool factory, `0x8e6a9fcd1d638cc760ffba397605fe3355de76d2`, and stable pool factory, `0x78589e876edcebdce72ee3436ab3c9ad3a7cef2d`, at the same address on both chains
- Every `Swap` log from those pools (the CL and the classic pool event), joined to each transaction's sender and each block's timestamp.
- Each token's `decimals()`, read with one `eth_call` per token over the chain's public RPC.

Robinhood Chain has other factories that emit the same `PoolCreated` event, so only these three addresses count.

Volume is each swap valued on one side. A dollar stablecoin counts at $1 (USDG on Robinhood Chain, and USDC, USDT, DAI, crvUSD, frxUSD, USDe and USDS on Ethereum). Otherwise the script uses WETH or BTC, priced from Aero's own stablecoin pools at the time of the swap, and then any other token priced from its Aero pool. A few swaps with no dollar route stay unpriced. Wallets are the distinct senders of transactions that contain a swap, so routers and bots count too. Days are UTC.

Every number in the finding comes from HyperSync. Prices come from Aero's own pools, so there's no outside price feed.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py              # every full UTC day so far
python3 script.py 2026-11-15   # stop after this day, the window used above
```

The Robinhood Chain pull reads about 22M blocks and 1.7M swaps, so give it around 15 minutes. Sample output from the run with `2026-11-15`.

```
Aero on Robinhood: 114 pools, first swap 2026-10-21, $1,696.5M across 1,693,153 swaps from 31,059 wallets (10 unpriced)
Aero on Ethereum: 124 pools, first swap 2026-10-21, $2,016.4M across 249,232 swaps from 16,003 wallets (140 unpriced)

day          Robinhood     Ethereum   Robinhood as % of Ethereum
2026-10-22  $    24.0M  $    10.7M   225.2%
2026-10-23  $    38.1M  $    21.1M   181.1%
2026-10-24  $    35.3M  $    15.9M   221.5%
...
2026-11-13  $    88.2M  $    91.4M    96.5%
2026-11-14  $    91.1M  $   108.2M    84.2%
2026-11-15  $    83.3M  $    89.8M    92.8%

Robinhood, 2026-11-09 to 2026-11-15: $563.2M, 656,476 swaps, 10,852 wallets, $858 a swap

Ethereum, 2026-11-09 to 2026-11-15: $667.4M, 81,191 swaps, 6,882 wallets, $8,220 a swap
```

The first two lines include the few swaps on 21 Oct, the day the pools opened, which is why their swap counts are a little higher than the table. Set `DUMP=days.json` to also write the daily numbers to a file.

## Change the window or chain

- **End date.** Pass a UTC date as the first argument. The start is always each chain's `first_block`, just before the factories were deployed. The two 7-day lines at the end cover the final 7 days of the table.
- **Chain.** Aero has deployment files for other chains in the same [folder](https://github.com/dromos-labs/metadex-slipstream-public/tree/main/deployment-addresses). Add an entry to `CHAINS` with that chain's HyperSync URL from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), a public RPC, its CL factory, a `first_block`, its stablecoins and its WETH and BTC tokens. Check the volatile and stable factory addresses too, since they may not match on every chain. The side-by-side table in `main()` names Robinhood and Ethereum, so update that as well.

## Check the numbers

Call `allPoolsLength()` on each of the three factories over a public RPC as the comparison. Added up per chain, they match the 114 and 124 pools the script finds. For a single swap, open its transaction on [Etherscan](https://etherscan.io) or the Robinhood Chain explorer and compare the token amounts with the decoded ones.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to find every Aero pool from
the factories' PoolCreated events on Robinhood Chain and Ethereum, then reads
every Swap in those pools and prices it from Aero's own pools. My HyperSync
token is in the ENVIO_API_TOKEN environment variable.

Add Base as a third chain. Take its factory addresses from
https://github.com/dromos-labs/metadex-slipstream-public/tree/main/deployment-addresses
and its HyperSync URL from
https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks. Keep the
standard library only, and change the daily table to show all three chains.
Run it for the last 3 days first, and check the Base pool count against
allPoolsLength() on each Base factory before you trust the totals.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Aero](https://aero.xyz) and its [deployment addresses](https://github.com/dromos-labs/metadex-slipstream-public/tree/main/deployment-addresses)
- [Robinhood Chain docs](https://docs.robinhood.com/chain/)
- [Envio Discord](https://discord.gg/envio)
