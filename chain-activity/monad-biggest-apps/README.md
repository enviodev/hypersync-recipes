# Monad's biggest apps

Over the 30 days from 6 Oct to 5 Nov 2026, **Nad.fun had the most wallets of any app on Monad (12.1K), and Fastlane had the most transactions (37.8M)**. Perpl came second by transactions with 29.5M, and Uniswap third by wallets with 5K.

| By wallets | Wallets | | By transactions | Transactions |
| --- | --- | --- | --- | --- |
| Nad.fun | 12,071 | | Fastlane | 37,791,029 |
| Fastlane | 11,547 | | Perpl | 29,455,270 |
| Uniswap | 4,962 | | LFJ | 8,559,408 |
| Monday Trade | 3,676 | | Drake Exchange | 1,285,636 |
| PancakeSwap | 3,551 | | HelloTrade | 897,493 |

## Why it's interesting

Wallets and transactions give two very different rankings. Some apps have thousands of wallets sending a few transactions each, while others have a handful of addresses sending millions. Showing both side by side gives the full picture. The app labels come from the Monad Foundation's own registry, so nothing is guessed.

## What it pulls

- Every transaction whose `to` address is one of the contracts in the Monad Foundation's registry file [`protocols-mainnet.csv`](https://github.com/monad-crypto/protocols/blob/main/protocols-mainnet.csv), with its `from` address. This comes from HyperSync.
- Block timestamps from HyperSync, to find the block 30 days back by binary search.
- The registry file itself, downloaded from GitHub when the script starts. Names are the registry's own.

Oracles (the registry's `Oracle` subtype) and the registry's "Canonical Contracts" entry (the staking precompile, WMON, ERC-4337 EntryPoints, Multicall3, Permit2) are left out, so the ranking is about apps. Reverted transactions count too, as they do on block explorers. Unique wallets are distinct `from` addresses across all of an app's contracts, so a wallet that uses two of Uniswap's routers counts once. Contracts that aren't in the registry aren't counted, even when they're busy.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py      # the last 30 days
python3 script.py 7    # the last 7 days
```

The 30-day run reads about 85M transactions in parallel and takes about 15 minutes. Sample output from a run on 5 Nov 2026.

```
Monad, blocks 111040311 to 119613818 (last 30 days), 1570 registry contracts

Top 10 apps by unique wallets sending transactions
   1. Nad.fun           12,071 wallets        91,544 txs
   2. Fastlane          11,547 wallets    37,791,029 txs
   3. Uniswap            4,962 wallets       247,004 txs
   4. Monday Trade       3,676 wallets         3,897 txs
   5. PancakeSwap        3,551 wallets       262,039 txs
   6. Capricorn          3,053 wallets        76,663 txs
   7. Relay              2,837 wallets        38,121 txs
   8. aPriori            2,749 wallets        83,361 txs
   9. Li.Fi              2,684 wallets         7,023 txs
  10. NFTs2Me            2,354 wallets         2,380 txs

Top 10 apps by transactions
   1. Fastlane           37,791,029 txs   11,547 wallets
   2. Perpl              29,455,270 txs      626 wallets
   3. LFJ                 8,559,408 txs       72 wallets
   4. Drake Exchange      1,285,636 txs       51 wallets
   5. HelloTrade            897,493 txs        2 wallets
   6. Levr Bet              575,579 txs       10 wallets
   7. Collective Memory     460,354 txs        7 wallets
   8. Metamask              358,803 txs      900 wallets
   9. Kuru                  332,574 txs      445 wallets
  10. PancakeSwap           262,039 txs    3,551 wallets
```

The window moves with the chain, and the registry gets new entries, so your numbers will differ.

## Change the window or chain

- **Window.** Pass a number of days. The window always ends at the latest block.
- **Top N.** `TOP` at the top of `script.py` sets how many apps each ranking lists.
- **Chain.** For another chain, swap `HYPERSYNC` for its endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and `REGISTRY` for a CSV with `name`, `address` and `csubtype` columns for that chain's apps.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) and the Monad Foundation's
protocol registry (https://github.com/monad-crypto/protocols) to rank Monad apps
by unique sending wallets and by transactions. My HyperSync token is in the
ENVIO_API_TOKEN environment variable.

Add a weekly view for the top 10 apps by wallets, with unique wallets per app
for each 7-day block of the window, using block timestamps. Keep the standard
library only. Run it with 7 days first and check that the single week's wallet
counts match the main ranking.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [Raw HTTP query examples](https://docs.envio.dev/docs/HyperSync/hypersync-curl-examples), the same plain requests this script makes
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Monad protocol registry](https://github.com/monad-crypto/protocols)
- [Envio Discord](https://discord.gg/envio)
