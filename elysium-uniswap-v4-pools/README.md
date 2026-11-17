# Uniswap v4 pools on Elysium

A [HyperIndex](https://docs.envio.dev/docs/HyperIndex/overview) indexer for every Uniswap v4 pool created on Elysium, Kinetiq's Hyperliquid L2 (chain ID 99901). Elysium opened its public mainnet on 9 Nov 2026 and Uniswap went live there with v2, v3 and v4.

From the PoolManager's deployment on 3 Nov 2026 to Elysium block 5,448,796 (12 Nov 2026, 17:00 UTC), **115,872 Uniswap v4 pools were created on Elysium, and 94.7% of them use a hook**. 109,537 are paired with native HYPE, against 108,201 different tokens. The busiest day was 9 Nov 2026, public mainnet day, with 28,722 new pools.

| Top hooks at block 5,448,796 | Pools |
| --- | ---: |
| `0x6b1216a40b65c83e9c9e18a562c446697b8cf8ec` (Montra) | 93,729 |
| `0xe0def4221b9840a610d4e7d55812a79a6431a8ec` | 4,613 |
| `0x3ab88ddc3cf2a012af88b60828edb4553697e5dc` | 3,405 |

This indexer syncs over Elysium's public RPC, which was how it was built in the chain's first days. Elysium is now on HyperSync as well (`https://99901.hypersync.xyz`).

## Why it's interesting

Most pools on Elysium come from one launchpad hook, which tells you how tokens are being launched there in the chain's first days. The same indexer works on any EVM chain the day it launches, because HyperIndex can sync over plain RPC.

Here's how Elysium compares with three other chains. The Elysium row is the indexer at block 5,448,796. The other rows count every v4 `Initialize` event on each chain's PoolManager (addresses from Uniswap's [deployments list](https://developers.uniswap.org/deployments.json)) as of 12 Nov 2026. They were pulled with HyperSync and again with HyperRPC `eth_getLogs`, which returned the same numbers. The indexer in this folder doesn't produce them.

| Chain | v4 pools | With a hook |
| --- | ---: | ---: |
| Elysium | 115,872 | 94.7% |
| Arbitrum | 27,037 | 18.3% |
| Unichain | 7,801 | 70.7% |
| Ethereum | 198,041 | 24.3% |

## What it indexes and stores

It listens to `Initialize` on the Uniswap v4 PoolManager from block 256,083, the block it was deployed in. Uniswap v4 emits `Initialize` once per pool, so pools are never double counted.

| Contract | Address |
| --- | --- |
| Uniswap v4 PoolManager (Elysium) | `0xE2e105d3F7209A9DA11f83cCf3E7398a753823F1` |

The address comes from Uniswap's [v4 deployments page](https://developers.uniswap.org/docs/protocols/v4/deployments) (section "Elysium: 99901").

The handler is [`src/handlers/PoolManager.ts`](src/handlers/PoolManager.ts). It stores four entities.

- **`Pool`** has one row per pool, with its two currencies, fee, tick spacing, hook, UTC day, block and timestamp.
- **`Totals`** is one row with id `elysium`, holding pools, pools paired with HYPE, pools with a hook and the last block seen.
- **`DailyPools`** counts pools per UTC day.
- **`HookPools`** counts pools per hook address. The zero address means no hook.

Paired with HYPE means `currency0` is the zero address, which v4 uses for the chain's native token, and HYPE is Elysium's gas token. With a hook means the `hooks` address isn't the zero address.

## Run it

You need Node.js 22.15 or newer, pnpm and Docker for the local Postgres. No API token is needed, since this one syncs over RPC.

```bash
git clone https://github.com/enviodev/hypersync-use-cases.git
cd hypersync-use-cases/elysium-uniswap-v4-pools
pnpm install
pnpm codegen
pnpm dev
```

The GraphQL playground is at http://localhost:8080 (local admin secret `testing`).

```graphql
{
  Totals { pools poolsPairedWithHype poolsWithHooks lastBlock }
  DailyPools(order_by: { id: asc }) { id pools }
  HookPools(order_by: { pools: desc }, limit: 5) { id pools }
}
```

To pin the count to the block used above, filter `Pool` on `blockNumber`.

```graphql
{
  Pool_aggregate(where: { blockNumber: { _lte: 5448796 } }) { aggregate { count } }
}
```

The public Elysium RPC is rate limited, and an RPC backfill reads one block per pool, so a full backfill on it takes about an hour. Set `ENVIO_ELYSIUM_RPC_URL` to your own Elysium RPC to go faster. `config.yaml` falls back to `https://rpc.elysium.kinetiq.xyz` when it isn't set.

### Make it live

There's no `end_block` in `config.yaml`, so `pnpm dev` backfills and then keeps following Elysium's head. Your totals will be higher than the ones above. Elysium is now on HyperSync, so you can drop the `rpc` block and HyperIndex will sync from HyperSync instead, which is much faster.

### Deploy it

Push your fork to GitHub and deploy it on [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service), with `ENVIO_ELYSIUM_RPC_URL` set as an environment variable if you have your own RPC.

## Check the numbers

These checks use outside sources as the comparison.

- **Public RPC.** A separate script pulled every `Initialize` log from the PoolManager with `eth_getLogs` on Elysium's public RPC, from block 0 to 5,448,796. It found 115,872 logs, 109,537 with the native token as `currency0` and 6,144 with no hook, the same as the indexer.
- **Explorer.** Elysium's block explorer API (`module=logs`) returned 115,872 `Initialize` logs for the same block range.
- **Per day.** The indexer's per-day counts match the RPC script for every UTC day from 3 to 11 Nov 2026, and for 12 Nov up to the pinned block.
- **The top hook.** It isn't verified on the explorer. We tie it to the Montra launchpad because all 25 Montra token pools listed on [montramarkets.xyz](https://montramarkets.xyz) that existed at the pinned block were initialised with it, and the same deployer created the contract that sends those `Initialize` calls. The next two hooks are unlabelled.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent from this folder.

```text
This is an Envio HyperIndex indexer for Uniswap v4 pools on Elysium (chain 99901),
syncing over RPC. Read README.md, config.yaml, schema.graphql and
src/handlers/PoolManager.ts, then https://docs.envio.dev/docs/HyperIndex/rpc-sync.

Add the PoolManager's Swap event and keep a swap count per pool and per hook,
plus swaps per UTC day. Set end_block to 5448796 in config.yaml, run
`pnpm codegen` and `pnpm dev`, and check that the swap count for the top hook
matches a direct eth_getLogs count of Swap events for its pools over the same
blocks.
```

## Links

- [HyperIndex overview](https://docs.envio.dev/docs/HyperIndex/overview)
- [Using RPC as your indexing data source](https://docs.envio.dev/docs/HyperIndex/rpc-sync)
- [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service)
- [Uniswap v4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments)
- [Elysium docs](https://elysium.kinetiq.xyz/docs)
- [HYPE deposits into Elysium](../elysium-hype-deposits), the same chain seen from the HyperEVM side
- [Envio Discord](https://discord.gg/envio)
