# Spiko SAFO on four EVM chains

In a run on 4 Nov 2026, **Spiko's SAFO fund held $727.2M across Ethereum, Arbitrum, Polygon and Base, with 83% in its euro share classes and 1.2K holders** across the four chains. Arbitrum was the largest at $474.9M.

| Chain | Value | In euro classes | Holders |
| --- | --- | --- | --- |
| Arbitrum | $474.9M | 93% | 494 |
| Ethereum | $138.8M | 48% | 38 |
| Polygon | $94.5M | 84% | 507 |
| Base | $19.0M | 83% | 118 |

## Why it's interesting

SAFO comes in dollar, euro, pound and franc share classes, each its own token on each chain. That's a lot of contracts to add up by hand. This script pulls the class list from Spiko's API, rebuilds every class's supply from its mints and burns, and values it all in dollars. It's a good template for any fund with several share classes or currencies.

## What it pulls

- Share classes, token addresses, the latest NAV per class and EUR, GBP and CHF to USD rates from Spiko's [public API](https://docs.spiko.io/developers/public_api/getting_started) (`/share-classes/`, SAFO fund only). That covers every currency class, including the D classes.
- Every ERC-20 `Transfer` of each class on Ethereum, Arbitrum, Polygon and Base, from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). Supply and holder counts come from HyperSync.

Dollar values are HyperSync supply times Spiko's NAV and FX rates, so the prices come from Spiko's API, not from HyperSync. Each SAFO class has a net asset value that the fund's administrator calculates once a day off chain, and the foreign exchange rates for the euro, pound and franc classes are also off chain. I could not find a published onchain oracle address for the SAFO classes (Spiko lists oracles for its older funds, but not for SAFO), so there is no onchain price HyperSync could read here. That is why the script keeps the API price. Supply and holders are from HyperSync, and only the dollar figure depends on it. Supply is mints minus burns and matches each token's `totalSupply()` onchain. Holders are addresses with a positive balance on each chain, so an address on two chains counts twice, and some holders are contracts. SAFO is also issued on Stellar, Starknet, Solana and Etherlink, which this script doesn't read.

## Run it

You need Python 3 (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

Sample output from the 4 Nov 2026 run.

```
Spiko SAFO on Ethereum, Arbitrum, Polygon and Base
  Arbitrum  $  474.9M    93% in euro classes   494 holders
  Ethereum  $  138.8M    48% in euro classes    38 holders
  Polygon   $   94.5M    84% in euro classes   507 holders
  Base      $   19.0M    83% in euro classes   118 holders
Total $727.2M, 83% in euro share classes, 1157 holders across the four chains
```

People subscribe and redeem every day, so your numbers will differ a little.

## Change the window or chain

- **Another Spiko fund.** The API lists every Spiko fund. Change `SAFO_FUND` to another fund's id from `/share-classes/` to run the same breakdown on it.
- **Chain.** If a class is on another EVM chain, add that chain to `CHAINS`, using the network name the API uses and the HyperSync subdomain from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks).
- **Over time.** Add `block_number` to the log fields and `"block": ["number", "timestamp"]` to the field selection, then group mints and burns by week to chart supply per chain and currency.

## Check the numbers

Each rebuilt supply matches the token's `totalSupply()` onchain, and you can check any class on [Arbiscan](https://arbiscan.io) or [Etherscan](https://etherscan.io) with its address from the API. Spiko's own fund pages show the fund's total size as an outside comparison, which will be larger since it includes the non-EVM chains.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) and Spiko's public API to rebuild the
supply of every Spiko SAFO share class on Ethereum, Arbitrum, Polygon and Base.
My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add a weekly series of supply per chain and currency since launch and write it to
weekly.csv. Keep the standard library only. Then check that the last week's dollar
total matches the total the script prints.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Spiko public API](https://docs.spiko.io/developers/public_api/getting_started)
- [Envio Discord](https://discord.gg/envio)
