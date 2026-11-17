# What sits in Aave on Monad

Up to Monad block 119,308,836, **Aave v3 on Monad held $281.4M, and $276.9M of it (98.4%) was dollar tokens**. USDe was the biggest pool at $119.2M, then syrupUSDC at $85.8M and a Pendle PT on AUSD at $43.4M.

| Asset | Held | Share |
| --- | --- | --- |
| USDe | $119.18M | 42.3% |
| syrupUSDC | $85.84M | 30.5% |
| PT-AUSD-17DEC2026 | $43.36M | 15.4% |
| USDC | $10.75M | 3.8% |
| mUSD | $10.31M | 3.7% |
| Total | $281.4M | |

## Why it's interesting

Aave's pools on Monad are almost all dollars, and a big part of that is yield-bearing dollars (USDe, syrupUSDC, Pendle PTs) rather than plain USDC. If you're building a vault, a looping strategy or a dashboard on Monad, this shows where the liquidity actually sits.

It's also a simple way to get TVL with no node. Every aToken's balance is the sum of transfers in minus transfers out, and HyperSync returns every one of those transfers since genesis in about two minutes.

## What it pulls

- ERC-20 `Transfer` logs for the 14 reserve tokens, filtered to transfers into or out of each reserve's aToken. Pool, aToken and reserve addresses come from the [Aave address book for Monad](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV3Monad.sol).
- One `getAssetPrice` call per asset on the [Aave oracle](https://aave.com/docs/aave-v3/smart-contracts/oracles) (`0x0c02b2c2038066c10eab8fe1d5cdb73d5a78a1bf`) through Monad's public RPC.

What a pool holds is supplied minus borrowed. Dollar tokens are the stablecoins, the yield-bearing dollars (syrupUSDC, sUSDe) and the Pendle PTs on AUSD. ETH and BTC tokens are counted separately.

The token balances come from HyperSync. The dollar values use Aave's oracle prices, read over Monad's public RPC.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py             # up to the latest block
python3 script.py 119308836   # up to the block used above
```

It takes about two minutes. Sample output from a run on 16 Nov 2026.

```
Held in Aave v3 on Monad up to block 122,749,347
  USDe               $  84.31M  34.9%  (84,394,004.88 USDe)
  syrupUSDC          $  71.83M  29.7%  (60,212,474.09 syrupUSDC)
  PT-AUSD-17DEC2026  $  41.53M  17.2%  (41,747,475.05 PT-AUSD-17DEC2026)
  mUSD               $  19.53M   8.1%  (19,531,056.05 mUSD)
  USDT0              $   9.26M   3.8%  (9,271,656.44 USDT0)
  USDC               $   8.65M   3.6%  (8,656,594.43 USDC)
  ...
Total $241.5M, of which dollar tokens $236.9M (98.1%)
```

Pool balances change every block, so your numbers will differ.

## Change the window or chain

- **Block.** Pass a block number as the first argument to stop there. Prices always come from the oracle at the latest block, so a past block gives today's prices on that block's balances.
- **Chain.** Aave v3 runs on many chains. Swap `URL` for that chain's HyperSync endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), `RPC` for a public RPC on that chain, and `ORACLE` and `RESERVES` for the matching file in the [Aave address book](https://github.com/bgd-labs/aave-address-book/tree/main/src).

## Check the numbers

Each token total should match `balanceOf(aToken)` on the reserve token at the same block. Run the script with a block number, then call `balanceOf` for any aToken on [Monadscan](https://monadscan.com) or with `cast call` at that block as the comparison. Aave's own [app](https://app.aave.com) also shows each Monad market's size.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to sum every ERC-20 Transfer
into and out of each Aave v3 aToken on Monad, then prices the balances with the
Aave oracle. My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Port it to Aave v3 on <CHAIN>. Take the HyperSync URL for <CHAIN> from
https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks and the oracle,
reserve and aToken addresses from the matching file in
https://github.com/bgd-labs/aave-address-book/tree/main/src. Keep the standard
library only. Then add a daily series of total held for the last 30 days and
check one aToken total against balanceOf at the same block.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Aave v3 docs](https://aave.com/docs)
- [Aave address book for Monad](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV3Monad.sol)
- [Envio Discord](https://discord.gg/envio)
