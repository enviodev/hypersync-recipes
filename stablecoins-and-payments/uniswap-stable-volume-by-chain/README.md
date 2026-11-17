# Uniswap stablecoin-to-stablecoin volume by chain

In the 30 days to 9 Nov 2026, **$13.9B traded between two dollar stablecoins on Uniswap v3 and v4 across 22 EVM chains**, and 92% of it went through v4. Ethereum carried $11.9B, then Polygon at $853.6M, BNB Chain at $510.0M, Arbitrum at $324.3M and Base at $232.5M.

| Chain | Volume | Share | v4 | v3 | Swaps |
| --- | --- | --- | --- | --- | --- |
| Ethereum | $11.89B | 85.6% | $11.00B | $886.4M | 473,613 |
| Polygon | $853.6M | 6.1% | $729.9M | $123.7M | 537,290 |
| BNB Chain | $510.0M | 3.7% | $498.9M | $11.0M | 1,467,159 |
| Arbitrum | $324.3M | 2.3% | $253.8M | $70.5M | 170,454 |
| Base | $232.5M | 1.7% | $210.1M | $22.4M | 1,111,945 |
| Monad | $35.8M | 0.3% | $35.3M | $0.5M | 157,496 |

## Why it's interesting

Stable-to-stable swaps are the plumbing of onchain dollars. They're how a wallet turns USDT into USDC, or how a payment app settles in the coin it needs. Seeing where that volume lands, and how much of it now runs through v4, tells you where dollar liquidity is deepest on each chain. It's also a neat pattern for any cross-chain question, finding the right pools first and then pulling only their swaps.

## What it pulls

- `PoolCreated` logs from each chain's Uniswap v3 factory and `Initialize` logs from each chain's v4 PoolManager, with addresses from Uniswap's official [deployments list](https://developers.uniswap.org/deployments.json). A pool counts when both of its tokens are dollar stablecoins.
- `Swap` logs from those pools over the 30 days.

The stablecoins are USDC (native and bridged), USDT and USDT0, DAI, USDS, USDe, PYUSD, USD1, RLUSD, USDG, FDUSD, GHO, AUSD, USDtb, frxUSD, crvUSD, LUSD, BOLD and a few smaller ones, listed per chain in `CHAINS`. Addresses come from Uniswap's default token list and the issuers, and all but Arc's native USDC were checked onchain with `symbol()` and `decimals()`. Euro stablecoins and yield-bearing tokens such as sUSDe are left out.

Each swap counts once, as the absolute amount of one side at $1. The script takes the more established coin's side (USDC, then USDT, then DAI, then USDS), so a smaller coin trading off its peg can't inflate the total. Uniswap v2 isn't included. Every number here comes from HyperSync.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                     # the 30 days to 9 Nov 2026, the window above
CHAINS=1,137 python3 script.py        # Ethereum and Polygon only
```

The full run reads pool creation events from the start of each chain, so it takes a while on chains with long histories such as Arbitrum and BNB Chain. Sample output from the window above.

```
Stable-to-stable volume on Uniswap v3 and v4: $13.88B (92% on v4)

Ethereum        $11.89B  85.6%   v4    $11.00B  v3   $886.4M     473,613 swaps
              v4 USDC/USDT $3.44B
              v4 USDT/USDS $2.24B
              v4 USDC/USDT $1.57B
Polygon         $853.6M   6.1%   v4    $729.9M  v3   $123.7M     537,290 swaps
              v4 USDC/USDT0 $292.8M
              v4 USDC/USDC $238.4M
              v4 DAI/USDT0 $119.7M
...
```

## Change the window or chain

- **Window.** Pass a unix timestamp to end the 30-day window somewhere else. With no argument it ends at 9 Nov 2026 00:00 UTC. The length is the `30 * 86400` in `START`.
- **Chains.** Set `CHAINS` to a comma-separated list of chain IDs to run a subset. To add a chain, give it an entry in the `CHAINS` dict with its factory, PoolManager and stablecoins, and check that it's on the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks).
- **Tokens.** Add a stablecoin to a chain's `stables` map with its decimals.

## Check the numbers

- **Receipts.** 32 swaps sampled across Ethereum, Polygon, BNB Chain, Arbitrum, Base and Monad were decoded again from transaction receipts on public RPC endpoints, as the comparison. Every one matched to the cent.
- **Uniswap's own figure.** As an outside comparison, Uniswap reported $15B+ of stable-to-stable volume on EVM chains for the same 30 days. The script finds $13.9B on v3 and v4, about 93% of that. The gap is likely v2 pools, chains outside this list and where exactly the 30 days start and end.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to find every Uniswap v3 and v4
pool where both tokens are dollar stablecoins on 22 chains, then sums their swap
volume over 30 days. My HyperSync token is in the ENVIO_API_TOKEN environment
variable.

Add Uniswap v2 pools, using PairCreated from each chain's v2 factory in
https://developers.uniswap.org/deployments.json, and print v2 as its own column.
Keep the standard library only and run it with CHAINS=1 first. Then decode three
v2 swaps again from their receipts and check the amounts match.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Uniswap deployments](https://developers.uniswap.org/deployments.json)
- [Envio Discord](https://discord.gg/envio)
