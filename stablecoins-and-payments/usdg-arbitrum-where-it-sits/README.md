# Where USDG sits on Arbitrum

Reads every transfer of Paxos Global Dollar (USDG) on Arbitrum One with [HyperSync](https://docs.envio.dev/docs/HyperSync/overview), rebuilds every holder's balance, and shows where the supply sits. It splits it into GMX markets, Morpho, other contracts and plain wallets.

## What we found

At block 524,987,577 (17 Nov 2026, 08:46 UTC), from 329,225 transfers.

- $65,078,215 of USDG is on Arbitrum One
- $26,175,523 of it (40.2%) sits in eight GMX markets, where it backs perp trading on BTC, ETH, ZEC, NEAR, XRP, HYPE and SOL, plus a USDC/USDG swap pool. The BTC/USD market alone holds $10.84M
- $15,928,898 (24.5%) sits in Morpho
- $13,705,168 (21.1%) sits in other contracts and $9,268,524 (14.2%) in plain wallets

So about two thirds of the USDG on Arbitrum is already in use in GMX and Morpho, six weeks after [Paxos launched it there](https://docs.paxos.com/guides/stablecoin/usdg/mainnet).

## Why it's interesting

A supply chart tells you a stablecoin is growing. It doesn't tell you what the money is doing. Token balances aren't stored as events, so to answer that you need every transfer since the first mint, replayed in order. With HyperSync that's one filtered log query from block 0, and it comes back in about a minute. From there, grouping balances by the contracts that hold them shows which apps a new stablecoin lands in first.

## What it pulls

| | |
|---|---|
| Chain | Arbitrum One, `https://arbitrum.hypersync.xyz` |
| Product | HyperSync produces the supply and every balance. A public RPC's `eth_getCode` only sorts holders into contracts and wallets |
| Logs | Every `Transfer` of USDG (`0x004b506865409877c9fa29bfb1eba929984b9bbc`), with `topic1`, `topic2`, `data`, `block_number` and `log_index` |
| Blocks | `number`, `timestamp`, for the daily series |
| Groups | The eight GMX market addresses that hold USDG, the Morpho contract, then contracts and wallets split by `eth_getCode` |
| Window | Block 0 to the chain head |

Balances are summed as integers and only divided by 6 decimals when printed.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). There are no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

It prints the breakdown and writes `usdg_arbitrum.json`, which also holds the supply, GMX and Morpho totals for every day since the first mint.

## Change the token or chain

Swap `USDG` for any ERC-20 and `HS` for another [supported network](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks). Replace `GMX_MARKETS` and `MORPHO` with the contracts you want to group by. The script refreshes the GMX list from GMX's own markets API on each run, so new USDG markets are picked up without an edit.

## Check the numbers yourself

The script runs the comparison for you. After the HyperSync totals it reads `totalSupply()` and `balanceOf()` from a public Arbitrum RPC at the same block, and prints `match` or `DIFFERENT` for the supply, the GMX total and the Morpho balance. At block 524,987,577 all three matched to the last unit.

The GMX market addresses come from [GMX's markets API](https://arbitrum-api.gmxinfra.io/markets), filtered to markets whose long or short token is USDG. The Morpho address comes from the [Morpho docs](https://docs.morpho.org/get-started/resources/addresses).

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```
Use HyperSync (https://docs.envio.dev/docs/HyperSync/overview, endpoint https://arbitrum.hypersync.xyz/query)
to read every Transfer log of USDG on Arbitrum One (0x004b506865409877c9fa29bfb1eba929984b9bbc) from block 0
to the head. Use the default join mode and keep only logs whose address and topic0 match. Page with next_block.
My API token is in ENVIO_API_TOKEN. Rebuild every holder's balance with integer maths, then show how the
USDG held in each GMX market (addresses from https://arbitrum-api.gmxinfra.io/markets) changed day by day,
and chart the net flow in and out of the BTC/USD market.
```

To keep this running as a live API instead of a one-off scan, scaffold a HyperIndex project with `pnpx envio init`. It adds Envio's agent skills to the project's `.claude/skills/` folder, so your agent has the docs in context ([Quickstart with AI](https://docs.envio.dev/docs/HyperIndex/quickstart-with-ai)).

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview) and [supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [HyperIndex on Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service)
- [USDG mainnet addresses](https://docs.paxos.com/guides/stablecoin/usdg/mainnet) in the Paxos docs
- [GMX docs](https://docs.gmx.io/) and [Morpho addresses](https://docs.morpho.org/get-started/resources/addresses)
- [Arbitrum docs](https://docs.arbitrum.io/)
- Questions: [Envio Discord](https://discord.gg/envio)
