# Ondo stocks on Robinhood Chain, first week

Reads every Uniswap v4 swap in a pool with one of Ondo's tokenized stocks on Robinhood Chain, using [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It prints swaps and wallets per token for a week, and how many swaps paired an Ondo token with the Robinhood token of the same stock.

These are the numbers behind Envio's post on the first week of Ondo stocks on Robinhood Chain.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

It covers the launch week, 27th Oct to 3rd Nov 2026 UTC. Pass a start date to look at another week:

```bash
python script.py 2026-11-03
```

## What it prints

```
Ondo stocks on Robinhood Chain, 2026-10-27 to 7 days later (UTC)
Uniswap v4 pools with an Ondo token  29
Swaps    226
Wallets  110
Swaps against the same company's Robinhood Stock Token  198 (88%)
  GOOGLon    87 swaps from  50 wallets
  TSLAon     40 swaps from  20 wallets
  NVDAon     22 swaps from  17 wallets
  ...
```

## How it counts

- Ondo's 15 Robinhood Chain token addresses come from the token sheet linked at [docs.ondo.finance/addresses](https://docs.ondo.finance/addresses).
- The PoolManager comes from Uniswap's [v4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments) page.
- A pool counts if either side is an Ondo token. Every Swap in those pools during the week is counted.
- Wallets are the addresses that sent the swap transactions.
- A swap pairs with "the same company's Robinhood Stock Token" when the other token's symbol is the Ondo symbol without the "on" suffix, for example GOOGLon and GOOGL. Symbols are read from the Robinhood Chain public RPC.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) on Robinhood Chain
to find every Uniswap v4 pool (PoolManager 0x8366a39cc670b4001a1121b8f6a443a643e40951)
that holds one of Ondo's tokenized stocks (addresses from https://docs.ondo.finance/addresses).
My API token is in the ENVIO_API_TOKEN environment variable.
Count swaps and unique wallets per token each week, and show which pairs they trade against.
```
