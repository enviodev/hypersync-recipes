# Uniswap v4 pools on Elysium

A [HyperIndex](https://docs.envio.dev/docs/HyperIndex/overview) indexer for every Uniswap v4 pool created on Elysium, Kinetiq's Hyperliquid L2 (chain ID 99901). Elysium opened its public mainnet on 9th November 2026 and Uniswap went live there with v2, v3 and v4.

It indexes the v4 PoolManager's `Initialize` event, so each new pool becomes a row with its two currencies, fee, tick spacing and hook. It also keeps running totals: pools created, pools paired with native HYPE, pools with a hook, pools per UTC day and pools per hook.

Elysium isn't on HyperSync yet, so the indexer syncs over RPC. HyperIndex works on any EVM chain this way from day one.

## Contract

| Contract | Address |
|---|---|
| Uniswap v4 PoolManager (Elysium) | `0xE2e105d3F7209A9DA11f83cCf3E7398a753823F1` |

The address comes from Uniswap's [v4 deployments page](https://developers.uniswap.org/docs/protocols/v4/deployments) (section "Elysium: 99901"). The indexer starts at block 256,083, the block the PoolManager was deployed in (3rd November 2026).

## The indexer

`config.yaml`:

```yaml
contracts:
  - name: PoolManager
    events:
      - event: Initialize(bytes32 indexed id, address indexed currency0, address indexed currency1, uint24 fee, int24 tickSpacing, address hooks, uint160 sqrtPriceX96, int24 tick)
chains:
  - id: 99901
    start_block: 256083
    rpc:
      - url: ${ENVIO_ELYSIUM_RPC_URL:-https://rpc.elysium.kinetiq.xyz}
        for: sync
    contracts:
      - name: PoolManager
        address: 0xE2e105d3F7209A9DA11f83cCf3E7398a753823F1
```

The handler is [`src/handlers/PoolManager.ts`](src/handlers/PoolManager.ts). It stores the pool, then bumps `Totals`, `DailyPools` and `HookPools`.

## Run it

You need Node.js 22.15 or newer, pnpm and Docker for the local Postgres.

```bash
pnpm install
pnpm codegen
pnpm dev
```

The GraphQL playground is at http://localhost:8080 (admin secret `testing`).

The public Elysium RPC is rate limited, and an RPC backfill reads one block per pool, so a full backfill on the public endpoint takes about an hour. Point `ENVIO_ELYSIUM_RPC_URL` at your own Elysium RPC to go faster.

## Deploy it on Envio Cloud

Push the folder to a GitHub repo, add it as an indexer in the [Envio Cloud dashboard](https://envio.dev/app) and set `ENVIO_ELYSIUM_RPC_URL` as an environment variable. Envio Cloud backfills, follows the chain head and gives you a hosted GraphQL endpoint. See [Hosted service deployment](https://docs.envio.dev/docs/HyperIndex/hosted-service-deployment).

## Query it

```graphql
{
  Totals { pools poolsPairedWithHype poolsWithHooks lastBlock }
  DailyPools(order_by: { id: asc }) { id pools }
  HookPools(order_by: { pools: desc }, limit: 5) { id pools }
}
```

Pinned to Elysium block 5,448,796 (12th November 2026, 17:00 UTC) by filtering `Pool` on `blockNumber`, it returned:

```
pools                  115,872
poolsPairedWithHype    109,537   (108,201 different tokens on the other side)
poolsWithHooks         109,728   (94.7%)
busiest day            2026-11-09, 28,722 pools (Elysium public mainnet day)
top hooks              0x6b1216a40b65c83e9c9e18a562c446697b8cf8ec (Montra) 93,729 · 0xe0def4221b9840a610d4e7d55812a79a6431a8ec 4,613 · 0x3ab88ddc3cf2a012af88b60828edb4553697e5dc 3,405
```

To pin it yourself:

```graphql
{
  Pool_aggregate(where: { blockNumber: { _lte: 5448796 } }) { aggregate { count } }
}
```

Your totals will be higher, since the indexer keeps following the chain.

## How it counts

- One pool per `Initialize` event on the PoolManager. Uniswap v4 emits it once per pool, so pools are never double counted.
- Paired with HYPE means `currency0` is the zero address, which v4 uses for the chain's native token. HYPE is Elysium's gas token.
- With a hook means the `hooks` address isn't the zero address.
- Days are UTC, from the block timestamp.

## How we checked it

- We pulled every `Initialize` log from the PoolManager straight from Elysium's public RPC with `eth_getLogs`, from block 0 to 5,448,796, in a separate script. It found 115,872 logs, 109,537 with the native token as `currency0` and 6,144 with no hook, the same as the indexer.
- Elysium's block explorer API (`elysium.kinetiq.xyz/explorer/api`, `module=logs`) returned 115,872 `Initialize` logs for the same block range.
- The indexer's per-day counts match the RPC script for every UTC day from 3rd to 11th November, and for 12th November up to the pinned block.
- The top hook isn't verified on the explorer. We tie it to the Montra launchpad because every Montra token pool listed on [montramarkets.xyz](https://montramarkets.xyz) that existed at the pinned block (25 of 25) was initialised with it, and the same deployer created the contract that sends those `Initialize` calls. The next two hooks are unlabelled.

## Next to other chains

Every Uniswap v4 `Initialize` event on each chain's PoolManager (addresses from Uniswap's [deployments list](https://developers.uniswap.org/deployments.json)), pulled with HyperSync and again with HyperRPC `eth_getLogs`:

| Chain | v4 pools | With a hook |
|---|---|---|
| Elysium | 115,872 | 94.7% |
| Arbitrum | 27,037 | 18.3% |
| Unichain | 7,801 | 70.7% |
| Ethereum | 198,041 | 24.3% |

Counts as of 12th November 2026. Both methods returned the same numbers for every chain.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Build an Envio HyperIndex indexer (https://docs.envio.dev/docs/HyperIndex/overview) for Uniswap v4 on
Elysium (chain 99901). Elysium isn't on HyperSync, so sync over RPC with an rpc entry marked for: sync
(https://docs.envio.dev/docs/HyperIndex/rpc-sync) using https://rpc.elysium.kinetiq.xyz. Index Initialize on
the PoolManager 0xE2e105d3F7209A9DA11f83cCf3E7398a753823F1 from block 256083. Store each pool, and keep
totals for pools, pools paired with native HYPE (currency0 = zero address), pools with a hook, pools per UTC
day and pools per hook.
```

## Learn more

- [Using RPC as your indexing data source](https://docs.envio.dev/docs/HyperIndex/rpc-sync)
- [Uniswap v4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments)
- [Elysium docs](https://elysium.kinetiq.xyz/docs)
