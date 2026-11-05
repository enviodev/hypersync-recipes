# Monad's biggest apps

Reads every transaction sent to a contract in the Monad Foundation's [protocol registry](https://github.com/monad-crypto/protocols) over the last 30 days with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), then ranks the apps by unique wallets and by transactions.

These are the numbers behind Envio's post on Monad's first year of mainnet.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

Pass a number of days to change the window, for example `python script.py 7`. The 30-day run reads about 85 million transactions in parallel and takes about 15 minutes.

## What it prints

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

That run covers 6th October to 5th November 2026. The window moves with the chain, so your numbers will differ.

## How it counts

- Apps and their contract addresses come from the Monad Foundation's registry file [`protocols-mainnet.csv`](https://github.com/monad-crypto/protocols/blob/main/protocols-mainnet.csv). Names are the registry's own.
- Oracles (the registry's `Oracle` subtype) and Monad's canonical contracts (the staking precompile, WMON, ERC-4337 EntryPoints, Multicall3, Permit2) are left out, so the ranking is about apps.
- A transaction counts for an app when its `to` address is one of that app's registry contracts. Reverted transactions count too, as they do on block explorers.
- Unique wallets are distinct `from` addresses across all of an app's contracts, so a wallet that uses two of Uniswap's routers counts once for Uniswap.
- Contracts that aren't in the registry are not counted, even when they are busy.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) and the Monad Foundation's
protocol registry (https://github.com/monad-crypto/protocols) to read every transaction sent to a
registry contract on Monad in the last 30 days. My API token is in the ENVIO_API_TOKEN environment
variable. Show me unique wallets per app, week by week, for the top 10 apps.
```
