# Metric's first month on Ethereum

Pulls every swap on [Metric](https://metric.xyz)'s Ethereum pools with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview) and prints swaps, wallets and volume per day.

## What we found

Metric went public on 15 Oct 2026 and [said a month later](https://x.com/metricxyz/status/2121990150112645232) that it had traded $8.0B across all its chains. On Ethereum alone, from 15 Oct to 15 Nov 2026:

- $2.80B traded in 166,657 swaps
- 17,360 wallets sent those swaps
- Daily volume averaged $47.6M in the first full week (16 to 22 Oct) and $198.9M in the latest one (9 to 15 Nov), which is 4.2x
- The biggest day was 13 Nov at $284.8M, with 2,178 wallets trading
- USDC/USDT is the largest pair at $2.02B, then WETH/USDC at $384M and WETH/USDT at $149M

## How volume is counted

One side of each swap, in dollars. If either token in the pool is a dollar stablecoin, the volume is the stablecoin amount that moved. For the few pools with no stablecoin (WSTETH/WETH, WBTC/WETH and similar) it is the token0 amount at the price Metric's API reports today. Those pools are under 1% of the total. "Wallets" are the addresses that sent the swap transactions, so a router or solver that trades for many users counts once.

## Why it matters

Metric's pools take their price from a live feed, so the same liquidity trades many times a day and volume runs far ahead of TVL. To see that for yourself you need every `Swap` event from every pool, with the sender of each transaction. HyperSync returns the logs, their transactions and block times in one query, so the whole month comes back in a few minutes.

## What it pulls

| | |
|---|---|
| Pools | The 49 Ethereum pools from Metric's public API, `GET https://api.metric.xyz/public/v1/evm/1/metadata` ([API docs](https://docs.metric.xyz/reference/api/metadata)) |
| Factory | `MetricOmmPoolFactory` `0x2a53833cc95548cf52c7b159110e22D3a9018f32` ([contract addresses](https://docs.metric.xyz/reference/supported-chains-and-deployments)) |
| Event | `Swap(address indexed sender, address indexed recipient, uint256 details, uint256 amountDeltas, uint256 platformFees)`, topic0 `0x9734819749a91fc3be03ea83205f924ee08479bd3f0da48efc91d94d050cac1e` |
| Amounts | `amountDeltas` packs two int128 values: token0's change in the top 128 bits, token1's in the bottom 128 |
| Joined | Each log's transaction (`from`) and block (`timestamp`) |

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). There are no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
FROM_DATE=2026-11-01 TO_DATE=2026-11-15 python script.py
```

It writes the daily table to `metric_ethereum_daily.json`, which is included here from the 16 Nov run.

## Check the numbers yourself

- **Daily volume:** DefiLlama's [Metric V1 page](https://defillama.com/protocol/metric-v1) has an Ethereum series. It reads $284.5M on 13 Nov, $251.4M on 14 Nov and $241.8M on 15 Nov, against $284.8M, $252.0M and $241.4M here.
- **Swap count:** call `eth_getLogs` on any Ethereum RPC for one pool and the Swap topic. For the USDC/USDT pool `0xaef2ad7aBB651945e6D24276715f25BDED0ad41e`, blocks 26,400,000 to 26,402,000, both an RPC and HyperSync return 426 swaps.
- **Single swaps:** open any transaction hash on Etherscan and compare the token transfers with the decoded amounts.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview, endpoint https://eth.hypersync.xyz/query)
to pull every Metric swap on Ethereum. Get the pool list from
https://api.metric.xyz/public/v1/evm/1/metadata?count=50 (page with offset). Query logs for those pool
addresses with topic0 0x9734819749a91fc3be03ea83205f924ee08479bd3f0da48efc91d94d050cac1e from block
26187000, selecting the log data, the transaction's from address and the block timestamp. Page with
next_block and retry on HTTP 429. My API token is in ENVIO_API_TOKEN. Decode amountDeltas (second data
word) as two int128 values, token0 in the top half and token1 in the bottom half, and print swaps,
unique senders and dollar volume per day, counting the stablecoin side. Then do the same for BNB Chain
(chain id 56, https://bsc.hypersync.xyz).
```

To keep it live, scaffold a HyperIndex project with `pnpx envio init` and index the factory's pools. `envio init` adds Envio's agent skills to the project's `.claude/skills/` folder, so your agent has the docs in context ([Quickstart with AI](https://docs.envio.dev/docs/HyperIndex/quickstart-with-ai)).

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview) and [supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [HyperIndex on Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service)
- [Metric docs](https://docs.metric.xyz), [contract addresses](https://docs.metric.xyz/reference/supported-chains-and-deployments) and [swapping via the pool](https://docs.metric.xyz/reference/smart-contracts/swapping-directly-via-pool)
- Questions: [Envio Discord](https://discord.gg/envio)
