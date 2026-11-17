# Coinbase borrowing on Morpho, Base

Coinbase's bitcoin-backed loans run through the cbBTC/USDC market on Morpho on Base, and its newer gold-backed loans run through a PAXG/USDC market. Up to Base block 58,686,515 on 17 Nov 2026, **76.5K wallets had borrowed $3.83B of USDC against cbBTC since Sep 2024, and 40.8K cbBTC sat in the market as collateral**. At the Chainlink BTC/USD price that the market's oracle reads, taken from the feed's `AnswerUpdated` logs through HyperSync, that collateral was worth about $2.65B, against $1.53B of USDC owed, which HyperSync also rebuilds from the market's events.

| | cbBTC/USDC | PAXG/USDC |
| --- | --- | --- |
| Collateral at that block | 40,821.8439 cbBTC | 133.9778 PAXG |
| USDC borrowed in total | $3,828,561,616 | $202,869 |
| Borrowers | 76,527 | 78 |
| Events | 1,613,581 | 1,246 |
| First borrow | 13 Sep 2024 | 27 Oct 2026 |

## Why it's interesting

When a big app runs loans through an open lending market, you can follow the whole book onchain. Every collateral deposit, borrow, repay and liquidation is an event on Morpho, so the market's history is a replay away. The cbBTC market has over 1.5M events, which makes it a good test of pulling a busy market from the first block.

## What it pulls

- `SupplyCollateral`, `WithdrawCollateral`, `Borrow`, `Repay` and `Liquidate` logs on Morpho on Base [`0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb`](https://basescan.org/address/0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb), from the [Morpho docs](https://docs.morpho.org/get-started/resources/addresses), for two market IDs.
  - cbBTC/USDC `0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836`
  - PAXG/USDC `0x48dca3ed245fb30931013a676d3451f7602b11150f92743ad93159628cbbe392`
- `AnswerUpdated` logs from those two Chainlink aggregators, from HyperSync, for the collateral prices. I found the aggregators from each oracle's `BASE_FEED_1()` (the PAXG oracle wraps a primary oracle with a PAXG/USD fallback, and its primary reads XAU/USD), then the feed proxy's `aggregator()`.
- The market IDs come from the Morpho API, and the script reads each market's oracle back from Morpho's `idToMarketParams` onchain. cbBTC is [`0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf`](https://basescan.org/address/0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf) (8 decimals) and PAXG is [`0xe904AEA5E1b110c9174728fA2efFc8aeD19E98Ef`](https://basescan.org/address/0xe904AEA5E1b110c9174728fA2efFc8aeD19E98Ef) (18 decimals), from the [Paxos docs](https://docs.paxos.com/guides/stablecoin/paxg/mainnet).

Collateral is `SupplyCollateral` minus `WithdrawCollateral` minus collateral seized in `Liquidate`. Morpho tracks debt in shares, and every `Borrow`, `Repay` and `Liquidate` carries the shares it adds or removes. USDC owed is the debt shares outstanding times the assets per share in the latest `Borrow` or `Repay`, so it includes interest. A borrower is any `onBehalf` address in a `Borrow` event. The cbBTC market is open to anyone on Morpho, so its totals cover every borrower in it, not only those who came through Coinbase.

Collateral, borrowers, total borrowed, USDC owed and the monthly series come from HyperSync. Dollar values for collateral use the latest `AnswerUpdated` of the Chainlink aggregator each market's oracle reads, taken from HyperSync at or before the snapshot block. The cbBTC market's oracle reads BTC/USD (aggregator `0xe5ec87a39445b8D5b751b116802A53C5ae7e9Df1`) and the PAXG market's oracle reads XAU/USD, gold per troy ounce (`0x3591Ffd547Db65020C18e80Fce399cF167B2BdcE`), and both scale the answer straight to USDC per token. The script reads each oracle's `price()` and the market's `totalBorrowAssets` over Base's public RPC only as checks.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py              # up to the latest block
python3 script.py 58686515     # up to the block used above
```

The cbBTC market has more than 1.6M events, so the script splits its history into block ranges and pulls them side by side. A full run takes about six minutes. Sample output from the block above.

```
cbBTC/USDC market 0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836 (oracle 0x663becd10dae6c4a3dcd89f1d76c1174199639b9), up to Base block 58,686,515
  collateral now: 40,821.8439 cbBTC ~ $2,647,989,983 at $64,866.99 per cbBTC (Chainlink feed, HyperSync)
  Check (oracle price() over RPC): $64,965.74 per cbBTC, gap -0.15%
  USDC owed now: $1,529,265,140 (HyperSync, debt shares outstanding times the latest borrow or repay rate)
  Check (RPC totalBorrowAssets): $1,529,265,160, gap $-19.75
  $3,828,561,616 borrowed in total since 2024-09-13
  76,527 unique borrowers, 1,613,581 collateral, borrow, repay and liquidation events
  end of each month: collateral, USDC principal outstanding (borrows minus repays)
    2024-09         16.8918 cbBTC  $         561,934
    ...
    2026-11     40,821.8439 cbBTC  $   1,443,240,918

PAXG/USDC market 0x48dca3ed245fb30931013a676d3451f7602b11150f92743ad93159628cbbe392 (oracle 0x6a47f48780eaeb07ee18ca47a9c33c925961bfad), up to Base block 58,686,515
  collateral now: 133.9778 PAXG ~ $517,394 at $3,861.79 per PAXG (Chainlink feed, HyperSync)
  Check (oracle price() over RPC): $3,861.79 per PAXG, gap +0.00%
  USDC owed now: $197,390 (HyperSync, debt shares outstanding times the latest borrow or repay rate)
  Check (RPC totalBorrowAssets): $197,385, gap $5.57
  $202,869 borrowed in total since 2026-10-27
  78 unique borrowers, 1,246 collateral, borrow, repay and liquidation events
```

Without a block number your numbers will differ a little.

## Change the window or chain

- **Block.** Pass a Base block number to rebuild the markets as they stood then.
- **Markets.** Add any Morpho market that lends USDC to `MARKETS`, with its ID and the collateral token's decimals. The script reads the oracle onchain. Find IDs in the [Morpho app](https://app.morpho.org) or the Morpho API.
- **Chain.** Morpho runs on many chains. Change `HYPERSYNC` to that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), `RPC` to a public RPC there and `MORPHO` to the address in the [Morpho docs](https://docs.morpho.org/get-started/resources/addresses).

## Check the numbers

The script checks itself against Base's public RPC at the same block. At block 58,686,515 the USDC owed rebuilt from events ($1,529,265,140) sat $20 below the market's `totalBorrowAssets` ($1,529,265,160), the interest accrued since the market's last borrow or repay. The PAXG market sat $5.57 above it. For prices, the script prints each oracle's own `price()` over RPC beside the Chainlink price it read with HyperSync. The PAXG prices were identical. The cbBTC price was 0.15% lower, because the feed's last answer in the logs ($64,866.99, posted in block 58,686,482) was newer than the $64,965.74 the oracle returned over RPC at the snapshot block. That moves the collateral value by about $4M of $2.65B. As an outside comparison, the rebuilt cbBTC collateral matches the Morpho API's `collateralAssets` to within 0.05 cbBTC, the gap being blocks between the two reads. The month-end principal (borrows minus repays, $1.54B) leaves interest out, so it sits below USDC owed.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every collateral,
borrow, repay and liquidation event in two Morpho markets on Base and rebuild
collateral and borrowers. My HyperSync token is in the ENVIO_API_TOKEN
environment variable.

Add a weekly count of new borrowers (the first Borrow for each onBehalf address)
for the cbBTC/USDC market since it opened, and write it to a CSV. Keep the
standard library only. Then check three borrowers against position(marketId,
borrower) on Morpho at the same block.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Morpho addresses](https://docs.morpho.org/get-started/resources/addresses)
- [PAXG on Morpho, Base](../../rwa-and-funds/paxg-on-morpho-base), a deeper look at the gold market
- [Envio Discord](https://discord.gg/envio)
