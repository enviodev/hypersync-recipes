# 1inch Aqua strategies on every chain

Since 1inch Aqua first appeared onchain on 19 Jul 2026, **2,190 wallets have shipped 186,919 strategies across 15 chains, and 732 of those wallets have shipped 10 or more**. Ethereum has 78.2% of the strategies, Robinhood Chain 12.1% and BSC 8.4%. This was pulled on 17 Nov 2026 with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview).

| Chain | Strategies | Share | Wallets |
| --- | --- | --- | --- |
| Ethereum | 146,223 | 78.2% | 1,547 |
| Robinhood Chain | 22,625 | 12.1% | 319 |
| BSC | 15,758 | 8.4% | 295 |
| Base | 998 | 0.5% | 179 |
| Polygon | 657 | 0.4% | 26 |
| Arbitrum | 403 | 0.2% | 72 |
| Ten other chains | 658 | 0.4% | |
| All chains | 186,919 | 100% | 2,190 |

## Why it's interesting

Aqua is 1inch's shared liquidity layer. A liquidity provider keeps their tokens in their own wallet and gives Aqua one approval, then "ships" as many strategies as they like against the same balance. Because every strategy is announced by one event on one contract, you can see how many LPs are using it, how many strategies each has shipped and which chains they chose, without reading any pool.

## What it pulls

- Every `Shipped(address maker, address app, bytes32 strategyHash, bytes strategy)` log on the Aqua registry, `0x1111113ccf1426a8e30e2bff5e005d929bf6a90a`. 1inch deploys it at the same address on every chain, listed in [1inch/aqua deployments](https://github.com/1inch/aqua/blob/main/deployments.md).
- The first word of the event's data is the LP wallet, so counting distinct values gives the number of LPs.

HyperSync filters by address and event on its side, so only the Shipped logs come back. The script reads all 15 chains in parallel.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

It takes about a minute. Sample output from a run on 17 Nov 2026.

```
1inch Aqua, all chains: 186,919 strategies shipped by 2,190 different wallets
Wallets that shipped 10 or more: 732
Chains with at least one strategy: 15 of 15

chain         strategies   share  wallets
eth              146,223   78.2%    1,547
robinhood         22,625   12.1%      319
bsc               15,758    8.4%      295
base                 998    0.5%      179
...
```

New strategies are shipped every day, so your numbers will be higher.

## Change the window or chain

- **Chain.** Run `CHAIN=base python3 script.py` for one chain. The names are the HyperSync subdomains in the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks).
- **Window.** The script reads from block 0. To count one month, set `from_block` and add `to_block` to the query body, and stop the loop when `next_block` reaches it.
- **Other events.** Swap `SHIPPED` for the topic of `Pulled`, `Pushed` or `Docked` to count swap legs, deposits into a trade and closed strategies. Their signatures are in [IAqua.sol](https://github.com/1inch/aqua/blob/main/contracts/interfaces/IAqua.sol).

## Check the numbers

On Gnosis and Avalanche the same count comes from a public RPC with `eth_getLogs`, in chunks the node allows. Avalanche returns 44 Shipped logs from 6 wallets and Gnosis returns 50 from 8, the same as HyperSync. Running the script twice, an hour apart, gave the same totals.

## Build your own with an AI agent

Paste this into your coding agent:

> Write a Python 3 script, standard library only, that uses Envio HyperSync to read every `Shipped` event of the 1inch Aqua registry at `0x1111113ccf1426a8e30e2bff5e005d929bf6a90a` on each chain listed at github.com/1inch/aqua/blob/main/deployments.md. Query `https://<chain>.hypersync.xyz/query` with `from_block` 0, filter by address and topic0, and page with `next_block`. Count strategies and distinct maker addresses per chain and in total, and print a table. Read the token from `ENVIO_API_TOKEN`.

## Links

- [HyperSync docs](https://docs.envio.dev/docs/HyperSync/overview)
- [1inch Aqua](https://1inch.com/aqua) and its [contracts](https://github.com/1inch/aqua)
