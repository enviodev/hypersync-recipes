# Metric's first month on Ethereum

Metric went public on 15 Oct 2026 and [said a month later](https://x.com/metricxyz/status/2121990150112645232) that it had traded $8.0B across all its chains. On Ethereum alone, from 15 Oct to 15 Nov 2026 (UTC), **$2.80B traded on Metric in 167K swaps, sent by 17.4K wallets**.

- Daily volume averaged $47.6M in the first full week (16 to 22 Oct) and $198.9M in the latest one (9 to 15 Nov), 4.2 times as much.
- The biggest day was 13 Nov at $284.8M, with 2,178 wallets trading.
- USDC/USDT was the largest pair at $2.02B, then WETH/USDC at $384M and WETH/USDT at $149M.

## Why it's interesting

[Metric](https://metric.xyz)'s pools take their price from a live feed, so the same liquidity can trade many times a day. To see that for yourself you need every `Swap` event from every pool, with the sender of each transaction. HyperSync returns the logs, their transactions and block times in one query, so the whole month comes back in a few minutes.

## What it pulls

- **Pools.** The 49 Ethereum pools listed by Metric's public API, `GET https://api.metric.xyz/public/v1/evm/1/metadata` ([API docs](https://docs.metric.xyz/reference/api/metadata)). They're created by `MetricOmmPoolFactory` [`0x2a53833cc95548cf52c7b159110e22D3a9018f32`](https://etherscan.io/address/0x2a53833cc95548cf52c7b159110e22D3a9018f32) ([contract addresses](https://docs.metric.xyz/reference/supported-chains-and-deployments)).
- **Event.** `Swap(address indexed sender, address indexed recipient, uint256 details, uint256 amountDeltas, uint256 platformFees)`, topic0 `0x9734819749a91fc3be03ea83205f924ee08479bd3f0da48efc91d94d050cac1e`, from block 26,187,000 (14 Oct 2026).
- **Amounts.** `amountDeltas` packs two int128 values, token0's change in the top 128 bits and token1's in the bottom 128.
- **Joined.** Each log's transaction (`from`) and block (`timestamp`).

Volume counts one side of each swap, in dollars. If either token in the pool is a dollar stablecoin, the volume is the stablecoin amount that moved. For the few pools with no stablecoin (WSTETH/WETH, WBTC/WETH and similar) it's the token0 amount at the price Metric's API reports when you run the script. Those pools are under 1% of the total. Wallets are the addresses that sent the swap transactions, so a router or solver that trades for many users counts once.

The swaps, wallets and stablecoin volume come from HyperSync. The pool list and the token decimals come from Metric's API, and so does the price for the non-stablecoin pools.

## Run it

You need Python 3.11 or newer (the script uses `datetime.UTC`) and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                                          # 15 Oct to 15 Nov 2026, the window above
FROM_DATE=2026-11-01 TO_DATE=2026-11-15 python3 script.py  # a shorter window
```

It prints the totals, one row per day and the top 8 pairs, and writes the daily table to `metric_ethereum_daily.json`. The copy in this folder is from the 16 Nov run, which looked like this.

```
Metric on Ethereum, 2026-10-15 to 2026-11-15, 49 pools
...
day          swaps  wallets   volume
2026-10-15   1,388      578  $   19.0M
2026-10-16   4,275    1,094  $   65.7M
2026-10-17   4,092      908  $   53.6M
...
2026-11-13   7,995    2,178  $  284.8M
2026-11-14   6,196    1,852  $  252.0M
2026-11-15   5,149    1,485  $  241.4M
```

## Change the window or chain

- **Window.** Set `FROM_DATE` and `TO_DATE` (UTC, both included). The scan always starts at `FROM_BLOCK`, 26,187,000 by default, and runs to the chain head, so for a window well after launch set `FROM_BLOCK` closer to it to save time.
- **Chain.** Metric's API takes a chain id in the path. Change the `1` in `API` to another chain Metric supports, swap `HS` for that chain's HyperSync URL from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), for example chain id 56 and `https://bsc.hypersync.xyz`, and set `FROM_BLOCK` to just before Metric launched there. Check `STABLES` covers that chain's stablecoin symbols.

## Check the numbers

- **Swap count, as the comparison.** Call `eth_getLogs` on any Ethereum RPC for one pool and the `Swap` topic. For the USDC/USDT pool [`0xaef2ad7aBB651945e6D24276715f25BDED0ad41e`](https://etherscan.io/address/0xaef2ad7aBB651945e6D24276715f25BDED0ad41e), blocks 26,400,000 to 26,402,000, both the RPC and HyperSync return 426 swaps.
- **Single swaps.** Open any transaction on [Etherscan](https://etherscan.io) and compare the token transfers with the decoded amounts.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to pull every Swap event from
Metric's Ethereum pools (listed by https://api.metric.xyz/public/v1/evm/1/metadata),
decodes amountDeltas as two int128 values and prints swaps, wallets and dollar
volume per day. My HyperSync token is in the ENVIO_API_TOKEN environment
variable.

Run the same thing on BNB Chain (chain id 56). Take its HyperSync URL from
https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks, change the
API path to chain 56 and set FROM_BLOCK to just before Metric's first pool
there. Keep the standard library only. Run it for 2 days first, then check one
pool's swap count over a 2,000-block range against eth_getLogs on a public BNB
Chain RPC.
```

To keep it live, scaffold a [HyperIndex](https://docs.envio.dev/docs/HyperIndex/overview) project with `pnpx envio init`, index the factory's pools and deploy it on [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service).

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Metric docs](https://docs.metric.xyz), [contract addresses](https://docs.metric.xyz/reference/supported-chains-and-deployments) and [swapping via the pool](https://docs.metric.xyz/reference/smart-contracts/swapping-directly-via-pool)
- [Envio Discord](https://discord.gg/envio)
