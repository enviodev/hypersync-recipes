# What sits in Aave on Monad

Up to Monad block 123,046,774 on 17 Nov 2026, **Aave v3 on Monad held $243.2M, and $238.6M of it (98.1%) was dollar tokens**. USDe was the biggest pool at $83.3M, then syrupUSDC at $71.9M and a Pendle PT on AUSD at $45.2M.

| 17 Nov 2026 | Held | Share |
| --- | --- | --- |
| USDe | $83.33M | 34.3% |
| syrupUSDC | $71.85M | 29.5% |
| PT-AUSD-17DEC2026 | $45.16M | 18.6% |
| mUSD | $19.67M | 8.1% |
| USDC | $10.65M | 4.4% |
| Total | $243.2M | |

## Why it's interesting

Aave's pools on Monad are almost all dollars, and a big part of that is yield-bearing dollars (USDe, syrupUSDC, Pendle PTs) rather than plain USDC. If you're building a vault, a looping strategy or a dashboard on Monad, this shows where the liquidity actually sits.

It's also a simple way to get TVL with no node. What each aToken contract holds of its reserve token is the sum of transfers in minus transfers out, and HyperSync returns every one of those transfers since genesis in about two minutes.

## What it pulls

- ERC-20 `Transfer` logs for the 14 reserve tokens, filtered to transfers into or out of each reserve's aToken. Pool, aToken and reserve addresses come from the [Aave address book for Monad](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV3Monad.sol).
- `AnswerUpdated` logs from the nine Chainlink aggregators behind Aave's price adapters on Monad (ETH/USD, cbBTC/USD, USDC/USD, USDT0/USD, AUSD/USD and the syrupUSDC, sUSDe, weETH and wstETH exchange rates). The script takes the latest answer of each at or before the snapshot block.

What a pool holds is supplied minus borrowed. Dollar tokens are the stablecoins, the yield-bearing dollars (syrupUSDC, sUSDe) and the Pendle PTs on AUSD. ETH and BTC tokens are counted separately.

Both the token balances and the dollar prices come from HyperSync. Prices are built the way Aave's adapters build them. USDC, USDT0, AUSD, ETH and cbBTC are the feed answers. syrupUSDC, sUSDe, weETH and wstETH are an exchange rate feed times the base feed. USDe uses the USDT0 feed, as Aave does. A Pendle PT is the AUSD price less a linear discount to maturity, using the maturity and yearly rate fixed in each adapter (5.745% to 17 Dec 2026 and 6.661% to 8 Oct 2026). mUSD and GHO are fixed at $1 in Aave's own adapters, so there is no onchain feed for them.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py             # up to the latest block
python3 script.py 119308836   # up to the block used above
```

It takes about two minutes. Sample output from a run on 17 Nov 2026, at block 123,046,774.

```
Held in Aave v3 on Monad up to block 123,046,774
  USDe               $  83.33M  34.3%  (83,394,004.88 USDe)
  syrupUSDC          $  71.85M  29.5%  (60,215,980.92 syrupUSDC)
  PT-AUSD-17DEC2026  $  45.16M  18.6%  (45,384,097.30 PT-AUSD-17DEC2026)
  mUSD               $  19.67M   8.1%  (19,674,755.66 mUSD)
  USDC               $  10.65M   4.4%  (10,651,911.79 USDC)
  ...
Total $243.2M, of which dollar tokens $238.6M (98.1%)
Prices from Chainlink AnswerUpdated logs read with HyperSync, latest answer at or before block 123,046,774
Check (Aave oracle getAssetPrice over RPC): total $243.2M, gap -0.00%
  WETH               HyperSync $1811.8172  oracle $1814.2000
  syrupUSDC          HyperSync $1.1932  oracle $1.1932
```

Pool balances change every block, so your numbers will differ.

## Change the window or chain

- **Block.** Pass a block number as the first argument to stop there. Prices are the latest Chainlink answers at or before that block, so a past block is valued at the prices of its own time.
- **Chain.** Aave v3 runs on many chains. Swap `URL` for that chain's HyperSync endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), `RPC` for a public RPC on that chain, `FEEDS` for that chain's Chainlink aggregators (find them from the adapters Aave's `getSourceOfAsset` returns), and `ORACLE` and `RESERVES` for the matching file in the [Aave address book](https://github.com/bgd-labs/aave-address-book/tree/main/src).

## Check the numbers

Each token total should match `balanceOf(aToken)` on the reserve token at the same block. Run the script with a block number, then call `balanceOf` for any aToken on [Monadscan](https://monadscan.com) or with `cast call` at that block as the comparison. Aave's own [app](https://app.aave.com) also shows each Monad market's size.

For prices, a latest-block run ends with a labelled check that values the same balances at Aave's oracle (`getAssetPrice` over Monad's public RPC) and prints both prices for each pool above $1M. In the 17 Nov run the two totals agree to within 0.01%. The only visible gaps are ETH and weETH, about $2 apart, because the oracle reads the live feed and the script reads the last answer HyperSync had at the snapshot block.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to sum every ERC-20 Transfer
into and out of each Aave v3 aToken on Monad, then prices the balances from the
Chainlink AnswerUpdated logs behind Aave's price adapters, read with HyperSync. My HyperSync token is in the ENVIO_API_TOKEN environment variable.

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
