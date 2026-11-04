# USDG on Morpho

Finds every Morpho market that lends Paxos USDG with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), then reads how much USDG each market holds right now. It prints the total per chain and the biggest markets by collateral.

These are the numbers behind Envio's post on USDG in DeFi.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

## What it prints

```
Robinhood Chain   371 USDG markets  $514.3M supplied
Arbitrum            8 USDG markets  $143.2M supplied
Ethereum            3 USDG markets  $0.0M supplied

USDG supplied on Morpho: $657.5M
  $  345.7M  Robinhood Chain  USDe collateral  (53%)
  $  143.2M  Arbitrum         syrupUSDG collateral  (22%)
  $  100.6M  Robinhood Chain  syrupUSDG collateral  (15%)
  ...
```

The numbers move as people supply and withdraw, so yours will differ a little.

## How it counts

- Morpho contract addresses come from the [Morpho docs](https://docs.morpho.org/get-started/resources/addresses), and USDG addresses from the [Paxos docs](https://docs.paxos.com/guides/stablecoin/usdg/mainnet).
- HyperSync reads every `CreateMarket` event on each chain's Morpho contract, and keeps the markets whose loan token is USDG.
- Each market's `totalSupplyAssets` is read live from the chain's public RPC. USDG is counted at $1.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every
Supply and Withdraw event on Morpho markets that lend USDG on Robinhood Chain
(Morpho 0x9D53d5E3bd5E8d4Cbfa6DB1ca238AEA02E651010, USDG 0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168).
My API token is in the ENVIO_API_TOKEN environment variable.
Chart how much USDG was supplied each day, and show the biggest suppliers.
```
