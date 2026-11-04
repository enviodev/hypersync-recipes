# What sits in Aave on Monad

Reads every transfer into and out of Aave v3's pools on Monad with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It prints what each pool holds by asset, priced in USD, and how much of the total is dollar tokens.

These are the numbers behind Envio's post on what makes up Aave's TVL on Monad.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

Pass a block number to stop there, for example `python script.py 119308836`.

## What it prints

```
Held in Aave v3 on Monad up to block 119,308,836
  USDe               $ 119.18M  42.3%  (119,352,217.78 USDe)
  syrupUSDC          $  85.84M  30.5%  (72,072,353.22 syrupUSDC)
  PT-AUSD-17DEC2026  $  43.36M  15.4%  (43,669,353.81 PT-AUSD-17DEC2026)
  USDC               $  10.75M   3.8%  (10,751,478.74 USDC)
  mUSD               $  10.31M   3.7%  (10,310,533.16 mUSD)
  ...
Total $281.4M, of which dollar tokens $276.9M (98.4%)
```

The pools change every block, so your numbers will differ a little.

## How it counts

- Pool, aToken and reserve addresses come from the [Aave address book](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV3Monad.sol).
- For each reserve, the script adds every token transfer into its aToken and subtracts every transfer out. That is the amount the pool holds, which is supplied minus borrowed, the same basis DefiLlama uses for TVL.
- Prices come from Aave's own oracle on Monad, read with one RPC call per asset.
- Dollar tokens are every stablecoin, yield-bearing dollar (syrupUSDC, sUSDe) and Pendle PT on AUSD. ETH and BTC tokens are counted separately.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) on Monad
(https://monad.hypersync.xyz) to sum every ERC-20 Transfer into and out of each
Aave v3 aToken listed in
https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV3Monad.sol.
My API token is in the ENVIO_API_TOKEN environment variable. Price each asset with
the Aave oracle (getAssetPrice) and chart what the pools hold by asset.
```
